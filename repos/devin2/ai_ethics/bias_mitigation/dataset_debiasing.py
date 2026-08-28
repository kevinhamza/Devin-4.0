# Devin/ai_ethics/bias_mitigation/dataset_debiasing.py # Training Data Cleaning

import pandas as pd
import numpy as np
from collections import Counter
from typing import Dict, Any, List, Optional, Tuple

# Note: Actual implementation often relies on libraries like imbalanced-learn (for resampling)
# or Fairlearn (which includes some pre-processing techniques).
# This skeleton provides conceptual implementations using basic pandas/numpy.

# --- Privacy & Utility Warning ---
# Applying these techniques requires access to sensitive attributes in the dataset.
# Ensure compliance with privacy regulations (GDPR, CCPA, etc.) and ethical guidelines.
# Debiasing can sometimes impact overall model utility or accuracy on the majority group.
# Careful evaluation and trade-off analysis are essential.

class DatasetDebiaser:
    """
    Provides conceptual implementations of pre-processing techniques
    to mitigate bias in datasets before model training.

    Focuses on adjusting class distribution or instance weights based
    on sensitive attributes.
    """

    def __init__(self, sensitive_attributes: Optional[List[str]] = None):
        """
        Initializes the DatasetDebiaser.

        Args:
            sensitive_attributes (Optional[List[str]]): List of known sensitive attribute
                                                       column names for logging/warnings.
        """
        self.sensitive_attributes = sensitive_attributes or []
        print("DatasetDebiaser initialized.")
        if self.sensitive_attributes:
             print(f"  - Will issue warnings when operating on sensitive attributes: {self.sensitive_attributes}")


    def _check_columns(self, df: pd.DataFrame, required_cols: List[str]):
        """Checks if required columns exist in the DataFrame."""
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in DataFrame: {missing_cols}")
        if any(col in self.sensitive_attributes for col in required_cols):
            print(f"  WARNING: Operation involves sensitive attributes: {required_cols}. Ensure compliance.")


    # --- Resampling Techniques ---

    def resample_by_group(self,
                          df: pd.DataFrame,
                          sensitive_attribute_col: str,
                          strategy: Literal['oversample', 'undersample'] = 'oversample',
                          target_balance: Optional[Dict[Any, int]] = None,
                          random_state: Optional[int] = None) -> pd.DataFrame:
        """
        Resamples the dataset to balance representation across groups defined by a sensitive attribute.

        Args:
            df (pd.DataFrame): The input dataset.
            sensitive_attribute_col (str): The column containing the sensitive attribute.
            strategy (Literal['oversample', 'undersample']): Whether to oversample minority groups
                                                             or undersample majority groups.
            target_balance (Optional[Dict[Any, int]]): If provided, specifies the desired number
                                                       of samples for each group. If None, balances
                                                       to the size of the largest group (oversample)
                                                       or smallest group (undersample).
            random_state (Optional[int]): Seed for reproducible random sampling.

        Returns:
            pd.DataFrame: The resampled dataset.
        """
        print(f"\nAttempting {strategy} based on '{sensitive_attribute_col}'...")
        self._check_columns(df, [sensitive_attribute_col])

        group_counts = df[sensitive_attribute_col].value_counts()
        print(f"  - Initial group counts:\n{group_counts}")

        if target_balance:
            print(f"  - Using specified target balance: {target_balance}")
            n_samples_per_group = target_balance
        elif strategy == 'oversample':
            majority_size = group_counts.max()
            print(f"  - Oversampling minority groups to match majority size: {majority_size}")
            n_samples_per_group = {group: majority_size for group in group_counts.index}
        elif strategy == 'undersample':
            minority_size = group_counts.min()
            print(f"  - Undersampling majority groups to match minority size: {minority_size}")
            n_samples_per_group = {group: minority_size for group in group_counts.index}
        else:
            raise ValueError("Invalid strategy. Choose 'oversample' or 'undersample'.")

        resampled_dfs = []
        for group, target_count in n_samples_per_group.items():
            group_df = df[df[sensitive_attribute_col] == group]
            current_count = len(group_df)

            if current_count == 0:
                 print(f"  - Warning: Group '{group}' has no samples. Skipping.")
                 continue

            if current_count == target_count:
                 print(f"  - Group '{group}' already at target count ({target_count}). Keeping original.")
                 resampled_dfs.append(group_df)
            elif current_count < target_count: # Oversampling needed
                 print(f"  - Oversampling group '{group}' from {current_count} to {target_count}...")
                 # Simple oversampling with replacement
                 samples_needed = target_count - current_count
                 oversamples = group_df.sample(n=samples_needed, replace=True, random_state=random_state)
                 resampled_dfs.append(pd.concat([group_df, oversamples]))
            else: # Undersampling needed (current_count > target_count)
                 print(f"  - Undersampling group '{group}' from {current_count} to {target_count}...")
                 # Simple random undersampling
                 undersamples = group_df.sample(n=target_count, replace=False, random_state=random_state)
                 resampled_dfs.append(undersamples)

        if not resampled_dfs:
             print("  - Error: No dataframes to concatenate after resampling.")
             return pd.DataFrame(columns=df.columns) # Return empty DataFrame

        final_df = pd.concat(resampled_dfs).sample(frac=1, random_state=random_state).reset_index(drop=True) # Shuffle rows
        print(f"  - Resampling complete. Final dataset size: {len(final_df)}")
        print(f"  - Final group counts:\n{final_df[sensitive_attribute_col].value_counts()}")
        return final_df


    # --- Reweighting Technique ---

    def calculate_instance_weights(self,
                                   df: pd.DataFrame,
                                   sensitive_attribute_col: str,
                                   label_col: str) -> pd.Series:
        """
        Calculates instance weights to mitigate bias.

        This example implements a simple inverse frequency weighting for group balance.
        More complex methods exist (e.g., balancing based on group and label combinations).

        Args:
            df (pd.DataFrame): The input dataset.
            sensitive_attribute_col (str): The column containing the sensitive attribute.
            label_col (str): The column containing the target label (can influence some weighting schemes).

        Returns:
            pd.Series: A pandas Series containing the calculated weight for each instance (row)
                       in the original DataFrame's index order.
        """
        print(f"\nCalculating instance weights based on '{sensitive_attribute_col}' inverse frequency...")
        self._check_columns(df, [sensitive_attribute_col, label_col])

        group_counts = df[sensitive_attribute_col].value_counts()
        total_samples = len(df)
        num_groups = len(group_counts)

        if total_samples == 0 or num_groups == 0:
             print("  - Warning: Cannot calculate weights for empty dataset or zero groups.")
             return pd.Series([1.0] * total_samples, index=df.index) # Return default weights

        # Simple inverse frequency weighting: weight = (total_samples / num_groups) / group_count
        # This aims to give each group roughly equal total weight in the dataset.
        weights = {}
        for group, count in group_counts.items():
            weights[group] = (total_samples / num_groups) / count if count > 0 else 0
            print(f"  - Group '{group}': Count={count}, Calculated Weight={weights[group]:.4f}")

        # Apply weights to each instance
        instance_weights = df[sensitive_attribute_col].map(weights)
        instance_weights = instance_weights.fillna(1.0) # Default weight if group mapping failed

        print(f"  - Instance weights calculated. Min={instance_weights.min():.4f}, Max={instance_weights.max():.4f}, Mean={instance_weights.mean():.4f}")
        return instance_weights

    # --- Other Potential Techniques (Placeholders) ---

    def augment_minority_data(self, df: pd.DataFrame, sensitive_attribute_col: str, label_col: str) -> pd.DataFrame:
        """Conceptual placeholder for data augmentation techniques (e.g., SMOTE)."""
        print(f"\nConceptual Data Augmentation based on '{sensitive_attribute_col}' (Placeholder)...")
        self._check_columns(df, [sensitive_attribute_col, label_col])
        # --- Placeholder Logic ---
        # Use libraries like 'imblearn.over_sampling.SMOTE' or custom generative models
        # trained specifically not to reinforce existing biases. Requires careful implementation.
        print("  - Placeholder: Data augmentation logic not implemented.")
        # --- End Placeholder ---
        return df # Return original df for now

    def modify_features(self, df: pd.DataFrame, sensitive_attribute_col: str) -> pd.DataFrame:
        """Conceptual placeholder for feature modification/transformation to remove bias."""
        print(f"\nConceptual Feature Modification for '{sensitive_attribute_col}' (Placeholder)...")
        self._check_columns(df, [sensitive_attribute_col])
        # --- Placeholder Logic ---
        # Techniques might include:
        # - Dropping the sensitive attribute (can hurt utility, doesn't remove proxy bias).
        # - Learning representations uncorrelated with the sensitive attribute (e.g., using adversarial debiasing).
        # These are advanced and can significantly impact model performance. Use with caution.
        print("  - Placeholder: Feature modification logic not implemented.")
         # --- End Placeholder ---
        return df # Return original df for now


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Dataset Debiasing Example ---")

    # Create Sample Biased Data
    data = {
        'feature1': np.random.rand(100),
        'feature2': np.random.rand(100) * 10,
        # Biased groups: 80 'A', 20 'B'
        'group': ['A'] * 80 + ['B'] * 20,
        # Biased labels within group B: Mostly 0
        'label': [random.choice([0, 1]) if g == 'A' else (0 if random.random() < 0.8 else 1) for g in ['A'] * 80 + ['B'] * 20]
    }
    biased_df = pd.DataFrame(data)
    # Shuffle for realism
    biased_df = biased_df.sample(frac=1).reset_index(drop=True)

    print("\nOriginal Biased Dataset Info:")
    print(biased_df['group'].value_counts())
    print(biased_df.groupby('group')['label'].mean()) # Show label imbalance per group

    # Initialize Debiaser
    debiaser = DatasetDebiaser(sensitive_attributes=['group'])

    # --- Example 1: Oversampling ---
    print("\nApplying Oversampling:")
    oversampled_df = debiaser.resample_by_group(biased_df.copy(), 'group', strategy='oversample', random_state=42)
    print("\nOversampled Dataset Info:")
    print(oversampled_df['group'].value_counts())
    print(oversampled_df.groupby('group')['label'].mean()) # Label mean might change slightly due to sampling

    # --- Example 2: Undersampling ---
    print("\nApplying Undersampling:")
    undersampled_df = debiaser.resample_by_group(biased_df.copy(), 'group', strategy='undersample', random_state=42)
    print("\nUndersampled Dataset Info:")
    print(undersampled_df['group'].value_counts())
    print(undersampled_df.groupby('group')['label'].mean())

    # --- Example 3: Reweighting ---
    print("\nApplying Reweighting:")
    instance_weights = debiaser.calculate_instance_weights(biased_df, 'group', 'label')
    # Add weights as a column for demonstration (usually passed directly to model training)
    biased_df['instance_weight'] = instance_weights
    print("\nDataset with Instance Weights (showing head):")
    print(biased_df[['group', 'label', 'instance_weight']].head())
    # Verify total weight per group (should be roughly equal)
    print("\nApproximate total weight per group:")
    print(biased_df.groupby('group')['instance_weight'].sum())

    print("\n--- End Example ---")
