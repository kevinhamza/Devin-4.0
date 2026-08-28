"""
monitoring/cpu_usage.py
-----------------------
This module monitors CPU usage and provides real-time statistics for system performance
and analysis. It includes alerts, historical logging, and API support for external tools.
"""

import psutil
import time
from datetime import datetime
import logging
from flask import Flask, jsonify
from threading import Thread

# Constants
LOG_FILE = "monitoring/cpu_usage.log"
CPU_ALERT_THRESHOLD = 85  # Percentage

# Flask app for API
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class monitor_cpu:
    def __init__(self, log_file=LOG_FILE, alert_threshold=CPU_ALERT_THRESHOLD):
        self.log_file = log_file
        self.alert_threshold = alert_threshold
        self.usage = None

    def log_cpu_usage(self):
        """Logs current CPU usage to the log file."""
        self.usage = psutil.cpu_percent(interval=1)
        logging.info(f"CPU Usage: {self.usage}%")
        return self.usage

    def check_alert_threshold(self):
        """
        Checks if the CPU usage exceeds the threshold.
        Triggers an alert if the threshold is crossed.
        """
        if self.usage > self.alert_threshold:
            alert_message = f"ALERT: High CPU usage detected at {self.usage}%!"
            logging.warning(alert_message)
            print(alert_message)

    def monitor_cpu(self, interval=5):
        """
        Monitors CPU usage at regular intervals.
        Args:
            interval (int): Time in seconds between checks.
        """
        try:
            while True:
                self.log_cpu_usage()
                self.check_alert_threshold()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("CPU monitoring stopped.")

    def run_monitoring_in_background(self, interval=5):
        """
        Run the CPU monitoring in the background while the Flask app is running.
        """
        monitor_thread = Thread(target=self.monitor_cpu, args=(interval,))
        monitor_thread.daemon = True  # Allows thread to exit when the program exits
        monitor_thread.start()

@app.route('/api/cpu', methods=['GET'])
def get_cpu_usage():
    """
    API Endpoint: Returns the current CPU usage as JSON.
    """
    cpu_usage = CPUUsage()
    usage = cpu_usage.log_cpu_usage()
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "cpu_usage": usage
    })

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CPU Usage Monitoring Tool")
    parser.add_argument('--api', action='store_true', help="Run API server")
    parser.add_argument('--interval', type=int, default=5, help="Monitoring interval in seconds")

    args = parser.parse_args()

    if args.api:
        print("Starting CPU Usage Monitoring API server...")
        cpu_usage = CPUUsage()
        cpu_usage.run_monitoring_in_background(interval=args.interval)  # Run monitoring in the background
        app.run(host='0.0.0.0', port=5000)
    else:
        print(f"Starting CPU Usage Monitoring (Interval: {args.interval}s)...")
        cpu_usage = CPUUsage()
        cpu_usage.monitor_cpu(interval=args.interval)
