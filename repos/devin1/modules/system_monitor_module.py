"""
System Monitor Module
Monitors system health, performance, and robot diagnostics.
"""

import psutil
import platform
import datetime
from typing import Dict, List, Any, Optional


class SystemMonitor:
    """
    Monitors and provides system health information, including CPU, memory, disk, and network statistics.
    """

    def get_cpu_usage(self) -> Dict[str, Any]:
        """
        Retrieves CPU usage details.

        Returns:
            Dict[str, Any]: CPU usage percentage and per-core utilization.
        """
        return {
            "total_usage": psutil.cpu_percent(interval=1),
            "per_core_usage": psutil.cpu_percent(interval=1, percpu=True),
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
        }

    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Retrieves memory usage details.

        Returns:
            Dict[str, Any]: Memory usage statistics.
        """
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percentage": mem.percent,
        }

    def get_disk_usage(self) -> List[Dict[str, Any]]:
        """
        Retrieves disk usage details for all partitions.

        Returns:
            List[Dict[str, Any]]: List of disk partitions and their usage details.
        """
        disk_partitions = psutil.disk_partitions()
        usage_details = []
        for partition in disk_partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                usage_details.append(
                    {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percentage": usage.percent,
                    }
                )
            except PermissionError:
                continue
        return usage_details

    def get_network_usage(self) -> Dict[str, Any]:
        """
        Retrieves network usage statistics.

        Returns:
            Dict[str, Any]: Network IO statistics.
        """
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_received": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_received": net_io.packets_recv,
        }

    def get_system_info(self) -> Dict[str, str]:
        """
        Retrieves general system information.

        Returns:
            Dict[str, str]: System details like OS, architecture, and boot time.
        """
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "boot_time": str(datetime.datetime.fromtimestamp(psutil.boot_time())),
        }


class RobotDiagnostics:
    """
    Monitors and provides diagnostics for robot systems.
    """

    def check_battery_status(self) -> Optional[Dict[str, Any]]:
        """
        Checks the battery status.

        Returns:
            Optional[Dict[str, Any]]: Battery status details if a battery is present, else None.
        """
        battery = psutil.sensors_battery()
        if not battery:
            return None
        return {
            "percentage": battery.percent,
            "charging": battery.power_plugged,
            "time_left": battery.secsleft,
        }

    def check_temperature(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Checks system temperatures.

        Returns:
            Dict[str, List[Dict[str, Any]]]: Temperature statistics for various hardware components.
        """
        temperatures = psutil.sensors_temperatures()
        return {
            sensor: [
                {"label": temp.label, "current": temp.current, "high": temp.high, "critical": temp.critical}
                for temp in temps
            ]
            for sensor, temps in temperatures.items()
        }

    def run_diagnostics(self) -> Dict[str, Any]:
        """
        Runs full diagnostics on the robot.

        Returns:
            Dict[str, Any]: A summary of all diagnostic information.
        """
        diagnostics = {
            "battery_status": self.check_battery_status(),
            "temperature_status": self.check_temperature(),
        }
        return diagnostics


class SystemMonitorModule:
    """
    Unified interface for system monitoring and robot diagnostics.
    """

    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.robot_diagnostics = RobotDiagnostics()

    def get_full_status(self) -> Dict[str, Any]:
        """
        Retrieves a comprehensive status report.

        Returns:
            Dict[str, Any]: Combined system and robot diagnostics status.
        """
        return {
            "system_info": self.system_monitor.get_system_info(),
            "cpu_usage": self.system_monitor.get_cpu_usage(),
            "memory_usage": self.system_monitor.get_memory_usage(),
            "disk_usage": self.system_monitor.get_disk_usage(),
            "network_usage": self.system_monitor.get_network_usage(),
            "robot_diagnostics": self.robot_diagnostics.run_diagnostics(),
        }


# Example Usage
if __name__ == "__main__":
    module = SystemMonitorModule()
    full_status = module.get_full_status()

    print("System and Robot Status:")
    for key, value in full_status.items():
        print(f"{key.capitalize()}: {value}")
