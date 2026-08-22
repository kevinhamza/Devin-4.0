# Devin/modules/claude_module.py
# Purpose: Interacts with the live Anthropic Claude API for chat and native
#          tool calling, following the same interface as ChatGPTModule /
#          GeminiModule so it can be used as a drop-in reasoning backend.

import json
import logging
import os
from typing import Any, Dict, List, Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger("ClaudeModule")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class ClaudeModule:
    """
    Interacts with the live Anthropic Claude API. Exposes the same
    get_chat_completion_content / get_tool_calling_response interface as
    ChatGPTModule so AIAgent can use either interchangeably.
    """
    DEFAULT_MODEL = "claude-opus-5"
    DEFAULT_MAX_TOKENS = 4096

    def __init__(self, api_key: Optional[str] = None):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("The 'anthropic' library is required. 'pip install anthropic'")

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set it via the ANTHROPIC_API_KEY environment variable.")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info("ClaudeModule initialized with live Anthropic client.")

    @staticmethod
    def _convert_messages(messages: List[Dict[str, Any]]) -> (List[Dict[str, Any]], Optional[str]):
        """
        Converts this codebase's flat role/content history (which also uses a
        bare "tool" role with no tool_use_id linkage) into Claude's
        user/assistant-only message format, pulling out any "system" entries
        into a separate system prompt.
        """
        claude_messages: List[Dict[str, Any]] = []
        system_parts: List[str] = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                system_parts.append(str(content))
            elif role == "user":
                claude_messages.append({"role": "user", "content": str(content)})
            elif role == "assistant":
                claude_messages.append({"role": "assistant", "content": str(content)})
            elif role == "tool":
                # Claude has no bare "tool" role outside a proper tool_result
                # block tied to a tool_use_id; this codebase's own history
                # doesn't track that linkage either, so fold it in as
                # user-visible context, same level of simplification already
                # used elsewhere in this file's callers.
                claude_messages.append({"role": "user", "content": f"[Tool result]: {content}"})

        if not claude_messages or claude_messages[0]["role"] != "user":
            claude_messages.insert(0, {"role": "user", "content": "Continue."})

        system_prompt = "\n".join(system_parts) if system_parts else None
        return claude_messages, system_prompt

    @staticmethod
    def _convert_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Converts OpenAI-style {"type": "function", "function": {...}} tool defs to Claude's flat tool schema."""
        claude_tools = []
        for t in tools:
            func = t.get("function", t)
            claude_tools.append({
                "name": func["name"],
                "description": func.get("description", ""),
                "input_schema": func.get("parameters") or {"type": "object", "properties": {}},
            })
        return claude_tools

    def get_chat_completion_content(self, messages: List[Dict[str, Any]], config: Optional[Dict] = None) -> Optional[str]:
        """Gets a general chat completion from Claude, returning only the text content."""
        claude_messages, system_prompt = self._convert_messages(messages)
        kwargs: Dict[str, Any] = {
            "model": self.DEFAULT_MODEL,
            "max_tokens": self.DEFAULT_MAX_TOKENS,
            "messages": claude_messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = self.client.messages.create(**kwargs)
            return " ".join(block.text for block in response.content if block.type == "text")
        except anthropic.AuthenticationError:
            logger.error("Claude API authentication failed. Check ANTHROPIC_API_KEY.")
            return "Error: Claude authentication failed."
        except anthropic.RateLimitError as e:
            logger.error(f"Claude API rate limit hit: {e}")
            return "Error: Claude rate limit exceeded."
        except anthropic.APIStatusError as e:
            logger.error(f"Claude API error: {e}")
            return f"Error: {e}"
        except anthropic.APIConnectionError as e:
            logger.error(f"Could not connect to Claude API: {e}")
            return "Error: Could not connect to the Claude API."

    def get_tool_calling_response(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Gets a response that may be a text message or a request to call a
        tool, normalized into the same shape ChatGPTModule.get_tool_calling_response
        returns (an OpenAI-style message dict) so AIAgent can treat either
        provider identically.
        """
        claude_messages, system_prompt = self._convert_messages(messages)
        claude_tools = self._convert_tools(tools)
        kwargs: Dict[str, Any] = {
            "model": self.DEFAULT_MODEL,
            "max_tokens": self.DEFAULT_MAX_TOKENS,
            "tools": claude_tools,
            "messages": claude_messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = self.client.messages.create(**kwargs)
        except anthropic.AuthenticationError:
            logger.error("Claude API authentication failed. Check ANTHROPIC_API_KEY.")
            return {"content": "Error: Claude authentication failed."}
        except anthropic.RateLimitError as e:
            logger.error(f"Claude API rate limit hit: {e}")
            return {"content": "Error: Claude rate limit exceeded."}
        except anthropic.APIStatusError as e:
            logger.error(f"Claude API error during tool calling request: {e}")
            return {"content": f"Error: {e}"}
        except anthropic.APIConnectionError as e:
            logger.error(f"Could not connect to Claude API: {e}")
            return {"content": "Error: Could not connect to the Claude API."}

        text_blocks = [block.text for block in response.content if block.type == "text"]
        tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

        if tool_use_blocks:
            block = tool_use_blocks[0]
            return {
                "role": "assistant",
                "content": " ".join(text_blocks) or None,
                "tool_calls": [{
                    "id": block.id,
                    "type": "function",
                    "function": {"name": block.name, "arguments": json.dumps(block.input)},
                }],
            }

        return {"role": "assistant", "content": " ".join(text_blocks) or "Task appears complete."}
