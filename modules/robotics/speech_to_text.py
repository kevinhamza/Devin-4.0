# # Devin/modules/robotics/speech_to_text.py
# # Purpose: Provides a dedicated, implementation-ready Speech-to-Text (STT)
# #          engine for transcribing spoken audio into text.

# import logging
# import queue
# import time
# from typing import Optional, Callable

# try:
#     import speech_recognition as sr
#     STT_LIBS_AVAILABLE = True
# except ImportError:
#     STT_LIBS_AVAILABLE = False
#     sr = None

# # Configure basic logging
# logger = logging.getLogger("SpeechToText")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class SpeechToText:
#     """
#     A dedicated wrapper for a Speech-to-Text engine to handle voice input.
#     """

#     def __init__(self, energy_threshold: int = 4000, pause_threshold: float = 0.8):
#         """
#         Initializes the STT recognizer.

#         Args:
#             energy_threshold (int): The energy level threshold for ambient noise.
#                                     Higher values are less sensitive.
#             pause_threshold (float): Seconds of non-speaking audio before a
#                                      phrase is considered complete.
#         """
#         if not STT_LIBS_AVAILABLE:
#             self.recognizer = None
#             logger.error("SpeechRecognition or PyAudio library not found! This module is non-functional.")
#             return

#         logger.info("Initializing STT engine...")
#         self.recognizer = sr.Recognizer()
#         self.recognizer.energy_threshold = energy_threshold
#         self.recognizer.pause_threshold = pause_threshold
#         self.recognizer.dynamic_energy_threshold = False # We will use manual calibration

#         # For background listening
#         self._stop_background_listener: Optional[Callable[[], None]] = None

#     def calibrate_for_ambient_noise(self, device_index: Optional[int] = None, duration: int = 1):
#         """
#         Listens to the ambient noise to calibrate the energy threshold for recognition.
#         This should be called once in a quiet moment before listening for commands.

#         Args:
#             device_index (Optional[int]): The index of the microphone to use.
#             duration (int): How long to listen to the ambient noise in seconds.
#         """
#         if not self.recognizer:
#             logger.error("Cannot calibrate: STT engine not initialized.")
#             return

#         logger.info("Calibrating for ambient noise... Please be quiet.")
#         try:
#             with sr.Microphone(device_index=device_index) as source:
#                 self.recognizer.adjust_for_ambient_noise(source, duration=duration)
#             logger.info(f"Calibration complete. New energy threshold: {self.recognizer.energy_threshold}")
#         except Exception as e:
#             logger.error(f"Could not calibrate microphone: {e}")

#     def listen_for_single_phrase(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
#         """
#         Listens for a single phrase and returns the transcribed text.
#         This is a blocking operation.

#         Returns:
#             Optional[str]: The transcribed text, or None on failure/timeout.
#         """
#         if not self.recognizer:
#             logger.error("Cannot listen: STT engine not initialized.")
#             return None

#         try:
#             with sr.Microphone() as source:
#                 logger.info("Listening for a single phrase...")
#                 audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                
#                 logger.info("Recognizing...")
#                 # Using Google's Web Speech API. For offline, use recognize_sphinx()
#                 text = self.recognizer.recognize_google(audio)
#                 logger.info(f"Transcribed: '{text}'")
#                 return text.lower()
#         except sr.WaitTimeoutError:
#             logger.warning("Listening timed out waiting for phrase to start.")
#             return None
#         except sr.UnknownValueError:
#             logger.warning("STT engine could not understand the audio.")
#             return None
#         except sr.RequestError as e:
#             logger.error(f"STT service request failed; {e}")
#             return None
#         except Exception as e:
#             logger.error(f"An unknown error occurred during listening: {e}")
#             return None

#     def start_background_listening(self, on_speech_recognized: Callable[[str], None]):
#         """
#         Starts a non-blocking background thread to continuously listen for speech.

#         Args:
#             on_speech_recognized (Callable[[str], None]): The callback function to execute
#                                                           with the transcribed text when speech is recognized.
#         """
#         if not self.recognizer:
#             logger.error("Cannot start background listening: STT engine not initialized.")
#             return

#         if self._stop_background_listener is not None:
#             logger.warning("Background listener is already active.")
#             return

#         # Define the internal callback that will pass data to the user's callback
#         def _internal_callback(recognizer, audio_data):
#             logger.debug("Background thread captured audio, attempting recognition.")
#             try:
#                 text = recognizer.recognize_google(audio_data)
#                 logger.info(f"Background listener transcribed: '{text}'")
#                 on_speech_recognized(text.lower()) # Call the user's function
#             except sr.UnknownValueError:
#                 logger.debug("Background listener could not understand audio.")
#             except sr.RequestError as e:
#                 logger.error(f"Background listener request failed; {e}")
        
#         try:
#             mic_source = sr.Microphone()
#             logger.info("Starting non-blocking background listener...")
#             self._stop_background_listener = self.recognizer.listen_in_background(mic_source, _internal_callback)
#             logger.info("Background listener is now active.")
#         except Exception as e:
#              logger.error(f"Could not start background listener. Is a microphone connected? Error: {e}")

#     def stop_background_listening(self):
#         """Stops the background listening thread if it is running."""
#         if self._stop_background_listener:
#             logger.info("Stopping background listener...")
#             self._stop_background_listener(wait_for_stop=False)
#             self._stop_background_listener = None
#             logger.info("Background listener stopped.")
#         else:
#             logger.info("Background listener is not currently active.")


# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Speech-to-Text (STT) Module Prototype 🎤 ===")
#     print("=========================================================")
    
#     if not STT_LIBS_AVAILABLE:
#         print("\n'SpeechRecognition' or 'PyAudio' not found. Please install them to run this demo.")
#     else:
#         stt = SpeechToText()

#         # --- 1. Calibrate for ambient noise ---
#         print("\n--- Step 1: Calibrating for ambient noise (1 second) ---")
#         stt.calibrate_for_ambient_noise(duration=1)

#         # --- 2. Demonstrate blocking listener ---
#         print("\n\n--- Step 2: Blocking Listener Demo ---")
#         print("Please say a single command (e.g., 'launch the drone'). I will listen for 10 seconds.")
#         command = stt.listen_for_single_phrase(phrase_time_limit=10)
#         if command:
#             print(f"  -> Blocking listener received: '{command}'")
#         else:
#             print("  -> Blocking listener did not catch a command.")
            
#         time.sleep(1)

#         # --- 3. Demonstrate non-blocking background listener ---
#         print("\n\n--- Step 3: Non-Blocking Background Listener Demo ---")
        
#         # Define the callback function that will handle transcribed text
#         def my_stt_callback(text: str):
#             print(f"\n  [CALLBACK] Heard in background: '{text}'")

#         stt.start_background_listening(my_stt_callback)

#         print("Background listener is now active. Say something every few seconds.")
#         print("The main program can continue doing other work. (Press Ctrl+C to stop)")
        
#         try:
#             # This loop simulates the main program doing other things
#             # while the STT module listens in the background.
#             for i in range(30):
#                 print(f".", end="", flush=True)
#                 time.sleep(1)
#             print("\nDemo finished.")
#         except KeyboardInterrupt:
#             print("\nUser interrupted.")
#         finally:
#             # --- 4. Cleanup ---
#             stt.stop_background_listening()

#     print("\n=========================================================")
#     print("=== STT Module Prototype Complete ===")
#     print("=========================================================")



# Devin/modules/robotics/speech_to_text.py
# Purpose: A dedicated, functional module for Speech-to-Text (STT) recognition.

import logging
from typing import Optional, Callable
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

logger = logging.getLogger("SpeechToText")
# (Logger setup is identical to the TTS module)

class SpeechToText:
    """A wrapper for the SpeechRecognition library."""
    def __init__(self):
        if not SPEECH_RECOGNITION_AVAILABLE:
            raise ImportError("SpeechRecognition is required. 'pip install SpeechRecognition PyAudio'")
        self.recognizer = sr.Recognizer()
        self.stop_listening_func = None
        logger.info("Speech-to-Text engine initialized.")

    def calibrate_for_ambient_noise(self, source, duration=1):
        """Adjusts the recognizer's sensitivity to ambient noise."""
        logger.info("Calibrating for ambient noise...")
        self.recognizer.adjust_for_ambient_noise(source, duration=duration)
        logger.info("Calibration complete.")

    def listen_for_single_phrase(self, timeout=5, phrase_time_limit=10) -> Optional[str]:
        """Listens for a single phrase and returns the transcribed text."""
        with sr.Microphone() as source:
            self.calibrate_for_ambient_noise(source)
            logger.info("Listening for a single phrase...")
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Recognized: '{text}'")
                return text.lower()
            except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError) as e:
                logger.warning(f"Could not recognize speech: {e}")
                return None

    def start_background_listening(self, callback: Callable[[str], None]):
        """Starts listening in a non-blocking background thread."""
        mic = sr.Microphone()
        # Calibrate once before starting
        with mic as source:
            self.calibrate_for_ambient_noise(source)
        
        def _background_callback(recognizer, audio_data):
            try:
                text = recognizer.recognize_google(audio_data)
                callback(text.lower())
            except (sr.UnknownValueError, sr.RequestError):
                pass # Ignore phrases we can't understand

        self.stop_listening_func = self.recognizer.listen_in_background(mic, _background_callback)
        logger.info("Background listening started.")

    def stop_background_listening(self):
        if self.stop_listening_func:
            self.stop_listening_func(wait_for_stop=False)
            self.stop_listening_func = None
            logger.info("Background listening stopped.")

if __name__ == "__main__":
    print("--- STT Module Self-Test ---")
    if not SPEECH_RECOGNITION_AVAILABLE:
        print("SpeechRecognition/PyAudio not found. Skipping test.")
    else:
        stt = SpeechToText()
        print("Please say 'hello devin' into your microphone.")
        text = stt.listen_for_single_phrase()
        if text:
            print(f"SUCCESS: Heard you say: '{text}'")
        else:
            print("FAILURE: Did not hear anything.")
