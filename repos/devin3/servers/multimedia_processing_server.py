# Devin/servers/multimedia_processing_server.py
# Purpose: A dedicated microservice for handling resource-intensive
#          multimedia processing tasks (image, audio, video).

import logging
import threading
import uuid
from pathlib import Path
import tempfile
from typing import Dict, Any

try:
    from flask import Flask, request, jsonify
    from modules.multimedia_tools.image_processing import ImageProcessor
    from modules.multimedia_tools.audio_processing import AudioProcessor
    from modules.multimedia_tools.video_processing import VideoProcessor
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("MultimediaServer")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class MultimediaProcessingServer:
    """
    Wraps a Flask application to provide a dedicated multimedia processing API.
    """
    def __init__(self):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")

        # --- Initialize Core Components ---
        self.image_processor = ImageProcessor()
        self.audio_processor = AudioProcessor()
        self.video_processor = VideoProcessor()
        
        # --- State for async video jobs ---
        self.video_jobs: Dict[str, Any] = {}
        
        # --- Initialize Flask App ---
        self.app = Flask(__name__)
        self._register_routes()

    def _register_routes(self):
        """Defines the API endpoints for the server."""

        @self.app.route("/image/extract_text", methods=["POST"])
        def image_extract_text():
            if 'file' not in request.files:
                return jsonify({"error": "No file part in request"}), 400
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No selected file"}), 400
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
                file.save(tmp.name)
                tmp_path = Path(tmp.name)

            logger.info(f"Processing image OCR for {tmp_path.name}")
            text = self.image_processor.extract_text_from_image(tmp_path)
            tmp_path.unlink() # Clean up temp file
            
            return jsonify({"extracted_text": text})

        @self.app.route("/video/summarize", methods=["POST"])
        def video_summarize():
            data = request.get_json()
            if not data or "url" not in data:
                return jsonify({"error": "Invalid request. 'url' field is required."}), 400
            
            job_id = str(uuid.uuid4())
            self.video_jobs[job_id] = {"status": "QUEUED", "result": None}
            
            # Run the long process in a background thread
            thread = threading.Thread(target=self._run_video_summary, args=(job_id, data['url']))
            thread.daemon = True
            thread.start()
            
            return jsonify({"message": "Video summarization started.", "job_id": job_id}), 202

        @self.app.route("/video/status/<job_id>", methods=["GET"])
        def get_video_status(job_id: str):
            job = self.video_jobs.get(job_id)
            if not job:
                return jsonify({"error": "Job not found."}), 404
            return jsonify(job)

    def _run_video_summary(self, job_id: str, url: str):
        """Wrapper function to run video summarization and update job status."""
        self.video_jobs[job_id]["status"] = "RUNNING"
        try:
            summary = self.video_processor.summarize_video_from_url(url)
            self.video_jobs[job_id]["status"] = "COMPLETED"
            self.video_jobs[job_id]["result"] = summary
        except Exception as e:
            logger.error(f"Video summarization job {job_id} failed: {e}")
            self.video_jobs[job_id]["status"] = "FAILED"
            self.video_jobs[job_id]["result"] = str(e)

    def run(self, host: str = '127.0.0.1', port: int = 5001):
        """Starts the Flask web server."""
        logger.warning(f"Starting Multimedia Processing Server on http://{host}:{port}")
        self.app.run(host=host, port=port)

# --- Example Usage ---
def run_client_demo():
    """A simple client to demonstrate interacting with the running server."""
    import requests
    import time
    
    SERVER_URL = "http://127.0.0.1:5001"
    
    # --- 1. Demonstrate Asynchronous Video Summarization ---
    print("\n--- 1. Submitting a video for summarization (asynchronous) ---")
    # This is a short, public domain video
    video_url = "https://www.youtube.com/watch?v=zPre8N4s-tI"
    response = requests.post(f"{SERVER_URL}/video/summarize", json={"url": video_url})
    
    if response.status_code == 202:
        data = response.json()
        job_id = data['job_id']
        print(f"Server accepted the job. Job ID: {job_id[:8]}...")
        
        # Poll for status
        print("\n--- 2. Polling for video summarization status ---")
        for i in range(20): # Poll for up to 200 seconds
            status_response = requests.get(f"{SERVER_URL}/video/status/{job_id}")
            status_data = status_response.json()
            print(f"  Current job status: {status_data['status']}")
            
            if status_data['status'] in ["COMPLETED", "FAILED"]:
                print("\n--- 3. Job finished ---")
                print("Final Result:")
                print(json.dumps(status_data, indent=2))
                break
            time.sleep(10)
    else:
        print(f"Error submitting job: {response.status_code} {response.text}")


if __name__ == "__main__":
    print("=========================================================")
    print("=== Multimedia Processing Server Prototype 🎞️🎵🖼️ ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module is missing. Please ensure all project files are present. Error: {_import_error}")
    elif not os.getenv("OPENAI_API_KEY"):
         print("\nERROR: OPENAI_API_KEY environment variable is required for many multimedia tools.")
    else:
        server = MultimediaProcessingServer()
        
        # Run the server in a background thread so we can run the client demo
        server_thread = threading.Thread(target=server.run, args=('127.0.0.1', 5001), daemon=True)
        server_thread.start()
        time.sleep(2) # Give the server a moment to start up
        
        run_client_demo()
        
        # For this demo, we will just exit, and the daemon thread will be terminated.
        logger.info("Demo complete. Exiting...")

    print("\n=========================================================")
    print("=== Multimedia Processing Server Prototype Complete ===")
    print("=========================================================")
