"""
scripts/robot_manager_api.py
----------------------------
This script provides a RESTful API interface for managing and controlling robots.
It enables external applications to interact with robot configurations, operations,
and status monitoring via HTTP requests.
"""

from flask import Flask, request, jsonify
import logging
import os
import json
from modules.robotics.robot_manager import RobotManager

app = Flask(__name__)
robot_manager = RobotManager()

# Configure logging
log_file = "logs/robot_manager_api.log"
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

@app.route('/api/v1/robots', methods=['GET'])
def get_all_robots():
    """
    Retrieve a list of all registered robots and their details.
    """
    try:
        robots = robot_manager.list_robots()
        logging.info("Fetched all robots.")
        return jsonify({"status": "success", "data": robots}), 200
    except Exception as e:
        logging.error(f"Error fetching robots: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/robots/<robot_id>', methods=['GET'])
def get_robot(robot_id):
    """
    Retrieve details of a specific robot.
    """
    try:
        robot = robot_manager.get_robot_details(robot_id)
        if robot:
            logging.info(f"Fetched details for robot ID: {robot_id}.")
            return jsonify({"status": "success", "data": robot}), 200
        else:
            logging.warning(f"Robot ID {robot_id} not found.")
            return jsonify({"status": "error", "message": "Robot not found"}), 404
    except Exception as e:
        logging.error(f"Error fetching robot {robot_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/robots', methods=['POST'])
def register_robot():
    """
    Register a new robot.
    """
    try:
        data = request.json
        robot_id = robot_manager.register_robot(data)
        logging.info(f"Registered new robot with ID: {robot_id}.")
        return jsonify({"status": "success", "robot_id": robot_id}), 201
    except Exception as e:
        logging.error(f"Error registering robot: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/v1/robots/<robot_id>/start', methods=['POST'])
def start_robot(robot_id):
    """
    Start a specific robot.
    """
    try:
        robot_manager.start_robot(robot_id)
        logging.info(f"Started robot ID: {robot_id}.")
        return jsonify({"status": "success", "message": f"Robot {robot_id} started"}), 200
    except Exception as e:
        logging.error(f"Error starting robot {robot_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/v1/robots/<robot_id>/stop', methods=['POST'])
def stop_robot(robot_id):
    """
    Stop a specific robot.
    """
    try:
        robot_manager.stop_robot(robot_id)
        logging.info(f"Stopped robot ID: {robot_id}.")
        return jsonify({"status": "success", "message": f"Robot {robot_id} stopped"}), 200
    except Exception as e:
        logging.error(f"Error stopping robot {robot_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/v1/robots/<robot_id>', methods=['DELETE'])
def delete_robot(robot_id):
    """
    Delete a specific robot from the system.
    """
    try:
        robot_manager.delete_robot(robot_id)
        logging.info(f"Deleted robot ID: {robot_id}.")
        return jsonify({"status": "success", "message": f"Robot {robot_id} deleted"}), 200
    except Exception as e:
        logging.error(f"Error deleting robot {robot_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/v1/status', methods=['GET'])
def api_status():
    """
    Check the status of the API service.
    """
    return jsonify({"status": "success", "message": "Robot Manager API is running"}), 200

if __name__ == "__main__":
    logging.info("Starting Robot Manager API...")
    app.run(host='0.0.0.0', port=5000, debug=True)
