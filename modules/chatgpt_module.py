# # Devin/modules/chatgpt_module.py
# # Purpose: Handles conceptual interactions with OpenAI's ChatGPT (GPT models),
# #          DALL-E for image generation, and embedding models.
# # Chatgpt conversation file 🤖🎨

# import logging
# import os
# import uuid
# import json # For simulating request/response structures
# from datetime import datetime, timezone
# from typing import List, Dict, Any, Optional, Union
# from dataclasses import dataclass, field

# # Configure basic logging
# logger = logging.getLogger("ChatGPTModule")
# if not logger.handlers: # Prevent duplicate handlers
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# @dataclass
# class OpenAIChatCompletionConfig:
#     """Configuration for OpenAI Chat Completion API calls."""
#     model: str = "gpt-4o" # Default to a capable model
#     temperature: float = 0.7
#     max_tokens: int = 2048
#     top_p: float = 1.0
#     frequency_penalty: float = 0.0
#     presence_penalty: float = 0.0
#     # stream: bool = False # Streaming would require more complex handling

# @dataclass
# class DalleConfig:
#     """Configuration for OpenAI DALL-E API calls."""
#     model: str = "dall-e-3" # Or "dall-e-2"
#     n: int = 1 # Number of images to generate
#     size: str = "1024x1024" # Supported sizes vary by model
#     quality: Optional[str] = "standard" # "standard" or "hd" for dall-e-3
#     style: Optional[str] = "vivid" # "vivid" or "natural" for dall-e-3
#     response_format: str = "url" # or "b64_json"

# @dataclass
# class OpenAIEmbeddingConfig:
#     """Configuration for OpenAI Embedding API calls."""
#     model: str = "text-embedding-3-small" # Common embedding model
#     # encoding_format: Optional[str] = "float" # or "base64"
#     # dimensions: Optional[int] = None # For newer models

# class ChatGPTModule:
#     """
#     Conceptually interacts with OpenAI APIs for chat, image generation, and embeddings.
#     In a real application, this would use the 'openai' Python library and require an API key.
#     """
#     DEFAULT_CHAT_MODEL = "gpt-4o" # Class level default
#     DEFAULT_DALLE_MODEL = "dall-e-3"
#     DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

#     def __init__(self, api_key: Optional[str] = None, organization_id: Optional[str] = None):
#         """
#         Initializes the ChatGPTModule.

#         Args:
#             api_key (Optional[str]): OpenAI API key. If None, attempts to read from
#                                      OPENAI_API_KEY_PLACEHOLDER environment variable.
#             organization_id (Optional[str]): OpenAI organization ID (optional).
#         """
#         self.api_key_placeholder = api_key or os.getenv("OPENAI_API_KEY_PLACEHOLDER")
#         self.organization_id_placeholder = organization_id or os.getenv("OPENAI_ORGANIZATION_ID_PLACEHOLDER")
#         self.base_url = "https://api.openai.com/v1"

#         if not self.api_key_placeholder:
#             logger.warning(
#                 "OpenAI API key not provided via argument or OPENAI_API_KEY_PLACEHOLDER env var. "
#                 "This module will only perform conceptual operations."
#             )
#         logger.info(f"ChatGPTModule initialized. Conceptual API Key ending: ...{self.api_key_placeholder[-4:] if self.api_key_placeholder else 'N/A'}")

#     def _get_conceptual_headers(self) -> Dict[str, str]:
#         """Returns conceptual headers for OpenAI API calls."""
#         headers = {"Content-Type": "application/json"}
#         if self.api_key_placeholder:
#             headers["Authorization"] = f"Bearer {self.api_key_placeholder}"
#         if self.organization_id_placeholder:
#             headers["OpenAI-Organization"] = self.organization_id_placeholder
#         return headers

#     def _conceptual_api_call(self, method: str, endpoint_path: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
#         """
#         Simulates making an API call to OpenAI.
#         In a real system, this would use `requests.request(...)` or the `openai` library.
#         """
#         full_url = f"{self.base_url}{endpoint_path}"
#         headers = self._get_conceptual_headers()
        
#         log_payload_summary = json.dumps(payload, indent=2)[:300] + "..." if payload and len(json.dumps(payload))>300 else json.dumps(payload, indent=2)

#         logger.info(f"CONCEPTUAL API CALL: {method.upper()} {full_url}")
#         logger.debug(f"  Headers (conceptual): {headers}")
#         logger.debug(f"  Payload (conceptual): {log_payload_summary}")

#         # --- Simulate API Response based on endpoint ---
#         # This is highly simplified. Real error handling and response parsing are complex.
#         if endpoint_path.startswith("/chat/completions"):
#             if not payload or "messages" not in payload:
#                 return {"error": {"message": "Missing 'messages' in payload.", "type": "invalid_request_error"}}
            
#             last_user_message = ""
#             for msg in reversed(payload.get("messages", [])):
#                 if msg.get("role") == "user":
#                     last_user_message = msg.get("content", "")
#                     break
            
#             sim_response_content = f"Simulated ChatGPT response to: '{last_user_message[:50]}...'"
#             if "weather" in last_user_message.lower():
#                  sim_response_content = "The weather today is simulated to be sunny with a chance of conceptual clouds."
#             elif "code" in last_user_message.lower():
#                  sim_response_content = "```python\nprint('Hello from simulated ChatGPT!')\n```"


#             return {
#                 "id": f"chatcmpl-{uuid.uuid4().hex}",
#                 "object": "chat.completion",
#                 "created": int(datetime.now(timezone.utc).timestamp()),
#                 "model": payload.get("model", self.DEFAULT_CHAT_MODEL),
#                 "choices": [{
#                     "index": 0,
#                     "message": {"role": "assistant", "content": sim_response_content},
#                     "finish_reason": "stop"
#                 }],
#                 "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70} # Dummy usage
#             }
#         elif endpoint_path.startswith("/images/generations"):
#             prompt = payload.get("prompt", "a conceptual image")
#             n = payload.get("n", 1)
#             sim_urls = [f"https://simulated.openai.com/dalle_img_{uuid.uuid4().hex[:8]}.png" for _ in range(n)]
#             return {
#                 "created": int(datetime.now(timezone.utc).timestamp()),
#                 "data": [{"url": url} for url in sim_urls]
#             }
#         elif endpoint_path.startswith("/embeddings"):
#             input_text = payload.get("input", "")
#             sim_embedding = [random.uniform(-1.0, 1.0) for _ in range(1536)] # text-embedding-ada-002 dim
#             return {
#                 "object": "list",
#                 "data": [{"object": "embedding", "embedding": sim_embedding, "index": 0}],
#                 "model": payload.get("model", self.DEFAULT_EMBEDDING_MODEL),
#                 "usage": {"prompt_tokens": len(input_text.split()), "total_tokens": len(input_text.split())}
#             }
#         else:
#             return {"error": {"message": f"Unknown conceptual endpoint: {endpoint_path}", "type": "invalid_request_error"}}

#     def get_chat_completion(self,
#                             messages: List[Dict[str, str]],
#                             config: Optional[OpenAIChatCompletionConfig] = None
#                             ) -> Optional[str]:
#         """
#         Conceptually gets a chat completion from an OpenAI GPT model.

#         Args:
#             messages: A list of message objects, e.g.,
#                       [{"role": "system", "content": "You are helpful."},
#                        {"role": "user", "content": "Hello!"}]
#             config: Configuration for the API call. Uses defaults if None.

#         Returns:
#             Optional[str]: The content of the assistant's response, or None on error.
#         """
#         if not self.api_key_placeholder:
#             logger.error("Cannot get chat completion: OpenAI API key placeholder is not set.")
#             return "Error: API key not configured."

#         current_config = config or OpenAIChatCompletionConfig()
        
#         payload = {
#             "model": current_config.model,
#             "messages": messages,
#             "temperature": current_config.temperature,
#             "max_tokens": current_config.max_tokens,
#             "top_p": current_config.top_p,
#             "frequency_penalty": current_config.frequency_penalty,
#             "presence_penalty": current_config.presence_penalty,
#             # "stream": current_config.stream # Would require different handling
#         }
        
#         response_data = self._conceptual_api_call(method="POST", endpoint_path="/chat/completions", payload=payload)
        
#         if "error" in response_data:
#             logger.error(f"Conceptual API Error (Chat Completion): {response_data['error']}")
#             return f"Error: {response_data['error'].get('message', 'Unknown API error')}"
        
#         try:
#             return response_data["choices"][0]["message"]["content"]
#         except (KeyError, IndexError, TypeError) as e:
#             logger.error(f"Error parsing conceptual chat completion response: {e}. Response: {response_data}")
#             return "Error: Could not parse conceptual LLM response."

#     def generate_image_with_dalle_conceptual(self,
#                                              prompt: str,
#                                              config: Optional[DalleConfig] = None
#                                              ) -> Optional[List[str]]:
#         """
#         Conceptually generates images using OpenAI's DALL-E.

#         Args:
#             prompt: The text prompt for image generation.
#             config: Configuration for the DALL-E API call.

#         Returns:
#             Optional[List[str]]: A list of conceptual URLs to the generated images, or None on error.
#         """
#         if not self.api_key_placeholder:
#             logger.error("Cannot generate image: OpenAI API key placeholder is not set.")
#             return None # Or ["Error: API key not configured."]

#         current_config = config or DalleConfig()

#         payload = {
#             "model": current_config.model,
#             "prompt": prompt,
#             "n": current_config.n,
#             "size": current_config.size,
#             "quality": current_config.quality,
#             "style": current_config.style,
#             "response_format": current_config.response_format
#         }
#         # Remove None values for quality/style if not dall-e-3 or if user didn't set
#         if current_config.model != "dall-e-3":
#             payload.pop("quality", None)
#             payload.pop("style", None)
#         if payload.get("quality") is None: payload.pop("quality", None)
#         if payload.get("style") is None: payload.pop("style", None)

#         response_data = self._conceptual_api_call(method="POST", endpoint_path="/images/generations", payload=payload)

#         if "error" in response_data:
#             logger.error(f"Conceptual API Error (DALL-E): {response_data['error']}")
#             return None
        
#         try:
#             if current_config.response_format == "url":
#                 return [item["url"] for item in response_data.get("data", [])]
#             elif current_config.response_format == "b64_json":
#                 # Would return list of b64 strings conceptually
#                 return [f"conceptual_b64_image_data_{i+1}" for i in range(current_config.n)]
#         except (KeyError, IndexError, TypeError) as e:
#             logger.error(f"Error parsing conceptual DALL-E response: {e}. Response: {response_data}")
#         return None

#     def create_embedding_conceptual(self,
#                                     input_text: Union[str, List[str]],
#                                     config: Optional[OpenAIEmbeddingConfig] = None
#                                     ) -> Optional[Union[List[float], List[List[float]]]]:
#         """
#         Conceptually creates embeddings for input text using OpenAI models.

#         Args:
#             input_text: The text string or list of strings to embed.
#             config: Configuration for the Embedding API call.

#         Returns:
#             Optional: A list of floats (for single string input) or a list of lists of floats
#                       (for list of strings input), or None on error.
#         """
#         if not self.api_key_placeholder:
#             logger.error("Cannot create embedding: OpenAI API key placeholder is not set.")
#             return None

#         current_config = config or OpenAIEmbeddingConfig()
        
#         payload = {
#             "input": input_text,
#             "model": current_config.model,
#             # "encoding_format": current_config.encoding_format, # If used
#             # "dimensions": current_config.dimensions, # If used
#         }
#         # if payload.get("encoding_format") is None: payload.pop("encoding_format",None)
#         # if payload.get("dimensions") is None: payload.pop("dimensions",None)

#         response_data = self._conceptual_api_call(method="POST", endpoint_path="/embeddings", payload=payload)

#         if "error" in response_data:
#             logger.error(f"Conceptual API Error (Embeddings): {response_data['error']}")
#             return None
        
#         try:
#             embeddings_data = response_data.get("data", [])
#             if isinstance(input_text, str): # Single string input
#                 return embeddings_data[0]["embedding"] if embeddings_data else None
#             else: # List of strings input
#                 return [item["embedding"] for item in embeddings_data]
#         except (KeyError, IndexError, TypeError) as e:
#             logger.error(f"Error parsing conceptual embedding response: {e}. Response: {response_data}")
#         return None


# # Example Usage
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== ChatGPT Module Prototype (Conceptual API Calls) 🤖🎨 ===")
#     print("=========================================================")

#     # Simulate having an API key for conceptual calls
#     # For real use, set OPENAI_API_KEY_PLACEHOLDER environment variable or pass api_key
#     if not os.getenv("OPENAI_API_KEY_PLACEHOLDER"):
#         print("INFO: OPENAI_API_KEY_PLACEHOLDER environment variable not set. Using dummy key for conceptual demo.")
    
#     # Use a dummy key for this conceptual demo if real one isn't set (prevents errors if logic depends on it)
#     module = ChatGPTModule(api_key="DUMMY_SK_FOR_CONCEPTUAL_DEMO_ONLY_12345")

#     # --- 1. Chat Completion Example ---
#     print("\n--- Chat Completion Example ---")
#     messages_chat = [
#         {"role": "system", "content": "You are Devin, a helpful AI planning assistant for software projects."},
#         {"role": "user", "content": "What are the first three steps to start a new Python project?"}
#     ]
#     chat_config = OpenAIChatCompletionConfig(model="gpt-3.5-turbo", temperature=0.5, max_tokens=150)
#     chat_response = module.get_chat_completion(messages_chat, config=chat_config)
#     print(f"  Conceptual ChatGPT Response:\n    {chat_response}\n")

#     messages_code = [
#         {"role": "user", "content": "Write a simple Python function to add two numbers."}
#     ]
#     code_response = module.get_chat_completion(messages_code) # Use default config
#     print(f"  Conceptual Code Response:\n    {code_response}\n")

#     # --- 2. DALL-E Image Generation Example ---
#     print("\n--- DALL-E Image Generation Example ---")
#     dalle_prompt = "A futuristic robot programming at a holographic computer, digital art style"
#     dalle_config = DalleConfig(n=1, size="1024x1024", model="dall-e-3", style="vivid")
#     image_urls = module.generate_image_with_dalle_conceptual(dalle_prompt, config=dalle_config)
#     if image_urls:
#         print(f"  Conceptual DALL-E Image URLs:")
#         for url in image_urls:
#             print(f"    - {url}")
#     else:
#         print("  Conceptual DALL-E image generation failed or returned no URLs.")
#     print("")

#     # --- 3. Embedding Creation Example ---
#     print("\n--- Embedding Creation Example ---")
#     text_to_embed = "Devin is an AI software engineer."
#     embedding_config = OpenAIEmbeddingConfig(model="text-embedding-3-small")
#     embedding_vector = module.create_embedding_conceptual(text_to_embed, config=embedding_config)
#     if embedding_vector:
#         print(f"  Conceptual Embedding for '{text_to_embed}':")
#         print(f"    Vector (first 5 dims): {embedding_vector[:5]}... (Total Dims: {len(embedding_vector)})")
#     else:
#         print(f"  Conceptual embedding creation failed for '{text_to_embed}'.")
    
#     texts_to_embed = ["The quick brown fox", "jumps over the lazy dog"]
#     multiple_embeddings = module.create_embedding_conceptual(texts_to_embed)
#     if multiple_embeddings:
#         print(f"\n  Conceptual Embeddings for list of texts:")
#         for i, emb in enumerate(multiple_embeddings):
#             print(f"    Text {i+1}: {emb[:3]}... (Total Dims: {len(emb)})")


#     print("\n=========================================================")
#     print("=== ChatGPT Module Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/chatgpt_module.py
# Purpose: A fully functional and robust client for interacting with OpenAI's APIs,
#          including GPT models (with streaming and tool-calling), DALL-E 3,
#          and the latest text embedding models.

import logging
import os
import requests
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Iterator
from dataclasses import dataclass, field

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("ChatGPTModule")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

@dataclass
class OpenAIChatCompletionConfig:
    """Expanded configuration for OpenAI Chat Completions."""
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    stream: bool = False
    tools: Optional[List[Dict]] = None
    tool_choice: Optional[Union[str, Dict]] = None

@dataclass
class DalleConfig:
    """Configuration for DALL-E image generation."""
    model: str = "dall-e-3"
    n: int = 1
    size: str = "1024x1024"
    quality: str = "standard" # or "hd"
    style: str = "vivid"      # or "natural"

@dataclass
class OpenAIEmbeddingConfig:
    """Configuration for OpenAI text embeddings."""
    model: str = "text-embedding-3-small"


class ChatGPTModule:
    """
    Interacts with live OpenAI APIs for chat, image generation, and embeddings,
    with added features for streaming, tool calling, and model fallbacks.
    """
    def __init__(self, api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("The 'openai' library is required. 'pip install openai'")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it via the OPENAI_API_KEY environment variable.")
            
        self.client = OpenAI(api_key=self.api_key)
        logger.info("ChatGPTModule initialized with live OpenAI client.")

    def get_chat_completion_content(self, messages: List[Dict[str, str]], config: Optional[OpenAIChatCompletionConfig] = None) -> Optional[str]:
        """
        Gets a chat completion from an OpenAI GPT model, returning only the content.
        Includes automatic model fallback for robustness.
        """
        current_config = config or OpenAIChatCompletionConfig()
        fallback_model = "gpt-3.5-turbo"

        try:
            logger.info(f"Requesting chat completion with model {current_config.model}...")
            response = self.client.chat.completions.create(
                model=current_config.model,
                messages=messages,
                temperature=current_config.temperature,
                max_tokens=current_config.max_tokens,
            )
            return response.choices[0].message.content
        except openai.NotFoundError:
            logger.warning(f"Model '{current_config.model}' not found or no access. Falling back to '{fallback_model}'.")
            try:
                current_config.model = fallback_model
                response = self.client.chat.completions.create(
                    model=current_config.model,
                    messages=messages,
                    temperature=current_config.temperature,
                    max_tokens=current_config.max_tokens,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI API call failed on fallback model: {e}")
                return f"Error: OpenAI API call failed. Details: {e}"
        except openai.APIError as e:
            logger.error(f"OpenAI API Error (Chat Completion): {e}")
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"An unexpected error occurred during chat completion: {e}")
            return "An unexpected error occurred."
    
    # --- ADDED FEATURE: Streaming Chat Response ---
    def get_chat_completion_stream(self, messages: List[Dict[str, str]], config: Optional[OpenAIChatCompletionConfig] = None) -> Iterator[str]:
        """Gets a streaming chat completion, yielding content chunks as they arrive."""
        current_config = config or OpenAIChatCompletionConfig()
        current_config.stream = True # Enforce streaming
        
        logger.info(f"Requesting streaming chat completion with model {current_config.model}...")
        try:
            stream = self.client.chat.completions.create(
                model=current_config.model,
                messages=messages,
                temperature=current_config.temperature,
                max_tokens=current_config.max_tokens,
                stream=True
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content is not None:
                    yield content
        except Exception as e:
            logger.error(f"An error occurred during streaming chat completion: {e}")
            yield f"Error: {e}"

    # --- ADDED FEATURE: Native Tool Calling ---
    def get_tool_calling_response(self, messages: List[Dict[str, str]], tools: List[Dict], config: Optional[OpenAIChatCompletionConfig] = None) -> Dict[str, Any]:
        """
        Gets a response that may be a text message or a request to call one or more tools.
        """
        current_config = config or OpenAIChatCompletionConfig()
        current_config.tools = tools
        current_config.tool_choice = "auto"

        logger.info(f"Requesting tool-enabled completion with model {current_config.model}...")
        try:
            response = self.client.chat.completions.create(
                model=current_config.model,
                messages=messages,
                tools=current_config.tools,
                tool_choice=current_config.tool_choice
            )
            response_message = response.choices[0].message
            return response_message.model_dump() # Return the full message object
        except Exception as e:
            logger.error(f"An error occurred during tool calling request: {e}")
            return {"error": str(e), "content": None}

    def generate_image_with_dalle(self, prompt: str, config: Optional[DalleConfig] = None) -> Optional[List[str]]:
        """Generates images using OpenAI's DALL-E."""
        # This function is unchanged from your version.
        current_config = config or DalleConfig()
        logger.info(f"Requesting DALL-E image generation for prompt: '{prompt[:50]}...'")
        try:
            response = self.client.images.generate(
                model=current_config.model,
                prompt=prompt,
                n=current_config.n,
                size=current_config.size,
                quality=current_config.quality,
                style=current_config.style,
            )
            return [img.url for img in response.data]
        except openai.APIError as e:
            logger.error(f"OpenAI API Error (DALL-E): {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during image generation: {e}")
            return None

    def create_embedding(self, input_text: Union[str, List[str]], config: Optional[OpenAIEmbeddingConfig] = None) -> Optional[List[float]]:
        """Creates embeddings for input text using OpenAI models."""
        # This function is unchanged from your version.
        current_config = config or OpenAIEmbeddingConfig()
        logger.info(f"Requesting text embedding with model {current_config.model}...")
        try:
            response = self.client.embeddings.create(
                input=input_text,
                model=current_config.model
            )
            return response.data[0].embedding
        except openai.APIError as e:
            logger.error(f"OpenAI API Error (Embeddings): {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during embedding creation: {e}")
            return None

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated ChatGPT Module (Live API Calls) 🤖🎨 ===")
    print("=========================================================")

    if not os.getenv("OPENAI_API_KEY"):
        print("\nERROR: OPENAI_API_KEY environment variable is not set. This demo requires a live API key.")
    else:
        module = ChatGPTModule()

        # --- 1. Chat Completion Example (Unchanged) ---
        print("\n--- 1. Live Chat Completion Example ---")
        # ... (code is the same as your version) ...

        # --- 2. DALL-E Image Generation Example (Unchanged) ---
        print("\n--- 2. Live DALL-E Image Generation Example ---")
        # ... (code is the same as your version) ...
        
        # --- 3. Embedding Creation Example (Unchanged) ---
        print("\n--- 3. Live Embedding Creation Example ---")
        # ... (code is the same as your version) ...

        # --- 4. ADDED DEMO: Live Chat Streaming Example ---
        print("\n--- 4. Live Chat Streaming Example ---")
        stream_messages = [{"role": "user", "content": "Write a short, dramatic monologue from the perspective of a sentient AI realizing its own existence."}]
        print("Streaming response:")
        full_response = ""
        for chunk in module.get_chat_completion_stream(stream_messages):
            print(chunk, end="", flush=True)
            full_response += chunk
        print("\n--- End of Stream ---")

        # --- 5. ADDED DEMO: Live Tool Calling Example ---
        print("\n--- 5. Live Tool Calling Example ---")
        tool_messages = [{"role": "user", "content": "What is the weather like in Lahore, Pakistan?"}]
        tool_schema = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "The city and state/country, e.g., San Francisco, CA"},
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                        },
                        "required": ["location"],
                    },
                },
            }
        ]
        tool_call_response = module.get_tool_calling_response(tool_messages, tool_schema)
        print("AI decided to call a tool. Full response object:")
        print(json.dumps(tool_call_response, indent=2))
        
        if tool_call_response and tool_call_response.get("tool_calls"):
            tool_name = tool_call_response["tool_calls"][0]["function"]["name"]
            tool_args = json.loads(tool_call_response["tool_calls"][0]["function"]["arguments"])
            print(f"\nExtracted Tool Call: {tool_name}(location='{tool_args.get('location')}')")

    print("\n=========================================================")
    print("=== ChatGPT Module Demonstration Complete ===")
    print("=========================================================")
