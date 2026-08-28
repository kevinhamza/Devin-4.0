# # Devin/modules/robotics/voice_assistant.py
# # Purpose: Provides a voice-based HMI for Devin, handling both
# #          Speech-to-Text (STT) and Text-to-Speech (TTS).
# # Voice-based HMI for robotics and general control 🗣️🤖

# import logging
# import queue
# import threading
# import time
# from typing import Optional, Callable, List

# # --- Dependency Installation Notes ---
# # This module requires several libraries for real functionality:
# #
# # 1. SpeechRecognition: A wrapper for many STT engines.
# #    pip install SpeechRecognition
# #
# # 2. PyAudio: Required by SpeechRecognition to access the microphone.
# #    On Linux: sudo apt-get install python3-pyaudio portaudio19-dev
# #    On macOS: brew install portaudio; pip install pyaudio
# #    On Windows: pip install pyaudio
# #
# # 3. pyttsx3: An offline, cross-platform Text-to-Speech library.
# #    pip install pyttsx3
# #    On Linux, it may require `espeak` or `festival`: sudo apt-get install espeak
# #
# # 4. (Optional) For advanced STT, you might need API libraries:
# #    pip install openai # For Whisper API
# #    pip install google-cloud-speech # For Google STT

# try:
#     import speech_recognition as sr
#     import pyttsx3
#     SPEECH_LIBS_AVAILABLE = True
# except ImportError:
#     SPEECH_LIBS_AVAILABLE = False
#     sr = None
#     pyttsx3 = None
#     logger.error("Required libraries not found! Please run: 'pip install SpeechRecognition pyttsx3 PyAudio'. This module will be non-functional.")

# # Configure basic logging
# logger = logging.getLogger("VoiceAssistant")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class VoiceAssistant:
#     """
#     Handles voice-based interaction, including listening for commands (STT)
#     and providing spoken feedback (TTS).
#     """

#     def __init__(self, tts_rate: int = 175, tts_volume: float = 1.0, wake_word: Optional[str] = "devin"):
#         """
#         Initializes the Voice Assistant's STT and TTS engines.

#         Args:
#             tts_rate (int): The speaking rate (words per minute).
#             tts_volume (float): The volume of the speech (0.0 to 1.0).
#             wake_word (Optional[str]): A wake word to activate listening in background mode.
#                                        If None, background mode will process all speech.
#         """
#         if not SPEECH_LIBS_AVAILABLE:
#             self.recognizer = None
#             self.tts_engine = None
#             logger.error("Voice Assistant could not be initialized due to missing libraries.")
#             return

#         self.wake_word = wake_word.lower() if wake_word else None
        
#         # --- Initialize TTS Engine (pyttsx3) ---
#         logger.info("Initializing Text-to-Speech engine (pyttsx3)...")
#         try:
#             self.tts_engine = pyttsx3.init()
#             self.tts_engine.setProperty('rate', tts_rate)
#             self.tts_engine.setProperty('volume', tts_volume)
#             # You can also select different voices if available on your system
#             # voices = self.tts_engine.getProperty('voices')
#             # self.tts_engine.setProperty('voice', voices[1].id) # Example: selecting a different voice
#             logger.info(f"TTS engine ready. Rate: {tts_rate}, Volume: {tts_volume}")
#         except Exception as e:
#             logger.error(f"Failed to initialize TTS engine: {e}")
#             self.tts_engine = None

#         # --- Initialize STT Engine (SpeechRecognition) ---
#         logger.info("Initializing Speech-to-Text engine (SpeechRecognition)...")
#         self.recognizer = sr.Recognizer()
#         self.recognizer.pause_threshold = 0.8 # Seconds of non-speaking audio before phrase is considered complete
#         self.recognizer.energy_threshold = 400 # Default is 300, raise if background is noisy
#         self.recognizer.dynamic_energy_threshold = True

#         # --- For background listening ---
#         self._stop_background_listening: Optional[Callable[[], None]] = None
#         self.command_queue = queue.Queue() # Thread-safe queue for commands from background listener

#     def speak(self, text: str, wait_for_completion: bool = True):
#         """
#         Converts a string of text to spoken audio.

#         Args:
#             text (str): The text to be spoken.
#             wait_for_completion (bool): If True, this method will block until speech is finished.
#         """
#         if not self.tts_engine:
#             logger.error("TTS engine not available. Cannot speak.")
#             print(f"DEVIN (TTS Fallback): {text}")
#             return
        
#         logger.info(f"Speaking: \"{text[:60]}{'...' if len(text)>60 else ''}\"")
#         try:
#             self.tts_engine.say(text)
#             if wait_for_completion:
#                 self.tts_engine.runAndWait()
#         except Exception as e:
#             logger.error(f"An error occurred during TTS processing: {e}")

#     def listen_for_command(self, timeout: Optional[int] = 5, phrase_time_limit: int = 10) -> Optional[str]:
#         """
#         Listens for a single command from the microphone and returns the transcribed text.
#         This is a blocking operation.

#         Args:
#             timeout (Optional[int]): Maximum number of seconds to wait for a phrase to start.
#             phrase_time_limit (int): Maximum number of seconds a phrase can be.

#         Returns:
#             Optional[str]: The transcribed text, or None if an error/timeout occurred.
#         """
#         if not self.recognizer:
#             logger.error("STT recognizer not available. Cannot listen.")
#             return None
            
#         with sr.Microphone() as source:
#             logger.info("Adjusting for ambient noise... please wait.")
#             # self.recognizer.adjust_for_ambient_noise(source, duration=1) # Can help in noisy environments
#             logger.info("Listening for command...")
#             try:
#                 # listen for the first phrase and extract it into audio data
#                 audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
#                 logger.info("Recognizing speech...")
                
#                 # --- Recognize speech using a backend ---
#                 # Using Google's web speech API here as a default (requires internet)
#                 # For offline, use recognize_sphinx() (requires PocketSphinx)
#                 # For high quality, use recognize_whisper(audio_data) (requires openai-whisper)
#                 text = self.recognizer.recognize_google(audio)
#                 logger.info(f"User said: \"{text}\"")
#                 return text
#             except sr.WaitTimeoutError:
#                 logger.warning("Listening timed out while waiting for phrase to start.")
#                 return None
#             except sr.UnknownValueError:
#                 logger.warning("Speech Recognition could not understand audio.")
#                 return None
#             except sr.RequestError as e:
#                 logger.error(f"Could not request results from STT service; {e}")
#                 return None
#             except Exception as e:
#                 logger.error(f"An error occurred during listening: {e}")
#                 return None

#     def _background_listener_callback(self, recognizer: Any, audio_data: Any):
#         """
#         Callback function for the background listener.
#         This is called in a separate thread whenever a phrase is detected.
#         """
#         logger.debug("Background listener captured audio, attempting recognition.")
#         try:
#             text = recognizer.recognize_google(audio_data)
#             logger.info(f"Background listener recognized: \"{text}\"")
            
#             if self.wake_word:
#                 if text.lower().strip().startswith(self.wake_word):
#                     # Wake word detected, put the rest of the command on the queue
#                     command = text.lower().strip()[len(self.wake_word):].strip()
#                     if command:
#                         logger.info(f"Wake word detected! Queuing command: '{command}'")
#                         self.command_queue.put(command)
#             else:
#                 # No wake word, process all speech as commands
#                 self.command_queue.put(text.strip())

#         except sr.UnknownValueError:
#             logger.debug("Background listener could not understand audio.")
#         except sr.RequestError as e:
#             logger.error(f"Background listener could not request results; {e}")

#     def start_background_listening(self) -> bool:
#         """
#         Starts listening for commands in a non-blocking background thread.
#         Listened commands are placed into a queue for retrieval.
#         """
#         if not self.recognizer:
#             logger.error("STT recognizer not available. Cannot start background listening.")
#             return False
            
#         if self._stop_background_listening is not None:
#             logger.warning("Background listening is already active.")
#             return True
            
#         # Create a new Microphone instance specifically for the background thread
#         # This can sometimes be more stable than sharing one across threads
#         mic = sr.Microphone()
        
#         logger.info(f"Starting background listening... (Wake Word: {'Enabled' if self.wake_word else 'Disabled'})")
#         # listen_in_background is non-blocking and returns a function to stop the listener
#         self._stop_background_listening = self.recognizer.listen_in_background(mic, self._background_listener_callback)
#         logger.info("Background listener is now active.")
#         return True

#     def stop_background_listening(self) -> None:
#         """Stops the background listening thread."""
#         if self._stop_background_listening:
#             logger.info("Stopping background listening...")
#             self._stop_background_listening(wait_for_stop=False)
#             self._stop_background_listening = None
#             logger.info("Background listener stopped.")
#         else:
#             logger.info("Background listening is not currently active.")

#     def get_queued_command(self, block: bool = False, timeout: Optional[float] = None) -> Optional[str]:
#         """
#         Retrieves a command from the queue populated by the background listener.

#         Args:
#             block (bool): If True, wait until a command is available.
#             timeout (Optional[float]): Max seconds to wait if blocking is True.

#         Returns:
#             Optional[str]: The recognized command string, or None if queue is empty (and not blocking).
#         """
#         try:
#             return self.command_queue.get(block=block, timeout=timeout)
#         except queue.Empty:
#             return None

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Voice Assistant Module Prototype 🗣️🤖 ===")
#     print("=========================================================")

#     if not SPEECH_LIBS_AVAILABLE:
#         print("\nRequired speech libraries not found. Please install them to run the demo.")
#         print("Run: pip install SpeechRecognition pyttsx3 PyAudio")
#         print("On Linux, you may also need: sudo apt-get install python3-pyaudio portaudio19-dev espeak")
#     else:
#         assistant = VoiceAssistant(wake_word="devin")

#         # --- 1. Text-to-Speech Demo ---
#         print("\n--- 1. Text-to-Speech (TTS) Demo ---")
#         assistant.speak("Hello, I am Devin's voice assistant prototype. I am now ready for commands.", wait_for_completion=True)
        
#         # --- 2. Blocking Listener Demo ---
#         print("\n--- 2. Blocking Listener Demo ---")
#         print("I will now listen for a single command for up to 10 seconds.")
#         print("Please say something clearly...")
#         command = assistant.listen_for_command(phrase_time_limit=10)
#         if command:
#             assistant.speak(f"You said: {command}", wait_for_completion=True)
#         else:
#             assistant.speak("I didn't catch that. Let's move on to the background listener.", wait_for_completion=True)
            
#         time.sleep(1)

#         # --- 3. Non-Blocking Background Listener Demo ---
#         print("\n--- 3. Non-Blocking Background Listener Demo ---")
#         print(f"I will now listen in the background. Say '{assistant.wake_word}' followed by a command.")
#         print("For example: 'Devin, what time is it?' or 'Devin, stop listening'.")
        
#         assistant.start_background_listening()
        
#         # Main loop to check for queued commands
#         try:
#             print("\nListening... (Press Ctrl+C to exit)")
#             while True:
#                 # Check for commands in the queue without blocking
#                 queued_command = assistant.get_queued_command(block=False)
                
#                 if queued_command:
#                     print(f"  [Main Loop] Received queued command: '{queued_command}'")
#                     if "stop listening" in queued_command.lower():
#                         assistant.speak("Acknowledged. Stopping background listener now.", wait_for_completion=True)
#                         break # Exit the loop
#                     else:
#                         assistant.speak(f"I received your command: {queued_command}", wait_for_completion=True)
#                         print("Resuming background listening...") # It's still running

#                 # Do other work in the main thread
#                 print(".", end="", flush=True)
#                 time.sleep(1)
#         except KeyboardInterrupt:
#             print("\nUser interrupted.")
#         finally:
#             # --- 4. Cleanup ---
#             print("\n--- Cleaning up ---")
#             assistant.stop_background_listening()


#     print("\n=========================================================")
#     print("=== Voice Assistant Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/robotics/voice_assistant.py
# Purpose: A high-level voice assistant that orchestrates dedicated TTS and STT
#          modules to manage a conversational user interface.

import logging
import time
from typing import Optional

logger = logging.getLogger("VoiceAssistant")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

try:
    from modules.robotics.text_to_speech import TextToSpeech
    from modules.robotics.speech_to_text import SpeechToText
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# (Logger setup is identical to the TTS module)

class VoiceAssistant:
    """
    Orchestrates TextToSpeech and SpeechToText to provide a
    seamless conversational experience.
    """
    def __init__(self, wake_word: str = "devin"):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")

        self.tts = TextToSpeech(rate=190)
        self.stt = SpeechToText()
        self.wake_word = wake_word.lower()
        self.is_awake = False
        self.last_interaction_time = 0
        self.timeout_seconds = 30
        logger.info(f"Voice Assistant ready. Listening for wake word: '{self.wake_word}'")

    def speak(self, text: str, wait: bool = True):
        self.tts.speak(text, wait=wait)

    def ask_question(self, question: str) -> Optional[str]:
        self.speak(question, wait=True)
        return self.stt.listen_for_single_phrase()

    def _handle_background_speech(self, text: str):
        """Callback for the STT listener to process wake words and commands."""
        current_time = time.time()
        
        if not self.is_awake:
            if text.strip().startswith(self.wake_word):
                command = text.strip()[len(self.wake_word):].strip()
                logger.info(f"Wake word detected!")
                self.is_awake = True
                self.last_interaction_time = current_time
                self.speak("Yes?", wait=False)
                if command:
                    self._process_command(command)
        else:
            self.last_interaction_time = current_time
            self._process_command(text)
            
    def _process_command(self, command: str):
        """(Placeholder) Processes a recognized command."""
        logger.info(f"Processing command: '{command}'")
        # In a real system, this would trigger the Task Orchestrator.
        if "time is it" in command:
            current_time_str = time.strftime("%I:%M %p")
            self.speak(f"The current time is {current_time_str}")
        elif "go to sleep" in command:
            self.speak("Going back to sleep.")
            self.is_awake = False
        else:
            self.speak(f"I understood the command: {command}")

    def start(self):
        """Starts the main operational loop of the voice assistant."""
        self.stt.start_background_listening(self._handle_background_speech)
        logger.info("Conversational loop started. Press Ctrl+C to exit.")
        try:
            while True:
                if self.is_awake and (time.time() - self.last_interaction_time > self.timeout_seconds):
                    logger.info("Assistant timing out due to inactivity.")
                    self.speak("Going to sleep now.", wait=False)
                    self.is_awake = False
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down Voice Assistant.")
            self.stt.stop_background_listening()

if __name__ == "__main__":
    print("=========================================================")
    print("=== Refactored Voice Assistant (Live Demo) 🗣️🧠 ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module is missing. Error: {_import_error}")
    else:
        print("!!! PREREQUISITE: This demo requires a working microphone and speaker. !!!")
        print("Please ensure you have installed the necessary libraries:")
        print("  pip install pyttsx3 SpeechRecognition PyAudio")
        print("On Linux, you may also need: sudo apt-get install portaudio19-dev espeak\n")

        try:
            assistant = VoiceAssistant(wake_word="devin")

            # --- 1. Demonstrate a direct, blocking question ---
            assistant.speak("To begin the live demo, I need to ask you a question.", wait=True)
            user_name = assistant.ask_question("Please state your name clearly into the microphone.")
            
            if user_name:
                assistant.speak(f"It's a pleasure to meet you, {user_name}.")
            else:
                assistant.speak("I didn't catch your name. We'll proceed anyway.")
            
            # --- 2. Demonstrate the background listener and conversation loop ---
            assistant.speak("I will now listen in the background. Please say my name, followed by a command.", wait=True)
            print("\n--- Listening for 'devin, what time is it?' or 'devin, go to sleep' ---")
            assistant.start()

        except Exception as e:
            logger.error(f"Demo failed to run: {e}")

    print("\n=========================================================")
    print("=== Voice Assistant Prototype Complete ===")
    print("=========================================================")
