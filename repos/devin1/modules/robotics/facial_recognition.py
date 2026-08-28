"""
Facial Recognition Module
==========================
Real-time face detection and recognition for robotics applications.
"""

import cv2
import numpy as np
import face_recognition
import logging
from modules.utils.ai_memory import MemoryManager


class FacialRecognitionConfig:
    def __init__(self, detection_model: str = "hog", tolerance: float = 0.6):
        """
        Configuration for facial recognition.

        Args:
            detection_model (str): Model for face detection ('hog' or 'cnn').
            tolerance (float): Tolerance for face recognition matching.
        """
        self.detection_model = detection_model
        self.tolerance = tolerance


class FacialRecognition:
    def __init__(self, config: FacialRecognitionConfig):
        """
        Initializes the facial recognition module with the given configuration.

        Args:
            config (FacialRecognitionConfig): Configuration for facial recognition.
        """
        logging.info("Initializing Facial Recognition Module...")
        self.config = config
        self.known_face_encodings = []
        self.known_face_names = []
        self.memory = MemoryManager()

    def load_known_faces(self, face_data: dict):
        """
        Loads known faces and their encodings.

        Args:
            face_data (dict): A dictionary where keys are names and values are image paths.
        """
        logging.info("Loading known faces...")
        for name, image_path in face_data.items():
            logging.info(f"Encoding face for: {name}")
            image = face_recognition.load_image_file(image_path)
            encoding = face_recognition.face_encodings(image)[0]
            self.known_face_encodings.append(encoding)
            self.known_face_names.append(name)

    def recognize_faces(self, frame: np.ndarray) -> list:
        """
        Detects and recognizes faces in a given video frame.

        Args:
            frame (np.ndarray): Input video frame.

        Returns:
            list: List of recognized faces with their names and locations.
        """
        logging.info("Recognizing faces in frame...")
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model=self.config.detection_model)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        recognized_faces = []
        for encoding, location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(self.known_face_encodings, encoding, self.config.tolerance)
            name = "Unknown"

            if True in matches:
                match_index = matches.index(True)
                name = self.known_face_names[match_index]

            recognized_faces.append({"name": name, "location": location})
            self.memory.save_recognition_result({"name": name, "location": location})
            logging.info(f"Recognized: {name}")

        return recognized_faces

    @staticmethod
    def draw_faces(frame: np.ndarray, recognized_faces: list) -> np.ndarray:
        """
        Draws recognized faces and their names on the video frame.

        Args:
            frame (np.ndarray): Original video frame.
            recognized_faces (list): List of recognized faces with names and locations.

        Returns:
            np.ndarray: Frame with faces and names drawn.
        """
        logging.info("Drawing recognized faces on frame...")
        for face in recognized_faces:
            top, right, bottom, left = face["location"]
            name = face["name"]

            # Draw rectangle around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            # Draw label below the rectangle
            cv2.putText(frame, name, (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return frame


# Example Usage
if __name__ == "__main__":
    config = FacialRecognitionConfig(detection_model="hog", tolerance=0.6)
    facial_recognizer = FacialRecognition(config)

    # Load known faces
    known_faces = {
        "Alice": "alice.jpg",
        "Bob": "bob.jpg"
    }
    facial_recognizer.load_known_faces(known_faces)

    # Initialize webcam
    video_capture = cv2.VideoCapture(0)
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        # Recognize faces in the frame
        recognized_faces = facial_recognizer.recognize_faces(frame)

        # Draw faces on the frame
        output_frame = facial_recognizer.draw_faces(frame, recognized_faces)

        # Display the frame
        cv2.imshow("Facial Recognition", output_frame)

        # Break on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video_capture.release()
    cv2.destroyAllWindows()
