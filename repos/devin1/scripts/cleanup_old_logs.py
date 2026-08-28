"""
scripts/cleanup_old_logs.py
Automates log maintenance by deleting old log files based on retention policy.
"""

import os
import time
from datetime import datetime, timedelta

# Configuration
LOG_DIRECTORIES = ["logs/access", "logs/error"]  # Directories containing log files
RETENTION_DAYS = 30  # Number of days to retain logs
LOG_EXTENSION = ".log"  # File extension for log files
VERBOSE = True  # Enable detailed output


def log_message(message):
    """
    Print and log a message if verbose mode is enabled.
    """
    if VERBOSE:
        print(message)


def delete_old_logs():
    """
    Deletes log files older than the retention policy from specified directories.
    """
    retention_time = time.time() - (RETENTION_DAYS * 86400)  # Convert days to seconds

    log_message(f"Starting log cleanup process...")
    log_message(f"Retention policy: {RETENTION_DAYS} days")

    for directory in LOG_DIRECTORIES:
        log_message(f"Processing directory: {directory}")

        if not os.path.exists(directory):
            log_message(f"Directory does not exist: {directory}")
            continue

        for filename in os.listdir(directory):
            if not filename.endswith(LOG_EXTENSION):
                continue

            file_path = os.path.join(directory, filename)
            file_mod_time = os.path.getmtime(file_path)

            if file_mod_time < retention_time:
                try:
                    os.remove(file_path)
                    log_message(f"Deleted old log file: {file_path}")
                except Exception as e:
                    log_message(f"Error deleting file {file_path}: {e}")
            else:
                log_message(f"Retained log file: {file_path}")

    log_message("Log cleanup process completed.")


if __name__ == "__main__":
    start_time = datetime.now()
    log_message(f"Log cleanup started at {start_time}")

    delete_old_logs()

    end_time = datetime.now()
    log_message(f"Log cleanup finished at {end_time}")
    log_message(f"Total time taken: {end_time - start_time}")
