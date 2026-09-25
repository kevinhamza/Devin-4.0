#!/usr/bin/env python3
"""
Devin AGI 4.0 — Enhanced Gemini Streaming Provider

Streaming text generation via Google Gemini API.
GEMINI_API_KEY must be set via .env — never hardcoded.
"""
from __future__ import annotations
import os
from typing import Generator, List, Dict, Optional
from pathlib import Path

# Load .env
try:
    _env = Path(__file__).resolve().parent.parent / '.env'
    if _env.exists():
        for _l in _env.read_text().splitlines():
            _l = _l.strip()
            if _l and not _l.startswith('#') and '=' in _l:
                _k, _, _v = _l.partition('=')
                os.environ.setdefault(_k.strip(), _v.strip().strip('"\'' ))
except Exception:
    pass

_API_KEY = os.environ.get('GEMINI_API_KEY', '')
_DEFAULT_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash-exp')


def _detect_sdk() -> Optional[str]:
    try:
        import google.genai  # noqa
        return 'new'
    except ImportError:
        pass
    try:
        import google.generativeai  # noqa
        return 'old'
    except ImportError:
        pass
    return None


def chat(
    prompt: str,
    history: Optional[List[Dict[str, str]]] = None,
    model: Optional[str] = None,
    system: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """
    Send a message to Gemini and return the full response text.

    Reads GEMINI_API_KEY from environment — never pass keys in source code.
    Returns error string starting with 'ERROR:' on failure.
    """
    key = api_key or _API_KEY
    if not key:
        return 'ERROR: GEMINI_API_KEY not set. Add it to .env: GEMINI_API_KEY=<your-key>'

    sdk = _detect_sdk()
    if sdk is None:
        return 'ERROR: No Google GenAI SDK. Run: pip install google-genai'

    m = model or _DEFAULT_MODEL
    h = history or []
    try:
        if sdk == 'new':
            return _chat_new(prompt, h, m, system, key)
        return _chat_old(prompt, h, m, system, key)
    except Exception as e:
        return f'ERROR: Gemini failed: {e}'


def stream_chat(
    prompt: str,
    history: Optional[List[Dict[str, str]]] = None,
    model: Optional[str] = None,
    system: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Generator[str, None, None]:
    """Stream a Gemini response chunk-by-chunk. Yields text strings."""
    key = api_key or _API_KEY
    if not key:
        yield 'ERROR: GEMINI_API_KEY not set.'
        return

    sdk = _detect_sdk()
    if sdk is None:
        yield 'ERROR: No Google GenAI SDK. Run: pip install google-genai'
        return

    m = model or _DEFAULT_MODEL
    h = history or []
    try:
        if sdk == 'new':
            yield from _stream_new(prompt, h, m, system, key)
        else:
            yield from _stream_old(prompt, h, m, system, key)
    except Exception as e:
        yield f'ERROR: {e}'


# ── New SDK (google.genai) ──────────────────────────────────────────────────────

def _chat_new(prompt, history, model_name, system, key) -> str:
    import google.genai as genai
    from google.genai import types as gt
    client = genai.Client(api_key=key)
    cfg = gt.GenerateContentConfig(
        system_instruction=system or None, temperature=0.7
    )
    r = client.models.generate_content(model=model_name, contents=prompt, config=cfg)
    return r.text or ''


def _stream_new(prompt, history, model_name, system, key) -> Generator[str, None, None]:
    import google.genai as genai
    from google.genai import types as gt
    client = genai.Client(api_key=key)
    cfg = gt.GenerateContentConfig(
        system_instruction=system or None, temperature=0.7
    )
    for chunk in client.models.generate_content_stream(
        model=model_name, contents=prompt, config=cfg
    ):
        if chunk.text:
            yield chunk.text


# ── Old SDK (google.generativeai) ──────────────────────────────────────────────

def _gemini_history(history):
    return [
        {'role': 'model' if m.get('role') == 'assistant' else 'user',
         'parts': [m.get('content', '')]}
        for m in history
    ]


def _chat_old(prompt, history, model_name, system, key) -> str:
    import google.generativeai as genai
    genai.configure(api_key=key)
    model = genai.GenerativeModel(model_name, system_instruction=system or None)
    chat_obj = model.start_chat(history=_gemini_history(history))
    return chat_obj.send_message(prompt).text or ''


def _stream_old(prompt, history, model_name, system, key) -> Generator[str, None, None]:
    import google.generativeai as genai
    genai.configure(api_key=key)
    model = genai.GenerativeModel(model_name, system_instruction=system or None)
    chat_obj = model.start_chat(history=_gemini_history(history))
    for chunk in chat_obj.send_message(prompt, stream=True):
        if chunk.text:
            yield chunk.text


def is_available() -> bool:
    return bool(_API_KEY) and _detect_sdk() is not None


if __name__ == '__main__':
    if is_available():
        print(chat('Say hello in one sentence.'))
    else:
        print('Not available. Set GEMINI_API_KEY in .env')
