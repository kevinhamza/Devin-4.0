"""
File: plugins/voice_assistant.py
Purpose: Provide voice-based assistant capabilities, enabling voice commands for task execution.
"""

import os
import pyttsx3  # For text-to-speech
import speech_recognition as sr  # For speech recognition
import logging
from modules.task_scheduler import schedule_task  # Hypothetical module
from modules.system_control import execute_command  # Hypothetical module

logging.basicConfig(
    filename="logs/voice_assistant.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

class VoiceAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.commands = {
            "schedule": self.schedule_task,
            "execute": self.execute_system_command,
            "search": self.search_online,
            "log out": self.log_out_user,
            "exit": self.exit_program,
        }
    
    def speak(self, text):
        """Convert text to speech."""
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        """Listen to user's voice input."""
        with self.microphone as source:
            self.speak("I'm listening...")
            audio = self.recognizer.listen(source)
            try:
                return self.recognizer.recognize_google(audio).lower()
            except sr.UnknownValueError:
                self.speak("Sorry, I didn't understand that. Please repeat.")
                return None
            except sr.RequestError:
                self.speak("There was an issue connecting to the recognition service.")
                return None

    def schedule_task(self, command):
        """Schedule a task based on user input."""
        task_details = command.replace("schedule", "").strip()
        if task_details:
            success = schedule_task(task_details)
            if success:
                self.speak(f"Task '{task_details}' has been scheduled.")
            else:
                self.speak(f"Failed to schedule the task: {task_details}")
        else:
            self.speak("Please specify the task to schedule.")

    def execute_system_command(self, command):
        """Execute a system command based on user input."""
        system_command = command.replace("execute", "").strip()
        if system_command:
            success = execute_command(system_command)
            if success:
                self.speak(f"The command '{system_command}' was executed successfully.")
            else:
                self.speak(f"Failed to execute the command: {system_command}")
        else:
            self.speak("Please specify the command to execute.")

    def search_online(self, query):
        """Perform an online search."""
        search_query = query.replace("search", "").strip()
        if search_query:
            self.speak(f"Searching the web for '{search_query}'...")
            os.system(f"start https://www.google.com/search?q={search_query}")
        else:
            self.speak("Please specify what you want to search for.")

    def log_out_user(self, _):
        """Log out the user."""
        self.speak("Logging out the user.")
        os.system("shutdown -l")

    def exit_program(self, _):
        """Exit the voice assistant."""
        self.speak("Goodbye!")
        exit()

    def run(self):
        """Start the voice assistant."""
        self.speak("Voice Assistant is now active. How can I assist you?")
        while True:
            command = self.listen()
            if command:
                for key in self.commands:
                    if command.startswith(key):
                        self.commands[key](command)
                        break
                else:
                    self.speak("Sorry, I don't recognize that command.")


if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
