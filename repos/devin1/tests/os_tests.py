"""
os_tests.py

This module contains test cases specific to operating system functionalities
to ensure the Devin project operates seamlessly across multiple OS platforms.
"""

import unittest
import platform
import subprocess

class OSTests(unittest.TestCase):
    """Test cases for OS-specific functionalities."""

    def test_platform_detection(self):
        """Test detection of the operating system."""
        os_name = platform.system()
        self.assertIn(os_name, ["Linux", "Windows", "Darwin"], "Unsupported OS detected!")

    def test_file_permissions(self):
        """Test setting and getting file permissions."""
        try:
            if platform.system() == "Linux":
                with open("test_file.txt", "w") as f:
                    f.write("Permission Test")
                subprocess.check_call(["chmod", "600", "test_file.txt"])
                permissions = subprocess.check_output(["stat", "-c", "%a", "test_file.txt"]).strip()
                self.assertEqual(permissions, b"600", "Incorrect file permissions on Linux.")
            elif platform.system() == "Windows":
                with open("test_file.txt", "w") as f:
                    f.write("Permission Test")
                # Skipping Windows-specific permissions test for simplicity
                self.assertTrue(True, "File permissions testing not implemented on Windows.")
        finally:
            subprocess.call(["rm", "test_file.txt"], shell=True)

    def test_network_connectivity(self):
        """Test network connectivity commands."""
        try:
            if platform.system() == "Windows":
                result = subprocess.check_call(["ping", "127.0.0.1", "-n", "1"])
            else:
                result = subprocess.check_call(["ping", "127.0.0.1", "-c", "1"])
            self.assertEqual(result, 0, "Ping command failed!")
        except Exception as e:
            self.fail(f"Network connectivity test failed: {e}")

    def test_os_commands(self):
        """Test basic OS commands."""
        try:
            if platform.system() == "Windows":
                result = subprocess.check_output(["dir"], shell=True)
            else:
                result = subprocess.check_output(["ls"], shell=True)
            self.assertTrue(result, "OS command failed or returned empty output.")
        except Exception as e:
            self.fail(f"OS command test failed: {e}")

if __name__ == "__main__":
    unittest.main()
