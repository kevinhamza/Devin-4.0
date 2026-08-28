import cv2
import face_recognition
import numpy as np
import os
from modules.social_media_search import SocialMediaSearch  # Correct import for SocialMediaSearch
from modules.error_handling import ErrorLogger

class FaceDetection:
    """
    AIA's module for real-time face detection and person information retrieval from social media platforms.
    """

    def __init__(self, known_faces_dir="known_faces", tolerance=0.6):
        """
        Initialize the FaceDetection module.
        :param known_faces_dir: Directory containing pre-known face encodings.
        :param tolerance: Tolerance for face matching.
        """
        self.known_faces = []
        self.known_names = []
        self.error_handler = ErrorLogger()

        # Load pre-known faces
        if os.path.exists(known_faces_dir):
            self.load_known_faces(known_faces_dir)
        else:
            os.makedirs(known_faces_dir, exist_ok=True)

        self.tolerance = tolerance
        self.social_search = SocialMediaSearch()  # Initialize SocialMediaSearch class

    def load_known_faces(self, directory):
        """
        Load known face encodings from a directory.
        :param directory: Path to the directory containing known face images.
        """
        for filename in os.listdir(directory):
            if filename.endswith((".jpg", ".png")):
                try:
                    filepath = os.path.join(directory, filename)
                    image = face_recognition.load_image_file(filepath)
                    encoding = face_recognition.face_encodings(image)[0]
                    self.known_faces.append(encoding)
                    self.known_names.append(os.path.splitext(filename)[0])
                except Exception as e:
                    self.error_handler.log_error(
                        f"Failed to load face encoding for {filename}: {e}"
                    )

    def detect_and_identify(self, video_source=0):
        """
        Perform real-time face detection and identification.
        :param video_source: Video source (0 for webcam, or path to video file).
        """
        video_capture = cv2.VideoCapture(video_source)

        while True:
            ret, frame = video_capture.read()
            if not ret:
                print("Failed to capture frame.")
                break

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(self.known_faces, face_encoding, self.tolerance)
                name = "Unknown"

                if True in matches:
                    first_match_index = matches.index(True)
                    name = self.known_names[first_match_index]

                else:
                    social_info = self.search_social_media(face_encoding)
                    name = social_info.get("name", "Unknown")

                self.display_info_on_frame(frame, face_location, name)

            cv2.imshow("Face Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        video_capture.release()
        cv2.destroyAllWindows()

    def search_social_media(self, face_encoding):
        """
        Search for a person's details on social media using their face encoding.
        :param face_encoding: The face encoding to search for.
        :return: A dictionary of social media details.
        """
        try:
            return self.social_search.search_by_face(face_encoding)  # Use SocialMediaSearch to find info
        except Exception as e:
            self.error_handler.handle_exception(e, "Error in social media search.")
            return {}

    def display_info_on_frame(self, frame, face_location, name):
        """
        Overlay the detected person's name and details on the frame.
        :param frame: The video frame to modify.
        :param face_location: The location of the face.
        :param name: Name or details to display.
        """
        top, right, bottom, left = [v * 4 for v in face_location]
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


if __name__ == "__main__":
    detector = FaceDetection()
    detector.detect_and_identify()
