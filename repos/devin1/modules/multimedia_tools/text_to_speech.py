import pyttsx3
from gtts import gTTS
import tempfile
import os
import logging


class TextToSpeech:
    """
    A class for converting text to speech using multiple engines like pyttsx3 and gTTS.
    """

    def __init__(self, engine: str = "pyttsx3", language: str = "en"):
        """
        Initialize the TextToSpeech class with the chosen engine and language.

        Args:
            engine (str): The speech synthesis engine to use ("pyttsx3" or "gTTS").
            language (str): The language code for the speech synthesis (default is "en").
        """
        self.engine = engine.lower()
        self.language = language
        self.pyttsx3_engine = None

        if self.engine == "pyttsx3":
            self._initialize_pyttsx3()

    def _initialize_pyttsx3(self):
        """
        Initialize the pyttsx3 engine with default properties.
        """
        self.pyttsx3_engine = pyttsx3.init()
        self.pyttsx3_engine.setProperty("rate", 150)  # Speed of speech
        self.pyttsx3_engine.setProperty("volume", 1.0)  # Volume (0.0 to 1.0)
        voices = self.pyttsx3_engine.getProperty("voices")
        self.pyttsx3_engine.setProperty("voice", voices[0].id)  # Default voice

    def convert_to_speech(self, text: str, output_file: str = None):
        """
        Convert the provided text to speech and optionally save it to a file.

        Args:
            text (str): The text to be converted to speech.
            output_file (str): The path to save the audio output (optional).

        Returns:
            str: Path to the saved audio file (if output_file is specified), otherwise None.
        """
        if not text.strip():
            logging.error("Input text cannot be empty.")
            raise ValueError("Input text cannot be empty.")

        if self.engine == "pyttsx3":
            return self._pyttsx3_speech(text, output_file)
        elif self.engine == "gtts":
            return self._gtts_speech(text, output_file)
        else:
            logging.error(f"Unsupported engine: {self.engine}")
            raise ValueError(f"Unsupported engine: {self.engine}")

    def _pyttsx3_speech(self, text: str, output_file: str = None):
        """
        Convert text to speech using pyttsx3.

        Args:
            text (str): The text to be converted.
            output_file (str): The file path to save the audio (optional).

        Returns:
            str: Path to the saved audio file (if output_file is specified), otherwise None.
        """
        if output_file:
            self.pyttsx3_engine.save_to_file(text, output_file)
            self.pyttsx3_engine.runAndWait()
            logging.info(f"Audio saved to {output_file}.")
            return output_file
        else:
            self.pyttsx3_engine.say(text)
            self.pyttsx3_engine.runAndWait()

    def _gtts_speech(self, text: str, output_file: str = None):
        """
        Convert text to speech using gTTS.

        Args:
            text (str): The text to be converted.
            output_file (str): The file path to save the audio (optional).

        Returns:
            str: Path to the saved audio file.
        """
        tts = gTTS(text=text, lang=self.language)
        if output_file:
            tts.save(output_file)
            logging.info(f"Audio saved to {output_file}.")
            return output_file
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                tts.save(temp_file.name)
                logging.info(f"Temporary audio saved to {temp_file.name}.")
                return temp_file.name

    def list_voices(self):
        """
        List available voices (only for pyttsx3).

        Returns:
            list: A list of available voice names.
        """
        if self.engine != "pyttsx3":
            logging.error("Voice listing is only supported for pyttsx3.")
            raise NotImplementedError("Voice listing is only supported for pyttsx3.")

        voices = self.pyttsx3_engine.getProperty("voices")
        return [voice.name for voice in voices]

    def set_voice(self, voice_name: str):
        """
        Set the voice for speech synthesis (only for pyttsx3).

        Args:
            voice_name (str): The name of the voice to use.
        """
        if self.engine != "pyttsx3":
            logging.error("Voice selection is only supported for pyttsx3.")
            raise NotImplementedError("Voice selection is only supported for pyttsx3.")

        voices = self.pyttsx3_engine.getProperty("voices")
        for voice in voices:
            if voice_name.lower() in voice.name.lower():
                self.pyttsx3_engine.setProperty("voice", voice.id)
                logging.info(f"Voice set to {voice.name}.")
                return

        logging.error(f"Voice '{voice_name}' not found.")
        raise ValueError(f"Voice '{voice_name}' not found.")


# Example Usage
if __name__ == "__main__":
    tts = TextToSpeech(engine="pyttsx3")
    tts.convert_to_speech("Welcome to Devin's advanced AI capabilities.", "output_audio.mp3")
    tts.list_voices()
