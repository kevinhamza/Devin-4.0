"""
gimini.py
Conversational AI module leveraging advanced natural language understanding.
"""

import logging
from transformers import pipeline, Conversation

# Configuration
class GiminiConfig:
    def __init__(self, model_name="facebook/blenderbot-400M-distill", max_conversation_length=1024):
        self.model_name = model_name
        self.max_conversation_length = max_conversation_length

# Gimini Conversational AI
class Gimini:
    def __init__(self, config: GiminiConfig):
        self.config = config
        try:
            logging.info(f"Initializing Gimini with model {self.config.model_name}.")
            self.chatbot = pipeline("conversational", model=self.config.model_name)
        except Exception as e:
            logging.error(f"Failed to load conversational AI model: {e}")
            raise e
        self.conversation_history = []

    def ask(self, user_input: str) -> str:
        """
        Processes user input and generates a response.
        """
        try:
            logging.info("Processing user input for conversation.")
            if len(self.conversation_history) > self.config.max_conversation_length:
                logging.warning("Conversation history exceeded maximum length. Resetting history.")
                self.conversation_history = []

            self.conversation_history.append({"role": "user", "content": user_input})
            conversation = Conversation(user_input)
            response = self.chatbot(conversation)
            bot_response = response.generated_responses[-1]
            self.conversation_history.append({"role": "bot", "content": bot_response})
            logging.info(f"Gimini response: {bot_response}")
            return bot_response
        except Exception as e:
            logging.error(f"Error during conversation processing: {e}")
            return "I'm sorry, I encountered an error while processing your request."

    def reset_conversation(self):
        """
        Resets the conversation history.
        """
        logging.info("Resetting conversation history.")
        self.conversation_history = []

    def get_conversation_history(self):
        """
        Returns the full conversation history.
        """
        return self.conversation_history

# Example usage
if __name__ == "__main__":
    config = GiminiConfig(model_name="facebook/blenderbot-400M-distill")
    gimini = Gimini(config)

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting conversation. Goodbye!")
            break
        response = gimini.ask(user_input)
        print(f"Gimini: {response}")
