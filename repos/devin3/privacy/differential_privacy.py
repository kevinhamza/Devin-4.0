# Devin/privacy/differential_privacy.py
# Purpose: A toolkit for applying differential privacy mechanisms to data,
#          allowing for statistical analysis with formal privacy guarantees.

import logging
import numpy as np
from typing import List, Dict, Tuple, Union

try:
    import diffprivlib.models as dp
    DIFFPRIVLIB_AVAILABLE = True
except ImportError:
    DIFFPRIVLIB_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("DifferentialPrivacy")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class DifferentialPrivacy:
    """
    Applies differential privacy mechanisms to queries on datasets.
    """
    def __init__(self):
        if not DIFFPRIVLIB_AVAILABLE:
            raise ImportError("The 'diffprivlib' library is required. 'pip install diffprivlib'")

    def get_private_mean(self, data: List[Union[int, float]], epsilon: float, data_bounds: Tuple[float, float]) -> float:
        """
        Calculates the differentially private mean of a numerical dataset.

        Args:
            data (List): The list of numbers to be averaged.
            epsilon (float): The privacy budget (epsilon > 0). Smaller values mean more privacy/noise.
            data_bounds (Tuple): A tuple (min, max) specifying the known bounds of the data.

        Returns:
            The differentially private mean of the data.
        """
        if epsilon <= 0:
            raise ValueError("Epsilon must be positive.")
        
        logger.info(f"Calculating private mean with epsilon={epsilon}...")
        # diffprivlib's Mean model is a simple way to apply the Laplace mechanism
        private_mean_calculator = dp.Mean(epsilon=epsilon, bounds=data_bounds)
        
        # The library expects a numpy array of shape (n_samples, n_features)
        numpy_data = np.array(data).reshape(-1, 1)
        
        private_mean_calculator.fit(numpy_data)
        
        return private_mean_calculator.predict(np.array([[0]]))[0]

    def get_private_histogram(self, data: List[str], epsilon: float) -> Dict[str, float]:
        """
        Calculates a differentially private histogram (counts) for a categorical dataset.

        Args:
            data (List): The list of categorical data (strings).
            epsilon (float): The privacy budget (epsilon > 0).
        
        Returns:
            A dictionary where keys are the categories and values are the noisy counts.
        """
        if epsilon <= 0:
            raise ValueError("Epsilon must be positive.")

        logger.info(f"Calculating private histogram with epsilon={epsilon}...")
        
        # Get the unique categories (the "bins" of our histogram)
        categories = list(set(data))
        
        private_histogram_calculator = dp.Histogram(epsilon=epsilon, bins=categories)
        
        numpy_data = np.array(data).reshape(-1, 1)
        private_histogram_calculator.fit(numpy_data)
        
        # The result is a numpy array of counts corresponding to the 'bins' order.
        private_counts = private_histogram_calculator.predict(np.array([[""]]))[0]
        
        return dict(zip(categories, private_counts))


# --- Example Usage ---
if __name__ == "__main__":
    if not DIFFPRIVLIB_AVAILABLE:
        print("\nERROR: The 'diffprivlib' library is required.")
        print("Please run: pip install diffprivlib")
    else:
        print("=========================================================")
        print("=== Differential Privacy Prototype 🤫📊 ===")
        print("=========================================================")
        print("This demo shows how differential privacy adds noise to protect individual data points while preserving statistical utility.")

        dp_toolkit = DifferentialPrivacy()

        # --- 1. Private Mean Demo ---
        print("\n\n--- 1. Private Mean Calculation ---")
        # Imagine this is sensitive data like user ages from a database
        ages = [25, 31, 45, 62, 28, 33, 50, 39, 22, 58]
        age_bounds = (18, 100) # We know ages fall within these bounds
        true_mean = np.mean(ages)
        
        print(f"Original dataset of ages: {ages}")
        print(f"The TRUE mean of the ages is: {true_mean:.2f}")
        
        # Run the private calculation multiple times to show the noise effect
        print("\nCalculating private mean with epsilon=1.0 (moderate privacy)...")
        for i in range(3):
            private_mean = dp_toolkit.get_private_mean(ages, epsilon=1.0, data_bounds=age_bounds)
            print(f"  - Run {i+1}: Private mean is {private_mean:.2f} (differs by {abs(private_mean - true_mean):.2f})")

        # --- 2. Private Histogram Demo ---
        print("\n\n--- 2. Private Histogram Calculation ---")
        # Imagine these are vulnerability types found in different private user reports
        vuln_types = ["XSS", "SQLi", "XSS", "CSRF", "XSS", "SQLi", "IDOR", "XSS"]
        true_counts = {k: v for k, v in zip(*np.unique(vuln_types, return_counts=True))}
        
        print(f"Original dataset of vulnerabilities: {vuln_types}")
        print(f"The TRUE counts are: {true_counts}")

        # Run with a relatively high epsilon because counts are small
        print("\nCalculating private histogram with epsilon=0.5 (high privacy for counts)...")
        private_counts = dp_toolkit.get_private_histogram(vuln_types, epsilon=0.5)
        
        print("The PRIVATE (noisy) counts are:")
        for vuln, count in private_counts.items():
            print(f"  - {vuln}: {count:.2f} (True count was {true_counts.get(vuln, 0)})")


        print("\n=========================================================")
        print("=== Differential Privacy Prototype Complete ===")
        print("=========================================================")
