# Devin/reality_engine/physical_world/iot_controller.py
# Purpose: A controller for discovering and managing Internet of Things (IoT)
#          devices, specifically focusing on the Tuya platform.

import logging
import json
from pathlib import Path
from typing import Dict, Optional, Any

try:
    import tinytuya
    TINUTUYA_AVAILABLE = True
except ImportError:
    TINUTUYA_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("IoTController")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class IoTController:
    """
    Manages discovery and control of local Tuya-based IoT devices.
    """
    def __init__(self, config_path: Path = Path("devices.json")):
        if not TINUTUYA_AVAILABLE:
            raise ImportError("The 'tinytuya' library is required. 'pip install tinytuya'")
        
        self.config_path = config_path
        self.devices = self._load_config()
        logger.info(f"IoT Controller initialized. Loaded {len(self.devices)} device(s) from config.")

    def _load_config(self) -> Dict[str, Any]:
        """Loads device credentials from the JSON config file."""
        if self.config_path.is_file():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {}

    def _get_device_handle(self, device_name: str) -> Optional[tinytuya.Device]:
        """Looks up a device by name and returns a tinytuya Device object."""
        device_info = self.devices.get(device_name)
        if not device_info:
            logger.error(f"Device '{device_name}' not found in '{self.config_path}'.")
            return None
            
        try:
            device_type = device_info.get("type", "outlet") # Default to outlet/switch
            if device_type == "bulb":
                handle = tinytuya.BulbDevice(
                    dev_id=device_info['id'],
                    address=device_info['ip'],
                    local_key=device_info['key']
                )
            else: # Outlet, Switch, etc.
                 handle = tinytuya.OutletDevice(
                    dev_id=device_info['id'],
                    address=device_info['ip'],
                    local_key=device_info['key']
                )
            handle.set_version(3.3) # Common protocol version
            return handle
        except KeyError as e:
            logger.error(f"Device '{device_name}' is missing required configuration key: {e}")
            return None

    @staticmethod
    def discover_devices(scan_duration: int = 10):
        """Scans the local network to discover Tuya devices."""
        logger.warning(f"Starting network scan for Tuya devices ({scan_duration} seconds)...")
        try:
            devices = tinytuya.scanner.scan(scan_duration)
            if not devices:
                logger.info("No Tuya devices found on the local network.")
                return
            
            print("\n--- Discovered Devices ---")
            for ip, device in devices.items():
                print(f"  IP Address: {ip}")
                print(f"    ID:    {device.get('gwId')}")
                print(f"    Product Key: {device.get('productKey')}")
                print(f"    Version: {device.get('version')}")
            print("\nUse the 'ID' and 'IP' to configure your 'devices.json' file.")

        except Exception as e:
            logger.error(f"Device discovery failed. Ensure you are on the correct network. Error: {e}")

    def get_status(self, device_name: str) -> Optional[Dict]:
        """Gets the full status of a configured device."""
        device = self._get_device_handle(device_name)
        if not device: return None
        
        try:
            status = device.status()
            logger.info(f"Status for '{device_name}': {status}")
            return status
        except Exception as e:
            logger.error(f"Failed to get status for '{device_name}': {e}")
            return None

    def turn_on(self, device_name: str):
        """Turns a device on."""
        logger.info(f"Turning ON '{device_name}'...")
        device = self._get_device_handle(device_name)
        if device: device.turn_on()

    def turn_off(self, device_name: str):
        """Turns a device off."""
        logger.info(f"Turning OFF '{device_name}'...")
        device = self._get_device_handle(device_name)
        if device: device.turn_off()
        
    def set_color(self, device_name: str, r: int, g: int, b: int):
        """Sets the color of an RGB-capable smart bulb."""
        logger.info(f"Setting color of '{device_name}' to ({r},{g},{b})...")
        device = self._get_device_handle(device_name)
        if device and isinstance(device, tinytuya.BulbDevice):
            device.set_colour(r, g, b)
        elif not isinstance(device, tinytuya.BulbDevice):
            logger.error(f"Device '{device_name}' is not configured as a bulb and does not support color changes.")


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== IoT Smart Device Controller Prototype 💡🔌 ===")
    print("=========================================================")
    print("!!! PREREQUISITE: This tool requires a 'devices.json' file with your device credentials. !!!")
    print("A dummy file will be created as a template.")
    
    if not TINUTUYA_AVAILABLE:
        print("\nERROR: The 'tinytuya' library is required. Please run: pip install tinytuya")
    else:
        # 1. Create a dummy config file for the demo
        dummy_config_path = Path("devices.json")
        dummy_config_content = {
            "living_room_light": {
                "id": "0123456789abcdefghij",
                "ip": "192.168.1.100",
                "key": "0123456789abcdef",
                "type": "bulb"
            },
            "desk_fan": {
                "id": "fedcba9876543210jihg",
                "ip": "192.168.1.101",
                "key": "fedcba9876543210",
                "type": "outlet"
            }
        }
        with open(dummy_config_path, 'w') as f:
            json.dump(dummy_config_content, f, indent=2)

        try:
            # 2. Demonstrate device discovery
            print("\n--- 1. Device Discovery ---")
            print("Running a 5-second scan to find devices on your network.")
            print("This can help you find the 'id' and 'ip' for your config file.")
            IoTController.discover_devices(scan_duration=5)
            
            # 3. Demonstrate control (will fail safely with dummy data)
            print("\n--- 2. Simulated Device Control ---")
            print("Initializing controller with the dummy 'devices.json' file.")
            print("The following commands will fail, but they demonstrate how the tool works.")
            
            controller = IoTController(config_path=dummy_config_path)
            try:
                controller.turn_on("desk_fan")
                controller.set_color("living_room_light", 255, 0, 0) # Set to red
            except Exception as e:
                logger.info(f"Safely caught expected error from dummy credentials: {type(e).__name__}")

            print("\nTo use this for real, you must:")
            print("  1. Use a tool like 'tinytuya-cli wizard' to get your device's local key.")
            print(f"  2. Populate '{dummy_config_path}' with the real id, ip, and key.")

        finally:
            # 4. Clean up the dummy file
            if dummy_config_path.exists():
                dummy_config_path.unlink()

    print("\n=========================================================")
    print("=== IoT Controller Prototype Complete ===")
    print("=========================================================")
