"""
modules/ai_tools/chatgpt.py
---------------------------
Conversational AI ChatGPT module for handling sophisticated natural language
interactions and generating context-aware responses.
"""

import openai
import logging
from typing import Dict, Any, Optional

class ChatGPT:
    """
    A class for interacting with the OpenAI ChatGPT API for conversational tasks.
    """

    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initializes the ChatGPT class with the OpenAI API key and model.

        Args:
            api_key (str): OpenAI API key.
            model (str): The model to use (default is "gpt-4").
        """
        self.api_key = api_key
        self.model = model
        openai.api_key = self.api_key
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger("ChatGPT")

    def generate_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0
    ) -> Optional[str]:
        """
        Generates a response from ChatGPT.

        Args:
            prompt (str): The input prompt for the model.
            temperature (float): Controls randomness of the response (default: 0.7).
            max_tokens (int): Maximum tokens in the response (default: 1000).
            top_p (float): Nucleus sampling parameter (default: 1.0).
            frequency_penalty (float): Penalizes new tokens based on frequency (default: 0.0).
            presence_penalty (float): Penalizes tokens based on presence in the prompt (default: 0.0).

        Returns:
            str: The generated response from ChatGPT.
        """
        self.logger.debug("Generating response from ChatGPT.")
        self.logger.debug(f"Prompt: {prompt}")
        self.logger.debug(f"Parameters: temperature={temperature}, max_tokens={max_tokens}, top_p={top_p}, frequency_penalty={frequency_penalty}, presence_penalty={presence_penalty}")

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a highly capable assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
            message = response['choices'][0]['message']['content']
            self.logger.debug(f"Response: {message}")
            return message
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return None

    def analyze_response(self, response: str) -> Dict[str, Any]:
        """
        Analyzes the response for specific information or sentiments.

        Args:
            response (str): The generated response to analyze.

        Returns:
            dict: Analysis results such as sentiment or key topics.
        """
        self.logger.debug(f"Analyzing response: {response}")
        # Placeholder for more advanced analysis (e.g., sentiment analysis, keyword extraction).
        analysis = {
            "length": len(response),
            "words": len(response.split()),
            "keywords": [word for word in response.split() if len(word) > 5]
        }
        self.logger.debug(f"Analysis: {analysis}")
        return analysis

    def summarize_text(self, text: str, summary_prompt: str = "Summarize the following text:") -> Optional[str]:
        """
        Summarizes the given text using ChatGPT.

        Args:
            text (str): The text to summarize.
            summary_prompt (str): Custom summary prompt (default: generic summary).

        Returns:
            str: Summarized text.
        """
        full_prompt = f"{summary_prompt}\n\n{text}"
        self.logger.debug(f"Summarizing text with prompt: {full_prompt}")
        return self.generate_response(full_prompt)

# Example usage:
if __name__ == "__main__":
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    chatbot = ChatGPT(api_key)
    user_input = "Explain the concept of artificial intelligence."
    response = chatbot.generate_response(user_input)
    print("ChatGPT Response:", response)
