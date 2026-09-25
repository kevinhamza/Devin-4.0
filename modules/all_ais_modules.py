"""
Unified capability registry for Devin-4.0.
Wires all new modules into a single importable namespace.
"""

import sys
from typing import Dict, Any, Optional

# --- Import all capability modules with graceful fallback ---

_MODULES: Dict[str, Any] = {}
_ERRORS: Dict[str, str] = {}


def _try_import(name: str, import_fn):
    try:
        mod = import_fn()
        _MODULES[name] = mod
    except BaseException as e:
        _ERRORS[name] = str(e)


def _load_all():
    _try_import("os_agent", lambda: __import__("modules.os_agent", fromlist=["get_os_agent"]))
    _try_import("reasoning_engine", lambda: __import__("modules.reasoning_engine", fromlist=["get_reasoning_engine"]))
    _try_import("conversation_engine", lambda: __import__("modules.conversation_engine", fromlist=["get_conversation_engine"]))
    _try_import("hf_enhanced", lambda: __import__("modules.hf_enhanced_provider", fromlist=["chat"]))
    _try_import("free_claude", lambda: __import__("modules.free_claude_provider", fromlist=["is_available"]))
    _try_import("system_monitor", lambda: __import__("modules.system_monitor_enhanced", fromlist=["get_system_monitor"]))
    _try_import("voice", lambda: __import__("modules.voice_engine", fromlist=["get_voice_engine"]))
    _try_import("browser", lambda: __import__("modules.browser_agent", fromlist=["get_browser_agent"]))
    _try_import("hf_provider", lambda: __import__("modules.hf_provider", fromlist=["chat"]))
    _try_import("keyboard_mouse", lambda: __import__("modules.keyboard_mouse_control", fromlist=["KeyboardMouseController"]))


_load_all()


# --- Public accessors ---

def get_os_agent(**kwargs):
    mod = _MODULES.get("os_agent")
    if mod:
        return mod.get_os_agent(**kwargs)
    return None


def get_reasoning_engine(**kwargs):
    mod = _MODULES.get("reasoning_engine")
    if mod:
        return mod.get_reasoning_engine(**kwargs)
    return None


def get_conversation_engine(**kwargs):
    mod = _MODULES.get("conversation_engine")
    if mod:
        return mod.get_conversation_engine(**kwargs)
    return None


def get_system_monitor(**kwargs):
    mod = _MODULES.get("system_monitor")
    if mod:
        return mod.get_system_monitor(**kwargs)
    return None


def get_voice_engine(**kwargs):
    mod = _MODULES.get("voice")
    if mod:
        return mod.get_voice_engine(**kwargs)
    return None


def get_browser_agent(**kwargs):
    mod = _MODULES.get("browser")
    if mod:
        return mod.get_browser_agent(**kwargs)
    return None


def capability_map() -> Dict[str, bool]:
    """Return which capabilities are available in this environment."""
    return {
        "os_agent": "os_agent" in _MODULES,
        "reasoning_engine": "reasoning_engine" in _MODULES,
        "conversation_engine": "conversation_engine" in _MODULES,
        "hf_enhanced_provider": "hf_enhanced" in _MODULES,
        "free_claude_provider": "free_claude" in _MODULES,
        "system_monitor": "system_monitor" in _MODULES,
        "voice_engine": "voice" in _MODULES,
        "browser_agent": "browser" in _MODULES,
        "hf_provider": "hf_provider" in _MODULES,
        "keyboard_mouse": "keyboard_mouse" in _MODULES,
    }


def print_capabilities() -> str:
    cmap = capability_map()
    lines = ["Devin-4.0 Capability Status:", "=" * 40]
    for cap, available in cmap.items():
        status = "✅ available" if available else "❌ missing"
        error = _ERRORS.get(cap, "")
        if error and not available:
            lines.append(f"  {status:20s}  {cap}  ({error[:60]})")
        else:
            lines.append(f"  {status:20s}  {cap}")
    return "\n".join(lines)


def system_summary() -> str:
    mon = get_system_monitor()
    if mon:
        return mon.summary()
    return "ERROR: system_monitor_enhanced not loaded"


def speak(text: str) -> str:
    ve = get_voice_engine()
    if ve:
        return ve.speak(text)
    return "ERROR: voice_engine not loaded"


def listen(timeout: float = 10.0) -> str:
    ve = get_voice_engine()
    if ve:
        return ve.listen_once(timeout=timeout)
    return "ERROR: voice_engine not loaded"


def browse(url: str) -> str:
    ba = get_browser_agent()
    if ba:
        return ba.navigate(url)
    return "ERROR: browser_agent not loaded"


def observe_screen() -> str:
    oa = get_os_agent()
    if oa:
        return oa.observe()
    return "ERROR: os_agent not loaded"


def think(task: str, context: str = "") -> str:
    re = get_reasoning_engine()
    if re:
        result = re.think(task, context=context)
        return result.answer
    return "ERROR: reasoning_engine not loaded"
