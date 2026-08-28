"""
plugins/seo_optimizer.py

This module provides tools for optimizing web content for search engines, 
enhancing visibility and traffic.
"""

import re
from collections import Counter
from bs4 import BeautifulSoup
from typing import List, Dict

class SEOOptimizer:
    """Provides SEO optimization tools for web content."""

    def __init__(self):
        self.stop_words = {"the", "and", "is", "in", "to", "it", "of", "for", "on", "at", "a", "an"}

    def analyze_keywords(self, content: str) -> Dict[str, int]:
        """
        Analyzes and counts the frequency of keywords in the content.

        Args:
            content (str): The HTML or plain text content to analyze.

        Returns:
            Dict[str, int]: A dictionary of keywords and their frequency.
        """
        text = BeautifulSoup(content, "html.parser").get_text()
        words = re.findall(r'\b\w+\b', text.lower())
        filtered_words = [word for word in words if word not in self.stop_words]
        keyword_counts = Counter(filtered_words)
        return dict(keyword_counts.most_common(20))

    def check_meta_tags(self, content: str) -> Dict[str, str]:
        """
        Checks the meta tags in the HTML content for SEO best practices.

        Args:
            content (str): The HTML content to analyze.

        Returns:
            Dict[str, str]: A dictionary of meta tag analysis results.
        """
        soup = BeautifulSoup(content, "html.parser")
        meta_description = soup.find("meta", attrs={"name": "description"})
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})

        results = {
            "meta_description": meta_description["content"] if meta_description else "Missing",
            "meta_keywords": meta_keywords["content"] if meta_keywords else "Missing"
        }
        return results

    def suggest_improvements(self, content: str) -> List[str]:
        """
        Suggests improvements for SEO based on the content analysis.

        Args:
            content (str): The HTML content to analyze.

        Returns:
            List[str]: A list of suggestions for improving SEO.
        """
        suggestions = []
        keyword_analysis = self.analyze_keywords(content)

        if not keyword_analysis:
            suggestions.append("Add more keywords to the content.")
        if "meta_description" not in self.check_meta_tags(content):
            suggestions.append("Add a meta description tag for better search engine visibility.")
        if len(content) < 300:
            suggestions.append("Increase content length to at least 300 words.")
        
        return suggestions

    def optimize_html(self, content: str) -> str:
        """
        Optimizes HTML content for better SEO.

        Args:
            content (str): The HTML content to optimize.

        Returns:
            str: Optimized HTML content.
        """
        soup = BeautifulSoup(content, "html.parser")

        # Add missing meta description
        if not soup.find("meta", attrs={"name": "description"}):
            meta_tag = soup.new_tag("meta", name="description", content="Optimized description for SEO.")
            soup.head.insert(0, meta_tag)

        # Add missing meta keywords
        if not soup.find("meta", attrs={"name": "keywords"}):
            keywords_tag = soup.new_tag("meta", name="keywords", content="example, seo, optimization")
            soup.head.insert(1, keywords_tag)

        return str(soup)

# Example usage:
if __name__ == "__main__":
    sample_html = """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Welcome to SEO Optimization</h1>
        <p>This is an example of content to analyze and optimize for search engines.</p>
    </body>
    </html>
    """

    optimizer = SEOOptimizer()
    print("Keyword Analysis:", optimizer.analyze_keywords(sample_html))
    print("Meta Tag Check:", optimizer.check_meta_tags(sample_html))
    print("Suggestions:", optimizer.suggest_improvements(sample_html))
    print("Optimized HTML:", optimizer.optimize_html(sample_html))
