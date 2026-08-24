# Devin/tests/robotics_tests.py
# Purpose: An integration test suite for the entire robotics stack,
#          verifying the "sense-think-act" loop in a simulated environment.

import unittest
import time
import math
from typing import Tuple, NamedTuple

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

_import_error = None

try:
    import numpy as np
    import cv2
    # --- Import all the REAL robotics modules to be tested ---
    from modules.robotics.sensor_integration import Camera
    from modules.robotics.object_detection import ObjectDetector
    from modules.robotics.path_planning import PathPlanner
    from modules.robotics.ai_navigation import AINavigationSystem, Pose, NavigationStatus
    from modules.robotics_control_module import RoboticsControlModule
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    _import_error = e


# --- Bug fix: `Pose` in modules.robotics.ai_navigation is just a typing
#     alias (`Tuple[float, float, float]`), which cannot be instantiated
#     like a class (`Pose(0.2, 0.2, 0.0)` raises TypeError: "Type Tuple
#     cannot be instantiated"). The tests below need a real, constructible
#     Pose, so we shadow the imported alias with a lightweight NamedTuple
#     that remains duck-type compatible with plain tuples (indexing,
#     slicing, unpacking) wherever production code expects a
#     `Tuple[float, float, float]`.
if DEPS_AVAILABLE:
    class Pose(NamedTuple):
        x: float
        y: float
        theta: float


# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)

# --- A Simulated World for the Test ---
class MockCamera(Camera):
    """A mock camera that returns a pre-generated image."""
    def __init__(self, image_to_serve: np.ndarray):
        self._image = image_to_serve
        self.is_active = False
    def connect(self) -> bool:
        self.is_active = True
        return True
    def read_data(self) -> np.ndarray:
        return self._image.copy()
    def disconnect(self):
        self.is_active = False

class MockRoboticsControlModule(RoboticsControlModule):
    """A mock controller that updates a simulated robot's pose."""
    def __init__(self):
        self.pose = Pose(0.2, 0.2, 0.0) # Start at (x=0.2m, y=0.2m, theta=0deg)
        self.linear_vel = 0.0
        self.angular_vel = 0.0
    def set_base_velocity(self, linear, angular):
        self.linear_vel = linear
        self.angular_vel = angular
    def trigger_emergency_stop(self):
        self.linear_vel = 0.0
        self.angular_vel = 0.0
    def get_pose(self) -> Pose:
        return self.pose
    def update(self, dt): # Simulate physics
        x, y, theta_deg = self.pose
        theta_rad = math.radians(theta_deg)
        x += self.linear_vel * math.cos(theta_rad) * dt
        y += self.linear_vel * math.sin(theta_rad) * dt
        theta_deg += math.degrees(self.angular_vel * dt)
        self.pose = Pose(x, y, theta_deg % 360)


@unittest.skipUnless(DEPS_AVAILABLE, f"Skipping robotics integration tests, dependency missing: {_import_error}")
class TestRoboticsIntegrationSuite(unittest.TestCase):
    """
    Tests the full robotics pipeline from perception to action.
    """
    @classmethod
    def setUpClass(cls):
        """Set up the entire simulated environment and all robot modules."""
        print("\n--- Setting up Robotics Integration Test Environment ---")
        # 1. Define the world
        cls.MAP_RESOLUTION = 0.1 # meters per pixel
        cls.TARGET_WORLD_POS = (2.5, 3.0) # Target object is at x=2.5m, y=3.0m
        
        # 2. Create the occupancy grid map
        grid_map = np.zeros((50, 50), dtype=np.uint8)
        grid_map[10:40, 20:25] = 1 # A vertical wall
        cls.grid_map = grid_map

        # 3. Create the camera's view of the world
        # A 640x480 image. Target is a red "cup"
        camera_view = np.full((480, 640, 3), (200, 200, 200), dtype=np.uint8)
        # The cup is at pixel (400, 200) in the image
        cv2.circle(camera_view, (400, 200), 30, (0, 0, 255), -1) # Red circle
        cls.camera_view = camera_view

        # 4. Instantiate Mocks
        cls.mock_camera = MockCamera(cls.camera_view)
        cls.mock_controller = MockRoboticsControlModule()

        # 5. Instantiate REAL modules
        # This will download the YOLO model on first run
        cls.object_detector = ObjectDetector(model_name='yolov8n.pt')
        cls.path_planner = PathPlanner(occupancy_grid=cls.grid_map)
        
        # 6. Instantiate the main navigation system
        cls.nav_system = AINavigationSystem(
            planner=cls.path_planner,
            robot_controller=cls.mock_controller,
            map_resolution=cls.MAP_RESOLUTION
        )

    def test_full_sense_plan_act_cycle(self):
        """
        Executes a full integration test:
        1. SENSE: Detect a "cup" with the camera.
        2. THINK: Plan a path to the cup's location.
        3. ACT: Navigate to the location and verify the final pose.
        """
        print("\n--- Testing Full Sense-Think-Act Cycle ---")

        # --- 1. SENSE PHASE ---
        print("  [Sense] Capturing and analyzing image...")
        frame = self.mock_camera.read_data()
        detections = self.object_detector.detect_objects(frame)
        
        self.assertGreater(len(detections), 0, "Object detector failed to find any objects.")
        
        # Find the cup (YOLOv8 knows what a cup is)
        cup_detections = [d for d in detections if d.label == 'cup']
        self.assertEqual(len(cup_detections), 1, "Expected to detect exactly one cup.")
        target_object = cup_detections[0]
        print(f"  [Sense] Successfully detected '{target_object.label}' in the image.")

        # --- 2. THINK PHASE ---
        print("  [Think] Planning path to the detected object...")
        # For this demo, we will map the single detected object directly to our known world position
        # A real system would use depth cameras or triangulation to find the 3D position.
        goal_pose = Pose(self.TARGET_WORLD_POS[0], self.TARGET_WORLD_POS[1], 0.0)
        
        # --- 3. ACT PHASE ---
        print(f"  [Act] Issuing navigation command to goal: {goal_pose[:2]}")
        self.nav_system.navigate_to_goal(goal_pose, self.mock_controller.get_pose)
        
        # Let the simulation run until the navigation is complete
        start_time = time.time()
        while self.nav_system.navigation_thread.is_alive():
            self.mock_controller.update(dt=0.1) # Update the simulation physics
            time.sleep(0.1)
            if time.time() - start_time > 30: # 30 second timeout
                self.fail("Navigation task timed out.")
        
        print("  [Act] Navigation task finished.")
        
        # --- 4. VERIFICATION ---
        print("  [Verify] Checking final robot pose against goal...")
        final_pose = self.mock_controller.get_pose()
        
        self.assertEqual(self.nav_system.status, NavigationStatus.SUCCEEDED, "Navigation system did not report success.")
        
        # Check if the final position is within a tolerance of the goal
        self.assertAlmostEqual(final_pose[0], goal_pose[0], delta=0.2, msg="Final X position is not close to the goal.")
        self.assertAlmostEqual(final_pose[1], goal_pose[1], delta=0.2, msg="Final Y position is not close to the goal.")
        
        print("  [Verify] SUCCESS! Robot navigated to the target object's location.")


if __name__ == '__main__':
    # Re-enable logging for the test runner's output
    logging.disable(logging.NOTSET)
    unittest.main()
