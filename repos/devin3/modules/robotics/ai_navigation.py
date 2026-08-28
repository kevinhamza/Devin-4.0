# # Devin/modules/robotics/ai_navigation.py
# # Purpose: Provides a high-level AI navigation system that orchestrates path
# #          planning, obstacle avoidance, and motion control for autonomous movement.

# import logging
# import threading
# import time
# from enum import Enum, auto
# from typing import Optional, Any, Tuple

# # This module would import the other robotics modules we've created.
# # from .path_planning import PathPlanner, GridLocation
# # from .motor_control import MotorController
# # from .sensor_integration import SensorSuite, Lidar

# # --- Conceptual Placeholders for Imported Modules & Data ---
# class PathPlanner:
#     def find_path(self, start, goal, smooth=True):
#         logger.info(f"[Planner] Finding path from {start} to {goal}...")
#         if goal == (10, 10): # Simulate a successful plan
#             return [(i, i) for i in range(11)]
#         return None # Simulate failure

# class MotorController:
#     def set_base_velocity(self, linear_vel: float, angular_vel: float):
#         logger.info(f"[MotorCtrl] Setting base velocity: linear={linear_vel:.2f} m/s, angular={angular_vel:.2f} rad/s")
#     def stop_base(self):
#         logger.info("[MotorCtrl] Stopping base.")

# class SensorSuite:
#     def get_lidar_scan(self):
#         # Simulate a clear path with one unexpected obstacle
#         return {"obstacle_directly_ahead": time.time() % 20 > 15} # Obstacle appears every 20s for 5s
#     def get_robot_pose(self):
#         # Simulate the robot's pose moving over time
#         return (self.pose_x, self.pose_y, self.pose_theta)
# # --- End of Conceptual Placeholders ---

# # Configure basic logging
# logger = logging.getLogger("AINavigation")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class NavigationStatus(Enum):
#     IDLE = auto()
#     PLANNING = auto()
#     NAVIGATING = auto()
#     OBSTACLE_AVOIDING = auto()
#     RECOVERING = auto()
#     SUCCEEDED = auto()
#     FAILED = auto()
#     CANCELLED = auto()

# Pose = Tuple[float, float, float] # (x, y, theta_radians)

# class AINavigationSystem:
#     """
#     Manages the entire autonomous navigation task, from planning to execution.
#     """
#     def __init__(self, planner: PathPlanner, motor_controller: MotorController, sensors: SensorSuite):
#         self.planner = planner
#         self.motors = motor_controller
#         self.sensors = sensors
        
#         self.status = NavigationStatus.IDLE
#         self.navigation_thread: Optional[threading.Thread] = None
#         self._stop_event = threading.Event()
        
#         logger.info("AI Navigation System initialized.")

#     def navigate_to_goal(self, goal_pose: Pose):
#         """
#         Starts the non-blocking navigation process to a specified goal pose.
#         """
#         if self.status not in [NavigationStatus.IDLE, NavigationStatus.SUCCEEDED, NavigationStatus.FAILED, NavigationStatus.CANCELLED]:
#             logger.warning("Already navigating to a goal. Please cancel first.")
#             return

#         self._stop_event.clear()
#         self.navigation_thread = threading.Thread(
#             target=self._navigation_loop,
#             args=(goal_pose,),
#             daemon=True
#         )
#         self.navigation_thread.start()
#         logger.info(f"Navigation to {goal_pose} initiated.")
    
#     def cancel_navigation(self):
#         """Stops the current navigation task."""
#         if self.navigation_thread and self.navigation_thread.is_alive():
#             logger.info("Cancellation request received. Stopping navigation...")
#             self._stop_event.set()
#             self.navigation_thread.join(timeout=2.0)
#             self.motors.stop_base()
#             self.status = NavigationStatus.CANCELLED

#     def get_status(self) -> Dict[str, Any]:
#         """Returns the current status of the navigation system."""
#         return {
#             "status": self.status.name,
#             "is_active": self.navigation_thread is not None and self.navigation_thread.is_alive()
#         }

#     def _navigation_loop(self, goal_pose: Pose):
#         """The core state machine for navigation, running in a separate thread."""
#         current_pose = self.sensors.get_robot_pose()
        
#         # 1. PLANNING State
#         self.status = NavigationStatus.PLANNING
#         global_path = self.planner.find_path(
#             start=(current_pose[0], current_pose[1]),
#             goal=(goal_pose[0], goal_pose[1])
#         )

#         if not global_path:
#             logger.error("Planning failed. Could not find a path to the goal.")
#             self.status = NavigationStatus.FAILED
#             return

#         logger.info(f"Path planned successfully with {len(global_path)} waypoints.")
#         self.status = NavigationStatus.NAVIGATING
        
#         waypoint_index = 0
#         stuck_counter = 0

#         # 2. NAVIGATING State (Main Loop)
#         while waypoint_index < len(global_path) and not self._stop_event.is_set():
#             current_pose = self.sensors.get_robot_pose()
#             target_waypoint = global_path[waypoint_index]

#             # --- Local Obstacle Avoidance ---
#             lidar_data = self.sensors.get_lidar_scan()
#             if lidar_data.get("obstacle_directly_ahead"):
#                 self.status = NavigationStatus.OBSTACLE_AVOIDING
#                 logger.warning("Dynamic obstacle detected! Attempting to avoid.")
#                 self.motors.set_base_velocity(0.0, 0.5) # Turn in place to look for a clear path
#                 time.sleep(1)
#                 continue # Re-evaluate on next loop iteration
            
#             self.status = NavigationStatus.NAVIGATING

#             # --- Path Following Logic ---
#             # In a real system, this would be a PID controller or similar control law.
#             # We will simulate the logic.
#             distance_to_waypoint = ((current_pose[0] - target_waypoint[0])**2 + (current_pose[1] - target_waypoint[1])**2)**0.5
            
#             if distance_to_waypoint < 0.2: # Waypoint reached tolerance
#                 logger.info(f"Reached waypoint {waypoint_index}: {target_waypoint}")
#                 waypoint_index += 1
#                 stuck_counter = 0
#             else:
#                 # Command motors to move towards the waypoint
#                 # This is a highly simplified control logic.
#                 linear_velocity = 0.5 # Constant forward speed
#                 angular_velocity = -0.3 # Turn towards the waypoint
#                 self.motors.set_base_velocity(linear_velocity, angular_velocity)

#             # --- Stuck Detection & Recovery ---
#             # (Conceptual) if the robot's pose hasn't changed much, increment stuck_counter
#             # if stuck_counter > 20: # e.g., stuck for 10 seconds
#             #     self.status = NavigationStatus.RECOVERING
#             #     logger.warning("Robot appears to be stuck. Initiating recovery behavior.")
#             #     self.motors.set_base_velocity(-0.2, 0.8) # Back up and turn
#             #     time.sleep(3)
#             #     # Force a replan
#             #     break # Exit inner loop and replan from current position

#             time.sleep(0.5) # Control loop frequency

#         # 3. END State
#         self.motors.stop_base()
#         if self._stop_event.is_set():
#             logger.info("Navigation was cancelled by user.")
#             self.status = NavigationStatus.CANCELLED
#         elif waypoint_index == len(global_path):
#             logger.info("Goal reached successfully!")
#             self.status = NavigationStatus.SUCCEEDED
#         else:
#              logger.error("Navigation loop exited without reaching goal. Setting status to FAILED.")
#              self.status = NavigationStatus.FAILED


# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== AI Navigation System Prototype 🧠🚗 ===")
#     print("=========================================================")

#     # 1. Create mock instances of the dependencies
#     mock_planner = PathPlanner()
#     mock_motors = MotorController()
#     mock_sensors = SensorSuite()
#     # Give the mock sensor a conceptual starting pose
#     mock_sensors.pose_x, mock_sensors.pose_y, mock_sensors.pose_theta = (0, 0, 0)

#     # 2. Initialize the navigation system
#     nav_system = AINavigationSystem(mock_planner, mock_motors, mock_sensors)

#     # 3. Start a navigation goal
#     goal = (10, 10, 0) # Target x=10, y=10, theta=0
#     print(f"\n--- Commanding robot to navigate to {goal} ---")
#     nav_system.navigate_to_goal(goal)

#     # 4. Monitor the status in the main thread
#     start_time = time.time()
#     while time.time() - start_time < 25: # Run demo for 25 seconds
#         status = nav_system.get_status()
#         print(f"  [{time.time() - start_time:.1f}s] Current Status: {status['status']}")
        
#         if not status['is_active']:
#             print("  -> Navigation task has finished.")
#             break
        
#         # Simulate the robot's pose changing over time
#         mock_sensors.pose_x += 0.25
#         mock_sensors.pose_y += 0.25
            
#         time.sleep(2)
        
#     # Final cleanup
#     nav_system.cancel_navigation()

#     print("\n=========================================================")
#     print("=== AI Navigation Prototype Complete ===")
#     print("=========================================================")

# Devin/modules/robotics/ai_navigation.py
# Purpose: A functional, high-level AI navigation system that orchestrates path
#          planning and motion control for autonomous movement.

import logging
import threading
import time
import math
from enum import Enum, auto
from typing import Optional, Any, Tuple, Dict

try:
    import numpy as np
    # --- Import other Devin modules ---
    from modules.robotics.path_planning import PathPlanner, PathType, GridLocation
    from modules.robotics_control_module import RoboticsControlModule
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("AINavigation")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class NavigationStatus(Enum):
    IDLE = auto()
    PLANNING = auto()
    NAVIGATING = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    CANCELLED = auto()

Pose = Tuple[float, float, float]  # (x_meters, y_meters, theta_degrees)

class AINavigationSystem:
    """
    Manages the entire autonomous navigation task, from planning to execution.
    """
    def __init__(self, planner: PathPlanner, robot_controller: RoboticsControlModule, map_resolution: float = 0.1):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
            
        self.planner = planner
        self.controller = robot_controller
        self.map_resolution = map_resolution # meters per grid cell
        
        self.status = NavigationStatus.IDLE
        self.navigation_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # This would come from a localization sensor (e.g., AMCL)
        self.current_pose: Pose = (0.0, 0.0, 0.0)

    def _world_to_grid(self, world_coord: Tuple[float, float]) -> GridLocation:
        """Converts real-world coordinates (meters) to grid coordinates."""
        return (int(world_coord[1] / self.map_resolution), int(world_coord[0] / self.map_resolution))

    def navigate_to_goal(self, goal_pose: Pose, get_current_pose_func: Callable[[], Pose]):
        """Starts the non-blocking navigation process."""
        if self.navigation_thread and self.navigation_thread.is_alive():
            logger.warning("Already navigating. Please cancel first.")
            return

        self._stop_event.clear()
        self.navigation_thread = threading.Thread(
            target=self._navigation_loop,
            args=(goal_pose, get_current_pose_func),
            daemon=True
        )
        self.navigation_thread.start()

    def cancel_navigation(self):
        """Stops the current navigation task."""
        if self.navigation_thread and self.navigation_thread.is_alive():
            self._stop_event.set()
            self.navigation_thread.join(timeout=2.0)
            self.controller.trigger_emergency_stop()
            self.status = NavigationStatus.CANCELLED

    def _navigation_loop(self, goal_pose: Pose, get_current_pose_func: Callable[[], Pose]):
        """The core state machine for navigation, running in a separate thread."""
        self.current_pose = get_current_pose_func()
        
        # 1. PLANNING State
        self.status = NavigationStatus.PLANNING
        start_grid = self._world_to_grid((self.current_pose[0], self.current_pose[1]))
        goal_grid = self._world_to_grid((goal_pose[0], goal_pose[1]))
        
        path = self.planner.find_path(start_grid, goal_grid, smooth=True)

        if not path:
            logger.error("Planning failed. Could not find a path to the goal.")
            self.status = NavigationStatus.FAILED
            return

        logger.info(f"Path planned successfully with {len(path)} waypoints.")
        self.status = NavigationStatus.NAVIGATING
        
        # 2. NAVIGATING State (Path Following)
        for i in range(len(path) - 1):
            if self._stop_event.is_set():
                break

            self.current_pose = get_current_pose_func()
            next_waypoint_grid = path[i+1]
            next_waypoint_world = (next_waypoint_grid[1] * self.map_resolution, next_waypoint_grid[0] * self.map_resolution)
            
            logger.info(f"Navigating to waypoint {i+1}/{len(path)-1}: {next_waypoint_world}")

            # Simple Go-To-Goal Controller
            while not self._stop_event.is_set():
                self.current_pose = get_current_pose_func()
                
                delta_x = next_waypoint_world[0] - self.current_pose[0]
                delta_y = next_waypoint_world[1] - self.current_pose[1]
                
                distance_to_goal = math.sqrt(delta_x**2 + delta_y**2)
                
                if distance_to_goal < 0.1: # Waypoint reached tolerance (10cm)
                    logger.info(f"  Reached waypoint {i+1}.")
                    break
                    
                # Calculate required heading
                target_theta = math.degrees(math.atan2(delta_y, delta_x))
                
                # Calculate heading error
                heading_error = target_theta - self.current_pose[2]
                # Normalize angle to [-180, 180]
                while heading_error > 180: heading_error -= 360
                while heading_error < -180: heading_error += 360
                
                # --- Control Logic ---
                if abs(heading_error) > 5.0: # Turn first if not facing the goal
                    # Proportional control for rotation
                    rotation_speed = 0.5 * (heading_error / 180.0)
                    self.controller.set_base_velocity(0.0, rotation_speed)
                else:
                    # Proportional control for forward movement
                    linear_speed = 0.3 * distance_to_goal
                    linear_speed = max(0.1, min(0.5, linear_speed)) # Clamp speed
                    self.controller.set_base_velocity(linear_speed, 0.0)
                
                time.sleep(0.1) # Control loop frequency

        # 3. END State
        self.controller.trigger_emergency_stop() # Stop all movement
        if self._stop_event.is_set():
            self.status = NavigationStatus.CANCELLED
        else:
            self.status = NavigationStatus.SUCCEEDED
            logger.warning("--- Navigation Succeeded: Goal Reached ---")

# --- Example Usage with a Live, Visual Simulation ---
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation

    print("=========================================================")
    print("=== Integrated AI Navigation System (Live Simulation) ===")
    print("=========================================================")

    # --- 1. Setup the Simulation Environment ---
    grid_map = np.zeros((50, 50))
    grid_map[10:40, 20:25] = 1 # Add a wall
    grid_map[25:30, 30:45] = 1 # Add another wall
    
    class SimulatedRobotState:
        def __init__(self, x=0.5, y=0.5, theta=0.0):
            self.pose = Pose(x, y, theta)
        def get_pose(self): return self.pose
        def update_pose(self, linear_vel, angular_vel, dt):
            x, y, theta_deg = self.pose
            theta_rad = math.radians(theta_deg)
            
            x += linear_vel * math.cos(theta_rad) * dt
            y += linear_vel * math.sin(theta_rad) * dt
            theta_deg += math.degrees(angular_vel * dt)
            
            self.pose = Pose(x, y, theta_deg % 360)

    class MockRoboticsController:
        def __init__(self, robot_state: SimulatedRobotState):
            self.state = robot_state
            self.linear = 0.0
            self.angular = 0.0
        def set_base_velocity(self, linear, angular):
            self.linear = linear
            self.angular = angular
        def trigger_emergency_stop(self):
            self.linear = 0.0
            self.angular = 0.0
        def update(self, dt):
            self.state.update_pose(self.linear, self.angular, dt)

    # --- 2. Initialize the Full Stack ---
    robot_state = SimulatedRobotState()
    mock_controller = MockRoboticsController(robot_state)
    planner = PathPlanner(occupancy_grid=grid_map)
    nav_system = AINavigationSystem(planner, mock_controller, map_resolution=0.1)

    # --- 3. Start the Navigation Task ---
    goal = Pose(4.5, 4.5, 0.0)
    nav_system.navigate_to_goal(goal, robot_state.get_pose)
    
    # --- 4. Live Visualization ---
    fig, ax = plt.subplots(figsize=(8, 8))
    path_history = []
    
    def animate(i):
        # Update the robot's physical state based on controller commands
        mock_controller.update(dt=0.1)
        
        ax.clear()
        ax.imshow(grid_map, cmap='gray_r', origin='lower')
        
        # Plot planned path if available
        if nav_system.status != NavigationStatus.PLANNING and hasattr(nav_system, 'path'):
            path_coords = np.array(nav_system.path)
            ax.plot(path_coords[:, 1], path_coords[:, 0], 'g--', label="Planned Path")
        
        # Plot robot's history
        path_history.append((robot_state.get_pose()[0] / 0.1, robot_state.get_pose()[1] / 0.1))
        if len(path_history) > 1:
            hist_arr = np.array(path_history)
            ax.plot(hist_arr[:, 0], hist_arr[:, 1], 'b-', label="Actual Path")
        
        # Plot robot's current position and orientation
        rx, ry, rtheta = robot_state.get_pose()
        rx_grid, ry_grid = rx / 0.1, ry / 0.1
        ax.plot(rx_grid, ry_grid, 'bo', markersize=10, label="Robot")
        ax.arrow(rx_grid, ry_grid, 2*math.cos(math.radians(rtheta)), 2*math.sin(math.radians(rtheta)), head_width=0.5, color='b')
        
        ax.set_title(f"AI Navigation Simulation - Status: {nav_system.status.name}")
        ax.legend()

    ani = animation.FuncAnimation(fig, animate, interval=100, frames=200) # Run for 200 frames (20s)
    plt.show()

    nav_system.cancel_navigation()

    print("\n=========================================================")
    print("=== AI Navigation Simulation Complete ===")
    print("=========================================================")
