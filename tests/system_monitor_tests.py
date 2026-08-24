# Devin/tests/system_monitor_tests.py
# Purpose: An integration test suite for the system monitoring stack,
#          verifying data collection and parsing from local and remote sources.

import unittest
from unittest.mock import patch, MagicMock

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

_import_error = None

try:
    from modules.system_monitor import SystemMonitorFacade, LocalMonitor, RemoteMonitor, SystemMetrics
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    _import_error = e

# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)


@unittest.skipUnless(DEPS_AVAILABLE, f"Skipping system monitor tests, dependency missing: {_import_error}")
class TestSystemMonitor(unittest.TestCase):
    """
    Tests the data collection and parsing logic of the system monitoring tools.
    """

    @patch('modules.system_monitor.psutil')
    def test_local_monitor_correctly_interprets_psutil(self, mock_psutil: MagicMock):
        """
        Verify that the LocalMonitor correctly calls psutil and formats the data.
        """
        print("\n\n--- Testing LocalMonitor with Mocked psutil ---")
        
        # 1. Configure the mock psutil to return known values
        mock_psutil.cpu_percent.return_value = 25.5
        mock_psutil.virtual_memory.return_value = MagicMock(percent=55.0, total=8 * (1024**3), used=4.4 * (1024**3))
        mock_psutil.disk_usage.return_value = MagicMock(percent=75.3, total=512 * (1024**3), used=385 * (1024**3))
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000, bytes_recv=2000)
        
        # 2. Instantiate the real LocalMonitor and get metrics
        monitor = LocalMonitor()
        metrics = monitor.get_metrics()
        
        # 3. Assert the results
        self.assertIsInstance(metrics, SystemMetrics)
        self.assertEqual(metrics.cpu_usage_percent, 25.5)
        self.assertEqual(metrics.memory_usage_percent, 55.0)
        self.assertEqual(metrics.disk_usage_percent, 75.3)
        self.assertEqual(metrics.net_bytes_sent, 1000)
        self.assertEqual(metrics.net_bytes_recv, 2000)
        print("  [SUCCESS] LocalMonitor correctly parsed data from mocked psutil.")

    @patch('modules.system_monitor.GenericRemoteShell')
    def test_remote_monitor_correctly_parses_shell_output(self, MockRemoteShell: MagicMock):
        """
        Verify that the RemoteMonitor correctly parses the stdout of various
        Linux commands from a mocked SSH session.
        """
        print("\n\n--- Testing RemoteMonitor with Mocked SSH ---")
        mock_ssh_instance = MockRemoteShell.return_value
        
        # 1. Configure the mock SSH client to return different strings for different commands
        mock_top_output = "top - 10:00:00 up 10 days,  1:00,  1 user,  load average: 0.00, 0.01, 0.05\n%Cpu(s): 10.0 us,  5.0 sy,  0.0 ni, 85.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st"
        mock_free_output = "              total        used        free      shared  buff/cache   available\nMem:        8000000     4000000     4000000       10000       500000     4500000"
        mock_df_output = "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       100G   90G   10G  90% /"
        mock_net_output = "Inter-|   Receive                                                |  Transmit\n face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed\n    lo:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0\n  eth0:  500000     5000    0    0    0     0          0         0   100000    1000    0    0    0     0       0          0"

        def mock_exec(command):
            if 'top' in command: return {'stdout': mock_top_output, 'exit_code': 0}
            if 'free' in command: return {'stdout': mock_free_output, 'exit_code': 0}
            if 'df' in command: return {'stdout': mock_df_output, 'exit_code': 0}
            if 'cat /proc/net/dev' in command: return {'stdout': mock_net_output, 'exit_code': 0}
            return {'stdout': '', 'stderr': 'Command not found in mock', 'exit_code': 1}
        
        mock_ssh_instance.execute_command.side_effect = mock_exec
        
        # 2. Instantiate the real RemoteMonitor and get metrics
        monitor = RemoteMonitor(ssh_client=mock_ssh_instance)
        metrics = monitor.get_metrics()
        
        # 3. Assert the results
        self.assertIsInstance(metrics, SystemMetrics)
        # top: 85.0 id -> 15.0 usage
        self.assertAlmostEqual(metrics.cpu_usage_percent, 15.0)
        # free: 4,000,000 used / 8,000,000 total = 50%
        self.assertAlmostEqual(metrics.memory_usage_percent, 50.0)
        # df: 90%
        self.assertAlmostEqual(metrics.disk_usage_percent, 90.0)
        # net: 100000 sent, 500000 received
        self.assertEqual(metrics.net_bytes_sent, 100000)
        self.assertEqual(metrics.net_bytes_recv, 500000)
        print("  [SUCCESS] RemoteMonitor correctly parsed all simulated shell outputs.")

    @patch('modules.system_monitor.RemoteMonitor')
    @patch('modules.system_monitor.LocalMonitor')
    def test_facade_correctly_aggregates_data(self, MockLocalMonitor, MockRemoteMonitor):
        """
        Verify that the SystemMonitorFacade correctly gathers and aggregates
        data from all its registered monitor objects.
        """
        print("\n\n--- Testing SystemMonitorFacade Aggregation ---")
        # 1. Configure the mock monitors to return pre-defined SystemMetrics objects
        mock_local_instance = MockLocalMonitor.return_value
        mock_local_instance.get_metrics.return_value = SystemMetrics(host="localhost", cpu_usage_percent=10.0, memory_usage_percent=20.0)

        mock_remote_instance = MockRemoteMonitor.return_value
        mock_remote_instance.host = "remote-server-1"
        mock_remote_instance.get_metrics.return_value = SystemMetrics(host="remote-server-1", cpu_usage_percent=30.0, memory_usage_percent=40.0)

        # 2. Instantiate the real Facade with the mock monitors
        facade = SystemMonitorFacade(monitors=[mock_local_instance, mock_remote_instance])
        
        # 3. Get all metrics
        all_metrics = facade.get_all_metrics()
        
        # 4. Assert the results
        self.assertIn("localhost", all_metrics)
        self.assertIn("remote-server-1", all_metrics)
        self.assertEqual(all_metrics["localhost"].cpu_usage_percent, 10.0)
        self.assertEqual(all_metrics["remote-server-1"].memory_usage_percent, 40.0)
        print("  [SUCCESS] Facade correctly aggregated metrics from multiple monitors.")


if __name__ == '__main__':
    # Re-enable logging for the test runner's output
    logging.disable(logging.NOTSET)
    unittest.main()
