"""
voice_profile.py
-----------------
This module manages enrollment, storage, and verification of voice profiles.

Features:
- Enrollment of voice profiles.
- Saving and retrieving voice embeddings for authentication.
- Supports multi-user voice authentication with high security.
- Enables Devin to respond only to specific voice profiles.

Dependencies:
- SpeechRecognition for audio capture.
- NumPy for numerical operations.
- TensorFlow/Keras for neural network embeddings.
- SQLite for database storage of voice embeddings.
"""

import os
import logging
import sqlite3
import numpy as np
import librosa
import sounddevice as sd
from scipy.io.wavfile import write
from tensorflow.keras.models import load_model

# Constants
DB_FILE = "voice_profiles.db"
AUDIO_FILE = "temp_audio.wav"
SAMPLE_RATE = 16000
DURATION = 5  # seconds
MODEL_PATH = "models/voice_embedding_model.h5"

# Logger configuration
logging.basicConfig(
    filename="voice_profile.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class VoiceProfileManager:
    """
    Handles the management of voice profiles, including enrollment, storage, and verification.
    """

    def __init__(self):
        self.db_path = DB_FILE
        self.model = self.load_embedding_model(MODEL_PATH)
        self.init_database()

    def init_database(self):
        """
        Initializes the SQLite database to store voice profiles.
        """
        logging.info("Initializing database...")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS voice_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT UNIQUE NOT NULL,
                    voice_embedding BLOB NOT NULL
                )
            """)
            conn.commit()
            conn.close()
            logging.info("Database initialized successfully.")
        except sqlite3.Error as e:
            logging.error(f"Database initialization failed: {e}")
            raise

    def load_embedding_model(self, model_path):
        """
        Loads the pre-trained voice embedding model.

        Args:
            model_path (str): Path to the model file.

        Returns:
            Model: The loaded TensorFlow/Keras model.
        """
        logging.info(f"Loading embedding model from {model_path}...")
        try:
            model = load_model(model_path)
            logging.info("Embedding model loaded successfully.")
            return model
        except Exception as e:
            logging.error(f"Failed to load embedding model: {e}")
            raise

    def record_audio(self, duration=DURATION, sample_rate=SAMPLE_RATE):
        """
        Records audio from the user's microphone.

        Args:
            duration (int): Duration of the recording in seconds.
            sample_rate (int): Audio sample rate.

        Returns:
            str: Path to the saved audio file.
        """
        logging.info(f"Recording audio for {duration} seconds...")
        try:
            audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()
            write(AUDIO_FILE, sample_rate, audio_data)
            logging.info(f"Audio recorded and saved to {AUDIO_FILE}.")
            return AUDIO_FILE
        except Exception as e:
            logging.error(f"Audio recording failed: {e}")
            raise

    def extract_features(self, audio_path):
        """
        Extracts MFCC features from the audio file.

        Args:
            audio_path (str): Path to the audio file.

        Returns:
            np.ndarray: Extracted features.
        """
        logging.info(f"Extracting features from {audio_path}...")
        try:
            audio, _ = librosa.load(audio_path, sr=SAMPLE_RATE)
            mfcc = librosa.feature.mfcc(audio, sr=SAMPLE_RATE, n_mfcc=40)
            feature = np.mean(mfcc.T, axis=0)
            logging.info("Features extracted successfully.")
            return feature
        except Exception as e:
            logging.error(f"Feature extraction failed: {e}")
            raise

    def enroll_voice_profile(self, user_name):
        """
        Enrolls a new voice profile by saving the user's voice embedding.

        Args:
            user_name (str): The user's name.

        Returns:
            str: Enrollment status message.
        """
        logging.info(f"Enrolling voice profile for user: {user_name}...")
        try:
            # Record audio
            audio_path = self.record_audio()
            features = self.extract_features(audio_path)
            
            # Generate voice embedding
            voice_embedding = self.model.predict(features.reshape(1, -1))[0]
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO voice_profiles (user_name, voice_embedding)
                VALUES (?, ?)
            """, (user_name, voice_embedding.tobytes()))
            conn.commit()
            conn.close()
            logging.info(f"Voice profile for {user_name} enrolled successfully.")
            return "Voice profile enrolled successfully."
        except sqlite3.IntegrityError:
            logging.warning(f"Voice profile for {user_name} already exists.")
            return "User already enrolled."
        except Exception as e:
            logging.error(f"Enrollment failed: {e}")
            return f"Error enrolling voice profile: {e}"

    def verify_voice(self, user_name):
        """
        Verifies the voice against the stored profile.

        Args:
            user_name (str): The user's name.

        Returns:
            bool: True if verified, False otherwise.
        """
        logging.info(f"Verifying voice for user: {user_name}...")
        try:
            # Record audio
            audio_path = self.record_audio()
            features = self.extract_features(audio_path)
            
            # Generate voice embedding
            new_embedding = self.model.predict(features.reshape(1, -1))[0]
            
            # Retrieve stored embedding
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT voice_embedding FROM voice_profiles WHERE user_name = ?", (user_name,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                stored_embedding = np.frombuffer(result[0], dtype=np.float32)
                similarity = np.dot(new_embedding, stored_embedding) / (
                    np.linalg.norm(new_embedding) * np.linalg.norm(stored_embedding))
                
                logging.info(f"Similarity score: {similarity}")
                return similarity >= 0.8  # Threshold for matching
            else:
                logging.warning("No profile found for the user.")
                return False
        except Exception as e:
            logging.error(f"Verification failed: {e}")
            return False


if __name__ == "__main__":
    manager = VoiceProfileManager()

    print("1. Enroll voice profile")
    print("2. Verify voice profile")
    choice = input("Enter your choice (1/2): ")

    if choice == "1":
        name = input("Enter your name: ")
        print(manager.enroll_voice_profile(name))
    elif choice == "2":
        name = input("Enter your name: ")
        if manager.verify_voice(name):
            print("Voice verified successfully.")
        else:
            print("Voice verification failed.")
    else:
        print("Invalid choice.")
