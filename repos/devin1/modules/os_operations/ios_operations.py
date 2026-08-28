"""
iOS System Utilities Module
Provides tools and utilities specific to iOS systems.
"""

import os
import subprocess
from typing import List, Dict, Optional


class iOSOperations:
    """
    A class for performing iOS-specific system operations.
    """

    def __init__(self):
        self.ideviceinfo_path = "ideviceinfo"  # Ensure libimobiledevice tools are installed and accessible
        self.idevicesyslog_path = "idevicesyslog"
        self.ideviceinstaller_path = "ideviceinstaller"
        self.idevice_id_path = "idevice_id"
        self.libimobiledevice_available = self._is_libimobiledevice_installed()

    def _is_libimobiledevice_installed(self) -> bool:
        """
        Check if libimobiledevice tools are installed.

        Returns:
            bool: True if libimobiledevice tools are installed, False otherwise.
        """
        try:
            subprocess.run([self.ideviceinfo_path, "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except FileNotFoundError:
            return False

    def list_connected_devices(self) -> List[str]:
        """
        List all connected iOS devices.

        Returns:
            List[str]: A list of connected device UDIDs.
        """
        if not self.libimobiledevice_available:
            return ["libimobiledevice tools are not installed or accessible."]
        
        try:
            result = subprocess.run([self.idevice_id_path, "-l"], capture_output=True, text=True, check=True)
            devices = result.stdout.strip().split("\n")
            return devices if devices else ["No devices found."]
        except Exception as e:
            return [f"Error listing devices: {e}"]

    def get_device_info(self, device_udid: str) -> Dict[str, str]:
        """
        Get detailed information about a connected iOS device.

        Args:
            device_udid (str): The UDID of the device.

        Returns:
            Dict[str, str]: A dictionary containing device information.
        """
        if not self.libimobiledevice_available:
            return {"Error": "libimobiledevice tools are not installed or accessible."}
        
        try:
            result = subprocess.run([self.ideviceinfo_path, "-u", device_udid], capture_output=True, text=True, check=True)
            info_lines = result.stdout.strip().split("\n")
            info = {line.split(":")[0].strip(): line.split(":")[1].strip() for line in info_lines if ":" in line}
            return info
        except Exception as e:
            return {"Error": f"Error fetching device info for {device_udid}: {e}"}

    def install_app(self, device_udid: str, ipa_path: str) -> str:
        """
        Install an IPA file on a connected iOS device.

        Args:
            device_udid (str): The UDID of the device.
            ipa_path (str): The path to the IPA file.

        Returns:
            str: The result of the installation process.
        """
        if not self.libimobiledevice_available:
            return "libimobiledevice tools are not installed or accessible."
        
        try:
            result = subprocess.run([self.ideviceinstaller_path, "-u", device_udid, "-i", ipa_path], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error installing app: {e}"

    def uninstall_app(self, device_udid: str, package_name: str) -> str:
        """
        Uninstall an application from a connected iOS device.

        Args:
            device_udid (str): The UDID of the device.
            package_name (str): The bundle identifier of the application to uninstall.

        Returns:
            str: The result of the uninstallation process.
        """
        if not self.libimobiledevice_available:
            return "libimobiledevice tools are not installed or accessible."
        
        try:
            result = subprocess.run([self.ideviceinstaller_path, "-u", device_udid, "-U", package_name], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error uninstalling app: {e}"

    def read_device_logs(self, device_udid: Optional[str] = None) -> None:
        """
        Stream logs from a connected iOS device.

        Args:
            device_udid (Optional[str]): The UDID of the device. Streams logs from all devices if None.
        """
        if not self.libimobiledevice_available:
            print("libimobiledevice tools are not installed or accessible.")
            return
        
        try:
            command = [self.idevicesyslog_path]
            if device_udid:
                command.extend(["-u", device_udid])
            subprocess.run(command)
        except Exception as e:
            print(f"Error reading logs: {e}")

    def transfer_file_to_device(self, device_udid: str, local_path: str, remote_path: str) -> str:
        """
        Transfer a file to the iOS device. (Placeholder for actual implementation)

        Args:
            device_udid (str): The UDID of the device.
            local_path (str): The file path on the host system.
            remote_path (str): The destination path on the iOS device.

        Returns:
            str: The result of the file transfer.
        """
        return "File transfer functionality is currently not implemented for iOS devices."


# Example Usage
if __name__ == "__main__":
    ios_ops = iOSOperations()
    devices = ios_ops.list_connected_devices()
    print("Connected Devices:", devices)

    if devices and "No devices found." not in devices:
        device_udid = devices[0]
        print("\nDevice Info:")
        print(ios_ops.get_device_info(device_udid))

        print("\nTesting app installation...")
        print(ios_ops.install_app(device_udid, "example.ipa"))
