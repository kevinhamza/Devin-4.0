# Devin/scripts/robot_manager.py
# Purpose: A command-line interface for managing the Devin robot's
#          software stack and operational state.

import argparse
import os
import sys
import subprocess
import json
from pathlib import Path
import time

# --- Add project root to Python path ---
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from modules.user_interaction_module import UserInteractionManager

# --- Configuration ---
PID_FILE = Path(os.getenv("TMPDIR", "/tmp")) / "devin_robot.pid"
ROS2_LAUNCH_FILE = "devin_robot.launch.py"
ROS2_PACKAGE_NAME = "devin_robot_pkg" # A conceptual package name

class RobotManager:
    """Encapsulates the logic for managing the robot's software."""

    def __init__(self):
        self.uim = UserInteractionManager()

    def _is_running(self) -> bool:
        """Checks if the robot stack is running by checking the PID file."""
        if not PID_FILE.exists():
            return False
        
        pid_str = PID_FILE.read_text().strip()
        if not pid_str.isdigit():
            return False
        
        pid = int(pid_str)
        # Check if a process with this PID exists
        try:
            os.kill(pid, 0) # Signal 0 doesn't kill but checks for existence
        except OSError:
            # Process does not exist, so clean up the stale PID file
            PID_FILE.unlink()
            return False
        else:
            return True

    def start(self):
        """Starts the main ROS 2 launch file in the background."""
        if self._is_running():
            pid = PID_FILE.read_text().strip()
            self.uim.display_message(f"Robot stack is already running with PID {pid}.", level='warning')
            return

        self.uim.display_message("Starting Devin robot software stack...")
        
        # Check if the ROS 2 environment is sourced
        if "ROS_DISTRO" not in os.environ:
            self.uim.display_message("ROS 2 environment not sourced. Please source your ROS 2 setup file (e.g., `source /opt/ros/humble/setup.bash`) and try again.", level='error')
            return

        command = ["ros2", "launch", ROS2_PACKAGE_NAME, ROS2_LAUNCH_FILE]
        try:
            # Start the process in the background, detaching it from this script
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            PID_FILE.write_text(str(process.pid))
            time.sleep(2) # Give it a moment to stabilize
            if process.poll() is None:
                self.uim.display_message(f"Robot stack started successfully with PID {process.pid}.", level='success')
            else:
                self.uim.display_message("Failed to start the robot stack. Check ROS 2 logs for errors.", level='error')
                PID_FILE.unlink()
        except FileNotFoundError:
            self.uim.display_message("`ros2` command not found. Is ROS 2 installed and sourced?", level='error')
        except Exception as e:
            self.uim.display_message(f"An error occurred while starting the robot stack: {e}", level='error')

    def stop(self):
        """Stops the running robot stack."""
        if not self._is_running():
            self.uim.display_message("Robot stack is not currently running.", level='info')
            return
        
        pid = int(PID_FILE.read_text().strip())
        self.uim.display_message(f"Stopping robot stack (PID {pid})...")
        try:
            # Send SIGTERM to the process and all its children
            os.killpg(os.getpgid(pid), 15)
            time.sleep(2)
            # Check if it stopped
            os.kill(pid, 0)
            self.uim.display_message("Process did not stop gracefully. Sending SIGKILL...", level='warning')
            os.killpg(os.getpgid(pid), 9)
        except OSError:
            # This is expected if the process terminated successfully
            pass
        
        PID_FILE.unlink()
        self.uim.display_message("Robot stack stopped successfully.", level='success')

    def status(self):
        """Checks and reports the status of the robot stack."""
        if self._is_running():
            pid = PID_FILE.read_text().strip()
            self.uim.display_message(f"Devin Robot Stack is RUNNING with PID {pid}.", level='success')
            
            # Bonus: provide more detailed ROS 2 status
            print("\n--- Checking ROS 2 Nodes ---")
            subprocess.run(["ros2", "node", "list"])
            print("\n--- Checking ROS 2 Topics ---")
            subprocess.run(["ros2", "topic", "list"])
        else:
            self.uim.display_message("Devin Robot Stack is STOPPED.", level='info')

    def reboot(self):
        """Reboots the robot's host machine."""
        if self.uim.ask_for_confirmation("This will reboot the entire robot computer. Are you sure?", is_dangerous=True):
            self.uim.display_message("Rebooting system now...", level='warning')
            try:
                # This command requires sudo privileges
                subprocess.run(["sudo", "reboot"], check=True)
            except Exception as e:
                self.uim.display_message(f"Failed to reboot. Make sure you have sudo privileges. Error: {e}", level='error')

    def teleop(self):
        """Launches the keyboard remote control interface."""
        self.uim.display_message("Launching keyboard teleoperation interface...")
        self.uim.display_message("Press Ctrl+C in this window to exit teleop mode.", level='info')
        try:
            # Assuming remote_control.py is in the modules/robotics directory
            remote_control_script = project_root / "modules" / "robotics" / "remote_control.py"
            subprocess.run([sys.executable, str(remote_control_script)], check=True)
        except FileNotFoundError:
             self.uim.display_message("remote_control.py script not found.", level='error')
        except KeyboardInterrupt:
            self.uim.display_message("\nTeleoperation stopped by user.", level='info')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Devin Robot Manager: A CLI to control the robot's software stack.",
        epilog="""
    --- CONCEPTUAL ROS 2 LAUNCH FILE (`devin_robot.launch.py`) ---
    This manager is designed to launch a master ROS 2 file. A simplified
    version of what that file might contain is shown below:

    from launch import LaunchDescription
    from launch_ros.actions import Node

    def generate_launch_description():
        return LaunchDescription([
            Node(
                package='devin_robot_pkg',
                executable='power_management_node', # From power_management.py
                name='power_monitor'
            ),
            Node(
                package='devin_robot_pkg',
                executable='environment_mapping_node', # From environment_mapping.py
                name='mapper'
            ),
            Node(
                package='devin_robot_pkg',
                executable='remote_control_node', # From remote_control.py
                name='teleop_node'
            ),
            # ... and so on for all other ROS 2 nodes.
        ])
    """,
        formatter_class=argparse.RawTextHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('start', help="Start the main robot software stack.")
    subparsers.add_parser('stop', help="Stop the main robot software stack.")
    subparsers.add_parser('status', help="Check the status of the robot software stack.")
    subparsers.add_parser('restart', help="Restart the robot software stack.")
    subparsers.add_parser('reboot', help="Reboot the robot's computer (requires sudo).")
    subparsers.add_parser('teleop', help="Launch the interactive keyboard remote control.")
    
    args = parser.parse_args()
    
    manager = RobotManager()
    
    if args.command == 'start':
        manager.start()
    elif args.command == 'stop':
        manager.stop()
    elif args.command == 'status':
        manager.status()
    elif args.command == 'restart':
        manager.stop()
        time.sleep(1)
        manager.start()
    elif args.command == 'reboot':
        manager.reboot()
    elif args.command == 'teleop':
        manager.teleop()
