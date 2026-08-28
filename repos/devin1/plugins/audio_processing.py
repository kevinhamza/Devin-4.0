"""
audio_processing.py
--------------------
Provides audio transcription, synthesis, and manipulation capabilities, including text-to-speech (TTS),
speech-to-text (STT), audio enhancement, and format conversion.
"""

import speech_recognition as sr
from gtts import gTTS
import pydub
from pydub import AudioSegment
import os


class AudioProcessing:
    def __init__(self, audio_file: str = None):
        self.audio_file = audio_file

    def transcribe_audio(self):
        """Transcribes speech from an audio file."""
        if not self.audio_file or not os.path.exists(self.audio_file):
            raise FileNotFoundError(f"Audio file '{self.audio_file}' not found.")
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(self.audio_file) as source:
                audio_data = recognizer.record(source)
                transcription = recognizer.recognize_google(audio_data)
                return transcription
        except Exception as e:
            raise RuntimeError(f"Error during audio transcription: {e}")

    def synthesize_speech(self, text: str, output_file: str):
        """Converts text to speech and saves it as an audio file."""
        try:
            tts = gTTS(text=text, lang='en')
            tts.save(output_file)
        except Exception as e:
            raise RuntimeError(f"Error during text-to-speech synthesis: {e}")

    def convert_audio_format(self, output_file: str, target_format: str):
        """Converts audio file to the specified format (e.g., mp3, wav)."""
        if not self.audio_file or not os.path.exists(self.audio_file):
            raise FileNotFoundError(f"Audio file '{self.audio_file}' not found.")
        try:
            audio = AudioSegment.from_file(self.audio_file)
            audio.export(output_file, format=target_format)
        except Exception as e:
            raise RuntimeError(f"Error during audio format conversion: {e}")

    def enhance_audio(self, output_file: str, gain_dB: float):
        """Enhances audio by applying a gain (in decibels)."""
        if not self.audio_file or not os.path.exists(self.audio_file):
            raise FileNotFoundError(f"Audio file '{self.audio_file}' not found.")
        try:
            audio = AudioSegment.from_file(self.audio_file)
            enhanced_audio = audio + gain_dB
            enhanced_audio.export(output_file, format="wav")
        except Exception as e:
            raise RuntimeError(f"Error during audio enhancement: {e}")

    def split_audio(self, chunk_duration_ms: int, output_dir: str):
        """Splits audio into smaller chunks of specified duration."""
        if not self.audio_file or not os.path.exists(self.audio_file):
            raise FileNotFoundError(f"Audio file '{self.audio_file}' not found.")
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            audio = AudioSegment.from_file(self.audio_file)
            for i, chunk in enumerate(audio[::chunk_duration_ms]):
                chunk.export(os.path.join(output_dir, f"chunk_{i}.wav"), format="wav")
        except Exception as e:
            raise RuntimeError(f"Error during audio splitting: {e}")


# Example Usage
if __name__ == "__main__":
    processor = AudioProcessing("example_audio.wav")

    # Transcribe audio
    transcription = processor.transcribe_audio()
    print(f"Transcription: {transcription}")

    # Synthesize speech
    processor.synthesize_speech("Hello, this is an audio synthesis example.", "output_speech.mp3")

    # Convert audio format
    processor.convert_audio_format("output_audio.mp3", "mp3")

    # Enhance audio
    processor.enhance_audio("enhanced_audio.wav", gain_dB=5.0)

    # Split audio into chunks of 10 seconds each
    processor.split_audio(chunk_duration_ms=10000, output_dir="audio_chunks")
