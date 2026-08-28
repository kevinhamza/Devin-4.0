"""
recommendations.py
-------------------
Implements intelligent recommendation engines for personalized suggestions.
Supports collaborative filtering, content-based filtering, and hybrid approaches.
"""

import os
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

class RecommendationEngine:
    """
    A class to build and provide recommendations using various algorithms.
    """

    def __init__(self, data_path=None):
        """
        Initialize the recommendation engine with optional dataset.

        Args:
            data_path (str): Path to the dataset for recommendations.
        """
        self.data_path = data_path
        self.data = None
        self.similarity_matrix = None

        if self.data_path:
            self.load_data(self.data_path)

    def load_data(self, file_path):
        """
        Load dataset for recommendations.

        Args:
            file_path (str): Path to the dataset.

        Returns:
            pandas.DataFrame: Loaded dataset.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset not found: {file_path}")
        self.data = pd.read_csv(file_path)
        print("Dataset loaded successfully.")

    def compute_similarity(self, method="cosine"):
        """
        Compute similarity matrix using specified method.

        Args:
            method (str): Similarity computation method ("cosine" or "correlation").

        Returns:
            numpy.ndarray: Similarity matrix.
        """
        if self.data is None:
            raise ValueError("No data loaded. Load data before computing similarity.")

        data_matrix = self.data.drop(columns=["user_id"]).values

        if method == "cosine":
            self.similarity_matrix = cosine_similarity(data_matrix)
        elif method == "correlation":
            self.similarity_matrix = np.corrcoef(data_matrix)
        else:
            raise ValueError("Unsupported similarity method. Use 'cosine' or 'correlation'.")
        print(f"Similarity matrix computed using {method} method.")
        return self.similarity_matrix

    def recommend_collaborative(self, user_id, top_n=5):
        """
        Generate collaborative filtering recommendations.

        Args:
            user_id (int): ID of the user to generate recommendations for.
            top_n (int): Number of recommendations to return.

        Returns:
            list: Recommended items.
        """
        if self.similarity_matrix is None:
            raise ValueError("Compute similarity matrix before making recommendations.")

        user_index = self.data[self.data["user_id"] == user_id].index[0]
        similarity_scores = self.similarity_matrix[user_index]
        similar_users = np.argsort(-similarity_scores)[1:top_n+1]
        recommendations = []

        for sim_user in similar_users:
            user_data = self.data.iloc[sim_user]
            recommended_items = user_data[user_data > 0].index.tolist()
            recommendations.extend(recommended_items)

        return list(set(recommendations))

    def recommend_content_based(self, item_features, top_n=5):
        """
        Generate content-based recommendations based on item features.

        Args:
            item_features (numpy.ndarray): Features of the item to compare.
            top_n (int): Number of recommendations to return.

        Returns:
            list: Recommended items.
        """
        if self.data is None:
            raise ValueError("No data loaded. Load data before making recommendations.")

        item_matrix = self.data.drop(columns=["user_id"]).values
        similarities = cosine_similarity(item_features.reshape(1, -1), item_matrix)[0]
        top_indices = np.argsort(-similarities)[:top_n]
        return self.data.iloc[top_indices]["user_id"].tolist()

    def hybrid_recommendation(self, user_id, item_features, weight=0.5, top_n=5):
        """
        Generate hybrid recommendations combining collaborative and content-based filtering.

        Args:
            user_id (int): ID of the user to generate recommendations for.
            item_features (numpy.ndarray): Features of the item to compare.
            weight (float): Weight for combining collaborative and content-based scores.
            top_n (int): Number of recommendations to return.

        Returns:
            list: Recommended items.
        """
        collaborative_recs = self.recommend_collaborative(user_id, top_n)
        content_recs = self.recommend_content_based(item_features, top_n)
        hybrid_scores = {}

        for rec in collaborative_recs:
            hybrid_scores[rec] = hybrid_scores.get(rec, 0) + weight

        for rec in content_recs:
            hybrid_scores[rec] = hybrid_scores.get(rec, 0) + (1 - weight)

        sorted_recs = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        return [rec[0] for rec in sorted_recs[:top_n]]

    def list_available_users(self):
        """
        List all user IDs in the dataset.

        Returns:
            list: User IDs.
        """
        if self.data is None:
            raise ValueError("No data loaded. Load data to list users.")
        return self.data["user_id"].unique().tolist()

# Example usage
if __name__ == "__main__":
    engine = RecommendationEngine(data_path="user_data.csv")
    
    # Compute similarity
    engine.compute_similarity(method="cosine")
    
    # Generate collaborative recommendations
    user_recommendations = engine.recommend_collaborative(user_id=1, top_n=5)
    print("Collaborative Recommendations:", user_recommendations)

    # Generate content-based recommendations
    sample_item_features = np.random.rand(engine.data.shape[1] - 1)  # Example item features
    content_recommendations = engine.recommend_content_based(sample_item_features, top_n=5)
    print("Content-Based Recommendations:", content_recommendations)

    # Hybrid recommendations
    hybrid_recs = engine.hybrid_recommendation(user_id=1, item_features=sample_item_features, weight=0.7, top_n=5)
    print("Hybrid Recommendations:", hybrid_recs)
