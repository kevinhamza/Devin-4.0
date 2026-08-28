"""
video_processing.py
--------------------
Provides video manipulation and editing capabilities, including cutting, merging, adding effects, and format conversion.
"""

import cv2
import moviepy.editor as mp
from pathlib import Path
import os

class VideoProcessing:
    def __init__(self, input_video: str):
        self.input_video = input_video
        self.output_video = None
        self.validate_input()

    def validate_input(self):
        if not Path(self.input_video).is_file():
            raise FileNotFoundError(f"Input video file '{self.input_video}' not found.")
        if not self.input_video.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
            raise ValueError("Unsupported video format. Supported formats: .mp4, .avi, .mkv, .mov")

    def trim_video(self, start_time: float, end_time: float, output_path: str):
        """Trims the video between specified start and end times."""
        try:
            video = mp.VideoFileClip(self.input_video).subclip(start_time, end_time)
            video.write_videofile(output_path, codec="libx264", audio_codec="aac")
            self.output_video = output_path
        except Exception as e:
            raise RuntimeError(f"Error during video trimming: {e}")

    def merge_videos(self, video_paths: list, output_path: str):
        """Merges a list of videos into one."""
        try:
            clips = [mp.VideoFileClip(vid) for vid in video_paths]
            final_clip = mp.concatenate_videoclips(clips)
            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
            self.output_video = output_path
        except Exception as e:
            raise RuntimeError(f"Error during video merging: {e}")

    def add_watermark(self, watermark_path: str, position: tuple, output_path: str):
        """Adds a watermark to the video at the specified position."""
        try:
            watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)
            cap = cv2.VideoCapture(self.input_video)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(output_path, fourcc, cap.get(cv2.CAP_PROP_FPS),
                                  (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                   int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                # Add watermark to frame
                overlay = frame.copy()
                h, w, _ = watermark.shape
                x, y = position
                overlay[y:y+h, x:x+w] = watermark
                out.write(overlay)

            cap.release()
            out.release()
            self.output_video = output_path
        except Exception as e:
            raise RuntimeError(f"Error during watermark addition: {e}")

    def convert_format(self, output_format: str, output_path: str):
        """Converts the video format to the specified format."""
        try:
            video = mp.VideoFileClip(self.input_video)
            video.write_videofile(output_path, codec="libx264", audio_codec="aac", preset=output_format)
            self.output_video = output_path
        except Exception as e:
            raise RuntimeError(f"Error during format conversion: {e}")

    def extract_frames(self, output_dir: str, frame_rate: int = 1):
        """Extracts frames from the video at the specified frame rate."""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            cap = cv2.VideoCapture(self.input_video)
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            count = 0
            frame_count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                if count % (fps // frame_rate) == 0:
                    frame_path = os.path.join(output_dir, f"frame_{frame_count}.jpg")
                    cv2.imwrite(frame_path, frame)
                    frame_count += 1
                count += 1
            cap.release()
        except Exception as e:
            raise RuntimeError(f"Error during frame extraction: {e}")

# Example Usage
if __name__ == "__main__":
    processor = VideoProcessing("example_video.mp4")
    processor.trim_video(10, 20, "trimmed_video.mp4")
    processor.merge_videos(["video1.mp4", "video2.mp4"], "merged_video.mp4")
    processor.add_watermark("watermark.png", (50, 50), "watermarked_video.mp4")
    processor.convert_format("mp4", "converted_video.mp4")
    processor.extract_frames("frames_output", frame_rate=1)
