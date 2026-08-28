"""
Text Translation Module for Robotics
Provides functionality to translate text between languages using advanced NLP models.
"""

from typing import List, Dict
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

class TextTranslator:
    """
    Translates text between languages using pretrained models.
    """

    def __init__(self, model_name: str = "Helsinki-NLP/opus-mt-en-de"):
        """
        Initialize the text translation model.
        
        Args:
            model_name (str): The name of the pretrained translation model to use.
        """
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.translator = pipeline("translation", model=self.model, tokenizer=self.tokenizer)

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate a single piece of text from source_lang to target_lang.
        
        Args:
            text (str): The text to translate.
            source_lang (str): Source language code (e.g., "en" for English).
            target_lang (str): Target language code (e.g., "de" for German).
        
        Returns:
            str: Translated text.
        """
        if len(text.strip()) == 0:
            raise ValueError("Input text cannot be empty.")
        
        model_code = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"
        translator = pipeline("translation", model=model_code)
        
        translation = translator(text)
        return translation[0]['translation_text']

    def batch_translate(self, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
        """
        Translate a batch of texts from source_lang to target_lang.
        
        Args:
            texts (List[str]): A list of texts to translate.
            source_lang (str): Source language code.
            target_lang (str): Target language code.
        
        Returns:
            List[str]: A list of translated texts.
        """
        translations = []
        for text in texts:
            try:
                translations.append(self.translate_text(text, source_lang, target_lang))
            except ValueError as e:
                translations.append(f"Error: {str(e)}")
        return translations

    def detect_language_and_translate(self, text: str, target_lang: str, language_detection_model: str = "xlm-roberta-base") -> str:
        """
        Detect the language of a text and translate it to the target language.
        
        Args:
            text (str): The text to detect and translate.
            target_lang (str): The target language code.
            language_detection_model (str): Pretrained model for language detection.
        
        Returns:
            str: Translated text.
        """
        if len(text.strip()) == 0:
            raise ValueError("Input text cannot be empty.")
        
        # Placeholder for language detection
        # Assume detection for demonstration purposes
        detected_lang = "en"  # In real use, integrate with a language detection tool
        print(f"Detected language: {detected_lang}")
        
        return self.translate_text(text, detected_lang, target_lang)


# Example Usage
if __name__ == "__main__":
    translator = TextTranslator()
    
    text = "Artificial intelligence is shaping the future of technology."
    print("Single Text Translation (EN -> DE):")
    print(translator.translate_text(text, "en", "de"))
    
    texts = [
        "Hello, how are you?",
        "The future of robotics is fascinating.",
        "Translation capabilities are essential in modern AI."
    ]
    print("\nBatch Translation (EN -> FR):")
    print(translator.batch_translate(texts, "en", "fr"))

    print("\nDetect and Translate:")
    print(translator.detect_language_and_translate("Hola, ¿cómo estás?", "en"))
