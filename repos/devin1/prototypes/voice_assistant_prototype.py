"""
voice_assistant_prototype.py
-----------------------------
This prototype module demonstrates the capabilities of the Devin voice assistant. It includes:
- Wake word detection ("Hey Devin").
- Speaker verification for personalized responses.
- Voice command recognition and execution.
- PC and OS control functionalities.
- Modular architecture for future enhancements.

Dependencies:
- Porcupine (wake word detection).
- TensorFlow/Keras (ML models for verification and recognition).
- SpeechRecognition (voice capture and processing).
- PyAutoGUI (system control).
- OS and subprocess for command execution.
"""

import os
import logging
import pyautogui
import subprocess
import threading
from modules.voice_assistant.wake_word_detection import WakeWordDetector
from modules.voice_assistant.speaker_verification import SpeakerVerifier
from modules.voice_assistant.voice_recognition import VoiceCommandRecognizer
from modules.voice_assistant.pc_integration import PCController
from modules.voice_assistant.otheros_integration import OtherOSController

# Logging configuration
logging.basicConfig(
    filename="voice_assistant_prototype.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class DevinVoiceAssistant:
    """
    The DevinVoiceAssistant class encapsulates functionalities of the voice assistant prototype.
    """

    def __init__(self):
        self.wake_word_detector = WakeWordDetector()
        self.speaker_verifier = SpeakerVerifier()
        self.command_recognizer = VoiceCommandRecognizer()
        self.pc_controller = PCController()
        self.os_controller = OtherOSController()
        self.authorized_user = "User"  # Replace with the enrolled user's name

    def start(self):
        """
        Start the voice assistant prototype.
        """
        logging.info("Starting Devin Voice Assistant...")
        try:
            print("Devin is ready. Say 'Hey Devin' to start.")
            while True:
                if self.wake_word_detector.detect_wake_word():
                    logging.info("Wake word detected.")
                    self.handle_interaction()
        except KeyboardInterrupt:
            logging.info("Devin Voice Assistant stopped.")
            print("Voice Assistant stopped.")

    def handle_interaction(self):
        """
        Handles user interaction after detecting the wake word.
        """
        print("Listening for your command...")
        try:
            # Verify the speaker's identity
            if not self.speaker_verifier.verify(self.authorized_user):
                logging.warning("Unauthorized user detected.")
                print("Access denied: Voice not recognized.")
                return

            # Recognize the command
            command = self.command_recognizer.recognize()
            logging.info(f"Command recognized: {command}")
            
            # Execute the command
            self.execute_command(command)

        except Exception as e:
            logging.error(f"Error during interaction: {e}")
            print(f"An error occurred: {e}")

    def execute_command(self, command):
        """
        Executes the recognized voice command.

        Args:
            command (str): The recognized voice command.
        """
        logging.info(f"Executing command: {command}")

        # System-level commands
        if "open browser" in command:
            self.pc_controller.open_browser()
        elif "shutdown" in command:
            self.os_controller.shutdown_system()
        elif "increase volume" in command:
            self.pc_controller.adjust_volume("up")
        elif "decrease volume" in command:
            self.pc_controller.adjust_volume("down")
        elif "take screenshot" in command:
            self.pc_controller.take_screenshot()
        elif "search for" in command:
            query = command.split("search for", 1)[1].strip()
            self.pc_controller.search_web(query)
        elif "lock system" in command:
            self.os_controller.lock_system()
        elif "run command" in command:
            custom_command = command.split("run command", 1)[1].strip()
            self.os_controller.execute_custom_command(custom_command)
        else:
            print(f"Unknown command: {command}")
            logging.warning(f"Unknown command received: {command}")

class PCController:
    """
    Handles PC-specific voice assistant tasks.
    """

    def open_browser(self):
        """
        Opens the default web browser.
        """
        logging.info("Opening web browser.")
        os.system("start chrome" if os.name == "nt" else "open -a Safari")

    def adjust_volume(self, direction):
        """
        Adjusts the system volume.

        Args:
            direction (str): "up" or "down".
        """
        logging.info(f"Adjusting volume {direction}.")
        if direction == "up":
            pyautogui.press("volumeup")
        elif direction == "down":
            pyautogui.press("volumedown")

    def take_screenshot(self):
        """
        Takes a screenshot and saves it to the desktop.
        """
        logging.info("Taking screenshot.")
        screenshot = pyautogui.screenshot()
        screenshot.save(os.path.expanduser("~/Desktop/screenshot.png"))
        print("Screenshot saved to desktop.")

    def search_web(self, query):
        """
        Searches the web for a given query.

        Args:
            query (str): Search query.
        """
        logging.info(f"Searching web for: {query}")
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        os.system(f"start {url}" if os.name == "nt" else f"open {url}")

class OtherOSController:
    """
    Handles OS-level control for Linux, MacOS, and other environments.
    """

    def shutdown_system(self):
        """
        Shuts down the system.
        """
        logging.info("Shutting down the system.")
        os.system("shutdown now" if os.name != "nt" else "shutdown /s /t 0")

    def lock_system(self):
        """
        Locks the system.
        """
        logging.info("Locking the system.")
        os.system("gnome-screensaver-command -l" if os.name != "nt" else "rundll32.exe user32.dll,LockWorkStation")

    def execute_custom_command(self, command):
        """
        Executes a custom terminal/command-line command.

        Args:
            command (str): Custom command to execute.
        """
        logging.info(f"Executing custom command: {command}")
        try:
            subprocess.run(command, shell=True)
        except Exception as e:
            logging.error(f"Failed to execute custom command: {e}")
            print(f"Error executing command: {e}")


if __name__ == "__main__":
    assistant = DevinVoiceAssistant()
    assistant.start()
