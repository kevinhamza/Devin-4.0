"""
plugins/text_similarity.py

This module provides functionalities for comparing and calculating the similarity 
between two or more text inputs using various algorithms and AI-based models.
"""

import difflib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer

nltk.download('stopwords')

class TextSimilarity:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """
        Initialize the TextSimilarity class with an NLP model for advanced text embedding.
        """
        self.stop_words = set(stopwords.words('english'))
        self.sentence_transformer = SentenceTransformer(model_name)

    def clean_text(self, text):
        """
        Preprocess and clean the input text by removing stopwords and unnecessary characters.
        """
        tokens = text.lower().split()
        tokens = [word for word in tokens if word not in self.stop_words]
        return ' '.join(tokens)

    def jaccard_similarity(self, text1, text2):
        """
        Compute Jaccard similarity between two texts.
        """
        set1 = set(self.clean_text(text1).split())
        set2 = set(self.clean_text(text2).split())
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union != 0 else 0

    def cosine_similarity_sklearn(self, text1, text2):
        """
        Compute cosine similarity using TF-IDF vectorization.
        """
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    def cosine_similarity_embeddings(self, text1, text2):
        """
        Compute cosine similarity using embeddings from a SentenceTransformer model.
        """
        embeddings = self.sentence_transformer.encode([text1, text2])
        return cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    def sequence_matcher_similarity(self, text1, text2):
        """
        Compute similarity using difflib's SequenceMatcher.
        """
        return difflib.SequenceMatcher(None, text1, text2).ratio()

    def calculate_similarity(self, text1, text2, method="cosine"):
        """
        Calculate similarity between two texts using a specified method.
        """
        if method == "jaccard":
            return self.jaccard_similarity(text1, text2)
        elif method == "cosine":
            return self.cosine_similarity_sklearn(text1, text2)
        elif method == "embedding":
            return self.cosine_similarity_embeddings(text1, text2)
        elif method == "sequence_matcher":
            return self.sequence_matcher_similarity(text1, text2)
        else:
            raise ValueError(f"Unsupported method: {method}")

# Example Usage
if __name__ == "__main__":
    ts = TextSimilarity()

    text1 = "Artificial Intelligence is the future of technology."
    text2 = "AI represents the future of tech innovations."

    print("Jaccard Similarity:", ts.calculate_similarity(text1, text2, method="jaccard"))
    print("Cosine Similarity (TF-IDF):", ts.calculate_similarity(text1, text2, method="cosine"))
    print("Cosine Similarity (Embeddings):", ts.calculate_similarity(text1, text2, method="embedding"))
    print("SequenceMatcher Similarity:", ts.calculate_similarity(text1, text2, method="sequence_matcher"))
