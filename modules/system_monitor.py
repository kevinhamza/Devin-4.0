# Devin/modules/system_monitor.py
# Purpose: A comprehensive suite for monitoring system resources on both the
#          local host and remote machines.

import logging
import sys
import re
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

try:
    import psutil
    from modules.os_operations.other_operations import GenericRemoteShell
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("SystemMonitor")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

# --- Data Model for Metrics ---
@dataclass
class SystemMetrics:
    """A standardized dataclass for system health metrics."""
    host: str
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    disk_usage_percent: Optional[float] = None
    net_bytes_sent: Optional[int] = None
    net_bytes_recv: Optional[int] = None

# --- Individual Monitor Implementations ---

class LocalMonitor:
    """Monitors the local machine using the psutil library."""
    def __init__(self):
        if 'psutil' not in sys.modules and not DEVIN_CORE_AVAILABLE:
             logger.warning("psutil not found. LocalMonitor metrics will be empty.")
        self.host = "localhost"
        logger.info("LocalMonitor initialized.")

    def get_metrics(self) -> SystemMetrics:
        """Gathers and returns metrics from the local system."""
        try:
            net_io = psutil.net_io_counters()
            return SystemMetrics(
                host=self.host,
                cpu_usage_percent=psutil.cpu_percent(interval=1),
                memory_usage_percent=psutil.virtual_memory().percent,
                disk_usage_percent=psutil.disk_usage('/').percent,
                net_bytes_sent=net_io.bytes_sent,
                net_bytes_recv=net_io.bytes_recv
            )
        except (ImportError, Exception):
            return SystemMetrics(host=self.host)

class RemoteMonitor:
    """Monitors a remote Linux machine by executing commands over SSH."""
    def __init__(self, ssh_client: 'GenericRemoteShell'):
        self.ssh = ssh_client
        self.host = ssh_client.host
        logger.info(f"RemoteMonitor initialized for host '{self.host}'.")

    def _parse_top_output_cpu(self, output: str) -> Optional[float]:
        """Parses the '%Cpu(s)' line from `top` to get CPU usage."""
        match = re.search(r"%Cpu\(s\):.*,\s*([\d.]+)\s+id", output)
        if match:
            idle_percent = float(match.group(1))
            return 100.0 - idle_percent
        return None

    def _parse_free_output_memory(self, output: str) -> Optional[float]:
        """Parses the output of `free -b` to get memory usage percentage."""
        lines = output.splitlines()
        if len(lines) > 1 and lines[0].startswith("      "): # A simple check for the correct header
            parts = lines[1].split()
            if len(parts) >= 3 and parts[0] == "Mem:":
                total_mem = int(parts[1])
                used_mem = int(parts[2])
                return (used_mem / total_mem) * 100 if total_mem > 0 else 0
        return None

    def _parse_df_output_disk(self, output: str) -> Optional[float]:
        """Parses the output of `df -h /` to get root disk usage."""
        match = re.search(r"(\d+)%\s+/$", output, re.MULTILINE)
        if match:
            return float(match.group(1))
        return None

    def _parse_net_dev_output(self, output: str) -> 'tuple[Optional[int], Optional[int]]':
        """
        Parses the output of `cat /proc/net/dev` to get bytes sent/received.

        Format per line is `iface: rx_bytes rx_packets rx_errs rx_drop rx_fifo
        rx_frame rx_compressed rx_multicast tx_bytes tx_packets tx_errs tx_drop
        tx_fifo tx_colls tx_carrier tx_compressed`, so tx_bytes (net_bytes_sent)
        is the 9th whitespace-separated field after the interface name, and
        rx_bytes (net_bytes_recv) is the 1st. The loopback interface ('lo') is
        skipped in favor of the first real interface found.
        """
        for line in output.splitlines():
            line = line.strip()
            if ':' not in line:
                continue
            iface_name, rest = line.split(':', 1)
            iface_name = iface_name.strip()
            if not iface_name or iface_name == 'lo' or iface_name.lower() == 'face':
                continue
            parts = rest.split()
            if len(parts) >= 9:
                rx_bytes = int(parts[0])
                tx_bytes = int(parts[8])
                return tx_bytes, rx_bytes
        return None, None

    def get_metrics(self) -> SystemMetrics:
        """Gathers and returns metrics from the remote system."""
        metrics = SystemMetrics(host=self.host)
        
        # CPU
        top_res = self.ssh.execute_command("top -bn1")
        if top_res['exit_code'] == 0:
            metrics.cpu_usage_percent = self._parse_top_output_cpu(top_res['stdout'])
        
        # Memory
        free_res = self.ssh.execute_command("free -b")
        if free_res['exit_code'] == 0:
            metrics.memory_usage_percent = self._parse_free_output_memory(free_res['stdout'])

        # Disk
        df_res = self.ssh.execute_command("df -h /")
        if df_res['exit_code'] == 0:
            metrics.disk_usage_percent = self._parse_df_output_disk(df_res['stdout'])

        # Network
        net_res = self.ssh.execute_command("cat /proc/net/dev")
        if net_res['exit_code'] == 0:
            sent, recv = self._parse_net_dev_output(net_res['stdout'])
            metrics.net_bytes_sent = sent
            metrics.net_bytes_recv = recv

        return metrics

# --- Main Facade ---

class SystemMonitorFacade:
    """
    A facade that provides a unified interface to all system monitoring capabilities.
    """
    def __init__(self, monitors: List[Any]):
        if not DEVIN_CORE_AVAILABLE:
            logger.warning(f"Some system monitoring features may be degraded. Error: {_import_error}")
        
        self.monitors = monitors
        logger.info(f"SystemMonitorFacade initialized with {len(monitors)} monitors.")

    def get_all_metrics(self) -> Dict[str, SystemMetrics]:
        """
        Generates a comprehensive health report from all configured monitors.
        """
        logger.info("Generating system health report from all monitors...")
        report = {}
        for monitor in self.monitors:
            try:
                metrics = monitor.get_metrics()
                report[metrics.host] = metrics
            except Exception as e:
                logger.error(f"Failed to get metrics from monitor for host '{getattr(monitor, 'host', 'unknown')}': {e}")
        
        logger.info("System health report generated successfully.")
        return report

# --- Example Usage ---
if __name__ == "__main__":
    import sys
    print("=========================================================")
    print("=== System Monitor Suite Demo 🩺💻 ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module is missing: {_import_error}")
    else:
        # --- 1. Initialize the Local Monitor ---
        print("\n--- 1. Getting metrics from Local Monitor ---")
        local_monitor = LocalMonitor()
        local_metrics = local_monitor.get_metrics()
        print(f"  - Host: {local_metrics.host}")
        print(f"  - CPU Usage: {local_metrics.cpu_usage_percent:.1f}%")
        print(f"  - Memory Usage: {local_metrics.memory_usage_percent:.1f}%")
        
        # --- 2. Initialize the Facade with all monitors ---
        # A remote monitor would be added here if SSH was configured, e.g.:
        # ssh_client = GenericRemoteShell(host="remote.server.com", user="user", password="password")
        # remote_monitor = RemoteMonitor(ssh_client)
        
        all_monitors = [local_monitor] #, remote_monitor]
        
        facade = SystemMonitorFacade(monitors=all_monitors)
        
        # --- 3. Generate and Display a Full Health Report ---
        print("\n--- 2. Generating Full Report from Facade ---")
        health_report = facade.get_all_metrics()
        
        for host, metrics in health_report.items():
            print(f"\n  Metrics for Host: {host}")
            print(f"  --------------------------")
            print(f"    CPU Usage:    {metrics.cpu_usage_percent:.1f}%")
            print(f"    Memory Usage: {metrics.memory_usage_percent:.1f}%")
            print(f"    Disk Usage:   {metrics.disk_usage_percent:.1f}%")
            print(f"    Net Sent/Recv: {metrics.net_bytes_sent}b / {metrics.net_bytes_recv}b")
            
    print("\n=========================================================")
    print("=== System Monitor Suite Demo Complete ===")
    print("=========================================================")
