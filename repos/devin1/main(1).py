"""
DO NOT REARRANGE THE ORDER OF FUNCTION CALLS AND VARIABLE DECLARATIONS
AS IT MAY CAUSE IMPORT ERRORS AND OTHER ISSUES
"""
from gevent import monkey
monkey.patch_all()

from src.init import init_devin
init_devin()

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from src.socket_instance import socketio, emit_agent
import os
import logging
from threading import Thread
import tiktoken
import speech_recognition as sr
import pyttsx3

from src.apis.project import project_bp
from src.config import Config
from src.logger import Logger, route_logger
from src.project import ProjectManager
from src.state import AgentState
from src.agents import Agent
from src.llm import LLM
from src.monitoring import SystemMonitor
from src.security import ThreatDetection
from src.analytics import AnalyticsEngine
from src.mobile_integration import MobileManager
from src.cloud_services import CloudManager
from src.utilities import UtilityTools
from src.pc_controller import PCController

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://localhost:3000", "http://localhost:3000"]}})

app.register_blueprint(project_bp)
socketio.init_app(app)

# Logging configuration
log = logging.getLogger("werkzeug")
log.disabled = True

# Initialize modules
TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

manager = ProjectManager()
agent_state = AgentState()
config = Config()
logger = Logger()
system_monitor = SystemMonitor()
analytics_engine = AnalyticsEngine()
mobile_manager = MobileManager()
cloud_manager = CloudManager()
utility_tools = UtilityTools()
threat_detection = ThreatDetection()
pc_controller = PCController()

# Speech and voice setup
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen_to_voice():
    try:
        with sr.Microphone() as source:
            speak("Listening for your command.")
            audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio)
            return command.lower()
    except Exception as e:
        logger.error(f"Voice recognition error: {e}")
        return None

# Socket initialization
@socketio.on('socket_connect')
def socket_connect(data):
    print("Socket connected:", data)
    emit_agent("socket_response", {"data": "Server Connected"})

@app.route("/api/system-monitor", methods=["GET"])
@route_logger(logger)
def get_system_stats():
    stats = system_monitor.collect_stats()
    return jsonify(stats)

@app.route("/api/threat-detection", methods=["POST"])
@route_logger(logger)
def detect_threats():
    data = request.json
    threat_report = threat_detection.analyze(data)
    return jsonify(threat_report)

@app.route("/api/cloud-management", methods=["POST"])
@route_logger(logger)
def manage_cloud():
    data = request.json
    response = cloud_manager.handle_request(data)
    return jsonify(response)

@app.route("/api/mobile-integration", methods=["GET"])
@route_logger(logger)
def mobile_status():
    status = mobile_manager.get_status()
    return jsonify({"mobile_status": status})

@app.route("/api/analytics-report", methods=["GET"])
@route_logger(logger)
def analytics_report():
    report = analytics_engine.generate_report()
    return jsonify({"analytics_report": report})

@app.route("/api/utility-tools", methods=["POST"])
@route_logger(logger)
def run_utility():
    data = request.json
    result = utility_tools.run_tool(data.get("tool_name"), data.get("parameters"))
    return jsonify(result)

@app.route("/api/control-pc", methods=["POST"])
@route_logger(logger)
def control_pc():
    data = request.json
    command = data.get("command")
    response = pc_controller.execute(command)
    return jsonify(response)

# Main socket handler for user messages
@socketio.on('user-message')
def handle_user_message(data):
    logger.info(f"User message: {data}")
    message = data.get('message')
    base_model = data.get('base_model')
    project_name = data.get('project_name')
    search_engine = data.get('search_engine').lower()

    agent = Agent(base_model=base_model, search_engine=search_engine)

    state = agent_state.get_latest_state(project_name)
    if not state:
        thread = Thread(target=lambda: agent.execute(message, project_name))
        thread.start()
    else:
        if agent_state.is_agent_completed(project_name):
            thread = Thread(target=lambda: agent.subsequent_execute(message, project_name))
            thread.start()
        else:
            emit_agent("info", {"type": "warning", "message": "Previous agent task is incomplete."})

@app.route("/api/voice-command", methods=["GET"])
@route_logger(logger)
def voice_command():
    command = listen_to_voice()
    if command:
        response = pc_controller.execute(command)
        speak(response.get("message", "Command executed"))
        return jsonify(response)
    else:
        return jsonify({"error": "Could not understand the voice command"})

# Additional routes for analytics, token usage, etc.
@app.route("/api/logs", methods=["GET"])
def logs():
    log_file = logger.read_log_file()
    return jsonify({"logs": log_file})

@app.route("/api/settings", methods=["POST", "GET"])
@route_logger(logger)
def settings():
    if request.method == "POST":
        data = request.json
        config.update_config(data)
        return jsonify({"message": "Settings updated"})
    else:
        return jsonify(config.get_config())

@app.route("/api/status", methods=["GET"])
@route_logger(logger)
def status():
    return jsonify({"status": "Devin is running!"})

if __name__ == "__main__":
    logger.info("Devin is up and running!")
    speak("Devin is ready for your commands.")
    socketio.run(app, debug=False, port=1337, host="0.0.0.0")
