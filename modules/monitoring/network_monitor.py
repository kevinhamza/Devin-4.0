# Devin/modules/monitoring/network_monitor.py
# Purpose: Network I/O monitoring utilities.

import logging
from typing import Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None  # type: ignore
    PSUTIL_AVAILABLE = False

logger = logging.getLogger("NetworkMonitor")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False


def get_network_stats() -> Dict[str, Any]:
    """Returns cumulative network bytes sent/received since system boot."""
    if not PSUTIL_AVAILABLE:
        return {}
    try:
        io = psutil.net_io_counters()
        return {
            "bytes_sent": io.bytes_sent,
            "bytes_recv": io.bytes_recv,
            "packets_sent": io.packets_sent,
            "packets_recv": io.packets_recv,
            "errin": io.errin,
            "errout": io.errout,
            "dropin": io.dropin,
            "dropout": io.dropout,
        }
    except Exception as e:
        logger.error(f"Failed to get network stats: {e}")
        return {}


def get_network_connections() -> list:
    """Returns a list of active network connections (requires root on some systems)."""
    if not PSUTIL_AVAILABLE:
        return []
    try:
        conns = []
        for conn in psutil.net_connections(kind='inet'):
            conns.append({
                "fd": conn.fd,
                "family": str(conn.family),
                "type": str(conn.type),
                "laddr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                "raddr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                "status": conn.status,
                "pid": conn.pid,
            })
        return conns
    except (psutil.AccessDenied, Exception) as e:
        logger.warning(f"Could not list network connections: {e}")
        return []
