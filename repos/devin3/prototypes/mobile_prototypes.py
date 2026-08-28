# Devin/prototypes/mobile_prototypes.py
# Purpose: Prototype implementations for interacting with mobile devices (Android via ADB, conceptual Appium).

import logging
import os
import subprocess
import re
import time
import shlex
from typing import Dict, Any, List, Optional, Tuple, Union

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("MobilePrototypes")

# --- Mobile Interaction Class ---

class MobileInteractionPrototype:
    """
    Conceptual prototype for interacting with mobile devices.
    Primarily focuses on Android using ADB. Includes conceptual Appium placeholders.

    Requires ADB executable in PATH or specified. Requires target device setup (USB Debugging / Network ADB).
    """

    def __init__(self, adb_path: Optional[str] = "adb"):
        """
        Initializes the mobile interaction prototype.

        Args:
            adb_path (Optional[str]): Path to the ADB executable. Defaults to 'adb' assuming it's in PATH.
        """
        self.adb_path = adb_path
        self._check_adb()
        # Placeholder for Appium driver (conceptual)
        self.appium_driver = None
        logger.info(f"MobileInteractionPrototype initialized (ADB Path: {self.adb_path}).")

    def _check_adb(self):
        """Checks if ADB executable is found."""
        try:
            result = self._run_command([self.adb_path, "version"])
            if result and result['returncode'] == 0 and "Android Debug Bridge version" in result['stdout']:
                logger.info(f"ADB found: {result['stdout'].splitlines()[0]}")
                return True
            else:
                logger.error(f"ADB command '{self.adb_path}' execution failed or returned unexpected output. Check path and installation.")
                logger.error(f"Output: {result['stdout'] if result else 'N/A'}, Error: {result['stderr'] if result else 'N/A'}")
                # Raising an error might be appropriate in a real application
                # raise FileNotFoundError(f"ADB executable not found or failed at '{self.adb_path}'")
                return False
        except FileNotFoundError:
             logger.error(f"ADB executable not found at '{self.adb_path}'. Please install Android SDK Platform Tools and ensure ADB is in PATH or provide the correct path.")
             return False
        except Exception as e:
             logger.error(f"An unexpected error occurred while checking ADB: {e}")
             return False

    def _run_command(self, command: List[str], timeout: Optional[int] = 30) -> Optional[Dict[str, Union[int, str]]]:
        """
        Internal helper to run a generic command using subprocess.

        Args:
            command (List[str]): The command and arguments as a list.
            timeout (Optional[int]): Timeout in seconds. Defaults to 30.

        Returns:
            Optional[Dict[str, Union[int, str]]]: A dictionary with 'returncode', 'stdout', 'stderr', or None on error.
        """
        try:
            logger.debug(f"Executing command: {' '.join(shlex.quote(arg) for arg in command)}")
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False, # Don't raise exception on non-zero exit code, handle it manually
                timeout=timeout
            )
            return {
                "returncode": process.returncode,
                "stdout": process.stdout.strip(),
                "stderr": process.stderr.strip()
            }
        except FileNotFoundError:
            logger.error(f"Command not found: {command[0]}. Ensure it's installed and in PATH.")
            return None
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
            return None
        except Exception as e:
            logger.error(f"Failed to execute command {' '.join(command)}: {e}")
            return None

    def execute_adb_command(self, adb_args: List[str], device_id: Optional[str] = None, timeout: Optional[int] = 30) -> Optional[Dict[str, Union[int, str]]]:
        """
        Executes an ADB command, optionally targeting a specific device.

        Args:
            adb_args (List[str]): List of arguments to pass to ADB (e.g., ["shell", "ls"]).
            device_id (Optional[str]): The specific device ID to target (from 'adb devices').
                                         If None, targets the only connected device or fails if multiple are present.
            timeout (Optional[int]): Timeout in seconds.

        Returns:
            Optional[Dict[str, Union[int, str]]]: Result dict from _run_command, or None on error.
        """
        if not self.adb_path:
             logger.error("ADB path not configured.")
             return None

        base_command = [self.adb_path]
        if device_id:
            base_command.extend(["-s", device_id])

        full_command = base_command + adb_args
        result = self._run_command(full_command, timeout=timeout)

        if result and result['returncode'] != 0:
             # Log common ADB errors
             error_message = result['stderr'] if result['stderr'] else result['stdout'] # Sometimes errors go to stdout
             if "device offline" in error_message:
                  logger.warning(f"ADB command failed: Device '{device_id or 'default'}' is offline.")
             elif "device not found" in error_message or "device unauthorized" in error_message:
                  logger.warning(f"ADB command failed: Device '{device_id or 'default'}' not found or unauthorized. Check connection and authorization.")
             elif "more than one device/emulator" in error_message:
                  logger.warning("ADB command failed: More than one device connected. Please specify a device_id.")
             else:
                  logger.warning(f"ADB command failed with return code {result['returncode']}. Command: {' '.join(full_command)}")
                  logger.warning(f"Stderr: {result['stderr']}")
                  logger.warning(f"Stdout: {result['stdout']}")
        elif result and result['returncode'] == 0:
             logger.debug(f"ADB command successful: {' '.join(full_command)}")

        return result

    # --- Device Management ---

    def list_devices(self) -> List[Tuple[str, str]]:
        """
        Lists connected devices and their states (e.g., 'device', 'offline', 'unauthorized').

        Returns:
            List[Tuple[str, str]]: List of (device_id, state) tuples. Returns empty list on error.
        """
        logger.info("Listing connected ADB devices...")
        result = self.execute_adb_command(["devices"])
        devices = []
        if result and result['returncode'] == 0 and result['stdout']:
            lines = result['stdout'].strip().splitlines()
            # Output format: "List of devices attached\n<device_id>\t<state>\n..."
            for line in lines[1:]: # Skip header line
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    device_id, state = parts
                    devices.append((device_id, state))
                    logger.info(f"  - Found: {device_id} ({state})")
                elif line.strip(): # Log unexpected lines if any
                     logger.debug(f"  - Ignoring unexpected line in 'adb devices' output: {line}")

            if not devices:
                 logger.info("  - No devices found or issue parsing output.")
        else:
            logger.error("Failed to list devices or parse output.")
        return devices

    def get_device_properties(self, device_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Gets system properties from the device using 'adb shell getprop'.

        Args:
            device_id (Optional[str]): Target device ID.

        Returns:
            Optional[Dict[str, str]]: Dictionary of property key-value pairs, or None on error.
        """
        logger.info(f"Getting properties for device '{device_id or 'default'}'...")
        result = self.execute_adb_command(["shell", "getprop"], device_id=device_id, timeout=60)
        properties = {}
        if result and result['returncode'] == 0 and result['stdout']:
             # Output format: "[prop.name]: [value]\n..."
             lines = result['stdout'].strip().splitlines()
             for line in lines:
                  match = re.match(r'\[([^\]]+)\]:\s*\[(.*)\]', line)
                  if match:
                      key, value = match.groups()
                      properties[key.strip()] = value.strip()
             logger.info(f"  - Retrieved {len(properties)} properties.")
             return properties
        else:
             logger.error(f"Failed to get properties for device '{device_id or 'default'}'.")
             return None

    def get_device_ip(self, device_id: Optional[str] = None) -> Optional[str]:
         """
         Attempts to find the device's primary network IP address (usually wlan0).

         Args:
             device_id (Optional[str]): Target device ID.

         Returns:
             Optional[str]: The IP address string, or None if not found or on error.
         """
         logger.info(f"Getting IP address for device '{device_id or 'default'}'...")
         # Command often used: adb shell ip addr show wlan0 | grep "inet\s" | cut -d' ' -f6 | cut -d'/' -f1
         # Simpler approach for typical output:
         result = self.execute_adb_command(["shell", "ip", "addr", "show", "wlan0"], device_id=device_id)
         ip_address = None
         if result and result['returncode'] == 0 and result['stdout']:
              # Look for 'inet xxx.xxx.xxx.xxx/yy'
              match = re.search(r'inet\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/', result['stdout'])
              if match:
                   ip_address = match.group(1)
                   logger.info(f"  - Found IP address: {ip_address}")
              else:
                   logger.info("  - Could not parse IP address from 'ip addr show wlan0' output.")
         else:
              logger.error(f"Failed to get IP address info for device '{device_id or 'default'}'.")
         return ip_address

    # --- Application Management ---

    def install_app(self, apk_path: str, grant_permissions: bool = False, device_id: Optional[str] = None) -> bool:
        """
        Installs an application from an APK file onto the device.

        Args:
            apk_path (str): The local path to the .apk file.
            grant_permissions (bool): If True, adds the '-g' flag to grant all runtime permissions (Android 6+).
            device_id (Optional[str]): Target device ID.

        Returns:
            bool: True if installation command appears successful (returns 'Success'), False otherwise.
        """
        logger.info(f"Installing app from '{apk_path}' on device '{device_id or 'default'}'...")
        if not os.path.exists(apk_path):
            logger.error(f"APK file not found at: {apk_path}")
            return False

        adb_command = ["install"]
        if grant_permissions:
            adb_command.append("-g")
        adb_command.append(apk_path)

        # Installation can take time
        result = self.execute_adb_command(adb_command, device_id=device_id, timeout=300)

        if result and result['returncode'] == 0 and "Success" in result['stdout']:
             logger.info(f"App '{os.path.basename(apk_path)}' installed successfully.")
             return True
        else:
             logger.error(f"Failed to install app '{os.path.basename(apk_path)}'.")
             if result: logger.error(f"ADB Output: {result['stdout']}\nStderr: {result['stderr']}")
             return False

    def uninstall_app(self, package_name: str, keep_data: bool = False, device_id: Optional[str] = None) -> bool:
        """
        Uninstalls an application by its package name.

        Args:
            package_name (str): The package name (e.g., 'com.example.app').
            keep_data (bool): If True, adds the '-k' flag to keep the data and cache directories.
            device_id (Optional[str]): Target device ID.

        Returns:
            bool: True if uninstallation command appears successful (returns 'Success'), False otherwise.
        """
        logger.info(f"Uninstalling app '{package_name}' from device '{device_id or 'default'}'...")
        adb_command = ["uninstall"]
        if keep_data:
            adb_command.append("-k")
        adb_command.append(package_name)

        result = self.execute_adb_command(adb_command, device_id=device_id, timeout=120)

        if result and result['returncode'] == 0 and "Success" in result['stdout']:
             logger.info(f"App '{package_name}' uninstalled successfully.")
             return True
        else:
             # Check if it failed because the app wasn't installed
             if result and ("DELETE_FAILED_INTERNAL_ERROR" in result['stderr'] or "Failure" in result['stdout']) and "not found" in result['stdout'].lower():
                  logger.warning(f"App '{package_name}' might not be installed. Uninstallation command indicated failure but mentioned 'not found'.")
                  return False # Still technically a failure to uninstall
             logger.error(f"Failed to uninstall app '{package_name}'.")
             if result: logger.error(f"ADB Output: {result['stdout']}\nStderr: {result['stderr']}")
             return False

    def list_packages(self, filter_str: Optional[str] = None, device_id: Optional[str] = None) -> Optional[List[str]]:
        """
        Lists installed package names on the device, optionally filtering.

        Args:
            filter_str (Optional[str]): If provided, only packages containing this string will be returned.
            device_id (Optional[str]): Target device ID.

        Returns:
            Optional[List[str]]: List of package name strings, or None on error.
        """
        logger.info(f"Listing packages on device '{device_id or 'default'}' (Filter: {filter_str or 'None'})...")
        adb_command = ["shell", "pm", "list", "packages"]
        if filter_str:
             # Note: Filtering directly in adb command for better performance if possible
             # However, simple approach is to pipe within shell, or filter post-retrieval
             adb_command.extend(["|", "grep", filter_str]) # This works if shell supports pipe+grep
             # Safer, less efficient: Get all, then filter in Python
             # adb_command = ["shell", "pm", "list", "packages"]

        result = self.execute_adb_command(adb_command, device_id=device_id, timeout=120)
        packages = []

        if result and result['returncode'] == 0 and result['stdout']:
             lines = result['stdout'].strip().splitlines()
             for line in lines:
                  # Output format: "package:<package_name>"
                  if line.startswith("package:"):
                       pkg_name = line[len("package:"):].strip()
                       # Apply filter here if not done in the shell command
                       if filter_str is None or filter_str in pkg_name:
                           packages.append(pkg_name)
             logger.info(f"  - Found {len(packages)} matching packages.")
             return packages
        elif result and result['returncode'] == 0 and not result['stdout'] and filter_str:
             logger.info(f"  - No packages found matching filter '{filter_str}'.")
             return []
        else:
             logger.error(f"Failed to list packages for device '{device_id or 'default'}'.")
             return None

    def start_activity(self, activity_name: str, device_id: Optional[str] = None) -> bool:
        """
        Starts an activity using 'am start'.

        Args:
            activity_name (str): The component name (e.g., 'com.example.app/.MainActivity')
                                 or an intent specification string.
            device_id (Optional[str]): Target device ID.

        Returns:
            bool: True if the command executed without immediate error, False otherwise.
                  Note: This doesn't guarantee the activity started successfully visually.
        """
        logger.info(f"Starting activity '{activity_name}' on device '{device_id or 'default'}'...")
        # Using 'am start -n component' is usually preferred if component is known
        # Example: adb shell am start -n com.example.app/.MainActivity
        # Using 'am start <intent_spec>' allows more flexibility
        # Example: adb shell am start -a android.intent.action.VIEW -d http://example.com
        # This prototype assumes activity_name could be either, simple 'am start' used
        adb_command = ["shell", "am", "start", activity_name]

        result = self.execute_adb_command(adb_command, device_id=device_id)

        # 'am start' often prints "Starting: Intent { ... }" on success to stdout/stderr
        # Error messages like "Error: Activity class {...} does not exist." go to stderr usually.
        if result and (result['returncode'] == 0 or "Warning: Activity not started" not in result['stderr']):
            # Success is tricky to define perfectly, return True if command ran okay
            # Check stderr for common failure indicators if needed.
            if "Error type" in result['stderr'] or "does not exist" in result['stderr']:
                 logger.error(f"Failed to start activity '{activity_name}'. Error indicated in stderr.")
                 logger.error(f"Stderr: {result['stderr']}")
                 return False
            logger.info(f"Activity start command for '{activity_name}' executed.")
            return True
        else:
             logger.error(f"Failed to execute start activity command for '{activity_name}'.")
             if result: logger.error(f"Stderr: {result['stderr']}")
             return False

    def force_stop_app(self, package_name: str, device_id: Optional[str] = None) -> bool:
        """
        Force stops an application using 'am force-stop'. Requires root on newer Android versions for user apps.

        Args:
            package_name (str): The package name to stop.
            device_id (Optional[str]): Target device ID.

        Returns:
            bool: True if the command executed without error return code, False otherwise.
        """
        logger.info(f"Force stopping app '{package_name}' on device '{device_id or 'default'}'...")
        adb_command = ["shell", "am", "force-stop", package_name]
        result = self.execute_adb_command(adb_command, device_id=device_id)

        # This command usually doesn't output anything on success.
        if result and result['returncode'] == 0:
             logger.info(f"Force stop command for '{package_name}' executed successfully.")
             return True
        else:
             # Check if failure was due to permissions (common on non-rooted devices for user apps)
             if result and ("permission" in result['stderr'].lower() or "requires root" in result['stderr'].lower()):
                  logger.warning(f"Could not force stop '{package_name}'. Insufficient permissions (root may be required).")
             else:
                  logger.error(f"Failed to execute force stop command for '{package_name}'.")
                  if result: logger.error(f"Stderr: {result['stderr']}")
             return False

    # --- Input Events ---

    def send_key_event(self, keycode_or_event: Union[int, str], device_id: Optional[str] = None) -> bool:
        """
        Sends a key event to the device using 'input keyevent'.

        Args:
            keycode_or_event (Union[int, str]): Android keycode (integer) or a common event name
                                                (e.g., "HOME", "BACK", "DPAD_UP", "ENTER", "VOLUME_UP").
            device_id (Optional[str]): Target device ID.

        Returns:
            bool: True if the command executed without error return code, False otherwise.
        """
        event_code_str = str(keycode_or_event)
        logger.info(f"Sending key event '{event_code_str}' to device '{device_id or 'default'}'...")
        adb_command = ["shell", "input", "keyevent", event_code_str]
        result = self.execute_adb_command(adb_command, device_id=device_id)

        # keyevent usually returns 0 on success, no output
        if result and result['returncode'] == 0:
            logger.info(f"Key event '{event_code_str}' sent successfully.")
            return True
        else:
            logger.error(f"Failed to send key event '{event_code_str}'.")
            if result: logger.error(f"Stderr: {result['stderr']}")
            return False

    def send_tap(self, x: int, y: int, device_id: Optional[str] = None) -> bool:
        """
        Sends a tap event at the specified coordinates using 'input tap'.

        Args:
            x (int): X coordinate.
            y (int): Y coordinate.
            device_id (Optional[str]): Target device ID.

        Returns:
            bool: True if the command executed without error return code, False otherwise.
        """
        logger.info(f"Sending tap at ({x}, {y}) to device '{device_id or 'default'}'...")
        adb_command = ["shell", "input", "tap", str(x), str(y)]
        result = self.execute_adb_command(adb_command, device_id=device_id)

        # tap usually returns 0 on success, no output
        if result and result['returncode'] == 0:
            logger.info(f"Tap at ({x}, {y}) sent successfully.")
            return True
        else:
            logger.error(f"Failed to send tap at ({x}, {y}).")
            if result: logger.error(f"Stderr: {result['stderr']}")
            return False

    def send_swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300, device_id: Optional[str] = None) -> bool:
        """
        Sends a swipe event from (x1, y1) to (x2, y2) using 'input swipe'.

        Args:
            x1 (int): Start X coordinate.
            y1 (int): Start Y coordinate.
            x2 (int): End X coordinate.
            y2 (int): End Y coordinate.
            duration_ms (int): Duration of the swipe in milliseconds. Defaults to 300.
            device_id (Optional[str]): Target device ID.

        Returns:
            bool: True if the command executed without error return code, False otherwise.
        """
        logger.info(f"Sending swipe from ({x1}, {y1}) to ({x2}, {y2}) over {duration_ms}ms on device '{device_id or 'default'}'...")
        adb_command = ["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)]
        result = self.execute_adb_command(adb_command, device_id=device_id)

        # swipe usually returns 0 on success, no output
        if result and result['returncode'] == 0:
            logger.info(f"Swipe from ({x1}, {y1}) to ({x2}, {y2}) sent successfully.")
            return True
        else:
            logger.error(f"Failed to send swipe.")
            if result: logger.error(f"Stderr: {result['stderr']}")
            return False

    def send_text(self, text: str, device_id: Optional[str] = None) -> bool:
        """
        Sends text input using 'input text'. Best for simple ASCII text.
        May not handle special characters, spaces correctly, or work with all keyboard types.

        Args:
            text (str): The text string to send. Spaces might need replacing with '%s'.
            device_id (Optional[str]): Target device ID.

        Returns:
            bool: True if the command executed without error return code, False otherwise.
        """
        # ADB 'input text' is tricky. Spaces must often be replaced with %s.
        # Special characters are often not supported directly.
        processed_text = text.replace(" ", "%s")
        logger.info(f"Sending text '{text}' (as '{processed_text}') to device '{device_id or 'default'}'...")
        if " " in text:
             logger.warning("Spaces in text sent via 'adb input text' might not work as expected; replaced with '%s'. Consider key events for complex input.")
        if not processed_text.isascii():
             logger.warning("Non-ASCII characters sent via 'adb input text' might not work correctly.")

        adb_command = ["shell", "input", "text", processed_text]
        result = self.execute_adb_command(adb_command, device_id=device_id)

        # text usually returns 0 on success, no output
        if result and result['returncode'] == 0:
            logger.info(f"Text input command for '{text}' executed.")
            return True
        else:
            logger.error(f"Failed to send text input '{text}'.")
            if result: logger.error(f"Stderr: {result['stderr']}")
            return False

    # --- File Transfer ---

    def pull_file(self, remote_path: str, local_path: str, device_id: Optional[str] = None) -> bool:
        """
        Copies a file from the device to the local machine using 'adb pull'.

        Args:
            remote_path (str): Path to the file on the device.
            local_path (str): Path to save the file locally.
            device_id (Optional[str]): Target device ID.

        Returns:
            bool: True if the command executed successfully, False otherwise.
        """
        logger.info(f"Pulling file '{remote_path}' from device '{device_id or 'default'}' to '{local_path}'...")
        adb_command = ["pull", remote_path, local_path]
        result = self.execute_adb_command(adb_command, device_id=device_id, timeout=300) # Allow more time for transfers

        # 'adb pull' output includes transfer speed on success, errors on stderr
        if result and result['returncode'] == 0:
             # Check if file exists locally now
             if os.path.exists(local_path):
                   logger.info(f"File pulled successfully to '{local_path}'.")
                   return True
             else:
                   # Command succeeded but file missing? Might be edge case or ADB quirk.
                   logger.warning(f"ADB pull command succeeded but local file '{local_path}' not found. Output: {result['stdout']}")
                   return False
        else:
             logger.error(f"Failed to pull file '{remote_path}'.")
             if result: logger.error(f"Stderr: {result['stderr']}")
             return False

    def push_file(self, local_path: str, remote_path: str, device_id: Optional[str] = None) -> bool:
        """
        Copies a file from the local machine to the device using 'adb push'.

        Args:
            local_path (str): Path to the local file.
            remote_path (str): Path to save the file on the device.
            device_id (Optional[str]): Target device ID.

        Returns:
            bool: True if the command executed successfully, False otherwise.
        """
        logger.info(f"Pushing file '{local_path}' to device '{device_id or 'default'}' at '{remote_path}'...")
        if not os.path.exists(local_path):
            logger.error(f"Local file not found: {local_path}")
            return False

        adb_command = ["push", local_path, remote_path]
        result = self.execute_adb_command(adb_command, device_id=device_id, timeout=300) # Allow more time for transfers

        # 'adb push' output includes transfer speed on success, errors on stderr
        if result and result['returncode'] == 0:
             logger.info(f"File pushed successfully to '{remote_path}'.")
             # We can't easily verify the push like we can verify the pull locally
             return True
        else:
             logger.error(f"Failed to push file to '{remote_path}'.")
             if result: logger.error(f"Stderr: {result['stderr']}")
             return False

    # --- Screenshot ---

    def take_screenshot(self, local_path: str, device_id: Optional[str] = None) -> bool:
        """
        Takes a screenshot on the device and saves it to a local path.

        Args:
            local_path (str): Path to save the screenshot locally (e.g., '/tmp/screenshot.png').
            device_id (Optional[str]): Target device ID.

        Returns:
            bool: True if successful, False otherwise.
        """
        logger.info(f"Taking screenshot on device '{device_id or 'default'}' and saving to '{local_path}'...")
        # Define a temporary path on the device (sdcard is usually accessible)
        remote_temp_path = "/sdcard/devin_screenshot_temp.png"
        adb_command_capture = ["shell", "screencap", "-p", remote_temp_path]

        result_capture = self.execute_adb_command(adb_command_capture, device_id=device_id, timeout=60)

        if not result_capture or result_capture['returncode'] != 0:
            logger.error(f"Failed to capture screenshot on device.")
            if result_capture: logger.error(f"Stderr: {result_capture['stderr']}")
            return False

        logger.info(f"  - Screenshot captured to '{remote_temp_path}' on device.")

        # Pull the screenshot file
        if not self.pull_file(remote_temp_path, local_path, device_id=device_id):
            logger.error(f"Failed to pull screenshot file from '{remote_temp_path}'.")
            # Attempt cleanup even if pull failed
            self.execute_adb_command(["shell", "rm", remote_temp_path], device_id=device_id)
            return False

        logger.info(f"  - Screenshot pulled successfully to '{local_path}'.")

        # Clean up the temporary file on the device
        logger.info(f"  - Cleaning up temporary file '{remote_temp_path}' on device...")
        result_cleanup = self.execute_adb_command(["shell", "rm", remote_temp_path], device_id=device_id)
        if not result_cleanup or result_cleanup['returncode'] != 0:
             logger.warning(f"Failed to clean up temporary screenshot file '{remote_temp_path}' on device.")
        else:
             logger.info("  - Cleanup successful.")

        return True

    # --- Shell Command Execution ---

    def run_shell_command(self, shell_cmd: str, device_id: Optional[str] = None, timeout: Optional[int] = 60) -> Optional[Dict[str, Union[int, str]]]:
        """
        Executes an arbitrary command on the device's shell using 'adb shell'.

        *** SECURITY WARNING: Executing arbitrary shell commands can be dangerous. ***
        *** Use with extreme caution. Validate inputs if commands are dynamic. ***

        Args:
            shell_cmd (str): The shell command to execute (e.g., "ls /sdcard/").
            device_id (Optional[str]): Target device ID.
            timeout (Optional[int]): Timeout in seconds.

        Returns:
            Optional[Dict[str, Union[int, str]]]: Result dict including 'returncode', 'stdout', 'stderr', or None on error.
                                                  Note: stdout/stderr are from the *device's* shell command.
        """
        logger.warning(f"Executing potentially dangerous shell command on device '{device_id or 'default'}': {shell_cmd}")
        # Note: Using shlex.split for the shell command itself is generally NOT correct here,
        # as 'adb shell' takes the command as a single string argument (or multiple args interpreted by device shell).
        # Pass the command string directly. If the command itself needs complex quoting for the *device's* shell,
        # it must be handled within the shell_cmd string itself.
        adb_command = ["shell", shell_cmd]
        result = self.execute_adb_command(adb_command, device_id=device_id, timeout=timeout)

        if result:
             logger.info(f"Shell command finished with return code {result['returncode']}.")
             logger.debug(f"Shell stdout:\n{result['stdout']}")
             logger.debug(f"Shell stderr:\n{result['stderr']}")
        else:
             logger.error(f"Failed to execute shell command.")

        return result

    # --- Appium Placeholders (Conceptual) ---

    def connect_appium_placeholder(self, server_url: str = 'http://localhost:4723/wd/hub', capabilities: Optional[Dict] = None) -> bool:
        """
        Conceptual placeholder for connecting to an Appium server.
        Requires Appium server running and 'appium-python-client' installed.
        """
        logger.info(f"Conceptually connecting to Appium server at {server_url}...")
        logger.warning("This requires a running Appium server and 'appium-python-client'.")

        if capabilities is None:
            # Example capabilities for an Android device
            capabilities = {
                "platformName": "Android",
                "appium:deviceName": "Android Emulator", # Or actual device name/UDID
                "appium:automationName": "UiAutomator2",
                # "appium:appPackage": "com.example.app", # Optionally specify app to launch
                # "appium:appActivity": ".MainActivity",
            }
            logger.info(f"  - Using default conceptual capabilities: {capabilities}")

        # --- Conceptual: from appium import webdriver ---
        # try:
        #     from appium import webdriver
        #     self.appium_driver = webdriver.Remote(server_url, capabilities)
        #     logger.info("Conceptual Appium driver initialized.")
        #     # Add implicit wait (conceptual)
        #     # self.appium_driver.implicitly_wait(10)
        #     return True
        # except ImportError:
        #     logger.error("Appium Python client not installed ('pip install Appium-Python-Client').")
        #     return False
        # except Exception as e:
        #     logger.error(f"Failed to connect to Appium server: {e}")
        #     return False
        # --- End Conceptual ---

        # Simulate connection
        self.appium_driver = {"session_id": "dummy-session-123"} # Simulate driver object
        logger.info("  - Conceptual Appium connection successful.")
        return True

    def disconnect_appium_placeholder(self):
        """Conceptual placeholder for disconnecting from the Appium server."""
        logger.info("Conceptually disconnecting from Appium server...")
        if self.appium_driver:
            # --- Conceptual: self.appium_driver.quit() ---
            self.appium_driver = None
            logger.info("  - Conceptual Appium driver quit.")
        else:
            logger.info("  - No active conceptual Appium connection.")

    def find_element_appium_placeholder(self, by: str, value: str) -> Optional[Any]:
        """
        Conceptual placeholder for finding an element using Appium locators.
        Requires an active Appium connection.
        """
        if not self.appium_driver:
             logger.warning("Cannot find element: Conceptual Appium driver not connected.")
             return None
        logger.info(f"Conceptually finding Appium element by {by} = '{value}'...")
        # --- Conceptual: from appium.webdriver.common.appiumby import AppiumBy ---
        # try:
        #     # Example using AppiumBy:
        #     # if by == "id": locator_strategy = AppiumBy.ID
        #     # elif by == "xpath": locator_strategy = AppiumBy.XPATH
        #     # ... other strategies ...
        #     # else: raise ValueError("Unsupported locator strategy")
        #     # element = self.appium_driver.find_element(by=locator_strategy, value=value)
        #     # logger.info("  - Conceptual element found.")
        #     # return element # Return the actual WebElement object
        # except Exception as e:
        #     logger.error(f"Conceptual error finding element: {e}")
        #     return None
        # --- End Conceptual ---
        # Simulate finding an element
        dummy_element = {"element_id": f"dummy-{by}-{value}", "by": by, "value": value}
        logger.info(f"  - Found conceptual element: {dummy_element}")
        return dummy_element

    def click_element_appium_placeholder(self, element_info: Any) -> bool:
        """Conceptual placeholder for clicking an Appium element."""
        if not self.appium_driver: return False
        if not element_info: return False
        logger.info(f"Conceptually clicking Appium element: {element_info}")
        # --- Conceptual: element_info.click() --- # where element_info is a WebElement
        logger.info("  - Conceptual click performed.")
        return True

    def send_keys_appium_placeholder(self, element_info: Any, text: str) -> bool:
        """Conceptual placeholder for sending keys to an Appium element."""
        if not self.appium_driver: return False
        if not element_info: return False
        logger.info(f"Conceptually sending keys '{text}' to Appium element: {element_info}")
        # --- Conceptual: element_info.send_keys(text) ---
        logger.info("  - Conceptual keys sent.")
        return True


# --- Main Execution Block ---
if __name__ == "__main__":
    print("=================================================")
    print("=== Running Mobile Interaction Prototypes ===")
    print("=================================================")
    print("(Note: Relies on ADB in PATH, connected/authorized device, conceptual implementations)")
    print("*** Security Warning: 'run_shell_command' can be dangerous! ***")

    # Use default adb path assumption
    mobile_controller = MobileInteractionPrototype()

    print("\n--- ADB Device Listing ---")
    devices = mobile_controller.list_devices()

    if not devices:
        print("\nNo ADB devices found or accessible. Skipping device-specific examples.")
        # Optionally run Appium conceptual tests even without physical device listing
    else:
        # Use the first listed device for examples
        target_device_id = devices[0][0]
        print(f"\n--- Running Examples on Device: {target_device_id} ---")

        # Example: Take Screenshot
        screenshot_path = f"/tmp/devin_mobile_screenshot_{int(time.time())}.png"
        print(f"\n1. Taking Screenshot (saving to {screenshot_path})...")
        success = mobile_controller.take_screenshot(screenshot_path, device_id=target_device_id)
        if success and os.path.exists(screenshot_path):
            print(f"   Screenshot saved successfully to {screenshot_path}")
            # os.remove(screenshot_path) # Optional: remove after check
        else:
            print("   Failed to take or save screenshot.")

        # Example: Send Key Event (HOME)
        print("\n2. Sending HOME key event...")
        mobile_controller.send_key_event("HOME", device_id=target_device_id)
        time.sleep(1) # Give time for UI to react

        # Example: List specific packages (e.g., settings)
        print("\n3. Listing packages containing 'settings'...")
        settings_packages = mobile_controller.list_packages("settings", device_id=target_device_id)
        if settings_packages is not None:
            print(f"   Found {len(settings_packages)} settings-related packages: {settings_packages[:5]}...") # Print first 5
        else:
            print("   Failed to list packages.")

        # Example: Run a safe shell command
        print("\n4. Running safe shell command 'ls /sdcard/'...")
        shell_result = mobile_controller.run_shell_command("ls /sdcard/", device_id=target_device_id)
        if shell_result:
            print(f"   Shell command stdout (first 100 chars): {shell_result['stdout'][:100]}...")
        else:
            print("   Failed to run shell command.")

        # Example: Get Device IP (WLAN)
        print("\n5. Getting device WLAN IP address...")
        ip = mobile_controller.get_device_ip(device_id=target_device_id)
        if ip:
            print(f"   Device IP: {ip}")
        else:
            print("   Could not retrieve device IP.")


    print("\n--- Conceptual Appium Interactions ---")
    # Conceptual: Connect
    if mobile_controller.connect_appium_placeholder():
        # Conceptual: Find and interact
        element = mobile_controller.find_element_appium_placeholder(by="xpath", value="//android.widget.Button[@text='Login']")
        if element:
            mobile_controller.click_element_appium_placeholder(element)
            keys_element = mobile_controller.find_element_appium_placeholder(by="id", value="com.example.app:id/username")
            if keys_element:
                mobile_controller.send_keys_appium_placeholder(keys_element, "testuser")

        # Conceptual: Disconnect
        mobile_controller.disconnect_appium_placeholder()
    else:
        print("   Skipping Appium examples (conceptual connection failed).")

    print("\n=================================================")
    print("=== Mobile Interaction Prototypes Complete ===")
    print("=================================================")
