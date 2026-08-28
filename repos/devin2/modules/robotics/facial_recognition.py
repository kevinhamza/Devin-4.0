# # Devin/modules/robotics/facial_recognition.py
# # Purpose: Provides facial recognition capabilities, including finding faces in
# #          images and identifying them against a database of known individuals.

# import logging
# import os
# from dataclasses import dataclass
# from typing import List, Tuple, Dict, Optional
# import pickle

# # --- Dependency Installation Notes ---
# # This module requires several powerful libraries. Installation can be complex.
# #
# # 1. OpenCV: For image processing.
# #    pip install opencv-python
# #
# # 2. NumPy: For numerical operations.
# #    pip install numpy
# #
# # 3. face_recognition: A high-level library for this task.
# #    This library depends on dlib.
# #    On Linux/macOS:
# #       pip install dlib
# #       pip install face_recognition
# #    On Windows, installing dlib can be tricky. It often requires installing
# #    CMake and a C++ compiler (like Visual Studio Build Tools).
# #

# try:
#     import cv2
#     import numpy as np
#     import face_recognition
#     CV_LIBS_AVAILABLE = True
# except ImportError:
#     CV_LIBS_AVAILABLE = False
#     cv2, np, face_recognition = None, None, None
#     logger.error("Required libraries not found! Please install 'opencv-python', 'numpy', and 'face_recognition'. This module will be non-functional.")

# # Configure basic logging
# logger = logging.getLogger("FacialRecognition")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# @dataclass
# class Recognition:
#     """Represents a single recognized face in an image."""
#     name: str  # The name of the person, or "Unknown"
#     # Bounding box in CSS order (top, right, bottom, left)
#     location: Tuple[int, int, int, int]

# class FacialRecognizer:
#     """
#     Recognizes faces in images by comparing them to a pre-encoded
#     database of known faces.
#     """
#     def __init__(self, known_faces_dir: str = "known_faces"):
#         """
#         Initializes the recognizer by loading and encoding faces
#         from a specified directory.
#         """
#         if not CV_LIBS_AVAILABLE:
#             self.known_encodings = []
#             self.known_names = []
#             logger.error("FacialRecognizer could not be initialized due to missing libraries.")
#             return

#         self.known_faces_dir = known_faces_dir
#         self.known_encodings: List[np.ndarray] = []
#         self.known_names: List[str] = []
        
#         logger.info("Initializing FacialRecognizer...")
#         self._load_or_create_known_faces()

#     def _load_or_create_known_faces(self):
#         """

#         Loads known face encodings from a file if it exists, otherwise
#         creates them by scanning the known_faces_dir. This saves time on startup.
#         """
#         encodings_file = os.path.join(self.known_faces_dir, "encodings.pkl")
#         try:
#             if os.path.exists(encodings_file):
#                 logger.info(f"Loading known face encodings from '{encodings_file}'...")
#                 with open(encodings_file, 'rb') as f:
#                     data = pickle.load(f)
#                     self.known_encodings = data['encodings']
#                     self.known_names = data['names']
#                 logger.info(f"Loaded {len(self.known_names)} known faces.")
#                 return
#         except Exception as e:
#             logger.warning(f"Could not load encodings file: {e}. Re-encoding from images.")

#         logger.info(f"No pre-computed encodings found. Scanning '{self.known_faces_dir}' for images...")
#         if not os.path.isdir(self.known_faces_dir):
#             logger.warning(f"Directory '{self.known_faces_dir}' not found. No known faces will be loaded.")
#             return

#         for filename in os.listdir(self.known_faces_dir):
#             if filename.lower().endswith((".png", ".jpg", ".jpeg")):
#                 name = os.path.splitext(filename)[0].replace("_", " ").title()
#                 image_path = os.path.join(self.known_faces_dir, filename)
                
#                 logger.info(f"  Processing image for '{name}' from '{filename}'...")
#                 image = face_recognition.load_image_file(image_path)
#                 # Get encodings. An image might have multiple faces, but we assume one per file for training.
#                 encodings = face_recognition.face_encodings(image)
                
#                 if encodings:
#                     self.known_encodings.append(encodings[0]) # Add the first face encoding found
#                     self.known_names.append(name)
        
#         if self.known_encodings:
#              logger.info(f"Saving {len(self.known_names)} new encodings to '{encodings_file}' for faster startup next time.")
#              with open(encodings_file, 'wb') as f:
#                  pickle.dump({"encodings": self.known_encodings, "names": self.known_names}, f)

#     def find_and_recognize_faces(self, image_bgr: np.ndarray, tolerance: float = 0.6) -> List[Recognition]:
#         """
#         Finds all faces in an image and identifies them.

#         Args:
#             image_bgr (np.ndarray): The input image in OpenCV format (BGR).
#             tolerance (float): How much distance between faces to consider it a match.
#                                Lower is more strict. 0.6 is a good default.

#         Returns:
#             List[Recognition]: A list of recognized faces.
#         """
#         if not self.known_encodings:
#             logger.warning("No known faces loaded. All faces will be 'Unknown'.")
        
#         # Convert the image from BGR (OpenCV default) to RGB (face_recognition default)
#         image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

#         # 1. Find all face locations and create their encodings
#         logger.info("Detecting face locations and computing encodings...")
#         face_locations = face_recognition.face_locations(image_rgb)
#         face_encodings = face_recognition.face_encodings(image_rgb, face_locations)

#         recognitions = []
#         for location, encoding in zip(face_locations, face_encodings):
#             # 2. Compare the new face encoding with all known face encodings
#             matches = face_recognition.compare_faces(self.known_encodings, encoding, tolerance=tolerance)
#             name = "Unknown"

#             # 3. Find the best match if one exists
#             if True in matches:
#                 face_distances = face_recognition.face_distance(self.known_encodings, encoding)
#                 best_match_index = np.argmin(face_distances)
#                 if matches[best_match_index]:
#                     name = self.known_names[best_match_index]
            
#             recognitions.append(Recognition(name=name, location=location))
#             logger.info(f"  Found face: {name} at location {location}")
            
#         return recognitions

#     @staticmethod
#     def draw_recognitions(image: np.ndarray, recognitions: List[Recognition]) -> np.ndarray:
#         """Draws bounding boxes and names on an image."""
#         img_copy = image.copy()
#         for recog in recognitions:
#             top, right, bottom, left = recog.location
#             name = recog.name
            
#             # Draw a box around the face
#             color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
#             cv2.rectangle(img_copy, (left, top), (right, bottom), color, 2)
            
#             # Draw a label with a name below the face
#             cv2.rectangle(img_copy, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
#             font = cv2.FONT_HERSHEY_DUPLEX
#             cv2.putText(img_copy, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
#         return img_copy

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Robotics Facial Recognition Prototype 👤👁️ ===")
#     print("=========================================================")

#     if not CV_LIBS_AVAILABLE:
#         print("\nRequired libraries not found. Please see installation notes in the script.")
#     else:
#         # --- 1. Setup the environment for the demo ---
#         # Create a directory for known faces and add some dummy images
#         KNOWN_FACES_DIR = "known_faces_demo"
#         if not os.path.exists(KNOWN_FACES_DIR):
#             os.makedirs(KNOWN_FACES_DIR)
        
#         # NOTE: For this demo to work, you need to place images of people
#         # in the 'known_faces_demo' directory. Name the files like 'Person_Name.jpg'.
#         # For now, we will create dummy placeholders.
#         print(f"Please place JPG or PNG images of faces to recognize in the '{KNOWN_FACES_DIR}' directory.")
#         print("For example: 'Elon_Musk.jpg', 'Marie_Curie.png'")
        
#         # Create a dummy test image
#         TEST_IMAGE_PATH = "test_recognition_image.jpg"
#         dummy_image = np.zeros((600, 800, 3), dtype="uint8")
#         cv2.putText(dummy_image, "Place a test image here", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
#         cv2.imwrite(TEST_IMAGE_PATH, dummy_image)
#         print(f"A placeholder test image has been saved to '{TEST_IMAGE_PATH}'. Please replace it with an image containing faces.")
        
#         # --- 2. Initialize the Recognizer ---
#         # This will scan the directory and create encodings.
#         recognizer = FacialRecognizer(known_faces_dir=KNOWN_FACES_DIR)
        
#         # --- 3. Load test image and perform recognition ---
#         if recognizer.known_names:
#             print(f"\nLoading test image from '{TEST_IMAGE_PATH}'...")
#             image_to_test = cv2.imread(TEST_IMAGE_PATH)
            
#             if image_to_test is not None:
#                 recognitions = recognizer.find_and_recognize_faces(image_to_test)
                
#                 # --- 4. Print results and save output image ---
#                 print("\n--- Recognition Results ---")
#                 if recognitions:
#                     for recog in recognitions:
#                         print(f"  - Found '{recog.name}'")
                    
#                     output_image = recognizer.draw_recognitions(image_to_test, recognitions)
#                     OUTPUT_IMAGE_PATH = "recognition_output.jpg"
#                     cv2.imwrite(OUTPUT_IMAGE_PATH, output_image)
#                     print(f"\nOutput image with recognitions saved to '{OUTPUT_IMAGE_PATH}'")
#                 else:
#                     print("  No faces were detected in the test image.")
#             else:
#                 print(f"  Could not load the test image at '{TEST_IMAGE_PATH}'.")
#         else:
#             print("\nSkipping recognition demo because no known faces were loaded.")

#     print("\n=========================================================")
#     print("=== Facial Recognition Prototype Complete ===")
#     print("=========================================================")

# Devin/modules/robotics/facial_recognition.py
# Purpose: Provides a real-time facial recognition system that identifies
#          faces in a live video stream against a known database.

import logging
import os
import pickle
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from pathlib import Path

try:
    import cv2
    import numpy as np
    import face_recognition
    from modules.robotics.sensor_integration import Camera
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("FacialRecognition")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

@dataclass
class Recognition:
    """Represents a single recognized face in an image."""
    name: str
    location: Tuple[int, int, int, int] # Bounding box in CSS order (top, right, bottom, left)

class FacialRecognizer:
    """Recognizes faces by comparing them to a pre-encoded database."""
    def __init__(self, known_faces_dir: str = "known_faces"):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core module is missing. Error: {_import_error}")

        self.known_faces_path = Path(known_faces_dir)
        self.encodings_file_path = self.known_faces_path / "encodings.pkl"
        self.known_encodings: List[np.ndarray] = []
        self.known_names: List[str] = []
        self._load_or_create_known_faces()

    def _load_or_create_known_faces(self):
        """Loads known face encodings, re-encoding only if necessary."""
        self.known_faces_path.mkdir(exist_ok=True)
        
        # Check if we need to re-encode
        re_encode = not self.encodings_file_path.exists()
        if not re_encode:
            last_encode_time = self.encodings_file_path.stat().st_mtime
            for img_path in self.known_faces_path.glob("*.[jp][pn]g"):
                if img_path.stat().st_mtime > last_encode_time:
                    re_encode = True
                    logger.info(f"Image '{img_path.name}' has been modified. Re-encoding all faces.")
                    break
        
        if re_encode:
            self._encode_faces_from_directory()
        else:
            logger.info(f"Loading cached face encodings from '{self.encodings_file_path}'...")
            with open(self.encodings_file_path, 'rb') as f:
                data = pickle.load(f)
                self.known_encodings = data['encodings']
                self.known_names = data['names']
        
        logger.info(f"Recognizer ready with {len(self.known_names)} known faces.")

    def _encode_faces_from_directory(self):
        """Scans the directory for images and creates facial encodings."""
        logger.warning(f"Performing full scan and encoding of '{self.known_faces_path}'...")
        self.known_encodings.clear()
        self.known_names.clear()

        for img_path in self.known_faces_path.glob("*.[jp][pn]g"):
            name = img_path.stem.replace("_", " ").title()
            logger.info(f"  Processing image for '{name}'...")
            image = face_recognition.load_image_file(str(img_path))
            encodings = face_recognition.face_encodings(image)
            if encodings:
                self.known_encodings.append(encodings[0])
                self.known_names.append(name)

        if self.known_encodings:
            logger.info(f"Saving {len(self.known_names)} new encodings to cache file.")
            with open(self.encodings_file_path, 'wb') as f:
                pickle.dump({"encodings": self.known_encodings, "names": self.known_names}, f)

    def find_and_recognize_faces(self, image_bgr: np.ndarray, tolerance: float = 0.6) -> List[Recognition]:
        """Finds and identifies all faces in a BGR image."""
        if not self.known_encodings:
            return [] # Cannot recognize if no known faces
        
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(image_rgb)
        face_encodings = face_recognition.face_encodings(image_rgb, face_locations)

        recognitions = []
        for location, encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(self.known_encodings, encoding, tolerance=tolerance)
            name = "Unknown"
            if True in matches:
                face_distances = face_recognition.face_distance(self.known_encodings, encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_names[best_match_index]
            recognitions.append(Recognition(name=name, location=location))
        return recognitions

    @staticmethod
    def draw_recognitions(image: np.ndarray, recognitions: List[Recognition]) -> np.ndarray:
        """Draws bounding boxes and names on an image."""
        for recog in recognitions:
            top, right, bottom, left = recog.location
            color = (0, 255, 0) if recog.name != "Unknown" else (0, 0, 255)
            cv2.rectangle(image, (left, top), (right, bottom), color, 2)
            cv2.rectangle(image, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(image, recog.name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)
        return image


class FacialRecognitionSystem:
    """A high-level system for running live facial recognition."""
    def __init__(self, recognizer: FacialRecognizer, camera: Camera):
        self.recognizer = recognizer
        self.camera = camera

    def run_live_recognition(self):
        """Starts a loop to capture and process frames from the camera."""
        if not self.camera.connect():
            logger.error("Could not start live recognition: Camera connection failed.")
            return

        process_this_frame = True
        while True:
            frame = self.camera.read_data()
            if frame is None:
                logger.warning("Dropped a frame.")
                continue

            # Performance optimization: only run recognition on every other frame
            if process_this_frame:
                recognitions = self.recognizer.find_and_recognize_faces(frame)

            process_this_frame = not process_this_frame

            # Draw the results on the current frame
            display_frame = self.recognizer.draw_recognitions(frame, recognitions)
            
            cv2.imshow('Live Facial Recognition (Press "q" to quit)', display_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.camera.disconnect()
        cv2.destroyAllWindows()


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Facial Recognition System (Live Demo) 👤👁️ ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core module is missing. Error: {_import_error}")
        print("Please ensure all dependencies are installed: 'pip install opencv-python numpy face_recognition dlib cmake'")
    else:
        # --- 1. Setup the environment for the demo ---
        KNOWN_FACES_DIR = Path("known_faces_demo")
        KNOWN_FACES_DIR.mkdir(exist_ok=True)
        print(f"\n--- Setup ---")
        print(f"Please place one or more images of faces in the '{KNOWN_FACES_DIR.resolve()}' directory.")
        print("Name the files like 'Your_Name.jpg' or 'Another_Person.png'.")
        
        # Check if the user has added any photos
        if not any(KNOWN_FACES_DIR.glob("*.[jp][pn]g")):
             print("\nWARNING: No images found in the known faces directory. The system will only detect 'Unknown' faces.")
             print("The demo will still run to show face detection.")

        input("\nPress Enter to start the live recognition demo...")
        
        try:
            # --- 2. Initialize the full system ---
            recognizer = FacialRecognizer(known_faces_dir=str(KNOWN_FACES_DIR))
            camera = Camera(sensor_id="system_webcam")
            recognition_system = FacialRecognitionSystem(recognizer=recognizer, camera=camera)

            # --- 3. Run the live demo ---
            print("\n--- Starting Live Recognition ---")
            print("A window with your webcam feed will open.")
            print("Look at the camera. Press 'q' in the window to quit.")
            recognition_system.run_live_recognition()

        except Exception as e:
            logger.error(f"Demo failed to run. Do you have a webcam connected and all dependencies installed? Error: {e}", exc_info=True)

    print("\n=========================================================")
    print("=== Facial Recognition Demo Complete ===")
    print("=========================================================")
