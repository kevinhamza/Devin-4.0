"""
AI Integration: GitHub Copilot Connector
Description: This module integrates the Devin project with GitHub Copilot API for advanced code generation and suggestions.
"""

import os
import requests
from typing import Dict, Optional, List

class CopilotConnector:
    """
    A connector class to interact with GitHub Copilot API for generating code suggestions, completing tasks,
    and assisting in software development workflows within the Devin framework.
    """

    def __init__(self, api_key: str, api_url: str = "https://api.github.com/copilot/v1/completions"):
        """
        Initializes the GitHub Copilot connector with the API key and endpoint.
        """
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def send_request(self, prompt: str, max_tokens: int = 100, temperature: float = 0.7) -> Optional[Dict]:
        """
        Sends a code generation request to the GitHub Copilot API and returns the response.

        :param prompt: The code or task description.
        :param max_tokens: Maximum tokens for the response.
        :param temperature: Sampling temperature for result variety.
        :return: The API response as a dictionary.
        """
        payload = {
            "model": "copilot-codex",
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with GitHub Copilot API: {e}")
            return None

    def extract_code_snippet(self, api_response: Dict) -> Optional[str]:
        """
        Extracts the generated code snippet from the API response.

        :param api_response: The raw response from the GitHub Copilot API.
        :return: The code snippet or None if unavailable.
        """
        try:
            return api_response["choices"][0]["text"]
        except (KeyError, IndexError):
            print("Error parsing API response.")
            return None

    def generate_code(self, task_description: str) -> Optional[str]:
        """
        Generates a code snippet based on the given task description.

        :param task_description: The task description or code snippet.
        :return: The generated code or suggestion.
        """
        response = self.send_request(task_description)
        if response:
            return self.extract_code_snippet(response)
        return None

# Example Usage
if __name__ == "__main__":
    # Set API key
    api_key = os.getenv("COPILOT_API_KEY", "your_api_key_here")
    copilot = CopilotConnector(api_key)

    # Example task
    task_description = "Write a Python function to calculate the Fibonacci sequence."
    code = copilot.generate_code(task_description)

    if code:
        print("Generated Code:")
        print(code)
    else:
        print("Failed to fetch code suggestion from Copilot.")
