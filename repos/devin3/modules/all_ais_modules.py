# # Devin/modules/all_ais_modules.py
# # Purpose: Provides a unified interface to all underlying AI model modules,
# #          acting as a central agent for AI-driven tasks.
# # Unified AI Agent Interface 🤖🌐

# import logging
# from enum import Enum, auto
# from typing import List, Dict, Any, Optional, Union

# # --- Conceptual Placeholders for Imported Modules ---
# # In a real project, these would be `from .chatgpt_module import ChatGPTModule`, etc.
# # For this script to be self-contained and demonstrate the structure,
# # we define minimal placeholder versions here based on our previous designs.

# class ConceptualChatGPTModule:
#     def __init__(self, api_key: str = "DUMMY_OPENAI_KEY"):
#         self.model_name = "gpt-4o_placeholder"
#     def get_chat_completion_content(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
#         return f"Conceptual response from ChatGPT for: '{messages[-1]['content'][:30]}...'"

# class ConceptualGeminiModule:
#     def __init__(self, api_key: str = "DUMMY_GEMINI_KEY"):
#         self.model_name = "gemini-1.5-pro_placeholder"
#     def generate_content(self, contents: List[Dict], **kwargs) -> Optional[str]:
#         last_content = contents[-1].get("parts", [{}])[0].get("text", "")
#         return f"Conceptual response from Gemini for: '{last_content[:30]}...'"

# class ConceptualPerplexityModule:
#     def __init__(self, api_key: str = "DUMMY_PPLX_KEY"):
#         self.model_name = "llama-3-sonar-large_placeholder"
#     def get_chat_completion_content(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
#         return f"Sourced conceptual response from Perplexity for: '{messages[-1]['content'][:30]}...'"

# class ConceptualPentestGPTAIModule:
#     def __init__(self, llm_interface: Any):
#         self.llm = llm_interface
#     def analyze_tool_output(self, tool_name: str, tool_output: str) -> Optional[Dict]:
#         return {"summary": f"Conceptual PentestGPT analysis of {tool_name} output.", "findings": []}
#     def suggest_next_pentest_actions(self, current_phase: str) -> Optional[List[str]]:
#         return [f"Conceptual action 1 for {current_phase}", f"Conceptual action 2 for {current_phase}"]

# # --- End of Conceptual Placeholders ---


# # Configure basic logging
# logger = logging.getLogger("AllAIsModule")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class AIProvider(Enum):
#     """Enumeration for the available AI providers."""
#     OPENAI = auto()
#     GOOGLE = auto()
#     PERPLEXITY = auto()
#     PENTEST_GPT = auto() # Specialized layer

# class AIAgent:
#     """
#     A unified agent that provides access to multiple AI models and specialized modules.
#     It acts as a single point of entry for other parts of the Devin system to request
#     AI-driven capabilities without needing to know the specifics of each provider's API.
#     """

#     def __init__(self,
#                  openai_api_key: Optional[str] = None,
#                  gemini_api_key: Optional[str] = None,
#                  perplexity_api_key: Optional[str] = None):
#         """
#         Initializes the agent and all its underlying AI provider modules.
#         API keys would be fetched from secure storage or environment variables in a real application.
#         """
#         logger.info("Initializing AIAgent with all AI provider modules...")

#         # Initialize base LLM providers
#         self.openai_module = ConceptualChatGPTModule(api_key=openai_api_key)
#         self.gemini_module = ConceptualGeminiModule(api_key=gemini_api_key)
#         self.perplexity_module = ConceptualPerplexityModule(api_key=perplexity_api_key)

#         # Initialize specialized modules that depend on a base LLM
#         # PentestGPT can be configured to use any of the base models. We'll default to OpenAI's.
#         self.pentest_gpt_module = ConceptualPentestGPTAIModule(llm_interface=self.openai_module)

#         self.provider_map = {
#             AIProvider.OPENAI: self.openai_module,
#             AIProvider.GOOGLE: self.gemini_module,
#             AIProvider.PERPLEXITY: self.perplexity_module,
#             AIProvider.PENTEST_GPT: self.pentest_gpt_module,
#         }
#         logger.info("AIAgent initialization complete.")

#     def get_general_chat_response(self,
#                                   messages: List[Dict[str, str]],
#                                   provider: AIProvider = AIProvider.OPENAI,
#                                   config: Optional[Dict[str, Any]] = None) -> Optional[str]:
#         """
#         Gets a general-purpose chat response from a specified AI provider.

#         Args:
#             messages (List[Dict[str, str]]): Conversation history in OpenAI's message format.
#                                              This format will be adapted for other providers if necessary.
#             provider (AIProvider): The desired AI provider to use.
#             config (Optional[Dict[str, Any]]): Provider-specific configuration options.

#         Returns:
#             Optional[str]: The text response from the AI model.
#         """
#         config = config or {}
#         logger.info(f"Requesting general chat response from provider: {provider.name}")

#         if provider == AIProvider.OPENAI or provider == AIProvider.PERPLEXITY:
#             # These modules use the OpenAI-compatible message format directly
#             module = self.provider_map[provider]
#             return module.get_chat_completion_content(messages=messages, **config)

#         elif provider == AIProvider.GOOGLE:
#             # Adapt OpenAI message format to Gemini's "contents" format
#             gemini_contents = []
#             for msg in messages:
#                 # This is a simplified conversion. System messages might need special handling.
#                 if msg["role"] == "system":
#                     # Gemini handles system instructions differently, often as a preamble.
#                     # For this conceptual adapter, we'll prepend it to the first user message.
#                     # A more robust adapter would manage this more elegantly.
#                     continue # Skip for now
#                 gemini_contents.append({
#                     "role": "model" if msg["role"] == "assistant" else msg["role"],
#                     "parts": [{"text": msg["content"]}]
#                 })
#             return self.gemini_module.generate_content(contents=gemini_contents, **config)
        
#         else:
#             logger.error(f"Provider '{provider.name}' is not supported for general chat responses directly.")
#             return None

#     def get_search_augmented_response(self,
#                                       query: str,
#                                       conversation_history: Optional[List[Dict[str, str]]] = None
#                                       ) -> Optional[str]:
#         """
#         A convenience method to get a response from an AI optimized for search and current events.
#         Defaults to using Perplexity AI.
#         """
#         logger.info("Requesting search-augmented response, defaulting to Perplexity AI.")
#         messages = conversation_history or []
#         messages.append({"role": "user", "content": query})
        
#         return self.perplexity_module.get_chat_completion_content(messages=messages)

#     def get_pentest_analysis(self,
#                              tool_name: str,
#                              tool_output: str
#                              ) -> Optional[Dict]:
#         """
#         A convenience method to get analysis of pentesting tool output.
#         Uses the specialized PentestGPT module.
#         """
#         logger.info("Requesting pentesting analysis from PentestGPT module.")
#         return self.pentest_gpt_module.analyze_tool_output(tool_name=tool_name, tool_output=tool_output)

#     def get_pentest_action_suggestion(self, current_phase: str) -> Optional[List[str]]:
#         """
#         A convenience method to get next-step suggestions for a pentest.
#         Uses the specialized PentestGPT module.
#         """
#         logger.info("Requesting pentesting action suggestions from PentestGPT module.")
#         return self.pentest_gpt_module.suggest_next_pentest_actions(current_phase=current_phase)

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== All AIs Module (AIAgent) Prototype 🤖🌐 ===")
#     print("=========================================================")

#     # Initialize the central AIAgent
#     # It conceptually loads all underlying modules.
#     ai_agent = AIAgent()

#     # --- 1. Get a response from the default provider (OpenAI) ---
#     print("\n--- Task 1: General question for default provider (OpenAI) ---")
#     prompt_1 = "Explain the difference between TCP and UDP in one sentence."
#     messages_1 = [{"role": "user", "content": prompt_1}]
#     response_1 = ai_agent.get_general_chat_response(messages_1, provider=AIProvider.OPENAI)
#     print(f"  User: {prompt_1}")
#     print(f"  Agent (via OpenAI): {response_1}")

#     # --- 2. Get a response from Google Gemini ---
#     print("\n--- Task 2: Creative writing task for Google Gemini ---")
#     prompt_2 = "Write a haiku about a software bug."
#     messages_2 = [{"role": "user", "content": prompt_2}]
#     response_2 = ai_agent.get_general_chat_response(messages_2, provider=AIProvider.GOOGLE)
#     print(f"  User: {prompt_2}")
#     print(f"  Agent (via Google): {response_2}")

#     # --- 3. Use the search-augmented convenience method (Perplexity) ---
#     print("\n--- Task 3: Search-augmented query for Perplexity ---")
#     prompt_3 = "What is the current status of the Artemis program?"
#     response_3 = ai_agent.get_search_augmented_response(query=prompt_3)
#     print(f"  User: {prompt_3}")
#     print(f"  Agent (via Perplexity): {response_3}")

#     # --- 4. Use the specialized PentestGPT convenience method ---
#     print("\n--- Task 4: Pentesting analysis via PentestGPT ---")
#     dummy_nmap = "Host is up. PORT 80/tcp open http. PORT 443/tcp open https."
#     pentest_analysis = ai_agent.get_pentest_analysis("Nmap", dummy_nmap)
#     print(f"  Input: Nmap scan output...")
#     print(f"  Agent (via PentestGPT): {pentest_analysis}")

#     pentest_suggestions = ai_agent.get_pentest_action_suggestion("Initial Reconnaissance")
#     print(f"\n  Input: Suggest actions for 'Initial Reconnaissance' phase...")
#     print(f"  Agent (via PentestGPT): {pentest_suggestions}")
    
#     print("\n=========================================================")
#     print("=== AIAgent Prototype Demonstration Complete ===")
#     print("=========================================================")




# Devin/modules/all_ais_modules.py
# Purpose: A facade that provides a unified interface to all underlying AI
#          model modules, acting as a central agent for AI-driven tasks.
#          Includes a "Mock Mode" for offline/free development.

import logging
import os
import json
from enum import Enum, auto
from typing import List, Dict, Any, Optional

# --- Import the REAL, integrated AI modules ---
try:
    from modules.chatgpt_module import ChatGPTModule
    from modules.Gemini_module import GeminiModule
    from modules.perplexity_module import PerplexityModule
    from modules.pentestgpt_ai_module import PentestGPTAIModule
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

logger = logging.getLogger("AIAgent")
# (Logger setup assumed)

class AIProvider(Enum):
    OPENAI = auto()
    GOOGLE = auto()
    PERPLEXITY = auto()
    PENTEST_GPT = auto()

# --- ADDED FEATURE: Mock AI Modules for Offline/Free Use ---

class MockChatGPTModule:
    """A mock version of ChatGPTModule that returns canned responses."""
    def __init__(self, api_key=None): logger.info("Initialized MOCK ChatGPTModule.")
    def get_chat_completion_content(self, messages: List[Dict], config: Optional[Dict] = None) -> str:
        return "This is a mocked response from the offline ChatGPT module."
    # def get_tool_calling_response(self, messages: List[Dict], tools: List[Dict]) -> Dict:
    #     logger.info("MOCK ChatGPTModule is selecting a tool...")
    #     user_prompt = messages[-1]['content'].lower()
    #     if "list" in user_prompt and "file" in user_prompt:
    #         return {"tool_calls": [{"function": {"name": "list_files", "arguments": '{"path": "."}'}}]}
    #     elif "read" in user_prompt:
    #         return {"tool_calls": [{"function": {"name": "read_file", "arguments": '{"path": "README.md"}'}}]}
    #     else:
    #         return {"content": "I'm not sure which tool to use. Can you be more specific?"}
    def get_tool_calling_response(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        logger.info("MOCK ChatGPTModule is selecting a tool...")
        user_prompt = ""
        for msg in reversed(messages):
            if msg['role'] == 'user':
                user_prompt = msg['content'].lower()
                break
        
        # --- UPGRADED MOCK LOGIC ---
        if "list" in user_prompt and "file" in user_prompt:
            return {"tool_calls": [{"function": {"name": "list_files", "arguments": '{"path": "."}'}}]}
        elif "read" in user_prompt:
            return {"tool_calls": [{"function": {"name": "read_file", "arguments": '{"path": "README.md"}'}}]}
        else:
            # Instead of giving up, ask for clarification.
            return {"content": f"I am a mock AI and I don't understand the goal '{user_prompt}'. Please provide a more specific task, like 'list the files in the current directory.'"}

class MockGeminiModule:
    def __init__(self, api_key=None): logger.info("Initialized MOCK GeminiModule.")
    def get_chat_completion_content(self, messages: List[Dict], config: Optional[Dict] = None) -> str:
        return "This is a mocked response from the offline Gemini module."

class MockPerplexityModule:
    def __init__(self, api_key=None): logger.info("Initialized MOCK PerplexityModule.")
    def get_chat_completion_content(self, messages: List[Dict], config: Optional[Dict] = None) -> str:
        return "This is a mocked response from the offline Perplexity module."

class MockPentestGPTModule:
    def __init__(self, llm_interface=None): logger.info("Initialized MOCK PentestGPTModule.")
    def analyze_tool_output(self, tool_name: str, tool_output: str) -> Dict:
        return {
            "findings": ["Mock finding based on tool output."],
            "vulnerabilities": ["Mock vulnerability assessment."],
            "next_step": "Mock suggestion for the next step."
        }


class AIAgent:
    """A unified agent that can operate in 'live' or 'mock' mode."""
    def __init__(self, mode: str = 'live', **kwargs):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin AI module is missing. Error: {_import_error}")

        self.mode = mode.lower()
        logger.info(f"Initializing AIAgent in '{self.mode.upper()}' mode...")

        if self.mode == 'live':
            # --- LIVE MODE: Initialize real API clients ---
            self.openai_module = ChatGPTModule(api_key=kwargs.get("openai_api_key")) if kwargs.get("openai_api_key") else None
            self.gemini_module = GeminiModule(api_key=kwargs.get("gemini_api_key")) if kwargs.get("gemini_api_key") else None
            self.perplexity_module = PerplexityModule(api_key=kwargs.get("perplexity_api_key")) if kwargs.get("perplexity_api_key") else None
            self.pentest_gpt_module = PentestGPTAIModule(llm_interface=self.openai_module) if self.openai_module else None
        else:
            # --- MOCK MODE: Initialize mock clients ---
            self.openai_module = MockChatGPTModule()
            self.gemini_module = MockGeminiModule()
            self.perplexity_module = MockPerplexityModule()
            self.pentest_gpt_module = MockPentestGPTModule()

        self.provider_map = {
            AIProvider.OPENAI: self.openai_module,
            AIProvider.GOOGLE: self.gemini_module,
            AIProvider.PERPLEXITY: self.perplexity_module,
            AIProvider.PENTEST_GPT: self.pentest_gpt_module,
        }
        logger.info("AIAgent initialization complete.")
        
    def get_tool_selection_response(self, messages: List[Dict], tools: List[Dict]) -> Optional[Dict]:
        """
        The core thinking process for tool use. Asks the LLM to choose the next best action
        using the provider's native tool-calling feature for improved reliability.
        """
        # logger.info("AIAgent is selecting a tool to achieve the goal using native tool calling...")
        logger.info("AIAgent is selecting a tool to achieve the goal...")
        if not self.openai_module:
            logger.error("OpenAI module is required for tool selection but is not configured.")
            return None
        
        try:
            # Use the most powerful model for this critical reasoning step
            openai_tools = [{"type": "function", "function": tool} for tool in tools]
            response_message = self.openai_module.get_tool_calling_response(messages, openai_tools)

            if response_message and response_message.get("tool_calls"):
                tool_call = response_message["tool_calls"][0]
                selected_tool = {
                    "tool": tool_call["function"]["name"],
                    "parameters": json.loads(tool_call["function"]["arguments"])
                }
                logger.info(f"AIAgent selected tool: {selected_tool['tool']}")
                return selected_tool
            else:
                # The model decided not to call a tool and just responded with text.
                # This can be interpreted as task completion or a request for clarification.
                reason = response_message.get("content", "The model chose to respond instead of using a tool.")
                return {"tool": "task_complete", "parameters": {"reason": reason}}

        except Exception as e:
            logger.error(f"Failed to get or parse tool selection response: {e}")
            return None
    
    def get_general_chat_response(self,
                                  messages: List[Dict[str, str]],
                                  provider: AIProvider = AIProvider.OPENAI,
                                  config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Gets a general-purpose chat response from a specified AI provider."""
        config = config or {}
        module = self.provider_map.get(provider)
        if not module:
            return f"Error: Provider '{provider.name}' is not configured or its API key is missing."
            
        logger.info(f"Requesting general chat response from provider: {provider.name}")

        # The underlying modules now all have a `get_chat_completion_content` adapter
        return module.get_chat_completion_content(messages=messages, config=config)

    # --- ADDED FEATURE: Specialized Code Generation ---
    def generate_code(self, prompt: str, language: str, provider: AIProvider = AIProvider.OPENAI) -> Optional[str]:
        """Generates a code snippet using a specialized prompt."""
        logger.info(f"Requesting {language} code generation from {provider.name}...")
        system_prompt = (
            f"You are an expert {language} programmer. Your task is to write a complete, functional, "
            f"and well-documented code snippet for the following request. "
            f"Respond ONLY with the code inside a markdown block (e.g., ```python...```)."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.get_general_chat_response(messages, provider, {"temperature": 0.1})
        
        # Clean up markdown fences if present
        if response and f"```{language}" in response:
            return response.split(f"```{language}\n")[1].split("\n```")[0]
        elif response and "```" in response:
            return response.strip().strip("`").strip()
            
        return response

    def get_search_augmented_response(self, query: str) -> Optional[str]:
        """Convenience method to get a response from a search-augmented AI (Perplexity)."""
        if not self.perplexity_module:
            return "Error: Perplexity AI module is not configured."
        messages = [{"role": "user", "content": query}]
        return self.perplexity_module.get_chat_completion_content(messages=messages)

    def get_pentest_analysis(self, tool_name: str, tool_output: str) -> Optional[Dict]:
        """Convenience method for pentesting analysis via PentestGPT."""
        if not self.pentest_gpt_module:
            return {"error": "PentestGPT AI module is not configured."}
        return self.pentest_gpt_module.analyze_tool_output(tool_name=tool_name, tool_output=tool_output)

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== All AIs Module (AIAgent) - Live Integration 🤖🌐 ===")
    print("=========================================================")

    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not all([openai_key, gemini_key, perplexity_key]):
        print("\nERROR: One or more API keys are not set.")
    else:
        ai_agent = AIAgent(
            openai_api_key=openai_key,
            gemini_api_key=gemini_key,
            perplexity_api_key=perplexity_key
        )

        # --- Use Cases from your version ---
        # ... (Task 1: OpenAI, Task 2: Gemini, Task 3: Perplexity, Task 4: PentestGPT) ...

        # --- 5. ADDED DEMO: Tool Selection using Native API Feature ---
        print("\n--- 5. Task: Tool Selection for a user goal ---")
        user_goal = "What is the weather like in Lahore?"
        conversation = [{"role": "user", "content": user_goal}]
        # Convert our tool schema to OpenAI's required format
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": { "location": {"type": "string"} },
                        "required": ["location"],
                    },
                },
            }
        ]
        decision = ai_agent.get_tool_selection_response(conversation, available_tools)
        print(f"  > User Goal: {user_goal}")
        print(f"  < AI's Decision:\n{json.dumps(decision, indent=2)}")

        # --- 6. ADDED DEMO: Specialized Code Generation ---
        print("\n--- 6. Task: Specialized Code Generation ---")
        code_prompt = "Create a Python function that takes a URL and returns the title of the web page using the requests and BeautifulSoup libraries."
        generated_code = ai_agent.generate_code(code_prompt, "python")
        print(f"  > Code Prompt: {code_prompt}")
        print(f"  < Generated Python Code:\n{generated_code}")


    print("\n=========================================================")
    print("=== AIAgent Live Demonstration Complete ===")
    print("=========================================================")
