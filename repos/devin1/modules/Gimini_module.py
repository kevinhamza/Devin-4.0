"""
Gimini Module
=============
This module handles conversational AI interactions through the Gimini platform for the Devin project.
"""

import requests
import logging
from modules.utils.nlp_tools import preprocess_text, analyze_sentiment
from modules.utils.ai_memory import MemoryManager

class GiminiConfig:
    def __init__(self, api_url, api_key, model="gimini-v1", max_tokens=1500, temperature=0.7):
        """
        Configuration for the Gimini module.

        Args:
            api_url (str): Base URL for the Gimini API.
            api_key (str): API key for authentication.
            model (str): Model name to be used.
            max_tokens (int): Maximum token count for responses.
            temperature (float): Response randomness parameter.
        """
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

class GiminiModule:
    def __init__(self, config: GiminiConfig):
        """
        Initializes the Gimini module with configuration.

        Args:
            config (GiminiConfig): Configuration object for the Gimini module.
        """
        self.api_url = config.api_url
        self.api_key = config.api_key
        self.model = config.model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
        self.memory = MemoryManager()

    def _call_gimini_api(self, prompt: str):
        """
        Makes a request to the Gimini API.

        Args:
            prompt (str): Input prompt for the API.

        Returns:
            str: AI-generated response from Gimini.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        try:
            logging.info("Sending request to Gimini API...")
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            ai_response = response.json().get("response", "").strip()
            logging.info("Response received from Gimini API.")
            return ai_response
        except requests.RequestException as e:
            logging.error(f"Error connecting to Gimini API: {e}")
            return "Error: Unable to process the request."

    def generate_response(self, user_input: str, context: str = "") -> str:
        """
        Generates a conversational response based on user input.

        Args:
            user_input (str): User's input message.
            context (str): Optional conversation context.

        Returns:
            str: AI-generated response.
        """
        try:
            logging.info("Preprocessing user input...")
            processed_input = preprocess_text(user_input)
            sentiment = analyze_sentiment(processed_input)
            self.memory.save_user_input(processed_input)

            prompt = f"Context: {context}\nUser: {processed_input}\nAI:"
            response = self._call_gimini_api(prompt)

            self.memory.save_ai_response(response)
            return response
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return "An error occurred while generating a response. Please try again."

# Example usage
if __name__ == "__main__":
    gimini_config = GiminiConfig(
        api_url="https://api.gimini.ai/converse",
        api_key="your_api_key_here"
    )
    gimini_module = GiminiModule(gimini_config)
    print(gimini_module.generate_response("Tell me about the Devin project."))
