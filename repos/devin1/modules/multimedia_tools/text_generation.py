"""
modules/multimedia_tools/text_generation.py

This module provides advanced text generation capabilities powered by state-of-the-art language models.
"""

import openai
from transformers import pipeline, GPT2LMHeadModel, GPT2Tokenizer
import os
from typing import Optional, Dict

class TextGeneration:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the TextGeneration module with support for OpenAI and Hugging Face models.

        Args:
            api_key (Optional[str]): API key for OpenAI GPT models. If not provided, defaults to environment variable.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.hugging_face_model = None
        self.hugging_face_tokenizer = None
        self.hugging_face_pipeline = None

    def configure_hugging_face_model(self, model_name: str = "gpt2"):
        """
        Configure a Hugging Face language model for text generation.

        Args:
            model_name (str): Name of the model from Hugging Face.
        """
        try:
            self.hugging_face_model = GPT2LMHeadModel.from_pretrained(model_name)
            self.hugging_face_tokenizer = GPT2Tokenizer.from_pretrained(model_name)
            self.hugging_face_pipeline = pipeline('text-generation', model=self.hugging_face_model, tokenizer=self.hugging_face_tokenizer)
            print(f"[INFO] Hugging Face model '{model_name}' configured successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to configure Hugging Face model: {e}")

    def generate_with_openai(self, prompt: str, max_tokens: int = 100, temperature: float = 0.7) -> str:
        """
        Generate text using OpenAI's GPT model.

        Args:
            prompt (str): Input prompt for text generation.
            max_tokens (int): Maximum number of tokens to generate.
            temperature (float): Sampling temperature. Higher values generate more random text.

        Returns:
            str: Generated text response.
        """
        if not self.api_key:
            return "[ERROR] OpenAI API key is missing."
        
        try:
            openai.api_key = self.api_key
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            return f"[ERROR] OpenAI generation failed: {e}"

    def generate_with_hugging_face(self, prompt: str, max_length: int = 100, temperature: float = 0.7) -> str:
        """
        Generate text using a Hugging Face model.

        Args:
            prompt (str): Input prompt for text generation.
            max_length (int): Maximum length of the generated sequence.
            temperature (float): Sampling temperature.

        Returns:
            str: Generated text response.
        """
        if not self.hugging_face_pipeline:
            return "[ERROR] Hugging Face model is not configured."

        try:
            outputs = self.hugging_face_pipeline(
                prompt,
                max_length=max_length,
                temperature=temperature,
                num_return_sequences=1
            )
            return outputs[0]['generated_text']
        except Exception as e:
            return f"[ERROR] Hugging Face generation failed: {e}"

    def generate_text(self, prompt: str, method: str = "openai", **kwargs) -> str:
        """
        Generate text using the specified method.

        Args:
            prompt (str): Input prompt for text generation.
            method (str): Generation method, either 'openai' or 'hugging_face'.
            **kwargs: Additional parameters for the generation method.

        Returns:
            str: Generated text response.
        """
        if method == "openai":
            return self.generate_with_openai(prompt, **kwargs)
        elif method == "hugging_face":
            return self.generate_with_hugging_face(prompt, **kwargs)
        else:
            return "[ERROR] Invalid generation method. Choose 'openai' or 'hugging_face'."

# Example usage
if __name__ == "__main__":
    text_gen = TextGeneration(api_key="your_openai_api_key_here")
    text_gen.configure_hugging_face_model()

    # OpenAI Example
    print("OpenAI Generated Text:")
    print(text_gen.generate_text("Write a story about an AI revolution.", method="openai", max_tokens=150, temperature=0.8))

    # Hugging Face Example
    print("\nHugging Face Generated Text:")
    print(text_gen.generate_text("Write a story about an AI revolution.", method="hugging_face", max_length=150, temperature=0.8))
