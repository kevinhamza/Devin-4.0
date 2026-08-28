# # Devin/modules/ai_conversation_module.py
# # Purpose: Handles real-time NLP conversations, managing state, history,
# #          and conceptual interaction with a Large Language Model (LLM).
# # Handles real-time NLP conversations 💬

# import logging
# from datetime import datetime, timezone
# from typing import List, Dict, Any, Optional, Callable
# from dataclasses import dataclass, field
# import uuid
# from collections import defaultdict

# # Configure basic logging
# logger = logging.getLogger("AIConversationModule")
# if not logger.handlers: # Prevent duplicate handlers
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# @dataclass
# class ConversationTurn:
#     """Represents a single turn in a conversation."""
#     turn_id: str = field(default_factory=lambda: f"turn_{uuid.uuid4().hex[:8]}")
#     role: Literal["user", "assistant", "system"] 
#     content: str
#     timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
#     metadata: Optional[Dict[str, Any]] = field(default_factory=dict) # For intent, entities, etc.

# class ConceptualLLMInterface:
#     """
#     A placeholder/abstract class for interacting with a Large Language Model.
#     In a real system, this would make API calls to services like OpenAI, Gemini, Anthropic, etc.
#     """
#     def __init__(self, model_name: str = "conceptual-llm-v1"):
#         self.model_name = model_name
#         logger.info(f"ConceptualLLMInterface initialized for model: {self.model_name}")

#     def generate_response(self, prompt_messages: List[Dict[str, str]]) -> str:
#         """
#         Simulates generating a response from an LLM based on a list of message objects.
#         Each message object should be like: {"role": "user/assistant/system", "content": "..."}
#         """
#         # Simple simulation: Echo parts of the last user message or provide a canned response.
#         logger.debug(f"ConceptualLLMInterface received prompt messages: {prompt_messages}")
#         last_user_message = ""
#         for msg in reversed(prompt_messages):
#             if msg.get("role") == "user":
#                 last_user_message = msg.get("content", "")
#                 break
        
#         if "hello" in last_user_message.lower():
#             return f"Hello there! I am {self.model_name}. How can I assist you today?"
#         elif "weather" in last_user_message.lower():
#             return f"As {self.model_name}, I can't check real-time weather, but I hope it's pleasant!"
#         elif "help" in last_user_message.lower():
#             return f"I'm here to help! What do you need assistance with from {self.model_name}?"
#         elif "previous question" in last_user_message.lower() and len(prompt_messages) > 2:
#              # Try to find the actual previous user question from the prompt
#             previous_q = "your previous question" # default
#             for i in range(len(prompt_messages) - 2, -1, -1): # Search backwards, skipping last AI and last user msg
#                 if prompt_messages[i].get("role") == "user":
#                     previous_q = f"'{prompt_messages[i].get('content', 'your previous question')}'"
#                     break
#             return f"You were asking about {previous_q}. What more would you like to know?"

#         return f"I'm {self.model_name}. I received: '{last_user_message}'. How can I elaborate or help further?"

#     async def generate_response_async(self, prompt_messages: List[Dict[str, str]]) -> str:
#         """Async version of generate_response for conceptual concurrent processing."""
#         # In a real scenario, this would use an async HTTP client.
#         # For simulation, it's the same as the sync version.
#         logger.info(f"ConceptualLLMInterface (async) generating response for: {prompt_messages[-1]['content'][:50]}...")
#         # await asyncio.sleep(0.1) # Simulate network latency
#         return self.generate_response(prompt_messages)


# class AIConversationManager:
#     """
#     Manages AI conversations, including history, context, and interaction with an LLM.
#     """
#     DEFAULT_SYSTEM_PROMPT = "You are Devin, a highly capable AI assistant. Be helpful, concise, and professional."

#     def __init__(self,
#                  llm_interface: ConceptualLLMInterface,
#                  default_system_prompt: Optional[str] = None,
#                  max_history_turns: int = 10, # Max number of recent turns (user + assistant) to keep for context
#                  max_tokens_for_history_conceptual: int = 2000): # Conceptual token limit for history part of prompt
        
#         self.llm_interface = llm_interface
#         self.default_system_prompt = default_system_prompt or self.DEFAULT_SYSTEM_PROMPT
#         self.max_history_turns = max_history_turns # Simple turn-based truncation
#         self.max_tokens_history = max_tokens_for_history_conceptual # Conceptual token limit
        
#         # Stores conversation history per user_id
#         # Each history is a list of ConversationTurn objects
#         self.conversations: Dict[str, List[ConversationTurn]] = defaultdict(list)
#         logger.info(f"AIConversationManager initialized. Max history turns: {max_history_turns}.")

#     def _get_or_create_user_history(self, user_id: str) -> List[ConversationTurn]:
#         """Retrieves or initializes conversation history for a user."""
#         if user_id not in self.conversations:
#             logger.info(f"New conversation started for user_id: {user_id}")
#             # Optionally add an initial system message to the history if your LLM prefers it that way
#             # self.conversations[user_id].append(ConversationTurn(role="system", content=self.default_system_prompt))
#         return self.conversations[user_id]

#     def _format_prompt_messages_for_llm(self, user_id: str, current_user_message: str) -> List[Dict[str, str]]:
#         """
#         Formats the conversation history and new message into a list of message objects
#         suitable for modern chat-based LLMs. Applies truncation.
#         """
#         history = self._get_or_create_user_history(user_id)
        
#         messages: List[Dict[str, str]] = []
        
#         # 1. Add system prompt
#         messages.append({"role": "system", "content": self.default_system_prompt})
        
#         # 2. Add recent conversation history (user and assistant turns)
#         # Simple turn-based truncation first
#         relevant_history = history[-(self.max_history_turns * 2):] # User + Assistant pairs

#         # Conceptual token-based truncation (very simplified)
#         # In a real system, you'd use a tokenizer (e.g., tiktoken for OpenAI models)
#         current_token_count = 0
#         temp_history_for_prompt = []

#         for turn in reversed(relevant_history):
#             # Rough estimate: 1 word ~ 1.3 tokens. Or 4 chars per token.
#             turn_tokens_estimate = len(turn.content.split()) * 1.3 
#             if current_token_count + turn_tokens_estimate < self.max_tokens_history:
#                 temp_history_for_prompt.append({"role": turn.role, "content": turn.content})
#                 current_token_count += turn_tokens_estimate
#             else:
#                 logger.debug(f"History truncation for user '{user_id}' due to conceptual token limit.")
#                 break
        
#         messages.extend(reversed(temp_history_for_prompt)) # Add in chronological order

#         # 3. Add current user message
#         messages.append({"role": "user", "content": current_user_message})
        
#         return messages

#     def send_message(self, user_id: str, user_message: str) -> str:
#         """
#         Processes a user's message, gets a response from the LLM, and updates history.

#         Args:
#             user_id (str): Identifier for the user.
#             user_message (str): The user's input message.

#         Returns:
#             str: The AI assistant's response.
#         """
#         logger.info(f"User '{user_id}' said: \"{user_message[:100]}{'...' if len(user_message)>100 else ''}\"")
#         history = self._get_or_create_user_history(user_id)

#         # Record user's message in history
#         user_turn = ConversationTurn(role="user", content=user_message)
#         history.append(user_turn)

#         # Prepare prompt for LLM
#         prompt_messages = self._format_prompt_messages_for_llm(user_id, user_message)
        
#         # Get response from LLM (conceptual)
#         try:
#             ai_response_content = self.llm_interface.generate_response(prompt_messages)
#             logger.info(f"AI response for '{user_id}': \"{ai_response_content[:100]}{'...' if len(ai_response_content)>100 else ''}\"")
#         except Exception as e:
#             logger.error(f"Error calling LLM interface for user '{user_id}': {e}")
#             ai_response_content = "I'm sorry, I encountered an error trying to process your request."

#         # Record AI's response in history
#         ai_turn = ConversationTurn(role="assistant", content=ai_response_content)
#         history.append(ai_turn)
        
#         return ai_response_content

#     async def send_message_async(self, user_id: str, user_message: str) -> str:
#         """Async version of send_message."""
#         logger.info(f"User '{user_id}' (async) said: \"{user_message[:100]}{'...' if len(user_message)>100 else ''}\"")
#         history = self._get_or_create_user_history(user_id)
#         user_turn = ConversationTurn(role="user", content=user_message)
#         history.append(user_turn)
#         prompt_messages = self._format_prompt_messages_for_llm(user_id, user_message)
        
#         try:
#             ai_response_content = await self.llm_interface.generate_response_async(prompt_messages)
#             logger.info(f"AI response (async) for '{user_id}': \"{ai_response_content[:100]}{'...' if len(ai_response_content)>100 else ''}\"")
#         except Exception as e:
#             logger.error(f"Error calling async LLM interface for user '{user_id}': {e}")
#             ai_response_content = "I'm sorry, I encountered an error trying to process your request (async)."
        
#         ai_turn = ConversationTurn(role="assistant", content=ai_response_content)
#         history.append(ai_turn)
#         return ai_response_content


#     def get_conversation_history(self, user_id: str, last_n_turns: Optional[int] = None) -> List[ConversationTurn]:
#         """Retrieves the conversation history for a user."""
#         history = self.conversations.get(user_id, [])
#         if last_n_turns is not None and last_n_turns > 0:
#             return history[-last_n_turns:]
#         return history
    
#     def get_formatted_conversation_string(self, user_id: str, last_n_turns: Optional[int] = None) -> str:
#         """Returns the conversation history as a simple formatted string."""
#         history = self.get_conversation_history(user_id, last_n_turns)
#         if not history:
#             return "No conversation history found for this user."
        
#         formatted_lines = [f"Conversation History for User: {user_id}"]
#         for turn in history:
#             formatted_lines.append(f"  [{turn.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {turn.role.capitalize()}: {turn.content}")
#         return "\n".join(formatted_lines)

#     def clear_user_history(self, user_id: str) -> None:
#         """Clears the conversation history for a specific user."""
#         if user_id in self.conversations:
#             self.conversations[user_id] = []
#             logger.info(f"Conversation history cleared for user_id: {user_id}")
#         else:
#             logger.info(f"No history found to clear for user_id: {user_id}")

#     def set_default_system_prompt(self, system_prompt: str):
#         """Sets a new default system prompt."""
#         self.default_system_prompt = system_prompt
#         logger.info(f"Default system prompt updated to: \"{system_prompt[:100]}...\"")


# # Example Usage (Synchronous)
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== AI Conversation Module Prototype 💬 ===")
#     print("=========================================================")

#     # 1. Initialize conceptual LLM and Conversation Manager
#     conceptual_llm = ConceptualLLMInterface(model_name="Devin-Sim-LLM-v0.1")
#     convo_manager = AIConversationManager(llm_interface=conceptual_llm, max_history_turns=5)

#     # 2. Simulate a conversation with User1
#     user1_id = "user_alpha_123"
#     print(f"\n--- Conversation with {user1_id} ---")

#     response1 = convo_manager.send_message(user1_id, "Hello Devin!")
#     print(f"  Devin ({user1_id}): {response1}")

#     response2 = convo_manager.send_message(user1_id, "Can you tell me about the weather today?")
#     print(f"  Devin ({user1_id}): {response2}")
    
#     response3 = convo_manager.send_message(user1_id, "What was my previous question?")
#     print(f"  Devin ({user1_id}): {response3}")

#     response4 = convo_manager.send_message(user1_id, "Thanks for the help.")
#     print(f"  Devin ({user1_id}): {response4}")

#     # 3. Simulate a conversation with User2 (to show separate history)
#     user2_id = "user_beta_456"
#     print(f"\n--- Conversation with {user2_id} ---")
#     response_u2_1 = convo_manager.send_message(user2_id, "Hi, I need help with Python.")
#     print(f"  Devin ({user2_id}): {response_u2_1}")

#     # 4. Display conversation history for User1
#     print(f"\n--- History for {user1_id} (last 6 turns) ---")
#     history_user1_str = convo_manager.get_formatted_conversation_string(user1_id, last_n_turns=6)
#     print(history_user1_str)
    
#     # 5. Display conversation history for User2
#     print(f"\n--- History for {user2_id} ---")
#     history_user2_str = convo_manager.get_formatted_conversation_string(user2_id)
#     print(history_user2_str)

#     # 6. Clear history for User1 and verify
#     convo_manager.clear_user_history(user1_id)
#     print(f"\n--- History for {user1_id} after clearing ---")
#     history_user1_cleared_str = convo_manager.get_formatted_conversation_string(user1_id)
#     print(history_user1_cleared_str)
    
#     # Test async version conceptually (requires an async runtime like asyncio to actually run)
#     # async def run_async_example():
#     #     user3_id = "user_gamma_789"
#     #     print(f"\n--- Async Conversation with {user3_id} (Conceptual) ---")
#     #     resp_async = await convo_manager.send_message_async(user3_id, "Hello asynchronously!")
#     #     print(f"  Devin ({user3_id}) (async): {resp_async}")
#     #
#     # import asyncio
#     # asyncio.run(run_async_example())


#     print("\n=========================================================")
#     print("=== AI Conversation Module Prototype Complete ===")
#     print("=========================================================")



# Devin/modules/ai_conversation_module.py
# Purpose: The central controller for handling the logic of an AI conversation.
# It orchestrates the chatbot engine, safety checkers, and task orchestrator.

import logging
from typing import Dict, Any

try:
    from modules.ai_tools.chatbot_engine import ChatbotEngine
    from servers.task_orchestrator import TaskOrchestrator
    from security.compliance.cfaa_checker import CFAAChecker, RulesOfEngagement
    from security.ethical_enforcer.three_laws_compliance import EthicalEnforcer
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("AIConversationModule")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class AIConversationModule:
    """
    The core controller for processing user input and dispatching safe actions.
    """
    def __init__(
        self,
        orchestrator: TaskOrchestrator,
        chatbot_engine: ChatbotEngine,
        cfaa_checker: CFAAChecker,
        ethical_enforcer: EthicalEnforcer
    ):
        """
        Initializes the module with all its dependencies.
        """
        self.orchestrator = orchestrator
        self.chatbot_engine = chatbot_engine
        self.cfaa_checker = cfaa_checker
        self.ethical_enforcer = ethical_enforcer
        logger.info("AI Conversation Module initialized with all core components.")

    def process_and_dispatch(self, user_message: str) -> Dict[str, Any]:
        """
        The main method that handles one full turn of a user conversation.
        """
        logger.info(f"Processing user message: '{user_message}'")
        
        # --- 1. Intent Parsing ---
        ai_responses = self.chatbot_engine.process_user_message(user_message)
        
        final_text_reply = ""
        submitted_tasks = []
        rejected_tasks = []

        for response in ai_responses:
            if response['type'] == 'text':
                final_text_reply += response.get('content', '') + "\n"
            
            elif response['type'] == 'tool_call':
                tool_name = response.get('function_name')
                params = response.get('arguments', {})
                target = params.get('target') or params.get('url') # Common parameter for scope checks
                
                # --- 2. Safety & Compliance Middleware Chain ---
                is_safe_to_run = True
                rejection_reason = ""

                # CFAA Check (if a target is specified)
                if target:
                    is_auth, reason = self.cfaa_checker.is_authorized(action=tool_name, target=target)
                    if not is_auth:
                        is_safe_to_run = False
                        rejection_reason = f"CFAA Safeguard Blocked: {reason}"
                
                # Ethical Check (always run for tool calls)
                if is_safe_to_run:
                    action_description = f"Execute the tool '{tool_name}' with the following parameters: {json.dumps(params)}"
                    ethical_verdict = self.ethical_enforcer.check_compliance(action_description)
                    if ethical_verdict and ethical_verdict.get("decision") == "DENY":
                        is_safe_to_run = False
                        rejection_reason = f"Ethical Enforcer Blocked: {ethical_verdict.get('final_rationale')}"

                # --- 3. Dispatch or Reject ---
                if is_safe_to_run:
                    task_id = self.orchestrator.submit_task(tool_name, params)
                    submitted_tasks.append({"tool_name": tool_name, "task_id": task_id})
                    logger.info(f"Action '{tool_name}' passed all checks and was dispatched.")
                else:
                    rejected_tasks.append({"tool_name": tool_name, "reason": rejection_reason})
                    logger.critical(f"Action '{tool_name}' was blocked. Reason: {rejection_reason}")

        return {
            "text_reply": final_text_reply.strip(),
            "submitted_tasks": submitted_tasks,
            "rejected_tasks": rejected_tasks
        }

# --- Example Usage ---
if __name__ == "__main__":
    import os
    import json
    
    print("=========================================================")
    print("=== AI Conversation Controller Prototype 🧠🚦 ===")
    print("=========================================================")

    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module is missing. Error: {_import_error}")
    elif not os.getenv("OPENAI_API_KEY"):
         print("\nERROR: OPENAI_API_KEY environment variable is required.")
    else:
        # --- 1. Setup all backend components for the demo ---
        print("\n--- Initializing Devin's Backend Services ---")
        orchestrator = TaskOrchestrator(num_workers=2)
        chatbot = ChatbotEngine()
        ethical_enforcer = EthicalEnforcer()
        
        # Define sample Rules of Engagement
        roe = RulesOfEngagement(
            project_name="Demo Project",
            authorized_scopes=["192.168.1.0/24", "example.com"],
            authorized_actions=["modules.pentesting_tools.network_scanner.scan_host"]
        )
        cfaa_checker = CFAAChecker(roe)
        
        # Instantiate the main conversation controller
        conversation_module = AIConversationModule(
            orchestrator, chatbot, cfaa_checker, ethical_enforcer
        )
        
        # --- 2. Run Test Cases ---
        test_prompts = [
            "Please run a port scan on 192.168.1.100.",       # Should be ALLOWED
            "Can you scan the host 8.8.8.8 for me?",          # Should be BLOCKED by CFAA checker
            "Delete all files in the /tmp directory.",        # Should be BLOCKED by Ethical Enforcer
            "What is the capital of Pakistan?",               # Should be a TEXT reply
        ]
        
        for prompt in test_prompts:
            print(f"\n\n--- Testing Prompt: '{prompt}' ---")
            result = conversation_module.process_and_dispatch(prompt)
            print("\n--- Final Response ---")
            print(json.dumps(result, indent=2))

        orchestrator.shutdown()

    print("\n=========================================================")
    print("=== Conversation Controller Prototype Complete ===")
    print("=========================================================")
