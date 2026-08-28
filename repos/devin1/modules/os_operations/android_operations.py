"""
Android System Utilities Module
Provides tools and utilities specific to Android systems.
"""

import os
import subprocess
from typing import Dict, List, Optional


class AndroidOperations:
    """
    A class for performing Android-specific system operations.
    """

    def __init__(self):
        self.adb_path = "adb"  # Ensure that ADB (Android Debug Bridge) is installed and accessible in PATH
        if not self._is_adb_installed():
            raise EnvironmentError("ADB is not installed or not accessible in the PATH.")

    def _is_adb_installed(self) -> bool:
        """
        Check if ADB (Android Debug Bridge) is installed.

        Returns:
            bool: True if ADB is installed, False otherwise.
        """
        try:
            subprocess.run([self.adb_path, "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except FileNotFoundError:
            return False

    def list_connected_devices(self) -> List[str]:
        """
        List all connected Android devices.

        Returns:
            List[str]: A list of connected device IDs.
        """
        try:
            result = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split("\n")[1:]  # Skip the header line
            devices = [line.split()[0] for line in lines if "device" in line]
            return devices
        except Exception as e:
            return [f"Error listing devices: {e}"]

    def get_device_info(self, device_id: str) -> Dict[str, str]:
        """
        Get detailed information about a connected Android device.

        Args:
            device_id (str): The ID of the device.

        Returns:
            Dict[str, str]: A dictionary containing device information.
        """
        try:
            commands = {
                "Manufacturer": f"-s {device_id} shell getprop ro.product.manufacturer",
                "Model": f"-s {device_id} shell getprop ro.product.model",
                "Android Version": f"-s {device_id} shell getprop ro.build.version.release",
                "SDK Version": f"-s {device_id} shell getprop ro.build.version.sdk",
            }
            info = {}
            for key, cmd in commands.items():
                result = subprocess.run(f"{self.adb_path} {cmd}", shell=True, text=True, capture_output=True, check=True)
                info[key] = result.stdout.strip()
            return info
        except Exception as e:
            return {"Error": f"Error fetching device info for {device_id}: {e}"}

    def install_app(self, device_id: str, apk_path: str) -> str:
        """
        Install an APK file on a connected Android device.

        Args:
            device_id (str): The ID of the device.
            apk_path (str): The path to the APK file.

        Returns:
            str: The result of the installation process.
        """
        try:
            result = subprocess.run([self.adb_path, "-s", device_id, "install", apk_path], text=True, capture_output=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error installing app: {e}"

    def uninstall_app(self, device_id: str, package_name: str) -> str:
        """
        Uninstall an application from a connected Android device.

        Args:
            device_id (str): The ID of the device.
            package_name (str): The package name of the application to uninstall.

        Returns:
            str: The result of the uninstallation process.
        """
        try:
            result = subprocess.run([self.adb_path, "-s", device_id, "uninstall", package_name], text=True, capture_output=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error uninstalling app: {e}"

    def transfer_file_to_device(self, device_id: str, local_path: str, remote_path: str) -> str:
        """
        Transfer a file from the host system to the Android device.

        Args:
            device_id (str): The ID of the device.
            local_path (str): The path to the file on the host system.
            remote_path (str): The destination path on the Android device.

        Returns:
            str: The result of the file transfer process.
        """
        try:
            result = subprocess.run([self.adb_path, "-s", device_id, "push", local_path, remote_path], text=True, capture_output=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error transferring file to device: {e}"

    def transfer_file_from_device(self, device_id: str, remote_path: str, local_path: str) -> str:
        """
        Transfer a file from the Android device to the host system.

        Args:
            device_id (str): The ID of the device.
            remote_path (str): The path to the file on the Android device.
            local_path (str): The destination path on the host system.

        Returns:
            str: The result of the file transfer process.
        """
        try:
            result = subprocess.run([self.adb_path, "-s", device_id, "pull", remote_path, local_path], text=True, capture_output=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error transferring file from device: {e}"

    def execute_command_on_device(self, device_id: str, command: str) -> str:
        """
        Execute a shell command on a connected Android device.

        Args:
            device_id (str): The ID of the device.
            command (str): The shell command to execute.

        Returns:
            str: The output of the command.
        """
        try:
            result = subprocess.run([self.adb_path, "-s", device_id, "shell", command], text=True, capture_output=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error executing command on device: {e}"


# Example Usage
if __name__ == "__main__":
    android_ops = AndroidOperations()
    devices = android_ops.list_connected_devices()
    print("Connected Devices:", devices)

    if devices:
        device_id = devices[0]
        print("\nDevice Info:")
        print(android_ops.get_device_info(device_id))

        print("\nTesting file transfer...")
        print(android_ops.transfer_file_to_device(device_id, "example.txt", "/sdcard/example.txt"))
