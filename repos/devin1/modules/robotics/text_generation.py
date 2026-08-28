"""
Text Generation Module for Robotics
Generates text based on predefined templates and dynamic data inputs.
"""

import random
import datetime

class TextGeneration:
    """
    Provides functionalities to generate text using templates and dynamic data.
    Useful for creating reports, responses, or logs in robotic systems.
    """

    templates = {
        "status_update": [
            "The system is operating at {efficiency}% efficiency as of {timestamp}.",
            "Current operational status: {status}. Updated at {timestamp}.",
            "All systems are functioning {status}. Last check at {timestamp}."
        ],
        "error_report": [
            "An error has occurred: {error_description}. Time: {timestamp}.",
            "System alert: {error_description} detected at {timestamp}.",
            "Warning: {error_description}. Occurred at {timestamp}."
        ],
        "task_completion": [
            "Task '{task_name}' completed successfully at {timestamp}.",
            "Successfully finished task: {task_name}. Completion time: {timestamp}.",
            "Task '{task_name}' was executed with {outcome}. Time: {timestamp}."
        ],
        "random_quote": [
            "The best way to predict the future is to create it.",
            "Innovation distinguishes between a leader and a follower.",
            "The journey of a thousand miles begins with a single step."
        ]
    }

    @staticmethod
    def generate_text(template_type, **kwargs):
        """
        Generate text based on the given template type and dynamic inputs.
        
        Args:
            template_type (str): The type of template to use.
            **kwargs: Dynamic inputs to populate the template.
        
        Returns:
            str: Generated text.
        """
        if template_type not in TextGeneration.templates:
            raise ValueError(f"Template type '{template_type}' not found.")
        
        selected_template = random.choice(TextGeneration.templates[template_type])
        filled_template = selected_template.format(**kwargs)
        return filled_template

    @staticmethod
    def generate_status_update(efficiency, status="normal"):
        """
        Generate a status update text.
        
        Args:
            efficiency (float): Current system efficiency.
            status (str): Current operational status.
        
        Returns:
            str: Generated status update.
        """
        timestamp = datetime.datetime.now().isoformat()
        return TextGeneration.generate_text(
            "status_update",
            efficiency=efficiency,
            status=status,
            timestamp=timestamp
        )

    @staticmethod
    def generate_error_report(error_description):
        """
        Generate an error report text.
        
        Args:
            error_description (str): Description of the error.
        
        Returns:
            str: Generated error report.
        """
        timestamp = datetime.datetime.now().isoformat()
        return TextGeneration.generate_text(
            "error_report",
            error_description=error_description,
            timestamp=timestamp
        )

    @staticmethod
    def generate_task_completion(task_name, outcome="success"):
        """
        Generate a task completion text.
        
        Args:
            task_name (str): Name of the completed task.
            outcome (str): Outcome of the task execution.
        
        Returns:
            str: Generated task completion text.
        """
        timestamp = datetime.datetime.now().isoformat()
        return TextGeneration.generate_text(
            "task_completion",
            task_name=task_name,
            outcome=outcome,
            timestamp=timestamp
        )

    @staticmethod
    def get_random_quote():
        """
        Get a random motivational quote.
        
        Returns:
            str: A motivational quote.
        """
        return TextGeneration.generate_text("random_quote")


# Example usage (for testing)
if __name__ == "__main__":
    print(TextGeneration.generate_status_update(efficiency=85.5))
    print(TextGeneration.generate_error_report("Overheating detected in motor control module"))
    print(TextGeneration.generate_task_completion(task_name="Path Planning"))
    print(TextGeneration.get_random_quote())
