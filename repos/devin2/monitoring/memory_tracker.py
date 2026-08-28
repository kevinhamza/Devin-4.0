# Devin/monitoring/memory_tracker.py
# Purpose: A toolkit for monitoring system and process-level memory utilization,
#          with background alerting and live visualization capabilities.

import logging
import psutil
import threading
import time
import os
from typing import List, Dict, Optional, Callable, Any
from collections import deque

try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("MemoryTracker")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

def format_bytes(byte_count: int) -> str:
    """Helper function to format bytes into KB, MB, GB, etc."""
    if byte_count is None: return "N/A"
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while byte_count >= power and n < len(power_labels):
        byte_count /= power
        n += 1
    return f"{byte_count:.2f} {power_labels[n]}B"

class MemoryTracker:
    """
    Provides a suite of tools for monitoring memory usage.
    """
    def __init__(self):
        if not psutil:
            raise ImportError("psutil library is required. Please 'pip install psutil'.")
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def get_virtual_memory_usage(self) -> psutil._common.svmem:
        """Gets system-wide virtual memory (RAM) statistics."""
        return psutil.virtual_memory()

    def get_swap_memory_usage(self) -> psutil._common.sswap:
        """Gets system-wide swap memory statistics."""
        return psutil.swap_memory()

    def get_process_memory_usage(self, pid: int) -> Optional[psutil._common.pmem]:
        """Gets the memory usage for a specific process."""
        try:
            process = psutil.Process(pid)
            return process.memory_info()
        except psutil.NoSuchProcess:
            logger.error(f"No process found with PID: {pid}")
            return None

    def get_top_processes_by_memory(self, count: int = 5) -> List[Dict[str, Any]]:
        """Gets a list of the top N processes by memory usage (RSS)."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                memory_info = proc.memory_info()
                processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "rss": memory_info.rss, # Resident Set Size
                    "username": proc.info['username']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return sorted(processes, key=lambda p: p['rss'], reverse=True)[:count]

    def _monitor_loop(self, threshold: float, callback: Callable[[float], None], interval: int):
        """The internal loop for the background monitoring thread."""
        logger.info(f"Background memory monitoring started. Threshold: >{threshold}%.")
        while not self._stop_event.is_set():
            usage_percent = psutil.virtual_memory().percent
            if usage_percent > threshold:
                logger.warning(f"Memory usage ({usage_percent}%) exceeded threshold ({threshold}%).")
                callback(usage_percent)
            time.sleep(interval)
        logger.info("Background memory monitoring stopped.")

    def start_monitoring(self, threshold: float = 85.0, interval: int = 5, callback: Callable[[float], None] = lambda u: None):
        """Starts monitoring memory usage in a background thread."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            logger.warning("Monitoring is already running.")
            return

        self._stop_event.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitor_loop,
            args=(threshold, callback, interval),
            daemon=True
        )
        self._monitoring_thread.start()

    def stop_monitoring(self):
        """Stops the background monitoring thread."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._stop_event.set()
            self._monitoring_thread.join()
        else:
            logger.info("Monitoring is not running.")

    def plot_live_usage(self, max_points: int = 60):
        """Displays a real-time plot of RAM usage."""
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Matplotlib is required for plotting. 'pip install matplotlib'")
        
        plt.style.use('fivethirtyeight')
        fig, ax = plt.subplots()
        data = deque(maxlen=max_points)
        
        def animate(i):
            usage = psutil.virtual_memory().percent
            data.append(usage)
            ax.clear()
            ax.plot(data)
            ax.set_ylim(0, 100)
            ax.set_title("Live RAM Usage")
            ax.set_ylabel("Usage (%)")
        
        ani = animation.FuncAnimation(fig, animate, interval=1000)
        plt.tight_layout()
        plt.show()


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== System Memory Tracking Prototype 🧠📊 ===")
    print("=========================================================")
    
    tracker = MemoryTracker()
    
    # 1. Get system-wide memory usage
    print("\n--- System Memory Usage ---")
    vmem = tracker.get_virtual_memory_usage()
    swap = tracker.get_swap_memory_usage()
    print(f"RAM Usage: {vmem.percent}% ({format_bytes(vmem.used)} / {format_bytes(vmem.total)})")
    print(f"Swap Usage: {swap.percent}% ({format_bytes(swap.used)} / {format_bytes(swap.total)})")
    
    # 2. Get usage for the current Python process
    print("\n--- Current Process Memory Usage ---")
    own_pid = os.getpid()
    proc_mem = tracker.get_process_memory_usage(own_pid)
    print(f"Monitoring PID {own_pid} (this script)...")
    print(f"Resident Set Size (RSS): {format_bytes(proc_mem.rss)}")
    
    # 3. Get top 5 memory-consuming processes
    print("\n--- Top 5 Processes by Memory Usage ---")
    top_procs = tracker.get_top_processes_by_memory(count=5)
    for p in top_procs:
        print(f"  - PID: {p['pid']}, Name: {p['name']}, RSS: {format_bytes(p['rss'])}")
        
    # 4. Background monitoring and alerting demo
    print("\n--- Background Alerting Demo ---")
    def high_mem_alert(usage_percent: float):
        print(f"  [ALERT CALLBACK] High memory detected: {usage_percent}%!")
        
    # Using a high threshold as this is less likely to trigger than CPU.
    tracker.start_monitoring(threshold=95.0, interval=2, callback=high_mem_alert)
    print("Monitoring memory usage in background for 6 seconds...")
    time.sleep(6)
    tracker.stop_monitoring()
    
    print("\n--- Plotting Demo ---")
    print("The 'plot_live_usage' function will open a new window with a real-time graph.")
    print("Close the graph window to end the script.")
    print("Uncomment the line below to run it.")
    # try:
    #     tracker.plot_live_usage()
    # except Exception as e:
    #     logger.error(f"Plotting failed: {e}")

    print("\n=========================================================")
    print("=== Memory Tracking Prototype Complete ===")
    print("=========================================================")
