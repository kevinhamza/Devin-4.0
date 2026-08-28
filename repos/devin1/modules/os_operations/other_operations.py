"""
Other Operating Systems Utilities Module
Provides tools and utilities for handling operations on non-mainstream or less common operating systems.
"""

import platform
import os
from typing import Dict, List, Optional


class OtherOSOperations:
    """
    A class for handling operations on non-mainstream operating systems.
    """

    def __init__(self):
        self.os_name = platform.system()
        self.supported_os = ["Solaris", "FreeBSD", "OpenBSD", "NetBSD", "Haiku", "ReactOS"]

    def is_supported_os(self) -> bool:
        """
        Check if the current operating system is supported by this module.

        Returns:
            bool: True if the operating system is supported, False otherwise.
        """
        return self.os_name in self.supported_os

    def get_os_details(self) -> Dict[str, str]:
        """
        Fetch details about the current operating system.

        Returns:
            Dict[str, str]: A dictionary containing OS details.
        """
        return {
            "OS Name": self.os_name,
            "Version": platform.version(),
            "Release": platform.release(),
            "Architecture": platform.architecture()[0],
            "Machine": platform.machine()
        }

    def list_directory(self, path: str = ".") -> List[str]:
        """
        List files and directories in the given path.

        Args:
            path (str): The directory path. Defaults to the current directory.

        Returns:
            List[str]: A list of files and directories in the specified path.
        """
        try:
            return os.listdir(path)
        except FileNotFoundError:
            return [f"Path not found: {path}"]
        except PermissionError:
            return [f"Permission denied for path: {path}"]
        except Exception as e:
            return [f"Error: {e}"]

    def create_directory(self, path: str) -> str:
        """
        Create a directory at the specified path.

        Args:
            path (str): The path where the directory should be created.

        Returns:
            str: Success or error message.
        """
        try:
            os.makedirs(path, exist_ok=True)
            return f"Directory created: {path}"
        except PermissionError:
            return f"Permission denied: {path}"
        except Exception as e:
            return f"Error: {e}"

    def delete_directory(self, path: str) -> str:
        """
        Delete the specified directory.

        Args:
            path (str): The path of the directory to delete.

        Returns:
            str: Success or error message.
        """
        try:
            os.rmdir(path)
            return f"Directory deleted: {path}"
        except FileNotFoundError:
            return f"Directory not found: {path}"
        except PermissionError:
            return f"Permission denied: {path}"
        except Exception as e:
            return f"Error: {e}"

    def execute_command(self, command: str) -> Dict[str, Optional[str]]:
        """
        Execute a shell command.

        Args:
            command (str): The command to execute.

        Returns:
            Dict[str, Optional[str]]: A dictionary containing the command's output and error messages.
        """
        try:
            result = os.popen(command).read()
            return {"Output": result.strip(), "Error": None}
        except Exception as e:
            return {"Output": None, "Error": str(e)}

    def check_process(self, process_name: str) -> bool:
        """
        Check if a specific process is running.

        Args:
            process_name (str): The name of the process to check.

        Returns:
            bool: True if the process is running, False otherwise.
        """
        try:
            command = f"ps -A | grep {process_name}" if self.os_name not in ["Windows"] else f"tasklist | findstr {process_name}"
            result = os.popen(command).read()
            return bool(result.strip())
        except Exception:
            return False

    def reboot_system(self) -> str:
        """
        Reboot the system.

        Returns:
            str: Success or error message.
        """
        try:
            command = "reboot" if self.os_name not in ["Windows"] else "shutdown /r /t 0"
            os.system(command)
            return "Reboot command executed."
        except Exception as e:
            return f"Error executing reboot: {e}"


# Example Usage
if __name__ == "__main__":
    other_os_ops = OtherOSOperations()
    if other_os_ops.is_supported_os():
        print("Operating System Details:")
        print(other_os_ops.get_os_details())

        print("\nListing current directory:")
        print(other_os_ops.list_directory())

        print("\nCreating a test directory:")
        print(other_os_ops.create_directory("test_dir"))

        print("\nDeleting the test directory:")
        print(other_os_ops.delete_directory("test_dir"))

        print("\nExecuting a sample command (ls):")
        print(other_os_ops.execute_command("ls"))
    else:
        print("This OS is not supported by this module.")
