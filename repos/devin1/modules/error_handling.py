"""
modules/error_handling.py
-------------------------
This module provides advanced error-handling utilities for the Devin project. It includes features for 
logging, monitoring, categorizing, and automatically resolving errors across all modules.
"""

import logging
import traceback
from datetime import datetime
from modules.notifications import send_error_notification


class ErrorHandler:
    """
    ErrorHandler provides tools for handling, logging, and resolving errors in the Devin project.
    """

    def __init__(self, log_file="error_logs.log"):
        self.log_file = log_file
        logging.basicConfig(
            filename=self.log_file,
            level=logging.ERROR,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    def log_error(self, error_message: str, exception_obj: Exception = None):
        """
        Logs an error message and optionally the associated exception details.

        Args:
            error_message (str): Description of the error.
            exception_obj (Exception, optional): Exception instance to log details from.
        """
        logging.error(error_message)
        if exception_obj:
            logging.error(traceback.format_exc())

    def send_notification(self, error_message: str):
        """
        Sends an error notification to the administrators.

        Args:
            error_message (str): Description of the error to send in the notification.
        """
        send_error_notification(error_message)

    def handle_exception(self, exception_obj: Exception, module_name: str):
        """
        Handles exceptions by logging details and sending notifications.

        Args:
            exception_obj (Exception): Exception instance to handle.
            module_name (str): Name of the module where the exception occurred.
        """
        error_message = (
            f"Exception occurred in module '{module_name}': {str(exception_obj)}"
        )
        self.log_error(error_message, exception_obj)
        self.send_notification(error_message)

    def retry_task(self, task_function, retries=3, *args, **kwargs):
        """
        Retries a task function a specified number of times upon failure.

        Args:
            task_function (callable): The function to retry.
            retries (int): Number of retry attempts.
            *args: Positional arguments for the task function.
            **kwargs: Keyword arguments for the task function.

        Returns:
            Any: Result of the successful task function execution.
        """
        for attempt in range(1, retries + 1):
            try:
                return task_function(*args, **kwargs)
            except Exception as e:
                self.log_error(
                    f"Attempt {attempt} failed for task {task_function.__name__}.", e
                )
                if attempt == retries:
                    self.handle_exception(e, task_function.__name__)
                    raise

    def monitor_system(self):
        """
        Monitors system health and logs anomalies or errors.
        """
        try:
            # Example health checks
            self.check_disk_space()
            self.check_memory_usage()
        except Exception as e:
            self.handle_exception(e, "System Monitoring")

    def check_disk_space(self):
        """
        Checks available disk space and logs warnings if below threshold.
        """
        # Example placeholder implementation
        free_space = 15  # Replace with actual disk space check
        if free_space < 20:
            raise Warning("Disk space critically low.")

    def check_memory_usage(self):
        """
        Checks memory usage and logs warnings if above threshold.
        """
        # Example placeholder implementation
        memory_usage = 85  # Replace with actual memory usage check
        if memory_usage > 80:
            raise Warning("Memory usage critically high.")


# Usage Example:
if __name__ == "__main__":
    error_handler = ErrorHandler()

    def example_task():
        raise ValueError("Example error for demonstration.")

    try:
        error_handler.retry_task(example_task)
    except Exception as e:
        print(f"Task failed: {str(e)}")
