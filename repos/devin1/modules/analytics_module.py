"""
Analytics Module
Tracks system performance, generates reports, and provides insights.
"""

import psutil
import platform
import datetime
from typing import Dict, Any, List
import json
import csv
import os


class SystemPerformanceTracker:
    """
    Tracks and logs system performance metrics, including CPU, memory, disk, and network usage.
    """

    def __init__(self, log_dir: str = "analytics_logs"):
        """
        Initializes the tracker with a specified log directory.

        Args:
            log_dir (str): Directory to save logs and reports.
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    def collect_metrics(self) -> Dict[str, Any]:
        """
        Collects system performance metrics.

        Returns:
            Dict[str, Any]: Collected metrics including CPU, memory, disk, and network usage.
        """
        metrics = {
            "timestamp": str(datetime.datetime.now()),
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_io": {
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_received": psutil.net_io_counters().bytes_recv,
            },
        }
        return metrics

    def log_metrics(self, metrics: Dict[str, Any], log_format: str = "json"):
        """
        Logs collected metrics to a file.

        Args:
            metrics (Dict[str, Any]): The performance metrics to log.
            log_format (str): The format to save the log ("json" or "csv").
        """
        if log_format == "json":
            log_file = os.path.join(self.log_dir, "performance_log.json")
            with open(log_file, "a") as file:
                json.dump(metrics, file)
                file.write("\n")
        elif log_format == "csv":
            log_file = os.path.join(self.log_dir, "performance_log.csv")
            file_exists = os.path.isfile(log_file)
            with open(log_file, "a", newline="") as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(metrics.keys())
                writer.writerow(metrics.values())

    def get_historical_metrics(self, log_format: str = "json") -> List[Dict[str, Any]]:
        """
        Retrieves historical metrics from logs.

        Args:
            log_format (str): The format of the log file ("json" or "csv").

        Returns:
            List[Dict[str, Any]]: A list of historical performance metrics.
        """
        log_file = os.path.join(self.log_dir, f"performance_log.{log_format}")
        if not os.path.exists(log_file):
            return []

        if log_format == "json":
            with open(log_file, "r") as file:
                return [json.loads(line) for line in file.readlines()]
        elif log_format == "csv":
            with open(log_file, "r") as file:
                reader = csv.DictReader(file)
                return [row for row in reader]

    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generates a summary report of historical metrics.

        Returns:
            Dict[str, Any]: Summary statistics of collected performance metrics.
        """
        historical_metrics = self.get_historical_metrics()
        if not historical_metrics:
            return {"error": "No data available to generate a report."}

        summary = {
            "total_logs": len(historical_metrics),
            "cpu_usage_avg": sum(float(entry["cpu_usage"]) for entry in historical_metrics) / len(historical_metrics),
            "memory_usage_avg": sum(float(entry["memory_usage"]) for entry in historical_metrics) / len(historical_metrics),
            "disk_usage_avg": sum(float(entry["disk_usage"]) for entry in historical_metrics) / len(historical_metrics),
        }
        return summary


class ReportGenerator:
    """
    Generates detailed system performance reports.
    """

    @staticmethod
    def save_report(report_data: Dict[str, Any], filename: str, report_dir: str = "analytics_reports"):
        """
        Saves a report to a file.

        Args:
            report_data (Dict[str, Any]): The report data to save.
            filename (str): The name of the report file.
            report_dir (str): Directory to save the report.
        """
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, filename)

        with open(report_path, "w") as file:
            json.dump(report_data, file, indent=4)

    @staticmethod
    def generate_detailed_report(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates a detailed report from metrics.

        Args:
            metrics (List[Dict[str, Any]]): The collected performance metrics.

        Returns:
            Dict[str, Any]: A detailed report with insights and patterns.
        """
        if not metrics:
            return {"error": "No metrics available for detailed report generation."}

        report = {
            "start_time": metrics[0]["timestamp"],
            "end_time": metrics[-1]["timestamp"],
            "total_entries": len(metrics),
            "cpu_max_usage": max(float(entry["cpu_usage"]) for entry in metrics),
            "memory_max_usage": max(float(entry["memory_usage"]) for entry in metrics),
            "disk_max_usage": max(float(entry["disk_usage"]) for entry in metrics),
        }
        return report


# Example Usage
if __name__ == "__main__":
    tracker = SystemPerformanceTracker()
    report_generator = ReportGenerator()

    # Collect and log metrics
    metrics = tracker.collect_metrics()
    tracker.log_metrics(metrics, log_format="json")

    # Generate and save a summary report
    summary = tracker.generate_summary_report()
    print("Summary Report:", summary)

    # Retrieve historical metrics and generate a detailed report
    historical_metrics = tracker.get_historical_metrics(log_format="json")
    detailed_report = report_generator.generate_detailed_report(historical_metrics)
    report_generator.save_report(detailed_report, "detailed_report.json")

    print("Detailed Report Saved.")
