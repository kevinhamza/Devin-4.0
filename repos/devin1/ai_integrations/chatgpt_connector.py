import os
import requests
from typing import Dict, Optional, List


class ChatGPTConnector:
    """
    A connector class to interact with the ChatGPT API for generating text responses, executing commands,
    and enabling conversational AI within the Devin framework.
    """

    def __init__(self, api_key: str, api_url: str = "https://api.openai.com/v1/chat/completions"):
        """
        Initializes the ChatGPT connector with the API key and endpoint.

        :param api_key: The API key to authenticate requests to the ChatGPT API.
        :param api_url: The API URL for interacting with the ChatGPT API (default is OpenAI's Chat Completion endpoint).
        """
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def send_message(self, messages: List[Dict[str, str]], max_tokens: int = 1500, temperature: float = 0.7) -> Optional[Dict]:
        """
        Sends a message to the ChatGPT API and returns the response.

        :param messages: A list of messages for the conversation context.
        :param max_tokens: Maximum tokens for the response.
        :param temperature: Sampling temperature for response creativity.
        :return: The API response as a dictionary, or None if the request fails.
        """
        payload = {
            "model": "gpt-4",  # Using GPT-4 model for better responses (could also choose other models if needed)
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()  # Return the parsed JSON response
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with ChatGPT API: {e}")
            return None  # Return None if the request fails

    def extract_response_text(self, api_response: Dict) -> Optional[str]:
        """
        Extracts the generated text from the ChatGPT API response.

        :param api_response: The raw response from the ChatGPT API.
        :return: The generated text or None if unavailable.
        """
        try:
            return api_response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            print(f"Error parsing API response: {e}")
            return None  # Return None if there is an error extracting the response

    def execute_task(self, prompt: str) -> Optional[str]:
        """
        Executes a specific task based on the given prompt.

        :param prompt: The task description or user query.
        :return: The response or execution result from ChatGPT.
        """
        # Create a conversation context, including a system message to define the assistant's role
        messages = [
            {"role": "system", "content": "You are a highly intelligent assistant."},
            {"role": "user", "content": prompt}
        ]

        response = self.send_message(messages)
        if response:
            return self.extract_response_text(response)  # Extract and return the generated text
        return None  # Return None if the response is empty or there was an error

# Example Usage
if __name__ == "__main__":
    # Retrieve API key from environment variables
    api_key = os.getenv("CHATGPT_API_KEY", "your_api_key_here")  # Replace with actual API key if not in .env
    connector = ChatGPTConnector(api_key)

    # Sample prompt for testing
    prompt = "Write a Python function to calculate the factorial of a number."
    result = connector.execute_task(prompt)

    if result:
        print("ChatGPT Response:")
        print(result)  # Output the result from ChatGPT
    else:
        print("Failed to fetch a response from ChatGPT.")
