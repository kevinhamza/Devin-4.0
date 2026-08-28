# Devin/mlops/model_serving/a_b_testing.py
# Purpose: Conceptual framework for A/B testing ML models (Champion-Challenger).
#          Includes experiment setup, data logging, KPI calculation, and
#          basic statistical significance testing.
# Champion-Challenger 🏆🆚🛡️

import logging
import uuid
import random
import pandas as pd
import numpy as np
from scipy import stats
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Literal, Tuple

# Configure basic logging
logger = logging.getLogger("ABTestingFramework")
if not logger.handlers: # Prevent duplicate handlers
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class ABTestExperiment:
    """
    Manages a conceptual A/B test (Champion-Challenger) for ML models.
    """

    def __init__(self,
                 experiment_id: str,
                 champion_model_id: str,
                 challenger_model_ids: List[str],
                 key_performance_indicators: List[str], # e.g., ["conversion_rate", "avg_order_value", "model_accuracy"]
                 traffic_allocation: Optional[Dict[str, float]] = None, # e.g., {"champion": 0.8, "challenger_A": 0.2}
                 significance_level: float = 0.05,
                 min_observations_per_variant: int = 1000): # For statistical power
        
        self.experiment_id = experiment_id
        self.champion_model_id = champion_model_id
        self.challenger_model_ids = challenger_model_ids
        self.all_model_ids = [champion_model_id] + challenger_model_ids
        self.kpis_to_track = key_performance_indicators
        self.alpha = significance_level
        self.min_observations_per_variant = min_observations_per_variant

        if traffic_allocation:
            if not np.isclose(sum(traffic_allocation.values()), 1.0):
                raise ValueError("Traffic allocation percentages must sum to 1.0.")
            if not all(model_id in traffic_allocation for model_id in self.all_model_ids):
                missing = [m for m in self.all_model_ids if m not in traffic_allocation]
                raise ValueError(f"Traffic allocation missing for model(s): {missing}")
            self.traffic_allocation = traffic_allocation
            self.model_ids_for_assignment = [model_id for model_id in traffic_allocation for _ in range(int(traffic_allocation[model_id]*100))] # Simple weighted list
            random.shuffle(self.model_ids_for_assignment) # For random assignment simulation
        else: # Default to equal split if not provided
            num_models = len(self.all_model_ids)
            default_alloc = 1.0 / num_models
            self.traffic_allocation = {model_id: default_alloc for model_id in self.all_model_ids}
            logger.warning(f"No traffic allocation provided. Defaulting to equal split: {self.traffic_allocation}")
            self.model_ids_for_assignment = [model_id for model_id in self.traffic_allocation for _ in range(int(self.traffic_allocation[model_id]*100))]
            random.shuffle(self.model_ids_for_assignment)


        # Data log: model_id -> list of observation dictionaries
        self.observations_log: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None

        logger.info(f"A/B Test Experiment '{experiment_id}' initialized.")
        logger.info(f"  Champion: {champion_model_id}")
        logger.info(f"  Challengers: {challenger_model_ids}")
        logger.info(f"  KPIs: {kpis_to_track}")
        logger.info(f"  Traffic Allocation: {self.traffic_allocation}")
        logger.info(f"  Significance Level (alpha): {self.alpha}")

    def assign_variant_conceptual(self, user_or_request_id: str) -> str:
        """
        Conceptually assigns a user/request to a model variant based on traffic allocation.
        A real system would use a robust assignment mechanism (e.g., hashing user_id, sticky sessions).
        """
        # This is a very simple random assignment for illustration.
        # A more robust approach would use hashing for consistent assignment.
        # For example: variant_index = hash(user_or_request_id) % len(self.model_ids_for_assignment)
        # return self.model_ids_for_assignment[variant_index]
        
        # Using weighted random choice based on pre-calculated list
        if not self.model_ids_for_assignment: # Should not happen with proper init
            return random.choice(self.all_model_ids)
        return random.choice(self.model_ids_for_assignment)


    def record_observation(self,
                           model_id: str,
                           user_id: str, # Or session_id, request_id
                           prediction_output: Any, # Model's prediction
                           # Example outcome metrics - tailor to your KPIs
                           did_convert: Optional[bool] = None, # For conversion rate KPI
                           order_value: Optional[float] = None, # For AOV KPI
                           true_label: Optional[Any] = None, # For accuracy/F1 KPI
                           latency_ms: Optional[float] = None, # For performance KPI
                           custom_metrics: Optional[Dict[str, Any]] = None
                           ) -> None:
        """Records an observation for a specific model variant."""
        if model_id not in self.all_model_ids:
            logger.warning(f"Attempted to record observation for unknown model_id '{model_id}'. Ignoring.")
            return

        observation = {
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "model_id": model_id,
            "prediction": prediction_output,
            "did_convert": did_convert,
            "order_value": order_value,
            "true_label": true_label,
            "latency_ms": latency_ms,
            **(custom_metrics or {})
        }
        self.observations_log[model_id].append(observation)

    def _calculate_kpis_for_variant(self, model_id: str) -> Dict[str, Any]:
        """Calculates all defined KPIs for a given model variant from its logged observations."""
        variant_observations = self.observations_log.get(model_id, [])
        if not variant_observations:
            return {kpi: np.nan for kpi in self.kpis_to_track} # Return NaNs if no data

        kpi_results = {"observation_count": len(variant_observations)}
        
        # Convert list of dicts to DataFrame for easier calculation
        df_obs = pd.DataFrame(variant_observations)

        for kpi in self.kpis_to_track:
            value = np.nan
            try:
                if kpi == "conversion_rate" and "did_convert" in df_obs.columns:
                    conversions = df_obs["did_convert"].sum()
                    total = len(df_obs["did_convert"].dropna())
                    value = conversions / total if total > 0 else 0.0
                elif kpi == "avg_order_value" and "order_value" in df_obs.columns and "did_convert" in df_obs.columns:
                    converted_sales = df_obs[df_obs["did_convert"] == True]["order_value"].sum()
                    num_conversions = df_obs["did_convert"].sum()
                    value = converted_sales / num_conversions if num_conversions > 0 else 0.0
                elif kpi == "model_accuracy" and "true_label" in df_obs.columns and "prediction" in df_obs.columns:
                    # This assumes prediction and true_label are comparable for accuracy
                    value = accuracy_score(df_obs["true_label"].dropna(), df_obs["prediction"].loc[df_obs["true_label"].dropna().index])
                elif kpi == "avg_latency_ms" and "latency_ms" in df_obs.columns:
                    value = df_obs["latency_ms"].mean()
                # Add more KPI calculations as needed
                elif kpi in df_obs.columns: # For custom metrics directly logged
                    value = df_obs[kpi].mean() # Example: take mean of a custom logged metric
                else:
                    logger.warning(f"KPI '{kpi}' calculation not implemented or required data missing for model '{model_id}'.")
            except Exception as e:
                logger.error(f"Error calculating KPI '{kpi}' for model '{model_id}': {e}")
            kpi_results[kpi] = value
        return kpi_results

    def _perform_significance_test_proportions(self,
                                               successes_A: int, n_A: int,
                                               successes_B: int, n_B: int
                                               ) -> Tuple[Optional[float], Optional[float]]:
        """
        Performs a two-proportion Z-test.
        H0: p_A = p_B (proportions are equal)
        HA: p_A != p_B
        Returns (z_statistic, p_value).
        """
        if n_A == 0 or n_B == 0: return None, None
        p_A = successes_A / n_A
        p_B = successes_B / n_B
        
        p_pooled = (successes_A + successes_B) / (n_A + n_B)
        if p_pooled == 0 or p_pooled == 1: # Avoid division by zero in SE if pooled_p is 0 or 1
            # If both are 0% or 100%, z_stat is 0, p_value is 1 (no difference)
            # unless one is 0 and other >0, or one is 1 and other <1.
            # This simplified check might need refinement for edge cases.
            if np.isclose(p_A,p_B): return 0.0, 1.0
            # if one is 0 and another is not, scipy.stats.chi2_contingency is more robust for small N or p near 0/1
            # return np.nan, np.nan # Or handle as significant if rates are different
        
        se_pooled = np.sqrt(p_pooled * (1 - p_pooled) * (1/n_A + 1/n_B))
        if se_pooled == 0: 
             return 0.0, 1.0 if np.isclose(p_A, p_B) else (np.inf if p_A != p_B else 0.0), (1.0 if np.isclose(p_A, p_B) else 0.0)

        z_statistic = (p_A - p_B) / se_pooled
        p_value = 2 * (1 - stats.norm.cdf(np.abs(z_statistic))) # Two-tailed test
        return z_statistic, p_value

    def _perform_significance_test_means_ttest(self,
                                               sample_A: List[float],
                                               sample_B: List[float]
                                               ) -> Tuple[Optional[float], Optional[float]]:
        """
        Performs an independent two-sample t-test for means.
        H0: mean_A = mean_B
        HA: mean_A != mean_B
        Returns (t_statistic, p_value). Assumes unequal variance (Welch's t-test).
        """
        sample_A_clean = [x for x in sample_A if x is not None and not np.isnan(x)]
        sample_B_clean = [x for x in sample_B if x is not None and not np.isnan(x)]
        if len(sample_A_clean) < 2 or len(sample_B_clean) < 2: # t-test needs at least 2 samples in each group
            return None, None
        
        t_stat, p_val = stats.ttest_ind(sample_A_clean, sample_B_clean, equal_var=False) # Welch's t-test
        return t_stat, p_val

    def analyze_results(self) -> Dict[str, Any]:
        """
        Analyzes the logged observations, calculates KPIs for all variants,
        and performs significance tests comparing challengers to the champion.
        """
        logger.info(f"Starting analysis for experiment '{self.experiment_id}'...")
        self.end_time = datetime.utcnow() # Mark analysis time as conceptual end
        analysis_summary = {"experiment_id": self.experiment_id, "analysis_timestamp": self.end_time.isoformat()}
        
        variant_kpis: Dict[str, Dict[str, Any]] = {}
        for model_id in self.all_model_ids:
            kpis = self._calculate_kpis_for_variant(model_id)
            variant_kpis[model_id] = kpis
            if kpis["observation_count"] < self.min_observations_per_variant:
                logger.warning(f"Model '{model_id}' has {kpis['observation_count']} observations, "
                               f"which is less than the minimum {self.min_observations_per_variant}. "
                               "Statistical significance may be unreliable.")
        analysis_summary["variant_kpis"] = variant_kpis

        # --- Perform Significance Testing (Challenger vs Champion) ---
        champion_kpis = variant_kpis.get(self.champion_model_id)
        if not champion_kpis:
            logger.error(f"Champion model '{self.champion_model_id}' has no data. Cannot perform comparisons.")
            return analysis_summary
        
        analysis_summary["comparisons"] = {}

        for challenger_id in self.challenger_model_ids:
            challenger_kpis = variant_kpis.get(challenger_id)
            if not challenger_kpis:
                logger.warning(f"Challenger '{challenger_id}' has no data. Skipping comparison.")
                continue
            
            comparison_results = {}
            for kpi_name in self.kpis_to_track:
                champion_val = champion_kpis.get(kpi_name)
                challenger_val = challenger_kpis.get(kpi_name)
                
                stat_test_result = {"p_value": None, "statistic": None, "significant_at_alpha": None, "test_type": "N/A"}

                if pd.isna(champion_val) or pd.isna(challenger_val):
                    stat_test_result["message"] = "KPI value missing for one or both variants."
                elif kpi_name == "conversion_rate": # Example: Proportions test
                    # Need raw counts for proportions test
                    obs_champion = pd.DataFrame(self.observations_log.get(self.champion_model_id,[]))
                    obs_challenger = pd.DataFrame(self.observations_log.get(challenger_id,[]))
                    if "did_convert" in obs_champion.columns and "did_convert" in obs_challenger.columns:
                        n_champ = len(obs_champion["did_convert"].dropna())
                        s_champ = obs_champion["did_convert"].sum()
                        n_chall = len(obs_challenger["did_convert"].dropna())
                        s_chall = obs_challenger["did_convert"].sum()
                        if n_champ > 0 and n_chall > 0: # Ensure some observations for test
                            z_stat, p_val = self._perform_significance_test_proportions(s_champ, n_champ, s_chall, n_chall)
                            stat_test_result.update({"p_value": p_val, "statistic": z_stat, "test_type": "Z-test (proportions)"})
                            if p_val is not None: stat_test_result["significant_at_alpha"] = p_val < self.alpha
                elif kpi_name == "avg_order_value": # Example: Means test (t-test)
                    obs_champion = pd.DataFrame(self.observations_log.get(self.champion_model_id,[]))
                    obs_challenger = pd.DataFrame(self.observations_log.get(challenger_id,[]))
                    # We'd typically test on order values of converted users only, or all users if appropriate
                    sample_champ = obs_champion[obs_champion["did_convert"] == True]["order_value"].dropna().tolist() if "did_convert" in obs_champion else obs_champion["order_value"].dropna().tolist()
                    sample_chall = obs_challenger[obs_challenger["did_convert"] == True]["order_value"].dropna().tolist() if "did_convert" in obs_challenger else obs_challenger["order_value"].dropna().tolist()
                    
                    t_stat, p_val = self._perform_significance_test_means_ttest(sample_champ, sample_chall)
                    stat_test_result.update({"p_value": p_val, "statistic": t_stat, "test_type": "T-test (means)"})
                    if p_val is not None: stat_test_result["significant_at_alpha"] = p_val < self.alpha
                # Add other KPI significance tests here (e.g., for accuracy if applicable)
                
                comparison_results[kpi_name] = {
                    "champion_value": champion_val,
                    "challenger_value": challenger_val,
                    "absolute_difference": challenger_val - champion_val if pd.notna(challenger_val) and pd.notna(champion_val) else np.nan,
                    "relative_difference_pct": ((challenger_val - champion_val) / champion_val) * 100 if pd.notna(challenger_val) and pd.notna(champion_val) and champion_val !=0 else np.nan,
                    "significance_test": stat_test_result
                }
            analysis_summary["comparisons"][f"{challenger_id}_vs_{self.champion_model_id}"] = comparison_results
        
        logger.info(f"Analysis complete for experiment '{self.experiment_id}'.")
        return analysis_summary

    def get_recommendation_conceptual(self, analysis_results: Dict[str, Any], primary_kpi: str) -> str:
        """Provides a conceptual recommendation based on analysis results."""
        recommendation = f"Experiment '{self.experiment_id}': No clear winner based on primary KPI '{primary_kpi}' or insufficient data."
        best_challenger = None
        best_challenger_primary_kpi_val = -np.inf # Assuming higher is better for primary KPI

        champion_primary_kpi_val = analysis_results.get("variant_kpis", {}).get(self.champion_model_id, {}).get(primary_kpi, -np.inf)

        for comp_key, comp_data in analysis_results.get("comparisons", {}).items():
            challenger_id = comp_key.split('_vs_')[0] # Extract challenger ID
            challenger_primary_kpi_info = comp_data.get(primary_kpi)
            
            if challenger_primary_kpi_info:
                challenger_val = challenger_primary_kpi_info["challenger_value"]
                is_significant = challenger_primary_kpi_info.get("significance_test", {}).get("significant_at_alpha", False)
                
                # Simple logic: if challenger is significantly better on primary KPI
                if pd.notna(challenger_val) and challenger_val > champion_primary_kpi_val and is_significant:
                    if challenger_val > best_challenger_primary_kpi_val:
                        best_challenger_primary_kpi_val = challenger_val
                        best_challenger = challenger_id
        
        if best_challenger:
            recommendation = (f"Experiment '{self.experiment_id}': Challenger '{best_challenger}' shows statistically significant "
                              f"improvement on primary KPI '{primary_kpi}' ({best_challenger_primary_kpi_val:.4f}) "
                              f"compared to Champion ({champion_primary_kpi_val:.4f}). "
                              "Consider promoting '{best_challenger}'. Review secondary KPIs.")
        elif any(comp_data.get(primary_kpi, {}).get("significant_at_alpha") for comp_data in analysis_results.get("comparisons", {}).values()):
            recommendation = f"Experiment '{self.experiment_id}': Some significant differences observed on primary KPI '{primary_kpi}', but no challenger is clearly superior or further analysis of trade-offs is needed."
        
        return recommendation

# Example Usage
if __name__ == "__main__":
    print("=========================================================")
    print("=== A/B Testing (Champion-Challenger) Prototype 🧪 ===")
    print("=========================================================")

    # --- 1. Setup Experiment ---
    exp_id = f"Exp-{uuid.uuid4().hex[:6]}"
    champion = "model_v1_classic"
    challengers = ["model_v2_alpha", "model_v2_beta"]
    kpis = ["conversion_rate", "avg_order_value"] # "model_accuracy" could be another
    
    # Define traffic allocation for all models
    traffic_alloc = {champion: 0.70, challengers[0]: 0.15, challengers[1]: 0.15}

    experiment = ABTestExperiment(
        experiment_id=exp_id,
        champion_model_id=champion,
        challenger_model_ids=challengers,
        key_performance_indicators=kpis,
        traffic_allocation=traffic_alloc,
        min_observations_per_variant=50 # Lower for quick demo
    )
    print(f"Experiment '{experiment.experiment_id}' running...")

    # --- 2. Simulate Data Collection (Observations) ---
    num_simulation_days = 7
    users_per_day = 200
    print(f"\nSimulating {num_simulation_days} days of traffic with {users_per_day} users/day...")

    for day in range(num_simulation_days):
        for i in range(users_per_day):
            user = f"user_{day*users_per_day + i}"
            assigned_model = experiment.assign_variant_conceptual(user)
            
            # Simulate model predictions and outcomes (these would come from your models and systems)
            # These are highly simplified and biased for demonstration
            pred_output = random.choice([0, 1]) # Generic prediction
            converted = False
            order_val = 0.0
            
            if assigned_model == champion: # Baseline performance
                if random.random() < 0.10: # 10% conversion rate
                    converted = True
                    order_val = random.uniform(50, 150)
            elif assigned_model == challengers[0]: # Challenger A - slightly better conversion
                if random.random() < 0.12: # 12% conversion rate
                    converted = True
                    order_val = random.uniform(45, 140)
            elif assigned_model == challengers[1]: # Challenger B - similar conversion, better AOV
                if random.random() < 0.105: # 10.5% conversion rate
                    converted = True
                    order_val = random.uniform(70, 180) # Higher order value
            
            experiment.record_observation(
                model_id=assigned_model,
                user_id=user,
                prediction_output=pred_output,
                did_convert=converted,
                order_value=order_val if converted else 0.0,
                latency_ms=random.uniform(50,200)
            )
    
    for model_id in experiment.all_model_ids:
        logger.info(f"Model '{model_id}' received {len(experiment.observations_log[model_id])} observations.")


    # --- 3. Analyze Results ---
    print("\n--- Analyzing Experiment Results ---")
    analysis = experiment.analyze_results()

    # Print a summary of KPIs per variant
    print("\n**KPI Summary per Variant:**")
    for model_id, kpi_data in analysis.get("variant_kpis", {}).items():
        print(f"  Model ID: {model_id}")
        print(f"    Observations: {kpi_data.get('observation_count')}")
        for kpi_name in experiment.kpis_to_track:
            print(f"    {kpi_name}: {kpi_data.get(kpi_name, 'N/A'):.4f}" if isinstance(kpi_data.get(kpi_name), float) else f"    {kpi_name}: {kpi_data.get(kpi_name, 'N/A')}")

    # Print comparison details
    print("\n**Challenger vs. Champion Comparisons:**")
    for comp_key, comp_details in analysis.get("comparisons", {}).items():
        print(f"  Comparison: {comp_key}")
        for kpi_name, kpi_comp_data in comp_details.items():
            print(f"    KPI: {kpi_name}")
            print(f"      Champion Value: {kpi_comp_data['champion_value']:.4f}" if isinstance(kpi_comp_data['champion_value'], float) else f"      Champion Value: {kpi_comp_data['champion_value']}")
            print(f"      Challenger Value: {kpi_comp_data['challenger_value']:.4f}" if isinstance(kpi_comp_data['challenger_value'], float) else f"      Challenger Value: {kpi_comp_data['challenger_value']}")
            print(f"      Improvement (Abs): {kpi_comp_data.get('absolute_difference', np.nan):.4f}")
            print(f"      Improvement (Rel %): {kpi_comp_data.get('relative_difference_pct', np.nan):.2f}%")
            sig_test = kpi_comp_data.get('significance_test',{})
            print(f"      Significance Test ({sig_test.get('test_type','N/A')}):")
            print(f"        P-value: {sig_test.get('p_value'):.4f}" if sig_test.get('p_value') is not None else "        P-value: N/A")
            print(f"        Significant at alpha={experiment.alpha}: {sig_test.get('significant_at_alpha')}")


    # --- 4. Get Conceptual Recommendation ---
    print("\n--- Conceptual Recommendation ---")
    # Let's assume conversion_rate is our primary KPI for decision making
    primary_kpi_for_decision = "conversion_rate" 
    recommendation = experiment.get_recommendation_conceptual(analysis, primary_kpi=primary_kpi_for_decision)
    print(recommendation)

    print("\n=========================================================")
    print("=== A/B Testing Prototype Complete ===")
    print("=========================================================")
