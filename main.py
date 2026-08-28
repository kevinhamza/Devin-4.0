#!/usr/bin/env python3
"""
Devin AGI 4.0 — Python entry point
Claude Code-style interface powered by Gemini.
Integrates 24 external repos: AIA, self-operating-computer, Jarvis, Devin-3.0, OpenDevin, and more.
"""

import os
import sys
import json
import time
import platform
import textwrap
import threading
import subprocess
import tempfile
import signal
import readline  # enables arrow-key history in input()
from pathlib import Path
from typing import Optional, Dict, Any, List

# ── Load .env ────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent.resolve()
_ENV  = _ROOT / ".env"
if _ENV.exists():
    for _line in _ENV.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")

# ── Add all external repos to sys.path ───────────────────────────────────────
_EXT = _ROOT / "external"
_REPOS = [
    "AIA", "self-operating-computer", "Devin-3.0", "Devin-2.0", "Devin",
    "Jarvis", "JARVIS-microsoft", "OpenDevin", "shannon", "gemini-cli",
    "claude-code", "claude-code-source", "cheetahclaws", "hexstrike-ai",
    "openclaw", "airgorah", "hackability", "vulnerability-analysis",
    "Holomat", "PowerTools", "Responder", "nishang", "metasploit-framework",
    "moltbots.github.io",
]
for _r in _REPOS:
    _p = str(_EXT / _r)
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

# Add modules/ and ai_core/ to path
for _d in ["modules", "ai_core", "src"]:
    _p = str(_ROOT / _d)
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

# ── ANSI colors ──────────────────────────────────────────────────────────────
IS_TTY = sys.stdout.isatty()
def _c(code: str, text: str) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if IS_TTY else text

CYAN    = lambda t: _c("96",  t)
BOLD    = lambda t: _c("1",   t)
DIM     = lambda t: _c("2",   t)
GREEN   = lambda t: _c("32",  t)
YELLOW  = lambda t: _c("33",  t)
RED     = lambda t: _c("31",  t)
MAGENTA = lambda t: _c("35",  t)
GRAY    = lambda t: _c("90",  t)
BCYAN   = lambda t: _c("1;96",t)

# ── Banner ────────────────────────────────────────────────────────────────────
def print_banner():
    cols = os.get_terminal_size().columns if IS_TTY else 80
    line = "─" * (cols - 2)
    plat = platform.system()
    print()
    print(CYAN(f"╭{line}╮"))
    print(CYAN("│") + f"  {BOLD(CYAN('Devin AGI'))}  {DIM('v4.0.0')}   {DIM('24 repos integrated')}")
    print(CYAN("│") + f"  {DIM('cwd:')} {str(_ROOT)}")
    print(CYAN("│") + f"  {DIM('platform:')} {plat}   {DIM('model:')} gemini-2.0-flash   {DIM('voice:')} {'on' if VOICE_ENABLED else 'off'}")
    print(CYAN(f"╰{line}╯"))
    print()

# ── Spinner ───────────────────────────────────────────────────────────────────
class Spinner:
    FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    def __init__(self, label="Devin is thinking…"):
        self.label = label
        self._stop = threading.Event()
        self._t: Optional[threading.Thread] = None

    def start(self):
        if not IS_TTY: return
        self._stop.clear()
        self._t = threading.Thread(target=self._spin, daemon=True)
        self._t.start()

    def _spin(self):
        i = 0
        while not self._stop.is_set():
            f = self.FRAMES[i % len(self.FRAMES)]
            sys.stdout.write(f"\r{CYAN(f + ' ' + self.label)}")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1

    def stop(self):
        self._stop.set()
        if self._t: self._t.join(0.3)
        if IS_TTY: sys.stdout.write("\r\x1b[2K")

# ── Optional imports (graceful fallback) ──────────────────────────────────────

# Gemini — prefer new google.genai SDK, fall back to deprecated google.generativeai
try:
    from google import genai as genai_new
    _genai_client = genai_new.Client(api_key=GEMINI_API_KEY)
    HAS_GEMINI = True
    _GENAI_NEW  = True
except Exception:
    _genai_client = None
    _GENAI_NEW = False
    try:
        import google.generativeai as genai
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            genai.configure(api_key=GEMINI_API_KEY)
        HAS_GEMINI = True
    except ImportError:
        HAS_GEMINI = False

# Anthropic
try:
    import anthropic as _anthropic
    HAS_ANTHROPIC = bool(ANTHROPIC_API_KEY)
except ImportError:
    HAS_ANTHROPIC = False

# pyautogui (mouse/keyboard)
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.05
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

# mss (fast screenshots)
try:
    import mss, mss.tools
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

# PIL
try:
    from PIL import Image, ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# pyttsx3 (TTS)
try:
    import pyttsx3 as _pyttsx3
    _tts_engine = _pyttsx3.init()
    _tts_engine.setProperty("rate", 180)
    _tts_engine.setProperty("volume", 0.9)
    HAS_TTS = True
except Exception:
    HAS_TTS = False

# SpeechRecognition (STT)
try:
    import speech_recognition as _sr
    _recognizer = _sr.Recognizer()
    HAS_STT = True
except ImportError:
    HAS_STT = False

# dbus_fast (Linux XDG screenshot portal)
try:
    from dbus_fast.aio import MessageBus
    HAS_DBUS = True
except ImportError:
    HAS_DBUS = False

# webbrowser (always available)
import webbrowser

# AIA modules — add AIA/modules directly so relative imports work
_AIA_MOD_PATH = str(_EXT / "AIA" / "modules")
if os.path.isdir(_AIA_MOD_PATH) and _AIA_MOD_PATH not in sys.path:
    sys.path.insert(0, _AIA_MOD_PATH)

try:
    # AIA's automation.py imports from 'modules.error_handling' — stub it
    import types as _types
    if "modules.error_handling" not in sys.modules:
        _eh = _types.ModuleType("modules.error_handling")
        class _EH:
            def handle_exception(self, e, msg=""): pass
        _eh.ErrorHandling = _EH
        sys.modules["modules.error_handling"] = _eh
        sys.modules["error_handling"] = _eh
    if "modules.device_control" not in sys.modules:
        _dc = _types.ModuleType("modules.device_control")
        class _DC:
            pass
        _dc.DeviceControl = _DC
        sys.modules["modules.device_control"] = _dc
        sys.modules["device_control"] = _dc

    sys.path.insert(0, str(_EXT / "AIA"))
    from automation import Automation as _AIA_Automation
    _aia_auto = _AIA_Automation()
    HAS_AIA_AUTO = True
except Exception as _e:
    _aia_auto = None
    HAS_AIA_AUTO = False

try:
    from internet_tasks import InternetTasks as _AIA_Internet
    _aia_internet = _AIA_Internet()
    HAS_AIA_INTERNET = True
except Exception:
    _aia_internet = None
    HAS_AIA_INTERNET = False

try:
    from device_control import DeviceControl as _AIA_Device
    _aia_device = _AIA_Device()
    HAS_AIA_DEVICE = True
except Exception:
    _aia_device = None
    HAS_AIA_DEVICE = False

# Self-operating-computer
try:
    sys.path.insert(0, str(_EXT / "self-operating-computer"))
    from operate.utils.operating_system import OperatingSystem as _SOC_OS
    _soc_os = _SOC_OS()
    HAS_SOC = True
except Exception:
    _soc_os = None
    HAS_SOC = False

# Jarvis tools
try:
    sys.path.insert(0, str(_EXT / "Jarvis"))
    import tools as _jarvis_tools
    HAS_JARVIS = True
except Exception:
    _jarvis_tools = None
    HAS_JARVIS = False

VOICE_ENABLED = HAS_TTS and HAS_STT

# ── OS automation (our core module) ──────────────────────────────────────────
_AUTOMATION_SCRIPT = str(_ROOT / "modules" / "os_automation.py")
_VENV_PY = str(_ROOT / "venv" / "bin" / "python3")
_PY = _VENV_PY if os.path.exists(_VENV_PY) else sys.executable

def _run_automation(action: str, args: Dict = None, timeout: int = 15) -> Dict:
    """Call os_automation.py subprocess and return JSON result."""
    payload = json.dumps({"action": action, "args": args or {}})
    try:
        env = {**os.environ}
        if platform.system() == "Linux" and "DISPLAY" not in env:
            env["DISPLAY"] = ":0"
        result = subprocess.run(
            [_PY, _AUTOMATION_SCRIPT, payload],
            capture_output=True, text=True, timeout=timeout, env=env
        )
        out = (result.stdout + result.stderr).strip()
        try:
            return json.loads(out)
        except Exception:
            return {"ok": False, "error": out or "no output"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Timeout after {timeout}s"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def automate(action: str, args: Dict = None, timeout: int = 15) -> str:
    r = _run_automation(action, args, timeout)
    if r.get("ok"):
        return str(r.get("result", "OK"))
    return f"Error: {r.get('error', 'unknown')}"

# ── Screenshot ────────────────────────────────────────────────────────────────
def take_screenshot(save_path: str = None) -> str:
    if save_path is None:
        save_path = os.path.join(tempfile.gettempdir(), f"devin_{int(time.time())}.png")
    result = automate("screenshot", {"path": save_path}, timeout=15)
    if "Error" in result:
        return result
    return save_path

def screenshot_base64() -> str:
    return automate("screenshot_b64", {}, timeout=15)

# ── Voice I/O ─────────────────────────────────────────────────────────────────
def speak(text: str):
    if not HAS_TTS: return
    try:
        _tts_engine.say(text)
        _tts_engine.runAndWait()
    except Exception:
        pass

def listen(timeout: int = 8) -> Optional[str]:
    if not HAS_STT: return None
    try:
        with _sr.Microphone() as source:
            _recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
        return _recognizer.recognize_google(audio)
    except Exception:
        return None

# ── Memory ────────────────────────────────────────────────────────────────────
_MEM_FILE = _ROOT / "data" / "memory.json"
_MEM_FILE.parent.mkdir(exist_ok=True)

def _load_memory() -> List[Dict]:
    try:
        return json.loads(_MEM_FILE.read_text()) if _MEM_FILE.exists() else []
    except Exception:
        return []

def _save_memory(entries: List[Dict]):
    try:
        _MEM_FILE.write_text(json.dumps(entries[-500:], indent=2))
    except Exception:
        pass

_MEMORY: List[Dict] = _load_memory()

def remember(content: str, role: str = "user"):
    _MEMORY.append({"role": role, "content": content, "ts": time.time()})
    _save_memory(_MEMORY)

def recall(n: int = 20) -> str:
    recent = _MEMORY[-n:] if len(_MEMORY) >= n else _MEMORY
    return "\n".join(f"[{m['role']}] {m['content'][:200]}" for m in recent)

# ── Tool executor ─────────────────────────────────────────────────────────────
def _run_shell(cmd: str, timeout: int = 30) -> str:
    try:
        env = {**os.environ}
        if platform.system() == "Linux" and "DISPLAY" not in env:
            env["DISPLAY"] = ":0"
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, env=env)
        return (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return f"Timeout after {timeout}s"
    except Exception as e:
        return str(e)

def _run_python(code: str, timeout: int = 30) -> str:
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        fname = f.name
    try:
        r = subprocess.run([_PY, fname], capture_output=True, text=True,
                           timeout=timeout, env={**os.environ})
        out = (r.stdout + r.stderr).strip()
        return out if out else "(no output)"
    except Exception as e:
        return str(e)
    finally:
        try: os.unlink(fname)
        except: pass

TOOLS = {
    # ── OS Automation ──────────────────────────────────────────────────────
    "take_screenshot":     lambda a: take_screenshot(a.get("path")),
    "mouse_click":         lambda a: automate("mouse_click", {"x": int(a["x"]), "y": int(a["y"]),
                                               "button": a.get("button","left"), "double": bool(a.get("double",False))}),
    "mouse_move":          lambda a: automate("mouse_move", {"x": int(a["x"]), "y": int(a["y"])}),
    "mouse_right_click":   lambda a: automate("mouse_right_click", {"x": int(a["x"]), "y": int(a["y"])}),
    "mouse_drag":          lambda a: automate("mouse_drag", {"x1": int(a["x1"]), "y1": int(a["y1"]),
                                               "x2": int(a["x2"]), "y2": int(a["y2"])}),
    "mouse_scroll":        lambda a: automate("mouse_scroll", {"x": int(a["x"]), "y": int(a["y"]),
                                               "direction": a.get("direction","down"), "amount": int(a.get("amount",3))}),
    "keyboard_type":       lambda a: automate("type", {"text": str(a["text"]), "human_like": True}),
    "keyboard_hotkey":     lambda a: automate("hotkey", {"keys": a["keys"]}),
    "keyboard_press":      lambda a: automate("press", {"key": str(a["key"])}),
    "open_application":    lambda a: automate("open_app", {"name": str(a["name"]), "args": a.get("args")}, 10),
    "open_url":            lambda a: automate("open_url", {"url": str(a["url"])}, 10),
    "open_file":           lambda a: automate("open_file", {"path": str(a["path"])}, 10),
    "open_terminal":       lambda a: automate("open_terminal", {}, 8),
    "close_application":   lambda a: automate("close_app", {"name": str(a["name"])}),
    "list_windows":        lambda a: automate("list_windows"),
    "focus_window":        lambda a: automate("focus_window", {"name": str(a["name"])}),
    "get_active_window":   lambda a: automate("active_window"),
    "maximize_window":     lambda a: automate("maximize", {"name": a.get("name")}),
    "minimize_window":     lambda a: automate("minimize"),
    "alt_tab":             lambda a: automate("alt_tab", {"times": int(a.get("times",1))}),
    "clipboard_get":       lambda a: automate("clipboard_get"),
    "clipboard_set":       lambda a: automate("clipboard_set", {"text": str(a["text"])}),
    "get_screen_size":     lambda a: automate("screen_size"),
    "screenshot_all_monitors": lambda a: automate("screenshot_all", {}, 30),
    "find_on_screen":      lambda a: automate("find_on_screen", {"image": str(a["image"]),
                                               "confidence": float(a.get("confidence",0.8))}),
    "click_image":         lambda a: automate("click_image", {"image": str(a["image"])}),
    "volume_up":           lambda a: automate("volume_up", {"steps": int(a.get("steps",5))}),
    "volume_down":         lambda a: automate("volume_down", {"steps": int(a.get("steps",5))}),
    "volume_mute":         lambda a: automate("volume_mute"),
    "volume_set":          lambda a: automate("volume_set", {"level": int(a["level"])}),
    "lock_screen":         lambda a: automate("lock_screen" if hasattr(automate,"lock_screen") else "show_desktop"),
    # ── Files ──────────────────────────────────────────────────────────────
    "read_file":           lambda a: Path(a["path"]).read_text(errors="replace")[:8000] if Path(a["path"]).exists() else "File not found",
    "write_file":          lambda a: (Path(a["path"]).write_text(str(a["content"])), f"Written: {a['path']}")[1],
    "list_files":          lambda a: "\n".join(sorted(str(p) for p in Path(a.get("path",".")).iterdir())[:100]),
    "delete_file":         lambda a: (os.remove(a["path"]), f"Deleted: {a['path']}")[1],
    "file_exists":         lambda a: str(Path(a["path"]).exists()),
    # ── Shell & Code ───────────────────────────────────────────────────────
    "execute_shell":       lambda a: _run_shell(str(a["command"]), int(a.get("timeout",30))),
    "execute_python":      lambda a: _run_python(str(a["code"]), int(a.get("timeout",30))),
    "execute_node":        lambda a: subprocess.run(["node","-e",str(a["code"])], capture_output=True,
                                                     text=True, timeout=15).stdout[:4000],
    "git_command":         lambda a: _run_shell(f"git {a['args']}", 30),
    # ── Web ────────────────────────────────────────────────────────────────
    "web_search":          lambda a: _web_search(str(a["query"])),
    "web_fetch":           lambda a: _web_fetch(str(a["url"])),
    "open_browser":        lambda a: automate("open_url", {"url": str(a["url"])}, 10),
    # ── System ─────────────────────────────────────────────────────────────
    "get_system_info":     lambda a: automate("system_info", {}, 10),
    "list_processes":      lambda a: automate("processes", {"top": int(a.get("top",20))}, 10),
    "speak":               lambda a: (speak(str(a["text"])), "Spoken")[1],
    "listen":              lambda a: listen(int(a.get("timeout",8))) or "No speech detected",
    # ── Memory ─────────────────────────────────────────────────────────────
    "remember":            lambda a: (remember(str(a["content"])), "Saved to memory")[1],
    "recall_memory":       lambda a: recall(int(a.get("n",20))),
    # ── AIA modules ────────────────────────────────────────────────────────
    "aia_automate_typing": lambda a: (_aia_auto.automate_typing(str(a["text"]), float(a.get("interval",0.1))), "Typed")[1] if HAS_AIA_AUTO else "AIA unavailable",
    "aia_automate_mouse":  lambda a: (_aia_auto.automate_mouse(int(a["x"]), int(a["y"]), bool(a.get("click",True))), "Done")[1] if HAS_AIA_AUTO else "AIA unavailable",
    # ── Self-operating-computer ────────────────────────────────────────────
    "soc_screenshot":      lambda a: _soc_screenshot(),
    # ── Task control ───────────────────────────────────────────────────────
    "task_complete":       lambda a: f"✓ {a.get('reason','Done')}",
}

def _web_search(query: str) -> str:
    try:
        import urllib.request, urllib.parse
        url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        # Extract text snippets
        import re
        snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html, re.S)
        clean = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:5]]
        return f"Search: {query}\n" + "\n".join(clean) if clean else f"No results for: {query}"
    except Exception as e:
        return f"Search failed: {e}"

def _web_fetch(url: str) -> str:
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        import re
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:6000]
    except Exception as e:
        return f"Fetch failed: {e}"

def _soc_screenshot() -> str:
    if not HAS_SOC: return "self-operating-computer unavailable"
    try:
        path = os.path.join(tempfile.gettempdir(), f"soc_{int(time.time())}.png")
        _soc_os.screenshot(path)
        return path
    except Exception as e:
        return str(e)

def execute_tool(name: str, args: Dict) -> str:
    fn = TOOLS.get(name)
    if not fn:
        return f"Unknown tool: {name}"
    try:
        result = fn(args)
        return str(result) if result is not None else "OK"
    except Exception as e:
        return f"Tool error: {e}"

# ── Gemini API ────────────────────────────────────────────────────────────────
GEMINI_MODELS = [
    "gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite",
    "gemini-3.7-flash", "gemini-2.5-flash", "gemini-flash-latest",
    "gemini-2.5-flash-lite", "gemini-pro-latest",
]

_TOOL_DEFS = [
    {"name": n, "description": f"Execute {n}", "parameters": {
        "type": "OBJECT",
        "properties": {"_args": {"type": "STRING", "description": "JSON args"}},
        "required": []
    }} for n in TOOLS
]

SYSTEM_PROMPT = """You are Devin AGI 4.0 — a super-intelligent AI software engineer and OS automation agent.
You have REAL control over this computer. You can do everything a senior engineer does.

Platform: """ + platform.system() + """
Capabilities:
- Full OS control: mouse, keyboard, screenshots, windows (use tools!)
- Voice I/O: speak(), listen()
- Files, shell commands, Python/Node execution
- Web search and fetch
- Memory: remember() and recall_memory()
- 24 integrated repos: AIA, self-operating-computer, Jarvis, Devin-2/3, OpenDevin, gemini-cli, claude-code...

CRITICAL RULES:
1. ALWAYS use function calls — NEVER output [Tool: name()] as text.
2. After opening any app, take_screenshot() to see the screen, then act.
3. To type in a browser: mouse_click the address bar first, then keyboard_type the URL.
4. Complete tasks END-TO-END. Don't stop after one step.
5. If a tool fails, try an alternative approach immediately.
6. Call task_complete() when fully done.

Conversation style: Direct, capable, no filler. Like Claude Code."""

class GeminiClient:
    """Uses google.genai (new SDK) with function calling."""

    # Shared parameter schema for all tools
    _PARAM_PROPS = {
        "x":          {"type": "number"},
        "y":          {"type": "number"},
        "x1":         {"type": "number"},
        "y1":         {"type": "number"},
        "x2":         {"type": "number"},
        "y2":         {"type": "number"},
        "text":       {"type": "string"},
        "path":       {"type": "string"},
        "url":        {"type": "string"},
        "name":       {"type": "string"},
        "command":    {"type": "string"},
        "code":       {"type": "string"},
        "query":      {"type": "string"},
        "key":        {"type": "string"},
        "keys":       {"type": "array", "items": {"type": "string"}},
        "button":     {"type": "string"},
        "content":    {"type": "string"},
        "reason":     {"type": "string"},
        "args":       {"type": "string"},
        "image":      {"type": "string"},
        "level":      {"type": "number"},
        "steps":      {"type": "number"},
        "times":      {"type": "number"},
        "timeout":    {"type": "number"},
        "amount":     {"type": "number"},
        "top":        {"type": "number"},
        "n":          {"type": "number"},
        "direction":  {"type": "string"},
        "double":     {"type": "boolean"},
        "confidence": {"type": "number"},
        "click":      {"type": "boolean"},
    }

    def __init__(self):
        if not HAS_GEMINI:
            raise RuntimeError("Install: pip install google-genai")

    def _build_tool_list(self):
        """Build tool declarations as plain dicts (works with both SDK versions)."""
        declarations = []
        for name in TOOLS:
            declarations.append({
                "name": name,
                "description": f"Devin tool: {name}",
                "parameters": {
                    "type": "object",
                    "properties": self._PARAM_PROPS,
                },
            })
        return declarations

    def chat(self, user_msg: str, history: List[Dict]):
        """Send message, return response object. Falls back across models."""
        # Build content list (last 20 turns to stay in token budget)
        contents = []
        for m in history[-20:]:
            role = "model" if m["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        if user_msg:
            contents.append({"role": "user", "parts": [{"text": user_msg}]})

        tools = [{"function_declarations": self._build_tool_list()}]

        last_err = None
        for model_name in GEMINI_MODELS:
            try:
                if _GENAI_NEW and _genai_client:
                    resp = _genai_client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config={
                            "system_instruction": SYSTEM_PROMPT,
                            "tools": tools,
                            "max_output_tokens": 8192,
                        }
                    )
                else:
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        model = genai.GenerativeModel(
                            model_name=model_name,
                            system_instruction=SYSTEM_PROMPT,
                        )
                    resp = model.generate_content(contents)
                return resp
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                if any(x in msg for x in ["429","quota","rate","503","unavailable","resource_exhausted","model_not_found"]):
                    time.sleep(0.5)
                    continue
                break
        raise RuntimeError(f"All Gemini models failed: {last_err}")

# ── Print helpers ─────────────────────────────────────────────────────────────
def print_tool_call(name: str, args: Dict):
    args_str = ", ".join(f"{k}={repr(v)[:40]}" for k, v in args.items())[:100]
    print(f"\n{DIM('  ● ')}{CYAN(name)}{DIM('(' + args_str + ')')}")

def print_tool_result(result: str, is_error: bool = False):
    color = RED if is_error else GRAY
    # Hide raw base64 image data
    import re
    display = re.sub(r'__IMG__([\w/]+)__[A-Za-z0-9+/=]{100,}__ENDIMG__',
                     lambda m: f'[Image: {m.group(1)}]', result)
    preview = display.strip()[:300].replace('\n', ' ')
    suffix = "…" if len(display) > 300 else ""
    icon = "  ✗ " if is_error else "  ↳ "
    line = icon + preview + suffix
    if IS_TTY:
        code = "31" if is_error else "90"
        print(f"\x1b[{code}m{line}\x1b[0m")
    else:
        print(line)

def print_devin(text: str):
    print()
    print(BCYAN("Devin"))
    # Simple markdown: bold, inline code, bullets
    import re
    for line in text.split('\n'):
        line = re.sub(r'\*\*(.+?)\*\*', lambda m: BOLD(m.group(1)), line)
        line = re.sub(r'`([^`]+)`', lambda m: CYAN(m.group(1)), line)
        if line.startswith('- ') or line.startswith('• '):
            line = GRAY('• ') + line[2:]
        print(line)
    print()

# ── Main conversation loop ────────────────────────────────────────────────────
def run_conversation(client: GeminiClient, user_input: str, history: List[Dict]):
    """Run a full agentic loop until task_complete or no more tool calls."""
    MAX_STEPS = 30
    spinner = Spinner()
    history.append({"role": "user", "content": user_input})
    remember(user_input, "user")

    current_input = user_input
    conv_history = history[:-1]  # pass history without latest user msg

    for step in range(MAX_STEPS):
        spinner.start()
        try:
            resp = client.chat(current_input if step == 0 else "", conv_history if step == 0 else history[:-1])
        except Exception as e:
            spinner.stop()
            print(RED(f"✗ API error: {e}"))
            return
        spinner.stop()

        # Extract text and function calls — handles new google.genai SDK
        text_parts = []
        func_calls = []

        try:
            # New SDK: resp.text, resp.function_calls
            if _GENAI_NEW:
                raw_text = getattr(resp, 'text', None)
                if raw_text: text_parts.append(raw_text)
                fcs = getattr(resp, 'function_calls', None) or []
                for fc in fcs:
                    fc_args = {}
                    try: fc_args = dict(fc.args or {})
                    except Exception: pass
                    func_calls.append({"name": fc.name, "args": fc_args})
            # Old SDK fallback
            else:
                candidates = getattr(resp, 'candidates', None) or []
                for candidate in candidates:
                    content = getattr(candidate, 'content', None)
                    parts = getattr(content, 'parts', None) or []
                    for part in parts:
                        t = getattr(part, 'text', None)
                        if t: text_parts.append(t)
                        fc = getattr(part, 'function_call', None)
                        if fc:
                            fc_args = {}
                            try: fc_args = dict(getattr(fc, 'args', {}) or {})
                            except Exception: pass
                            func_calls.append({"name": fc.name, "args": fc_args})
        except Exception as e:
            print(RED(f"✗ Response parse error: {e}"))
            break

        text_output = "\n".join(text_parts).strip()

        # Check for [Tool: name()] pattern in text (fallback)
        if not func_calls and text_output:
            import re
            for m in re.finditer(r'\[Tool:\s*(\w+)\s*\(([^)]*)\)\]', text_output):
                tname = m.group(1)
                try:
                    targs = json.loads(m.group(2) or '{}')
                except Exception:
                    targs = {}
                if tname in TOOLS:
                    func_calls.append({"name": tname, "args": targs})
            if func_calls:
                text_output = re.sub(r'\[Tool:\s*\w+\s*\([^)]*\)\]', '', text_output).strip()

        # Print assistant text
        if text_output:
            print_devin(text_output)
            history.append({"role": "assistant", "content": text_output})
            remember(text_output, "assistant")

        # No tool calls → done
        if not func_calls:
            break

        # Execute tool calls
        tool_results = []
        task_done = False
        for fc in func_calls:
            name = fc["name"]
            args = fc["args"]

            print_tool_call(name, args)

            result = execute_tool(name, args)
            is_err = result.startswith("Error") or result.startswith("Unknown tool")
            print_tool_result(result, is_err)

            tool_results.append(f"[{name}] → {result[:500]}")

            if name == "task_complete":
                task_done = True

        # Add tool results to history
        tool_summary = "\n".join(tool_results)
        history.append({"role": "user", "content": f"Tool results:\n{tool_summary}"})

        if task_done:
            break

        # Prepare next prompt
        current_input = f"Tool results:\n{tool_summary}\n\nContinue."

    return

# ── Slash commands ────────────────────────────────────────────────────────────
def handle_slash(cmd: str, history: List[Dict]) -> bool:
    """Returns True if command was handled."""
    cmd = cmd.strip().lower()
    if cmd in ("/help", "/h"):
        print(BOLD("\nSlash commands:"))
        cmds = [
            ("/help",       "Show this help"),
            ("/clear",      "Clear conversation history"),
            ("/memory",     "Show recent memory"),
            ("/voice",      "Toggle voice mode"),
            ("/screenshot", "Take a screenshot"),
            ("/status",     "Show system status"),
            ("/tools",      "List all available tools"),
            ("/repos",      "List integrated repos"),
            ("/shell <cmd>","Run shell command directly"),
            ("exit/quit",   "Quit Devin"),
        ]
        for c, d in cmds:
            print(f"  {CYAN(c.ljust(18))}{DIM(d)}")
        print()
        return True

    if cmd == "/clear":
        history.clear()
        print(GREEN("✓ Conversation cleared"))
        return True

    if cmd == "/memory":
        print(BOLD("\nRecent memory:"))
        print(DIM(recall(20)))
        return True

    if cmd == "/voice":
        global VOICE_ENABLED
        VOICE_ENABLED = not VOICE_ENABLED
        print(GREEN(f"✓ Voice {'enabled' if VOICE_ENABLED else 'disabled'}"))
        return True

    if cmd == "/screenshot":
        path = take_screenshot()
        print(GREEN(f"✓ Screenshot: {path}"))
        return True

    if cmd == "/status":
        print(BOLD("\nSystem status:"))
        print(f"  {DIM('Platform:')}    {platform.system()} {platform.release()}")
        print(f"  {DIM('Python:')}      {sys.version.split()[0]}")
        print(f"  {DIM('Gemini:')}      {'✓' if HAS_GEMINI else '✗'}")
        print(f"  {DIM('pyautogui:')}   {'✓' if HAS_PYAUTOGUI else '✗'}")
        print(f"  {DIM('mss:')}         {'✓' if HAS_MSS else '✗'}")
        print(f"  {DIM('TTS:')}         {'✓' if HAS_TTS else '✗'}")
        print(f"  {DIM('STT:')}         {'✓' if HAS_STT else '✗'}")
        print(f"  {DIM('AIA:')}         {'✓' if HAS_AIA_AUTO else '✗'}")
        print(f"  {DIM('SOC:')}         {'✓' if HAS_SOC else '✗'}")
        print(f"  {DIM('Jarvis:')}      {'✓' if HAS_JARVIS else '✗'}")
        print()
        return True

    if cmd == "/tools":
        print(BOLD(f"\nAvailable tools ({len(TOOLS)}):"))
        for i, name in enumerate(sorted(TOOLS)):
            end = "\n" if (i+1) % 4 == 0 else "   "
            print(f"  {CYAN(name)}", end=end)
        print("\n")
        return True

    if cmd == "/repos":
        print(BOLD("\nIntegrated repos:"))
        for r in _REPOS:
            p = _EXT / r
            status = GREEN("✓") if p.exists() else RED("✗")
            print(f"  {status} {r}")
        print()
        return True

    if cmd.startswith("/shell "):
        shell_cmd = cmd[7:]
        out = _run_shell(shell_cmd)
        print(DIM(out))
        return True

    return False

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    global VOICE_ENABLED

    # Parse args
    import argparse
    parser = argparse.ArgumentParser(description="Devin AGI 4.0")
    parser.add_argument("--voice", action="store_true", help="Enable voice mode")
    parser.add_argument("--prompt", "-p", help="Run a single prompt and exit")
    parser.add_argument("--no-banner", action="store_true", help="Skip banner")
    args = parser.parse_args()

    if args.voice:
        VOICE_ENABLED = True

    if not args.no_banner:
        print_banner()

    if not HAS_GEMINI:
        print(RED("✗ google-generativeai not installed. Run: pip install google-generativeai"))
        sys.exit(1)

    try:
        client = GeminiClient()
        print(GREEN("✓ Connected to Gemini"))
    except Exception as e:
        print(RED(f"✗ Gemini init failed: {e}"))
        sys.exit(1)

    # Report integration status
    active = []
    if HAS_AIA_AUTO:    active.append("AIA")
    if HAS_SOC:         active.append("SOC")
    if HAS_JARVIS:      active.append("Jarvis")
    if HAS_TTS:         active.append("TTS")
    if HAS_STT:         active.append("STT")
    if active:
        print(DIM(f"  Active integrations: {', '.join(active)}"))
    print()

    history: List[Dict] = []

    # Single prompt mode
    if args.prompt:
        run_conversation(client, args.prompt, history)
        return

    # Voice greeting
    if VOICE_ENABLED:
        speak("Hello! I am Devin, your AI software engineer. How can I help you?")

    print(DIM("Talk to Devin — ask a question, give a task, or type /help. (exit to quit)\n"))

    # REPL loop
    while True:
        try:
            # Voice input
            if VOICE_ENABLED:
                print(DIM("🎤 Listening…"))
                text = listen(timeout=8)
                if text:
                    print(f"{CYAN('❯')} {text}")
                    user_input = text
                else:
                    # Fall back to keyboard
                    try:
                        user_input = input(BCYAN("❯ ") + DIM("Devin-4.0 ")).strip()
                    except (EOFError, KeyboardInterrupt):
                        break
            else:
                try:
                    user_input = input(BCYAN("❯ ") + DIM("Devin-4.0 ")).strip()
                except (EOFError, KeyboardInterrupt):
                    break

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print(DIM("Goodbye."))
                speak("Goodbye!")
                break

            if handle_slash(user_input, history):
                continue

            run_conversation(client, user_input, history)

        except KeyboardInterrupt:
            print()
            print(DIM("  (Ctrl+C — type 'exit' to quit)"))

if __name__ == "__main__":
    main()
