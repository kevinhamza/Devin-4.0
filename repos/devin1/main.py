import os
import psutil
import sys
import time
import json
import logging
import socket
from threading import Thread
from datetime import datetime
from googletrans import Translator
from transformers import pipeline
from modules.nlp_conversation import start_conversation
from modules.keyboard_mouse_control import control_input
from modules.scheduler import schedule_tasks
from modules.cloud_tools import manage_cloud_resources
from modules.voice_assistant.wake_word_detection import WakeWordDetector
from modules.voice_assistant.speaker_verification import verify_speaker
from modules.voice_assistant.voice_recognition import recognize_command
from ai_integrations.chatgpt_connector import ChatGPTConnector
from ai_integrations.copilot_connector import CopilotConnector
from utils.logger import setup_logger
from monitoring.cpu_usage import monitor_cpu  # PC-specific
from monitoring.analytics_dashboard import generate_dashboard  # PC-specific
from dotenv import load_dotenv
import pyaudio

# Load environment variables from .env file
load_dotenv()

# Retrieve the API keys from environment variables
chatgpt_api_key = os.getenv("CHATGPT_API_KEY")
copilot_api_key = os.getenv("COPILOT_API_KEY")

# Global Constants
VERSION = "1.0.0"
APP_NAME = "Devin"
WAKE_WORD = "Hey Devin"
USER_VOICE_PROFILE = "path/to/user_voice_profile"
TASK_MEMORY_FILE = "task_memory.json"
SAFE_PORTS = [80, 443, 22]
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Initialize logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("Devin")

# AI Models and Translators
translator = Translator()
nlp_pipeline = pipeline("text2text-generation", model="t5-large")  # Example NLP model

# Initialize the connectors with the API keys
chatgpt = ChatGPTConnector(api_key=chatgpt_api_key)
copilot = CopilotConnector(api_key=copilot_api_key)

# Utility Functions
def load_preferences():
    if not os.path.exists("preferences.json"):
        return {}
    with open("preferences.json", "r") as f:
        return json.load(f)

def save_preferences(key, value):
    preferences = load_preferences()
    preferences[key] = value
    with open("preferences.json", "w") as f:
        json.dump(preferences, f)

def load_task_memory():
    if not os.path.exists(TASK_MEMORY_FILE):
        return []
    with open(TASK_MEMORY_FILE, "r") as f:
        return json.load(f)

def save_task_to_memory(task_description):
    tasks = load_task_memory()
    tasks.append({"task": task_description, "timestamp": datetime.now().isoformat()})
    with open(TASK_MEMORY_FILE, "w") as f:
        json.dump(tasks, f)

# Task Execution and Queue Management
task_queue = []

def execute_task_in_background(task_description):
    def task_runner(task):
        try:
            print(f"Executing task: {task}")
            save_task_to_memory(task)
            print(f"Task '{task}' completed.")
        except Exception as e:
            print(f"Error executing task: {e}")
    task_thread = Thread(target=task_runner, args=(task_description,))
    task_thread.start()
    task_queue.append(task_thread)

def monitor_task_queue():
    global task_queue
    task_queue = [t for t in task_queue if t.is_alive()]

# Device and IoT Management
def control_remote_device(ip, port, command):
    try:
        print(f"Connecting to device at {ip}:{port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            s.sendall(command.encode())
            response = s.recv(1024).decode()
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error controlling remote device: {e}")

def control_iot_device(device_name, action):
    try:
        print(f"Performing '{action}' on IoT device: {device_name}")
        print("Action completed.")
    except Exception as e:
        print(f"Failed to control IoT device '{device_name}': {e}")

# Threat Detection
def detect_threats():
    connections = psutil.net_connections()
    for conn in connections:
        if conn.status == "LISTEN" and conn.laddr.port not in SAFE_PORTS:
            print(f"Potential threat detected on port {conn.laddr.port}!")

# System Dashboard (PC-specific)
def show_system_dashboard():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    print(f"CPU Usage: {cpu_usage}%")
    print(f"Memory Usage: {memory.percent}%")
    print(f"Available Memory: {memory.available / (1024**2):.2f} MB")

# AI Response Handling
def translate_input(user_input, target_language="en"):
    detected_lang = translator.detect(user_input).lang
    if detected_lang != target_language:
        return translator.translate(user_input, src=detected_lang, dest=target_language).text
    return user_input

def translate_output(response, target_language="en"):
    return translator.translate(response, src="en", dest=target_language).text

def process_complex_query(query):
    response = nlp_pipeline(query, max_length=300)
    return response[0]["generated_text"]

def generate_ai_response(user_input):
    translated_input = translate_input(user_input)
    response = chatgpt.get_response(translated_input)
    return translate_output(response)

# Voice and Command Handling
def handle_command(command):
    log.info(f"Handling command: {command}")
    if "chat" in command:
        start_conversation()
    elif "schedule task" in command:
        schedule_tasks()
    elif "cloud" in command:
        manage_cloud_resources()
    elif "system dashboard" in command:
        show_system_dashboard()
    elif "control remote" in command:
        ip = "192.168.1.100"
        port = 12345
        remote_command = "shutdown"
        control_remote_device(ip, port, remote_command)
    elif "smart light" in command:
        control_iot_device("Smart Light", "turn on")
    else:
        response = chatgpt.execute_command(command)
        print(f"Result: {response if response else 'Failed to execute command.'}")

def get_audio_frame():
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=16000,
                     input=True,
                     frames_per_buffer=512)
    audio_frame = stream.read(512)
    return audio_frame

# def handle_voice_interaction():
#     print("Listening for wake word...")
#     try:
#         detector = WakeWordDetector(
#             access_key="VktnNTGZEo/yIvoys2/9xLkNx6lDGXgLShF1MNSqVvN/UE+HW7zsdw==",
#             keyword_model_path="modules/voice_assistant/Hey-Devin_en_windows_v3_0_0.ppn",
#             sensitivity=0.5
#         )
#         while True:
#             audio_frame = get_audio_frame()
#             if detector.detect_wake_word(audio_frame):
#                 print("Wake word detected!")
#     except Exception as e:
#         log.error(f"Error in wake word detection: {e}")

def handle_voice_interaction():
    print("Listening for wake word...")
    try:
        # Initialize the WakeWordDetector
        # detector = WakeWordDetector(
        #     access_key="VktnNTGZEo/yIvoys2/9xLkNx6lDGXgLShF1MNSqVvN/UE+HW7zsdw==",
        #     keyword_model_path="modules/voice_assistant/Hey-Devin_en_windows_v3_0_0.ppn",
        #     sensitivity=0.5
        # )
        detector = WakeWordDetector()
        # Initialize pyaudio for capturing audio frames
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=512
        )
        print("Porcupine initialized. Ready to detect wake word.")

        while True:
            audio_frame = stream.read(512, exception_on_overflow=False)  # Capture audio frame
            # Call detect_wake_word with the audio frame
            if detector.detect_wake_word(audio_frame):
                print("Wake word detected!")
                # Additional logic for handling voice commands can be added here
    except Exception as e:
        log.error(f"Error in wake word detection: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

# Main Function
def main():
    log.info(f"Starting {APP_NAME} v{VERSION}")
    print(f"Welcome to {APP_NAME} - Your AI Assistant!")
    print(f"Say '{WAKE_WORD}' to get started.")
    try:
        handle_voice_interaction()
    except KeyboardInterrupt:
        log.info("Application terminated by user.")
    except Exception as e:
        log.error(f"Unexpected error: {e}", exc_info=True)

# if __name__ == "__main__":
#     WAKE_WORD = load_preferences().get("wake_word", WAKE_WORD)
#     main()

if __name__ == "__main__":
    handle_voice_interaction()
