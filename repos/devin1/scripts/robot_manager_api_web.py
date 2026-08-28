"""
scripts/robot_manager_api_web.py
Robot Management API Web App
This script sets up a Flask-based web application to manage robotic operations through APIs and a user-friendly web interface.
"""

from flask import Flask, jsonify, request, render_template
import os
import json
from robot_manager_api import RobotManagerAPI  # Assuming robot_manager_api.py is a module
from utils.logger import setup_logger  # Assuming a utility for setting up logging

app = Flask(__name__)

# Logger setup
logger = setup_logger("robot_manager_api_web", "logs/robot_manager_api_web.log")

# Initialize RobotManagerAPI
robot_manager = RobotManagerAPI()

@app.route('/')
def home():
    """Home page with an overview of API usage."""
    return render_template('index.html', title="Robot Management API", description="Manage your robots seamlessly.")

@app.route('/api/v1/robot/start', methods=['POST'])
def start_robot():
    """API endpoint to start a robot."""
    data = request.get_json()
    robot_id = data.get('robot_id')
    if not robot_id:
        logger.error("Robot ID not provided.")
        return jsonify({"error": "robot_id is required"}), 400
    try:
        result = robot_manager.start_robot(robot_id)
        logger.info(f"Robot {robot_id} started successfully.")
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        logger.error(f"Failed to start robot {robot_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/robot/stop', methods=['POST'])
def stop_robot():
    """API endpoint to stop a robot."""
    data = request.get_json()
    robot_id = data.get('robot_id')
    if not robot_id:
        logger.error("Robot ID not provided.")
        return jsonify({"error": "robot_id is required"}), 400
    try:
        result = robot_manager.stop_robot(robot_id)
        logger.info(f"Robot {robot_id} stopped successfully.")
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        logger.error(f"Failed to stop robot {robot_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/robot/status', methods=['GET'])
def robot_status():
    """API endpoint to get the status of a robot."""
    robot_id = request.args.get('robot_id')
    if not robot_id:
        logger.error("Robot ID not provided in query params.")
        return jsonify({"error": "robot_id is required"}), 400
    try:
        status = robot_manager.get_robot_status(robot_id)
        logger.info(f"Retrieved status for robot {robot_id}: {status}")
        return jsonify({"status": "success", "data": status}), 200
    except Exception as e:
        logger.error(f"Failed to get status for robot {robot_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/robots', methods=['GET'])
def list_robots():
    """Web interface to list all registered robots."""
    try:
        robots = robot_manager.list_robots()
        logger.info("Robot list retrieved successfully.")
        return render_template('robots.html', robots=robots, title="Registered Robots")
    except Exception as e:
        logger.error(f"Failed to retrieve robot list: {e}")
        return render_template('error.html', error=str(e), title="Error"), 500

@app.route('/api/v1/robot/register', methods=['POST'])
def register_robot():
    """API endpoint to register a new robot."""
    data = request.get_json()
    robot_id = data.get('robot_id')
    details = data.get('details')
    if not robot_id or not details:
        logger.error("Missing robot_id or details in the request body.")
        return jsonify({"error": "robot_id and details are required"}), 400
    try:
        result = robot_manager.register_robot(robot_id, details)
        logger.info(f"Robot {robot_id} registered successfully.")
        return jsonify({"status": "success", "data": result}), 201
    except Exception as e:
        logger.error(f"Failed to register robot {robot_id}: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = os.getenv("ROBOT_API_WEB_PORT", 8080)
    debug_mode = os.getenv("ROBOT_API_WEB_DEBUG", "False").lower() == "true"
    logger.info(f"Starting Robot Management API Web on port {port}.")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
