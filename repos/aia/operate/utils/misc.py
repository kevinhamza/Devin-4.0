import os
import platform
import subprocess
import time
import random
import string
from datetime import datetime
from modules.error_handling import ErrorHandling


class MiscUtils:
    """
    A collection of miscellaneous utility functions for system operations, 
    data processing, and general-purpose tasks.
    """

    def __init__(self):
        self.error_handler = ErrorHandling()

    def generate_random_string(self, length=8, include_special_chars=False):
        """
        Generate a random string.
        :param length: Length of the string to generate.
        :param include_special_chars: Whether to include special characters.
        :return: Random string.
        """
        try:
            chars = string.ascii_letters + string.digits
            if include_special_chars:
                chars += string.punctuation

            random_string = ''.join(random.choices(chars, k=length))
            print(f"Generated random string: {random_string}")
            return random_string
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to generate a random string.")

    def create_timestamp(self):
        """
        Create a timestamp in ISO 8601 format.
        :return: Timestamp string.
        """
        try:
            timestamp = datetime.now().isoformat()
            print(f"Generated timestamp: {timestamp}")
            return timestamp
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to create timestamp.")

    def get_system_info(self):
        """
        Retrieve basic system information.
        :return: Dictionary containing system details.
        """
        try:
            system_info = {
                "os": platform.system(),
                "version": platform.version(),
                "architecture": platform.architecture(),
                "hostname": platform.node(),
                "processor": platform.processor(),
            }
            print(f"System Info: {system_info}")
            return system_info
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to retrieve system information.")

    def run_command(self, command):
        """
        Execute a shell command and return the output.
        :param command: Command to execute.
        :return: Output of the command.
        """
        try:
            result = subprocess.run(
                command, shell=True, text=True, capture_output=True, check=True
            )
            print(f"Command Output: {result.stdout.strip()}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.error_handler.handle_exception(e, f"Command '{command}' failed.")
            return None

    def wait_for_duration(self, seconds):
        """
        Pause the program execution for a specified duration.
        :param seconds: Duration to wait in seconds.
        """
        try:
            print(f"Waiting for {seconds} seconds...")
            time.sleep(seconds)
        except Exception as e:
            self.error_handler.handle_exception(e, "Error during wait operation.")

    def list_files_in_directory(self, directory_path):
        """
        List all files in a directory.
        :param directory_path: Path to the directory.
        :return: List of file names.
        """
        try:
            if not os.path.exists(directory_path):
                raise FileNotFoundError(f"Directory not found: {directory_path}")

            files = [
                f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))
            ]
            print(f"Files in {directory_path}: {files}")
            return files
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to list files in directory.")

    def check_directory_exists(self, directory_path):
        """
        Check if a directory exists.
        :param directory_path: Path to the directory.
        :return: Boolean indicating existence.
        """
        try:
            exists = os.path.isdir(directory_path)
            print(f"Directory exists ({directory_path}): {exists}")
            return exists
        except Exception as e:
            self.error_handler.handle_exception(e, "Error checking directory existence.")

    def create_directory(self, directory_path):
        """
        Create a directory if it doesn't exist.
        :param directory_path: Path to the directory.
        """
        try:
            if not self.check_directory_exists(directory_path):
                os.makedirs(directory_path)
                print(f"Created directory: {directory_path}")
            else:
                print(f"Directory already exists: {directory_path}")
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to create directory.")


if __name__ == "__main__":
    utils = MiscUtils()

    # Example usage: Generate a random string
    utils.generate_random_string(12, include_special_chars=True)

    # Example usage: Get system information
    utils.get_system_info()

    # Example usage: Run a command
    utils.run_command("echo Hello, World!")

    # Example usage: Wait for 5 seconds
    utils.wait_for_duration(5)

    # Example usage: List files in a directory
    utils.list_files_in_directory(".")

    # Example usage: Create a new directory
    utils.create_directory("./test_directory")
