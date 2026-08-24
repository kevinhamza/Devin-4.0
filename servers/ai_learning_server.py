# Devin/servers/ai_learning_server.py
# Purpose: A microservice for managing and executing long-running machine
#          learning training jobs (supervised, reinforcement, etc.).

import logging
import json
import threading
import uuid
import time
from typing import Dict, Any, Callable

try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("AILearningServer")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class AILearningServer:
    """
    Wraps a Flask application to provide an API for ML training jobs.
    """
    def __init__(self):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required. 'pip install Flask'")

        # --- State for async jobs ---
        self.jobs: Dict[str, Any] = {}
        
        # --- Registry for trainable models ---
        self.training_registry: Dict[str, Callable] = {}

        # --- Initialize Flask App ---
        self.app = Flask(__name__)
        self._register_routes()

    def register_training_job(self, model_name: str, training_function: Callable):
        """Registers a new training function with the server."""
        logger.info(f"Registering training function for model '{model_name}'")
        self.training_registry[model_name] = training_function

    def _run_training_process(self, job_id: str, params: Dict):
        """Wrapper function to run a training job and update its status."""
        self.jobs[job_id]["status"] = "RUNNING"
        self.jobs[job_id]["start_time"] = time.time()
        logger.info(f"Starting training job {job_id}...")
        try:
            model_name = self.jobs[job_id]["model_name"]
            training_func = self.training_registry[model_name]
            # The training function itself is responsible for logging progress
            result = training_func(**params)
            self.jobs[job_id]["status"] = "COMPLETED"
            self.jobs[job_id]["result"] = result
        except Exception as e:
            logger.error(f"Training job {job_id} failed: {e}", exc_info=True)
            self.jobs[job_id]["status"] = "FAILED"
            self.jobs[job_id]["result"] = str(e)
        finally:
            self.jobs[job_id]["end_time"] = time.time()
            duration = self.jobs[job_id]["end_time"] - self.jobs[job_id]["start_time"]
            logger.info(f"Training job {job_id} finished with status '{self.jobs[job_id]['status']}' in {duration:.2f}s.")

    def _register_routes(self):
        """Defines the API endpoints for the server."""
        
        @self.app.route("/train", methods=["POST"])
        def train_model():
            data = request.get_json()
            if not data or "model_name" not in data:
                return jsonify({"error": "Missing 'model_name' in request."}), 400
            
            model_name = data["model_name"]
            params = data.get("parameters", {})
            
            training_func = self.training_registry.get(model_name)
            if not training_func:
                return jsonify({"error": f"Model '{model_name}' not registered."}), 404

            job_id = str(uuid.uuid4())
            self.jobs[job_id] = {"status": "QUEUED", "result": None, "model_name": model_name}
            
            thread = threading.Thread(
                target=self._run_training_process,
                args=(job_id, params)
            )
            thread.daemon = True
            thread.start()

            return jsonify({"message": f"Training job for model '{model_name}' started.", "job_id": job_id}), 202

        @self.app.route("/train/status/<job_id>", methods=["GET"])
        def get_training_status(job_id: str):
            job = self.jobs.get(job_id)
            if not job:
                return jsonify({"error": "Job not found."}), 404
            return jsonify(job)

        @self.app.route("/train/jobs", methods=["GET"])
        def list_jobs():
            return jsonify(self.jobs)

        @self.app.route("/shutdown", methods=["POST"])
        def shutdown():
            func = request.environ.get('werkzeug.server.shutdown')
            if func:
                func()
            return jsonify({"status": "shutting down"})

    def run(self, host: str = '127.0.0.1', port: int = 5005):
        """Starts the Flask web server."""
        logger.warning(f"Starting AI Learning Server on http://{host}:{port}")
        self.app.run(host=host, port=port)

# --- Example Usage ---

def dummy_supervised_training(epochs: int, learning_rate: float):
    """A mock training function that simulates a long-running ML task."""
    logger.info(f"Starting dummy training for {epochs} epochs with lr={learning_rate}...")
    for epoch in range(1, epochs + 1):
        logger.info(f"  Epoch {epoch}/{epochs}...")
        time.sleep(2) # Simulate work
    logger.info("Dummy training complete.")
    return {"final_accuracy": 0.95, "model_path": "/models/dummy_model_v1.pth"}

def run_client_demo():
    """A simple client to demonstrate interacting with the running server."""
    import requests
    
    SERVER_URL = "http://127.0.0.1:5005"
    
    print("\n--- 1. Submitting a training job for 'dummy_classifier' ---")
    payload = {
        "model_name": "dummy_classifier",
        "parameters": {
            "epochs": 5,
            "learning_rate": 0.01
        }
    }
    response = requests.post(f"{SERVER_URL}/train", json=payload)
    
    if response.status_code == 202:
        data = response.json()
        job_id = data['job_id']
        print(f"Server accepted the training job. Job ID: {job_id[:8]}...")
        
        print("\n--- 2. Polling for training status ---")
        while True:
            status_response = requests.get(f"{SERVER_URL}/train/status/{job_id}")
            status_data = status_response.json()
            print(f"  Current job status: {status_data['status']}")
            
            if status_data['status'] in ["COMPLETED", "FAILED"]:
                print("\n--- 3. Job finished ---")
                print("Final Result:")
                print(json.dumps(status_data, indent=2))
                break
            time.sleep(1)
    else:
        print(f"Error submitting job: {response.status_code} {response.text}")


if __name__ == "__main__":
    print("=========================================================")
    print("=== AI Learning Server Prototype 🧠🎓 ===")
    print("=========================================================")
    
    if not FLASK_AVAILABLE:
        print(f"\nERROR: Flask is missing. Please run 'pip install Flask'")
    else:
        server = AILearningServer()
        
        # Register our dummy training function so the server knows about it
        server.register_training_job("dummy_classifier", dummy_supervised_training)
        
        # Run the server in a background thread so we can run the client demo
        server_thread = threading.Thread(target=server.run, args=('127.0.0.1', 5005), daemon=True)
        server_thread.start()
        time.sleep(2) # Give the server a moment to start up
        
        run_client_demo()
        
        logger.info("Demo complete. Exiting...")

    print("\n=========================================================")
    print("=== AI Learning Server Prototype Complete ===")
    print("=========================================================")
