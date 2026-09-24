"""
modules/hf_provider.py — Hugging Face Inference provider for the Python runtime.

Mirrors the TypeScript provider in src/providers/huggingface.ts:
- Auth via HF_TOKEN or HUGGINGFACE_API_KEY env var (never hard-coded).
- Talks to https://router.huggingface.co/v1/chat/completions (OpenAI-compatible).
- Supports a text-only chat call plus prompt-formatted tool-use fallback.
- Registered by main.py as a fallback after Gemini and Anthropic.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:  # pragma: no cover
    _requests = None
    _HAS_REQUESTS = False

HF_ROUTER_BASE = "https://router.huggingface.co/v1"

FALLBACK_MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",
    "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "HuggingFaceH4/zephyr-7b-beta",
]


def has_hf_token() -> bool:
    return bool(_HAS_REQUESTS and (os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")))


def _token() -> str:
    return os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY") or ""


def _tool_instructions(tool_schemas: List[Dict[str, Any]]) -> str:
    if not tool_schemas:
        return ""
    lines = []
    for t in tool_schemas:
        params = t.get("parameters", {}) or {}
        props = params.get("properties", {}) or {}
        arg_lines = ",\n".join(
            f'    "{k}": <{(v or {}).get("type", "string")}>' for k, v in props.items()
        )
        lines.append(
            f"- {t['name']}: {t.get('description', '')}\n  args: {{\n{arg_lines}\n  }}"
        )
    schema = "\n".join(lines)
    return (
        "\n\nYou have these tools. To call a tool, emit exactly one JSON block per turn wrapped "
        "in <tool_use>...</tool_use>, with no other text:\n"
        '<tool_use>{"name":"<tool_name>","input":{...}}</tool_use>\n'
        "When the task is complete, reply with plain text (no <tool_use> block).\n\n"
        f"Tools:\n{schema}"
    )


_TOOL_RE = re.compile(r"<tool_use>([\s\S]*?)</tool_use>")
_JSON_OBJ_RE = re.compile(r"\{[\s\S]*\}")
_LINE_COMMENT_RE = re.compile(r"(?m)//[^\n]*")


def _extract_json_object(blob: str) -> Optional[Dict[str, Any]]:
    """Find the first {...} JSON object inside a possibly-noisy blob and parse it.
    Tolerates trailing `// ...` comments and stray non-JSON text before/after.
    """
    cleaned = _LINE_COMMENT_RE.sub("", blob)
    m = _JSON_OBJ_RE.search(cleaned)
    if not m:
        return None
    candidate = m.group(0)
    try:
        result = json.loads(candidate)
    except Exception:
        # Try trimming trailing garbage after balanced-brace scan.
        depth = 0
        end = -1
        for i, ch in enumerate(candidate):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end <= 0:
            return None
        try:
            result = json.loads(candidate[:end])
        except Exception:
            return None
    return result if isinstance(result, dict) else None


def _parse_tool_calls(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    calls: List[Dict[str, Any]] = []
    residual = text
    for m in _TOOL_RE.finditer(text):
        inner = m.group(1)
        obj = _extract_json_object(inner)
        if obj is None or "name" not in obj:
            # Drop malformed block from residual too so it doesn't get shown to the user.
            residual = residual.replace(m.group(0), "").strip()
            continue
        calls.append({
            "name": obj["name"],
            "input": obj.get("input") or obj.get("arguments") or {},
        })
        residual = residual.replace(m.group(0), "").strip()
    return residual, calls


def _post(model: str, messages: List[Dict[str, str]], max_tokens: int = 4096, timeout: int = 60):
    if not _HAS_REQUESTS:
        raise RuntimeError("requests library not available")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_token()}",
        "X-Use-Cache": "false",
    }
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": False,
    }
    return _requests.post(f"{HF_ROUTER_BASE}/chat/completions", headers=headers, json=body, timeout=timeout)


def chat(
    messages: List[Dict[str, str]],
    tool_schemas: Optional[List[Dict[str, Any]]] = None,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """Chat call with an OpenAI-style messages list.

    Returns a dict shaped like:
        {"text": str, "tool_calls": [{"name": str, "input": dict}, ...], "model": str}
    """
    if not has_hf_token():
        raise RuntimeError("HF_TOKEN or HUGGINGFACE_API_KEY not set")

    payload_messages: List[Dict[str, str]] = []
    system_text = (system_prompt or "") + _tool_instructions(tool_schemas or [])
    if system_text.strip():
        payload_messages.append({"role": "system", "content": system_text})
    for m in messages:
        if m.get("role") == "system":
            continue
        payload_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

    models_to_try = []
    if model:
        models_to_try.append(model)
    for fm in FALLBACK_MODELS:
        if fm not in models_to_try:
            models_to_try.append(fm)

    last_error = ""
    for m_id in models_to_try:
        try:
            resp = _post(m_id, payload_messages, max_tokens=max_tokens)
        except Exception as e:
            last_error = f"post: {e}"
            continue
        if resp.status_code == 429 or resp.status_code == 503:
            last_error = f"{resp.status_code} rate/unavailable"
            time.sleep(2.0)
            continue
        if resp.status_code == 404 or "not_found" in resp.text.lower() or "model not found" in resp.text.lower():
            last_error = f"404 {resp.text[:200]}"
            continue
        if resp.status_code >= 400:
            last_error = f"{resp.status_code} {resp.text[:300]}"
            break
        try:
            data = resp.json()
        except Exception:
            last_error = f"json: {resp.text[:200]}"
            continue

        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        raw_text = msg.get("content") or ""
        native = msg.get("tool_calls") or []

        tool_calls: List[Dict[str, Any]] = []
        for tc in native:
            fn = tc.get("function") or {}
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except Exception:
                args = {}
            tool_calls.append({"name": fn.get("name", ""), "input": args})

        if not tool_calls and raw_text:
            residual, parsed_calls = _parse_tool_calls(raw_text)
            if parsed_calls:
                tool_calls.extend(parsed_calls)
                raw_text = residual

        return {
            "text": raw_text,
            "tool_calls": tool_calls,
            "model": data.get("model") or m_id,
        }

    raise RuntimeError(f"Hugging Face: all models failed. Last: {last_error}")
