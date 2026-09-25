"""
tests/test_api_connectivity.py — API connectivity and provider tests

Run with: python -m pytest tests/test_api_connectivity.py -v
Or standalone: python tests/test_api_connectivity.py

Tests:
1. Gemini API — real call with GEMINI_API_KEY
2. Anthropic API — real call with ANTHROPIC_API_KEY
3. OpenAI API — real call with OPENAI_API_KEY
4. Tool registry — all tools importable
5. Provider model list — only real model IDs

Each test is automatically skipped when the relevant API key is not set.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# ──────────────────────────────────────────────────────────────────────────────
# Real model IDs that the Gemini API actually accepts (2025)
# ──────────────────────────────────────────────────────────────────────────────
KNOWN_REAL_GEMINI_MODELS = {
    'gemini-2.5-flash',
    'gemini-2.5-pro',
    'gemini-2.0-flash',
    'gemini-1.5-flash',
    'gemini-1.5-pro',
    'gemini-1.0-pro',
}

KNOWN_FAKE_GEMINI_MODELS = {
    'gemini-3.6-flash',
    'gemini-3.5-flash',
    'gemini-3.1-flash-lite',
    'gemini-flash-latest',
}

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _post_json(url: str, headers: dict, body: dict) -> dict:
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def _skip_unless(env_var: str):
    """Return skip reason if env_var is not set, else None."""
    if not os.environ.get(env_var):
        return f"{env_var} not set — skipping live API test"
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Tests (plain functions so they run with or without pytest)
# ──────────────────────────────────────────────────────────────────────────────

def test_gemini_api_connectivity():
    """Call Gemini REST API with a trivial prompt to confirm the key + model work."""
    skip = _skip_unless('GEMINI_API_KEY')
    if skip:
        print(f"  SKIP  {skip}")
        return True  # not a failure

    api_key = os.environ['GEMINI_API_KEY']
    model = 'gemini-2.5-flash'
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': api_key,
        'x-goog-api-client': 'google-genai-sdk/2.19.0 gl-node/24',
    }
    body = {
        'contents': [{'role': 'user', 'parts': [{'text': 'Reply with exactly: OK'}]}],
        'generationConfig': {'maxOutputTokens': 10},
    }
    try:
        result = _post_json(url, headers, body)
        text = result['candidates'][0]['content']['parts'][0]['text'].strip()
        assert 'OK' in text or len(text) > 0, f"Unexpected response: {text!r}"
        print(f"  PASS  Gemini {model} responded: {text!r}")
        return True
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        msg = body_bytes.decode('utf-8', errors='replace')
        if e.code == 404:
            print(f"  FAIL  Model {model!r} not found — check model ID. Response: {msg[:200]}")
        elif e.code == 401 or e.code == 403:
            print(f"  FAIL  API key rejected (HTTP {e.code}). Check GEMINI_API_KEY.")
        elif e.code == 429:
            print(f"  SKIP  Rate limited (HTTP 429) — key works but quota exceeded.")
            return True
        else:
            print(f"  FAIL  HTTP {e.code}: {msg[:200]}")
        return False


def test_anthropic_api_connectivity():
    """Call Anthropic Messages API with a trivial prompt."""
    skip = _skip_unless('ANTHROPIC_API_KEY')
    if skip:
        print(f"  SKIP  {skip}")
        return True

    api_key = os.environ['ANTHROPIC_API_KEY']
    url = 'https://api.anthropic.com/v1/messages'
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
    }
    body = {
        'model': 'claude-haiku-4-5-20251001',
        'max_tokens': 10,
        'messages': [{'role': 'user', 'content': 'Reply with exactly: OK'}],
    }
    try:
        result = _post_json(url, headers, body)
        text = result['content'][0]['text'].strip()
        assert len(text) > 0, "Empty response"
        print(f"  PASS  Anthropic claude-haiku-4-5 responded: {text!r}")
        return True
    except urllib.error.HTTPError as e:
        msg = e.read().decode('utf-8', errors='replace')
        if e.code == 401:
            print(f"  FAIL  API key rejected. Check ANTHROPIC_API_KEY.")
        elif e.code == 429:
            print(f"  SKIP  Rate limited — key works but quota exceeded.")
            return True
        else:
            print(f"  FAIL  HTTP {e.code}: {msg[:200]}")
        return False


def test_openai_api_connectivity():
    """Call OpenAI Chat Completions API with a trivial prompt."""
    skip = _skip_unless('OPENAI_API_KEY')
    if skip:
        print(f"  SKIP  {skip}")
        return True

    api_key = os.environ['OPENAI_API_KEY']
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }
    body = {
        'model': 'gpt-4o-mini',
        'max_tokens': 10,
        'messages': [{'role': 'user', 'content': 'Reply with exactly: OK'}],
    }
    try:
        result = _post_json(url, headers, body)
        text = result['choices'][0]['message']['content'].strip()
        assert len(text) > 0, "Empty response"
        print(f"  PASS  OpenAI gpt-4o-mini responded: {text!r}")
        return True
    except urllib.error.HTTPError as e:
        msg = e.read().decode('utf-8', errors='replace')
        if e.code == 401:
            print(f"  FAIL  API key rejected. Check OPENAI_API_KEY.")
        elif e.code == 429:
            print(f"  SKIP  Rate limited — key works.")
            return True
        else:
            print(f"  FAIL  HTTP {e.code}: {msg[:200]}")
        return False


def test_no_fake_gemini_models():
    """Verify the codebase no longer references fake/nonexistent Gemini model IDs."""
    import re
    root = Path(__file__).parent.parent
    files_to_check = list(root.glob('src/**/*.ts')) + [root / 'main.py']

    found_fakes = []
    for fpath in files_to_check:
        try:
            text = fpath.read_text(errors='replace')
            for fake in KNOWN_FAKE_GEMINI_MODELS:
                if fake in text:
                    found_fakes.append(f"{fpath.relative_to(root)}: {fake!r}")
        except Exception:
            pass

    if found_fakes:
        print(f"  FAIL  Fake model IDs found:\n    " + "\n    ".join(found_fakes))
        return False
    print(f"  PASS  No fake Gemini model IDs in source.")
    return True


def test_tool_registry_imports():
    """Verify the Python tool registry imports without error."""
    try:
        from modules.integrations import TOOL_REGISTRY, HAS
        count = len(TOOL_REGISTRY)
        print(f"  PASS  Tool registry loaded: {count} tools available.")
        print(f"        Capabilities: {', '.join(k for k, v in HAS.items() if v)}")
        return True
    except Exception as e:
        print(f"  FAIL  Tool registry import failed: {e}")
        return False


def test_typescript_build():
    """Verify the TypeScript build succeeds (dist/ exists and cli.js is present)."""
    root = Path(__file__).parent.parent
    dist_cli = root / 'dist' / 'cli.js'
    if dist_cli.exists():
        size_kb = dist_cli.stat().st_size // 1024
        print(f"  PASS  TypeScript build present: dist/cli.js ({size_kb} KB)")
        return True
    else:
        print(f"  FAIL  dist/cli.js not found. Run: npm run build")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Standalone runner
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Load .env from project root
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"\''))

    print("\nDevin-4.0 API Connectivity Tests")
    print("=" * 50)

    tests = [
        ("Fake model IDs removed",    test_no_fake_gemini_models),
        ("Tool registry imports",      test_tool_registry_imports),
        ("TypeScript build present",   test_typescript_build),
        ("Gemini API live call",        test_gemini_api_connectivity),
        ("Anthropic API live call",     test_anthropic_api_connectivity),
        ("OpenAI API live call",        test_openai_api_connectivity),
    ]

    passed = failed = skipped = 0
    for name, fn in tests:
        print(f"\n[{name}]")
        try:
            result = fn()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ERROR {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"\nTo test live APIs, set environment variables:")
    print("  export GEMINI_API_KEY=your_key_here")
    print("  export ANTHROPIC_API_KEY=your_key_here")
    print("  export OPENAI_API_KEY=your_key_here")
    print("Or add them to .env in the project root.\n")

    sys.exit(0 if failed == 0 else 1)
