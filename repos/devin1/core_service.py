"""
core_service.py

This module serves as the backbone of the Devin project. It initializes core services, manages APIs,
and acts as a mediator between different components of the project.
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from modules.ai_module import AIModule
from modules.device_control import DeviceController
from modules.analytics import AnalyticsModule
from modules.cloud_service import CloudService
from modules.security_manager import SecurityManager
from modules.system_monitor import SystemMonitor

# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DevinCoreService")

# Flask App for Core API
app = Flask(__name__)

# Global service instances
ai_module = AIModule()
device_controller = DeviceController()
analytics_module = AnalyticsModule()
cloud_service = CloudService()
security_manager = SecurityManager()
system_monitor = SystemMonitor()

# Thread pool executor for handling concurrent tasks
executor = ThreadPoolExecutor(max_workers=20)

# Route: Health check
@app.route("/health", methods=["GET"])
def health_check():
    """Check if the core service is running."""
    return jsonify({"status": "healthy", "message": "Core service is running"}), 200

# Route: AI Interaction
@app.route("/ai", methods=["POST"])
def ai_interact():
    """Handle AI-based tasks."""
    data = request.json
    task = data.get("task", "")
    context = data.get("context", {})
    try:
        response = ai_module.process_task(task, context)
        return jsonify({"status": "success", "response": response}), 200
    except Exception as e:
        logger.error(f"AI Interaction failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Route: Device Control
@app.route("/device", methods=["POST"])
def control_device():
    """Handle device control operations."""
    data = request.json
    command = data.get("command", "")
    device_id = data.get("device_id", "")
    try:
        result = device_controller.execute_command(device_id, command)
        return jsonify({"status": "success", "result": result}), 200
    except Exception as e:
        logger.error(f"Device control error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Route: Analytics
@app.route("/analytics", methods=["GET"])
def get_analytics():
    """Fetch analytics data."""
    try:
        data = analytics_module.fetch_data()
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logger.error(f"Analytics retrieval error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Route: Security Management
@app.route("/security", methods=["POST"])
def manage_security():
    """Handle security tasks like threat analysis and management."""
    data = request.json
    action = data.get("action", "")
    params = data.get("params", {})
    try:
        result = security_manager.handle_action(action, params)
        return jsonify({"status": "success", "result": result}), 200
    except Exception as e:
        logger.error(f"Security management error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Route: System Monitoring
@app.route("/system", methods=["GET"])
def monitor_system():
    """Get system monitoring metrics."""
    try:
        metrics = system_monitor.get_metrics()
        return jsonify({"status": "success", "metrics": metrics}), 200
    except Exception as e:
        logger.error(f"System monitoring error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Route: Cloud Services
@app.route("/cloud", methods=["POST"])
def cloud_operations():
    """Manage cloud services and operations."""
    data = request.json
    operation = data.get("operation", "")
    params = data.get("params", {})
    try:
        response = cloud_service.perform_operation(operation, params)
        return jsonify({"status": "success", "response": response}), 200
    except Exception as e:
        logger.error(f"Cloud operation error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Background Service Initialization
def initialize_services():
    """Initialize all core services in the background."""
    try:
        logger.info("Initializing AI Module...")
        ai_module.initialize()

        logger.info("Initializing Device Controller...")
        device_controller.initialize()

        logger.info("Initializing Analytics Module...")
        analytics_module.initialize()

        logger.info("Initializing Cloud Service...")
        cloud_service.initialize()

        logger.info("Initializing Security Manager...")
        security_manager.initialize()

        logger.info("Initializing System Monitor...")
        system_monitor.initialize()

        logger.info("All services initialized successfully.")
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")

# Main Execution
if __name__ == "__main__":
    logger.info("Starting Core Service...")
    threading.Thread(target=initialize_services).start()
    app.run(host="0.0.0.0", port=8080, debug=False)
