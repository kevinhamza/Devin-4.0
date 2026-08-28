"""
Module: Data Cleaning Tools
Description: Provides advanced utilities for cleaning and preprocessing datasets.
Author: [Your Name or Team]
"""

import pandas as pd
import numpy as np
import re
import logging
from typing import List, Union

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCleaner:
    """
    A class to perform data cleaning tasks.
    """

    def __init__(self):
        logger.info("DataCleaner initialized.")

    def remove_null_values(self, dataframe: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
        """
        Removes rows with null values in specified columns.

        Args:
            dataframe (pd.DataFrame): The input dataframe.
            columns (List[str], optional): List of columns to check for nulls. Defaults to None, which means all columns.

        Returns:
            pd.DataFrame: Cleaned dataframe with rows containing nulls removed.
        """
        if columns is None:
            columns = dataframe.columns
        cleaned_df = dataframe.dropna(subset=columns)
        logger.info(f"Removed null values from columns: {columns}")
        return cleaned_df

    def standardize_column_names(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Standardizes column names by converting them to lowercase and replacing spaces with underscores.

        Args:
            dataframe (pd.DataFrame): The input dataframe.

        Returns:
            pd.DataFrame: Dataframe with standardized column names.
        """
        dataframe.columns = [re.sub(r'\s+', '_', col).lower() for col in dataframe.columns]
        logger.info("Standardized column names.")
        return dataframe

    def remove_duplicates(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Removes duplicate rows from the dataframe.

        Args:
            dataframe (pd.DataFrame): The input dataframe.

        Returns:
            pd.DataFrame: Dataframe with duplicate rows removed.
        """
        cleaned_df = dataframe.drop_duplicates()
        logger.info("Removed duplicate rows.")
        return cleaned_df

    def handle_outliers(self, dataframe: pd.DataFrame, column: str, method: str = 'IQR') -> pd.DataFrame:
        """
        Handles outliers in a specified column using the specified method.

        Args:
            dataframe (pd.DataFrame): The input dataframe.
            column (str): The column to process for outliers.
            method (str): The method to handle outliers ('IQR', 'Z-score'). Defaults to 'IQR'.

        Returns:
            pd.DataFrame: Dataframe with outliers handled.
        """
        if method == 'IQR':
            Q1 = dataframe[column].quantile(0.25)
            Q3 = dataframe[column].quantile(0.75)
            IQR = Q3 - Q1
            cleaned_df = dataframe[(dataframe[column] >= (Q1 - 1.5 * IQR)) & (dataframe[column] <= (Q3 + 1.5 * IQR))]
        elif method == 'Z-score':
            mean = dataframe[column].mean()
            std = dataframe[column].std()
            cleaned_df = dataframe[np.abs((dataframe[column] - mean) / std) <= 3]
        else:
            raise ValueError("Method must be 'IQR' or 'Z-score'.")
        logger.info(f"Handled outliers in column: {column} using {method} method.")
        return cleaned_df

    def fill_missing_values(self, dataframe: pd.DataFrame, column: str, strategy: str = 'mean') -> pd.DataFrame:
        """
        Fills missing values in a specified column using a chosen strategy.

        Args:
            dataframe (pd.DataFrame): The input dataframe.
            column (str): The column to process.
            strategy (str): The strategy to fill missing values ('mean', 'median', 'mode'). Defaults to 'mean'.

        Returns:
            pd.DataFrame: Dataframe with missing values filled.
        """
        if strategy == 'mean':
            fill_value = dataframe[column].mean()
        elif strategy == 'median':
            fill_value = dataframe[column].median()
        elif strategy == 'mode':
            fill_value = dataframe[column].mode()[0]
        else:
            raise ValueError("Strategy must be 'mean', 'median', or 'mode'.")
        dataframe[column] = dataframe[column].fillna(fill_value)
        logger.info(f"Filled missing values in column: {column} using {strategy} strategy.")
        return dataframe

# Example usage
if __name__ == "__main__":
    # Sample dataframe
    data = {'Name': ['Alice', 'Bob', None, 'David'],
            'Age': [25, 30, np.nan, 40],
            'Score': [90, None, 85, 88]}
    df = pd.DataFrame(data)

    cleaner = DataCleaner()
    df = cleaner.remove_null_values(df, ['Age'])
    df = cleaner.standardize_column_names(df)
    df = cleaner.remove_duplicates()
    df = cleaner.handle_outliers(df, 'Score', 'IQR')
    df = cleaner.fill_missing_values(df, 'Score', 'mean')

    print(df)
