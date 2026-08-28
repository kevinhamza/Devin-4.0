import logging
import os
from datetime import datetime


class LogManager:
    """
    A utility class for managing application logs.
    Provides centralized logging with options for custom formats, levels, and output destinations.
    """

    def __init__(self, log_dir="logs", log_level=logging.INFO):
        self.log_dir = log_dir
        self.log_level = log_level
        self.logger = logging.getLogger("AIA_LogManager")
        self.logger.setLevel(self.log_level)
        self._ensure_log_directory()
        self._configure_logging()

    def _ensure_log_directory(self):
        """Ensure the log directory exists."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            print(f"Log directory created at: {self.log_dir}")

    def _configure_logging(self):
        """Configure logging handlers and formatters."""
        log_file = os.path.join(self.log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_file)
        console_handler = logging.StreamHandler()

        # Define a detailed log format
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(module)s.%(funcName)s] %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        print(f"Logging configured. Log file: {log_file}")

    def log_info(self, message):
        """Log an informational message."""
        self.logger.info(message)

    def log_warning(self, message):
        """Log a warning message."""
        self.logger.warning(message)

    def log_error(self, message, exc_info=True):
        """Log an error message with optional exception info."""
        self.logger.error(message, exc_info=exc_info)

    def log_critical(self, message, exc_info=True):
        """Log a critical error message with optional exception info."""
        self.logger.critical(message, exc_info=exc_info)

    def log_debug(self, message):
        """Log a debug-level message."""
        self.logger.debug(message)


# Example usage
if __name__ == "__main__":
    log_manager = LogManager()

    log_manager.log_info("Application started successfully.")
    log_manager.log_warning("This is a warning message.")
    try:
        1 / 0
    except ZeroDivisionError as e:
        log_manager.log_error("A division by zero error occurred.", exc_info=True)
    log_manager.log_debug("Debug information: Variable values, etc.")
    log_manager.log_critical("Critical system failure! Immediate action required.")
