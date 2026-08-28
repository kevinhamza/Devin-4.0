import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk import pos_tag, ne_chunk
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

# Download required NLTK resources
nltk.download("punkt")
nltk.download("averaged_perceptron_tagger")
nltk.download("maxent_ne_chunker")
nltk.download("words")
nltk.download("vader_lexicon")
nltk.download("stopwords")

class NLPProcessing:
    """
    A class for handling various NLP tasks including text analysis, summarization, translation, 
    sentiment analysis, and more.
    """

    def __init__(self):
        # Initialize models and pipelines
        self.summarization_pipeline = pipeline("summarization", model="facebook/bart-large-cnn")
        self.translation_pipeline = pipeline("translation_en_to_fr", model="Helsinki-NLP/opus-mt-en-fr")
        self.qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
        self.sia = SentimentIntensityAnalyzer()
    
    @staticmethod
    def tokenize_text(text):
        """
        Tokenizes text into sentences and words.
        """
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        return {"sentences": sentences, "words": words}
    
    @staticmethod
    def remove_stopwords(text):
        """
        Removes stopwords from the text.
        """
        stop_words = set(stopwords.words("english"))
        words = word_tokenize(text)
        filtered_text = [word for word in words if word.lower() not in stop_words]
        return " ".join(filtered_text)
    
    @staticmethod
    def part_of_speech_tagging(text):
        """
        Performs part-of-speech tagging on the given text.
        """
        words = word_tokenize(text)
        return pos_tag(words)
    
    @staticmethod
    def named_entity_recognition(text):
        """
        Performs named entity recognition (NER) on the given text.
        """
        words = word_tokenize(text)
        pos_tags = pos_tag(words)
        return ne_chunk(pos_tags)
    
    def sentiment_analysis(self, text):
        """
        Performs sentiment analysis on the given text.
        """
        scores = self.sia.polarity_scores(text)
        sentiment = "positive" if scores["compound"] > 0 else "negative" if scores["compound"] < 0 else "neutral"
        return {"sentiment": sentiment, "scores": scores}
    
    def summarize_text(self, text, max_length=130, min_length=30):
        """
        Summarizes the given text using a pre-trained model.
        """
        try:
            summary = self.summarization_pipeline(text, max_length=max_length, min_length=min_length, do_sample=False)
            return summary[0]["summary_text"]
        except Exception as e:
            return str(e)
    
    def translate_text(self, text):
        """
        Translates the given text from English to French.
        """
        try:
            translated = self.translation_pipeline(text)
            return translated[0]["translation_text"]
        except Exception as e:
            return str(e)
    
    def question_answering(self, question, context):
        """
        Answers a question based on the provided context.
        """
        try:
            result = self.qa_pipeline(question=question, context=context)
            return {"answer": result["answer"], "score": result["score"]}
        except Exception as e:
            return str(e)
    
    def detect_language(self, text):
        """
        Detects the language of the given text.
        """
        try:
            blob = TextBlob(text)
            return blob.detect_language()
        except Exception as e:
            return str(e)
    
    def correct_grammar(self, text):
        """
        Corrects grammatical errors in the given text.
        """
        try:
            blob = TextBlob(text)
            return str(blob.correct())
        except Exception as e:
            return str(e)
    
    def extract_keywords(self, text, num_keywords=5):
        """
        Extracts keywords from the given text based on word frequency.
        """
        try:
            words = word_tokenize(text.lower())
            stop_words = set(stopwords.words("english"))
            filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
            freq_dist = nltk.FreqDist(filtered_words)
            keywords = [word for word, _ in freq_dist.most_common(num_keywords)]
            return keywords
        except Exception as e:
            return str(e)

if __name__ == "__main__":
    # Example usage
    nlp = NLPProcessing()
    sample_text = "Devin is an AI that can handle any task, including complex NLP tasks."
    context = "Devin is a powerful AI that can control a PC, manage tasks, and perform natural language processing."

    print("Tokenization:", nlp.tokenize_text(sample_text))
    print("Without Stopwords:", nlp.remove_stopwords(sample_text))
    print("POS Tagging:", nlp.part_of_speech_tagging(sample_text))
    print("NER:", nlp.named_entity_recognition(sample_text))
    print("Sentiment Analysis:", nlp.sentiment_analysis(sample_text))
    print("Summary:", nlp.summarize_text(sample_text))
    print("Translation:", nlp.translate_text(sample_text))
    print("Question Answering:", nlp.question_answering("What can Devin do?", context))
    print("Language Detection:", nlp.detect_language("Bonjour, Devin!"))
    print("Grammar Correction:", nlp.correct_grammar("Devin are a powerfull AI."))
    print("Keyword Extraction:", nlp.extract_keywords(sample_text))
