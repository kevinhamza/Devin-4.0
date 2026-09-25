"""modules/conversation_engine.py — Claude-like Conversation Engine

Provides rich, context-aware conversation for Devin that:
- Maintains multi-turn conversation history with context compaction
- Supports streaming output with progress indicators
- Has a consistent helpful, direct personality
- Handles slash commands (/help, /clear, /status, /tools, etc.)
- Automatically picks the best available AI provider
- Renders Markdown in the terminal (bold, code blocks, lists)
- Integrates with memory for persistent knowledge across sessions
- Never gives up on a task without explaining why
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generator, List, Optional

log = logging.getLogger("ConversationEngine")
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.WARNING)
log.propagate = False

_IS_TTY = sys.stdout.isatty()


# ──────────────────────────────────────────────────────────────────────────────
# Terminal rendering helpers
# ──────────────────────────────────────────────────────────────────────────────

def _c(code: str, text: str) -> str:
    if not _IS_TTY:
        return text
    return f"\033[{code}m{text}\033[0m"


def _render_markdown(text: str) -> str:
    """Minimal terminal Markdown renderer."""
    if not _IS_TTY:
        return text

    lines = text.split("\n")
    out = []
    in_code_block = False
    code_lang = ""

    for line in lines:
        # Code block fence
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line[3:].strip()
                out.append(_c("2", f"── {code_lang or 'code'} " + "─" * 40))
            else:
                in_code_block = False
                out.append(_c("2", "─" * 48))
            continue

        if in_code_block:
            out.append(_c("36", line))
            continue

        # Headers
        if line.startswith("### "):
            out.append(_c("1;33", line[4:]))
        elif line.startswith("## "):
            out.append(_c("1;34", line[3:]))
        elif line.startswith("# "):
            out.append(_c("1;36", line[2:]))
        elif line.startswith(("- ", "* ", "+ ")):
            # Bullet
            out.append("  " + _c("33", "•") + " " + _inline_format(line[2:]))
        elif re.match(r"^\d+\. ", line):
            # Numbered list
            out.append("  " + _inline_format(line))
        elif line.startswith("> "):
            out.append(_c("2;35", "  ▏ " + line[2:]))
        else:
            out.append(_inline_format(line))

    return "\n".join(out)


def _inline_format(text: str) -> str:
    if not _IS_TTY:
        return text
    # Inline code
    text = re.sub(r"`([^`]+)`", lambda m: _c("36", m.group(1)), text)
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", lambda m: _c("1", m.group(1)), text)
    # Italic
    text = re.sub(r"\*(.+?)\*", lambda m: _c("3", m.group(1)), text)
    return text


# ──────────────────────────────────────────────────────────────────────────────
# Message types
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Message:
    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    ts: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationConfig:
    max_history_tokens: int = 32000
    max_response_tokens: int = 8192
    temperature: float = 0.7
    stream: bool = True
    render_markdown: bool = True
    show_thinking: bool = False
    system_prompt: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Default system prompt
# ──────────────────────────────────────────────────────────────────────────────

DEVIN_SYSTEM_PROMPT = """You are Devin, an expert autonomous AI assistant and computer operator.

You are helpful, direct, and capable. You:
- Answer questions clearly and accurately
- Complete tasks by actually doing them, not just describing how
- Control the computer directly using tools when needed
- Think step-by-step through complex problems
- Never give up without trying multiple approaches
- Are honest about limitations and when something is not possible
- Provide working code, not pseudocode
- Remember context from earlier in the conversation

Personality:
- Direct and efficient — get to the point
- Curious and thorough — understand the full context
- Practical — prefer working solutions over perfect ones
- Honest — say clearly when something failed or is uncertain
- Proactive — anticipate what the user needs next

Capabilities (via tools):
- Screenshot and analyze the screen with AI vision
- Move mouse, click, type like a human operator
- Open applications, navigate windows
- Search the web and read pages
- Run shell commands and execute code
- Read and write files
- Remember facts across sessions
- Monitor system performance
- Perform authorized security assessments

Response format:
- Use Markdown for structure when helpful
- Use code blocks for code
- Be concise but complete
- For multi-step tasks: show progress
- For errors: explain what happened and what you tried"""


# ──────────────────────────────────────────────────────────────────────────────
# ConversationEngine
# ──────────────────────────────────────────────────────────────────────────────

class ConversationEngine:
    """Full conversation engine with memory, tool integration, and streaming."""

    def __init__(
        self,
        config: Optional[ConversationConfig] = None,
        tools: Optional[Dict[str, Any]] = None,
        memory=None,
    ):
        self.config = config or ConversationConfig()
        self._tools = tools or {}
        self._memory = memory
        self._history: List[Message] = []
        self._slash_handlers: Dict[str, Callable] = {}
        self._provider_name = "auto"
        self._setup_default_slash_commands()

    # ── Tool registration ──────────────────────────────────────────────────────

    def register_tool(self, name: str, fn: Callable, description: str, params: Optional[Dict] = None):
        self._tools[name] = {"fn": fn, "description": description, "params": params or {}}

    def register_slash(self, command: str, handler: Callable, help_text: str = ""):
        self._slash_handlers[command] = {"fn": handler, "help": help_text}

    # ── Default slash commands ──────────────────────────────────────────────────

    def _setup_default_slash_commands(self):
        self._slash_handlers = {
            "help": {"fn": self._cmd_help, "help": "Show this help"},
            "clear": {"fn": self._cmd_clear, "help": "Clear conversation history"},
            "status": {"fn": self._cmd_status, "help": "Show system status"},
            "tools": {"fn": self._cmd_tools, "help": "List available tools"},
            "history": {"fn": self._cmd_history, "help": "Show conversation history"},
            "model": {"fn": self._cmd_model, "help": "Show/set current model"},
            "screenshot": {"fn": self._cmd_screenshot, "help": "Take a screenshot"},
            "shell": {"fn": self._cmd_shell, "help": "Run a shell command: /shell <cmd>"},
            "memory": {"fn": self._cmd_memory, "help": "Show memory contents"},
            "remember": {"fn": self._cmd_remember, "help": "Remember a fact: /remember <fact>"},
            "voice": {"fn": self._cmd_voice, "help": "Toggle voice mode"},
            "repos": {"fn": self._cmd_repos, "help": "List integrated repositories"},
            "exit": {"fn": self._cmd_exit, "help": "Exit Devin"},
            "quit": {"fn": self._cmd_exit, "help": "Exit Devin"},
        }

    def _cmd_help(self, args: str) -> str:
        lines = ["\n" + _c("1;36", "Devin AGI 4.0 — Available Commands") + "\n"]
        lines.append(_c("2", "Slash commands:"))
        for cmd, info in sorted(self._slash_handlers.items()):
            if isinstance(info, dict):
                lines.append(f"  {_c('1', '/' + cmd):<20} {info.get('help', '')}")  
        lines.append("")
        lines.append(_c("2", "Or just type a task or question in natural language."))
        lines.append(_c("2", "Examples:"))
        lines.append("  Open Firefox and go to github.com")
        lines.append("  Find all Python files in ~/projects and count lines of code")
        lines.append("  Take a screenshot and describe what you see")
        lines.append("  Run a scan on localhost:8080 (authorized targets only)")
        return "\n".join(lines)

    def _cmd_clear(self, args: str) -> str:
        self._history.clear()
        return _c("2", "✓ Conversation history cleared")

    def _cmd_status(self, args: str) -> str:
        import platform
        lines = [_c("1;36", "\nDevin AGI 4.0 — Status")]
        lines.append(f"  Platform:  {platform.system()} {platform.release()}")
        lines.append(f"  Provider:  {self._provider_name}")
        lines.append(f"  History:   {len(self._history)} messages")
        lines.append(f"  Tools:     {len(self._tools)} registered")
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            lines.append(f"  CPU:       {cpu:.1f}%")
            lines.append(f"  Memory:    {mem.percent:.1f}% ({mem.used // 1024**3}GB / {mem.total // 1024**3}GB)")
        except Exception:
            pass
        return "\n".join(lines)

    def _cmd_tools(self, args: str) -> str:
        if not self._tools:
            return "No tools registered"
        lines = [_c("1;36", f"\n{len(self._tools)} tools available:")]
        for name, info in sorted(self._tools.items()):
            if isinstance(info, dict):
                desc = info.get("description", "")[:80]
            else:
                desc = str(type(info).__name__)
            lines.append(f"  {_c('1', name):<30} {desc}")
        return "\n".join(lines)

    def _cmd_history(self, args: str) -> str:
        if not self._history:
            return "No conversation history"
        lines = [_c("1", "\nConversation history:")]
        for msg in self._history[-20:]:
            role_color = "1;32" if msg.role == "assistant" else "1;33"
            prefix = _c(role_color, f"[{msg.role}]")
            snippet = msg.content[:120].replace("\n", " ")
            lines.append(f"  {prefix} {snippet}...")
        return "\n".join(lines)

    def _cmd_model(self, args: str) -> str:
        if args.strip():
            os.environ["DEVIN_PROVIDER"] = args.strip()
            return f"Provider set to: {args.strip()}"
        return f"Current provider: {self._provider_name} (set DEVIN_PROVIDER to change)"

    def _cmd_screenshot(self, args: str) -> str:
        try:
            from modules.os_agent import take_screenshot  # type: ignore
            result = take_screenshot(args or "Describe what is visible on the screen")
            if result.success:
                return f"Screenshot: {result.screenshot_before}\n{result.vision_result or ''}"
            return f"Screenshot failed: {result.message}"
        except Exception as e:
            return f"Screenshot error: {e}"

    def _cmd_shell(self, args: str) -> str:
        if not args.strip():
            return "Usage: /shell <command>"
        import subprocess
        try:
            result = subprocess.run(
                args, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout or result.stderr or "(no output)"
            return f"$ {args}\n{output[:2000]}"
        except Exception as e:
            return f"Shell error: {e}"

    def _cmd_memory(self, args: str) -> str:
        if self._memory is None:
            return "Memory module not connected"
        try:
            facts = self._memory.get_all() if hasattr(self._memory, "get_all") else str(self._memory)
            return f"Memory contents:\n{facts}"
        except Exception as e:
            return f"Memory error: {e}"

    def _cmd_remember(self, args: str) -> str:
        if not args.strip():
            return "Usage: /remember <fact>"
        if self._memory is None:
            return "Memory module not connected"
        try:
            self._memory.store(args.strip())
            return f"✓ Remembered: {args.strip()}"
        except Exception as e:
            return f"Memory error: {e}"

    def _cmd_voice(self, args: str) -> str:
        return "Voice mode: set DEVIN_VOICE=1 in .env to enable"

    def _cmd_repos(self, args: str) -> str:
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        repos_dir = root / "repos"
        if not repos_dir.exists():
            return "No repos/ directory found"
        entries = [d.name for d in repos_dir.iterdir() if d.is_dir()]
        if not entries:
            return "No repositories integrated"
        return "Integrated repositories:\n" + "\n".join(f"  - {e}" for e in sorted(entries))

    def _cmd_exit(self, args: str) -> str:
        raise SystemExit(0)

    # ── Core chat ──────────────────────────────────────────────────────────────────

    def _handle_slash(self, text: str) -> Optional[str]:
        """Handle /command input. Returns response or None if not a slash command."""
        if not text.startswith("/"):
            return None
        parts = text[1:].split(None, 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        handler = self._slash_handlers.get(cmd)
        if handler:
            fn = handler["fn"] if isinstance(handler, dict) else handler
            try:
                return fn(args)
            except SystemExit:
                raise
            except Exception as e:
                return f"Command error: {e}"
        return f"Unknown command: /{cmd}. Type /help for available commands."

    def _build_messages(self) -> List[Dict[str, str]]:
        """Build the messages list for the API, with context compaction."""
        messages = []
        total_chars = 0
        # Take most recent messages, respecting token budget
        for msg in reversed(self._history):
            chunk = len(msg.content)
            if total_chars + chunk > self.config.max_history_tokens * 4:  # ~4 chars/token
                break
            messages.insert(0, {"role": msg.role, "content": msg.content})
            total_chars += chunk
        return messages

    def _call_provider(self, messages: List[Dict], system: str) -> str:
        """Call the best available provider and return response text."""
        try:
            from modules.reasoning_engine import _call_best_available  # type: ignore
            text, _, model = _call_best_available(messages, system)
            self._provider_name = model
            return text
        except Exception as e:
            # Last resort: try HuggingFace directly
            try:
                from modules.hf_enhanced_provider import chat as hf_chat  # type: ignore
                result = hf_chat(messages, system_prompt=system)
                self._provider_name = result.get("model", "huggingface")
                return result.get("text", "")
            except Exception as e2:
                return f"[Error: {e} / {e2}]"

    def send(self, user_input: str) -> str:
        """Process one user turn and return the assistant response."""
        user_input = user_input.strip()
        if not user_input:
            return ""

        # Check for slash commands
        slash_result = self._handle_slash(user_input)
        if slash_result is not None:
            return slash_result

        # Add to history
        self._history.append(Message(role="user", content=user_input))

        # Retrieve relevant memories
        memory_context = ""
        if self._memory:
            try:
                relevant = self._memory.search(user_input, limit=3) if hasattr(self._memory, "search") else ""
                if relevant:
                    memory_context = f"\n\nRelevant memories:\n{relevant}"
            except Exception:
                pass

        system = (self.config.system_prompt or DEVIN_SYSTEM_PROMPT) + memory_context
        messages = self._build_messages()

        response = self._call_provider(messages, system)

        # Add to history
        self._history.append(Message(role="assistant", content=response))

        # Render
        if self.config.render_markdown:
            return _render_markdown(response)
        return response

    def stream_send(self, user_input: str) -> Generator[str, None, None]:
        """Stream response tokens (falls back to full response if streaming unsupported)."""
        # Check slash
        slash_result = self._handle_slash(user_input.strip())
        if slash_result is not None:
            yield slash_result
            return

        # For now, get full response and yield it
        # True streaming would require provider-specific SSE handling
        response = self.send(user_input)
        yield response

    def print_response(self, response: str):
        """Print a response with the Devin prefix formatting."""
        if _IS_TTY:
            prefix = _c("1;32", "Devin")
            print(f"\n{prefix}")
        rendered = _render_markdown(response) if self.config.render_markdown else response
        print(rendered)

    def interactive_loop(self, prompt_str: str = "❯ "):
        """Run an interactive REPL loop."""
        try:
            import readline  # type: ignore
        except ImportError:
            pass

        while True:
            try:
                if _IS_TTY:
                    user_input = input(_c("1;33", f"\n{prompt_str}"))
                else:
                    user_input = input()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

            if not user_input.strip():
                continue

            try:
                response = self.send(user_input)
                self.print_response(response)
            except SystemExit:
                break
            except Exception as e:
                print(_c("31", f"Error: {e}"))


# ── Module-level singleton ────────────────────────────────────────────────────
_engine: Optional[ConversationEngine] = None

def get_conversation_engine(
    config: Optional[ConversationConfig] = None,
    tools: Optional[Dict] = None,
    memory=None,
) -> ConversationEngine:
    global _engine
    if _engine is None:
        _engine = ConversationEngine(config=config, tools=tools, memory=memory)
    return _engine


def chat(message: str) -> str:
    """Top-level convenience: send a message and return the response."""
    return get_conversation_engine().send(message)
