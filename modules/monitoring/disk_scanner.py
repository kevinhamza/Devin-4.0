# Devin/modules/monitoring/disk_scanner.py
# Purpose: Disk usage monitoring utilities.

import logging
from typing import Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None  # type: ignore
    PSUTIL_AVAILABLE = False

logger = logging.getLogger("DiskScanner")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False


def get_disk_usage(path: str = '/') -> Dict[str, Any]:
    """Returns disk usage stats for the given path as a plain dict."""
    if not PSUTIL_AVAILABLE:
        return {}
    try:
        usage = psutil.disk_usage(path)
        return {
            "path": path,
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent,
        }
    except Exception as e:
        logger.error(f"Failed to get disk usage for '{path}': {e}")
        return {}


def get_all_disk_partitions() -> list:
    """Returns a list of mounted disk partitions with their usage stats."""
    if not PSUTIL_AVAILABLE:
        return []
    partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            })
        except (PermissionError, Exception):
            pass
    return partitions
