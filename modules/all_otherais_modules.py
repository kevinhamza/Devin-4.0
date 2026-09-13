# # Devin/modules/all_otherais_modules.py
# # Purpose: Provides a conceptual interface for other AI models like Anthropic's Claude
# #          and a generic handler for any OpenAI-compatible API endpoint.
# # Conversation for all other ais 🤝✨

# import logging
# import os
# import uuid
# import json
# from typing import List, Dict, Any, Optional

# # Configure basic logging
# logger = logging.getLogger("AllOtherAIsModule")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class ConceptualAnthropicClaudeModule:
#     """
#     Conceptually interacts with Anthropic's Claude API.
#     Note: The Claude API has a different structure than OpenAI's.
#     It uses a single 'prompt' string with alternating '\n\nHuman:' and '\n\nAssistant:' roles.
#     """
#     def __init__(self, api_key: Optional[str] = None):
#         self.api_key_placeholder = api_key or os.getenv("ANTHROPIC_API_KEY_PLACEHOLDER")
#         self.base_url = "https://api.anthropic.com/v1"
#         self.model_name = "claude-2.1" # Example model
#         logger.info(f"ConceptualAnthropicClaudeModule initialized for model: {self.model_name}")

#     def _format_prompt_for_claude(self, messages: List[Dict[str, str]]) -> str:
#         """Converts OpenAI-style messages to Claude's single-prompt format."""
#         prompt_string = ""
#         for msg in messages:
#             role = msg.get("role")
#             content = msg.get("content")
#             if role == "user":
#                 prompt_string += f"\n\nHuman: {content}"
#             elif role == "assistant":
#                 prompt_string += f"\n\nAssistant: {content}"
#             elif role == "system":
#                 # System prompts are often placed before the first "Human:" turn.
#                 prompt_string = f"{content}{prompt_string}"
#         prompt_string += "\n\nAssistant:" # Prompt the model to respond
#         return prompt_string

#     def get_completion_conceptual(self, messages: List[Dict[str, str]], max_tokens_to_sample: int = 1000, temperature: float = 0.7) -> Optional[str]:
#         """Conceptually gets a completion from Claude."""
#         if not self.api_key_placeholder:
#             logger.error("Cannot get Claude completion: ANTHROPIC_API_KEY_PLACEHOLDER not set.")
#             return "Error: Anthropic API key not configured."

#         full_url = f"{self.base_url}/complete"
#         headers = {
#             "x-api-key": self.api_key_placeholder,
#             "anthropic-version": "2023-06-01",
#             "content-type": "application/json"
#         }
#         prompt = self._format_prompt_for_claude(messages)
#         payload = {
#             "model": self.model_name,
#             "prompt": prompt,
#             "max_tokens_to_sample": max_tokens_to_sample,
#             "temperature": temperature,
#         }

#         logger.info(f"CONCEPTUAL API CALL: POST {full_url}")
#         logger.debug(f"  Payload (conceptual): {json.dumps(payload, indent=2)}")

#         # Simulate response
#         return f"Conceptual response from Anthropic Claude for: '{messages[-1]['content'][:40]}...'"

# class GenericOpenAICompatibleModule:
#     """
#     A generic module to interact with any API that exposes an OpenAI-compatible
#     '/chat/completions' endpoint. Useful for local models (Ollama, vLLM) or other services.
#     """
#     def __init__(self, model_name: str, api_base_url: str, api_key: Optional[str] = "DUMMY_KEY_FOR_LOCAL_MODEL"):
#         self.model_name = model_name
#         self.api_base_url = api_base_url.rstrip('/')
#         self.api_key_placeholder = api_key
#         logger.info(f"GenericOpenAICompatibleModule initialized for model '{model_name}' at base URL '{api_base_url}'")

#     def _conceptual_api_call(self, payload: Dict) -> Dict:
#         """Simulates an API call to a generic OpenAI-compatible endpoint."""
#         full_url = f"{self.api_base_url}/chat/completions"
#         headers = {
#             "Authorization": f"Bearer {self.api_key_placeholder}",
#             "Content-Type": "application/json"
#         }
#         logger.info(f"CONCEPTUAL API CALL: POST {full_url}")
#         logger.debug(f"  Payload (conceptual): {json.dumps(payload, indent=2)}")

#         # Simulate a generic response
#         last_user_message = payload.get("messages", [{}])[-1].get("content", "")
#         return {
#             "id": f"generic-chatcmpl-{uuid.uuid4().hex[:8]}",
#             "object": "chat.completion",
#             "model": self.model_name,
#             "choices": [{
#                 "index": 0,
#                 "message": {
#                     "role": "assistant",
#                     "content": f"Generic response from '{self.model_name}' for: '{last_user_message[:40]}...'"
#                 },
#                 "finish_reason": "stop"
#             }]
#         }

#     def get_chat_completion_content(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
#         """Gets a chat completion from the generic endpoint."""
#         payload = {
#             "model": self.model_name,
#             "messages": messages,
#             **kwargs # Pass through other params like temperature, max_tokens
#         }
#         response = self._conceptual_api_call(payload)
#         if "choices" in response:
#             return response["choices"][0]["message"]["content"]
#         logger.error(f"Error or invalid response from generic endpoint: {response}")
#         return None

# class OtherAIsManager:
#     """

#     Aggregates and provides access to other AI modules not covered by the primary AIAgent,
#     such as Anthropic's Claude or generic/local models.
#     """
#     def __init__(self,
#                  anthropic_api_key: Optional[str] = None,
#                  local_model_config: Optional[Dict[str, Any]] = None):
#         """
#         Initializes the manager for "other" AIs.

#         Args:
#             anthropic_api_key (Optional[str]): API key for Anthropic's Claude.
#             local_model_config (Optional[Dict[str, Any]]): Configuration for a generic
#                 OpenAI-compatible local model. e.g.,
#                 {"model_name": "llama3:instruct", "api_base_url": "http://localhost:11434/v1"}
#         """
#         logger.info("Initializing OtherAIsManager...")
#         self.claude_module = ConceptualAnthropicClaudeModule(api_key=anthropic_api_key)

#         self.local_llm_module = None
#         if local_model_config:
#             self.local_llm_module = GenericOpenAICompatibleModule(
#                 model_name=local_model_config.get("model_name", "local-model"),
#                 api_base_url=local_model_config.get("api_base_url", "http://localhost:8000/v1")
#             )

#         logger.info("OtherAIsManager initialization complete.")

#     def get_claude_response(self, messages: List[Dict[str, str]]) -> Optional[str]:
#         """Convenience method to get a response from the Claude module."""
#         logger.info("Requesting response from Anthropic Claude module.")
#         return self.claude_module.get_completion_conceptual(messages)

#     def get_local_llm_response(self, messages: List[Dict[str, str]]) -> Optional[str]:
#         """Convenience method to get a response from a configured local/generic LLM."""
#         if not self.local_llm_module:
#             logger.error("Local LLM module is not configured.")
#             return "Error: Local LLM not configured."
#         logger.info(f"Requesting response from generic/local LLM: {self.local_llm_module.model_name}")
#         return self.local_llm_module.get_chat_completion_content(messages)

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== All Other AIs Module Prototype 🤝✨ ===")
#     print("=========================================================")

#     # Configuration for a conceptual local model (e.g., via Ollama)
#     local_config = {
#         "model_name": "llama3:8b-instruct-q5_K_M",
#         "api_base_url": "http://localhost:11434/v1" # Ollama's default OpenAI-compatible endpoint
#     }

#     # Initialize the manager
#     other_ais = OtherAIsManager(
#         anthropic_api_key="DUMMY_ANTHROPIC_KEY_FOR_DEMO",
#         local_model_config=local_config
#     )

#     # --- 1. Get a response from Anthropic's Claude (Conceptual) ---
#     print("\n--- Task 1: Get a response from Anthropic Claude ---")
#     prompt_1 = "What are the core principles of constitutional AI?"
#     messages_1 = [
#         {"role": "system", "content": "You are a helpful and harmless AI assistant."},
#         {"role": "user", "content": prompt_1}
#     ]
#     response_1 = other_ais.get_claude_response(messages_1)
#     print(f"  User: {prompt_1}")
#     print(f"  Agent (via Claude): {response_1}")

#     # --- 2. Get a response from a generic/local LLM (Conceptual) ---
#     print("\n--- Task 2: Get a response from a local LLM ---")
#     prompt_2 = "Give me a 3-step plan to set up a basic web server using Python's http.server module."
#     messages_2 = [{"role": "user", "content": prompt_2}]
#     response_2 = other_ais.get_local_llm_response(messages_2)
#     print(f"  User: {prompt_2}")
#     print(f"  Agent (via Local LLM '{local_config['model_name']}'): {response_2}")

#     # --- 3. Demonstrate calling the local LLM without the manager for clarity ---
#     print("\n--- Direct use of GenericOpenAICompatibleModule ---")
#     if other_ais.local_llm_module:
#         direct_local_response = other_ais.local_llm_module.get_chat_completion_content(messages_2)
#         print(f"  Direct call response: {direct_local_response}")

#     print("\n=========================================================")
#     print("=== Other AIs Module Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/all_otherais_modules.py
# Purpose: Provides a functional interface for other AI models like Anthropic's
#          Claude and a generic handler for any OpenAI-compatible API endpoint.

import logging
import os
import json
from typing import List, Dict, Any, Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("AllOtherAIsModule")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class AnthropicClaudeModule:
    """
    Interacts with the live Anthropic Claude API.
    """
    def __init__(self, api_key: Optional[str] = None):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic SDK is required. 'pip install anthropic'")
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set it via ANTHROPIC_API_KEY env var.")
            
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model_name = "claude-3-haiku-20240307" # A fast and capable model
        logger.info(f"AnthropicClaudeModule initialized for model: {self.model_name}")

    def _format_messages_for_claude(self, messages: List[Dict[str, str]]) -> Tuple[Optional[str], List[Dict[str, str]]]:
        """Converts OpenAI-style messages to Claude's format."""
        system_prompt = None
        claude_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if role == "system":
                system_prompt = content
            elif role in ["user", "assistant"]:
                claude_messages.append({"role": role, "content": content})
        return system_prompt, claude_messages

    def get_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1024) -> Optional[str]:
        """Gets a completion from Claude."""
        system_prompt, claude_messages = self._format_messages_for_claude(messages)
        
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                system=system_prompt, # The system prompt is a top-level parameter
                messages=claude_messages
            )
            return response.content[0].text
        except anthropic.APIError as e:
            logger.error(f"Anthropic API Error: {e}")
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"An unexpected error occurred with Anthropic API: {e}")
            return "An unexpected error occurred."


class GenericOpenAICompatibleModule:
    """
    A generic module to interact with any API that exposes an OpenAI-compatible
    '/chat/completions' endpoint.
    """
    def __init__(self, model_name: str, api_base_url: str, api_key: str = "NA"):
        if not OPENAI_AVAILABLE:
            raise ImportError("The 'openai' library is required to use the compatible client. 'pip install openai'")
        
        self.model_name = model_name
        self.client = openai.OpenAI(api_key=api_key, base_url=api_base_url)
        logger.info(f"GenericOpenAICompatibleModule initialized for model '{model_name}' at '{api_base_url}'")

    def get_chat_completion_content(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """Gets a chat completion from the generic endpoint."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except openai.APIError as e:
            logger.error(f"Generic OpenAI-compatible API Error: {e}")
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"An unexpected error occurred with the generic endpoint: {e}")
            return "An unexpected error occurred."


class OtherAIsManager:
    """Aggregates and provides access to other AI modules."""
    def __init__(self,
                 anthropic_api_key: Optional[str] = None,
                 local_model_config: Optional[Dict[str, Any]] = None):
        
        self.claude_module = AnthropicClaudeModule(api_key=anthropic_api_key) if anthropic_api_key else None
        self.local_llm_module = None
        if local_model_config:
            self.local_llm_module = GenericOpenAICompatibleModule(
                model_name=local_model_config["model_name"],
                api_base_url=local_model_config["api_base_url"],
                api_key=local_model_config.get("api_key", "NA")
            )

    def get_claude_response(self, messages: List[Dict[str, str]]) -> Optional[str]:
        if not self.claude_module:
            return "Error: Anthropic Claude module not configured."
        return self.claude_module.get_completion(messages)

    def get_local_llm_response(self, messages: List[Dict[str, str]]) -> Optional[str]:
        if not self.local_llm_module:
            return "Error: Local/Generic LLM module not configured."
        return self.local_llm_module.get_chat_completion_content(messages)

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== All Other AIs Module (Live Integration) 🤝✨ ===")
    print("=========================================================")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Configuration for a local model (e.g., via Ollama)
    # This assumes an Ollama server is running and has the 'llama3' model.
    local_config = {
        "model_name": "llama3",
        "api_base_url": "http://localhost:11434/v1"
    }

    other_ais = OtherAIsManager(
        anthropic_api_key=anthropic_key,
        local_model_config=local_config
    )

    # --- 1. Get a response from Anthropic's Claude (Live) ---
    print("\n--- 1. Task: Get a response from Anthropic Claude ---")
    if other_ais.claude_module:
        prompt_1 = "Explain the concept of 'prompt engineering' in two sentences."
        messages_1 = [{"role": "user", "content": prompt_1}]
        response_1 = other_ais.get_claude_response(messages_1)
        print(f"  > Prompt: {prompt_1}")
        print(f"  < Live Claude Response:\n    {response_1}")
    else:
        print("  Skipping: ANTHROPIC_API_KEY not set.")

    # --- 2. Get a response from a generic/local LLM (Live) ---
    print("\n\n--- 2. Task: Get a response from a local LLM (e.g., Ollama) ---")
    if other_ais.local_llm_module:
        prompt_2 = "Write a bash command to find all files in the current directory that have been modified in the last 24 hours."
        messages_2 = [{"role": "user", "content": prompt_2}]
        print(f"  > Prompt: {prompt_2}")
        print("  (Connecting to local model, this may take a moment...)")
        response_2 = other_ais.get_local_llm_response(messages_2)
        print(f"  < Live Local LLM Response:\n    {response_2}")
    else:
        print("  Skipping: Local LLM is not configured in this script.")
        
    print("\n=========================================================")
    print("=== Other AIs Module Prototype Complete ===")
    print("=========================================================")
