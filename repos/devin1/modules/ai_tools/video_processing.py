"""
Video Processing Tools
======================
This module provides tools for video manipulation and editing using OpenCV and moviepy.
It supports video resizing, frame extraction, effects, and basic video editing.

Dependencies:
- OpenCV for video manipulation
- MoviePy for advanced video editing
- NumPy for array-based operations
"""

import cv2
import numpy as np
from moviepy.editor import VideoFileClip, concatenate_videoclips

class VideoProcessing:
    """
    A class to handle advanced video manipulation and editing tasks.
    """

    def __init__(self):
        """
        Initializes the VideoProcessing class.
        """
        self.default_codec = "XVID"
        self.default_fps = 30

    @staticmethod
    def load_video(file_path):
        """
        Loads a video file.

        Args:
            file_path (str): Path to the video file.

        Returns:
            VideoCapture: OpenCV VideoCapture object.
        """
        return cv2.VideoCapture(file_path)

    @staticmethod
    def save_video(frames, output_path, fps=30, frame_size=(640, 480), codec="XVID"):
        """
        Saves video frames to a file.

        Args:
            frames (list): List of video frames.
            output_path (str): Path to save the video.
            fps (int): Frames per second (default: 30).
            frame_size (tuple): Size of video frames (width, height).
            codec (str): FourCC codec (default: 'XVID').
        """
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(output_path, fourcc, fps, frame_size)
        for frame in frames:
            out.write(frame)
        out.release()

    def resize_video(self, input_path, output_path, width, height):
        """
        Resizes a video to specified dimensions.

        Args:
            input_path (str): Path to the input video file.
            output_path (str): Path to save the resized video.
            width (int): Desired width.
            height (int): Desired height.
        """
        cap = self.load_video(input_path)
        frame_size = (width, height)
        frames = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            resized_frame = cv2.resize(frame, frame_size)
            frames.append(resized_frame)

        cap.release()
        self.save_video(frames, output_path, frame_size=frame_size)

    def extract_frames(self, video_path, output_dir, frame_interval=1):
        """
        Extracts frames from a video at regular intervals.

        Args:
            video_path (str): Path to the video file.
            output_dir (str): Directory to save extracted frames.
            frame_interval (int): Interval between frames to save (default: 1).
        """
        cap = self.load_video(video_path)
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % frame_interval == 0:
                frame_path = f"{output_dir}/frame_{frame_count:04d}.jpg"
                cv2.imwrite(frame_path, frame)
            frame_count += 1

        cap.release()

    def add_effect(self, input_path, output_path, effect="grayscale"):
        """
        Applies an effect to the entire video.

        Args:
            input_path (str): Path to the input video file.
            output_path (str): Path to save the processed video.
            effect (str): Type of effect ('grayscale', 'negative').

        Returns:
            None
        """
        cap = self.load_video(input_path)
        frames = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if effect == "grayscale":
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif effect == "negative":
                frame = cv2.bitwise_not(frame)
            frames.append(frame)

        cap.release()
        self.save_video(frames, output_path, frame_size=(frame.shape[1], frame.shape[0]))

    def merge_videos(self, video_paths, output_path):
        """
        Merges multiple videos into one.

        Args:
            video_paths (list): List of video file paths to merge.
            output_path (str): Path to save the merged video.
        """
        clips = [VideoFileClip(video) for video in video_paths]
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(output_path, codec="libx264", fps=self.default_fps)

    def overlay_text(self, input_path, output_path, text, position=(50, 50), font_scale=1, color=(0, 255, 0)):
        """
        Overlays text onto a video.

        Args:
            input_path (str): Path to the input video file.
            output_path (str): Path to save the processed video.
            text (str): Text to overlay.
            position (tuple): Position of the text (x, y).
            font_scale (float): Font scale.
            color (tuple): Text color (B, G, R).
        """
        cap = self.load_video(input_path)
        frames = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)
            frames.append(frame)

        cap.release()
        self.save_video(frames, output_path, frame_size=(frame.shape[1], frame.shape[0]))

# Example usage
if __name__ == "__main__":
    video_processor = VideoProcessing()
    input_video = "input.mp4"

    # Resize video
    video_processor.resize_video(input_video, "resized.mp4", 640, 360)

    # Extract frames
    video_processor.extract_frames(input_video, "frames", frame_interval=30)

    # Add effects
    video_processor.add_effect(input_video, "grayscale.mp4", effect="grayscale")
    video_processor.add_effect(input_video, "negative.mp4", effect="negative")

    # Merge videos
    video_processor.merge_videos(["resized.mp4", "grayscale.mp4"], "merged.mp4")

    # Overlay text
    video_processor.overlay_text(input_video, "text_overlay.mp4", "Sample Text", position=(100, 100))
