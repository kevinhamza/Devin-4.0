# Devin/security/ai_security/model_poisoning_detector.py
# Purpose: A tool to detect potential data poisoning attacks in machine
#          learning datasets using anomaly detection algorithms.

import logging
from typing import Optional

try:
    import numpy as np
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.datasets import make_blobs
    import matplotlib.pyplot as plt
    ML_LIBS_AVAILABLE = True
except ImportError:
    ML_LIBS_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("PoisoningDetector")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class ModelPoisoningDetector:
    """
    Uses anomaly detection to identify potentially poisoned data points.
    """
    def __init__(self, contamination: float = 0.05):
        """
        Initializes the detector.

        Args:
            contamination: The expected proportion of outliers (poisoned data)
                         in the dataset. This is a key parameter for the
                         Isolation Forest algorithm.
        """
        if not ML_LIBS_AVAILABLE:
            raise ImportError("Required libraries missing. 'pip install scikit-learn numpy matplotlib'")
        
        # Isolation Forest is an effective algorithm for anomaly detection.
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.scaler = StandardScaler()

    def detect_anomalies(self, dataset: np.ndarray) -> np.ndarray:
        """
        Analyzes a dataset to find outliers/anomalies.

        Args:
            dataset: A NumPy array of shape (n_samples, n_features).

        Returns:
            A NumPy array of predictions, where 1 indicates an inlier (clean)
            and -1 indicates an outlier (potentially poisoned).
        """
        logger.info(f"Analyzing dataset with shape {dataset.shape} for anomalies...")
        
        # 1. Scale the data for better performance
        scaled_data = self.scaler.fit_transform(dataset)
        
        # 2. Fit the model and predict which points are outliers
        predictions = self.model.fit_predict(scaled_data)
        
        num_anomalies = np.sum(predictions == -1)
        logger.warning(f"Detection complete. Found {num_anomalies} potential anomalies.")
        
        return predictions

    def visualize_detection(self, dataset: np.ndarray, predictions: np.ndarray, title: str):
        """
        Creates a 2D scatter plot to visualize the detected anomalies.
        NOTE: This is only effective for datasets with 2 features.
        """
        if dataset.shape[1] != 2:
            logger.warning("Visualization is only supported for 2D data.")
            return

        plt.style.use('fivethirtyeight')
        plt.figure(figsize=(10, 7))
        
        # Separate inliers and outliers
        inliers = dataset[predictions == 1]
        outliers = dataset[predictions == -1]
        
        # Plot the data
        plt.scatter(inliers[:, 0], inliers[:, 1], c='cornflowerblue', s=50, label='Clean Data (Inliers)')
        plt.scatter(outliers[:, 0], outliers[:, 1], c='red', s=50, edgecolor='k', label='Poisoned Data (Outliers)')
        
        plt.title(title)
        plt.xlabel("Feature 1")
        plt.ylabel("Feature 2")
        plt.legend()
        plt.show()


# --- Example Usage ---
if __name__ == "__main__":
    if not ML_LIBS_AVAILABLE:
        print("\nERROR: Missing one or more required libraries. Please run: 'pip install scikit-learn numpy matplotlib'")
    else:
        print("=========================================================")
        print("=== AI Model Poisoning Detector Prototype 🧪🛡️ ===")
        print("=========================================================")
        print("This demo will create a sample dataset, inject poisoned data,")
        print("and then use an Isolation Forest to detect the anomalies.")
        
        # 1. Create a simulated dataset
        # 950 clean data points in a tight cluster
        clean_data, _ = make_blobs(n_samples=950, centers=[[2, 2]], cluster_std=0.5, random_state=42)
        # 50 poisoned data points in a separate, distant cluster
        poisoned_data, _ = make_blobs(n_samples=50, centers=[[-5, -5]], cluster_std=0.5, random_state=42)
        
        # Combine into a single dataset
        full_dataset = np.vstack([clean_data, poisoned_data])
        np.random.shuffle(full_dataset) # Shuffle to mix the data
        
        logger.info(f"Created a sample dataset of {len(full_dataset)} points with 5% poisoned data.")
        
        # 2. Initialize and run the detector
        # We set contamination to 0.05 because we know that 50/1000 points are poisoned.
        detector = ModelPoisoningDetector(contamination=0.05)
        anomaly_predictions = detector.detect_anomalies(full_dataset)

        # 3. Visualize the results
        print("\nDisplaying visualization... Close the plot window to exit.")
        detector.visualize_detection(full_dataset, anomaly_predictions, "Model Poisoning Detection Results")

        print("\n=========================================================")
        print("=== Poisoning Detector Prototype Complete ===")
        print("=========================================================")
