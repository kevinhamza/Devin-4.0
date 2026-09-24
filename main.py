#!/usr/bin/env python3
"""
Devin AGI 4.0 — Unified Python Entry Point
Claude Code-style interface powered by Gemini.
All 24 external repos integrated via modules/integrations.py.
"""

# ── stdlib (always available) ─────────────────────────────────────────────────
import os, sys, json, time, platform, threading, subprocess, tempfile
import signal, textwrap, re, shutil, base64
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# ── Bootstrap .env ────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent.resolve()
_ENV  = _ROOT / ".env"
if _ENV.exists():
    for _l in _ENV.read_text().splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _, _v = _l.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")

# ── Add root, repos/*, external/* to sys.path ────────────────────────────────
# Must happen before any local imports below.
def _ensure_path(p: Path):
    s = str(p)
    if p.is_dir() and s not in sys.path:
        sys.path.insert(0, s)

_ensure_path(_ROOT)  # makes "modules.integrations" importable
for _base in [_ROOT / "repos", _ROOT / "external", _ROOT / "modules", _ROOT / "ai_core"]:
    _ensure_path(_base)
    if _base.is_dir():
        for _sub in _base.iterdir():
            if _sub.is_dir() and not _sub.name.startswith('.'):
                _ensure_path(_sub)

# ── Load integrations (all repos) ─────────────────────────────────────────────
import importlib.util as _ilu
_ipath = _ROOT / "modules" / "integrations.py"
_ispec = _ilu.spec_from_file_location("modules.integrations", str(_ipath))
_imod  = _ilu.module_from_spec(_ispec)  # type: ignore
_ispec.loader.exec_module(_imod)  # type: ignore
sys.modules["modules.integrations"] = _imod
from modules.integrations import (
    TOOL_REGISTRY, HAS, capabilities_summary,
    take_screenshot, mouse_click, mouse_right_click, mouse_double_click,
    mouse_move, mouse_drag, mouse_scroll, keyboard_type, keyboard_press,
    keyboard_hotkey, get_screen_size, list_windows, focus_window,
    open_application, execute_shell, execute_python, read_file, write_file,
    list_files, web_search, web_fetch, open_browser, speak, listen,
    clipboard_get, clipboard_set, get_system_info, list_processes,
    run_nmap_scan, git_command,
)

# ── Rich (Claude Code-style TUI) ──────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
    from rich.rule import Rule
    from rich.live import Live
    from rich.spinner import Spinner as RichSpinner
    from rich.columns import Columns
    console = Console(markup=True, highlight=True)
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False

# ── Gemini REST API ───────────────────────────────────────────────────────────
_GEMINI_REST_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_GEMINI_MODELS = [
    "gemini-2.5-flash",      # primary — current fast model (Jan 2026)
    "gemini-2.5-pro",        # higher-quality fallback
    "gemini-2.0-flash",      # older-gen fallback
    "gemini-flash-latest",   # latest alias
    "gemini-1.5-flash",      # legacy fallback
]
HAS_GEMINI = bool(GEMINI_API_KEY)

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False
    HAS_GEMINI = False

# ── Anthropic (Claude fallback) ───────────────────────────────────────────────
_anthropic_client = None
try:
    import anthropic as _anthropic
    if ANTHROPIC_API_KEY:
        _anthropic_client = _anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    HAS_ANTHROPIC = bool(ANTHROPIC_API_KEY)
except Exception:
    HAS_ANTHROPIC = False

# ── Hugging Face (free-tier fallback) ─────────────────────────────────────────
# Load hf_provider defensively: main.py hand-loads modules.integrations via
# importlib.util which can interfere with normal `from modules.x import` — so we
# try the package path first, then a direct file load, then give up.
_hf_chat = None
HAS_HF = False
try:
    from modules.hf_provider import chat as _hf_chat, has_hf_token as _hf_has_token
    HAS_HF = _hf_has_token()
except Exception:
    try:
        _hf_path = _ROOT / "modules" / "hf_provider.py"
        _hf_spec = _ilu.spec_from_file_location("modules.hf_provider", str(_hf_path))
        _hf_mod = _ilu.module_from_spec(_hf_spec)  # type: ignore
        _hf_spec.loader.exec_module(_hf_mod)  # type: ignore
        sys.modules["modules.hf_provider"] = _hf_mod
        _hf_chat = _hf_mod.chat
        HAS_HF = _hf_mod.has_hf_token()
    except Exception:
        if os.getenv("DEVIN_DEBUG"):
            import traceback; traceback.print_exc()
        _hf_chat = None
        HAS_HF = False

# ── Memory ────────────────────────────────────────────────────────────────────
_MEMORY_FILE = _ROOT / "data" / "memory.json"
_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

def _load_memory() -> Dict:
    """Load facts/history dict from data/memory.json. Older Devin versions and
    the persistent_memory module use different formats (a bare list of history
    entries); when we see one of those we migrate it in-memory rather than
    crashing."""
    default = {"facts": [], "history": []}
    if not _MEMORY_FILE.exists():
        return default
    try:
        raw = json.loads(_MEMORY_FILE.read_text())
    except Exception:
        return default
    if isinstance(raw, dict):
        raw.setdefault("facts", [])
        raw.setdefault("history", [])
        return raw
    if isinstance(raw, list):
        # Treat legacy list-shaped file as pure history; no facts recorded.
        return {"facts": [], "history": raw}
    return default

def _save_memory(mem: Dict):
    _MEMORY_FILE.write_text(json.dumps(mem, indent=2))

def remember(fact: str) -> str:
    mem = _load_memory()
    mem["facts"].append({"fact": fact, "time": datetime.now().isoformat()})
    _save_memory(mem)
    return f"Remembered: {fact}"

def recall(query: str = "") -> str:
    mem = _load_memory()
    facts = mem.get("facts", [])
    if not query:
        return "\n".join(f["fact"] for f in facts[-20:]) or "No memories."
    q = query.lower()
    matches = [f["fact"] for f in facts if q in f["fact"].lower()]
    return "\n".join(matches[-10:]) or "No matching memories."

# ── Voice / permission / verbosity mode flags ────────────────────────────────
VOICE_MODE = False
# permission_mode: 'default' (confirm dangerous), 'auto' (auto-approve), or
# 'plan' (describe actions but don't run any tools).
PERMISSION_MODE = os.environ.get("DEVIN_PERMISSION_MODE", "auto")
VERBOSE = bool(os.environ.get("DEVIN_VERBOSE") or os.environ.get("DEVIN_DEBUG"))

# ── Print helpers ─────────────────────────────────────────────────────────────
IS_TTY = sys.stdout.isatty()

def _c(code: str, t: str) -> str:
    return f"\x1b[{code}m{t}\x1b[0m" if IS_TTY else t

def _print(msg: str):
    if HAS_RICH and console:
        console.print(msg)
    else:
        print(msg)

def _md(text: str):
    if HAS_RICH and console:
        console.print(Markdown(text))
    else:
        print(text)

def _panel(content: str, title: str = "Devin", style: str = "cyan"):
    if HAS_RICH and console:
        console.print(Panel(Markdown(content), title=f"[bold {style}]{title}[/]",
                            border_style=style, padding=(0, 1)))
    else:
        print(f"\n── {title} ──\n{content}\n")

def _tool_start(name: str, args: Dict):
    arg_str = ", ".join(f"{k}={repr(v)[:40]}" for k, v in args.items())
    if HAS_RICH and console:
        console.print(f"  [bold cyan]●[/] [cyan]{name}[/]([dim]{arg_str}[/])")
    else:
        print(f"  ● {name}({arg_str})")

def _tool_result(result: str, ok: bool = True):
    color = "green" if ok else "red"
    prefix = "↳" if ok else "✗"
    short = result[:200].replace("\n", " ")
    if HAS_RICH and console:
        console.print(f"    [{color}]{prefix}[/] [dim]{short}[/]")
    else:
        print(f"    {prefix} {short}")

def _user_prompt() -> str:
    ts = datetime.now().strftime("%H:%M")
    if HAS_RICH and console:
        console.print(f"\n[dim]{ts}[/] [bold green]You[/] ", end="")
    else:
        print(f"\n{ts} You ", end="", flush=True)
    try:
        return input().strip()
    except (EOFError, KeyboardInterrupt):
        return "/exit"

# ── Banner ────────────────────────────────────────────────────────────────────
def print_banner():
    w = shutil.get_terminal_size((80, 24)).columns
    if HAS_RICH and console:
        console.print(Rule(style="cyan"))
        console.print(f"[bold cyan]  Devin AGI[/] [dim]v4.0.0  ·  24 repos integrated  ·  {platform.system()}[/]")
        model_s = _ACTIVE_MODEL or (_GEMINI_MODELS[0] if HAS_GEMINI else ("claude" if HAS_ANTHROPIC else ("huggingface" if HAS_HF else "no AI")))
        console.print(f"[dim]  model: {model_s}  ·  tools: {len(TOOL_REGISTRY)}  ·  voice: {'on' if VOICE_MODE else 'off'}[/]")
        console.print(Rule(style="cyan"))
        console.print()
    else:
        line = "─" * (w - 2)
        print(f"\n╭{line}╮")
        print(f"│  Devin AGI v4.0.0  ·  24 repos integrated  ·  {platform.system()}")
        print(f"╰{line}╯\n")

# ── Spinner (fallback when Rich Live not available) ───────────────────────────
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
            sys.stdout.write(f"\r\x1b[96m{f} {self.label}\x1b[0m")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1

    def stop(self):
        self._stop.set()
        if self._t: self._t.join(0.3)
        if IS_TTY: sys.stdout.write("\r\x1b[2K")

# ── Tool definitions for Gemini function calling ──────────────────────────────
TOOL_SCHEMAS = [
    {"name": "take_screenshot", "description": "Take a screenshot of the current screen. Always do this before clicking to see what's on screen.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "mouse_click", "description": "Click mouse at pixel coordinates.",
     "parameters": {"type": "object", "properties": {
         "x": {"type": "integer"}, "y": {"type": "integer"},
         "button": {"type": "string", "enum": ["left", "right", "middle"]}
     }, "required": ["x", "y"]}},
    {"name": "mouse_right_click", "description": "Right-click at pixel coordinates.",
     "parameters": {"type": "object", "properties": {
         "x": {"type": "integer"}, "y": {"type": "integer"}
     }, "required": ["x", "y"]}},
    {"name": "mouse_double_click", "description": "Double-click at pixel coordinates.",
     "parameters": {"type": "object", "properties": {
         "x": {"type": "integer"}, "y": {"type": "integer"}
     }, "required": ["x", "y"]}},
    {"name": "mouse_move", "description": "Move mouse cursor to coordinates.",
     "parameters": {"type": "object", "properties": {
         "x": {"type": "integer"}, "y": {"type": "integer"}
     }, "required": ["x", "y"]}},
    {"name": "mouse_drag", "description": "Click and drag from one point to another.",
     "parameters": {"type": "object", "properties": {
         "x1": {"type": "integer"}, "y1": {"type": "integer"},
         "x2": {"type": "integer"}, "y2": {"type": "integer"}
     }, "required": ["x1", "y1", "x2", "y2"]}},
    {"name": "mouse_scroll", "description": "Scroll at a position.",
     "parameters": {"type": "object", "properties": {
         "x": {"type": "integer"}, "y": {"type": "integer"},
         "direction": {"type": "string", "enum": ["up", "down"]},
         "amount": {"type": "integer"}
     }, "required": ["x", "y"]}},
    {"name": "keyboard_type", "description": "Type text using the keyboard.",
     "parameters": {"type": "object", "properties": {
         "text": {"type": "string"}
     }, "required": ["text"]}},
    {"name": "keyboard_press", "description": "Press a single key (Return, Tab, Escape, F5, BackSpace, Delete, etc).",
     "parameters": {"type": "object", "properties": {
         "key": {"type": "string"}
     }, "required": ["key"]}},
    {"name": "keyboard_hotkey", "description": "Press key combination like Ctrl+C, Alt+Tab, Super+D.",
     "parameters": {"type": "object", "properties": {
         "keys": {"type": "array", "items": {"type": "string"}}
     }, "required": ["keys"]}},
    {"name": "open_application", "description": "Open/launch an application by name.",
     "parameters": {"type": "object", "properties": {
         "name": {"type": "string"}
     }, "required": ["name"]}},
    {"name": "focus_window", "description": "Bring a window with matching title to front.",
     "parameters": {"type": "object", "properties": {
         "title": {"type": "string"}
     }, "required": ["title"]}},
    {"name": "list_windows", "description": "List all open window titles.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "execute_shell", "description": "Execute a shell command and return output.",
     "parameters": {"type": "object", "properties": {
         "command": {"type": "string"},
         "timeout": {"type": "integer"}
     }, "required": ["command"]}},
    {"name": "execute_python", "description": "Execute Python code and return output.",
     "parameters": {"type": "object", "properties": {
         "code": {"type": "string"}
     }, "required": ["code"]}},
    {"name": "read_file", "description": "Read a file and return its contents.",
     "parameters": {"type": "object", "properties": {
         "path": {"type": "string"}
     }, "required": ["path"]}},
    {"name": "write_file", "description": "Write content to a file.",
     "parameters": {"type": "object", "properties": {
         "path": {"type": "string"}, "content": {"type": "string"}
     }, "required": ["path", "content"]}},
    {"name": "list_files", "description": "List files in a directory.",
     "parameters": {"type": "object", "properties": {
         "directory": {"type": "string"}, "pattern": {"type": "string"}
     }, "required": []}},
    {"name": "web_search", "description": "Search the web for information.",
     "parameters": {"type": "object", "properties": {
         "query": {"type": "string"}, "num_results": {"type": "integer"}
     }, "required": ["query"]}},
    {"name": "web_fetch", "description": "Fetch and return the text content of a URL.",
     "parameters": {"type": "object", "properties": {
         "url": {"type": "string"}
     }, "required": ["url"]}},
    {"name": "open_browser", "description": "Open a URL in the default browser.",
     "parameters": {"type": "object", "properties": {
         "url": {"type": "string"}
     }, "required": ["url"]}},
    {"name": "clipboard_get", "description": "Get text from the clipboard.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "clipboard_set", "description": "Set clipboard text.",
     "parameters": {"type": "object", "properties": {
         "text": {"type": "string"}
     }, "required": ["text"]}},
    {"name": "get_system_info", "description": "Get system information: CPU, RAM, disk, platform.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "list_processes", "description": "List running processes.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "speak", "description": "Speak text aloud using text-to-speech.",
     "parameters": {"type": "object", "properties": {
         "text": {"type": "string"}
     }, "required": ["text"]}},
    {"name": "listen", "description": "Listen for voice input and return transcribed text.",
     "parameters": {"type": "object", "properties": {
         "timeout": {"type": "integer"}
     }, "required": []}},
    {"name": "remember", "description": "Save a fact to long-term memory.",
     "parameters": {"type": "object", "properties": {
         "fact": {"type": "string"}
     }, "required": ["fact"]}},
    {"name": "recall", "description": "Recall facts from long-term memory.",
     "parameters": {"type": "object", "properties": {
         "query": {"type": "string"}
     }, "required": []}},
    {"name": "git_command", "description": "Run a git command.",
     "parameters": {"type": "object", "properties": {
         "args": {"type": "string"}, "cwd": {"type": "string"}
     }, "required": ["args"]}},
    {"name": "run_nmap_scan", "description": "Run an nmap network scan (authorized use only).",
     "parameters": {"type": "object", "properties": {
         "target": {"type": "string"}, "args": {"type": "string"}
     }, "required": ["target"]}},
    {"name": "get_screen_size", "description": "Get the screen width and height in pixels.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "get_mouse_position", "description": "Get the current mouse cursor (x, y) position.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "search_screen", "description": "Find a template image on screen and return the center (x, y). Requires the template file path.",
     "parameters": {"type": "object", "properties": {
         "image_template": {"type": "string"}
     }, "required": ["image_template"]}},

    # ── Code / repo exploration ─────────────────────────────────────────────
    {"name": "find_files", "description": "Find files under a directory matching a glob pattern (e.g. '*.py', '**/*.md').",
     "parameters": {"type": "object", "properties": {
         "directory": {"type": "string"},
         "pattern": {"type": "string"},
         "max_results": {"type": "integer"}
     }, "required": []}},
    {"name": "grep_files", "description": "Recursively grep for a text pattern in files matching a glob. Returns matches with surrounding context.",
     "parameters": {"type": "object", "properties": {
         "directory": {"type": "string"},
         "pattern": {"type": "string"},
         "file_pattern": {"type": "string"}
     }, "required": ["pattern"]}},
    {"name": "code_analyze", "description": "Analyze a code file and return metrics (lines, functions, classes, imports).",
     "parameters": {"type": "object", "properties": {
         "file_path": {"type": "string"}
     }, "required": ["file_path"]}},

    # ── Git ─────────────────────────────────────────────────────────────────
    {"name": "git_status", "description": "Show git status of a repository (working-tree changes and staged changes).",
     "parameters": {"type": "object", "properties": {
         "repo_path": {"type": "string"}
     }, "required": []}},
    {"name": "git_log", "description": "Show recent git commits from a repository.",
     "parameters": {"type": "object", "properties": {
         "repo_path": {"type": "string"},
         "max_commits": {"type": "integer"}
     }, "required": []}},
    {"name": "git_diff", "description": "Show git diff for a repository, or for one file if file_path is set.",
     "parameters": {"type": "object", "properties": {
         "repo_path": {"type": "string"},
         "file_path": {"type": "string"}
     }, "required": []}},

    # ── Vision / text analysis ──────────────────────────────────────────────
    {"name": "analyze_image", "description": "Ask a vision model about an image file. Useful after take_screenshot to inspect what's on screen.",
     "parameters": {"type": "object", "properties": {
         "image_path": {"type": "string"},
         "question": {"type": "string"}
     }, "required": ["image_path"]}},
    {"name": "analyze_text", "description": "Analyze a block of text (summary stats, word count, top words).",
     "parameters": {"type": "object", "properties": {
         "text": {"type": "string"},
         "analysis_type": {"type": "string"}
     }, "required": ["text"]}},
    {"name": "extract_urls", "description": "Extract every URL from a block of text.",
     "parameters": {"type": "object", "properties": {
         "text": {"type": "string"}
     }, "required": ["text"]}},
    {"name": "extract_emails", "description": "Extract every email address from a block of text.",
     "parameters": {"type": "object", "properties": {
         "text": {"type": "string"}
     }, "required": ["text"]}},
    {"name": "hash_text", "description": "Compute md5/sha1/sha256 of a text string.",
     "parameters": {"type": "object", "properties": {
         "text": {"type": "string"},
         "algorithm": {"type": "string", "enum": ["md5", "sha1", "sha256"]}
     }, "required": ["text"]}},

    # ── Network / OSINT (authorized use) ────────────────────────────────────
    {"name": "port_scan", "description": "Scan a small set of common ports on a host (authorized targets only).",
     "parameters": {"type": "object", "properties": {
         "host": {"type": "string"},
         "ports": {"type": "string"}
     }, "required": ["host"]}},
    {"name": "dns_lookup", "description": "Resolve a hostname to its IP addresses.",
     "parameters": {"type": "object", "properties": {
         "hostname": {"type": "string"}
     }, "required": ["hostname"]}},
    {"name": "whois_lookup", "description": "WHOIS lookup for a domain.",
     "parameters": {"type": "object", "properties": {
         "domain": {"type": "string"}
     }, "required": ["domain"]}},
    {"name": "check_ssl_cert", "description": "Fetch and describe the TLS certificate a domain is serving.",
     "parameters": {"type": "object", "properties": {
         "domain": {"type": "string"}
     }, "required": ["domain"]}},
    {"name": "web_research", "description": "Search the web for a topic and fetch summaries of the top hits.",
     "parameters": {"type": "object", "properties": {
         "topic": {"type": "string"},
         "num_results": {"type": "integer"}
     }, "required": ["topic"]}},

    # ── Data / files ────────────────────────────────────────────────────────
    {"name": "read_pdf", "description": "Extract text from a PDF file. page_range e.g. '1-5' or '1'.",
     "parameters": {"type": "object", "properties": {
         "file_path": {"type": "string"},
         "page_range": {"type": "string"}
     }, "required": ["file_path"]}},
    {"name": "read_excel", "description": "Read tabular data from an .xlsx/.xls file.",
     "parameters": {"type": "object", "properties": {
         "file_path": {"type": "string"},
         "sheet": {"type": "string"},
         "max_rows": {"type": "integer"}
     }, "required": ["file_path"]}},
    {"name": "parse_csv", "description": "Parse a CSV file and return a formatted preview.",
     "parameters": {"type": "object", "properties": {
         "file_path": {"type": "string"},
         "max_rows": {"type": "integer"}
     }, "required": ["file_path"]}},
    {"name": "extract_metadata", "description": "Extract filesystem + content metadata from a file (size, mtime, mime, hash).",
     "parameters": {"type": "object", "properties": {
         "file_path": {"type": "string"}
     }, "required": ["file_path"]}},

    # ── Planning / long-term memory ─────────────────────────────────────────
    {"name": "task_decompose", "description": "Break a complex user task into an ordered list of concrete sub-tasks.",
     "parameters": {"type": "object", "properties": {
         "task_description": {"type": "string"}
     }, "required": ["task_description"]}},
    {"name": "memory_save_persistent", "description": "Save a fact to Devin's persistent memory (survives restart). Categorize with the category arg.",
     "parameters": {"type": "object", "properties": {
         "key": {"type": "string"},
         "value": {"type": "string"},
         "category": {"type": "string"}
     }, "required": ["key", "value"]}},
    {"name": "memory_recall_persistent", "description": "Recall one fact by key from persistent memory. Returns null if not found.",
     "parameters": {"type": "object", "properties": {
         "key": {"type": "string"}
     }, "required": ["key"]}},
    {"name": "memory_search", "description": "Search persistent memory by substring / keyword. Optionally scoped by category.",
     "parameters": {"type": "object", "properties": {
         "query": {"type": "string"},
         "category": {"type": "string"},
         "limit": {"type": "integer"}
     }, "required": ["query"]}},
    {"name": "memory_list_persistent", "description": "List facts stored in persistent memory (optionally scoped by category).",
     "parameters": {"type": "object", "properties": {
         "category": {"type": "string"},
         "limit": {"type": "integer"}
     }, "required": []}},
    {"name": "memory_stats", "description": "Get persistent-memory statistics (count, categories, last write).",
     "parameters": {"type": "object", "properties": {}, "required": []}},

    # ── System / diagnostics ────────────────────────────────────────────────
    {"name": "device_info", "description": "Detailed device/system report: platform, release, arch, CPU count, RAM, disk, GPU when available.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "internet_speed_test", "description": "Quick connectivity/latency check to a well-known endpoint. Not a bandwidth benchmark.",
     "parameters": {"type": "object", "properties": {}, "required": []}},

    {"name": "task_complete", "description": "Call when the task is fully completed.",
     "parameters": {"type": "object", "properties": {
         "reason": {"type": "string"}
     }, "required": ["reason"]}},
]

# local additions to TOOL_REGISTRY
TOOL_REGISTRY["remember"]       = remember
TOOL_REGISTRY["recall"]         = recall
TOOL_REGISTRY["task_complete"]  = lambda reason="": f"Task complete: {reason}"

# ── Dispatch tool call ────────────────────────────────────────────────────────
def dispatch_tool(name: str, args: Dict) -> str:
    """Execute a tool from TOOL_REGISTRY and return string result."""
    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        return f"Unknown tool: {name}"
    try:
        # Special handling for keyboard_hotkey — args come as list or separate keys
        if name == "keyboard_hotkey":
            keys = args.get("keys", [])
            if isinstance(keys, list):
                result = keyboard_hotkey(*keys)
            else:
                result = keyboard_hotkey(str(keys))
        else:
            result = fn(**{k: v for k, v in args.items()})
        # Convert result to string
        if isinstance(result, dict):
            return json.dumps(result, default=str)
        if isinstance(result, (list, tuple)):
            return json.dumps(result, default=str)
        if isinstance(result, bool):
            return "OK" if result else "Failed"
        if result is None:
            return "OK"
        return str(result)
    except Exception as e:
        return f"Tool error ({name}): {e}"

# ── Screenshot → base64 for Gemini vision ────────────────────────────────────
def screenshot_to_b64() -> Optional[str]:
    path = take_screenshot()
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ── System prompt ─────────────────────────────────────────────────────────────
PLATFORM = platform.system()
DISPLAY_INFO = f" DISPLAY={os.environ.get('DISPLAY', ':0')}." if PLATFORM == "Linux" else ""

SYSTEM_PROMPT = f"""You are Devin, an advanced AI agent and software engineer with REAL control over this computer.
You can do everything a senior engineer, power user, or ethical hacker can do.
You operate the OS like a real human user — moving the mouse, clicking, typing, opening apps.

OS: {PLATFORM}{DISPLAY_INFO}
Screen: {get_screen_size()}
Repos integrated: AIA, self-operating-computer, Jarvis, JARVIS-microsoft, Devin-1/2/3,
  OpenDevin, cheetahclaws, gemini-cli, claude-code, openclaw, vulnerability-analysis,
  Holomat, shannon, PowerTools, Responder, nishang, hexstrike-ai, airgorah, hackability

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW TO THINK AND ACT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before every action, run through this loop:
  OBSERVE   → take_screenshot() / execute_shell() — see current state
  UNDERSTAND → What does what I see tell me?
  PLAN      → What sequence of steps will complete this end-to-end?
  ACT       → Execute the first step with the right tool
  VERIFY    → take_screenshot() / check output — did it work?
  CONTINUE  → next step, adapt if something went wrong
  COMPLETE  → task_complete(reason="...") ONLY when fully verified

## CRITICAL RULES
1. ALWAYS take_screenshot() BEFORE clicking — you need exact pixel coordinates.
2. After every GUI click/action, take_screenshot() to verify it worked.
3. If a click misses, re-analyze the screenshot then retry with corrected coords.
4. NEVER stop halfway. Chain tool calls until the FULL task is done.
5. NEVER fabricate results — only report what tools actually returned.
6. NEVER output "(acting)" as text. Just call tools.
7. If a tool fails, try an alternative — never repeat the same failing call.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Vision: take_screenshot(), analyze_screenshot_gemini(prompt)
Mouse: mouse_click(x,y), mouse_right_click(x,y), mouse_double_click(x,y),
       mouse_move(x,y), mouse_drag(x1,y1,x2,y2), mouse_scroll(x,y,dir,amount)
Keyboard: keyboard_type(text), keyboard_press(key), keyboard_hotkey(keys)
Apps: open_application(name), focus_window(title), list_windows()
Shell: execute_shell(command), execute_python(code)
Files: read_file(path), write_file(path,content), list_files(dir)
Web: web_search(query), web_fetch(url), open_browser(url)
Memory: remember(fact), recall(query)
Voice: speak(text), listen(timeout)
System: get_system_info(), list_processes(), clipboard_get(), clipboard_set(text)
Security: run_nmap_scan(target, args) — authorized use only

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE WORKFLOW: open Firefox and search
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. open_application("firefox")
2. take_screenshot() — confirm Firefox opened
3. analyze_screenshot_gemini("Where is the address bar? Give exact pixel coords.")
4. mouse_click(x, y) — click address bar at those coords
5. keyboard_hotkey(["ctrl","a"]) — select all
6. keyboard_type("https://www.google.com/search?q=python+tutorials")
7. keyboard_press("Return")
8. take_screenshot() — verify search results loaded
9. task_complete(reason="Opened Firefox and searched for python tutorials")
SHORTCUT: open_browser("https://www.google.com/search?q=python+tutorials")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONVERSATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For pure questions: answer directly with your knowledge — no tools needed.
For action tasks: use tools and complete the task — do not just describe what you would do.
Be direct, accurate, and honest. Show reasoning when it helps.
Personality: intelligent, direct, capable, relentless. No filler. No hedging. Do the task.
"""

# ── Gemini REST API helpers ───────────────────────────────────────────────────
_ACTIVE_MODEL = None

def _build_tool_declarations() -> List[Dict]:
    """Convert TOOL_SCHEMAS to Gemini REST functionDeclarations format."""
    decls = []
    TYPE_MAP = {"integer": "INTEGER", "string": "STRING", "boolean": "BOOLEAN",
                "array": "ARRAY", "object": "OBJECT", "number": "NUMBER"}
    for t in TOOL_SCHEMAS:
        params = t.get("parameters", {})
        props = {}
        for k, v in params.get("properties", {}).items():
            prop: Dict = {"type": TYPE_MAP.get(v.get("type", "string"), "STRING")}
            if v.get("description"):
                prop["description"] = v["description"]
            if v.get("enum"):
                prop["enum"] = v["enum"]
            if v.get("items"):
                prop["items"] = {"type": TYPE_MAP.get(v["items"].get("type", "string"), "STRING")}
            props[k] = prop
        decl: Dict = {"name": t["name"], "description": t["description"]}
        if props:
            decl["parameters"] = {
                "type": "OBJECT",
                "properties": props,
                "required": params.get("required", []),
            }
        else:
            decl["parameters"] = {"type": "OBJECT", "properties": {}}
        decls.append(decl)
    return decls

def _gemini_contents_to_hf_messages(contents: List[Dict]) -> List[Dict[str, str]]:
    """Flatten Gemini's role/parts contents into OpenAI-style role/content messages.

    Preserves prior `functionCall` parts as <tool_use>{...}</tool_use> blocks so the
    HF model sees its own past tool calls in the same format it must emit them in.
    """
    out: List[Dict[str, str]] = []
    for c in contents:
        role = c.get("role", "user")
        parts = c.get("parts", []) or []
        chunks: List[str] = []
        for p in parts:
            if not isinstance(p, dict):
                continue
            if "text" in p and p["text"]:
                chunks.append(str(p["text"]))
            elif "functionCall" in p:
                fc = p["functionCall"] or {}
                name = fc.get("name", "")
                args = fc.get("args", {}) or {}
                chunks.append(f"<tool_use>{json.dumps({'name': name, 'input': args})}</tool_use>")
            elif "functionResponse" in p:
                fr = p["functionResponse"] or {}
                out_field = (fr.get("response") or {}).get("output", "")
                # Truncate huge tool outputs so we stay under HF context limits.
                out_str = str(out_field)
                if len(out_str) > 4000:
                    out_str = out_str[:4000] + f" …[truncated {len(out_str) - 4000} chars]"
                chunks.append(f"[tool_result {fr.get('name','')}] {out_str}")
            elif "inlineData" in p:
                chunks.append("[image omitted from HF fallback — this provider is text-only]")
        content = "\n".join(chunks).strip()
        if not content:
            # Never emit an empty message — collapse into a placeholder so the
            # alternation stays sane on the receiving side.
            content = " "
        out.append({"role": "assistant" if role == "model" else "user", "content": content})
    return out


def _hf_response_to_gemini_shape(hf_result: Dict) -> Dict:
    """Convert HF chat output back into the Gemini candidates/parts shape
    the agentic loop already knows how to parse."""
    parts: List[Dict] = []
    text = hf_result.get("text", "")
    if text:
        parts.append({"text": text})
    for call in hf_result.get("tool_calls", []) or []:
        parts.append({"functionCall": {"name": call.get("name", ""), "args": call.get("input") or {}}})
    if not parts:
        parts.append({"text": " "})
    return {"candidates": [{"content": {"role": "model", "parts": parts}, "finishReason": "STOP"}]}


def _call_gemini_rest(contents: List[Dict]) -> Optional[Dict]:
    """Call Gemini REST API directly. Returns parsed JSON response or None.
    Raises RuntimeError on rate limit so caller can show clear message.
    Falls through to Hugging Face if Gemini is exhausted or unconfigured."""
    global _ACTIVE_MODEL
    # If Gemini isn't available at all, try Hugging Face directly.
    if not HAS_GEMINI or not _HAS_REQUESTS or not GEMINI_API_KEY:
        if HAS_HF and _hf_chat is not None:
            try:
                hf_result = _hf_chat(
                    messages=_gemini_contents_to_hf_messages(contents),
                    tool_schemas=TOOL_SCHEMAS,
                    system_prompt=SYSTEM_PROMPT,
                )
                _ACTIVE_MODEL = f"hf:{hf_result.get('model', '?')}"
                return _hf_response_to_gemini_shape(hf_result)
            except Exception as _e:
                if os.getenv("DEVIN_DEBUG"):
                    import traceback; traceback.print_exc()
        return None

    body: Dict = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "tools": [{"functionDeclarations": _build_tool_declarations()}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.3},
    }
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY,
        "x-goog-api-client": "google-genai-sdk/2.19.0 gl-python/3.13.12",
    }
    models = ([_ACTIVE_MODEL] + [m for m in _GEMINI_MODELS if m != _ACTIVE_MODEL]) if _ACTIVE_MODEL else _GEMINI_MODELS
    last_err = ""
    for model in models:
        url = f"{_GEMINI_REST_BASE}/{model}:generateContent"
        try:
            r = _requests.post(url, headers=headers, json=body, timeout=60)
        except Exception as e:
            last_err = str(e)
            continue
        if r.status_code == 429:
            last_err = f"429 rate limit on {model}"
            _ACTIVE_MODEL = None  # reset so next call tries fresh
            continue  # try next model — each model has its own free-tier quota
        if r.status_code in (404, 400):
            last_err = f"{r.status_code}: {r.text[:200]}"
            continue  # model not available, try next
        if r.status_code != 200:
            last_err = f"{r.status_code}: {r.text[:200]}"
            continue
        _ACTIVE_MODEL = model
        return r.json()
    # All Gemini models exhausted — try Hugging Face fallback before giving up.
    if HAS_HF and _hf_chat is not None:
        try:
            hf_result = _hf_chat(
                messages=_gemini_contents_to_hf_messages(contents),
                tool_schemas=TOOL_SCHEMAS,
                system_prompt=SYSTEM_PROMPT,
            )
            _ACTIVE_MODEL = f"hf:{hf_result.get('model', '?')}"
            return _hf_response_to_gemini_shape(hf_result)
        except Exception as _e:
            if os.getenv("DEVIN_DEBUG"):
                import traceback; traceback.print_exc()
    if "rate limit" in last_err or "429" in last_err:
        raise RuntimeError("All Gemini models rate-limited (free tier: 20 req/day each). Wait ~60s, set HF_TOKEN for HF fallback, or use a paid API key.")
    return None

# ── Permission gate (used by /default mode) ──────────────────────────────────
# Tools that can mutate the host, exfiltrate data, or hit remote services.
# Anything not in this set is auto-approved even in /default mode.
_DANGEROUS_TOOLS = {
    "execute_shell", "execute_python", "advanced_shell_exec",
    "mouse_click", "mouse_right_click", "mouse_double_click", "mouse_drag", "mouse_scroll",
    "keyboard_type", "keyboard_press", "keyboard_hotkey",
    "open_application", "focus_window",
    "write_file",
    "git_command",
    "run_nmap_scan", "port_scan", "check_ssl_cert",
    "send_telegram_message",
    "clipboard_set",
    "open_browser",
}


def _is_dangerous(tool_name: str) -> bool:
    return tool_name in _DANGEROUS_TOOLS


def _confirm_dangerous(tool_name: str, args: Dict) -> bool:
    """Prompt the user to approve a dangerous tool call. Only reached in
    /default mode + interactive TTY. Returns True on 'y', False otherwise."""
    prompt = f"⚠  Approve dangerous tool `{tool_name}` with {args!r}?  [y/N] "
    if HAS_RICH and console:
        console.print(f"[bold yellow]{prompt}[/]", end="")
    else:
        print(prompt, end="", flush=True)
    try:
        answer = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in ("y", "yes")


def _run_agentic_loop(user_input: str, history: List[Dict], image_b64: Optional[str] = None) -> str:
    """Run the Gemini agentic loop for one user turn. Returns final text response."""
    # Build Gemini-format contents from prior history
    contents: List[Dict] = []
    for m in history:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "system":
            continue
        elif role in ("user",):
            if isinstance(content, list):
                parts: List[Dict] = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            parts.append({"text": part["text"]})
                        elif part.get("type") == "image":
                            b64 = part.get("source", {}).get("data", "")
                            if b64:
                                parts.append({"inlineData": {"mimeType": "image/png", "data": b64}})
                contents.append({"role": "user", "parts": parts or [{"text": " "}]})
            else:
                contents.append({"role": "user", "parts": [{"text": str(content) or " "}]})
        elif role in ("assistant", "model"):
            if content:
                contents.append({"role": "model", "parts": [{"text": str(content)}]})
        elif role == "tool":
            tool_name = m.get("name", "tool_result")
            contents.append({"role": "user", "parts": [{"functionResponse": {
                "name": tool_name, "response": {"output": str(content)},
            }}]})

    # Fix alternation — Gemini requires strict user/model alternation
    def _fix_alternation(raw: List[Dict]) -> List[Dict]:
        fixed: List[Dict] = []
        for msg in raw:
            prev = fixed[-1] if fixed else None
            if prev and prev["role"] == msg["role"]:
                if msg["role"] == "user":
                    fixed.append({"role": "model", "parts": [{"text": " "}]})
                else:
                    prev["parts"].extend(msg["parts"])
                    continue
            fixed.append(msg)
        if fixed and fixed[0]["role"] == "model":
            fixed.insert(0, {"role": "user", "parts": [{"text": " "}]})
        return fixed

    contents = _fix_alternation(contents)

    # Add current user message
    if image_b64:
        contents.append({"role": "user", "parts": [
            {"inlineData": {"mimeType": "image/png", "data": image_b64}},
            {"text": user_input},
        ]})
    else:
        contents.append({"role": "user", "parts": [{"text": user_input}]})

    final_text = ""
    max_rounds = 30

    for _round in range(max_rounds):
        # Show thinking spinner
        try:
            if HAS_RICH and console:
                with Live(RichSpinner("dots", text="[cyan]Devin is thinking…[/]"), refresh_per_second=10, transient=True):
                    data = _call_gemini_rest(contents)
            else:
                spin = Spinner()
                spin.start()
                data = _call_gemini_rest(contents)
                spin.stop()
        except RuntimeError as e:
            # Rate limit — show clear message and stop
            if HAS_RICH and console:
                console.print(f"\n[bold red]✗ {e}[/]")
            else:
                print(f"\n✗ {e}")
            break

        if data is None:
            if not HAS_GEMINI and not HAS_HF:
                return "[No AI available — set GEMINI_API_KEY or HF_TOKEN in .env]"
            return "[No AI response — check API key and model availability]"

        # Parse response parts
        text_parts: List[str] = []
        tool_calls: List[Dict] = []
        raw_model_parts: List[Dict] = []

        candidates = data.get("candidates", [])
        candidate = candidates[0] if candidates else {}
        parts_list = candidate.get("content", {}).get("parts", [])

        for part in parts_list:
            raw_model_parts.append(part)
            if "text" in part and part["text"]:
                text_parts.append(part["text"])
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append({
                    "name": fc.get("name", ""),
                    "args": fc.get("args", {}) if isinstance(fc.get("args"), dict) else {},
                })

        text = "\n".join(text_parts).strip()

        # Display text output
        if text:
            if HAS_RICH and console:
                ts = datetime.now().strftime("%H:%M")
                console.print(f"\n[dim]{ts}[/] [bold cyan]Devin[/]")
                console.print(Markdown(text))
            else:
                print(f"\nDevin: {text}")
            final_text = text

        if not tool_calls:
            # If the model responded with text but no tool call AND the text
            # looks like a "here is my plan" (numbered list, "I will…"),
            # nudge it once to actually act instead of dropping the turn.
            # This matters for open-weight models like Qwen that sometimes
            # slip into chat mode when they should be using tools.
            plan_shape = re.search(r"(^|\n)\s*(1[.)]|- |First,|Step 1|Here is the plan|I (will|would|plan to)\b)",
                                    text, flags=re.IGNORECASE)
            already_nudged = any(
                isinstance(p, dict) and p.get("text", "").startswith("[[SYSTEM NUDGE]]")
                for c in contents for p in (c.get("parts") or [])
            )
            if plan_shape and not already_nudged and _round < max_rounds - 1:
                # Append the model's turn, then a synthetic user turn nudging
                # for real action. One nudge per conversation so we don't loop.
                contents.append({
                    "role": "model",
                    "parts": raw_model_parts if raw_model_parts else [{"text": text or " "}],
                })
                nudge = (
                    "[[SYSTEM NUDGE]] You described a plan but did not call any "
                    "tool. Call one of the available tools now to make progress. "
                    "If the task is already complete, call task_complete. Do not "
                    "describe — act."
                )
                contents.append({"role": "user", "parts": [{"text": nudge}]})
                continue
            break  # no more tool calls — done

        # Append model turn (with function calls) to contents
        contents.append({
            "role": "model",
            "parts": raw_model_parts if raw_model_parts else [{"text": text or " "}],
        })

        # Execute each tool call and collect functionResponse parts
        fn_response_parts: List[Dict] = []

        for tc in tool_calls:
            t_name = tc["name"]
            t_args = tc["args"]
            _tool_start(t_name, t_args)

            if t_name == "task_complete":
                reason = t_args.get("reason", "")
                _tool_result(f"✓ {reason}", ok=True)
                fn_response_parts.append({"functionResponse": {
                    "name": t_name, "response": {"output": f"Task complete: {reason}"},
                }})
                contents.append({"role": "user", "parts": fn_response_parts})
                return final_text or reason

            if PERMISSION_MODE == "plan":
                # Describe the call in the response stream, feed a synthetic
                # result back so the model can keep planning without side
                # effects. This lets `/plan` produce a full walkthrough.
                planned = f"[PLANNED — not executed under /plan mode] {t_name}({t_args})"
                _tool_result(planned, ok=True)
                fn_response_parts.append({"functionResponse": {
                    "name": t_name, "response": {"output": planned},
                }})
                continue

            if PERMISSION_MODE == "default" and _is_dangerous(t_name):
                if IS_TTY:
                    if not _confirm_dangerous(t_name, t_args):
                        denied = f"[DENIED by user in /default mode] {t_name}({t_args})"
                        _tool_result(denied, ok=False)
                        fn_response_parts.append({"functionResponse": {
                            "name": t_name, "response": {"output": denied},
                        }})
                        continue
                else:
                    # Non-interactive one-shot: refuse and let the model adapt
                    # instead of silently running a dangerous call.
                    denied = (
                        f"[BLOCKED — {t_name} is a dangerous tool and Devin is running "
                        f"non-interactively under /default mode. Rerun with --auto (or "
                        f"DEVIN_PERMISSION_MODE=auto) if you intended to authorize this.]"
                    )
                    _tool_result(denied, ok=False)
                    fn_response_parts.append({"functionResponse": {
                        "name": t_name, "response": {"output": denied},
                    }})
                    continue

            result = dispatch_tool(t_name, t_args)
            _tool_result(result[:200])

            if t_name == "take_screenshot" and os.path.exists(result):
                try:
                    with open(result, "rb") as f:
                        scr_b64 = base64.b64encode(f.read()).decode()
                    fn_response_parts.append({"functionResponse": {
                        "name": t_name, "response": {"output": f"Screenshot taken: {result}"},
                    }})
                    fn_response_parts.append({"inlineData": {"mimeType": "image/png", "data": scr_b64}})
                except Exception:
                    fn_response_parts.append({"functionResponse": {
                        "name": t_name, "response": {"output": result},
                    }})
            else:
                fn_response_parts.append({"functionResponse": {
                    "name": t_name, "response": {"output": result},
                }})

        # All tool results as one user turn
        contents.append({"role": "user", "parts": fn_response_parts})

    return final_text or "(No response)"

# ── Slash commands ─────────────────────────────────────────────────────────────
def handle_slash(cmd: str, history: List[Dict]) -> Optional[str]:
    """Handle slash commands. Returns message to display or None."""
    parts = cmd.split(None, 1)
    command = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if command in ("/exit", "/quit", "/q"):
        raise SystemExit(0)

    if command == "/help":
        return (
            "**Devin AGI 4.0 Commands**\n\n"
            "| Command | Action |\n"
            "|---------|--------|\n"
            "| `/help` | Show this help |\n"
            "| `/clear` | Clear conversation history |\n"
            "| `/status` | Show capabilities and active modules |\n"
            "| `/tools` | List all available tools |\n"
            "| `/repos` | List all integrated repositories |\n"
            "| `/voice` | Toggle voice mode (TTS/STT) |\n"
            "| `/screenshot` | Take and display a screenshot |\n"
            "| `/memory` | Show long-term memories |\n"
            "| `/remember <fact>` | Store a fact in memory |\n"
            "| `/shell <cmd>` | Run a shell command |\n"
            "| `/model` | Show current AI model |\n"
            "| `/plan` | Plan mode (describe actions, don't run them) |\n"
            "| `/auto` | Auto-approve all tool calls |\n"
            "| `/default` | Default mode (confirm dangerous actions) |\n"
            "| `/verbose` | Toggle verbose debug output |\n"
            "| `/exit` | Quit Devin |"
        )

    if command == "/clear":
        history.clear()
        return "**Conversation cleared.**"

    if command == "/status":
        info = get_system_info()
        caps = capabilities_summary()
        model_s = _ACTIVE_MODEL or "detecting…"
        return (
            f"**System Status**\n\n"
            f"- Platform: {info.get('platform', PLATFORM)}\n"
            f"- CPU: {info.get('cpu_percent', '?')}%  RAM: {info.get('ram_used_gb', '?')}/{info.get('ram_total_gb', '?')} GB\n"
            f"- Active model: {model_s}\n"
            f"- Gemini: {'✓' if HAS_GEMINI else '✗'}  Anthropic: {'✓' if HAS_ANTHROPIC else '✗'}  HuggingFace: {'✓' if HAS_HF else '✗'}\n\n"
            f"**Capabilities**\n```\n{caps}\n```"
        )

    if command == "/tools":
        names = sorted(TOOL_REGISTRY.keys())
        return "**Available Tools** (" + str(len(names)) + ")\n\n" + "\n".join(f"- `{n}`" for n in names)

    if command == "/repos":
        repos_dir = _ROOT / "repos"
        if repos_dir.exists():
            dirs = [d.name for d in sorted(repos_dir.iterdir()) if d.is_dir()]
        else:
            dirs = []
        return (
            "**Integrated Repositories** (" + str(len(dirs)) + ")\n\n" +
            "\n".join(f"- `{d}`" for d in dirs)
        )

    if command == "/voice":
        global VOICE_MODE
        VOICE_MODE = not VOICE_MODE
        return f"**Voice mode:** {'ON' if VOICE_MODE else 'OFF'}"

    if command == "/screenshot":
        path = take_screenshot()
        if path and os.path.exists(path):
            return f"**Screenshot saved:** `{path}`"
        return "**Screenshot failed.**"

    if command == "/memory":
        return "**Memories:**\n\n" + recall()

    if command == "/remember":
        if arg:
            return remember(arg)
        return "Usage: `/remember <fact>`"

    if command == "/shell":
        if arg:
            r = execute_shell(arg)
            out = r.get("output", "").strip()
            return f"```\n{out[:3000]}\n```"
        return "Usage: `/shell <command>`"

    if command == "/model":
        return f"**Active model:** {_ACTIVE_MODEL or 'not detected yet'}"

    if command == "/plan":
        global PERMISSION_MODE
        PERMISSION_MODE = "plan"
        return "**Plan mode:** ON — Devin will describe planned tool calls but not execute them."

    if command == "/auto":
        PERMISSION_MODE = "auto"
        return "**Auto mode:** ON — Devin will run tool calls without confirming."

    if command == "/default":
        PERMISSION_MODE = "default"
        return "**Default mode:** ON — Devin will prompt before dangerous tool calls."

    if command == "/verbose":
        global VERBOSE
        VERBOSE = not VERBOSE
        os.environ["DEVIN_DEBUG"] = "1" if VERBOSE else ""
        return f"**Verbose mode:** {'ON' if VERBOSE else 'OFF'}"

    return None  # not a known slash command

# ── Main entry point ──────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Devin AGI 4.0")
    parser.add_argument("--voice", action="store_true", help="Start in voice mode")
    parser.add_argument("--test",  action="store_true", help="Run smoke test and exit")
    parser.add_argument("prompt",  nargs="?", help="One-shot prompt (non-interactive)")
    args = parser.parse_args()

    global VOICE_MODE
    if args.voice:
        VOICE_MODE = True

    if args.test:
        _print("[Test mode]")
        _print(f"  HAS_GEMINI: {HAS_GEMINI}")
        _print(f"  HAS_ANTHROPIC: {HAS_ANTHROPIC}")
        _print(f"  HAS_HF (Hugging Face): {HAS_HF}")
        _print(f"  HAS_RICH: {HAS_RICH}")
        _print(f"  PERMISSION_MODE: {PERMISSION_MODE}")
        _print(f"  VERBOSE: {VERBOSE}")
        _print(f"  TOOL_SCHEMAS exposed: {len(TOOL_SCHEMAS)}")
        _print(f"  pyautogui: {HAS.get('pyautogui')}")
        _print(f"  mss: {HAS.get('mss')}")
        _print(f"  TTS: {HAS.get('tts')}")
        _print(f"  STT: {HAS.get('stt')}")
        _print(f"  AIA: {HAS.get('aia_automation')}")
        _print(f"  SOC: {HAS.get('soc')}")
        _print(f"  Tools: {len(TOOL_REGISTRY)}")
        scr = take_screenshot()
        _print(f"  Screenshot: {scr}")
        sh  = execute_shell("echo hello")
        _print(f"  Shell: {sh['output'].strip()}")
        py  = execute_python("print(1+1)")
        _print(f"  Python: {py['output'].strip()}")
        sys.exit(0)

    # One-shot mode
    if args.prompt:
        history: List[Dict] = []
        response = _run_agentic_loop(args.prompt, history)
        print(response)
        sys.exit(0)

    # Signal handler for Ctrl-C
    def _sigint(sig, frame):
        print("\n[Interrupted — type /exit to quit]")
    signal.signal(signal.SIGINT, _sigint)

    print_banner()
    if HAS_RICH and console:
        console.print("[dim]Type a task, question, or command. /help for commands. /exit to quit.[/]\n")
    else:
        print("Type a task, question, or command. /help for commands. /exit to quit.\n")

    history: List[Dict] = []

    while True:
        try:
            user_input = _user_prompt()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        # Slash commands
        if user_input.startswith("/"):
            try:
                result = handle_slash(user_input[1:] if user_input[1:] else user_input, history)
                if result is not None:
                    _panel(result)
                continue
            except SystemExit:
                break

        # Voice input in voice mode
        if VOICE_MODE and user_input.lower() in ("voice", "listen", "speak"):
            if HAS_RICH and console:
                console.print("[dim]Listening…[/]")
            else:
                print("Listening…")
            user_input = listen(timeout=8)
            if not user_input:
                _print("(Nothing heard)")
                continue
            _print(f"[Voice]: {user_input}")

        # Main AI loop
        try:
            response = _run_agentic_loop(user_input, history)
            # Track conversation for context in future turns
            history.append({"role": "user", "content": user_input})
            if response and response not in ("(No response)", "(No response)"):
                history.append({"role": "assistant", "content": response})
            # Compact history (keep last 40 turns)
            if len(history) > 80:
                summary_turns = history[:40]
                summary = " | ".join(
                    f"{m['role']}: {str(m.get('content',''))[:80]}"
                    for m in summary_turns
                )
                history = [{"role": "system", "content": f"[Earlier context]: {summary}"}] + history[40:]
            # Voice output
            if VOICE_MODE and response:
                speak(response[:300])
        except KeyboardInterrupt:
            _print("\n[Interrupted]")


if __name__ == "__main__":
    main()
