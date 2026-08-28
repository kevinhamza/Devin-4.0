"""
AI Composer Plugin
-------------------
This module focuses on generating AI-driven content, such as articles, poetry, or scripts.
It integrates advanced language models to create contextually relevant and creative outputs.
"""

from transformers import pipeline, GPT2LMHeadModel, GPT2Tokenizer
import logging

class AIComposer:
    def __init__(self, model_name="gpt2", max_length=200):
        """
        Initialize the AI Composer with a specified language model.
        :param model_name: Name of the language model to use (default: 'gpt2').
        :param max_length: Maximum length for generated content.
        """
        self.model_name = model_name
        self.max_length = max_length
        self.generator = None
        self._load_model()

    def _load_model(self):
        """
        Load the language model and tokenizer.
        """
        logging.info(f"Loading model: {self.model_name}")
        try:
            tokenizer = GPT2Tokenizer.from_pretrained(self.model_name)
            model = GPT2LMHeadModel.from_pretrained(self.model_name)
            self.generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
            logging.info("Model loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load model: {e}")
            raise

    def generate_content(self, prompt, num_return_sequences=1):
        """
        Generate AI-driven content based on a prompt.
        :param prompt: The input text prompt to generate content from.
        :param num_return_sequences: Number of outputs to return.
        :return: List of generated content strings.
        """
        if not self.generator:
            raise RuntimeError("Model not loaded. Call _load_model() to initialize.")
        
        logging.info(f"Generating content for prompt: {prompt}")
        try:
            results = self.generator(
                prompt,
                max_length=self.max_length,
                num_return_sequences=num_return_sequences,
                do_sample=True,
                temperature=0.7
            )
            return [result['generated_text'] for result in results]
        except Exception as e:
            logging.error(f"Content generation failed: {e}")
            raise

# Example usage
if __name__ == "__main__":
    composer = AIComposer()
    prompt = "Write a poem about the beauty of nature."
    generated_content = composer.generate_content(prompt, num_return_sequences=2)
    for i, content in enumerate(generated_content):
        print(f"\nGenerated Content {i+1}:\n{content}")
