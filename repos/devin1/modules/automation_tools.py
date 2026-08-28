"""
Automation Tools Module
Automates tasks such as scheduling, routine execution, and workflow management.
"""

import os
import time
import schedule
from datetime import datetime
from typing import Callable, List, Dict, Any


class Task:
    """
    Represents an automatable task.
    """

    def __init__(self, name: str, action: Callable, schedule_time: str, interval_type: str = "daily"):
        """
        Initialize a Task object.

        Args:
            name (str): Name of the task.
            action (Callable): Function to execute for the task.
            schedule_time (str): Time to schedule the task (HH:MM format).
            interval_type (str): Interval for scheduling (e.g., 'daily', 'hourly').
        """
        self.name = name
        self.action = action
        self.schedule_time = schedule_time
        self.interval_type = interval_type

    def execute(self):
        """
        Execute the task action.
        """
        print(f"Executing Task: {self.name}")
        self.action()


class AutomationManager:
    """
    Manages and schedules automated tasks.
    """

    def __init__(self):
        """
        Initialize the Automation Manager.
        """
        self.tasks: List[Task] = []

    def add_task(self, task: Task):
        """
        Add a task to the manager.

        Args:
            task (Task): Task to add.
        """
        self.tasks.append(task)
        print(f"Task '{task.name}' added to the manager.")

    def schedule_task(self, task: Task):
        """
        Schedule a task based on its interval type.

        Args:
            task (Task): Task to schedule.
        """
        if task.interval_type == "daily":
            schedule.every().day.at(task.schedule_time).do(task.execute)
        elif task.interval_type == "hourly":
            schedule.every().hour.at(f":{task.schedule_time.split(':')[1]}").do(task.execute)
        elif task.interval_type == "weekly":
            schedule.every().week.at(task.schedule_time).do(task.execute)
        print(f"Task '{task.name}' scheduled as {task.interval_type} at {task.schedule_time}.")

    def start_scheduler(self):
        """
        Start the scheduler to run tasks at specified times.
        """
        print("Scheduler started...")
        while True:
            schedule.run_pending()
            time.sleep(1)

    def list_tasks(self) -> List[str]:
        """
        List all scheduled tasks.

        Returns:
            List[str]: Names of all scheduled tasks.
        """
        return [task.name for task in self.tasks]

    def run_task_now(self, task_name: str):
        """
        Immediately execute a task by name.

        Args:
            task_name (str): Name of the task to run.
        """
        for task in self.tasks:
            if task.name == task_name:
                task.execute()
                return
        print(f"Task '{task_name}' not found.")


class WorkflowAutomation:
    """
    Handles workflow automation by chaining tasks and routines.
    """

    def __init__(self):
        """
        Initialize the Workflow Automation.
        """
        self.workflow: List[Callable] = []

    def add_to_workflow(self, action: Callable):
        """
        Add an action to the workflow.

        Args:
            action (Callable): Function to add to the workflow.
        """
        self.workflow.append(action)
        print("Action added to workflow.")

    def execute_workflow(self):
        """
        Execute the entire workflow sequentially.
        """
        print("Executing Workflow...")
        for step, action in enumerate(self.workflow, 1):
            print(f"Executing Step {step}...")
            action()
        print("Workflow execution completed.")


class LoggingManager:
    """
    Manages logging of automation activities.
    """

    @staticmethod
    def log_event(event: str, log_file: str = "automation_logs.txt"):
        """
        Log an event to a file.

        Args:
            event (str): Event description.
            log_file (str): Path to the log file.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a") as file:
            file.write(f"[{timestamp}] {event}\n")
        print(f"Event logged: {event}")


# Example Usage
if __name__ == "__main__":
    manager = AutomationManager()
    workflow = WorkflowAutomation()

    # Define sample actions
    def morning_routine():
        print("Starting morning routine...")
        LoggingManager.log_event("Morning routine started.")

    def system_backup():
        print("Performing system backup...")
        LoggingManager.log_event("System backup completed.")

    # Create and add tasks
    morning_task = Task("Morning Routine", morning_routine, "08:00")
    backup_task = Task("System Backup", system_backup, "22:00", interval_type="daily")

    manager.add_task(morning_task)
    manager.add_task(backup_task)

    # Schedule tasks
    manager.schedule_task(morning_task)
    manager.schedule_task(backup_task)

    # Add actions to workflow
    workflow.add_to_workflow(morning_routine)
    workflow.add_to_workflow(system_backup)

    # Start workflow or scheduler
    workflow.execute_workflow()
    # Uncomment below to run the scheduler
    # manager.start_scheduler()
