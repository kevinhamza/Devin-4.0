"""
Multimedia Processing Module
============================
Handles audio, video, and image processing tasks, providing APIs for real-time multimedia manipulation and analysis.
"""

import os
import cv2
import numpy as np
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, concatenate_videoclips
from PIL import Image, ImageEnhance

class MultimediaProcessingModule:
    """
    MultimediaProcessingModule provides tools to handle and process audio, video, and image files.
    """
    
    def __init__(self):
        print("[INFO] Multimedia Processing Module initialized.")

    # --------------------------- AUDIO PROCESSING --------------------------- #

    def merge_audio(self, audio_files, output_path):
        """
        Merges multiple audio files into one.

        Args:
            audio_files (list): List of audio file paths.
            output_path (str): Path for the merged output file.

        Returns:
            str: Path to the merged audio file.
        """
        combined_audio = AudioSegment.empty()
        for file in audio_files:
            audio = AudioSegment.from_file(file)
            combined_audio += audio
        combined_audio.export(output_path, format="mp3")
        print(f"[INFO] Merged audio saved at: {output_path}")
        return output_path

    def change_audio_speed(self, file_path, speed_factor, output_path):
        """
        Changes the speed of an audio file.

        Args:
            file_path (str): Path to the audio file.
            speed_factor (float): Speed factor (e.g., 1.5 for 1.5x speed).
            output_path (str): Path for the processed output file.

        Returns:
            str: Path to the adjusted audio file.
        """
        audio = AudioSegment.from_file(file_path)
        adjusted_audio = audio.speedup(playback_speed=speed_factor)
        adjusted_audio.export(output_path, format="mp3")
        print(f"[INFO] Adjusted audio saved at: {output_path}")
        return output_path

    # --------------------------- VIDEO PROCESSING --------------------------- #

    def merge_videos(self, video_files, output_path):
        """
        Merges multiple video files into one.

        Args:
            video_files (list): List of video file paths.
            output_path (str): Path for the merged output file.

        Returns:
            str: Path to the merged video file.
        """
        clips = [VideoFileClip(video) for video in video_files]
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(output_path, codec="libx264")
        print(f"[INFO] Merged video saved at: {output_path}")
        return output_path

    def extract_frames(self, video_path, output_folder, frame_rate=1):
        """
        Extracts frames from a video at the specified frame rate.

        Args:
            video_path (str): Path to the video file.
            output_folder (str): Folder to save the extracted frames.
            frame_rate (int): Number of frames to extract per second.

        Returns:
            list: List of file paths for the extracted frames.
        """
        os.makedirs(output_folder, exist_ok=True)
        video = cv2.VideoCapture(video_path)
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps / frame_rate)
        frame_count = 0
        saved_frames = []

        while True:
            success, frame = video.read()
            if not success:
                break
            if frame_count % frame_interval == 0:
                frame_file = os.path.join(output_folder, f"frame_{frame_count}.jpg")
                cv2.imwrite(frame_file, frame)
                saved_frames.append(frame_file)
            frame_count += 1
        video.release()
        print(f"[INFO] Extracted frames saved in: {output_folder}")
        return saved_frames

    # --------------------------- IMAGE PROCESSING --------------------------- #

    def enhance_image(self, image_path, output_path, enhancement_type="brightness", factor=1.2):
        """
        Enhances an image by adjusting brightness, contrast, or sharpness.

        Args:
            image_path (str): Path to the input image.
            output_path (str): Path to save the enhanced image.
            enhancement_type (str): Type of enhancement ("brightness", "contrast", "sharpness").
            factor (float): Enhancement factor (e.g., 1.2 for 20% increase).

        Returns:
            str: Path to the enhanced image.
        """
        image = Image.open(image_path)
        if enhancement_type == "brightness":
            enhancer = ImageEnhance.Brightness(image)
        elif enhancement_type == "contrast":
            enhancer = ImageEnhance.Contrast(image)
        elif enhancement_type == "sharpness":
            enhancer = ImageEnhance.Sharpness(image)
        else:
            raise ValueError("Invalid enhancement_type. Choose 'brightness', 'contrast', or 'sharpness'.")
        enhanced_image = enhancer.enhance(factor)
        enhanced_image.save(output_path)
        print(f"[INFO] Enhanced image saved at: {output_path}")
        return output_path

    def resize_image(self, image_path, output_path, width, height):
        """
        Resizes an image to the specified dimensions.

        Args:
            image_path (str): Path to the input image.
            output_path (str): Path to save the resized image.
            width (int): Desired width.
            height (int): Desired height.

        Returns:
            str: Path to the resized image.
        """
        image = Image.open(image_path)
        resized_image = image.resize((width, height))
        resized_image.save(output_path)
        print(f"[INFO] Resized image saved at: {output_path}")
        return output_path
