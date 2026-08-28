"""
otherai.py - Conversational AI Other AIs Module

This module integrates with other conversational AI systems to enhance functionality,
such as connecting to APIs of external AI services for diverse tasks and robust AI capabilities.
"""

import openai
import requests
import json
from typing import Dict, Any

class OtherAI:
    def __init__(self, api_configs: Dict[str, Dict[str, Any]]):
        """
        Initialize the OtherAI class with the configurations for external AI APIs.

        Args:
            api_configs (dict): A dictionary containing configurations for external AI APIs.
        """
        self.api_configs = api_configs

    def query_openai(self, prompt: str, max_tokens: int = 150) -> str:
        """
        Query the OpenAI API.

        Args:
            prompt (str): The text prompt to send to OpenAI.
            max_tokens (int): Maximum number of tokens for the response.

        Returns:
            str: The response from OpenAI.
        """
        api_key = self.api_configs.get('openai', {}).get('api_key')
        if not api_key:
            raise ValueError("OpenAI API key not provided in the configurations.")
        
        openai.api_key = api_key
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=max_tokens
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            return f"Error querying OpenAI: {str(e)}"

    def query_custom_ai(self, url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Any:
        """
        Query a custom AI system.

        Args:
            url (str): The endpoint URL of the custom AI system.
            payload (dict): The data payload for the request.
            headers (dict): Headers for the request.

        Returns:
            Any: The response from the custom AI system.
        """
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def use_external_ai(self, system_name: str, input_data: str) -> Any:
        """
        Interact with an external AI system by name.

        Args:
            system_name (str): The name of the external AI system to use.
            input_data (str): The input data for the AI system.

        Returns:
            Any: The response from the AI system.
        """
        system_config = self.api_configs.get(system_name)
        if not system_config:
            raise ValueError(f"Configuration for {system_name} not found.")
        
        url = system_config.get("url")
        headers = system_config.get("headers", {})
        payload = {
            "input": input_data,
            **system_config.get("additional_payload", {})
        }
        return self.query_custom_ai(url, payload, headers)

    def summarize_text(self, text: str, ai_system: str = "openai") -> str:
        """
        Summarize the given text using a specified AI system.

        Args:
            text (str): The text to summarize.
            ai_system (str): The AI system to use for summarization.

        Returns:
            str: The summarized text.
        """
        prompt = f"Summarize the following text: {text}"
        if ai_system == "openai":
            return self.query_openai(prompt)
        else:
            return self.use_external_ai(ai_system, prompt)

    def translate_text(self, text: str, target_language: str, ai_system: str = "openai") -> str:
        """
        Translate the given text to a target language using a specified AI system.

        Args:
            text (str): The text to translate.
            target_language (str): The target language for translation.
            ai_system (str): The AI system to use for translation.

        Returns:
            str: The translated text.
        """
        prompt = f"Translate the following text to {target_language}: {text}"
        if ai_system == "openai":
            return self.query_openai(prompt)
        else:
            return self.use_external_ai(ai_system, prompt)

# Example usage:
# api_configs = {
#     "openai": {"api_key": "your_openai_api_key"},
#     "custom_ai": {
#         "url": "https://custom-ai.example.com/api",
#         "headers": {"Authorization": "Bearer your_custom_token"},
#         "additional_payload": {"context": "general"}
#     }
# }
# other_ai = OtherAI(api_configs)
# print(other_ai.summarize_text("This is a long text that needs summarization."))
