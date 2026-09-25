"""
Enhanced system monitor for Devin-4.0.
Monitors CPU, memory, disk, processes, network, and GPU usage.
"""

import os
import sys
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

_HAS_PSUTIL = False
try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    pass

_HAS_GPUTIL = False
try:
    import GPUtil
    _HAS_GPUTIL = True
except ImportError:
    pass


@dataclass
class CPUInfo:
    percent: float
    per_core: List[float]
    freq_mhz: float
    count_logical: int
    count_physical: int
    load_avg: List[float]


@dataclass
class MemoryInfo:
    total_gb: float
    available_gb: float
    used_gb: float
    percent: float
    swap_total_gb: float
    swap_used_gb: float
    swap_percent: float


@dataclass
class DiskInfo:
    device: str
    mountpoint: str
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float


@dataclass
class ProcessInfo:
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    username: str
    cmdline: str


@dataclass
class NetworkInfo:
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errin: int
    errout: int
    interfaces: Dict[str, Dict]


@dataclass
class GPUInfo:
    id: int
    name: str
    load_percent: float
    memory_total_mb: float
    memory_used_mb: float
    memory_free_mb: float
    temperature_c: float


@dataclass
class SystemSnapshot:
    timestamp: float
    cpu: Optional[CPUInfo]
    memory: Optional[MemoryInfo]
    disks: List[DiskInfo]
    processes_top: List[ProcessInfo]
    network: Optional[NetworkInfo]
    gpus: List[GPUInfo]
    alerts: List[str]


_THRESHOLDS = {
    "cpu_percent": 85.0,
    "memory_percent": 90.0,
    "disk_percent": 90.0,
    "swap_percent": 80.0,
}


class SystemMonitor:
    """Comprehensive system resource monitor with alerting and history."""

    def __init__(
        self,
        history_size: int = 60,
        cpu_threshold: float = _THRESHOLDS["cpu_percent"],
        memory_threshold: float = _THRESHOLDS["memory_percent"],
        disk_threshold: float = _THRESHOLDS["disk_percent"],
        alert_callback: Optional[Callable[[str], None]] = None,
    ):
        self.history_size = history_size
        self.thresholds = {
            "cpu_percent": cpu_threshold,
            "memory_percent": memory_threshold,
            "disk_percent": disk_threshold,
            "swap_percent": _THRESHOLDS["swap_percent"],
        }
        self.alert_callback = alert_callback
        self._history: List[SystemSnapshot] = []
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        self._interval = 5.0

    # --- Data collection ---

    def _collect_cpu(self) -> Optional[CPUInfo]:
        if not _HAS_PSUTIL:
            return None
        try:
            pct = psutil.cpu_percent(interval=0.1)
            per_core = psutil.cpu_percent(interval=None, percpu=True)
            freq = psutil.cpu_freq()
            freq_mhz = freq.current if freq else 0.0
            logical = psutil.cpu_count(logical=True) or 0
            physical = psutil.cpu_count(logical=False) or 0
            load_avg = list(os.getloadavg()) if hasattr(os, "getloadavg") else [0.0, 0.0, 0.0]
            return CPUInfo(
                percent=pct,
                per_core=list(per_core) if per_core else [],
                freq_mhz=freq_mhz,
                count_logical=logical,
                count_physical=physical,
                load_avg=load_avg,
            )
        except Exception:
            return None

    def _collect_memory(self) -> Optional[MemoryInfo]:
        if not _HAS_PSUTIL:
            return None
        try:
            vm = psutil.virtual_memory()
            sw = psutil.swap_memory()
            gb = 1024 ** 3
            return MemoryInfo(
                total_gb=vm.total / gb,
                available_gb=vm.available / gb,
                used_gb=vm.used / gb,
                percent=vm.percent,
                swap_total_gb=sw.total / gb,
                swap_used_gb=sw.used / gb,
                swap_percent=sw.percent,
            )
        except Exception:
            return None

    def _collect_disks(self) -> List[DiskInfo]:
        if not _HAS_PSUTIL:
            return []
        disks = []
        try:
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    gb = 1024 ** 3
                    disks.append(DiskInfo(
                        device=part.device,
                        mountpoint=part.mountpoint,
                        total_gb=usage.total / gb,
                        used_gb=usage.used / gb,
                        free_gb=usage.free / gb,
                        percent=usage.percent,
                    ))
                except (PermissionError, OSError):
                    pass
        except Exception:
            pass
        return disks

    def _collect_processes(self, top_n: int = 10) -> List[ProcessInfo]:
        if not _HAS_PSUTIL:
            return []
        procs = []
        try:
            for proc in psutil.process_iter(
                ["pid", "name", "status", "cpu_percent", "memory_info",
                 "memory_percent", "username", "cmdline"]
            ):
                try:
                    info = proc.info
                    mem_mb = (info["memory_info"].rss / (1024 ** 2)) if info.get("memory_info") else 0.0
                    cmdline = " ".join(info.get("cmdline") or [])[:200]
                    procs.append(ProcessInfo(
                        pid=info["pid"],
                        name=info.get("name") or "",
                        status=info.get("status") or "",
                        cpu_percent=info.get("cpu_percent") or 0.0,
                        memory_mb=mem_mb,
                        memory_percent=info.get("memory_percent") or 0.0,
                        username=info.get("username") or "",
                        cmdline=cmdline,
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass
        procs.sort(key=lambda p: p.cpu_percent, reverse=True)
        return procs[:top_n]

    def _collect_network(self) -> Optional[NetworkInfo]:
        if not _HAS_PSUTIL:
            return None
        try:
            counters = psutil.net_io_counters()
            ifaces: Dict[str, Dict] = {}
            for iface, c in psutil.net_io_counters(pernic=True).items():
                ifaces[iface] = {
                    "bytes_sent": c.bytes_sent,
                    "bytes_recv": c.bytes_recv,
                    "packets_sent": c.packets_sent,
                    "packets_recv": c.packets_recv,
                }
            return NetworkInfo(
                bytes_sent=counters.bytes_sent,
                bytes_recv=counters.bytes_recv,
                packets_sent=counters.packets_sent,
                packets_recv=counters.packets_recv,
                errin=counters.errin,
                errout=counters.errout,
                interfaces=ifaces,
            )
        except Exception:
            return None

    def _collect_gpus(self) -> List[GPUInfo]:
        if not _HAS_GPUTIL:
            return []
        try:
            gpus = []
            for g in GPUtil.getGPUs():
                gpus.append(GPUInfo(
                    id=g.id,
                    name=g.name,
                    load_percent=g.load * 100,
                    memory_total_mb=g.memoryTotal,
                    memory_used_mb=g.memoryUsed,
                    memory_free_mb=g.memoryFree,
                    temperature_c=g.temperature,
                ))
            return gpus
        except Exception:
            return []

    def _check_alerts(self, snap: SystemSnapshot) -> List[str]:
        alerts = []
        if snap.cpu and snap.cpu.percent > self.thresholds["cpu_percent"]:
            alerts.append(f"HIGH CPU: {snap.cpu.percent:.1f}%")
        if snap.memory and snap.memory.percent > self.thresholds["memory_percent"]:
            alerts.append(f"HIGH MEMORY: {snap.memory.percent:.1f}%")
        if snap.memory and snap.memory.swap_percent > self.thresholds["swap_percent"]:
            alerts.append(f"HIGH SWAP: {snap.memory.swap_percent:.1f}%")
        for disk in snap.disks:
            if disk.percent > self.thresholds["disk_percent"]:
                alerts.append(f"HIGH DISK {disk.mountpoint}: {disk.percent:.1f}%")
        return alerts

    # --- Snapshot ---

    def snapshot(self) -> SystemSnapshot:
        snap = SystemSnapshot(
            timestamp=time.time(),
            cpu=self._collect_cpu(),
            memory=self._collect_memory(),
            disks=self._collect_disks(),
            processes_top=self._collect_processes(),
            network=self._collect_network(),
            gpus=self._collect_gpus(),
            alerts=[],
        )
        snap.alerts = self._check_alerts(snap)
        if snap.alerts and self.alert_callback:
            for alert in snap.alerts:
                try:
                    self.alert_callback(alert)
                except Exception:
                    pass
        return snap

    def snapshot_dict(self) -> Dict:
        snap = self.snapshot()
        return {
            "timestamp": snap.timestamp,
            "cpu": snap.cpu.__dict__ if snap.cpu else None,
            "memory": snap.memory.__dict__ if snap.memory else None,
            "disks": [d.__dict__ for d in snap.disks],
            "processes_top": [p.__dict__ for p in snap.processes_top],
            "network": snap.network.__dict__ if snap.network else None,
            "gpus": [g.__dict__ for g in snap.gpus],
            "alerts": snap.alerts,
        }

    def summary(self) -> str:
        snap = self.snapshot()
        lines = ["=== System Status ==="]
        if snap.cpu:
            lines.append(
                f"CPU    : {snap.cpu.percent:.1f}% | "
                f"{snap.cpu.count_logical} cores | {snap.cpu.freq_mhz:.0f} MHz"
            )
            if snap.cpu.load_avg:
                lines.append(
                    f"Load   : {snap.cpu.load_avg[0]:.2f} "
                    f"{snap.cpu.load_avg[1]:.2f} {snap.cpu.load_avg[2]:.2f}"
                )
        else:
            lines.append("CPU    : unavailable (install psutil)")
        if snap.memory:
            lines.append(
                f"Memory : {snap.memory.used_gb:.1f}/{snap.memory.total_gb:.1f} GB "
                f"({snap.memory.percent:.1f}%)"
            )
            if snap.memory.swap_total_gb > 0:
                lines.append(
                    f"Swap   : {snap.memory.swap_used_gb:.1f}/{snap.memory.swap_total_gb:.1f} GB "
                    f"({snap.memory.swap_percent:.1f}%)"
                )
        else:
            lines.append("Memory : unavailable")
        for disk in snap.disks[:3]:
            lines.append(
                f"Disk {disk.mountpoint}: {disk.used_gb:.1f}/{disk.total_gb:.1f} GB "
                f"({disk.percent:.1f}%)"
            )
        if snap.network:
            mb = 1024 ** 2
            lines.append(
                f"Net    : ↑{snap.network.bytes_sent/mb:.1f} MB  "
                f"↓{snap.network.bytes_recv/mb:.1f} MB"
            )
        for gpu in snap.gpus:
            lines.append(
                f"GPU {gpu.id} ({gpu.name}): {gpu.load_percent:.1f}% | "
                f"{gpu.memory_used_mb:.0f}/{gpu.memory_total_mb:.0f} MB | {gpu.temperature_c:.0f}°C"
            )
        if snap.alerts:
            lines.append("\n⚠ ALERTS:")
            for a in snap.alerts:
                lines.append(f"  ! {a}")
        if snap.processes_top:
            lines.append("\nTop processes (CPU):")
            for p in snap.processes_top[:5]:
                lines.append(
                    f"  [{p.pid}] {p.name}: CPU {p.cpu_percent:.1f}% MEM {p.memory_mb:.1f}MB"
                )
        return "\n".join(lines)

    # --- Background monitoring ---

    def start_background(self, interval: float = 5.0) -> None:
        self._interval = interval
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_background(self) -> None:
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=10)

    def _monitor_loop(self) -> None:
        while self._running:
            try:
                snap = self.snapshot()
                with self._lock:
                    self._history.append(snap)
                    if len(self._history) > self.history_size:
                        self._history.pop(0)
            except Exception:
                pass
            time.sleep(self._interval)

    def get_history(self) -> List[Dict]:
        with self._lock:
            return [
                {
                    "timestamp": s.timestamp,
                    "cpu_percent": s.cpu.percent if s.cpu else None,
                    "memory_percent": s.memory.percent if s.memory else None,
                    "alerts": s.alerts,
                }
                for s in self._history
            ]

    # --- Process management ---

    def kill_process(self, pid: int) -> str:
        if not _HAS_PSUTIL:
            return "ERROR: psutil not available"
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                proc.kill()
            return f"Terminated process {pid} ({name})"
        except psutil.NoSuchProcess:
            return f"ERROR: process {pid} not found"
        except psutil.AccessDenied:
            return f"ERROR: access denied killing process {pid}"
        except Exception as e:
            return f"ERROR: {e}"

    def find_processes(self, name_pattern: str) -> List[Dict]:
        if not _HAS_PSUTIL:
            return []
        results = []
        try:
            for proc in psutil.process_iter(["pid", "name", "status", "cpu_percent", "memory_percent"]):
                try:
                    if name_pattern.lower() in (proc.info.get("name") or "").lower():
                        results.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass
        return results

    def set_process_priority(self, pid: int, nice: int) -> str:
        if not _HAS_PSUTIL:
            return "ERROR: psutil not available"
        try:
            proc = psutil.Process(pid)
            proc.nice(nice)
            return f"Set process {pid} nice value to {nice}"
        except psutil.NoSuchProcess:
            return f"ERROR: process {pid} not found"
        except psutil.AccessDenied:
            return "ERROR: access denied"
        except Exception as e:
            return f"ERROR: {e}"


_monitor_instance: Optional[SystemMonitor] = None


def get_system_monitor(**kwargs) -> SystemMonitor:
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SystemMonitor(**kwargs)
    return _monitor_instance


def system_summary() -> str:
    return get_system_monitor().summary()


def system_snapshot() -> Dict:
    return get_system_monitor().snapshot_dict()
