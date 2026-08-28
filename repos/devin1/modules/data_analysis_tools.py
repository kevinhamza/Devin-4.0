"""
modules/data_analysis_tools.py
==============================
Provides tools for data analysis, including statistical computations, data visualization,
and large dataset handling.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

class DataAnalysisTools:
    """
    A comprehensive suite for data analysis, visualization, and modeling.
    """
    
    @staticmethod
    def load_dataset(file_path, file_type='csv'):
        """
        Loads a dataset from a file.

        :param file_path: Path to the dataset.
        :param file_type: File type ('csv', 'excel', 'json').
        :return: DataFrame object.
        """
        try:
            if file_type == 'csv':
                return pd.read_csv(file_path)
            elif file_type == 'excel':
                return pd.read_excel(file_path)
            elif file_type == 'json':
                return pd.read_json(file_path)
            else:
                raise ValueError("Unsupported file type. Use 'csv', 'excel', or 'json'.")
        except Exception as e:
            raise Exception(f"Error loading dataset: {e}")
    
    @staticmethod
    def describe_data(dataframe):
        """
        Provides a statistical summary of the dataset.

        :param dataframe: DataFrame object.
        :return: Summary statistics.
        """
        try:
            return dataframe.describe(include='all')
        except Exception as e:
            raise Exception(f"Error describing data: {e}")
    
    @staticmethod
    def visualize_distribution(dataframe, column):
        """
        Visualizes the distribution of a specific column.

        :param dataframe: DataFrame object.
        :param column: Column name to visualize.
        """
        try:
            plt.figure(figsize=(10, 6))
            sns.histplot(dataframe[column], kde=True, color='blue')
            plt.title(f"Distribution of {column}")
            plt.xlabel(column)
            plt.ylabel("Frequency")
            plt.show()
        except Exception as e:
            raise Exception(f"Error visualizing distribution: {e}")
    
    @staticmethod
    def perform_pca(dataframe, n_components=2):
        """
        Performs Principal Component Analysis (PCA) on the dataset.

        :param dataframe: DataFrame object.
        :param n_components: Number of principal components.
        :return: Transformed dataset.
        """
        try:
            pca = PCA(n_components=n_components)
            scaled_data = (dataframe - dataframe.mean()) / dataframe.std()
            return pca.fit_transform(scaled_data.dropna(axis=1))
        except Exception as e:
            raise Exception(f"Error performing PCA: {e}")
    
    @staticmethod
    def cluster_data(dataframe, n_clusters=3):
        """
        Performs clustering on the dataset.

        :param dataframe: DataFrame object.
        :param n_clusters: Number of clusters.
        :return: Cluster labels.
        """
        try:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            return kmeans.fit_predict(dataframe.dropna(axis=1))
        except Exception as e:
            raise Exception(f"Error clustering data: {e}")
    
    @staticmethod
    def visualize_correlation_matrix(dataframe):
        """
        Visualizes the correlation matrix of the dataset.

        :param dataframe: DataFrame object.
        """
        try:
            plt.figure(figsize=(12, 8))
            sns.heatmap(dataframe.corr(), annot=True, cmap="coolwarm")
            plt.title("Correlation Matrix")
            plt.show()
        except Exception as e:
            raise Exception(f"Error visualizing correlation matrix: {e}")
    
    @staticmethod
    def detect_outliers(dataframe, column):
        """
        Detects outliers in a specific column using Z-scores.

        :param dataframe: DataFrame object.
        :param column: Column name to check for outliers.
        :return: DataFrame with outlier rows.
        """
        try:
            z_scores = np.abs(stats.zscore(dataframe[column]))
            return dataframe[z_scores > 3]
        except Exception as e:
            raise Exception(f"Error detecting outliers: {e}")
