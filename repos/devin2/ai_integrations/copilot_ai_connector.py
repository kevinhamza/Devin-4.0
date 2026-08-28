# Devin/ai_integrations/copilot_ai_connector.py

import os
import time
import json
import requests # Using requests library for HTTP calls
from typing import Dict, Any, List, Optional, Union

# --- Constants ---
# Assuming use of OpenAI API for backend code generation model
OPENAI_API_BASE_URL = "https://api.openai.com/v1"
# Recommend using models known for strong code generation, e.g., GPT-4 variants
DEFAULT_CODE_MODEL = "gpt-4-turbo"
DEFAULT_TIMEOUT_SECONDS = 60 # Code generation might be quicker
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1

class CopilotConnector:
    """
    Conceptual connector for interacting with an AI code generation/completion service,
    similar in function to GitHub Copilot.

    *** Assumes use of a backend API (like OpenAI's API with a code-capable model) ***
    Handles API key authentication, prompt formatting for code tasks, API calls,
    response parsing, and basic error handling/retry logic.
    """

    def __init__(self, api_key: Optional[str] = None, default_model: str = DEFAULT_CODE_MODEL):
        """
        Initializes the CopilotConnector.

        Args:
            api_key (Optional[str]): API key for the backend code generation service
                                     (e.g., OpenAI API key). Reads from OPENAI_API_KEY env var if None.
                                     *** Handle keys securely. ***
            default_model (str): The default code generation model to use.
        """
        # Using OpenAI key env var name for consistency with assumed backend
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            print("WARNING: OpenAI API key (assumed backend for Copilot-like features) not provided via argument or OPENAI_API_KEY environment variable.")
            print("         Connector will not be able to make authenticated calls.")
        self.default_model = default_model
        self.base_url = OPENAI_API_BASE_URL
        print(f"CopilotConnector initialized (Backend Model Target: {self.default_model})")

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepares the authorization headers for the backend API calls."""
        if not self.api_key:
             print("Error: Cannot prepare headers, API key is missing.")
             return {"Content-Type": "application/json"}

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def get_code_completion(self,
                            code_context: str,
                            language: Optional[str] = None,
                            cursor_position: Optional[int] = None, # Index within code_context
                            model: Optional[str] = None,
                            temperature: float = 0.2, # Lower temp often better for code
                            max_tokens: Optional[int] = 150, # Max tokens for completion
                            stop_sequences: Optional[List[str]] = None, # e.g., ["\n", "```"]
                            **kwargs
                           ) -> Optional[str]:
        """
        Requests code completion suggestions based on the provided context.

        Args:
            code_context (str): The existing code surrounding the point where completion is needed.
            language (Optional[str]): The programming language (e.g., "python", "javascript"). Helps model.
            cursor_position (Optional[int]): The index in code_context where completion is requested.
                                            If None, assumes completion at the end.
            model (Optional[str]): Specific backend model to use. Defaults to self.default_model.
            temperature (float): Sampling temperature. Lower values (e.g., 0.0-0.4) are often better for code.
            max_tokens (Optional[int]): Max number of tokens for the completion.
            stop_sequences (Optional[List[str]]): Sequences where the model should stop generating.
            **kwargs: Additional valid parameters for the backend API endpoint.

        Returns:
            Optional[str]: The generated code completion snippet, or None on error.
        """
        if not self.api_key:
             print("Error: Cannot get code completion, API key is missing.")
             return None

        selected_model = model or self.default_model
        endpoint = f"{self.base_url}/chat/completions" # Using Chat endpoint is flexible
        headers = self._prepare_headers()

        # --- Prompt Engineering for Code Completion ---
        # Format the input for the model. Using Chat Completions allows structuring.
        # Separate context before/after cursor if position is provided.
        prompt_prefix = code_context
        prompt_suffix = None # Code after the cursor, useful for some models (e.g., fill-in-the-middle)

        if cursor_position is not None and 0 <= cursor_position <= len(code_context):
            prompt_prefix = code_context[:cursor_position]
            prompt_suffix = code_context[cursor_position:]
            print(f"  - Formatting prompt for completion at position {cursor_position}")
        else:
            print("  - Formatting prompt for completion at the end.")

        # Construct messages for Chat API
        messages = []
        system_message = f"You are an AI programming assistant, expert in {language or 'various languages'}."
        system_message += " Complete the following code snippet. Provide only the code completion, without explanations, introductory phrases, or markdown formatting unless it's part of the code itself."
        messages.append({"role": "system", "content": system_message})

        # User message contains the context. How to structure depends on model's training.
        # Option 1: Simple continuation
        user_content = f"Complete the following {language or 'code'}:\n```\n{prompt_prefix}\n```"
        # Option 2: Explicit prefix/suffix (might require specific model fine-tuning or prompt techniques)
        # if prompt_suffix is not None:
        #    user_content = f"Complete the code between the prefix and suffix.\nPREFIX:\n```\n{prompt_prefix}\n```\nSUFFIX:\n```\n{prompt_suffix}\n```\nCOMPLETION:"

        messages.append({"role": "user", "content": user_content})
        # --- End Prompt Engineering ---


        payload = {
            "model": selected_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            # "stop": stop_sequences, # Pass stop sequences if provided
            **kwargs
        }
        if stop_sequences:
             payload["stop"] = stop_sequences


        print(f"Sending request to Backend API for Code Completion (Model: {selected_model})...")

        current_retry = 0
        while current_retry <= MAX_RETRIES:
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=DEFAULT_TIMEOUT_SECONDS
                )
                response.raise_for_status()
                response_data = response.json()

                # Extract completion
                if response_data.get("choices") and len(response_data["choices"]) > 0:
                    message = response_data["choices"][0].get("message")
                    if message and isinstance(message, dict):
                        completion = message.get("content")
                        if completion is not None: # Completion can be empty string
                             print("  - Success: Received code completion.")
                             # Post-processing: remove potential ``` artifacts if model adds them
                             completion = completion.strip()
                             if completion.startswith("```"): completion = completion[3:]
                             if completion.endswith("```"): completion = completion[:-3]
                             # Further cleanup might be needed based on model behavior
                             return completion.strip('\n') # Remove leading/trailing newlines often added
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
                print(f"  - Error during API request (Attempt {current_retry+1}/{MAX_RETRIES+1}): {e}")
                error_code = e.response.status_code if e.response is not None else None
                if error_code in [429, 500, 502, 503, 504] and current_retry < MAX_RETRIES:
                    delay = (INITIAL_RETRY_DELAY_SECONDS * (2 ** current_retry)) + random.uniform(0, 1)
                    print(f"    - Retrying after {delay:.2f} seconds...")
                    time.sleep(delay)
                    current_retry += 1
                else:
                    return None # Failed
            except Exception as e:
                 print(f"  - Unexpected error processing API call: {e}")
                 return None # Failed

        print(f"  - Error: Failed to get code completion after {MAX_RETRIES} retries.")
        return None

    # Could add other methods like:
    # - generate_code_from_description(description: str, language: str) -> Optional[str]:
    # - find_code_bugs(code_snippet: str, language: str) -> Optional[List[Dict]]:
    # - explain_code(code_snippet: str, language: str) -> Optional[str]:


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Copilot Connector Example (Conceptual) ---")

    # IMPORTANT: Set the OPENAI_API_KEY environment variable.
    if not os.environ.get("OPENAI_API_KEY"):
        print("\nWARNING: OPENAI_API_KEY environment variable not set.")
        print("         The following example will fail to make real API calls.")
        connector = CopilotConnector(api_key="DUMMY_KEY_FOR_EXAMPLE_ONLY")
    else:
        connector = CopilotConnector()

    # Example 1: Complete a Python function
    python_context = """
import pandas as pd

def calculate_mean(data: list) -> float:
    \"\"\"Calculates the mean of a list of numbers.\"\"\"
    if not data:
        return 0.0
    # Complete the calculation below
"""
    print("\nRequesting completion for Python function:")
    completion1 = connector.get_code_completion(
        code_context=python_context,
        language="python",
        max_tokens=50,
        temperature=0.1,
        stop_sequences=["\n\n", "def ", "class "] # Stop at blank lines or new definitions
    )

    if completion1 is not None:
        print("\nGenerated Completion 1:")
        print(f"```python\n{python_context.rstrip()}{completion1}\n```") # Display completed code
    else:
        print("\nFailed to get completion 1.")


    # Example 2: Complete HTML
    html_context = """
<!DOCTYPE html>
<html>
<head>
    <title>My Page</title>
</head>
<body>
    <h1>Welcome</h1>
    <p>This is a paragraph.</p>
    """
    print("\nRequesting completion for HTML:")
    completion2 = connector.get_code_completion(
        code_context=html_context,
        language="html",
        max_tokens=30,
        temperature=0.3
    )

    if completion2 is not None:
        print("\nGenerated Completion 2:")
        print(f"```html\n{html_context.rstrip()}{completion2}\n```")
    else:
        print("\nFailed to get completion 2.")

    print("\n--- End Example ---")
