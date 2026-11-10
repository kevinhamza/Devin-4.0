"""modules/ollama_provider.py — Ollama local LLM provider

Streams responses from a locally-running Ollama instance.
No API key required — fully offline.

Setup:
  curl -fsSL https://ollama.com/install.sh | sh
  ollama pull qwen2.5:0.5b   # fast, free, capable
  ollama pull llama3.2:3b    # better quality
  ollama serve                # already running as a service on most installs
"""
from __future__ import annotations

import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any, Dict, Generator, List, Optional

log = logging.getLogger("OllamaProvider")
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(levelname)s OllamaProvider: %(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.WARNING)
log.propagate = False


def _base() -> str:
    return (os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")


def _model() -> str:
    return os.environ.get("OLLAMA_MODEL") or "qwen2.5:0.5b"


def is_available() -> bool:
    """Return True if Ollama is running and has at least one model."""
    try:
        with urllib.request.urlopen(f"{_base()}/api/tags", timeout=3) as r:
            data = json.loads(r.read())
            return bool(data.get("models"))
    except Exception:
        return False


def list_models() -> List[str]:
    """Return list of available model names."""
    try:
        with urllib.request.urlopen(f"{_base()}/api/tags", timeout=5) as r:
            data = json.loads(r.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def _best_model() -> str:
    """Pick the best available model."""
    available = list_models()
    if not available:
        return _model()
    # Prefer larger/smarter models
    preferred = [
        "llama3.3", "llama3.2", "qwen2.5:7b", "qwen2.5:3b", "llama3.1",
        "mistral", "phi4", "phi3", "gemma2", "qwen2.5",
    ]
    env_model = _model()
    if any(env_model == m or env_model in m for m in available):
        return env_model
    for pref in preferred:
        for avail in available:
            if pref in avail.lower():
                return avail
    return available[0]


def stream_chat(
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> Generator[str, None, None]:
    """Stream a chat response from Ollama. Yields text chunks."""
    model_id = model or _best_model()

    # Build Ollama message list
    ollama_messages: List[Dict[str, str]] = []
    if system_prompt:
        ollama_messages.append({"role": "system", "content": system_prompt})
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "system":
            if not system_prompt:  # don't double-add system
                ollama_messages.append({"role": "system", "content": content})
        else:
            ollama_messages.append({"role": role, "content": content})

    body = {
        "model": model_id,
        "messages": ollama_messages,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    payload = json.dumps(body).encode()
    try:
        req = urllib.request.Request(
            f"{_base()}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    text = chunk.get("message", {}).get("content", "")
                    if text:
                        yield text
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
    except urllib.error.URLError as e:
        yield f"[Ollama connection error: {e} — is Ollama running? Run: ollama serve]"
    except Exception as e:
        yield f"[Ollama error: {e}]"


def complete(
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 4096,
) -> str:
    """Non-streaming chat completion."""
    return "".join(stream_chat(messages, system_prompt=system_prompt, model=model, max_tokens=max_tokens))


def _tools_to_ollama(tools: Dict[str, Any]) -> list:
    """Convert devin tool registry to Ollama tool format."""
    result = []
    for name, info in tools.items():
        props = {}
        required = []
        for param_name, param_desc in info.get('params', {}).items():
            props[param_name] = {'type': 'string', 'description': str(param_desc)}
        result.append({
            'type': 'function',
            'function': {
                'name': name,
                'description': info.get('desc', ''),
                'parameters': {
                    'type': 'object',
                    'properties': props,
                    'required': list(props.keys()),
                }
            }
        })
    return result


def chat_with_tools(
    messages: List[Dict[str, str]],
    tools: Dict[str, Any],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """
    Single-shot chat with native tool calling support.
    Returns: {"content": str, "tool_calls": [{"name": str, "arguments": dict}], "done": bool}
    """
    model_id = model or _best_model()

    ollama_messages: List[Dict] = []
    if system_prompt:
        ollama_messages.append({"role": "system", "content": system_prompt})
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "system" and system_prompt:
            continue  # don't double-add system
        ollama_messages.append({"role": role, "content": content})

    ollama_tools = _tools_to_ollama(tools) if tools else []

    body = {
        "model": model_id,
        "messages": ollama_messages,
        "tools": ollama_tools,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": max_tokens},
    }

    payload = json.dumps(body).encode()
    try:
        req = urllib.request.Request(
            f"{_base()}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            msg = data.get("message", {})
            content = msg.get("content") or ""
            tool_calls_raw = msg.get("tool_calls") or []
            tool_calls = []
            for tc in tool_calls_raw:
                fn = tc.get("function", {})
                tool_calls.append({
                    "name": fn.get("name", ""),
                    "arguments": fn.get("arguments") or {},
                })
            return {
                "content": content,
                "tool_calls": tool_calls,
                "done": data.get("done", True),
            }
    except Exception as e:
        return {"content": f"[Ollama tool call error: {e}]", "tool_calls": [], "done": True}


def pull_model(model_name: str) -> bool:
    """Pull (download) a model. Returns True on success."""
    try:
        payload = json.dumps({"name": model_name}).encode()
        req = urllib.request.Request(
            f"{_base()}/api/pull",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            for raw in resp:
                line = raw.decode("utf-8", errors="replace").strip()
                if line:
                    try:
                        data = json.loads(line)
                        status = data.get("status", "")
                        if status:
                            log.info("Pull %s: %s", model_name, status)
                    except Exception:
                        pass
        return True
    except Exception as e:
        log.error("Pull failed: %s", e)
        return False
