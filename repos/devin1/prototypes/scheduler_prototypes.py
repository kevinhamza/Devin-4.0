"""
Scheduler Prototypes
====================
This file contains experimental prototypes for scheduling functionalities.
It includes task automation, calendar integration, real-time scheduling, notifications,
and AI-based task optimization.
"""

import schedule
import time
from datetime import datetime, timedelta
import threading

class Scheduler:
    def __init__(self):
        """
        Initializes the Scheduler with empty task lists and settings for optimization.
        """
        self.jobs = []
        self.default_interval = 1  # Default interval in seconds for checking tasks
        self.logs = []
    
    def add_task(self, task_name, task_function, run_at=None, interval=None, every=None, unit="seconds"):
        """
        Adds a task to the scheduler.
        
        :param task_name: Name of the task.
        :param task_function: Callable function for the task.
        :param run_at: Optional datetime for the first run.
        :param interval: Interval between task runs.
        :param every: Frequency of the task, e.g., "daily", "hourly".
        :param unit: Unit for the interval, e.g., "seconds", "minutes".
        """
        job = {
            "task_name": task_name,
            "task_function": task_function,
            "run_at": run_at,
            "interval": interval,
            "every": every,
            "unit": unit
        }
        self.jobs.append(job)
        self.log(f"Task '{task_name}' added to scheduler.")
    
    def start_scheduler(self):
        """
        Starts the scheduler loop in a separate thread.
        """
        threading.Thread(target=self._run_scheduler, daemon=True).start()
        self.log("Scheduler started.")
    
    def _run_scheduler(self):
        """
        Private method to run the scheduler.
        """
        while True:
            current_time = datetime.now()
            for job in self.jobs:
                if job["run_at"] and current_time >= job["run_at"]:
                    self.execute_task(job)
                elif job["interval"]:
                    # Interval-based execution
                    if not job.get("last_run") or (current_time - job["last_run"]).total_seconds() >= job["interval"]:
                        self.execute_task(job)
            time.sleep(self.default_interval)
    
    def execute_task(self, job):
        """
        Executes a given task.
        
        :param job: Task details dictionary.
        """
        try:
            self.log(f"Executing task '{job['task_name']}'...")
            job["task_function"]()
            job["last_run"] = datetime.now()
        except Exception as e:
            self.log(f"Error executing task '{job['task_name']}': {e}")
    
    def log(self, message):
        """
        Logs a message with a timestamp.
        
        :param message: The message to log.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def get_logs(self):
        """
        Returns the log entries.
        """
        return self.logs

# Example Usage
if __name__ == "__main__":
    scheduler = Scheduler()

    def task_1():
        print("Task 1 executed.")

    def task_2():
        print("Task 2 executed.")

    scheduler.add_task("Task 1", task_1, interval=10)  # Run every 10 seconds
    scheduler.add_task("Task 2", task_2, run_at=datetime.now() + timedelta(seconds=5))  # Run at specific time

    scheduler.start_scheduler()

    # Keep the program running for testing
    while True:
        time.sleep(1)
