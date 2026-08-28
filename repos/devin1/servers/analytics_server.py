# servers/analytics_server.py

import time
import psutil
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AnalyticsServer:
    def __init__(self, report_interval=60):
        self.report_interval = report_interval  # Interval in seconds to generate reports
        self.system_data = {
            "cpu_usage": [],
            "memory_usage": [],
            "disk_usage": [],
            "network_stats": []
        }

    def gather_data(self):
        # Gather CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        self.system_data["cpu_usage"].append(cpu_usage)

        # Gather memory usage
        memory_info = psutil.virtual_memory()
        self.system_data["memory_usage"].append(memory_info.percent)

        # Gather disk usage
        disk_info = psutil.disk_usage('/')
        self.system_data["disk_usage"].append(disk_info.percent)

        # Gather network stats
        net_info = psutil.net_io_counters()
        self.system_data["network_stats"].append({
            "bytes_sent": net_info.bytes_sent,
            "bytes_recv": net_info.bytes_recv
        })

        logging.info(f"Data gathered: {json.dumps(self.system_data, indent=4)}")

    def generate_report(self):
        # Prepare report data
        report_data = {
            "cpu_usage": sum(self.system_data["cpu_usage"]) / len(self.system_data["cpu_usage"]),
            "memory_usage": sum(self.system_data["memory_usage"]) / len(self.system_data["memory_usage"]),
            "disk_usage": sum(self.system_data["disk_usage"]) / len(self.system_data["disk_usage"]),
            "network_stats": self.system_data["network_stats"][-1]  # Latest network stats
        }

        # Reset system data for next reporting cycle
        self.system_data = {
            "cpu_usage": [],
            "memory_usage": [],
            "disk_usage": [],
            "network_stats": []
        }

        logging.info(f"Generated report: {json.dumps(report_data, indent=4)}")

    def start(self):
        while True:
            self.gather_data()
            self.generate_report()
            time.sleep(self.report_interval)

if __name__ == "__main__":
    analytics_server = AnalyticsServer(report_interval=60)  # Report every 60 seconds
    analytics_server.start()
