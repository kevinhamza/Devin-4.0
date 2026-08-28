"""
ai_integrations/gemini_connector.py
-----------------------------------
This module provides integration with the Gemini AI platform, enabling
Devin to leverage Gemini's advanced AI capabilities for task execution
and automation.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeminiConnector:
    """
    A class to interface with the Gemini AI platform.
    """

    def __init__(self):
        self.base_url = os.getenv("GEMINI_BASE_URL", "https://api.gemini.ai/v1")
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError("Gemini API Key is missing. Set GEMINI_API_KEY in your .env file.")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def send_prompt(self, prompt: str, model: str = "default", max_tokens: int = 512) -> dict:
        """
        Sends a prompt to Gemini AI and retrieves the response.
        
        :param prompt: The input prompt for Gemini AI.
        :param model: The Gemini AI model to use (e.g., "default", "advanced").
        :param max_tokens: Maximum number of tokens in the response.
        :return: The response from Gemini AI as a dictionary.
        """
        url = f"{self.base_url}/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
        }

        response = self.session.post(url, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Gemini API Error: {response.status_code} - {response.text}")

        return response.json()

    def execute_task(self, task_name: str, parameters: dict) -> dict:
        """
        Executes a predefined task on Gemini AI.
        
        :param task_name: The name of the task to execute.
        :param parameters: A dictionary of parameters for the task.
        :return: The result of the task execution.
        """
        url = f"{self.base_url}/tasks/execute"
        payload = {
            "task_name": task_name,
            "parameters": parameters,
        }

        response = self.session.post(url, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Gemini API Task Error: {response.status_code} - {response.text}")

        return response.json()

    def fetch_available_models(self) -> list:
        """
        Fetches the list of available models from Gemini AI.
        
        :return: A list of available models.
        """
        url = f"{self.base_url}/models"
        response = self.session.get(url)
        if response.status_code != 200:
            raise RuntimeError(f"Gemini API Model Error: {response.status_code} - {response.text}")

        return response.json().get("models", [])

    def health_check(self) -> bool:
        """
        Checks if the Gemini API is reachable.
        
        :return: True if the API is reachable, False otherwise.
        """
        url = f"{self.base_url}/health"
        try:
            response = self.session.get(url)
            return response.status_code == 200
        except requests.RequestException:
            return False


if __name__ == "__main__":
    # Example usage
    try:
        connector = GeminiConnector()
        
        print("Gemini Health Check:", "Online" if connector.health_check() else "Offline")

        models = connector.fetch_available_models()
        print(f"Available Models: {models}")

        prompt = "What is the capital of France?"
        response = connector.send_prompt(prompt)
        print("Response from Gemini:", response)

        task_result = connector.execute_task("translate", {"text": "Hello, world!", "target_language": "es"})
        print("Task Execution Result:", task_result)

    except Exception as e:
        print(f"Error: {e}")
