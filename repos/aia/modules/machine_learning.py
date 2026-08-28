import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report

class ModelManager:
    def __init__(self, model_type='random_forest'):
        self.model_type = model_type
        self.model = self._initialize_model()

    def _initialize_model(self):
        """Initialize model based on the model_type"""
        if self.model_type == 'random_forest':
            return RandomForestClassifier(n_estimators=100, random_state=42)
        elif self.model_type == 'logistic_regression':
            return LogisticRegression(random_state=42)
        elif self.model_type == 'decision_tree':
            return DecisionTreeClassifier(random_state=42)
        else:
            raise ValueError(f"Model type '{self.model_type}' not supported. Supported types: 'random_forest', 'logistic_regression', 'decision_tree'.")

    def load_data(self, filepath):
        """Load dataset from CSV file"""
        data = pd.read_csv(filepath)
        return data

    def preprocess_data(self, data):
        """Preprocess the data (handle missing values, scale features)"""
        data = data.dropna()  # Dropping rows with missing values
        features = data.drop('target', axis=1)
        target = data['target']
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        return features_scaled, target

    def train_model(self, X_train, y_train):
        """Train the model using the training data"""
        self.model.fit(X_train, y_train)

    def evaluate_model(self, X_test, y_test):
        """Evaluate the model on test data"""
        predictions = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        report = classification_report(y_test, predictions)
        return accuracy, report

    def save_model(self, model_filepath):
        """Save the trained model to a file"""
        import joblib
        joblib.dump(self.model, model_filepath)

    def load_model(self, model_filepath):
        """Load a trained model from a file"""
        import joblib
        self.model = joblib.load(model_filepath)

if __name__ == "__main__":
    ml = ModelManager(model_type='logistic_regression')  # Change model type if needed
    
    # Load data
    data = ml.load_data('path_to_data.csv')
    
    # Preprocess data
    X, y = ml.preprocess_data(data)
    
    # Train the model
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    ml.train_model(X_train, y_train)
    
    # Evaluate the model
    accuracy, report = ml.evaluate_model(X_test, y_test)
    print(f"Model Accuracy: {accuracy}")
    print(f"Classification Report:\n{report}")
    
    # Save the model
    ml.save_model('model.joblib')
