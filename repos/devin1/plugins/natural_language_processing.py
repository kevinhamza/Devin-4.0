"""
plugins/natural_language_processing.py

Provides advanced natural language processing (NLP) capabilities.
"""

import nltk
from nltk.corpus import wordnet
from textblob import TextBlob
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import re

# Load Spacy Model
nlp_spacy = spacy.load("en_core_web_sm")

# Transformer-based sentiment analysis
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased")
sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

class NaturalLanguageProcessor:
    """Handles advanced NLP tasks."""

    def __init__(self):
        nltk.download('wordnet')
        nltk.download('omw-1.4')
        nltk.download('punkt')

    def sentiment_analysis(self, text):
        """
        Analyze the sentiment of a given text using Transformers.

        :param text: Input text to analyze.
        :return: Sentiment analysis result.
        """
        return sentiment_pipeline(text)

    def keyword_extraction(self, text):
        """
        Extract keywords from a given text using Spacy.

        :param text: Input text to analyze.
        :return: List of extracted keywords.
        """
        doc = nlp_spacy(text)
        keywords = [token.text for token in doc if token.is_alpha and not token.is_stop]
        return list(set(keywords))

    def text_summarization(self, text):
        """
        Summarize the provided text using TextBlob.

        :param text: Input text to summarize.
        :return: Summary of the text.
        """
        blob = TextBlob(text)
        sentences = blob.sentences
        return " ".join(str(s) for s in sentences[:3])  # First 3 sentences as summary

    def synonym_suggestion(self, word):
        """
        Suggest synonyms for a given word using WordNet.

        :param word: Input word to find synonyms for.
        :return: List of synonyms.
        """
        synonyms = set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonyms.add(lemma.name())
        return list(synonyms)

    def correct_spelling(self, text):
        """
        Correct spelling errors in a text using TextBlob.

        :param text: Input text with potential spelling errors.
        :return: Corrected text.
        """
        blob = TextBlob(text)
        return str(blob.correct())

    def named_entity_recognition(self, text):
        """
        Perform Named Entity Recognition (NER) on text using Spacy.

        :param text: Input text to analyze.
        :return: Entities and their labels.
        """
        doc = nlp_spacy(text)
        return [(ent.text, ent.label_) for ent in doc.ents]

    def generate_ngrams(self, text, n=2):
        """
        Generate n-grams from the provided text.

        :param text: Input text to generate n-grams from.
        :param n: Number of words in each n-gram.
        :return: List of n-grams.
        """
        words = re.findall(r'\b\w+\b', text)
        return [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]


# Example Usage
if __name__ == "__main__":
    nlp = NaturalLanguageProcessor()

    sample_text = "Natural Language Processing is an exciting field of Artificial Intelligence."
    print("Sentiment Analysis:", nlp.sentiment_analysis(sample_text))
    print("Keywords:", nlp.keyword_extraction(sample_text))
    print("Summarization:", nlp.text_summarization(sample_text))
    print("Synonyms for 'exciting':", nlp.synonym_suggestion("exciting"))
    print("Spelling Correction:", nlp.correct_spelling("Natrual Langage Processng is excting."))
    print("Named Entities:", nlp.named_entity_recognition(sample_text))
    print("Bigrams:", nlp.generate_ngrams(sample_text, 2))
