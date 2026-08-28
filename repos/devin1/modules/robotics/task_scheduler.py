"""
Task Scheduler Module
=====================
Schedules and manages tasks for the robotics system.
Handles task prioritization, resource allocation, and time management.
"""

import threading
import time
from queue import PriorityQueue
from datetime import datetime


class Task:
    """
    Represents a task to be executed by the robotics system.
    """

    def __init__(self, task_id, description, priority, execution_time, callback):
        """
        Initializes a task.

        Args:
            task_id (str): Unique identifier for the task.
            description (str): Description of the task.
            priority (int): Priority of the task (lower value = higher priority).
            execution_time (int): Time required to execute the task (in seconds).
            callback (function): Function to execute for the task.
        """
        self.task_id = task_id
        self.description = description
        self.priority = priority
        self.execution_time = execution_time
        self.callback = callback

    def execute(self):
        """
        Executes the task's callback function.
        """
        print(f"[TASK] Executing task: {self.description}")
        try:
            self.callback()
        except Exception as e:
            print(f"[ERROR] Task execution failed: {e}")


class TaskScheduler:
    """
    Schedules and manages task execution.
    """

    def __init__(self):
        """
        Initializes the task scheduler.
        """
        print("[INFO] Initializing Task Scheduler...")
        self.task_queue = PriorityQueue()
        self.running = False
        self.lock = threading.Lock()

    def add_task(self, task: Task):
        """
        Adds a task to the scheduler.

        Args:
            task (Task): The task to be added.
        """
        with self.lock:
            self.task_queue.put((task.priority, datetime.now(), task))
            print(f"[SCHEDULER] Task added: {task.description}")

    def run_scheduler(self):
        """
        Runs the task scheduler to execute tasks in priority order.
        """
        print("[INFO] Starting Task Scheduler...")
        self.running = True
        while self.running:
            with self.lock:
                if not self.task_queue.empty():
                    _, _, task = self.task_queue.get()
                    print(f"[SCHEDULER] Running task: {task.description}")
                    time.sleep(task.execution_time)  # Simulating task execution
                    task.execute()
                else:
                    time.sleep(1)  # Avoid busy-waiting

    def stop_scheduler(self):
        """
        Stops the task scheduler.
        """
        print("[INFO] Stopping Task Scheduler...")
        self.running = False


# Example callback functions
def example_task_callback():
    print("[TASK CALLBACK] Task completed successfully!")


def complex_task_callback():
    print("[TASK CALLBACK] Performing complex operations...")
    time.sleep(3)  # Simulating a complex operation
    print("[TASK CALLBACK] Complex task completed.")


# Example usage
if __name__ == "__main__":
    # Initialize the scheduler
    scheduler = TaskScheduler()

    # Create and add tasks
    task1 = Task(
        task_id="task_001",
        description="Navigate to location A",
        priority=1,
        execution_time=2,
        callback=example_task_callback,
    )
    task2 = Task(
        task_id="task_002",
        description="Analyze sensor data",
        priority=2,
        execution_time=3,
        callback=complex_task_callback,
    )

    scheduler.add_task(task1)
    scheduler.add_task(task2)

    # Run the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=scheduler.run_scheduler)
    scheduler_thread.start()

    # Simulate running the system for 10 seconds
    time.sleep(10)
    scheduler.stop_scheduler()
    scheduler_thread.join()
