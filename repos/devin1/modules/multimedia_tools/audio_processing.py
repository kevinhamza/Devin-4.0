"""
Audio Processing Tools
======================
This module provides tools for audio transcription and synthesis. 
It supports tasks such as audio file processing, text-to-speech (TTS), 
speech-to-text (STT), and audio editing.

Dependencies:
- SpeechRecognition for speech-to-text
- pyttsx3 for text-to-speech
- Pydub for audio file manipulation
- ffmpeg/avconv for audio conversion (required by Pydub)
"""

import os
import speech_recognition as sr
import pyttsx3
from pydub import AudioSegment
from pydub.playback import play


class AudioProcessing:
    """
    A class to handle audio transcription and synthesis tasks.
    """

    def __init__(self):
        """
        Initializes the AudioProcessing class.
        """
        self.tts_engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()

    # -----------------------
    # Speech-to-Text (STT)
    # -----------------------

    def transcribe_audio(self, audio_file):
        """
        Transcribes speech from an audio file.

        Args:
            audio_file (str): Path to the audio file.

        Returns:
            str: Transcribed text.
        """
        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = self.recognizer.record(source)
                transcription = self.recognizer.recognize_google(audio_data)
                return transcription
        except Exception as e:
            return f"Error during transcription: {e}"

    # -----------------------
    # Text-to-Speech (TTS)
    # -----------------------

    def synthesize_speech(self, text, output_file=None):
        """
        Converts text to speech.

        Args:
            text (str): The text to convert to speech.
            output_file (str, optional): Path to save the audio file. If None, plays audio.

        Returns:
            None
        """
        self.tts_engine.say(text)
        if output_file:
            self.tts_engine.save_to_file(text, output_file)
        self.tts_engine.runAndWait()

    # -----------------------
    # Audio Conversion
    # -----------------------

    def convert_audio_format(self, input_file, output_file, target_format="wav"):
        """
        Converts an audio file to a different format.

        Args:
            input_file (str): Path to the input audio file.
            output_file (str): Path to save the converted audio file.
            target_format (str): Target audio format (e.g., "wav", "mp3").

        Returns:
            None
        """
        try:
            audio = AudioSegment.from_file(input_file)
            audio.export(output_file, format=target_format)
        except Exception as e:
            print(f"Error during conversion: {e}")

    # -----------------------
    # Audio Editing
    # -----------------------

    def split_audio(self, input_file, output_dir, segment_duration):
        """
        Splits an audio file into smaller segments.

        Args:
            input_file (str): Path to the input audio file.
            output_dir (str): Directory to save the segments.
            segment_duration (int): Duration of each segment in milliseconds.

        Returns:
            None
        """
        try:
            audio = AudioSegment.from_file(input_file)
            for i, segment in enumerate(audio[::segment_duration]):
                segment.export(os.path.join(output_dir, f"segment_{i + 1}.wav"), format="wav")
        except Exception as e:
            print(f"Error during splitting: {e}")

    def merge_audio(self, audio_files, output_file):
        """
        Merges multiple audio files into one.

        Args:
            audio_files (list): List of audio file paths to merge.
            output_file (str): Path to save the merged audio.

        Returns:
            None
        """
        try:
            combined_audio = AudioSegment.empty()
            for file in audio_files:
                audio = AudioSegment.from_file(file)
                combined_audio += audio
            combined_audio.export(output_file, format="wav")
        except Exception as e:
            print(f"Error during merging: {e}")

    def apply_volume_change(self, input_file, output_file, decibels):
        """
        Adjusts the volume of an audio file.

        Args:
            input_file (str): Path to the input audio file.
            output_file (str): Path to save the adjusted audio.
            decibels (int): Volume adjustment in decibels (+/-).

        Returns:
            None
        """
        try:
            audio = AudioSegment.from_file(input_file)
            adjusted_audio = audio + decibels
            adjusted_audio.export(output_file, format="wav")
        except Exception as e:
            print(f"Error during volume adjustment: {e}")

    def playback_audio(self, audio_file):
        """
        Plays an audio file.

        Args:
            audio_file (str): Path to the audio file.

        Returns:
            None
        """
        try:
            audio = AudioSegment.from_file(audio_file)
            play(audio)
        except Exception as e:
            print(f"Error during playback: {e}")


# Example usage
if __name__ == "__main__":
    audio_processor = AudioProcessing()

    # Speech-to-Text
    print("Transcription:", audio_processor.transcribe_audio("example.wav"))

    # Text-to-Speech
    audio_processor.synthesize_speech("Hello, this is a text-to-speech example.", "tts_output.wav")

    # Audio Conversion
    audio_processor.convert_audio_format("example.mp3", "converted.wav", target_format="wav")

    # Split Audio
    audio_processor.split_audio("example.wav", "segments", segment_duration=10000)

    # Merge Audio
    audio_processor.merge_audio(["segment_1.wav", "segment_2.wav"], "merged.wav")

    # Adjust Volume
    audio_processor.apply_volume_change("example.wav", "volume_adjusted.wav", decibels=5)

    # Playback
    audio_processor.playback_audio("volume_adjusted.wav")
