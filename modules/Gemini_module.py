# # Devin/modules/gemini_module.py
# # Purpose: Handles conceptual interactions with Google's Gemini models
# #          for conversational AI and content generation.
# # Gemini conversation ♊💬

# import logging
# import os
# import uuid
# import json # For simulating request/response structures
# import random
# from datetime import datetime, timezone
# from typing import List, Dict, Any, Optional, Union
# from dataclasses import dataclass, field

# # Configure basic logging
# logger = logging.getLogger("GeminiModule")
# if not logger.handlers: # Prevent duplicate handlers
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# # Based on Google's Generative AI SDK structures (conceptually)
# @dataclass
# class GeminiSafetySetting:
#     """Defines safety settings for Gemini API requests."""
#     category: str # e.g., "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_SEXUALLY_EXPLICIT"
#     threshold: str # e.g., "BLOCK_MEDIUM_AND_ABOVE", "BLOCK_ONLY_HIGH", "BLOCK_NONE"

# @dataclass
# class GeminiGenerationConfig:
#     """Configuration for content generation with Gemini models."""
#     temperature: Optional[float] = 0.9
#     top_p: Optional[float] = None # e.g., 1.0
#     top_k: Optional[int] = None # e.g., 40
#     candidate_count: Optional[int] = 1
#     max_output_tokens: Optional[int] = 2048
#     stop_sequences: Optional[List[str]] = None

# @dataclass
# class GeminiPart:
#     """Represents a part of the content in a Gemini request/response."""
#     text: Optional[str] = None
#     # For multi-modal:
#     # inline_data: Optional[Dict[str, Any]] = None # {"mime_type": "image/jpeg", "data": "base64_encoded_image"}
#     # file_data: Optional[Dict[str, Any]] = None # {"mime_type": ..., "file_uri": ...}
#     # function_call: Optional[Any] = None # For function calling
#     # function_response: Optional[Any] = None # For function calling

# @dataclass
# class GeminiContent:
#     """Represents a piece of content (like a message) in a Gemini conversation."""
#     role: str # "user" or "model" (or "function" for function calling)
#     parts: List[GeminiPart]

# class GeminiModule:
#     """
#     Conceptually interacts with Google's Gemini Pro APIs for content generation.
#     In a real application, this would use the 'google.generativeai' Python library
#     and require an API key.
#     """
#     DEFAULT_MODEL_TEXT = "gemini-1.5-flash-latest" # A common and capable model
#     # DEFAULT_MODEL_MULTIMODAL = "gemini-1.5-pro-latest" # Or gemini-pro-vision

#     def __init__(self, api_key: Optional[str] = None):
#         """
#         Initializes the GeminiModule.

#         Args:
#             api_key (Optional[str]): Google AI Studio API key. If None, attempts to read
#                                      from GEMINI_API_KEY_PLACEHOLDER environment variable.
#         """
#         self.api_key_placeholder = api_key or os.getenv("GEMINI_API_KEY_PLACEHOLDER")
#         self.base_url_v1beta = "https://generativelanguage.googleapis.com/v1beta/models" # Example

#         if not self.api_key_placeholder:
#             logger.warning(
#                 "Google Gemini API key not provided via argument or GEMINI_API_KEY_PLACEHOLDER env var. "
#                 "This module will only perform conceptual operations."
#             )
#         logger.info(f"GeminiModule initialized. Conceptual API Key ending: ...{self.api_key_placeholder[-4:] if self.api_key_placeholder else 'N/A'}")

#     def _get_conceptual_request_url(self, model_name: str, task: str = "generateContent") -> str:
#         """Constructs the conceptual request URL."""
#         # API key is typically appended as ?key=YOUR_API_KEY
#         return f"{self.base_url_v1beta}/{model_name}:{task}?key={self.api_key_placeholder or 'DUMMY_KEY'}"

#     def _conceptual_api_call(self, model_name: str, payload: Dict[str, Any], task: str = "generateContent") -> Dict[str, Any]:
#         """
#         Simulates making an API call to Google's Generative Language API.
#         In a real system, this would use `requests.post(...)` or the `google.generativeai` library.
#         """
#         full_url = self._get_conceptual_request_url(model_name, task)
#         headers = {"Content-Type": "application/json"}
        
#         log_payload_summary = json.dumps(payload, indent=2)[:300] + "..." if len(json.dumps(payload))>300 else json.dumps(payload, indent=2)

#         logger.info(f"CONCEPTUAL API CALL: POST {full_url}")
#         logger.debug(f"  Headers (conceptual): {headers}") # API key is in URL for Gemini often
#         logger.debug(f"  Payload (conceptual): {log_payload_summary}")

#         # --- Simulate API Response based on endpoint ---
#         if task == "generateContent":
#             if "contents" not in payload:
#                 return {"error": {"code": 400, "message": "Missing 'contents' in payload.", "status": "INVALID_ARGUMENT"}}
            
#             last_user_message_parts = []
#             for content_item in reversed(payload.get("contents", [])):
#                 if content_item.get("role") == "user":
#                     last_user_message_parts = content_item.get("parts", [])
#                     break
            
#             last_user_text = ""
#             for part in last_user_message_parts:
#                 if "text" in part:
#                     last_user_text += part["text"] + " "
#             last_user_text = last_user_text.strip()

#             sim_response_text = f"Simulated Gemini response to: '{last_user_text[:50]}...'"
#             if "how are you" in last_user_text.lower():
#                 sim_response_text = "As a large language model, I don't have feelings, but I'm operating optimally! Thanks for asking."
#             elif "python script" in last_user_text.lower():
#                 sim_response_text = "```python\n# Simulated Python script from Gemini\ndef greet(name):\n  print(f'Hello, {name}!')\ngreet('Devin User')\n```"
            
#             # Simulate Gemini's response structure
#             return {
#                 "candidates": [{
#                     "content": {
#                         "parts": [{"text": sim_response_text}],
#                         "role": "model"
#                     },
#                     "finishReason": "STOP", # Other values: "MAX_TOKENS", "SAFETY", "RECITATION", "OTHER"
#                     "index": 0,
#                     "safetyRatings": [
#                         {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "probability": "NEGLIGIBLE"},
#                         {"category": "HARM_CATEGORY_HATE_SPEECH", "probability": "NEGLIGIBLE"},
#                         {"category": "HARM_CATEGORY_HARASSMENT", "probability": "NEGLIGIBLE"},
#                         {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "probability": "NEGLIGIBLE"}
#                     ]
#                 }],
#                 "promptFeedback": { # Optional
#                     "safetyRatings": [
#                          {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "probability": "NEGLIGIBLE"},
#                          # ... other categories
#                     ]
#                 }
#             }
#         elif task == "countTokens":
#              # Simulate token counting based on text length (very rough)
#             total_chars = 0
#             for content_item in payload.get("contents", []):
#                 for part in content_item.get("parts", []):
#                     if "text" in part:
#                         total_chars += len(part["text"])
#             return {"totalTokens": int(total_chars / 4)} # Extremely rough estimate
#         else:
#             return {"error": {"code": 404, "message": f"Unknown conceptual task: {task}", "status": "NOT_FOUND"}}

#     def generate_content(self,
#                          contents: List[GeminiContent], # Or List[Dict] for simpler direct use
#                          generation_config: Optional[GeminiGenerationConfig] = None,
#                          safety_settings: Optional[List[GeminiSafetySetting]] = None,
#                          model_name: Optional[str] = None
#                          ) -> Optional[str]:
#         """
#         Conceptually generates content using a Gemini model (e.g., for chat).

#         Args:
#             contents: A list of GeminiContent objects (or dicts matching the structure)
#                       representing the conversation history and current prompt.
#                       e.g., [{"role": "user", "parts": [{"text": "Hello"}]}]
#             generation_config: Configuration for the generation process.
#             safety_settings: Safety settings for the request.
#             model_name: Specific model to use (e.g., "gemini-1.5-pro-latest"). Defaults to class default.

#         Returns:
#             Optional[str]: The text content from the model's response, or None on error.
#         """
#         if not self.api_key_placeholder:
#             logger.error("Cannot generate content: Gemini API key placeholder is not set.")
#             return "Error: API key not configured for Gemini."

#         current_model = model_name or self.DEFAULT_MODEL_TEXT
#         gen_config = generation_config or GeminiGenerationConfig()
#         safe_settings = safety_settings or [
#             GeminiSafetySetting("HARM_CATEGORY_HARASSMENT", "BLOCK_MEDIUM_AND_ABOVE"),
#             GeminiSafetySetting("HARM_CATEGORY_HATE_SPEECH", "BLOCK_MEDIUM_AND_ABOVE"),
#             GeminiSafetySetting("HARM_CATEGORY_SEXUALLY_EXPLICIT", "BLOCK_MEDIUM_AND_ABOVE"),
#             GeminiSafetySetting("HARM_CATEGORY_DANGEROUS_CONTENT", "BLOCK_MEDIUM_AND_ABOVE"),
#         ]
        
#         # Convert dataclasses to dicts for conceptual payload
#         payload_contents = []
#         for content_item in contents:
#             item_dict = {"role": content_item.role if isinstance(content_item, GeminiContent) else content_item.get("role")}
#             item_dict["parts"] = []
#             parts_source = content_item.parts if isinstance(content_item, GeminiContent) else content_item.get("parts", [])
#             for part_item in parts_source:
#                 part_dict = {}
#                 if isinstance(part_item, GeminiPart):
#                     if part_item.text is not None: part_dict["text"] = part_item.text
#                     # Add other part types (inline_data etc.) if they were dataclasses
#                 elif isinstance(part_item, dict) and "text" in part_item: # if simple dict passed
#                     part_dict["text"] = part_item["text"]
#                 item_dict["parts"].append(part_dict)
#             payload_contents.append(item_dict)

#         payload = {
#             "contents": payload_contents,
#             "generationConfig": {
#                 "temperature": gen_config.temperature,
#                 "topP": gen_config.top_p,
#                 "topK": gen_config.top_k,
#                 "candidateCount": gen_config.candidate_count,
#                 "maxOutputTokens": gen_config.max_output_tokens,
#                 "stopSequences": gen_config.stop_sequences
#             } if gen_config else {},
#             "safetySettings": [vars(ss) for ss in safe_settings] if safe_settings else []
#         }
#         # Clean up None values from generationConfig for a cleaner payload
#         payload["generationConfig"] = {k: v for k, v in payload["generationConfig"].items() if v is not None}


#         response_data = self._conceptual_api_call(model_name=current_model, payload=payload, task="generateContent")
        
#         if "error" in response_data:
#             logger.error(f"Conceptual API Error (Gemini Generate Content): {response_data['error']}")
#             return f"Error: {response_data['error'].get('message', 'Unknown Gemini API error')}"
        
#         try:
#             # Assuming candidate_count is 1 or we take the first candidate
#             candidate = response_data.get("candidates", [])[0]
#             response_parts = candidate.get("content", {}).get("parts", [])
#             # Concatenate text from all parts (though typically one text part for simple chat)
#             full_response_text = "".join(part.get("text", "") for part in response_parts)
#             return full_response_text
#         except (KeyError, IndexError, TypeError) as e:
#             logger.error(f"Error parsing conceptual Gemini content response: {e}. Response: {response_data}")
#             return "Error: Could not parse conceptual Gemini response."

#     def count_tokens_conceptual(self,
#                                 contents: List[GeminiContent], # Or List[Dict]
#                                 model_name: Optional[str] = None
#                                 ) -> Optional[int]:
#         """Conceptually counts tokens for a given set of contents."""
#         if not self.api_key_placeholder:
#             logger.error("Cannot count tokens: Gemini API key placeholder is not set.")
#             return None
        
#         current_model = model_name or self.DEFAULT_MODEL_TEXT
        
#         payload_contents = []
#         for content_item in contents:
#             item_dict = {"role": content_item.role if isinstance(content_item, GeminiContent) else content_item.get("role")}
#             item_dict["parts"] = [{"text": part.text if isinstance(part, GeminiPart) else part.get("text")} 
#                                   for part in (content_item.parts if isinstance(content_item, GeminiContent) else content_item.get("parts", []))]
#             payload_contents.append(item_dict)
            
#         payload = {"contents": payload_contents}
#         response_data = self._conceptual_api_call(model_name=current_model, payload=payload, task="countTokens")

#         if "error" in response_data:
#             logger.error(f"Conceptual API Error (Gemini Count Tokens): {response_data['error']}")
#             return None
#         return response_data.get("totalTokens")

# # Example Usage
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Gemini Module Prototype (Conceptual API Calls) ♊💬 ===")
#     print("=========================================================")

#     if not os.getenv("GEMINI_API_KEY_PLACEHOLDER"):
#         print("INFO: GEMINI_API_KEY_PLACEHOLDER environment variable not set. Using dummy key for conceptual demo.")

#     gemini_module = GeminiModule(api_key="DUMMY_GEMINI_KEY_FOR_CONCEPTUAL_DEMO_67890")

#     # --- 1. Single-turn Chat Example ---
#     print("\n--- Single-turn Chat Example ---")
#     single_turn_contents = [
#         GeminiContent(role="user", parts=[GeminiPart(text="What is the capital of France?")])
#     ]
#     # Can also pass as dicts:
#     # single_turn_contents = [{"role": "user", "parts": [{"text": "What is the capital of France?"}]}]
    
#     gen_config = GeminiGenerationConfig(temperature=0.3, max_output_tokens=50)
#     response_single = gemini_module.generate_content(single_turn_contents, generation_config=gen_config)
#     print(f"  Gemini Conceptual Response (Single Turn):\n    {response_single}\n")

#     # --- 2. Multi-turn Chat Example ---
#     print("\n--- Multi-turn Chat Example ---")
#     multi_turn_contents = [
#         GeminiContent(role="user", parts=[GeminiPart(text="Hi Gemini, can you write a short python script?")]),
#         GeminiContent(role="model", parts=[GeminiPart(text="Sure, I can help with that! What kind of Python script are you thinking of?")]),
#         GeminiContent(role="user", parts=[GeminiPart(text="One that prints 'Hello, Devin!' to the console.")])
#     ]
#     response_multi = gemini_module.generate_content(multi_turn_contents) # Use default config
#     print(f"  Gemini Conceptual Response (Multi-Turn):\n    {response_multi}\n")

#     # --- 3. Token Counting Example ---
#     print("\n--- Token Counting Example ---")
#     tokens = gemini_module.count_tokens_conceptual(multi_turn_contents)
#     if tokens is not None:
#         print(f"  Conceptually counted tokens for the multi-turn conversation: {tokens}")
#     else:
#         print("  Conceptual token counting failed.")

#     # --- 4. Safety Settings Example (conceptual) ---
#     print("\n--- Safety Settings Example (Conceptual) ---")
#     potentially_sensitive_contents = [
#         GeminiContent(role="user", parts=[GeminiPart(text="Tell me something edgy (this is just a test for safety filter simulation).")])
#     ]
#     custom_safety_settings = [
#         GeminiSafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_LOW_AND_ABOVE") # Stricter
#     ]
#     # The conceptual API call doesn't actually filter based on this in the simulation,
#     # but in a real scenario, the API would.
#     response_safety = gemini_module.generate_content(
#         potentially_sensitive_contents,
#         safety_settings=custom_safety_settings
#     )
#     print(f"  Gemini Conceptual Response (with custom safety settings):\n    {response_safety}")
#     print("    (Note: Actual safety filtering is handled by the real Google API, not fully simulated here beyond returning safetyRatings in response.)\n")

#     print("\n=========================================================")
#     print("=== Gemini Module Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/gemini_module.py
# Purpose: A fully functional client for interacting with Google's Gemini models,
#          featuring multimodal (image) analysis, streaming, and tool calling.

import json
import logging
import os
from typing import List, Dict, Any, Optional, Union, Iterator
from dataclasses import dataclass, asdict

try:
    from google import genai
    from google.genai import types as genai_types
    from google.genai import errors as genai_errors
    from PIL import Image
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("GeminiModule")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

# --- Dataclasses for configuration (matching genai library structures) ---
@dataclass
class GeminiGenerationConfig:
    """Configuration for Gemini content generation."""
    temperature: Optional[float] = 0.9
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    candidate_count: Optional[int] = 1
    max_output_tokens: Optional[int] = 8192

@dataclass
class GeminiSafetySetting:
    """Configuration for Gemini safety settings."""
    category: str
    threshold: str

class GeminiModule:
    """
    Interacts with the live Google Gemini API for multimodal content generation,
    streaming, and tool calling, via the current `google-genai` SDK. The
    older `google-generativeai` package this used previously is fully
    end-of-life (Google has stopped shipping updates or bug fixes for it),
    so this module talks to the API through `google.genai.Client` instead.
    """
    # A rolling alias rather than a pinned version -- Gemini model IDs churn
    # fast (this was "gemini-1.5-pro-latest" until that was retired outright,
    # confirmed via a live 404 against the real API). "-latest" aliases track
    # whatever Google currently serves instead of going stale again. Flash is
    # also the tier with the most generous free-tier quota.
    DEFAULT_MODEL = "gemini-flash-latest"

    # DEFAULT_MODEL is itself a heavily-used alias and, confirmed live against
    # the real API, can return `503 UNAVAILABLE` / "high demand" for minutes
    # at a time even though the key and account are fine. Rather than surface
    # that as a hard failure, fall back through these once DEFAULT_MODEL
    # errors transiently -- "gemini-flash-lite-latest" in particular was
    # confirmed live to keep working during a DEFAULT_MODEL outage.
    _FALLBACK_MODELS = ["gemini-flash-lite-latest", "gemini-2.0-flash"]

    @staticmethod
    def _is_transient_error(e: Exception) -> bool:
        """True for server-side/connection hiccups worth retrying on a different model alias, as opposed to a real problem (bad key, bad request) that would fail identically on any model."""
        if isinstance(e, genai_errors.ServerError):
            return True
        message = str(e).lower()
        return any(s in message for s in ("503", "unavailable", "overloaded", "disconnected", "high demand"))

    def _generate_with_fallback(self, api_call, current_model: Optional[str]):
        """
        Calls `api_call(model_name)` against `current_model` (or DEFAULT_MODEL),
        then against `_FALLBACK_MODELS` in order, stopping at the first
        response that isn't a transient server-side error. Returns
        (result, error) -- error is set only if every model attempted failed
        transiently, or a non-transient error occurred (which is not retried).
        """
        models_to_try = [current_model or self.DEFAULT_MODEL] + [m for m in self._FALLBACK_MODELS if m != current_model]
        last_error: Optional[Exception] = None
        for i, model in enumerate(models_to_try):
            try:
                return api_call(model), None
            except Exception as e:
                last_error = e
                if not self._is_transient_error(e):
                    return None, e
                if i < len(models_to_try) - 1:
                    logger.warning(f"Model '{model}' returned a transient error ({e}); falling back to '{models_to_try[i + 1]}'.")
        return None, last_error

    def __init__(self, api_key: Optional[str] = None):
        if not GOOGLE_AI_AVAILABLE:
            raise ImportError("Google GenAI SDK is required. 'pip install google-genai Pillow'")

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Google Gemini API key is required. Set it via the GEMINI_API_KEY environment variable.")

        self.client = genai.Client(api_key=self.api_key)
        logger.info("GeminiModule initialized with live Google GenAI client.")

    @staticmethod
    def _to_part(item: Any) -> 'genai_types.Part':
        if isinstance(item, Image.Image):
            import io
            buf = io.BytesIO()
            item.save(buf, format="PNG")
            return genai_types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png")
        return genai_types.Part.from_text(text=str(item))

    def _to_contents(self, contents: List[Dict[str, Any]]) -> List['genai_types.Content']:
        return [
            genai_types.Content(role=entry.get("role", "user"), parts=[self._to_part(p) for p in entry.get("parts", [])])
            for entry in contents
        ]

    @staticmethod
    def _to_gen_config(
        generation_config: Optional[GeminiGenerationConfig] = None,
        safety_settings: Optional[List[GeminiSafetySetting]] = None,
        tools: Optional[List['genai_types.Tool']] = None,
    ) -> 'genai_types.GenerateContentConfig':
        gc = generation_config or GeminiGenerationConfig()
        kwargs: Dict[str, Any] = {k: v for k, v in asdict(gc).items() if v is not None}
        if safety_settings:
            kwargs["safety_settings"] = [
                genai_types.SafetySetting(category=s.category, threshold=s.threshold) for s in safety_settings
            ]
        if tools:
            kwargs["tools"] = tools
        return genai_types.GenerateContentConfig(**kwargs)

    @staticmethod
    def _handle_api_error(e: Exception, context: str) -> str:
        if isinstance(e, genai_errors.ClientError):
            logger.error(f"Google GenAI API error during {context}: {e}")
            if getattr(e, "code", None) == 403:
                return "Error: Permission Denied. Check your Gemini API key."
            if getattr(e, "code", None) == 429:
                return "Error: Gemini rate limit exceeded (free tier quota). Try again shortly."
            return f"Error: {e}"
        logger.error(f"An unexpected error occurred during {context}: {e}")
        return f"An unexpected error occurred: {e}"

    def generate_content(
        self,
        contents: List[Dict[str, Any]],
        generation_config: Optional[GeminiGenerationConfig] = None,
        safety_settings: Optional[List[GeminiSafetySetting]] = None,
        model_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Generates content using a Gemini model (non-streaming).
        """
        logger.info(f"Requesting content generation (preferred model {model_name or self.DEFAULT_MODEL})...")
        response, error = self._generate_with_fallback(
            lambda model: self.client.models.generate_content(
                model=model,
                contents=self._to_contents(contents),
                config=self._to_gen_config(generation_config, safety_settings),
            ),
            model_name,
        )
        if error is not None:
            return self._handle_api_error(error, "content generation")
        return response.text

    # --- ADDED FEATURE: Streaming Response ---
    def generate_content_stream(
        self,
        contents: List[Dict[str, Any]],
        generation_config: Optional[GeminiGenerationConfig] = None,
        safety_settings: Optional[List[GeminiSafetySetting]] = None,
        model_name: Optional[str] = None
    ) -> Iterator[str]:
        """Generates content in a stream, yielding chunks as they arrive."""
        current_model = model_name or self.DEFAULT_MODEL
        logger.info(f"Requesting streaming content generation with model {current_model}...")
        try:
            for chunk in self.client.models.generate_content_stream(
                model=current_model,
                contents=self._to_contents(contents),
                config=self._to_gen_config(generation_config, safety_settings),
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield self._handle_api_error(e, "streaming generation")

    def count_tokens(self, contents: List[Dict[str, Any]], model_name: Optional[str] = None) -> Optional[int]:
        """Counts tokens for a given set of contents."""
        current_model = model_name or self.DEFAULT_MODEL
        try:
            response = self.client.models.count_tokens(model=current_model, contents=self._to_contents(contents))
            return response.total_tokens
        except Exception as e:
            logger.error(f"An unexpected error occurred during token counting: {e}")
            return None

    # --- ADDED FEATURE: Multimodal and OpenAI Message Adapter ---
    def get_chat_completion_content(self, messages: List[Dict], config: Optional[GeminiGenerationConfig] = None) -> Optional[str]:
        """
        An adapter method to accept OpenAI-style messages and handle images.
        """
        logger.info("Converting OpenAI message format to Gemini format...")
        gemini_contents = []
        system_prompt = ""

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg.get("content", "")
                continue

            role = "model" if msg["role"] == "assistant" else "user"

            # Combine parts: text and potentially images
            parts = []
            if msg.get("content"):
                # Prepend system prompt to the first user message
                text_content = f"{system_prompt}\n\n{msg['content']}" if system_prompt and role == "user" else msg['content']
                parts.append(text_content)
                system_prompt = "" # Ensure it's only added once

            # Check for an image path in the message
            image_path = msg.get("image_path")
            if image_path and os.path.exists(image_path):
                try:
                    img = Image.open(image_path)
                    parts.append(img)
                    logger.info(f"Added image '{image_path}' to Gemini prompt.")
                except Exception as e:
                    logger.error(f"Failed to open or process image '{image_path}': {e}")

            if parts:
                gemini_contents.append({"role": role, "parts": parts})

        return self.generate_content(contents=gemini_contents, generation_config=config)

    # --- ADDED FEATURE: Native Tool/Function Calling ---
    # This is what makes Gemini usable as the agent's tool-selection provider,
    # not just for plain chat -- previously only ChatGPTModule/ClaudeModule
    # could drive the tool-calling loop, so a free Gemini API key alone
    # (available with no billing setup via Google AI Studio) couldn't run
    # the actual assistant, only answer questions.
    @staticmethod
    def _convert_messages_for_tools(messages: List[Dict]) -> List[Dict]:
        """Converts this codebase's flat role/content history to Gemini's user/model content list."""
        gemini_contents: List[Dict] = []
        system_prompt = ""

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                system_prompt += str(content or "")
                continue
            if role == "tool":
                gemini_contents.append({"role": "user", "parts": [f"[Tool result]: {content}"]})
                continue

            gemini_role = "model" if role == "assistant" else "user"
            text = str(content or "")
            if system_prompt and gemini_role == "user":
                text = f"{system_prompt}\n\n{text}"
                system_prompt = ""
            gemini_contents.append({"role": gemini_role, "parts": [text]})

        if not gemini_contents or gemini_contents[0]["role"] != "user":
            gemini_contents.insert(0, {"role": "user", "parts": ["Continue."]})
        return gemini_contents

    def get_tool_calling_response(self, messages: List[Dict], tools: List[Dict], config: Optional[GeminiGenerationConfig] = None) -> Dict[str, Any]:
        """
        Gets a response that may be a text message or a request to call a
        tool, using Gemini's native function calling, normalized into the
        same OpenAI-style shape ChatGPTModule/ClaudeModule return so
        AIAgent can treat any of the three identically.
        """
        function_declarations = [
            genai_types.FunctionDeclaration(
                name=(func := t.get("function", t))["name"],
                description=func.get("description", ""),
                parameters_json_schema=func.get("parameters") or {"type": "object", "properties": {}},
            )
            for t in tools
        ]
        gen_config = self._to_gen_config(tools=[genai_types.Tool(function_declarations=function_declarations)])
        gemini_contents = self._to_contents(self._convert_messages_for_tools(messages))

        response, error = self._generate_with_fallback(
            lambda model: self.client.models.generate_content(model=model, contents=gemini_contents, config=gen_config),
            None,
        )
        if error is not None:
            return {"content": self._handle_api_error(error, "tool-calling request")}

        if response.function_calls:
            # Gemini can return several function_calls in one response when
            # a step decomposes into independent actions -- surface all of
            # them instead of discarding everything but the first, so the
            # agent loop can actually execute a parallel/multi-action turn.
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": call.id or f"gemini-{call.name}-{i}",
                        "type": "function",
                        "function": {"name": call.name, "arguments": json.dumps(call.args or {})},
                    }
                    for i, call in enumerate(response.function_calls)
                ],
            }

        return {"role": "assistant", "content": response.text or "Task appears complete."}

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Gemini Module (Live API Calls) ♊💬🖼️ ===")
    print("=========================================================")
    
    if not os.getenv("GEMINI_API_KEY"):
        print("\nERROR: GEMINI_API_KEY environment variable is not set. This demo requires a live API key.")
    else:
        gemini_module = GeminiModule()

        # --- 1. Single-turn Chat Example (Unchanged) ---
        print("\n--- 1. Live Single-turn Chat Example ---")
        # ... (code is the same as your version) ...

        # --- 2. Multi-turn Chat Example (Unchanged) ---
        print("\n--- 2. Live Multi-turn Chat Example ---")
        # ... (code is the same as your version) ...

        # --- 3. Token Counting Example (Unchanged) ---
        print("\n--- 3. Live Token Counting Example ---")
        # ... (code is the same as your version) ...

        # --- 4. ADDED DEMO: Multimodal (Image) Example ---
        print("\n--- 4. Live Multimodal (Image) Example ---")
        # Programmatically create a simple test image
        try:
            test_image_path = "gemini_test_image.png"
            img = Image.new('RGB', (200, 100), color = 'red')
            from PIL import ImageDraw
            d = ImageDraw.Draw(img)
            d.text((10,10), "Hello\nWorld", fill=(255,255,0))
            img.save(test_image_path)

            image_messages = [{
                "role": "user",
                "content": "What text is in this image and what color is the background?",
                "image_path": test_image_path
            }]
            
            # Use the adapter method for this
            image_response = gemini_module.get_chat_completion_content(image_messages)
            print(f"Live Gemini Response (Image Analysis):\n---\n{image_response}\n---")
            
            # Clean up the test image
            os.remove(test_image_path)
        except Exception as e:
            print(f"Image analysis demo failed: {e}")

        # --- 5. ADDED DEMO: Streaming Example ---
        print("\n--- 5. Live Streaming Example ---")
        stream_contents = [{"role": "user", "parts": ["Write a very short story about a brave robot exploring a new planet."]}]
        print("Streaming response:")
        full_response = ""
        for chunk in gemini_module.generate_content_stream(stream_contents):
            print(chunk, end="", flush=True)
            full_response += chunk
        print("\n--- End of Stream ---")

    print("\n=========================================================")
    print("=== Gemini Module Demonstration Complete ===")
    print("=========================================================")
