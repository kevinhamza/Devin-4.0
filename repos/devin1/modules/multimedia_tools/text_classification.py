"""
modules/multimedia_tools/text_classification.py
------------------------------------------------
This module provides advanced text classification capabilities using machine learning models.
It supports custom categories, pretrained NLP models, and both single and batch classifications.
"""

from typing import List, Dict, Union
from transformers import pipeline


class TextClassification:
    """
    A class for performing text classification using NLP models.
    """

    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """
        Initialize the TextClassification module.

        :param model_name: The name of the pre-trained model to use for classification.
        """
        self.model_name = model_name
        self.classifier = self.load_model()

    def load_model(self):
        """
        Load the classification model from Hugging Face Transformers.

        :return: A pipeline object for text classification.
        """
        return pipeline("text-classification", model=self.model_name)

    def classify_text(self, text: str) -> Dict[str, Union[str, float]]:
        """
        Classify a single text input.

        :param text: The input text to classify.
        :return: A dictionary with the classification label and confidence score.
        """
        if not text.strip():
            raise ValueError("Input text is empty or whitespace only.")

        classification = self.classifier(text)[0]
        return {"label": classification["label"], "score": classification["score"]}

    def batch_classify(self, texts: List[str]) -> List[Dict[str, Union[str, float]]]:
        """
        Classify a batch of texts.

        :param texts: A list of input texts to classify.
        :return: A list of dictionaries containing classification labels and confidence scores.
        """
        return [self.classify_text(text) for text in texts]


# Example usage
if __name__ == "__main__":
    # Initialize the TextClassification class
    text_classifier = TextClassification()

    # Example of single text classification
    single_text = "Artificial Intelligence is transforming the future."
    try:
        single_classification = text_classifier.classify_text(single_text)
        print("Single Text Classification:")
        print(f"Text: {single_text}")
        print(f"Classification: {single_classification}")
    except ValueError as e:
        print(f"Error: {e}")

    # Example of batch text classification
    batch_texts = [
        "The weather is sunny and bright.",
        "I am feeling very sad today.",
        "The stock market crashed unexpectedly."
    ]

    try:
        batch_classifications = text_classifier.batch_classify(batch_texts)
        print("\nBatch Text Classification:")
        for idx, classification in enumerate(batch_classifications):
            print(f"{idx + 1}. Text: {batch_texts[idx]}")
            print(f"   Classification: {classification}")
    except ValueError as e:
        print(f"Error: {e}")
