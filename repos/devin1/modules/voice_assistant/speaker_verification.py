"""
speaker_verification.py
------------------------
This module verifies the speaker by comparing their voice against an enrolled voice profile.

Dependencies:
- librosa (Audio processing)
- numpy (Numerical operations)
- sklearn (Machine learning)
- sounddevice (Recording audio)
- pickle (Saving and loading profiles)
"""

import librosa
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import sounddevice as sd
import pickle
import os
import logging
import tempfile

class verify_speaker:
    """
    A class to handle speaker verification based on voice embeddings.
    """

    def __init__(self, profile_path="voice_profiles/", log_file="speaker_verification.log", sample_rate=16000):
        """
        Initializes the SpeakerVerification system.

        Args:
            profile_path (str): Path to save and load voice profiles.
            log_file (str): Path to the log file.
            sample_rate (int): Sampling rate for audio recording.
        """
        self.profile_path = profile_path
        self.sample_rate = sample_rate
        self.log_file = log_file
        self.audio_duration = 5  # Seconds for recording

        # Setup logging
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        logging.info("SpeakerVerification initialized.")

        # Create directory for voice profiles if it doesn't exist
        if not os.path.exists(self.profile_path):
            os.makedirs(self.profile_path)
            logging.info(f"Voice profile directory created at: {self.profile_path}")

    def record_audio(self, duration=None):
        """
        Records audio from the microphone.

        Args:
            duration (int): Duration in seconds. Defaults to the system's audio_duration.

        Returns:
            np.ndarray: Recorded audio as a numpy array.
        """
        if not duration:
            duration = self.audio_duration

        logging.info(f"Recording audio for {duration} seconds...")
        try:
            audio = sd.rec(int(duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype="float32")
            sd.wait()  # Wait for the recording to finish
            logging.info("Audio recording completed.")
            return np.squeeze(audio)
        except Exception as e:
            logging.error(f"Audio recording failed: {e}")
            raise

    def extract_features(self, audio):
        """
        Extracts audio features using MFCCs.

        Args:
            audio (np.ndarray): Audio data as a numpy array.

        Returns:
            np.ndarray: Extracted MFCC features.
        """
        try:
            mfccs = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=40)
            mfccs_mean = np.mean(mfccs.T, axis=0)
            logging.info("Audio features extracted successfully.")
            return mfccs_mean
        except Exception as e:
            logging.error(f"Feature extraction failed: {e}")
            raise

    def enroll_voice(self, name):
        """
        Enrolls a new voice profile.

        Args:
            name (str): Name of the person to associate with the voice profile.
        """
        logging.info(f"Enrolling voice for: {name}")
        audio = self.record_audio()
        features = self.extract_features(audio)

        profile_file = os.path.join(self.profile_path, f"{name}.pkl")
        try:
            with open(profile_file, "wb") as f:
                pickle.dump(features, f)
            logging.info(f"Voice profile saved for {name} at {profile_file}.")
        except Exception as e:
            logging.error(f"Failed to save voice profile: {e}")
            raise

    def verify_voice(self, name):
        """
        Verifies if the recorded voice matches the enrolled profile.

        Args:
            name (str): Name of the person to verify against.

        Returns:
            bool: True if the voice matches the profile, False otherwise.
        """
        logging.info(f"Verifying voice for: {name}")
        profile_file = os.path.join(self.profile_path, f"{name}.pkl")

        if not os.path.exists(profile_file):
            logging.error(f"Voice profile for {name} does not exist.")
            return False

        try:
            with open(profile_file, "rb") as f:
                enrolled_features = pickle.load(f)
        except Exception as e:
            logging.error(f"Failed to load voice profile for {name}: {e}")
            raise

        recorded_audio = self.record_audio()
        recorded_features = self.extract_features(recorded_audio)

        similarity = cosine_similarity([enrolled_features], [recorded_features])[0][0]
        logging.info(f"Similarity score: {similarity}")

        threshold = 0.75  # Similarity threshold
        if similarity >= threshold:
            logging.info(f"Voice verification for {name} successful.")
            return True
        else:
            logging.info(f"Voice verification for {name} failed.")
            return False

if __name__ == "__main__":
    verifier = SpeakerVerification()

    print("1. Enroll a new voice profile")
    print("2. Verify a voice profile")
    choice = input("Enter your choice (1/2): ")

    if choice == "1":
        user_name = input("Enter the name for enrollment: ")
        verifier.enroll_voice(user_name)
        print(f"Voice enrolled for {user_name}.")
    elif choice == "2":
        user_name = input("Enter the name for verification: ")
        if verifier.verify_voice(user_name):
            print(f"Voice verified for {user_name}.")
        else:
            print(f"Voice verification failed for {user_name}.")
    else:
        print("Invalid choice. Exiting.")
