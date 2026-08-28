"""
scripts/robot_manager_web_cli.py

Robot Management Web App Command Line Interface (CLI) script
This script provides CLI access to manage robot operations via a web-based API.
"""

import argparse
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = os.getenv("ROBOT_API_BASE_URL", "http://localhost:8000/api")

# Utility functions
def make_request(endpoint, method="GET", data=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    try:
        if method.upper() == "POST":
            response = requests.post(url, headers=headers, data=json.dumps(data))
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, data=json.dumps(data))
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            response = requests.get(url, headers=headers)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


# CLI command handlers
def list_robots():
    """List all robots managed by the web app."""
    response = make_request("robots")
    if response:
        print("Robots:")
        for robot in response.get("data", []):
            print(f"- ID: {robot['id']}, Name: {robot['name']}, Status: {robot['status']}")
    else:
        print("Failed to retrieve robots.")


def get_robot_details(robot_id):
    """Get detailed information about a specific robot."""
    response = make_request(f"robots/{robot_id}")
    if response:
        print("Robot Details:")
        print(json.dumps(response, indent=4))
    else:
        print(f"Failed to retrieve details for robot ID {robot_id}.")


def add_robot(name, model, capabilities):
    """Add a new robot to the management system."""
    data = {
        "name": name,
        "model": model,
        "capabilities": capabilities.split(","),
    }
    response = make_request("robots", method="POST", data=data)
    if response:
        print("Robot added successfully!")
    else:
        print("Failed to add robot.")


def update_robot(robot_id, name=None, status=None):
    """Update robot details."""
    data = {"name": name, "status": status}
    response = make_request(f"robots/{robot_id}", method="PUT", data=data)
    if response:
        print("Robot updated successfully!")
    else:
        print(f"Failed to update robot ID {robot_id}.")


def delete_robot(robot_id):
    """Delete a robot from the system."""
    response = make_request(f"robots/{robot_id}", method="DELETE")
    if response:
        print("Robot deleted successfully!")
    else:
        print(f"Failed to delete robot ID {robot_id}.")


def execute_command(robot_id, command):
    """Send a command to a robot."""
    data = {"command": command}
    response = make_request(f"robots/{robot_id}/execute", method="POST", data=data)
    if response:
        print(f"Command executed: {response.get('message')}")
    else:
        print(f"Failed to execute command for robot ID {robot_id}.")


# Main function
def main():
    parser = argparse.ArgumentParser(description="Robot Management Web App CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command: list
    subparsers.add_parser("list", help="List all robots")

    # Sub-command: details
    details_parser = subparsers.add_parser("details", help="Get details of a specific robot")
    details_parser.add_argument("robot_id", type=str, help="Robot ID")

    # Sub-command: add
    add_parser = subparsers.add_parser("add", help="Add a new robot")
    add_parser.add_argument("name", type=str, help="Robot name")
    add_parser.add_argument("model", type=str, help="Robot model")
    add_parser.add_argument("capabilities", type=str, help="Comma-separated list of robot capabilities")

    # Sub-command: update
    update_parser = subparsers.add_parser("update", help="Update robot details")
    update_parser.add_argument("robot_id", type=str, help="Robot ID")
    update_parser.add_argument("--name", type=str, help="New name for the robot")
    update_parser.add_argument("--status", type=str, choices=["active", "inactive"], help="New status for the robot")

    # Sub-command: delete
    delete_parser = subparsers.add_parser("delete", help="Delete a robot")
    delete_parser.add_argument("robot_id", type=str, help="Robot ID")

    # Sub-command: execute
    execute_parser = subparsers.add_parser("execute", help="Send a command to a robot")
    execute_parser.add_argument("robot_id", type=str, help="Robot ID")
    execute_parser.add_argument("command", type=str, help="Command to execute")

    # Parse arguments and call appropriate function
    args = parser.parse_args()
    if args.command == "list":
        list_robots()
    elif args.command == "details":
        get_robot_details(args.robot_id)
    elif args.command == "add":
        add_robot(args.name, args.model, args.capabilities)
    elif args.command == "update":
        update_robot(args.robot_id, name=args.name, status=args.status)
    elif args.command == "delete":
        delete_robot(args.robot_id)
    elif args.command == "execute":
        execute_command(args.robot_id, args.command)


if __name__ == "__main__":
    main()
