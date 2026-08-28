"""
plugins/text_classification.py
===============================
Text classification capabilities for categorizing textual data.
"""

import os
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from typing import List, Tuple

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextClassifier:
    """
    A text classifier that uses TF-IDF and Multinomial Naive Bayes for text categorization.
    """

    def __init__(self):
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer()),
            ('classifier', MultinomialNB())
        ])
        self.is_trained = False

    def train(self, data: List[str], labels: List[str]) -> None:
        """
        Train the classifier using labeled data.

        Args:
            data (List[str]): List of text samples.
            labels (List[str]): Corresponding labels for the text samples.
        """
        logger.info("Splitting data into training and testing sets.")
        X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, random_state=42)
        
        logger.info("Training the model...")
        self.model.fit(X_train, y_train)
        self.is_trained = True

        logger.info("Evaluating the model...")
        predictions = self.model.predict(X_test)
        logger.info("\n%s", classification_report(y_test, predictions))
        logger.info("Training accuracy: %.2f%%", accuracy_score(y_test, predictions) * 100)

    def classify(self, text: str) -> str:
        """
        Classify a single text sample.

        Args:
            text (str): The text to classify.

        Returns:
            str: The predicted label.
        """
        if not self.is_trained:
            raise RuntimeError("The classifier has not been trained yet.")
        logger.info("Classifying text: %s", text)
        return self.model.predict([text])[0]

def save_model(classifier: TextClassifier, filepath: str) -> None:
    """
    Save the trained classifier model to a file.

    Args:
        classifier (TextClassifier): The trained classifier.
        filepath (str): Filepath to save the model.
    """
    import joblib
    if not classifier.is_trained:
        logger.warning("Model has not been trained. Saving an untrained model.")
    joblib.dump(classifier.model, filepath)
    logger.info("Model saved to %s", filepath)

def load_model(filepath: str) -> TextClassifier:
    """
    Load a trained classifier model from a file.

    Args:
        filepath (str): Filepath to load the model.

    Returns:
        TextClassifier: The loaded classifier.
    """
    import joblib
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No model file found at {filepath}")
    logger.info("Loading model from %s", filepath)
    classifier = TextClassifier()
    classifier.model = joblib.load(filepath)
    classifier.is_trained = True
    return classifier

# Example usage
if __name__ == "__main__":
    logger.info("Text Classification Plugin Example")

    # Sample data
    texts = [
        "I love programming in Python.",
        "The weather is sunny and bright today.",
        "Artificial intelligence is the future of technology.",
        "I enjoy playing football during weekends.",
        "Python is great for data science and machine learning."
    ]
    labels = ["technology", "weather", "technology", "sports", "technology"]

    # Initialize and train the classifier
    classifier = TextClassifier()
    classifier.train(texts, labels)

    # Classify a new text
    new_text = "Machine learning is a branch of artificial intelligence."
    logger.info("Predicted category: %s", classifier.classify(new_text))

    # Save the model
    save_model(classifier, "text_classifier_model.pkl")

    # Load the model and classify another text
    loaded_classifier = load_model("text_classifier_model.pkl")
    another_text = "It's raining heavily outside."
    logger.info("Predicted category: %s", loaded_classifier.classify(another_text))
