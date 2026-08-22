# Devin/mlops/data_validation/bias_detector.py
# Purpose: Conceptual implementations for detecting bias in datasets and ML models.
#          Focuses on fairness checks. 🛡️
# AI Lifecycle & Production AI 🧠🚀

import logging
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression # For a simple model example
from typing import Dict, Any, List, Union, Optional, Tuple

# Configure basic logging
logger = logging.getLogger("BiasDetector")
if not logger.handlers: # Prevent duplicate handlers
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class BiasDetector:
    """
    A conceptual class for detecting bias in datasets and ML model predictions.
    Provides methods to calculate various fairness metrics.
    """

    def __init__(self):
        logger.info("BiasDetector initialized. Ready for fairness checks. 🛡️")

    def _validate_inputs(self,
                         name_val_dict: Dict[str, pd.Series],
                         expected_length: Optional[int] = None) -> Optional[int]:
        """Helper to validate if inputs are Pandas Series and have consistent lengths."""
        current_length = expected_length
        for name, series in name_val_dict.items():
            if not isinstance(series, pd.Series):
                raise TypeError(f"Input '{name}' must be a Pandas Series. Got {type(series)}.")
            if current_length is None:
                current_length = len(series)
            elif len(series) != current_length:
                raise ValueError(f"Input Series '{name}' has length {len(series)}, inconsistent with expected length {current_length}.")
        return current_length

    def _get_group_data(self,
                        data_series: pd.Series,
                        protected_attribute_series: pd.Series,
                        group_value: Any) -> pd.Series:
        """Filters a data series for a specific group based on the protected attribute."""
        return data_series[protected_attribute_series == group_value]

    def check_dataset_representation(self,
                                     data: pd.DataFrame,
                                     protected_attribute_column: str,
                                     target_column: Optional[str] = None) -> Dict[str, Any]:
        """
        Checks the representation of different groups defined by the protected attribute
        in the dataset, and optionally, the distribution of the target variable within those groups.

        Args:
            data (pd.DataFrame): The dataset to analyze.
            protected_attribute_column (str): The name of the column containing protected attribute values.
            target_column (Optional[str]): The name of the target variable column (if applicable).

        Returns:
            Dict[str, Any]: A dictionary containing representation statistics.
        """
        if protected_attribute_column not in data.columns:
            raise ValueError(f"Protected attribute column '{protected_attribute_column}' not found in DataFrame.")
        if target_column and target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in DataFrame.")

        logger.info(f"Checking dataset representation for protected attribute: '{protected_attribute_column}'")
        results = {}
        
        group_counts = data[protected_attribute_column].value_counts()
        group_proportions = data[protected_attribute_column].value_counts(normalize=True)
        results["group_representation"] = {
            "counts": group_counts.to_dict(),
            "proportions": group_proportions.to_dict()
        }
        logger.info(f"  Group counts: {group_counts.to_dict()}")
        logger.info(f"  Group proportions: {group_proportions.to_dict()}")

        if target_column:
            target_distribution_by_group = data.groupby(protected_attribute_column)[target_column].agg(
                ['count', lambda x: (x == 1).sum(), lambda x: (x == 1).mean()] # Assuming binary target 0/1
            ).rename(columns={'<lambda_0>': 'positive_target_count', '<lambda_1>': 'positive_target_rate'})
            
            results["target_distribution_by_group"] = target_distribution_by_group.to_dict('index')
            logger.info(f"  Target (1s) distribution by group:\n{target_distribution_by_group}")
            
        return results

    def calculate_demographic_parity_metrics(self,
                                             predictions: pd.Series,
                                             protected_attribute: pd.Series,
                                             privileged_group_value: Any,
                                             unprivileged_group_value: Any,
                                             positive_outcome_label: Any = 1
                                             ) -> Dict[str, Optional[float]]:
        """
        Calculates Demographic Parity Difference and Disparate Impact Ratio.
        - Demographic Parity Difference: P(Y_hat=1 | G=unprivileged) - P(Y_hat=1 | G=privileged)
          Ideal value is 0. Negative values indicate bias against unprivileged group.
        - Disparate Impact Ratio: [P(Y_hat=1 | G=unprivileged)] / [P(Y_hat=1 | G=privileged)]
          Ideal value is 1. Values < 0.8 or > 1.25 often indicate adverse impact.

        Args:
            predictions (pd.Series): Model's predictions.
            protected_attribute (pd.Series): Series with protected attribute values.
            privileged_group_value (Any): Value representing the privileged group.
            unprivileged_group_value (Any): Value representing the unprivileged group.
            positive_outcome_label (Any): Label considered as the positive outcome in predictions.

        Returns:
            Dict containing 'demographic_parity_difference' and 'disparate_impact_ratio'.
        """
        self._validate_inputs({"predictions": predictions, "protected_attribute": protected_attribute})

        preds_priv = self._get_group_data(predictions, protected_attribute, privileged_group_value)
        preds_unpriv = self._get_group_data(predictions, protected_attribute, unprivileged_group_value)

        if preds_priv.empty or preds_unpriv.empty:
            logger.warning("Demographic Parity: One or both groups are empty. Cannot calculate metrics.")
            return {"demographic_parity_difference": None, "disparate_impact_ratio": None, "message": "Empty group(s)."}

        rate_priv = (preds_priv == positive_outcome_label).mean()
        rate_unpriv = (preds_unpriv == positive_outcome_label).mean()

        dp_difference = rate_unpriv - rate_priv
        
        di_ratio = None
        if rate_priv > 1e-9: # Avoid division by zero
            di_ratio = rate_unpriv / rate_priv
        else:
            logger.warning("Disparate Impact: Selection rate for privileged group is zero. Ratio is undefined or infinite.")
            if rate_unpriv > 1e-9:
                 di_ratio = np.inf # Unprivileged selected, privileged not. Max disparity.
            else: # both zero
                 di_ratio = 1.0 # Or undefined, depends on convention for 0/0

        logger.info(f"Demographic Parity Difference ({unprivileged_group_value} - {privileged_group_value}): {dp_difference:.4f}")
        logger.info(f"Disparate Impact Ratio ({unprivileged_group_value} / {privileged_group_value}): {di_ratio if di_ratio is not None else 'Undefined'}")
        
        return {"demographic_parity_difference": dp_difference, "disparate_impact_ratio": di_ratio}


    def calculate_equalized_odds_metrics(self,
                                         true_labels: pd.Series,
                                         predictions: pd.Series,
                                         protected_attribute: pd.Series,
                                         privileged_group_value: Any,
                                         unprivileged_group_value: Any,
                                         positive_outcome_label: Any = 1
                                        ) -> Dict[str, Optional[float]]:
        """
        Calculates metrics related to Equalized Odds:
        - Equal Opportunity Difference: TPR_unpriv - TPR_priv
        - Average Odds Difference: 0.5 * [(TPR_unpriv - TPR_priv) + (FPR_unpriv - FPR_priv)]
          TPR (True Positive Rate) = Recall = TP / (TP + FN)
          FPR (False Positive Rate) = FP / (FP + TN)
          Ideal values are 0.

        Args:
            true_labels (pd.Series): Ground truth labels.
            predictions (pd.Series): Model's predictions.
            protected_attribute (pd.Series): Series with protected attribute values.
            privileged_group_value (Any): Value representing the privileged group.
            unprivileged_group_value (Any): Value representing the unprivileged group.
            positive_outcome_label (Any): Label considered as the positive outcome.

        Returns:
            Dict containing 'equal_opportunity_difference' and 'average_odds_difference'.
        """
        self._validate_inputs({"true_labels": true_labels, "predictions": predictions, "protected_attribute": protected_attribute})

        metrics = {"equal_opportunity_difference": None, "average_odds_difference": None}
        group_metrics = {}

        for group_val, group_name in [(privileged_group_value, "privileged"), (unprivileged_group_value, "unprivileged")]:
            true_group = self._get_group_data(true_labels, protected_attribute, group_val)
            preds_group = self._get_group_data(predictions, protected_attribute, group_val)

            if true_group.empty or preds_group.empty:
                logger.warning(f"Equalized Odds for group '{group_name}' ({group_val}): Group is empty. Cannot calculate metrics.")
                group_metrics[group_name] = {"tpr": np.nan, "fpr": np.nan}
                continue

            # Ensure positive_outcome_label is treated correctly for confusion matrix
            # If positive_outcome_label is not 1, we might need to remap or use pos_label in confusion_matrix
            # For simplicity, assume positive_outcome_label is what we consider "positive" (e.g., 1)
            # and the other label is "negative" (e.g., 0).
            # If labels are like 'A', 'B', then pos_label needs to be specified carefully.
            
            # Make sure labels for confusion_matrix are consistent (e.g., 0 and 1)
            # This simplified version assumes binary 0/1 or that positive_outcome_label is the "positive" class.
            cm_labels = sorted(true_labels.unique()) # Get unique labels present in the entire dataset
            if len(cm_labels) > 2 and positive_outcome_label not in cm_labels:
                logger.error(f"Positive outcome label {positive_outcome_label} not in true_labels for confusion matrix. Check labels.")
                # This path might need more robust handling of labels for cm.
                # For now, let's proceed assuming simple binary or correct positive_outcome_label.

            # If positive_outcome_label is, for example, 'Approved' and negative is 'Denied',
            # and these are strings, confusion_matrix needs `labels=['Denied', 'Approved']`
            # with the positive class as the second element for standard TN, FP, FN, TP indexing.
            # This implementation assumes numeric 0/1 with 1 as positive.
            
            try:
                # tn, fp, fn, tp = confusion_matrix(true_group, preds_group, labels=cm_labels).ravel()
                # More robust: explicitly use labels=[negative_label, positive_label] for consistent TP/FP meaning
                # Assuming positive_outcome_label is 1 and negative is 0 or any other value treated as negative.
                # Scikit-learn's confusion_matrix by default uses sorted unique labels.
                # If positive_outcome_label is not 1, this might be tricky.
                # Let's assume binary classification where positive_outcome_label = 1.
                if positive_outcome_label != 1: # A simple check, might need adjustment for non-0/1 labels
                    logger.warning("Metrics calculation assumes positive_outcome_label is 1 for TP/FP rates. Review if using other labels.")

                cm = confusion_matrix(true_group, preds_group, labels=[0, positive_outcome_label] if positive_outcome_label != 0 else [1,0])
                if cm.shape == (1,1): # Only one class present in true_group and preds_group for this group
                    if true_group.iloc[0] == positive_outcome_label: # All true are positive
                        tp = cm[0,0] if preds_group.iloc[0] == positive_outcome_label else 0
                        fn = cm[0,0] - tp
                        tn, fp = 0,0
                    else: # All true are negative
                        tn = cm[0,0] if preds_group.iloc[0] != positive_outcome_label else 0
                        fp = cm[0,0] - tn
                        tp, fn = 0,0
                elif cm.shape == (2,2):
                    tn, fp, fn, tp = cm.ravel()
                else: # Unexpected cm shape
                    logger.error(f"Unexpected confusion matrix shape {cm.shape} for group {group_name}.")
                    group_metrics[group_name] = {"tpr": np.nan, "fpr": np.nan}
                    continue


                tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
                group_metrics[group_name] = {"tpr": tpr, "fpr": fpr}

            except Exception as e:
                logger.error(f"Error calculating confusion matrix for group '{group_name}': {e}")
                group_metrics[group_name] = {"tpr": np.nan, "fpr": np.nan}


        if "privileged" in group_metrics and "unprivileged" in group_metrics:
            tpr_priv = group_metrics["privileged"]["tpr"]
            fpr_priv = group_metrics["privileged"]["fpr"]
            tpr_unpriv = group_metrics["unprivileged"]["tpr"]
            fpr_unpriv = group_metrics["unprivileged"]["fpr"]

            if not (np.isnan(tpr_unpriv) or np.isnan(tpr_priv)):
                metrics["equal_opportunity_difference"] = tpr_unpriv - tpr_priv
                logger.info(f"Equal Opportunity Difference (TPR_unpriv - TPR_priv): {metrics['equal_opportunity_difference']:.4f}")
            else:
                 logger.warning("Could not calculate Equal Opportunity Difference due to NaN TPR values.")


            if not (np.isnan(tpr_unpriv) or np.isnan(tpr_priv) or np.isnan(fpr_unpriv) or np.isnan(fpr_priv)):
                metrics["average_odds_difference"] = 0.5 * ((tpr_unpriv - tpr_priv) + (fpr_unpriv - fpr_priv))
                logger.info(f"Average Odds Difference: {metrics['average_odds_difference']:.4f}")
            else:
                 logger.warning("Could not calculate Average Odds Difference due to NaN TPR/FPR values.")
        else:
            logger.warning("Could not retrieve metrics for both privileged and unprivileged groups.")
            
        return metrics

# Example Usage
if __name__ == "__main__":
    print("=========================================================")
    print("=== Bias Detector Prototype (Fairness Checks) 🛡️ ===")
    print("=========================================================")

    # --- Sample Data Generation ---
    # Create a synthetic dataset where a protected attribute might correlate with features and outcomes
    np.random.seed(42)
    num_samples = 1000
    
    # Protected attribute (e.g., Group A is privileged, Group B is unprivileged)
    # Group A more likely to have higher feature1, Group B lower
    protected_attr = np.random.choice(['GroupA', 'GroupB'], size=num_samples, p=[0.6, 0.4])
    
    # Feature that correlates with protected attribute
    feature1 = np.where(protected_attr == 'GroupA', 
                        np.random.normal(loc=70, scale=10, size=num_samples),
                        np.random.normal(loc=50, scale=12, size=num_samples))
    
    feature2 = np.random.normal(loc=30, scale=5, size=num_samples)

    # Target variable: make it somewhat dependent on features and potentially on the protected group indirectly through feature1
    # Higher feature1 -> higher probability of positive outcome (1)
    # Let's introduce a slight direct bias for GroupA for demonstration if not careful
    # P(Y=1) = sigmoid(c0 + c1*feature1 + c2*feature2 + c3*(group=='GroupA'))
    # For simplicity, let's make it more based on feature1 which is already skewed
    true_labels_prob = 1 / (1 + np.exp(-(0.05 * feature1 - 0.02 * feature2 - 1))) # Biased towards higher feature1
    # Introduce a little more direct advantage for GroupA for clear bias demo
    true_labels_prob[protected_attr == 'GroupA'] *= 1.1 # Increase prob for GroupA
    true_labels_prob = np.clip(true_labels_prob, 0, 1)
    
    true_labels = (true_labels_prob > 0.5).astype(int)

    df = pd.DataFrame({
        'feature1': feature1,
        'feature2': feature2,
        'protected_group': protected_attr,
        'true_target': true_labels
    })

    logger.info(f"Sample DataFrame head:\n{df.head()}")

    # --- Initialize Detector ---
    bias_detector = BiasDetector()

    # --- 1. Dataset Representation Check ---
    print("\n--- 1. Dataset Representation Analysis ---")
    representation_stats = bias_detector.check_dataset_representation(
        data=df,
        protected_attribute_column='protected_group',
        target_column='true_target'
    )
    # print(f"  Representation Stats: {representation_stats}") # Detailed print

    # --- Train a simple model for prediction bias checks ---
    print("\n--- Training a simple model for illustration ---")
    X = df[['feature1', 'feature2']]
    y = df['true_target']
    
    # To simulate bias in model, we could use imbalanced data or features that strongly correlate with protected group
    # The data itself is already generated with some skew.
    X_train, X_test, y_train, y_test, protected_attr_train, protected_attr_test = train_test_split(
        X, y, df['protected_group'], test_size=0.3, random_state=42, stratify=df['protected_group'] # Stratify by group
    )

    model = LogisticRegression(solver='liblinear', random_state=42)
    model.fit(X_train, y_train)
    predictions_test = pd.Series(model.predict(X_test), index=X_test.index)
    true_labels_test = y_test

    logger.info(f"Model trained. Predictions generated on test set of size {len(predictions_test)}.")

    # --- 2. Demographic Parity & Disparate Impact ---
    print("\n--- 2. Demographic Parity & Disparate Impact ---")
    # Assuming 'GroupA' is privileged and 'GroupB' is unprivileged for this example
    dp_di_metrics = bias_detector.calculate_demographic_parity_metrics(
        predictions=predictions_test,
        protected_attribute=protected_attr_test,
        privileged_group_value='GroupA',
        unprivileged_group_value='GroupB',
        positive_outcome_label=1
    )
    print(f"  Demographic Parity Difference (GroupB - GroupA): {dp_di_metrics['demographic_parity_difference']:.4f}")
    print(f"  Disparate Impact Ratio (GroupB / GroupA): {dp_di_metrics['disparate_impact_ratio']:.4f}")
    if dp_di_metrics['disparate_impact_ratio'] is not None and (dp_di_metrics['disparate_impact_ratio'] < 0.8 or dp_di_metrics['disparate_impact_ratio'] > 1.25):
        print("  WARNING: Disparate Impact Ratio suggests potential adverse impact.")


    # --- 3. Equalized Odds Metrics ---
    print("\n--- 3. Equalized Odds Metrics (Equal Opportunity, Average Odds Diff) ---")
    eq_odds_metrics = bias_detector.calculate_equalized_odds_metrics(
        true_labels=true_labels_test,
        predictions=predictions_test,
        protected_attribute=protected_attr_test,
        privileged_group_value='GroupA',
        unprivileged_group_value='GroupB',
        positive_outcome_label=1
    )
    if eq_odds_metrics['equal_opportunity_difference'] is not None:
        print(f"  Equal Opportunity Difference (TPR_GroupB - TPR_GroupA): {eq_odds_metrics['equal_opportunity_difference']:.4f}")
    if eq_odds_metrics['average_odds_difference'] is not None:
        print(f"  Average Odds Difference: {eq_odds_metrics['average_odds_difference']:.4f}")
    
    if eq_odds_metrics.get('equal_opportunity_difference') is None and eq_odds_metrics.get('average_odds_difference') is None:
        print("  Could not calculate Equalized Odds metrics. Check group sizes or TPR/FPR validity.")


    print("\nReminder: These are conceptual calculations. Real-world bias detection")
    print("requires careful consideration of context, appropriate metrics, and potentially")
    print("specialized libraries (e.g., Fairlearn, AIF360) and expert review.")
    print("The choice of privileged/unprivileged group and positive label significantly impacts results.")

    print("\n=========================================================")
    print("=== Bias Detector Prototype Complete ===")
    print("=========================================================")
