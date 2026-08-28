"""
Linux-Specific Utilities Module
Provides utilities tailored for the Linux operating system.
"""

import os
import platform
import subprocess
from typing import List, Dict, Optional


class LinuxOperations:
    """
    A class to encapsulate Linux-specific utilities and operations.
    """

    def __init__(self):
        self.is_linux = platform.system() == "Linux"
        if not self.is_linux:
            raise EnvironmentError("This module is designed to run on Linux systems only.")

    def get_system_version(self) -> str:
        """
        Get the Linux distribution and version.

        Returns:
            str: The Linux distribution and version.
        """
        try:
            result = subprocess.run(["lsb_release", "-a"], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except FileNotFoundError:
            return "lsb_release command not found. Install it with 'sudo apt install lsb-release'."
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

    def list_installed_packages(self) -> List[str]:
        """
        List all installed packages on the Linux machine.

        Returns:
            List[str]: A list of installed package names.
        """
        try:
            result = subprocess.run(["dpkg", "--get-selections"], capture_output=True, text=True, check=True)
            packages = [line.split("\t")[0] for line in result.stdout.splitlines() if "\tinstall" in line]
            return packages
        except FileNotFoundError:
            return ["dpkg command not found. This functionality is specific to Debian-based distributions."]
        except Exception as e:
            return [f"Error fetching installed packages: {e}"]

    def execute_command(self, command: str) -> str:
        """
        Execute a shell command on the Linux system.

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
            with open("/etc/environment", "a") as env_file:
                env_file.write(f"\n{key}={value}")
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
        Start, stop, or restart a system service.

        Args:
            service_name (str): The name of the service.
            action (str): The action to perform (start, stop, restart, status).

        Returns:
            str: The output of the service management command.
        """
        try:
            command = f"sudo systemctl {action} {service_name}"
            result = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error managing service {service_name}: {e}"

    def update_system(self) -> str:
        """
        Update the system's package lists and upgrade installed packages.

        Returns:
            str: The output of the update and upgrade process.
        """
        try:
            update_result = subprocess.run("sudo apt update", shell=True, text=True, capture_output=True, check=True)
            upgrade_result = subprocess.run("sudo apt upgrade -y", shell=True, text=True, capture_output=True, check=True)
            return f"Update output:\n{update_result.stdout.strip()}\nUpgrade output:\n{upgrade_result.stdout.strip()}"
        except Exception as e:
            return f"Error updating the system: {e}"


# Example Usage
if __name__ == "__main__":
    linux_ops = LinuxOperations()

    print("Linux Version:")
    print(linux_ops.get_system_version())

    print("\nUser Account Information:")
    print(linux_ops.get_user_account_info())

    print("\nInstalled Packages:")
    packages = linux_ops.list_installed_packages()
    print(packages[:10])  # Displaying only the first 10 packages

    print("\nChecking Root Privileges:")
    print(linux_ops.check_root_privileges())
