"""modules/devin_integration.py — Capability Integration Bridge

Auto-loaded by agent.py's module scanner (modules/*.py discovery).
Injects new capability tools from os_agent, reasoning_engine,
system_monitor, and voice_engine into agent.py's TOOLS dict.

Works without any modification to agent.py:
  1. Gets singletons from sys.modules['_devin_caps'] (set by main.py)
     or falls back to factory functions.
  2. Finds agent.py's TOOLS dict via call-stack frame inspection.
  3. Injects up to 13 new tools if TOOLS is found in the frame.

All failures are silent — if any step fails the rest of agent.py
continues normally with its original 136 tools.
"""
from __future__ import annotations
import sys
from typing import Any, Dict, Optional


# ── Get capability singletons ─────────────────────────────────────────────────

def _get_caps():
    """Load capability singletons from registry or factory functions."""
    reg = sys.modules.get('_devin_caps')
    if reg is not None:
        return reg

    class _Fallback:
        os_agent = reasoning = system_monitor = voice = browser = None
        hf_provider = free_claude = conversation = None

    fb = _Fallback()
    try:
        from modules.os_agent import get_os_agent
        fb.os_agent = get_os_agent()
    except Exception:
        pass
    try:
        from modules.reasoning_engine import get_reasoning_engine  # type: ignore
        fb.reasoning = get_reasoning_engine()
    except Exception:
        try:
            from modules.reasoning_engine import get_engine  # type: ignore
            fb.reasoning = get_engine()
        except Exception:
            pass
    try:
        from modules.system_monitor_enhanced import get_system_monitor
        fb.system_monitor = get_system_monitor()
    except Exception:
        pass
    try:
        from modules.voice_engine import get_voice_engine
        fb.voice = get_voice_engine()
    except Exception:
        pass
    return fb


# ── String-coerce ActionResult or any return value ────────────────────────────

def _s(r: Any) -> str:
    if hasattr(r, 'vision_result') and r.vision_result:
        return str(r.vision_result)
    if hasattr(r, 'message'):
        return str(r.message)
    if isinstance(r, str):
        return r
    try:
        import json
        return json.dumps(r, default=str)
    except Exception:
        return str(r)


# ── Build new tool definitions ────────────────────────────────────────────────

def _build_new_tools(caps) -> Dict[str, Any]:
    tools: Dict[str, Any] = {}
    oa  = getattr(caps, 'os_agent', None)
    re_ = getattr(caps, 'reasoning', None)
    sm  = getattr(caps, 'system_monitor', None)
    ve  = getattr(caps, 'voice', None)

    if oa:
        tools['os_screenshot_analyze'] = {
            'fn': lambda prompt='Describe everything visible on screen':
                _s(oa.screenshot(str(prompt))),
            'desc': 'Take a screenshot and have AI describe what is on screen in detail',
            'params': {'prompt': {'type': 'string', 'description': 'What to look for or describe'}},
            'required': [],
            'category': 'OS Control',
        }
        tools['os_observe_screen'] = {
            'fn': lambda: _s(oa.observe()),
            'desc': 'Capture and return a detailed description of the entire current screen',
            'params': {},
            'required': [],
            'category': 'OS Control',
        }
        tools['os_vision_click'] = {
            'fn': lambda description='': _s(oa.click_element(str(description))),
            'desc': 'Find and click a UI element by visual description (e.g. "OK button", "search box")',
            'params': {'description': {'type': 'string', 'description': 'Visual description of the UI element'}},
            'required': ['description'],
            'category': 'OS Control',
        }
        tools['os_open_application'] = {
            'fn': lambda app_name='': _s(oa.open_application(str(app_name))),
            'desc': 'Open an application by name — works on Linux, macOS, Windows',
            'params': {'app_name': {'type': 'string', 'description': 'Name of the application to open'}},
            'required': ['app_name'],
            'category': 'OS Control',
        }
        tools['os_find_element'] = {
            'fn': lambda description='': _s(oa.find_element(str(description))),
            'desc': 'Find a UI element by visual description and return its (x,y) pixel coordinates',
            'params': {'description': {'type': 'string', 'description': 'Description of the element'}},
            'required': ['description'],
            'category': 'OS Control',
        }
        tools['os_list_windows'] = {
            'fn': lambda: str(oa.list_windows()),
            'desc': 'List all open windows with their titles and IDs',
            'params': {},
            'required': [],
            'category': 'OS Control',
        }
        tools['os_focus_window'] = {
            'fn': lambda title='': _s(oa.focus_window(str(title))),
            'desc': 'Bring a window to focus by matching its title (partial match)',
            'params': {'title': {'type': 'string', 'description': 'Window title or partial title to match'}},
            'required': ['title'],
            'category': 'OS Control',
        }
        tools['os_navigate_url'] = {
            'fn': lambda url='': _s(oa.navigate_browser(str(url))),
            'desc': 'Open a URL in the default web browser',
            'params': {'url': {'type': 'string', 'description': 'URL to open'}},
            'required': ['url'],
            'category': 'OS Control',
        }
        tools['os_execute_task_steps'] = {
            'fn': lambda task='', steps='[]': _s(oa.execute_task_with_vision(
                str(task),
                __import__('json').loads(str(steps)) if isinstance(steps, str) else steps
            )),
            'desc': 'Execute a multi-step OS automation task with vision verification',
            'params': {
                'task': {'type': 'string', 'description': 'Description of the overall task'},
                'steps': {'type': 'string', 'description': 'JSON array of step dicts: {"action":"click","x":100,"y":200}'},
            },
            'required': ['task', 'steps'],
            'category': 'OS Control',
        }

    if re_:
        tools['think_step_by_step'] = {
            'fn': lambda problem='', context='':
                (lambda res: res.answer if hasattr(res, 'answer') else str(res))(
                    re_.think(str(problem), context=str(context))
                ),
            'desc': 'Use chain-of-thought + ReAct loop to reason about and solve a complex problem',
            'params': {
                'problem': {'type': 'string', 'description': 'The problem or task to reason about'},
                'context': {'type': 'string', 'description': 'Additional context (optional)'},
            },
            'required': ['problem'],
            'category': 'Reasoning',
        }

    if sm:
        tools['detailed_system_status'] = {
            'fn': lambda: sm.summary(),
            'desc': 'Get detailed system status: CPU, RAM, disk, swap, GPU, top processes',
            'params': {},
            'required': [],
            'category': 'System',
        }

    if ve:
        tools['speak_aloud'] = {
            'fn': lambda text='': ve.speak(str(text)),
            'desc': 'Convert text to speech and play through speakers (TTS)',
            'params': {'text': {'type': 'string', 'description': 'Text to speak aloud'}},
            'required': ['text'],
            'category': 'Voice',
        }
        tools['listen_for_voice'] = {
            'fn': lambda timeout=10: ve.listen_once(float(timeout)),
            'desc': 'Listen for voice input via microphone and return transcribed text (STT)',
            'params': {'timeout': {'type': 'number', 'description': 'How many seconds to listen (default 10)'}},
            'required': [],
            'category': 'Voice',
        }

    return tools


# ── Find TOOLS dict in agent.py via call-stack frame inspection ────────────────

def _find_agent_tools() -> Optional[Dict]:
    """Walk the call stack to find agent.py's TOOLS dict."""
    try:
        frame = sys._getframe()
        while frame is not None:
            fname = frame.f_code.co_filename or ''
            if fname.endswith('agent.py') or '/agent.py' in fname or '\\agent.py' in fname:
                globs = frame.f_globals
                if 'TOOLS' in globs and isinstance(globs['TOOLS'], dict):
                    return globs['TOOLS']
            frame = frame.f_back
    except Exception:
        pass
    # Fallback: __main__ module
    main_mod = sys.modules.get('__main__')
    if main_mod and hasattr(main_mod, 'TOOLS') and isinstance(main_mod.TOOLS, dict):  # type: ignore
        return main_mod.TOOLS  # type: ignore
    return None


# ── Main patch function ───────────────────────────────────────────────────────

def patch_agent_tools() -> int:
    """
    Inject capability tools into agent.py's TOOLS dict.
    Returns the number of tools added (0 if TOOLS not found or no caps).
    """
    try:
        tools_dict = _find_agent_tools()
        if tools_dict is None:
            return 0

        caps = _get_caps()
        new_tools = _build_new_tools(caps)
        if not new_tools:
            return 0

        added = 0
        for name, defn in new_tools.items():
            if name not in tools_dict:
                tools_dict[name] = defn
                added += 1
        return added
    except Exception:
        return 0


# ── Auto-run on import ────────────────────────────────────────────────────────
_patched_count = patch_agent_tools()
