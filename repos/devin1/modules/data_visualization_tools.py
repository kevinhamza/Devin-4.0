"""
modules/data_visualization_tools.py

Advanced visualization techniques for data analysis and presentation.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

class DataVisualizationTools:
    """
    Provides advanced visualization techniques for data analysis and presentation.
    """

    def __init__(self):
        """
        Initialize the visualization tools with default settings.
        """
        sns.set(style="whitegrid")

    def plot_line_chart(self, data, x_col, y_col, title=None, xlabel=None, ylabel=None):
        """
        Creates a line chart.
        """
        plt.figure(figsize=(10, 6))
        plt.plot(data[x_col], data[y_col], marker='o')
        plt.title(title or "Line Chart")
        plt.xlabel(xlabel or x_col)
        plt.ylabel(ylabel or y_col)
        plt.grid(True)
        plt.show()

    def plot_bar_chart(self, data, x_col, y_col, title=None, xlabel=None, ylabel=None):
        """
        Creates a bar chart.
        """
        plt.figure(figsize=(10, 6))
        sns.barplot(x=x_col, y=y_col, data=data)
        plt.title(title or "Bar Chart")
        plt.xlabel(xlabel or x_col)
        plt.ylabel(ylabel or y_col)
        plt.show()

    def plot_scatter(self, data, x_col, y_col, hue=None, title=None):
        """
        Creates a scatter plot.
        """
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=x_col, y=y_col, hue=hue, data=data)
        plt.title(title or "Scatter Plot")
        plt.show()

    def plot_correlation_matrix(self, data, title=None):
        """
        Visualizes the correlation matrix.
        """
        corr = data.corr()
        plt.figure(figsize=(12, 8))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", cbar=True)
        plt.title(title or "Correlation Matrix")
        plt.show()

    def plot_histogram(self, data, column, bins=20, title=None, xlabel=None):
        """
        Creates a histogram.
        """
        plt.figure(figsize=(10, 6))
        sns.histplot(data[column], bins=bins, kde=True, color='blue')
        plt.title(title or f"Histogram of {column}")
        plt.xlabel(xlabel or column)
        plt.show()

    def plot_pie_chart(self, labels, sizes, title=None):
        """
        Creates a pie chart.
        """
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.title(title or "Pie Chart")
        plt.axis('equal')
        plt.show()

    def save_plot(self, fig, filename):
        """
        Saves the current plot to a file.
        """
        fig.savefig(filename, dpi=300)
        print(f"Plot saved as {filename}")

if __name__ == "__main__":
    # Example usage
    visualizer = DataVisualizationTools()

    # Dummy data for demonstration
    df = pd.DataFrame({
        'Category': ['A', 'B', 'C', 'D'],
        'Values': [23, 45, 56, 78]
    })

    visualizer.plot_bar_chart(df, 'Category', 'Values', title="Example Bar Chart")
