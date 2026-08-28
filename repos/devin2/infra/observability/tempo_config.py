# Devin/infra/observability/tempo_config.py
# Purpose: Provides configurations and utilities for integrating with Grafana Tempo
#          as a distributed tracing backend using OpenTelemetry.

import logging
import os
from typing import Dict, Optional, Union
from urllib.parse import urlencode

# Conceptual import from the previous OTel setup file, if needed to call its init function
# from .distributed_tracing_setup import init_tracing, OPENTELEMETRY_AVAILABLE, trace

# Check if OpenTelemetry was notionally available from the sibling file
# This is just for conceptual linkage in the example.
try:
    # Attempt to reference a variable that would exist if distributed_tracing_setup was loaded and OTel available
    from .distributed_tracing_setup import OPENTELEMETRY_AVAILABLE # type: ignore
except ImportError:
    OPENTELEMETRY_AVAILABLE = False # Assume false if the other file isn't "present" conceptually
    # Define placeholder if OpenTelemetry is not available, for structural integrity
    class PlaceholderTracer:
        def start_as_current_span(self, name, *args, **kwargs): return PlaceholderSpanContextManager(name) # type: ignore
    class PlaceholderSpan: # type: ignore
        def set_attribute(self, key, value): pass
        def add_event(self, name, attributes=None): pass
        def set_status(self, status): pass
        def record_exception(self, exception): pass
        def end(self): pass
    class PlaceholderSpanContextManager: # type: ignore
        def __init__(self, name): self.name = name; self.span = PlaceholderSpan()
        def __enter__(self): module_logger.info(f"OTel Placeholder: Entering span '{self.name}'"); return self.span
        def __exit__(self, exc_type, exc_val, exc_tb): module_logger.info(f"OTel Placeholder: Exiting span '{self.name}'")
    trace = type('PlaceholderTraceModule', (object,), {'get_tracer': lambda name, version=None: PlaceholderTracer()})()


module_logger = logging.getLogger("TempoConfig")
# Basic configuration for this module's logger, if not handled globally
if not module_logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    module_logger.addHandler(_console_handler)
    module_logger.setLevel(logging.INFO)


# --- Default Configuration Values for Tempo ---
DEFAULT_TEMPO_OTLP_GRPC_ENDPOINT = "http://localhost:4317"  # Common default for OTLP/gRPC
DEFAULT_TEMPO_OTLP_HTTP_ENDPOINT = "http://localhost:4318"  # Common default for OTLP/HTTP
DEFAULT_DEVIN_SERVICE_NAME_FOR_TRACING = "Devin"

DEFAULT_GRAFANA_URL = "http://localhost:3000"
DEFAULT_TEMPO_GRAFANA_DATASOURCE_UID = "tempo" # Common default Tempo datasource UID in Grafana

class TempoTraceConfig:
    """
    Provides configuration parameters specifically for sending OpenTelemetry traces to Tempo.
    """

    def __init__(self,
                 service_name: str = DEFAULT_DEVIN_SERVICE_NAME_FOR_TRACING,
                 service_version: str = "0.1.0",
                 otlp_grpc_endpoint: Optional[str] = None,
                 otlp_http_endpoint: Optional[str] = None,
                 use_console_exporter_for_debug: bool = False):
        """
        Initializes Tempo-specific trace configuration.

        Args:
            service_name (str): The name of the service producing traces (e.g., "DevinCore").
            service_version (str): The version of the service.
            otlp_grpc_endpoint (Optional[str]): OTLP/gRPC endpoint for Tempo.
                                                Overrides environment variables if set.
            otlp_http_endpoint (Optional[str]): OTLP/HTTP endpoint for Tempo.
                                                 Overrides environment variables if set.
                                                 (Note: OTel SDK usually supports one OTLP exporter type at a time via env vars easily)
            use_console_exporter_for_debug (bool): Whether to also enable console exporter for local debugging.
        """
        self.service_name = service_name
        self.service_version = service_version

        # Prioritize passed endpoint, then env var, then default
        self.otlp_grpc_endpoint = otlp_grpc_endpoint or \
                                  os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT") or \
                                  os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or \
                                  DEFAULT_TEMPO_OTLP_GRPC_ENDPOINT

        # Note: The Python OTel SDK typically uses OTEL_EXPORTER_OTLP_TRACES_PROTOCOL to choose between grpc/http
        # when OTEL_EXPORTER_OTLP_ENDPOINT is set. Explicitly setting one endpoint type is clearer here.
        # If both gRPC and HTTP endpoints are provided, gRPC might be preferred by convention.
        self.otlp_protocol = os.environ.get("OTEL_EXPORTER_OTLP_TRACES_PROTOCOL", "grpc")
        self.final_otlp_endpoint = self.otlp_grpc_endpoint # Default to gRPC if both somehow specified or from generic env

        if self.otlp_protocol == "http/protobuf" and otlp_http_endpoint:
            self.final_otlp_endpoint = otlp_http_endpoint
        elif otlp_http_endpoint and not otlp_grpc_endpoint: # if only HTTP endpoint is given
             self.final_otlp_endpoint = otlp_http_endpoint
             self.otlp_protocol = "http/protobuf"


        self.use_console_exporter = use_console_exporter_for_debug
        module_logger.info(
            f"TempoTraceConfig initialized: Service='{self.service_name}', "
            f"OTLP Endpoint='{self.final_otlp_endpoint}' (Protocol: {self.otlp_protocol}), "
            f"ConsoleExporterDebug={self.use_console_exporter}"
        )

    def get_otel_init_kwargs(self) -> Dict[str, Any]:
        """
        Returns a dictionary of keyword arguments suitable for passing to
        `distributed_tracing_setup.init_tracing`.
        """
        return {
            "service_name": self.service_name,
            "service_version": self.service_version,
            "otlp_endpoint": self.final_otlp_endpoint, # Pass the determined endpoint
            "use_console_exporter": self.use_console_exporter,
            "use_otlp_exporter": True if self.final_otlp_endpoint else False
        }

def generate_grafana_tempo_deep_link(
    trace_id: str,
    grafana_url: str = DEFAULT_GRAFANA_URL,
    tempo_datasource_uid: str = DEFAULT_TEMPO_GRAFANA_DATASOURCE_UID,
    org_id: int = 1
) -> str:
    """
    Generates a deep link URL to view a specific trace ID in Grafana,
    assuming Grafana is configured with Tempo as a datasource.

    Args:
        trace_id (str): The ID of the trace to view (hexadecimal string).
        grafana_url (str): The base URL of your Grafana instance.
        tempo_datasource_uid (str): The UID of your Tempo datasource in Grafana.
                                     You can find this in Grafana's datasource settings.
        org_id (int): The Grafana organization ID (usually 1 for default).

    Returns:
        str: A URL to directly view the trace in Grafana.
    """
    if not trace_id:
        module_logger.warning("Cannot generate Grafana Tempo link: trace_id is empty.")
        return ""

    # Grafana's explore view for Tempo uses a specific JSON structure in the 'left' query parameter
    # This structure defines the datasource UID and the query (the trace ID).
    explore_query = {
        "datasource": tempo_datasource_uid,
        "queries": [{"query": trace_id, "datasource": tempo_datasource_uid}],
        "range": {"from": "now-1h", "to": "now"} # Default time range, can be adjusted
    }
    # The 'left' parameter is a URL-encoded JSON string.
    left_param_json = json.dumps(explore_query)
    query_params = urlencode({"orgId": org_id, "left": left_param_json})

    deep_link = f"{grafana_url.rstrip('/')}/explore?{query_params}"
    module_logger.debug(f"Generated Grafana-Tempo deep link for trace {trace_id}: {deep_link}")
    return deep_link


# Example of how this configuration could be used with the OTel setup
def setup_devin_tracing_for_tempo(config: TempoTraceConfig) -> Optional[Any]: # Returns Optional[Tracer]
    """
    Initializes OpenTelemetry tracing using configurations tailored for Tempo.
    This function conceptually calls `init_tracing` from the sibling module.
    """
    # This is a conceptual call to the function defined in distributed_tracing_setup.py
    # In a real project, you'd import it directly.
    # For this standalone example, we'll just log what would happen or use a placeholder if OTel is not "available".
    module_logger.info(f"Attempting to initialize OpenTelemetry with Tempo-specific config: {config.get_otel_init_kwargs()}")

    if OPENTELEMETRY_AVAILABLE:
        # Assuming `init_tracing` from distributed_tracing_setup.py is available in the same package
        try:
            from .distributed_tracing_setup import init_tracing as initialize_opentelemetry # type: ignore
            tracer = initialize_opentelemetry(**config.get_otel_init_kwargs())
            if tracer:
                module_logger.info("Successfully initialized OpenTelemetry with Tempo configuration.")
            else:
                module_logger.warning("OpenTelemetry initialization returned no tracer, despite library being available.")
            return tracer
        except ImportError:
            module_logger.error("Could not import 'init_tracing' from '.distributed_tracing_setup'. Ensure files are in the same package.")
            return trace.get_tracer(config.service_name, config.service_version) # Fallback to placeholder if import fails
        except Exception as e:
            module_logger.error(f"Error during OpenTelemetry initialization with Tempo config: {e}", exc_info=True)
            return trace.get_tracer(config.service_name, config.service_version) # Fallback
    else:
        module_logger.warning("OpenTelemetry libraries not fully available. Using placeholder tracer.")
        return trace.get_tracer(config.service_name, config.service_version) # Returns placeholder tracer


# Example Usage
if __name__ == "__main__":
    print("=========================================================")
    print("=== Running Tempo Configuration & Utilities Prototype ===")
    print("=========================================================")

    # 1. Create a Tempo-specific configuration object
    tempo_config = TempoTraceConfig(
        service_name="DevinDataProcessor",
        service_version="v1.2.3",
        otlp_grpc_endpoint=os.environ.get("TEMPO_OTLP_ENDPOINT_GRPC", DEFAULT_TEMPO_OTLP_GRPC_ENDPOINT), # Allow override
        use_console_exporter_for_debug=True
    )
    print(f"\nGenerated TempoTraceConfig:")
    print(f"  Service Name: {tempo_config.service_name}")
    print(f"  Service Version: {tempo_config.service_version}")
    print(f"  OTLP Endpoint: {tempo_config.final_otlp_endpoint}")
    print(f"  Use Console Exporter: {tempo_config.use_console_exporter}")

    # 2. Conceptually initialize tracing using these settings
    # This would typically happen once at application startup.
    print("\nConceptual call to setup Devin tracing for Tempo:")
    devin_tracer = setup_devin_tracing_for_tempo(tempo_config)

    # 3. Generate a deep link for a hypothetical trace ID
    example_trace_id = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6" # Example 32-char hex trace ID
    grafana_instance_url = os.environ.get("GRAFANA_URL", DEFAULT_GRAFANA_URL)
    tempo_ds_uid = os.environ.get("GRAFANA_TEMPO_DATASOURCE_UID", DEFAULT_TEMPO_GRAFANA_DATASOURCE_UID)

    deep_link = generate_grafana_tempo_deep_link(
        trace_id=example_trace_id,
        grafana_url=grafana_instance_url,
        tempo_datasource_uid=tempo_ds_uid
    )
    print(f"\nGenerated Grafana deep link for trace '{example_trace_id}':")
    print(f"  {deep_link}")

    # 4. Simulate creating a span using the configured tracer (if OTel is available)
    if devin_tracer and OPENTELEMETRY_AVAILABLE: # Check if we got a real or placeholder tracer
        print("\nSimulating a traced operation using the configured tracer:")
        # In a real app, you'd get the tracer once after init_tracing.
        # Here, setup_devin_tracing_for_tempo would have called init_tracing.
        # For direct use if setup_devin_tracing_for_tempo was simplified:
        # actual_tracer = trace.get_tracer(tempo_config.service_name, tempo_config.service_version)
        actual_tracer = devin_tracer # Use the tracer returned by setup function

        with actual_tracer.start_as_current_span("ProcessDataItemWithTempoConfig") as span: # type: ignore
            span.set_attribute("item.id", "item_123") # type: ignore
            module_logger.info("  - Inside 'ProcessDataItemWithTempoConfig' span.")
            time.sleep(0.05)
            span.add_event("Processing checkpoint 1") # type: ignore
            time.sleep(0.05)
            span.set_attribute("item.processed_status", "success") # type: ignore
            module_logger.info("  - Span 'ProcessDataItemWithTempoConfig' finished.")
        
        # Ensure spans are flushed if using BatchSpanProcessor by shutting down provider (for demo)
        if OPENTELEMETRY_AVAILABLE:
            global_provider = trace.get_tracer_provider()
            if hasattr(global_provider, "shutdown"):
                module_logger.info("Flushing traces by shutting down global TracerProvider...")
                global_provider.shutdown() # type: ignore
    elif not OPENTELEMETRY_AVAILABLE:
        print("\nSkipping traced operation simulation as OpenTelemetry libraries are not available.")
    else:
        print("\nSkipping traced operation simulation as tracer setup might have used placeholders.")


    print("\n=========================================================")
    print("=== Tempo Configuration & Utilities Prototype Complete ===")
    print("=========================================================")
