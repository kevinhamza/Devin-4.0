# Devin/ai_integrations/whiterabbitneo_ai_connector.py # (Conceptual Generic Local/Custom LLM Connector)

import os
import time
import json
import requests # Using requests library for HTTP calls
from typing import Dict, Any, List, Optional, Union

# --- Constants ---
# Default URL often used by local LLM servers (Ollama, LM Studio OpenAI-compatible endpoint)
# Should be configurable via config/ai_config.yaml or environment variables
DEFAULT_LOCAL_LLM_URL = os.environ.get("LOCAL_LLM_API_URL", "http://localhost:1234/v1") # Example LM Studio default
# DEFAULT_LOCAL_LLM_URL = os.environ.get("LOCAL_LLM_API_URL", "http://localhost:11434/api") # Example Ollama default (endpoint structure differs)

DEFAULT_LOCAL_MODEL_NAME = os.environ.get("LOCAL_LLM_MODEL_NAME", "local-model") # Model name depends on what's served
DEFAULT_TIMEOUT_SECONDS = 180 # Local models can sometimes be slower
MAX_RETRIES = 2
INITIAL_RETRY_DELAY_SECONDS = 2

class LocalLLMConnector:
    """
    Conceptual connector for interacting with a generic local or custom LLM service
    via a REST API endpoint (potentially hosting models like WhiteRabbitNeo or others).

    *** WARNING: Assumes the target endpoint might serve uncensored models. ***
    *** User is responsible for safe, ethical use and output filtering. ***

    NOTE: This skeleton primarily assumes an OpenAI-compatible API structure,
          common for servers like LM Studio or vLLM. Adjustments needed for
          other API structures (like Ollama's native API).
    """

    def __init__(self, api_url: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initializes the LocalLLMConnector.

        Args:
            api_url (Optional[str]): The base URL of the local LLM API service.
                                     Defaults to DEFAULT_LOCAL_LLM_URL.
            model_name (Optional[str]): The specific model identifier to use on the local server.
                                       Defaults to DEFAULT_LOCAL_MODEL_NAME.
        """
        self.api_url = api_url or DEFAULT_LOCAL_LLM_URL
        # Determine if targeting OpenAI compatible endpoint structure based on common URLs
        self.is_openai_compatible = "/v1" in self.api_url
        self.default_model = model_name or DEFAULT_LOCAL_MODEL_NAME
        print(f"LocalLLMConnector initialized (API URL: {self.api_url}, Default Model: {self.default_model})")
        print(f"  - Assuming OpenAI Compatible API: {self.is_openai_compatible}")
        print("  - *** WARNING: Use this connector with caution. Ensure ethical use and filter outputs if connecting to uncensored models. ***")

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepares headers. Local models usually don't require auth."""
        return {"Content-Type": "application/json"}

    # --- Primary Method (assuming OpenAI Chat compatible endpoint) ---
    def get_chat_completion(self,
                            messages: List[Dict[str, str]],
                            model: Optional[str] = None,
                            temperature: float = 0.7,
                            max_tokens: Optional[int] = 1536, # Local models might handle larger contexts/outputs
                            stop_sequences: Optional[List[str]] = None,
                            **kwargs # Allow passing other valid API parameters
                            ) -> Optional[str]:
        """
        Sends a request to a local LLM server using an OpenAI-compatible Chat Completions format.

        Args:
            messages (List[Dict[str, str]]): List of message objects [{"role": "user", "content": "..."}].
            model (Optional[str]): Specific model name served by the local endpoint. Defaults to self.default_model.
            temperature (float): Sampling temperature.
            max_tokens (Optional[int]): Max tokens for completion.
            stop_sequences (Optional[List[str]]): Sequences to stop generation at.
            **kwargs: Additional parameters supported by the local server's endpoint.

        Returns:
            Optional[str]: The generated text content, or None if an error occurs.
                           *** WARNING: Output may be unfiltered and potentially harmful. ***
        """
        if not self.is_openai_compatible:
            print("Error: This method assumes an OpenAI-compatible API structure (e.g., '/v1/chat/completions'). Adjust connector or endpoint.")
            # Potentially call a different method tailored for Ollama or other APIs here
            return self._call_other_local_api(payload={"model": model or self.default_model, "messages": messages, **kwargs})


        endpoint = f"{self.api_url.strip('/')}/chat/completions" # Standard OpenAI path
        headers = self._prepare_headers()
        selected_model = model or self.default_model

        payload = {
            "model": selected_model, # Model name might be required by the local server
            "messages": messages,
            "temperature": max(0.01, temperature), # Some local servers dislike temp=0
            "max_tokens": max_tokens,
            # Add other common parameters if needed and supported by local server
            # "top_p": kwargs.get("top_p", 1.0),
            # "stream": False,
            **kwargs
        }
        if stop_sequences:
             payload["stop"] = stop_sequences

        print(f"\nSending request to Local LLM API (Model: {selected_model}, Endpoint: {endpoint})...")
        print("  - *** WARNING: Requesting potentially unfiltered content. Use responsibly. ***")

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

                # Parse response (structure matches OpenAI)
                if response_data.get("choices") and len(response_data["choices"]) > 0:
                    message = response_data["choices"][0].get("message")
                    if message and isinstance(message, dict):
                        content = message.get("content")
                        if content is not None:
                             print("  - Success: Received potentially unfiltered response content.")
                             # *** NO FILTERING APPLIED HERE - USER MUST HANDLE SAFETY ***
                             return content.strip()
                        else:
                             print("  - Warning: Response choice message has no 'content'.")
                             return None
                    else:
                         print("  - Warning: Response choice format unexpected or missing 'message'.")
                         return None
                else:
                    # Handle cases where local server might just return text directly (less common for OpenAI standard)
                    # Or if choices is empty
                    print("  - Warning: API response did not contain expected 'choices' structure.")
                    # Attempt to extract text if response looks like simple text completion (adjust if needed)
                    potential_text = response_data.get("text") or response_data.get("completion")
                    if isinstance(potential_text, str):
                         print("  - Attempting to extract text from alternate response field.")
                         return potential_text.strip()
                    return None

            except requests.exceptions.ConnectionError as e:
                 print(f"  - Error: Cannot connect to Local LLM API at {self.api_url}. Is the server running? ({e})")
                 return None # Connection errors usually aren't retryable immediately
            except requests.exceptions.Timeout as e:
                 print(f"  - Error: Request timed out after {DEFAULT_TIMEOUT_SECONDS}s (Attempt {current_retry+1}/{MAX_RETRIES+1}): {e}")
                 # Optionally retry timeouts
                 if current_retry < MAX_RETRIES:
                     delay = (INITIAL_RETRY_DELAY_SECONDS * (2 ** current_retry)) + random.uniform(0, 1)
                     print(f"    - Retrying after {delay:.2f} seconds...")
                     time.sleep(delay)
                     current_retry += 1
                 else:
                    return None
            except requests.exceptions.RequestException as e:
                print(f"  - Error during Local LLM API request (Attempt {current_retry+1}/{MAX_RETRIES+1}): {e}")
                # Basic retry for generic server errors (5xx)
                error_code = e.response.status_code if e.response is not None else None
                if error_code is not None and 500 <= error_code <= 599 and current_retry < MAX_RETRIES:
                    delay = (INITIAL_RETRY_DELAY_SECONDS * (2 ** current_retry)) + random.uniform(0, 1)
                    print(f"    - Server error ({error_code}). Retrying after {delay:.2f} seconds...")
                    time.sleep(delay)
                    current_retry += 1
                else:
                    # Non-retryable or max retries hit
                    try:
                        error_details = e.response.json() if e.response is not None else None
                        print(f"    - API Error Details: {error_details}")
                    except: # Ignore JSON decode errors on error response
                        pass
                    return None
            except Exception as e:
                 print(f"  - Unexpected error processing API call: {e}")
                 return None

        print(f"  - Error: Failed to get completion after {MAX_RETRIES} retries.")
        return None

    def _call_other_local_api(self, payload: Dict) -> Optional[str]:
        """Placeholder for handling non-OpenAI-compatible local APIs like Ollama."""
        print(f"  - Notice: Calling generic local API structure (Placeholder - logic for {self.api_url} needed).")
        # Example structure for Ollama /api/generate
        if "ollama" in self.api_url:
             endpoint = f"{self.api_url.strip('/')}/generate"
             ollama_payload = {
                 "model": payload.get("model", self.default_model),
                 "prompt": payload.get("messages", [{"role":"user", "content":""}])[-1].get("content",""), # Simple: use last message content as prompt
                 "stream": False,
                 # Map other params if possible: "options": {"temperature": ..., "num_predict": ...}
             }
             # Make requests.post call similar to _send_request but parse Ollama's response format
             # response_data = self._send_request_generic(endpoint, ollama_payload) # Requires adapting _send_request
             # if response_data: return response_data.get("response")
             print("    - Placeholder: Ollama request/response logic not implemented.")
             return None
        else:
             print(f"    - Error: Unsupported local API structure inferred for {self.api_url}")
             return None


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Local LLM Connector Example (Conceptual) ---")

    # Assumes a local LLM server is running at DEFAULT_LOCAL_LLM_URL (e.g., http://localhost:1234/v1)
    # And serving a model named DEFAULT_LOCAL_MODEL_NAME (e.g., "local-model")
    # If no server is running, the example will fail connection.

    # *** REMINDER: ENSURE ETHICAL USE AND OUTPUT FILTERING ***
    print("\n*** WARNING: This example interacts with potentially unfiltered models. Review outputs carefully. ***")

    connector = LocalLLMConnector() # Uses defaults from env vars or constants

    # Example chat messages
    messages = [
        {"role": "system", "content": "You are a helpful, locally running assistant."},
        {"role": "user", "content": "Write a short Python function to add two numbers."}
    ]

    # Get completion
    response_content = connector.get_chat_completion(messages, max_tokens=100, temperature=0.5)

    if response_content is not None:
        print("\nLocal LLM Response:")
        # *** NO FILTERING APPLIED HERE ***
        print(response_content)
    else:
        print("\nFailed to get response from Local LLM API.")
        print(f"(Check if a local server is running at {connector.api_url} and serving model '{connector.default_model}')")

    print("\n--- End Example ---")
