"""
Text Classification Module for Robotics
Provides functionality to classify text into predefined categories using machine learning.
"""

from typing import List, Dict
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

class TextClassifier:
    """
    Classifies text into categories using a pretrained model.
    """

    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """
        Initialize the text classification model.
        
        Args:
            model_name (str): The name of the pretrained classification model to use.
        """
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.classifier = pipeline("text-classification", model=self.model, tokenizer=self.tokenizer)

    def classify_text(self, text: str) -> Dict[str, float]:
        """
        Classify a single piece of text into a category.
        
        Args:
            text (str): The text to classify.
        
        Returns:
            Dict[str, float]: Classification label and its confidence score.
        """
        if len(text.strip()) == 0:
            raise ValueError("Input text cannot be empty.")
        
        result = self.classifier(text)[0]
        return {"label": result['label'], "score": result['score']}

    def batch_classify(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Classify a batch of texts into categories.
        
        Args:
            texts (List[str]): A list of texts to classify.
        
        Returns:
            List[Dict[str, float]]: A list of classification results with labels and scores.
        """
        classifications = []
        for text in texts:
            try:
                classifications.append(self.classify_text(text))
            except ValueError as e:
                classifications.append({"error": str(e)})
        return classifications


# Example Usage
if __name__ == "__main__":
    classifier = TextClassifier()

    # Single text classification
    text = "Robotics is an exciting field of artificial intelligence."
    print("Single Text Classification:")
    print(classifier.classify_text(text))

    # Batch text classification
    texts = [
        "The robot successfully completed the task.",
        "This is a challenging problem to solve.",
        "The system encountered an unexpected error."
    ]
    print("\nBatch Text Classification:")
    print(classifier.batch_classify(texts))
