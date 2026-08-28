# # Devin/modules/robotics/anomaly_detection.py
# # Purpose: Provides an AI-based anomaly detection system to monitor real-time
# #          robotics data streams for unusual behavior that may indicate a fault.

# import logging
# from typing import Dict, Any, Optional, List
# import numpy as np

# # A real implementation would use scikit-learn
# # from sklearn.ensemble import IsolationForest

# # Configure basic logging
# logger = logging.getLogger("AnomalyDetection")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# # --- Conceptual Placeholder for the ML Model ---
# class MockIsolationForest:
#     """A conceptual placeholder for sklearn.ensemble.IsolationForest."""
#     def __init__(self, contamination=0.1):
#         self._is_fitted = False
#         self.contamination = contamination
#         logger.info(f"Conceptual IsolationForest initialized. Contamination set to {contamination}.")

#     def fit(self, X):
#         logger.info(f"Conceptual model fitting on data with shape {X.shape}...")
#         self._is_fitted = True
#         # In a real model, this step learns the structure of normal data.
#         self.normal_mean = np.mean(X, axis=0)
#         self.normal_std = np.std(X, axis=0)
#         logger.info("Conceptual model has been 'trained'.")

#     def predict(self, X):
#         if not self._is_fitted:
#             raise RuntimeError("Model must be fitted before prediction.")
        
#         predictions = []
#         for point in X:
#             # Simple simulation: if a point is more than 2 standard deviations
#             # away from the mean on any feature, flag it as an anomaly (-1).
#             distance_from_mean = np.abs(point - self.normal_mean)
#             if np.any(distance_from_mean > 2.5 * self.normal_std):
#                 predictions.append(-1) # Anomaly
#             else:
#                 predictions.append(1) # Inlier (normal)
#         return np.array(predictions)

# class AnomalyDetector:
#     """
#     Uses a machine learning model to detect anomalies in real-time data streams.
#     """
#     def __init__(self, features: List[str]):
#         """
#         Initializes the anomaly detector.

#         Args:
#             features (List[str]): A list of the data feature names the model
#                                   will be trained on (e.g., ['motor1_current', 'accel_x']).
#         """
#         self.features = features
#         self.model = MockIsolationForest(contamination='auto') # Let the model determine the threshold
#         logger.info(f"AnomalyDetector initialized for features: {self.features}")

#     def train(self, normal_behavior_data: np.ndarray):
#         """
#         Trains the anomaly detection model on a dataset of normal operational data.

#         Args:
#             normal_behavior_data (np.ndarray): A 2D NumPy array where rows are
#                                                timesteps and columns match the features.
#         """
#         if normal_behavior_data.shape[1] != len(self.features):
#             raise ValueError(f"Input data has {normal_behavior_data.shape[1]} columns, but model expects {len(self.features)} features.")
        
#         logger.info("Training anomaly detection model on normal behavior data...")
#         self.model.fit(normal_behavior_data)
#         logger.info("Model training complete.")

#     def check_for_anomaly(self, current_data_point: Dict[str, float]) -> bool:
#         """
#         Checks if a single, new data point is an anomaly.

#         Args:
#             current_data_point (Dict[str, float]): A dictionary of the latest sensor
#                                                    readings, matching the model's features.

#         Returns:
#             bool: True if the point is an anomaly, False otherwise.
#         """
#         try:
#             # Convert dictionary to a NumPy array in the correct order
#             data_vector = np.array([[current_data_point[f] for f in self.features]])
#         except KeyError as e:
#             logger.error(f"Missing feature in data point: {e}")
#             return False # Cannot classify if data is incomplete

#         prediction = self.model.predict(data_vector)
        
#         is_anomaly = (prediction[0] == -1)
        
#         if is_anomaly:
#             logger.warning(f"ANOMALY DETECTED! Data point {current_data_point} is unusual.")
        
#         return is_anomaly

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== AI-Based Anomaly Detection Prototype 📈❗ ===")
#     print("=========================================================")

#     # 1. Define the features we want to monitor
#     # Let's monitor the current of two arm motors and the vibration on the x-axis.
#     MONITORED_FEATURES = ['motor2_current', 'motor3_current', 'accelerometer_x']

#     # 2. Generate some simulated "normal" training data
#     # Normal operation: motor currents are low, and vibration is minimal.
#     print("--- Step 1: Generating simulated 'normal' operational data ---")
#     mean_normal = [1.2, 1.3, 0.05] # Amps, Amps, G's
#     cov_normal = np.diag([0.1, 0.1, 0.01]) # Small variance
#     normal_data = np.random.multivariate_normal(mean_normal, cov_normal, 500)
#     print(f"Generated {len(normal_data)} normal data points.")

#     # 3. Initialize and train the detector
#     print("\n--- Step 2: Training the anomaly detection model ---")
#     detector = AnomalyDetector(features=MONITORED_FEATURES)
#     detector.train(normal_behavior_data=normal_data)

#     # 4. Test the detector with new data points
#     print("\n--- Step 3: Checking new, incoming data points ---")
    
#     # Point 1: A normal data point
#     normal_point = {'motor2_current': 1.25, 'motor3_current': 1.32, 'accelerometer_x': 0.06}
#     print(f"\nChecking normal point: {normal_point}")
#     is_anomaly = detector.check_for_anomaly(normal_point)
#     print(f"  -> Is it an anomaly? {is_anomaly}") # Expected: False

#     # Point 2: An anomalous data point (e.g., robot arm hit something)
#     # Motor current spikes, and there's a large vibration.
#     anomaly_point = {'motor2_current': 5.8, 'motor3_current': 1.4, 'accelerometer_x': 2.5}
#     print(f"\nChecking anomalous point: {anomaly_point}")
#     is_anomaly = detector.check_for_anomaly(anomaly_point)
#     print(f"  -> Is it an anomaly? {is_anomaly}") # Expected: True
    
#     # Point 3: Another normal data point
#     normal_point_2 = {'motor2_current': 1.18, 'motor3_current': 1.29, 'accelerometer_x': -0.04}
#     print(f"\nChecking another normal point: {normal_point_2}")
#     is_anomaly = detector.check_for_anomaly(normal_point_2)
#     print(f"  -> Is it an anomaly? {is_anomaly}") # Expected: False

#     print("\n=========================================================")
#     print("=== Anomaly Detection Prototype Complete ===")
#     print("=========================================================")



# Devin/modules/robotics/anomaly_detection.py
# Purpose: A functional, AI-based anomaly detection system that trains on
#          historical data to monitor real-time streams for faults.

import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional

try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import IsolationForest
    # For the live demo, we'll use our DataLogger
    from modules.robotics.data_logger import DataLogger
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("AnomalyDetection")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class AnomalyDetector:
    """
    Uses a scikit-learn IsolationForest model to detect anomalies in data streams.
    """
    def __init__(self, features: List[str], model_path: str = "anomaly_model.pkl"):
        if not DEPS_AVAILABLE:
            raise ImportError(f"Required libraries missing. Error: {_import_error}")
            
        self.features = features
        self.model_path = Path(model_path)
        self.model: Optional[IsolationForest] = None
        self._load_model()

    def _load_model(self):
        """Loads a pre-trained model from disk if it exists."""
        if self.model_path.exists():
            logger.info(f"Loading pre-trained anomaly detection model from '{self.model_path}'...")
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            logger.info("Model loaded successfully.")
        else:
            logger.warning("No pre-trained model found. The model must be trained before use.")
            self.model = IsolationForest(contamination='auto', random_state=42)

    def train(self, normal_behavior_data: pd.DataFrame):
        """
        Trains the IsolationForest model and saves it to disk.

        Args:
            normal_behavior_data (pd.DataFrame): A DataFrame where columns match
                                                  the detector's features.
        """
        if not all(f in normal_behavior_data.columns for f in self.features):
            raise ValueError("The training data is missing one or more required feature columns.")
            
        X_train = normal_behavior_data[self.features]
        
        logger.info(f"Training anomaly detection model on {len(X_train)} data points...")
        self.model.fit(X_train)
        logger.info("Model training complete.")
        
        # Save the trained model for future use
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Trained model saved to '{self.model_path}'.")

    def check_for_anomaly(self, current_data_point: Dict[str, float]) -> bool:
        """Checks if a single, new data point is an anomaly."""
        if not isinstance(self.model, IsolationForest) or not hasattr(self.model, 'estimators_'):
             raise RuntimeError("Model is not trained. Please call the 'train' method first.")
            
        try:
            # Create a DataFrame from the dict to ensure column order
            data_df = pd.DataFrame([current_data_point], columns=self.features)
            prediction = self.model.predict(data_df)
            
            is_anomaly = (prediction[0] == -1)
            if is_anomaly:
                logger.warning(f"ANOMALY DETECTED! Data point {current_data_point} is unusual.")
            
            return is_anomaly
        except (KeyError, ValueError) as e:
            logger.error(f"Prediction failed. Data point may be malformed. Error: {e}")
            return False

# --- Example Usage with a Full Log -> Train -> Detect Pipeline ---
if __name__ == "__main__":
    import time
    
    print("=========================================================")
    print("=== Integrated Anomaly Detection (Live ML Demo) 📈❗ ===")
    print("=========================================================")
    
    if not DEPS_AVAILABLE:
        print(f"\nERROR: A required library is missing: {_import_error}")
        print("Please run: 'pip install scikit-learn pandas pyarrow'")
    else:
        MONITORED_FEATURES = ['motor_current', 'imu_accel_z']
        MODEL_FILE = Path("demo_anomaly_model.pkl")
        LOG_FILE = Path("robot_logs/normal_operation.feather")
        
        # Clean up old files for a fresh demo
        if MODEL_FILE.exists(): MODEL_FILE.unlink()
        if LOG_FILE.exists(): LOG_FILE.unlink()

        try:
            # --- 1. Generate a "Normal Operation" Log File ---
            print("\n--- 1. Generating a log file of normal robot behavior ---")
            logger.info("This simulates running the robot for a while to gather baseline data.")
            data_logger = DataLogger(log_directory=LOG_FILE.parent)
            data_logger.start_logging()
            
            for _ in range(500):
                # Normal current is ~1.2A with some noise, normal Z-accel is ~9.8
                normal_point = {
                    'motor_current': np.random.normal(1.2, 0.1),
                    'imu_accel_z': np.random.normal(9.8, 0.05)
                }
                data_logger.log(topic="sensor_stream", data=normal_point)
                time.sleep(0.001)
            
            data_logger.stop_logging()
            print(f"  Normal data logged to '{LOG_FILE}'")

            # --- 2. Train the Anomaly Detector ---
            print("\n--- 2. Training the anomaly detection model from the log file ---")
            training_data = pd.read_feather(LOG_FILE)
            detector = AnomalyDetector(features=MONITORED_FEATURES, model_path=str(MODEL_FILE))
            detector.train(normal_behavior_data=training_data)
            
            # --- 3. Live Monitoring Simulation ---
            print("\n--- 3. Simulating a live data stream for anomaly detection ---")
            print("     (Will inject an anomaly after a few seconds)")
            
            for i in range(10):
                if i == 5: # Inject an anomaly!
                    live_point = {'motor_current': 8.5, 'imu_accel_z': 9.7} # Current spikes
                    print(f"\nInjecting ANOMALOUS data point: {live_point}")
                else:
                    live_point = {
                        'motor_current': np.random.normal(1.2, 0.1),
                        'imu_accel_z': np.random.normal(9.8, 0.05)
                    }
                
                is_anomaly = detector.check_for_anomaly(live_point)
                status = "ANOMALY" if is_anomaly else "NORMAL"
                print(f"  t={i+1}s | Status: {status}")
                time.sleep(0.5)

        except (ImportError, RuntimeError, ValueError) as e:
            logger.error(f"Demo failed to run. Error: {e}", exc_info=True)
        finally:
             # Clean up generated files
            if MODEL_FILE.exists(): MODEL_FILE.unlink()
            if LOG_FILE.exists(): LOG_FILE.unlink()

    print("\n=========================================================")
    print("=== Anomaly Detection Demo Complete ===")
    print("=========================================================")
