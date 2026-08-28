"""
plugins/speech_to_text.py

Speech-to-text translation module for converting spoken audio into text
using advanced machine learning models and APIs.
"""

import os
import speech_recognition as sr
from typing import Optional, Dict
from pydub import AudioSegment

class SpeechToText:
    """
    Class to handle speech-to-text functionality using offline and online methods.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.recognizer = sr.Recognizer()
        self.api_key = api_key

    def transcribe_audio_file(self, file_path: str, language: str = "en-US") -> str:
        """
        Transcribes an audio file into text.

        Args:
            file_path (str): Path to the audio file.
            language (str): Language code for transcription (default is 'en-US').

        Returns:
            str: Transcribed text.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        try:
            with sr.AudioFile(file_path) as source:
                print(f"Loading audio file: {file_path}")
                audio_data = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio_data, language=language)
        except sr.UnknownValueError:
            return "Speech could not be understood."
        except sr.RequestError as e:
            return f"API request error: {e}"

    def live_transcription(self, language: str = "en-US") -> str:
        """
        Performs live transcription from microphone input.

        Args:
            language (str): Language code for transcription (default is 'en-US').

        Returns:
            str: Transcribed text.
        """
        try:
            with sr.Microphone() as source:
                print("Please speak now...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio_data = self.recognizer.listen(source)
                return self.recognizer.recognize_google(audio_data, language=language)
        except sr.UnknownValueError:
            return "Speech could not be understood."
        except sr.RequestError as e:
            return f"API request error: {e}"

    def convert_audio_format(self, input_file: str, output_file: str, format: str = "wav") -> str:
        """
        Converts an audio file to a different format.

        Args:
            input_file (str): Path to the input audio file.
            output_file (str): Path to save the converted audio file.
            format (str): Desired audio format (default is 'wav').

        Returns:
            str: Path to the converted audio file.
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"The input file {input_file} does not exist.")

        try:
            audio = AudioSegment.from_file(input_file)
            audio.export(output_file, format=format)
            print(f"Audio converted to {format} format and saved as {output_file}")
            return output_file
        except Exception as e:
            raise RuntimeError(f"Error in converting audio format: {e}")

    def api_transcription(self, file_path: str, api_url: str, headers: Optional[Dict[str, str]] = None) -> str:
        """
        Transcribes audio using an external API.

        Args:
            file_path (str): Path to the audio file.
            api_url (str): URL of the external API.
            headers (Optional[Dict[str, str]]): Additional headers for the API request.

        Returns:
            str: Transcribed text.
        """
        import requests

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")

        try:
            with open(file_path, 'rb') as audio_file:
                print("Sending audio to external API for transcription...")
                response = requests.post(api_url, files={'file': audio_file}, headers=headers)
                response.raise_for_status()
                return response.json().get("transcription", "No transcription returned.")
        except requests.RequestException as e:
            raise RuntimeError(f"API request error: {e}")

# Example usage
if __name__ == "__main__":
    stt = SpeechToText()
    audio_path = "sample_audio.wav"
    try:
        text = stt.transcribe_audio_file(audio_path)
        print(f"Transcribed text: {text}")
    except Exception as e:
        print(f"Error: {e}")
