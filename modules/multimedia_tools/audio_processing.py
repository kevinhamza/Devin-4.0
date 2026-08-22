# Devin/modules/multimedia_tools/audio_processing.py
# Purpose: A toolkit for audio processing, including manipulation, format
#          conversion, and multi-engine speech-to-text/text-to-speech.

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from pydub import AudioSegment
    # A check for FFMPEG/FFPROBE can be implicitly done by pydub's internals
    # but we will rely on user installation.
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("AudioProcessor")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class AudioProcessor:
    """
    Provides a suite of tools for audio analysis and manipulation.
    """
    def __init__(self, audio_path: Optional[Path] = None, openai_api_key: Optional[str] = None):
        if not PYDUB_AVAILABLE:
            raise ImportError("Pydub is required. 'pip install pydub'")
        
        self.audio_path = audio_path
        self.audio: Optional[AudioSegment] = None
        
        if self.audio_path and self.audio_path.is_file():
            self._load_audio()

        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

    def _load_audio(self):
        """Loads the audio from the specified path."""
        try:
            self.audio = AudioSegment.from_file(self.audio_path)
            logger.info(f"Audio loaded from {self.audio_path}")
        except Exception as e:
            logger.error(f"Failed to load audio file. Is FFMPEG installed? Error: {e}")
            self.audio = None
            
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Returns key metadata from the loaded audio file."""
        if not self.audio: return None
        return {
            "duration_seconds": self.audio.duration_seconds,
            "channels": self.audio.channels,
            "sample_width_bytes": self.audio.sample_width,
            "frame_rate_hz": self.audio.frame_rate,
            "max_amplitude": self.audio.max
        }

    def convert_format(self, output_path: Path, format: str = "mp3"):
        """Converts the audio to a different format."""
        if not self.audio: return False
        logger.info(f"Converting audio to '{format}' format at {output_path}...")
        try:
            self.audio.export(output_path, format=format)
            return True
        except Exception as e:
            logger.error(f"Format conversion failed: {e}")
            return False

    def transcribe_audio(self, engine: str = 'google') -> Optional[str]:
        """
        Transcribes the audio using a specified engine ('whisper' or 'google').
        """
        if not self.audio_path: return None
        
        if engine == 'whisper':
            if not self.openai_client:
                logger.error("OpenAI client not configured. Cannot use 'whisper' engine.")
                return None
            try:
                with open(self.audio_path, "rb") as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                return transcript.text
            except Exception as e:
                logger.error(f"Whisper transcription failed: {e}")
                return None

        elif engine == 'google':
            if not SPEECH_RECOGNITION_AVAILABLE:
                logger.error("SpeechRecognition library not installed. Cannot use 'google' engine.")
                return None
            
            recognizer = sr.Recognizer()
            try:
                # The library needs a file path, so we ensure it's saved first
                with sr.AudioFile(str(self.audio_path)) as source:
                    audio_data = recognizer.record(source)
                return recognizer.recognize_google(audio_data)
            except Exception as e:
                logger.error(f"Google Web Speech transcription failed: {e}")
                return None
        else:
            raise ValueError("Unsupported transcription engine. Choose 'whisper' or 'google'.")

    @staticmethod
    def text_to_speech(text: str, output_path: Path, lang: str = 'en'):
        """Generates a spoken audio file from text using gTTS."""
        if not GTTS_AVAILABLE:
            raise ImportError("gTTS library not installed. 'pip install gTTS'")
        logger.info(f"Generating speech from text to '{output_path}'...")
        try:
            tts = gTTS(text=text, lang=lang)
            tts.save(str(output_path))
            return True
        except Exception as e:
            logger.error(f"Text-to-speech generation failed: {e}")
            return False


# --- Example Usage ---
if __name__ == "__main__":
    # Check for all dependencies first
    if not all([PYDUB_AVAILABLE, SPEECH_RECOGNITION_AVAILABLE, GTTS_AVAILABLE]):
        print("ERROR: Missing one or more required libraries. Please run:")
        print("pip install pydub SpeechRecognition gTTS")
        sys.exit(1)

    print("=========================================================")
    print("=== Multimedia Audio Processing Prototype 🔊🎤 ===")
    print("=========================================================")
    
    demo_audio_path = Path("demo_tts_audio.mp3")
    
    # --- 1. Text-to-Speech Demo ---
    print("\n--- 1. Generating Speech from Text ---")
    test_phrase = "Devin project audio test successful."
    if AudioProcessor.text_to_speech(test_phrase, demo_audio_path):
        print(f"Generated audio file: {demo_audio_path}")
        
        processor = None
        try:
            # 2. Initialize processor with the generated file
            processor = AudioProcessor(audio_path=demo_audio_path)
            
            # --- 2. Metadata Demo ---
            print("\n--- 2. Extracting Audio Metadata ---")
            metadata = processor.get_metadata()
            if metadata:
                print(json.dumps(metadata, indent=2))

            # --- 3. Transcription Demo ---
            print("\n--- 3. Transcribing Audio with Google Web Speech API ---")
            # Using 'google' for the demo as it doesn't require a paid API key.
            transcription = processor.transcribe_audio(engine='google')
            if transcription:
                print(f"Original Text:    '{test_phrase}'")
                print(f"Transcribed Text: '{transcription}'")
                # A simple check for demo success
                if test_phrase.lower().strip('.') == transcription.lower():
                    print("SUCCESS: Transcription matches original text!")
        finally:
            # --- 4. Clean up ---
            if demo_audio_path.exists():
                demo_audio_path.unlink()
                logger.info("Cleaned up demo audio file.")

    print("\n=========================================================")
    print("=== Audio Processing Prototype Complete ===")
    print("=========================================================")
