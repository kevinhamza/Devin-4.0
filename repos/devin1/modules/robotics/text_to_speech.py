"""
Text-to-Speech Module
======================
Converts text into speech for vocal interactions in the robotics system.
Utilizes TTS libraries and APIs for natural voice output.
"""

import pyttsx3
import logging
from gtts import gTTS
import os

class TextToSpeech:
    """
    Handles text-to-speech conversion using multiple engines for flexible voice generation.
    """

    def __init__(self, engine="pyttsx3", language="en"):
        """
        Initializes the TTS module.

        Args:
            engine (str): The TTS engine to use ("pyttsx3" or "gTTS").
            language (str): Language for speech synthesis (ISO 639-1 code).
        """
        self.engine_name = engine.lower()
        self.language = language
        self.engine = None
        logging.info(f"[TTS] Initializing TTS engine: {self.engine_name}")

        if self.engine_name == "pyttsx3":
            self._initialize_pyttsx3()
        elif self.engine_name == "gtts":
            logging.info("[TTS] Using gTTS for speech synthesis.")
        else:
            logging.error(f"[TTS] Unsupported TTS engine: {self.engine_name}")

    def _initialize_pyttsx3(self):
        """
        Sets up the pyttsx3 TTS engine.
        """
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 150)  # Speech rate
            self.engine.setProperty("volume", 0.9)  # Volume (0.0 to 1.0)
            logging.info("[TTS] pyttsx3 engine initialized.")
        except Exception as e:
            logging.error(f"[TTS] Error initializing pyttsx3: {e}")

    def speak(self, text: str, save_to_file=False, file_path="output.mp3"):
        """
        Converts text to speech and plays it.

        Args:
            text (str): The text to convert to speech.
            save_to_file (bool): If True, saves the speech output to a file.
            file_path (str): The file path to save the speech output (used only with gTTS).
        """
        if self.engine_name == "pyttsx3" and self.engine:
            self._speak_with_pyttsx3(text)
        elif self.engine_name == "gtts":
            self._speak_with_gtts(text, save_to_file, file_path)
        else:
            logging.error(f"[TTS] No valid TTS engine initialized for: {self.engine_name}")

    def _speak_with_pyttsx3(self, text: str):
        """
        Speaks text using pyttsx3.

        Args:
            text (str): The text to convert to speech.
        """
        try:
            logging.info(f"[TTS] Speaking text with pyttsx3: {text}")
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logging.error(f"[TTS] Error speaking text with pyttsx3: {e}")

    def _speak_with_gtts(self, text: str, save_to_file: bool, file_path: str):
        """
        Speaks text using gTTS.

        Args:
            text (str): The text to convert to speech.
            save_to_file (bool): If True, saves the speech output to a file.
            file_path (str): The file path to save the speech output.
        """
        try:
            logging.info(f"[TTS] Generating speech with gTTS: {text}")
            tts = gTTS(text=text, lang=self.language, slow=False)

            if save_to_file:
                logging.info(f"[TTS] Saving speech to file: {file_path}")
                tts.save(file_path)
            else:
                tts.save("temp.mp3")
                os.system("mpg123 temp.mp3")  # Playback with system tool
                os.remove("temp.mp3")
        except Exception as e:
            logging.error(f"[TTS] Error generating speech with gTTS: {e}")

    def change_voice(self, voice_index: int = 0):
        """
        Changes the voice for the pyttsx3 engine.

        Args:
            voice_index (int): Index of the desired voice.
        """
        if self.engine_name == "pyttsx3" and self.engine:
            try:
                voices = self.engine.getProperty("voices")
                self.engine.setProperty("voice", voices[voice_index].id)
                logging.info(f"[TTS] Voice changed to index: {voice_index}")
            except Exception as e:
                logging.error(f"[TTS] Error changing voice: {e}")
        else:
            logging.error(f"[TTS] Voice changing not supported for: {self.engine_name}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Initialize TTS
    tts = TextToSpeech(engine="gtts", language="en")
    tts.speak("Hello, this is a test of the Text to Speech module.", save_to_file=True)

    # Example with pyttsx3
    tts_pyttsx3 = TextToSpeech(engine="pyttsx3")
    tts_pyttsx3.speak("This is another test with the pyttsx3 engine.")
    tts_pyttsx3.change_voice(1)  # Switch voice
    tts_pyttsx3.speak("Voice has been changed successfully.")
