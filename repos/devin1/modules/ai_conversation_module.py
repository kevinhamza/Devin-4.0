"""
ai_conversation_module.py
Handles real-time NLP conversations for the Devin project.
"""

import openai
import logging
from modules.utils.nlp_tools import preprocess_text, analyze_sentiment
from modules.utils.ai_memory import MemoryManager

# Configuration
class AIConversationConfig:
    def __init__(self, api_key, model="gpt-4", max_tokens=1500, temperature=0.7):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

# AI Conversation Module
class AIConversationModule:
    def __init__(self, config: AIConversationConfig):
        self.api_key = config.api_key
        self.model = config.model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
        self.memory = MemoryManager()
        openai.api_key = self.api_key

    def generate_response(self, user_input: str, context: str = "") -> str:
        """
        Generates a conversational response based on user input.
        """
        try:
            logging.info("Preprocessing user input...")
            processed_input = preprocess_text(user_input)
            sentiment = analyze_sentiment(processed_input)
            self.memory.save_user_input(processed_input)

            prompt = f"Context: {context}\nUser: {processed_input}\nAI:"
            logging.info("Calling OpenAI API for response generation...")
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            ai_response = response['choices'][0]['message']['content'].strip()
            logging.info("AI response generated successfully.")
            self.memory.save_ai_response(ai_response)
            return ai_response
        except Exception as e:
            logging.error(f"Error in generating response: {e}")
            return "I'm sorry, I couldn't process your request. Please try again."

# Utilities
class NLPUtilities:
    @staticmethod
    def process_conversation_log(log_path: str):
        """
        Analyzes conversation logs for insights.
        """
        try:
            with open(log_path, 'r') as file:
                log_data = file.read()
            logging.info("Processing conversation log...")
            summary = NLPUtilities.summarize_conversation(log_data)
            return summary
        except Exception as e:
            logging.error(f"Error processing conversation log: {e}")
            return "Error processing log."

    @staticmethod
    def summarize_conversation(log: str) -> str:
        """
        Summarizes the given conversation log.
        """
        try:
            logging.info("Summarizing conversation...")
            response = openai.ChatCompletion.create(
                model="text-davinci-003",
                prompt=f"Summarize the following conversation: {log}",
                max_tokens=500
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            logging.error(f"Error in summarization: {e}")
            return "Error summarizing conversation."

# Example usage
if __name__ == "__main__":
    config = AIConversationConfig(api_key="your_api_key_here")
    ai_conversation = AIConversationModule(config)
    print(ai_conversation.generate_response("Hello! How are you today?"))
