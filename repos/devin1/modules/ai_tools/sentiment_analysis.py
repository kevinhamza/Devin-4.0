"""
sentiment_analysis.py
----------------------
Provides sentiment analysis tools to classify text as positive, negative, or neutral.
Supports multiple languages and customizable sentiment scoring methods.
"""

import re
import numpy as np
from textblob import TextBlob
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

class SentimentAnalyzer:
    """
    A class for performing sentiment analysis using TextBlob and machine learning models.
    """

    def __init__(self):
        """
        Initialize the SentimentAnalyzer with prebuilt models and training pipelines.
        """
        self.model_pipeline = None
        self._initialize_ml_pipeline()

    def preprocess_text(self, text):
        """
        Preprocess input text for sentiment analysis.

        Args:
            text (str): Input text.

        Returns:
            str: Cleaned and processed text.
        """
        text = re.sub(r"http\S+", "", text)  # Remove URLs
        text = re.sub(r"@\w+", "", text)    # Remove mentions
        text = re.sub(r"#\w+", "", text)    # Remove hashtags
        text = re.sub(r"[^a-zA-Z\s]", "", text)  # Remove non-alphanumeric characters
        text = text.lower().strip()        # Convert to lowercase and trim whitespace
        return text

    def analyze_with_textblob(self, text):
        """
        Perform sentiment analysis using TextBlob.

        Args:
            text (str): Input text.

        Returns:
            dict: Sentiment polarity and subjectivity scores.
        """
        processed_text = self.preprocess_text(text)
        analysis = TextBlob(processed_text)
        return {
            "polarity": analysis.sentiment.polarity,
            "subjectivity": analysis.sentiment.subjectivity,
            "sentiment": self._get_sentiment_label(analysis.sentiment.polarity),
        }

    def _initialize_ml_pipeline(self):
        """
        Initialize a machine learning pipeline for sentiment analysis.
        """
        self.model_pipeline = Pipeline([
            ("vectorizer", TfidfVectorizer()),
            ("classifier", MultinomialNB()),
        ])

    def train_ml_model(self, texts, labels):
        """
        Train the machine learning sentiment analysis model.

        Args:
            texts (list): List of text samples.
            labels (list): Corresponding sentiment labels.

        Returns:
            None
        """
        texts = [self.preprocess_text(text) for text in texts]
        X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)
        self.model_pipeline.fit(X_train, y_train)
        predictions = self.model_pipeline.predict(X_test)
        print("Model training complete.")
        print(classification_report(y_test, predictions))

    def predict_with_ml_model(self, text):
        """
        Predict sentiment using the trained machine learning model.

        Args:
            text (str): Input text.

        Returns:
            str: Predicted sentiment label.
        """
        processed_text = self.preprocess_text(text)
        prediction = self.model_pipeline.predict([processed_text])[0]
        return prediction

    def _get_sentiment_label(self, polarity):
        """
        Map polarity score to sentiment label.

        Args:
            polarity (float): Polarity score.

        Returns:
            str: Sentiment label.
        """
        if polarity > 0:
            return "Positive"
        elif polarity < 0:
            return "Negative"
        return "Neutral"

# Example Usage
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()

    # TextBlob-based sentiment analysis
    text = "I absolutely love this product! It's amazing."
    sentiment = analyzer.analyze_with_textblob(text)
    print(f"TextBlob Analysis: {sentiment}")

    # Machine learning model training and prediction
    sample_texts = [
        "I love this!",
        "This is awful.",
        "I'm not sure about this product.",
        "It's okay, not the best but not the worst.",
        "Fantastic quality and great support!",
    ]
    sample_labels = ["Positive", "Negative", "Neutral", "Neutral", "Positive"]

    analyzer.train_ml_model(sample_texts, sample_labels)

    new_text = "This is the worst experience I've ever had."
    ml_sentiment = analyzer.predict_with_ml_model(new_text)
    print(f"Machine Learning Model Prediction: {ml_sentiment}")
