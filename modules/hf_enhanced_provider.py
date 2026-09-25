"""modules/hf_enhanced_provider.py — Enhanced HuggingFace Free-Tier Provider

Full-featured HuggingFace Inference API integration using the official
HuggingFace Router (OpenAI-compatible endpoint).

Credentials:
  HF_TOKEN or HUGGINGFACE_API_KEY environment variable.
  Never hard-coded. Set in .env file.

Free-tier model chain (tried in order, falls back on 429/404):
  1. Qwen/Qwen2.5-72B-Instruct    (best reasoning)
  2. meta-llama/Meta-Llama-3.1-70B-Instruct
  3. mistralai/Mixtral-8x7B-Instruct-v0.1
  4. mistralai/Mistral-7B-Instruct-v0.3
  5. HuggingFaceH4/zephyr-7b-beta  (most available)

Features:
- OpenAI-compatible chat completions
- Native tool calling (function_call channel)
- Fallback text-mode tool parsing (<tool_use> blocks)
- Automatic model fallback on rate limit / not found
- Configurable max_tokens, temperature
- Streaming support (yields partial text chunks)
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, Generator, List, Optional, Tuple

log = logging.getLogger("HFEnhancedProvider")
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.WARNING)
log.propagate = False

HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"
HF_DIRECT_URL = "https://api-inference.huggingface.co/models"

FREE_MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",
    "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "HuggingFaceH4/zephyr-7b-beta",
]

CODE_MODELS = [
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    "bigcode/starcoder2-15b",
]

# Vision models (for screenshot analysis)
VISION_MODELS = [
    "Qwen/Qwen2-VL-7B-Instruct",
    "llava-hf/llava-1.5-7b-hf",
]


def _token() -> str:
    """Get HF token from environment — never from source code."""
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY") or ""


def has_token() -> bool:
    return bool(_token())


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_token()}",
        "Content-Type": "application/json",
        "X-Use-Cache": "false",
    }


# ──────────────────────────────────────────────────────────────────────────────
# Tool schema conversion
# ──────────────────────────────────────────────────────────────────────────────

def _to_openai_tool(schema: Dict[str, Any]) -> Dict[str, Any]:
    params = schema.get("parameters") or {"type": "object", "properties": {}}
    params.setdefault("type", "object")
    params.setdefault("properties", {})
    return {
        "type": "function",
        "function": {
            "name": schema["name"],
            "description": schema.get("description", ""),
            "parameters": params,
        },
    }


def _tool_fallback_instructions(tool_schemas: List[Dict[str, Any]]) -> str:
    """Text instructions for models that don't support native tool calling."""
    if not tool_schemas:
        return ""
    lines = []
    for t in tool_schemas:
        props = (t.get("parameters") or {}).get("properties") or {}
        arg_str = ", ".join(f"{k}: {(v or {}).get('type', 'any')}" for k, v in props.items())
        lines.append(f"- {t['name']}({arg_str}): {t.get('description', '')}")
    tools_text = "\n".join(lines)
    return (
        "\n\nTo use a tool, output EXACTLY this format (nothing else after the block):\n"
        '<tool_use>{"name": "<tool>", "input": {<args>}}</tool_use>\n'
        "When done with ALL steps, say \"Task complete: <summary>\".\n"
        f"Available tools:\n{tools_text}"
    )


_TOOL_RE = re.compile(r"<tool_use>(.*?)</tool_use>", re.DOTALL)


def _parse_fallback_calls(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    calls = []
    clean = text
    for m in _TOOL_RE.finditer(text):
        raw = m.group(1).strip()
        try:
            obj = json.loads(re.sub(r"//[^\n]*", "", raw))
            if "name" in obj:
                calls.append({"name": obj["name"], "input": obj.get("input") or {}})
        except Exception:
            pass
        clean = clean.replace(m.group(0), "").strip()
    return clean, calls


# ──────────────────────────────────────────────────────────────────────────────
# Core API call
# ──────────────────────────────────────────────────────────────────────────────

def _post_completion(
    model: str,
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    timeout: int = 90,
):
    """Single POST to HF router. Returns requests.Response."""
    try:
        import requests  # type: ignore
    except ImportError:
        raise RuntimeError("pip install requests")

    body: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    return requests.post(HF_ROUTER_URL, headers=_headers(), json=body, timeout=timeout)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def chat(
    messages: List[Dict[str, str]],
    tool_schemas: Optional[List[Dict[str, Any]]] = None,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    prefer_code: bool = False,
) -> Dict[str, Any]:
    """Chat completion with automatic model fallback.

    Returns: {"text": str, "tool_calls": list, "model": str}
    """
    if not has_token():
        raise RuntimeError(
            "HF_TOKEN or HUGGINGFACE_API_KEY not set. "
            "Add to .env: HF_TOKEN=your_token_here"
        )

    # Build message list
    payload_messages: List[Dict[str, Any]] = []
    sys_text = system_prompt or ""
    if tool_schemas:
        sys_text += _tool_fallback_instructions(tool_schemas)
    if sys_text:
        payload_messages.append({"role": "system", "content": sys_text})
    for m in messages:
        if m.get("role") != "system":
            payload_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

    openai_tools = [_to_openai_tool(s) for s in (tool_schemas or [])]

    # Model priority
    models_to_try: List[str] = []
    if model:
        models_to_try.append(model)
    if prefer_code:
        models_to_try.extend(CODE_MODELS)
    models_to_try.extend(FREE_MODELS)
    # Deduplicate while preserving order
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

    last_error = "no models tried"
    for m_id in models_to_try:
        try:
            resp = _post_completion(
                m_id, payload_messages,
                tools=openai_tools if openai_tools else None,
                max_tokens=max_tokens, temperature=temperature
            )
        except Exception as e:
            last_error = f"network: {e}"
            continue

        status = resp.status_code
        if status == 429 or status == 503:
            last_error = f"{m_id}: rate limit"
            time.sleep(2.0)
            continue
        if status == 404:
            last_error = f"{m_id}: not found"
            continue
        if status >= 400:
            body_text = resp.text[:300]
            if "model not found" in body_text.lower() or "not_found" in body_text.lower():
                last_error = f"{m_id}: {body_text[:100]}"
                continue
            last_error = f"{m_id}: HTTP {status} {body_text}"
            break

        try:
            data = resp.json()
        except Exception:
            last_error = f"{m_id}: bad JSON"
            continue

        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        raw_text = msg.get("content") or ""
        native_calls = msg.get("tool_calls") or []

        tool_calls: List[Dict[str, Any]] = []
        for tc in native_calls:
            fn = tc.get("function") or {}
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except Exception:
                args = {}
            tool_calls.append({"name": fn.get("name", ""), "input": args})

        if not tool_calls and raw_text:
            raw_text, fallback_calls = _parse_fallback_calls(raw_text)
            tool_calls.extend(fallback_calls)

        return {
            "text": raw_text,
            "tool_calls": tool_calls,
            "model": data.get("model") or m_id,
        }

    raise RuntimeError(f"HuggingFace: all models failed. Last error: {last_error}")


def stream_chat(
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 4096,
) -> Generator[str, None, None]:
    """Streaming chat — yields text chunks as they arrive."""
    if not has_token():
        yield "[Error: HF_TOKEN not set]"
        return

    try:
        import requests  # type: ignore
    except ImportError:
        yield "[Error: requests not installed]"
        return

    payload_messages: List[Dict[str, Any]] = []
    if system_prompt:
        payload_messages.append({"role": "system", "content": system_prompt})
    for m in messages:
        if m.get("role") != "system":
            payload_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

    model_id = model or FREE_MODELS[0]
    body: Dict[str, Any] = {
        "model": model_id,
        "messages": payload_messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": True,
    }

    try:
        resp = requests.post(HF_ROUTER_URL, headers=_headers(), json=body, stream=True, timeout=120)
        if resp.status_code != 200:
            yield f"[Error: HTTP {resp.status_code}]"
            return

        for line in resp.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8") if isinstance(line, bytes) else line
            if line_str.startswith("data: "):
                data_str = line_str[6:].strip()
                if data_str == "[DONE]":
                    return
                try:
                    chunk = json.loads(data_str)
                    delta = (chunk.get("choices") or [{}])[0].get("delta") or {}
                    content = delta.get("content") or ""
                    if content:
                        yield content
                except Exception:
                    continue
    except Exception as e:
        yield f"[Stream error: {e}]"


def list_free_models() -> List[str]:
    """Return the list of free-tier models this provider tries."""
    return list(FREE_MODELS)


def test_connection() -> Dict[str, Any]:
    """Test HF connection and return status."""
    if not has_token():
        return {"ok": False, "error": "HF_TOKEN not set"}
    try:
        result = chat(
            [{"role": "user", "content": "Say 'OK' in one word."}],
            max_tokens=10
        )
        return {"ok": True, "model": result["model"], "response": result["text"][:50]}
    except Exception as e:
        return {"ok": False, "error": str(e)}
