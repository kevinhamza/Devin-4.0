"""
plugins/chatgpt_integration.py

Integrates OpenAI ChatGPT for conversational capabilities.
"""

import openai
import os
from typing import Any, Dict, Optional

class ChatGPTIntegration:
    """
    A class for integrating ChatGPT into the Devin project.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it in the environment variables or pass it directly.")
        openai.api_key = self.api_key

    def chat(self, prompt: str, model: str = "gpt-4", temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """
        Interacts with the ChatGPT API to get a response based on the provided prompt.

        Args:
            prompt (str): The input prompt for ChatGPT.
            model (str): The model version to use. Default is 'gpt-4'.
            temperature (float): Controls randomness. Lower values make output more deterministic.
            max_tokens (int): The maximum number of tokens to generate.

        Returns:
            str: The response from ChatGPT.
        """
        try:
            response = openai.Completion.create(
                engine=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            return f"Error: {e}"

    def generate_code(self, description: str, model: str = "gpt-4-codex") -> str:
        """
        Generates code snippets based on the provided description.

        Args:
            description (str): A natural language description of the code.
            model (str): The model version for code generation.

        Returns:
            str: The generated code.
        """
        prompt = f"Write a code snippet for the following task:\n\n{description}"
        return self.chat(prompt, model=model, temperature=0)

    def summarize_conversation(self, conversation: str, model: str = "gpt-4") -> str:
        """
        Summarizes a conversation using ChatGPT.

        Args:
            conversation (str): The conversation text to summarize.
            model (str): The model version to use for summarization.

        Returns:
            str: A summary of the conversation.
        """
        prompt = f"Summarize the following conversation:\n\n{conversation}"
        return self.chat(prompt, model=model)

    def translate_text(self, text: str, target_language: str, model: str = "gpt-4") -> str:
        """
        Translates the given text into the specified target language.

        Args:
            text (str): The text to translate.
            target_language (str): The language to translate into.

        Returns:
            str: The translated text.
        """
        prompt = f"Translate the following text to {target_language}:\n\n{text}"
        return self.chat(prompt, model=model)

# Example usage
if __name__ == "__main__":
    api_key = "your-openai-api-key"
    chatgpt = ChatGPTIntegration(api_key)
    
    prompt = "What is the impact of AI on the job market?"
    response = chatgpt.chat(prompt)
    print(f"ChatGPT Response: {response}")

    code_description = "Create a Python function to calculate factorial using recursion."
    code = chatgpt.generate_code(code_description)
    print(f"Generated Code:\n{code}")
