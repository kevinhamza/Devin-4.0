# Devin/modules/multimedia_tools/speech_recognition.py
# Purpose: A tool for real-time speech recognition from a microphone,
#          enabling voice command input for Devin.

import logging
import os
import sys
import tempfile
import wave
from typing import Optional

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    # PyAudio is a critical dependency for microphone access
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("SpeechRecognizer")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class LiveSpeechRecognizer:
    """
    Captures and transcribes audio from a live microphone feed.
    """
    def __init__(self, openai_api_key: Optional[str] = None):
        if not SPEECH_RECOGNITION_AVAILABLE or not PYAUDIO_AVAILABLE:
            logger.warning("SpeechRecognition and PyAudio are required for voice input.")
            self.recognizer = None
            self.microphone = None
        else:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()

        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            try:
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            except Exception:
                self.openai_client = None
        else:
            self.openai_client = None

    def _transcribe_with_whisper(self, audio_data) -> Optional[str]:
        """Saves audio data to a temp file and sends it to Whisper API."""
        if not self.openai_client:
            logger.error("OpenAI client not configured. Cannot use 'whisper' engine.")
            return None
        
        try:
            # Create a temporary WAV file to send to the API
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio_file:
                wav_data = audio_data.get_wav_data()
                tmp_audio_file.write(wav_data)
                tmp_audio_path = tmp_audio_file.name

            with open(tmp_audio_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            os.remove(tmp_audio_path) # Clean up the temporary file
            return transcript.text
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            if 'tmp_audio_path' in locals() and os.path.exists(tmp_audio_path):
                os.remove(tmp_audio_path)
            return None

    def listen_and_transcribe(self, engine: str = 'google', phrase_time_limit: int = 10) -> Optional[str]:
        """
        Listens for a single phrase from the microphone and transcribes it.
        """
        with self.microphone as source:
            logger.info("Calibrating for ambient noise... Please be quiet.")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Listening for command...")
            
            try:
                audio = self.recognizer.listen(source, phrase_time_limit=phrase_time_limit)
                logger.info("Audio captured, now transcribing...")

                if engine == 'google':
                    text = self.recognizer.recognize_google(audio)
                    return text
                elif engine == 'whisper':
                    return self._transcribe_with_whisper(audio)
                else:
                    logger.error(f"Unsupported engine: {engine}. Choose 'google' or 'whisper'.")
                    return None

            except sr.UnknownValueError:
                logger.warning("Could not understand the audio. Please try again.")
                return None
            except sr.RequestError as e:
                logger.error(f"API request failed for engine '{engine}': {e}")
                return None
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
                return None

# --- Example Usage ---
if __name__ == "__main__":
    if not all([SPEECH_RECOGNITION_AVAILABLE, PYAUDIO_AVAILABLE]):
        print("\nERROR: Missing one or more required libraries. Please run:")
        print("pip install SpeechRecognition PyAudio")
        sys.exit(1)

    print("=========================================================")
    print("=== Live Speech Recognition Prototype 🎙️➡️📄 ===")
    print("=========================================================")
    print("This demo will listen for your voice via your default microphone.")

    try:
        recognizer = LiveSpeechRecognizer()
        
        while True:
            input("\nPress Enter to start listening for a command (or Ctrl+C to exit)...")
            
            # Use Google's engine for a quick, free demo
            transcribed_text = recognizer.listen_and_transcribe(engine='google')
            
            if transcribed_text:
                print(f"\nI heard you say: '{transcribed_text}'")
                if transcribed_text.lower() in ['exit', 'quit', 'stop']:
                    print("Exiting demo...")
                    break
            else:
                print("No text was recognized.")

    except (ImportError, ValueError) as e:
        logger.error(f"Initialization failed: {e}")
    except (KeyboardInterrupt, EOFError):
        print("\nDemo stopped by user.")


    print("\n=========================================================")
    print("=== Speech Recognition Prototype Complete ===")
    print("=========================================================")
