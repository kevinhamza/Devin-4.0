import cv2
import face_recognition
import numpy as np
from modules.error_handling import ErrorLogger
from config.social_media_keys import SocialMediaKeys
from modules.pimeye_integration import PimEyeIntegration


class FaceRecognitionSystem:
    """
    Advanced face recognition system for detecting faces, extracting details, and retrieving personal information
    from multiple platforms and PimEyes-like services.
    """

    def __init__(self):
        self.error_handler = ErrorHandling()
        self.social_media_apis = {
            "Facebook": {"api_key": FACEBOOK_API_KEY, "base_url": "https://graph.facebook.com/"},
            "Twitter": {"api_key": TWITTER_API_KEY, "base_url": "https://api.twitter.com/2/"},
            "Instagram": {"api_key": INSTAGRAM_API_KEY, "base_url": "https://graph.instagram.com/"},
            "LinkedIn": {"api_key": LINKEDIN_API_KEY, "base_url": "https://api.linkedin.com/v2/"},
        }
        self.pimeye_search = PimEyeSearch()
        self.tolerance = 0.5
        self.known_faces = []
        self.known_names = []

    def load_known_faces(self, directory="known_faces"):
        """
        Load known face encodings from a directory.
        :param directory: Path to directory containing known face images.
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
                    self.error_handler.log_error(f"Error loading face {filename}: {e}")

    def process_frame(self, frame):
        """
        Detect and process faces in a given frame.
        :param frame: Video frame to process.
        :return: Processed frame with annotations.
        """
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_frame = small_frame[:, :, ::-1]

        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(self.known_faces, face_encoding, self.tolerance)
            name = "Unknown"

            if True in matches:
                match_index = matches.index(True)
                name = self.known_names[match_index]
                self.display_on_frame(frame, face_location, name)
            else:
                details = self.search_person_details(face_encoding)
                self.display_on_frame(frame, face_location, details.get("name", "Unknown"))

        return frame

    def search_person_details(self, face_encoding):
        """
        Search for a person's details on social media and PimEyes-like services.
        :param face_encoding: Encoding of the face to search.
        :return: A dictionary containing the person's details.
        """
        try:
            # PimEye-like search
            search_results = self.pimeye_search.search_by_face(face_encoding)
            if search_results:
                return {"name": search_results[0].get("name", "Unknown"), "profile": search_results[0]}

            # Social media APIs search
            for platform, config in self.social_media_apis.items():
                try:
                    response = self.search_social_media(platform, face_encoding, config)
                    if response and "name" in response:
                        return response
                except Exception as e:
                    self.error_handler.log_error(f"Error searching on {platform}: {e}")

        except Exception as e:
            self.error_handler.handle_exception(e, "Error searching person details.")
        return {"name": "Unknown"}

    def search_social_media(self, platform, face_encoding, config):
        """
        Search for a person's details on a specific social media platform.
        :param platform: Social media platform name.
        :param face_encoding: Encoding of the face to search.
        :param config: API configuration for the platform.
        :return: Dictionary containing person's details if found.
        """
        try:
            # Simulated API request
            headers = {"Authorization": f"Bearer {config['api_key']}"}
            payload = {"face_encoding": face_encoding.tolist()}
            response = requests.post(f"{config['base_url']}face/search", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.error_handler.log_error(f"API request to {platform} failed: {e}")
        return {}

    def display_on_frame(self, frame, face_location, name):
        """
        Overlay information on the video frame.
        :param frame: Video frame to annotate.
        :param face_location: Location of the face in the frame.
        :param name: Name or details of the person to display.
        """
        top, right, bottom, left = [v * 4 for v in face_location]
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def run_face_recognition(self, video_source=0):
        """
        Run the real-time face recognition system.
        :param video_source: Video source (default is webcam).
        """
        video_capture = cv2.VideoCapture(video_source)

        while True:
            ret, frame = video_capture.read()
            if not ret:
                print("Failed to grab frame.")
                break

            processed_frame = self.process_frame(frame)
            cv2.imshow("Face Recognition", processed_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        video_capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    system = FaceRecognitionSystem()
    system.load_known_faces()
    system.run_face_recognition()
