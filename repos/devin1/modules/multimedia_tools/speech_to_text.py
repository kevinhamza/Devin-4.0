"""
Speech-to-Text Translation Module
This module provides functionalities to process audio inputs and convert them into transcribed text.
It supports multiple languages, custom dictionaries, and real-time transcription capabilities.
"""

import os
import speech_recognition as sr
import wave
import contextlib
from pydub import AudioSegment
from typing import Optional, Dict, List, Tuple

class SpeechToText:
    def __init__(self, language: str = "en-US", custom_dict: Optional[Dict[str, str]] = None):
        """
        Initialize the Speech-to-Text system.

        :param language: Language code for transcription (default: "en-US").
        :param custom_dict: Optional dictionary for word replacements (e.g., {"u": "you"}).
        """
        self.recognizer = sr.Recognizer()
        self.language = language
        self.custom_dict = custom_dict or {}

    @staticmethod
    def convert_audio_to_wav(input_audio_path: str, output_audio_path: str) -> None:
        """
        Convert audio to WAV format.

        :param input_audio_path: Path to the input audio file.
        :param output_audio_path: Path to save the converted WAV file.
        """
        audio = AudioSegment.from_file(input_audio_path)
        audio.export(output_audio_path, format="wav")

    @staticmethod
    def get_audio_duration(audio_path: str) -> float:
        """
        Get the duration of an audio file.

        :param audio_path: Path to the audio file.
        :return: Duration in seconds.
        """
        with contextlib.closing(wave.open(audio_path, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            return frames / float(rate)

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio file to text.

        :param audio_path: Path to the WAV audio file.
        :return: Transcribed text.
        """
        with sr.AudioFile(audio_path) as source:
            audio_data = self.recognizer.record(source)

        try:
            transcription = self.recognizer.recognize_google(audio_data, language=self.language)
            return self._apply_custom_dictionary(transcription)
        except sr.UnknownValueError:
            return "Could not understand the audio."
        except sr.RequestError as e:
            return f"Speech Recognition API error: {e}"

    def transcribe_audio_chunks(self, audio_path: str, chunk_duration: float = 30.0) -> List[Tuple[int, str]]:
        """
        Transcribe audio file in chunks for long recordings.

        :param audio_path: Path to the WAV audio file.
        :param chunk_duration: Duration of each chunk in seconds.
        :return: List of tuples with chunk index and transcribed text.
        """
        audio_duration = self.get_audio_duration(audio_path)
        transcriptions = []
        with sr.AudioFile(audio_path) as source:
            for i in range(0, int(audio_duration), int(chunk_duration)):
                audio_data = self.recognizer.record(source, duration=chunk_duration)
                try:
                    transcription = self.recognizer.recognize_google(audio_data, language=self.language)
                    transcriptions.append((i, self._apply_custom_dictionary(transcription)))
                except sr.UnknownValueError:
                    transcriptions.append((i, "Could not understand the audio."))
                except sr.RequestError as e:
                    transcriptions.append((i, f"Speech Recognition API error: {e}"))
        return transcriptions

    def _apply_custom_dictionary(self, transcription: str) -> str:
        """
        Apply custom dictionary to the transcription.

        :param transcription: Original transcription text.
        :return: Modified transcription text.
        """
        for word, replacement in self.custom_dict.items():
            transcription = transcription.replace(word, replacement)
        return transcription

    def real_time_transcription(self) -> None:
        """
        Perform real-time transcription using the microphone.
        """
        print("Starting real-time transcription. Speak into the microphone.")
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                while True:
                    print("Listening...")
                    audio_data = self.recognizer.listen(source)
                    try:
                        transcription = self.recognizer.recognize_google(audio_data, language=self.language)
                        print(f"Transcription: {self._apply_custom_dictionary(transcription)}")
                    except sr.UnknownValueError:
                        print("Could not understand the audio.")
                    except sr.RequestError as e:
                        print(f"Speech Recognition API error: {e}")
        except KeyboardInterrupt:
            print("\nReal-time transcription stopped.")

# Example usage
if __name__ == "__main__":
    stt = SpeechToText(language="en-US", custom_dict={"u": "you", "r": "are"})
    audio_path = "path/to/audio/file.mp3"
    wav_path = "path/to/output/file.wav"

    # Convert and transcribe
    stt.convert_audio_to_wav(audio_path, wav_path)
    print("Transcription:", stt.transcribe_audio(wav_path))

    # Real-time transcription
    # stt.real_time_transcription()
