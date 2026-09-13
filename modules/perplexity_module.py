# # Devin/modules/perplexity_module.py
# # Purpose: Handles conceptual interactions with Perplexity AI's API,
# #          focusing on conversational search and sourced answers.
# # Perplexity AI conversation & search 🌐💡

# import logging
# import os
# import uuid
# import json # For simulating request/response structures
# import random
# from datetime import datetime, timezone
# from typing import List, Dict, Any, Optional, Union
# from dataclasses import dataclass, field

# # Configure basic logging
# logger = logging.getLogger("PerplexityModule")
# if not logger.handlers: # Prevent duplicate handlers
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# @dataclass
# class PerplexityChatConfig:
#     """
#     Configuration for Perplexity API chat completion calls.
#     Many parameters are similar to OpenAI's.
#     """
#     model: str = "llama-3-sonar-small-32k-online" # Perplexity's online model for sourced answers
#     temperature: Optional[float] = 0.7
#     max_tokens: Optional[int] = 1024
#     top_p: Optional[float] = None # e.g., 0.9
#     # top_k: Optional[int] = None # Perplexity API might not use top_k for chat directly, focus on OpenAI compat
#     frequency_penalty: Optional[float] = 0.0
#     presence_penalty: Optional[float] = 0.0
#     # stream: bool = False # Streaming would require different handling

# class PerplexityModule:
#     """
#     Conceptually interacts with Perplexity AI's API.
#     Perplexity's API is OpenAI-compatible for chat completions.
#     In a real application, this would use 'requests' or the 'openai' library (configured for PPLX endpoint)
#     and require a Perplexity API key.
#     """
#     DEFAULT_MODEL = "llama-3-sonar-small-32k-online" # Known for good search-augmented responses

#     def __init__(self, api_key: Optional[str] = None):
#         """
#         Initializes the PerplexityModule.

#         Args:
#             api_key (Optional[str]): Perplexity API key. If None, attempts to read from
#                                      PERPLEXITY_API_KEY_PLACEHOLDER environment variable.
#         """
#         self.api_key_placeholder = api_key or os.getenv("PERPLEXITY_API_KEY_PLACEHOLDER")
#         self.base_url = "https://api.perplexity.ai" # Official API endpoint

#         if not self.api_key_placeholder:
#             logger.warning(
#                 "Perplexity API key not provided via argument or PERPLEXITY_API_KEY_PLACEHOLDER env var. "
#                 "This module will only perform conceptual operations."
#             )
#         logger.info(f"PerplexityModule initialized. Conceptual API Key ending: ...{self.api_key_placeholder[-4:] if self.api_key_placeholder else 'N/A'}")

#     def _get_conceptual_headers(self) -> Dict[str, str]:
#         """Returns conceptual headers for Perplexity API calls."""
#         headers = {"Content-Type": "application/json"}
#         if self.api_key_placeholder:
#             headers["Authorization"] = f"Bearer {self.api_key_placeholder}"
#         return headers

#     def _conceptual_api_call(self, endpoint_path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Simulates making an API call to Perplexity AI.
#         The response structure is OpenAI-compatible.
#         """
#         full_url = f"{self.base_url}{endpoint_path}"
#         headers = self._get_conceptual_headers()
        
#         log_payload_summary = json.dumps(payload, indent=2)[:300] + "..." if len(json.dumps(payload)) > 300 else json.dumps(payload, indent=2)

#         logger.info(f"CONCEPTUAL API CALL: POST {full_url}")
#         logger.debug(f"  Headers (conceptual): {headers}")
#         logger.debug(f"  Payload (conceptual): {log_payload_summary}")

#         # --- Simulate API Response (OpenAI-compatible structure) ---
#         if endpoint_path == "/chat/completions":
#             if not payload or "messages" not in payload:
#                 return {"error": {"message": "Missing 'messages' in payload.", "type": "invalid_request_error", "code": "missing_messages"}}
            
#             last_user_message = ""
#             for msg in reversed(payload.get("messages", [])):
#                 if msg.get("role") == "user":
#                     last_user_message = msg.get("content", "")
#                     break
            
#             sim_response_content = f"Simulated Perplexity AI response to: '{last_user_message[:50]}...'. This answer would typically include citations."
#             if "latest developments in AI regulation" in last_user_message.lower():
#                  sim_response_content = (
#                      "Recent AI regulation developments include the EU AI Act moving towards implementation, "
#                      "discussions on watermarking AI-generated content, and ongoing national strategy updates. [1][2]\n\n"
#                      "Sources (conceptual):\n[1] European Parliament News - EU AI Act\n[2] White House OSTP - AI Bill of Rights"
#                  )
#             elif "who won the world cup 2022" in last_user_message.lower():
#                 sim_response_content = "Argentina won the FIFA World Cup in 2022. [Source: FIFA Official Website (conceptual)]"


#             return {
#                 "id": f"pplx-chatcmpl-{uuid.uuid4().hex}",
#                 "object": "chat.completion",
#                 "created": int(datetime.now(timezone.utc).timestamp()),
#                 "model": payload.get("model", self.DEFAULT_MODEL),
#                 "choices": [{
#                     "index": 0,
#                     "message": {"role": "assistant", "content": sim_response_content},
#                     "finish_reason": "stop" # Could also be "length", "tool_calls" etc.
#                 }],
#                 "usage": {"prompt_tokens": random.randint(20,100), "completion_tokens": random.randint(50,300), "total_tokens": random.randint(70,400)} 
#             }
#         else:
#             return {"error": {"message": f"Unknown conceptual Perplexity endpoint: {endpoint_path}", "type": "not_found_error", "code": "endpoint_not_found"}}

#     def get_chat_completion(self,
#                             messages: List[Dict[str, str]],
#                             config: Optional[PerplexityChatConfig] = None
#                             ) -> Optional[Dict[str, Any]]: # Returns the full conceptual choice object or error dict
#         """
#         Conceptually gets a chat completion from Perplexity AI.
#         The response is an OpenAI-compatible dictionary.

#         Args:
#             messages: A list of message objects in OpenAI format.
#             config: Configuration for the API call. Uses defaults if None.

#         Returns:
#             Optional[Dict[str, Any]]: The conceptual 'choice' object containing the assistant's
#                                       message and other info, or an error dictionary, or None if API key missing.
#         """
#         if not self.api_key_placeholder:
#             logger.error("Cannot get chat completion: Perplexity API key placeholder is not set.")
#             return {"error": {"message": "API key not configured for Perplexity.", "type": "authentication_error"}}

#         current_config = config or PerplexityChatConfig()
        
#         payload = {
#             "model": current_config.model,
#             "messages": messages,
#         }
#         # Add optional parameters if they are not None
#         if current_config.temperature is not None: payload["temperature"] = current_config.temperature
#         if current_config.max_tokens is not None: payload["max_tokens"] = current_config.max_tokens
#         if current_config.top_p is not None: payload["top_p"] = current_config.top_p
#         if current_config.frequency_penalty is not None: payload["frequency_penalty"] = current_config.frequency_penalty
#         if current_config.presence_penalty is not None: payload["presence_penalty"] = current_config.presence_penalty
#         # if current_config.stream: payload["stream"] = True # Requires different response handling

#         response_data = self._conceptual_api_call(endpoint_path="/chat/completions", payload=payload)
        
#         if "error" in response_data:
#             logger.error(f"Conceptual API Error (Perplexity Chat Completion): {response_data['error']}")
#             return response_data # Return the error dict
        
#         try:
#             # Return the first choice object, which contains the message and finish_reason
#             return response_data["choices"][0] 
#         except (KeyError, IndexError, TypeError) as e:
#             logger.error(f"Error parsing conceptual Perplexity chat completion response: {e}. Response: {response_data}")
#             return {"error": {"message": "Could not parse conceptual Perplexity response.", "type": "api_error"}}

#     def get_chat_completion_content(self,
#                                     messages: List[Dict[str, str]],
#                                     config: Optional[PerplexityChatConfig] = None
#                                     ) -> Optional[str]:
#         """
#         Convenience method to get only the text content from Perplexity AI chat completion.
#         """
#         choice_object = self.get_chat_completion(messages, config)
#         if choice_object and "message" in choice_object and "content" in choice_object["message"]:
#             return choice_object["message"]["content"]
#         elif choice_object and "error" in choice_object: # Pass through error message
#              return f"Error: {choice_object['error'].get('message', 'Unknown API error')}"
#         return None


# # Example Usage
# if __name__ == "__main__":
#     print("================================================================")
#     print("=== Perplexity Module Prototype (Conceptual API Calls) 🌐💡 ===")
#     print("================================================================")

#     if not os.getenv("PERPLEXITY_API_KEY_PLACEHOLDER"):
#         print("INFO: PERPLEXITY_API_KEY_PLACEHOLDER environment variable not set. Using dummy key for conceptual demo.")
    
#     # Use a dummy key if real one isn't set for conceptual demo
#     module = PerplexityModule(api_key="DUMMY_PPLX_KEY_FOR_CONCEPTUAL_DEMO_98765")

#     # --- 1. Conversational Search Example ---
#     print("\n--- Conversational Search Example ---")
#     messages_search = [
#         {"role": "system", "content": "You are an AI assistant that provides accurate and sourced information."},
#         {"role": "user", "content": "What were the latest major developments in AI regulation in early 2024?"}
#     ]
#     # Using a Perplexity online model known for search
#     search_config = PerplexityChatConfig(model="llama-3-sonar-large-32k-online", temperature=0.3, max_tokens=500)
    
#     # Get the full choice object
#     search_choice_obj = module.get_chat_completion(messages_search, config=search_config)
    
#     if search_choice_obj and "error" not in search_choice_obj:
#         response_content = search_choice_obj.get("message", {}).get("content")
#         finish_reason = search_choice_obj.get("finish_reason")
#         print(f"  Conceptual Perplexity Response (Content):\n    {response_content}")
#         print(f"  Finish Reason: {finish_reason}")
#     elif search_choice_obj and "error" in search_choice_obj:
#         print(f"  Error from Perplexity API (conceptual): {search_choice_obj['error']}")
#     else:
#         print("  Failed to get a conceptual response from Perplexity API.")
#     print("")

#     # --- 2. General Question Example using convenience method ---
#     print("\n--- General Question Example ---")
#     messages_general = [
#         {"role": "user", "content": "Explain the concept of 'zero-shot learning' in simple terms."}
#     ]
#     general_config = PerplexityChatConfig(model="llama-3-sonar-small-32k-online", temperature=0.7)
#     general_response_content = module.get_chat_completion_content(messages_general, config=general_config)
#     print(f"  Conceptual Perplexity Response Content:\n    {general_response_content}\n")

#     # --- 3. Example with a different model (conceptual open-source model via Perplexity) ---
#     print("\n--- Example with a different (conceptual open-source) model ---")
#     messages_creative = [
#         {"role": "user", "content": "Write a very short poem about a curious robot."}
#     ]
#     # Perplexity also hosts open-source models, e.g., Llama, Mixtral.
#     # The 'online' models are typically better for sourced/current info.
#     creative_config = PerplexityChatConfig(model="mixtral-8x7b-instruct", temperature=0.8, max_tokens=100) 
#     creative_response_content = module.get_chat_completion_content(messages_creative, config=creative_config)
#     print(f"  Conceptual Perplexity Response (Creative Task):\n    {creative_response_content}\n")


#     print("\n================================================================")
#     print("=== Perplexity Module Prototype Complete ===")
#     print("================================================================")

# # Devin/modules/perplexity_module.py
# # Purpose: A fully functional client for interacting with the Perplexity AI API,
# #          focusing on conversational search and sourced answers.

# import logging
# import os
# import json
# import request
# from dataclasses import dataclass
# from typing import List, Dict, Optional, Any

# try:
#     import openai
#     from openai import OpenAI
#     OPENAI_AVAILABLE = True
# except ImportError:
#     OPENAI_AVAILABLE = False


# # Configure basic logging
# logger = logging.getLogger("PerplexityModule")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# @dataclass
# class PerplexityChatConfig:
#     """
#     Configuration for Perplexity API chat completion calls.
#     """
#     model: str = "llama-3-sonar-large-32k-online"
#     temperature: Optional[float] = 0.7
#     max_tokens: Optional[int] = 1024

# class PerplexityModule:
#     """
#     Interacts with the live Perplexity AI API using an OpenAI-compatible client.
#     """
#     def __init__(self, api_key: Optional[str] = None):
#         if not OPENAI_AVAILABLE:
#             raise ImportError("The 'openai' library is required. 'pip install openai'")
        
#         self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
#         if not self.api_key:
#             raise ValueError("Perplexity API key is required. Set it via the PERPLEXITY_API_KEY environment variable.")
            
#         # The key is to override the base_url to point to Perplexity's API
#         self.client = OpenAI(
#             api_key=self.api_key,
#             base_url="https://api.perplexity.ai"
#         )
#         logger.info("PerplexityModule initialized with live Perplexity API client.")

#     def get_chat_completion(self, messages: List[Dict[str, str]], config: Optional[PerplexityChatConfig] = None) -> Optional[Dict[str, Any]]:
#         """
#         Gets a chat completion from Perplexity AI.

#         Returns:
#             The 'choice' object from the API response, or an error dictionary.
#         """
#         current_config = config or PerplexityChatConfig()
#         logger.info(f"Requesting chat completion with model {current_config.model}...")
        
#         try:
#             response = self.client.chat.completions.create(
#                 model=current_config.model,
#                 messages=messages,
#                 temperature=current_config.temperature,
#                 max_tokens=current_config.max_tokens,
#             )
#             return response.choices[0]
#         except openai.APIError as e:
#             logger.error(f"Perplexity API Error (Chat Completion): {e}")
#             return {"error": {"message": str(e), "type": "api_error"}}
#         except Exception as e:
#             logger.error(f"An unexpected error occurred during chat completion: {e}")
#             return {"error": {"message": "An unexpected error occurred.", "type": "client_error"}}

#     def get_chat_completion_content(self, messages: List[Dict[str, str]], config: Optional[PerplexityChatConfig] = None) -> Optional[str]:
#         """
#         Convenience method to get only the text content from a chat completion.
#         """
#         choice_object = self.get_chat_completion(messages, config)
#         if choice_object and "message" in choice_object and "content" in choice_object.message:
#             return choice_object.message.content
#         elif choice_object and "error" in choice_object:
#              return f"Error: {choice_object['error'].get('message', 'Unknown API error')}"
#         return None

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Integrated Perplexity Module (Live API Calls) 🌐💡 ===")
#     print("=========================================================")

#     if not os.getenv("PERPLEXITY_API_KEY"):
#         print("\nERROR: PERPLEXITY_API_KEY environment variable is not set. This demo requires a live API key.")
#     else:
#         module = PerplexityModule()

#         # --- 1. Conversational Search Example ---
#         print("\n--- 1. Live Conversational Search Example ---")
#         messages_search = [
#             {"role": "system", "content": "You are an AI assistant that provides accurate and sourced information."},
#             {"role": "user", "content": "What were the key findings of the Artemis I mission?"}
#         ]
        
#         search_response_content = module.get_chat_completion_content(messages_search)
#         print(f"Live Perplexity Response:\n---\n{search_response_content}\n---")

#         # --- 2. General Question Example ---
#         print("\n--- 2. Live General Question Example ---")
#         messages_general = [
#             {"role": "user", "content": "Explain the difference between a VPN and a proxy server in simple terms."}
#         ]
#         general_response_content = module.get_chat_completion_content(messages_general)
#         print(f"Live Perplexity Response:\n---\n{general_response_content}\n---")

#     print("\n=========================================================")
#     print("=== Perplexity Module Prototype Complete ===")
#     print("=========================================================")












# Devin/modules/perplexity_module.py
# Purpose: A fully functional, native client for interacting with the Perplexity AI API,
#          focusing on conversational search, sourced answers, and streaming.

import logging
import os
import json
import requests
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any, Iterator

# Configure basic logging
logger = logging.getLogger("PerplexityModule")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

@dataclass
class PerplexityChatConfig:
    """
    Expanded configuration for Perplexity API chat completion calls.
    """
    model: str = "llama-3-sonar-large-32k-online" # Search-enabled model
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = 1024
    frequency_penalty: Optional[float] = 0.0

class PerplexityModule:
    """
    Interacts with the live Perplexity AI API using native HTTP requests.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("Perplexity API key is required. Set it via the PERPLEXITY_API_KEY environment variable.")
            
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        logger.info("PerplexityModule initialized with live Perplexity API client.")

    def get_chat_completion_content(self, messages: List[Dict[str, str]], config: Optional[PerplexityChatConfig] = None) -> Optional[str]:
        """
        Gets a standard (non-streaming) chat completion from Perplexity AI.
        """
        current_config = config or PerplexityChatConfig()
        
        # Prepare payload from dataclass, removing None values
        payload = asdict(current_config)
        payload = {k: v for k, v in payload.items() if v is not None}
        payload["messages"] = messages
        
        logger.info(f"Requesting chat completion with model {current_config.model}...")
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
            
            response_data = response.json()
            return response_data['choices'][0]['message']['content']
            
        except requests.HTTPError as e:
            logger.error(f"Perplexity API HTTP Error: {e.response.status_code} - {e.response.text}")
            return f"Error: Perplexity API call failed. Details: {e.response.text}"
        except requests.RequestException as e:
            logger.error(f"Network error during Perplexity request: {e}")
            return f"Error: Network error. Details: {e}"
        except Exception as e:
            logger.error(f"An unexpected error occurred during chat completion: {e}")
            return "An unexpected error occurred."

    # --- ADDED FEATURE: Streaming Chat Response ---
    def get_chat_completion_stream(self, messages: List[Dict[str, str]], config: Optional[PerplexityChatConfig] = None) -> Iterator[str]:
        """
        Gets a streaming chat completion, yielding content chunks as they arrive.
        """
        current_config = config or PerplexityChatConfig()
        
        payload = asdict(current_config)
        payload = {k: v for k, v in payload.items() if v is not None}
        payload["messages"] = messages
        payload["stream"] = True
        
        logger.info(f"Requesting STREAMING chat completion with model {current_config.model}...")
        try:
            with requests.post(self.api_url, headers=self.headers, json=payload, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data: '):
                            # Remove the 'data: ' prefix and parse the JSON
                            json_str = decoded_line[6:]
                            if json_str.strip() == "[DONE]":
                                break
                            
                            chunk_data = json.loads(json_str)
                            delta = chunk_data['choices'][0].get('delta', {})
                            content = delta.get('content')
                            if content:
                                yield content
        except Exception as e:
            logger.error(f"An error occurred during streaming chat completion: {e}")
            yield f"Error: An unexpected error occurred during streaming. Details: {e}"

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Perplexity Module (Live API Calls) 🌐💡 ===")
    print("=========================================================")

    if not os.getenv("PERPLEXITY_API_KEY"):
        print("\nERROR: PERPLEXITY_API_KEY environment variable is not set. This demo requires a live API key.")
    else:
        module = PerplexityModule()

        # --- 1. Conversational Search Example (Unchanged) ---
        print("\n--- 1. Live Conversational Search Example ---")
        messages_search = [
            {"role": "system", "content": "You are an AI assistant that provides accurate and sourced information."},
            {"role": "user", "content": "What were the key findings of the Artemis I mission?"}
        ]
        
        search_response_content = module.get_chat_completion_content(messages_search)
        print(f"Live Perplexity Response:\n---\n{search_response_content}\n---")

        # --- 2. General Question Example (Unchanged) ---
        print("\n--- 2. Live General Question Example ---")
        messages_general = [
            {"role": "user", "content": "Explain the difference between a VPN and a proxy server in simple terms."}
        ]
        general_response_content = module.get_chat_completion_content(messages_general)
        print(f"Live Perplexity Response:\n---\n{general_response_content}\n---")

        # --- 3. ADDED DEMO: Live Streaming Example ---
        print("\n--- 3. Live Streaming Example ---")
        stream_messages = [
            {"role": "system", "content": "Be brief and concise."},
            {"role": "user", "content": "List the first three planets of our solar system."}
        ]
        
        print("Streaming Perplexity Response:")
        full_response = ""
        for chunk in module.get_chat_completion_stream(stream_messages):
            print(chunk, end="", flush=True)
            full_response += chunk
        print("\n--- End of Stream ---")

    print("\n=========================================================")
    print("=== Perplexity Module Demonstration Complete ===")
    print("=========================================================")
