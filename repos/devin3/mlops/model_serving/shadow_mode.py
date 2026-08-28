# Devin/mlops/model_serving/shadow_mode.py
# Purpose: Conceptual framework for Shadow Mode model deployments.
#          Allows testing a new model with live traffic without impacting users.
# Safe Rollouts 🛡️➡️🚀

import logging
import uuid
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error

# Configure basic logging
logger = logging.getLogger("ShadowDeployment")
if not logger.handlers: # Prevent duplicate handlers
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class ShadowDeploymentManager:
    """
    Manages a conceptual shadow mode deployment for comparing a shadow model
    against a champion model using live traffic.
    """

    def __init__(self,
                 champion_model_id: str,
                 shadow_model_id: str,
                 champion_predict_func: Callable[[Any], Any], # Function that takes input_data, returns prediction
                 shadow_predict_func: Callable[[Any], Any],   # Function that takes input_data, returns prediction
                 log_input_data: bool = True):
        """
        Initializes the ShadowDeploymentManager.

        Args:
            champion_model_id (str): Identifier for the champion (live) model.
            shadow_model_id (str): Identifier for the shadow (challenger) model.
            champion_predict_func (Callable): A function that simulates or calls the champion model's prediction.
                                             It should accept input_data and return a prediction.
            shadow_predict_func (Callable): A function that simulates or calls the shadow model's prediction.
                                            It should accept input_data and return a prediction.
            log_input_data (bool): Whether to store the input data in the log (can be large).
        """
        self.champion_model_id = champion_model_id
        self.shadow_model_id = shadow_model_id
        self.champion_predict = champion_predict_func
        self.shadow_predict = shadow_predict_func
        self.log_input_data_flag = log_input_data

        self.observations_log: List[Dict[str, Any]] = []
        # Each entry: {"request_id", "timestamp", "input_data_ref" (or data),
        #              "champion_prediction", "shadow_prediction", "ground_truth",
        #              "champion_latency_ms", "shadow_latency_ms"}

        logger.info(f"ShadowDeploymentManager initialized for Champion '{champion_model_id}' and Shadow '{shadow_model_id}'.")

    def process_request(self, input_data: Any, request_id: Optional[str] = None) -> Any:
        """
        Processes an incoming request using both champion and shadow models.
        Only the champion's prediction is returned (as it would be in a real scenario).
        Shadow model's prediction is logged for later analysis.

        Args:
            input_data (Any): The input data for the models.
            request_id (Optional[str]): A unique identifier for the request. If None, generated.

        Returns:
            Any: The prediction from the champion model.
        """
        if request_id is None:
            request_id = f"req_{uuid.uuid4().hex[:8]}"
        
        timestamp = datetime.utcnow()
        log_entry: Dict[str, Any] = {
            "request_id": request_id,
            "timestamp": timestamp,
            "ground_truth": None # To be filled later if available
        }

        if self.log_input_data_flag:
            log_entry["input_data"] = input_data # Store actual data or a reference/hash

        # Get champion prediction (this is what's served to the user)
        start_time_champion = datetime.utcnow()
        try:
            champion_prediction = self.champion_predict(input_data)
            log_entry["champion_prediction"] = champion_prediction
        except Exception as e:
            logger.error(f"Error getting prediction from champion model '{self.champion_model_id}' for request '{request_id}': {e}")
            log_entry["champion_prediction"] = None # Or some error indicator
            log_entry["champion_error"] = str(e)
            champion_prediction = None # Or fallback
        log_entry["champion_latency_ms"] = (datetime.utcnow() - start_time_champion).total_seconds() * 1000
        
        # Get shadow prediction (for logging and analysis only)
        start_time_shadow = datetime.utcnow()
        try:
            shadow_prediction = self.shadow_predict(input_data)
            log_entry["shadow_prediction"] = shadow_prediction
        except Exception as e:
            logger.error(f"Error getting prediction from shadow model '{self.shadow_model_id}' for request '{request_id}': {e}")
            log_entry["shadow_prediction"] = None # Or some error indicator
            log_entry["shadow_error"] = str(e)
        log_entry["shadow_latency_ms"] = (datetime.utcnow() - start_time_shadow).total_seconds() * 1000

        self.observations_log.append(log_entry)
        # logger.debug(f"Processed request '{request_id}': Champion={log_entry['champion_prediction']}, Shadow={log_entry['shadow_prediction']}")
        
        return champion_prediction # Only champion's prediction is "live"

    def add_ground_truth(self, request_id: str, ground_truth_value: Any) -> bool:
        """
        Adds the ground truth (actual outcome) for a previously processed request.

        Args:
            request_id (str): The ID of the request to update.
            ground_truth_value (Any): The actual outcome.

        Returns:
            bool: True if the request was found and updated, False otherwise.
        """
        for obs in self.observations_log:
            if obs["request_id"] == request_id:
                obs["ground_truth"] = ground_truth_value
                # logger.debug(f"Added ground truth for request_id '{request_id}'.")
                return True
        logger.warning(f"Request ID '{request_id}' not found in log for adding ground truth.")
        return False

    def analyze_shadow_run(self,
                           model_task_type: Literal["classification", "regression"] = "classification"
                           ) -> Dict[str, Any]:
        """
        Analyzes the logged observations from the shadow run.
        Compares champion vs. shadow predictions and their performance against ground truth if available.

        Args:
            model_task_type (str): Type of ML task ("classification" or "regression")
                                   to determine appropriate metrics.

        Returns:
            Dict[str, Any]: A dictionary containing analysis results.
        """
        if not self.observations_log:
            logger.warning("No observations logged. Cannot perform analysis.")
            return {"message": "No observations to analyze."}

        df = pd.DataFrame(self.observations_log)
        logger.info(f"Analyzing {len(df)} observations from shadow run...")

        results: Dict[str, Any] = {
            "total_requests": len(df),
            "champion_model_id": self.champion_model_id,
            "shadow_model_id": self.shadow_model_id,
        }

        # 1. Prediction Agreement
        # Ensure predictions are comparable (handle None types from errors)
        df_valid_preds = df.dropna(subset=['champion_prediction', 'shadow_prediction'])
        if not df_valid_preds.empty:
            agreement = (np.array(df_valid_preds['champion_prediction'].tolist()) == np.array(df_valid_preds['shadow_prediction'].tolist()))
            results["prediction_agreement_rate"] = np.mean(agreement) if len(agreement) > 0 else 0.0
            results["prediction_disagreement_count"] = len(agreement) - np.sum(agreement)
        else:
            results["prediction_agreement_rate"] = np.nan
            results["prediction_disagreement_count"] = np.nan
        
        logger.info(f"  Prediction Agreement Rate: {results['prediction_agreement_rate']:.4f}")

        # 2. Performance against Ground Truth (if available)
        df_with_truth = df.dropna(subset=['ground_truth', 'champion_prediction', 'shadow_prediction'])
        results["requests_with_ground_truth"] = len(df_with_truth)
        
        if not df_with_truth.empty:
            y_true = np.array(df_with_truth['ground_truth'].tolist())
            champion_preds_for_eval = np.array(df_with_truth['champion_prediction'].tolist())
            shadow_preds_for_eval = np.array(df_with_truth['shadow_prediction'].tolist())

            if model_task_type == "classification":
                results["champion_performance"] = {
                    "accuracy": accuracy_score(y_true, champion_preds_for_eval),
                    "precision_macro": precision_score(y_true, champion_preds_for_eval, average='macro', zero_division=0),
                    "recall_macro": recall_score(y_true, champion_preds_for_eval, average='macro', zero_division=0),
                    "f1_macro": f1_score(y_true, champion_preds_for_eval, average='macro', zero_division=0),
                }
                results["shadow_performance"] = {
                    "accuracy": accuracy_score(y_true, shadow_preds_for_eval),
                    "precision_macro": precision_score(y_true, shadow_preds_for_eval, average='macro', zero_division=0),
                    "recall_macro": recall_score(y_true, shadow_preds_for_eval, average='macro', zero_division=0),
                    "f1_macro": f1_score(y_true, shadow_preds_for_eval, average='macro', zero_division=0),
                }
            elif model_task_type == "regression":
                results["champion_performance"] = {
                    "mse": mean_squared_error(y_true, champion_preds_for_eval),
                    "rmse": np.sqrt(mean_squared_error(y_true, champion_preds_for_eval)),
                }
                results["shadow_performance"] = {
                    "mse": mean_squared_error(y_true, shadow_preds_for_eval),
                    "rmse": np.sqrt(mean_squared_error(y_true, shadow_preds_for_eval)),
                }
            logger.info(f"  Champion Performance (on {len(df_with_truth)} samples): {results.get('champion_performance')}")
            logger.info(f"  Shadow Performance (on {len(df_with_truth)} samples): {results.get('shadow_performance')}")
        else:
            logger.info("  No ground truth available for performance metric calculation against actuals.")
            results["champion_performance"] = "N/A (No ground truth)"
            results["shadow_performance"] = "N/A (No ground truth)"

        # 3. Latency Comparison
        results["avg_champion_latency_ms"] = df['champion_latency_ms'].mean()
        results["avg_shadow_latency_ms"] = df['shadow_latency_ms'].mean()
        logger.info(f"  Avg Champion Latency: {results['avg_champion_latency_ms']:.2f} ms")
        logger.info(f"  Avg Shadow Latency: {results['avg_shadow_latency_ms']:.2f} ms")

        # 4. Error Rate Comparison
        results["champion_error_count"] = df['champion_error'].notna().sum()
        results["shadow_error_count"] = df['shadow_error'].notna().sum()
        logger.info(f"  Champion Prediction Error Count: {results['champion_error_count']}")
        logger.info(f"  Shadow Prediction Error Count: {results['shadow_error_count']}")

        # Optional: Prediction distribution comparison (using concepts from drift_detection.py)
        # from ..data_validation.drift_detection import DriftDetector # Relative import if in same package
        # drift_detector = DriftDetector()
        # if not df_valid_preds.empty:
        #     pred_drift = drift_detector.detect_prediction_drift_univariate(...) # Champion vs Shadow preds
        #     results["prediction_output_drift"] = pred_drift
        #     logger.info(f"  Conceptual Prediction Output Drift (Champion vs Shadow): {pred_drift}")

        return results

# --- Example Usage ---

# Conceptual model prediction functions
def champion_model_predict(data: Dict[str, float]) -> int:
    # Simple rule-based champion
    if data.get("feature1", 0) > 50 and data.get("feature2", 0) < 20:
        return 1 # Positive prediction
    return 0 # Negative prediction

def shadow_model_predict_v1(data: Dict[str, float]) -> int:
    # Shadow model - slightly different logic, maybe an ML model
    # For simplicity, let's make it more lenient or stricter
    # This one might be more prone to false positives
    if data.get("feature1", 0) > 45: # Lower threshold for feature1
        return 1
    return 0
    
def shadow_model_predict_v2(data: Dict[str, float]) -> int:
    # Another shadow model - perhaps one that errors more often
    if random.random() < 0.05: # 5% chance of erroring
        raise ValueError("Simulated shadow model internal error")
    if data.get("feature1", 0) > 50 and data.get("feature2", 0) < 22: # Slightly different boundary
        return 1
    return 0


if __name__ == "__main__":
    print("=========================================================")
    print("=== Shadow Mode Deployment Prototype 🛡️➡️🚀 ===")
    print("=========================================================")

    # Initialize Shadow Deployment Manager
    shadow_manager = ShadowDeploymentManager(
        champion_model_id="ChampionV1.0",
        shadow_model_id="ChallengerV1.1_beta",
        champion_predict_func=champion_model_predict,
        shadow_predict_func=shadow_model_predict_v1 # Test this shadow first
    )
    print(f"\nRunning shadow test for {shadow_manager.shadow_model_id}...")

    # Simulate processing some live requests
    num_requests = 1000
    request_ids_processed = []
    true_outcomes = [] # Store true outcomes for later evaluation

    print(f"\nSimulating {num_requests} requests...")
    for i in range(num_requests):
        req_id = f"req_{i:04d}"
        request_ids_processed.append(req_id)
        # Simulate input data
        input_features = {
            "feature1": random.uniform(0, 100),
            "feature2": random.uniform(0, 50)
        }
        
        # User only sees champion's prediction
        _ = shadow_manager.process_request(input_data=input_features, request_id=req_id)

        # Simulate ground truth (e.g., becomes known later)
        # For this demo, let's say ground truth is closer to champion's logic but not identical
        if input_features["feature1"] > 55 and input_features["feature2"] < 18:
            true_outcomes.append({"request_id": req_id, "outcome": 1})
        elif random.random() < 0.1: # some random positives
             true_outcomes.append({"request_id": req_id, "outcome": 1})
        else:
            true_outcomes.append({"request_id": req_id, "outcome": 0})

    # Simulate adding ground truth after some time
    print("\nSimulating ground truth becoming available...")
    for item in true_outcomes:
        shadow_manager.add_ground_truth(item["request_id"], item["outcome"])

    # Analyze the shadow run
    print("\n--- Analyzing Shadow Run Results ---")
    analysis_results_v1 = shadow_manager.analyze_shadow_run(model_task_type="classification")

    print("\n**Analysis Summary:**")
    print(f"  Total Requests Logged: {analysis_results_v1.get('total_requests')}")
    print(f"  Requests with Ground Truth: {analysis_results_v1.get('requests_with_ground_truth')}")
    print(f"  Prediction Agreement Rate (Champion vs Shadow): {analysis_results_v1.get('prediction_agreement_rate', np.nan):.4f}")
    print(f"  Prediction Disagreement Count: {analysis_results_v1.get('prediction_disagreement_count', np.nan)}")
    
    print("\n  Champion Performance:")
    if isinstance(analysis_results_v1.get('champion_performance'), dict):
        for metric, value in analysis_results_v1['champion_performance'].items():
            print(f"    {metric}: {value:.4f}")
    else:
        print(f"    {analysis_results_v1.get('champion_performance')}")

    print("\n  Shadow Performance ({shadow_manager.shadow_model_id}):")
    if isinstance(analysis_results_v1.get('shadow_performance'), dict):
        for metric, value in analysis_results_v1['shadow_performance'].items():
            print(f"    {metric}: {value:.4f}")
    else:
        print(f"    {analysis_results_v1.get('shadow_performance')}")

    print(f"\n  Avg Champion Latency: {analysis_results_v1.get('avg_champion_latency_ms', np.nan):.2f} ms")
    print(f"  Avg Shadow Latency: {analysis_results_v1.get('avg_shadow_latency_ms', np.nan):.2f} ms")
    print(f"  Champion Error Count: {analysis_results_v1.get('champion_error_count', np.nan)}")
    print(f"  Shadow Error Count: {analysis_results_v1.get('shadow_error_count', np.nan)}")


    # --- Example with a different shadow model (e.g., one that errors more) ---
    print("\n\n--- Testing a different shadow model (ShadowV2 - potentially error-prone) ---")
    shadow_manager_v2 = ShadowDeploymentManager(
        champion_model_id="ChampionV1.0",
        shadow_model_id="ChallengerV2.0_error_test",
        champion_predict_func=champion_model_predict,
        shadow_predict_func=shadow_model_predict_v2 # Model that might error
    )
    request_ids_v2 = []
    true_outcomes_v2 = []
    for i in range(200): # Smaller run
        req_id = f"req_v2_{i:04d}"
        request_ids_v2.append(req_id)
        input_features = {"feature1": random.uniform(0, 100), "feature2": random.uniform(0, 50)}
        _ = shadow_manager_v2.process_request(input_data=input_features, request_id=req_id)
        if input_features["feature1"] > 55 and input_features["feature2"] < 18: true_outcomes_v2.append({"request_id": req_id, "outcome": 1})
        else: true_outcomes_v2.append({"request_id": req_id, "outcome": 0})
    for item in true_outcomes_v2: shadow_manager_v2.add_ground_truth(item["request_id"], item["outcome"])
    
    analysis_results_v2 = shadow_manager_v2.analyze_shadow_run(model_task_type="classification")
    print("\n**Analysis Summary for ShadowV2:**")
    print(f"  Total Requests Logged: {analysis_results_v2.get('total_requests')}")
    print(f"  Prediction Agreement Rate: {analysis_results_v2.get('prediction_agreement_rate', np.nan):.4f}")
    print(f"  Shadow Error Count: {analysis_results_v2.get('shadow_error_count', np.nan)}")
    print(f"  Shadow Accuracy: {analysis_results_v2.get('shadow_performance', {}).get('accuracy', np.nan):.4f}")


    print("\n=========================================================")
    print("=== Shadow Mode Deployment Prototype Complete ===")
    print("=========================================================")
