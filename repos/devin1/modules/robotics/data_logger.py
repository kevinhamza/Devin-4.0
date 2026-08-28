"""
Data Logger Module
==================
Handles data logging for the robotics system, including sensor data, operational metrics,
and error reports. Supports real-time logging and data export for analysis.
"""

import os
import csv
import json
import logging
from datetime import datetime


class DataLogger:
    """
    Logs data to files and provides data export capabilities.
    """

    def __init__(self, log_dir="logs/robotics", log_format="csv"):
        """
        Initializes the Data Logger.

        Args:
            log_dir (str): Directory to save log files.
            log_format (str): Format of the logs ("csv" or "json").
        """
        self.log_dir = log_dir
        self.log_format = log_format.lower()
        self.current_log_file = None
        self.logs = []

        os.makedirs(self.log_dir, exist_ok=True)
        logging.info(f"[DATA LOGGER] Log directory set to {self.log_dir}")

    def start_new_log(self, session_name=None):
        """
        Starts a new log file for the current session.

        Args:
            session_name (str): Optional custom name for the log session.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = session_name or f"session_{timestamp}"
        self.current_log_file = os.path.join(self.log_dir, f"{session_name}.{self.log_format}")
        self.logs = []
        logging.info(f"[DATA LOGGER] New log session started: {self.current_log_file}")

    def log_data(self, **data):
        """
        Logs a new data entry.

        Args:
            **data: Data fields to log as key-value pairs.
        """
        data["timestamp"] = datetime.now().isoformat()
        self.logs.append(data)
        logging.info(f"[DATA LOGGER] Logged data: {data}")

    def save_logs(self):
        """
        Saves all logged data to the log file in the specified format.
        """
        if not self.current_log_file:
            logging.error("[DATA LOGGER] No log session active. Call `start_new_log` first.")
            return

        try:
            if self.log_format == "csv":
                self._save_as_csv()
            elif self.log_format == "json":
                self._save_as_json()
            else:
                logging.error(f"[DATA LOGGER] Unsupported log format: {self.log_format}")
        except Exception as e:
            logging.error(f"[DATA LOGGER] Error saving logs: {e}")

    def _save_as_csv(self):
        """
        Saves logs in CSV format.
        """
        if not self.logs:
            logging.warning("[DATA LOGGER] No logs to save.")
            return

        with open(self.current_log_file, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=self.logs[0].keys())
            writer.writeheader()
            writer.writerows(self.logs)
        logging.info(f"[DATA LOGGER] Logs saved to {self.current_log_file}")

    def _save_as_json(self):
        """
        Saves logs in JSON format.
        """
        if not self.logs:
            logging.warning("[DATA LOGGER] No logs to save.")
            return

        with open(self.current_log_file, mode="w") as file:
            json.dump(self.logs, file, indent=4)
        logging.info(f"[DATA LOGGER] Logs saved to {self.current_log_file}")

    def load_logs(self, log_file):
        """
        Loads logs from an existing log file.

        Args:
            log_file (str): Path to the log file to load.

        Returns:
            list: List of logged data entries.
        """
        try:
            if log_file.endswith(".csv"):
                return self._load_from_csv(log_file)
            elif log_file.endswith(".json"):
                return self._load_from_json(log_file)
            else:
                logging.error(f"[DATA LOGGER] Unsupported log file format: {log_file}")
                return []
        except Exception as e:
            logging.error(f"[DATA LOGGER] Error loading logs: {e}")
            return []

    def _load_from_csv(self, log_file):
        """
        Loads logs from a CSV file.

        Args:
            log_file (str): Path to the CSV log file.

        Returns:
            list: List of logged data entries.
        """
        with open(log_file, mode="r") as file:
            reader = csv.DictReader(file)
            return [row for row in reader]

    def _load_from_json(self, log_file):
        """
        Loads logs from a JSON file.

        Args:
            log_file (str): Path to the JSON log file.

        Returns:
            list: List of logged data entries.
        """
        with open(log_file, mode="r") as file:
            return json.load(file)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    logger = DataLogger(log_format="csv")
    logger.start_new_log(session_name="test_session")

    # Simulate logging sensor data
    logger.log_data(sensor="LIDAR", value=23.4)
    logger.log_data(sensor="Camera", value="Active")
    logger.log_data(sensor="Temperature", value=35.2)

    # Save logs to file
    logger.save_logs()

    # Load logs for analysis
    loaded_logs = logger.load_logs(logger.current_log_file)
    logging.info(f"[DATA LOGGER] Loaded logs: {loaded_logs}")
