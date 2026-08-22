# Devin/security/incident_response/ransomware_detector.py
# Purpose: An ML-based tool for detecting ransomware activity by monitoring
#          filesystem events and analyzing file entropy in real-time.

import logging
import os
import math
import time
import threading
from pathlib import Path
from collections import deque
from typing import Optional, List, Deque

# --- Core Dependencies ---
try:
    import numpy as np
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    import joblib
    from cryptography.fernet import Fernet
    ML_LIBS_AVAILABLE = True
except ImportError:
    ML_LIBS_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("RansomwareDetector")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


def _calculate_entropy(data: bytes) -> float:
    """Calculates the Shannon entropy of a byte string."""
    if not data:
        return 0
    entropy = 0
    for x in range(256):
        p_x = float(data.count(x)) / len(data)
        if p_x > 0:
            entropy += -p_x * math.log(p_x, 2)
    return entropy


class FeatureExtractor(FileSystemEventHandler):
    """A watchdog event handler that extracts features from filesystem events."""
    def __init__(self, window_size_sec: int = 5):
        self.window_size = window_size_sec
        self.event_queue: Deque[dict] = deque()
        self.feature_vectors: Deque[List] = deque()
        
        self._thread = threading.Thread(target=self._process_events, daemon=True)
        self._stop_event = threading.Event()
        
    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def on_any_event(self, event):
        """Captures all filesystem events."""
        event_data = {
            "type": event.event_type,
            "path": event.src_path,
            "time": time.time(),
            "is_dir": event.is_directory,
        }
        self.event_queue.append(event_data)

    def _process_events(self):
        """Processes events in time windows to generate feature vectors."""
        while not self._stop_event.is_set():
            time.sleep(self.window_size)
            
            cutoff_time = time.time() - self.window_size
            
            # Get all events from the current window
            window_events = []
            while self.event_queue and self.event_queue[0]['time'] <= cutoff_time:
                window_events.append(self.event_queue.popleft())
            
            if not window_events:
                continue

            # Calculate features for this window
            creations = sum(1 for e in window_events if e['type'] == 'created' and not e['is_dir'])
            modifications = sum(1 for e in window_events if e['type'] == 'modified' and not e['is_dir'])
            deletions = sum(1 for e in window_events if e['type'] == 'deleted' and not e['is_dir'])
            renames = sum(1 for e in window_events if e['type'] == 'moved' and not e['is_dir'])

            entropies = []
            for e in window_events:
                if e['type'] == 'modified' and not e['is_dir']:
                    try:
                        with open(e['path'], 'rb') as f:
                            entropies.append(_calculate_entropy(f.read()))
                    except (IOError, FileNotFoundError):
                        pass
            
            avg_entropy = np.mean(entropies) if entropies else 0
            
            # Feature vector
            vector = [creations, modifications, deletions, renames, avg_entropy]
            self.feature_vectors.append(vector)


class RansomwareDetector:
    """The main class for training and running the ransomware detector."""
    def __init__(self, model_path: Path = Path("ransomware_detector.joblib")):
        if not ML_LIBS_AVAILABLE:
            raise ImportError("Required libraries missing. 'pip install scikit-learn numpy watchdog joblib cryptography'")
        self.model_path = model_path
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)
        else:
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            
    def train_model(self, base_dir: Path):
        """Generates training data and trains the detection model."""
        logger.warning("--- Starting Model Training ---")
        base_dir.mkdir(exist_ok=True)
        
        features = []
        labels = []
        
        # 1. Generate "Normal" activity data
        logger.info("Simulating 'normal' user activity...")
        extractor = FeatureExtractor(window_size_sec=2)
        extractor.start()
        observer = Observer()
        observer.schedule(extractor, str(base_dir), recursive=True)
        observer.start()
        
        for i in range(10): # Simulate 10 windows of normal activity
            # Create and write low-entropy text files
            (base_dir / f"doc_{i}.txt").write_text("this is a normal document " * 200)
            time.sleep(0.5)
            # Modify files
            (base_dir / f"doc_{i}.txt").write_text("this is a normal document with an edit." * 200)
            time.sleep(1.5)
            
        observer.stop()
        observer.join()
        extractor.stop()
        
        features.extend(extractor.feature_vectors)
        labels.extend([0] * len(extractor.feature_vectors)) # Label 0 for normal
        
        # Clean up normal files
        for item in base_dir.iterdir(): item.unlink()

        # 2. Generate "Ransomware" activity data
        logger.info("Simulating 'ransomware' activity...")
        for i in range(10): # Create 10 files to be encrypted
             (base_dir / f"secret_{i}.txt").write_text(f"secret content {i}" * 200)

        extractor = FeatureExtractor(window_size_sec=2)
        extractor.start()
        observer = Observer()
        observer.schedule(extractor, str(base_dir), recursive=True)
        observer.start()

        # Simulate the ransomware attack
        key = Fernet.generate_key()
        fernet = Fernet(key)
        for item in base_dir.glob("*.txt"):
            encrypted_data = fernet.encrypt(item.read_bytes())
            item.write_bytes(encrypted_data)
            item.rename(item.with_suffix(".locked"))
            time.sleep(0.1) # Ransomware is fast

        time.sleep(3) # Wait for the last window to be processed
        observer.stop()
        observer.join()
        extractor.stop()
        
        features.extend(extractor.feature_vectors)
        labels.extend([1] * len(extractor.feature_vectors)) # Label 1 for ransomware

        # 3. Train the classifier
        logger.info("Training the Random Forest classifier...")
        X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        logger.warning(f"Model training complete. Accuracy: {acc:.2%}")
        
        # 4. Save the trained model
        joblib.dump(self.model, self.model_path)
        logger.info(f"Model saved to {self.model_path}")
        logger.warning("--- Model Training Finished ---")

    def start_monitoring(self, directory_to_watch: Path):
        """Starts real-time monitoring of a directory for ransomware."""
        if not self.model_path.exists():
            logger.error("Model file not found. Please train the model first.")
            return

        logger.warning(f"--- Starting Real-Time Ransomware Monitoring on '{directory_to_watch}' ---")
        extractor = FeatureExtractor(window_size_sec=3)
        extractor.start()
        observer = Observer()
        observer.schedule(extractor, str(directory_to_watch), recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
                if extractor.feature_vectors:
                    latest_vector = extractor.feature_vectors.popleft()
                    prediction = self.model.predict([latest_vector])
                    if prediction[0] == 1:
                        logger.critical("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        logger.critical("!!! RANSOMWARE ACTIVITY DETECTED !!!")
                        logger.critical("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        # Here you could trigger other actions, like quarantining the host
        except KeyboardInterrupt:
            logger.warning("Monitoring stopped by user.")
        finally:
            observer.stop()
            observer.join()
            extractor.stop()

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== ML Ransomware Detector Prototype 🦠🤖 ===")
    print("=========================================================")

    if not ML_LIBS_AVAILABLE:
        print("\nERROR: Missing one or more required libraries.")
        print("Please run: pip install scikit-learn numpy watchdog joblib cryptography")
    else:
        # 1. Setup demo environment
        demo_dir = Path("./protected_folder")
        if demo_dir.exists(): shutil.rmtree(demo_dir)
        demo_dir.mkdir()
        
        detector = RansomwareDetector()

        try:
            # 2. Train the model
            detector.train_model(demo_dir.parent / "training_temp")
            
            # 3. Start monitoring a folder
            # For the demo, we run this in a thread so the main thread can trigger the attack
            monitor_thread = threading.Thread(target=detector.start_monitoring, args=(demo_dir,))
            monitor_thread.daemon = True
            monitor_thread.start()

            # Create some dummy files in the protected folder
            (demo_dir / "report.docx").write_text("This is my very important report.")
            (demo_dir / "family_photo.jpg").write_text("pretend this is image data")
            
            print("\n--- Real-time monitoring has started on './protected_folder'. ---")
            print("--- Simulating ransomware attack in 10 seconds... ---")
            time.sleep(10)

            # 4. Simulate the attack
            key = Fernet.generate_key()
            fernet = Fernet(key)
            for item in demo_dir.iterdir():
                if item.is_file():
                    logger.warning(f"(Attacker) Encrypting '{item.name}'...")
                    encrypted_data = fernet.encrypt(item.read_bytes())
                    item.write_bytes(encrypted_data)
                    item.rename(item.with_suffix(item.suffix + ".LOCKED"))
                    time.sleep(0.2)
            
            print("\n--- Attack simulation finished. Waiting for detection... ---")
            time.sleep(5) # Give the monitor time to react
        
        finally:
            # 5. Clean up
            if demo_dir.exists(): shutil.rmtree(demo_dir)
            training_dir = demo_dir.parent / "training_temp"
            if training_dir.exists(): shutil.rmtree(training_dir)
            if detector.model_path.exists(): detector.model_path.unlink()
            logger.info("Cleaned up demo files.")

    print("\n=========================================================")
    print("=== Ransomware Detector Prototype Complete ===")
    print("=========================================================")
