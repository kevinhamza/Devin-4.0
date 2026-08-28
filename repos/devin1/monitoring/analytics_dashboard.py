"""
monitoring/analytics_dashboard.py

This module provides functionalities for generating, managing, and displaying analytics data
in a dashboard format. It integrates real-time data visualization for system performance and
user-specific metrics.
"""

import os
import psutil
import platform
import time
import matplotlib.pyplot as plt
from flask import Flask, render_template, jsonify
from threading import Thread

app = Flask(__name__)

class generate_dashboard:
    def __init__(self, static_dir="static", update_interval=30):
        self.static_dir = static_dir
        self.update_interval = update_interval

    def collect_system_metrics(self):
        """Collect system metrics such as CPU, memory, and disk usage."""
        metrics = {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "uptime": time.time() - psutil.boot_time(),
            "os": platform.system(),
            "os_version": platform.version(),
            "hostname": platform.node(),
        }
        return metrics

    def generate_visualizations(self):
        """Generate real-time visualizations for system analytics."""
        metrics = self.collect_system_metrics()

        # Create CPU usage pie chart
        cpu_usage = metrics["cpu_usage"]
        plt.figure(figsize=(6, 4))
        plt.pie(
            [cpu_usage, 100 - cpu_usage],
            labels=["Used", "Available"],
            autopct="%1.1f%%",
            colors=["red", "green"],
        )
        plt.title("CPU Usage")
        plt.savefig(os.path.join(self.static_dir, "cpu_usage.png"))
        plt.close()

        # Create memory usage bar chart
        memory_usage = metrics["memory_usage"]
        plt.figure(figsize=(6, 4))
        plt.bar(["Memory Used", "Memory Available"], [memory_usage, 100 - memory_usage], color="blue")
        plt.title("Memory Usage")
        plt.savefig(os.path.join(self.static_dir, "memory_usage.png"))
        plt.close()

        # Disk usage
        disk_usage = metrics["disk_usage"]
        plt.figure(figsize=(6, 4))
        plt.pie(
            [disk_usage, 100 - disk_usage],
            labels=["Used", "Available"],
            autopct="%1.1f%%",
            colors=["purple", "yellow"],
        )
        plt.title("Disk Usage")
        plt.savefig(os.path.join(self.static_dir, "disk_usage.png"))
        plt.close()

    def periodic_visualization_updates(self):
        """Update visualizations periodically."""
        while True:
            self.generate_visualizations()
            time.sleep(self.update_interval)

    def start_periodic_updates(self):
        """Start the background thread to periodically update visualizations."""
        update_thread = Thread(target=self.periodic_visualization_updates)
        update_thread.daemon = True  # Allows thread to exit when the program exits
        update_thread.start()

# Endpoint to fetch analytics data
@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """API endpoint to fetch system metrics."""
    dashboard = AnalyticsDashboard()
    metrics = dashboard.collect_system_metrics()
    return jsonify(metrics)

# Main dashboard route
@app.route('/')
def dashboard():
    """Render the main analytics dashboard."""
    return render_template('dashboard.html')

# Main function to run the Flask app
if __name__ == '__main__':
    # Ensure the static directory exists
    os.makedirs("static", exist_ok=True)

    # Create an AnalyticsDashboard instance
    dashboard = AnalyticsDashboard()

    # Generate initial visualizations
    dashboard.generate_visualizations()

    # Start periodic updates in the background
    dashboard.start_periodic_updates()

    # Start the Flask application
    app.run(host='0.0.0.0', port=8080, debug=True)
