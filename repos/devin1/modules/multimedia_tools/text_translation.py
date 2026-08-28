"""
modules/multimedia_tools/text_translation.py
--------------------------------------------
This module provides advanced text translation capabilities using state-of-the-art NLP models.
It supports translation between multiple languages with custom model configurations.
"""

from transformers import pipeline
from typing import List, Dict, Union


class TextTranslation:
    """
    A class for text translation between multiple languages using NLP models.
    """

    def __init__(self, model_name: str = "Helsinki-NLP/opus-mt-en-fr"):
        """
        Initialize the TextTranslation module.

        :param model_name: The name of the pre-trained model for translation.
        """
        self.model_name = model_name
        self.translator = self.load_model()

    def load_model(self):
        """
        Load the translation model from Hugging Face Transformers.

        :return: A pipeline object for text translation.
        """
        return pipeline("translation", model=self.model_name)

    def translate_text(self, text: str, source_lang: str = "en", target_lang: str = "fr") -> str:
        """
        Translate the input text from source language to target language.

        :param text: The input text to translate.
        :param source_lang: The source language code.
        :param target_lang: The target language code.
        :return: Translated text.
        """
        if not text.strip():
            raise ValueError("Input text is empty or whitespace only.")

        translation = self.translator(text, src_lang=source_lang, tgt_lang=target_lang)
        return translation[0]["translation_text"]

    def batch_translate(self, texts: List[str], source_lang: str = "en", target_lang: str = "fr") -> List[str]:
        """
        Translate a batch of texts from source language to target language.

        :param texts: A list of input texts to translate.
        :param source_lang: The source language code.
        :param target_lang: The target language code.
        :return: A list of translated texts.
        """
        return [self.translate_text(text, source_lang, target_lang) for text in texts]


# Example usage
if __name__ == "__main__":
    # Initialize the TextTranslation class
    translator = TextTranslation()

    # Sample text for translation
    sample_text = "Artificial Intelligence is revolutionizing the world."

    # Translate the sample text
    try:
        translated_text = translator.translate_text(sample_text, source_lang="en", target_lang="fr")
        print("Original Text:")
        print(sample_text)
        print("\nTranslated Text (English to French):")
        print(translated_text)
    except ValueError as e:
        print(f"Error: {e}")

    # Example of batch translation
    batch_texts = [
        "Hello, how are you?",
        "The quick brown fox jumps over the lazy dog.",
        "What time is it?"
    ]

    try:
        batch_translations = translator.batch_translate(batch_texts, source_lang="en", target_lang="es")
        print("\nBatch Translations (English to Spanish):")
        for idx, translation in enumerate(batch_translations):
            print(f"{idx + 1}. {translation}")
    except ValueError as e:
        print(f"Error: {e}")
