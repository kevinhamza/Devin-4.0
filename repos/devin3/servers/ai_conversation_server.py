# Devin/servers/ai_conversation_server.py
# Purpose: A web server that handles real-time conversations with the AI,
#          integrating the ChatbotEngine and the TaskOrchestrator.

import logging
import os
import threading
from typing import Optional

try:
    from flask import Flask, request, jsonify
    from servers.task_orchestrator import TaskOrchestrator
    from modules.ai_tools.chatbot_engine import ChatbotEngine
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e


# Configure basic logging
logger = logging.getLogger("AIConversationServer")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class AIConversationServer:
    """
    Wraps the Flask application and manages the core AI and orchestration components.
    """
    def __init__(self):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required for the ChatbotEngine.")

        # --- Initialize Core Components ---
        # These are treated as singletons for the lifetime of the server.
        self.orchestrator = TaskOrchestrator()
        self.chatbot_engine = ChatbotEngine()
        
        # --- Initialize Flask App ---
        self.app = Flask(__name__)
        self._register_routes()

    def _register_routes(self):
        """Defines the API endpoints for the server."""
        @self.app.route("/message", methods=["POST"])
        def handle_message():
            data = request.get_json()
            if not data or "message" not in data:
                return jsonify({"error": "Invalid request. 'message' field is required."}), 400
            
            user_message = data["message"]
            logger.info(f"Received message: '{user_message}'")
            
            # Process message with the AI "brain"
            responses = self.chatbot_engine.process_user_message(user_message)
            
            final_reply = ""
            task_ids = []

            for response in responses:
                if response['type'] == 'text':
                    final_reply += response.get('content', '') + "\n"
                elif response['type'] == 'tool_call':
                    tool_name = response.get('function_name')
                    parameters = response.get('arguments', {})
                    # TODO: Add safety checks here (CFAA, Ethical Enforcer)
                    # before submitting the task.
                    task_id = self.orchestrator.submit_task(tool_name, parameters)
                    task_ids.append(task_id)

            return jsonify({
                "reply": final_reply.strip(),
                "task_ids": task_ids
            })

        @self.app.route("/task_status/<task_id>", methods=["GET"])
        def get_task_status(task_id: str):
            task = self.orchestrator.get_task_status(task_id)
            if not task:
                return jsonify({"error": "Task not found."}), 404
            
            # Convert dataclass to dict for JSON serialization
            return jsonify(task.__dict__)

    def run(self, host: str = '127.0.0.1', port: int = 5000):
        """Starts the TaskOrchestrator and the Flask web server."""
        try:
            # Start the backend task processing system
            self.orchestrator.start()
            # Start the user-facing web server
            logger.warning(f"Starting AI Conversation Server on http://{host}:{port}")
            self.app.run(host=host, port=port)
        finally:
            self.orchestrator.shutdown()

# --- Example Usage ---

def run_client_demo():
    """A simple client to demonstrate interacting with the running server."""
    import requests
    import time
    
    SERVER_URL = "http://127.0.0.1:5000"
    
    # --- 1. Send a message that will trigger a tool call ---
    print("\n--- 1. Sending a message to the AI server ---")
    message = "What is the result of 25 * 4?"
    print(f"Client: '{message}'")
    response = requests.post(f"{SERVER_URL}/message", json={"message": message})
    
    if response.status_code == 200:
        data = response.json()
        print(f"Server: '{data['reply']}'")
        
        # --- 2. Poll for the task status ---
        if data['task_ids']:
            task_id = data['task_ids'][0]
            print(f"\n--- 2. Polling for status of task {task_id[:8]}... ---")
            
            while True:
                status_response = requests.get(f"{SERVER_URL}/task_status/{task_id}")
                status_data = status_response.json()
                print(f"  Current task status: {status_data['status']}")
                
                if status_data['status'] in ["COMPLETED", "FAILED"]:
                    print("\n--- 3. Task finished ---")
                    print("Final Result:")
                    print(json.dumps(status_data, indent=2))
                    break
                time.sleep(1)
        else:
            print("Server did not initiate a background task.")
    else:
        print(f"Error communicating with server: {response.status_code} {response.text}")


if __name__ == "__main__":
    print("=========================================================")
    print("=== AI Conversation Server Prototype 🤖💬 ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module is missing. Please ensure all project files are present. Error: {_import_error}")
    elif not os.getenv("OPENAI_API_KEY"):
        print("\nERROR: OPENAI_API_KEY environment variable is required.")
    else:
        server = AIConversationServer()
        
        # Run the server in a background thread so we can run the client demo
        server_thread = threading.Thread(target=server.run, daemon=True)
        server_thread.start()
        time.sleep(2) # Give the server a moment to start up
        
        run_client_demo()
        
        # In a real app, the server would run indefinitely. For the demo, we stop it here.
        # This requires a way to gracefully shut down Flask, which is complex.
        # For this demo, we will just exit, and the daemon thread will be terminated.
        logger.info("Demo complete. Exiting...")


    print("\n=========================================================")
    print("=== AI Conversation Server Prototype Complete ===")
    print("=========================================================")
