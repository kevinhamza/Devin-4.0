# Devin/modules/ai_tools/chatbot_engine.py
# Purpose: The core conversational AI engine for Devin, responsible for
#          understanding user intent and deciding which tool to use.

import logging
import os
import json
from typing import List, Dict, Optional, Any

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

# Configure basic logging
logger = logging.getLogger("ChatbotEngine")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class ChatbotEngine:
    """
    Manages the conversation with the user and translates their requests
    into structured, executable commands using an LLM.
    """
    def __init__(self, openai_api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Please 'pip install openai'.")
            
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.client = openai.OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized for Chatbot Engine.")
        else:
            self.client = None
            raise ValueError("OPENAI_API_KEY environment variable not set.")

        self.conversation_history: List[Dict[str, Any]] = []
        self._initialize_system_prompt_and_tools()

    def _initialize_system_prompt_and_tools(self):
        """Defines the persona, rules, and available tools for the AI."""
        
        # The System Prompt is the master instruction for the AI's behavior.
        self.system_prompt = {
            "role": "system",
            "content": (
                "You are Devin, a world-class AI penetration testing assistant. Your primary goal is to help users by executing security tools based on their requests. "
                "You are precise, professional, and you always prioritize safety and ethics.\n\n"
                "RULES:\n"
                "1. **Understand the Goal:** Analyze the user's request to understand their ultimate goal.\n"
                "2. **Clarify Ambiguity:** If a request is unclear (e.g., 'scan the server'), ask for clarification (e.g., 'Which server? Which ports should I scan?').\n"
                "3. **Select the Right Tool:** Based on the user's goal, select the appropriate tool from the available functions.\n"
                "4. **Confirm Before Acting:** Before executing any active or potentially disruptive tool (like a vulnerability scan or exploit), YOU MUST ask the user for confirmation.\n"
                "5. **Be Concise:** Keep your responses clear and to the point.\n"
                "6. **Structured Tool Calls:** When you decide to use a tool, you must use the provided tool-calling function to return a structured JSON command. Do not just describe the action in text."
            )
        }
        self.conversation_history.append(self.system_prompt)

        # The Tool Schema defines the functions the AI can "call".
        # This is a representative subset of the tools we have built.
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "run_subdomain_enumeration",
                    "description": "Finds subdomains for a given domain using various techniques.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "domain": {"type": "string", "description": "The target domain, e.g., 'example.com'"},
                            "use_bruteforce": {"type": "boolean", "description": "Whether to use a wordlist for brute-forcing."},
                            "wordlist_path": {"type": "string", "description": "Path to the wordlist file for brute-forcing."}
                        },
                        "required": ["domain"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_port_scan",
                    "description": "Scans a target IP or domain for open ports.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target": {"type": "string", "description": "The target IP address or domain."},
                            "ports": {"type": "string", "description": "A comma-separated list or range of ports, e.g., '22,80,443' or '1-1024'."}
                        },
                        "required": ["target", "ports"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_vulnerability_assessment",
                    "description": "Performs a full, automated vulnerability assessment (port scan, CVE search, etc.) against a target.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target": {"type": "string", "description": "The target IP address or domain."}
                        },
                        "required": ["target"]
                    }
                }
            }
        ]

    def process_user_message(self, message: str) -> List[Dict[str, Any]]:
        """
        Processes a user's message, interacts with the LLM, and returns the AI's response or intended tool call.
        """
        self.conversation_history.append({"role": "user", "content": message})
        
        logger.info("Sending request to LLM...")
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=self.conversation_history,
                tools=self.tools,
                tool_choice="auto",
            )
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return [{"type": "text", "content": "I'm sorry, I'm having trouble connecting to my brain right now."}]

        response_message = response.choices[0].message
        self.conversation_history.append(response_message) # Add AI response to history

        if response_message.tool_calls:
            # The AI wants to call one or more tools
            tool_calls = []
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_calls.append({
                    "type": "tool_call",
                    "function_name": function_name,
                    "arguments": function_args
                })
            return tool_calls
        else:
            # The AI is responding with a text message
            return [{"type": "text", "content": response_message.content}]

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Devin Chatbot Engine Prototype 🧠💬 ===")
    print("=========================================================")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set. This demo cannot run.")
    else:
        engine = ChatbotEngine()
        print("Devin: Hello! I am Devin, your AI penetration testing assistant. How can I help you today?")
        
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                responses = engine.process_user_message(user_input)
                
                for response in responses:
                    if response["type"] == "text":
                        print(f"Devin: {response['content']}")
                    elif response["type"] == "tool_call":
                        print("\n--- [DEVIN ACTION REQUIRED] ---")
                        print(f"Tool to run: {response['function_name']}")
                        print(f"Parameters: {json.dumps(response['arguments'], indent=2)}")
                        print("-----------------------------\n")

            except (EOFError, KeyboardInterrupt):
                break
                
    print("\nDevin: Goodbye!")
    print("\n=========================================================")
    print("=== Chatbot Engine Prototype Complete ===")
    print("=========================================================")
