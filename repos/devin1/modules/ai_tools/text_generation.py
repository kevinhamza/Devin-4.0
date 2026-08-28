"""
text_generation.py
-------------------
Provides tools for generating coherent and contextually relevant text using pre-trained
natural language generation (NLG) models.
"""

from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

class TextGenerator:
    """
    A class for generating text using pre-trained models.
    """

    def __init__(self, model_name="gpt-2"):
        """
        Initialize the TextGenerator with a specified model.

        Args:
            model_name (str): The name of the pre-trained model to use.
        """
        self.model_name = model_name
        self.pipeline = None
        self.tokenizer = None
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """
        Load the model and tokenizer.
        """
        try:
            self.pipeline = pipeline("text-generation", model=self.model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        except Exception as e:
            print(f"Error initializing the model '{self.model_name}': {e}")

    def generate_text(self, prompt, max_length=50, num_return_sequences=1, temperature=1.0, top_p=0.9):
        """
        Generate text based on the provided prompt.

        Args:
            prompt (str): The initial text to guide generation.
            max_length (int): The maximum length of the generated text.
            num_return_sequences (int): The number of generated text sequences to return.
            temperature (float): Controls randomness (higher values = more random).
            top_p (float): Controls diversity using nucleus sampling (0.0 to 1.0).

        Returns:
            list: Generated text sequences.
        """
        try:
            generated_texts = self.pipeline(
                prompt,
                max_length=max_length,
                num_return_sequences=num_return_sequences,
                temperature=temperature,
                top_p=top_p
            )
            return [text["generated_text"] for text in generated_texts]
        except Exception as e:
            return [f"Error generating text: {e}"]

    def generate_custom(self, prompt, max_length=50):
        """
        Generate text using a more custom implementation with direct model/tokenizer calls.

        Args:
            prompt (str): The initial text to guide generation.
            max_length (int): The maximum length of the generated text.

        Returns:
            str: Generated text.
        """
        try:
            input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
            output_ids = self.model.generate(
                input_ids,
                max_length=max_length,
                temperature=1.0,
                top_k=50,
                top_p=0.95,
                do_sample=True
            )
            return self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        except Exception as e:
            return f"Error in custom text generation: {e}"


# Example Usage
if __name__ == "__main__":
    generator = TextGenerator(model_name="gpt-2")

    # Example prompt
    prompt = "Artificial intelligence is revolutionizing the world by"

    # Generate text with default settings
    print("Generated Text:")
    generated_texts = generator.generate_text(prompt, max_length=50, num_return_sequences=2)
    for i, text in enumerate(generated_texts, 1):
        print(f"[{i}] {text}")

    # Generate text using the custom method
    print("\nCustom Generated Text:")
    custom_text = generator.generate_custom(prompt, max_length=50)
    print(custom_text)
