# Devin/modules/ollama_module.py
# Purpose: A fully local, zero-cost LLM provider via a local Ollama server --
#          conversational AI and tool-calling that works completely offline,
#          with no API key, no billing, and no cloud dependency at all.
#
# This is the offline-first idea behind itachity/Holomat's assist_local.py
# (a Jarvis-style voice assistant that falls back to a local Ollama model
# when no OpenAI key is configured), ported here as a first-class AIAgent
# provider -- alongside ChatGPTModule/GeminiModule/ClaudeModule -- rather
# than a standalone voice script, so any part of Devin can use a fully
# local model, not just voice interaction.

import json
import logging
from typing import Any, Dict, List, Optional

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logger = logging.getLogger("OllamaModule")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)
logger.propagate = False


class OllamaModule:
    """Talks to a local Ollama server -- no API key, no cloud, no cost."""

    def __init__(self, model: str = "llama3.1", host: Optional[str] = None):
        if not OLLAMA_AVAILABLE:
            raise ImportError("The 'ollama' package is required. 'pip install ollama'")
        self.model = model
        self.client = ollama.Client(host=host) if host else ollama.Client()

    def get_chat_completion_content(self, messages: List[Dict], config: Optional[Dict] = None) -> Optional[str]:
        """Gets a plain-text chat response from the local Ollama model."""
        try:
            response = self.client.chat(model=self.model, messages=messages)
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama chat request failed: {e}")
            return f"Error: local Ollama request failed ({e}). Is 'ollama serve' running with '{self.model}' pulled?"

    def get_tool_calling_response(self, messages: List[Dict], tools: List[Dict]) -> Dict[str, Any]:
        """
        Gets a response that may be a text message or a request to call a
        tool, using Ollama's native tool calling (requires a tool-capable
        local model, e.g. llama3.1 or qwen2.5), normalized into the same
        shape ChatGPTModule/GeminiModule/ClaudeModule return so AIAgent can
        treat any of them identically.
        """
        try:
            response = self.client.chat(model=self.model, messages=messages, tools=tools)
        except Exception as e:
            logger.error(f"Ollama tool-calling request failed: {e}")
            return {"content": f"Error: local Ollama request failed ({e}). Is 'ollama serve' running with '{self.model}' pulled?"}

        message = response.get("message", {}) if isinstance(response, dict) else dict(response.get("message", {}))
        tool_calls = message.get("tool_calls")
        if tool_calls:
            call = tool_calls[0]
            arguments = call["function"]["arguments"]
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": f"ollama-{call['function']['name']}",
                    "type": "function",
                    "function": {
                        "name": call["function"]["name"],
                        "arguments": json.dumps(arguments) if isinstance(arguments, dict) else arguments,
                    },
                }],
            }
        return {"role": "assistant", "content": message.get("content") or "Task appears complete."}
