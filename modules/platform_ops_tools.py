# Devin/modules/platform_ops_tools.py
# Purpose: A high-level facade that orchestrates Devin's platform-operations
#          tools -- local system monitoring, Prometheus metrics exposition,
#          license/feature-gating, and real statistical data-drift/bias
#          checks for ML data -- into one cohesive interface for the AGI.
#
# Deliberately NOT wrapped here (verified by reading the source, not just the
# module docstring), with reasons:
#   - monitoring/analytics_dashboard.py (AnalyticsDashboard): a curses-based
#     interactive TUI that clears the terminal and blocks in a getch()/render
#     loop from inside __init__. It cannot be launched from a single tool
#     call. Instead, get_system_dashboard_snapshot() below reimplements the
#     same CPU+memory+top-processes view as a plain JSON-serializable dict,
#     reusing the real CPU_Monitor/MemoryTracker methods that dashboard uses.
#   - enterprise/sso_integration.py (SSOManager): genuinely conceptual. Its
#     own settings validation is hard-coded to `errors = []` ("Simulate no
#     errors for placeholder") regardless of whether python3-saml is
#     installed, and every SAML call is either delegated to a non-functional
#     placeholder class or left as commented-out pseudocode. There is no real
#     SAML protocol/crypto logic to expose.
#   - mlops/canary_releases.py, mlops/model_serving/a_b_testing.py,
#     mlops/model_serving/shadow_mode.py: their statistics (t-tests, KPI
#     aggregation) are real, but every one of them requires the caller to
#     supply live Python `Callable` champion/challenger prediction functions
#     to their constructors. That can't be expressed as a JSON-schema-typed
#     agent-tool parameter (str/int/float/bool/dict/list), and there's no
#     actual model-serving/deployment infrastructure underneath to call in
#     this repo -- so wrapping them would mean exposing a fake, always-empty
#     capability. Skipped per the task's own guidance for this exact case.
#   - api_gateway/*: Flask/FastAPI middleware and route classes meant to run
#     inside a web server process, not standalone callable tools (excluded
#     per task instructions).

import logging
from typing import Any, Dict, List, Optional, Union

# --- Import the low-level platform-ops tools this facade will manage ---
from monitoring.cpu_usage import CPU_Monitor
from monitoring.memory_tracker import MemoryTracker, format_bytes
from infra.observability.prometheus_exporter import DevinPrometheusExporter
from enterprise.license_manager import LicenseManager
from mlops.data_validation.drift_detection import DriftDetector
from mlops.data_validation.bias_detector import BiasDetector

# Configure basic logging
logger = logging.getLogger("PlatformOpsFacade")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class PlatformOpsFacade:
    """
    A single, simplified interface to Devin's platform-operations toolchain:
    local CPU/memory monitoring, Prometheus metrics exposition, license/
    feature-tier gating, and real statistical data-drift and fairness/bias
    checks (Kolmogorov-Smirnov, Chi-Squared, PSI, demographic parity,
    equalized odds) for ML datasets.

    All components are real, local, dependency-light logic -- none require a
    live Kubernetes cluster or an external SaaS. Optional dependencies (e.g.
    prometheus_client) degrade gracefully via placeholders already built into
    the underlying modules.
    """

    def __init__(self, license_data_path: Optional[str] = None, devin_version: str = "0.1.0-alpha"):
        """
        Initializes all underlying platform-ops tools.

        Args:
            license_data_path (Optional[str]): Path to the license data JSON
                file used by LicenseManager. Defaults to that module's own
                default path if not given.
            devin_version (str): Version string reported in Prometheus build info.
        """
        self.cpu_monitor = CPU_Monitor()
        self.memory_tracker = MemoryTracker()
        self.license_manager = LicenseManager(license_data_path=license_data_path)
        self.drift_detector = DriftDetector()
        self.bias_detector = BiasDetector()

        self.prometheus_exporter: Optional[DevinPrometheusExporter] = None
        try:
            self.prometheus_exporter = DevinPrometheusExporter(devin_version=devin_version)
        except Exception as e:
            logger.warning(f"DevinPrometheusExporter unavailable: {e}")

        logger.info("PlatformOpsFacade initialized.")

    # ------------------------------------------------------------------
    # Local system monitoring (CPU / memory)
    # ------------------------------------------------------------------

    def get_cpu_usage(self, per_cpu: bool = False) -> Any:
        """Gets current system-wide CPU utilization percent (overall, or a list of per-core percentages)."""
        return self.cpu_monitor.get_system_cpu_usage(per_cpu=per_cpu)

    def get_process_cpu_usage(self, pid: int) -> Optional[float]:
        """Gets CPU utilization percent for a specific process ID (samples over ~1 second)."""
        return self.cpu_monitor.get_process_cpu_usage(pid)

    def get_top_cpu_processes(self, count: int = 5) -> List[Dict[str, Any]]:
        """Lists the top N processes by current CPU usage."""
        return self.cpu_monitor.get_top_processes(count=count)

    def get_memory_usage(self) -> Dict[str, Any]:
        """Gets system-wide RAM and swap usage statistics (bytes and percentages)."""
        vmem = self.memory_tracker.get_virtual_memory_usage()
        swap = self.memory_tracker.get_swap_memory_usage()
        return {
            "ram_percent": vmem.percent,
            "ram_used": format_bytes(vmem.used),
            "ram_total": format_bytes(vmem.total),
            "swap_percent": swap.percent,
            "swap_used": format_bytes(swap.used),
            "swap_total": format_bytes(swap.total),
        }

    def get_process_memory_usage(self, pid: int) -> Optional[Dict[str, Any]]:
        """Gets memory usage (RSS/VMS) for a specific process ID."""
        mem = self.memory_tracker.get_process_memory_usage(pid)
        if mem is None:
            return None
        return {"rss": format_bytes(mem.rss), "vms": format_bytes(mem.vms)}

    def get_top_memory_processes(self, count: int = 5) -> List[Dict[str, Any]]:
        """Lists the top N processes by current resident memory (RSS) usage."""
        return self.memory_tracker.get_top_processes_by_memory(count=count)

    def get_system_dashboard_snapshot(self, top_n: int = 5) -> Dict[str, Any]:
        """
        Returns a single JSON-serializable snapshot of system health: overall
        and per-core CPU usage, RAM/swap usage, and the top-N processes by CPU
        and by memory. This is a non-interactive equivalent of the curses-based
        AnalyticsDashboard TUI (which cannot be driven from a tool call).

        Args:
            top_n (int): How many top processes to include per category.

        Returns:
            Dict[str, Any]: {"cpu": {...}, "memory": {...}, "top_cpu_processes": [...], "top_memory_processes": [...]}.
        """
        return {
            "cpu": {
                "total_percent": self.get_cpu_usage(per_cpu=False),
                "per_core_percent": self.get_cpu_usage(per_cpu=True),
            },
            "memory": self.get_memory_usage(),
            "top_cpu_processes": self.get_top_cpu_processes(count=top_n),
            "top_memory_processes": self.get_top_memory_processes(count=top_n),
        }

    def start_resource_monitoring(self, cpu_threshold: float = 80.0, memory_threshold: float = 85.0, interval_sec: int = 10) -> str:
        """
        Starts background threads that watch CPU and memory usage and log a
        warning whenever either exceeds its threshold. Safe to call repeatedly
        (a no-op if already running).

        Args:
            cpu_threshold (float): CPU percent above which a warning is logged.
            memory_threshold (float): RAM percent above which a warning is logged.
            interval_sec (int): Seconds between samples.
        """
        def _cpu_alert(usage: float):
            logger.warning(f"[resource-monitor] CPU usage high: {usage:.1f}% (threshold {cpu_threshold}%).")

        def _mem_alert(usage: float):
            logger.warning(f"[resource-monitor] Memory usage high: {usage:.1f}% (threshold {memory_threshold}%).")

        self.cpu_monitor.start_monitoring(threshold=cpu_threshold, interval=interval_sec, callback=_cpu_alert)
        self.memory_tracker.start_monitoring(threshold=memory_threshold, interval=interval_sec, callback=_mem_alert)
        return f"Started background CPU (>{cpu_threshold}%) and memory (>{memory_threshold}%) monitoring, sampling every {interval_sec}s."

    def stop_resource_monitoring(self) -> str:
        """Stops the background CPU and memory monitoring threads started by start_resource_monitoring()."""
        self.cpu_monitor.stop_monitoring()
        self.memory_tracker.stop_monitoring()
        return "Stopped background CPU and memory monitoring."

    # ------------------------------------------------------------------
    # Prometheus metrics exposition
    # ------------------------------------------------------------------

    def start_metrics_server(self, port: int = 8088, addr: str = "0.0.0.0") -> str:
        """
        Starts an HTTP server exposing Devin's Prometheus metrics at /metrics.
        No-ops with a warning if the 'prometheus_client' package isn't installed.
        """
        if not self.prometheus_exporter:
            return "Prometheus exporter is unavailable."
        self.prometheus_exporter.start_http_server(port=port, addr=addr)
        return f"Prometheus metrics server started on {addr}:{port}/metrics (if 'prometheus_client' is installed)."

    def record_task_metric(self, task_type: str, status: str, duration_seconds: Optional[float] = None) -> str:
        """Records that a task was processed (and optionally its duration) as a Prometheus metric."""
        if not self.prometheus_exporter:
            return "Prometheus exporter is unavailable."
        self.prometheus_exporter.record_task_processed(task_type=task_type, status=status)
        if duration_seconds is not None:
            self.prometheus_exporter.observe_task_duration(task_type=task_type, duration_seconds=duration_seconds)
        return f"Recorded task metric: type='{task_type}' status='{status}'."

    def record_error_metric(self, error_type: str, component: str) -> str:
        """Records an error occurrence as a Prometheus counter."""
        if not self.prometheus_exporter:
            return "Prometheus exporter is unavailable."
        self.prometheus_exporter.record_error(error_type=error_type, component=component)
        return f"Recorded error metric: type='{error_type}' component='{component}'."

    def publish_system_gauges(self) -> str:
        """
        Reads real, current CPU/memory usage of this process's host (via
        CPU_Monitor/MemoryTracker) and publishes them as Prometheus gauges,
        replacing the source module's own "conceptual" placeholder values.
        """
        if not self.prometheus_exporter:
            return "Prometheus exporter is unavailable."
        vmem = self.memory_tracker.get_virtual_memory_usage()
        cpu_percent = self.cpu_monitor.get_system_cpu_usage(per_cpu=False)
        self.prometheus_exporter.set_memory_usage_bytes(vmem.used)
        self.prometheus_exporter.set_cpu_usage_percent(cpu_percent)
        return f"Published gauges: cpu={cpu_percent}%, memory_used={format_bytes(vmem.used)}."

    # ------------------------------------------------------------------
    # License / feature-tier gating
    # ------------------------------------------------------------------

    def validate_license(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Validates whether an active, non-expired license exists for an identifier (user/org/API-key hash)."""
        info = self.license_manager.validate_license(identifier)
        if info is None:
            return None
        return {"license_id": info.license_id, "tier": info.tier.value, "status": info.status, "expiry_utc": info.expiry_utc}

    def check_feature_access(self, identifier: str, feature_key: str) -> bool:
        """Checks whether the identifier's license grants access to a named feature (e.g. 'sso_integration')."""
        return self.license_manager.check_feature_access(identifier, feature_key)

    def get_usage_limit(self, identifier: str, limit_key: str, default_value: int = 0) -> Union[int, float]:
        """Gets a numeric usage limit (e.g. 'max_api_calls_per_day') for the identifier's license."""
        return self.license_manager.get_usage_limit(identifier, limit_key, default_value)

    # ------------------------------------------------------------------
    # ML data-validation: drift detection (real scipy/sklearn statistics)
    # ------------------------------------------------------------------

    def detect_numerical_drift(self, reference_data: List[float], current_data: List[float], feature_name: str, alpha: float = 0.05) -> Dict[str, Any]:
        """
        Detects drift in a numerical feature via the two-sample Kolmogorov-Smirnov test.

        Args:
            reference_data (List[float]): Baseline/training sample.
            current_data (List[float]): Current/production sample.
            feature_name (str): Name of the feature, for reporting.
            alpha (float): Significance level (p-value below this flags drift).
        """
        if not PANDAS_AVAILABLE:
            return {"error": "pandas is required for this method."}
        return self.drift_detector.detect_univariate_numerical_drift_ks(pd.Series(reference_data), pd.Series(current_data), feature_name, alpha=alpha)

    def detect_categorical_drift(self, reference_data: List[str], current_data: List[str], feature_name: str, alpha: float = 0.05) -> Dict[str, Any]:
        """Detects drift in a categorical feature via the Chi-Squared goodness-of-fit test."""
        if not PANDAS_AVAILABLE:
            return {"error": "pandas is required for this method."}
        return self.drift_detector.detect_univariate_categorical_drift_chisquare(pd.Series(reference_data), pd.Series(current_data), feature_name, alpha=alpha)

    def calculate_population_stability_index(self, reference_data: List[Any], current_data: List[Any], feature_name: str, num_bins: int = 10, is_categorical: bool = False) -> Dict[str, Any]:
        """
        Calculates the Population Stability Index (PSI) for a feature: <0.1 no
        significant drift, 0.1-0.2 minor drift, >=0.2 major drift.
        """
        if not PANDAS_AVAILABLE:
            return {"error": "pandas is required for this method."}
        return self.drift_detector.calculate_population_stability_index(pd.Series(reference_data), pd.Series(current_data), feature_name, num_bins=num_bins, is_categorical=is_categorical)

    def detect_prediction_drift(self, reference_predictions: List[Any], current_predictions: List[Any], prediction_type: str = "numerical_score", alpha: float = 0.05, num_bins_for_psi: int = 10) -> Dict[str, Any]:
        """
        Detects drift in a model's output predictions between two periods.

        Args:
            prediction_type (str): One of "numerical_score" (KS test), "categorical_label" (Chi-Squared), or "probability_distribution" (PSI).
        """
        if not PANDAS_AVAILABLE:
            return {"error": "pandas is required for this method."}
        return self.drift_detector.detect_prediction_drift_univariate(pd.Series(reference_predictions), pd.Series(current_predictions), prediction_type=prediction_type, alpha=alpha, num_bins_for_psi=num_bins_for_psi)

    def monitor_performance_degradation(self, y_true_current: List[Any], y_pred_current: List[Any], baseline_metrics: Dict[str, float], metric_tolerances_relative: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Compares current accuracy/F1/precision/recall against baseline values
        to flag concept drift (performance degradation beyond tolerance).

        Args:
            baseline_metrics (Dict[str, float]): e.g. {"accuracy": 0.95, "f1": 0.92}.
            metric_tolerances_relative (Optional[Dict[str, float]]): Relative drop
                tolerance per metric (default 10% for any metric not specified).
        """
        return self.drift_detector.monitor_performance_degradation(y_true_current, y_pred_current, baseline_metrics, metric_tolerances_relative=metric_tolerances_relative)

    # ------------------------------------------------------------------
    # ML data-validation: bias / fairness detection (real pandas/sklearn statistics)
    # ------------------------------------------------------------------

    def check_dataset_representation(self, data: List[Dict[str, Any]], protected_attribute_column: str, target_column: Optional[str] = None) -> Dict[str, Any]:
        """
        Checks group representation (counts/proportions) for a protected
        attribute across a dataset, and optionally the target-label
        distribution within each group.

        Args:
            data (List[Dict[str, Any]]): Dataset rows, each a flat dict of column -> value.
            protected_attribute_column (str): Column name holding the protected attribute (e.g. "gender").
            target_column (Optional[str]): Binary (0/1) target column, if checking outcome parity too.
        """
        if not PANDAS_AVAILABLE:
            return {"error": "pandas is required for this method."}
        df = pd.DataFrame(data)
        return self.bias_detector.check_dataset_representation(df, protected_attribute_column, target_column=target_column)

    def calculate_demographic_parity(self, predictions: List[Any], protected_attribute: List[Any], privileged_group_value: Any, unprivileged_group_value: Any, positive_outcome_label: Any = 1) -> Dict[str, Any]:
        """
        Calculates Demographic Parity Difference and Disparate Impact Ratio
        between a privileged and unprivileged group's positive-outcome rates.
        """
        if not PANDAS_AVAILABLE:
            return {"error": "pandas is required for this method."}
        preds = pd.Series(predictions)
        attr = pd.Series(protected_attribute)
        return self.bias_detector.calculate_demographic_parity_metrics(preds, attr, privileged_group_value, unprivileged_group_value, positive_outcome_label=positive_outcome_label)

    def calculate_equalized_odds(self, true_labels: List[Any], predictions: List[Any], protected_attribute: List[Any], privileged_group_value: Any, unprivileged_group_value: Any, positive_outcome_label: Any = 1) -> Dict[str, Any]:
        """
        Calculates Equal Opportunity Difference and Average Odds Difference
        between a privileged and unprivileged group (true/false positive rate gaps).
        """
        if not PANDAS_AVAILABLE:
            return {"error": "pandas is required for this method."}
        true_s = pd.Series(true_labels)
        preds = pd.Series(predictions)
        attr = pd.Series(protected_attribute)
        return self.bias_detector.calculate_equalized_odds_metrics(true_s, preds, attr, privileged_group_value, unprivileged_group_value, positive_outcome_label=positive_outcome_label)


# --- Example Usage ---
if __name__ == "__main__":
    import json
    print("=========================================================")
    print("=== Platform Ops Facade Demo ===")
    print("=========================================================")

    facade = PlatformOpsFacade()

    print("\n--- System Dashboard Snapshot ---")
    print(json.dumps(facade.get_system_dashboard_snapshot(top_n=3), indent=2, default=str))

    print("\n--- Numerical Drift (KS test, no real drift expected) ---")
    ref = [1.0, 2.0, 3.0, 4.0, 5.0, 2.5, 3.5]
    cur = [1.1, 2.1, 3.1, 4.1, 5.1, 2.6, 3.6]
    print(json.dumps(facade.detect_numerical_drift(ref, cur, "example_feature"), indent=2, default=str))

    print("\n--- License check (no license file present -> should be None/False) ---")
    print(facade.validate_license("nonexistent_user"))
    print(facade.check_feature_access("nonexistent_user", "basic_chat"))

    print("\n=========================================================")
    print("=== Platform Ops Facade Demo Complete ===")
    print("=========================================================")
