# Devin/security/incident_response/soar_workflows.py
# Purpose: A client for a SOAR platform (modeled after Cortex XSOAR) to
#          automate incident response workflows.

import logging
import requests
import json
from typing import Dict, Any, Optional

# Imports for the self-contained mock server demo
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configure basic logging
logger = logging.getLogger("SOAR_Client")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class CortexXSOAR_Client:
    """
    An API client for interacting with a Palo Alto Cortex XSOAR instance.
    """
    def __init__(self, base_url: str, api_key: str):
        if not base_url.startswith(('http://', 'https://')):
            raise ValueError("Invalid base_url. Must start with http:// or https://")
        
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _api_request(self, method: str, endpoint: str, json_data: Optional[Dict] = None) -> Dict:
        """Helper method for making API requests."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.request(method, url, json=json_data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"HTTP Error for {method} {url}: {e.response.status_code} {e.response.text}")
            raise
        except requests.RequestException as e:
            logger.error(f"Request failed for {method} {url}: {e}")
            raise

    def create_incident(self, name: str, severity: int, incident_type: str, owner: str) -> Dict:
        """Creates a new incident in XSOAR."""
        logger.info(f"Creating incident: '{name}'")
        payload = {
            "name": name,
            "type": incident_type,
            "severity": severity,
            "owner": owner,
            "createInvestigation": True
        }
        return self._api_request("POST", "incident", json_data=payload)

    def execute_command(self, incident_id: str, command: str) -> Dict:
        """Executes a command (automation) in the context of an incident."""
        logger.info(f"Executing command '{command}' on incident {incident_id}...")
        payload = {
            "query": command,
            "incidentId": incident_id
        }
        return self._api_request("POST", "execute-command", json_data=payload)

# --- Example Usage with a Mock API Server ---

class MockAPIHandler(BaseHTTPRequestHandler):
    """A mock HTTP request handler to simulate the Cortex XSOAR API."""
    mock_incidents = {}
    next_id = 1

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        if self.path == '/incident':
            incident_id = str(self.next_id)
            self.mock_incidents[incident_id] = {**data, "id": incident_id, "status": "active"}
            self.next_id += 1
            self._send_json_response(self.mock_incidents[incident_id])
        
        elif self.path == '/execute-command':
            response = {
                "reply": f"Command '{data.get('query')}' executed successfully on incident {data.get('incidentId')}.",
                "entries": []
            }
            self._send_json_response(response)
        else:
            self._send_error(404)

    def _send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _send_error(self, code):
        self.send_response(code)
        self.end_headers()

def start_mock_server(port=8080):
    """Starts the mock API server in a background thread."""
    server = HTTPServer(('', port), MockAPIHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    logger.info(f"Mock API server started on http://localhost:{port}")
    return server


if __name__ == "__main__":
    print("=========================================================")
    print("=== SOAR Workflow Client Prototype 🛡️⚙️ ===")
    print("=========================================================")
    
    mock_server = start_mock_server()
    
    try:
        # 1. Initialize the client to talk to our mock server
        client = CortexXSOAR_Client(base_url="http://localhost:8080", api_key="dummy-key")
        
        # 2. Create a new incident
        print("\n--- 1. Creating a new 'Phishing Alert' incident ---")
        new_incident = client.create_incident(
            name="Phishing Email Detected from ceo@example-corp.com",
            severity=3, # High
            incident_type="Phishing",
            owner="Devin-AI"
        )
        print("Mock server responded with new incident:")
        print(json.dumps(new_incident, indent=2))
        incident_id = new_incident['id']
        
        # 3. Execute an enrichment command on the new incident
        print(f"\n--- 2. Running an enrichment playbook on incident #{incident_id} ---")
        command_result = client.execute_command(
            incident_id=incident_id,
            command="!Phishing-Investigation-Playbook"
        )
        print("Mock server responded:")
        print(json.dumps(command_result, indent=2))

    except Exception as e:
        logger.error(f"An error occurred during the demo: {e}", exc_info=True)
    finally:
        logger.info("Shutting down mock API server.")
        mock_server.shutdown()


    print("\n=========================================================")
    print("=== SOAR Client Prototype Complete ===")
    print("=========================================================")
