import os
import time
import threading
from datetime import datetime
import pyautogui
from modules.error_handling import ErrorHandling
from modules.device_control import DeviceControl


class Automation:
    def __init__(self):
        """
        Initialize the Automation module with error handling and device control capabilities.
        """
        self.error_handler = ErrorHandling()
        self.device_control = DeviceControl()

    def schedule_task(self, task, run_at):
        """
        Schedule a task to run at a specific time.
        :param task: A callable representing the task to execute.
        :param run_at: A datetime object specifying when to run the task.
        """
        try:
            delay = (run_at - datetime.now()).total_seconds()
            if delay > 0:
                threading.Timer(delay, task).start()
            else:
                raise ValueError("Scheduled time must be in the future.")
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to schedule task.")

    def automate_typing(self, text, interval=0.1):
        """
        Automate typing a string.
        :param text: The text to type.
        :param interval: Time delay between keystrokes.
        """
        try:
            pyautogui.typewrite(text, interval=interval)
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to automate typing.")

    def automate_mouse(self, x, y, click=True):
        """
        Automate mouse movement and optional click.
        :param x: X-coordinate.
        :param y: Y-coordinate.
        :param click: Whether to click the mouse.
        """
        try:
            pyautogui.moveTo(x, y, duration=0.5)
            if click:
                pyautogui.click()
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to automate mouse movement.")

    def create_task_automation(self, task_name, action_sequence):
        """
        Automate a sequence of actions as a task.
        :param task_name: Name of the task.
        :param action_sequence: List of actions (functions) to execute.
        """
        try:
            for action in action_sequence:
                action()
            print(f"Task '{task_name}' completed successfully.")
        except Exception as e:
            self.error_handler.handle_exception(e, f"Failed to complete task '{task_name}'.")

    def log_task_execution(self, task_name):
        """
        Log the execution of a task.
        :param task_name: Name of the task being executed.
        """
        log_file = os.path.join("logs", "task_execution.log")
        with open(log_file, "a") as log:
            log.write(f"{datetime.now()} - Executed task: {task_name}\n")

    def monitor_system_for_events(self, event_callback):
        """
        Continuously monitor the system for specific events and trigger a callback.
        :param event_callback: Callback function to execute on event detection.
        """
        try:
            while True:
                event_detected = self.device_control.check_for_event()
                if event_detected:
                    event_callback()
                time.sleep(1)
        except KeyboardInterrupt:
            print("Event monitoring stopped.")
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed during event monitoring.")

    def add_whiterabbit_ai_support(self, task_name, description):
        """
        Integrate WhiteRabbit AI for advanced task automation.
        :param task_name: Name of the task to be automated.
        :param description: Description of what the task should accomplish.
        """
        try:
            print(f"Using WhiteRabbit AI for task: {task_name}. Description: {description}")
            # Placeholder for real AI integration
            response = "AI executed the task successfully."
            self.log_task_execution(f"WhiteRabbit AI: {task_name}")
            return response
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to integrate WhiteRabbit AI.")


if __name__ == "__main__":
    automation = Automation()

    # Example: Automate typing
    automation.automate_typing("Hello, this is an automated message.", interval=0.2)

    # Example: Schedule a task
    run_time = datetime.now() + timedelta(seconds=10)
    automation.schedule_task(lambda: print("Scheduled task executed!"), run_time)

    # Example: Integrate WhiteRabbit AI
    automation.add_whiterabbit_ai_support("Daily Report Automation", "Generate and email a daily report.")
