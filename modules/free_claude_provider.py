"""modules/free_claude_provider.py — Free Claude Code integration

Integrates the free-claude-code project as a fallback AI provider
when no commercial API keys are configured.

Source: https://github.com/alishahryar1/free-claude-code
Strategy: subprocess-based or HTTP-based depending on availability.

Fall-through order when this module is active:
  1. free-claude-code subprocess (if installed)
  2. Claude.ai unofficial session (if session cookie available)
  3. Other free providers (HF, local Ollama)
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("FreeClaudeProvider")
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.INFO)
log.propagate = False

_ROOT = Path(__file__).resolve().parent.parent
_FREE_CLAUDE_DIR = _ROOT / "repos" / "free-claude-code"


def _find_free_claude_binary() -> Optional[Path]:
    """Locate the free-claude-code executable."""
    candidates = [
        _FREE_CLAUDE_DIR / "bin" / "claude",
        _FREE_CLAUDE_DIR / "index.js",
        _FREE_CLAUDE_DIR / "cli.js",
        Path(os.environ.get("FREE_CLAUDE_PATH", "")) if os.environ.get("FREE_CLAUDE_PATH") else None,
    ]
    for c in candidates:
        if c and c.exists():
            return c
    # Check PATH
    import shutil
    p = shutil.which("free-claude")
    if p:
        return Path(p)
    p = shutil.which("claude-free")
    if p:
        return Path(p)
    return None


def is_available() -> bool:
    """Return True if free-claude-code is available."""
    # Check for session cookie
    session_key = os.environ.get("CLAUDE_SESSION_KEY") or os.environ.get("FREE_CLAUDE_SESSION")
    if session_key:
        return True
    # Check for binary
    return _find_free_claude_binary() is not None


def _call_via_session_key(messages: List[Dict], system: str) -> str:
    """Call Claude via session key (unofficial API)."""
    session_key = os.environ.get("CLAUDE_SESSION_KEY") or os.environ.get("FREE_CLAUDE_SESSION", "")
    if not session_key:
        raise RuntimeError("CLAUDE_SESSION_KEY not set")

    try:
        import requests  # type: ignore
        # Build conversation text
        conv = ""
        if system:
            conv = f"System: {system}\n\n"
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            conv += f"{role.capitalize()}: {content}\n"

        # Use the free-claude-code API format
        headers = {
            "Content-Type": "application/json",
            "Cookie": f"sessionKey={session_key}",
        }
        payload = {
            "prompt": conv,
            "model": "claude-opus-4-5",
        }
        resp = requests.post(
            "https://claude.ai/api/append_message",
            headers=headers,
            json=payload,
            timeout=60,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("completion", "") or str(data)
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
    except ImportError:
        raise RuntimeError("requests not available")


def _call_via_subprocess(messages: List[Dict], system: str) -> str:
    """Call free-claude-code via subprocess."""
    binary = _find_free_claude_binary()
    if binary is None:
        raise RuntimeError("free-claude-code binary not found")

    # Build prompt
    prompt_parts = []
    if system:
        prompt_parts.append(f"[System]: {system}")
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        prompt_parts.append(f"[{role.capitalize()}]: {content}")
    prompt = "\n".join(prompt_parts)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        cmd = ["node", str(binary), "--prompt-file", prompt_file] if binary.suffix == ".js" else [str(binary), "--prompt-file", prompt_file]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return result.stdout.strip()
        raise RuntimeError(f"Subprocess failed: {result.stderr[:300]}")
    finally:
        try:
            os.unlink(prompt_file)
        except Exception:
            pass


def chat(messages: List[Dict], system: str = "") -> Tuple[str, List]:
    """Free Claude chat. Returns (text, tool_calls)."""
    # Try session key first
    try:
        text = _call_via_session_key(messages, system)
        return text, []
    except Exception as e:
        log.debug("Session key method failed: %s", e)

    # Try subprocess
    try:
        text = _call_via_subprocess(messages, system)
        return text, []
    except Exception as e:
        log.debug("Subprocess method failed: %s", e)

    raise RuntimeError("free-claude-code: all methods failed")


def ensure_installed():
    """Attempt to install free-claude-code if not present."""
    if _find_free_claude_binary():
        return True
    try:
        _FREE_CLAUDE_DIR.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", "https://github.com/alishahryar1/free-claude-code",
             str(_FREE_CLAUDE_DIR)],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            # Install npm deps
            subprocess.run(["npm", "install"], cwd=str(_FREE_CLAUDE_DIR), timeout=120)
            return True
    except Exception as e:
        log.warning("Could not install free-claude-code: %s", e)
    return False
