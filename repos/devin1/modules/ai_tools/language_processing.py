"""
language_processing.py
Handles advanced NLP (Natural Language Processing) tasks such as sentiment analysis, text summarization,
translation, named entity recognition, and more.

Part of the Devin AI project.
"""

import os
import re
from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

class LanguageProcessing:
    def __init__(self):
        """Initialize the NLP pipelines and models."""
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        self.summarizer = pipeline("summarization")
        self.translation_tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-de")
        self.translation_model = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-en-de")
        self.ner = pipeline("ner", grouped_entities=True)

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Perform sentiment analysis on the given text."""
        try:
            result = self.sentiment_analyzer(text)
            return {"success": True, "sentiment": result[0]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def summarize_text(self, text: str, max_length: int = 100) -> Dict[str, Any]:
        """Summarize the input text."""
        try:
            summary = self.summarizer(text, max_length=max_length, min_length=25, do_sample=False)
            return {"success": True, "summary": summary[0]["summary_text"]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def translate_text(self, text: str, target_language: str = "de") -> Dict[str, Any]:
        """Translate the text into the target language."""
        try:
            inputs = self.translation_tokenizer.encode(text, return_tensors="pt", max_length=512, truncation=True)
            outputs = self.translation_model.generate(inputs, max_length=512, num_beams=4, early_stopping=True)
            translation = self.translation_tokenizer.decode(outputs[0], skip_special_tokens=True)
            return {"success": True, "translation": translation}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def named_entity_recognition(self, text: str) -> Dict[str, Any]:
        """Identify named entities in the given text."""
        try:
            entities = self.ner(text)
            return {"success": True, "entities": entities}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def perform_task(self, task: str, text: str, **kwargs) -> Dict[str, Any]:
        """
        Execute the specified NLP task.
        Args:
            task (str): The name of the NLP task (e.g., "sentiment", "summarize", "translate", "ner").
            text (str): The input text for the task.
        """
        task_mapping = {
            "sentiment": self.analyze_sentiment,
            "summarize": self.summarize_text,
            "translate": self.translate_text,
            "ner": self.named_entity_recognition,
        }

        if task not in task_mapping:
            return {"success": False, "error": f"Task '{task}' is not supported."}

        return task_mapping[task](text, **kwargs)


# Example usage
if __name__ == "__main__":
    nlp_processor = LanguageProcessing()

    # Sentiment Analysis
    sentiment_result = nlp_processor.analyze_sentiment("I love programming!")
    print("Sentiment Analysis:", sentiment_result)

    # Text Summarization
    text = (
        "Artificial intelligence (AI) refers to the simulation of human intelligence in machines that are programmed "
        "to think like humans and mimic their actions. The term may also be applied to any machine that exhibits traits "
        "associated with a human mind such as learning and problem-solving."
    )
    summary_result = nlp_processor.summarize_text(text)
    print("Text Summarization:", summary_result)

    # Translation
    translation_result = nlp_processor.translate_text("Hello, how are you?")
    print("Translation:", translation_result)

    # Named Entity Recognition
    ner_result = nlp_processor.named_entity_recognition("John lives in New York and works for Google.")
    print("Named Entity Recognition:", ner_result)
