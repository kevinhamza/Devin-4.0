"""
AI Navigation Module
====================
Handles AI-powered navigation and decision-making for robotics.
"""

import logging
import numpy as np
from modules.robotics.path_planning import PathPlanning
from modules.robotics.sensor_integration import SensorManager
from modules.utils.ai_memory import MemoryManager


class NavigationConfig:
    def __init__(self, max_speed: float = 1.5, obstacle_tolerance: float = 0.2, replan_threshold: float = 0.5):
        """
        Configuration for AI Navigation.

        Args:
            max_speed (float): Maximum speed of the robot in m/s.
            obstacle_tolerance (float): Minimum distance from obstacles in meters.
            replan_threshold (float): Threshold to trigger path replanning in meters.
        """
        self.max_speed = max_speed
        self.obstacle_tolerance = obstacle_tolerance
        self.replan_threshold = replan_threshold


class AINavigation:
    def __init__(self, config: NavigationConfig):
        """
        Initializes the AI Navigation system.

        Args:
            config (NavigationConfig): Navigation configuration.
        """
        logging.info("Initializing AI Navigation Module...")
        self.config = config
        self.path_planner = PathPlanning()
        self.sensor_manager = SensorManager()
        self.memory = MemoryManager()
        self.current_path = []

    def plan_route(self, start: tuple, goal: tuple) -> list:
        """
        Plans a route from the start to the goal using path planning algorithms.

        Args:
            start (tuple): Starting coordinates (x, y).
            goal (tuple): Goal coordinates (x, y).

        Returns:
            list: Planned route as a list of waypoints.
        """
        logging.info(f"Planning route from {start} to {goal}...")
        self.current_path = self.path_planner.plan_path(start, goal)
        self.memory.save_navigation_log({"start": start, "goal": goal, "path": self.current_path})
        return self.current_path

    def avoid_obstacles(self, sensor_data: dict) -> tuple:
        """
        Adjusts the robot's path to avoid detected obstacles.

        Args:
            sensor_data (dict): Data from sensors (e.g., LIDAR, ultrasonic).

        Returns:
            tuple: Adjusted velocity (linear, angular).
        """
        logging.info("Checking for obstacles...")
        obstacles = sensor_data.get("obstacles", [])
        if not obstacles:
            return self.config.max_speed, 0.0  # No obstacles, move forward

        min_distance = min(obstacle["distance"] for obstacle in obstacles)
        if min_distance < self.config.obstacle_tolerance:
            logging.warning("Obstacle detected! Stopping robot.")
            return 0.0, 0.0  # Stop the robot

        # Adjust angular velocity to steer away from obstacles
        angular_velocity = -np.sign(obstacles[0]["angle"]) * 0.5
        logging.info(f"Avoiding obstacle with angular velocity: {angular_velocity}")
        return self.config.max_speed * 0.5, angular_velocity

    def execute_navigation(self, start: tuple, goal: tuple):
        """
        Executes the navigation process from start to goal.

        Args:
            start (tuple): Starting coordinates (x, y).
            goal (tuple): Goal coordinates (x, y).
        """
        logging.info("Starting navigation...")
        self.plan_route(start, goal)

        while True:
            sensor_data = self.sensor_manager.get_sensor_data()
            if not sensor_data:
                logging.error("Sensor data unavailable. Stopping navigation.")
                break

            current_position = sensor_data["position"]
            if np.linalg.norm(np.array(current_position) - np.array(goal)) < self.config.replan_threshold:
                logging.info("Goal reached!")
                break

            velocity = self.avoid_obstacles(sensor_data)
            self.sensor_manager.set_motor_commands(velocity)

            if velocity == (0.0, 0.0):
                logging.warning("Replanning route due to obstacle.")
                self.plan_route(current_position, goal)

    def log_navigation(self):
        """
        Logs detailed navigation data for debugging and optimization.
        """
        logging.info("Logging navigation details...")
        self.memory.save_navigation_summary()


# Example Usage
if __name__ == "__main__":
    config = NavigationConfig(max_speed=1.0, obstacle_tolerance=0.3, replan_threshold=0.5)
    ai_navigation = AINavigation(config)

    start_point = (0, 0)
    goal_point = (10, 10)

    try:
        ai_navigation.execute_navigation(start_point, goal_point)
    except KeyboardInterrupt:
        logging.info("Navigation terminated by user.")
