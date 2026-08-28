"""
pc_integration.py
------------------
This module handles PC-specific integration for the Devin voice assistant.

Features:
- Execute PC-specific voice commands.
- Control system settings, open applications, and manage files.
- Cross-platform support for Windows, macOS, and Linux.
"""

import os
import subprocess
import logging
import platform
import shutil

# Optional imports for extended functionality
try:
    import pyttsx3  # Text-to-speech
    from plyer import notification  # Cross-platform notifications
except ImportError as e:
    raise ImportError(f"Missing module: {e}. Please ensure all dependencies are installed.")


class PCIntegration:
    """
    Handles PC-specific tasks for the Devin voice assistant.
    """

    def __init__(self, tts_engine="sapi5", log_file="pc_integration.log"):
        """
        Initializes the PC integration module.

        Args:
            tts_engine (str): Text-to-speech engine to use.
            log_file (str): Path to the log file.
        """
        self.tts_engine = pyttsx3.init(tts_engine)
        self.os_name = platform.system().lower()

        # Set up logging
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        logging.info("PCIntegration initialized.")

    def notify_user(self, title, message):
        """
        Sends a desktop notification.

        Args:
            title (str): Notification title.
            message (str): Notification message.
        """
        logging.info(f"Sending notification: {title} - {message}")
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Devin Voice Assistant"
            )
        except Exception as e:
            logging.error(f"Notification failed: {e}")
            raise

    def execute_command(self, command):
        """
        Executes a system command.

        Args:
            command (str): The command to execute.

        Returns:
            str: Output of the command.
        """
        logging.info(f"Executing command: {command}")
        try:
            result = subprocess.check_output(command, shell=True, text=True)
            logging.info(f"Command output: {result}")
            return result.strip()
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed: {e}")
            return f"Error executing command: {e}"

    def open_application(self, app_name):
        """
        Opens an application by name.

        Args:
            app_name (str): The name of the application to open.

        Returns:
            str: Status message.
        """
        logging.info(f"Opening application: {app_name}")
        try:
            if self.os_name == "windows":
                subprocess.Popen(f"start {app_name}", shell=True)
            elif self.os_name == "darwin":  # macOS
                subprocess.Popen(["open", f"/Applications/{app_name}.app"])
            elif self.os_name == "linux":
                subprocess.Popen([app_name])
            else:
                return f"Unsupported platform: {self.os_name}"
            return f"Application '{app_name}' opened successfully."
        except Exception as e:
            logging.error(f"Failed to open application: {e}")
            return f"Error opening application: {e}"

    def control_system(self, action):
        """
        Performs system control actions like shutdown, restart, or sleep.

        Args:
            action (str): The action to perform ("shutdown", "restart", "sleep").

        Returns:
            str: Status message.
        """
        logging.info(f"Performing system action: {action}")
        try:
            if self.os_name == "windows":
                actions = {
                    "shutdown": "shutdown /s /t 0",
                    "restart": "shutdown /r /t 0",
                    "sleep": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"
                }
            elif self.os_name == "darwin":  # macOS
                actions = {
                    "shutdown": "sudo shutdown -h now",
                    "restart": "sudo shutdown -r now",
                    "sleep": "pmset sleepnow"
                }
            elif self.os_name == "linux":
                actions = {
                    "shutdown": "shutdown now",
                    "restart": "reboot",
                    "sleep": "systemctl suspend"
                }
            else:
                return f"Unsupported platform: {self.os_name}"

            if action in actions:
                self.execute_command(actions[action])
                return f"System {action} executed successfully."
            else:
                return f"Unknown action: {action}"
        except Exception as e:
            logging.error(f"System control failed: {e}")
            return f"Error performing system action: {e}"

    def manage_files(self, file_path, operation, destination=None):
        """
        Manages files on the PC.

        Args:
            file_path (str): Path to the file.
            operation (str): Operation to perform ("delete", "copy", "move").
            destination (str): Destination path for copy/move operations.

        Returns:
            str: Status message.
        """
        logging.info(f"Managing file: {file_path}, operation: {operation}")
        try:
            if operation == "delete":
                os.remove(file_path)
                return f"File '{file_path}' deleted successfully."
            elif operation == "copy":
                if not destination:
                    return "Destination path is required for copy operation."
                shutil.copy(file_path, destination)
                return f"File '{file_path}' copied to '{destination}'."
            elif operation == "move":
                if not destination:
                    return "Destination path is required for move operation."
                shutil.move(file_path, destination)
                return f"File '{file_path}' moved to '{destination}'."
            else:
                return f"Unknown operation: {operation}"
        except Exception as e:
            logging.error(f"File management failed: {e}")
            return f"Error managing file: {e}"

    def text_to_speech(self, text):
        """
        Converts text to speech.

        Args:
            text (str): Text to speak.
        """
        logging.info(f"Converting text to speech: {text}")
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            logging.error(f"Text-to-speech failed: {e}")
            raise


if __name__ == "__main__":
    # Example usage
    pc_integration = PCIntegration()

    print("1. Send a notification")
    print("2. Open an application")
    print("3. Perform a system action")
    print("4. Manage a file")
    print("5. Speak a text")

    choice = input("Choose an option (1/2/3/4/5): ")

    if choice == "1":
        pc_integration.notify_user("Test Notification", "This is a test notification.")
    elif choice == "2":
        app = input("Enter the app name to open: ")
        print(pc_integration.open_application(app))
    elif choice == "3":
        action = input("Enter the action (shutdown/restart/sleep): ")
        print(pc_integration.control_system(action))
    elif choice == "4":
        file_path = input("Enter the file path: ")
        operation = input("Enter the operation (delete/copy/move): ")
        destination = None
        if operation in ["copy", "move"]:
            destination = input("Enter the destination path: ")
        print(pc_integration.manage_files(file_path, operation, destination))
    elif choice == "5":
        text = input("Enter the text to speak: ")
        pc_integration.text_to_speech(text)
    else:
        print("Invalid choice.")
