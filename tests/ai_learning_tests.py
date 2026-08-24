# Devin/tests/ai_learning_tests.py
# Purpose: An integration test suite for the AI learning pipeline, verifying
#          the client-server communication for managing training jobs.

import unittest
import threading
import time
import requests

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

_import_error = None

try:
    from servers.ai_learning_server import AILearningServer
    from modules.ai_learning_module import AILearningFacade
    from unittest.mock import patch
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    _import_error = e

# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)


@unittest.skipUnless(DEPS_AVAILABLE, f"Skipping AI learning tests, dependency missing: {_import_error}")
class TestAILearningPipeline(unittest.TestCase):
    """
    Tests the full client-server pipeline for starting and monitoring training jobs.
    """
    server_thread = None
    server_port = 5007 # Use a unique port for testing
    server_url = f"http://127.0.0.1:{server_port}"
    
    @classmethod
    def setUpClass(cls):
        """Starts the AILearningServer in a background thread before any tests run."""
        cls.server_instance = AILearningServer()
        # The server only accepts jobs for models registered ahead of time.
        cls.server_instance.register_training_job("test-model", lambda **kwargs: kwargs)

        # This is the actual training function we will mock.
        # Note: _run_training_process is a real instance method (self, job_id,
        # params), so accessing it as self._run_training_process(...) always
        # binds the instance as the first positional argument -- the mock
        # must accept it too, even though it uses the closed-over
        # cls.server_instance instead.
        def mock_training_process(self, job_id, params):
            """A mock function that simulates a fast, successful training run."""
            cls.server_instance.jobs[job_id]["status"] = "RUNNING"
            time.sleep(2) # Simulate work
            cls.server_instance.jobs[job_id]["status"] = "COMPLETED"
            cls.server_instance.jobs[job_id]["fine_tuned_model_id"] = f"ft-model-{job_id[:8]}"

        # Patch the real, slow training method with our fast mock
        cls.patcher = patch.object(AILearningServer, '_run_training_process', new=mock_training_process)
        cls.patcher.start()

        cls.server_thread = threading.Thread(
            target=cls.server_instance.run,
            args=("127.0.0.1", cls.server_port),
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(1) # Give the server a moment to start up

    @classmethod
    def tearDownClass(cls):
        """Stops the server and the patcher after all tests have run."""
        cls.patcher.stop()
        # To stop a Flask/Werkzeug server, we can send a shutdown request
        try:
            requests.post(f"{cls.server_url}/shutdown")
        except requests.ConnectionError:
            # This is expected as the server shuts down immediately
            pass
        if cls.server_thread:
            cls.server_thread.join(timeout=2)

    def setUp(self):
        """Create a new facade instance for each test."""
        self.facade = AILearningFacade(server_url=self.server_url)

    def test_full_training_job_lifecycle(self):
        """
        Verifies the complete lifecycle of a training job:
        1. Start the job and get a valid ID.
        2. Poll the status and see it "RUNNING".
        3. Poll again after a delay and see it "COMPLETED".
        4. List all jobs and find the created job.
        """
        print("\n\n--- Testing Full AI Training Job Lifecycle ---")
        
        # 1. Start the job
        print("  [1/4] Submitting new training job...")
        job_id = self.facade.start_training_job(
            model_name="test-model",
            parameters={"dataset": "test.jsonl", "epochs": 1}
        )
        self.assertIsNotNone(job_id)
        self.assertIsInstance(job_id, str)
        print(f"  --> Job submitted successfully with ID: {job_id}")

        # 2. Poll for "RUNNING" status
        print("  [2/4] Polling for 'RUNNING' status...")
        time.sleep(0.5) # Give the server a moment to process
        status = self.facade.get_training_job_status(job_id)
        self.assertIsNotNone(status)
        self.assertEqual(status["status"], "RUNNING")
        print("  --> Status is correctly 'RUNNING'.")
        
        # 3. Poll for "COMPLETED" status
        print("  [3/4] Waiting for job to complete...")
        time.sleep(2.5) # Wait for our 2-second mock training to finish
        status = self.facade.get_training_job_status(job_id)
        self.assertIsNotNone(status)
        self.assertEqual(status["status"], "COMPLETED")
        self.assertIn("ft-model-", status["fine_tuned_model_id"])
        print(f"  --> Status is correctly 'COMPLETED'. New model ID: {status['fine_tuned_model_id']}")

        # 4. List all jobs
        print("  [4/4] Verifying job appears in the full job list...")
        all_jobs = self.facade.list_all_jobs()
        self.assertIn(job_id, all_jobs)
        self.assertEqual(all_jobs[job_id]['status'], "COMPLETED")
        print("  --> Job found in the list.")

    def test_get_status_for_invalid_job_id(self):
        """
        Verify that querying for a non-existent job ID returns None.
        """
        print("\n\n--- Testing Invalid Job ID Handling ---")
        status = self.facade.get_training_job_status("this-is-not-a-valid-id")
        self.assertIsNone(status)
        print("  [SUCCESS] Facade correctly returned None for an invalid job ID.")


if __name__ == '__main__':
    unittest.main()
