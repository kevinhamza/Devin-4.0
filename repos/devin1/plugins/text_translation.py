"""
plugins/text_summarization.py
-----------------------------
Provides tools for summarizing text using advanced NLP techniques.
"""

from transformers import pipeline
from typing import List, Dict, Any


class TextSummarizer:
    def __init__(self):
        """
        Initializes the text summarizer using a pre-trained model.
        """
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    def summarize_text(self, text: str, max_length: int = 150, min_length: int = 40) -> str:
        """
        Summarizes the given text.

        :param text: The text to summarize.
        :param max_length: The maximum length of the summary.
        :param min_length: The minimum length of the summary.
        :return: The summarized text.
        """
        try:
            summary = self.summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
            return summary[0]['summary_text']
        except Exception as e:
            return f"Error during summarization: {e}"

    def summarize_batch(self, texts: List[str], max_length: int = 150, min_length: int = 40) -> List[str]:
        """
        Summarizes a batch of texts.

        :param texts: A list of texts to summarize.
        :param max_length: The maximum length of the summaries.
        :param min_length: The minimum length of the summaries.
        :return: A list of summarized texts.
        """
        try:
            summaries = self.summarizer(texts, max_length=max_length, min_length=min_length, do_sample=False)
            return [summary['summary_text'] for summary in summaries]
        except Exception as e:
            return [f"Error during summarization: {e}"]

    def summarize_to_dict(self, texts: Dict[str, str], max_length: int = 150, min_length: int = 40) -> Dict[str, Any]:
        """
        Summarizes a dictionary of texts, preserving their keys.

        :param texts: A dictionary where keys are identifiers, and values are texts to summarize.
        :param max_length: The maximum length of the summaries.
        :param min_length: The minimum length of the summaries.
        :return: A dictionary with keys and their summarized texts.
        """
        try:
            return {key: self.summarize_text(text, max_length, min_length) for key, text in texts.items()}
        except Exception as e:
            return {key: f"Error during summarization: {e}" for key, text in texts.items()}


if __name__ == "__main__":
    summarizer = TextSummarizer()
    sample_text = (
        "Artificial Intelligence (AI) is a field of computer science focused on creating intelligent machines "
        "that can perform tasks typically requiring human intelligence. These tasks include problem-solving, "
        "learning, reasoning, and understanding language. AI has applications in various industries, from healthcare "
        "to finance, and is revolutionizing the way we interact with technology."
    )
    
    print("Single text summarization:")
    print(summarizer.summarize_text(sample_text))

    batch_texts = [
        sample_text,
        "Natural language processing (NLP) is a branch of AI that focuses on the interaction between computers and "
        "humans through language. NLP enables computers to understand, interpret, and respond to human language in "
        "a way that is both meaningful and useful."
    ]
    print("\nBatch text summarization:")
    print(summarizer.summarize_batch(batch_texts))

    text_dict = {
        "Article1": sample_text,
        "Article2": batch_texts[1]
    }
    print("\nDictionary text summarization:")
    print(summarizer.summarize_to_dict(text_dict))
