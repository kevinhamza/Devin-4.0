# Devin/monitoring/cpu_usage.py
# Purpose: A toolkit for monitoring system and process-level CPU utilization,
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
logger = logging.getLogger("CPU_Monitor")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class CPU_Monitor:
    """
    Provides a suite of tools for monitoring CPU usage.
    """
    def __init__(self):
        if not psutil:
            raise ImportError("psutil library is required. Please 'pip install psutil'.")
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def get_system_cpu_usage(self, per_cpu: bool = False) -> Any:
        """Gets the current system-wide CPU utilization percentage."""
        return psutil.cpu_percent(interval=1, percpu=per_cpu)

    def get_process_cpu_usage(self, pid: int) -> Optional[float]:
        """Gets the CPU utilization percentage for a specific process."""
        try:
            process = psutil.Process(pid)
            # The first call to cpu_percent for a process should have interval=None
            # to initialize it. Subsequent calls can have an interval.
            process.cpu_percent(interval=None)
            time.sleep(1) # Wait for a second to get a meaningful reading
            return process.cpu_percent(interval=None)
        except psutil.NoSuchProcess:
            logger.error(f"No process found with PID: {pid}")
            return None

    def get_top_processes(self, count: int = 5) -> List[Dict[str, Any]]:
        """Gets a list of the top N processes by CPU usage."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                # Initialize cpu_percent for all processes
                proc.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Wait a bit to get meaningful data
        time.sleep(1)

        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                cpu_usage = proc.cpu_percent(interval=None)
                if cpu_usage > 0.0: # Only include processes with some usage
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "cpu_usage": cpu_usage,
                        "username": proc.info['username']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return sorted(processes, key=lambda p: p['cpu_usage'], reverse=True)[:count]

    def _monitor_loop(self, threshold: float, callback: Callable[[float], None], interval: int):
        """The internal loop for the background monitoring thread."""
        logger.info(f"Background monitoring started. Threshold: >{threshold}%.")
        while not self._stop_event.is_set():
            usage = psutil.cpu_percent(interval=interval)
            if usage > threshold:
                logger.warning(f"CPU usage ({usage}%) exceeded threshold ({threshold}%).")
                callback(usage)
            # No need for extra sleep, interval in cpu_percent handles it.
        logger.info("Background monitoring stopped.")

    def start_monitoring(self, threshold: float = 80.0, interval: int = 5, callback: Callable[[float], None] = lambda u: None):
        """Starts monitoring CPU usage in a background thread."""
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
        """Displays a real-time plot of CPU usage."""
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("Matplotlib is required for plotting. 'pip install matplotlib'")
        
        plt.style.use('fivethirtyeight')
        fig, ax = plt.subplots()
        data = deque(maxlen=max_points)
        
        def animate(i):
            usage = psutil.cpu_percent(interval=None)
            data.append(usage)
            ax.clear()
            ax.plot(data)
            ax.set_ylim(0, 100)
            ax.set_title("Live CPU Usage")
            ax.set_ylabel("Usage (%)")
        
        ani = animation.FuncAnimation(fig, animate, interval=1000)
        plt.tight_layout()
        plt.show()

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== System CPU Monitoring Prototype 💻🩺 ===")
    print("=========================================================")
    
    monitor = CPU_Monitor()
    
    # 1. Get system-wide and per-core usage
    print("\n--- System CPU Usage ---")
    print(f"Overall Usage: {monitor.get_system_cpu_usage()}%")
    print(f"Per-Core Usage: {monitor.get_system_cpu_usage(per_cpu=True)}%")
    
    # 2. Get usage for the current Python process
    print("\n--- Current Process CPU Usage ---")
    own_pid = os.getpid()
    print(f"Monitoring PID {own_pid} (this script)...")
    print(f"Usage: {monitor.get_process_cpu_usage(own_pid)}%")
    
    # 3. Get top 5 CPU-consuming processes
    print("\n--- Top 5 Processes by CPU Usage ---")
    top_procs = monitor.get_top_processes(count=5)
    for p in top_procs:
        print(f"  - PID: {p['pid']}, Name: {p['name']}, Usage: {p['cpu_usage']:.2f}%")
        
    # 4. Background monitoring and alerting demo
    print("\n--- Background Alerting Demo ---")
    def high_cpu_alert(usage: float):
        print(f"  [ALERT CALLBACK] High CPU detected: {usage}%!")
        
    # Using a low threshold for demonstration purposes
    monitor.start_monitoring(threshold=10.0, interval=2, callback=high_cpu_alert)
    print("Monitoring in background for 6 seconds...")
    time.sleep(6)
    monitor.stop_monitoring()
    
    print("\n--- Plotting Demo ---")
    print("The 'plot_live_usage' function will open a new window with a real-time graph.")
    print("Close the graph window to end the script.")
    print("Uncomment the line below to run it.")
    # try:
    #     monitor.plot_live_usage()
    # except Exception as e:
    #     logger.error(f"Plotting failed: {e}")

    print("\n=========================================================")
    print("=== CPU Monitoring Prototype Complete ===")
    print("=========================================================")
