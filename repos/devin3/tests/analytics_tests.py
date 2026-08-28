# Devin/tests/analytics_tests.py
# Purpose: An integration test suite for the analytics pipeline, verifying
#          the client-server communication for logging and retrieving data.

import unittest
import threading
import time
import requests
from unittest.mock import patch

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

try:
    from servers.analytics_server import AnalyticsServer
    from modules.analytics_module import AnalyticsFacade
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    _import_error = e

# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)


@unittest.skipUnless(DEPS_AVAILABLE, f"Skipping analytics tests, dependency missing: {_import_error}")
class TestAnalyticsPipeline(unittest.TestCase):
    """
    Tests the full client-server pipeline for the AnalyticsServer.
    """
    server_thread = None
    server_port = 5005 # Use a unique port for testing
    server_url = f"http://127.0.0.1:{server_port}"
    
    @classmethod
    def setUpClass(cls):
        """Starts the AnalyticsServer in a background thread before any tests run."""
        cls.server_instance = AnalyticsServer()
        cls.server_thread = threading.Thread(
            target=cls.server_instance.run,
            args=("127.0.0.1", cls.server_port),
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(1) # Give the server a moment to start up

    @classmethod
    def tearDownClass(cls):
        """Stops the server after all tests have run."""
        try:
            requests.post(f"{cls.server_url}/shutdown")
        except requests.ConnectionError:
            pass
        if cls.server_thread:
            cls.server_thread.join(timeout=2)

    def setUp(self):
        """Create a new facade and reset the server's state before each test."""
        self.facade = AnalyticsFacade(base_url=self.server_url)
        # Reset the server's in-memory DataFrame for test isolation
        requests.post(f"{self.server_url}/reset")

    def test_log_and_retrieve_workflow_with_time_windows(self):
        """
        Verify the full workflow:
        1. Log events with different timestamps.
        2. Retrieve data with different time windows.
        3. Assert that the server's aggregation and filtering is correct.
        """
        print("\n\n--- Testing Log & Retrieve Workflow ---")

        # --- 1. Log Events with Controlled Timestamps ---
        print("  [1/3] Logging events with controlled timestamps...")
        # Use mock to control the current time
        with patch('time.time') as mock_time:
            # Log an event "now"
            mock_time.return_value = 1724800000.0 # A fixed point in time
            self.assertTrue(self.facade.log_event("cpu_usage", 55.5))
            
            # Log an event 2 minutes (120s) in the past
            mock_time.return_value = 1724800000.0 - 120
            self.assertTrue(self.facade.log_event("cpu_usage", 25.0))
            
            # Log an event 10 minutes (600s) in the past
            mock_time.return_value = 1724800000.0 - 600
            self.assertTrue(self.facade.log_event("api_calls", 1))

        # --- 2. Retrieve Data with a Short Time Window ---
        print("  [2/3] Retrieving data for the last 5 minutes...")
        data_5m = self.facade.get_timeseries_data(period="5m")
        
        # Assertions for the 5-minute window
        self.assertIn("cpu_usage", data_5m)
        self.assertIn("api_calls", data_5m)
        # Should only contain the 2 events within the last 5 minutes
        self.assertEqual(len(data_5m["cpu_usage"]), 2)
        self.assertEqual(len(data_5m["api_calls"]), 0) # The api_call event was 10m ago
        # Check the value of the most recent CPU usage event
        self.assertEqual(data_5m["cpu_usage"][-1]['value'], 55.5)
        print("  --> Correctly filtered data for '5m' period.")

        # --- 3. Retrieve Data with a Longer Time Window ---
        print("  [3/3] Retrieving data for the last 15 minutes...")
        data_15m = self.facade.get_timeseries_data(period="15m")

        # Assertions for the 15-minute window
        self.assertIn("cpu_usage", data_15m)
        self.assertIn("api_calls", data_15m)
        # Should contain all 3 events
        self.assertEqual(len(data_15m["cpu_usage"]), 2)
        self.assertEqual(len(data_15m["api_calls"]), 1)
        print("  --> Correctly included all data for '15m' period.")

    def test_server_handles_bad_requests(self):
        """
        Verify that the server returns 400 Bad Request for invalid inputs.
        """
        print("\n\n--- Testing Server Input Validation ---")
        
        # 1. Test logging with a non-numeric value
        bad_log_payload = {"event_type": "cpu_usage", "value": "this-is-not-a-number"}
        response = requests.post(f"{self.server_url}/log", json=bad_log_payload)
        self.assertEqual(response.status_code, 400)
        print(f"  [SUCCESS] Server correctly returned {response.status_code} for invalid log value.")
        
        # 2. Test retrieving data with an invalid time period
        response = requests.get(f"{self.server_url}/data?period=5y") # 'y' for years is not supported
        self.assertEqual(response.status_code, 400)
        print(f"  [SUCCESS] Server correctly returned {response.status_code} for invalid time period.")

if __name__ == '__main__':
    unittest.main()
