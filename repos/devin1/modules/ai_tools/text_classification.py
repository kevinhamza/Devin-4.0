"""
text_classification.py
=======================

This module provides text classification tools for the Devin project. It supports various tasks,
including sentiment analysis, topic modeling, and spam detection using pre-trained machine learning models,
deep learning architectures, and customizable pipelines.

Dependencies:
- scikit-learn
- tensorflow
- transformers
"""

import os
import json
import numpy as np
from typing import List, Dict, Union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from transformers import pipeline as hf_pipeline, AutoTokenizer, AutoModelForSequenceClassification

class TextClassifier:
    """
    A powerful and extensible text classification system with support for ML and DL models.
    """
    def __init__(self):
        self.models = {}
        self.default_model = None
        self.tokenizer = None
        self.transformer_model = None

    def load_pretrained_model(self, model_name: str = "bert-base-uncased", task: str = "text-classification"):
        """
        Load a pre-trained transformer model for text classification.
        """
        try:
            print(f"Loading pre-trained model '{model_name}' for task '{task}'...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.transformer_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.default_model = hf_pipeline(task, model=self.transformer_model, tokenizer=self.tokenizer)
            print("Pre-trained model loaded successfully.")
        except Exception as e:
            print(f"Error loading pre-trained model: {e}")

    def add_custom_pipeline(self, name: str, model_pipeline: Pipeline):
        """
        Add a custom scikit-learn pipeline for text classification.
        """
        if name in self.models:
            print(f"Model pipeline '{name}' already exists. Overwriting.")
        self.models[name] = model_pipeline

    def classify(self, text: str, model_name: str = None) -> Union[str, Dict]:
        """
        Classify the input text using the specified model or the default model.
        """
        if model_name:
            if model_name in self.models:
                return self.models[model_name].predict([text])[0]
            else:
                raise ValueError(f"Model '{model_name}' not found in custom pipelines.")
        elif self.default_model:
            return self.default_model(text)
        else:
            raise RuntimeError("No models are loaded. Load a model first.")

    def classify_batch(self, texts: List[str], model_name: str = None) -> List[Union[str, Dict]]:
        """
        Classify a batch of texts using the specified model or the default model.
        """
        return [self.classify(text, model_name=model_name) for text in texts]


def build_naive_bayes_pipeline() -> Pipeline:
    """
    Build a scikit-learn pipeline for text classification using Naive Bayes.
    """
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    classifier = MultinomialNB()
    pipeline = Pipeline([("vectorizer", vectorizer), ("classifier", classifier)])
    return pipeline


def train_naive_bayes_pipeline(texts: List[str], labels: List[str]) -> Pipeline:
    """
    Train a Naive Bayes pipeline on provided data.
    """
    pipeline = build_naive_bayes_pipeline()
    pipeline.fit(texts, labels)
    print("Naive Bayes pipeline trained successfully.")
    return pipeline


def save_pipeline(pipeline: Pipeline, filepath: str):
    """
    Save a scikit-learn pipeline to a file.
    """
    import joblib
    joblib.dump(pipeline, filepath)
    print(f"Pipeline saved to {filepath}")


def load_pipeline(filepath: str) -> Pipeline:
    """
    Load a scikit-learn pipeline from a file.
    """
    import joblib
    pipeline = joblib.load(filepath)
    print(f"Pipeline loaded from {filepath}")
    return pipeline


def main():
    # Example usage of TextClassifier
    classifier = TextClassifier()

    # Load a pre-trained transformer model
    classifier.load_pretrained_model()

    # Example classification
    text = "The Devin project is extremely innovative and groundbreaking!"
    print("Transformer Classification:", classifier.classify(text))

    # Training a Naive Bayes pipeline
    texts = ["I love this!", "This is terrible.", "An amazing experience.", "Not good at all."]
    labels = ["positive", "negative", "positive", "negative"]
    nb_pipeline = train_naive_bayes_pipeline(texts, labels)

    # Adding the pipeline to the classifier
    classifier.add_custom_pipeline("naive_bayes", nb_pipeline)
    print("Naive Bayes Classification:", classifier.classify(text, model_name="naive_bayes"))

    # Save and reload the pipeline
    save_pipeline(nb_pipeline, "naive_bayes_pipeline.pkl")
    loaded_pipeline = load_pipeline("naive_bayes_pipeline.pkl")

    # Batch classification example
    batch_texts = ["Fantastic project!", "Needs improvement.", "Absolutely stunning!"]
    print("Batch Classification:", classifier.classify_batch(batch_texts, model_name="naive_bayes"))


if __name__ == "__main__":
    main()
