"""
tests/system_monitor_tests.py

Unit and integration tests for the System Monitor module in the Devin project.
This file ensures that the system monitoring functionalities work as expected.
"""

import unittest
from modules.system_monitor import SystemMonitor

class TestSystemMonitor(unittest.TestCase):
    """Tests for the System Monitor module."""

    def setUp(self):
        """Initialize resources for testing."""
        self.monitor = SystemMonitor()
    
    def test_cpu_usage(self):
        """Test fetching CPU usage."""
        cpu_usage = self.monitor.get_cpu_usage()
        self.assertGreaterEqual(cpu_usage, 0)
        self.assertLessEqual(cpu_usage, 100)
    
    def test_memory_usage(self):
        """Test fetching memory usage."""
        memory_usage = self.monitor.get_memory_usage()
        self.assertGreaterEqual(memory_usage['used'], 0)
        self.assertGreaterEqual(memory_usage['total'], memory_usage['used'])
    
    def test_disk_usage(self):
        """Test fetching disk usage."""
        disk_usage = self.monitor.get_disk_usage()
        for partition, usage in disk_usage.items():
            self.assertIn('total', usage)
            self.assertIn('used', usage)
            self.assertIn('free', usage)
            self.assertGreaterEqual(usage['total'], usage['used'])
            self.assertGreaterEqual(usage['free'], 0)
    
    def test_network_activity(self):
        """Test fetching network activity."""
        network_activity = self.monitor.get_network_activity()
        self.assertIn('sent', network_activity)
        self.assertIn('received', network_activity)
        self.assertGreaterEqual(network_activity['sent'], 0)
        self.assertGreaterEqual(network_activity['received'], 0)

    def test_process_list(self):
        """Test fetching the process list."""
        processes = self.monitor.get_process_list()
        self.assertIsInstance(processes, list)
        self.assertGreater(len(processes), 0)
        for process in processes:
            self.assertIn('pid', process)
            self.assertIn('name', process)
            self.assertIn('cpu_percent', process)
            self.assertIn('memory_percent', process)
    
    def tearDown(self):
        """Clean up resources."""
        del self.monitor

if __name__ == '__main__':
    unittest.main()
