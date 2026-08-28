"""
Other AI Modules
=================
Handles conversational and task execution through various third-party AI platforms.
This module serves as a generic interface for integration with other AI services beyond ChatGPT and Gimini.
"""

import requests
import logging
from modules.utils.nlp_tools import preprocess_text, analyze_sentiment
from modules.utils.ai_memory import MemoryManager

class OtherAIConfig:
    def __init__(self, api_details: dict, default_model="generic-ai", max_tokens=1500, temperature=0.7):
        """
        Configuration for connecting with multiple AI services.

        Args:
            api_details (dict): A dictionary containing platform-specific API URLs and keys.
            default_model (str): The default model to use.
            max_tokens (int): Maximum token count for responses.
            temperature (float): Response randomness parameter.
        """
        self.api_details = api_details
        self.default_model = default_model
        self.max_tokens = max_tokens
        self.temperature = temperature

class OtherAIModule:
    def __init__(self, config: OtherAIConfig):
        """
        Initializes the module with configurations for various AI platforms.

        Args:
            config (OtherAIConfig): Configuration object for the Other AI module.
        """
        self.api_details = config.api_details
        self.default_model = config.default_model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
        self.memory = MemoryManager()

    def _call_api(self, platform: str, prompt: str):
        """
        Makes a request to the specified AI platform.

        Args:
            platform (str): The AI platform to use.
            prompt (str): Input prompt for the API.

        Returns:
            str: AI-generated response from the platform.
        """
        if platform not in self.api_details:
            logging.error(f"Platform '{platform}' not configured.")
            return f"Error: Platform '{platform}' is not available."

        api_url = self.api_details[platform].get("url")
        api_key = self.api_details[platform].get("key")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.default_model,
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        try:
            logging.info(f"Sending request to {platform} API...")
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            ai_response = response.json().get("response", "").strip()
            logging.info(f"Response received from {platform} API.")
            return ai_response
        except requests.RequestException as e:
            logging.error(f"Error connecting to {platform} API: {e}")
            return f"Error: Unable to process the request through {platform}."

    def generate_response(self, user_input: str, platform: str, context: str = "") -> str:
        """
        Generates a conversational response based on user input for a specific AI platform.

        Args:
            user_input (str): User's input message.
            platform (str): AI platform to use for generating a response.
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
            response = self._call_api(platform, prompt)

            self.memory.save_ai_response(response)
            return response
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return f"An error occurred while generating a response from {platform}. Please try again."

# Example usage
if __name__ == "__main__":
    other_ai_config = OtherAIConfig(
        api_details={
            "thirdparty1": {"url": "https://api.thirdparty1.ai/converse", "key": "api_key_1"},
            "thirdparty2": {"url": "https://api.thirdparty2.ai/converse", "key": "api_key_2"}
        }
    )
    other_ai_module = OtherAIModule(other_ai_config)
    print(other_ai_module.generate_response("What's the weather like?", "thirdparty1"))
