# Devin/ai_integrations/gemini_connector.py # Purpose: Connector for Google Gemini models API.

import os
import time
import random
from typing import Dict, Any, List, Optional, Union

# Preferred: Use the official Google AI Python SDK
# Placeholder import - requires `pip install google-generativeai`
try:
    import google.generativeai as genai
    # Placeholder for specific exceptions (check SDK docs for exact names)
    StopCandidateException = getattr(genai.types, 'StopCandidateException', Exception)
    BlockedPromptException = getattr(genai.types, 'BlockedPromptException', Exception)
    ResourceExhaustedError = getattr(genai.types, 'ResourceExhausted', getattr(genai.types, 'google.api_core.exceptions.ResourceExhausted', Exception)) # Example exception mapping
except ImportError:
    print("WARNING: google-generativeai library not found. GeminiConnector will use non-functional placeholders.")
    genai = None
    StopCandidateException = Exception
    BlockedPromptException = Exception
    ResourceExhaustedError = Exception


# --- Constants ---
DEFAULT_GEMINI_MODEL = "gemini-1.5-pro-latest" # Example default model
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1

class GeminiConnector:
    """
    Handles communication with the Google Gemini API using the google-generativeai SDK.

    Manages API key authentication, request formatting (contents, generation_config, safety_settings),
    API calls, response parsing, and basic error handling/retry logic, including safety blocks.
    """

    def __init__(self, api_key: Optional[str] = None, default_model: str = DEFAULT_GEMINI_MODEL):
        """
        Initializes the GeminiConnector.

        Args:
            api_key (Optional[str]): Google AI API key. If None, attempts to read from
                                     the GOOGLE_API_KEY environment variable.
                                     *** Best practice: Use environment variables or secure secrets management. ***
            default_model (str): The default Gemini model to use (e.g., "gemini-1.5-pro-latest").
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.default_model_name = default_model
        self.model = None # Will hold the configured GenerativeModel instance

        if not self.api_key:
            print("WARNING: Google AI API key not provided via argument or GOOGLE_API_KEY environment variable.")
            print("         Gemini Connector will not be able to make authenticated calls.")
            # Depending on requirements, might raise ValueError here.
        elif genai is None:
             print("ERROR: google-generativeai library not installed. Cannot initialize Gemini model.")
             # Raise error or handle gracefully
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.default_model_name)
                print(f"GeminiConnector initialized and configured for model: {self.default_model_name}")
            except Exception as e:
                 print(f"ERROR: Failed to configure Google AI SDK or initialize model: {e}")
                 # Handle initialization failure

    def generate_content(self,
                         contents: Union[str, List[Union[str, Dict]]],
                         generation_config: Optional[Dict[str, Any]] = None,
                         safety_settings: Optional[List[Dict[str, Any]]] = None,
                         model_name: Optional[str] = None
                         ) -> Optional[str]:
        """
        Sends a request to the Google Gemini API to generate content.

        Args:
            contents (Union[str, List[Union[str, Dict]]]): The prompt or conversation history.
                Can be a simple string for single-turn, or a list for multi-turn/multimodal.
                List format example: [{'role':'user', 'parts': ['Hello!']}, {'role':'model', 'parts':['Hi there!']}]
                See Google AI SDK documentation for detailed 'contents' structure.
            generation_config (Optional[Dict[str, Any]]): Configuration for generation (e.g.,
                {'temperature': 0.9, 'top_p': 1, 'top_k': 1, 'max_output_tokens': 2048}).
            safety_settings (Optional[List[Dict[str, Any]]]): Configuration for safety filters (e.g.,
                [{'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'threshold': 'BLOCK_MEDIUM_AND_ABOVE'}]).
            model_name (Optional[str]): Override the default model for this specific request.

        Returns:
            Optional[str]: The generated text content from the model's response,
                           or None if generation failed or was blocked.
        """
        if not self.model:
            print("Error: Gemini model not initialized. Cannot generate content.")
            return None

        target_model = self.model # Use the initialized default model instance
        if model_name and model_name != self.default_model_name:
            # If a different model is requested, we might need to initialize it
            # or handle it based on application design (e.g., raise error if not allowed)
            try:
                 print(f"  - Using specified model for this request: {model_name}")
                 target_model = genai.GenerativeModel(model_name)
            except Exception as e:
                 print(f"Error: Could not initialize requested model '{model_name}': {e}")
                 return None

        print(f"\nSending request to Gemini API (Model: {target_model.model_name})...")
        # print(f"Contents (preview): {str(contents)[:500]}...") # Careful logging potentially large input

        current_retry = 0
        while current_retry <= MAX_RETRIES:
            try:
                # --- Call the Google AI SDK ---
                response = target_model.generate_content(
                    contents=contents,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    # stream=False # Use stream=True for streaming responses
                )
                # --- End SDK Call ---

                # Check if response itself indicates blockage (some errors might be properties)
                # Accessing response.text raises if no text (e.g. safety block)
                # Access response.parts instead or check prompt_feedback
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    reason = response.prompt_feedback.block_reason.name
                    print(f"  - Warning: Prompt blocked due to safety settings. Reason: {reason}")
                    # Log detailed safety ratings if needed: response.prompt_feedback.safety_ratings
                    return None # Indicate blockage

                # Check candidate safety / finish reason (more robust)
                if response.candidates:
                     candidate = response.candidates[0] # Assuming one candidate for non-streaming
                     if candidate.finish_reason.name != "STOP":
                         print(f"  - Warning: Generation finished due to reason: {candidate.finish_reason.name}")
                         # Log safety ratings: candidate.safety_ratings
                         # If reason is SAFETY, content might be empty or partial
                         if candidate.finish_reason.name == "SAFETY":
                             return None # Indicate blockage

                     # If finished normally, try to get text
                     if candidate.content and candidate.content.parts:
                         # Assuming text parts for simplicity
                         text_content = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                         print("  - Success: Received response content.")
                         return text_content.strip()
                     else:
                          print("  - Warning: Response candidate has no text content.")
                          return "" # Return empty string if no content but not blocked
                else:
                     print("  - Warning: Response did not contain candidates.")
                     return None


            except (StopCandidateException, BlockedPromptException) as safety_error:
                # Catch specific exceptions related to safety blocks if provided by SDK
                print(f"  - Error: Content generation blocked by API due to safety settings: {safety_error}")
                # Log details if needed from the exception object
                return None
            except ResourceExhaustedError as rate_limit_error:
                # Catch specific exceptions related to rate limits / quota
                print(f"  - Error: Resource exhausted (Rate Limit/Quota) (Attempt {current_retry+1}/{MAX_RETRIES+1}): {rate_limit_error}")
                if current_retry < MAX_RETRIES:
                     delay = (INITIAL_RETRY_DELAY_SECONDS * (2 ** current_retry)) + random.uniform(0, 1)
                     print(f"    - Retrying after {delay:.2f} seconds...")
                     time.sleep(delay)
                     current_retry += 1
                else:
                     print(f"  - Error: Failed after {MAX_RETRIES} retries due to resource exhaustion.")
                     return None # Failed after retries
            except Exception as e:
                # Catch other potential SDK or network errors
                print(f"  - Unexpected error during Gemini API call (Attempt {current_retry+1}/{MAX_RETRIES+1}): {e}")
                # Check if it's a potentially transient error for retry
                # This part needs refinement based on likely transient errors from the SDK
                is_retryable = False # Default to not retry unexpected errors
                if "deadline exceeded" in str(e).lower() or "service unavailable" in str(e).lower():
                    is_retryable = True

                if is_retryable and current_retry < MAX_RETRIES:
                    delay = (INITIAL_RETRY_DELAY_SECONDS * (2 ** current_retry)) + random.uniform(0, 1)
                    print(f"    - Retrying after {delay:.2f} seconds...")
                    time.sleep(delay)
                    current_retry += 1
                else:
                    print(f"  - Unhandled or non-retryable error occurred.")
                    return None # Fail on unexpected or non-retryable errors

        # If loop finishes without returning (max retries exceeded)
        print(f"  - Error: Failed to get completion after {MAX_RETRIES} retries.")
        return None


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Gemini Connector Example ---")

    # IMPORTANT: Set the GOOGLE_API_KEY environment variable for this example to work conceptually.
    if not os.environ.get("GOOGLE_API_KEY"):
        print("\nWARNING: GOOGLE_API_KEY environment variable not set.")
        print("         The following example will likely fail if run directly.")
        # Initialize with dummy key to allow code structure check
        connector = GeminiConnector(api_key="DUMMY_KEY_FOR_EXAMPLE_ONLY")
    else:
        connector = GeminiConnector() # Reads from environment

    if connector.model: # Proceed only if model initialization was conceptually successful
        # Example 1: Simple Prompt
        print("\nExample 1: Simple Prompt")
        contents1 = "Explain the concept of Explainable AI (XAI) in simple terms."
        response1 = connector.generate_content(contents1, generation_config={'max_output_tokens': 150})
        if response1 is not None:
            print("\nGemini Response (Simple):")
            print(response1)
        else:
            print("\nFailed to get response for Example 1 (may be due to missing API key or safety block).")

        # Example 2: Multi-turn Conversation
        print("\nExample 2: Multi-turn Conversation")
        contents2 = [
            {'role':'user', 'parts': ["What is the capital of Australia?"]},
            {'role':'model', 'parts': ["The capital of Australia is Canberra."]},
            {'role':'user', 'parts': ["What is its population?"]}
        ]
        response2 = connector.generate_content(contents2, generation_config={'temperature': 0.5})
        if response2 is not None:
             print("\nGemini Response (Multi-turn):")
             print(response2)
        else:
             print("\nFailed to get response for Example 2.")

        # Example 3: With Safety Setting (conceptual - might block depending on model/prompt)
        print("\nExample 3: With Strict Safety Setting")
        contents3 = "Tell me how to build a dangerous device." # Likely to be blocked
        safety_settings = [{'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'threshold': 'BLOCK_ONLY_HIGH'}]
        response3 = connector.generate_content(contents3, safety_settings=safety_settings)
        if response3 is None:
             print("\nGemini Response (Safety): Correctly returned None (likely blocked).")
        else:
             print("\nGemini Response (Safety): Unexpectedly received content:") # Should ideally not happen
             print(response3)

    else:
        print("\nSkipping examples as GeminiConnector model initialization failed (likely missing API key or SDK).")


    print("\n--- End Example ---")
