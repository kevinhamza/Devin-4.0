# Devin/mlops/data_validation/drift_detection.py
# Purpose: Conceptual implementations for detecting data drift, concept drift,
#          and prediction drift for model monitoring in an AI lifecycle.
# AI Lifecycle & Production AI 🧠🚀

import logging
import pandas as pd
import numpy as np
from scipy import stats # For Kolmogorov-Smirnov, Chi-Squared tests
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score # For performance monitoring
from sklearn.preprocessing import KBinsDiscretizer # For binning continuous data for PSI/Chi-squared
from typing import Dict, Any, List, Union, Optional, Literal

# Configure basic logging
logger = logging.getLogger("DriftDetector")
# Basic configuration for this module's logger, if not handled globally
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class DriftDetector:
    """
    A conceptual class for detecting various types of drift in ML models and data.
    This class provides methods to compare reference (e.g., training/baseline) data
    with current (e.g., live production) data.
    """

    PSI_THRESHOLDS = {
        "no_drift": 0.1,
        "minor_drift": 0.2,
        # Anything above 0.2 can be considered major drift
    }

    def __init__(self, reference_dataframe: Optional[pd.DataFrame] = None):
        """
        Initializes the DriftDetector.

        Args:
            reference_dataframe (Optional[pd.DataFrame]): A Pandas DataFrame representing the
                                                         reference dataset (e.g., training data).
                                                         If provided, some methods might use it to
                                                         establish baselines automatically.
        """
        self.reference_df = reference_dataframe
        if self.reference_df is not None:
            logger.info(f"DriftDetector initialized with reference data of shape {self.reference_df.shape}.")
        else:
            logger.info("DriftDetector initialized without reference data. Reference data must be passed to detection methods.")

    def _get_data_series(self,
                         data: Union[pd.DataFrame, pd.Series, np.ndarray],
                         feature_name: Optional[str] = None) -> pd.Series:
        """Helper to extract a Pandas Series from various input types."""
        if isinstance(data, pd.Series):
            return data
        elif isinstance(data, pd.DataFrame):
            if feature_name is None or feature_name not in data.columns:
                raise ValueError("If data is DataFrame, feature_name must be provided and exist in columns.")
            return data[feature_name]
        elif isinstance(data, np.ndarray):
            return pd.Series(data.flatten()) # Flatten in case of multi-dim array, though 1D expected
        else:
            raise TypeError(f"Unsupported data type: {type(data)}. Expected pd.DataFrame, pd.Series, or np.ndarray.")

    def detect_univariate_numerical_drift_ks(self,
                                             reference_data: Union[pd.Series, np.ndarray, List[float]],
                                             current_data: Union[pd.Series, np.ndarray, List[float]],
                                             feature_name: str,
                                             alpha: float = 0.05) -> Dict[str, Any]:
        """
        Detects drift in a numerical feature using the two-sample Kolmogorov-Smirnov (KS) test.
        The KS test compares the cumulative distributions of two data samples.
        Null hypothesis (H0): The two samples are drawn from the same distribution.
        If p-value < alpha, H0 is rejected, indicating significant drift.

        Args:
            reference_data: Reference data sample (e.g., from training set).
            current_data: Current data sample (e.g., from production).
            feature_name (str): Name of the numerical feature being tested.
            alpha (float): Significance level for the test.

        Returns:
            Dict[str, Any]: Results including drift status, p-value, and KS statistic.
        """
        ref_series = self._get_data_series(reference_data)
        curr_series = self._get_data_series(current_data)

        if ref_series.empty or curr_series.empty:
            logger.warning(f"KS Test for '{feature_name}': One or both data samples are empty. Cannot perform test.")
            return {"feature_name": feature_name, "drift_detected": None, "message": "Empty data sample(s)."}

        # Remove NaNs as KS test doesn't handle them directly in scipy.stats
        ref_series_cleaned = ref_series.dropna()
        curr_series_cleaned = curr_series.dropna()

        if ref_series_cleaned.empty or curr_series_cleaned.empty:
            logger.warning(f"KS Test for '{feature_name}': One or both data samples are empty after NaN removal.")
            return {"feature_name": feature_name, "drift_detected": None, "message": "Empty data sample(s) after NaN removal."}

        statistic, p_value = stats.ks_2samp(ref_series_cleaned, curr_series_cleaned)
        drift_detected = p_value < alpha

        logger.info(
            f"KS Test for '{feature_name}': Statistic={statistic:.4f}, P-value={p_value:.4f}. "
            f"Alpha={alpha}. Drift detected: {drift_detected}."
        )
        return {
            "feature_name": feature_name,
            "test_type": "Kolmogorov-Smirnov",
            "drift_detected": drift_detected,
            "p_value": p_value,
            "statistic": statistic,
            "alpha": alpha,
            "reference_size": len(ref_series_cleaned),
            "current_size": len(curr_series_cleaned),
        }

    def detect_univariate_categorical_drift_chisquare(self,
                                                      reference_data: Union[pd.Series, np.ndarray, List[Any]],
                                                      current_data: Union[pd.Series, np.ndarray, List[Any]],
                                                      feature_name: str,
                                                      alpha: float = 0.05,
                                                      min_expected_freq: int = 5) -> Dict[str, Any]:
        """
        Detects drift in a categorical feature using the Chi-Squared goodness-of-fit test.
        This compares the observed frequencies of categories in the current data
        against the expected frequencies derived from the reference data.
        Null hypothesis (H0): The observed frequencies match the expected frequencies (no drift).
        If p-value < alpha, H0 is rejected, indicating significant drift.

        Args:
            reference_data: Reference data sample.
            current_data: Current data sample.
            feature_name (str): Name of the categorical feature.
            alpha (float): Significance level.
            min_expected_freq (int): Minimum expected frequency for categories. Categories below this
                                     might be grouped or test might be less reliable.

        Returns:
            Dict[str, Any]: Results including drift status, p-value, and Chi-Squared statistic.
        """
        ref_series = self._get_data_series(reference_data).astype(str).dropna() # Ensure string type for categories and dropna
        curr_series = self._get_data_series(current_data).astype(str).dropna()

        if ref_series.empty or curr_series.empty:
            logger.warning(f"Chi-Squared Test for '{feature_name}': One or both data samples are empty. Cannot perform test.")
            return {"feature_name": feature_name, "drift_detected": None, "message": "Empty data sample(s)."}

        ref_counts = ref_series.value_counts(normalize=False)
        curr_counts = curr_series.value_counts(normalize=False)

        # Combine all unique categories from both reference and current data
        all_categories = sorted(list(set(ref_counts.index) | set(curr_counts.index)))

        if not all_categories:
            return {"feature_name": feature_name, "drift_detected": None, "message": "No categories found in data."}

        # Observed frequencies from current data, aligned with all categories
        observed_freq = curr_counts.reindex(all_categories, fill_value=0).values

        # Expected frequencies based on reference data distribution and current data size
        ref_proportions = ref_counts.reindex(all_categories, fill_value=0) / len(ref_series)
        expected_freq = (ref_proportions * len(curr_series)).values
        
        # Filter out categories where expected frequency is zero to avoid division by zero in chi2
        # and to handle categories present in current but not reference (expected_freq=0).
        # The chi-squared test typically expects non-zero expected frequencies.
        valid_indices = expected_freq > 1e-9 # Use a small epsilon instead of 0
        observed_freq_filtered = observed_freq[valid_indices]
        expected_freq_filtered = expected_freq[valid_indices]

        if len(observed_freq_filtered) < 2: # Chi-squared needs at least 2 categories typically
             logger.warning(f"Chi-Squared Test for '{feature_name}': Not enough categories with non-zero expected frequency after filtering ({len(observed_freq_filtered)} found).")
             return {"feature_name": feature_name, "drift_detected": None, "message": "Too few categories for reliable Chi-Squared test after filtering zero expected frequencies."}

        # Check for low expected frequencies (can make Chi-Squared unreliable)
        if np.any(expected_freq_filtered < min_expected_freq):
            logger.warning(
                f"Chi-Squared Test for '{feature_name}': Some categories have expected frequency < {min_expected_freq}. "
                "Results might be less reliable. Consider grouping categories or using Fisher's exact test for small samples."
            )

        statistic, p_value = stats.chisquare(f_obs=observed_freq_filtered, f_exp=expected_freq_filtered)
        drift_detected = p_value < alpha

        logger.info(
            f"Chi-Squared Test for '{feature_name}': Statistic={statistic:.4f}, P-value={p_value:.4f}. "
            f"Alpha={alpha}. Drift detected: {drift_detected}."
        )
        return {
            "feature_name": feature_name,
            "test_type": "Chi-Squared Goodness-of-Fit",
            "drift_detected": drift_detected,
            "p_value": p_value,
            "statistic": statistic,
            "alpha": alpha,
            "degrees_of_freedom": len(observed_freq_filtered) - 1,
            "reference_size": len(ref_series),
            "current_size": len(curr_series),
        }

    def calculate_population_stability_index(self,
                                             reference_data: Union[pd.Series, np.ndarray, List[Any]],
                                             current_data: Union[pd.Series, np.ndarray, List[Any]],
                                             feature_name: str,
                                             num_bins: int = 10,
                                             binning_strategy: Literal['uniform', 'quantile', 'kmeans'] = 'quantile',
                                             is_categorical: bool = False) -> Dict[str, Any]:
        """
        Calculates the Population Stability Index (PSI) for a single feature.
        PSI measures how much a variable's distribution has shifted between two samples.
        Common interpretation:
            - PSI < 0.1: No significant drift.
            - 0.1 <= PSI < 0.2: Minor drift.
            - PSI >= 0.2: Major drift, investigate.

        Args:
            reference_data: Reference data sample.
            current_data: Current data sample.
            feature_name (str): Name of the feature.
            num_bins (int): Number of bins to use for numerical data or max categories for categorical.
            binning_strategy (str): Strategy for binning numerical data ('uniform', 'quantile', 'kmeans').
            is_categorical (bool): True if the feature is categorical. If True, num_bins acts as max categories considered.

        Returns:
            Dict[str, Any]: PSI value and drift magnitude interpretation.
        """
        ref_series = self._get_data_series(reference_data).dropna()
        curr_series = self._get_data_series(current_data).dropna()

        if ref_series.empty or curr_series.empty:
            logger.warning(f"PSI for '{feature_name}': One or both data samples are empty. Cannot calculate PSI.")
            return {"feature_name": feature_name, "psi_value": np.nan, "drift_magnitude": "Error: Empty data."}

        if is_categorical:
            ref_counts = ref_series.value_counts(normalize=True)
            curr_counts = curr_series.value_counts(normalize=True)
            all_categories = sorted(list(set(ref_counts.index) | set(curr_counts.index)))

            ref_proportions = ref_counts.reindex(all_categories, fill_value=0.0)
            curr_proportions = curr_counts.reindex(all_categories, fill_value=0.0)
        else: # Numerical: Bin the data
            # Combine data to determine global bins based on reference distribution or combined
            combined_data_for_binning = pd.concat([ref_series, curr_series]) # Or just ref_series if bins should be static
            
            # Using KBinsDiscretizer to find bin edges based on reference data
            # This ensures bins are consistent.
            if len(np.unique(ref_series)) <=1 : # Not enough unique values to bin
                 logger.warning(f"PSI for '{feature_name}': Not enough unique values in reference data to bin. Treating as single category or returning NaN.")
                 # Fallback to treating as a single category or returning error
                 if len(np.unique(combined_data_for_binning)) <=1:
                      return {"feature_name": feature_name, "psi_value": 0.0, "drift_magnitude": "No Drift (single value)"} # Or error
                 # If not, this path might lead to issues with discretizer, so we should handle it.
                 # For simplicity, let's assume this won't happen with diverse enough data.


            discretizer = KBinsDiscretizer(n_bins=num_bins, encode='ordinal', strategy=binning_strategy, subsample=None) # subsample=None for newer sklearn
            
            try:
                # Fit on reference data to establish bins
                discretizer.fit(ref_series.values.reshape(-1, 1))
                # Transform both reference and current data using these bins
                ref_binned = discretizer.transform(ref_series.values.reshape(-1, 1)).flatten()
                curr_binned = discretizer.transform(curr_series.values.reshape(-1, 1)).flatten()
            except ValueError as e:
                 logger.error(f"PSI for '{feature_name}': Error during binning ({e}). Check data variance and num_bins.")
                 return {"feature_name": feature_name, "psi_value": np.nan, "drift_magnitude": "Error: Binning failed."}


            ref_proportions = pd.Series(ref_binned).value_counts(normalize=True).sort_index()
            curr_proportions = pd.Series(curr_binned).value_counts(normalize=True).sort_index()
            
            # Ensure both series have the same bins after value_counts
            all_bins = sorted(list(set(ref_proportions.index) | set(curr_proportions.index)))
            ref_proportions = ref_proportions.reindex(all_bins, fill_value=0.0)
            curr_proportions = curr_proportions.reindex(all_bins, fill_value=0.0)


        # Replace 0 with a very small number to avoid division by zero in log
        ref_proportions = ref_proportions.replace(0, 0.00001)
        curr_proportions = curr_proportions.replace(0, 0.00001)

        psi_values_per_bin = (curr_proportions - ref_proportions) * np.log(curr_proportions / ref_proportions)
        psi = np.sum(psi_values_per_bin)

        if psi < self.PSI_THRESHOLDS["no_drift"]:
            magnitude = "No Significant Drift"
        elif psi < self.PSI_THRESHOLDS["minor_drift"]:
            magnitude = "Minor Drift"
        else:
            magnitude = "Major Drift (Investigate)"

        logger.info(f"PSI for '{feature_name}': Value={psi:.4f}. Magnitude: {magnitude}.")
        return {
            "feature_name": feature_name,
            "psi_value": psi,
            "drift_magnitude": magnitude,
            "reference_proportions": ref_proportions.to_dict(),
            "current_proportions": curr_proportions.to_dict()
        }

    def monitor_performance_degradation(self,
                                        y_true_current: Union[np.ndarray, List[Any]],
                                        y_pred_current: Union[np.ndarray, List[Any]],
                                        baseline_metrics: Dict[str, float],
                                        metric_tolerances_relative: Optional[Dict[str, float]] = None,
                                        metric_functions: Optional[Dict[str, callable]] = None
                                        ) -> Dict[str, Any]:
        """
        Monitors model performance degradation by comparing current performance
        metrics against baseline metrics. This is a key way to detect concept drift.

        Args:
            y_true_current: True labels for the current evaluation period.
            y_pred_current: Model predictions for the current evaluation period.
            baseline_metrics (Dict[str, float]): Dictionary of baseline performance metrics
                                                 (e.g., {"accuracy": 0.95, "f1_score": 0.92}).
            metric_tolerances_relative (Optional[Dict[str, float]]): Dictionary of relative tolerance
                                                                    for degradation for each metric.
                                                                    E.g., {"accuracy": 0.05} means a 5% drop from baseline is flagged.
                                                                    If None, a default of 10% (0.1) is used.
            metric_functions (Optional[Dict[str, callable]]): Functions to calculate metrics.
                                                              Defaults to accuracy, f1, precision, recall.

        Returns:
            Dict[str, Any]: Current metrics and drift status for each monitored metric.
        """
        if metric_functions is None:
            metric_functions = {
                "accuracy": accuracy_score,
                "f1": f1_score, # Add average='weighted' or 'micro'/'macro' if needed for multiclass
                "precision": precision_score,
                "recall": recall_score
            }
        if metric_tolerances_relative is None:
            metric_tolerances_relative = {key: 0.10 for key in metric_functions.keys()} # Default 10% drop tolerance

        y_t = np.array(y_true_current)
        y_p = np.array(y_pred_current)

        results: Dict[str, Any] = {"overall_drift_detected": False, "metrics": {}}
        logger.info("Monitoring performance degradation (concept drift indicator)...")

        for metric_name, func in metric_functions.items():
            if metric_name not in baseline_metrics:
                logger.warning(f"Baseline metric for '{metric_name}' not provided. Skipping.")
                continue
            
            try:
                current_value = func(y_t, y_p) # Add relevant params like average for f1/precision/recall if needed
            except Exception as e:
                logger.error(f"Error calculating metric '{metric_name}': {e}. Skipping.")
                current_value = np.nan # Or handle as needed

            baseline_value = baseline_metrics[metric_name]
            tolerance = metric_tolerances_relative.get(metric_name, 0.10) # Default tolerance if not specified

            # Performance degradation means current value is lower than baseline minus tolerance margin
            # (assuming higher metric value is better)
            drift_detected = current_value < (baseline_value * (1 - tolerance))

            if drift_detected:
                results["overall_drift_detected"] = True

            results["metrics"][metric_name] = {
                "baseline_value": baseline_value,
                "current_value": current_value,
                "tolerance_relative": tolerance,
                "threshold_value": baseline_value * (1-tolerance),
                "drift_detected": drift_detected,
                "degradation_percentage": ((baseline_value - current_value) / baseline_value) * 100 if baseline_value > 1e-9 else np.nan
            }
            logger.info(
                f"  Metric '{metric_name}': Baseline={baseline_value:.4f}, Current={current_value:.4f}, "
                f"Drift Detected (Degradation): {drift_detected}"
            )
        
        return results

    def detect_prediction_drift_univariate(self,
                                           reference_predictions: Union[pd.Series, np.ndarray, List[Any]],
                                           current_predictions: Union[pd.Series, np.ndarray, List[Any]],
                                           prediction_type: Literal["numerical_score", "probability_distribution", "categorical_label"] = "numerical_score",
                                           alpha: float = 0.05,
                                           num_bins_for_psi: int = 10
                                           ) -> Dict[str, Any]:
        """
        Detects drift in the distribution of model predictions.
        Uses KS test for numerical scores/probabilities, Chi-Squared or PSI for categorical labels.
        For probability distributions (multiclass), could apply tests per class probability or use divergence measures.

        Args:
            reference_predictions: Predictions from a reference period.
            current_predictions: Predictions from the current period.
            prediction_type: Type of predictions being analyzed.
            alpha: Significance level for statistical tests.
            num_bins_for_psi: Number of bins if PSI is used for scores/probabilities.

        Returns:
            Dict with drift detection results.
        """
        ref_preds = self._get_data_series(reference_predictions)
        curr_preds = self._get_data_series(current_predictions)

        logger.info(f"Detecting prediction drift (Type: {prediction_type})...")

        if prediction_type == "numerical_score": # e.g., regression output, probability score for binary classification
            return self.detect_univariate_numerical_drift_ks(
                ref_preds, curr_preds, feature_name="PredictionScore", alpha=alpha
            )
        elif prediction_type == "categorical_label": # e.g., class labels
            return self.detect_univariate_categorical_drift_chisquare(
                ref_preds, curr_preds, feature_name="PredictionLabel", alpha=alpha
            )
        elif prediction_type == "probability_distribution": # More complex, could use PSI on probabilities
             # This example uses PSI for a single probability score (e.g. positive class prob)
             # For full distributions, one might use Jensen-Shannon divergence or PSI per class.
            logger.info("Using PSI for probability distribution drift (conceptual for single probability score).")
            return self.calculate_population_stability_index(
                ref_preds, curr_preds, feature_name="PredictionProbability", num_bins=num_bins_for_psi
            )
        else:
            logger.error(f"Unsupported prediction_type for drift detection: {prediction_type}")
            return {"error": f"Unsupported prediction_type: {prediction_type}"}


# Example Usage
if __name__ == "__main__":
    print("=========================================================")
    print("=== Drift Detection Prototype (MLOps Model Monitoring) ===")
    print("=========================================================")

    # --- Sample Data Generation ---
    np.random.seed(42)
    # Reference Data (e.g., Training Data)
    ref_size = 1000
    reference_data = pd.DataFrame({
        'numerical_feature_A': np.random.normal(loc=10, scale=2, size=ref_size),
        'numerical_feature_B': np.random.gamma(shape=2, scale=2, size=ref_size),
        'categorical_feature_X': np.random.choice(['Cat1', 'Cat2', 'Cat3', 'Cat4'], size=ref_size, p=[0.4, 0.3, 0.2, 0.1]),
        'target_labels': np.random.randint(0, 2, size=ref_size) # For performance monitoring
    })
    # Simulate reference predictions (e.g., model output scores on a validation set)
    reference_predictions_scores = np.random.beta(a=2, b=5, size=ref_size) # Skewed probabilities
    reference_predicted_labels = (reference_predictions_scores > 0.3).astype(int) # Thresholding for labels

    # Current Data (e.g., Production Data - with potential drift)
    curr_size = 500
    current_data_drifted = pd.DataFrame({
        'numerical_feature_A': np.random.normal(loc=12, scale=2.5, size=curr_size), # Drift: mean and std changed
        'numerical_feature_B': np.random.gamma(shape=3, scale=1.5, size=curr_size), # Drift: shape and scale changed
        'categorical_feature_X': np.random.choice(['Cat1', 'Cat2', 'Cat3', 'Cat4', 'Cat5'], size=curr_size, p=[0.2, 0.2, 0.3, 0.2, 0.1]), # Drift: proportions and new category
        'target_labels': np.random.randint(0, 2, size=curr_size) # New true labels
    })
    # Simulate current predictions (e.g., from the same model on new data)
    current_predictions_scores_drifted = np.random.beta(a=2.5, b=4, size=curr_size) # Slightly different distribution
    current_predicted_labels_drifted = (current_predictions_scores_drifted > 0.35).astype(int) # Potentially different threshold or model degradation


    # --- Initialize Detector ---
    # detector = DriftDetector(reference_dataframe=reference_data) # Can pass reference_df here
    detector = DriftDetector()


    # --- 1. Univariate Numerical Feature Drift (KS Test) ---
    print("\n--- 1. Numerical Feature Drift (Kolmogorov-Smirnov Test) ---")
    ks_result_A = detector.detect_univariate_numerical_drift_ks(
        reference_data['numerical_feature_A'],
        current_data_drifted['numerical_feature_A'],
        feature_name='numerical_feature_A'
    )
    print(f"  Drift Result for numerical_feature_A: {ks_result_A}")

    # Example with no drift (comparing reference to itself)
    ks_result_A_no_drift = detector.detect_univariate_numerical_drift_ks(
        reference_data['numerical_feature_A'],
        reference_data['numerical_feature_A'].sample(curr_size, random_state=1), # Sample from reference
        feature_name='numerical_feature_A (No Drift Check)'
    )
    print(f"  Drift Result for numerical_feature_A (No Drift Check): {ks_result_A_no_drift}")


    # --- 2. Univariate Categorical Feature Drift (Chi-Squared Test) ---
    print("\n--- 2. Categorical Feature Drift (Chi-Squared Test) ---")
    chi2_result_X = detector.detect_univariate_categorical_drift_chisquare(
        reference_data['categorical_feature_X'],
        current_data_drifted['categorical_feature_X'],
        feature_name='categorical_feature_X'
    )
    print(f"  Drift Result for categorical_feature_X: {chi2_result_X}")

    # Example with no drift
    chi2_result_X_no_drift = detector.detect_univariate_categorical_drift_chisquare(
         reference_data['categorical_feature_X'],
         reference_data['categorical_feature_X'].sample(curr_size, random_state=1),
         feature_name='categorical_feature_X (No Drift Check)'
    )
    print(f"  Drift Result for categorical_feature_X (No Drift Check): {chi2_result_X_no_drift}")


    # --- 3. Population Stability Index (PSI) ---
    print("\n--- 3. Population Stability Index (PSI) ---")
    psi_result_B_numerical = detector.calculate_population_stability_index(
        reference_data['numerical_feature_B'],
        current_data_drifted['numerical_feature_B'],
        feature_name='numerical_feature_B',
        is_categorical=False,
        num_bins=10
    )
    print(f"  PSI Result for numerical_feature_B: {psi_result_B_numerical['psi_value']:.4f} ({psi_result_B_numerical['drift_magnitude']})")

    psi_result_X_categorical = detector.calculate_population_stability_index(
        reference_data['categorical_feature_X'],
        current_data_drifted['categorical_feature_X'],
        feature_name='categorical_feature_X',
        is_categorical=True
    )
    print(f"  PSI Result for categorical_feature_X: {psi_result_X_categorical['psi_value']:.4f} ({psi_result_X_categorical['drift_magnitude']})")


    # --- 4. Prediction Drift ---
    print("\n--- 4. Prediction Drift ---")
    # For numerical prediction scores (e.g., probabilities)
    pred_drift_scores = detector.detect_prediction_drift_univariate(
        reference_predictions_scores,
        current_predictions_scores_drifted,
        prediction_type="numerical_score"
    )
    print(f"  Prediction Score Drift Result: {pred_drift_scores}")

    # For categorical prediction labels
    pred_drift_labels = detector.detect_prediction_drift_univariate(
        reference_predicted_labels,
        current_predicted_labels_drifted,
        prediction_type="categorical_label"
    )
    print(f"  Prediction Label Drift Result: {pred_drift_labels}")


    # --- 5. Model Performance Degradation (Concept Drift Indicator) ---
    print("\n--- 5. Model Performance Degradation (Concept Drift) ---")
    baseline_model_metrics = {
        "accuracy": accuracy_score(reference_data['target_labels'], reference_predicted_labels), # Calculated on ref/validation
        "f1": f1_score(reference_data['target_labels'], reference_predicted_labels, average='binary' if len(np.unique(reference_data['target_labels'])) == 2 else 'weighted'),
    }
    print(f"  Baseline Metrics: {baseline_model_metrics}")

    performance_drift_results = detector.monitor_performance_degradation(
        y_true_current=current_data_drifted['target_labels'],
        y_pred_current=current_predicted_labels_drifted, # These are current predictions on new data
        baseline_metrics=baseline_model_metrics,
        metric_tolerances_relative={"accuracy": 0.05, "f1": 0.1} # Allow 5% drop in acc, 10% in F1
    )
    print(f"  Performance Degradation Results:")
    for metric, details in performance_drift_results.get("metrics", {}).items():
        print(f"    {metric}: Current={details['current_value']:.4f}, Baseline={details['baseline_value']:.4f}, Drift Detected={details['drift_detected']}")
    print(f"  Overall Performance Drift Detected: {performance_drift_results['overall_drift_detected']}")


    print("\n=========================================================")
    print("=== Drift Detection Prototype Complete ===")
    print("=========================================================")
