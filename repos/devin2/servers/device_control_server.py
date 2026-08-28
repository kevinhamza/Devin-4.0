# Devin/servers/device_control_server.py
# Purpose: A microservice to control hardware and connected peripherals like
#          webcams and serial port devices.

import logging
import threading
import time
from io import BytesIO

try:
    from flask import Flask, request, jsonify, send_file
    import cv2
    import serial
    import serial.tools.list_ports
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("DeviceControlServer")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class DeviceControlServer:
    """
    Wraps a Flask application to provide a REST API for hardware control.
    """
    def __init__(self):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")

        self.app = Flask(__name__)
        self._register_routes()

    def _register_routes(self):
        """Defines the API endpoints for the server."""
        
        @self.app.route("/webcam/capture", methods=["GET"])
        def webcam_capture():
            logger.info("Received request to capture image from webcam...")
            # Open a connection to the default webcam (index 0)
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return jsonify({"error": "Could not open webcam."}), 500
            
            try:
                # Allow camera to warm up
                time.sleep(1)
                ret, frame = cap.read()
                if not ret:
                    return jsonify({"error": "Failed to capture frame from webcam."}), 500
                
                # Encode the captured frame as a JPEG in memory
                is_success, buffer = cv2.imencode(".jpg", frame)
                if not is_success:
                    return jsonify({"error": "Failed to encode frame as JPEG."}), 500
                
                logger.info("Successfully captured and encoded frame.")
                return send_file(BytesIO(buffer), mimetype='image/jpeg')

            finally:
                cap.release()

        @self.app.route("/serial/ports", methods=["GET"])
        def serial_list_ports():
            logger.info("Scanning for available serial ports...")
            ports = serial.tools.list_ports.comports()
            return jsonify([{"device": p.device, "description": p.description} for p in ports])

        @self.app.route("/serial/send", methods=["POST"])
        def serial_send():
            data = request.get_json()
            if not data or "port" not in data or "command" not in data:
                return jsonify({"error": "Missing 'port' or 'command' in request."}), 400
            
            port = data['port']
            command = data['command']
            baud_rate = data.get('baud_rate', 9600)
            
            logger.info(f"Sending command to serial port {port}: '{command.strip()}'")
            try:
                with serial.Serial(port, baud_rate, timeout=1) as ser:
                    ser.write(command.encode('utf-8'))
                return jsonify({"status": "success", "message": f"Command sent to {port}."})
            except serial.SerialException as e:
                logger.error(f"Serial communication failed: {e}")
                return jsonify({"error": str(e)}), 500

    def run(self, host: str = '127.0.0.1', port: int = 5007):
        """Starts the Flask web server."""
        logger.warning(f"Starting Device Control Server on http://{host}:{port}")
        self.app.run(host=host, port=port)

# --- Example Usage ---
def run_client_demo():
    """A simple client to demonstrate interacting with the running server."""
    import requests
    from pathlib import Path

    SERVER_URL = "http://127.0.0.1:5007"
    
    # --- 1. List available serial ports ---
    print("\n--- 1. Listing available serial ports ---")
    try:
        response = requests.get(f"{SERVER_URL}/serial/ports")
        if response.status_code == 200:
            ports = response.json()
            if ports:
                print(f"Found serial ports: {ports}")
            else:
                print("No active serial ports found.")
        else:
            print(f"Error: {response.status_code} {response.text}")
    except requests.ConnectionError:
        print("Could not connect to server. Is it running?")
        return
        
    # --- 2. Capture an image from the webcam ---
    print("\n--- 2. Capturing an image from the default webcam ---")
    try:
        response = requests.get(f"{SERVER_URL}/webcam/capture", timeout=10)
        if response.status_code == 200:
            image_path = Path("webcam_capture.jpg")
            image_path.write_bytes(response.content)
            print(f"[SUCCESS] Webcam image saved to '{image_path.resolve()}'")
        else:
            print(f"[FAILURE] Could not capture image. Error: {response.json().get('error', 'Unknown')}")
    except requests.exceptions.RequestException as e:
        print(f"[FAILURE] Request to capture image failed: {e}")


if __name__ == "__main__":
    print("=========================================================")
    print("=== Device Control Server Prototype 📷🔌 ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module is missing. Please check your installation. Error: {_import_error}")
        print("Required libraries: flask, opencv-python, pyserial")
    else:
        print("!!! PREREQUISITE: This tool requires hardware (webcam, serial devices) to be connected to the host machine. !!!")
        
        server = DeviceControlServer()
        
        # Run the server in a background thread so we can run the client demo
        server_thread = threading.Thread(target=server.run, args=('127.0.0.1', 5007), daemon=True)
        server_thread.start()
        time.sleep(2) # Give the server a moment to start up
        
        run_client_demo()
        
        logger.info("Demo complete. Exiting...")

    print("\n=========================================================")
    print("=== Device Control Server Prototype Complete ===")
    print("=========================================================")
