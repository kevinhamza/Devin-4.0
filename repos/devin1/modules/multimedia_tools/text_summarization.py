"""
modules/multimedia_tools/text_summarization.py
----------------------------------------------
This module provides advanced text summarization capabilities using Natural Language Processing (NLP) models.
It supports extractive and abstractive summarization methods.
"""

from transformers import pipeline
from typing import List, Dict, Union


class TextSummarization:
    """
    A class to perform text summarization using advanced NLP models.
    """

    def __init__(self, model_name: str = "facebook/bart-large-cnn", max_length: int = 150, min_length: int = 30):
        """
        Initialize the TextSummarization module.

        :param model_name: The name of the pre-trained model to use.
        :param max_length: The maximum length of the summary.
        :param min_length: The minimum length of the summary.
        """
        self.model_name = model_name
        self.max_length = max_length
        self.min_length = min_length
        self.summarizer = self.load_model()

    def load_model(self):
        """
        Load the summarization model from Hugging Face Transformers.

        :return: A pipeline object for text summarization.
        """
        return pipeline("summarization", model=self.model_name)

    def summarize_text(self, text: str, max_length: int = None, min_length: int = None) -> str:
        """
        Generate a summary for the given text.

        :param text: The input text to summarize.
        :param max_length: The maximum length of the summary.
        :param min_length: The minimum length of the summary.
        :return: A summarized version of the input text.
        """
        if not text.strip():
            raise ValueError("Input text is empty or whitespace only.")

        max_length = max_length or self.max_length
        min_length = min_length or self.min_length

        summary = self.summarizer(
            text,
            max_length=max_length,
            min_length=min_length,
            truncation=True
        )
        return summary[0]["summary_text"]

    def batch_summarize(self, texts: List[str], max_length: int = None, min_length: int = None) -> List[str]:
        """
        Generate summaries for a batch of texts.

        :param texts: A list of input texts to summarize.
        :param max_length: The maximum length of the summaries.
        :param min_length: The minimum length of the summaries.
        :return: A list of summarized texts.
        """
        return [self.summarize_text(text, max_length, min_length) for text in texts]


# Example usage
if __name__ == "__main__":
    # Initialize the TextSummarization class
    summarizer = TextSummarization()

    # Sample text for summarization
    sample_text = (
        "Artificial Intelligence (AI) is the simulation of human intelligence processes by machines, especially "
        "computer systems. These processes include learning, reasoning, and self-correction. AI is increasingly "
        "playing a significant role in various sectors such as healthcare, finance, transportation, and more. "
        "The rapid advancement in AI technology has led to the development of autonomous systems and intelligent "
        "assistants that are capable of performing complex tasks."
    )

    # Summarize the sample text
    try:
        summary = summarizer.summarize_text(sample_text)
        print("Original Text:")
        print(sample_text)
        print("\nSummary:")
        print(summary)
    except ValueError as e:
        print(f"Error: {e}")
