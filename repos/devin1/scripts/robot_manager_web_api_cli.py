"""
scripts/robot_manager_web_api_cli.py

Robot Management Web App API Command Line Interface (CLI) script
This script provides CLI access to interact with the robot management web app's API endpoints.
"""

import argparse
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_API_URL = os.getenv("ROBOT_WEB_API_BASE_URL", "http://localhost:8000/api/v1")

# Utility function for API requests
def api_request(endpoint, method="GET", data=None):
    url = f"{BASE_API_URL}/{endpoint}"
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
    except requests.exceptions.RequestException as error:
        print(f"API Request Error: {error}")
        return None

# CLI Commands
def list_robots():
    """Retrieve a list of all robots via the API."""
    response = api_request("robots")
    if response:
        print("Robot List:")
        for robot in response.get("data", []):
            print(f"- ID: {robot['id']}, Name: {robot['name']}, Status: {robot['status']}")
    else:
        print("Failed to retrieve the robot list.")

def robot_details(robot_id):
    """Retrieve details of a specific robot by ID."""
    response = api_request(f"robots/{robot_id}")
    if response:
        print("Robot Details:")
        print(json.dumps(response, indent=4))
    else:
        print(f"Failed to retrieve details for Robot ID: {robot_id}")

def add_robot(name, model, capabilities):
    """Add a new robot via the API."""
    data = {
        "name": name,
        "model": model,
        "capabilities": capabilities.split(",")
    }
    response = api_request("robots", method="POST", data=data)
    if response:
        print(f"Robot '{name}' added successfully.")
    else:
        print("Failed to add the robot.")

def update_robot(robot_id, name=None, status=None):
    """Update an existing robot's details."""
    data = {"name": name, "status": status}
    response = api_request(f"robots/{robot_id}", method="PUT", data=data)
    if response:
        print(f"Robot ID {robot_id} updated successfully.")
    else:
        print(f"Failed to update Robot ID {robot_id}.")

def delete_robot(robot_id):
    """Delete a robot via the API."""
    response = api_request(f"robots/{robot_id}", method="DELETE")
    if response:
        print(f"Robot ID {robot_id} deleted successfully.")
    else:
        print(f"Failed to delete Robot ID {robot_id}.")

def execute_robot_command(robot_id, command):
    """Send a command to a robot via the API."""
    data = {"command": command}
    response = api_request(f"robots/{robot_id}/commands", method="POST", data=data)
    if response:
        print(f"Command executed: {response.get('message')}")
    else:
        print(f"Failed to execute command for Robot ID {robot_id}.")

# Main CLI
def main():
    parser = argparse.ArgumentParser(description="Robot Management Web API CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List robots
    subparsers.add_parser("list", help="List all robots")

    # Robot details
    details_parser = subparsers.add_parser("details", help="Get robot details by ID")
    details_parser.add_argument("robot_id", type=str, help="Robot ID")

    # Add robot
    add_parser = subparsers.add_parser("add", help="Add a new robot")
    add_parser.add_argument("name", type=str, help="Robot name")
    add_parser.add_argument("model", type=str, help="Robot model")
    add_parser.add_argument("capabilities", type=str, help="Comma-separated robot capabilities")

    # Update robot
    update_parser = subparsers.add_parser("update", help="Update robot details")
    update_parser.add_argument("robot_id", type=str, help="Robot ID")
    update_parser.add_argument("--name", type=str, help="New robot name")
    update_parser.add_argument("--status", type=str, choices=["active", "inactive"], help="New robot status")

    # Delete robot
    delete_parser = subparsers.add_parser("delete", help="Delete a robot")
    delete_parser.add_argument("robot_id", type=str, help="Robot ID")

    # Execute command
    command_parser = subparsers.add_parser("command", help="Execute a command on a robot")
    command_parser.add_argument("robot_id", type=str, help="Robot ID")
    command_parser.add_argument("command", type=str, help="Command to execute")

    # Parse arguments
    args = parser.parse_args()

    # Execute the appropriate function based on the sub-command
    if args.command == "list":
        list_robots()
    elif args.command == "details":
        robot_details(args.robot_id)
    elif args.command == "add":
        add_robot(args.name, args.model, args.capabilities)
    elif args.command == "update":
        update_robot(args.robot_id, name=args.name, status=args.status)
    elif args.command == "delete":
        delete_robot(args.robot_id)
    elif args.command == "command":
        execute_robot_command(args.robot_id, args.command)

if __name__ == "__main__":
    main()
