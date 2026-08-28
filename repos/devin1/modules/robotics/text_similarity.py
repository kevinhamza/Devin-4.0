"""
Text Similarity Module for Robotics
Provides functionality to compute similarity between two pieces of text using advanced NLP models.
"""

from typing import Tuple, List
from transformers import AutoTokenizer, AutoModel
import torch


class TextSimilarity:
    """
    Computes similarity between texts using a pretrained transformer-based model.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the text similarity model.

        Args:
            model_name (str): The name of the pretrained similarity model to use.
        """
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute the similarity score between two pieces of text.

        Args:
            text1 (str): The first text.
            text2 (str): The second text.

        Returns:
            float: A similarity score between 0 and 1.
        """
        if not text1.strip() or not text2.strip():
            raise ValueError("Both texts must be non-empty.")

        # Encode texts
        encoded_texts = self.tokenizer([text1, text2], padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            embeddings = self.model(**encoded_texts).last_hidden_state.mean(dim=1)

        # Compute cosine similarity
        similarity = self._cosine_similarity(embeddings[0], embeddings[1])
        return similarity

    def batch_compute_similarity(self, text_pairs: List[Tuple[str, str]]) -> List[float]:
        """
        Compute similarity scores for a batch of text pairs.

        Args:
            text_pairs (List[Tuple[str, str]]): A list of text pairs.

        Returns:
            List[float]: A list of similarity scores for each pair.
        """
        results = []
        for text1, text2 in text_pairs:
            try:
                results.append(self.compute_similarity(text1, text2))
            except ValueError as e:
                results.append(f"Error: {str(e)}")
        return results

    @staticmethod
    def _cosine_similarity(embedding1: torch.Tensor, embedding2: torch.Tensor) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            embedding1 (torch.Tensor): The first embedding vector.
            embedding2 (torch.Tensor): The second embedding vector.

        Returns:
            float: The cosine similarity score.
        """
        return torch.nn.functional.cosine_similarity(embedding1.unsqueeze(0), embedding2.unsqueeze(0)).item()


# Example Usage
if __name__ == "__main__":
    similarity_tool = TextSimilarity()

    # Single similarity computation
    text_a = "Robots are revolutionizing industries."
    text_b = "Automation through robotics is changing the world."
    print("Single Pair Similarity:")
    print(similarity_tool.compute_similarity(text_a, text_b))

    # Batch similarity computation
    text_pairs = [
        ("Machine learning is amazing.", "Artificial intelligence is fascinating."),
        ("The weather is great today.", "I love sunny days."),
        ("The robot is working perfectly.", "The machine is malfunctioning."),
    ]
    print("\nBatch Similarity Computation:")
    print(similarity_tool.batch_compute_similarity(text_pairs))
