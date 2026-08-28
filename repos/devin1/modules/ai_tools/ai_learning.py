"""
ai_learning.py
--------------
Provides machine learning capabilities for Devin, including model training, prediction, and evaluation.
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

class AILearning:
    """
    A class for machine learning tasks, including data preprocessing, model training,
    prediction, and evaluation.
    """

    def __init__(self, storage_dir="models/"):
        """
        Initialize the AI Learning module.

        Args:
            storage_dir (str): Directory where models are stored.
        """
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.models = {}

    def load_data(self, file_path):
        """
        Load dataset from a CSV file.

        Args:
            file_path (str): Path to the dataset.

        Returns:
            pandas.DataFrame: Loaded dataset.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset not found: {file_path}")
        return pd.read_csv(file_path)

    def preprocess_data(self, data, target_column):
        """
        Preprocess the dataset.

        Args:
            data (pandas.DataFrame): Dataset to preprocess.
            target_column (str): Target column name.

        Returns:
            tuple: Preprocessed features and target.
        """
        X = data.drop(columns=[target_column])
        y = data[target_column]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
        return X_train, X_test, y_train, y_test

    def train_model(self, model_name, X_train, y_train, model_type="logistic"):
        """
        Train a machine learning model.

        Args:
            model_name (str): Name of the model to save.
            X_train (numpy.ndarray): Training features.
            y_train (numpy.ndarray): Training target.
            model_type (str): Type of model ("logistic" or "random_forest").

        Returns:
            object: Trained model.
        """
        if model_type == "logistic":
            model = LogisticRegression(random_state=42)
        elif model_type == "random_forest":
            model = RandomForestClassifier(random_state=42)
        else:
            raise ValueError("Unsupported model type. Use 'logistic' or 'random_forest'.")

        model.fit(X_train, y_train)
        self.models[model_name] = model

        with open(os.path.join(self.storage_dir, f"{model_name}.pkl"), "wb") as f:
            pickle.dump(model, f)

        return model

    def predict(self, model_name, X_test):
        """
        Make predictions using a trained model.

        Args:
            model_name (str): Name of the model to use.
            X_test (numpy.ndarray): Test features.

        Returns:
            numpy.ndarray: Predictions.
        """
        if model_name not in self.models:
            model_path = os.path.join(self.storage_dir, f"{model_name}.pkl")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found: {model_name}")
            with open(model_path, "rb") as f:
                self.models[model_name] = pickle.load(f)

        model = self.models[model_name]
        return model.predict(X_test)

    def evaluate_model(self, y_true, y_pred):
        """
        Evaluate the performance of a model.

        Args:
            y_true (numpy.ndarray): True target values.
            y_pred (numpy.ndarray): Predicted values.

        Returns:
            dict: Evaluation metrics.
        """
        accuracy = accuracy_score(y_true, y_pred)
        report = classification_report(y_true, y_pred, output_dict=True)
        return {"accuracy": accuracy, "classification_report": report}

    def list_models(self):
        """
        List all available models.

        Returns:
            list: Names of available models.
        """
        return [f.split(".pkl")[0] for f in os.listdir(self.storage_dir) if f.endswith(".pkl")]

# Example usage
if __name__ == "__main__":
    learning = AILearning()
    try:
        # Replace 'your_dataset.csv' with your dataset path and 'target_column_name' with the actual target column
        data = learning.load_data("your_dataset.csv")
        X_train, X_test, y_train, y_test = learning.preprocess_data(data, "target_column_name")
        
        # Train and evaluate logistic regression model
        model = learning.train_model("logistic_model", X_train, y_train, "logistic")
        predictions = learning.predict("logistic_model", X_test)
        metrics = learning.evaluate_model(y_test, predictions)
        print(metrics)

    except Exception as e:
        print(f"Error: {e}")
