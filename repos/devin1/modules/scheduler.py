"""
scheduler.py

Manages task scheduling and execution. Supports one-time, recurring, and prioritized tasks.
"""

import time
import threading
import logging
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime, timedelta
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskType(Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    PRIORITY = "priority"

class Task:
    """
    Represents a scheduled task.
    """
    def __init__(
        self,
        name: str,
        action: Callable,
        run_time: datetime,
        task_type: TaskType,
        interval: Optional[timedelta] = None,
        priority: Optional[int] = None
    ):
        self.name = name
        self.action = action
        self.run_time = run_time
        self.task_type = task_type
        self.interval = interval
        self.priority = priority
        self.last_run = None

    def __str__(self):
        return f"Task(name={self.name}, type={self.task_type}, next_run={self.run_time})"

class schedule_tasks:
    """
    Manages the scheduling and execution of tasks.
    """
    def __init__(self):
        self.tasks: List[Task] = []
        self.lock = threading.Lock()
        self.running = False

    def add_task(
        self,
        name: str,
        action: Callable,
        run_time: datetime,
        task_type: TaskType = TaskType.ONE_TIME,
        interval: Optional[timedelta] = None,
        priority: Optional[int] = None
    ):
        """
        Adds a task to the schedule.
        """
        if task_type == TaskType.RECURRING and not interval:
            raise ValueError("Recurring tasks must have an interval.")
        if task_type == TaskType.PRIORITY and priority is None:
            raise ValueError("Priority tasks must have a priority value.")

        task = Task(name, action, run_time, task_type, interval, priority)
        with self.lock:
            self.tasks.append(task)
            self.tasks.sort(key=lambda t: (t.priority or 0, t.run_time))
        logger.info(f"Task added: {task}")

    def remove_task(self, name: str):
        """
        Removes a task by name.
        """
        with self.lock:
            self.tasks = [task for task in self.tasks if task.name != name]
        logger.info(f"Task removed: {name}")

    def run(self):
        """
        Starts the scheduler.
        """
        self.running = True
        while self.running:
            now = datetime.now()
            with self.lock:
                for task in self.tasks:
                    if task.run_time <= now:
                        logger.info(f"Executing task: {task.name}")
                        threading.Thread(target=self._execute_task, args=(task,)).start()

                        if task.task_type == TaskType.ONE_TIME:
                            self.tasks.remove(task)
                        elif task.task_type == TaskType.RECURRING:
                            task.last_run = now
                            task.run_time += task.interval
                        elif task.task_type == TaskType.PRIORITY:
                            self.tasks.remove(task)

            time.sleep(1)

    def stop(self):
        """
        Stops the scheduler.
        """
        self.running = False
        logger.info("Scheduler stopped.")

    def _execute_task(self, task: Task):
        """
        Executes the task's action.
        """
        try:
            task.action()
        except Exception as e:
            logger.error(f"Error executing task {task.name}: {e}")

# Example usage
if __name__ == "__main__":
    def sample_task():
        print(f"Task executed at {datetime.now()}!")

    scheduler = Scheduler()
    scheduler.add_task(
        name="One-Time Task",
        action=sample_task,
        run_time=datetime.now() + timedelta(seconds=5)
    )
    scheduler.add_task(
        name="Recurring Task",
        action=sample_task,
        run_time=datetime.now() + timedelta(seconds=10),
        task_type=TaskType.RECURRING,
        interval=timedelta(seconds=10)
    )
    scheduler.add_task(
        name="Priority Task",
        action=sample_task,
        run_time=datetime.now() + timedelta(seconds=3),
        task_type=TaskType.PRIORITY,
        priority=1
    )

    try:
        threading.Thread(target=scheduler.run).start()
        time.sleep(30)  # Run the scheduler for 30 seconds
    finally:
        scheduler.stop()
