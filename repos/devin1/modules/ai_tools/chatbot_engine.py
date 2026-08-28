"""
chatbot_engine.py
Conversational AI module for the Devin project.
This module handles advanced conversational capabilities using AI APIs.
"""

import openai
import logging
from typing import List, Dict, Union

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class ChatbotEngine:
    """
    A class to interact with conversational AI services.
    """
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize the ChatbotEngine.

        Args:
            api_key (str): The API key for accessing AI services.
            model (str): The AI model to use for the chatbot.
        """
        self.api_key = api_key
        self.model = model
        openai.api_key = self.api_key
        logging.info("ChatbotEngine initialized with model: %s", self.model)

    def process_query(self, query: str, context: List[Dict[str, str]] = None) -> str:
        """
        Process user query and generate a response.

        Args:
            query (str): User input query.
            context (List[Dict[str, str]], optional): Contextual conversation history.

        Returns:
            str: AI-generated response.
        """
        try:
            messages = context if context else []
            messages.append({"role": "user", "content": query})

            logging.info("Sending query to AI model...")
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages
            )
            ai_response = response.choices[0].message["content"]
            logging.info("AI response generated.")
            return ai_response
        except Exception as e:
            logging.error("Error in process_query: %s", str(e))
            return "Sorry, I encountered an error processing your request."

    def extract_keywords(self, text: str) -> Union[List[str], str]:
        """
        Extract keywords from a given text.

        Args:
            text (str): Text input for keyword extraction.

        Returns:
            Union[List[str], str]: List of keywords or error message.
        """
        try:
            logging.info("Extracting keywords...")
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"Extract keywords from the following text: {text}",
                max_tokens=50
            )
            keywords = response.choices[0].text.strip().split(", ")
            logging.info("Keywords extracted successfully.")
            return keywords
        except Exception as e:
            logging.error("Error in extract_keywords: %s", str(e))
            return "Error extracting keywords."

    def summarize_text(self, text: str) -> Union[str, str]:
        """
        Summarize a given text.

        Args:
            text (str): Text to be summarized.

        Returns:
            Union[str, str]: Summary of the text or error message.
        """
        try:
            logging.info("Summarizing text...")
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=f"Summarize the following text: {text}",
                max_tokens=100
            )
            summary = response.choices[0].text.strip()
            logging.info("Text summarized successfully.")
            return summary
        except Exception as e:
            logging.error("Error in summarize_text: %s", str(e))
            return "Error summarizing text."

    def generate_response(self, prompt: str, personality: str = "neutral") -> str:
        """
        Generate a detailed AI response based on the prompt and personality.

        Args:
            prompt (str): User input prompt.
            personality (str): Personality style for the response.

        Returns:
            str: AI-generated detailed response.
        """
        try:
            full_prompt = f"Respond as a {personality} assistant: {prompt}"
            logging.info("Generating AI response with personality: %s", personality)
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=full_prompt,
                max_tokens=150
            )
            detailed_response = response.choices[0].text.strip()
            logging.info("Detailed response generated successfully.")
            return detailed_response
        except Exception as e:
            logging.error("Error in generate_response: %s", str(e))
            return "Error generating detailed response."

# Example usage
if __name__ == "__main__":
    api_key = "your_openai_api_key"
    chatbot = ChatbotEngine(api_key=api_key)
    
    query = "What are the benefits of AI?"
    context = [{"role": "system", "content": "You are a helpful assistant."}]
    
    response = chatbot.process_query(query, context)
    print("AI Response:", response)

    keywords = chatbot.extract_keywords("Artificial intelligence is transforming industries.")
    print("Keywords:", keywords)

    summary = chatbot.summarize_text("Artificial intelligence enables machines to learn and adapt.")
    print("Summary:", summary)
