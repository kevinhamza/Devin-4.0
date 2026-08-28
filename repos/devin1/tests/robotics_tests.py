"""
tests/robotics_tests.py

This file contains unit and integration tests for the robotics modules
to ensure accurate functionality and compatibility.
"""

import unittest
from modules.robotics.diagnostic_tools import DiagnosticTools
from modules.robotics.movement_controller import MovementController
from modules.robotics.sensor_manager import SensorManager
from modules.robotics.ai_planner import AIPlanner

class TestRoboticsModule(unittest.TestCase):

    def setUp(self):
        """Set up common resources for testing."""
        self.diagnostic_tools = DiagnosticTools()
        self.movement_controller = MovementController()
        self.sensor_manager = SensorManager()
        self.ai_planner = AIPlanner()

    def test_diagnostic_health_check(self):
        """Test the health check diagnostic functionality."""
        result = self.diagnostic_tools.run_health_check()
        self.assertTrue(result['status'], "Health check should pass")
        self.assertIn('details', result, "Result should contain diagnostic details")

    def test_movement_controller_initialization(self):
        """Test if the movement controller initializes correctly."""
        self.assertTrue(self.movement_controller.initialize())
        self.assertEqual(self.movement_controller.status, 'Initialized')

    def test_sensor_manager_data(self):
        """Test if the sensor manager retrieves accurate data."""
        sensor_data = self.sensor_manager.fetch_sensor_data()
        self.assertIsInstance(sensor_data, dict, "Sensor data should be a dictionary")
        self.assertIn('temperature', sensor_data, "Temperature data should be included")

    def test_ai_planner_task_execution(self):
        """Test if the AI planner can execute a given task."""
        task = {'name': 'navigate_to_point', 'parameters': {'x': 10, 'y': 20}}
        result = self.ai_planner.execute_task(task)
        self.assertTrue(result['success'], "Task execution should succeed")
        self.assertEqual(result['task_name'], task['name'])

    def test_full_integration(self):
        """Test full integration between modules."""
        self.movement_controller.initialize()
        self.sensor_manager.fetch_sensor_data()
        task = {'name': 'collect_data', 'parameters': {}}
        result = self.ai_planner.execute_task(task)
        self.assertTrue(result['success'], "Integration task should succeed")
        self.assertIn('task_name', result, "Result should include task name")

if __name__ == "__main__":
    unittest.main()
