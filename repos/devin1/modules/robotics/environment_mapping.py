"""
Environment Mapping Module
===========================
Generates real-time maps of the surrounding environment using sensor data
to aid in navigation and path planning.
"""

import numpy as np
import logging
from modules.robotics.sensor_integration import SensorManager
from scipy.spatial import KDTree


class EnvironmentMapping:
    """
    Handles the mapping of the environment for robotics applications.
    """

    def __init__(self, map_size=(100, 100), resolution=0.1):
        """
        Initializes the mapping module.

        Args:
            map_size (tuple): Size of the map (width, height) in meters.
            resolution (float): Map resolution in meters per grid cell.
        """
        print("[INFO] Initializing Environment Mapping Module...")
        self.map_size = map_size
        self.resolution = resolution
        self.grid_map = np.zeros(
            (int(map_size[0] / resolution), int(map_size[1] / resolution)), dtype=np.uint8
        )
        self.sensor_manager = SensorManager()
        self.kd_tree = None

    def update_map(self, sensor_data):
        """
        Updates the grid map with the latest sensor data.

        Args:
            sensor_data (dict): Sensor readings, including LIDAR and cameras.
        """
        print("[INFO] Updating the environment map with sensor data...")
        try:
            lidar_data = sensor_data.get("lidar")
            if lidar_data is not None:
                self.add_lidar_data(lidar_data)

            obstacle_points = np.argwhere(self.grid_map == 1)
            self.kd_tree = KDTree(obstacle_points)
            print("[INFO] Map updated successfully.")
        except Exception as e:
            logging.error(f"Error updating map: {e}")

    def add_lidar_data(self, lidar_points):
        """
        Adds LIDAR data to the grid map.

        Args:
            lidar_points (list): List of LIDAR points as (x, y) tuples in meters.
        """
        print("[INFO] Adding LIDAR data to the map...")
        try:
            for x, y in lidar_points:
                grid_x = int(x / self.resolution)
                grid_y = int(y / self.resolution)
                if 0 <= grid_x < self.grid_map.shape[0] and 0 <= grid_y < self.grid_map.shape[1]:
                    self.grid_map[grid_x, grid_y] = 1
        except Exception as e:
            logging.error(f"Error adding LIDAR data: {e}")

    def get_map(self):
        """
        Returns the current grid map.

        Returns:
            np.ndarray: The current grid map.
        """
        return self.grid_map

    def save_map(self, file_path="environment_map.npy"):
        """
        Saves the current map to a file.

        Args:
            file_path (str): Path to save the map file.
        """
        print(f"[INFO] Saving the map to {file_path}...")
        try:
            np.save(file_path, self.grid_map)
            print("[INFO] Map saved successfully.")
        except Exception as e:
            logging.error(f"Error saving map: {e}")

    def load_map(self, file_path="environment_map.npy"):
        """
        Loads a saved map from a file.

        Args:
            file_path (str): Path to the saved map file.
        """
        print(f"[INFO] Loading the map from {file_path}...")
        try:
            self.grid_map = np.load(file_path)
            print("[INFO] Map loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading map: {e}")

    def find_nearest_obstacle(self, point):
        """
        Finds the nearest obstacle to the given point.

        Args:
            point (tuple): The point (x, y) in meters.

        Returns:
            tuple: Coordinates of the nearest obstacle or None if no obstacles are found.
        """
        if self.kd_tree is None:
            print("[WARNING] No obstacles detected yet.")
            return None

        print("[INFO] Finding the nearest obstacle...")
        grid_point = (int(point[0] / self.resolution), int(point[1] / self.resolution))
        distance, index = self.kd_tree.query(grid_point)
        return self.kd_tree.data[index] * self.resolution


# Example usage
if __name__ == "__main__":
    env_map = EnvironmentMapping(map_size=(50, 50), resolution=0.5)
    sample_lidar_data = [(5, 5), (10, 10), (15, 15), (20, 20)]
    env_map.update_map({"lidar": sample_lidar_data})
    env_map.save_map()
    print("[INFO] Map data saved.")
