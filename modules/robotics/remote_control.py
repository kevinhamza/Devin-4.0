# # Devin/modules/robotics/remote_control.py
# # Purpose: Provides a real-time, non-blocking remote control system for a robot's
# #          base movement using the keyboard of the host computer.

# import logging
# import threading
# import time
# from typing import Optional, Any, Dict

# # --- Dependency Installation Notes ---
# # This module requires the 'pynput' library for cross-platform keyboard monitoring.
# # pip install pynput
# try:
#     from pynput import keyboard
#     PYNPUT_AVAILABLE = True
# except ImportError:
#     PYNPUT_AVAILABLE = False
#     keyboard = None

# # --- Conceptual Placeholder for the Motor Controller ---
# # In a real system, you would import the actual MotorController class
# # from .motor_control import MotorController
# class MotorController:
#     """A conceptual placeholder for the actual MotorController."""
#     def set_base_velocity(self, linear_vel: float, angular_vel: float):
#         # This is where the command to the robot's hardware would go.
#         # We simulate it by logging the intended action.
#         logger.debug(f"[MotorController] Setting base velocity: linear={linear_vel:.2f} m/s, angular={angular_vel:.2f} rad/s")
#     def stop_base(self):
#         logger.info("[MotorController] STOPPING ALL MOVEMENT.")
#         self.set_base_velocity(0.0, 0.0)
# # --- End of Conceptual Placeholder ---


# # Configure basic logging
# logger = logging.getLogger("RemoteControl")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)


# class RemoteControl:
#     """
#     Manages a real-time, keyboard-based remote control session for a robot.
#     """
#     def __init__(self, motor_controller: MotorController, move_speed: float = 0.5, turn_speed: float = 1.0):
#         """
#         Initializes the RemoteControl system.

#         Args:
#             motor_controller (MotorController): An instance of the low-level motor controller.
#             move_speed (float): The default linear speed in meters/second.
#             turn_speed (float): The default angular speed in radians/second.
#         """
#         if not PYNPUT_AVAILABLE:
#             raise ImportError("The 'pynput' library is required for remote control. Please run 'pip install pynput'.")

#         self.motors = motor_controller
#         self.move_speed = move_speed
#         self.turn_speed = turn_speed

#         self.linear_velocity = 0.0
#         self.angular_velocity = 0.0
#         self.keys_pressed = set()

#         self._control_thread: Optional[threading.Thread] = None
#         self._listener_thread: Optional[keyboard.Listener] = None
#         self._stop_event = threading.Event()
#         self._lock = threading.Lock()

#         logger.info("RemoteControl initialized.")

#     def _update_velocity(self):
#         """Calculates desired velocity based on the set of currently pressed keys."""
#         with self._lock:
#             # Reset velocities
#             self.linear_velocity = 0.0
#             self.angular_velocity = 0.0

#             # Set linear velocity based on W/S keys
#             if 'w' in self.keys_pressed:
#                 self.linear_velocity = self.move_speed
#             elif 's' in self.keys_pressed:
#                 self.linear_velocity = -self.move_speed

#             # Set angular velocity based on A/D keys
#             if 'a' in self.keys_pressed:
#                 self.angular_velocity = self.turn_speed
#             elif 'd' in self.keys_pressed:
#                 self.angular_velocity = -self.turn_speed

#     def _on_press(self, key):
#         """Callback function for pynput key press events."""
#         try:
#             # Get the character of the key
#             key_char = key.char.lower()
#             if key_char in ['w', 'a', 's', 'd']:
#                 with self._lock:
#                     self.keys_pressed.add(key_char)
#                 self._update_velocity()
#         except AttributeError:
#             # This handles special keys like Key.shift, Key.esc
#             if key == keyboard.Key.esc:
#                 logger.info("Escape key pressed. Shutting down remote control.")
#                 self.stop_control()
#             # You can add more special key handling here if needed

#     def _on_release(self, key):
#         """Callback function for pynput key release events."""
#         try:
#             key_char = key.char.lower()
#             if key_char in self.keys_pressed:
#                 with self._lock:
#                     self.keys_pressed.discard(key_char)
#                 self._update_velocity()
#         except AttributeError:
#             pass # Ignore special key releases for this simple control scheme

#     def _control_loop(self):
#         """
#         The background thread that continuously sends velocity commands to the motors.
#         """
#         logger.info("Control loop thread started.")
#         while not self._stop_event.is_set():
#             with self._lock:
#                 linear = self.linear_velocity
#                 angular = self.angular_velocity

#             # Only send a command if there is movement, to avoid flooding the bus
#             if linear != 0.0 or angular != 0.0:
#                 self.motors.set_base_velocity(linear, angular)
#             else:
#                 # When no movement keys are pressed, ensure the robot stops.
#                 # This check prevents a stop command from being sent on every single loop tick.
#                 # We could add a simple state check to only send it once.
#                 self.motors.stop_base()

#             time.sleep(0.1) # Send commands at 10Hz

#         # Final command to ensure the robot is stopped upon exit
#         self.motors.stop_base()
#         logger.info("Control loop thread stopped.")

#     def start_control(self):
#         """Starts the remote control session (keyboard listener and control loop)."""
#         if self._listener_thread and self._listener_thread.is_alive():
#             logger.warning("Remote control is already active.")
#             return

#         logger.info("Starting remote control session.")
#         self._stop_event.clear()

#         # Start the control loop that sends commands to the robot
#         self._control_thread = threading.Thread(target=self._control_loop, daemon=True)
#         self._control_thread.start()

#         # Start the non-blocking keyboard listener
#         self._listener_thread = keyboard.Listener(
#             on_press=self._on_press,
#             on_release=self._on_release
#         )
#         self._listener_thread.start()
        
#         print("\n--- Remote Control Active ---")
#         print("Use WASD keys to move the robot.")
#         print("  W: Forward")
#         print("  S: Backward")
#         print("  A: Turn Left")
#         print("  D: Turn Right")
#         print("Press 'ESC' to stop remote control.")
#         print("-----------------------------")


#     def stop_control(self):
#         """Stops the remote control session."""
#         if not self._listener_thread:
#             logger.info("Remote control is not running.")
#             return

#         logger.info("Stopping remote control session...")
#         self._stop_event.set()

#         if self._listener_thread:
#             self._listener_thread.stop()
#             self._listener_thread.join()
#             self._listener_thread = None
        
#         if self._control_thread:
#             self._control_thread.join(timeout=1.0)
#             self._control_thread = None
            
#         logger.info("Remote control session stopped.")

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Remote Control Module Prototype ⌨️🕹️ ===")
#     print("=========================================================")
    
#     if not PYNPUT_AVAILABLE:
#         print("\n'pynput' library not found. Please run 'pip install pynput' to run this interactive demo.")
#     else:
#         # 1. Initialize the motor controller (conceptual) and the remote controller
#         motors = MotorController()
#         remote_controller = RemoteControl(motor_controller=motors)

#         # 2. Start the remote control session
#         remote_controller.start_control()

#         # 3. The main program can now do other things while the remote control
#         #    runs in the background. We'll just wait here until ESC is pressed.
#         # The listener thread will call `stop_control` when ESC is pressed.
#         if remote_controller._listener_thread:
#             remote_controller._listener_thread.join()
        
#         print("\n--- Main Program ---")
#         print("Remote control has been stopped.")
#         print("The main program can now continue or exit.")

#     print("\n=========================================================")
#     print("=== Remote Control Prototype Complete ===")
#     print("=========================================================")





# Devin/modules/robotics/remote_control.py
# Purpose: A professional-grade, ROS 2-based teleoperation node that provides
#          real-time robot control via the keyboard with a Curses TUI.

import logging
import threading
import time
import platform

# Curses is standard on Linux/macOS, but needs a special install on Windows
if platform.system() != "Windows":
    import curses

try:
    from pynput import keyboard
    # --- ROS 2 Integration ---
    from modules.robotics.network_interface import ROS2Interface
    from geometry_msgs.msg import Twist
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("RemoteControl")
# (Logger setup omitted for brevity, assumed to be configured)

class RemoteControl:
    """
    Manages a real-time, keyboard-based remote control session by publishing
    ROS 2 Twist messages to the /cmd_vel topic.
    """
    def __init__(self, ros_interface: ROS2Interface, move_speed: float = 0.5, turn_speed: float = 1.0):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core module is missing. Error: {_import_error}")
        
        self.ros_interface = ros_interface
        self.move_speed = move_speed
        self.turn_speed = turn_speed

        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        self.keys_pressed = set()

        self._control_thread: Optional[threading.Thread] = None
        self._listener_thread: Optional[keyboard.Listener] = None
        self._ui_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def _update_velocity(self):
        """Calculates desired velocity based on currently pressed keys."""
        with self._lock:
            self.linear_velocity = 0.0
            self.angular_velocity = 0.0
            if 'w' in self.keys_pressed: self.linear_velocity = self.move_speed
            elif 's' in self.keys_pressed: self.linear_velocity = -self.move_speed
            if 'a' in self.keys_pressed: self.angular_velocity = self.turn_speed
            elif 'd' in self.keys_pressed: self.angular_velocity = -self.turn_speed

    def _on_press(self, key):
        try:
            key_char = key.char.lower()
            if key_char in ['w', 'a', 's', 'd']:
                with self._lock:
                    self.keys_pressed.add(key_char)
                self._update_velocity()
        except AttributeError:
            if key == keyboard.Key.esc:
                self.stop_control()

    def _on_release(self, key):
        try:
            key_char = key.char.lower()
            if key_char in self.keys_pressed:
                with self._lock:
                    self.keys_pressed.discard(key_char)
                self._update_velocity()
        except AttributeError: pass

    def _control_loop(self):
        """Background thread that continuously publishes velocity commands."""
        while not self._stop_event.is_set():
            twist_msg = Twist()
            with self._lock:
                twist_msg.linear.x = float(self.linear_velocity)
                twist_msg.angular.z = float(self.angular_velocity)
            
            self.ros_interface.publish("/cmd_vel", Twist, twist_msg)
            time.sleep(0.1) # Publish at 10Hz

    def _ui_loop(self, stdscr):
        """Background thread for the Curses TUI."""
        curses.curs_set(0) # Hide the cursor
        stdscr.nodelay(True) # Make getch non-blocking
        
        while not self._stop_event.is_set():
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            
            title = "--- Devin Robotics: Remote Control (Teleop) ---"
            stdscr.addstr(1, w//2 - len(title)//2, title)
            
            instructions = [
                "[ W ] - Forward", "[ A ] - Turn Left",
                "[ S ] - Backward", "[ D ] - Turn Right",
                "[ESC] - Quit"
            ]
            for i, txt in enumerate(instructions):
                stdscr.addstr(3 + i, 2, txt)

            with self._lock:
                lin_vel, ang_vel = self.linear_velocity, self.angular_velocity
            
            status_title = "--- Live Status ---"
            stdscr.addstr(3, w - 30, status_title)
            stdscr.addstr(4, w - 30, f"Linear Velocity : {lin_vel:+.2f} m/s")
            stdscr.addstr(5, w - 30, f"Angular Velocity: {ang_vel:+.2f} rad/s")
            
            stdscr.refresh()
            time.sleep(0.1)

    def start_control(self):
        """Starts the remote control session (listener, control loop, and UI)."""
        self._stop_event.clear()

        # Start the control loop (ROS publisher)
        self._control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self._control_thread.start()

        # Start the keyboard listener
        self._listener_thread = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener_thread.start()

        # Start the UI
        if platform.system() != "Windows":
            self._ui_thread = threading.Thread(target=lambda: curses.wrapper(self._ui_loop), daemon=True)
            self._ui_thread.start()
        else:
            logger.warning("Curses TUI is not supported on Windows. Only console logs will be shown.")

    def stop_control(self):
        """Stops the remote control session."""
        self._stop_event.set()
        if self._listener_thread: self._listener_thread.stop()

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Remote Control (Live ROS 2 Demo) ⌨️🕹️ ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core module is missing: {_import_error}")
    elif not hasattr(globals(), 'curses') and platform.system() != "Windows":
        print("\nERROR: Curses library not available.")
    else:
        print("\n--- Prerequisites ---")
        print("1. A sourced ROS 2 environment (e.g., Humble) is required.")
        print("2. For a visual demo, run a simulator like Gazebo with a robot that subscribes to /cmd_vel.")
        print("   e.g., `ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py`")
        print("3. In another terminal, you can monitor the messages with `ros2 topic echo /cmd_vel`")
        input("\nPress Enter to start the remote control node...")

        ros_interface = None
        try:
            ros_interface = ROS2Interface("devin_teleop_node")
            ros_interface.start()
            
            remote_controller = RemoteControl(ros_interface=ros_interface)
            remote_controller.start_control()
            
            # Keep the main thread alive until the ESC key stops the listener
            if remote_controller._listener_thread:
                remote_controller._listener_thread.join()

        except Exception as e:
            logger.error(f"Demo failed to run: {e}", exc_info=True)
        finally:
            if ros_interface:
                ros_interface.stop()

    print("\n=========================================================")
    print("=== Remote Control Demo Complete ===")
    print("=========================================================")
