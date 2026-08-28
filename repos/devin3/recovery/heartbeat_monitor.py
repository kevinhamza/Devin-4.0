# Devin/recovery/heartbeat_monitor.py
# Purpose: A "watchdog" system that monitors critical processes via a
#          heartbeat mechanism and automatically restarts them upon failure.

import logging
import psutil
import subprocess
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# Configure basic logging
logger = logging.getLogger("HeartbeatMonitor")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


@dataclass
class MonitoredProcess:
    """Holds the state for a single process being monitored."""
    name: str
    command: List[str]
    heartbeat_file: Path
    process: Optional[subprocess.Popen] = None
    last_heartbeat: float = 0.0


class HeartbeatManager:
    """A helper to be used by the application BEING monitored.
    It runs in a thread and periodically "touches" a file."""
    def __init__(self, heartbeat_file: Path, interval_sec: int = 5):
        self.heartbeat_file = heartbeat_file
        self.interval = interval_sec
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def _heartbeat_loop(self):
        while not self._stop_event.is_set():
            try:
                self.heartbeat_file.touch()
            except Exception as e:
                logger.error(f"HeartbeatManager failed to touch file {self.heartbeat_file}: {e}")
            time.sleep(self.interval)

    def start(self):
        logger.info(f"HeartbeatManager started. Touching {self.heartbeat_file} every {self.interval}s.")
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()


class HeartbeatMonitor:
    """The main watchdog class that monitors and restarts processes."""
    def __init__(self, check_interval_sec: int = 10, stale_threshold_sec: int = 30):
        self.check_interval = check_interval_sec
        self.stale_threshold = stale_threshold_sec
        self.monitored_processes: Dict[str, MonitoredProcess] = {}
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def register_process(self, name: str, command: List[str], heartbeat_file: Path):
        """Adds a new process to the watchlist."""
        if name in self.monitored_processes:
            logger.warning(f"Process '{name}' is already being monitored.")
            return
        logger.info(f"Registering process '{name}' for monitoring.")
        self.monitored_processes[name] = MonitoredProcess(
            name=name, command=command, heartbeat_file=heartbeat_file
        )

    def _recover_process(self, proc: MonitoredProcess):
        """Handles the recovery of a failed process."""
        logger.critical(f"RECOVERY: Process '{proc.name}' declared dead. Attempting restart.")
        
        # Terminate any lingering zombie process
        if proc.process and psutil.pid_exists(proc.process.pid):
            logger.warning(f"Terminating old process with PID {proc.process.pid}...")
            p = psutil.Process(proc.process.pid)
            p.terminate()
            try:
                p.wait(timeout=3)
            except psutil.TimeoutExpired:
                p.kill()

        logger.warning(f"Restarting process with command: {' '.join(proc.command)}")
        new_process = subprocess.Popen(proc.command)
        proc.process = new_process
        logger.warning(f"Process '{proc.name}' restarted successfully with new PID {new_process.pid}.")

    def _monitor_loop(self):
        """The main loop that checks the health of all registered processes."""
        while not self._stop_event.is_set():
            time.sleep(self.check_interval)
            now = time.time()
            for name, proc in self.monitored_processes.items():
                if not proc.heartbeat_file.exists():
                    logger.warning(f"Heartbeat file for '{name}' does not exist. Process may not have started correctly.")
                    if proc.process and proc.process.poll() is not None: # Check if process exited
                        self._recover_process(proc)
                    continue

                last_modified = proc.heartbeat_file.stat().st_mtime
                if (now - last_modified) > self.stale_threshold:
                    self._recover_process(proc)

    def start(self):
        """Starts the monitoring service in a background thread."""
        logger.warning("HeartbeatMonitor service starting.")
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the monitoring service."""
        logger.warning("HeartbeatMonitor service stopping.")
        self._stop_event.set()
        if self._thread:
            self._thread.join()

# --- Example Usage ---
# We define the worker process logic here so it can be called by subprocess
def critical_worker_process():
    """A dummy process that sends heartbeats and then simulates a crash."""
    heartbeat_file = Path("worker.heartbeat")
    manager = HeartbeatManager(heartbeat_file, interval_sec=2)
    manager.start()
    
    print(f"(Worker {os.getpid()}) Process started. I will work for 15 seconds then crash.")
    time.sleep(15)
    print(f"(Worker {os.getpid()}) Crashing now!")
    # The process exits, stopping the heartbeat updates.
    
if __name__ == "__main__":
    print("=========================================================")
    print("=== Heartbeat Monitor & Auto-Restart Prototype ❤️‍🩹🔄 ===")
    print("=========================================================")
    
    # --- 1. Define the critical process to run ---
    # We need to run the worker function in a separate python process
    command_to_run = [sys.executable, "-c", "from heartbeat_monitor import critical_worker_process; critical_worker_process()"]
    heartbeat_file = Path("worker.heartbeat")
    
    # Clean up old heartbeat file if it exists
    if heartbeat_file.exists(): heartbeat_file.unlink()
    
    monitor = HeartbeatMonitor(check_interval_sec=5, stale_threshold_sec=10)
    
    try:
        # --- 2. Start the critical process for the first time ---
        print(f"\n--- Starting the critical worker process ---")
        worker_process = subprocess.Popen(command_to_run)
        print(f"Worker started with PID: {worker_process.pid}")
        
        # --- 3. Register it with the monitor and start monitoring ---
        monitor.register_process(name="CriticalWorker-1", command=command_to_run, heartbeat_file=heartbeat_file)
        monitor.monitored_processes["CriticalWorker-1"].process = worker_process
        monitor.start()
        
        # --- 4. Wait for the cycle of crash and recovery ---
        print("\nMonitor is now active. The worker will crash in ~15s.")
        print("The monitor should detect the stale heartbeat and restart it within 10s after that.")
        # Wait long enough for a full cycle to occur
        time.sleep(35)

    finally:
        # --- 5. Clean up ---
        monitor.stop()
        # Find and terminate any remaining worker processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['cmdline'] and "critical_worker_process" in ' '.join(proc.info['cmdline']):
                print(f"Terminating leftover worker process {proc.pid}...")
                proc.kill()
        if heartbeat_file.exists(): heartbeat_file.unlink()

    print("\n=========================================================")
    print("=== Heartbeat Monitor Prototype Complete ===")
    print("=========================================================")
