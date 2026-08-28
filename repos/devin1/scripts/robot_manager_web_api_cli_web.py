"""
scripts/robot_manager_web_api_cli_web.py
========================================
This script integrates robot management functionalities for web app, API, and CLI systems.
"""

import argparse
import flask
from flask import Flask, jsonify, request
from concurrent.futures import ThreadPoolExecutor
import threading

# Flask App for Web Interface
app = Flask(__name__)

# Robot state and operations
robot_state = {
    "status": "idle",
    "tasks": []
}

# Thread-safe lock for state modifications
state_lock = threading.Lock()

# Initialize Flask API
@app.route('/api/status', methods=['GET'])
def get_status():
    """API Endpoint: Get robot status."""
    with state_lock:
        return jsonify(robot_state)

@app.route('/api/task', methods=['POST'])
def add_task():
    """API Endpoint: Add a new task to the robot."""
    task = request.json.get('task')
    if not task:
        return jsonify({"error": "Task not provided"}), 400
    with state_lock:
        robot_state["tasks"].append(task)
        robot_state["status"] = "task_added"
    return jsonify({"message": "Task added", "current_tasks": robot_state["tasks"]})

# CLI Interface
def cli_interface():
    """Command-line interface for managing the robot."""
    parser = argparse.ArgumentParser(description="Robot Management CLI")
    parser.add_argument('--status', action='store_true', help="Check robot status")
    parser.add_argument('--add-task', type=str, help="Add a new task to the robot")
    
    args = parser.parse_args()
    if args.status:
        with state_lock:
            print("Robot Status:", robot_state["status"])
            print("Tasks:", robot_state["tasks"])
    if args.add_task:
        with state_lock:
            robot_state["tasks"].append(args.add_task)
            robot_state["status"] = "task_added"
        print(f"Task '{args.add_task}' added successfully.")

# Web Interface
@app.route('/')
def web_dashboard():
    """Main Web Dashboard for robot management."""
    with state_lock:
        return f"""
        <html>
        <head><title>Robot Manager</title></head>
        <body>
        <h1>Robot Management Dashboard</h1>
        <p>Status: {robot_state['status']}</p>
        <h2>Tasks:</h2>
        <ul>
            {''.join(f'<li>{task}</li>' for task in robot_state['tasks'])}
        </ul>
        </body>
        </html>
        """

# Threaded Flask Execution
def run_web_app():
    """Run the web app in a separate thread."""
    app.run(port=5000, debug=False)

if __name__ == '__main__':
    executor = ThreadPoolExecutor(max_workers=2)
    executor.submit(run_web_app)
    cli_interface()
