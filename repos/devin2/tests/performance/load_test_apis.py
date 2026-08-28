# Devin/tests/performance/load_test_apis.py
# Purpose: A multi-threaded load testing script to stress-test the backend
#          API servers and measure their performance under concurrent load.

import logging
import threading
import time
import requests
from typing import List, Dict, Any, Callable
from collections import defaultdict
import numpy as np

# Configure basic logging
logger = logging.getLogger("APILoadTest")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

# --- Test Configuration ---
# These can be adjusted to increase the load
CONFIG = {
    "duration_seconds": 10,
    "concurrent_users": 10,
    "server_base_url": "http://127.0.0.1" # Assumes servers are running locally
}

# Define the server ports
SERVER_PORTS = {
    "CloudIntegration": 5002,
    "Analytics": 5004,
    "MobileIntegration": 5006,
}

class ResultsCollector:
    """A thread-safe class to collect results from all worker threads."""
    def __init__(self):
        self.results: Dict[str, List[Tuple[float, bool]]] = defaultdict(list)
        self._lock = threading.Lock()

    def add_result(self, scenario_name: str, latency: float, success: bool):
        with self._lock:
            self.results[scenario_name].append((latency, success))

# --- Test Scenarios ---
# Each scenario is a function that takes a requests.Session and the collector
def scenario_cloud_list_vms(session: requests.Session, collector: ResultsCollector):
    """Hits the endpoint to list AWS EC2 instances."""
    url = f"{CONFIG['server_base_url']}:{SERVER_PORTS['CloudIntegration']}/aws/vms"
    session.get(url, timeout=5)

def scenario_analytics_get_data(session: requests.Session, collector: ResultsCollector):
    """Hits the endpoint to get recent analytics data."""
    url = f"{CONFIG['server_base_url']}:{SERVER_PORTS['Analytics']}/data?period=5m"
    session.get(url, timeout=5)

def scenario_mobile_list_devices(session: requests.Session, collector: ResultsCollector):
    """Hits the endpoint to list connected mobile devices."""
    url = f"{CONFIG['server_base_url']}:{SERVER_PORTS['MobileIntegration']}/devices"
    session.get(url, timeout=5)

# --- Load Test Engine ---
def worker(scenario_func: Callable, stop_event: threading.Event, collector: ResultsCollector):
    """A worker thread that repeatedly runs a test scenario."""
    scenario_name = scenario_func.__name__
    with requests.Session() as session:
        while not stop_event.is_set():
            success = False
            start_time = time.perf_counter()
            try:
                scenario_func(session, collector)
                success = True
            except requests.RequestException as e:
                logger.warning(f"Request failed in '{scenario_name}': {e}")
            finally:
                end_time = time.perf_counter()
                latency = end_time - start_time
                collector.add_result(scenario_name, latency, success)

def analyze_and_print_report(results: Dict, duration: int):
    """Calculates and prints a summary of the load test results."""
    print("\n--- Load Test Results ---")
    for scenario_name, data in results.items():
        if not data:
            print(f"\nScenario: {scenario_name}\n  No data collected.")
            continue
            
        latencies = np.array([d[0] for d in data if d[1]])
        success_count = sum(1 for d in data if d[1])
        error_count = len(data) - success_count
        total_requests = len(data)

        print(f"\n📈 Scenario: {scenario_name}")
        print("-" * (15 + len(scenario_name)))
        print(f"  Total Requests:   {total_requests}")
        print(f"  Requests/Sec (RPS): {total_requests / duration:.2f}")
        print(f"  Successful:       {success_count}")
        print(f"  Failed:           {error_count} ({error_count / total_requests:.2%})")

        if len(latencies) > 0:
            print("  Latency (seconds):")
            print(f"    - Average:      {np.mean(latencies):.4f}")
            print(f"    - p50 (Median):   {np.percentile(latencies, 50):.4f}")
            print(f"    - p95:            {np.percentile(latencies, 95):.4f}")
            print(f"    - p99:            {np.percentile(latencies, 99):.4f}")

# --- Main Execution ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== API Server Load Test Suite 🚀 ===")
    print("=========================================================")
    print("!!! PREREQUISITE: The target servers must be running in separate terminals. !!!")
    print(f"This test will run for {CONFIG['duration_seconds']} seconds with {CONFIG['concurrent_users']} concurrent users per scenario.")
    
    # Scenarios to run in this test session
    scenarios_to_run = [
        scenario_cloud_list_vms,
        scenario_analytics_get_data,
        scenario_mobile_list_devices,
    ]
    
    all_threads = []
    stop_event = threading.Event()
    results_collector = ResultsCollector()
    
    print("\nStarting load test...")
    try:
        # Start all worker threads for all scenarios
        for scenario in scenarios_to_run:
            for _ in range(CONFIG['concurrent_users']):
                thread = threading.Thread(target=worker, args=(scenario, stop_event, results_collector))
                all_threads.append(thread)
                thread.start()
        
        # Let the test run for the configured duration
        time.sleep(CONFIG['duration_seconds'])

    except KeyboardInterrupt:
        print("\nUser interrupted. Stopping test...")
    finally:
        # Stop all threads and wait for them to finish
        stop_event.set()
        for thread in all_threads:
            thread.join()
        
        # Analyze and print the final report
        analyze_and_print_report(results_collector.results, CONFIG['duration_seconds'])

    print("\n=========================================================")
    print("=== Load Test Suite Complete ===")
    print("=========================================================")
