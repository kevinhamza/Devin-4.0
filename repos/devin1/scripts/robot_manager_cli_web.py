"""
scripts/robot_manager_cli_web.py
--------------------------------
Robot management CLI web app for controlling and monitoring robot operations via a web-based CLI interface.
"""

from flask import Flask, request, jsonify, render_template
import subprocess
import os
import logging
from threading import Thread

app = Flask(__name__)

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    handlers=[logging.FileHandler("robot_manager_cli_web.log"), logging.StreamHandler()]
)

# Commands storage for dynamic execution
COMMANDS = {
    "status": "robot_manager status",
    "start": "robot_manager start",
    "stop": "robot_manager stop",
    "restart": "robot_manager restart",
    "log": "robot_manager log"
}

@app.route("/")
def home():
    """
    Render the CLI web interface.
    """
    logging.info("Rendering the CLI web interface.")
    return render_template("cli_interface.html")


@app.route("/execute", methods=["POST"])
def execute_command():
    """
    Execute robot management commands.
    """
    data = request.json
    command = data.get("command", "").strip()
    if not command:
        logging.warning("No command provided in the request.")
        return jsonify({"error": "No command provided"}), 400

    if command not in COMMANDS:
        logging.error(f"Invalid command: {command}")
        return jsonify({"error": "Invalid command"}), 400

    try:
        logging.info(f"Executing command: {COMMANDS[command]}")
        output = subprocess.check_output(COMMANDS[command], shell=True, stderr=subprocess.STDOUT)
        return jsonify({"status": "success", "output": output.decode("utf-8")})
    except subprocess.CalledProcessError as e:
        logging.error(f"Command execution failed: {e.output.decode('utf-8')}")
        return jsonify({"status": "error", "output": e.output.decode("utf-8")})


def monitor_robot_logs():
    """
    Monitor and stream robot logs in real-time.
    """
    log_file = "/var/log/robot_manager.log"
    if not os.path.exists(log_file):
        logging.warning("Log file does not exist. Skipping log monitoring.")
        return

    with open(log_file, "r") as f:
        f.seek(0, os.SEEK_END)  # Go to the end of the file
        while True:
            line = f.readline()
            if line:
                logging.info(f"Log: {line.strip()}")


@app.route("/logs", methods=["GET"])
def fetch_logs():
    """
    Fetch robot logs.
    """
    log_file = "/var/log/robot_manager.log"
    try:
        logging.info("Fetching logs.")
        with open(log_file, "r") as file:
            logs = file.readlines()
        return jsonify({"logs": logs})
    except Exception as e:
        logging.error(f"Failed to fetch logs: {str(e)}")
        return jsonify({"error": "Failed to fetch logs"}), 500


if __name__ == "__main__":
    # Start the log monitoring thread
    logging.info("Starting robot manager CLI web app.")
    Thread(target=monitor_robot_logs, daemon=True).start()

    app.run(host="0.0.0.0", port=5000)
