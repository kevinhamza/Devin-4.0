# Devin/tests/mobile_integration_tests.py
# Purpose: An integration test suite for the mobile control pipeline, verifying
#          the client-server communication for controlling Android devices.

import unittest
import threading
import time
import requests
from unittest.mock import patch, MagicMock

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

_import_error = None

try:
    from servers.mobile_integration_server import MobileIntegrationServer
    from modules.mobile_integration_module import MobileFacade
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    _import_error = e

# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)


@unittest.skipUnless(DEPS_AVAILABLE, f"Skipping mobile tests, dependency missing: {_import_error}")
class TestMobileIntegrationPipeline(unittest.TestCase):
    """
    Tests the full client-server pipeline for the MobileIntegrationServer.
    """
    server_thread = None
    server_port = 5008 # Use a unique port for testing
    server_url = f"http://127.0.0.1:{server_port}"
    
    @classmethod
    def setUpClass(cls):
        """Starts the MobileIntegrationServer in a background thread."""
        cls.server_instance = MobileIntegrationServer()
        
        # Patch the subprocess.run call within the server's module
        cls.patcher = patch('servers.mobile_integration_server.subprocess.run')
        cls.mock_subprocess_run = cls.patcher.start()

        cls.server_thread = threading.Thread(
            target=cls.server_instance.run,
            args=("127.0.0.1", cls.server_port),
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(1) # Give the server a moment to start up

    @classmethod
    def tearDownClass(cls):
        """Stops the server and the patcher after all tests have run."""
        cls.patcher.stop()
        try:
            requests.post(f"{cls.server_url}/shutdown")
        except requests.ConnectionError:
            pass
        if cls.server_thread:
            cls.server_thread.join(timeout=2)

    def setUp(self):
        """Create a new facade instance for each test and reset mocks."""
        self.facade = MobileFacade(base_url=self.server_url)
        self.mock_subprocess_run.reset_mock()

    def test_list_devices_workflow(self):
        """
        Verify the full workflow for listing connected devices.
        """
        print("\n\n--- Testing '/devices' Endpoint Workflow ---")
        # 1. Configure the mock to simulate the output of `adb devices`
        mock_output = "List of devices attached\nemulator-5554\tdevice\n12345ABC\toffline\n"
        self.mock_subprocess_run.return_value = MagicMock(stdout=mock_output, stderr="", returncode=0)
        
        # 2. Call the facade, which calls the server, which calls the mock
        devices = self.facade.list_connected_devices()
        
        # 3. Verify the subprocess call
        self.mock_subprocess_run.assert_called_once_with(
            ['adb', 'devices'], capture_output=True, text=True, check=False
        )
        print("  [SUCCESS] Server correctly called 'adb devices'.")

        # 4. Verify the facade's parsed output
        expected_devices = [
            {'serial': 'emulator-5554', 'status': 'device'},
            {'serial': '12345ABC', 'status': 'offline'}
        ]
        self.assertEqual(devices, expected_devices)
        print("  [SUCCESS] Facade correctly parsed the JSON response from the server.")

    def test_shell_command_workflow(self):
        """
        Verify the full workflow for executing a shell command on a specific device.
        """
        print("\n\n--- Testing '/shell' Endpoint Workflow ---")
        # 1. Configure the mock to simulate the output of a `getprop` command
        device_id = "emulator-5554"
        command = "getprop ro.product.model"
        mock_output = "Pixel 8 Pro\n"
        self.mock_subprocess_run.return_value = MagicMock(stdout=mock_output, stderr="", returncode=0)
        
        # 2. Call the facade
        result = self.facade.run_shell_command(device_id, command)
        
        # 3. Verify the subprocess call
        expected_adb_command = ['adb', '-s', device_id, 'shell', 'getprop', 'ro.product.model']
        self.mock_subprocess_run.assert_called_once_with(
            expected_adb_command, capture_output=True, text=True, check=False
        )
        print("  [SUCCESS] Server correctly constructed and called the targeted 'adb shell' command.")
        
        # 4. Verify the facade's result
        self.assertEqual(result, "Pixel 8 Pro")
        print("  [SUCCESS] Facade correctly returned the command's stdout.")

    def test_server_handles_adb_command_failure(self):
        """
        Verify that the server returns a 500 error if the underlying adb command fails.
        """
        print("\n\n--- Testing Server Error Handling for Failed ADB Command ---")
        # 1. Configure the mock to simulate a failed adb command
        device_id = "unknown-device"
        command = "ls"
        mock_error = "error: device not found"
        self.mock_subprocess_run.return_value = MagicMock(stdout="", stderr=mock_error, returncode=1)
        
        # 2. Call the server directly with `requests` to check the HTTP status code
        response = requests.post(f"{self.server_url}/shell", json={"device_id": device_id, "command": command})
        
        # 3. Verify the HTTP response
        self.assertEqual(response.status_code, 500)
        self.assertIn(mock_error, response.json()['error'])
        print("  [SUCCESS] Server correctly returned a 500 Internal Server Error.")

        # 4. Verify the facade handles the error by returning None
        facade_result = self.facade.run_shell_command(device_id, command)
        self.assertIsNone(facade_result)
        print("  [SUCCESS] Facade correctly returned None on server error.")


if __name__ == '__main__':
    unittest.main()
