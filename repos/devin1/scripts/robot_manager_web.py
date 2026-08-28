from flask import Flask, render_template, request, jsonify
from robot_manager_api import RobotManagerAPI
import logging
import os

# Initialize the Flask application
app = Flask(__name__)
robot_api = RobotManagerAPI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("robot_manager_web.log"),
        logging.StreamHandler()
    ]
)

# Routes

@app.route("/")
def index():
    """Render the homepage."""
    try:
        return render_template("index.html", title="Robot Management Web App")
    except Exception as e:
        logging.error(f"Error rendering index page: {e}")
        return "An error occurred while loading the page.", 500

@app.route("/robots", methods=["GET"])
def list_robots():
    """Fetch and display all connected robots."""
    try:
        robots = robot_api.get_all_robots()
        return jsonify(robots)
    except Exception as e:
        logging.error(f"Error fetching robot list: {e}")
        return jsonify({"error": "Failed to fetch robots"}), 500

@app.route("/robot/<robot_id>", methods=["GET"])
def get_robot(robot_id):
    """Fetch details of a specific robot."""
    try:
        robot = robot_api.get_robot(robot_id)
        return jsonify(robot)
    except Exception as e:
        logging.error(f"Error fetching robot details for ID {robot_id}: {e}")
        return jsonify({"error": "Failed to fetch robot details"}), 500

@app.route("/robot/<robot_id>/execute", methods=["POST"])
def execute_command(robot_id):
    """Execute a command on a robot."""
    try:
        command = request.json.get("command")
        if not command:
            return jsonify({"error": "Command is required"}), 400
        result = robot_api.execute_command(robot_id, command)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error executing command on robot {robot_id}: {e}")
        return jsonify({"error": "Failed to execute command"}), 500

@app.route("/robot/<robot_id>/update", methods=["POST"])
def update_robot(robot_id):
    """Update a robot's firmware."""
    try:
        firmware_version = request.json.get("firmware_version")
        if not firmware_version:
            return jsonify({"error": "Firmware version is required"}), 400
        result = robot_api.update_firmware(robot_id, firmware_version)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error updating firmware for robot {robot_id}: {e}")
        return jsonify({"error": "Failed to update firmware"}), 500

@app.route("/robot/<robot_id>/config", methods=["POST"])
def configure_robot(robot_id):
    """Configure a robot."""
    try:
        configuration = request.json
        if not configuration:
            return jsonify({"error": "Configuration data is required"}), 400
        result = robot_api.configure_robot(robot_id, configuration)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error configuring robot {robot_id}: {e}")
        return jsonify({"error": "Failed to configure robot"}), 500

@app.route("/logs", methods=["GET"])
def fetch_logs():
    """Fetch system logs."""
    try:
        with open("robot_manager_web.log", "r") as log_file:
            logs = log_file.read()
        return jsonify({"logs": logs})
    except Exception as e:
        logging.error(f"Error fetching logs: {e}")
        return jsonify({"error": "Failed to fetch logs"}), 500

# Run the application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
