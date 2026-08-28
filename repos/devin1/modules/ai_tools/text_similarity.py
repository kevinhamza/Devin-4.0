"""
Text Similarity Tools
=====================
This module provides tools to compute text similarity using various techniques,
such as token-based similarity, embedding-based similarity, and semantic similarity.

Dependencies:
- NLTK for tokenization and preprocessing
- SpaCy for word embeddings and linguistic features
- Transformers library for transformer-based embeddings
"""

import spacy
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import word_tokenize
from transformers import AutoTokenizer, AutoModel

class TextSimilarity:
    """
    A class to handle various text similarity computations.
    """
    
    def __init__(self, transformer_model="bert-base-uncased"):
        """
        Initializes the text similarity class with necessary models.

        Args:
            transformer_model (str): The name of the Hugging Face transformer model to use.
        """
        self.nlp = spacy.load("en_core_web_md")  # Load SpaCy model
        self.tokenizer = AutoTokenizer.from_pretrained(transformer_model)  # Tokenizer for transformer
        self.model = AutoModel.from_pretrained(transformer_model)  # Transformer model

    def token_based_similarity(self, text1, text2):
        """
        Computes similarity based on token overlap.

        Args:
            text1 (str): First text input.
            text2 (str): Second text input.

        Returns:
            float: Token overlap similarity score.
        """
        tokens1 = set(word_tokenize(text1.lower()))
        tokens2 = set(word_tokenize(text2.lower()))
        common_tokens = tokens1.intersection(tokens2)
        return len(common_tokens) / max(len(tokens1), len(tokens2))

    def embedding_based_similarity(self, text1, text2):
        """
        Computes similarity based on embeddings using SpaCy.

        Args:
            text1 (str): First text input.
            text2 (str): Second text input.

        Returns:
            float: Cosine similarity score between the text embeddings.
        """
        doc1 = self.nlp(text1)
        doc2 = self.nlp(text2)
        return doc1.similarity(doc2)

    def transformer_based_similarity(self, text1, text2):
        """
        Computes similarity using transformer embeddings.

        Args:
            text1 (str): First text input.
            text2 (str): Second text input.

        Returns:
            float: Cosine similarity score between the transformer embeddings.
        """
        # Tokenize and encode text
        tokens1 = self.tokenizer(text1, return_tensors="pt", padding=True, truncation=True)
        tokens2 = self.tokenizer(text2, return_tensors="pt", padding=True, truncation=True)

        # Compute embeddings
        embeddings1 = self.model(**tokens1).last_hidden_state.mean(dim=1).detach().numpy()
        embeddings2 = self.model(**tokens2).last_hidden_state.mean(dim=1).detach().numpy()

        # Compute cosine similarity
        return cosine_similarity(embeddings1, embeddings2)[0][0]

    def hybrid_similarity(self, text1, text2, alpha=0.5):
        """
        Combines token-based and embedding-based similarities.

        Args:
            text1 (str): First text input.
            text2 (str): Second text input.
            alpha (float): Weighting factor for embedding-based similarity.

        Returns:
            float: Combined similarity score.
        """
        token_similarity = self.token_based_similarity(text1, text2)
        embedding_similarity = self.embedding_based_similarity(text1, text2)
        return alpha * embedding_similarity + (1 - alpha) * token_similarity

    def rank_similar_texts(self, base_text, text_list):
        """
        Ranks a list of texts by their similarity to the base text.

        Args:
            base_text (str): The text to compare against.
            text_list (list of str): List of texts to rank.

        Returns:
            list of tuple: Sorted list of (text, similarity score) in descending order.
        """
        similarities = [
            (text, self.embedding_based_similarity(base_text, text))
            for text in text_list
        ]
        return sorted(similarities, key=lambda x: x[1], reverse=True)


# Example usage
if __name__ == "__main__":
    ts = TextSimilarity()
    text_a = "AI is transforming the future."
    text_b = "Artificial Intelligence is shaping the future of technology."
    text_c = "AI and ML are the next big things."
    
    print("Token-based Similarity:", ts.token_based_similarity(text_a, text_b))
    print("Embedding-based Similarity:", ts.embedding_based_similarity(text_a, text_b))
    print("Transformer-based Similarity:", ts.transformer_based_similarity(text_a, text_b))
    print("Hybrid Similarity:", ts.hybrid_similarity(text_a, text_b))
    ranked_texts = ts.rank_similar_texts(text_a, [text_b, text_c])
    print("Ranked Texts by Similarity:", ranked_texts)
