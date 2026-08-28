import speech_recognition as sr
import pyttsx3
import os
import subprocess
import threading
from modules.gesture_recognition import GestureRecognition
from ai_integrations.chatgpt_connector import ChatGPTConnector
from modules.system_control import SystemControl
from modules.nlp_processing import NLPProcessing


class VoiceAssistant:
    def __init__(self, wake_word="Hey Devin", user_voice_id=None, chatgpt_api_key=None):
        # Initialize TTS engine
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 160)  # Speed of speech
        self.tts_engine.setProperty('volume', 1.0)  # Volume level

        # Initialize Speech Recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Wake word for activation
        self.wake_word = wake_word

        # User voice ID (if needed)
        self.user_voice_id = user_voice_id

        # NLP Processor
        self.nlp_processor = NLPProcessing()

        # Gesture Recognition for multitasking
        self.gesture_recognition = GestureRecognition()

        # AI Integration
        if chatgpt_api_key:
            self.ai_connector = ChatGPTConnector(api_key=chatgpt_api_key)
        else:
            raise ValueError("ChatGPT API key is required to initialize VoiceAssistant.")

        # System Control
        self.system_control = SystemControl()

    def speak(self, text):
        """Convert text to speech."""
        print(f"Devin says: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def listen(self):
        """Capture audio from the microphone."""
        with self.microphone as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5)
                print("Processing...")
                return self.recognizer.recognize_google(audio)
            except sr.WaitTimeoutError:
                print("Listening timed out.")
                return None
            except sr.UnknownValueError:
                print("Could not understand the audio.")
                return None
            except sr.RequestError as e:
                print(f"Speech Recognition service error: {e}")
                return None

    def process_command(self, command):
        """Process and execute the user's command."""
        if self.wake_word.lower() in command.lower():
            command = command.lower().replace(self.wake_word.lower(), "").strip()
            self.speak("I'm listening. How can I assist you?")

            # Command categorization
            intent = self.nlp_processor.identify_intent(command)

            if intent == "system_control":
                self.system_control.execute_command(command)
            elif intent == "search_query":
                response = self.ai_connector.generate_response(command)
                self.speak(response)
            elif intent == "open_application":
                self.system_control.open_application(command)
            elif intent == "close_application":
                self.system_control.close_application(command)
            elif intent == "gesture_mode":
                self.speak("Activating gesture mode.")
                self.gesture_recognition.activate()
            elif intent == "keyboard_mouse_control":
                self.speak("Entering keyboard and mouse control mode.")
                self.system_control.control_with_keyboard_mouse()
            else:
                self.speak("I couldn't understand your request. Please try again.")

    def wake_word_detected(self):
        """Continuously listen for the wake word."""
        print("Waiting for the wake word...")
        while True:
            command = self.listen()
            if command and self.wake_word.lower() in command.lower():
                self.process_command(command)

    def start(self):
        """Start the voice assistant."""
        wake_word_thread = threading.Thread(target=self.wake_word_detected)
        wake_word_thread.daemon = True
        wake_word_thread.start()
        self.speak(f"{self.wake_word} activated. Ready to assist.")

        try:
            while True:
                pass
        except KeyboardInterrupt:
            print("Voice Assistant stopped.")


if __name__ == "__main__":
    # Replace with your actual ChatGPT API key
    chatgpt_api_key = "your_chatgpt_api_key"
    assistant = VoiceAssistant(chatgpt_api_key=chatgpt_api_key)
    assistant.start()
