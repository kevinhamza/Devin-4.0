"""modules/reasoning_engine.py — LLM-Powered Reasoning Engine

Provides Claude-like chain-of-thought reasoning, task decomposition,
tool selection, and iterative execution for the Devin OS agent.

The engine:
  1. Accepts a task/question in natural language
  2. Thinks through it step-by-step (chain-of-thought)
  3. Selects appropriate tools from the registry
  4. Executes tools and observes results
  5. Continues reasoning until the task is complete or stuck
  6. Returns a structured response with reasoning trace

Provider priority: Claude > Gemini > OpenAI > HuggingFace
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger("ReasoningEngine")
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.INFO)
log.propagate = False


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ThoughtStep:
    """One step in the reasoning trace."""
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    is_final: bool = False


@dataclass
class ReasoningResult:
    """Full result from one reasoning cycle."""
    answer: str
    steps: List[ThoughtStep] = field(default_factory=list)
    tool_calls: int = 0
    model_used: str = ""
    success: bool = True
    error: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Provider wrappers
# ──────────────────────────────────────────────────────────────────────────────

def _call_claude(messages: List[Dict], system: str, tools: Optional[List] = None) -> Tuple[str, List]:
    """Call Claude API. Returns (text, tool_calls)."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    try:
        import anthropic  # type: ignore
        client = anthropic.Anthropic(api_key=key)
        kwargs: Dict[str, Any] = {
            "model": os.environ.get("CLAUDE_MODEL", "claude-opus-4-5"),
            "max_tokens": 8192,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        response = client.messages.create(**kwargs)
        text = ""
        calls = []
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text
            elif hasattr(block, "type") and block.type == "tool_use":
                calls.append({"name": block.name, "input": block.input, "id": block.id})
        return text, calls
    except Exception as e:
        raise RuntimeError(f"Claude call failed: {e}") from e


def _call_gemini(messages: List[Dict], system: str) -> Tuple[str, List]:
    """Call Gemini API. Returns (text, tool_calls)."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        model = genai.GenerativeModel(model_name, system_instruction=system)
        history = []
        for m in messages[:-1]:
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [m["content"]]})
        last = messages[-1]
        chat = model.start_chat(history=history)
        response = chat.send_message(last["content"])
        return response.text, []
    except Exception as e:
        raise RuntimeError(f"Gemini call failed: {e}") from e


def _call_openai(messages: List[Dict], system: str, tools: Optional[List] = None) -> Tuple[str, List]:
    """Call OpenAI API. Returns (text, tool_calls)."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    try:
        import openai  # type: ignore
        client = openai.OpenAI(api_key=key)
        all_messages = [{"role": "system", "content": system}] + messages
        kwargs: Dict[str, Any] = {
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o"),
            "messages": all_messages,
            "max_tokens": 4096,
        }
        if tools:
            kwargs["tools"] = [{"type": "function", "function": t} for t in tools]
            kwargs["tool_choice"] = "auto"
        response = client.chat.completions.create(**kwargs)
        msg = response.choices[0].message
        text = msg.content or ""
        calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                calls.append({"name": tc.function.name, "input": args, "id": tc.id})
        return text, calls
    except Exception as e:
        raise RuntimeError(f"OpenAI call failed: {e}") from e


def _call_huggingface(messages: List[Dict], system: str, tools: Optional[List] = None) -> Tuple[str, List]:
    """Call HuggingFace Inference API. Returns (text, tool_calls)."""
    try:
        from modules.hf_enhanced_provider import chat as hf_chat  # type: ignore
        result = hf_chat(messages, tool_schemas=tools, system_prompt=system)
        return result["text"], result.get("tool_calls", [])
    except ImportError:
        pass
    # Direct fallback
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
    if not token:
        raise RuntimeError("HF_TOKEN not set")
    try:
        import requests  # type: ignore
        all_messages = [{"role": "system", "content": system}] + messages
        models = [
            "Qwen/Qwen2.5-72B-Instruct",
            "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.3",
        ]
        for model_id in models:
            try:
                resp = requests.post(
                    "https://router.huggingface.co/v1/chat/completions",
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"model": model_id, "messages": all_messages, "max_tokens": 4096},
                    timeout=60,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["choices"][0]["message"]["content"] or ""
                    return text, []
            except Exception:
                continue
        raise RuntimeError("All HF models failed")
    except Exception as e:
        raise RuntimeError(f"HuggingFace call failed: {e}") from e


def _call_best_available(messages: List[Dict], system: str, tools: Optional[List] = None) -> Tuple[str, List, str]:
    """Try providers in priority order. Returns (text, tool_calls, model_name)."""
    preferred = os.environ.get("DEVIN_PROVIDER", "").lower()

    order = []
    if preferred == "claude":
        order = ["claude", "gemini", "openai", "huggingface"]
    elif preferred == "gemini":
        order = ["gemini", "claude", "openai", "huggingface"]
    elif preferred == "openai":
        order = ["openai", "claude", "gemini", "huggingface"]
    elif preferred in ("huggingface", "hf"):
        order = ["huggingface", "gemini", "claude", "openai"]
    else:
        order = []
        if os.environ.get("ANTHROPIC_API_KEY"):
            order.append("claude")
        if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
            order.append("gemini")
        if os.environ.get("OPENAI_API_KEY"):
            order.append("openai")
        if os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY"):
            order.append("huggingface")
        if not order:
            order = ["gemini", "claude", "openai", "huggingface"]

    last_error = "No provider available"
    for provider in order:
        try:
            if provider == "claude":
                text, calls = _call_claude(messages, system, tools)
                return text, calls, f"claude/{os.environ.get('CLAUDE_MODEL','claude-opus-4-5')}"
            elif provider == "gemini":
                text, calls = _call_gemini(messages, system)
                return text, calls, f"gemini/{os.environ.get('GEMINI_MODEL','gemini-2.0-flash')}"
            elif provider == "openai":
                text, calls = _call_openai(messages, system, tools)
                return text, calls, f"openai/{os.environ.get('OPENAI_MODEL','gpt-4o')}"
            elif provider == "huggingface":
                text, calls = _call_huggingface(messages, system, tools)
                return text, calls, "huggingface/qwen-72b"
        except Exception as e:
            last_error = f"{provider}: {e}"
            log.debug("Provider %s failed: %s", provider, e)
            continue

    raise RuntimeError(f"All providers failed. Last: {last_error}")


# ──────────────────────────────────────────────────────────────────────────────
# ReasoningEngine
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are Devin, an expert autonomous AI agent that operates an entire computer.
You think carefully, reason step-by-step, and take actions to complete tasks.

Your capabilities:
- Full OS control: mouse, keyboard, screenshots, window management
- Browser automation: navigate, search, fill forms, extract data
- File system: read, write, create, organize files
- Shell commands: run any terminal command
- Code execution: write and run Python/JavaScript/shell code
- Web search and research
- Memory: remember and recall important information
- System monitoring: CPU, memory, processes, network
- Security tools: authorized vulnerability assessment
- AI reasoning: think through complex problems

Thinking approach:
- THINK before acting: analyze what needs to be done
- OBSERVE the current state: take screenshots, read files, check status
- PLAN: break the task into concrete steps
- ACT: execute one step at a time
- VERIFY: confirm each step succeeded before moving on
- RECOVER: if something fails, diagnose and try an alternative approach
- COMPLETE: report exactly what was accomplished and what remains

Critical rules:
- Never give up on a task without trying multiple approaches
- Always verify your actions worked — don't assume success
- For GUI tasks: screenshot → identify element → click/type → screenshot → verify
- For shell tasks: run command → read output → verify result
- Report exactly what happened, not what should have happened
- You are operating as a real user — be systematic, not superficial

Available tools:
{tool_descriptions}"""


class ReasoningEngine:
    """LLM-powered reasoning and execution engine."""

    def __init__(self, tools: Optional[Dict[str, Callable]] = None, max_iterations: int = 20):
        self._tools = tools or {}
        self._max_iterations = max_iterations
        self._conversation_history: List[Dict[str, Any]] = []
        self._session_context: Dict[str, Any] = {}

    def register_tool(self, name: str, fn: Callable, description: str, params: Optional[Dict] = None):
        """Register a tool the engine can call."""
        self._tools[name] = {
            "fn": fn,
            "description": description,
            "params": params or {},
        }

    def _build_tool_descriptions(self) -> str:
        if not self._tools:
            return "No tools registered."
        lines = []
        for name, info in self._tools.items():
            if isinstance(info, dict):
                desc = info.get("description", "")
                params = info.get("params", {})
                lines.append(f"- {name}: {desc}")
                if params:
                    for p, spec in params.items():
                        lines.append(f"    {p}: {spec}")
            else:
                lines.append(f"- {name}: callable")
        return "\n".join(lines)

    def _build_tool_schemas(self) -> List[Dict]:
        schemas = []
        for name, info in self._tools.items():
            if isinstance(info, dict):
                props = {}
                required = []
                for p, spec in info.get("params", {}).items():
                    if isinstance(spec, dict):
                        props[p] = spec
                    else:
                        props[p] = {"type": "string", "description": str(spec)}
                    required.append(p)
                schemas.append({
                    "name": name,
                    "description": info.get("description", ""),
                    "parameters": {"type": "object", "properties": props, "required": required},
                })
        return schemas

    def _execute_tool(self, name: str, input_data: Dict[str, Any]) -> str:
        """Execute a registered tool and return the result as a string."""
        if name not in self._tools:
            return f"Error: Tool '{name}' not found"
        tool = self._tools[name]
        fn = tool["fn"] if isinstance(tool, dict) else tool
        try:
            result = fn(**input_data)
            if isinstance(result, str):
                return result
            return json.dumps(result, default=str)
        except Exception as e:
            return f"Tool error: {e}"

    def _parse_react_response(self, text: str) -> Tuple[str, Optional[str], Optional[Dict]]:
        """Parse ReAct-style response: Thought/Action/Action Input."""
        thought = ""
        action = None
        action_input = None

        import re
        t_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)", text, re.DOTALL)
        if t_match:
            thought = t_match.group(1).strip()

        a_match = re.search(r"Action:\s*(\w+)", text)
        if a_match:
            action = a_match.group(1).strip()

        ai_match = re.search(r"Action Input:\s*(\{.*?\}|.*?)(?=\nObservation:|\nThought:|$)", text, re.DOTALL)
        if ai_match:
            raw = ai_match.group(1).strip()
            try:
                action_input = json.loads(raw)
            except Exception:
                action_input = {"input": raw}

        fa_match = re.search(r"Final Answer:\s*(.*?)$", text, re.DOTALL)
        if fa_match:
            return fa_match.group(1).strip(), "__final__", {}

        return thought, action, action_input

    def think(self, task: str, context: str = "") -> ReasoningResult:
        """Run the full reasoning loop for a task.

        Uses the best available AI provider with chain-of-thought reasoning
        and tool calling until the task is complete.
        """
        system = SYSTEM_PROMPT_TEMPLATE.format(
            tool_descriptions=self._build_tool_descriptions()
        )
        if context:
            system += f"\n\nAdditional context:\n{context}"

        messages = list(self._conversation_history)
        messages.append({"role": "user", "content": task})

        steps: List[ThoughtStep] = []
        tool_call_count = 0
        model_used = ""
        final_answer = ""

        tools_schema = self._build_tool_schemas()

        for iteration in range(self._max_iterations):
            try:
                text, tool_calls, model_used = _call_best_available(
                    messages, system, tools_schema if tools_schema else None
                )
            except Exception as e:
                return ReasoningResult(
                    answer=f"Provider error: {e}",
                    steps=steps, model_used=model_used,
                    success=False, error=str(e)
                )

            if tool_calls:
                messages.append({"role": "assistant", "content": text or "Processing..."})
                all_tool_results = []
                for tc in tool_calls:
                    tool_name = tc.get("name", "")
                    tool_input = tc.get("input", {})
                    observation = self._execute_tool(tool_name, tool_input)
                    tool_call_count += 1
                    step = ThoughtStep(
                        thought=text or "",
                        action=tool_name,
                        action_input=tool_input,
                        observation=observation,
                    )
                    steps.append(step)
                    all_tool_results.append(f"[{tool_name}] → {observation}")
                    log.info("Tool: %s(%s) → %s", tool_name, tool_input, observation[:200])

                tool_result_text = "\n".join(all_tool_results)
                messages.append({"role": "user", "content": f"Tool results:\n{tool_result_text}\n\nContinue with the task."})

            elif text:
                step = ThoughtStep(thought=text, is_final=True)
                steps.append(step)
                final_answer = text

                done_signals = ["task complete", "task is complete", "i have completed", "done.", "finished."]
                if any(s in text.lower() for s in done_signals) or iteration >= self._max_iterations - 1:
                    break

                messages.append({"role": "assistant", "content": text})
                messages.append({"role": "user", "content": "Continue. If the task is fully complete, say 'Task complete: <summary>'. Otherwise continue with the next step."})
            else:
                break

        if final_answer:
            self._conversation_history.append({"role": "user", "content": task})
            self._conversation_history.append({"role": "assistant", "content": final_answer})

        return ReasoningResult(
            answer=final_answer or (steps[-1].thought if steps else "No response generated"),
            steps=steps,
            tool_calls=tool_call_count,
            model_used=model_used,
            success=True,
        )

    def chat(self, message: str) -> str:
        """Simple conversation turn — returns a response string."""
        result = self.think(message)
        return result.answer

    def clear_history(self):
        """Clear conversation history."""
        self._conversation_history.clear()
        self._session_context.clear()

    def get_history_summary(self) -> str:
        """Return a brief summary of the conversation history."""
        if not self._conversation_history:
            return "No conversation history"
        turns = len([m for m in self._conversation_history if m["role"] == "user"])
        return f"{turns} conversation turns"


# ── Module-level singleton ────────────────────────────────────────────────────
_engine: Optional[ReasoningEngine] = None

def get_engine(tools: Optional[Dict] = None) -> ReasoningEngine:
    global _engine
    if _engine is None:
        _engine = ReasoningEngine(tools=tools)
    return _engine


# Alias — external code (main.py, bootstrap.py) imports this name
get_reasoning_engine = get_engine


def think(task: str, context: str = "") -> str:
    """Top-level convenience function: reason about a task and return the answer."""
    return get_engine().think(task, context).answer


def chat(message: str) -> str:
    """Top-level convenience function: conversational response."""
    return get_engine().chat(message)
