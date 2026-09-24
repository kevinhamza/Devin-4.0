#!/usr/bin/env python3
"""
Devin Agent — Proper agentic AI CLI
=====================================
Self-contained. Zero external dependencies.
Interactive REPL + one-shot task mode.
Supports Gemini, Claude, and OpenAI.

Usage:
  python agent.py                          # interactive mode
  python agent.py "search today's AI news" # one-shot task
  python agent.py --provider claude        # force provider
  python agent.py --model gemini-2.5-pro   # force model

Slash commands (interactive):
  /help    /tools    /status   /model    /providers
  /clear   /memory   /forget   /history  /shell <cmd>
  /exit    /quit

API keys (.env or environment):
  GEMINI_API_KEY     https://aistudio.google.com/app/apikey
  ANTHROPIC_API_KEY  https://console.anthropic.com/
  OPENAI_API_KEY     https://platform.openai.com/api-keys
"""

from __future__ import annotations
import os, sys, json, time, re, subprocess, html as _html_lib, sqlite3, hashlib
import urllib.request, urllib.parse, urllib.error, textwrap, shutil, threading
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ── Load .env ─────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent
_ENV  = _ROOT / '.env'
if _ENV.exists():
    for _l in _ENV.read_text().splitlines():
        _l = _l.strip()
        if _l and not _l.startswith('#') and '=' in _l:
            _k, _v = _l.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"\''))

# ── Terminal colours ──────────────────────────────────────────────────────────
_TTY = sys.stdout.isatty()
def _c(code, t): return f'\033[{code}m{t}\033[0m' if _TTY else t
cyan   = lambda t: _c('36;1', t)
green  = lambda t: _c('32;1', t)
yellow = lambda t: _c('33;1', t)
red    = lambda t: _c('31;1', t)
bold   = lambda t: _c('1',    t)
dim    = lambda t: _c('2',    t)
blue   = lambda t: _c('34;1', t)
magenta= lambda t: _c('35;1', t)
white  = lambda t: _c('37;1', t)

def _hr(char='─', width=0):
    w = width or (shutil.get_terminal_size().columns - 1)
    return dim(char * w)

def _box(title: str, char='─'):
    w = shutil.get_terminal_size().columns - 1
    pad = max(0, w - len(title) - 2)
    return dim(char * 2) + ' ' + bold(title) + ' ' + dim(char * pad)

# ── Memory (SQLite) ───────────────────────────────────────────────────────────
_DB_PATH = _ROOT / '.devin_memory.db'

def _db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fact TEXT NOT NULL,
        tags TEXT DEFAULT '',
        ts TEXT DEFAULT (datetime('now')),
        session TEXT DEFAULT ''
    )''')
    conn.commit()
    return conn

_DB = _db_connect()
_SESSION_ID = datetime.now().strftime('%Y%m%d_%H%M%S')

def _remember(fact: str, tags: str = '') -> str:
    _DB.execute('INSERT INTO memories (fact, tags, session) VALUES (?,?,?)',
                (fact, tags, _SESSION_ID))
    _DB.commit()
    return f"Remembered: {fact[:80]}"

def _recall(query: str = '', n: int = 10) -> str:
    if query:
        rows = _DB.execute(
            "SELECT ts, fact FROM memories WHERE fact LIKE ? ORDER BY id DESC LIMIT ?",
            (f'%{query}%', n)
        ).fetchall()
    else:
        rows = _DB.execute(
            "SELECT ts, fact FROM memories ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
    if not rows:
        return "No memories found."
    return '\n'.join(f"[{r[0]}] {r[1]}" for r in rows)

def _forget_all() -> str:
    _DB.execute('DELETE FROM memories')
    _DB.commit()
    return "All memories cleared."

# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

def _ua_get(url: str, timeout: int = 20, extra_headers: dict = {}) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36',
        'Accept': 'text/html,application/json,*/*;q=0.9',
        **extra_headers,
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            enc = r.headers.get_content_charset('utf-8')
            return raw.decode(enc, errors='replace')
    except urllib.error.HTTPError as e:
        return f"ERROR:{e.code} {e.reason}"
    except Exception as e:
        return f"ERROR:{e}"

def _strip_html(s: str, max_chars: int = 8000) -> str:
    s = re.sub(r'<script[^>]*>.*?</script>', ' ', s, flags=re.S|re.I)
    s = re.sub(r'<style[^>]*>.*?</style>',  ' ', s, flags=re.S|re.I)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = _html_lib.unescape(s)
    s = re.sub(r'\s{3,}', '\n\n', s)
    return s.strip()[:max_chars]

# ── Tool implementations ──────────────────────────────────────────────────────

def tool_think(thought: str) -> str:
    """Record AI reasoning without side effects."""
    return f"[thought recorded] {thought[:200]}"

def tool_web_search(query: str, num_results: int = 8) -> str:
    """Search the web via DuckDuckGo (no key needed)."""
    q = urllib.parse.quote_plus(query)
    html = _ua_get(f"https://html.duckduckgo.com/html/?q={q}")
    if html.startswith('ERROR:'):
        # fallback: try Google search
        html = _ua_get(f"https://www.google.com/search?q={q}&num={num_results}")
    results = []
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*result__a[^"]*"[^>]*>(.*?)</a>', html, re.S):
        url, title = m.group(1), re.sub('<[^>]+>', '', m.group(2)).strip()
        if url and title and not url.startswith('//duckduckgo'):
            results.append(f"• {title}\n  {url}")
        if len(results) >= num_results:
            break
    if not results:
        # generic link extraction fallback
        for m in re.finditer(r'href="(https?://[^"]+)"', html):
            u = m.group(1)
            if 'duckduckgo' not in u and 'google' not in u:
                results.append(f"• {u}")
            if len(results) >= 5:
                break
    return '\n'.join(results) if results else f"No results for: {query}"

def tool_web_fetch(url: str, max_chars: int = 6000) -> str:
    """Fetch a web page and return readable text."""
    raw = _ua_get(url, timeout=20)
    if raw.startswith('ERROR:'):
        return raw
    return _strip_html(raw, max_chars)

def tool_execute_shell(command: str, cwd: str = '', timeout: int = 30) -> str:
    """Run a shell command. Returns stdout+stderr."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=cwd or str(_ROOT)
        )
        out = (result.stdout or '') + (result.stderr or '')
        return out.strip()[:4000] or '(no output)'
    except subprocess.TimeoutExpired:
        return f"ERROR: command timed out after {timeout}s"
    except Exception as e:
        return f"ERROR: {e}"

def tool_execute_python(code: str, cwd: str = '') -> str:
    """Execute Python code in a subprocess and return output."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        fname = f.name
    try:
        result = subprocess.run(
            [sys.executable, fname], capture_output=True, text=True,
            timeout=30, cwd=cwd or str(_ROOT)
        )
        out = (result.stdout or '') + (result.stderr or '')
        return out.strip()[:4000] or '(no output)'
    except subprocess.TimeoutExpired:
        return "ERROR: python execution timed out"
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        try:
            os.unlink(fname)
        except Exception:
            pass

def tool_read_file(path: str, offset: int = 0, limit: int = 200) -> str:
    """Read a file (relative to project root or absolute)."""
    p = Path(path) if Path(path).is_absolute() else _ROOT / path
    try:
        lines = p.read_text(errors='replace').splitlines()
        chunk = lines[offset:offset + limit]
        total = len(lines)
        result = '\n'.join(f"{offset+i+1:4}: {l}" for i, l in enumerate(chunk))
        if total > offset + limit:
            result += f"\n... ({total - offset - limit} more lines)"
        return result
    except Exception as e:
        return f"ERROR: {e}"

def tool_write_file(path: str, content: str) -> str:
    """Write content to a file."""
    p = Path(path) if Path(path).is_absolute() else _ROOT / path
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Written {len(content)} bytes to {p}"
    except Exception as e:
        return f"ERROR: {e}"

def tool_edit_file(path: str, old_string: str, new_string: str) -> str:
    """Replace old_string with new_string in a file."""
    p = Path(path) if Path(path).is_absolute() else _ROOT / path
    try:
        text = p.read_text(errors='replace')
        if old_string not in text:
            return f"ERROR: old_string not found in {path}"
        updated = text.replace(old_string, new_string, 1)
        p.write_text(updated)
        return f"Patched {path}"
    except Exception as e:
        return f"ERROR: {e}"

def tool_list_files(path: str = '.', pattern: str = '*', recursive: bool = False) -> str:
    """List files in a directory."""
    base = Path(path) if Path(path).is_absolute() else _ROOT / path
    try:
        if recursive:
            files = list(base.rglob(pattern))
        else:
            files = list(base.glob(pattern))
        files = [f for f in files if not any(p.startswith('.') for p in f.parts[-3:])]
        files = sorted(files)[:100]
        return '\n'.join(str(f.relative_to(_ROOT) if f.is_relative_to(_ROOT) else f) for f in files) or "(empty)"
    except Exception as e:
        return f"ERROR: {e}"

def tool_search_files(pattern: str, path: str = '.') -> str:
    """Grep for pattern in files under path."""
    base = Path(path) if Path(path).is_absolute() else _ROOT / path
    try:
        result = subprocess.run(
            ['grep', '-rl', '--include=*.py', '--include=*.ts', '--include=*.js',
             pattern, str(base)],
            capture_output=True, text=True, timeout=15
        )
        lines = result.stdout.strip().splitlines()[:30]
        return '\n'.join(lines) or f"No matches for {pattern!r}"
    except Exception as e:
        return f"ERROR: {e}"

def tool_screenshot(save_path: str = '') -> str:
    """Take a screenshot (requires display). Returns path or error."""
    if not save_path:
        save_path = f"/tmp/devin_shot_{int(time.time())}.png"
    display = os.environ.get('DISPLAY', '')
    if not display:
        return "ERROR: No DISPLAY set — headless environment. Cannot take screenshot."
    try:
        r = subprocess.run(['scrot', save_path], capture_output=True, timeout=10)
        if r.returncode == 0:
            return f"Screenshot saved: {save_path}"
        r2 = subprocess.run(['import', '-window', 'root', save_path], capture_output=True, timeout=10)
        if r2.returncode == 0:
            return f"Screenshot saved: {save_path}"
        return "ERROR: No screenshot tool available (scrot, import)"
    except Exception as e:
        return f"ERROR: {e}"

def tool_clipboard_get() -> str:
    """Read the clipboard contents."""
    try:
        r = subprocess.run(['xclip', '-o', '-selection', 'clipboard'], capture_output=True, text=True, timeout=5)
        return r.stdout.strip() or "(empty clipboard)"
    except Exception:
        try:
            r = subprocess.run(['xsel', '--clipboard', '--output'], capture_output=True, text=True, timeout=5)
            return r.stdout.strip() or "(empty clipboard)"
        except Exception as e:
            return f"ERROR: {e}"

def tool_clipboard_set(text: str) -> str:
    """Write to clipboard."""
    try:
        r = subprocess.run(['xclip', '-selection', 'clipboard'],
                           input=text.encode(), capture_output=True, timeout=5)
        return "Copied to clipboard." if r.returncode == 0 else "ERROR: xclip failed"
    except Exception as e:
        return f"ERROR: {e}"

def tool_remember(fact: str, tags: str = '') -> str:
    """Save a fact to persistent memory."""
    return _remember(fact, tags)

def tool_recall(query: str = '') -> str:
    """Retrieve memories. Optional query to filter."""
    return _recall(query)

def tool_get_system_info() -> str:
    """Return system info: OS, CPU, RAM, disk."""
    import platform
    lines = [
        f"OS:      {platform.system()} {platform.release()} {platform.machine()}",
        f"Python:  {platform.python_version()}",
    ]
    try:
        cpu = subprocess.run(['nproc'], capture_output=True, text=True).stdout.strip()
        lines.append(f"CPUs:    {cpu}")
    except Exception:
        pass
    try:
        free = subprocess.run(['free', '-h'], capture_output=True, text=True).stdout
        lines.append(f"Memory:\n{free.strip()}")
    except Exception:
        pass
    try:
        df = subprocess.run(['df', '-h', '/'], capture_output=True, text=True).stdout
        lines.append(f"Disk:\n{df.strip()}")
    except Exception:
        pass
    return '\n'.join(lines)

def tool_task_complete(result: str) -> str:
    """Signal that the task is fully completed."""
    return f"TASK_COMPLETE:{result}"

# ── Tool registry ─────────────────────────────────────────────────────────────

TOOLS: Dict[str, Dict] = {
    "think": {
        "fn": tool_think,
        "desc": "Record your reasoning or plan a step. No side effects.",
        "params": {"thought": {"type": "string", "description": "Your thought or reasoning step"}},
        "required": ["thought"],
    },
    "web_search": {
        "fn": tool_web_search,
        "desc": "Search the web via DuckDuckGo. Returns titles and URLs.",
        "params": {
            "query": {"type": "string", "description": "Search query"},
            "num_results": {"type": "integer", "description": "Number of results (default 8)"},
        },
        "required": ["query"],
    },
    "web_fetch": {
        "fn": tool_web_fetch,
        "desc": "Fetch a web page and return its readable text content.",
        "params": {
            "url": {"type": "string", "description": "Full URL to fetch"},
            "max_chars": {"type": "integer", "description": "Max characters to return (default 6000)"},
        },
        "required": ["url"],
    },
    "execute_shell": {
        "fn": tool_execute_shell,
        "desc": "Run a shell command. Returns stdout and stderr.",
        "params": {
            "command": {"type": "string", "description": "Shell command to run"},
            "cwd": {"type": "string", "description": "Working directory (optional)"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"},
        },
        "required": ["command"],
    },
    "execute_python": {
        "fn": tool_execute_python,
        "desc": "Execute Python code and return its output.",
        "params": {
            "code": {"type": "string", "description": "Python code to execute"},
        },
        "required": ["code"],
    },
    "read_file": {
        "fn": tool_read_file,
        "desc": "Read a file from the filesystem with line numbers.",
        "params": {
            "path": {"type": "string", "description": "File path (relative to project root or absolute)"},
            "offset": {"type": "integer", "description": "Start line (0-indexed)"},
            "limit": {"type": "integer", "description": "Max lines to read (default 200)"},
        },
        "required": ["path"],
    },
    "write_file": {
        "fn": tool_write_file,
        "desc": "Write content to a file (creates parent dirs if needed).",
        "params": {
            "path": {"type": "string", "description": "File path"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
    },
    "edit_file": {
        "fn": tool_edit_file,
        "desc": "Edit a file by replacing old_string with new_string (first occurrence).",
        "params": {
            "path": {"type": "string", "description": "File path"},
            "old_string": {"type": "string", "description": "Text to find"},
            "new_string": {"type": "string", "description": "Replacement text"},
        },
        "required": ["path", "old_string", "new_string"],
    },
    "list_files": {
        "fn": tool_list_files,
        "desc": "List files in a directory.",
        "params": {
            "path": {"type": "string", "description": "Directory path (default: project root)"},
            "pattern": {"type": "string", "description": "Glob pattern (default: *)"},
            "recursive": {"type": "boolean", "description": "Search recursively (default: false)"},
        },
        "required": [],
    },
    "search_files": {
        "fn": tool_search_files,
        "desc": "Search file contents for a text pattern (grep).",
        "params": {
            "pattern": {"type": "string", "description": "Text pattern to search for"},
            "path": {"type": "string", "description": "Directory to search (default: project root)"},
        },
        "required": ["pattern"],
    },
    "screenshot": {
        "fn": tool_screenshot,
        "desc": "Take a screenshot of the current screen (requires display/X11).",
        "params": {
            "save_path": {"type": "string", "description": "Where to save the screenshot (default: /tmp/devin_shot_*.png)"},
        },
        "required": [],
    },
    "clipboard_get": {
        "fn": tool_clipboard_get,
        "desc": "Read the clipboard contents.",
        "params": {},
        "required": [],
    },
    "clipboard_set": {
        "fn": tool_clipboard_set,
        "desc": "Write text to the clipboard.",
        "params": {"text": {"type": "string", "description": "Text to write to clipboard"}},
        "required": ["text"],
    },
    "remember": {
        "fn": tool_remember,
        "desc": "Save a fact to persistent memory for future recall.",
        "params": {
            "fact": {"type": "string", "description": "Fact to remember"},
            "tags": {"type": "string", "description": "Comma-separated tags"},
        },
        "required": ["fact"],
    },
    "recall": {
        "fn": tool_recall,
        "desc": "Retrieve memories. Pass a query to filter, or empty for recent.",
        "params": {
            "query": {"type": "string", "description": "Optional search query"},
        },
        "required": [],
    },
    "get_system_info": {
        "fn": tool_get_system_info,
        "desc": "Get OS, CPU, RAM, and disk information.",
        "params": {},
        "required": [],
    },
    "task_complete": {
        "fn": tool_task_complete,
        "desc": "Signal that the task is fully completed. Call this ONLY when the task is done.",
        "params": {
            "result": {"type": "string", "description": "Final result / summary of what was accomplished"},
        },
        "required": ["result"],
    },
}

def _dispatch_tool(name: str, args: dict) -> str:
    if name not in TOOLS:
        return f"ERROR: unknown tool {name!r}"
    fn = TOOLS[name]["fn"]
    try:
        return str(fn(**args))
    except TypeError as e:
        return f"ERROR calling {name}: {e}"
    except Exception as e:
        return f"ERROR in {name}: {e}"

# ═══════════════════════════════════════════════════════════════════════════════
# AI PROVIDERS
# ═══════════════════════════════════════════════════════════════════════════════

def _http_post(url: str, headers: dict, body: dict, timeout: int = 60) -> dict:
    data = json.dumps(body).encode()
    req  = urllib.request.Request(url, data=data, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def _tool_schema_gemini() -> list:
    props = {}
    for name, t in TOOLS.items():
        p = {}
        for k, v in t["params"].items():
            tp = v["type"]
            gemini_type = {"string": "STRING", "integer": "INTEGER",
                           "boolean": "BOOLEAN", "number": "NUMBER"}.get(tp, "STRING")
            p[k] = {"type": gemini_type, "description": v["description"]}
        props[name] = {
            "name": name,
            "description": t["desc"],
            "parameters": {
                "type": "OBJECT",
                "properties": p,
                "required": t["required"],
            },
        }
    return [{"functionDeclarations": list(props.values())}]

def _tool_schema_claude() -> list:
    out = []
    for name, t in TOOLS.items():
        out.append({
            "name": name,
            "description": t["desc"],
            "input_schema": {
                "type": "object",
                "properties": {k: {"type": v["type"], "description": v["description"]}
                               for k, v in t["params"].items()},
                "required": t["required"],
            },
        })
    return out

def _tool_schema_openai() -> list:
    out = []
    for name, t in TOOLS.items():
        out.append({
            "type": "function",
            "function": {
                "name": name,
                "description": t["desc"],
                "parameters": {
                    "type": "object",
                    "properties": {k: {"type": v["type"], "description": v["description"]}
                                   for k, v in t["params"].items()},
                    "required": t["required"],
                },
            },
        })
    return out

# ─── Gemini ────────────────────────────────────────────────────────────────────

class GeminiProvider:
    BASE = "https://generativelanguage.googleapis.com/v1beta"
    # Model aliases supported by AI Studio
    MODEL_ALIASES = {
        'gemini-flash-latest': 'gemini-3.6-flash',
        'gemini-pro-latest':   'gemini-2.5-pro',
        'gemini-flash-lite-latest': 'gemini-3.6-flash',
    }
    # Ordered list of models to try (newest first)
    FALLBACK_MODELS = [
        'gemini-3.6-flash',
        'gemini-2.5-flash',
        'gemini-2.5-pro',
        'gemini-2.0-flash',
        'gemini-1.5-flash',
    ]

    def __init__(self, api_key: str, model: str = "gemini-3.6-flash"):
        self.api_key  = api_key
        self.model    = self.MODEL_ALIASES.get(model, model)
        self.name     = f"gemini/{self.model}"

    def _url(self, endpoint: str) -> str:
        # Use header auth for AI Studio tokens (AQ. prefix); URL key for traditional keys
        if self.api_key.startswith('AI'):
            return f"{self.BASE}/models/{self.model}:{endpoint}?key={self.api_key}"
        return f"{self.BASE}/models/{self.model}:{endpoint}"

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if not self.api_key.startswith('AI'):
            # AI Studio token — use header auth
            h['X-goog-api-key'] = self.api_key
        return h

    def call(self, messages: list, system: str = '') -> Tuple[str, List[dict]]:
        """Returns (text, tool_calls). tool_calls = [{"name":..,"args":..}]"""
        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": f"[System]: {system}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        for m in messages:
            role = "model" if m["role"] == "assistant" else "user"
            parts = []
            if isinstance(m.get("content"), list):
                for blk in m["content"]:
                    if blk.get("type") == "tool_result":
                        parts.append({"text": f"[Tool result: {blk.get('content','')}]"})
                    elif blk.get("type") == "tool_use":
                        parts.append({"text": f"[Calling {blk['name']}({json.dumps(blk.get('input',{}))})]"})
                    else:
                        parts.append({"text": str(blk.get("text", ""))})
            else:
                parts.append({"text": str(m.get("content", ""))})
            if parts:
                contents.append({"role": role, "parts": parts})

        body = {
            "contents": contents,
            "tools": _tool_schema_gemini(),
            "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.7},
        }
        models_to_try = [self.model] + [m for m in self.FALLBACK_MODELS if m != self.model]
        last_err = ""
        for model_name in models_to_try:
            orig_model = self.model
            self.model = model_name
            for attempt in range(3):
                try:
                    resp = _http_post(
                        self._url("generateContent"),
                        self._headers(),
                        body, timeout=90
                    )
                    if "error" in resp:
                        raise ValueError(resp["error"].get("message", "Gemini error"))
                    cand = resp.get("candidates", [{}])[0]
                    parts = cand.get("content", {}).get("parts", [])
                    text  = "".join(p.get("text", "") for p in parts if "text" in p)
                    calls = []
                    for p in parts:
                        fc = p.get("functionCall")
                        if fc:
                            calls.append({"name": fc["name"], "args": fc.get("args", {})})
                    return text, calls
                except urllib.error.HTTPError as e:
                    body_txt = e.read().decode('utf-8', errors='replace')
                    if e.code == 429:
                        wait = 2 ** (attempt + 1)
                        print(yellow(f"  ⏳ rate limited ({model_name}), retrying in {wait}s…"), flush=True)
                        time.sleep(wait)
                        continue
                    if e.code == 404:
                        last_err = f"model {model_name} not available"
                        break  # try next model
                    raise ValueError(f"Gemini HTTP {e.code}: {body_txt[:300]}")
            self.model = orig_model
        raise ValueError(f"Gemini: all models exhausted. Last error: {last_err}")

# ─── Claude ────────────────────────────────────────────────────────────────────

class ClaudeProvider:
    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.model   = model
        self.name    = f"claude/{model}"

    def call(self, messages: list, system: str = '') -> Tuple[str, List[dict]]:
        hdrs = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        body = {
            "model": self.model,
            "max_tokens": 8192,
            "tools": _tool_schema_claude(),
            "messages": messages,
        }
        if system:
            body["system"] = system
        for attempt in range(4):
            try:
                resp = _http_post(self.URL, hdrs, body, timeout=90)
                text  = ""
                calls = []
                for blk in resp.get("content", []):
                    if blk.get("type") == "text":
                        text += blk.get("text", "")
                    elif blk.get("type") == "tool_use":
                        calls.append({"id": blk.get("id"), "name": blk["name"], "args": blk.get("input", {})})
                return text, calls
            except urllib.error.HTTPError as e:
                body_txt = e.read().decode('utf-8', errors='replace')
                if e.code == 429:
                    wait = 2 ** (attempt + 1)
                    print(yellow(f"  ⏳ rate limited, retrying in {wait}s…"), flush=True)
                    time.sleep(wait)
                    continue
                raise ValueError(f"Claude HTTP {e.code}: {body_txt[:300]}")
        raise ValueError("Claude: max retries exceeded")

# ─── OpenAI ────────────────────────────────────────────────────────────────────

class OpenAIProvider:
    URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model   = model
        self.name    = f"openai/{model}"

    def call(self, messages: list, system: str = '') -> Tuple[str, List[dict]]:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        for m in messages:
            role = m["role"]
            content = m.get("content", "")
            if isinstance(content, list):
                text_parts = []
                for blk in content:
                    if blk.get("type") == "tool_result":
                        text_parts.append(f"[Tool result: {blk.get('content','')}]")
                    else:
                        text_parts.append(str(blk.get("text", "")))
                content = " ".join(text_parts)
            msgs.append({"role": role, "content": content})

        body = {
            "model": self.model,
            "max_tokens": 4096,
            "tools": _tool_schema_openai(),
            "messages": msgs,
        }
        hdrs = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        for attempt in range(4):
            try:
                resp  = _http_post(self.URL, hdrs, body, timeout=90)
                msg   = resp["choices"][0]["message"]
                text  = msg.get("content") or ""
                calls = []
                for tc in (msg.get("tool_calls") or []):
                    fn = tc.get("function", {})
                    try:
                        args = json.loads(fn.get("arguments", "{}"))
                    except Exception:
                        args = {}
                    calls.append({"id": tc.get("id"), "name": fn.get("name"), "args": args})
                return text, calls
            except urllib.error.HTTPError as e:
                body_txt = e.read().decode('utf-8', errors='replace')
                if e.code == 429:
                    wait = 2 ** (attempt + 1)
                    print(yellow(f"  ⏳ rate limited, retrying in {wait}s…"), flush=True)
                    time.sleep(wait)
                    continue
                raise ValueError(f"OpenAI HTTP {e.code}: {body_txt[:300]}")
        raise ValueError("OpenAI: max retries exceeded")

# ─── Provider selector ────────────────────────────────────────────────────────

def _pick_provider(name: str = '', model: str = ''):
    gk = os.environ.get('GEMINI_API_KEY', '')
    ak = os.environ.get('ANTHROPIC_API_KEY', '')
    ok = os.environ.get('OPENAI_API_KEY', '')

    if name == 'gemini':
        if not gk: raise ValueError("GEMINI_API_KEY not set")
        return GeminiProvider(gk, model or 'gemini-2.5-flash')
    if name in ('claude', 'anthropic'):
        if not ak: raise ValueError("ANTHROPIC_API_KEY not set")
        return ClaudeProvider(ak, model or 'claude-sonnet-4-6')
    if name == 'openai':
        if not ok: raise ValueError("OPENAI_API_KEY not set")
        return OpenAIProvider(ok, model or 'gpt-4o-mini')

    # auto-select by available key
    if gk: return GeminiProvider(gk, model or 'gemini-3.6-flash')
    if ak: return ClaudeProvider(ak, model or 'claude-sonnet-4-6')
    if ok: return OpenAIProvider(ok, model or 'gpt-4o-mini')
    raise ValueError(
        "No API key found. Set GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY "
        "in .env or environment."
    )

def _available_providers() -> List[str]:
    out = []
    if os.environ.get('GEMINI_API_KEY'):    out.append(green('gemini') + ' ✓')
    else:                                    out.append(dim('gemini') + ' (no key)')
    if os.environ.get('ANTHROPIC_API_KEY'): out.append(green('claude') + ' ✓')
    else:                                    out.append(dim('claude') + ' (no key)')
    if os.environ.get('OPENAI_API_KEY'):    out.append(green('openai') + ' ✓')
    else:                                    out.append(dim('openai') + ' (no key)')
    return out

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """\
You are Devin, an advanced AI agent with real tool-calling capabilities.
You can search the web, read/write files, execute code, take screenshots,
manage memory, and complete complex multi-step tasks autonomously.

## How to behave
1. THINK FIRST — call the `think` tool to reason through the task before acting.
2. ACT — use the appropriate tools step by step.
3. VERIFY — check results after each action.
4. CONTINUE — keep going until the task is done.
5. COMPLETE — call `task_complete` with a clear result summary when done.

## Rules
- Never fabricate tool results — only report what tools actually return.
- Never stop mid-task unless truly blocked.
- Use `think` freely to reason, plan, and self-correct.
- For web tasks: search → fetch the relevant pages → extract info → answer.
- For code tasks: write → execute → verify output → fix if needed.
- For file tasks: read first, then edit precisely.
- Call `task_complete` exactly once when the full task is verified done.
- If you cannot complete a task, call `task_complete` explaining exactly why.

## Tool calling
You have these tools available (use them, don't just describe what you would do):
think, web_search, web_fetch, execute_shell, execute_python,
read_file, write_file, edit_file, list_files, search_files,
screenshot, clipboard_get, clipboard_set,
remember, recall, get_system_info, task_complete
"""

# ═══════════════════════════════════════════════════════════════════════════════
# AGENTIC LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def _fmt_tool_call(name: str, args: dict) -> str:
    arg_str = ', '.join(f'{k}={repr(v)[:60]}' for k, v in args.items())
    return f"{cyan(name)}({arg_str})"

def run_agent(task: str, provider, max_steps: int = 60, quiet: bool = False) -> str:
    """
    Run the agentic loop for a given task.
    Returns the final result string.
    """
    messages: List[dict] = [{"role": "user", "content": task}]
    final_result = ""
    step = 0

    if not quiet:
        print()
        print(_box(f"Task: {task[:70]}", '═'))
        print(dim(f"Provider: {provider.name}  |  Max steps: {max_steps}"))
        print(_hr())

    while step < max_steps:
        step += 1
        spinner_chars = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
        if not quiet:
            print(dim(f"\n[step {step}/{max_steps}] thinking…"), end='\r', flush=True)

        try:
            text, calls = provider.call(messages, system=SYSTEM_PROMPT)
        except Exception as e:
            if not quiet:
                print(red(f"\n⚠ Provider error: {e}"))
            break

        # Print assistant text
        if text and text.strip() and not quiet:
            clean = text.strip()
            # strip any (acting) artifacts
            clean = re.sub(r'^\s*\(acting\)\s*', '', clean, flags=re.I)
            if clean:
                print(f"\n{bold(cyan('Devin'))}  {clean}")

        # Add assistant message
        if isinstance(provider, ClaudeProvider):
            content_blocks: List[dict] = []
            if text:
                content_blocks.append({"type": "text", "text": text})
            for c in calls:
                content_blocks.append({
                    "type": "tool_use",
                    "id": c.get("id", f"call_{step}_{c['name']}"),
                    "name": c["name"],
                    "input": c["args"],
                })
            if content_blocks:
                messages.append({"role": "assistant", "content": content_blocks})
        else:
            messages.append({"role": "assistant", "content": text or ""})

        if not calls:
            # No tool calls — AI is done or stuck
            if text.strip():
                final_result = text.strip()
            break

        # Execute each tool call
        tool_results = []
        for call in calls:
            name = call["name"]
            args = call["args"]

            if not quiet:
                print(f"\n  {blue('▶')} {_fmt_tool_call(name, args)}")

            result = _dispatch_tool(name, args)

            # Check for task completion
            if name == "task_complete" or result.startswith("TASK_COMPLETE:"):
                final_result = result.replace("TASK_COMPLETE:", "").strip()
                if not quiet:
                    print(f"  {green('✓')} {dim(result[:200])}")
                    print()
                    print(_hr())
                    print(green(bold("✅ Task complete")))
                    print(final_result)
                return final_result

            # Display result preview
            if not quiet:
                preview = result[:300].replace('\n', ' ')
                print(f"  {dim('←')} {dim(preview)}")

            tool_results.append({
                "call_id": call.get("id", f"call_{step}_{name}"),
                "name": name,
                "result": result,
            })

        # Add tool results back to messages
        if isinstance(provider, ClaudeProvider):
            tool_result_blocks = [
                {
                    "type": "tool_result",
                    "tool_use_id": tr["call_id"],
                    "content": tr["result"],
                }
                for tr in tool_results
            ]
            messages.append({"role": "user", "content": tool_result_blocks})
        elif isinstance(provider, OpenAIProvider):
            for tr in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tr["call_id"],
                    "content": tr["result"],
                })
        else:
            # Gemini: pack all results as user turn
            combined = "\n\n".join(
                f"[Tool: {tr['name']}]\n{tr['result']}" for tr in tool_results
            )
            messages.append({"role": "user", "content": combined})

    if not final_result:
        final_result = "(task ended without explicit completion)"

    if not quiet:
        print()
        print(_hr())
        print(dim(f"Loop ended after {step} steps."))

    return final_result

# ═══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE REPL
# ═══════════════════════════════════════════════════════════════════════════════

SLASH_HELP = f"""
{bold('Slash commands')}
  {cyan('/help')}              Show this help
  {cyan('/tools')}             List available tools
  {cyan('/status')}            Show provider, model, key status
  {cyan('/providers')}         Show all providers and key status
  {cyan('/model <name>')}      Switch model  (e.g. /model gemini-2.5-pro)
  {cyan('/provider <name>')}   Switch provider  (gemini | claude | openai)
  {cyan('/memory')}            Show stored memories
  {cyan('/remember <fact>')}   Save a fact to memory
  {cyan('/forget')}            Clear all memories
  {cyan('/history')}           Show conversation history (current session)
  {cyan('/shell <cmd>')}       Run a shell command directly
  {cyan('/clear')}             Clear the screen
  {cyan('/exit')} / {cyan('/quit')}     Exit Devin

{bold('Usage')}
  Type a task or question, press Enter.
  Devin reasons and uses tools autonomously until the task is done.

{bold('API keys')}  (.env or environment)
  GEMINI_API_KEY      https://aistudio.google.com/app/apikey
  ANTHROPIC_API_KEY   https://console.anthropic.com/
  OPENAI_API_KEY      https://platform.openai.com/api-keys
"""

def _banner():
    w = shutil.get_terminal_size().columns
    lines = [
        "",
        bold(cyan(" ██████╗ ███████╗██╗   ██╗██╗███╗   ██╗")),
        bold(cyan(" ██╔══██╗██╔════╝██║   ██║██║████╗  ██║")),
        bold(cyan(" ██║  ██║█████╗  ██║   ██║██║██╔██╗ ██║")),
        bold(cyan(" ██║  ██║██╔══╝  ╚██╗ ██╔╝██║██║╚██╗██║")),
        bold(cyan(" ██████╔╝███████╗ ╚████╔╝ ██║██║ ╚████║")),
        bold(cyan(" ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝╚═╝  ╚═══╝")),
        "",
        dim("  Agentic AI  ·  Self-contained  ·  All providers"),
        "",
    ]
    for l in lines:
        print(l)

def _print_status(provider):
    print(f"\n  {bold('Provider')}  {green(provider.name)}")
    keys = []
    if os.environ.get('GEMINI_API_KEY'):    keys.append(green('gemini ✓'))
    else:                                    keys.append(dim('gemini ✗'))
    if os.environ.get('ANTHROPIC_API_KEY'): keys.append(green('claude ✓'))
    else:                                    keys.append(dim('claude ✗'))
    if os.environ.get('OPENAI_API_KEY'):    keys.append(green('openai ✓'))
    else:                                    keys.append(dim('openai ✗'))
    print(f"  {bold('Keys')}      {' | '.join(keys)}")
    print(f"  {bold('Memory')}    {_DB_PATH.name}  ({_DB.execute('SELECT count(*) FROM memories').fetchone()[0]} facts)")
    print(f"  {bold('Tools')}     {len(TOOLS)} built-in")
    print()

def repl(provider_name: str = '', model: str = ''):
    """Interactive REPL."""
    try:
        import readline
        history_file = str(_ROOT / '.devin_history')
        try:
            readline.read_history_file(history_file)
        except FileNotFoundError:
            pass
        import atexit
        atexit.register(readline.write_history_file, history_file)
        readline.set_history_length(500)
    except ImportError:
        pass

    _banner()

    try:
        provider = _pick_provider(provider_name, model)
    except ValueError as e:
        print(red(f"⚠ {e}"))
        print(dim("Set an API key in .env to get started. Type /help for info."))
        provider = None

    if provider:
        _print_status(provider)
        print(dim("Type a task or question. /help for commands. /exit to quit.\n"))
    else:
        print(dim("No provider active. Set an API key and restart, or /help for info.\n"))

    while True:
        try:
            user_input = input(f"{bold(cyan('you'))} › ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        # ── Slash commands ────────────────────────────────────────────────────
        if user_input.startswith('/'):
            parts = user_input.split(None, 1)
            cmd   = parts[0].lower()
            arg   = parts[1] if len(parts) > 1 else ''

            if cmd in ('/exit', '/quit'):
                print(dim("Bye."))
                break

            elif cmd == '/help':
                print(SLASH_HELP)

            elif cmd == '/clear':
                os.system('clear' if os.name != 'nt' else 'cls')

            elif cmd == '/tools':
                print(f"\n{bold('Available tools')} ({len(TOOLS)}):\n")
                for name, t in TOOLS.items():
                    print(f"  {cyan(name):30s} {t['desc']}")
                print()

            elif cmd == '/status':
                if provider:
                    _print_status(provider)
                else:
                    print(red("No provider active."))

            elif cmd == '/providers':
                for p in _available_providers():
                    print(f"  {p}")
                print()

            elif cmd == '/model':
                if not arg:
                    print(yellow("Usage: /model <model-name>"))
                else:
                    try:
                        pname = provider_name or ('gemini' if os.environ.get('GEMINI_API_KEY') else
                                                   'claude' if os.environ.get('ANTHROPIC_API_KEY') else 'openai')
                        provider = _pick_provider(pname, arg)
                        print(green(f"Switched to {provider.name}"))
                    except Exception as e:
                        print(red(f"Error: {e}"))

            elif cmd == '/provider':
                if not arg:
                    print(yellow("Usage: /provider gemini|claude|openai"))
                else:
                    try:
                        provider = _pick_provider(arg, model)
                        provider_name = arg
                        print(green(f"Switched to {provider.name}"))
                    except Exception as e:
                        print(red(f"Error: {e}"))

            elif cmd == '/memory':
                print(_recall(arg))

            elif cmd == '/remember':
                if arg:
                    print(_remember(arg))
                else:
                    print(yellow("Usage: /remember <fact>"))

            elif cmd == '/forget':
                print(_forget_all())

            elif cmd == '/history':
                rows = _DB.execute(
                    "SELECT ts, session, fact FROM memories WHERE session=? ORDER BY id",
                    (_SESSION_ID,)
                ).fetchall()
                if rows:
                    for r in rows:
                        print(f"  {dim(r[0])} {r[2]}")
                else:
                    print(dim("No memories this session."))

            elif cmd == '/shell':
                if arg:
                    out = tool_execute_shell(arg)
                    print(out)
                else:
                    print(yellow("Usage: /shell <command>"))

            else:
                print(yellow(f"Unknown command {cmd!r}. Type /help."))

            continue

        # ── Run agent task ────────────────────────────────────────────────────
        if provider is None:
            print(red("No provider. Set an API key in .env and restart."))
            continue

        try:
            run_agent(user_input, provider)
        except KeyboardInterrupt:
            print(yellow("\n  Interrupted."))
        except Exception as e:
            print(red(f"\n⚠ Agent error: {e}"))

# ═══════════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]

    # Parse flags
    provider_name = ''
    model         = ''
    task_args     = []

    i = 0
    while i < len(args):
        a = args[i]
        if a in ('--provider', '-p') and i + 1 < len(args):
            provider_name = args[i + 1]; i += 2
        elif a in ('--model', '-m') and i + 1 < len(args):
            model = args[i + 1]; i += 2
        elif a.startswith('--provider='):
            provider_name = a.split('=', 1)[1]; i += 1
        elif a.startswith('--model='):
            model = a.split('=', 1)[1]; i += 1
        elif a in ('--help', '-h'):
            print(__doc__)
            sys.exit(0)
        else:
            task_args.append(a); i += 1

    if task_args:
        # One-shot mode
        task = ' '.join(task_args)
        try:
            provider = _pick_provider(provider_name, model)
        except ValueError as e:
            print(red(f"⚠ {e}"))
            sys.exit(1)
        print(dim(f"Provider: {provider.name}"))
        result = run_agent(task, provider)
        if result and not result.startswith("(task ended"):
            print(f"\n{green('Result:')} {result}")
        sys.exit(0)
    else:
        # Interactive REPL
        repl(provider_name, model)

if __name__ == '__main__':
    main()
