# Devin/infra/observability/loki_integration.py
# Purpose: Configure Python logging to send logs to Grafana Loki for aggregation.

import logging
import os
import sys
import time
import random
from typing import Dict, Optional, Tuple, Any

# --- Loki Logging Handler Import ---
# Requires: pip install python-logging-loki
try:
    from python_logging_loki import LokiHandler, LokiQueueHandler
    # LokiQueueHandler uses a background thread for sending logs, which is generally better for performance.
    PYTHON_LOGGING_LOKI_AVAILABLE = True
    print("Conceptual: 'python-logging-loki' library assumed available.")
except ImportError:
    PYTHON_LOGGING_LOKI_AVAILABLE = False
    print("WARNING: 'python-logging-loki' library not found. Loki integration will be non-functional.")
    # Define placeholders if library not found
    class LokiHandlerPlaceholder: # type: ignore
        def __init__(self, url, tags, auth, version, verify_ssl, **kwargs):
            logger.info(f"Loki Placeholder Handler Initialized: url={url}, tags={tags}")
        def handleError(self, record):
            logger.error("Loki Placeholder: Error in handling log record.")
    LokiHandler = LokiHandlerPlaceholder # type: ignore
    LokiQueueHandler = LokiHandlerPlaceholder # type: ignore


# Configure a basic logger for this module's own messages if needed
module_logger = logging.getLogger("LokiIntegrationSetup")
# Prevent duplicate logging if root logger is also configured by this module later
module_logger.propagate = False
if not module_logger.handlers:
    _console_handler = logging.StreamHandler(sys.stdout)
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    module_logger.addHandler(_console_handler)
    module_logger.setLevel(logging.INFO)


# Global variable to hold the configured Loki handler if needed for dynamic tag changes (advanced)
_loki_handler_instance: Optional[LokiQueueHandler] = None

def configure_loki_logging(
    loki_url: str,
    base_labels: Dict[str, str],
    app_logger_name: Optional[str] = "devin_app", # Name of the logger to attach Loki to
    log_level: int = logging.INFO,
    loki_version: str = "1",
    auth: Optional[Tuple[str, str]] = None, # (username, password) for Basic Auth
    verify_ssl: bool = True,
    use_queue_handler: bool = True,
    extra_handler_opts: Optional[Dict[str, Any]] = None
) -> Optional[logging.Handler]:
    """
    Configures and adds a Loki handler to the specified Python logger (or root logger).

    Args:
        loki_url (str): The URL to the Loki push API (e.g., "http://localhost:3100/loki/api/v1/push").
        base_labels (Dict[str, str]): Base labels to apply to all logs sent via this handler.
                                     Example: {"app": "devin", "environment": "production"}.
                                     Keep cardinality low for these labels.
        app_logger_name (Optional[str]): The name of the logger to configure.
                                         If None, configures the root logger.
        log_level (int): The minimum logging level for messages to be sent to Loki.
        loki_version (str): Loki API version, usually "1".
        auth (Optional[Tuple[str, str]]): Optional (username, password) for Basic Authentication.
        verify_ssl (bool): Whether to verify SSL certificates for the Loki endpoint.
        use_queue_handler (bool): If True, uses LokiQueueHandler for background sending. Recommended.
        extra_handler_opts (Optional[Dict[str, Any]]): Extra keyword arguments for the Loki handler.

    Returns:
        Optional[logging.Handler]: The configured Loki handler instance, or None if setup failed.
    """
    global _loki_handler_instance
    if not PYTHON_LOGGING_LOKI_AVAILABLE:
        module_logger.error("Cannot configure Loki logging: 'python-logging-loki' library not available.")
        return None

    if not loki_url:
        module_logger.error("Loki URL not provided. Cannot configure Loki logging.")
        return None

    handler_opts = {
        "url": loki_url,
        "tags": base_labels, # The 'tags' parameter in python-logging-loki sets the labels
        "auth": auth,
        "version": loki_version,
        "verify_ssl": verify_ssl,
        **(extra_handler_opts or {})
    }

    try:
        if use_queue_handler:
            # LokiQueueHandler handles sending logs in a background thread, which is non-blocking.
            # It has parameters like `max_retries`, `retry_timeout`, `queue_size`.
            loki_handler = LokiQueueHandler(**handler_opts) # type: ignore
        else:
            loki_handler = LokiHandler(**handler_opts) # type: ignore

        # Optional: Customize the log format sent to Loki.
        # Default format includes basic log record attributes.
        # For structured logging, you can add a custom formatter that outputs JSON
        # or ensures specific fields are present.
        # Example:
        # formatter = logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s", "extra_data": "%(custom_extra_data)s"}')
        # loki_handler.setFormatter(formatter)
        # Note: Loki primarily uses labels for querying, but structured log lines are good for readability.

        loki_handler.setLevel(log_level)

        # Get the target logger
        if app_logger_name:
            target_logger = logging.getLogger(app_logger_name)
        else:
            target_logger = logging.getLogger() # Root logger

        # Add the Loki handler to the target logger
        # Avoid adding multiple times if re-configured
        if not any(isinstance(h, (LokiHandler, LokiQueueHandler, LokiHandlerPlaceholder)) for h in target_logger.handlers): # type: ignore
            target_logger.addHandler(loki_handler)
            # Ensure the target logger itself has a level set to process messages
            if target_logger.level == logging.NOTSET or target_logger.level > log_level:
                target_logger.setLevel(log_level)
            module_logger.info(f"Loki logging handler configured for logger '{target_logger.name}' at URL '{loki_url}' with base labels {base_labels}.")
        else:
            module_logger.warning(f"Loki handler already present on logger '{target_logger.name}'. Skipping re-addition.")


        _loki_handler_instance = loki_handler # Store for potential dynamic updates (advanced)
        return loki_handler

    except Exception as e:
        module_logger.error(f"Failed to configure Loki logging handler: {e}", exc_info=True)
        return None

def get_devin_logger_with_loki_context(logger_name: str, contextual_labels: Optional[Dict[str, str]] = None) -> logging.LoggerAdapter:
    """
    Returns a LoggerAdapter that can add contextual labels to log messages for Loki.
    This assumes configure_loki_logging has already been called.

    Args:
        logger_name (str): The name of the logger to adapt.
        contextual_labels (Optional[Dict[str, str]]): Extra labels to add for logs from this adapter.
                                                      These are added to the `extra` dict of the log record.
                                                      The LokiHandler's formatter or a custom filter would need to
                                                      process these `extra` fields to convert them to Loki labels if dynamic labels
                                                      beyond the base_labels are desired per log message.
                                                      The `python-logging-loki` handler typically uses the 'tags' passed at init
                                                      as static labels. For dynamic labels per log message, you'd typically
                                                      pass them in `extra` and have a custom formatter or filter handle them,
                                                      or use a more advanced setup.

                                                      A simpler approach for dynamic *values* in logs is to include them
                                                      in the log message itself or as part of structured logging (e.g., JSON).
                                                      Loki queries primarily on the static labels set per stream.

    Returns:
        logging.LoggerAdapter: An adapter that can be used for logging.
    """
    base_logger = logging.getLogger(logger_name)
    extra_context = {"loki_context_labels": contextual_labels or {}}

    # For `python-logging-loki`, the primary way to set labels is via `tags` at handler init.
    # To add dynamic labels per log message, one might need to customize the handler or use a filter
    # to extract from `extra` and modify what's sent.
    # This adapter just shows how to pass `extra` data.
    adapter = logging.LoggerAdapter(base_logger, extra_context)
    return adapter


# Example Usage
if __name__ == "__main__":
    print("=========================================================")
    print("=== Running Loki Integration Prototype ===")
    print("=========================================================")

    if not PYTHON_LOGGING_LOKI_AVAILABLE:
        print("\n'python-logging-loki' library not found. Log messages will only go to console (if configured).")
        print("Please install it: pip install python-logging-loki")
        # Basic console logging setup if Loki isn't available, for demo purposes
        if not logging.getLogger().handlers: # Check if root logger has no handlers
             logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(custom_task_id)s')
    else:
        # --- Configuration ---
        # Get Loki URL from environment variable or use a default
        # For local testing, you can run Loki via Docker:
        # docker run -d --name=loki -p 3100:3100 grafana/loki:latest
        loki_push_url = os.environ.get("LOKI_URL", "http://localhost:3100/loki/api/v1/push")

        # Base labels for all logs from this Devin instance
        # Keep these labels low cardinality!
        devin_instance_id = os.environ.get("DEVIN_INSTANCE_ID", f"devin-dev-{random.randint(1000,9999)}")
        base_app_labels = {
            "app": "devin",
            "instance_id": devin_instance_id,
            "environment": os.environ.get("DEVIN_ENVIRONMENT", "development"),
            "source": "python_logger" # Differentiates from Promtail or other shippers
        }

        # Configure Loki for the root logger (or a specific application logger)
        # All subsequent `logging.info()`, `logging.error()`, etc., from configured loggers
        # will also go to Loki.
        loki_handler = configure_loki_logging(
            loki_url=loki_push_url,
            base_labels=base_app_labels,
            app_logger_name=None,  # Configure for root logger
            log_level=logging.DEBUG # Send DEBUG and above to Loki for this example
        )

        if loki_handler:
            module_logger.info(f"Loki logging configured. Sending test logs to {loki_push_url} with labels {base_app_labels}")
            # If using LokiQueueHandler, logs are sent in background. A small delay might be needed for them to appear.
        else:
            module_logger.error("Loki logging setup failed. Logs will not be sent to Loki.")

    # --- Test Logging ---
    # Get the root logger (since we configured it for None/root)
    # Or get a specific logger if app_logger_name was used in configure_loki_logging
    test_logger = logging.getLogger("devin.main_logic.example_module")
    test_logger.setLevel(logging.DEBUG) # Ensure this logger passes messages to handlers

    # Example of logging with 'extra' fields for structured data within the log message
    # (These 'extra' fields don't automatically become Loki labels with the default handler config,
    # but would be part of the log line content. Loki queries on the `base_labels`.)
    test_logger.info("Devin application starting up...", extra={"custom_event_type": "app_lifecycle", "phase": "startup"})
    time.sleep(0.1) # Small delay for queue handler

    for i in range(3):
        task_id = f"task-{uuid.uuid4().hex[:6]}"
        user_id = f"user-{random.randint(100,200)}"
        test_logger.debug(
            f"Processing item {i} for task.",
            extra={"task_id": task_id, "user_id": user_id, "item_index": i}
        )
        time.sleep(0.05)
        if i % 2 == 0:
            test_logger.warning(
                "Potential issue detected during processing.",
                extra={"task_id": task_id, "user_id": user_id, "warning_code": "W001"}
            )
            time.sleep(0.05)

    try:
        x = 1 / 0
    except ZeroDivisionError:
        test_logger.error(
            "A critical error occurred: Division by zero!",
            exc_info=True, # Includes stack trace in the log
            extra={"error_code": "E500", "context": "critical_calculation"}
        )
    time.sleep(0.1)

    # Using the LoggerAdapter example (for passing contextual labels to be handled by custom formatter/filter if set up)
    # Note: `python-logging-loki` primarily uses the initial `tags` for labels.
    # Dynamic labels per message via `extra` require more advanced handler customization.
    context_logger = get_devin_logger_with_loki_context(
        "devin.specific_service",
        contextual_labels={"service_id": "auth_service", "region": "us-east-1"}
    )
    context_logger.info("User authentication attempt.", extra={"user_id": "user_abc", "auth_method": "password"})
    time.sleep(0.1)


    module_logger.info("Test logs sent. Check your Loki instance with labels like "
                f"{{app=\"devin\", instance_id=\"{base_app_labels['instance_id']}\"}}")
    module_logger.info("If using LokiQueueHandler, allow a few moments for logs to be flushed.")

    # If using LokiQueueHandler, it's good practice to properly close it on application shutdown
    # This ensures any buffered logs are sent.
    if _loki_handler_instance and isinstance(_loki_handler_instance, LokiQueueHandler): # type: ignore
        module_logger.info("Flushing and closing LokiQueueHandler...")
        _loki_handler_instance.close() # type: ignore
        module_logger.info("LokiQueueHandler closed.")


    print("\n=========================================================")
    print("=== Loki Integration Prototype Complete ===")
    print("=========================================================")
