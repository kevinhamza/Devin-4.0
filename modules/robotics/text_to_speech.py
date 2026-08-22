# # Devin/modules/robotics/text_to_speech.py
# # Purpose: Provides a dedicated, implementation-ready Text-to-Speech (TTS)
# #          engine for converting text into spoken audio.

# import logging
# from typing import List, Dict, Optional

# try:
#     import pyttsx3
#     TTS_LIBS_AVAILABLE = True
# except ImportError:
#     TTS_LIBS_AVAILABLE = False
#     pyttsx3 = None

# # Configure basic logging
# logger = logging.getLogger("TextToSpeech")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class TextToSpeech:
#     """
#     A dedicated wrapper for a Text-to-Speech engine (pyttsx3) to provide
#     spoken output for Devin.
#     """

#     def __init__(self, rate: int = 180, volume: float = 1.0, voice_id: Optional[str] = None):
#         """
#         Initializes the TTS engine.

#         Args:
#             rate (int): The speaking rate in words per minute.
#             volume (float): The speaking volume (0.0 to 1.0).
#             voice_id (Optional[str]): The specific voice ID to use. If None, the system default is used.
#         """
#         if not TTS_LIBS_AVAILABLE:
#             self.engine = None
#             logger.error("pyttsx3 library not found! Please run: 'pip install pyttsx3'.")
#             logger.error("On Linux, you may also need `espeak`: `sudo apt-get install espeak`")
#             return
            
#         try:
#             logger.info("Initializing TTS engine...")
#             self.engine = pyttsx3.init()
#             self.engine.setProperty('rate', rate)
#             self.engine.setProperty('volume', volume)
#             if voice_id:
#                 self.engine.setProperty('voice', voice_id)
#             logger.info(f"TTS engine ready. Current voice: {self.engine.getProperty('voice')}")
#         except Exception as e:
#             logger.error(f"Failed to initialize pyttsx3 engine: {e}")
#             self.engine = None

#     def list_voices(self) -> List[Dict[str, str]]:
#         """
#         Lists all available voices on the system.

#         Returns:
#             A list of dictionaries, with each dictionary representing a voice.
#         """
#         if not self.engine:
#             logger.error("Cannot list voices: TTS engine not initialized.")
#             return []
            
#         voices_data = []
#         voices = self.engine.getProperty('voices')
#         for voice in voices:
#             voices_data.append({
#                 "id": voice.id,
#                 "name": voice.name,
#                 "lang": voice.languages,
#                 "gender": voice.gender,
#             })
#         return voices_data

#     def set_voice(self, voice_id: str) -> bool:
#         """
#         Sets the voice to be used for speech.

#         Args:
#             voice_id (str): The ID of the voice to use (from list_voices()).

#         Returns:
#             True if the voice was set successfully, False otherwise.
#         """
#         if not self.engine:
#             logger.error("Cannot set voice: TTS engine not initialized.")
#             return False
            
#         available_ids = [v['id'] for v in self.list_voices()]
#         if voice_id in available_ids:
#             self.engine.setProperty('voice', voice_id)
#             logger.info(f"TTS voice changed to: {voice_id}")
#             return True
#         else:
#             logger.error(f"Voice ID '{voice_id}' not found.")
#             return False

#     def speak(self, text: str, wait: bool = True):
#         """
#         Converts the given text to speech.

#         Args:
#             text (str): The text to speak.
#             wait (bool): If True, the method blocks until speech is finished.
#                          If False, it queues the speech and returns immediately.
#         """
#         if not self.engine:
#             logger.error("Cannot speak: TTS engine not initialized.")
#             # Provide a fallback for systems without TTS
#             print(f"DEVIN (Spoken): {text}")
#             return

#         logger.info(f"Speaking: '{text[:70]}...'")
#         try:
#             self.engine.say(text)
#             if wait:
#                 self.engine.runAndWait()
#         except Exception as e:
#             logger.error(f"An error occurred during speech synthesis: {e}")

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Text-to-Speech (TTS) Module Prototype 🗣️ ===")
#     print("=========================================================")

#     if not TTS_LIBS_AVAILABLE:
#         print("\n'pyttsx3' library not found. Please install it to run this demo.")
#     else:
#         tts = TextToSpeech(rate=190)

#         # --- 1. List available voices ---
#         print("\n--- Listing available system voices ---")
#         available_voices = tts.list_voices()
#         if available_voices:
#             for i, voice in enumerate(available_voices):
#                 print(f"  Voice {i}:")
#                 print(f"    - Name: {voice['name']}")
#                 print(f"    - ID: {voice['id']}")
            
#             # --- 2. Speak with the default voice ---
#             print("\n\n--- Speaking with the default voice ---")
#             tts.speak("Hello, this is the default system voice. I am ready to serve as Devin's primary audio output.")

#             # --- 3. Change voice and speak again (if multiple voices exist) ---
#             if len(available_voices) > 1:
#                 print("\n\n--- Attempting to switch to a different voice ---")
#                 # Try to find a voice of the opposite gender or just the next one
#                 # This is a simple example; a real app might have more robust logic
#                 new_voice_id = available_voices[1].get('id')
#                 if tts.set_voice(new_voice_id):
#                     tts.speak("I have now switched to a new voice. How does this sound?")
#                 else:
#                     tts.speak("I was unable to switch voices, so I am speaking with the default voice again.")
#             else:
#                 print("\n\n--- Only one voice found, cannot demonstrate switching ---")
#                 tts.speak("My apologies, but it seems I only have one voice available on this system.")

#         else:
#             print("\nNo TTS voices were found on this system.")
#             tts.speak("Error: No text to speech voices were found on this system.")


#     print("\n=========================================================")
#     print("=== TTS Module Prototype Complete ===")
#     print("=========================================================")



# Devin/modules/robotics/text_to_speech.py
# Purpose: A dedicated, functional module for Text-to-Speech (TTS) synthesis.

import logging
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

logger = logging.getLogger("TextToSpeech")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

class TextToSpeech:
    """A wrapper for the pyttsx3 library to provide text-to-speech."""
    def __init__(self, rate: int = 190, volume: float = 1.0):
        if not PYTTSX3_AVAILABLE:
            raise ImportError("pyttsx3 is required. 'pip install pyttsx3'")
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            logger.info("Text-to-Speech engine initialized successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize pyttsx3 engine: {e}")

    def speak(self, text: str, wait: bool = True):
        """Converts text to spoken audio."""
        logger.info(f"Speaking: \"{text[:60]}{'...' if len(text)>60 else ''}\"")
        self.engine.say(text)
        if wait:
            self.engine.runAndWait()

    def list_voices(self):
        """Lists available TTS voices on the system."""
        return self.engine.getProperty('voices')

if __name__ == "__main__":
    print("--- TTS Module Self-Test ---")
    if not PYTTSX3_AVAILABLE:
        print("pyttsx3 not found. Skipping test.")
    else:
        try:
            tts = TextToSpeech()
            print("Available voices:")
            for voice in tts.list_voices():
                print(f"  - ID: {voice.id}, Name: {voice.name}, Lang: {voice.languages}")
            tts.speak("Text to speech module is functioning correctly.")
        except Exception as e:
            print(f"TTS self-test failed: {e}")
