"""
scripts/robot_manager_web_api.py
-------------------------------
Robot Management Web App API Project File.
This module provides API endpoints for managing and interacting with robots via a web interface.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import json
from utils.robot_manager_core import RobotManagerCore

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Robot Manager instance
robot_manager = RobotManagerCore()

@app.route('/api/robots', methods=['GET'])
def get_all_robots():
    """Endpoint to retrieve all registered robots."""
    try:
        robots = robot_manager.get_all_robots()
        return jsonify({"status": "success", "data": robots}), 200
    except Exception as e:
        logger.error(f"Error fetching robots: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to fetch robots"}), 500

@app.route('/api/robots/<robot_id>', methods=['GET'])
def get_robot(robot_id):
    """Endpoint to get details of a specific robot."""
    try:
        robot = robot_manager.get_robot(robot_id)
        if robot:
            return jsonify({"status": "success", "data": robot}), 200
        else:
            return jsonify({"status": "error", "message": "Robot not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching robot {robot_id}: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to fetch robot"}), 500

@app.route('/api/robots', methods=['POST'])
def add_robot():
    """Endpoint to add a new robot."""
    try:
        data = request.get_json()
        robot_name = data.get('name')
        robot_type = data.get('type')
        robot_specs = data.get('specs', {})
        if not robot_name or not robot_type:
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        robot_id = robot_manager.add_robot(robot_name, robot_type, robot_specs)
        return jsonify({"status": "success", "message": "Robot added successfully", "robot_id": robot_id}), 201
    except Exception as e:
        logger.error(f"Error adding robot: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to add robot"}), 500

@app.route('/api/robots/<robot_id>', methods=['PUT'])
def update_robot(robot_id):
    """Endpoint to update an existing robot."""
    try:
        data = request.get_json()
        updated = robot_manager.update_robot(robot_id, data)
        if updated:
            return jsonify({"status": "success", "message": "Robot updated successfully"}), 200
        else:
            return jsonify({"status": "error", "message": "Robot not found"}), 404
    except Exception as e:
        logger.error(f"Error updating robot {robot_id}: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to update robot"}), 500

@app.route('/api/robots/<robot_id>', methods=['DELETE'])
def delete_robot(robot_id):
    """Endpoint to delete a robot."""
    try:
        deleted = robot_manager.delete_robot(robot_id)
        if deleted:
            return jsonify({"status": "success", "message": "Robot deleted successfully"}), 200
        else:
            return jsonify({"status": "error", "message": "Robot not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting robot {robot_id}: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to delete robot"}), 500

@app.route('/api/robots/execute', methods=['POST'])
def execute_robot_task():
    """Endpoint to execute a task on a robot."""
    try:
        data = request.get_json()
        robot_id = data.get('robot_id')
        task = data.get('task')
        params = data.get('params', {})

        if not robot_id or not task:
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        result = robot_manager.execute_task(robot_id, task, params)
        return jsonify({"status": "success", "message": "Task executed successfully", "result": result}), 200
    except Exception as e:
        logger.error(f"Error executing task on robot: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to execute task"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
