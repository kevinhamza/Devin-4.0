# Devin/ai_integrations/chatgpt_connector.py

import os
import time
import json
import requests # Using requests library for HTTP calls
from typing import Dict, Any, List, Optional, Union

# --- Constants ---
# Consider moving URLs and default models to config/ai_config.yaml
OPENAI_API_BASE_URL = "https://api.openai.com/v1"
DEFAULT_CHAT_MODEL = "gpt-4-turbo" # Example default model
DEFAULT_TIMEOUT_SECONDS = 120 # Timeout for API requests
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1

class ChatGPTConnector:
    """
    Handles communication with the OpenAI ChatGPT API (Chat Completions endpoint).

    Manages API key authentication, request formatting, API calls,
    response parsing, and basic error handling/retry logic.
    """

    def __init__(self, api_key: Optional[str] = None, default_model: str = DEFAULT_CHAT_MODEL):
        """
        Initializes the ChatGPTConnector.

        Args:
            api_key (Optional[str]): OpenAI API key. If None, attempts to read from
                                     the OPENAI_API_KEY environment variable.
                                     *** Best practice: Use environment variables or a secure secrets manager. ***
            default_model (str): The default ChatGPT model to use if not specified in requests.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            # In a real application, you might raise an error or have a more robust
            # way to handle missing keys depending on required functionality.
            print("WARNING: OpenAI API key not provided via argument or OPENAI_API_KEY environment variable.")
            print("         Connector will not be able to make authenticated calls.")
            # raise ValueError("OpenAI API Key is required.")
        self.default_model = default_model
        self.base_url = OPENAI_API_BASE_URL
        print(f"ChatGPTConnector initialized (Default Model: {self.default_model})")

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepares the authorization headers for OpenAI API calls."""
        if not self.api_key:
             print("Error: Cannot prepare headers, API key is missing.")
             # Depending on design, might want to raise error here if key is essential
             return {"Content-Type": "application/json"} # Return basic header anyway

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Optionally add OpenAI-Organization header if needed:
            # "OpenAI-Organization": "YOUR_ORG_ID"
        }

    def get_chat_completion(self,
                            messages: List[Dict[str, str]],
                            model: Optional[str] = None,
                            temperature: float = 0.7,
                            max_tokens: Optional[int] = 1024,
                            top_p: float = 1.0,
                            presence_penalty: float = 0.0,
                            frequency_penalty: float = 0.0,
                            **kwargs # Allow passing other valid API parameters
                            ) -> Optional[str]:
        """
        Sends a request to the OpenAI Chat Completions API.

        Args:
            messages (List[Dict[str, str]]): A list of message objects, following the OpenAI format
                                            (e.g., [{"role": "user", "content": "Hello!"}]).
            model (Optional[str]): The specific model to use (e.g., "gpt-4", "gpt-3.5-turbo").
                                   Defaults to self.default_model.
            temperature (float): Sampling temperature (0.0-2.0). Higher values make output more random.
            max_tokens (Optional[int]): Maximum number of tokens to generate.
            top_p (float): Nucleus sampling parameter.
            presence_penalty (float): Penalty for new tokens based on whether they appear in the text so far.
            frequency_penalty (float): Penalty for new tokens based on their existing frequency.
            **kwargs: Additional valid parameters for the OpenAI API endpoint.

        Returns:
            Optional[str]: The content of the assistant's response message, or None if an error occurs.
        """
        if not self.api_key:
             print("Error: Cannot get chat completion, API key is missing.")
             return None

        if not messages:
             print("Error: 'messages' list cannot be empty.")
             return None

        endpoint = f"{self.base_url}/chat/completions"
        headers = self._prepare_headers()
        selected_model = model or self.default_model

        payload = {
            "model": selected_model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            **kwargs # Include any extra valid parameters passed
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        print(f"\nSending request to OpenAI Chat Completions API (Model: {selected_model})...")
        # print(f"Payload (preview): {json.dumps(payload, indent=2)[:500]}...") # Careful logging payload

        current_retry = 0
        while current_retry <= MAX_RETRIES:
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=DEFAULT_TIMEOUT_SECONDS
                )

                # Raise HTTP errors (4xx, 5xx)
                response.raise_for_status()

                # Successful response
                response_data = response.json()
                # print(f"API Response Data (preview): {json.dumps(response_data, indent=2)[:500]}...") # Careful logging response

                # Extract the content from the first choice's message
                if response_data.get("choices") and len(response_data["choices"]) > 0:
                    message = response_data["choices"][0].get("message")
                    if message and isinstance(message, dict):
                        content = message.get("content")
                        if content:
                             print("  - Success: Received response content.")
                             return content.strip()
                        else:
                             print("  - Warning: Response choice message has no 'content'.")
                             return None # Or handle function calls etc. if implemented
                    else:
                         print("  - Warning: Response choice format unexpected or missing 'message'.")
                         return None
                else:
                    print("  - Warning: API response did not contain 'choices'.")
                    return None # Or raise specific error

            except requests.exceptions.RequestException as e:
                print(f"  - Error during API request (Attempt {current_retry+1}/{MAX_RETRIES+1}): {e}")
                error_code = None
                if e.response is not None:
                    error_code = e.response.status_code
                    try:
                         error_details = e.response.json()
                         print(f"    - API Error Details: {error_details}")
                    except json.JSONDecodeError:
                         print(f"    - API Response Body (non-JSON): {e.response.text[:500]}")

                # Retry logic for specific errors
                if error_code in [429, 500, 502, 503, 504] and current_retry < MAX_RETRIES: # Rate limit or server error
                    delay = (INITIAL_RETRY_DELAY_SECONDS * (2 ** current_retry)) + random.uniform(0, 1)
                    print(f"    - Retrying after {delay:.2f} seconds...")
                    time.sleep(delay)
                    current_retry += 1
                else:
                    # Non-retryable error or max retries reached
                    return None # Failed after retries or due to non-retryable error
            except Exception as e: # Catch other potential errors
                 print(f"  - Unexpected error processing API call: {e}")
                 return None # Fail on unexpected errors

        # If loop finishes without returning (max retries exceeded)
        print(f"  - Error: Failed to get completion after {MAX_RETRIES} retries.")
        return None


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- ChatGPT Connector Example ---")

    # IMPORTANT: Set the OPENAI_API_KEY environment variable for this example to work conceptually.
    if not os.environ.get("OPENAI_API_KEY"):
        print("\nWARNING: OPENAI_API_KEY environment variable not set.")
        print("         The following example will fail to make real API calls.")
        # Assign a dummy key for the example to proceed without erroring immediately
        connector = ChatGPTConnector(api_key="DUMMY_KEY_FOR_EXAMPLE_ONLY")
    else:
        connector = ChatGPTConnector() # Reads from environment

    # Example chat messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]

    # Get completion
    response_content = connector.get_chat_completion(messages, max_tokens=50, temperature=0.5)

    if response_content:
        print("\nAssistant Response:")
        print(response_content)
    else:
        print("\nFailed to get response from ChatGPT API.")
        print("(This is expected if OPENAI_API_KEY is not set or is invalid/dummy)")

    print("\n--- End Example ---")
