"""
automation_module.py
Automates user workflows and routines for the Devin project.
"""

import os
import time
import logging
from threading import Thread
from modules.utils.scheduler import TaskScheduler
from modules.utils.system_tools import SystemCommands, FileManager

# Configuration
class AutomationConfig:
    def __init__(self, enable_notifications=True, retry_attempts=3, retry_delay=5):
        self.enable_notifications = enable_notifications
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

# Automation Module
class AutomationModule:
    def __init__(self, config: AutomationConfig):
        self.scheduler = TaskScheduler()
        self.system_tools = SystemCommands()
        self.file_manager = FileManager()
        self.config = config

    def add_scheduled_task(self, task_name: str, task_function, schedule_time: str):
        """
        Adds a task to the scheduler.
        """
        try:
            logging.info(f"Scheduling task '{task_name}' at {schedule_time}.")
            self.scheduler.schedule_task(task_name, task_function, schedule_time)
        except Exception as e:
            logging.error(f"Failed to schedule task '{task_name}': {e}")

    def execute_task(self, task_function, *args, **kwargs):
        """
        Executes a task and handles retries if needed.
        """
        attempt = 0
        while attempt < self.config.retry_attempts:
            try:
                logging.info(f"Executing task (attempt {attempt + 1}).")
                task_function(*args, **kwargs)
                logging.info("Task executed successfully.")
                return True
            except Exception as e:
                logging.warning(f"Task execution failed: {e}. Retrying in {self.config.retry_delay} seconds...")
                time.sleep(self.config.retry_delay)
                attempt += 1
        logging.error("Task execution failed after maximum retry attempts.")
        return False

    def automate_backup(self, source_path: str, backup_path: str):
        """
        Automates file backups.
        """
        try:
            logging.info(f"Backing up files from {source_path} to {backup_path}.")
            self.file_manager.copy_files(source_path, backup_path)
            if self.config.enable_notifications:
                logging.info("Backup completed successfully. Notification sent.")
        except Exception as e:
            logging.error(f"Backup automation failed: {e}")

    def automate_script_execution(self, script_path: str, parameters: list = []):
        """
        Automates execution of scripts.
        """
        try:
            logging.info(f"Executing script at {script_path} with parameters {parameters}.")
            result = self.system_tools.run_script(script_path, parameters)
            logging.info(f"Script executed. Output: {result}")
        except Exception as e:
            logging.error(f"Script automation failed: {e}")

    def automate_cleanup(self, target_path: str, file_extension: str = "*"):
        """
        Automates cleanup of files in a directory.
        """
        try:
            logging.info(f"Cleaning up files in {target_path} with extension {file_extension}.")
            self.file_manager.delete_files(target_path, file_extension)
            logging.info("Cleanup completed successfully.")
        except Exception as e:
            logging.error(f"Cleanup automation failed: {e}")

# Example usage
if __name__ == "__main__":
    config = AutomationConfig(enable_notifications=True)
    automation = AutomationModule(config)

    def example_task():
        logging.info("Example task is running...")

    automation.add_scheduled_task("example_task", example_task, "14:00")
    automation.automate_backup("/path/to/source", "/path/to/backup")
    automation.automate_script_execution("/path/to/script.sh", ["--flag", "value"])
    automation.automate_cleanup("/path/to/cleanup", "*.tmp")
