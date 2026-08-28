# Devin/modules/robotics/voice_assistant.py
# Purpose: A high-level voice assistant that orchestrates dedicated TTS and STT
#          modules to manage a conversational user interface.
# (This file has been refactored to use dedicated speech modules)

import logging
import time
from typing import Optional, Callable

# --- Important: This module now depends on the two we just created ---
# A real implementation would use these imports.
#
# from .text_to_speech import TextToSpeech
# from .speech_to_text import SpeechToText

# For this script to be runnable on its own, we'll use conceptual placeholders.
# --- Conceptual Placeholders for Imported Modules ---
class TextToSpeech:
    def __init__(self, *args, **kwargs): logger.info("Conceptual TTS engine initialized.")
    def speak(self, text: str, wait: bool = True):
        print(f"DEVIN (Speaking): {text}")
        if wait: time.sleep(1 + len(text) / 20) # Simulate speech time
    def list_voices(self): return [{"id": "default", "name": "Default"}]

class SpeechToText:
    def __init__(self, *args, **kwargs): logger.info("Conceptual STT engine initialized.")
    def calibrate_for_ambient_noise(self, *args, **kwargs): logger.info("Calibrating for ambient noise...")
    def listen_for_single_phrase(self, *args, **kwargs) -> Optional[str]:
        response = input("You: ")
        return response.lower() if response else None
    def start_background_listening(self, callback: Callable[[str], None]):
        self._callback = callback
        logger.info("Conceptual background listener started. In demo, type 'devin <cmd>' to trigger callback.")
    def stop_background_listening(self): logger.info("Conceptual background listener stopped.")
# --- End of Conceptual Placeholders ---

# Configure basic logging
logger = logging.getLogger("VoiceAssistant")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class VoiceAssistant:
    """
    Orchestrates the TextToSpeech and SpeechToText modules to provide a
    seamless conversational experience.
    """
    def __init__(self, wake_word: str = "devin"):
        """
        Initializes the assistant by creating instances of the TTS and STT engines.
        """
        logger.info("Initializing Voice Assistant...")
        self.tts = TextToSpeech(rate=190)
        self.stt = SpeechToText()
        
        self.wake_word = wake_word.lower()
        self.is_awake = False
        self.last_interaction_time = 0
        self.timeout_seconds = 30 # Time before assistant goes back to sleep

        logger.info("Calibrating microphone...")
        self.stt.calibrate_for_ambient_noise()
        logger.info(f"Voice Assistant ready. Listening for wake word: '{self.wake_word}'")

    def speak(self, text: str, wait: bool = True):
        """A simple wrapper to make the assistant speak."""
        self.tts.speak(text, wait=wait)

    def ask_question(self, question: str) -> Optional[str]:
        """
        Asks the user a question and waits for a spoken response.
        This is a blocking conversational turn.

        Args:
            question (str): The question to ask the user.

        Returns:
            Optional[str]: The user's transcribed response.
        """
        self.speak(question, wait=True)
        return self.stt.listen_for_single_phrase()

    def _handle_background_speech(self, text: str):
        """
        The callback function passed to the STT background listener.
        It processes incoming text for the wake word or subsequent commands.
        """
        current_time = time.time()
        
        # Check if the assistant is "asleep" and listening for the wake word
        if not self.is_awake:
            if text.strip().startswith(self.wake_word):
                command = text.strip()[len(self.wake_word):].strip()
                logger.info(f"Wake word detected!")
                self.is_awake = True
                self.last_interaction_time = current_time
                self.speak("Yes?", wait=False) # Acknowledge being woken up
                if command:
                    # If a command was included with the wake word, process it.
                    self._process_command(command)
        else:
            # The assistant is already "awake", so process any speech as a command
            self.last_interaction_time = current_time
            self._process_command(text)
            
    def _process_command(self, command: str):
        """(Placeholder) Processes a recognized command."""
        logger.info(f"Processing command: '{command}'")
        # In a real system, this would trigger the Task Orchestrator.
        if "time is it" in command:
            current_time_str = time.strftime("%I:%M %p", time.localtime())
            self.speak(f"The current time is {current_time_str}")
        elif "go to sleep" in command:
            self.speak("Going back to sleep.")
            self.is_awake = False
        else:
            self.speak(f"I understood the command: {command}")

    def start(self):
        """Starts the main operational loop of the voice assistant."""
        self.stt.start_background_listening(self._handle_background_speech)
        
        # This loop checks if the assistant should go back to sleep due to inactivity
        while True:
            try:
                if self.is_awake and (time.time() - self.last_interaction_time > self.timeout_seconds):
                    logger.info("Assistant timing out due to inactivity.")
                    self.speak("Going to sleep now.", wait=False)
                    self.is_awake = False
                
                # In the demo, we check for typed commands to simulate background speech
                # In a real app, this loop could do other work.
                if isinstance(self.stt, SpeechToText): # Conceptual check
                    time.sleep(1) # Normal operation
                else:
                    # This part is for the interactive demo only
                    typed_input = input()
                    if typed_input:
                        self._handle_background_speech(typed_input)
                        
            except KeyboardInterrupt:
                logger.info("Shutting down Voice Assistant.")
                self.stt.stop_background_listening()
                break

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Refactored Voice Assistant Prototype 🗣️🧠 ===")
    print("=========================================================")
    
    assistant = VoiceAssistant(wake_word="devin")

    # --- 1. Demonstrate a direct, blocking question ---
    print("\n--- Demo 1: Asking a direct question ---")
    user_name = assistant.ask_question("Hello. To begin, please state your name.")
    if user_name:
        assistant.speak(f"It's a pleasure to meet you, {user_name}.")
    else:
        assistant.speak("I didn't catch your name. We'll proceed anyway.")
    
    # --- 2. Demonstrate the background listener and conversation loop ---
    print("\n\n--- Demo 2: Starting conversational loop ---")
    print("The assistant is now listening in the background.")
    print("Say 'devin, what time is it?' to get the time.")
    print("Say 'devin, go to sleep' to make the assistant stop listening for commands.")
    print("If you wake it, it will 'time out' and go back to sleep after 30 seconds of inactivity.")
    print("\nNOTE FOR DEMO: Since this is a text-based simulation, please TYPE your commands.")
    print("Type 'devin what time is it' and press Enter.")
    print("Type 'quit' or press Ctrl+C to exit.")
    
    # In a real app with a microphone, assistant.start() would just run.
    # We simulate it here for the text-based demo.
    try:
        assistant.start()
    except Exception as e:
        logger.error(f"Demo stopped due to an error: {e}")

    print("\n=========================================================")
    print("=== Voice Assistant Prototype Complete ===")
    print("=========================================================")
