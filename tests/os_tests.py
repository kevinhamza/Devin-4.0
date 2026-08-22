# Devin/tests/os_tests.py
# Purpose: An integration test suite for the OS operations stack, verifying that
#          the UniversalOSOperator correctly dispatches to the right sub-module.

import unittest
from unittest.mock import patch, MagicMock

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

_import_error = None

try:
    from modules.os_operations.universal_operations import UniversalOSOperator
    import numpy as np
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)


@unittest.skipUnless(DEVIN_CORE_AVAILABLE, f"Skipping OS tests, dependency missing: {_import_error}")
class TestUniversalOSOperator(unittest.TestCase):
    """
    Tests the UniversalOSOperator's ability to correctly initialize and
    delegate to the appropriate platform-specific modules.
    """

    # We patch the low-level compatibility modules to isolate our test
    # to the UniversalOSOperator's logic and avoid hardware dependencies.
    @patch('modules.os_operations.universal_operations.Win32APIWrapper')
    @patch('modules.os_operations.universal_operations.LinuxSyscallWrapper')
    @patch('modules.os_operations.universal_operations.MetalWrapper')
    @patch('platform.system', return_value='Windows')
    def test_initialization_and_dispatch_on_windows(self, mock_platform, mock_metal, mock_linux, mock_win32):
        """Verify the operator loads the correct modules when pretending to be on Windows."""
        print("\n\n--- Testing Dispatch Logic on a MOCKED Windows OS ---")
        
        # Instantiate the operator *inside* the patched context
        operator = UniversalOSOperator()
        
        # 1. Test Initialization
        self.assertEqual(operator.os_type, 'Windows')
        mock_win32.assert_called_once()
        mock_linux.assert_not_called()
        mock_metal.assert_not_called()
        self.assertIsNotNone(operator.platform_api)
        self.assertIsNone(operator.gpu_accelerator)
        print("  [SUCCESS] Correctly initialized Win32APIWrapper for Windows.")
        
        # 2. Test Method Dispatch
        # Get a handle to the *instance* of the mock that the operator is holding
        mock_win32_instance = operator.platform_api
        mock_win32_instance.read_registry_key.return_value = "Windows Test Build"
        
        # Call the high-level method
        operator.get_detailed_os_version()
        
        # Assert that the correct low-level method was called
        mock_win32_instance.read_registry_key.assert_called()
        print("  [SUCCESS] Correctly dispatched get_detailed_os_version to the Win32 module.")

    @patch('modules.os_operations.universal_operations.Win32APIWrapper')
    @patch('modules.os_operations.universal_operations.LinuxSyscallWrapper')
    @patch('modules.os_operations.universal_operations.MetalWrapper')
    @patch('platform.system', return_value='Linux')
    def test_initialization_and_dispatch_on_linux(self, mock_platform, mock_metal, mock_linux, mock_win32):
        """Verify the operator loads the correct modules when pretending to be on Linux."""
        print("\n\n--- Testing Dispatch Logic on a MOCKED Linux OS ---")
        
        operator = UniversalOSOperator()
        
        # 1. Test Initialization
        self.assertEqual(operator.os_type, 'Linux')
        mock_win32.assert_not_called()
        mock_linux.assert_called_once()
        mock_metal.assert_not_called()
        self.assertIsNotNone(operator.platform_api)
        self.assertIsNone(operator.gpu_accelerator)
        print("  [SUCCESS] Correctly initialized LinuxSyscallWrapper for Linux.")
        
        # 2. Test Method Dispatch
        mock_linux_instance = operator.platform_api
        mock_linux_instance.uname.return_value = {"release": "6.1.0-generic"}
        
        operator.get_detailed_os_version()
        
        mock_linux_instance.uname.assert_called_once()
        print("  [SUCCESS] Correctly dispatched get_detailed_os_version to the Linux module.")

    @patch('modules.os_operations.universal_operations.Win32APIWrapper')
    @patch('modules.os_operations.universal_operations.LinuxSyscallWrapper')
    @patch('modules.os_operations.universal_operations.MetalWrapper')
    @patch('platform.system', return_value='Darwin')
    def test_initialization_and_dispatch_on_macos(self, mock_platform, mock_metal, mock_linux, mock_win32):
        """Verify the operator loads the correct modules when pretending to be on macOS."""
        print("\n\n--- Testing Dispatch Logic on a MOCKED macOS ---")
        
        operator = UniversalOSOperator()
        
        # 1. Test Initialization
        self.assertEqual(operator.os_type, 'Darwin')
        mock_win32.assert_not_called()
        mock_linux.assert_called_once() # For POSIX compatibility
        mock_metal.assert_called_once() # For GPU acceleration
        self.assertIsNotNone(operator.platform_api)
        self.assertIsNotNone(operator.gpu_accelerator)
        print("  [SUCCESS] Correctly initialized both Linux (POSIX) and Metal wrappers for macOS.")
        
        # 2. Test GPU-specific dispatch
        mock_metal_instance = operator.gpu_accelerator
        vec_a = np.array([1, 2, 3])
        vec_b = np.array([4, 5, 6])
        
        operator.accelerated_vector_add(vec_a, vec_b)
        
        # Assert that the a method on the Metal wrapper was called (we'll check compile_shader as a proxy)
        mock_metal_instance.compile_shader.assert_called_once()
        print("  [SUCCESS] Correctly dispatched accelerated_vector_add to the Metal module.")
        
        # 3. Test CPU fallback logic by pretending to be on Linux again
        with patch('platform.system', return_value='Linux'):
            linux_op = UniversalOSOperator()
            mock_metal_instance.reset_mock() # Reset the call count
            
            # This should now use the NumPy fallback
            linux_op.accelerated_vector_add(vec_a, vec_b)
            
            # Assert that the Metal wrapper was NOT called this time
            mock_metal_instance.compile_shader.assert_not_called()
            print("  [SUCCESS] Correctly used CPU fallback for accelerated compute on non-macOS platform.")


if __name__ == '__main__':
    # Re-enable logging for the test runner's output
    logging.disable(logging.NOTSET)
    unittest.main()
