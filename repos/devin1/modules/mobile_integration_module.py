"""
Mobile Integration Module
Provides functionality to connect, communicate, and interact with Android and iOS devices.
"""

import os
import subprocess
from typing import List, Tuple, Dict, Optional


class AndroidIntegration:
    """
    Provides integration utilities for Android devices.
    """

    def __init__(self, adb_path: str = "adb"):
        """
        Initialize the AndroidIntegration class.

        Args:
            adb_path (str): Path to the ADB (Android Debug Bridge) executable.
        """
        self.adb_path = adb_path

    def list_connected_devices(self) -> List[str]:
        """
        Lists all connected Android devices.

        Returns:
            List[str]: List of connected device serial numbers.
        """
        result = subprocess.run([self.adb_path, "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        devices = [line.split("\t")[0] for line in result.stdout.splitlines() if "\tdevice" in line]
        return devices

    def install_apk(self, device_id: str, apk_path: str) -> bool:
        """
        Installs an APK on the specified device.

        Args:
            device_id (str): Serial number of the target device.
            apk_path (str): Path to the APK file.

        Returns:
            bool: True if installation is successful, False otherwise.
        """
        result = subprocess.run(
            [self.adb_path, "-s", device_id, "install", apk_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return "Success" in result.stdout

    def execute_shell_command(self, device_id: str, command: str) -> str:
        """
        Executes a shell command on the specified device.

        Args:
            device_id (str): Serial number of the target device.
            command (str): Shell command to execute.

        Returns:
            str: Command output.
        """
        result = subprocess.run(
            [self.adb_path, "-s", device_id, "shell", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()


class IOSIntegration:
    """
    Provides integration utilities for iOS devices.
    """

    def __init__(self, libimobiledevice_path: str = "ideviceinfo"):
        """
        Initialize the IOSIntegration class.

        Args:
            libimobiledevice_path (str): Path to the libimobiledevice tool (e.g., ideviceinfo).
        """
        self.libimobiledevice_path = libimobiledevice_path

    def list_connected_devices(self) -> List[Dict[str, str]]:
        """
        Lists all connected iOS devices with details.

        Returns:
            List[Dict[str, str]]: List of dictionaries containing device information.
        """
        devices = []
        try:
            result = subprocess.run(
                [self.libimobiledevice_path, "-u"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            device_ids = result.stdout.strip().splitlines()
            for device_id in device_ids:
                device_info = subprocess.run(
                    [self.libimobiledevice_path, "-u", device_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                devices.append({"id": device_id, "info": device_info.stdout.strip()})
        except FileNotFoundError:
            print("libimobiledevice tools are not installed.")
        return devices

    def install_ipa(self, device_id: str, ipa_path: str) -> bool:
        """
        Installs an IPA on the specified iOS device.

        Args:
            device_id (str): UDID of the target device.
            ipa_path (str): Path to the IPA file.

        Returns:
            bool: True if installation is successful, False otherwise.
        """
        result = subprocess.run(
            ["ideviceinstaller", "-u", device_id, "-i", ipa_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return "Complete" in result.stdout

    def execute_shell_command(self, device_id: str, command: str) -> str:
        """
        Executes a shell command on the specified iOS device (if possible).

        Args:
            device_id (str): UDID of the target device.
            command (str): Shell command to execute.

        Returns:
            str: Command output.
        """
        # Placeholder: Requires advanced tools for executing shell commands on iOS devices.
        return f"Shell command execution on iOS devices is limited. Command attempted: {command}"


class MobileIntegration:
    """
    Unified interface for mobile integration with both Android and iOS devices.
    """

    def __init__(self):
        self.android = AndroidIntegration()
        self.ios = IOSIntegration()

    def list_all_devices(self) -> Dict[str, List[str]]:
        """
        Lists all connected Android and iOS devices.

        Returns:
            Dict[str, List[str]]: Dictionary containing lists of Android and iOS devices.
        """
        android_devices = self.android.list_connected_devices()
        ios_devices = self.ios.list_connected_devices()
        return {"Android": android_devices, "iOS": ios_devices}


# Example Usage
if __name__ == "__main__":
    integration = MobileIntegration()

    print("Connected Android Devices:")
    print(integration.android.list_connected_devices())

    print("Connected iOS Devices:")
    print(integration.ios.list_connected_devices())
