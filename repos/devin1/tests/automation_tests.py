# tests/automation_tests.py
# Automation Module Tests

import unittest
from modules.automation_tools import TaskScheduler, TaskExecutor, WebAutomation, APIHandler

class TestAutomationModule(unittest.TestCase):
    def setUp(self):
        # Set up common data for testing
        self.scheduler = TaskScheduler()
        self.executor = TaskExecutor()
        self.web_automation = WebAutomation()
        self.api_handler = APIHandler()

    def test_task_scheduler(self):
        # Test task scheduling functionality
        task_id = self.scheduler.schedule_task("Send Email", "2024-12-30 10:00:00")
        self.assertIsNotNone(task_id, "Task ID should not be None after scheduling.")
        self.assertTrue(self.scheduler.cancel_task(task_id), "Should be able to cancel scheduled tasks.")

    def test_task_executor(self):
        # Test task execution functionality
        task = {"name": "Clean Temporary Files", "time": "Immediate"}
        result = self.executor.execute_task(task)
        self.assertEqual(result["status"], "Success", "Task execution should succeed.")

    def test_web_automation(self):
        # Test web automation functionality
        result = self.web_automation.login_to_website(
            url="https://example.com",
            username="test_user",
            password="test_password"
        )
        self.assertTrue(result, "Web automation login should succeed.")

    def test_api_handler(self):
        # Test API handling functionality
        response = self.api_handler.send_request(
            method="GET",
            url="https://jsonplaceholder.typicode.com/posts/1",
            headers={"Accept": "application/json"}
        )
        self.assertEqual(response.status_code, 200, "API request should return status code 200.")
        self.assertIn("userId", response.json(), "Response should contain 'userId' key.")

    def tearDown(self):
        # Clean up resources
        del self.scheduler
        del self.executor
        del self.web_automation
        del self.api_handler

if __name__ == "__main__":
    unittest.main()
