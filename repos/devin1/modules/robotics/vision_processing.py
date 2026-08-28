"""
Vision Processing Module
=========================
Handles advanced AI-based vision tasks for robotics, including object classification,
scene understanding, and visual mapping.
"""

import cv2
import numpy as np
import logging
from tensorflow.keras.models import load_model
from modules.robotics.object_detection import ObjectDetector
from modules.utils.ai_memory import MemoryManager


class VisionConfig:
    def __init__(self, model_path: str, input_size: tuple = (224, 224)):
        """
        Configuration for the Vision Processing module.

        Args:
            model_path (str): Path to the pre-trained AI model.
            input_size (tuple): Input size for the AI model (width, height).
        """
        self.model_path = model_path
        self.input_size = input_size


class VisionProcessor:
    def __init__(self, config: VisionConfig):
        """
        Initializes the Vision Processing module.

        Args:
            config (VisionConfig): Vision configuration.
        """
        logging.info("Initializing Vision Processing Module...")
        self.config = config
        self.model = self.load_vision_model(config.model_path)
        self.object_detector = ObjectDetector()
        self.memory = MemoryManager()

    @staticmethod
    def load_vision_model(model_path: str):
        """
        Loads the pre-trained AI model for vision processing.

        Args:
            model_path (str): Path to the model.

        Returns:
            Model: Loaded AI model.
        """
        try:
            logging.info(f"Loading vision model from {model_path}...")
            model = load_model(model_path)
            logging.info("Vision model loaded successfully.")
            return model
        except Exception as e:
            logging.error(f"Error loading vision model: {e}")
            raise e

    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocesses a video frame for AI inference.

        Args:
            frame (np.ndarray): Input video frame.

        Returns:
            np.ndarray: Preprocessed frame.
        """
        try:
            logging.info("Preprocessing video frame...")
            resized_frame = cv2.resize(frame, self.config.input_size)
            normalized_frame = resized_frame / 255.0
            return np.expand_dims(normalized_frame, axis=0)
        except Exception as e:
            logging.error(f"Error preprocessing frame: {e}")
            raise e

    def classify_scene(self, frame: np.ndarray) -> str:
        """
        Classifies the current scene based on input video frame.

        Args:
            frame (np.ndarray): Input video frame.

        Returns:
            str: Classification label.
        """
        try:
            preprocessed_frame = self.preprocess_frame(frame)
            predictions = self.model.predict(preprocessed_frame)
            label = np.argmax(predictions, axis=1)[0]
            logging.info(f"Scene classified as: {label}")
            self.memory.save_vision_log({"frame": frame, "label": label})
            return label
        except Exception as e:
            logging.error(f"Error classifying scene: {e}")
            return "Unknown"

    def process_frame(self, frame: np.ndarray) -> dict:
        """
        Processes a frame for object detection and scene classification.

        Args:
            frame (np.ndarray): Input video frame.

        Returns:
            dict: Detected objects and scene classification.
        """
        try:
            logging.info("Processing video frame...")
            objects = self.object_detector.detect_objects(frame)
            scene_label = self.classify_scene(frame)
            logging.info(f"Processed frame: {len(objects)} objects detected, Scene: {scene_label}")
            return {"objects": objects, "scene": scene_label}
        except Exception as e:
            logging.error(f"Error processing frame: {e}")
            return {"error": str(e)}

    def stream_processing(self, video_source: int = 0):
        """
        Streams video input and processes frames in real-time.

        Args:
            video_source (int): Video source ID (default is 0 for webcam).
        """
        logging.info("Starting video stream for vision processing...")
        cap = cv2.VideoCapture(video_source)
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    logging.warning("Failed to retrieve video frame. Ending stream.")
                    break

                processed_data = self.process_frame(frame)
                logging.info(f"Real-time processed data: {processed_data}")

                # Display processed frame (with detected objects and scene info)
                display_frame = self.object_detector.annotate_frame(frame, processed_data["objects"])
                cv2.imshow("Vision Processing", display_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logging.info("Stream ended by user.")
                    break
        except Exception as e:
            logging.error(f"Error during video streaming: {e}")
        finally:
            cap.release()
            cv2.destroyAllWindows()


# Example Usage
if __name__ == "__main__":
    config = VisionConfig(model_path="models/vision_model.h5", input_size=(224, 224))
    vision_processor = VisionProcessor(config)

    try:
        vision_processor.stream_processing()
    except KeyboardInterrupt:
        logging.info("Vision processing terminated by user.")
