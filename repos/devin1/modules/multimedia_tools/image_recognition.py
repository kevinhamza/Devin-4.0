"""
modules/multimedia_tools/image_recognition.py
----------------------------------------------
This module provides advanced image recognition capabilities, including object detection,
scene understanding, and image classification. It integrates with machine learning models
to enable accurate and efficient processing of visual data.
"""

import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from typing import List, Dict

# Define constants
MODEL_PATH = "models/image_recognition_model.h5"
LABELS_PATH = "models/image_labels.txt"

class ImageRecognition:
    """
    Class to perform image recognition tasks, including object detection and classification.
    """

    def __init__(self, model_path: str = MODEL_PATH, labels_path: str = LABELS_PATH):
        """
        Initialize the ImageRecognition module.

        :param model_path: Path to the pre-trained image recognition model.
        :param labels_path: Path to the label file containing class names.
        """
        self.model_path = model_path
        self.labels_path = labels_path
        self.model = self.load_model()
        self.labels = self.load_labels()

    def load_model(self) -> tf.keras.Model:
        """
        Load the pre-trained model for image recognition.

        :return: Loaded TensorFlow model.
        """
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        return load_model(self.model_path)

    def load_labels(self) -> List[str]:
        """
        Load the labels for the image recognition model.

        :return: List of class labels.
        """
        if not os.path.exists(self.labels_path):
            raise FileNotFoundError(f"Labels file not found: {self.labels_path}")
        with open(self.labels_path, 'r') as file:
            return [line.strip() for line in file.readlines()]

    def preprocess_image(self, image_path: str, target_size: tuple = (224, 224)) -> np.ndarray:
        """
        Preprocess the input image for recognition.

        :param image_path: Path to the input image.
        :param target_size: Target size for resizing the image.
        :return: Preprocessed image as a NumPy array.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, target_size)
        image = image / 255.0
        return np.expand_dims(image, axis=0)

    def recognize_image(self, image_path: str) -> Dict[str, float]:
        """
        Recognize objects or scenes in the given image.

        :param image_path: Path to the input image.
        :return: Dictionary with class labels and their probabilities.
        """
        preprocessed_image = self.preprocess_image(image_path)
        predictions = self.model.predict(preprocessed_image)[0]
        return {self.labels[i]: float(predictions[i]) for i in range(len(predictions))}

    def get_top_predictions(self, predictions: Dict[str, float], top_k: int = 5) -> Dict[str, float]:
        """
        Get the top-k predictions from the recognition results.

        :param predictions: Dictionary with class labels and their probabilities.
        :param top_k: Number of top predictions to return.
        :return: Dictionary with top-k class labels and their probabilities.
        """
        return dict(sorted(predictions.items(), key=lambda item: item[1], reverse=True)[:top_k])

# Example usage
if __name__ == "__main__":
    # Initialize the ImageRecognition class
    recognizer = ImageRecognition()

    # Path to the input image
    image_path = "sample_images/test_image.jpg"

    # Recognize the image
    try:
        results = recognizer.recognize_image(image_path)
        top_results = recognizer.get_top_predictions(results)
        print("Top Predictions:")
        for label, probability in top_results.items():
            print(f"{label}: {probability * 100:.2f}%")
    except FileNotFoundError as e:
        print(e)
