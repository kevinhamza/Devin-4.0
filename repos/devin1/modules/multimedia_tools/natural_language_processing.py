"""
natural_language_processing.py

This module provides advanced NLP capabilities for text processing,
understanding, and generation. It includes features for sentiment analysis,
entity recognition, text summarization, machine translation, and more.
"""

from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import spacy
from textblob import TextBlob

class NaturalLanguageProcessing:
    def __init__(self):
        """
        Initialize NLP tools and pipelines.
        """
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        self.ner_model = spacy.load("en_core_web_sm")
        self.summarization_model_name = "facebook/bart-large-cnn"
        self.translation_model_name = "Helsinki-NLP/opus-mt-en-fr"
        self.summarization_model = AutoModelForSeq2SeqLM.from_pretrained(self.summarization_model_name)
        self.summarization_tokenizer = AutoTokenizer.from_pretrained(self.summarization_model_name)
        self.translation_model = AutoModelForSeq2SeqLM.from_pretrained(self.translation_model_name)
        self.translation_tokenizer = AutoTokenizer.from_pretrained(self.translation_model_name)

    def analyze_sentiment(self, text: str) -> dict:
        """
        Perform sentiment analysis on the given text.

        Args:
            text (str): Input text.

        Returns:
            dict: Sentiment analysis results.
        """
        return self.sentiment_analyzer(text)

    def recognize_entities(self, text: str) -> list:
        """
        Recognize named entities in the given text.

        Args:
            text (str): Input text.

        Returns:
            list: List of recognized entities with their labels.
        """
        doc = self.ner_model(text)
        return [{"entity": ent.text, "label": ent.label_} for ent in doc.ents]

    def summarize_text(self, text: str, max_length: int = 130, min_length: int = 30) -> str:
        """
        Summarize the given text.

        Args:
            text (str): Input text.
            max_length (int): Maximum length of the summary.
            min_length (int): Minimum length of the summary.

        Returns:
            str: Summarized text.
        """
        inputs = self.summarization_tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=1024, truncation=True)
        summary_ids = self.summarization_model.generate(inputs, max_length=max_length, min_length=min_length, length_penalty=2.0, num_beams=4, early_stopping=True)
        return self.summarization_tokenizer.decode(summary_ids[0], skip_special_tokens=True)

    def translate_text(self, text: str, target_language: str = "fr") -> str:
        """
        Translate the given text into a target language.

        Args:
            text (str): Input text.
            target_language (str): Target language code (default is French - "fr").

        Returns:
            str: Translated text.
        """
        prefix = f"translate English to {target_language}: "
        inputs = self.translation_tokenizer.encode(prefix + text, return_tensors="pt", max_length=512, truncation=True)
        translated_ids = self.translation_model.generate(inputs, max_length=512, num_beams=4, early_stopping=True)
        return self.translation_tokenizer.decode(translated_ids[0], skip_special_tokens=True)

    def detect_language(self, text: str) -> str:
        """
        Detect the language of the given text.

        Args:
            text (str): Input text.

        Returns:
            str: Detected language.
        """
        blob = TextBlob(text)
        return blob.detect_language()

# Example usage
if __name__ == "__main__":
    nlp_tool = NaturalLanguageProcessing()
    sample_text = "The quick brown fox jumps over the lazy dog."

    # Sentiment Analysis
    print("Sentiment Analysis:", nlp_tool.analyze_sentiment(sample_text))

    # Named Entity Recognition
    print("Named Entities:", nlp_tool.recognize_entities(sample_text))

    # Text Summarization
    long_text = (
        "Artificial intelligence is a branch of computer science that aims to "
        "create machines as intelligent as humans. AI is an interdisciplinary "
        "field with multiple approaches, but advancements in machine learning "
        "and deep learning are creating a paradigm shift in virtually every "
        "sector of the tech industry."
    )
    print("Summarized Text:", nlp_tool.summarize_text(long_text))

    # Translation
    print("Translation (to French):", nlp_tool.translate_text(sample_text))

    # Language Detection
    print("Language Detected:", nlp_tool.detect_language("Bonjour tout le monde!"))
