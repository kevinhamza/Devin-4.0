# # Devin/modules/robotics_control_module.py
# # Purpose: Handles real-time control of robot movement and tasks.
# #          Provides an interface for sending commands and receiving status.
# # Real-time control of robot movement and tasks 🤖⚙️

# import logging
# import uuid
# import time
# import random
# from datetime import datetime, timezone
# from enum import Enum, auto
# from abc import ABC, abstractmethod
# from typing import List, Dict, Any, Optional, Tuple, Union
# from dataclasses import dataclass, field

# # Configure basic logging
# logger = logging.getLogger("RoboticsControlModule")
# if not logger.handlers: # Prevent duplicate handlers
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class RobotCommandType(Enum):
#     """Defines types of commands that can be sent to a robot."""
#     CONNECT = auto()
#     DISCONNECT = auto()
#     MOVE_ABSOLUTE = auto()      # Move to specific coordinates (x, y, z)
#     MOVE_RELATIVE = auto()      # Move by delta (dx, dy, dz)
#     ROTATE_ABSOLUTE = auto()    # Rotate to specific orientation (roll, pitch, yaw)
#     ROTATE_RELATIVE = auto()    # Rotate by delta angles
#     SET_JOINT_ANGLES = auto()   # For articulated arms
#     CONTROL_END_EFFECTOR = auto() # e.g., gripper open/close, tool activation
#     SPEAK_TEXT = auto()
#     EXECUTE_PREDEFINED_TASK = auto() # Run a named task/program on the robot
#     GET_STATUS = auto()
#     EMERGENCY_STOP = auto()
#     RESET_ERRORS = auto()
#     HOME_ROBOT = auto()

# class RobotTaskStatus(Enum):
#     """Represents the status of the robot or a task it's performing."""
#     IDLE = auto()
#     CONNECTING = auto()
#     CONNECTED = auto()
#     DISCONNECTED = auto()
#     MOVING = auto()
#     EXECUTING_TASK = auto()
#     AWAITING_COMMAND = auto()
#     TASK_COMPLETED = auto()
#     TASK_FAILED = auto()
#     ERROR = auto()
#     SAFETY_STOP_ENGAGED = auto()
#     CALIBRATING = auto()

# @dataclass
# class RobotCommand:
#     """Represents a command sent to a robot."""
#     command_id: str = field(default_factory=lambda: f"rcmd_{uuid.uuid4().hex[:8]}")
#     command_type: RobotCommandType
#     parameters: Dict[str, Any] = field(default_factory=dict)
#     timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

# @dataclass
# class RobotFeedback:
#     """Represents feedback received from a robot."""
#     timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
#     robot_id: str
#     status: RobotTaskStatus
#     current_position: Optional[Tuple[float, float, float]] = None # (x, y, z)
#     current_orientation: Optional[Tuple[float, float, float]] = None # (roll, pitch, yaw)
#     joint_angles: Optional[List[float]] = None
#     end_effector_status: Optional[Dict[str, Any]] = None # e.g., {"gripper_open": True, "pressure": 0.5}
#     sensor_readings: Optional[Dict[str, Any]] = field(default_factory=dict) # e.g., {"lidar": [...], "camera_status": "OK"}
#     active_task_id: Optional[str] = None
#     battery_level_percent: Optional[float] = None
#     error_messages: List[str] = field(default_factory=list)
#     message: Optional[str] = None


# class RobotInterface(ABC):
#     """Abstract Base Class for a generic robot interface."""

#     @abstractmethod
#     def connect(self, connection_params: Optional[Dict[str, Any]] = None) -> bool:
#         """Establishes a connection to the robot."""
#         pass

#     @abstractmethod
#     def disconnect(self) -> bool:
#         """Disconnects from the robot."""
#         pass

#     @abstractmethod
#     def send_command(self, command: RobotCommand) -> Tuple[bool, Optional[str]]:
#         """Sends a command to the robot. Returns (success_status, message_or_error)."""
#         pass

#     @abstractmethod
#     def get_feedback(self) -> Optional[RobotFeedback]:
#         """Retrieves the latest status/feedback from the robot."""
#         pass

#     @abstractmethod
#     def emergency_stop(self) -> bool:
#         """Triggers an emergency stop on the robot."""
#         pass
    
#     @abstractmethod
#     def is_connected(self) -> bool:
#         """Checks if currently connected to the robot."""
#         pass


# class SimulatedRobot(RobotInterface):
#     """
#     A simulated robot implementation for testing and demonstration.
#     """
#     def __init__(self, robot_id: str = "SimBot_Devin_001", initial_battery: float = 100.0):
#         self.robot_id = robot_id
#         self._is_connected = False
#         self._current_pos = (0.0, 0.0, 0.0)
#         self._current_orientation = (0.0, 0.0, 0.0) # Roll, Pitch, Yaw
#         self._joint_angles_sim = [0.0] * 6 # Simulate a 6-DOF arm
#         self._gripper_open = True
#         self._gripper_pressure = 0.0
#         self._current_status = RobotTaskStatus.DISCONNECTED
#         self._active_task_id: Optional[str] = None
#         self._error_log: List[str] = []
#         self._safety_stop_active = False
#         self._battery = initial_battery # Percentage
#         self._last_command_time = datetime.now(timezone.utc)

#         logger.info(f"SimulatedRobot '{self.robot_id}' created. Status: {self._current_status.name}")

#     def is_connected(self) -> bool:
#         return self._is_connected

#     def connect(self, connection_params: Optional[Dict[str, Any]] = None) -> bool:
#         if self._is_connected:
#             logger.warning(f"SimulatedRobot '{self.robot_id}' is already connected.")
#             return True
#         logger.info(f"SimulatedRobot '{self.robot_id}' attempting to connect with params: {connection_params}...")
#         self._current_status = RobotTaskStatus.CONNECTING
#         time.sleep(0.1) # Simulate connection time
#         self._is_connected = True
#         self._current_status = RobotTaskStatus.CONNECTED
#         self._error_log.clear()
#         self._safety_stop_active = False
#         logger.info(f"SimulatedRobot '{self.robot_id}' connected successfully.")
#         return True

#     def disconnect(self) -> bool:
#         if not self._is_connected:
#             logger.warning(f"SimulatedRobot '{self.robot_id}' is already disconnected.")
#             return True
#         logger.info(f"SimulatedRobot '{self.robot_id}' disconnecting...")
#         time.sleep(0.05)
#         self._is_connected = False
#         self._current_status = RobotTaskStatus.DISCONNECTED
#         logger.info(f"SimulatedRobot '{self.robot_id}' disconnected.")
#         return True

#     def _simulate_action(self, duration_seconds: float, new_status_during_action: RobotTaskStatus):
#         """Helper to simulate time passing for an action."""
#         if self._safety_stop_active:
#             self._error_log.append("Action cannot be performed: Safety stop is active.")
#             self._current_status = RobotTaskStatus.SAFETY_STOP_ENGAGED
#             return False
            
#         self._current_status = new_status_during_action
#         time.sleep(duration_seconds * 0.1) # Faster simulation
#         self._battery -= duration_seconds * 0.5 # Simulate battery drain
#         if self._battery < 0: self._battery = 0
#         self._last_command_time = datetime.now(timezone.utc)
#         return True

#     def send_command(self, command: RobotCommand) -> Tuple[bool, Optional[str]]:
#         if not self._is_connected:
#             msg = "Cannot send command: SimulatedRobot is not connected."
#             logger.error(msg)
#             return False, msg
#         if self._safety_stop_active and command.command_type not in [RobotCommandType.EMERGENCY_STOP, RobotCommandType.RESET_ERRORS]:
#             msg = "Cannot send command: Safety stop is active. Only RESET or another E-STOP allowed."
#             self._error_log.append(msg)
#             self._current_status = RobotTaskStatus.SAFETY_STOP_ENGAGED
#             logger.error(msg)
#             return False, msg

#         logger.info(f"SimulatedRobot '{self.robot_id}' received command: {command.command_type.name} with params {command.parameters}")
        
#         success = True
#         message = f"Command {command.command_type.name} executed successfully (simulated)."
        
#         if command.command_type == RobotCommandType.MOVE_ABSOLUTE:
#             if not self._simulate_action(0.2, RobotTaskStatus.MOVING): return False, self._error_log[-1]
#             self._current_pos = command.parameters.get("position", self._current_pos)
#         elif command.command_type == RobotCommandType.MOVE_RELATIVE:
#             if not self._simulate_action(0.2, RobotTaskStatus.MOVING): return False, self._error_log[-1]
#             dx, dy, dz = command.parameters.get("delta", (0,0,0))
#             self._current_pos = (self._current_pos[0] + dx, self._current_pos[1] + dy, self._current_pos[2] + dz)
#         elif command.command_type == RobotCommandType.ROTATE_ABSOLUTE:
#             if not self._simulate_action(0.1, RobotTaskStatus.MOVING): return False, self._error_log[-1]
#             self._current_orientation = command.parameters.get("orientation", self._current_orientation)
#         elif command.command_type == RobotCommandType.SET_JOINT_ANGLES:
#             if not self._simulate_action(0.15, RobotTaskStatus.MOVING): return False, self._error_log[-1]
#             self._joint_angles_sim = command.parameters.get("angles", self._joint_angles_sim)
#         elif command.command_type == RobotCommandType.CONTROL_END_EFFECTOR:
#             if not self._simulate_action(0.05, RobotTaskStatus.EXECUTING_TASK): return False, self._error_log[-1]
#             self._gripper_open = command.parameters.get("open", self._gripper_open)
#             self._gripper_pressure = command.parameters.get("pressure", self._gripper_pressure)
#         elif command.command_type == RobotCommandType.SPEAK_TEXT:
#             if not self._simulate_action(0.1, RobotTaskStatus.EXECUTING_TASK): return False, self._error_log[-1]
#             logger.info(f"SimBot SPEAKS: '{command.parameters.get('text', '...')}'")
#             message = f"Spoke: '{command.parameters.get('text', '...')}'"
#         elif command.command_type == RobotCommandType.EXECUTE_PREDEFINED_TASK:
#             task_name = command.parameters.get("task_name", "unknown_task")
#             self._active_task_id = command.command_id
#             if not self._simulate_action(0.5, RobotTaskStatus.EXECUTING_TASK): return False, self._error_log[-1]
#             # Simulate task outcome
#             if random.random() < 0.1: # 10% chance of task failure
#                 self._current_status = RobotTaskStatus.TASK_FAILED
#                 self._error_log.append(f"Simulated failure for task: {task_name}")
#                 success = False
#                 message = f"Task '{task_name}' failed (simulated)."
#             else:
#                 self._current_status = RobotTaskStatus.TASK_COMPLETED
#                 message = f"Task '{task_name}' completed (simulated)."
#             self._active_task_id = None
#         elif command.command_type == RobotCommandType.EMERGENCY_STOP:
#             self._safety_stop_active = True
#             self._current_status = RobotTaskStatus.SAFETY_STOP_ENGAGED
#             message = "EMERGENCY STOP ENGAGED."
#             logger.critical(message)
#         elif command.command_type == RobotCommandType.RESET_ERRORS:
#             self._error_log.clear()
#             self._safety_stop_active = False # Assuming reset also clears safety stop
#             self._current_status = RobotTaskStatus.IDLE
#             message = "Errors reset, safety stop disengaged."
#             logger.info(message)
#         elif command.command_type == RobotCommandType.HOME_ROBOT:
#             if not self._simulate_action(0.3, RobotTaskStatus.CALIBRATING): return False, self._error_log[-1]
#             self._current_pos = (0.0,0.0,0.0)
#             self._current_orientation = (0.0,0.0,0.0)
#             self._joint_angles_sim = [0.0] * len(self._joint_angles_sim)
#             self._current_status = RobotTaskStatus.IDLE
#             message = "Robot homed successfully (simulated)."
#         elif command.command_type == RobotCommandType.GET_STATUS:
#             # This command type is typically handled by get_feedback, but can acknowledge
#             pass 
#         else:
#             success = False
#             message = f"Command type {command.command_type.name} not fully implemented in simulation."
#             self._error_log.append(message)
#             self._current_status = RobotTaskStatus.ERROR
#             logger.warning(message)

#         if self._current_status not in [RobotTaskStatus.EXECUTING_TASK, RobotTaskStatus.MOVING, RobotTaskStatus.CONNECTING, RobotTaskStatus.SAFETY_STOP_ENGAGED, RobotTaskStatus.ERROR, RobotTaskStatus.TASK_FAILED]:
#             if not self._safety_stop_active: # Don't override safety stop status unless resetting
#                 self._current_status = RobotTaskStatus.IDLE 
        
#         return success, message

#     def get_feedback(self) -> Optional[RobotFeedback]:
#         if not self._is_connected:
#             # Optionally return a disconnected status feedback
#             # return RobotFeedback(robot_id=self.robot_id, status=RobotTaskStatus.DISCONNECTED, message="Not connected.")
#             return None

#         # Simulate sensor data
#         sim_sensor_data = {
#             "proximity_front_m": round(random.uniform(0.1, 5.0), 2),
#             "imu_orientation_deg": [round(o + random.uniform(-0.5, 0.5),1) for o in self._current_orientation], # slight noise
#             "camera_feed_status": "OPERATIONAL" if random.random() > 0.05 else "DEGRADED"
#         }
        
#         feedback = RobotFeedback(
#             robot_id=self.robot_id,
#             status=self._current_status,
#             current_position=self._current_pos,
#             current_orientation=self._current_orientation,
#             joint_angles=self._joint_angles_sim,
#             end_effector_status={"gripper_open": self._gripper_open, "pressure_reading": self._gripper_pressure * random.uniform(0.9, 1.1)},
#             sensor_readings=sim_sensor_data,
#             active_task_id=self._active_task_id,
#             battery_level_percent=round(self._battery,1),
#             error_messages=list(self._error_log), # Return a copy
#             message=f"SimBot status at {datetime.now(timezone.utc).isoformat()}"
#         )
#         return feedback

#     def emergency_stop(self) -> bool:
#         logger.critical(f"SimulatedRobot '{self.robot_id}' EMERGENCY STOP initiated by direct call.")
#         self._safety_stop_active = True
#         self._current_status = RobotTaskStatus.SAFETY_STOP_ENGAGED
#         self._active_task_id = None # Stop any active task
#         self._error_log.append("EMERGENCY STOP ACTIVATED.")
#         return True

# class RoboticsControlModule:
#     """
#     Module for controlling a robot via a RobotInterface.
#     """
#     def __init__(self, robot_interface: RobotInterface):
#         self.robot = robot_interface
#         logger.info(f"RoboticsControlModule initialized with interface: {type(robot_interface).__name__}")

#     def startup_robot_system(self, connection_params: Optional[Dict[str, Any]] = None) -> bool:
#         logger.info("Attempting to connect to robot...")
#         if self.robot.connect(connection_params):
#             logger.info("Robot connected successfully.")
#             # Optionally send a HOME command or RESET_ERRORS after connection
#             self.robot.send_command(RobotCommand(command_type=RobotCommandType.RESET_ERRORS))
#             # self.robot.send_command(RobotCommand(command_type=RobotCommandType.HOME_ROBOT))
#             return True
#         logger.error("Failed to connect to robot.")
#         return False

#     def shutdown_robot_system(self) -> bool:
#         logger.info("Attempting to disconnect from robot...")
#         if self.robot.disconnect():
#             logger.info("Robot disconnected successfully.")
#             return True
#         logger.error("Failed to disconnect from robot (or was already disconnected).")
#         return False

#     def _send_and_log_command(self, command_type: RobotCommandType, params: Dict = None) -> Tuple[bool, Optional[str]]:
#         if not self.robot.is_connected():
#             msg = "Robot not connected. Cannot send command."
#             logger.error(msg)
#             return False, msg
        
#         # Conceptual Safety Check (very basic)
#         if not self._is_command_safe_conceptual(command_type, params):
#             msg = f"Conceptual safety check failed for command {command_type.name}. Command not sent."
#             logger.error(msg)
#             return False, msg

#         cmd = RobotCommand(command_type=command_type, parameters=params or {})
#         logger.debug(f"Sending command: {cmd.command_type.name} with params {cmd.parameters}")
#         success, message = self.robot.send_command(cmd)
#         if success:
#             logger.info(f"Command {cmd.command_type.name} sent. Robot response: {message}")
#         else:
#             logger.error(f"Command {cmd.command_type.name} failed. Robot response: {message}")
#         return success, message

#     def _is_command_safe_conceptual(self, command_type: RobotCommandType, params: Optional[Dict]) -> bool:
#         """Extremely basic conceptual safety check. Real systems need robust safety logic."""
#         if command_type in [RobotCommandType.MOVE_ABSOLUTE, RobotCommandType.MOVE_RELATIVE]:
#             # Example: Check if target coordinates are within a known safe zone
#             # For now, always return True in simulation unless it's an E-STOP
#             pass
#         if command_type == RobotCommandType.EMERGENCY_STOP:
#             return True # E-stop is always "safe" to send
#         # Add more conceptual checks if desired
#         return True


#     def move_to_position(self, x: float, y: float, z: float) -> Tuple[bool, Optional[str]]:
#         return self._send_and_log_command(RobotCommandType.MOVE_ABSOLUTE, {"position": (x, y, z)})

#     def move_relative(self, dx: float, dy: float, dz: float) -> Tuple[bool, Optional[str]]:
#         return self._send_and_log_command(RobotCommandType.MOVE_RELATIVE, {"delta": (dx, dy, dz)})

#     def set_gripper(self, is_open: bool, pressure_percentage: Optional[float] = None) -> Tuple[bool, Optional[str]]:
#         params = {"open": is_open}
#         if pressure_percentage is not None:
#             params["pressure"] = max(0.0, min(1.0, pressure_percentage / 100.0)) # Normalize to 0-1
#         return self._send_and_log_command(RobotCommandType.CONTROL_END_EFFECTOR, params)

#     def robot_speak(self, text: str) -> Tuple[bool, Optional[str]]:
#         return self._send_and_log_command(RobotCommandType.SPEAK_TEXT, {"text": text})

#     def execute_robot_task(self, task_name: str, task_parameters: Optional[Dict] = None) -> Tuple[bool, Optional[str]]:
#         params = {"task_name": task_name}
#         if task_parameters:
#             params.update(task_parameters)
#         return self._send_and_log_command(RobotCommandType.EXECUTE_PREDEFINED_TASK, params)

#     def get_current_status(self) -> Optional[RobotFeedback]:
#         if not self.robot.is_connected():
#             logger.warning("Cannot get status: Robot not connected.")
#             return None
#         return self.robot.get_feedback()

#     def trigger_emergency_stop(self) -> bool:
#         logger.critical("EMERGENCY STOP triggered via RoboticsControlModule!")
#         return self.robot.emergency_stop()

#     def reset_robot_errors(self) -> Tuple[bool, Optional[str]]:
#         return self._send_and_log_command(RobotCommandType.RESET_ERRORS)

# # Example Usage
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Robotics Control Module Prototype 🤖⚙️ ===")
#     print("=========================================================")

#     # 1. Initialize Simulated Robot and Control Module
#     sim_robot = SimulatedRobot(robot_id="DevinBot_AlphaSim")
#     robot_controller = RoboticsControlModule(robot_interface=sim_robot)

#     # 2. Connect to the robot
#     if not robot_controller.startup_robot_system({"port": "/dev/ttySim0", "baudrate": 115200}):
#         print("Exiting due to connection failure.")
#         exit()
    
#     # 3. Get initial status
#     initial_status = robot_controller.get_current_status()
#     if initial_status:
#         print(f"\nInitial Robot Status ({initial_status.robot_id}): {initial_status.status.name}, Batt: {initial_status.battery_level_percent}%")
#         print(f"  Position: {initial_status.current_position}, Orientation: {initial_status.current_orientation}")

#     # 4. Perform a sequence of actions
#     print("\n--- Performing Robot Actions ---")
#     robot_controller.robot_speak("Hello Devin! I am ready for commands.")
#     time.sleep(0.2)
#     robot_controller.move_to_position(x=1.0, y=0.5, z=0.2)
#     time.sleep(0.3)
    
#     status_after_move = robot_controller.get_current_status()
#     if status_after_move:
#         print(f"Status after move: Pos: {status_after_move.current_position}, Batt: {status_after_move.battery_level_percent}%")

#     robot_controller.set_gripper(is_open=False, pressure_percentage=75.0) # Close gripper
#     time.sleep(0.2)
#     status_after_grip = robot_controller.get_current_status()
#     if status_after_grip:
#          print(f"Gripper status: {status_after_grip.end_effector_status}")
    
#     robot_controller.set_gripper(is_open=True) # Open gripper
#     time.sleep(0.2)

#     robot_controller.execute_robot_task(task_name="ScanEnvironment", task_parameters={"scan_area_sqm": 10})
#     time.sleep(0.6) # Wait for task to "complete"
    
#     status_after_task = robot_controller.get_current_status()
#     if status_after_task:
#         print(f"Status after task 'ScanEnvironment': {status_after_task.status.name}, Errors: {status_after_task.error_messages}")

#     # 5. Simulate an emergency stop
#     # print("\n--- Simulating Emergency Stop ---")
#     # robot_controller.trigger_emergency_stop()
#     # estop_status = robot_controller.get_current_status()
#     # if estop_status:
#     #     print(f"Status after E-STOP: {estop_status.status.name}, Errors: {estop_status.error_messages}")
    
#     # # Attempt a command while E-stopped
#     # robot_controller.robot_speak("Can I move now?") 
#     # time.sleep(0.1)

#     # # Reset errors
#     # print("\n--- Resetting Errors ---")
#     # robot_controller.reset_robot_errors()
#     # reset_status = robot_controller.get_current_status()
#     # if reset_status:
#     #      print(f"Status after Reset: {reset_status.status.name}, Errors: {reset_status.error_messages}")


#     # 6. Disconnect
#     print("\n--- Shutting Down ---")
#     robot_controller.shutdown_robot_system()
    
#     final_sim_status = sim_robot.get_feedback() # Direct check on sim
#     if final_sim_status:
#          print(f"Final simulated robot status (direct check): {final_sim_status.status.name if final_sim_status else 'N/A'}")
#     else: # if disconnect makes get_feedback return None
#          print(f"Final simulated robot status (direct check): {'DISCONNECTED' if not sim_robot.is_connected() else 'UNKNOWN'}")


#     print("\n=========================================================")
#     print("=== Robotics Control Module Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/robotics_control_module.py
# Purpose: An integrated module for controlling a robot by sending commands
#          to the ROS 2 robotics_control_server.

import logging
import uuid
import time
import yaml
import subprocess
import shutil
from datetime import datetime, timezone
from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

# ... (All enums and dataclasses like RobotCommandType, RobotCommand, etc. remain unchanged from the previous version)
class RobotCommandType(Enum):
    MOVE_RELATIVE = auto()
    ROTATE_RELATIVE = auto()
    SPEAK_TEXT = auto()
    EMERGENCY_STOP = auto()
# ... add other command types as needed

@dataclass
class RobotCommand:
    command_type: RobotCommandType
    command_id: str = field(default_factory=lambda: f"rcmd_{uuid.uuid4().hex[:8]}")
    parameters: Dict[str, Any] = field(default_factory=dict)
# ... other data classes are the same

class RobotInterface(ABC):
    @abstractmethod
    def connect(self) -> bool: pass
    @abstractmethod
    def disconnect(self) -> bool: pass
    @abstractmethod
    def send_command(self, command: RobotCommand) -> Tuple[bool, Optional[str]]: pass
    @abstractmethod
    def is_connected(self) -> bool: pass


class ROS2_RobotInterface(RobotInterface):
    """
    An implementation of the RobotInterface that communicates with the
    `robotics_control_server` via the ROS 2 command-line tools.
    """
    def __init__(self, service_name: str = "/devin/control_robot", service_type: str = "devin_robotics/srv/ControlRobot"):
        self.service_name = service_name
        self.service_type = service_type
        if not shutil.which("ros2"):
            raise FileNotFoundError("`ros2` command not found. Is ROS 2 installed and sourced in your environment?")
        self._is_connected = False

    def is_connected(self) -> bool:
        return self._is_connected

    def connect(self) -> bool:
        logger.info("Checking for ROS 2 robotics control service...")
        success, stdout, _ = self._run_ros_command(["service", "list"])
        if success and self.service_name in stdout:
            logger.info("ROS 2 service found. Connection successful.")
            self._is_connected = True
            return True
        logger.error(f"ROS 2 service '{self.service_name}' not found. Is the robotics_control_server running?")
        self._is_connected = False
        return False

    def disconnect(self) -> bool:
        logger.info("Disconnecting from ROS 2 interface (conceptual).")
        self._is_connected = False
        return True

    def send_command(self, command: RobotCommand) -> Tuple[bool, Optional[str]]:
        if not self.is_connected():
            return False, "Not connected to ROS 2 service."

        # Translate our generic command into the specific format for the ROS service
        ros_command = ""
        ros_value = 0.0
        
        if command.command_type == RobotCommandType.MOVE_RELATIVE:
            delta = command.parameters.get("delta", (0,0,0))
            if delta[0] > 0:
                ros_command = "forward"
                ros_value = delta[0]
            else:
                ros_command = "backward"
                ros_value = abs(delta[0])
        elif command.command_type == RobotCommandType.ROTATE_RELATIVE:
            # Assuming rotation is around Z axis (yaw)
            delta_yaw = command.parameters.get("delta_yaw", 0.0)
            if delta_yaw > 0:
                ros_command = "rotate_left"
                ros_value = delta_yaw
            else:
                ros_command = "rotate_right"
                ros_value = abs(delta_yaw)
        elif command.command_type == RobotCommandType.EMERGENCY_STOP:
            ros_command = "stop"
            ros_value = 0.0
        else:
            return False, f"Command type '{command.command_type.name}' not supported by ROS2 interface."

        # Construct the ros2 service call command
        request_str = f"{{command: '{ros_command}', value: {ros_value}}}"
        cli_command = ["ros2", "service", "call", self.service_name, self.service_type, request_str]
        
        logger.info(f"Executing ROS 2 command: {' '.join(cli_command)}")
        success, stdout, stderr = self._run_ros_command(cli_command)

        if not success:
            return False, f"ROS 2 command failed: {stderr}"
        
        # Parse the YAML response from the service call
        try:
            response_data = yaml.safe_load(stdout.split('---')[1]) # Response is after the '---'
            if response_data['response']['success']:
                return True, response_data['response']['message']
            else:
                return False, response_data['response']['message']
        except Exception as e:
            return False, f"Failed to parse ROS 2 service response: {e}"

    def _run_ros_command(self, args: List[str]) -> Tuple[bool, str, str]:
        """A wrapper for running ros2 commands."""
        try:
            result = subprocess.run(["ros2"] + args, capture_output=True, text=True, timeout=15, check=True)
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
        except Exception as e:
            return False, "", str(e)


class RoboticsControlModule:
    """High-level module for controlling a robot via a RobotInterface."""
    def __init__(self, robot_interface: RobotInterface):
        self.robot = robot_interface
        logger.info(f"RoboticsControlModule initialized with interface: {type(robot_interface).__name__}")
    
    def startup_robot_system(self) -> bool:
        return self.robot.connect()

    def shutdown_robot_system(self) -> bool:
        return self.robot.disconnect()
        
    def move_relative(self, dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> Tuple[bool, Optional[str]]:
        cmd = RobotCommand(command_type=RobotCommandType.MOVE_RELATIVE, parameters={"delta": (dx, dy, dz)})
        return self.robot.send_command(cmd)

    def rotate_relative(self, delta_yaw: float) -> Tuple[bool, Optional[str]]:
        cmd = RobotCommand(command_type=RobotCommandType.ROTATE_RELATIVE, parameters={"delta_yaw": delta_yaw})
        return self.robot.send_command(cmd)

    def trigger_emergency_stop(self) -> Tuple[bool, Optional[str]]:
        cmd = RobotCommand(command_type=RobotCommandType.EMERGENCY_STOP)
        return self.robot.send_command(cmd)

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Robotics Control Module Prototype 🤖🔗 ===")
    print("=========================================================")
    print("!!! PREREQUISITE: The `robotics_control_server` ROS 2 node must be built and running in a separate terminal. !!!")
    
    # 1. Initialize the live ROS 2 interface
    try:
        ros_interface = ROS2_RobotInterface()
        robot_controller = RoboticsControlModule(robot_interface=ros_interface)
        
        # 2. Connect to the robot service
        if robot_controller.startup_robot_system():
            print("\n--- Performing Robot Actions via ROS 2 Service ---")
            
            # 3. Send a sequence of commands
            print("\nAction: Moving forward 0.2 meters...")
            success, msg = robot_controller.move_relative(dx=0.2)
            print(f"  Response: {msg}")
            
            time.sleep(2)
            
            print("\nAction: Rotating left 45 degrees...")
            success, msg = robot_controller.rotate_relative(delta_yaw=45.0)
            print(f"  Response: {msg}")

            time.sleep(2)

            print("\nAction: Triggering STOP...")
            success, msg = robot_controller.trigger_emergency_stop()
            print(f"  Response: {msg}")

            robot_controller.shutdown_robot_system()
        else:
            print("\n[FAILURE] Could not connect to the ROS 2 robotics server.")
            print("Please ensure you have sourced your ROS 2 workspace and run:")
            print("`ros2 run devin_robotics robotics_server` in another terminal.")

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

    print("\n=========================================================")
    print("=== Robotics Control Module Prototype Complete ===")
    print("=========================================================")
