# Devin/modules/data_logger.py
# Purpose: A high-performance, asynchronous, structured data logger that
#          writes events to efficient binary files (Apache Feather format).

import logging
import threading
import time
from queue import Queue, Empty
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

try:
    import pandas as pd
    import pyarrow # Required for feather
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("DataLogger")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

class DataLogger:
    """
    An asynchronous logger for structured data, using a producer-consumer model.
    """
    def __init__(self, log_directory: str = "robot_logs", flush_interval: int = 5):
        if not PANDAS_AVAILABLE:
            raise ImportError("The 'pandas' and 'pyarrow' libraries are required for DataLogger. Please run 'pip install pandas pyarrow'.")
        
        self.log_dir = Path(log_directory)
        self.log_dir.mkdir(exist_ok=True)
        self.flush_interval = flush_interval
        
        self.log_queue: Queue = Queue()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        
        logger.info(f"DataLogger initialized. Logs will be written to '{self.log_dir.resolve()}'.")

    def _worker(self):
        """The consumer thread that periodically drains the queue and writes to disk."""
        while not self._stop_event.is_set():
            time.sleep(self.flush_interval)
            self._flush_queue()
        
        # Perform one final flush after the stop event is set to clear the queue
        logger.info("Shutdown signal received. Performing final flush...")
        self._flush_queue()

    def _flush_queue(self):
        """Drains the queue and writes all pending logs to their respective files."""
        if self.log_queue.empty():
            return
            
        logs_by_topic: Dict[str, List[Dict]] = defaultdict(list)
        
        # Drain the queue
        while True:
            try:
                topic, data = self.log_queue.get_nowait()
                logs_by_topic[topic].append(data)
            except Empty:
                break
        
        logger.info(f"Flushing {sum(len(v) for v in logs_by_topic.values())} log entries across {len(logs_by_topic)} topics...")
        
        for topic, records in logs_by_topic.items():
            file_path = self.log_dir / f"{topic}.feather"
            new_df = pd.DataFrame(records)
            
            try:
                if file_path.exists():
                    existing_df = pd.read_feather(file_path)
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                else:
                    combined_df = new_df
                
                # Write the combined data back to the file
                combined_df.to_feather(file_path)
            except Exception as e:
                logger.error(f"Failed to write logs for topic '{topic}' to file '{file_path}': {e}")

    def start_logging(self):
        """Starts the background logging thread."""
        if self._worker_thread.is_alive():
            logger.warning("Logger is already running.")
            return
        logger.info("Starting background data logger thread...")
        self._worker_thread.start()

    def stop_logging(self):
        """Stops the background logging thread gracefully."""
        if not self._worker_thread.is_alive():
            logger.info("Logger is not running.")
            return
        logger.info("Stopping background data logger thread...")
        self._stop_event.set()
        self._worker_thread.join() # Wait for the thread to finish
        logger.info("Data logger stopped.")

    def log(self, topic: str, data: Dict[str, Any]):
        """
        Public method to add a structured log entry to the queue.
        This method is fast and non-blocking.
        """
        if not isinstance(data, dict):
            logger.warning("Log data must be a dictionary. Discarding log.")
            return
            
        # Add a precise timestamp to every record
        data["timestamp"] = time.time()
        self.log_queue.put((topic, data))

# --- Example Usage ---
if __name__ == "__main__":
    import random
    print("=========================================================")
    print("=== High-Performance Data Logger Demo 🚀📊 ===")
    print("=========================================================")
    
    if not PANDAS_AVAILABLE:
        print("ERROR: This demo requires pandas and pyarrow. Run 'pip install pandas pyarrow'")
    else:
        # 1. Initialize and start the logger (with a short flush interval for the demo)
        data_logger = DataLogger(flush_interval=2)
        data_logger.start_logging()
        
        # 2. Log a high volume of data very quickly
        print("Logging a burst of 1000 events... (This will be non-blocking)")
        log_start_time = time.time()
        for i in range(500):
            data_logger.log("cpu_telemetry", {"core_1_temp": random.uniform(40, 90), "core_2_load": random.random()})
            data_logger.log("network_events", {"packets_tx": random.randint(100, 1000), "packets_rx": random.randint(500, 5000)})
        log_end_time = time.time()
        print(f"Finished logging 1000 events in {log_end_time - log_start_time:.4f} seconds.")
        
        # 3. Wait for the background thread to flush the data
        print("Waiting for the background worker to flush logs to disk...")
        time.sleep(3)
        
        # 4. Stop the logger (this will also trigger a final flush)
        data_logger.stop_logging()
        
        # 5. Verify the output files
        print("\n--- Verifying Logged Data ---")
        cpu_log_path = Path("robot_logs/cpu_telemetry.feather")
        net_log_path = Path("robot_logs/network_events.feather")
        
        if cpu_log_path.exists():
            cpu_df = pd.read_feather(cpu_log_path)
            print(f"Successfully read '{cpu_log_path}'. Shape: {cpu_df.shape}")
            print("Head of CPU Telemetry Log:")
            print(cpu_df.head())
        else:
            print(f"ERROR: CPU log file '{cpu_log_path}' was not created.")

        if net_log_path.exists():
            net_df = pd.read_feather(net_log_path)
            print(f"\nSuccessfully read '{net_log_path}'. Shape: {net_df.shape}")
            print("Head of Network Events Log:")
            print(net_df.head())
        else:
            print(f"ERROR: Network log file '{net_log_path}' was not created.")
            
        # Clean up
        cpu_log_path.unlink(missing_ok=True)
        net_log_path.unlink(missing_ok=True)


    print("\n=========================================================")
    print("=== Data Logger Demo Complete ===")
    print("=========================================================")
