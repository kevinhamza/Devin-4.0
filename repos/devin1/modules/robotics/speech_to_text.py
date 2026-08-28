"""
Speech-to-Text Module
=====================
This module transcribes speech into text using advanced speech recognition
technologies and NLP (Natural Language Processing) for contextual understanding.
"""

import speech_recognition as sr
import logging
from modules.utils.audio_processing import enhance_audio_quality

class SpeechToText:
    """
    Speech-to-text processor that uses an external microphone or audio input
    to convert speech into text in real-time.
    """

    def __init__(self, language="en-US", energy_threshold=300, dynamic_energy=True):
        """
        Initializes the speech recognition system.

        Args:
            language (str): Language for recognition (e.g., "en-US").
            energy_threshold (int): Threshold for ambient noise energy.
            dynamic_energy (bool): Whether to adjust energy dynamically.
        """
        self.recognizer = sr.Recognizer()
        self.language = language
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.dynamic_energy_threshold = dynamic_energy
        self.microphone = sr.Microphone()
        logging.info("Speech-to-text module initialized.")

    def calibrate_microphone(self, duration=2):
        """
        Calibrates the microphone for ambient noise.

        Args:
            duration (int): Duration in seconds for calibration.
        """
        try:
            with self.microphone as source:
                logging.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                logging.info("Microphone calibration complete.")
        except Exception as e:
            logging.error(f"Error calibrating microphone: {e}")

    def listen_and_transcribe(self):
        """
        Listens to the microphone input and transcribes speech into text.

        Returns:
            str: The transcribed text, or error message if transcription fails.
        """
        try:
            with self.microphone as source:
                logging.info("Listening for speech...")
                audio = self.recognizer.listen(source)
                logging.info("Processing speech...")
                enhanced_audio = enhance_audio_quality(audio)
                text = self.recognizer.recognize_google(enhanced_audio, language=self.language)
                logging.info(f"Transcription: {text}")
                return text
        except sr.UnknownValueError:
            logging.warning("Speech recognition could not understand audio.")
            return "Could not understand audio."
        except sr.RequestError as e:
            logging.error(f"Speech recognition service error: {e}")
            return "Error with speech recognition service."
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return "An error occurred during transcription."

    def transcribe_audio_file(self, file_path):
        """
        Transcribes speech from an audio file.

        Args:
            file_path (str): Path to the audio file.

        Returns:
            str: The transcribed text, or error message if transcription fails.
        """
        try:
            with sr.AudioFile(file_path) as source:
                audio = self.recognizer.record(source)
                logging.info(f"Transcribing audio file: {file_path}")
                enhanced_audio = enhance_audio_quality(audio)
                text = self.recognizer.recognize_google(enhanced_audio, language=self.language)
                logging.info(f"Transcription: {text}")
                return text
        except FileNotFoundError:
            logging.error(f"Audio file not found: {file_path}")
            return "Audio file not found."
        except sr.UnknownValueError:
            logging.warning("Speech recognition could not understand audio from file.")
            return "Could not understand audio from file."
        except sr.RequestError as e:
            logging.error(f"Speech recognition service error: {e}")
            return "Error with speech recognition service."
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return "An error occurred during transcription."

# Example Usage
if __name__ == "__main__":
    stt = SpeechToText()
    stt.calibrate_microphone()
    print("Say something:")
    print(stt.listen_and_transcribe())
