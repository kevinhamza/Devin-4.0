import sys
import os
import time
import threading
from dotenv import load_dotenv
from pynput.mouse import Controller as MouseController
from pynput.keyboard import Controller as KeyboardController
from modules.gesture_recognition import GestureRecognition
from modules.system_control import SystemControl
from ai_integrations.chatgpt_connector import ChatGPTConnector
from ai_integrations.gemini_connector import GeminiConnector
from cloud.aws_integration import AWSIntegration
from monitoring.cpu_usage import get_cpu_usage
from monitoring.analytics_dashboard import collect_system_metrics
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Print the values for debugging
aws_access_key = os.getenv('AWS_ACCESS_KEY')
aws_secret_key = os.getenv('AWS_SECRET_KEY')

print(f"AWS Access Key: {aws_access_key}")
print(f"AWS Secret Key: {aws_secret_key}")

if not aws_access_key or not aws_secret_key:
    raise EnvironmentError("AWS_ACCESS_KEY and AWS_SECRET_KEY must be set in .env file.")

# Validate API keys
chatgpt_api_key = os.getenv("CHATGPT_API_KEY")
if not chatgpt_api_key:
    raise ValueError("API key for ChatGPT is not configured. Please set it in the .env file.")

gemini_api_key = os.getenv("GEMINI_API_KEY")  # Optional
# Uncomment and validate if Gemini requires an API key:
# if not gemini_api_key:
#     raise ValueError("API key for Gemini is not configured. Please set it in the .env file.")

# Initialize logger
logger = setup_logger("Devin")

# Mouse and keyboard controllers
mouse = MouseController()
keyboard = KeyboardController()

# Initialize AI modules
chatgpt = ChatGPTConnector(api_key=chatgpt_api_key)
gemini = GeminiConnector()  # Comment out if Gemini is not needed

# Initialize system modules
gesture_recognizer = GestureRecognition()
system_controller = SystemControl()
cpu_monitor = get_cpu_usage
analytics_dashboard = collect_system_metrics

# Cloud integrations
aws_integration = AWSIntegration()

# Define tasks
def handle_ai_conversation(command):
    """
    Process AI-based conversation requests and execute corresponding tasks.
    """
    try:
        logger.info(f"Received command: {command}")
        response = chatgpt.get_response(command)
        logger.info(f"ChatGPT response: {response}")
        print(response)  # For logging the response to the terminal or UI
    except Exception as e:
        logger.error(f"Error handling AI conversation: {e}")
        print("Sorry, I encountered an error processing your request.")

def control_mouse_with_gesture():
    """
    Enable gesture-based mouse control.
    """
    logger.info("Activating gesture-based mouse control...")
    print("Gesture-based mouse control activated. Use hand gestures to control the pointer.")
    gesture_recognizer.start_recognition(mouse)

def monitor_resources():
    """
    Monitor system resources and provide insights.
    """
    while True:
        try:
            cpu_usage = cpu_monitor()
            logger.info(f"CPU usage: {cpu_usage}%")
            if cpu_usage > 90:
                print("Warning: CPU usage is critically high!")
            time.sleep(10)
        except Exception as e:
            logger.error(f"Error monitoring resources: {e}")
            time.sleep(10)  # Ensure we don't break the loop on error

def perform_cloud_tasks():
    """
    Handle cloud-related tasks.
    """
    try:
        logger.info("Performing cloud operations...")
        aws_integration.sync_files()
    except Exception as e:
        logger.error(f"Cloud operation error: {e}")

def keyboard_typing_simulation(text):
    """
    Simulate keyboard typing for automation tasks.
    """
    logger.info(f"Typing text: {text}")
    for char in text:
        keyboard.type(char)
        time.sleep(0.1)

# Main loop
def main():
    logger.info(f"Starting Devin...")
    print("Devin is ready.")

    # Start monitoring in a separate thread
    threading.Thread(target=monitor_resources, daemon=True).start()

    # Start cloud tasks in a separate thread
    threading.Thread(target=perform_cloud_tasks, daemon=True).start()

    # Listen for commands or user input (you can replace this with any method to trigger conversation)
    while True:
        try:
            command = input("You: ")  # Replace with a real input method or command handling system
            handle_ai_conversation(command)
        except KeyboardInterrupt:
            logger.info("Shutting down Devin...")
            print("Goodbye!")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            print("An unexpected error occurred.")

if __name__ == "__main__":
    # Initialize the ChatGPT connector with the correct API key
    api_key = os.getenv("CHATGPT_API_KEY", "your_api_key_here")
    chat_gpt_connector = ChatGPTConnector(api_key)

    # Command received
    command = "hi"
    
    # Process command with execute_task
    response = chat_gpt_connector.execute_task(command)

    if response:
        print("ChatGPT Response:", response)
    else:
        print("Error: Could not get a valid response.")
