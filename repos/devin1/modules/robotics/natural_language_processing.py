"""
Natural Language Processing Module
==================================
Implements NLP algorithms for understanding, processing, and generating natural language
within the robotics system.
"""

import spacy
import nltk
import logging
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from modules.utils.nlp_tools import preprocess_text, tokenize_text, analyze_sentiment

# Load required NLTK data
nltk.download("punkt")
nltk.download("wordnet")

class NaturalLanguageProcessing:
    """
    Handles NLP tasks such as tokenization, sentiment analysis, summarization, and more.
    """

    def __init__(self, transformer_model="t5-small"):
        """
        Initializes the NLP module with essential tools and models.

        Args:
            transformer_model (str): The Hugging Face transformer model to use for NLP tasks.
        """
        logging.info("[NLP] Initializing NLP module...")
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logging.info("[NLP] SpaCy language model loaded successfully.")
        except Exception as e:
            logging.error(f"[NLP] Error loading SpaCy language model: {e}")
            raise

        try:
            self.transformer_model_name = transformer_model
            self.tokenizer = AutoTokenizer.from_pretrained(transformer_model)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(transformer_model)
            self.summarization_pipeline = pipeline("summarization", model=self.model, tokenizer=self.tokenizer)
            logging.info("[NLP] Transformer model loaded successfully.")
        except Exception as e:
            logging.error(f"[NLP] Error loading Hugging Face transformer model: {e}")
            raise

    def preprocess(self, text: str) -> str:
        """
        Preprocesses the input text for NLP tasks.

        Args:
            text (str): The input text to preprocess.

        Returns:
            str: The preprocessed text.
        """
        return preprocess_text(text)

    def tokenize(self, text: str) -> list:
        """
        Tokenizes the input text.

        Args:
            text (str): The input text to tokenize.

        Returns:
            list: List of tokens.
        """
        return tokenize_text(text)

    def analyze_sentiment(self, text: str) -> str:
        """
        Analyzes the sentiment of the input text.

        Args:
            text (str): The input text for sentiment analysis.

        Returns:
            str: The sentiment result (positive, neutral, or negative).
        """
        return analyze_sentiment(text)

    def summarize_text(self, text: str) -> str:
        """
        Summarizes the input text using a transformer model.

        Args:
            text (str): The input text to summarize.

        Returns:
            str: The summarized text.
        """
        try:
            logging.info("[NLP] Summarizing text...")
            summary = self.summarization_pipeline(text, max_length=100, min_length=30, do_sample=False)
            return summary[0]["summary_text"]
        except Exception as e:
            logging.error(f"[NLP] Error summarizing text: {e}")
            return "Error generating summary."

    def named_entity_recognition(self, text: str) -> list:
        """
        Performs named entity recognition (NER) on the input text.

        Args:
            text (str): The input text for NER.

        Returns:
            list: List of recognized entities.
        """
        try:
            logging.info("[NLP] Performing named entity recognition...")
            doc = self.nlp(text)
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            return entities
        except Exception as e:
            logging.error(f"[NLP] Error performing NER: {e}")
            return []

    def translate_text(self, text: str, target_language: str = "es") -> str:
        """
        Translates the input text into a target language using a transformer model.

        Args:
            text (str): The text to translate.
            target_language (str): The target language (e.g., "es" for Spanish).

        Returns:
            str: The translated text.
        """
        try:
            logging.info(f"[NLP] Translating text to {target_language}...")
            prompt = f"Translate the following text to {target_language}: {text}"
            translation = self.summarization_pipeline(prompt, max_length=200)
            return translation[0]["summary_text"]
        except Exception as e:
            logging.error(f"[NLP] Error translating text: {e}")
            return "Error translating text."

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Initialize NLP
    nlp_module = NaturalLanguageProcessing()

    text = "Artificial intelligence is the simulation of human intelligence by machines."
    preprocessed_text = nlp_module.preprocess(text)
    print(f"Preprocessed Text: {preprocessed_text}")

    tokens = nlp_module.tokenize(text)
    print(f"Tokens: {tokens}")

    sentiment = nlp_module.analyze_sentiment(text)
    print(f"Sentiment: {sentiment}")

    summary = nlp_module.summarize_text(text)
    print(f"Summary: {summary}")

    entities = nlp_module.named_entity_recognition(text)
    print(f"Entities: {entities}")

    translated_text = nlp_module.translate_text(text, target_language="fr")
    print(f"Translated Text: {translated_text}")
