"""
modules/nlp_conversation.py
---------------------------
This module handles natural language processing (NLP) conversations for the Devin project.
It enables the system to understand and generate human-like responses in a conversational context.
"""

import logging
import openai  # Ensure you have installed OpenAI SDK or the relevant API
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Configure logging
LOG_FILE = "modules/nlp_conversation.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class start_conversation:
    def __init__(self, model="gpt-3.5-turbo"):
        """
        Initialize the NLPConversation class.

        :param model: The model to use for NLP (e.g., gpt-3.5-turbo).
        """
        self.api_key = os.getenv('OPENAI_API_KEY')  # Fetch the API key from .env file
        if not self.api_key:
            raise ValueError("API key not found in environment variables.")
        
        self.model = model
        openai.api_key = self.api_key  # Setup OpenAI API key or any other API service

    def chat(self, prompt):
        """
        Generate a response from the model based on the provided prompt.

        :param prompt: User's input or query.
        :return: Generated response from the model.
        """
        try:
            logging.info(f"Sending prompt to model: {prompt}")
            response = openai.Completion.create(
                engine=self.model,
                prompt=prompt,
                max_tokens=150
            )
            message = response.choices[0].text.strip()
            logging.info(f"Model response: {message}")
            return message
        except Exception as e:
            logging.error(f"Error during conversation: {e}")
            return "Sorry, I encountered an error while processing your request."

    def respond_to_user(self, user_input):
        """
        Generate a conversation response to the user's input.

        :param user_input: User's message or question.
        :return: Model's generated response.
        """
        prompt = f"The following is a conversation with Devin, an AI assistant:\nUser: {user_input}\nDevin:"
        return self.chat(prompt)

if __name__ == "__main__":
    # Example usage of the NLPConversation class
    try:
        nlp_conversation = NLPConversation()
        user_input = input("Ask Devin: ")
        response = nlp_conversation.respond_to_user(user_input)
        print(f"Devin: {response}")
    except ValueError as e:
        print(e)
