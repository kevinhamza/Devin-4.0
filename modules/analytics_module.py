# # Devin/modules/analytics_module.py
# # Purpose: Tracks system performance, agent activity, and other key metrics
# #          over time to generate analytical reports and visualizations.
# # Tracks system performance and generates reports 📊📈

# import logging
# import uuid
# import random
# from collections import defaultdict
# from datetime import datetime, timezone, timedelta
# from pathlib import Path
# from typing import List, Dict, Any, Optional, Union

# # For conceptual dependency on other modules
# # from .system_monitor_module import SystemHealthReport
# # from .servers.task_orchestrator import Task # Placeholder for a Task object

# # Configure basic logging
# logger = logging.getLogger("AnalyticsModule")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)


# class AnalyticsModule:
#     """
#     Analyzes historical data to track performance and generate reports.
#     This module consumes data from other modules (SystemMonitor, TaskOrchestrator, etc.)
#     to provide insights into long-term trends. In a real system, it would use libraries
#     like pandas for data analysis and matplotlib/seaborn for plotting.
#     """

#     def __init__(self, output_dir: str = "devin_analytics_reports", data_retention_days: int = 30):
#         """
#         Initializes the Analytics Module.

#         Args:
#             output_dir (str): Directory to save generated reports and plots.
#             data_retention_days (int): How long to keep conceptual metric data.
#         """
#         self.output_dir = Path(output_dir)
#         self.output_dir.mkdir(parents=True, exist_ok=True)
#         self.retention_period = timedelta(days=data_retention_days)

#         # In-memory conceptual data store: metric_name -> list of (timestamp, value) tuples
#         self.time_series_data: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
#         # Store discrete events like task completions
#         self.event_data: List[Dict[str, Any]] = []

#         logger.info(f"AnalyticsModule initialized. Reports will be saved to '{self.output_dir.resolve()}'.")
#         logger.warning("All analytics and plots from this module are SIMULATED.")

#     def log_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None) -> None:
#         """Logs a time-series data point."""
#         ts = timestamp or datetime.now(timezone.utc)
#         self.time_series_data[metric_name].append((ts, value))
#         # logger.debug(f"Logged metric '{metric_name}': {value} at {ts.isoformat()}")

#     def log_event(self, event_type: str, event_data: Dict[str, Any], timestamp: Optional[datetime] = None) -> None:
#         """Logs a discrete event."""
#         ts = timestamp or datetime.now(timezone.utc)
#         log_entry = {
#             "event_id": f"evt_{uuid.uuid4().hex[:8]}",
#             "event_type": event_type,
#             "timestamp": ts,
#             "data": event_data
#         }
#         self.event_data.append(log_entry)
#         logger.debug(f"Logged event '{event_type}': {event_data}")

#     def _prune_old_data(self) -> None:
#         """Conceptually removes data older than the retention period."""
#         cutoff_date = datetime.now(timezone.utc) - self.retention_period
#         pruned_count = 0
#         for metric, data_points in self.time_series_data.items():
#             original_count = len(data_points)
#             self.time_series_data[metric] = [(ts, val) for ts, val in data_points if ts > cutoff_date]
#             pruned_count += original_count - len(self.time_series_data[metric])
        
#         original_event_count = len(self.event_data)
#         self.event_data = [evt for evt in self.event_data if evt["timestamp"] > cutoff_date]
#         pruned_count += original_event_count - len(self.event_data)

#         if pruned_count > 0:
#             logger.info(f"Pruned {pruned_count} old data points to maintain retention policy.")

#     def analyze_time_series_metric(self, metric_name: str, time_window: timedelta) -> Optional[Dict[str, float]]:
#         """
#         Analyzes a specific metric over a given time window.
#         In a real system, this would use pandas: `df[metric].rolling(...).mean()` etc.
#         """
#         now = datetime.now(timezone.utc)
#         cutoff_date = now - time_window
        
#         relevant_data = [val for ts, val in self.time_series_data.get(metric_name, []) if ts > cutoff_date]
        
#         if not relevant_data:
#             return None

#         # Simulate pandas-like analysis
#         return {
#             "metric": metric_name,
#             "time_window_hours": round(time_window.total_seconds() / 3600, 2),
#             "count": len(relevant_data),
#             "average": sum(relevant_data) / len(relevant_data),
#             "min": min(relevant_data),
#             "max": max(relevant_data),
#             "latest": relevant_data[-1]
#         }

#     def analyze_event_data(self, time_window: timedelta) -> Dict[str, Any]:
#         """Analyzes discrete event data over a time window."""
#         now = datetime.now(timezone.utc)
#         cutoff_date = now - time_window
#         relevant_events = [evt for evt in self.event_data if evt["timestamp"] > cutoff_date]

#         if not relevant_events:
#             return {"total_events": 0}

#         # Simulate aggregation
#         task_outcomes = defaultdict(int)
#         ai_model_usage = defaultdict(int)
#         for evt in relevant_events:
#             if evt["event_type"] == "task_completed":
#                 outcome = evt["data"].get("status", "UNKNOWN").upper()
#                 task_outcomes[outcome] += 1
#             elif evt["event_type"] == "ai_call":
#                 model_name = evt["data"].get("model", "unknown")
#                 ai_model_usage[model_name] += 1
        
#         total_tasks = sum(task_outcomes.values())
#         success_rate = (task_outcomes.get("SUCCEEDED", 0) / total_tasks) * 100 if total_tasks > 0 else 0

#         return {
#             "total_events": len(relevant_events),
#             "tasks_completed": total_tasks,
#             "task_success_rate_percent": round(success_rate, 2),
#             "task_outcomes": dict(task_outcomes),
#             "ai_model_usage": dict(ai_model_usage)
#         }

#     def generate_plot_conceptual(self,
#                                  metric_name: str,
#                                  time_window: timedelta,
#                                  title: Optional[str] = None) -> Optional[str]:
#         """
#         Conceptually generates a plot for a time-series metric.
#         In a real system, this would use matplotlib/seaborn to create an image file.
#         Here, we will create a text-based plot and a dummy file.
#         """
#         analysis = self.analyze_time_series_metric(metric_name, time_window)
#         if not analysis:
#             logger.warning(f"No data available to plot for metric '{metric_name}'.")
#             return None
        
#         plot_title = title or f"Trend for '{metric_name}' over last {analysis['time_window_hours']} hours"
#         plot_filename = f"{metric_name}_trend_{uuid.uuid4().hex[:6]}.png"
#         output_path = self.output_dir / plot_filename
        
#         logger.info(f"CONCEPTUAL PLOT: Generating plot '{plot_title}'...")
        
#         # Create a simple text-based "sparkline" style plot
#         text_plot = "--- Text Plot ---\n"
#         text_plot += f"{plot_title}\n"
#         min_val, max_val = analysis['min'], analysis['max']
#         avg_val = analysis['average']
#         text_plot += f"Min: {min_val:.2f} | Avg: {avg_val:.2f} | Max: {max_val:.2f}\n"
        
#         # Simulate a sparkline
#         sparkline_chars = " ▂▃▄▅▆▇█"
#         data_points = [val for _, val in self.time_series_data.get(metric_name, [])]
#         if data_points:
#             sparkline = ""
#             val_range = max_val - min_val if max_val > min_val else 1
#             for val in data_points[-20:]: # Plot last 20 points
#                 index = int(((val - min_val) / val_range) * (len(sparkline_chars) - 1))
#                 sparkline += sparkline_chars[index]
#             text_plot += f"Trend: {sparkline}\n"

#         # Create a dummy file to represent the graphical plot
#         try:
#             with open(output_path, "w") as f:
#                 f.write(text_plot)
#             logger.info(f"  Conceptual plot saved to '{output_path}'.")
#             return str(output_path)
#         except Exception as e:
#             logger.error(f"  Failed to write conceptual plot file: {e}")
#             return None

#     def generate_performance_report(self, time_window_hours: int = 24) -> str:
#         """
#         Generates a comprehensive text-based performance report.
#         """
#         self._prune_old_data() # Clean up old data before reporting
#         time_window = timedelta(hours=time_window_hours)
#         now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')
#         logger.info(f"Generating performance report for the last {time_window_hours} hours...")

#         # --- Gather Analytics ---
#         cpu_stats = self.analyze_time_series_metric("cpu_usage_percent", time_window)
#         mem_stats = self.analyze_time_series_metric("memory_usage_percent", time_window)
#         event_stats = self.analyze_event_data(time_window)

#         # --- Generate Plots ---
#         cpu_plot_path = self.generate_plot_conceptual("cpu_usage_percent", time_window, title="CPU Usage Trend")
        
#         # --- Build Report ---
#         report_parts = [
#             f"==================================================",
#             f" Devin Performance & Analytics Report",
#             f"==================================================",
#             f"Generated On: {now_str}",
#             f"Reporting Period: Last {time_window_hours} hours",
#             f"--------------------------------------------------",
#             f"### System Health Summary\n",
#         ]
#         if cpu_stats:
#             report_parts.append(f"- CPU Usage (%):    Avg: {cpu_stats['average']:.2f}, Max: {cpu_stats['max']:.2f}, Latest: {cpu_stats['latest']:.2f}")
#         else:
#             report_parts.append("- CPU Usage (%):    No data available.")

#         if mem_stats:
#             report_parts.append(f"- Memory Usage (%): Avg: {mem_stats['average']:.2f}, Max: {mem_stats['max']:.2f}, Latest: {mem_stats['latest']:.2f}")
#         else:
#              report_parts.append("- Memory Usage (%): No data available.")

#         report_parts.append(f"\nConceptual Plot for CPU Usage saved to: {cpu_plot_path or 'N/A'}")

#         report_parts.extend([
#             f"\n--------------------------------------------------",
#             f"### Agent Activity Summary\n",
#             f"- Total Events Logged: {event_stats.get('total_events', 0)}",
#             f"- Tasks Processed:     {event_stats.get('tasks_completed', 0)}",
#             f"- Task Success Rate:   {event_stats.get('task_success_rate_percent', 0):.2f}%",
#             f"- Task Outcomes:       {event_stats.get('task_outcomes', {})}",
#             f"- AI Model Usage:      {event_stats.get('ai_model_usage', {})}",
#             f"--------------------------------------------------\n"
#         ])
        
#         report_str = "\n".join(report_parts)
        
#         # Save report to a file
#         report_path = self.output_dir / f"performance_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
#         try:
#             with open(report_path, "w") as f:
#                 f.write(report_str)
#             logger.info(f"Performance report saved to '{report_path}'")
#         except Exception as e:
#             logger.error(f"Failed to save performance report: {e}")

#         return report_str

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Analytics Module Prototype 📊📈 ===")
#     print("=========================================================")
    
#     analytics = AnalyticsModule(data_retention_days=1) # Short retention for demo
    
#     # --- 1. Simulate logging data over a period ---
#     print("\n--- Simulating data logging over a few hours ---")
#     start_time = datetime.now(timezone.utc) - timedelta(hours=5)
#     for i in range(100):
#         current_time = start_time + timedelta(minutes=i * 3)
#         # Log system metrics
#         analytics.log_metric("cpu_usage_percent", random.uniform(10, 60), timestamp=current_time)
#         analytics.log_metric("memory_usage_percent", 50.0 + random.uniform(-10, 10), timestamp=current_time)
        
#         # Log discrete events
#         if i % 5 == 0:
#             analytics.log_event(
#                 "task_completed",
#                 {"task_id": f"task_{i}", "status": random.choice(["SUCCEEDED", "SUCCEEDED", "FAILED"])},
#                 timestamp=current_time
#             )
#         if i % 3 == 0:
#              analytics.log_event(
#                 "ai_call",
#                 {"model": random.choice(["gpt-4o", "gemini-1.5-pro", "llama-3-sonar-large"])},
#                 timestamp=current_time
#             )
#     print("  Finished logging 100 conceptual data points.")

#     # --- 2. Generate a comprehensive performance report ---
#     print("\n--- Generating Performance Report ---")
#     performance_report = analytics.generate_performance_report(time_window_hours=6)
    
#     print("\n--- Generated Report ---")
#     print(performance_report)
#     print("=========================================================")
#     print("=== Analytics Module Prototype Complete ===")
#     print("=========================================================")

# Devin/modules/analytics_module.py
# Purpose: A facade that provides a unified interface for querying the
#          AnalyticsServer to generate reports and visualizations.

import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import timedelta

try:
    import requests
    import pandas as pd
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("AnalyticsFacade")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class AnalyticsFacade:
    """
    Provides a client interface to the AnalyticsServer for generating reports.
    """
    def __init__(self, server_url: str = "http://127.0.0.1:5004", output_dir: str = "devin_reports"):
        if not DEPS_AVAILABLE:
            raise ImportError(f"A required library is missing. Error: {_import_error}")
        
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"AnalyticsFacade initialized for server: {self.server_url}")

    def _handle_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Helper to make requests and handle common errors."""
        try:
            response = self.session.request(method, f"{self.server_url}/{endpoint}", **kwargs)
            response.raise_for_status()
            return response
        except requests.HTTPError as e:
            logger.error(f"HTTP Error for {endpoint}: {e.response.status_code} - {e.response.text}")
        except requests.ConnectionError:
            logger.error(f"Connection Error: Could not connect to the AnalyticsServer at {self.server_url}. Is it running?")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
        return None

    def log_event(self, event_type: str, value: float) -> bool:
        """
        Logs a single event to the AnalyticsServer.

        Args:
            event_type: The name/category of the event (e.g., "cpu_usage").
            value: The numeric value associated with the event.

        Returns:
            True if the event was logged successfully, False otherwise.
        """
        payload = {
            "event_type": event_type,
            "value": value,
            "timestamp": time.time(),
        }
        response = self._handle_request("POST", "log", json=payload)
        return response is not None and response.status_code == 200

    def get_timeseries_data(self, period: str = "5m") -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """
        Retrieves logged event data from the server, grouped by event_type,
        filtered to the given time window.

        Args:
            period: Time period string, e.g., "5m", "1h", "1d".

        Returns:
            A dict mapping event_type -> list of {"timestamp", "value"} records,
            or None on error.
        """
        response = self._handle_request("GET", "data", params={"period": period})
        if response and response.status_code == 200:
            return response.json()
        return None

    def get_historical_data(self, period: str = "1h") -> Optional[pd.DataFrame]:
        """
        Retrieves raw historical data from the server for a given period.
        
        Args:
            period: Time period string, e.g., "15m", "1h", "1d".
        
        Returns:
            A pandas DataFrame with the time-series data, or None on error.
        """
        response = self._handle_request("GET", "data", params={"period": period})
        if response and response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        return None

    def generate_plot(self, metric: str, period: str = "1h") -> Optional[Path]:
        """
        Requests a plot from the server and saves it to a local file.
        
        Args:
            metric: The metric to plot (e.g., "cpu", "memory").
            period: Time period string, e.g., "15m", "1h", "1d".
            
        Returns:
            The path to the saved image file, or None on error.
        """
        endpoint = f"report/{metric}.png"
        response = self._handle_request("GET", endpoint, params={"period": period})
        
        if response and response.status_code == 200:
            output_path = self.output_dir / f"{metric}_report_{period}.png"
            try:
                output_path.write_bytes(response.content)
                logger.info(f"Plot saved successfully to '{output_path}'")
                return output_path
            except IOError as e:
                logger.error(f"Failed to save plot to '{output_path}': {e}")
        return None

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Analytics Facade Prototype 📊🔗 ===")
    print("=========================================================")
    
    if not DEPS_AVAILABLE:
        print(f"\nERROR: A required library is missing. Error: {_import_error}")
    else:
        print("!!! PREREQUISITE: This client requires BOTH the `system_monitor_server.py` AND `analytics_server.py` to be running. !!!")
        print("\n1. In terminal 1, run: python -m servers.system_monitor_server")
        print("2. In terminal 2, run: python -m servers.analytics_server")
        print("3. Wait ~30 seconds for some data to be collected.")
        print("4. Run this script.\n")
        
        # 1. Initialize the facade
        facade = AnalyticsFacade(server_url="http://127.0.0.1:5004")
        
        # 2. Get and analyze some raw data
        print("--- 1. Fetching and analyzing raw data for the last minute ---")
        df = facade.get_historical_data(period="1m")
        if df is not None and not df.empty:
            avg_cpu = df['cpu_percent'].mean()
            max_mem = df['memory_percent'].max()
            print(f"  [SUCCESS] Data received. Analysis (last 1m):")
            print(f"    - Average CPU Usage: {avg_cpu:.2f}%")
            print(f"    - Max Memory Usage:  {max_mem:.2f}%")
        else:
            print("  [FAILURE] Could not retrieve or analyze historical data. Are the servers running and collecting data?")

        # 3. Generate and save a plot
        print("\n--- 2. Generating a CPU performance plot for the last minute ---")
        plot_path = facade.generate_plot(metric="cpu", period="1m")
        if plot_path:
            print(f"  [SUCCESS] Plot saved to '{plot_path.resolve()}'")
        else:
            print("  [FAILURE] Could not generate plot from server.")
            
    print("\n=========================================================")
    print("=== Analytics Facade Prototype Complete ===")
    print("=========================================================")
