"""
macOS-Specific Utilities Module
Provides utilities tailored for the macOS operating system.
"""

import os
import platform
import subprocess
from typing import Dict, List, Optional


class MacOSOperations:
    """
    A class to encapsulate macOS-specific utilities and operations.
    """

    def __init__(self):
        self.is_macos = platform.system() == "Darwin"
        if not self.is_macos:
            raise EnvironmentError("This module is designed to run on macOS systems only.")

    def get_system_version(self) -> str:
        """
        Get the macOS version.

        Returns:
            str: The macOS version.
        """
        try:
            result = subprocess.run(["sw_vers"], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except FileNotFoundError:
            return "sw_vers command not found. This functionality is macOS-specific."
        except Exception as e:
            return f"Error fetching system version: {e}"

    def get_user_account_info(self) -> Dict[str, str]:
        """
        Retrieve the current user account information.

        Returns:
            Dict[str, str]: A dictionary containing account-related information.
        """
        user_info = {
            "Username": os.getenv("USER"),
            "Home Directory": os.getenv("HOME"),
            "Shell": os.getenv("SHELL"),
        }
        return user_info

    def list_installed_applications(self) -> List[str]:
        """
        List installed applications in the `/Applications` directory.

        Returns:
            List[str]: A list of installed application names.
        """
        try:
            apps_path = "/Applications"
            apps = [app for app in os.listdir(apps_path) if app.endswith(".app")]
            return apps
        except FileNotFoundError:
            return ["Applications directory not found."]
        except Exception as e:
            return [f"Error listing applications: {e}"]

    def execute_command(self, command: str) -> str:
        """
        Execute a shell command on the macOS system.

        Args:
            command (str): The shell command to execute.

        Returns:
            str: The output of the command.
        """
        try:
            result = subprocess.run(command, shell=True, text=True, capture_output=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error executing command: {e}"

    def check_root_privileges(self) -> bool:
        """
        Check if the script is running with root privileges.

        Returns:
            bool: True if running as root, False otherwise.
        """
        return os.geteuid() == 0

    def set_environment_variable(self, key: str, value: str) -> bool:
        """
        Set a system environment variable.

        Args:
            key (str): The variable name.
            value (str): The variable value.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            os.environ[key] = value
            with open(os.path.expanduser("~/.zshrc"), "a") as zshrc_file:
                zshrc_file.write(f"\nexport {key}={value}")
            return True
        except Exception as e:
            print(f"Error setting environment variable: {e}")
            return False

    def get_environment_variable(self, key: str) -> Optional[str]:
        """
        Get the value of a system environment variable.

        Args:
            key (str): The variable name.

        Returns:
            Optional[str]: The variable value or None if not found.
        """
        return os.getenv(key)

    def manage_service(self, service_name: str, action: str) -> str:
        """
        Manage macOS services using `launchctl`.

        Args:
            service_name (str): The name of the service.
            action (str): The action to perform (start, stop, status).

        Returns:
            str: The output of the service management command.
        """
        try:
            command = f"launchctl {action} {service_name}"
            result = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error managing service {service_name}: {e}"

    def update_system(self) -> str:
        """
        Update macOS software using the `softwareupdate` command.

        Returns:
            str: The output of the update process.
        """
        try:
            result = subprocess.run("softwareupdate -ia", shell=True, text=True, capture_output=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error updating the system: {e}"


# Example Usage
if __name__ == "__main__":
    mac_ops = MacOSOperations()

    print("macOS Version:")
    print(mac_ops.get_system_version())

    print("\nUser Account Information:")
    print(mac_ops.get_user_account_info())

    print("\nInstalled Applications:")
    applications = mac_ops.list_installed_applications()
    print(applications[:10])  # Displaying only the first 10 applications

    print("\nChecking Root Privileges:")
    print(mac_ops.check_root_privileges())
