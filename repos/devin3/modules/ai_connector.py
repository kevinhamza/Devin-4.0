# # Devin/modules/ai_connector.py
# # Purpose: Defines a generic, abstract interface (contract) for connecting
# #          to any AI model, ensuring all AI modules are interchangeable.
# # Generic AI connection 🔌

# import logging
# from abc import ABC, abstractmethod
# from dataclasses import dataclass, field
# from typing import List, Dict, Any, Optional

# # Configure basic logging
# logger = logging.getLogger("AIConnector")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# @dataclass
# class AIRequest:
#     """A standardized representation of a request to an AI model."""
#     messages: List[Dict[str, str]]
#     model: str
#     config: Dict[str, Any] = field(default_factory=dict) # e.g., temperature, max_tokens

# @dataclass
# class AIResponse:
#     """A standardized representation of a response from an AI model."""
#     content: Optional[str]
#     is_success: bool
#     finish_reason: Optional[str] = None
#     error_message: Optional[str] = None
#     raw_response: Optional[Dict] = None # To store the original provider response

# class AIGenericConnector(ABC):
#     """
#     An Abstract Base Class (ABC) that defines the "contract" for any AI connector.
#     Any class that interacts with an AI model (like ChatGPT, Gemini, Claude) should
#     inherit from this class and implement its abstract methods.
#     """
#     def __init__(self, model_name: str):
#         self.model_name = model_name
#         logger.info(f"Connector for model '{self.model_name}' of type '{type(self).__name__}' is being initialized.")
#         super().__init__()

#     @abstractmethod
#     def get_chat_completion(self, request: AIRequest) -> AIResponse:
#         """
#         Sends a request to the AI model and gets a chat completion.

#         Args:
#             request (AIRequest): The standardized request object.

#         Returns:
#             AIResponse: The standardized response object.
#         """
#         pass

#     @abstractmethod
#     def count_tokens_conceptual(self, text_or_messages: Any) -> int:
#         """
#         Conceptually counts the number of tokens for a given text or message list.

#         Args:
#             text_or_messages: The content to be tokenized.

#         Returns:
#             int: The conceptual number of tokens.
#         """
#         pass

#     def get_provider_name(self) -> str:
#         """Returns the name of the AI provider for this connector."""
#         # This can be overridden but provides a default based on the class name.
#         return self.__class__.__name__.replace("Connector", "")

# # --- Example Concrete Implementation ---
# # This demonstrates how a real module like ChatGPTModule would implement the interface.

# class SimpleEchoConnector(AIGenericConnector):
#     """
#     A simple, concrete implementation of the AIGenericConnector for testing.
#     It doesn't connect to any real AI; it just echoes the user's message back.
#     """
#     def __init__(self, model_name: str = "echo-v1"):
#         super().__init__(model_name)

#     def get_chat_completion(self, request: AIRequest) -> AIResponse:
#         """Implements the abstract method for the Echo connector."""
#         logger.info(f"SimpleEchoConnector processing request for model '{request.model}'...")
#         if not request.messages or request.messages[-1]["role"] != "user":
#             error_msg = "Invalid request: Last message must be from 'user'."
#             logger.error(error_msg)
#             return AIResponse(content=None, is_success=False, error_message=error_msg)

#         last_user_message = request.messages[-1]["content"]
#         echo_content = f"Echo from {self.model_name}: '{last_user_message}'"
        
#         return AIResponse(
#             content=echo_content,
#             is_success=True,
#             finish_reason="stop",
#             raw_response={"simulated": True, "echoed_text": last_user_message}
#         )
    
#     def count_tokens_conceptual(self, text_or_messages: Any) -> int:
#         """Implements the abstract method for the Echo connector."""
#         # A simple token counting simulation (e.g., words)
#         if isinstance(text_or_messages, str):
#             return len(text_or_messages.split())
#         elif isinstance(text_or_messages, list):
#             total_words = 0
#             for msg in text_or_messages:
#                 total_words += len(msg.get("content", "").split())
#             return total_words
#         return 0


# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Generic AI Connector Prototype 🔌 ===")
#     print("=========================================================")

#     # 1. Demonstrate that the Abstract Base Class cannot be instantiated directly
#     print("\n--- Attempting to instantiate the abstract class (should fail) ---")
#     try:
#         generic_connector = AIGenericConnector(model_name="abstract-model")
#     except TypeError as e:
#         print(f"  SUCCESS: Caught expected TypeError: {e}")

#     # 2. Instantiate and use the concrete implementation
#     print("\n\n--- Using the concrete 'SimpleEchoConnector' implementation ---")
#     echo_connector = SimpleEchoConnector()
    
#     # Create a standardized request
#     my_request = AIRequest(
#         messages=[
#             {"role": "system", "content": "You are an echo bot."},
#             {"role": "user", "content": "Hello, world! Can you hear me?"}
#         ],
#         model="echo-v1",
#         config={"temperature": 0.1} # Config is passed but not used by echo bot
#     )
    
#     # Get a response
#     response = echo_connector.get_chat_completion(my_request)
    
#     print(f"\n  Provider: {echo_connector.get_provider_name()}")
#     print(f"  Request Model: {my_request.model}")
#     print(f"  Response Success: {response.is_success}")
#     print(f"  Response Content: {response.content}")
#     print(f"  Finish Reason: {response.finish_reason}")

#     # 3. Demonstrate token counting
#     print("\n\n--- Demonstrating conceptual token counting ---")
#     messages_for_counting = my_request.messages
#     token_count = echo_connector.count_tokens_conceptual(messages_for_counting)
#     print(f"  Conceptual token count for messages: {token_count}")
    
#     string_for_counting = "This is another test string."
#     token_count_str = echo_connector.count_tokens_conceptual(string_for_counting)
#     print(f"  Conceptual token count for a string: {token_count_str}")

#     print("\n=========================================================")
#     print("=== AI Connector Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/ai_connector.py
# Purpose: Provides concrete implementations of a generic AI connector for
#          various AI providers, ensuring they are interchangeable.

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

try:
    from modules.chatgpt_module import ChatGPTModule, OpenAIChatCompletionConfig
    from modules.gemini_module import GeminiModule, GeminiGenerationConfig
    from modules.perplexity_module import PerplexityModule, PerplexityChatConfig
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("AIConnector")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

@dataclass
class AIRequest:
    """A standardized representation of a request to an AI model."""
    messages: List[Dict[str, str]]
    model: str
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AIResponse:
    """A standardized representation of a response from an AI model."""
    content: Optional[str]
    is_success: bool
    error_message: Optional[str] = None
    raw_response: Optional[Any] = None

class AIGenericConnector(ABC):
    """Abstract Base Class defining the contract for any AI connector."""
    def __init__(self, model_name: str):
        self.model_name = model_name
        super().__init__()

    @abstractmethod
    def get_chat_completion(self, request: AIRequest) -> AIResponse:
        """Sends a request to the AI model and gets a chat completion."""
        pass

# --- Concrete Implementations ---

class OpenAIConnector(AIGenericConnector):
    """A live, concrete connector for OpenAI models via our ChatGPTModule."""
    def __init__(self, api_key: Optional[str] = None):
        if not DEVIN_CORE_AVAILABLE: raise ImportError(f"Core modules missing: {_import_error}")
        self.chatgpt_module = ChatGPTModule(api_key=api_key)
        super().__init__(model_name=self.chatgpt_module.client.models.list().data[0].id)

    def get_chat_completion(self, request: AIRequest) -> AIResponse:
        config = OpenAIChatCompletionConfig(model=request.model, **request.config)
        content = self.chatgpt_module.get_chat_completion(request.messages, config=config)
        if content is None or content.startswith("Error:"):
            return AIResponse(content=None, is_success=False, error_message=content)
        return AIResponse(content=content, is_success=True)

class GeminiConnector(AIGenericConnector):
    """A live, concrete connector for Google Gemini models."""
    def __init__(self, api_key: Optional[str] = None):
        if not DEVIN_CORE_AVAILABLE: raise ImportError(f"Core modules missing: {_import_error}")
        self.gemini_module = GeminiModule(api_key=api_key)
        super().__init__(model_name=self.gemini_module.DEFAULT_MODEL)

    def get_chat_completion(self, request: AIRequest) -> AIResponse:
        # --- Adapter Logic ---
        system_prompt, gemini_messages = self._adapt_messages(request.messages)
        config = GeminiGenerationConfig(**request.config)
        
        # Pass the system prompt separately for newer Gemini models
        content = self.gemini_module.generate_content(
            contents=gemini_messages,
            generation_config=config,
            model_name=request.model
        )
        if content is None or content.startswith("Error:"):
            return AIResponse(content=None, is_success=False, error_message=content)
        return AIResponse(content=content, is_success=True)

    def _adapt_messages(self, messages: List[Dict[str, str]]) -> (Optional[str], List[Dict]):
        """Translates OpenAI message format to Gemini's format."""
        system_prompt = None
        gemini_contents = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] in ["user", "assistant"]:
                 gemini_contents.append({
                    "role": "model" if msg["role"] == "assistant" else "user",
                    "parts": [msg["content"]]
                })
        return system_prompt, gemini_contents

class PerplexityConnector(AIGenericConnector):
    """A live, concrete connector for Perplexity AI models."""
    def __init__(self, api_key: Optional[str] = None):
        if not DEVIN_CORE_AVAILABLE: raise ImportError(f"Core modules missing: {_import_error}")
        self.perplexity_module = PerplexityModule(api_key=api_key)
        super().__init__(model_name=self.perplexity_module.get_chat_completion_content([{"role":"user","content":""}]).model)
        
    def get_chat_completion(self, request: AIRequest) -> AIResponse:
        config = PerplexityChatConfig(model=request.model, **request.config)
        content = self.perplexity_module.get_chat_completion_content(request.messages, config=config)
        if content is None or content.startswith("Error:"):
            return AIResponse(content=None, is_success=False, error_message=content)
        return AIResponse(content=content, is_success=True)

# --- Example Usage ---
if __name__ == "__main__":
    import os
    print("=========================================================")
    print("=== Integrated AI Connector (Live API Calls) 🔌 ===")
    print("=========================================================")

    # Check for API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")

    if not all([openai_key, gemini_key, perplexity_key]):
        print("\nERROR: One or more API keys (OPENAI_API_KEY, GEMINI_API_KEY, PERPLEXITY_API_KEY) are not set.")
    else:
        # 1. Instantiate all concrete connectors
        print("--- Initializing all AI connectors... ---")
        try:
            openai_connector = OpenAIConnector(api_key=openai_key)
            gemini_connector = GeminiConnector(api_key=gemini_key)
            perplexity_connector = PerplexityConnector(api_key=perplexity_key)
            connectors = {
                "OpenAI": openai_connector,
                "Gemini": gemini_connector,
                "Perplexity": perplexity_connector,
            }
            print("--- All connectors initialized successfully. ---")

            # 2. Create a single, standard request object
            common_messages = [
                {"role": "system", "content": "You are a concise assistant."},
                {"role": "user", "content": "What is the core concept of quantum entanglement?"}
            ]
            
            # 3. Send the *same* request to each connector
            for name, connector in connectors.items():
                print(f"\n\n--- Querying {name} via the standard connector interface ---")
                
                # Use a specific model for each provider
                model = "gpt-4o" if name == "OpenAI" else "gemini-1.5-flash-latest" if name == "Gemini" else "llama-3-sonar-large-32k-online"
                request = AIRequest(messages=common_messages, model=model)
                
                response = connector.get_chat_completion(request)
                
                print(f"  > Request sent to model: {request.model}")
                print(f"  < Response Success: {response.is_success}")
                if response.is_success:
                    print(f"  < Response Content:\n    {response.content}")
                else:
                    print(f"  < Error: {response.error_message}")
                    
        except Exception as e:
            print(f"\nAn error occurred during initialization or execution: {e}")

    print("\n=========================================================")
    print("=== AI Connector Prototype Complete ===")
    print("=========================================================")
