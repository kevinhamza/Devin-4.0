"""
Robot Management CLI Tool
=========================
This script provides a Command-Line Interface (CLI) for managing robot configurations, operations, and status checks.
"""

import argparse
import json
import os
from datetime import datetime
from modules.robotics.diagnostic_tools import run_diagnostics
from scripts.update_firmware import update_robot_firmware
from scripts.robot_configurator import configure_robot

LOG_FILE = "logs/robot_manager_cli.log"

def log_action(action, status, details=""):
    """
    Logs actions and results to a log file.
    """
    with open(LOG_FILE, "a") as log:
        log_entry = f"{datetime.now()} | ACTION: {action} | STATUS: {status} | DETAILS: {details}\n"
        log.write(log_entry)

def load_robot_data(file_path):
    """
    Loads robot data from a configuration file.
    """
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        log_action("LOAD DATA", "FAILED", f"File not found: {file_path}")
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    except json.JSONDecodeError:
        log_action("LOAD DATA", "FAILED", "Invalid JSON format.")
        raise ValueError("Invalid JSON format in configuration file.")

def handle_configure(args):
    """
    Handles the robot configuration process.
    """
    try:
        configure_robot(args.config_file)
        log_action("CONFIGURE ROBOT", "SUCCESS", f"Config file: {args.config_file}")
        print("Robot configuration completed successfully.")
    except Exception as e:
        log_action("CONFIGURE ROBOT", "FAILED", str(e))
        print(f"Error configuring robot: {e}")

def handle_update_firmware(args):
    """
    Handles firmware updates for the robot.
    """
    try:
        update_robot_firmware(args.firmware_version)
        log_action("UPDATE FIRMWARE", "SUCCESS", f"Version: {args.firmware_version}")
        print(f"Firmware updated to version {args.firmware_version}.")
    except Exception as e:
        log_action("UPDATE FIRMWARE", "FAILED", str(e))
        print(f"Error updating firmware: {e}")

def handle_diagnostics(args):
    """
    Handles running diagnostics on the robot.
    """
    try:
        results = run_diagnostics(args.diagnostic_level)
        log_action("RUN DIAGNOSTICS", "SUCCESS", f"Level: {args.diagnostic_level}")
        print("Diagnostics completed successfully.")
        print("Results:")
        print(json.dumps(results, indent=4))
    except Exception as e:
        log_action("RUN DIAGNOSTICS", "FAILED", str(e))
        print(f"Error running diagnostics: {e}")

def main():
    parser = argparse.ArgumentParser(description="Robot Management CLI Tool")
    subparsers = parser.add_subparsers(title="commands", description="Available commands", dest="command")

    # Configure Command
    parser_configure = subparsers.add_parser("configure", help="Configure the robot")
    parser_configure.add_argument("config_file", type=str, help="Path to the configuration file")
    parser_configure.set_defaults(func=handle_configure)

    # Update Firmware Command
    parser_update = subparsers.add_parser("update", help="Update robot firmware")
    parser_update.add_argument("firmware_version", type=str, help="Target firmware version")
    parser_update.set_defaults(func=handle_update_firmware)

    # Run Diagnostics Command
    parser_diagnostics = subparsers.add_parser("diagnostics", help="Run diagnostics on the robot")
    parser_diagnostics.add_argument(
        "diagnostic_level", 
        choices=["basic", "intermediate", "advanced"], 
        help="Level of diagnostics to perform"
    )
    parser_diagnostics.set_defaults(func=handle_diagnostics)

    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
