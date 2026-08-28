"""
Windows-Specific Utilities Module
Provides utilities tailored for Windows operating system.
"""

import os
import ctypes
import platform
from typing import List, Dict, Optional
import subprocess
import winreg


class WindowsOperations:
    """
    A class to encapsulate Windows-specific utilities and operations.
    """

    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        if not self.is_windows:
            raise EnvironmentError("This module is designed to run on Windows systems only.")

    def get_system_version(self) -> str:
        """
        Get the Windows version.

        Returns:
            str: The Windows version string.
        """
        return platform.version()

    def get_user_account_info(self) -> Dict[str, str]:
        """
        Retrieve the current user account information.

        Returns:
            Dict[str, str]: A dictionary containing account-related information.
        """
        user_info = {
            "Username": os.getenv("USERNAME"),
            "User Domain": os.getenv("USERDOMAIN"),
            "Home Directory": os.getenv("HOMEPATH"),
        }
        return user_info

    def list_installed_programs(self) -> List[str]:
        """
        List all installed programs on the Windows machine.

        Returns:
            List[str]: A list of installed program names.
        """
        program_list = []
        reg_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ]

        for reg_path in reg_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey_path = os.path.join(reg_path, subkey_name)
                            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path) as subkey:
                                program_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                program_list.append(program_name)
                        except FileNotFoundError:
                            continue
            except Exception as e:
                print(f"Error reading registry: {e}")
        return program_list

    def execute_command(self, command: str) -> str:
        """
        Execute a shell command on the Windows system.

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

    def check_admin_privileges(self) -> bool:
        """
        Check if the script is running with administrator privileges.

        Returns:
            bool: True if running as administrator, False otherwise.
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() == 1
        except Exception as e:
            print(f"Error checking admin privileges: {e}")
            return False

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
            subprocess.run(f"setx {key} {value}", shell=True, check=True)
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

    def enable_firewall(self) -> bool:
        """
        Enable the Windows firewall.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            subprocess.run("netsh advfirewall set allprofiles state on", shell=True, check=True)
            return True
        except Exception as e:
            print(f"Error enabling firewall: {e}")
            return False

    def disable_firewall(self) -> bool:
        """
        Disable the Windows firewall.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            subprocess.run("netsh advfirewall set allprofiles state off", shell=True, check=True)
            return True
        except Exception as e:
            print(f"Error disabling firewall: {e}")
            return False


# Example Usage
if __name__ == "__main__":
    win_ops = WindowsOperations()

    print("Windows Version:")
    print(win_ops.get_system_version())

    print("\nUser Account Information:")
    print(win_ops.get_user_account_info())

    print("\nInstalled Programs:")
    programs = win_ops.list_installed_programs()
    print(programs[:10])  # Displaying only the first 10 programs

    print("\nChecking Admin Privileges:")
    print(win_ops.check_admin_privileges())
