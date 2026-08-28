import logging
import os
from datetime import datetime


class ErrorLogger:
    """
    A class to handle error logging and monitoring for the project.
    """

    def __init__(self, log_directory="logs"):
        """
        Initialize the error logger with logging capabilities.

        :param log_directory: Directory to store log files.
        """
        self.log_directory = log_directory
        os.makedirs(log_directory, exist_ok=True)

        log_file = os.path.join(log_directory, f"errors_{datetime.now().strftime('%Y-%m-%d')}.log")
        logging.basicConfig(
            filename=log_file,
            filemode='a',
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.ERROR
        )

    def log_error(self, context, error_message):
        """
        Log an error with context.

        :param context: Additional context about where the error occurred.
        :param error_message: The error message to log.
        """
        if context:
            logging.error(f"Context: {context} | Error: {error_message}")
        else:
            logging.error(f"Error: {error_message}")

    def handle_exception(self, exception, context="An error occurred"):
        """
        Handle an exception by logging it and returning a user-friendly message.

        :param exception: The exception to handle.
        :param context: Additional context about the error.
        :return: A user-friendly error message.
        """
        error_message = f"{context}. Exception: {exception}"
        self.log_error(context, str(exception))
        return error_message

    def validate_inputs(self, **kwargs):
        """
        Validate inputs and ensure they are not empty or None.

        :param kwargs: Key-value pairs of inputs to validate.
        :raises ValueError: If validation fails.
        """
        for key, value in kwargs.items():
            if value is None or value == "":
                error_message = f"Validation failed: Missing value for '{key}'."
                self.log_error("[Validation]", error_message)
                raise ValueError(error_message)

    def monitor_performance(self, task_name, start_time, end_time):
        """
        Monitor performance and log tasks taking longer than expected.

        :param task_name: Name of the task being monitored.
        :param start_time: Start time of the task (datetime object).
        :param end_time: End time of the task (datetime object).
        """
        duration = (end_time - start_time).total_seconds()
        if duration > 5:  # Example threshold (5 seconds)
            warning_message = f"Task '{task_name}' took {duration:.2f} seconds, exceeding the threshold."
            logging.warning(warning_message)

    def alert_critical_error(self, error_message):
        """
        Alert critical errors to administrators or users.

        :param error_message: The critical error message to alert.
        """
        # Placeholder for real alert system (email, SMS, etc.)
        logging.critical(f"CRITICAL ALERT: {error_message}")
        print(f"CRITICAL ALERT: {error_message}")


if __name__ == "__main__":
    # Example usage for testing
    logger = ErrorLogger()

    try:
        logger.validate_inputs(username="admin", password=None)
    except Exception as e:
        user_message = logger.handle_exception(e, "Input validation failed")
        print(user_message)
