"""
Voice Assistant Module
======================
Handles voice commands and interactions for controlling robotic functionalities.
"""

import speech_recognition as sr
import pyttsx3
import logging
from modules.robotics.motor_control import MotorController
from modules.robotics.sensor_integration import SensorInterface

# Voice Assistant Configuration
class VoiceAssistantConfig:
    def __init__(self, language="en-US", rate=150, volume=1.0):
        """
        Initializes voice assistant configuration.

        Args:
            language (str): Language code for speech recognition.
            rate (int): Speaking rate for text-to-speech.
            volume (float): Volume level for text-to-speech (0.0 to 1.0).
        """
        self.language = language
        self.rate = rate
        self.volume = volume

# Voice Assistant
class VoiceAssistant:
    def __init__(self, config: VoiceAssistantConfig):
        """
        Initializes the voice assistant with the given configuration.

        Args:
            config (VoiceAssistantConfig): Configuration for voice assistant.
        """
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", config.rate)
        self.engine.setProperty("volume", config.volume)
        self.language = config.language
        self.motor_controller = MotorController()
        self.sensor_interface = SensorInterface()

    def speak(self, message: str):
        """
        Converts text to speech.

        Args:
            message (str): Message to be spoken.
        """
        logging.info(f"Speaking: {message}")
        self.engine.say(message)
        self.engine.runAndWait()

    def listen(self):
        """
        Captures and processes user voice input.

        Returns:
            str: Recognized speech as text.
        """
        with sr.Microphone() as source:
            try:
                logging.info("Listening for voice commands...")
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source)
                command = self.recognizer.recognize_google(audio, language=self.language)
                logging.info(f"Recognized command: {command}")
                return command.lower()
            except sr.UnknownValueError:
                logging.error("Speech not understood.")
                self.speak("I didn't understand that. Could you please repeat?")
                return ""
            except sr.RequestError as e:
                logging.error(f"Speech recognition service error: {e}")
                self.speak("There seems to be an issue with the speech recognition service.")
                return ""

    def process_command(self, command: str):
        """
        Processes the voice command and executes corresponding actions.

        Args:
            command (str): Voice command as text.
        """
        if "move forward" in command:
            self.speak("Moving forward.")
            self.motor_controller.move_forward()

        elif "move backward" in command:
            self.speak("Moving backward.")
            self.motor_controller.move_backward()

        elif "turn left" in command:
            self.speak("Turning left.")
            self.motor_controller.turn_left()

        elif "turn right" in command:
            self.speak("Turning right.")
            self.motor_controller.turn_right()

        elif "stop" in command:
            self.speak("Stopping all movement.")
            self.motor_controller.stop()

        elif "status" in command:
            self.speak("Fetching status from sensors.")
            status = self.sensor_interface.get_status()
            self.speak(f"Current status: {status}")

        else:
            self.speak("I didn't understand that command.")

# Example Usage
if __name__ == "__main__":
    config = VoiceAssistantConfig(language="en-US", rate=150, volume=1.0)
    assistant = VoiceAssistant(config)

    while True:
        command = assistant.listen()
        if command:
            if "exit" in command or "shutdown" in command:
                assistant.speak("Shutting down. Goodbye!")
                break
            assistant.process_command(command)
