# Devin/mlops/model_serving/canary_releases.py
# Purpose: Conceptual framework for Canary Releases of ML models.
#          Facilitates gradual rollouts to a subset of users/traffic.
# Gradual Rollouts 🐦📡 (Distinct from Shadow Mode)

import logging
import uuid
import random
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Literal, Tuple
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error

# Configure basic logging
logger = logging.getLogger("CanaryReleaseManager")
if not logger.handlers: # Prevent duplicate handlers
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class CanaryReleaseManager:
    """
    Manages a conceptual canary release process for ML models.
    """

    def __init__(self,
                 champion_model_id: str,
                 canary_model_id: str,
                 champion_predict_func: Callable[[Any], Any],
                 canary_predict_func: Callable[[Any], Any],
                 initial_canary_traffic_percentage: float = 5.0, # Percentage (0-100)
                 kpis_to_monitor: Optional[List[str]] = None,
                 min_observations_for_analysis: int = 100):
        """
        Initializes the CanaryReleaseManager.

        Args:
            champion_model_id (str): Identifier for the current production (champion) model.
            canary_model_id (str): Identifier for the new (canary) model.
            champion_predict_func (Callable): Function for champion model predictions.
            canary_predict_func (Callable): Function for canary model predictions.
            initial_canary_traffic_percentage (float): Initial % of traffic routed to canary (0-100).
            kpis_to_monitor (List[str]): List of KPI names to track (e.g., "conversion_rate", "error_rate", "latency").
            min_observations_for_analysis (int): Minimum observations per variant for meaningful analysis.
        """
        if not (0 <= initial_canary_traffic_percentage <= 100):
            raise ValueError("Initial canary traffic percentage must be between 0 and 100.")

        self.champion_model_id = champion_model_id
        self.canary_model_id = canary_model_id
        self.champion_predict = champion_predict_func
        self.canary_predict = canary_predict_func
        self.canary_traffic_percentage = initial_canary_traffic_percentage / 100.0 # Store as fraction
        self.kpis_to_monitor = kpis_to_monitor if kpis_to_monitor else ["conversion_rate", "error_count", "avg_latency_ms"]
        self.min_observations = min_observations_for_analysis

        self.observations_log: List[Dict[str, Any]] = []
        # Log entry: {"request_id", "timestamp", "user_id", "served_by_model_id",
        #             "input_data_ref", "prediction", "ground_truth", "latency_ms", "custom_metrics"}
        
        self.release_start_time = datetime.utcnow()
        logger.info(
            f"CanaryReleaseManager initialized for Champion '{champion_model_id}' and Canary '{canary_model_id}'. "
            f"Initial canary traffic: {self.canary_traffic_percentage*100:.1f}%"
        )

    def _route_traffic_conceptual(self, user_id: str) -> str:
        """
        Conceptually routes traffic to either champion or canary based on percentage.
        A real system would use a more robust routing/bucketing mechanism.
        """
        # For consistent assignment, hash user_id or request_id
        # For this simulation, simple random weighted choice:
        if random.random() < self.canary_traffic_percentage:
            return self.canary_model_id
        return self.champion_model_id

    def serve_request(self,
                      input_data: Any,
                      user_id: str, # Important for consistent routing in real systems
                      request_id: Optional[str] = None
                      ) -> Tuple[Any, str]: # Returns (prediction, model_id_served)
        """
        Processes an incoming request, routing it to champion or canary.
        The prediction from the chosen model IS served to the user.
        """
        if request_id is None:
            request_id = f"creq_{uuid.uuid4().hex[:8]}"
        
        timestamp = datetime.utcnow()
        model_to_serve = self._route_traffic_conceptual(user_id)
        
        prediction = None
        latency_ms = None
        error_info = None
        
        start_time = datetime.utcnow()
        try:
            if model_to_serve == self.canary_model_id:
                prediction = self.canary_predict(input_data)
            else: # Champion
                prediction = self.champion_predict(input_data)
        except Exception as e:
            logger.error(f"Error during prediction for request '{request_id}' by model '{model_to_serve}': {e}")
            error_info = str(e)
            # Fallback strategy could be implemented here (e.g., serve champion if canary fails)
            # For simplicity, we just log the error and prediction might be None.
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        log_entry = {
            "request_id": request_id,
            "timestamp": timestamp,
            "user_id": user_id,
            "served_by_model_id": model_to_serve,
            # "input_data": input_data, # Optionally log input, can be large
            "prediction": prediction,
            "ground_truth": None,
            "latency_ms": latency_ms,
            "error": error_info,
            "custom_metrics": {}
        }
        self.observations_log.append(log_entry)
        
        return prediction, model_to_serve

    def record_outcome(self,
                       request_id: str,
                       ground_truth_value: Optional[Any] = None,
                       business_kpis: Optional[Dict[str, Any]] = None) -> bool:
        """
        Records the outcome (ground truth, business KPIs like conversion) for a request.
        """
        for obs in self.observations_log:
            if obs["request_id"] == request_id:
                if ground_truth_value is not None:
                    obs["ground_truth"] = ground_truth_value
                if business_kpis:
                    obs["custom_metrics"].update(business_kpis)
                # logger.debug(f"Outcome recorded for request '{request_id}'.")
                return True
        logger.warning(f"Request ID '{request_id}' not found in log for recording outcome.")
        return False

    def adjust_canary_traffic(self, new_percentage: float):
        """Adjusts the percentage of traffic going to the canary model."""
        if not (0 <= new_percentage <= 100):
            raise ValueError("New canary traffic percentage must be between 0 and 100.")
        self.canary_traffic_percentage = new_percentage / 100.0
        logger.info(f"Canary traffic for '{self.canary_model_id}' adjusted to {new_percentage:.1f}%.")

    def get_performance_summary(self, model_task_type: Literal["classification", "regression"] = "classification") -> Dict[str, Any]:
        """
        Analyzes logged data and provides performance summary for champion and canary.
        """
        if not self.observations_log:
            return {"message": "No observations logged yet."}

        df = pd.DataFrame(self.observations_log)
        summary = {"analysis_timestamp": datetime.utcnow().isoformat(), "variants": {}}
        
        for model_id in [self.champion_model_id, self.canary_model_id]:
            variant_df = df[df["served_by_model_id"] == model_id]
            if variant_df.empty:
                summary["variants"][model_id] = {"observation_count": 0, "message": "No traffic received."}
                continue

            kpi_values: Dict[str, Any] = {"observation_count": len(variant_df)}
            kpi_values["error_count"] = variant_df["error"].notna().sum()
            kpi_values["avg_latency_ms"] = variant_df["latency_ms"].mean()

            # Calculate ground truth based metrics if available
            variant_df_with_truth = variant_df.dropna(subset=['ground_truth', 'prediction'])
            if not variant_df_with_truth.empty:
                y_true = np.array(variant_df_with_truth['ground_truth'].tolist())
                y_pred = np.array(variant_df_with_truth['prediction'].tolist())
                
                if model_task_type == "classification":
                    kpi_values["accuracy"] = accuracy_score(y_true, y_pred)
                    kpi_values["f1_macro"] = f1_score(y_true, y_pred, average='macro', zero_division=0)
                elif model_task_type == "regression":
                    kpi_values["mse"] = mean_squared_error(y_true, y_pred)
            
            # Calculate custom/business KPIs (example: conversion_rate)
            if "conversion_rate" in self.kpis_to_monitor and not variant_df.empty:
                # Assume 'did_convert' is logged in custom_metrics via record_outcome
                conversions = sum(obs["custom_metrics"].get("did_convert", 0) for obs in variant_df.to_dict('records') if isinstance(obs.get("custom_metrics"), dict))
                kpi_values["conversion_rate"] = conversions / len(variant_df) if len(variant_df) > 0 else 0.0

            summary["variants"][model_id] = kpi_values
        
        logger.info("Performance summary generated.")
        return summary

    def decide_next_step_conceptual(self, performance_summary: Dict[str, Any]) -> Literal["PROMOTE_CANARY", "ROLLBACK_CANARY", "INCREASE_TRAFFIC", "CONTINUE_MONITORING"]:
        """
        Conceptual: Makes a decision based on canary performance.
        This logic would be highly business-specific.
        """
        canary_id = self.canary_model_id
        champion_id = self.champion_model_id
        
        canary_stats = performance_summary.get("variants", {}).get(canary_id)
        champion_stats = performance_summary.get("variants", {}).get(champion_id)

        if not canary_stats or canary_stats.get("observation_count", 0) < self.min_observations:
            logger.info("Decision: Insufficient data for canary. CONTINUE_MONITORING.")
            return "CONTINUE_MONITORING"
        if not champion_stats: # Should not happen if some traffic always goes to champion
             logger.warning("Decision: Champion stats missing. Cannot make informed decision. CONTINUE_MONITORING")
             return "CONTINUE_MONITORING"


        # Simple example: Check error rates and a key performance metric (e.g., conversion_rate)
        canary_error_rate = canary_stats.get("error_count", 0) / canary_stats.get("observation_count", 1)
        champion_error_rate = champion_stats.get("error_count", 0) / champion_stats.get("observation_count", 1)
        
        # Higher is better for conversion_rate, lower is better for error_rate
        canary_conversion = canary_stats.get("conversion_rate", 0.0)
        champion_conversion = champion_stats.get("conversion_rate", 0.0)
        
        logger.info(f"Canary ({canary_id}): Errors={canary_error_rate:.3f}, Conversion={canary_conversion:.3f}")
        logger.info(f"Champion ({champion_id}): Errors={champion_error_rate:.3f}, Conversion={champion_conversion:.3f}")

        # CRITICAL FAILURE: Rollback if canary is significantly worse in errors
        if canary_error_rate > champion_error_rate * 1.5 and canary_error_rate > 0.05: # e.g. 50% more errors and >5% actual
            logger.warning("Decision: Canary error rate significantly higher. ROLLBACK_CANARY.")
            return "ROLLBACK_CANARY"

        # Performance check
        if canary_conversion >= champion_conversion * 0.98: # Canary is at least 98% as good as champion
            current_traffic_pct = self.canary_traffic_percentage * 100
            if np.isclose(current_traffic_pct, 100.0):
                logger.info("Decision: Canary at 100% traffic and performing well. PROMOTE_CANARY.")
                return "PROMOTE_CANARY"
            elif current_traffic_pct < 50.0: # Example: if less than 50%, increase
                logger.info("Decision: Canary performing well at current level. INCREASE_TRAFFIC.")
                return "INCREASE_TRAFFIC"
            else: # Between 50 and <100, continue monitoring or prepare for promotion
                 logger.info("Decision: Canary performing well at >50% traffic. CONTINUE_MONITORING (or prepare for promotion).")
                 return "CONTINUE_MONITORING" # Or PROMOTE_CANARY if a final check passes
        else: # Canary performance is worse than 98% of champion on key KPI
            logger.warning("Decision: Canary conversion rate significantly lower. ROLLBACK_CANARY.")
            return "ROLLBACK_CANARY"


# Example Usage
def dummy_predict_v1(data: Any) -> int: # Champion
    # Simulate some processing
    if isinstance(data, dict) and data.get("featureX", 0) > 0.5:
        return 1
    return 0

def dummy_predict_v2_canary(data: Any) -> int: # Canary
    # Simulate slightly better or different behavior
    if isinstance(data, dict) and data.get("featureX", 0) > 0.45: # More sensitive
        if random.random() < 0.02: # Small chance of error
            raise Exception("Simulated canary internal error")
        return 1
    return 0

if __name__ == "__main__":
    print("=========================================================")
    print("=== Canary Release Manager Prototype 🐦📡 ===")
    print("=========================================================")

    canary_manager = CanaryReleaseManager(
        champion_model_id="StableDiffusion_v1.5",
        canary_model_id="StableDiffusion_v2.1_Canary",
        champion_predict_func=dummy_predict_v1,
        canary_predict_func=dummy_predict_v2_canary,
        initial_canary_traffic_percentage=10.0, # Start with 10% traffic to canary
        kpis_to_monitor=["conversion_rate", "error_count", "avg_latency_ms", "accuracy"],
        min_observations_for_analysis=50 # For demo purposes
    )

    # --- Phase 1: Initial Canary Rollout (10% traffic) ---
    print(f"\n--- Phase 1: Canary at {canary_manager.canary_traffic_percentage*100:.0f}% traffic ---")
    num_requests_phase1 = 200
    for i in range(num_requests_phase1):
        user_id = f"user_{uuid.uuid4().hex[:6]}"
        # Simulate input data (could be more complex)
        input_d = {"featureX": random.random(), "user_segment": random.choice(["A", "B"])}
        
        prediction, model_served = canary_manager.serve_request(input_data=input_d, user_id=user_id)
        
        # Simulate outcome recording (e.g., user converted or not)
        # Let's say canary has a slightly better true conversion rate
        did_convert = False
        if model_served == canary_manager.canary_model_id:
            if random.random() < 0.15: # 15% true conversion for canary
                did_convert = True
        else: # Champion
            if random.random() < 0.12: # 12% true conversion for champion
                did_convert = True
        
        canary_manager.record_outcome(
            request_id=canary_manager.observations_log[-1]["request_id"], # Get last request_id
            ground_truth_value=1 if did_convert else 0, # Assuming target for accuracy is conversion
            business_kpis={"did_convert": did_convert}
        )

    phase1_summary = canary_manager.get_performance_summary(model_task_type="classification")
    print("\n**Phase 1 Performance Summary:**")
    for model_id, stats in phase1_summary.get("variants", {}).items():
        print(f"  Model: {model_id}, Obs: {stats.get('observation_count')}, "
              f"Conversion: {stats.get('conversion_rate', np.nan):.3f}, "
              f"Errors: {stats.get('error_count', np.nan)}, "
              f"Accuracy: {stats.get('accuracy', np.nan):.3f}")

    decision_phase1 = canary_manager.decide_next_step_conceptual(phase1_summary)
    print(f"Conceptual Decision after Phase 1: {decision_phase1}")

    # --- Phase 2: Increase Traffic if Phase 1 was good ---
    if decision_phase1 == "INCREASE_TRAFFIC" or decision_phase1 == "CONTINUE_MONITORING":
        canary_manager.adjust_canary_traffic(50.0) # Increase to 50%
        print(f"\n--- Phase 2: Canary at {canary_manager.canary_traffic_percentage*100:.0f}% traffic ---")
        num_requests_phase2 = 300 # More requests
        for i in range(num_requests_phase2):
            user_id = f"user_{uuid.uuid4().hex[:6]}"
            input_d = {"featureX": random.random(), "user_segment": random.choice(["C", "D"])}
            prediction, model_served = canary_manager.serve_request(input_data=input_d, user_id=user_id)
            did_convert = False
            if model_served == canary_manager.canary_model_id:
                if random.random() < 0.155: # Slightly improved canary
                    did_convert = True
            else: # Champion
                if random.random() < 0.12:
                    did_convert = True
            canary_manager.record_outcome(
                request_id=canary_manager.observations_log[-1]["request_id"],
                ground_truth_value=1 if did_convert else 0,
                business_kpis={"did_convert": did_convert}
            )

        phase2_summary = canary_manager.get_performance_summary(model_task_type="classification")
        print("\n**Phase 2 Performance Summary:**")
        for model_id, stats in phase2_summary.get("variants", {}).items():
            print(f"  Model: {model_id}, Obs: {stats.get('observation_count')}, "
                  f"Conversion: {stats.get('conversion_rate', np.nan):.3f}, "
                  f"Errors: {stats.get('error_count', np.nan)}, "
                  f"Accuracy: {stats.get('accuracy', np.nan):.3f}")

        decision_phase2 = canary_manager.decide_next_step_conceptual(phase2_summary)
        print(f"Conceptual Decision after Phase 2: {decision_phase2}")

        if decision_phase2 == "PROMOTE_CANARY":
            logger.info(f"'{canary_manager.canary_model_id}' is ready for full promotion to champion!")
        elif decision_phase2 == "ROLLBACK_CANARY":
            logger.warning(f"'{canary_manager.canary_model_id}' needs to be rolled back. Reverting to '{canary_manager.champion_model_id}'.")
            canary_manager.adjust_canary_traffic(0.0) # Rollback

    print("\n=========================================================")
    print("=== Canary Release Manager Prototype Complete ===")
    print("=========================================================")
