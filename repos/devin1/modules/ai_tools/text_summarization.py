"""
text_summarization.py
----------------------
Provides tools for generating concise summaries of text content using extractive
and abstractive summarization techniques.
"""

from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import nltk
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Ensure NLTK components are available
nltk.download('punkt')

class TextSummarizer:
    """
    A class for performing text summarization using extractive and abstractive methods.
    """

    def __init__(self):
        """
        Initialize the TextSummarizer with prebuilt models and tools.
        """
        self.extractive_model = None
        self.abstractive_pipeline = None
        self._initialize_models()

    def _initialize_models(self):
        """
        Initialize models for both extractive and abstractive summarization.
        """
        self.abstractive_pipeline = pipeline("summarization", model="facebook/bart-large-cnn")
        self.extractive_model = TfidfVectorizer(stop_words="english")

    def summarize_extractive(self, text, num_sentences=3):
        """
        Perform extractive summarization by selecting the most important sentences.

        Args:
            text (str): Input text to summarize.
            num_sentences (int): Number of sentences to include in the summary.

        Returns:
            str: Extractive summary.
        """
        sentences = sent_tokenize(text)
        if len(sentences) <= num_sentences:
            return text  # Return original text if too short

        tfidf_matrix = self.extractive_model.fit_transform(sentences)
        sentence_scores = np.array(tfidf_matrix.sum(axis=1)).flatten()
        top_indices = sentence_scores.argsort()[-num_sentences:][::-1]

        summary = " ".join([sentences[i] for i in sorted(top_indices)])
        return summary

    def summarize_abstractive(self, text, max_length=130, min_length=30, do_sample=False):
        """
        Perform abstractive summarization using a pre-trained transformer model.

        Args:
            text (str): Input text to summarize.
            max_length (int): Maximum length of the summary.
            min_length (int): Minimum length of the summary.
            do_sample (bool): Whether to sample randomly for generating summary.

        Returns:
            str: Abstractive summary.
        """
        try:
            summary = self.abstractive_pipeline(
                text, max_length=max_length, min_length=min_length, do_sample=do_sample
            )[0]["summary_text"]
            return summary
        except Exception as e:
            return f"Error during abstractive summarization: {e}"

    def summarize(self, text, method="extractive", **kwargs):
        """
        Summarize the given text using the specified method.

        Args:
            text (str): Input text to summarize.
            method (str): Method of summarization ('extractive' or 'abstractive').
            **kwargs: Additional arguments for the summarization methods.

        Returns:
            str: Generated summary.
        """
        if method == "extractive":
            return self.summarize_extractive(text, **kwargs)
        elif method == "abstractive":
            return self.summarize_abstractive(text, **kwargs)
        else:
            raise ValueError("Invalid summarization method. Choose 'extractive' or 'abstractive'.")

# Example Usage
if __name__ == "__main__":
    summarizer = TextSummarizer()

    text = """
    Artificial intelligence (AI) is a field of computer science that aims to create machines
    that can perform tasks that would typically require human intelligence. This includes areas
    such as natural language processing, computer vision, robotics, and more. With the rapid
    advancements in machine learning and deep learning, AI has become an integral part of
    modern technology. Applications range from virtual assistants like Siri and Alexa to
    self-driving cars and predictive analytics in business. However, the rise of AI also brings
    challenges related to ethics, data privacy, and job displacement, requiring careful
    consideration and regulation.
    """

    # Extractive summarization
    extractive_summary = summarizer.summarize(text, method="extractive", num_sentences=2)
    print("Extractive Summary:")
    print(extractive_summary)

    # Abstractive summarization
    abstractive_summary = summarizer.summarize(text, method="abstractive", max_length=50, min_length=20)
    print("\nAbstractive Summary:")
    print(abstractive_summary)
