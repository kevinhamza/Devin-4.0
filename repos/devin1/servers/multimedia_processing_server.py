# servers/multimedia_processing_server.py

import os
import logging
from PIL import Image
import numpy as np
import cv2
import pydub

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Function to process images
def process_image(image_path, output_path):
    try:
        # Load the image
        image = Image.open(image_path)
        # Resize image
        image = image.resize((800, 600))
        # Save processed image
        image.save(output_path)
        logging.info(f"Image processed: {output_path}")
        return "Image processed successfully"
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        return "Error processing image"

# Function to process audio
def process_audio(audio_path, output_path):
    try:
        # Load audio
        audio = pydub.AudioSegment.from_file(audio_path)
        # Set the frame rate to 22050 Hz
        audio = audio.set_frame_rate(22050)
        # Export processed audio
        audio.export(output_path, format="wav")
        logging.info(f"Audio processed: {output_path}")
        return "Audio processed successfully"
    except Exception as e:
        logging.error(f"Error processing audio: {e}")
        return "Error processing audio"

# Function to process video
def process_video(video_path, output_path, format='avi'):
    try:
        # Capture video
        cap = cv2.VideoCapture(video_path)
        # Get video frame rate
        frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
        # Get video resolution
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # Define codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_path, fourcc, frame_rate, (width, height))
        while(cap.isOpened()):
            ret, frame = cap.read()
            if ret:
                # Write the frame
                out.write(frame)
            else:
                break
        cap.release()
        out.release()
        logging.info(f"Video processed: {output_path}")
        return "Video processed successfully"
    except Exception as e:
        logging.error(f"Error processing video: {e}")
        return "Error processing video"

# Main function to handle multimedia tasks
def handle_multimedia_task(task_type, *args):
    try:
        if task_type == "image":
            return process_image(*args)
        elif task_type == "audio":
            return process_audio(*args)
        elif task_type == "video":
            return process_video(*args)
        else:
            return "Unknown multimedia task"
    except Exception as e:
        logging.error(f"Error handling multimedia task: {e}")
        return "Error handling task"

if __name__ == "__main__":
    # Example usage
    task_type = "image"
    input_file = "path/to/image.jpg"
    output_file = "path/to/processed_image.jpg"
    print(handle_multimedia_task(task_type, input_file, output_file))

    task_type = "audio"
    input_file = "path/to/audio.mp3"
    output_file = "path/to/processed_audio.wav"
    print(handle_multimedia_task(task_type, input_file, output_file))

    task_type = "video"
    input_file = "path/to/video.mp4"
    output_file = "path/to/processed_video.avi"
    print(handle_multimedia_task(task_type, input_file, output_file))
