# # Devin/modules/robotics/speech_recognition.py
# # Purpose: Provides advanced speech analysis, focusing on Speaker Recognition
# #          (identifying who is speaking) from an audio clip.

# import logging
# import os
# import pickle
# from dataclasses import dataclass
# from typing import List, Tuple, Dict, Optional, Any

# # This module would rely on advanced audio processing and ML libraries.
# # Real-world implementations might use:
# # - librosa: for audio feature extraction (like MFCCs).
# # - scikit-learn: for training models like Gaussian Mixture Models (GMMs) for each speaker.
# # - pytorch/tensorflow: for deep learning-based d-vector/x-vector approaches.
# # - speechbrain: A high-level toolkit for speech processing.
# #
# # For the STT part, it would use the same libraries as voice_assistant.py
# try:
#     import numpy as np
#     import speech_recognition as sr
#     # Conceptually import librosa for feature extraction
#     # import librosa
#     SPEECH_LIBS_AVAILABLE = True
# except ImportError:
#     SPEECH_LIBS_AVAILABLE = False
#     np, sr = None, None
#     logger.error("Required libraries not found! This module will be non-functional.")

# # Configure basic logging
# logger = logging.getLogger("SpeakerRecognition")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# @dataclass
# class SpeechAnalysisResult:
#     """Structured result of a speech analysis."""
#     transcribed_text: Optional[str]
#     identified_speaker: Optional[str] = "Unknown"
#     confidence: float = 0.0

# class AdvancedSpeechAnalyzer:
#     """
#     Analyzes audio to perform Speech-to-Text and Speaker Recognition.
#     """
#     def __init__(self, voiceprints_path: str = "voiceprints.pkl"):
#         """
#         Initializes the analyzer and loads a database of known voiceprints.
#         """
#         if not SPEECH_LIBS_AVAILABLE:
#             self.recognizer = None
#             self.voiceprints = {}
#             logger.error("AdvancedSpeechAnalyzer could not be initialized due to missing libraries.")
#             return

#         self.recognizer = sr.Recognizer()
#         self.voiceprints_path = voiceprints_path
#         self.voiceprints: Dict[str, Any] = {} # { 'speaker_name': <conceptual_voice_model> }

#         logger.info("Initializing AdvancedSpeechAnalyzer...")
#         self._load_voiceprints()

#     def _load_voiceprints(self):
#         """Loads pre-computed voiceprints from a file."""
#         try:
#             if os.path.exists(self.voiceprints_path):
#                 logger.info(f"Loading known voiceprints from '{self.voiceprints_path}'...")
#                 with open(self.voiceprints_path, 'rb') as f:
#                     self.voiceprints = pickle.load(f)
#                 logger.info(f"Loaded {len(self.voiceprints)} known voiceprints.")
#         except Exception as e:
#             logger.error(f"Could not load voiceprints file: {e}. The database is empty.")
#             self.voiceprints = {}

#     def _save_voiceprints(self):
#         """Saves the current voiceprints database to a file."""
#         logger.info(f"Saving {len(self.voiceprints)} voiceprints to '{self.voiceprints_path}'...")
#         with open(self.voiceprints_path, 'wb') as f:
#             pickle.dump(self.voiceprints, f)

#     def _extract_voiceprint_conceptual(self, audio_data: sr.AudioData) -> Any:
#         """
#         Conceptually extracts a unique voiceprint from audio data.

#         In a real system, this would be a complex function involving:
#         1. Converting audio data to a NumPy array.
#         2. Using a library like `librosa` to extract features (e.g., MFCCs - Mel-frequency cepstral coefficients).
#         3. Returning these features as the voiceprint.
#         """
#         logger.info("Conceptually extracting voiceprint (e.g., MFCCs) from audio...")
#         # Simulate a voiceprint as a numpy array of a fixed size
#         return np.random.rand(20, 40) # A conceptual 20x40 feature matrix

#     def enroll_speaker(self, audio_source: Any, speaker_name: str):
#         """
#         Enrolls a new speaker by creating a voiceprint from an audio sample.

#         Args:
#             audio_source: A path to an audio file or an active sr.Microphone() source.
#             speaker_name (str): The name of the speaker to enroll.
#         """
#         if not self.recognizer: return
        
#         logger.info(f"Enrolling new speaker: '{speaker_name}'. Please provide a speech sample.")
        
#         try:
#             # Handle both file and microphone sources
#             if isinstance(audio_source, str): # Path to audio file
#                 with sr.AudioFile(audio_source) as source:
#                     audio_data = self.recognizer.record(source)
#             elif isinstance(audio_source, sr.Microphone):
#                  print(f"Please speak clearly for a few seconds to enroll '{speaker_name}'...")
#                  audio_data = self.recognizer.listen(audio_source, phrase_time_limit=5)
#             else:
#                 logger.error("Invalid audio source for enrollment.")
#                 return

#             # In a real system, you'd train a model (like a GMM) on these features.
#             # For this prototype, we'll just store the raw (conceptual) features.
#             voiceprint = self._extract_voiceprint_conceptual(audio_data)
#             self.voiceprints[speaker_name.lower()] = voiceprint
#             self._save_voiceprints()
#             logger.info(f"Speaker '{speaker_name}' enrolled successfully.")

#         except Exception as e:
#             logger.error(f"An error occurred during enrollment: {e}")

#     def analyze_speech(self, audio_data: sr.AudioData) -> SpeechAnalysisResult:
#         """
#         Performs both STT and Speaker Recognition on a given audio clip.

#         Returns:
#             SpeechAnalysisResult: An object containing the text and identified speaker.
#         """
#         if not self.recognizer:
#             return SpeechAnalysisResult(transcribed_text=None, identified_speaker="Error")

#         # 1. Perform Speech-to-Text
#         try:
#             text = self.recognizer.recognize_google(audio_data)
#             logger.info(f"STT Result: '{text}'")
#         except sr.UnknownValueError:
#             text = None
#             logger.warning("STT could not understand audio.")
#         except sr.RequestError as e:
#             text = None
#             logger.error(f"STT request failed; {e}")

#         # 2. Perform Speaker Recognition
#         identified_speaker = "Unknown"
#         best_confidence = 0.0
#         if self.voiceprints:
#             new_voiceprint = self._extract_voiceprint_conceptual(audio_data)
            
#             lowest_distance = float('inf')
            
#             for name, known_print in self.voiceprints.items():
#                 # Conceptual distance calculation (e.g., Euclidean distance between feature vectors)
#                 # In a real GMM-based system, this would be model.score(new_voiceprint)
#                 distance = np.linalg.norm(known_print - new_voiceprint)
#                 logger.debug(f"  Comparing with '{name}', conceptual distance: {distance:.2f}")

#                 if distance < lowest_distance:
#                     lowest_distance = distance
#                     identified_speaker = name.title()

#             # Convert distance to a conceptual confidence score
#             # This is a made-up conversion for demonstration.
#             best_confidence = max(0, 1.0 - (lowest_distance / 20.0))
            
#             # If confidence is too low, revert to "Unknown"
#             if best_confidence < 0.60:
#                 identified_speaker = "Unknown"
            
#             logger.info(f"Speaker Recognition Result: '{identified_speaker}' with {best_confidence:.2%} confidence.")
        
#         return SpeechAnalysisResult(
#             transcribed_text=text,
#             identified_speaker=identified_speaker,
#             confidence=best_confidence
#         )

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Advanced Speech Analyzer Prototype 🗣️🆔 ===")
#     print("=========================================================")
    
#     if not SPEECH_LIBS_AVAILABLE:
#         print("\nRequired libraries not found. This demo is non-functional.")
#     else:
#         # Clean up previous enrollment file for a fresh demo
#         if os.path.exists("voiceprints.pkl"):
#             os.remove("voiceprints.pkl")
            
#         analyzer = AdvancedSpeechAnalyzer()
#         mic = sr.Microphone()

#         # --- 1. Enroll Speakers ---
#         print("\n--- Step 1: Enrolling Speakers ---")
#         if not analyzer.voiceprints:
#             try:
#                 # In a real scenario, you'd use pre-recorded, clean audio files.
#                 # Here, we use the microphone for an interactive demo.
#                 analyzer.enroll_speaker(mic, speaker_name="Alice")
#                 print("-" * 20)
#                 analyzer.enroll_speaker(mic, speaker_name="Bob")
#             except Exception as e:
#                 print(f"\nCould not run interactive enrollment. Please ensure you have a working microphone. Error: {e}")
                
#         # --- 2. Analyze a new speech sample ---
#         if analyzer.voiceprints:
#             print("\n\n--- Step 2: Analyzing a New Voice ---")
#             print("A speaker (Alice or Bob) should now say a phrase like 'Devin, activate the primary protocol.'")
#             print("Listening for a 5-second clip...")
            
#             try:
#                 with mic as source:
#                     test_audio = analyzer.recognizer.listen(source, phrase_time_limit=5)
                
#                 print("\nAnalyzing clip...")
#                 analysis_result = analyzer.analyze_speech(test_audio)
                
#                 print("\n--- Analysis Complete ---")
#                 print(f"  Transcribed Text: '{analysis_result.transcribed_text}'")
#                 print(f"  Identified Speaker: '{analysis_result.identified_speaker}' (Confidence: {analysis_result.confidence:.2%})")

#             except Exception as e:
#                 print(f"\nCould not run analysis. Please ensure you have a working microphone. Error: {e}")
#         else:
#             print("\nSkipping analysis because no speakers are enrolled.")

#     print("\n=========================================================")
#     print("=== Advanced Speech Analyzer Prototype Complete ===")
#     print("=========================================================")

# Devin/modules/robotics/speaker_recognition.py
# Purpose: Provides Speaker Recognition (identifying who is speaking) by
#          training a model for each speaker's voiceprint.

import logging
import os
import pickle
from dataclasses import dataclass
from typing import Dict, Optional, Any

try:
    import numpy as np
    import librosa
    from sklearn.mixture import GaussianMixture
    import speech_recognition as sr
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("SpeakerRecognition")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class SpeakerRecognizer:
    """
    Identifies speakers by training a Gaussian Mixture Model (GMM)
    on the MFCC features of their voice.
    """
    def __init__(self, voiceprints_path: str = "voiceprints.pkl"):
        if not DEPS_AVAILABLE:
            raise ImportError(f"A required library is missing. Error: {_import_error}")
        
        self.recognizer = sr.Recognizer()
        self.voiceprints_path = voiceprints_path
        self.voiceprints: Dict[str, GaussianMixture] = {}
        self._load_voiceprints()

    def _load_voiceprints(self):
        """Loads pre-trained GMMs from a file."""
        if os.path.exists(self.voiceprints_path):
            with open(self.voiceprints_path, 'rb') as f:
                self.voiceprints = pickle.load(f)
            logger.info(f"Loaded {len(self.voiceprints)} known voiceprints.")

    def _save_voiceprints(self):
        """Saves the GMM database to a file."""
        with open(self.voiceprints_path, 'wb') as f:
            pickle.dump(self.voiceprints, f)
        logger.info(f"Saved {len(self.voiceprints)} voiceprints.")

    def _extract_voiceprint(self, audio: sr.AudioData) -> Optional[np.ndarray]:
        """Extracts Mel-Frequency Cepstral Coefficients (MFCCs) from audio."""
        try:
            # Convert audio data to a NumPy array
            samples = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
            # Extract MFCCs
            mfccs = librosa.feature.mfcc(y=samples.astype(float), sr=audio.sample_rate, n_mfcc=20)
            return mfccs.T # Transpose to have features as columns
        except Exception as e:
            logger.error(f"Failed to extract voiceprint features: {e}")
            return None

    def enroll_speaker(self, audio_data: sr.AudioData, speaker_name: str):
        """Trains a GMM for a new speaker and saves it."""
        logger.info(f"Enrolling new speaker: '{speaker_name}'...")
        features = self._extract_voiceprint(audio_data)
        if features is None:
            logger.error("Enrollment failed: Could not extract features.")
            return

        gmm = GaussianMixture(n_components=16, covariance_type='diag', n_init=3)
        gmm.fit(features)
        
        self.voiceprints[speaker_name.lower()] = gmm
        self._save_voiceprints()
        logger.info(f"Speaker '{speaker_name}' enrolled successfully.")

    def identify_speaker(self, audio_data: sr.AudioData) -> Optional[str]:
        """Identifies the speaker in an audio clip."""
        if not self.voiceprints:
            logger.warning("No speakers enrolled. Cannot identify.")
            return "Unknown"
            
        features = self._extract_voiceprint(audio_data)
        if features is None: return "Unknown"
            
        scores = {}
        for name, gmm in self.voiceprints.items():
            scores[name] = gmm.score(features)
        
        # The GMM with the highest log-likelihood score is the winner
        identified_speaker = max(scores, key=scores.get)
        logger.info(f"Identification complete. Best match: {identified_speaker.title()} (Score: {scores[identified_speaker]:.2f})")
        return identified_speaker.title()


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Speaker Recognition (Live Demo) 🗣️🆔 ===")
    print("=========================================================")
    
    if not DEPS_AVAILABLE:
        print(f"\nERROR: A required library is missing: {_import_error}")
        print("Please run: 'pip install librosa scikit-learn SpeechRecognition PyAudio'")
    else:
        # Clean up previous enrollment file for a fresh demo
        if os.path.exists("voiceprints.pkl"):
            os.remove("voiceprints.pkl")
            
        analyzer = SpeakerRecognizer()
        mic = sr.Microphone()

        try:
            # --- 1. Enroll Speakers ---
            print("\n--- Step 1: Enrolling Speakers ---")
            print("This demo requires two speakers for enrollment.")
            
            for i in range(2):
                speaker_name = input(f"Enter the name for Speaker {i+1}: ")
                if not speaker_name: continue
                
                print(f"\nHello, {speaker_name}! Please say the following phrase clearly into your microphone:")
                print("--- 'The quick brown fox jumps over the lazy dog' ---")
                input("Press Enter when you are ready to record...")

                with mic as source:
                    analyzer.recognizer.adjust_for_ambient_noise(source)
                    audio = analyzer.recognizer.listen(source, phrase_time_limit=7)
                    analyzer.enroll_speaker(audio, speaker_name)
            
            # --- 2. Analyze a new speech sample ---
            if analyzer.voiceprints:
                print("\n\n--- Step 2: Identifying a New Speaker ---")
                print("One of the enrolled speakers should now say a new sentence.")
                print("For example: 'Devin, activate the primary protocol.'")
                input("Press Enter when you are ready to record for identification...")
                
                with mic as source:
                    analyzer.recognizer.adjust_for_ambient_noise(source)
                    test_audio = analyzer.recognizer.listen(source, phrase_time_limit=5)
                
                print("\nAnalyzing clip...")
                identified_speaker = analyzer.identify_speaker(test_audio)
                
                print("\n--- Identification Complete ---")
                print(f"I believe the speaker is: {identified_speaker}")

        except Exception as e:
            print(f"\nAn error occurred during the demo. Please ensure you have a working microphone. Error: {e}")

    print("\n=========================================================")
    print("=== Speaker Recognition Prototype Complete ===")
    print("=========================================================")
