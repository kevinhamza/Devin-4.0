"""
modules/multimedia_tools/text_similarity.py
-------------------------------------------
This module provides advanced text similarity capabilities using natural language processing (NLP).
It supports similarity scoring between two or multiple texts and advanced semantic matching using pre-trained models.
"""

from typing import List, Dict, Union
from transformers import AutoTokenizer, AutoModel
import torch


class TextSimilarity:
    """
    A class for calculating text similarity using pre-trained transformer models.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the TextSimilarity module.

        :param model_name: The name of the pre-trained model to use for embedding generation.
        """
        self.model_name = model_name
        self.tokenizer, self.model = self.load_model()

    def load_model(self):
        """
        Load the pre-trained model and tokenizer.

        :return: A tuple containing the tokenizer and model.
        """
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model = AutoModel.from_pretrained(self.model_name)
        return tokenizer, model

    def encode_text(self, text: str) -> torch.Tensor:
        """
        Generate embeddings for a single text input.

        :param text: The input text to encode.
        :return: A tensor representation of the text embedding.
        """
        if not text.strip():
            raise ValueError("Input text is empty or whitespace only.")

        encoded = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            embeddings = self.model(**encoded).last_hidden_state.mean(dim=1)
        return embeddings

    def cosine_similarity(self, tensor1: torch.Tensor, tensor2: torch.Tensor) -> float:
        """
        Calculate cosine similarity between two tensors.

        :param tensor1: The first text embedding.
        :param tensor2: The second text embedding.
        :return: A similarity score as a float.
        """
        return torch.nn.functional.cosine_similarity(tensor1, tensor2).item()

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute the similarity between two pieces of text.

        :param text1: The first text input.
        :param text2: The second text input.
        :return: A similarity score as a float.
        """
        embedding1 = self.encode_text(text1)
        embedding2 = self.encode_text(text2)
        return self.cosine_similarity(embedding1, embedding2)

    def batch_similarity(self, texts: List[str]) -> List[Dict[str, Union[str, float]]]:
        """
        Calculate pairwise similarity scores for a list of texts.

        :param texts: A list of text inputs.
        :return: A list of dictionaries containing pairwise text combinations and their similarity scores.
        """
        if len(texts) < 2:
            raise ValueError("At least two texts are required for batch similarity calculation.")

        results = []
        for i, text1 in enumerate(texts):
            for j, text2 in enumerate(texts):
                if i < j:
                    similarity_score = self.compute_similarity(text1, text2)
                    results.append({
                        "text1": text1,
                        "text2": text2,
                        "similarity_score": similarity_score
                    })
        return results


# Example usage
if __name__ == "__main__":
    # Initialize the TextSimilarity class
    text_similarity = TextSimilarity()

    # Example of similarity between two texts
    text_a = "Artificial Intelligence is revolutionizing the world."
    text_b = "The advancements in AI are transforming industries."

    try:
        similarity_score = text_similarity.compute_similarity(text_a, text_b)
        print("Text Similarity:")
        print(f"Text 1: {text_a}")
        print(f"Text 2: {text_b}")
        print(f"Similarity Score: {similarity_score}")
    except ValueError as e:
        print(f"Error: {e}")

    # Example of batch similarity
    text_list = [
        "AI is shaping the future.",
        "Machine learning is a subset of AI.",
        "Deep learning models are achieving state-of-the-art performance."
    ]

    try:
        batch_results = text_similarity.batch_similarity(text_list)
        print("\nBatch Text Similarity:")
        for result in batch_results:
            print(f"Text 1: {result['text1']}")
            print(f"Text 2: {result['text2']}")
            print(f"Similarity Score: {result['similarity_score']}")
    except ValueError as e:
        print(f"Error: {e}")
