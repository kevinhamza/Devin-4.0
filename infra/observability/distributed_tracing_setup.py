# Devin/infra/observability/distributed_tracing_setup.py
# Purpose: Setup for distributed tracing using OpenTelemetry.

import logging
import os
import sys
import time
from typing import Optional

# --- OpenTelemetry Imports ---
# Requires:
# pip install opentelemetry-api opentelemetry-sdk \
#             opentelemetry-exporter-otlp-proto-grpc \
#             opentelemetry-instrumentation-requests (example)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME as ResourceAttributesServiceName
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
    # OTLP Exporter (preferred for sending to Collector/Jaeger/Zipkin supporting OTLP)
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    # Example auto-instrumentation (many others exist for Flask, Django, SQLAlchemy, etc.)
    # from opentelemetry.instrumentation.requests import RequestsInstrumentor

    OPENTELEMETRY_AVAILABLE = True
    print("Conceptual: 'opentelemetry' libraries assumed available.")
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    print("WARNING: 'opentelemetry' libraries not found. Distributed tracing will be non-functional.")
    # Define placeholders if library not found for structural integrity
    class PlaceholderTracer:
        def start_as_current_span(self, name, *args, **kwargs): return PlaceholderSpanContextManager(name)
    class PlaceholderSpan:
        def set_attribute(self, key, value): pass
        def add_event(self, name, attributes=None): pass
        def set_status(self, status): pass
        def record_exception(self, exception): pass
        def end(self): pass
    class PlaceholderSpanContextManager:
        def __init__(self, name): self.name = name; self.span = PlaceholderSpan()
        def __enter__(self): logger.info(f"OTel Placeholder: Entering span '{self.name}'"); return self.span
        def __exit__(self, exc_type, exc_val, exc_tb): logger.info(f"OTel Placeholder: Exiting span '{self.name}'")
    trace = type('PlaceholderTraceModule', (object,), {'get_tracer': lambda name: PlaceholderTracer()})() # type: ignore

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("DistributedTracingSetup")

_TRACER_PROVIDER: Optional[TracerProvider] = None # Global tracer provider

def init_tracing(
    service_name: str = "DevinCoreService",
    service_version: str = "0.1.0",
    otlp_endpoint: Optional[str] = None, # e.g., "http://localhost:4317" for OTLP/gRPC
    use_console_exporter: bool = True,
    use_otlp_exporter: bool = True
) -> Optional[trace.Tracer]: # type: ignore
    """
    Initializes the OpenTelemetry tracing system for the application.

    Args:
        service_name (str): The name of this service/application (e.g., "Devin").
        service_version (str): The version of this service.
        otlp_endpoint (Optional[str]): The endpoint for the OTLP exporter (gRPC).
                                       If None, OTLP exporter won't be configured unless
                                       standard OTel environment variables are set.
        use_console_exporter (bool): Whether to add a console exporter for debugging traces.
        use_otlp_exporter (bool): Whether to configure and add an OTLP exporter.

    Returns:
        Optional[opentelemetry.trace.Tracer]: A tracer instance for creating spans, or None if OTel not available.
    """
    global _TRACER_PROVIDER
    if not OPENTELEMETRY_AVAILABLE:
        logger.error("OpenTelemetry libraries not available. Tracing cannot be initialized.")
        return None

    if _TRACER_PROVIDER is not None:
        logger.warning("Tracing already initialized. Returning existing tracer.")
        return trace.get_tracer(service_name, service_version)

    # 1. Define a Resource for your application
    # This adds common attributes to all spans from this service.
    resource = Resource(attributes={
        ResourceAttributesServiceName: service_name,
        "service.version": service_version,
        "environment": os.environ.get("DEVIN_ENVIRONMENT", "development"),
        # Add other relevant resource attributes: deployment.environment, host.name, os.type etc.
    })

    # 2. Create a TracerProvider
    provider = TracerProvider(resource=resource)
    _TRACER_PROVIDER = provider # Store globally for potential access by instrumentors

    # 3. Configure Span Exporters
    exporters_configured = False

    # Console Exporter (for local debugging - prints spans to console)
    if use_console_exporter:
        console_exporter = ConsoleSpanExporter()
        # SimpleSpanProcessor exports spans one by one as they finish (good for dev/debug)
        console_processor = SimpleSpanProcessor(console_exporter)
        provider.add_span_processor(console_processor)
        logger.info("Configured ConsoleSpanExporter for tracing.")
        exporters_configured = True

    # OTLP Exporter (sends spans to an OTel Collector, Jaeger, Zipkin, etc. via OTLP)
    # OTLP endpoint can be configured via env vars (OTEL_EXPORTER_OTLP_ENDPOINT) or passed directly.
    actual_otlp_endpoint = otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if use_otlp_exporter and actual_otlp_endpoint:
        try:
            # For OTLP/gRPC (port 4317 is common). For OTLP/HTTP (port 4318), use OTLPSpanExporter from
            # opentelemetry.exporter.otlp.proto.http.trace_exporter
            # `insecure=True` for local dev if collector doesn't have TLS. Use secure in prod.
            otlp_exporter = OTLPSpanExporter(endpoint=actual_otlp_endpoint, insecure=True) # type: ignore
            # BatchSpanProcessor is recommended for production (batches spans before sending)
            otlp_processor = BatchSpanProcessor(otlp_exporter) # type: ignore
            provider.add_span_processor(otlp_processor)
            logger.info(f"Configured OTLPSpanExporter to endpoint: {actual_otlp_endpoint}")
            exporters_configured = True
        except Exception as e:
            logger.error(f"Failed to configure OTLPSpanExporter to '{actual_otlp_endpoint}': {e}")
    elif use_otlp_exporter:
        logger.warning("OTLP exporter requested but no endpoint provided (otlp_endpoint param or OTEL_EXPORTER_OTLP_ENDPOINT env var).")


    if not exporters_configured:
        logger.warning("No tracing exporters were configured. Spans will be created but not sent anywhere.")
        # Still set the provider so manual instrumentation doesn't fail, but it won't do much.
        trace.set_tracer_provider(provider)
        return trace.get_tracer(service_name, service_version)


    # 4. Set the global TracerProvider
    trace.set_tracer_provider(provider)

    # 5. Get a Tracer instance
    # It's common practice to use the instrumenting library's name as the tracer name.
    tracer = trace.get_tracer(service_name, service_version)
    logger.info(f"OpenTelemetry tracing initialized for service: '{service_name}'.")
    return tracer

def instrument_libraries_placeholder():
    """
    Placeholder for applying auto-instrumentation to common libraries.
    This should be called once, after `init_tracing`.
    """
    if not OPENTELEMETRY_AVAILABLE:
        return

    logger.info("Conceptual: Applying OpenTelemetry auto-instrumentation for libraries...")
    # Examples (uncomment and install corresponding opentelemetry-instrumentation-* package):
    # try:
    #     from opentelemetry.instrumentation.requests import RequestsInstrumentor
    #     RequestsInstrumentor().instrument()
    #     logger.info("  - Requests library instrumented.")
    # except ImportError:
    #     logger.warning("  - opentelemetry-instrumentation-requests not found. Skipping requests instrumentation.")
    #
    # try:
    #     from opentelemetry.instrumentation.flask import FlaskInstrumentor
    #     # If Devin uses Flask for an API: FlaskInstrumentor().instrument_app(app)
    #     logger.info("  - Flask instrumentation would be applied here if app instance available.")
    # except ImportError:
    #     logger.warning("  - opentelemetry-instrumentation-flask not found.")
    logger.info("  - Conceptual auto-instrumentation applied (actual libraries commented out).")


# --- Example functions demonstrating manual span creation ---
def perform_example_task(tracer: Optional[trace.Tracer], task_name: str, task_input: str): # type: ignore
    """Simulates performing a task with manual OpenTelemetry spans."""
    if not tracer:
        logger.warning(f"No tracer available for '{task_name}'. Performing task without tracing.")
        time.sleep(random.uniform(0.1, 0.5)) # Simulate work
        return f"Task '{task_name}' completed without tracing."

    # Start a new span. This span becomes the "current span" for its duration.
    with tracer.start_as_current_span(f"Task: {task_name}") as parent_span:
        logger.info(f"Span '{parent_span.get_span_context().span_id}' started for task: {task_name}")
        parent_span.set_attribute("task.name", task_name)
        parent_span.set_attribute("task.input_length", len(task_input))

        try:
            # Simulate sub-operations
            time.sleep(random.uniform(0.05, 0.2))
            with tracer.start_as_current_span("SubOperation_Validation") as child_span_1:
                child_span_1.add_event("Validation started", {"input_preview": task_input[:10]})
                time.sleep(random.uniform(0.02, 0.1))
                if len(task_input) < 3:
                    raise ValueError("Task input too short for validation.")
                child_span_1.set_attribute("validation.result", "passed")
                child_span_1.add_event("Validation completed")

            time.sleep(random.uniform(0.05, 0.3))
            with tracer.start_as_current_span("SubOperation_Processing") as child_span_2:
                child_span_2.set_attribute("processing.complexity", random.choice(["low", "medium", "high"]))
                # Simulate an external call that would be auto-instrumented if requests is instrumented
                # if requests: requests.get("http://example.com", timeout=0.1) # Conceptual
                time.sleep(random.uniform(0.1, 0.5))
                child_span_2.add_event("Processing core logic finished")

            result_data = f"Processed result for {task_name} with input '{task_input}'"
            parent_span.set_attribute("task.output_length", len(result_data))
            parent_span.set_status(trace.Status(trace.StatusCode.OK)) # Mark span as successful
            return result_data

        except Exception as e:
            logger.error(f"Error during task '{task_name}': {e}")
            if parent_span: # Check if span was created
                parent_span.set_status(trace.Status(trace.StatusCode.ERROR, f"Error: {str(e)}"))
                parent_span.record_exception(e) # Records exception details on the span
            raise # Re-raise the exception if needed

# Example Usage
if __name__ == "__main__":
    print("=========================================================")
    print("=== Running Distributed Tracing Setup Prototype (OTel) ===")
    print("=========================================================")

    if not OPENTELEMETRY_AVAILABLE:
        print("\n'opentelemetry' libraries not found. Tracing functionality will be disabled.")
        print("Please install them: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc")
    else:
        # Initialize tracing for the "DevinMainApp" service
        # To send to Jaeger/Collector via OTLP, ensure it's running and set OTEL_EXPORTER_OTLP_ENDPOINT
        # e.g., export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
        # For this example, we'll primarily use the console exporter.
        devin_tracer = init_tracing(
            service_name="DevinExampleService",
            service_version="1.0-demo",
            otlp_endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"), # Use env var if set
            use_console_exporter=True,
            use_otlp_exporter=bool(os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")) # Only enable if endpoint is there
        )

        # Apply auto-instrumentation (conceptual)
        instrument_libraries_placeholder()

        if devin_tracer:
            print("\nOpenTelemetry tracing initialized. Performing some example tasks...")
            print("If ConsoleSpanExporter is active, you should see span details printed below.")
            print("If OTLP exporter is active and an OTel collector/Jaeger is running, traces will be sent there.")

            try:
                perform_example_task(devin_tracer, "UserQueryProcessing", "What is the weather in Lahore?")
                perform_example_task(devin_tracer, "CodeGeneration", "Create a python function for fibonacci")
                perform_example_task(devin_tracer, "ShortTask", "Hi") # This one will fail validation
            except ValueError as e:
                logger.info(f"Caught expected ValueError from task: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred during example tasks: {e}")

            print("\nExample tasks completed. Check console output or your tracing backend.")
            # In a real application, tracing is initialized once at startup.
            # Spans are created around operations throughout the codebase.
            # The application would then run its normal course.
            # For this demo, we'll just wait a moment for BatchSpanProcessor to potentially send traces.
            if _TRACER_PROVIDER and hasattr(_TRACER_PROVIDER, 'shutdown'):
                logger.info("Shutting down TracerProvider to flush any pending spans...")
                _TRACER_PROVIDER.shutdown() # type: ignore
                logger.info("TracerProvider shutdown complete.")
        else:
            logger.warning("Tracer could not be initialized. Skipping example tasks.")

    print("\n=========================================================")
    print("=== Distributed Tracing Setup Prototype Complete ===")
    print("=========================================================")
