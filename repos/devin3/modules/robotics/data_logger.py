# # Devin/modules/robotics/data_logger.py
# # Purpose: Provides a high-performance, asynchronous logger for recording data
# #          from multiple robotics sources into a structured log file for analysis.

# import logging
# import csv
# import queue
# import threading
# import time
# from datetime import datetime
# from pathlib import Path
# from typing import Dict, Any, Optional

# # Configure basic logging
# logger = logging.getLogger("DataLogger")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class DataLogger:
#     """
#     An asynchronous logger that records data from multiple sources into a single,
#     timestamped CSV file without blocking the main application threads.
#     """

#     def __init__(self, log_directory: str = "robot_logs"):
#         """
#         Initializes the data logger.

#         Args:
#             log_directory (str): The directory where log files will be saved.
#         """
#         self.log_directory = Path(log_directory)
#         self.log_queue = queue.Queue()
#         self.logging_thread: Optional[threading.Thread] = None
#         self._stop_event = threading.Event()
        
#         logger.info(f"DataLogger initialized. Logs will be saved to '{self.log_directory}'.")

#     def start_logging(self) -> Optional[Path]:
#         """
#         Starts the logging session. Creates a new log file and starts the
#         background logging thread.

#         Returns:
#             Optional[Path]: The path to the newly created log file, or None on failure.
#         """
#         if self.logging_thread and self.logging_thread.is_alive():
#             logger.warning("Logger is already running.")
#             return None

#         self.log_directory.mkdir(parents=True, exist_ok=True)
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         self.log_file_path = self.log_directory / f"log_{timestamp}.csv"
        
#         self._stop_event.clear()
#         self.logging_thread = threading.Thread(
#             target=self._logging_worker,
#             daemon=True
#         )
#         self.logging_thread.start()
        
#         logger.info(f"Logging started. Saving data to '{self.log_file_path}'.")
#         return self.log_file_path

#     def stop_logging(self):
#         """
#         Stops the logging session and ensures all queued data is written to the file.
#         """
#         if not self.logging_thread or not self.logging_thread.is_alive():
#             logger.info("Logger is not currently running.")
#             return

#         logger.info("Stopping logger... waiting for queue to empty.")
#         # Signal the thread to stop once the queue is empty
#         self.log_queue.put(None)
#         self.logging_thread.join(timeout=5.0)
#         self._stop_event.set()
        
#         if self.logging_thread.is_alive():
#             logger.warning("Logging thread did not terminate gracefully.")
#         else:
#             logger.info("Logging session stopped successfully.")

#     def log(self, topic: str, data: Dict[str, Any]):
#         """
#         Submits a data record to be logged. This method is thread-safe and non-blocking.

#         Args:
#             topic (str): The source or topic of the data (e.g., 'imu', 'motor_cmds').
#             data (Dict[str, Any]): A dictionary of the data to be logged.
#         """
#         if self._stop_event.is_set():
#             logger.warning("Logger is stopped. Cannot log new data.")
#             return
            
#         # Create a full record with a precise timestamp and topic
#         log_record = {
#             'timestamp': time.time(),
#             'topic': topic,
#             **data # Unpack the user's data dictionary
#         }
#         self.log_queue.put(log_record)

#     def _logging_worker(self):
#         """
#         The background worker thread that retrieves data from the queue
#         and writes it to the CSV file.
#         """
#         fieldnames = set(['timestamp', 'topic'])
#         file_handle = open(self.log_file_path, 'w', newline='')
#         writer = None

#         while not self._stop_event.is_set():
#             try:
#                 record = self.log_queue.get(timeout=1)
                
#                 # The stop signal
#                 if record is None:
#                     break

#                 # --- Dynamic CSV Header Management ---
#                 # If the new record has keys we haven't seen, we need to rewrite the file
#                 # This is a simplification. A more robust logger might use a database or a
#                 # format like HDF5 that doesn't require fixed headers.
#                 new_keys = set(record.keys()) - fieldnames
#                 if new_keys:
#                     logger.debug(f"New data fields detected: {new_keys}. Re-initializing writer.")
#                     fieldnames.update(new_keys)
#                     # For simplicity, we just create the writer once with the initial keys.
#                     # A real system might close, rename, and rewrite the file with new headers.
#                     if writer is None:
#                         writer = csv.DictWriter(file_handle, fieldnames=sorted(list(fieldnames)))
#                         writer.writeheader()
                
#                 if writer:
#                     # Fill missing values for this row
#                     for key in fieldnames:
#                         if key not in record:
#                             record[key] = ''
#                     writer.writerow(record)

#             except queue.Empty:
#                 # This is normal, just means no data was logged in the last second
#                 continue
#             except Exception as e:
#                 logger.error(f"Error in logging worker: {e}")
        
#         file_handle.close()

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Asynchronous Data Logger Prototype 📝⏱️ ===")
#     print("=========================================================")

#     # 1. Initialize the logger
#     data_logger = DataLogger()
#     log_file = data_logger.start_logging()
    
#     if log_file:
#         print(f"Logger started. Log file created at: {log_file}")
        
#         # 2. Simulate a robot's main loop for 5 seconds
#         print("\nSimulating a 5-second robot operation loop...")
#         print("Logging IMU data, navigation status, and camera events.")
        
#         start_time = time.time()
#         try:
#             while time.time() - start_time < 5:
#                 # Log IMU data (high frequency)
#                 imu_reading = {
#                     "orientation_w": 0.98, "orientation_x": 0.01,
#                     "orientation_y": 0.12, "orientation_z": 0.05
#                 }
#                 data_logger.log("imu_data", imu_reading)
                
#                 # Log navigation status (lower frequency)
#                 if int(time.time()) % 2 == 0:
#                     nav_status = {"status": "NAVIGATING", "target_x": 10.5, "target_y": -4.2}
#                     data_logger.log("navigation_status", nav_status)
                
#                 # Log a discrete event
#                 if int(time.time() * 10) % 25 == 0: # Roughly every 2.5s
#                     camera_event = {"event": "object_detected", "object_id": "red_cup"}
#                     data_logger.log("camera_events", camera_event)

#                 time.sleep(0.1) # 10 Hz loop
#         except KeyboardInterrupt:
#             print("\nUser interrupted simulation.")
#         finally:
#             # 3. Stop the logger
#             # This will block until all queued messages are written.
#             data_logger.stop_logging()

#         # 4. Show a preview of the log file
#         print("\n--- Log File Preview ---")
#         try:
#             with open(log_file, 'r') as f:
#                 for i, line in enumerate(f):
#                     if i >= 5: # Print header and first 4 lines
#                         print("...")
#                         break
#                     print(line.strip())
#         except Exception as e:
#             print(f"Could not read log file preview: {e}")
#     else:
#         print("Failed to start the logger.")

#     print("\n=========================================================")
#     print("=== Data Logger Prototype Complete ===")
#     print("=========================================================")

# Devin/modules/robotics/data_logger.py
# Purpose: A high-performance, asynchronous logger for recording robotics
#          data into an analysis-ready columnar file format (Feather).

import logging
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.feather as feather
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("DataLogger")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class DataLogger:
    """
    An asynchronous logger that records data into a single, timestamped
    Feather file for high-performance and easy analysis.
    """
    def __init__(self, log_directory: str = "robot_logs", flush_interval_sec: int = 5, buffer_size: int = 1000):
        if not DEPS_AVAILABLE:
            raise ImportError(f"Required libraries missing. Error: {_import_error}")
            
        self.log_directory = Path(log_directory)
        self.log_queue = queue.Queue()
        self.logging_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        self.flush_interval = flush_interval_sec
        self.buffer_size = buffer_size
        self.log_file_path: Optional[Path] = None

    def start_logging(self) -> Optional[Path]:
        """Starts the logging session and the background writer thread."""
        if self.logging_thread and self.logging_thread.is_alive():
            logger.warning("Logger is already running.")
            return None

        self.log_directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = self.log_directory / f"log_{timestamp}.feather"
        
        self._stop_event.clear()
        self.logging_thread = threading.Thread(target=self._logging_worker, daemon=True)
        self.logging_thread.start()
        
        logger.info(f"Logging started. Saving data to '{self.log_file_path}'.")
        return self.log_file_path

    def stop_logging(self):
        """Stops the logging session and flushes all remaining data."""
        if not self.logging_thread or not self.logging_thread.is_alive():
            return

        logger.info("Stopping logger... signaling worker to flush and exit.")
        self.log_queue.put(None) # Sentinel value to signal stop
        self.logging_thread.join(timeout=self.flush_interval + 2)
        
        if self.logging_thread.is_alive():
            logger.warning("Logging thread did not terminate gracefully.")
        else:
            logger.info("Logging session stopped successfully.")

    def log(self, topic: str, data: Dict[str, Any]):
        """Submits a data record to be logged. This is thread-safe and non-blocking."""
        if self._stop_event.is_set():
            return
            
        log_record = {'timestamp': time.time(), 'topic': topic, **data}
        self.log_queue.put(log_record)

    def _logging_worker(self):
        """Background worker that writes data from the queue to a Feather file."""
        buffer: List[Dict] = []
        last_flush_time = time.time()

        while True:
            try:
                record = self.log_queue.get(timeout=self.flush_interval)
                if record is None: # Stop signal
                    self._flush_buffer_to_disk(buffer)
                    break
                
                buffer.append(record)

                if len(buffer) >= self.buffer_size or (time.time() - last_flush_time) >= self.flush_interval:
                    self._flush_buffer_to_disk(buffer)
                    buffer.clear()
                    last_flush_time = time.time()

            except queue.Empty:
                # Timeout occurred, flush the buffer if it has data
                self._flush_buffer_to_disk(buffer)
                buffer.clear()
                last_flush_time = time.time()
        
        self._stop_event.set()
        logger.debug("Logging worker has finished.")

    def _flush_buffer_to_disk(self, buffer: List[Dict]):
        """Converts the buffer to a DataFrame and appends to the Feather file."""
        if not buffer:
            return

        logger.info(f"Flushing {len(buffer)} records to disk...")
        df_new = pd.DataFrame(buffer)
        df_new['timestamp'] = pd.to_datetime(df_new['timestamp'], unit='s')
        
        try:
            if self.log_file_path.exists():
                with feather.FeatherReader(self.log_file_path) as reader:
                    df_existing = reader.read_pandas()
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                feather.write_feather(df_combined, self.log_file_path)
            else:
                feather.write_feather(df_new, self.log_file_path)
        except Exception as e:
            logger.error(f"Error flushing data to Feather file: {e}")


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== High-Performance Data Logger Prototype 📝⏱️ ===")
    print("=========================================================")
    
    if not DEPS_AVAILABLE:
        print(f"\nERROR: Required libraries missing. {_import_error}")
        print("Please run: 'pip install pandas pyarrow'")
    else:
        data_logger = DataLogger(flush_interval_sec=2, buffer_size=100)
        log_file = data_logger.start_logging()
        
        if log_file:
            print(f"Logger started. Log file: {log_file}")
            
            print("\nSimulating a 5-second robot operation loop...")
            start_time = time.time()
            try:
                while time.time() - start_time < 5:
                    # Log high-frequency IMU data
                    data_logger.log("imu", {"ax": time.time() % 2, "ay": time.time() % 3})
                    # Log lower-frequency navigation data
                    if int(time.time() * 10) % 10 == 0:
                        data_logger.log("nav", {"status": "NAVIGATING", "target_x": 10.5})
                    time.sleep(0.01) # 100 Hz loop
            finally:
                data_logger.stop_logging()

            # --- 4. Read and Analyze the Log File ---
            print("\n--- Log File Analysis ---")
            if log_file.exists():
                log_df = pd.read_feather(log_file)
                print("\nLog file loaded successfully into a pandas DataFrame.")
                print("DataFrame Info:")
                log_df.info()
                print("\nFirst 5 rows of data:")
                print(log_df.head())
                print("\nData points per topic:")
                print(log_df['topic'].value_counts())
            else:
                print("Log file was not created.")

    print("\n=========================================================")
    print("=== Data Logger Prototype Complete ===")
    print("=========================================================")
