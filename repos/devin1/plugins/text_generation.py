"""
File: plugins/text_generation.py
Description: Text generation capabilities for various contexts using AI models.
"""

import openai
from typing import List, Dict, Optional

class TextGeneration:
    """
    A class to handle AI-driven text generation for various applications.
    """

    def __init__(self, api_key: str):
        """
        Initialize the TextGeneration module with an API key.
        """
        self.api_key = api_key
        openai.api_key = self.api_key

    def generate_text(
        self, 
        prompt: str, 
        model: str = "gpt-4", 
        max_tokens: int = 150, 
        temperature: float = 0.7,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0
    ) -> str:
        """
        Generate text based on a given prompt.

        :param prompt: The input text prompt.
        :param model: The model to use (e.g., gpt-4, gpt-3.5-turbo).
        :param max_tokens: Maximum number of tokens in the generated text.
        :param temperature: Controls randomness in generation.
        :param top_p: Controls diversity via nucleus sampling.
        :param frequency_penalty: Penalizes frequent token repetition.
        :param presence_penalty: Penalizes tokens already present in the text.
        :return: Generated text as a string.
        """
        try:
            response = openai.Completion.create(
                engine=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return f"Error in text generation: {e}"

    def batch_generate_texts(
        self, 
        prompts: List[str], 
        model: str = "gpt-4", 
        max_tokens: int = 150, 
        temperature: float = 0.7
    ) -> List[str]:
        """
        Generate text for a batch of prompts.

        :param prompts: List of input text prompts.
        :param model: The model to use for text generation.
        :param max_tokens: Maximum number of tokens for each generation.
        :param temperature: Controls randomness in generation.
        :return: List of generated text results.
        """
        results = []
        for prompt in prompts:
            result = self.generate_text(prompt, model=model, max_tokens=max_tokens, temperature=temperature)
            results.append(result)
        return results

    def refine_text(
        self, 
        input_text: str, 
        instructions: str, 
        model: str = "gpt-4", 
        max_tokens: int = 200
    ) -> str:
        """
        Refine or rewrite text based on user instructions.

        :param input_text: The text to refine or rewrite.
        :param instructions: Instructions on how to modify the text.
        :param model: The model to use for text generation.
        :param max_tokens: Maximum number of tokens for the refinement.
        :return: Refined text as a string.
        """
        prompt = f"Refine the following text based on these instructions:\n\n{instructions}\n\nText:\n{input_text}\n\nRefined Text:"
        return self.generate_text(prompt, model=model, max_tokens=max_tokens)

# Example usage
if __name__ == "__main__":
    api_key = "your_openai_api_key"
    text_gen = TextGeneration(api_key)

    # Single text generation
    print(text_gen.generate_text(prompt="Write a poem about AI."))

    # Batch text generation
    prompts = ["Describe the future of technology.", "Explain quantum computing in simple terms."]
    print(text_gen.batch_generate_texts(prompts))

    # Refining text
    input_text = "The cat sat on the mat."
    instructions = "Make it more dramatic and poetic."
    print(text_gen.refine_text(input_text, instructions))
