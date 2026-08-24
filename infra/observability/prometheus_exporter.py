# Devin/infra/observability/prometheus_exporter.py
# Purpose: Exposes Devin's operational metrics for Prometheus scraping.

import datetime
import logging
import sys
import time
import os
from typing import Dict, Any, Literal

# --- Prometheus Client Library Import ---
# Requires: pip install prometheus_client
try:
    from prometheus_client import start_http_server
    from prometheus_client import Counter, Gauge, Histogram, Summary, Info
    PROMETHEUS_CLIENT_AVAILABLE = True
    print("Conceptual: 'prometheus_client' library assumed available.")
except ImportError:
    # Define placeholders if library not found for structural integrity
    PROMETHEUS_CLIENT_AVAILABLE = False
    print("WARNING: 'prometheus_client' library not found. Prometheus exporter will be non-functional.")
    class BaseMetricPlaceholder:
        def __init__(self, name, documentation, labelnames=(), **kwargs):
            self.name = name
            self.documentation = documentation
            self.labelnames = labelnames
            logger.info(f"Prometheus Placeholder Metric Created: {name} ({type(self).__name__})")
        def labels(self, *args, **kwargs): return self # Chain for placeholder
        def inc(self, amount=1): pass
        def dec(self, amount=1): pass
        def set(self, value): pass
        def observe(self, amount): pass
        def info(self, info_dict): pass

    Counter, Gauge, Histogram, Summary, Info = (type(f'{cls_name}Placeholder', (BaseMetricPlaceholder,), {}) for cls_name in ["Counter", "Gauge", "Histogram", "Summary", "Info"]) # type: ignore

    def start_http_server(port, addr=''):
        logger.info(f"Prometheus Placeholder: Would start HTTP server on {addr}:{port} if library was available.")

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("DevinPrometheusExporter")

class DevinPrometheusExporter:
    """
    Manages and exposes Devin's operational metrics to Prometheus.
    """

    def __init__(self, devin_version: str = "0.1.0-alpha"):
        """
        Initializes the exporter and defines the metrics to be exposed.
        """
        logger.info("Initializing DevinPrometheusExporter...")

        # --- Define Metrics ---
        # It's good practice to prefix metrics with application name (e.g., 'devin_')

        # 1. Counters (values that only increase or reset to zero on restart)
        self.tasks_processed_total = Counter(
            'devin_tasks_processed_total',
            'Total number of tasks processed by Devin',
            ['task_type', 'status'] # Labels: e.g., task_type='code_generation', status='success'
        )
        self.errors_total = Counter(
            'devin_errors_total',
            'Total number of errors encountered by Devin',
            ['error_type', 'component'] # Labels: e.g., error_type='api_failure', component='llm_interface'
        )
        self.api_calls_total = Counter(
            'devin_api_calls_total',
            'Total API calls made by Devin to external services',
            ['service_name', 'endpoint', 'http_status_code']
        )
        self.files_accessed_total = Counter(
            'devin_files_accessed_total',
            'Total number of files accessed by Devin',
            ['operation_type'] # e.g., 'read', 'write', 'delete'
        )

        # 2. Gauges (values that can go up or down)
        self.active_agents = Gauge(
            'devin_active_agents',
            'Number of currently active Devin agents or concurrent tasks'
        )
        self.memory_usage_bytes = Gauge(
            'devin_memory_usage_bytes',
            'Current memory usage of the Devin process in bytes (conceptual)'
            # Note: Getting accurate process memory is platform-specific, often via 'psutil'
        )
        self.cpu_usage_percent = Gauge(
            'devin_cpu_usage_percent',
            'Current CPU usage of the Devin process as a percentage (conceptual)'
        )
        self.active_connections = Gauge(
            'devin_active_connections',
            'Number of active network connections (e.g., to services, UIs)',
            ['connection_type'] # e.g., 'websocket_ui', 'external_api'
        )


        # 3. Histograms (observe distributions of values, e.g., latencies)
        # Buckets should be tailored to expected value ranges.
        self.task_execution_duration_seconds = Histogram(
            'devin_task_execution_duration_seconds',
            'Histogram of task execution durations in seconds',
            ['task_type'],
            buckets=[0.1, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300] # 0.1s to 5 mins
        )
        self.llm_api_latency_seconds = Histogram(
            'devin_llm_api_latency_seconds',
            'Histogram of LLM API call latencies in seconds',
            ['llm_provider', 'model_name']
        )

        # 4. Summaries (similar to Histograms, but calculate quantiles on client-side)
        # Use sparingly as they are more resource-intensive.
        self.prompt_token_count = Summary(
            'devin_prompt_token_count',
            'Summary of token counts in prompts sent to LLMs',
            ['llm_provider', 'model_name']
        )

        # 5. Info (exposes information about the application)
        self.devin_build_info = Info(
            'devin_build',
            'Build information about the Devin application'
        )
        self.devin_build_info.info({
            'version': devin_version,
            'build_date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'python_version': sys.version.split()[0] # Example
        })

        logger.info("Prometheus metrics defined.")

    def start_http_server(self, port: int = 8088, addr: str = '0.0.0.0') -> None:
        """
        Starts the HTTP server to expose the metrics on /metrics.
        This is typically called once when Devin starts.

        Args:
            port (int): Port number for the metrics server.
            addr (str): Address to bind the server to (0.0.0.0 for all interfaces).
        """
        if not PROMETHEUS_CLIENT_AVAILABLE:
            logger.error("Cannot start Prometheus HTTP server: prometheus_client library not available.")
            return
        try:
            start_http_server(port, addr=addr)
            logger.info(f"Prometheus metrics server started on http://{addr if addr != '0.0.0.0' else 'localhost'}:{port}/metrics")
        except Exception as e:
            logger.error(f"Failed to start Prometheus metrics server: {e}")

    # --- Methods to Update Metrics ---

    def record_task_processed(self, task_type: str, status: Literal["success", "failure", "error"]):
        """Records that a task has been processed."""
        self.tasks_processed_total.labels(task_type=task_type, status=status).inc()
        logger.debug(f"Metric: Task '{task_type}' processed with status '{status}'.")

    def record_error(self, error_type: str, component: str):
        """Records an error occurrence."""
        self.errors_total.labels(error_type=error_type, component=component).inc()
        logger.debug(f"Metric: Error '{error_type}' in component '{component}'.")

    def record_api_call(self, service_name: str, endpoint: str, http_status_code: int):
        """Records an API call to an external service."""
        self.api_calls_total.labels(service_name=service_name, endpoint=endpoint, http_status_code=str(http_status_code)).inc()
        logger.debug(f"Metric: API call to {service_name}{endpoint} -> {http_status_code}.")

    def record_file_access(self, operation_type: Literal["read", "write", "delete", "create"]):
        """Records a file access operation."""
        self.files_accessed_total.labels(operation_type=operation_type).inc()

    def set_active_agents(self, count: int):
        """Sets the current number of active agents/threads."""
        self.active_agents.set(count)
        logger.debug(f"Metric: Active agents set to {count}.")

    def set_memory_usage_bytes(self, memory_bytes: int):
        """Sets the current conceptual memory usage."""
        # In real app, use psutil: import psutil; process = psutil.Process(os.getpid()); memory_bytes = process.memory_info().rss
        self.memory_usage_bytes.set(memory_bytes)

    def set_cpu_usage_percent(self, cpu_percent: float):
        """Sets the current conceptual CPU usage."""
        # In real app, use psutil: process.cpu_percent(interval=None)
        self.cpu_usage_percent.set(cpu_percent)

    def update_active_connections(self, connection_type: str, count_delta: int):
        """Updates the gauge for active connections (can inc or dec)."""
        if count_delta > 0:
            self.active_connections.labels(connection_type=connection_type).inc(count_delta)
        elif count_delta < 0:
            self.active_connections.labels(connection_type=connection_type).dec(abs(count_delta))


    def observe_task_duration(self, task_type: str, duration_seconds: float):
        """Observes the duration of a task for the histogram."""
        self.task_execution_duration_seconds.labels(task_type=task_type).observe(duration_seconds)
        logger.debug(f"Metric: Task '{task_type}' duration observed: {duration_seconds:.3f}s.")

    def observe_llm_api_latency(self, provider: str, model: str, latency_seconds: float):
        """Observes LLM API call latency."""
        self.llm_api_latency_seconds.labels(llm_provider=provider, model_name=model).observe(latency_seconds)

    def observe_prompt_tokens(self, provider: str, model: str, token_count: int):
        """Observes the number of tokens in a prompt."""
        self.prompt_token_count.labels(llm_provider=provider, model_name=model).observe(token_count)


# Example Usage (conceptual)
if __name__ == "__main__":
    print("=========================================================")
    print("=== Running Devin Prometheus Exporter Prototype ===")
    print("=========================================================")

    if not PROMETHEUS_CLIENT_AVAILABLE:
        print("\n'prometheus_client' library not found. Metrics will not be exposed.")
        print("Please install it: pip install prometheus_client")
    else:
        # Initialize and start the exporter
        devin_version_str = os.environ.get("DEVIN_VERSION", "0.1.0-dev")
        exporter = DevinPrometheusExporter(devin_version=devin_version_str)
        
        # Exporter server usually started by the main application process
        # For this example, we start it here.
        exporter_port = int(os.environ.get("DEVIN_METRICS_PORT", 8088))
        exporter.start_http_server(port=exporter_port)
        
        print(f"\nPrometheus exporter started. Metrics available at: http://localhost:{exporter_port}/metrics")
        print("Simulating some Devin activity to generate metrics...")

        # Simulate some activity
        exporter.set_active_agents(5)
        exporter.record_task_processed(task_type="code_generation", status="success")
        exporter.observe_task_duration(task_type="code_generation", duration_seconds=random.uniform(2.0, 15.0))
        
        exporter.record_task_processed(task_type="web_search", status="success")
        exporter.observe_task_duration(task_type="web_search", duration_seconds=random.uniform(0.5, 3.0))
        
        exporter.record_api_call("OpenAI", "/v1/chat/completions", 200)
        exporter.observe_llm_api_latency("OpenAI", "gpt-4", random.uniform(0.8, 5.0))
        exporter.observe_prompt_tokens("OpenAI", "gpt-4", random.randint(500, 2000))

        exporter.record_error(error_type="network_timeout", component="external_api_client")
        exporter.record_task_processed(task_type="file_edit", status="error")
        exporter.observe_task_duration(task_type="file_edit", duration_seconds=random.uniform(0.1, 1.0))

        exporter.set_active_agents(3)
        exporter.set_memory_usage_bytes(random.randint(500, 2000) * 1024 * 1024) # Conceptual MB
        exporter.set_cpu_usage_percent(random.uniform(10.0, 70.0)) # Conceptual %
        exporter.update_active_connections("websocket_ui", 2)


        print("\nMetrics have been updated. Check the /metrics endpoint.")
        print("Exporter will keep running. Press Ctrl+C to stop this example.")
        try:
            while True:
                # Simulate ongoing activity for gauges that might change
                exporter.set_memory_usage_bytes(random.randint(500, 2000) * 1024 * 1024)
                exporter.set_cpu_usage_percent(random.uniform(5.0, 60.0))
                # Simulate a new task occasionally
                if random.random() < 0.1:
                    exporter.record_task_processed("background_check", "success")
                    exporter.observe_task_duration("background_check", random.uniform(1.0, 10.0))
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nExporter example stopped by user.")
        except Exception as e:
            logger.error(f"An error occurred in the main loop: {e}")

    print("\n=========================================================")
    print("=== Devin Prometheus Exporter Prototype Complete ===")
    print("=========================================================")
