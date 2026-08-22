# Devin/ai_integrations/perplexity_ai_connector.py

import os
import time
import json
import requests # Using requests library for HTTP calls
from typing import Dict, Any, List, Optional, Union

# --- Constants ---
# Perplexity API details (Confirm URL from official Perplexity AI documentation)
PERPLEXITY_API_BASE_URL = "https://api.perplexity.ai"
# Common Perplexity models (Check official docs for current/available models)
# Online models provide up-to-date info but might be slower/different cost
DEFAULT_PPLX_ONLINE_MODEL = "llama-3-sonar-small-32k-online"
DEFAULT_PPLX_OFFLINE_MODEL = "mixtral-8x7b-instruct" # Example offline model
DEFAULT_TIMEOUT_SECONDS = 120
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1

class PerplexityConnector:
    """
    Handles communication with the Perplexity AI API (pplx-api).

    Manages API key authentication, request formatting (OpenAI-compatible chat format),
    API calls, response parsing, and basic error handling/retry logic.
    """

    def __init__(self, api_key: Optional[str] = None, default_model: str = DEFAULT_PPLX_ONLINE_MODEL):
        """
        Initializes the PerplexityConnector.

        Args:
            api_key (Optional[str]): Perplexity AI API key. If None, attempts to read from
                                     the PERPLEXITY_API_KEY environment variable.
                                     *** Handle keys securely. ***
            default_model (str): The default Perplexity model to use if not specified in requests.
                                 Choose between online (e.g., *-online) and offline models.
        """
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        if not self.api_key:
            print("WARNING: Perplexity API key not provided via argument or PERPLEXITY_API_KEY environment variable.")
            print("         Connector will not be able to make authenticated calls.")
        self.default_model = default_model
        self.base_url = PERPLEXITY_API_BASE_URL
        print(f"PerplexityConnector initialized (Default Model: {self.default_model})")

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepares the authorization headers for Perplexity AI API calls."""
        if not self.api_key:
             print("Error: Cannot prepare headers, Perplexity API key is missing.")
             return {"Content-Type": "application/json"}

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_chat_completion(self,
                            messages: List[Dict[str, str]],
                            model: Optional[str] = None,
                            temperature: float = 0.7,
                            max_tokens: Optional[int] = 1024,
                            top_p: float = 1.0,
                            presence_penalty: float = 0.0, # Check Perplexity docs for supported penalties
                            frequency_penalty: float = 0.0, # Check Perplexity docs for supported penalties
                            **kwargs # Allow passing other valid API parameters
                            ) -> Optional[str]:
        """
        Sends a request to the Perplexity Chat Completions API.
        API structure is generally compatible with OpenAI's Chat Completions.

        Args:
            messages (List[Dict[str, str]]): List of message objects [{"role": "user", "content": "..."}].
            model (Optional[str]): Specific Perplexity model to use (e.g., "llama-3-sonar-small-32k-online").
                                   Defaults to self.default_model.
            temperature (float): Sampling temperature.
            max_tokens (Optional[int]): Maximum number of tokens to generate.
            top_p (float): Nucleus sampling parameter.
            presence_penalty (float): Penalty for new tokens. (Verify support in Perplexity docs).
            frequency_penalty (float): Penalty for frequent tokens. (Verify support in Perplexity docs).
            **kwargs: Additional valid parameters for the Perplexity API endpoint.

        Returns:
            Optional[str]: The content of the assistant's response message, or None if an error occurs.
        """
        if not self.api_key:
             print("Error: Cannot get chat completion, Perplexity API key is missing.")
             return None

        if not messages:
             print("Error: 'messages' list cannot be empty.")
             return None

        endpoint = f"{self.base_url}/chat/completions"
        headers = self._prepare_headers()
        selected_model = model or self.default_model

        # Ensure the model name is valid for Perplexity if possible (basic check)
        # if not selected_model.startswith(('llama-', 'mixtral-', 'pplx-')):
        #    print(f"Warning: Model name '{selected_model}' might not be standard Perplexity format.")

        payload = {
            "model": selected_model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            # Include penalties only if known to be supported
            # "presence_penalty": presence_penalty,
            # "frequency_penalty": frequency_penalty,
            **kwargs
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        print(f"\nSending request to Perplexity Chat Completions API (Model: {selected_model})...")

        current_retry = 0
        while current_retry <= MAX_RETRIES:
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=DEFAULT_TIMEOUT_SECONDS
                )
                response.raise_for_status() # Check for HTTP errors (4xx, 5xx)
                response_data = response.json()

                # Parse response (expecting OpenAI-compatible structure)
                if response_data.get("choices") and len(response_data["choices"]) > 0:
                    message = response_data["choices"][0].get("message")
                    if message and isinstance(message, dict):
                        content = message.get("content")
                        if content:
                             print("  - Success: Received response content.")
                             return content.strip()
                        else:
                             print("  - Warning: Response choice message has no 'content'.")
                             return None
                    else:
                         print("  - Warning: Response choice format unexpected or missing 'message'.")
                         return None
                else:
                    print("  - Warning: API response did not contain 'choices'.")
                    return None

            except requests.exceptions.RequestException as e:
                print(f"  - Error during Perplexity API request (Attempt {current_retry+1}/{MAX_RETRIES+1}): {e}")
                error_code = e.response.status_code if e.response is not None else None
                try:
                    error_details = e.response.json() if e.response is not None else None
                    print(f"    - API Error Details: {error_details}")
                except: pass # Ignore JSON decoding errors on error response

                # Retry logic for specific errors (Rate limit, Server errors)
                if error_code in [429, 500, 502, 503, 504] and current_retry < MAX_RETRIES:
                    delay = (INITIAL_RETRY_DELAY_SECONDS * (2 ** current_retry)) + random.uniform(0, 1)
                    print(f"    - Retrying after {delay:.2f} seconds...")
                    time.sleep(delay)
                    current_retry += 1
                else:
                    return None # Failed or non-retryable error
            except Exception as e: # Catch other potential errors
                 print(f"  - Unexpected error processing API call: {e}")
                 return None # Fail on unexpected errors

        print(f"  - Error: Failed to get completion after {MAX_RETRIES} retries.")
        return None

# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Perplexity AI Connector Example ---")

    # IMPORTANT: Set the PERPLEXITY_API_KEY environment variable for this example to work conceptually.
    if not os.environ.get("PERPLEXITY_API_KEY"):
        print("\nWARNING: PERPLEXITY_API_KEY environment variable not set.")
        print("         The following example will fail to make real API calls.")
        connector = PerplexityConnector(api_key="DUMMY_KEY_FOR_EXAMPLE_ONLY")
    else:
        connector = PerplexityConnector() # Reads from environment

    # Example messages
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant providing concise answers."},
        {"role": "user", "content": "What is the main difference between llama-3-sonar-small-32k-online and mixtral-8x7b-instruct on Perplexity?"}
    ]

    # Get completion using default model (likely online)
    response_content = connector.get_chat_completion(
        messages,
        max_tokens=200,
        temperature=0.7
    )

    if response_content:
        print("\nPerplexity Response:")
        print(response_content)
    else:
        print("\nFailed to get response from Perplexity API.")
        print("(This is expected if PERPLEXITY_API_KEY is not set or is invalid/dummy)")

    # Example using a specific (offline) model if needed
    # print("\nTrying specific offline model:")
    # response_offline = connector.get_chat_completion(
    #     messages,
    #     model="mixtral-8x7b-instruct", # Specify different model
    #     max_tokens=200
    # )
    # if response_offline:
    #    print("\nPerplexity Response (Offline Model):")
    #    print(response_offline)
    # else:
    #    print("\nFailed to get response using offline model.")


    print("\n--- End Example ---")
