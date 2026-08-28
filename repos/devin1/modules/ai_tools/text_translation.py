"""
text_translation.py
--------------------
Provides tools for translating text between different languages using pre-trained
language models.
"""

from transformers import pipeline, MarianMTModel, MarianTokenizer

class TextTranslator:
    """
    A class for translating text between different languages.
    """

    def __init__(self, source_language="en", target_language="fr"):
        """
        Initialize the TextTranslator with source and target languages.

        Args:
            source_language (str): The source language code (e.g., 'en').
            target_language (str): The target language code (e.g., 'fr').
        """
        self.source_language = source_language
        self.target_language = target_language
        self.model_name = f"Helsinki-NLP/opus-mt-{source_language}-{target_language}"
        self.pipeline = None
        self.tokenizer = None
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """
        Load the translation model and tokenizer.
        """
        try:
            self.pipeline = pipeline("translation", model=self.model_name)
            self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
            self.model = MarianMTModel.from_pretrained(self.model_name)
        except Exception as e:
            print(f"Error initializing the translation model '{self.model_name}': {e}")

    def translate_text(self, text):
        """
        Translate text from the source language to the target language.

        Args:
            text (str): The input text to translate.

        Returns:
            str: The translated text.
        """
        try:
            translation = self.pipeline(text)
            return translation[0]["translation_text"]
        except Exception as e:
            return f"Error translating text: {e}"

    def translate_batch(self, texts):
        """
        Translate a batch of texts.

        Args:
            texts (list): A list of texts to translate.

        Returns:
            list: A list of translated texts.
        """
        try:
            translations = self.pipeline(texts)
            return [t["translation_text"] for t in translations]
        except Exception as e:
            return [f"Error translating batch: {e}"]

    def custom_translate(self, text):
        """
        Translate text using a custom implementation with direct model/tokenizer calls.

        Args:
            text (str): The input text to translate.

        Returns:
            str: The translated text.
        """
        try:
            input_ids = self.tokenizer.encode(text, return_tensors="pt")
            translated_ids = self.model.generate(input_ids)
            return self.tokenizer.decode(translated_ids[0], skip_special_tokens=True)
        except Exception as e:
            return f"Error in custom translation: {e}"


# Example Usage
if __name__ == "__main__":
    # Initialize the translator for English to French
    translator = TextTranslator(source_language="en", target_language="fr")

    # Translate a single sentence
    text = "Hello, how are you?"
    translated_text = translator.translate_text(text)
    print(f"Translated Text: {translated_text}")

    # Translate a batch of sentences
    texts = [
        "Good morning, everyone.",
        "What is your favorite color?",
        "This is a test sentence for translation."
    ]
    translated_texts = translator.translate_batch(texts)
    print("\nBatch Translations:")
    for i, translation in enumerate(translated_texts, 1):
        print(f"[{i}] {translation}")

    # Custom translation example
    custom_translation = translator.custom_translate("How is the weather today?")
    print("\nCustom Translation:")
    print(custom_translation)
