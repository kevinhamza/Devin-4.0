# Devin/modules/face_recognition_tools.py
# Purpose: Matches faces in an image against a local, explicitly consented
#          set of known people -- e.g. "is this any of my verified team
#          members" or personal photo-library tagging.
#
# Deliberately does NOT do what aia's face_recognition.py/face_detection.py
# did when a face doesn't match anyone known: those fell back to a
# PimEye-style reverse image search and social-media lookup to identify
# strangers from their photo. That's a fundamentally different, harmful
# capability -- it targets people who never consented to being searchable,
# and no code-side check can verify consent that was never actually given.
# This module was deliberately scoped to drop that fallback: an unmatched
# face is reported as "Unknown" and nothing further is attempted. Every
# name this can ever return is a name YOU added via add_known_face(), which
# is why it's on you to only add people who actually agreed to this use.

import logging
import os
from typing import Any, Dict, List, Optional

try:
    import face_recognition
    import numpy as np
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

logger = logging.getLogger("FaceRecognitionTools")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)
logger.propagate = False


class ConsentedFaceRecognizer:
    """
    Matches faces against a closed, explicitly-consented set of known
    people. Never attempts to identify anyone outside that set.
    """

    def __init__(self, known_faces_dir: str = "known_faces", tolerance: float = 0.6):
        if not FACE_RECOGNITION_AVAILABLE:
            raise ImportError("The 'face_recognition' package is required. 'pip install face_recognition'")

        self.known_faces_dir = known_faces_dir
        self.tolerance = tolerance
        self.known_encodings: List[Any] = []
        self.known_names: List[str] = []

        os.makedirs(self.known_faces_dir, exist_ok=True)
        self._load_known_faces()

    def _load_known_faces(self):
        self.known_encodings = []
        self.known_names = []
        for filename in os.listdir(self.known_faces_dir):
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            filepath = os.path.join(self.known_faces_dir, filename)
            try:
                image = face_recognition.load_image_file(filepath)
                encodings = face_recognition.face_encodings(image)
                if not encodings:
                    logger.warning(f"No face found in '{filename}'; skipping.")
                    continue
                self.known_encodings.append(encodings[0])
                self.known_names.append(os.path.splitext(filename)[0])
            except Exception as e:
                logger.error(f"Failed to load face encoding for '{filename}': {e}")
        logger.info(f"Loaded {len(self.known_names)} known face(s) from '{self.known_faces_dir}'.")

    def add_known_face(self, name: str, image_path: str) -> Dict[str, Any]:
        """
        Adds a person to the consented recognition set. Only call this for
        someone who has actually agreed to be recognized by this system --
        this method has no way to verify that itself, so that judgment call
        is the caller's responsibility every time.
        """
        if not os.path.exists(image_path):
            return {"status": "error", "message": f"Image not found: {image_path}"}
        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if not encodings:
                return {"status": "error", "message": "No face detected in the provided image."}

            dest_filename = f"{name}{os.path.splitext(image_path)[1]}"
            dest_path = os.path.join(self.known_faces_dir, dest_filename)
            with open(image_path, "rb") as src, open(dest_path, "wb") as dst:
                dst.write(src.read())

            self.known_encodings.append(encodings[0])
            self.known_names.append(name)
            logger.info(f"Added '{name}' to the consented recognition set.")
            return {"status": "success", "name": name}
        except Exception as e:
            logger.error(f"Failed to add known face '{name}': {e}")
            return {"status": "error", "message": str(e)}

    def remove_known_face(self, name: str) -> Dict[str, Any]:
        """Removes a person from the consented recognition set."""
        removed = False
        for filename in os.listdir(self.known_faces_dir):
            if os.path.splitext(filename)[0] == name:
                os.remove(os.path.join(self.known_faces_dir, filename))
                removed = True
        if removed:
            self._load_known_faces()
            return {"status": "success", "message": f"Removed '{name}'."}
        return {"status": "error", "message": f"No known face found named '{name}'."}

    def identify_faces_in_image(self, image_path: str) -> Dict[str, Any]:
        """
        Identifies faces in the given image against the consented known set.
        Any face that doesn't match someone in that set is reported as
        "Unknown" -- no external lookup is ever attempted for it.
        """
        if not os.path.exists(image_path):
            return {"status": "error", "message": f"Image not found: {image_path}"}
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)

            results = []
            for encoding, location in zip(face_encodings, face_locations):
                name = "Unknown"
                if self.known_encodings:
                    matches = face_recognition.face_distance(self.known_encodings, encoding)
                    best_match_index = int(np.argmin(matches))
                    if matches[best_match_index] <= self.tolerance:
                        name = self.known_names[best_match_index]
                top, right, bottom, left = location
                results.append({"name": name, "location": {"top": top, "right": right, "bottom": bottom, "left": left}})

            return {"status": "success", "faces": results}
        except Exception as e:
            logger.error(f"Face identification failed: {e}")
            return {"status": "error", "message": str(e)}
