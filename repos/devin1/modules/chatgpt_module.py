"""
ChatGPT Module
==============
This module handles conversations with the OpenAI ChatGPT API.
It enables seamless interaction for generating conversational responses, summarization, and task-specific AI-driven solutions.
"""

import openai


class ChatGPTModule:
    """
    A module for interacting with OpenAI's ChatGPT API.
    """

    def __init__(self, api_key: str):
        """
        Initializes the ChatGPT module with the provided API key.

        Args:
            api_key (str): OpenAI API key for authentication.
        """
        print("[INFO] Initializing ChatGPT Module...")
        self.api_key = api_key
        openai.api_key = self.api_key
        self.model = "gpt-4"

    def send_message(self, message: str, context: list = None) -> str:
        """
        Sends a message to ChatGPT and returns the response.

        Args:
            message (str): The user's input message.
            context (list): Optional list of previous messages for context.

        Returns:
            str: The AI's response.
        """
        print("[INFO] Sending message to ChatGPT...")
        context = context or []
        context.append({"role": "user", "content": message})

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=context
            )
            reply = response['choices'][0]['message']['content'].strip()
            context.append({"role": "assistant", "content": reply})
            print("[INFO] Response received successfully.")
            return reply
        except Exception as e:
            print(f"[ERROR] Failed to get response from ChatGPT: {e}")
            return "Error: Unable to process the request at this time."

    def summarize_text(self, text: str) -> str:
        """
        Summarizes a given text using ChatGPT.

        Args:
            text (str): The text to be summarized.

        Returns:
            str: The summarized text.
        """
        print("[INFO] Summarizing text with ChatGPT...")
        prompt = f"Please provide a concise summary of the following text:\n{text}"
        return self.send_message(prompt)

    def generate_code(self, description: str, language: str = "Python") -> str:
        """
        Generates code snippets based on a description.

        Args:
            description (str): Description of the desired functionality.
            language (str): The programming language for the code.

        Returns:
            str: The generated code snippet.
        """
        print("[INFO] Generating code with ChatGPT...")
        prompt = f"Generate a {language} code snippet for the following task:\n{description}"
        return self.send_message(prompt)

    def translate_text(self, text: str, target_language: str) -> str:
        """
        Translates text to a specified target language.

        Args:
            text (str): The text to translate.
            target_language (str): The target language for translation.

        Returns:
            str: The translated text.
        """
        print("[INFO] Translating text with ChatGPT...")
        prompt = f"Translate the following text to {target_language}:\n{text}"
        return self.send_message(prompt)

    def contextual_task(self, task_description: str, user_context: list = None) -> str:
        """
        Executes a contextual task based on a description and optional user context.

        Args:
            task_description (str): Description of the task.
            user_context (list): Previous messages or context for better understanding.

        Returns:
            str: The response or result of the task.
        """
        print("[INFO] Performing a contextual task with ChatGPT...")
        prompt = f"Perform the following task:\n{task_description}"
        return self.send_message(prompt, context=user_context)

    def debug_code(self, code_snippet: str, language: str = "Python") -> str:
        """
        Debugs a given code snippet.

        Args:
            code_snippet (str): The code to debug.
            language (str): The programming language of the code.

        Returns:
            str: Debugging suggestions or corrected code.
        """
        print("[INFO] Debugging code with ChatGPT...")
        prompt = f"Debug the following {language} code and provide suggestions or corrections:\n{code_snippet}"
        return self.send_message(prompt)

    def summarize_conversation(self, conversation: list) -> str:
        """
        Summarizes a chat conversation.

        Args:
            conversation (list): List of messages in the conversation.

        Returns:
            str: The summarized conversation.
        """
        print("[INFO] Summarizing conversation with ChatGPT...")
        prompt = "Summarize the following conversation:\n" + "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in conversation]
        )
        return self.send_message(prompt)

    def summary(self):
        """
        Prints a summary of available features in the ChatGPT module.
        """
        tools = [
            "Real-time Conversation",
            "Text Summarization",
            "Code Generation",
            "Text Translation",
            "Contextual Task Execution",
            "Code Debugging",
            "Conversation Summarization",
        ]
        print("[INFO] ChatGPT Module Summary:")
        for tool in tools:
            print(f"- {tool}")
