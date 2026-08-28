"""
memory_tracker.py
-----------------
This module monitors memory usage in real-time, logs excessive memory usage, and provides memory optimization suggestions.
"""

import os
import psutil
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='logs/memory_tracker.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def get_memory_usage():
    """
    Get the current memory usage of the system.
    Returns:
        dict: Memory statistics including total, available, used, and percentage used.
    """
    memory = psutil.virtual_memory()
    return {
        "total": memory.total,
        "available": memory.available,
        "used": memory.used,
        "percentage": memory.percent,
    }

def log_memory_usage():
    """
    Log the current memory usage statistics.
    """
    usage = get_memory_usage()
    logger.info(
        f"Memory Usage - Total: {usage['total'] // (1024 ** 2)} MB, "
        f"Used: {usage['used'] // (1024 ** 2)} MB, "
        f"Available: {usage['available'] // (1024 ** 2)} MB, "
        f"Percentage: {usage['percentage']}%"
    )

def monitor_memory(threshold=80):
    """
    Continuously monitor memory usage and log warnings when usage exceeds the threshold.
    Args:
        threshold (int): Memory usage percentage threshold to trigger warnings.
    """
    while True:
        usage = get_memory_usage()
        if usage['percentage'] > threshold:
            logger.warning(
                f"High memory usage detected: {usage['percentage']}%. "
                f"Consider closing unused applications or increasing memory resources."
            )
        log_memory_usage()
        time.sleep(5)

def suggest_optimizations():
    """
    Suggest memory optimizations based on the current usage.
    Returns:
        list: List of suggested optimizations.
    """
    usage = get_memory_usage()
    suggestions = []
    if usage['percentage'] > 75:
        suggestions.append("Close unused applications.")
    if usage['available'] < (usage['total'] * 0.1):
        suggestions.append("Consider adding more physical memory.")
    if len(suggestions) == 0:
        suggestions.append("Memory usage is within normal limits.")
    return suggestions

if __name__ == "__main__":
    logger.info("Starting Memory Tracker...")
    try:
        monitor_memory()
    except KeyboardInterrupt:
        logger.info("Memory Tracker stopped by user.")
