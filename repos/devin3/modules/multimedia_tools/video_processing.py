# Devin/modules/multimedia_tools/video_processing.py
# Purpose: A toolkit for video processing, including frame/audio extraction,
#          metadata analysis, and AI-powered transcription.

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import moviepy.editor as mp
    # Check for FFMPEG on import
    from moviepy.config import get_setting
    get_setting("FFMPEG_BINARY")
    MOVIEPY_AVAILABLE = True
except (ImportError, KeyError):
    MOVIEPY_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("VideoProcessor")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class VideoProcessor:
    """
    Provides a suite of tools for video analysis and manipulation.
    """
    def __init__(self, video_path: Path, openai_api_key: Optional[str] = None):
        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy is required and/or FFMPEG is not found. 'pip install moviepy' and ensure FFMPEG is in your system's PATH.")
        
        self.video_path = video_path
        self.clip: Optional[mp.VideoFileClip] = None
        
        if self.video_path.is_file():
            self._load_video()
        
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

    def _load_video(self):
        """Loads the video file using moviepy."""
        try:
            self.clip = mp.VideoFileClip(str(self.video_path))
            logger.info(f"Video loaded from {self.video_path}")
        except Exception as e:
            logger.error(f"Failed to load video file: {e}")
            self.clip = None

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Returns key metadata from the loaded video file."""
        if not self.clip: return None
        
        return {
            "duration_seconds": self.clip.duration,
            "fps": self.clip.fps,
            "resolution": self.clip.size, # [width, height]
            "codec": self.clip.reader.iformat
        }

    def extract_frames(self, output_dir: Path, interval_sec: int = 1):
        """
        Extracts frames from the video at a given interval.
        """
        if not self.clip: return False
        logger.info(f"Extracting frames every {interval_sec} second(s) to '{output_dir}'...")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            for i, frame in enumerate(self.clip.iter_frames(fps=1/interval_sec)):
                frame_path = output_dir / f"frame_{i:04d}.png"
                # moviepy frames are numpy arrays, need to convert to Image
                img = mp.Image.fromarray(frame)
                img.save(frame_path)
            logger.info("Frame extraction complete.")
            return True
        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
            return False

    def extract_audio(self, output_path: Path) -> bool:
        """Extracts the audio track from the video and saves it."""
        if not self.clip or not self.clip.audio:
            logger.warning("No audio track found in the video.")
            return False
        
        logger.info(f"Extracting audio to '{output_path}'...")
        try:
            self.clip.audio.write_audiofile(str(output_path))
            logger.info("Audio extraction complete.")
            return True
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return False

    def transcribe_audio_ai(self, audio_path: Path) -> Optional[str]:
        """Sends an extracted audio file to OpenAI's Whisper for transcription."""
        if not self.openai_client:
            logger.error("OpenAI client not initialized. Cannot transcribe audio.")
            return None
        if not audio_path.is_file():
            logger.error(f"Audio file not found: {audio_path}")
            return None
            
        logger.warning("Transcribing audio with Whisper API. This may take a moment...")
        try:
            with open(audio_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            logger.info("Transcription complete.")
            return transcript.text
        except Exception as e:
            logger.error(f"AI transcription failed: {e}")
            return None
            
    def close(self):
        """Closes the video clip to release file handles."""
        if self.clip:
            self.clip.close()

# --- Example Usage ---
if __name__ == "__main__":
    import numpy as np
    
    # Check for all dependencies first
    if not MOVIEPY_AVAILABLE:
        print("\nERROR: MoviePy library not found or FFMPEG is not configured.")
        print("Please run 'pip install moviepy' and ensure FFMPEG is installed and accessible.")
        sys.exit(1)
    if not OPENAI_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        print("\nWARNING: OpenAI library not installed or API key not set. Transcription will be skipped.")

    print("=========================================================")
    print("=== Multimedia Video Processing Prototype 🎬🎵 ===")
    print("=========================================================")
    
    # 1. Create a dummy video with audio for the demo
    demo_video_path = Path("demo_video.mp4")
    audio_output_path = Path("demo_audio.mp3")
    frames_output_dir = Path("./demo_frames")
    
    # Create a simple 5-second color-changing video clip
    duration = 5
    make_frame = lambda t: np.array([
        (int(255 * (t/duration)), int(255 * (1-t/duration)), 0)
        for y in range(150) for x in range(200)
    ]).reshape((150, 200, 3)).astype(np.uint8)
    
    clip = mp.VideoClip(make_frame, duration=duration)
    # Create a simple sine wave audio tone
    audio = mp.AudioClip(lambda t: np.sin(440 * 2 * np.pi * t), duration=duration, fps=44100)
    clip = clip.set_audio(audio)
    clip.write_videofile(str(demo_video_path), fps=24, codec='libx264', audio_codec='aac')
    logger.info(f"Created demo video at {demo_video_path}")

    processor = None
    try:
        # 2. Run the processing tools
        processor = VideoProcessor(video_path=demo_video_path)
        
        # Metadata Demo
        print("\n--- Extracting Video Metadata ---")
        metadata = processor.get_metadata()
        if metadata:
            print(json.dumps(metadata, indent=2))
            
        # Frame Extraction Demo
        print("\n--- Extracting Video Frames (1 per second) ---")
        processor.extract_frames(output_dir=frames_output_dir, interval_sec=1)
        if frames_output_dir.exists():
            print(f"Frames saved to '{frames_output_dir}' directory.")
        
        # Audio Extraction & Transcription Demo
        print("\n--- Extracting & Transcribing Audio ---")
        if processor.extract_audio(audio_output_path):
            # Because our audio is just a tone, Whisper will likely return nothing or gibberish.
            # This still demonstrates the full workflow is functional.
            transcription = processor.transcribe_audio_ai(audio_output_path)
            if transcription is not None:
                print(f"AI Transcription Result: '{transcription}' (Note: may be empty for a simple tone)")
            
    finally:
        # 3. Clean up
        if processor: processor.close()
        if demo_video_path.exists(): demo_video_path.unlink()
        if audio_output_path.exists(): audio_output_path.unlink()
        if frames_output_dir.exists():
            import shutil
            shutil.rmtree(frames_output_dir)
        logger.info("Cleaned up demo files.")


    print("\n=========================================================")
    print("=== Video Processing Prototype Complete ===")
    print("=========================================================")
