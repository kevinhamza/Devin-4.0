import openai
import logging
import os
from transformers import GPT2TokenizerFast
from dotenv import load_dotenv

load_dotenv()

class ChatBot:
    def __init__(self, model='gpt-3.5-turbo', api_key=None):
        """
        Initialize the Chatbot with OpenAI's model.
        """
        self.model = model
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("API key for OpenAI is required.")
        openai.api_key = self.api_key
        self.tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

    def generate_response(self, user_prompt, max_tokens=300, temperature=0.7):
        """
        Generate a response for the given user prompt using the OpenAI model.
        """
        logging.info("Generating response for user prompt.")
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                stop=None
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return "Sorry, I couldn't process your request at the moment."

    def estimate_tokens(self, text):
        """
        Estimate the number of tokens in the text using GPT-2 tokenizer.
        """
        return len(self.tokenizer.encode(text))

    def interact(self):
        """
        Facilitate a conversational interaction with the user.
        """
        print("Chatbot initialized. Type 'exit' to quit.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                print("Chatbot: Goodbye!")
                break
            estimated_tokens = self.estimate_tokens(user_input)
            print(f"Estimated Tokens: {estimated_tokens}")
            response = self.generate_response(user_input)
            print(f"Chatbot: {response}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    chatbot = Chatbot()
    chatbot.interact()
