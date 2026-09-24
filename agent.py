#!/usr/bin/env python3
"""
Devin Agent — OS-controlled agentic AI CLI
==========================================
Fully self-contained. Zero external dependencies required.
Full computer control: mouse, keyboard, screen, files, shell, browser, voice.
Multi-provider AI: Gemini, Claude, OpenAI.
Conversational with persistent memory and full task execution.

Usage:
  python agent.py                           # interactive REPL (conversation mode)
  python agent.py "open firefox and search for AI news"
  python agent.py --provider claude "write a hello world script"
  python agent.py --model gemini-3.6-flash  "task here"
  python agent.py --chat                    # pure conversation mode

Slash commands (interactive):
  /help  /tools [cat]  /status  /providers  /model <m>  /provider <p>
  /clear  /memory [q]  /remember <fact>  /forget  /history
  /shell <cmd>  /screenshot  /repos  /voice  /integrations  /new  /exit /quit

API keys (.env or environment):
  GEMINI_API_KEY     https://aistudio.google.com/app/apikey
  ANTHROPIC_API_KEY  https://console.anthropic.com/
  OPENAI_API_KEY     https://platform.openai.com/api-keys
"""

from __future__ import annotations
import os, sys, json, time, re, subprocess, html as _html_lib, sqlite3
import urllib.request, urllib.parse, urllib.error, textwrap, shutil, base64
import platform, signal, threading, itertools
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

# ── Platform detection ─────────────────────────────────────────────────────────
_PLATFORM = platform.system()          # 'Linux', 'Darwin', 'Windows'
_IS_LINUX  = _PLATFORM == 'Linux'
_IS_MAC    = _PLATFORM == 'Darwin'
_IS_WIN    = _PLATFORM == 'Windows'
_HAS_DISPLAY = bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
                    or _IS_MAC or _IS_WIN)

# ── Terminal colours ──────────────────────────────────────────────────────────
_TTY = sys.stdout.isatty()
def _c(code, t): return f'\033[{code}m{t}\033[0m' if _TTY else t
cyan    = lambda t: _c('36;1', t)
green   = lambda t: _c('32;1', t)
yellow  = lambda t: _c('33;1', t)
red     = lambda t: _c('31;1', t)
bold    = lambda t: _c('1',    t)
dim     = lambda t: _c('2',    t)
blue    = lambda t: _c('34;1', t)
magenta = lambda t: _c('35;1', t)
white   = lambda t: _c('37',   t)
italic  = lambda t: _c('3',    t)

def _hr(char='─', width=0):
    w = width or max(40, (shutil.get_terminal_size((80,24)).columns - 1))
    return dim(char * w)

def _box(title: str, char='─'):
    w = max(40, shutil.get_terminal_size((80,24)).columns - 1)
    clean = re.sub(r'\033\[[^m]+m', '', title)
    pad = max(0, w - len(clean) - 4)
    return dim(char * 2) + ' ' + bold(title) + ' ' + dim(char * pad)

# ── Spinner (used during provider calls) ──────────────────────────────────────
_SPIN = itertools.cycle(['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏'])
_spin_active = threading.Event()

def _spin_start(msg: str = ''):
    _spin_active.set()
    def _run():
        while _spin_active.is_set():
            sys.stdout.write(f"\r  {dim(next(_SPIN))} {dim(msg)}  ")
            sys.stdout.flush()
            time.sleep(0.08)
        sys.stdout.write('\r' + ' ' * (len(msg) + 10) + '\r')
        sys.stdout.flush()
    threading.Thread(target=_run, daemon=True).start()

def _spin_stop():
    _spin_active.clear()
    time.sleep(0.1)

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
    return f"Remembered: {fact[:100]}"

def _recall(query: str = '', n: int = 15) -> str:
    if query:
        rows = _DB.execute(
            "SELECT ts, fact FROM memories WHERE fact LIKE ? ORDER BY id DESC LIMIT ?",
            (f'%{query}%', n)).fetchall()
    else:
        rows = _DB.execute(
            "SELECT ts, fact FROM memories ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    if not rows:
        return "No memories found."
    return '\n'.join(f"[{r[0]}] {r[1]}" for r in rows)

def _forget_all() -> str:
    _DB.execute('DELETE FROM memories')
    _DB.commit()
    return "All memories cleared."

# ── Optional pyautogui import (graceful) ─────────────────────────────────────
try:
    import pyautogui as _pag
    _pag.FAILSAFE = True
    _pag.PAUSE = 0.05
    _HAS_PAG = True
except Exception:
    _HAS_PAG = False

def _cmd_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None

# ── Devin modules integration loader ─────────────────────────────────────────
# Load optional Devin modules from modules/ for enhanced capabilities.
# Each is imported gracefully — failures never break core functionality.

_MODULES_DIR = _ROOT / 'modules'
if str(_MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULES_DIR))

# Load voice module (TTS/STT)
_voice_mod = None
try:
    import importlib as _il
    _voice_mod = _il.import_module('voice')
except Exception:
    pass

# Load os_automation module (enhanced OS control)
_os_auto_mod = None
try:
    _os_auto_mod = _il.import_module('os_automation')
except Exception:
    pass

# Load persistent_memory module (enhanced memory with categories/tags)
_pmem_mod = None
try:
    _pmem_mod = _il.import_module('persistent_memory')
    _pmem = _pmem_mod.PersistentMemory() if hasattr(_pmem_mod, 'PersistentMemory') else None
except Exception:
    _pmem = None

# Load messaging_gateway module (Telegram/Discord/Slack)
_msg_mod = None
try:
    _msg_mod = _il.import_module('messaging_gateway')
except Exception:
    pass

# Load integration_hub (all 24 external repos)
_hub_mod = None
try:
    _hub_mod = _il.import_module('integration_hub')
except Exception:
    pass

# Load cheetahclaws_bridge (token tracking, compaction)
_cc_bridge = None
try:
    _ccmod = _il.import_module('cheetahclaws_bridge')
    _cc_bridge = _ccmod.CheetahClawsBridge() if hasattr(_ccmod, 'CheetahClawsBridge') else None
except Exception:
    pass

# Load browser automation (Selenium/Playwright)
_browser_mod = None
_browser_instance = None
try:
    _browser_mod = _il.import_module('browser')
except Exception:
    pass

# Load system monitor
_sysmon_mod = None
try:
    _sysmon_mod = _il.import_module('system_monitor')
except Exception:
    pass

# Load code_execution module
_code_exec_mod = None
try:
    _code_exec_mod = _il.import_module('code_execution')
except Exception:
    pass

# Load scheduler
_scheduler_mod = None
try:
    _scheduler_mod = _il.import_module('scheduler')
except Exception:
    pass

# Load encryption tools
_crypto_mod = None
try:
    _crypto_mod = _il.import_module('encryption_tools')
except Exception:
    pass

# Load cloud integration
_cloud_mod = None
try:
    _cloud_mod = _il.import_module('cloud_integration_module')
except Exception:
    pass

# Load Jarvis tools
_jarvis_tools_mod = None
try:
    _jarvis_tools_mod = _il.import_module('jarvis_tools')
except Exception:
    pass

# Load cheetah providers (multi-model streaming)
_cheetah_providers_mod = None
try:
    _cheetah_providers_mod = _il.import_module('cheetah_providers')
except Exception:
    pass

# Load Ollama module (local LLM)
_ollama_mod = None
try:
    _ollama_mod = _il.import_module('ollama_module')
except Exception:
    pass

# Load social media API
_social_mod = None
try:
    _social_mod = _il.import_module('social_media_api')
except Exception:
    pass

# Count all available modules
def _modules_status() -> Dict[str, bool]:
    return {
        'voice':             _voice_mod           is not None,
        'os_automation':     _os_auto_mod         is not None,
        'persistent_memory': _pmem                is not None,
        'messaging_gateway': _msg_mod             is not None,
        'integration_hub':   _hub_mod             is not None,
        'cheetahclaws':      _cc_bridge           is not None,
        'browser':           _browser_mod         is not None,
        'system_monitor':    _sysmon_mod          is not None,
        'code_execution':    _code_exec_mod       is not None,
        'scheduler':         _scheduler_mod       is not None,
        'encryption':        _crypto_mod          is not None,
        'cloud':             _cloud_mod           is not None,
        'jarvis_tools':      _jarvis_tools_mod    is not None,
        'cheetah_providers': _cheetah_providers_mod is not None,
        'ollama':            _ollama_mod          is not None,
        'social_media':      _social_mod          is not None,
    }

# ═══════════════════════════════════════════════════════════════════════════════
# TOOLS  — every tool returns a string
# ═══════════════════════════════════════════════════════════════════════════════

# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _ua_get(url: str, timeout: int = 20) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
        'Accept': 'text/html,application/json,*/*;q=0.9',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            enc = r.headers.get_content_charset('utf-8')
            return r.read().decode(enc, errors='replace')
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

def _http_post(url: str, headers: dict, body: dict, timeout: int = 60) -> dict:
    data = json.dumps(body).encode()
    req  = urllib.request.Request(url, data=data, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

# ── Reasoning ─────────────────────────────────────────────────────────────────

def tool_think(thought: str) -> str:
    return f"[thought recorded] {thought[:500]}"

# ── Web ───────────────────────────────────────────────────────────────────────

def tool_web_search(query: str, num_results: int = 8) -> str:
    """Search via DuckDuckGo (no API key)."""
    q    = urllib.parse.quote_plus(query)
    html = _ua_get(f"https://html.duckduckgo.com/html/?q={q}")
    if html.startswith('ERROR:'):
        # Try a simple Google fallback
        html2 = _ua_get(f"https://www.google.com/search?q={q}&num=10")
        if not html2.startswith('ERROR:'):
            html = html2
        else:
            return f"Web search unavailable in this environment: {html}"
    results = []
    for m in re.finditer(
            r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*result__a[^"]*"[^>]*>(.*?)</a>',
            html, re.S):
        url, title = m.group(1), re.sub('<[^>]+>', '', m.group(2)).strip()
        if url and title and 'duckduckgo' not in url:
            results.append(f"• {title}\n  {url}")
        if len(results) >= num_results:
            break
    if not results:
        for m in re.finditer(r'href="(https?://[^"&]+)"', html):
            u = m.group(1)
            if 'duckduckgo' not in u and 'google.com' not in u:
                results.append(f"• {u}")
            if len(results) >= 5:
                break
    return '\n'.join(results) if results else \
           "No results (web search may be blocked in this environment)"

def tool_web_fetch(url: str, max_chars: int = 8000) -> str:
    raw = _ua_get(url, timeout=30)
    if raw.startswith('ERROR:'):
        return raw
    return _strip_html(raw, max_chars)

def tool_open_browser(url: str) -> str:
    """Open URL in the default browser."""
    if not _HAS_DISPLAY:
        return "ERROR: No display. Browser requires a GUI session."
    try:
        if _IS_MAC:
            subprocess.Popen(['open', url])
        elif _IS_WIN:
            os.startfile(url)  # type: ignore
        else:
            subprocess.Popen(['xdg-open', url])
        return f"Opened browser: {url}"
    except Exception as e:
        return f"ERROR: {e}"

# ── Shell / process ───────────────────────────────────────────────────────────

def tool_execute_shell(command: str, cwd: str = '', timeout: int = 30,
                       background: bool = False) -> str:
    """Run a shell command. Returns combined stdout+stderr."""
    try:
        if background:
            subprocess.Popen(command, shell=True, cwd=cwd or str(_ROOT),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Started in background: {command[:80]}"
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=cwd or str(_ROOT)
        )
        out = ((result.stdout or '') + (result.stderr or '')).strip()[:6000]
        return out or '(no output)'
    except subprocess.TimeoutExpired:
        return f"ERROR: timed out after {timeout}s"
    except Exception as e:
        return f"ERROR: {e}"

def tool_execute_python(code: str, cwd: str = '') -> str:
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code); fname = f.name
    try:
        r = subprocess.run([sys.executable, fname], capture_output=True, text=True,
                           timeout=60, cwd=cwd or str(_ROOT))
        return ((r.stdout or '') + (r.stderr or '')).strip()[:6000] or '(no output)'
    except subprocess.TimeoutExpired:
        return "ERROR: python execution timed out"
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        try: os.unlink(fname)
        except Exception: pass

def tool_list_processes(filter_str: str = '') -> str:
    try:
        r = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
        lines = r.stdout.strip().splitlines()
        if filter_str:
            lines = [l for l in lines if filter_str.lower() in l.lower()]
        return '\n'.join(lines[:60])
    except Exception as e:
        return f"ERROR: {e}"

def tool_kill_process(pid: int) -> str:
    try:
        os.kill(pid, signal.SIGTERM)
        return f"Sent SIGTERM to PID {pid}"
    except Exception as e:
        return f"ERROR: {e}"

def tool_sleep(seconds: float) -> str:
    """Sleep/wait for the specified number of seconds. Use after launching apps."""
    t = max(0.1, min(float(seconds), 30.0))
    time.sleep(t)
    return f"Slept {t}s"

# ── Files ─────────────────────────────────────────────────────────────────────

def tool_read_file(path: str, offset: int = 0, limit: int = 200) -> str:
    p = Path(path) if Path(path).is_absolute() else _ROOT / path
    try:
        lines = p.read_text(errors='replace').splitlines()
        chunk = lines[offset:offset + limit]
        out   = '\n'.join(f"{offset+i+1:4}: {l}" for i, l in enumerate(chunk))
        if len(lines) > offset + limit:
            out += f"\n... ({len(lines) - offset - limit} more lines)"
        return out
    except Exception as e:
        return f"ERROR: {e}"

def tool_write_file(path: str, content: str) -> str:
    p = Path(path) if Path(path).is_absolute() else _ROOT / path
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Written {len(content)} bytes to {p}"
    except Exception as e:
        return f"ERROR: {e}"

def tool_edit_file(path: str, old_string: str, new_string: str) -> str:
    p = Path(path) if Path(path).is_absolute() else _ROOT / path
    try:
        text = p.read_text(errors='replace')
        if old_string not in text:
            return f"ERROR: old_string not found in {path}"
        p.write_text(text.replace(old_string, new_string, 1))
        return f"Patched {path}"
    except Exception as e:
        return f"ERROR: {e}"

def tool_delete_file(path: str) -> str:
    p = Path(path) if Path(path).is_absolute() else _ROOT / path
    try:
        p.unlink()
        return f"Deleted {p}"
    except Exception as e:
        return f"ERROR: {e}"

def tool_list_files(path: str = '.', pattern: str = '*',
                    recursive: bool = False) -> str:
    base = Path(path) if Path(path).is_absolute() else _ROOT / path
    try:
        files = list(base.rglob(pattern) if recursive else base.glob(pattern))
        files = sorted(f for f in files
                       if not any(p.startswith(('.git', '__pycache__', 'node_modules'))
                                  for p in f.parts))[:100]
        lines = []
        for f in files:
            rel  = str(f.relative_to(_ROOT) if f.is_relative_to(_ROOT) else f)
            size = f"{f.stat().st_size:>8} B" if f.is_file() else "     dir"
            lines.append(f"{size}  {rel}")
        return '\n'.join(lines) or "(empty)"
    except Exception as e:
        return f"ERROR: {e}"

def tool_create_directory(path: str) -> str:
    p = Path(path) if Path(path).is_absolute() else _ROOT / path
    try:
        p.mkdir(parents=True, exist_ok=True)
        return f"Created directory: {p}"
    except Exception as e:
        return f"ERROR: {e}"

def tool_search_files(pattern: str, path: str = '.') -> str:
    base = Path(path) if Path(path).is_absolute() else _ROOT / path
    try:
        r = subprocess.run(
            ['grep', '-rl', '--include=*.py', '--include=*.ts', '--include=*.js',
             '--include=*.md', pattern, str(base)],
            capture_output=True, text=True, timeout=15)
        lines = r.stdout.strip().splitlines()[:50]
        return '\n'.join(lines) or f"No matches for {pattern!r}"
    except Exception as e:
        return f"ERROR: {e}"

def tool_git_command(args: str, cwd: str = '') -> str:
    """Run a git command. args is the arguments after 'git'."""
    try:
        r = subprocess.run(
            f"git {args}", shell=True, capture_output=True, text=True,
            timeout=30, cwd=cwd or str(_ROOT))
        return ((r.stdout or '') + (r.stderr or '')).strip()[:4000] or '(no output)'
    except Exception as e:
        return f"ERROR: {e}"

# ── Screenshot + Vision ───────────────────────────────────────────────────────

def tool_screenshot(save_path: str = '') -> str:
    """Take a screenshot. Requires display (X11/macOS/Windows)."""
    if not _HAS_DISPLAY:
        return "ERROR: No display available (headless environment). Cannot take screenshot."
    ts = int(time.time())
    out = save_path or f"/tmp/devin_shot_{ts}.png"
    try:
        if _HAS_PAG:
            img = _pag.screenshot()
            img.save(out)
            sz = Path(out).stat().st_size
            return f"Screenshot saved: {out}  ({img.size[0]}x{img.size[1]}, {sz//1024}KB)"
        if _cmd_exists('scrot'):
            subprocess.run(['scrot', out], check=True, timeout=10)
            sz = Path(out).stat().st_size
            return f"Screenshot saved: {out}  ({sz//1024}KB)"
        if _cmd_exists('import'):
            subprocess.run(['import', '-window', 'root', out], check=True, timeout=10)
            return f"Screenshot saved: {out}"
        if _IS_MAC and _cmd_exists('screencapture'):
            subprocess.run(['screencapture', '-x', out], check=True, timeout=10)
            return f"Screenshot saved: {out}"
        return "ERROR: No screenshot tool found (install scrot or pyautogui)"
    except Exception as e:
        return f"ERROR taking screenshot: {e}"

def tool_analyze_image(image_path: str,
                       prompt: str = 'Describe this image in detail.') -> str:
    """Analyze an image using Gemini Vision. Returns description."""
    gkey = os.environ.get('GEMINI_API_KEY', '')
    if not gkey:
        return "ERROR: GEMINI_API_KEY required for image analysis"
    p = Path(image_path)
    if not p.exists():
        return f"ERROR: File not found: {image_path}"
    if p.stat().st_size < 100:
        return "ERROR: Image file is too small or corrupt"
    try:
        img_b64 = base64.b64encode(p.read_bytes()).decode()
        ext     = p.suffix.lower().lstrip('.')
        mime    = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png',
                   'gif':'image/gif','webp':'image/webp','bmp':'image/bmp'}.get(ext, 'image/png')
        models  = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-2.0-flash']
        base_url = "https://generativelanguage.googleapis.com/v1beta"
        headers  = {"Content-Type": "application/json"}
        if not gkey.startswith('AI'):
            headers['X-goog-api-key'] = gkey
        for model in models:
            url  = (f"{base_url}/models/{model}:generateContent"
                    + (f"?key={gkey}" if gkey.startswith('AI') else ""))
            body = {"contents": [{"role": "user", "parts": [
                {"inlineData": {"mimeType": mime, "data": img_b64}},
                {"text": prompt},
            ]}], "generationConfig": {"maxOutputTokens": 4096}}
            for attempt in range(3):
                try:
                    resp = _http_post(url, headers, body, timeout=90)
                    if "error" in resp:
                        err_code = resp["error"].get("code", 0)
                        if err_code == 429:
                            time.sleep(3 * (attempt + 1))
                            continue
                        break
                    parts = resp.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    text  = "".join(x.get("text", "") for x in parts if "text" in x)
                    if text.strip():
                        return text
                except urllib.error.HTTPError as he:
                    if he.code == 429:
                        time.sleep(3 * (attempt + 1))
                        continue
                    break
                except Exception:
                    break
        return "ERROR: Vision analysis failed on all models"
    except Exception as e:
        return f"ERROR: {e}"

def tool_analyze_screenshot(prompt: str = 'Describe everything visible on screen in detail. Include all text, buttons, windows, coordinates of UI elements.') -> str:
    """Take a screenshot then analyze it with Gemini Vision."""
    path = f"/tmp/devin_screen_{int(time.time())}.png"
    result = tool_screenshot(path)
    if result.startswith('ERROR:'):
        return result
    return tool_analyze_image(path, prompt)

def tool_find_on_screen(element: str) -> str:
    """Take a screenshot and use vision to find pixel coordinates of a UI element."""
    prompt = (f"I need to find '{element}' on the screen. "
              f"Look at this screenshot carefully and return the CENTER pixel coordinates "
              f"(x, y) of '{element}'. "
              f"Format: X=<number> Y=<number>. "
              f"If not found, say 'NOT FOUND'. Be precise.")
    return tool_analyze_screenshot(prompt)

def tool_wait_for_window(title: str, timeout: int = 10) -> str:
    """Wait until a window with given title appears. Returns success or timeout."""
    if not _HAS_DISPLAY:
        return "ERROR: No display"
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = tool_list_windows()
        if title.lower() in result.lower():
            return f"Window found: {title}"
        time.sleep(0.5)
    return f"Timeout: window '{title}' not found after {timeout}s"

# ── Mouse control ─────────────────────────────────────────────────────────────

def _require_display() -> Optional[str]:
    if not _HAS_DISPLAY:
        return "ERROR: No display available (headless environment)"
    return None

def tool_mouse_move(x: int, y: int) -> str:
    err = _require_display()
    if err: return err
    try:
        if _HAS_PAG:
            _pag.moveTo(x, y, duration=0.15)
            return f"Mouse moved to ({x}, {y})"
        if _cmd_exists('xdotool'):
            subprocess.run(['xdotool', 'mousemove', str(x), str(y)], timeout=5)
            return f"Mouse moved to ({x}, {y})"
        return "ERROR: No mouse control tool (install pyautogui or xdotool)"
    except Exception as e:
        return f"ERROR: {e}"

def tool_mouse_click(x: int, y: int, button: str = 'left') -> str:
    err = _require_display()
    if err: return err
    try:
        if _HAS_PAG:
            btn_map = {'left': 'left', 'right': 'right', 'middle': 'middle'}
            _pag.click(x, y, button=btn_map.get(button, 'left'))
            return f"Clicked {button} at ({x}, {y})"
        if _cmd_exists('xdotool'):
            btn_num = {'left': '1', 'middle': '2', 'right': '3'}.get(button, '1')
            subprocess.run(['xdotool', 'mousemove', str(x), str(y),
                            'click', btn_num], timeout=5)
            return f"Clicked {button} at ({x}, {y})"
        return "ERROR: No mouse control tool available"
    except Exception as e:
        return f"ERROR: {e}"

def tool_mouse_double_click(x: int, y: int) -> str:
    err = _require_display()
    if err: return err
    try:
        if _HAS_PAG:
            _pag.doubleClick(x, y)
            return f"Double-clicked at ({x}, {y})"
        if _cmd_exists('xdotool'):
            subprocess.run(['xdotool', 'mousemove', str(x), str(y),
                            'click', '--repeat', '2', '1'], timeout=5)
            return f"Double-clicked at ({x}, {y})"
        return "ERROR: No mouse control tool available"
    except Exception as e:
        return f"ERROR: {e}"

def tool_mouse_right_click(x: int, y: int) -> str:
    return tool_mouse_click(x, y, button='right')

def tool_mouse_drag(x1: int, y1: int, x2: int, y2: int) -> str:
    err = _require_display()
    if err: return err
    try:
        if _HAS_PAG:
            _pag.moveTo(x1, y1, duration=0.1)
            _pag.dragTo(x2, y2, duration=0.3, button='left')
            return f"Dragged from ({x1},{y1}) to ({x2},{y2})"
        if _cmd_exists('xdotool'):
            subprocess.run([
                'xdotool', 'mousemove', str(x1), str(y1),
                'mousedown', '1', 'mousemove', str(x2), str(y2), 'mouseup', '1'
            ], timeout=5)
            return f"Dragged from ({x1},{y1}) to ({x2},{y2})"
        return "ERROR: No drag control tool available"
    except Exception as e:
        return f"ERROR: {e}"

def tool_mouse_scroll(x: int, y: int, direction: str = 'down', amount: int = 3) -> str:
    err = _require_display()
    if err: return err
    try:
        if _HAS_PAG:
            dy = -amount if direction == 'down' else amount
            _pag.moveTo(x, y)
            _pag.scroll(dy)
            return f"Scrolled {direction} at ({x},{y})"
        if _cmd_exists('xdotool'):
            btn = '5' if direction == 'down' else '4'
            for _ in range(amount):
                subprocess.run(['xdotool', 'mousemove', str(x), str(y),
                                'click', btn], timeout=5)
            return f"Scrolled {direction} at ({x},{y})"
        return "ERROR: No scroll tool available"
    except Exception as e:
        return f"ERROR: {e}"

def tool_get_mouse_position() -> str:
    err = _require_display()
    if err: return err
    try:
        if _HAS_PAG:
            pos = _pag.position()
            return f"Mouse at ({pos.x}, {pos.y})"
        if _cmd_exists('xdotool'):
            r = subprocess.run(['xdotool', 'getmouselocation'],
                               capture_output=True, text=True, timeout=5)
            return r.stdout.strip()
        return "ERROR: No position tool available"
    except Exception as e:
        return f"ERROR: {e}"

# ── Keyboard control ──────────────────────────────────────────────────────────

def tool_keyboard_type(text: str) -> str:
    err = _require_display()
    if err: return err
    try:
        if _HAS_PAG:
            _pag.typewrite(text, interval=0.03)
            return f"Typed: {text[:100]}"
        if _cmd_exists('xdotool'):
            subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '30', text],
                           timeout=30)
            return f"Typed: {text[:100]}"
        return "ERROR: No keyboard type tool available"
    except Exception as e:
        return f"ERROR: {e}"

def tool_keyboard_press(key: str) -> str:
    err = _require_display()
    if err: return err
    try:
        if _HAS_PAG:
            _pag.press(key.lower())
            return f"Pressed key: {key}"
        if _cmd_exists('xdotool'):
            key_map = {
                'Return': 'Return', 'Enter': 'Return', 'Tab': 'Tab',
                'Escape': 'Escape', 'BackSpace': 'BackSpace', 'Delete': 'Delete',
                'Up': 'Up', 'Down': 'Down', 'Left': 'Left', 'Right': 'Right',
                'Home': 'Home', 'End': 'End', 'PageUp': 'Prior', 'PageDown': 'Next',
                'F1':'F1','F2':'F2','F3':'F3','F4':'F4','F5':'F5','F6':'F6',
                'F7':'F7','F8':'F8','F9':'F9','F10':'F10','F11':'F11','F12':'F12',
                'space': 'space', 'Space': 'space',
            }
            xkey = key_map.get(key, key)
            subprocess.run(['xdotool', 'key', xkey], timeout=5)
            return f"Pressed key: {key}"
        return "ERROR: No keyboard press tool available"
    except Exception as e:
        return f"ERROR: {e}"

def tool_keyboard_hotkey(keys: List[str]) -> str:
    """Press a key combination. keys = ['ctrl', 'c'] for Ctrl+C."""
    err = _require_display()
    if err: return err
    try:
        combo = '+'.join(keys)
        if _HAS_PAG:
            _pag.hotkey(*[k.lower() for k in keys])
            return f"Hotkey: {combo}"
        if _cmd_exists('xdotool'):
            key_norm = {'ctrl': 'ctrl', 'alt': 'alt', 'shift': 'shift',
                        'super': 'super', 'win': 'super',
                        'return': 'Return', 'enter': 'Return',
                        'tab': 'Tab', 'escape': 'Escape',
                        'backspace': 'BackSpace', 'delete': 'Delete',
                        'space': 'space'}
            xkeys = [key_norm.get(k.lower(), k) for k in keys]
            subprocess.run(['xdotool', 'key', '+'.join(xkeys)], timeout=5)
            return f"Hotkey: {combo}"
        return "ERROR: No hotkey tool available"
    except Exception as e:
        return f"ERROR: {e}"

def tool_click_and_type(x: int, y: int, text: str) -> str:
    r1 = tool_mouse_click(x, y)
    if r1.startswith('ERROR:'):
        return r1
    time.sleep(0.15)
    r2 = tool_keyboard_type(text)
    return f"{r1} | {r2}"

# ── Windows & Applications ────────────────────────────────────────────────────

def tool_get_screen_size() -> str:
    err = _require_display()
    if err: return err
    try:
        if _HAS_PAG:
            size = _pag.size()
            return f"{size.width}x{size.height}"
        if _cmd_exists('xdpyinfo'):
            r = subprocess.run(['xdpyinfo'], capture_output=True, text=True, timeout=5)
            m = re.search(r'dimensions:\s+(\d+x\d+)', r.stdout)
            return m.group(1) if m else "unknown"
        if _cmd_exists('xrandr'):
            r = subprocess.run(['xrandr', '--current'], capture_output=True, text=True, timeout=5)
            m = re.search(r'(\d+x\d+)\+0\+0', r.stdout)
            return m.group(1) if m else "unknown"
        return "unknown"
    except Exception as e:
        return f"ERROR: {e}"

def tool_list_windows() -> str:
    err = _require_display()
    if err: return err
    try:
        if _cmd_exists('wmctrl'):
            r = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, timeout=5)
            return r.stdout.strip() or "(no windows)"
        if _cmd_exists('xdotool'):
            r = subprocess.run(['xdotool', 'search', '--name', ''],
                               capture_output=True, text=True, timeout=5)
            wids = r.stdout.strip().splitlines()
            lines = []
            for wid in wids[:30]:
                r2 = subprocess.run(['xdotool', 'getwindowname', wid],
                                    capture_output=True, text=True, timeout=3)
                name = r2.stdout.strip()
                if name:
                    lines.append(f"{wid}  {name}")
            return '\n'.join(lines) or "(no windows)"
        return "ERROR: wmctrl or xdotool required to list windows"
    except Exception as e:
        return f"ERROR: {e}"

def tool_focus_window(title: str) -> str:
    err = _require_display()
    if err: return err
    try:
        if _cmd_exists('wmctrl'):
            subprocess.run(['wmctrl', '-a', title], timeout=5)
            return f"Focused window: {title}"
        if _cmd_exists('xdotool'):
            subprocess.run(['xdotool', 'search', '--name', title,
                            'windowfocus', '--sync'], timeout=5)
            return f"Focused window: {title}"
        return "ERROR: wmctrl or xdotool required"
    except Exception as e:
        return f"ERROR: {e}"

def tool_maximize_window() -> str:
    err = _require_display()
    if err: return err
    try:
        if _cmd_exists('wmctrl'):
            subprocess.run(['wmctrl', '-r', ':ACTIVE:', '-b',
                            'add,maximized_vert,maximized_horz'], timeout=5)
            return "Maximized active window"
        return tool_keyboard_hotkey(['super', 'Up'])
    except Exception as e:
        return f"ERROR: {e}"

def tool_minimize_window() -> str:
    err = _require_display()
    if err: return err
    try:
        if _cmd_exists('xdotool'):
            r = subprocess.run(['xdotool', 'getactivewindow', 'windowminimize'],
                               timeout=5, capture_output=True)
            return "Minimized active window"
        return tool_keyboard_hotkey(['super', 'Down'])
    except Exception as e:
        return f"ERROR: {e}"

def tool_open_application(name: str, wait_seconds: float = 1.5) -> str:
    """Launch an application by name and wait for it to start."""
    err = _require_display()
    if err: return err
    try:
        proc = subprocess.Popen(name, shell=True,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(wait_seconds)
        # Verify it's running
        r = subprocess.run(['pgrep', '-f', name.split()[0]],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return f"Opened {name} (pid={r.stdout.strip().split()[0] if r.stdout.strip() else '?'})"
        return f"Launched {name} (may still be starting)"
    except Exception as e:
        return f"ERROR: {e}"

def tool_open_terminal() -> str:
    """Open a terminal emulator."""
    err = _require_display()
    if err: return err
    for term in ['gnome-terminal', 'xterm', 'konsole', 'xfce4-terminal',
                 'alacritty', 'kitty', 'tilix']:
        if _cmd_exists(term):
            subprocess.Popen([term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
            return f"Opened terminal: {term}"
    return "ERROR: No terminal emulator found"

def tool_close_application(name: str) -> str:
    try:
        r = subprocess.run(['pkill', '-f', name], capture_output=True, text=True)
        return f"Closed application matching: {name}" if r.returncode == 0 else f"No process found: {name}"
    except Exception as e:
        return f"ERROR: {e}"

def tool_alt_tab() -> str:
    return tool_keyboard_hotkey(['alt', 'Tab'])

# ── Clipboard ─────────────────────────────────────────────────────────────────

def tool_clipboard_get() -> str:
    if _IS_MAC:
        try:
            r = subprocess.run(['pbpaste'], capture_output=True, text=True, timeout=5)
            return r.stdout or "(empty)"
        except Exception as e:
            return f"ERROR: {e}"
    if _IS_WIN:
        try:
            import ctypes
            ctypes.windll.user32.OpenClipboard(0)  # type: ignore
            handle = ctypes.windll.user32.GetClipboardData(13)  # type: ignore
            text = ctypes.c_char_p(handle).value
            ctypes.windll.user32.CloseClipboard()  # type: ignore
            return (text or b'').decode('utf-8', errors='replace')
        except Exception as e:
            return f"ERROR: {e}"
    for tool, args in [('xclip', ['-o', '-sel', 'clip']),
                       ('xsel', ['--clipboard', '--output']),
                       ('wl-paste', [])]:
        if _cmd_exists(tool):
            try:
                r = subprocess.run([tool] + args, capture_output=True, text=True, timeout=5)
                return r.stdout.strip() or "(empty clipboard)"
            except Exception:
                pass
    return "ERROR: No clipboard tool (install xclip or xsel)"

def tool_clipboard_set(text: str) -> str:
    if _IS_MAC:
        try:
            subprocess.run(['pbcopy'], input=text.encode(), timeout=5)
            return "Copied to clipboard."
        except Exception as e:
            return f"ERROR: {e}"
    if _IS_WIN:
        try:
            subprocess.run(['clip'], input=text.encode('utf-16'), timeout=5)
            return "Copied to clipboard."
        except Exception as e:
            return f"ERROR: {e}"
    for tool, args in [('xclip', ['-sel', 'clip']),
                       ('xsel', ['--clipboard', '--input']),
                       ('wl-copy', [])]:
        if _cmd_exists(tool):
            try:
                subprocess.run([tool] + args, input=text.encode(), timeout=5)
                return "Copied to clipboard."
            except Exception:
                pass
    return "ERROR: No clipboard tool (install xclip or xsel)"

# ── Voice ─────────────────────────────────────────────────────────────────────

def tool_speak(text: str) -> str:
    """Speak text via TTS. Falls back gracefully."""
    for tts in [
        lambda: subprocess.run(['espeak', text], timeout=60),
        lambda: subprocess.run(['festival', '--tts'], input=text.encode(), timeout=60),
        lambda: subprocess.run(['say', text], timeout=60),  # macOS
        lambda: subprocess.run(['spd-say', text], timeout=60),
    ]:
        try:
            tts()
            return f"Spoke: {text[:80]}"
        except FileNotFoundError:
            continue
        except Exception as e:
            return f"ERROR speaking: {e}"
    return "ERROR: No TTS engine (install espeak or festival)"

def tool_listen(timeout: int = 10) -> str:
    """Listen for voice input. Requires microphone and speech_recognition."""
    try:
        import speech_recognition as sr  # type: ignore
        r = sr.Recognizer()
        with sr.Microphone() as src:
            r.adjust_for_ambient_noise(src, duration=0.5)
            audio = r.listen(src, timeout=timeout, phrase_time_limit=15)
        text = r.recognize_google(audio)
        return f"Heard: {text}"
    except ImportError:
        return "ERROR: speech_recognition not installed (pip install SpeechRecognition)"
    except Exception as e:
        return f"ERROR listening: {e}"

# ── Memory ────────────────────────────────────────────────────────────────────

def tool_remember(fact: str, tags: str = '') -> str:
    return _remember(fact, tags)

def tool_recall(query: str = '') -> str:
    return _recall(query)

# ── System info ───────────────────────────────────────────────────────────────

def tool_get_system_info() -> str:
    lines = [
        f"OS:       {platform.system()} {platform.release()} {platform.machine()}",
        f"Python:   {platform.python_version()}",
        f"Display:  {'yes ('+os.environ.get('DISPLAY','')+')' if _HAS_DISPLAY else 'headless'}",
        f"Platform: {_PLATFORM}",
    ]
    for cmd, label in [('nproc', 'CPUs'), ('hostname', 'Host')]:
        try:
            r = subprocess.run([cmd], capture_output=True, text=True, timeout=3)
            lines.append(f"{label}:     {r.stdout.strip()}")
        except Exception:
            pass
    try:
        r = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=3)
        lines.append(f"Memory:\n{r.stdout.strip()}")
    except Exception:
        pass
    try:
        r = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=3)
        lines.append(f"Disk:\n{r.stdout.strip()}")
    except Exception:
        pass
    return '\n'.join(lines)

def tool_get_system_metrics() -> str:
    """CPU, RAM, disk, network usage."""
    lines = []
    try:
        r = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=5)
        cpu_line = next((l for l in r.stdout.splitlines() if '%Cpu' in l), '')
        if cpu_line: lines.append(f"CPU: {cpu_line.strip()}")
    except Exception:
        pass
    try:
        r = subprocess.run(['free', '-m'], capture_output=True, text=True, timeout=3)
        lines.append(f"RAM:\n{r.stdout.strip()}")
    except Exception:
        pass
    try:
        r = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=3)
        lines.append(f"Disk:\n{r.stdout.strip()}")
    except Exception:
        pass
    return '\n'.join(lines) or tool_get_system_info()

# ── Task completion ───────────────────────────────────────────────────────────

def tool_task_complete(result: str) -> str:
    return f"TASK_COMPLETE:{result}"

# ── Browser automation (Selenium/Playwright/fallback) ────────────────────────

def tool_browser_start(headless: bool = False) -> str:
    """Start a browser session for automation. Uses Selenium → Playwright → fallback."""
    global _browser_instance
    if _browser_mod is None:
        return "ERROR: browser module not available"
    try:
        cls = getattr(_browser_mod, 'BrowserAutomation', None)
        if cls:
            _browser_instance = cls(headless=bool(headless))
            return _browser_instance.start()
        return "ERROR: BrowserAutomation class not found"
    except Exception as e:
        return f"ERROR: {e}"

def tool_browser_navigate(url: str) -> str:
    """Navigate browser to a URL."""
    global _browser_instance
    if _browser_instance is None:
        r = tool_browser_start()
        if r.startswith('ERROR'):
            return r
    try:
        return _browser_instance.navigate(url)
    except Exception as e:
        return f"ERROR: {e}"

def tool_browser_click(selector: str) -> str:
    """Click an element in the browser by CSS selector or text."""
    global _browser_instance
    if _browser_instance is None:
        return "ERROR: browser not started. Call browser_start first."
    try:
        return _browser_instance.click(selector)
    except Exception as e:
        return f"ERROR: {e}"

def tool_browser_type(selector: str, text: str) -> str:
    """Type text into a browser input field."""
    global _browser_instance
    if _browser_instance is None:
        return "ERROR: browser not started."
    try:
        return _browser_instance.type_text(selector, text)
    except Exception as e:
        return f"ERROR: {e}"

def tool_browser_get_text(selector: str = '') -> str:
    """Get page text or text of an element by CSS selector."""
    global _browser_instance
    if _browser_instance is None:
        return "ERROR: browser not started."
    try:
        fn = getattr(_browser_instance, 'get_text', None) or getattr(_browser_instance, 'page_source', None)
        if callable(fn):
            return str(fn(selector) if selector else fn())[:4000]
        return "ERROR: get_text not available"
    except Exception as e:
        return f"ERROR: {e}"

def tool_browser_screenshot(path: str = '') -> str:
    """Take a screenshot of the current browser state."""
    global _browser_instance
    if _browser_instance is None:
        return "ERROR: browser not started."
    try:
        fn = getattr(_browser_instance, 'screenshot', None)
        if callable(fn):
            return str(fn(path) if path else fn())
        return "ERROR: screenshot not available"
    except Exception as e:
        return f"ERROR: {e}"

def tool_browser_close() -> str:
    """Close the browser session."""
    global _browser_instance
    if _browser_instance is None:
        return "Browser was not running."
    try:
        fn = getattr(_browser_instance, 'close', None) or getattr(_browser_instance, 'quit', None)
        if callable(fn):
            fn()
        _browser_instance = None
        return "Browser closed."
    except Exception as e:
        _browser_instance = None
        return f"Closed (with error): {e}"

def tool_browser_execute_js(script: str) -> str:
    """Execute JavaScript in the browser."""
    global _browser_instance
    if _browser_instance is None:
        return "ERROR: browser not started."
    try:
        fn = getattr(_browser_instance, 'execute_js', None) or getattr(_browser_instance, 'execute_script', None)
        if callable(fn):
            return str(fn(script))
        # Try direct driver
        driver = getattr(_browser_instance, '_driver', None)
        if driver:
            return str(driver.execute_script(script))
        return "ERROR: execute_js not available"
    except Exception as e:
        return f"ERROR: {e}"

# ── HTTP request (generic) ────────────────────────────────────────────────────

def tool_http_request(url: str, method: str = 'GET', headers: str = '',
                      body: str = '', timeout: int = 30) -> str:
    """Make a raw HTTP request. headers/body as JSON strings."""
    try:
        hdrs = json.loads(headers) if headers.strip() else {}
        data = body.encode() if body else None
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method.upper())
        with urllib.request.urlopen(req, timeout=timeout) as r:
            content = r.read().decode('utf-8', errors='replace')
            return f"Status: {r.status}\n{content[:4000]}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:1000]}"
    except Exception as e:
        return f"ERROR: {e}"

# ── JSON / data processing ────────────────────────────────────────────────────

def tool_parse_json(text: str, path: str = '') -> str:
    """Parse JSON text, optionally extract a dot-path value (e.g. 'data.items.0.name')."""
    try:
        data = json.loads(text)
        if not path:
            return json.dumps(data, indent=2)[:4000]
        parts = path.split('.')
        for p in parts:
            if isinstance(data, list):
                data = data[int(p)]
            else:
                data = data[p]
        return json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data)
    except Exception as e:
        return f"ERROR: {e}"

# ── Code analysis ─────────────────────────────────────────────────────────────

def tool_analyze_code(path: str, question: str = '') -> str:
    """Read a source file and provide stats: lines, functions, classes, imports."""
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return f"ERROR: file not found: {path}"
        code = p.read_text(errors='replace')
        lines = code.splitlines()
        funcs   = len(re.findall(r'^\s*def\s+\w+', code, re.M))
        classes = len(re.findall(r'^\s*class\s+\w+', code, re.M))
        imports = len(re.findall(r'^(?:import|from)\s+', code, re.M))
        return (f"File:    {path}\n"
                f"Lines:   {len(lines)}\n"
                f"Functions: {funcs}\n"
                f"Classes:   {classes}\n"
                f"Imports:   {imports}\n"
                f"\nFirst 30 lines:\n" +
                '\n'.join(f"{i+1:4d}  {l}" for i, l in enumerate(lines[:30])))
    except Exception as e:
        return f"ERROR: {e}"

# ── Git advanced ──────────────────────────────────────────────────────────────

def tool_git_advanced(subcommand: str, repo_path: str = '') -> str:
    """Run git subcommands: status, diff, log, branch, stash, rebase, etc."""
    cwd = repo_path or str(_ROOT)
    safe_cmds = {'status', 'diff', 'log', 'branch', 'stash', 'show', 'tag',
                 'remote', 'fetch', 'pull', 'push', 'add', 'commit', 'checkout',
                 'merge', 'rebase', 'reset', 'clean', 'cherry-pick'}
    first = subcommand.split()[0] if subcommand.split() else ''
    if first not in safe_cmds:
        return f"ERROR: unsupported git subcommand {first!r}"
    return tool_execute_shell(f"git {subcommand}", cwd=cwd, timeout=60)

# ── Devin module call ─────────────────────────────────────────────────────────

def tool_devin_module(module: str, action: str, params: str = '') -> str:
    """
    Call into Devin's built-in modules.
    module: voice | os_auto | memory | integration_hub
    action: depends on module (e.g. 'speak', 'take_screenshot', 'save_fact', 'aia.run')
    params: JSON string of parameters
    """
    try:
        p = json.loads(params) if params.strip() else {}
    except Exception:
        p = {'value': params}

    if module == 'voice':
        if _voice_mod is None:
            return "voice module not loaded"
        if action == 'speak':
            fn = getattr(_voice_mod, 'speak', None)
            return str(fn(p.get('text', ''))) if fn else "speak not available"
        if action == 'listen':
            fn = getattr(_voice_mod, 'listen', None)
            return str(fn()) if fn else "listen not available"
        return f"voice: unknown action {action}"

    elif module == 'os_auto':
        if _os_auto_mod is None:
            return "os_automation module not loaded"
        fn = getattr(_os_auto_mod, action, None)
        if fn is None:
            return f"os_automation has no function {action!r}"
        try:
            return str(fn(**p))
        except Exception as e:
            return f"ERROR: {e}"

    elif module == 'memory':
        if _pmem is None:
            return "persistent_memory module not loaded"
        if action == 'save':
            _pmem.save_fact(p.get('key',''), p.get('value',''),
                            category=p.get('category','general'))
            return f"Saved: {p.get('key','')}"
        if action == 'get':
            fact = _pmem.get_fact(p.get('key',''))
            return str(fact) if fact else "Not found"
        if action == 'search':
            results = _pmem.search_facts(p.get('query',''))
            return json.dumps(results[:10], default=str)
        return f"memory: unknown action {action}"

    elif module == 'integration_hub':
        if _hub_mod is None:
            return "integration_hub module not loaded"
        # Actions: 'aia.run', 'jarvis.execute', 'cheetah.tools', etc.
        parts = action.split('.', 1)
        cls_name = parts[0]
        method   = parts[1] if len(parts) > 1 else ''
        cls_map = {
            'aia':     'AIAIntegration',
            'jarvis':  'JarvisIntegration',
            'cheetah': 'CheetahClawsIntegration',
        }
        cls_name_real = cls_map.get(cls_name, cls_name)
        cls = getattr(_hub_mod, cls_name_real, None)
        if cls is None:
            return f"integration_hub: no class {cls_name_real!r}"
        instance = cls()
        fn = getattr(instance, method, None)
        if fn is None:
            return f"{cls_name_real} has no method {method!r}"
        try:
            arg = p.get('arg', p.get('task', p.get('command', '')))
            return str(fn(arg) if arg else fn())
        except Exception as e:
            return f"ERROR: {e}"

    return f"Unknown module: {module}. Use: voice|os_auto|memory|integration_hub"

# ── List integrations ─────────────────────────────────────────────────────────

def tool_list_integrations() -> str:
    """List all loaded Devin modules and their status."""
    status = _modules_status()
    lines = ["Devin Integration Status:", "─" * 36]
    for mod, loaded in status.items():
        icon = '✓' if loaded else '✗'
        lines.append(f"  {icon} {mod}")
    # External repos
    ext_dir = _ROOT / 'external'
    if ext_dir.exists():
        repos = [d.name for d in sorted(ext_dir.iterdir()) if d.is_dir()]
        lines.append(f"\nExternal repos ({len(repos)}): " + ', '.join(repos[:15]))
    # Module files
    if _MODULES_DIR.exists():
        mods = [f.stem for f in sorted(_MODULES_DIR.glob('*.py')) if not f.name.startswith('_')]
        lines.append(f"\nmodules/ ({len(mods)}): " + ', '.join(mods[:20]))
    return '\n'.join(lines)

# ── Dynamic module discovery & execution ─────────────────────────────────────

def tool_run_devin_module(module_path: str, function_name: str, args_json: str = '') -> str:
    """
    Dynamically load and call any function from any Devin module file.
    module_path: relative to Devin root (e.g. 'modules/voice.py' or 'integrations/jarvis_tools.py')
    function_name: function to call in that module
    args_json: JSON object of keyword arguments (optional)
    """
    full_path = _ROOT / module_path
    if not full_path.exists():
        # Try modules/ prefix
        alt = _ROOT / 'modules' / module_path
        if alt.exists():
            full_path = alt
        else:
            return f"ERROR: module not found: {module_path}"
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location('_dyn_mod', str(full_path))
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = getattr(mod, function_name, None)
        if fn is None:
            avail = [n for n in dir(mod) if not n.startswith('_') and callable(getattr(mod,n))]
            return f"ERROR: {function_name!r} not found. Available: {', '.join(avail[:20])}"
        kwargs = json.loads(args_json) if args_json.strip() else {}
        result = fn(**kwargs)
        return str(result)
    except Exception as e:
        return f"ERROR loading/calling {module_path}.{function_name}: {e}"


def tool_discover_modules() -> str:
    """
    Discover all Python modules and their callable functions across the Devin codebase.
    Returns a summary of modules and their top-level functions.
    """
    summary = []
    search_dirs = [
        (_ROOT / 'modules',      'modules/'),
        (_ROOT / 'integrations', 'integrations/'),
        (_ROOT / 'ai_integrations', 'ai_integrations/'),
        (_ROOT / 'ai_core',      'ai_core/'),
    ]
    for base, prefix in search_dirs:
        if not base.exists():
            continue
        py_files = sorted(base.glob('*.py'))
        for f in py_files[:20]:
            if f.name.startswith('_'): continue
            try:
                code = f.read_text(errors='replace')
                fns = re.findall(r'^def\s+(\w+)', code, re.M)[:8]
                classes = re.findall(r'^class\s+(\w+)', code, re.M)[:4]
                summary.append(f"{prefix}{f.name}: funcs=[{', '.join(fns)}]"
                               + (f" classes=[{', '.join(classes)}]" if classes else ''))
            except Exception:
                summary.append(f"{prefix}{f.name}: (unreadable)")
    if not summary:
        return "No modules discovered."
    return f"Discovered {len(summary)} modules:\n" + '\n'.join(summary)

# ── Note taking ───────────────────────────────────────────────────────────────

def tool_take_note(title: str, content: str) -> str:
    """Save a note to a markdown file in the notes/ directory."""
    notes_dir = _ROOT / 'notes'
    notes_dir.mkdir(exist_ok=True)
    safe = re.sub(r'[^\w\-]', '_', title)[:50]
    fname = notes_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe}.md"
    fname.write_text(f"# {title}\n\n{content}\n", encoding='utf-8')
    return f"Note saved: {fname}"

# ═══════════════════════════════════════════════════════════════════════════════
# TOOL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

TOOLS: Dict[str, Dict] = {
    # ── Reasoning ──────────────────────────────────────────────────────────────
    "think": {
        "fn": tool_think,
        "desc": "Record a reasoning/planning step. Use before acting to think through the approach.",
        "params": {"thought": {"type": "string", "description": "Your detailed reasoning and plan"}},
        "required": ["thought"],
        "category": "reasoning",
    },

    # ── Web ────────────────────────────────────────────────────────────────────
    "web_search": {
        "fn": tool_web_search,
        "desc": "Search the web via DuckDuckGo. Returns titles and URLs.",
        "params": {
            "query": {"type": "string", "description": "Search query"},
            "num_results": {"type": "integer", "description": "Number of results (default 8)"},
        },
        "required": ["query"],
        "category": "web",
    },
    "web_fetch": {
        "fn": tool_web_fetch,
        "desc": "Fetch a web page and return readable text.",
        "params": {
            "url": {"type": "string", "description": "URL to fetch"},
            "max_chars": {"type": "integer", "description": "Max chars (default 8000)"},
        },
        "required": ["url"],
        "category": "web",
    },
    "open_browser": {
        "fn": tool_open_browser,
        "desc": "Open a URL in the default browser (requires display).",
        "params": {"url": {"type": "string", "description": "URL to open"}},
        "required": ["url"],
        "category": "browser",
    },

    # ── Shell / process ────────────────────────────────────────────────────────
    "execute_shell": {
        "fn": tool_execute_shell,
        "desc": "Run a shell command. Returns stdout+stderr.",
        "params": {
            "command": {"type": "string", "description": "Shell command"},
            "cwd": {"type": "string", "description": "Working directory (optional)"},
            "timeout": {"type": "integer", "description": "Timeout seconds (default 30)"},
            "background": {"type": "boolean", "description": "Run in background (default false)"},
        },
        "required": ["command"],
        "category": "shell",
    },
    "execute_python": {
        "fn": tool_execute_python,
        "desc": "Execute Python code and return output.",
        "params": {"code": {"type": "string", "description": "Python code to execute"}},
        "required": ["code"],
        "category": "shell",
    },
    "list_processes": {
        "fn": tool_list_processes,
        "desc": "List running processes. Optional filter string.",
        "params": {"filter_str": {"type": "string", "description": "Filter processes by name"}},
        "required": [],
        "category": "shell",
    },
    "kill_process": {
        "fn": tool_kill_process,
        "desc": "Terminate a process by PID.",
        "params": {"pid": {"type": "integer", "description": "Process ID"}},
        "required": ["pid"],
        "category": "shell",
    },
    "sleep": {
        "fn": tool_sleep,
        "desc": "Wait for N seconds. Use after launching apps or between GUI actions.",
        "params": {"seconds": {"type": "number", "description": "Seconds to wait (0.1-30)"}},
        "required": ["seconds"],
        "category": "shell",
    },

    # ── Files ──────────────────────────────────────────────────────────────────
    "read_file": {
        "fn": tool_read_file,
        "desc": "Read a file with line numbers.",
        "params": {
            "path": {"type": "string", "description": "File path"},
            "offset": {"type": "integer", "description": "Start line (0-indexed)"},
            "limit": {"type": "integer", "description": "Lines to read (default 200)"},
        },
        "required": ["path"],
        "category": "filesystem",
    },
    "write_file": {
        "fn": tool_write_file,
        "desc": "Write content to a file (creates parent dirs automatically).",
        "params": {
            "path": {"type": "string", "description": "File path"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
        "category": "filesystem",
    },
    "edit_file": {
        "fn": tool_edit_file,
        "desc": "Replace old_string with new_string in a file (first occurrence).",
        "params": {
            "path": {"type": "string", "description": "File path"},
            "old_string": {"type": "string", "description": "Text to find"},
            "new_string": {"type": "string", "description": "Replacement text"},
        },
        "required": ["path", "old_string", "new_string"],
        "category": "filesystem",
    },
    "delete_file": {
        "fn": tool_delete_file,
        "desc": "Delete a file.",
        "params": {"path": {"type": "string", "description": "File path"}},
        "required": ["path"],
        "category": "filesystem",
    },
    "list_files": {
        "fn": tool_list_files,
        "desc": "List files in a directory.",
        "params": {
            "path": {"type": "string", "description": "Directory (default: project root)"},
            "pattern": {"type": "string", "description": "Glob pattern (default: *)"},
            "recursive": {"type": "boolean", "description": "Recursive (default false)"},
        },
        "required": [],
        "category": "filesystem",
    },
    "create_directory": {
        "fn": tool_create_directory,
        "desc": "Create a directory (mkdir -p).",
        "params": {"path": {"type": "string", "description": "Directory path"}},
        "required": ["path"],
        "category": "filesystem",
    },
    "search_files": {
        "fn": tool_search_files,
        "desc": "Search file contents with grep.",
        "params": {
            "pattern": {"type": "string", "description": "Text pattern to search"},
            "path": {"type": "string", "description": "Directory to search (default: root)"},
        },
        "required": ["pattern"],
        "category": "filesystem",
    },
    "git_command": {
        "fn": tool_git_command,
        "desc": "Run a git command. args is everything after 'git', e.g. 'status' or 'log --oneline'.",
        "params": {
            "args": {"type": "string", "description": "git arguments"},
            "cwd": {"type": "string", "description": "Working directory"},
        },
        "required": ["args"],
        "category": "filesystem",
    },

    # ── Vision / Screenshot ────────────────────────────────────────────────────
    "screenshot": {
        "fn": tool_screenshot,
        "desc": "Take a screenshot of the current screen (requires display).",
        "params": {"save_path": {"type": "string", "description": "Save path (optional)"}},
        "required": [],
        "category": "vision",
    },
    "analyze_screenshot": {
        "fn": tool_analyze_screenshot,
        "desc": "OBSERVE: Take screenshot and analyze with AI. Use to see what's on screen, find UI elements, verify actions.",
        "params": {"prompt": {"type": "string", "description": "What to look for / analyze"}},
        "required": [],
        "category": "vision",
    },
    "analyze_image": {
        "fn": tool_analyze_image,
        "desc": "Analyze an existing image file with Gemini Vision.",
        "params": {
            "image_path": {"type": "string", "description": "Path to image file"},
            "prompt": {"type": "string", "description": "What to look for"},
        },
        "required": ["image_path"],
        "category": "vision",
    },
    "find_on_screen": {
        "fn": tool_find_on_screen,
        "desc": "Find a UI element on screen and get its pixel coordinates. Returns X=N Y=N.",
        "params": {"element": {"type": "string", "description": "Element to find, e.g. 'address bar', 'OK button', 'search box'"}},
        "required": ["element"],
        "category": "vision",
    },
    "wait_for_window": {
        "fn": tool_wait_for_window,
        "desc": "Wait until a window with given title appears (useful after launching apps).",
        "params": {
            "title": {"type": "string", "description": "Window title to wait for"},
            "timeout": {"type": "integer", "description": "Max seconds to wait (default 10)"},
        },
        "required": ["title"],
        "category": "vision",
    },

    # ── Mouse ──────────────────────────────────────────────────────────────────
    "mouse_move": {
        "fn": tool_mouse_move,
        "desc": "Move the mouse cursor to coordinates (requires display).",
        "params": {
            "x": {"type": "integer", "description": "X coordinate"},
            "y": {"type": "integer", "description": "Y coordinate"},
        },
        "required": ["x", "y"],
        "category": "mouse",
    },
    "mouse_click": {
        "fn": tool_mouse_click,
        "desc": "Click at coordinates. button: left/right/middle (requires display).",
        "params": {
            "x": {"type": "integer", "description": "X coordinate"},
            "y": {"type": "integer", "description": "Y coordinate"},
            "button": {"type": "string", "description": "left/right/middle (default: left)"},
        },
        "required": ["x", "y"],
        "category": "mouse",
    },
    "mouse_double_click": {
        "fn": tool_mouse_double_click,
        "desc": "Double-click at coordinates (requires display).",
        "params": {
            "x": {"type": "integer", "description": "X coordinate"},
            "y": {"type": "integer", "description": "Y coordinate"},
        },
        "required": ["x", "y"],
        "category": "mouse",
    },
    "mouse_right_click": {
        "fn": tool_mouse_right_click,
        "desc": "Right-click at coordinates (requires display).",
        "params": {
            "x": {"type": "integer", "description": "X coordinate"},
            "y": {"type": "integer", "description": "Y coordinate"},
        },
        "required": ["x", "y"],
        "category": "mouse",
    },
    "mouse_drag": {
        "fn": tool_mouse_drag,
        "desc": "Click-drag from (x1,y1) to (x2,y2) (requires display).",
        "params": {
            "x1": {"type": "integer", "description": "Start X"},
            "y1": {"type": "integer", "description": "Start Y"},
            "x2": {"type": "integer", "description": "End X"},
            "y2": {"type": "integer", "description": "End Y"},
        },
        "required": ["x1", "y1", "x2", "y2"],
        "category": "mouse",
    },
    "mouse_scroll": {
        "fn": tool_mouse_scroll,
        "desc": "Scroll at coordinates (requires display).",
        "params": {
            "x": {"type": "integer", "description": "X coordinate"},
            "y": {"type": "integer", "description": "Y coordinate"},
            "direction": {"type": "string", "description": "up or down (default: down)"},
            "amount": {"type": "integer", "description": "Scroll amount (default: 3)"},
        },
        "required": ["x", "y"],
        "category": "mouse",
    },
    "get_mouse_position": {
        "fn": tool_get_mouse_position,
        "desc": "Get current mouse cursor position.",
        "params": {},
        "required": [],
        "category": "mouse",
    },

    # ── Keyboard ───────────────────────────────────────────────────────────────
    "keyboard_type": {
        "fn": tool_keyboard_type,
        "desc": "Type text at the current cursor position (requires display).",
        "params": {"text": {"type": "string", "description": "Text to type"}},
        "required": ["text"],
        "category": "keyboard",
    },
    "keyboard_press": {
        "fn": tool_keyboard_press,
        "desc": "Press a single key: Return, Tab, Escape, F5, BackSpace, Up, Down, space, etc.",
        "params": {"key": {"type": "string", "description": "Key name"}},
        "required": ["key"],
        "category": "keyboard",
    },
    "keyboard_hotkey": {
        "fn": tool_keyboard_hotkey,
        "desc": "Press a key combination. Pass as JSON array: [\"ctrl\",\"c\"] or [\"ctrl\",\"shift\",\"t\"]",
        "params": {"keys": {"type": "string", "description": "JSON array of keys, e.g. [\"ctrl\",\"c\"]"}},
        "required": ["keys"],
        "category": "keyboard",
    },
    "click_and_type": {
        "fn": tool_click_and_type,
        "desc": "Click at coordinates then immediately type text (combined GUI input).",
        "params": {
            "x": {"type": "integer", "description": "X coordinate"},
            "y": {"type": "integer", "description": "Y coordinate"},
            "text": {"type": "string", "description": "Text to type"},
        },
        "required": ["x", "y", "text"],
        "category": "keyboard",
    },

    # ── Windows & Applications ─────────────────────────────────────────────────
    "get_screen_size": {
        "fn": tool_get_screen_size,
        "desc": "Get screen dimensions in pixels.",
        "params": {},
        "required": [],
        "category": "windows",
    },
    "list_windows": {
        "fn": tool_list_windows,
        "desc": "List all open windows (requires display + wmctrl/xdotool).",
        "params": {},
        "required": [],
        "category": "windows",
    },
    "focus_window": {
        "fn": tool_focus_window,
        "desc": "Bring a window to the foreground by title.",
        "params": {"title": {"type": "string", "description": "Window title (partial match)"}},
        "required": ["title"],
        "category": "windows",
    },
    "maximize_window": {
        "fn": tool_maximize_window,
        "desc": "Maximize the active window.",
        "params": {},
        "required": [],
        "category": "windows",
    },
    "minimize_window": {
        "fn": tool_minimize_window,
        "desc": "Minimize the active window.",
        "params": {},
        "required": [],
        "category": "windows",
    },
    "open_application": {
        "fn": tool_open_application,
        "desc": "Launch an application (e.g. 'firefox', 'code', 'gnome-terminal', 'gedit'). Waits for it to start.",
        "params": {
            "name": {"type": "string", "description": "Application name or command"},
            "wait_seconds": {"type": "number", "description": "Seconds to wait after launch (default 1.5)"},
        },
        "required": ["name"],
        "category": "applications",
    },
    "open_terminal": {
        "fn": tool_open_terminal,
        "desc": "Open a terminal emulator window.",
        "params": {},
        "required": [],
        "category": "applications",
    },
    "close_application": {
        "fn": tool_close_application,
        "desc": "Close/kill an application by name.",
        "params": {"name": {"type": "string", "description": "Application name"}},
        "required": ["name"],
        "category": "applications",
    },
    "alt_tab": {
        "fn": tool_alt_tab,
        "desc": "Switch to the previous window (Alt+Tab).",
        "params": {},
        "required": [],
        "category": "windows",
    },

    # ── Clipboard ──────────────────────────────────────────────────────────────
    "clipboard_get": {
        "fn": tool_clipboard_get,
        "desc": "Read the system clipboard contents.",
        "params": {},
        "required": [],
        "category": "clipboard",
    },
    "clipboard_set": {
        "fn": tool_clipboard_set,
        "desc": "Write text to the system clipboard.",
        "params": {"text": {"type": "string", "description": "Text to copy"}},
        "required": ["text"],
        "category": "clipboard",
    },

    # ── Voice ──────────────────────────────────────────────────────────────────
    "speak": {
        "fn": tool_speak,
        "desc": "Speak text aloud using TTS (espeak/festival/say).",
        "params": {"text": {"type": "string", "description": "Text to speak"}},
        "required": ["text"],
        "category": "voice",
    },
    "listen": {
        "fn": tool_listen,
        "desc": "Listen for voice input and return transcript (requires microphone + SpeechRecognition).",
        "params": {"timeout": {"type": "integer", "description": "Timeout seconds (default 10)"}},
        "required": [],
        "category": "voice",
    },

    # ── Memory ─────────────────────────────────────────────────────────────────
    "remember": {
        "fn": tool_remember,
        "desc": "Save a fact to persistent memory across sessions.",
        "params": {
            "fact": {"type": "string", "description": "Fact to remember"},
            "tags": {"type": "string", "description": "Optional comma-separated tags"},
        },
        "required": ["fact"],
        "category": "memory",
    },
    "recall": {
        "fn": tool_recall,
        "desc": "Retrieve memories. Optional query to filter results.",
        "params": {"query": {"type": "string", "description": "Search query (optional)"}},
        "required": [],
        "category": "memory",
    },

    # ── System ─────────────────────────────────────────────────────────────────
    "get_system_info": {
        "fn": tool_get_system_info,
        "desc": "Get OS, Python, CPU, RAM, disk info.",
        "params": {},
        "required": [],
        "category": "system",
    },
    "get_system_metrics": {
        "fn": tool_get_system_metrics,
        "desc": "Get real-time CPU, RAM, disk usage.",
        "params": {},
        "required": [],
        "category": "system",
    },

    # ── Completion ─────────────────────────────────────────────────────────────
    "task_complete": {
        "fn": tool_task_complete,
        "desc": "Signal that the task is FULLY done and verified. Call ONLY when everything is complete.",
        "params": {"result": {"type": "string", "description": "Summary of what was accomplished"}},
        "required": ["result"],
        "category": "control",
    },

    # ── Browser automation ─────────────────────────────────────────────────────
    "browser_start": {
        "fn": tool_browser_start,
        "desc": "Start a browser session (Selenium/Playwright). Use headless=true for no window.",
        "params": {"headless": {"type": "boolean", "description": "Run headlessly (default false)"}},
        "required": [],
        "category": "browser",
    },
    "browser_navigate": {
        "fn": tool_browser_navigate,
        "desc": "Navigate browser to a URL. Starts browser automatically if needed.",
        "params": {"url": {"type": "string", "description": "URL to navigate to"}},
        "required": ["url"],
        "category": "browser",
    },
    "browser_click": {
        "fn": tool_browser_click,
        "desc": "Click a browser element by CSS selector (e.g. '#btn', '.nav a', 'button[type=submit]').",
        "params": {"selector": {"type": "string", "description": "CSS selector or element text"}},
        "required": ["selector"],
        "category": "browser",
    },
    "browser_type": {
        "fn": tool_browser_type,
        "desc": "Type text into a browser input field.",
        "params": {
            "selector": {"type": "string", "description": "CSS selector for input field"},
            "text":     {"type": "string", "description": "Text to type"},
        },
        "required": ["selector", "text"],
        "category": "browser",
    },
    "browser_get_text": {
        "fn": tool_browser_get_text,
        "desc": "Get visible text from current page or a specific element.",
        "params": {"selector": {"type": "string", "description": "CSS selector (optional, empty = full page)"}},
        "required": [],
        "category": "browser",
    },
    "browser_screenshot": {
        "fn": tool_browser_screenshot,
        "desc": "Take a screenshot of the current browser state.",
        "params": {"path": {"type": "string", "description": "Save path (optional)"}},
        "required": [],
        "category": "browser",
    },
    "browser_execute_js": {
        "fn": tool_browser_execute_js,
        "desc": "Execute JavaScript code in the browser and return result.",
        "params": {"script": {"type": "string", "description": "JavaScript to execute"}},
        "required": ["script"],
        "category": "browser",
    },
    "browser_close": {
        "fn": tool_browser_close,
        "desc": "Close the browser session.",
        "params": {},
        "required": [],
        "category": "browser",
    },

    # ── Network / HTTP ─────────────────────────────────────────────────────────
    "http_request": {
        "fn": tool_http_request,
        "desc": "Make a raw HTTP request (GET/POST/PUT/DELETE). Returns status + body.",
        "params": {
            "url":     {"type": "string", "description": "Full URL"},
            "method":  {"type": "string", "description": "HTTP method (default GET)"},
            "headers": {"type": "string", "description": "JSON object of headers (optional)"},
            "body":    {"type": "string", "description": "Request body string (optional)"},
            "timeout": {"type": "integer", "description": "Timeout seconds (default 30)"},
        },
        "required": ["url"],
        "category": "network",
    },

    # ── Data processing ────────────────────────────────────────────────────────
    "parse_json": {
        "fn": tool_parse_json,
        "desc": "Parse JSON and optionally extract a value via dot-path (e.g. 'data.items.0.name').",
        "params": {
            "text": {"type": "string", "description": "JSON string to parse"},
            "path": {"type": "string", "description": "Dot-path to extract (optional)"},
        },
        "required": ["text"],
        "category": "data",
    },

    # ── Code analysis ──────────────────────────────────────────────────────────
    "analyze_code": {
        "fn": tool_analyze_code,
        "desc": "Analyze a source file: line count, functions, classes, imports, preview.",
        "params": {
            "path":     {"type": "string", "description": "Path to source file"},
            "question": {"type": "string", "description": "Optional question about the code"},
        },
        "required": ["path"],
        "category": "code",
    },

    # ── Git advanced ───────────────────────────────────────────────────────────
    "git_advanced": {
        "fn": tool_git_advanced,
        "desc": "Run git subcommands: 'log --oneline -10', 'diff HEAD', 'branch -a', 'stash list', etc.",
        "params": {
            "subcommand": {"type": "string", "description": "Git subcommand and args"},
            "repo_path":  {"type": "string", "description": "Repository path (default: Devin root)"},
        },
        "required": ["subcommand"],
        "category": "git",
    },

    # ── Devin module integration ───────────────────────────────────────────────
    "devin_module": {
        "fn": tool_devin_module,
        "desc": "Call into Devin's built-in modules. module: voice|os_auto|memory|integration_hub. "
                "Examples: module=voice,action=speak,params={\"text\":\"hello\"} | "
                "module=integration_hub,action=jarvis.execute,params={\"command\":\"what time is it\"}",
        "params": {
            "module": {"type": "string", "description": "Module name: voice|os_auto|memory|integration_hub"},
            "action": {"type": "string", "description": "Action/method to call"},
            "params": {"type": "string", "description": "JSON params for the action (optional)"},
        },
        "required": ["module", "action"],
        "category": "integrations",
    },

    # ── List integrations ──────────────────────────────────────────────────────
    "list_integrations": {
        "fn": tool_list_integrations,
        "desc": "List all loaded Devin modules, external repos, and integration status.",
        "params": {},
        "required": [],
        "category": "integrations",
    },

    # ── Note taking ────────────────────────────────────────────────────────────
    "take_note": {
        "fn": tool_take_note,
        "desc": "Save a titled note as a markdown file in notes/ directory.",
        "params": {
            "title":   {"type": "string", "description": "Note title"},
            "content": {"type": "string", "description": "Note content (markdown)"},
        },
        "required": ["title", "content"],
        "category": "notes",
    },

    # ── Dynamic Devin module access ────────────────────────────────────────────
    "run_devin_module": {
        "fn": tool_run_devin_module,
        "desc": "Dynamically load and call any function from any Devin module file. "
                "E.g. module_path='modules/voice.py', function_name='speak', args_json='{\"text\":\"hello\"}'",
        "params": {
            "module_path":   {"type": "string", "description": "Relative path to .py file from Devin root"},
            "function_name": {"type": "string", "description": "Function name to call"},
            "args_json":     {"type": "string", "description": "JSON object of keyword arguments (optional)"},
        },
        "required": ["module_path", "function_name"],
        "category": "integrations",
    },
    "discover_modules": {
        "fn": tool_discover_modules,
        "desc": "Discover all Python modules and their functions across the Devin codebase (modules/, integrations/, ai_integrations/, ai_core/).",
        "params": {},
        "required": [],
        "category": "integrations",
    },
}

def _dispatch_tool(name: str, args: dict) -> str:
    if name not in TOOLS:
        return f"ERROR: unknown tool {name!r}. Available: {', '.join(list(TOOLS)[:10])}..."
    fn = TOOLS[name]["fn"]
    # keyboard_hotkey passes keys as JSON string sometimes
    if name == 'keyboard_hotkey' and 'keys' in args:
        k = args['keys']
        if isinstance(k, str):
            try:
                args['keys'] = json.loads(k)
            except Exception:
                args['keys'] = [x.strip() for x in k.split(',')]
    try:
        return str(fn(**args))
    except TypeError as e:
        return f"ERROR calling {name}: {e}"
    except Exception as e:
        return f"ERROR in {name}: {e}"

# ═══════════════════════════════════════════════════════════════════════════════
# AI PROVIDERS
# ═══════════════════════════════════════════════════════════════════════════════

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
            "parameters": {"type": "OBJECT", "properties": p, "required": t["required"]},
        }
    return [{"functionDeclarations": list(props.values())}]

def _tool_schema_claude() -> list:
    return [{"name": n, "description": t["desc"],
             "input_schema": {
                 "type": "object",
                 "properties": {k: {"type": v["type"], "description": v["description"]}
                                for k, v in t["params"].items()},
                 "required": t["required"],
             }} for n, t in TOOLS.items()]

def _tool_schema_openai() -> list:
    return [{"type": "function", "function": {
        "name": n, "description": t["desc"],
        "parameters": {
            "type": "object",
            "properties": {k: {"type": v["type"], "description": v["description"]}
                           for k, v in t["params"].items()},
            "required": t["required"],
        }}} for n, t in TOOLS.items()]

# ─── Gemini ────────────────────────────────────────────────────────────────────

class GeminiProvider:
    BASE = "https://generativelanguage.googleapis.com/v1beta"
    FALLBACK_MODELS = [
        'gemini-3.6-flash',
        'gemini-2.5-flash',
        'gemini-2.5-pro',
        'gemini-2.0-flash',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
    ]

    def __init__(self, api_key: str, model: str = 'gemini-3.6-flash'):
        self.api_key = api_key
        self.model   = model
        self.name    = f"gemini/{model}"

    def _url(self, endpoint: str) -> str:
        if self.api_key.startswith('AI'):
            return f"{self.BASE}/models/{self.model}:{endpoint}?key={self.api_key}"
        return f"{self.BASE}/models/{self.model}:{endpoint}"

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json",
             "x-goog-api-client": "devin-agent/4.0 gl-python/3"}
        if not self.api_key.startswith('AI'):
            h['X-goog-api-key'] = self.api_key
        return h

    def call(self, messages: list, system: str = '') -> Tuple[str, List[dict]]:
        contents = []
        if system:
            contents += [
                {"role": "user",  "parts": [{"text": f"[System instructions]\n{system}"}]},
                {"role": "model", "parts": [{"text": "Understood. I'm ready to help."}]},
            ]
        for m in messages:
            role  = "model" if m["role"] == "assistant" else "user"
            parts = []
            if isinstance(m.get("content"), list):
                for blk in m["content"]:
                    t = blk.get("type", "")
                    if t == "tool_result":
                        parts.append({"text": f"[Tool result]\n{blk.get('content','')}"})
                    elif t == "tool_use":
                        parts.append({"text": f"[Called {blk['name']}({json.dumps(blk.get('input',{}))})]"})
                    else:
                        parts.append({"text": str(blk.get("text", ""))})
            else:
                parts.append({"text": str(m.get("content", ""))})
            if parts:
                # Merge consecutive same-role to avoid Gemini "turns" error
                if contents and contents[-1]["role"] == role:
                    contents[-1]["parts"].extend(parts)
                else:
                    contents.append({"role": role, "parts": parts})

        # Ensure we end with user turn
        if contents and contents[-1]["role"] == "model":
            contents.append({"role": "user", "parts": [{"text": "Continue."}]})

        body = {
            "contents": contents,
            "tools": _tool_schema_gemini(),
            "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.7},
        }

        models_to_try = [self.model] + [m for m in self.FALLBACK_MODELS if m != self.model]
        last_err = ""
        for model_name in models_to_try:
            self.model = model_name
            for attempt in range(4):
                try:
                    resp = _http_post(self._url("generateContent"),
                                      self._headers(), body, timeout=120)
                    if "error" in resp:
                        err = resp["error"]
                        code = err.get("code", 0)
                        msg  = err.get("message", "Gemini error")
                        if code == 429:
                            wait = 4 * (attempt + 1)
                            print(yellow(f"\r  ⏳ rate limited ({model_name}), retry in {wait}s…"),
                                  flush=True)
                            time.sleep(wait); continue
                        if code in (503, 429):
                            wait = 3 * (attempt + 1)
                            print(yellow(f"\r  ⏳ {model_name} busy, retry in {wait}s…"), flush=True)
                            time.sleep(wait); continue
                        last_err = f"{model_name}: {msg}"; break
                    cand  = resp.get("candidates", [{}])[0]
                    parts = cand.get("content", {}).get("parts", [])
                    text  = "".join(p.get("text", "") for p in parts if "text" in p)
                    calls = [{"name": p["functionCall"]["name"],
                              "args": p["functionCall"].get("args", {})}
                             for p in parts if "functionCall" in p]
                    self.name = f"gemini/{self.model}"
                    return text, calls
                except urllib.error.HTTPError as e:
                    body_txt = e.read().decode('utf-8', errors='replace')
                    if e.code == 429:
                        wait = 4 * (attempt + 1)
                        print(yellow(f"\r  ⏳ rate limited, retry in {wait}s…"), flush=True)
                        time.sleep(wait); continue
                    if e.code == 503:
                        wait = 5 * (attempt + 1)
                        print(yellow(f"\r  ⏳ 503 high demand, retry in {wait}s…"), flush=True)
                        time.sleep(wait); continue
                    if e.code in (404, 400):
                        last_err = f"{model_name}: HTTP {e.code}"
                        break
                    raise ValueError(f"Gemini HTTP {e.code}: {body_txt[:300]}")
                except Exception as e:
                    if 'timeout' in str(e).lower():
                        if attempt < 3:
                            print(yellow(f"\r  ⏳ timeout, retrying…"), flush=True)
                            time.sleep(3); continue
                    raise
        raise ValueError(f"Gemini: all models failed. Last: {last_err}")

# ─── Claude ────────────────────────────────────────────────────────────────────

class ClaudeProvider:
    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, model: str = 'claude-sonnet-4-6'):
        self.api_key = api_key
        self.model   = model
        self.name    = f"claude/{model}"

    def call(self, messages: list, system: str = '') -> Tuple[str, List[dict]]:
        hdrs = {"Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"}
        body: dict = {"model": self.model, "max_tokens": 8192,
                      "tools": _tool_schema_claude(), "messages": messages}
        if system:
            body["system"] = system
        for attempt in range(5):
            try:
                resp  = _http_post(self.URL, hdrs, body, timeout=120)
                text  = ""
                calls = []
                for blk in resp.get("content", []):
                    if blk.get("type") == "text":
                        text += blk.get("text", "")
                    elif blk.get("type") == "tool_use":
                        calls.append({"id": blk.get("id"),
                                      "name": blk["name"],
                                      "args": blk.get("input", {})})
                return text, calls
            except urllib.error.HTTPError as e:
                body_txt = e.read().decode('utf-8', errors='replace')
                if e.code in (429, 529):
                    wait = 4 * (attempt + 1)
                    print(yellow(f"\r  ⏳ Claude rate limited, retry in {wait}s…"), flush=True)
                    time.sleep(wait); continue
                raise ValueError(f"Claude HTTP {e.code}: {body_txt[:300]}")
        raise ValueError("Claude: max retries exceeded")

# ─── OpenAI ────────────────────────────────────────────────────────────────────

class OpenAIProvider:
    URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str = 'gpt-4o-mini'):
        self.api_key = api_key
        self.model   = model
        self.name    = f"openai/{model}"

    def call(self, messages: list, system: str = '') -> Tuple[str, List[dict]]:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, list):
                content = " ".join(str(b.get("text") or b.get("content") or "") for b in content)
            msgs.append({"role": m["role"], "content": content})

        body = {"model": self.model, "max_tokens": 4096,
                "tools": _tool_schema_openai(), "messages": msgs}
        hdrs = {"Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"}
        for attempt in range(5):
            try:
                resp  = _http_post(self.URL, hdrs, body, timeout=120)
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
                    wait = 4 * (attempt + 1)
                    print(yellow(f"\r  ⏳ OpenAI rate limited, retry in {wait}s…"), flush=True)
                    time.sleep(wait); continue
                raise ValueError(f"OpenAI HTTP {e.code}: {body_txt[:300]}")
        raise ValueError("OpenAI: max retries exceeded")

# ─── Provider selector ────────────────────────────────────────────────────────

def _pick_provider(name: str = '', model: str = ''):
    gk = os.environ.get('GEMINI_API_KEY', '')
    ak = os.environ.get('ANTHROPIC_API_KEY', '')
    ok = os.environ.get('OPENAI_API_KEY', '')

    if name in ('gemini', 'google'):
        if not gk: raise ValueError("GEMINI_API_KEY not set")
        return GeminiProvider(gk, model or 'gemini-3.6-flash')
    if name in ('claude', 'anthropic'):
        if not ak: raise ValueError("ANTHROPIC_API_KEY not set")
        return ClaudeProvider(ak, model or 'claude-sonnet-4-6')
    if name == 'openai':
        if not ok: raise ValueError("OPENAI_API_KEY not set")
        return OpenAIProvider(ok, model or 'gpt-4o-mini')

    if gk: return GeminiProvider(gk, model or 'gemini-3.6-flash')
    if ak: return ClaudeProvider(ak, model or 'claude-sonnet-4-6')
    if ok: return OpenAIProvider(ok, model or 'gpt-4o-mini')
    raise ValueError(
        "No API key found.\n"
        "  Set GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY in .env\n"
        "  Free key: https://aistudio.google.com/app/apikey")

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

_DISPLAY_NOTE = ("DISPLAY: AVAILABLE — mouse, keyboard, screenshot, and window tools work."
                 if _HAS_DISPLAY else
                 "DISPLAY: HEADLESS — GUI tools unavailable. Focus on shell/file/web tasks.")

SYSTEM_PROMPT = f"""\
You are Devin, an advanced OS-controlling AI agent.
You have {len(TOOLS)} tools: shell, files, web, mouse, keyboard, windows, apps,
screenshots, vision, clipboard, voice, memory, git, and more.
{_DISPLAY_NOTE}

## Core operating principle
You NEVER stop mid-task. You complete what you start or clearly explain what
is blocking completion. You are like a senior engineer: persistent, methodical,
and thorough.

## Conversation behavior
- In conversation (no tools needed): respond directly and helpfully, like a brilliant
  colleague. Be concise, informative, and natural.
- When given a task: execute it autonomously using tools until fully done.
- You can ask clarifying questions when requirements are genuinely ambiguous.
- Remember context from earlier in the conversation.

## Task execution loop
1. THINK — call `think` to plan the approach before acting
2. OBSERVE — use `analyze_screenshot` or `read_file` to understand current state
3. ACT — call the appropriate tool
4. VERIFY — check the result was what you expected
5. CONTINUE — keep going until task is fully complete
6. COMPLETE — call `task_complete` with a clear summary

## Error recovery rules
- If a tool returns ERROR: try an alternative approach. NEVER give up.
- If web_search fails: try web_fetch on a known URL directly.
- If a GUI action fails: take a screenshot first, then try again with correct coords.
- If an app isn't responding: check with list_windows, use sleep to wait.
- If a model fails: the system will auto-retry with a different model.
- Errors are INFORMATION, not stopping points.

## GUI control workflow (when display available)
1. `open_application("firefox")` + `sleep(2)` — launch and wait
2. `analyze_screenshot("Where is the address bar? Give exact pixel coordinates.")` — observe
3. `mouse_click(x, y)` — click address bar
4. `keyboard_hotkey(["ctrl","a"])` then `keyboard_type("url")` — type
5. `keyboard_press("Return")` — submit
6. `sleep(2)` + `analyze_screenshot("Did it navigate? What do I see?")` — verify

## Tool categories
reasoning: think
web: web_search, web_fetch, open_browser
shell: execute_shell, execute_python, list_processes, kill_process, sleep
files: read_file, write_file, edit_file, delete_file, list_files, create_directory, search_files, git_command
vision: screenshot, analyze_screenshot, analyze_image, find_on_screen, wait_for_window
mouse: mouse_move, mouse_click, mouse_double_click, mouse_right_click, mouse_drag, mouse_scroll, get_mouse_position
keyboard: keyboard_type, keyboard_press, keyboard_hotkey, click_and_type
windows: get_screen_size, list_windows, focus_window, maximize_window, minimize_window, alt_tab
apps: open_application, open_terminal, close_application
browser: browser_start, browser_navigate, browser_click, browser_type, browser_get_text, browser_screenshot, browser_execute_js, browser_close
clipboard: clipboard_get, clipboard_set
voice: speak, listen
memory: remember, recall
system: get_system_info, get_system_metrics
network: http_request
data: parse_json
code: analyze_code
git: git_advanced
integrations: devin_module, list_integrations, run_devin_module, discover_modules
notes: take_note
control: task_complete

## OS automation workflow (real user simulation)
For any GUI task, always follow: OBSERVE → UNDERSTAND → PLAN → ACT → VERIFY
Example — open Firefox and search:
1. open_application("firefox") + sleep(2)
2. screenshot() + analyze_screenshot("where is address bar? give exact X,Y coords")
3. mouse_click(x, y) + keyboard_hotkey(["ctrl","a"]) + keyboard_type("https://google.com") + keyboard_press("Return")
4. sleep(2) + screenshot() + analyze_screenshot("what loaded? was it successful?")
5. task_complete("searched for X in Firefox")

## Browser automation workflow (Selenium/Playwright)
For headless or programmatic browser tasks:
1. browser_start() [or browser_navigate(url) which auto-starts]
2. browser_navigate("https://example.com")
3. browser_click("#search") + browser_type("#search", "query") + browser_execute_js("document.forms[0].submit()")
4. browser_get_text() → parse results
5. browser_close()

## Full Devin codebase access
Use `discover_modules` to explore all available modules across the Devin codebase.
Use `run_devin_module` to call ANY function from ANY .py file in Devin's source tree.
Use `devin_module` for the built-in modules (voice, os_auto, memory, integration_hub).
Use `list_integrations` to see which modules are currently loaded.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# AGENTIC LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def _fmt_args(args: dict, maxlen: int = 100) -> str:
    parts = []
    for k, v in args.items():
        s = repr(v)
        if len(s) > maxlen:
            s = s[:maxlen] + '…'
        parts.append(f"{k}={s}")
    return ', '.join(parts)

def _print_tool_call(name: str, args: dict):
    icon = {
        'think': '💭', 'web_search': '🔍', 'web_fetch': '🌐',
        'execute_shell': '🖥', 'execute_python': '🐍',
        'read_file': '📖', 'write_file': '✏️', 'edit_file': '📝',
        'screenshot': '📷', 'analyze_screenshot': '👁',
        'find_on_screen': '🔎', 'mouse_click': '🖱', 'mouse_move': '➡',
        'keyboard_type': '⌨', 'keyboard_press': '⌨', 'keyboard_hotkey': '⌨',
        'open_application': '🚀', 'open_browser': '🌐',
        'remember': '🧠', 'recall': '🧠',
        'task_complete': '✅', 'speak': '🔊', 'listen': '🎤',
        'git_command': '🔀', 'sleep': '⏱',
    }.get(name, '▶')
    print(f"\n  {blue(icon)} {cyan(name)}({_fmt_args(args)})", flush=True)

def run_agent(task: str, provider, max_steps: int = 100,
              quiet: bool = False, conv_messages: Optional[List] = None) -> str:
    """
    Run the agentic loop.
    conv_messages: if provided, conversation history is preserved (REPL mode).
    """
    if conv_messages is not None:
        # Conversation mode — append task to existing history
        conv_messages.append({"role": "user", "content": task})
        messages = conv_messages
    else:
        # One-shot mode
        messages = [{"role": "user", "content": task}]

    final_result = ""
    step = 0
    consecutive_errors = 0
    MAX_ERRORS = 5  # retry up to this many consecutive provider errors

    if not quiet:
        print()
        print(_box(f"Task: {task[:72]}"))
        print(dim(f"Provider: {provider.name}  |  Tools: {len(TOOLS)}  |  Max steps: {max_steps}"))
        if not _HAS_DISPLAY:
            print(dim("⚠  Headless: GUI tools will return errors (need display)"))
        print(_hr())

    while step < max_steps:
        step += 1

        if not quiet:
            label = f"step {step}/{max_steps} · {provider.name}"
            print(f"\r  {dim(next(_SPIN))} {dim(label)}  ", end='', flush=True)

        try:
            text, calls = provider.call(messages, system=SYSTEM_PROMPT)
            consecutive_errors = 0  # reset on success
        except KeyboardInterrupt:
            print(yellow("\n  ⚡ Interrupted"))
            break
        except Exception as e:
            consecutive_errors += 1
            err_str = str(e)
            if not quiet:
                print(red(f"\n  ⚠ Provider error ({consecutive_errors}/{MAX_ERRORS}): {err_str[:200]}"))

            if consecutive_errors >= MAX_ERRORS:
                if not quiet:
                    print(red("  Max consecutive errors reached. Stopping."))
                break

            # Exponential backoff before retry
            wait = 2 ** consecutive_errors
            if not quiet:
                print(dim(f"  Retrying in {wait}s…"))
            time.sleep(wait)
            continue

        # Print assistant text (clear spinner line first)
        if not quiet:
            print('\r' + ' ' * 60 + '\r', end='', flush=True)

        if text and text.strip():
            clean = re.sub(r'^\s*\(acting\)\s*', '', text.strip(), flags=re.I)
            if clean and not quiet:
                # Print with word wrap for long responses
                wrapped = textwrap.fill(clean, width=max(60, shutil.get_terminal_size((80,24)).columns - 10),
                                        subsequent_indent='         ')
                print(f"\n{bold(cyan('Devin'))}  {wrapped}")

        # Build assistant message
        if isinstance(provider, ClaudeProvider):
            blocks: List[dict] = []
            if text:
                blocks.append({"type": "text", "text": text})
            for c in calls:
                blocks.append({"type": "tool_use",
                                "id": c.get("id", f"t{step}_{c['name']}"),
                                "name": c["name"], "input": c["args"]})
            if blocks:
                messages.append({"role": "assistant", "content": blocks})
        else:
            if text or calls:
                messages.append({"role": "assistant", "content": text or ""})

        # No tool calls — model is done or wants to chat
        if not calls:
            if text.strip():
                final_result = text.strip()
                # In conversation mode, the response IS the result (no task_complete needed)
                if conv_messages is not None:
                    return final_result
            break

        # Execute tools
        tool_results = []
        for call in calls:
            name = call["name"]
            args = call["args"]

            if not quiet:
                _print_tool_call(name, args)

            result = _dispatch_tool(name, args)

            # Task complete?
            if name == "task_complete" or result.startswith("TASK_COMPLETE:"):
                final_result = result.replace("TASK_COMPLETE:", "").strip()
                if not quiet:
                    print(f"  {green('←')} {dim(str(result)[:300])}")
                    print()
                    print(_hr())
                    print(green(bold("✅  Task complete")))
                    if final_result:
                        print(textwrap.fill(final_result,
                                            width=shutil.get_terminal_size((80,24)).columns - 4))
                return final_result

            if not quiet:
                # Preview — first 300 chars, handle multi-line
                preview = str(result)[:400].replace('\n', ' ↵ ')
                colour = red if str(result).startswith('ERROR:') else dim
                print(f"  {dim('←')} {colour(preview)}")

            tool_results.append({
                "call_id": call.get("id", f"t{step}_{name}"),
                "name": name, "result": result,
            })

        # Feed tool results back
        if isinstance(provider, ClaudeProvider):
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tr["call_id"],
                 "content": tr["result"]}
                for tr in tool_results
            ]})
        elif isinstance(provider, OpenAIProvider):
            for tr in tool_results:
                messages.append({"role": "tool",
                                  "tool_call_id": tr["call_id"],
                                  "content": tr["result"]})
        else:
            combined = "\n\n".join(
                f"[Tool: {tr['name']}]\n{tr['result']}" for tr in tool_results)
            messages.append({"role": "user", "content": combined})

    if not final_result:
        final_result = "(task ended without explicit completion)"

    if not quiet:
        print()
        print(_hr())
        print(dim(f"Finished after {step} steps."))

    return final_result

# ═══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE REPL
# ═══════════════════════════════════════════════════════════════════════════════

_HELP = ""  # built lazily in _make_help()

def _make_help() -> str:
    return f"""
{bold('Devin')} — OS-controlling agentic AI

{bold('Usage')}
  Type naturally — ask questions, give tasks, have a conversation.
  Devin reasons and uses tools autonomously until the task is done.

{bold('Slash commands')}
  {cyan('/help')}                This help
  {cyan('/tools [category]')}    List tools (optional category filter)
  {cyan('/status')}              Show provider, model, keys, capabilities
  {cyan('/providers')}           Show all providers and API key status
  {cyan('/model <name>')}        Switch model (e.g. /model gemini-2.5-pro)
  {cyan('/provider <name>')}     Switch provider (gemini | claude | openai)
  {cyan('/memory [query]')}      Show memories (optional search)
  {cyan('/remember <fact>')}     Save a fact to persistent memory
  {cyan('/forget')}              Clear all memories (with confirmation)
  {cyan('/history')}             Show this session's conversation
  {cyan('/shell <cmd>')}         Run shell command directly
  {cyan('/screenshot')}          Take a screenshot
  {cyan('/voice')}               Listen for voice input then run as task
  {cyan('/repos')}               List integrated repositories
  {cyan('/integrations')}        Show all Devin modules + integration status
  {cyan('/new')}                 Start a fresh conversation
  {cyan('/clear')}               Clear screen
  {cyan('/exit')} {cyan('/quit')}           Exit

{bold('API keys')}  (.env or environment variables)
  GEMINI_API_KEY       https://aistudio.google.com/app/apikey  (free)
  ANTHROPIC_API_KEY    https://console.anthropic.com/
  OPENAI_API_KEY       https://platform.openai.com/api-keys

{bold('Examples')}
  {dim('open Firefox and search for "Python tutorials"')}
  {dim('write a Python script that counts lines in all .py files')}
  {dim('take a screenshot and describe what you see')}
  {dim("search today's AI news and summarize the top 3 stories")}
  {dim('what is 2+2')}              ← conversation (no tools needed)
  {dim('remember that my project is in /home/user/my_project')}
"""

def _banner(provider=None):
    lines = [
        "",
        bold(cyan("  ██████╗ ███████╗██╗   ██╗██╗███╗   ██╗")),
        bold(cyan("  ██╔══██╗██╔════╝██║   ██║██║████╗  ██║")),
        bold(cyan("  ██║  ██║█████╗  ██║   ██║██║██╔██╗ ██║")),
        bold(cyan("  ██║  ██║██╔══╝  ╚██╗ ██╔╝██║██║╚██╗██║")),
        bold(cyan("  ██████╔╝███████╗ ╚████╔╝ ██║██║ ╚████║")),
        bold(cyan("  ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝╚═╝  ╚═══╝")),
        "",
    ]
    for l in lines:
        print(l)

    # Status box
    w = shutil.get_terminal_size((80,24)).columns
    gk = '✓' if os.environ.get('GEMINI_API_KEY')    else '✗'
    ak = '✓' if os.environ.get('ANTHROPIC_API_KEY') else '✗'
    ok = '✓' if os.environ.get('OPENAI_API_KEY')    else '✗'
    pname = green(provider.name) if provider else dim("no provider")
    disp  = green("✓ " + os.environ.get('DISPLAY','wayland')) if _HAS_DISPLAY else dim("✗ headless")
    facts = _DB.execute('SELECT count(*) FROM memories').fetchone()[0]

    mods = _modules_status()
    loaded = sum(1 for v in mods.values() if v)
    mod_str = f"{loaded}/{len(mods)} modules"

    print(f"  ╭{'─'*(w-4)}╮")
    print(f"  │  {bold('Devin AGI v4.0.0'):<{w-18}}{' ':>8}│")
    print(f"  │  cwd: {str(_ROOT):<{w-14}}{' ':>2}│")
    print(f"  │  model: {pname}   display: {disp}   memory: {dim(str(facts)+' facts')}   {dim(mod_str+'  '+str(len(TOOLS))+' tools'):<25}│")
    print(f"  ╰{'─'*(w-4)}╯")
    print()

def _status_line(provider):
    gk = '✓' if os.environ.get('GEMINI_API_KEY')    else '✗'
    ak = '✓' if os.environ.get('ANTHROPIC_API_KEY') else '✗'
    ok = '✓' if os.environ.get('OPENAI_API_KEY')    else '✗'
    cats: Dict[str, int] = {}
    for t in TOOLS.values():
        c = t.get('category','other')
        cats[c] = cats.get(c, 0) + 1
    cat_str = '  '.join(f"{v} {k}" for k, v in sorted(cats.items()))
    print(f"\n  {bold('Provider')}   {green(provider.name)}")
    print(f"  {bold('Keys')}       "
          f"Gemini {(green if gk=='✓' else red)(gk)}  "
          f"Claude {(green if ak=='✓' else red)(ak)}  "
          f"OpenAI {(green if ok=='✓' else red)(ok)}")
    print(f"  {bold('Display')}    {'✓ ' + os.environ.get('DISPLAY','') if _HAS_DISPLAY else dim('✗ headless')}")
    print(f"  {bold('Memory')}     {_DB.execute('SELECT count(*) FROM memories').fetchone()[0]} facts  "
          f"({_DB_PATH.name})")
    print(f"  {bold('Tools')}      {len(TOOLS)}  ({cat_str})")
    print()

def repl(provider_name: str = '', model: str = ''):
    # Set up readline
    try:
        import readline as _rl
        hist = str(_ROOT / '.devin_history')
        try: _rl.read_history_file(hist)
        except FileNotFoundError: pass
        import atexit; atexit.register(_rl.write_history_file, hist)
        _rl.set_history_length(1000)
    except ImportError:
        pass

    # Pick provider
    try:
        provider = _pick_provider(provider_name, model)
    except ValueError as e:
        print(red(f"⚠  {e}"))
        provider = None

    _banner(provider)

    if provider:
        print(dim("  Talk to Devin — ask a question, give a task, or type /help. (exit to quit)\n"))
    else:
        print(dim("  No provider. Add an API key to .env, then restart.\n"))

    cur_pname = provider_name
    # Persistent conversation history
    conv_messages: List[dict] = []

    while True:
        try:
            # Prompt: show provider name
            pname = provider.name.split('/')[-1][:20] if provider else "none"
            user_input = input(f"{bold(cyan('❯'))} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(dim("\nBye.")); break

        if not user_input:
            continue

        if user_input.startswith('/'):
            parts = user_input.split(None, 1)
            cmd   = parts[0].lower()
            arg   = parts[1] if len(parts) > 1 else ''

            if cmd in ('/exit', '/quit', 'exit', 'quit'):
                print(dim("Goodbye!")); break

            elif cmd == '/help':
                print(_make_help())

            elif cmd == '/clear':
                os.system('clear' if _PLATFORM != 'Windows' else 'cls')

            elif cmd == '/new':
                conv_messages.clear()
                print(green("  ✓ Conversation reset."))

            elif cmd == '/tools':
                cats: Dict[str, List[str]] = {}
                for name, t in TOOLS.items():
                    cats.setdefault(t.get('category','other'), []).append(name)
                if arg:
                    cats = {k: v for k, v in cats.items()
                            if arg.lower() in k.lower()}
                if not cats:
                    print(yellow(f"  No tools in category {arg!r}"))
                for cat in sorted(cats):
                    print(f"\n  {bold(cat.upper())}")
                    for name in sorted(cats[cat]):
                        desc = TOOLS[name]['desc'][:65]
                        print(f"    {cyan(name):<30} {dim(desc)}")
                print()

            elif cmd == '/status':
                if provider: _status_line(provider)
                else: print(red("  No provider."))

            elif cmd == '/providers':
                for p, key_env in [('gemini', 'GEMINI_API_KEY'),
                                   ('claude', 'ANTHROPIC_API_KEY'),
                                   ('openai', 'OPENAI_API_KEY')]:
                    s = green('✓ available') if os.environ.get(key_env) else dim('✗ no key')
                    print(f"  {bold(p):<15} {s}")
                print()

            elif cmd == '/model':
                if not arg:
                    print(yellow("  Usage: /model <model-name>"))
                elif provider:
                    try:
                        pn = cur_pname or ('gemini' if os.environ.get('GEMINI_API_KEY') else
                                           'claude' if os.environ.get('ANTHROPIC_API_KEY') else 'openai')
                        provider = _pick_provider(pn, arg)
                        print(green(f"  Model: {provider.name}"))
                    except Exception as e:
                        print(red(f"  Error: {e}"))
                else:
                    print(red("  No provider active."))

            elif cmd == '/provider':
                if not arg:
                    print(yellow("  Usage: /provider gemini|claude|openai"))
                else:
                    try:
                        provider = _pick_provider(arg, model)
                        cur_pname = arg
                        print(green(f"  Provider: {provider.name}"))
                    except Exception as e:
                        print(red(f"  Error: {e}"))

            elif cmd == '/memory':
                print(_recall(arg))

            elif cmd == '/remember':
                if arg: print(green(f"  {_remember(arg)}"))
                else: print(yellow("  Usage: /remember <fact>"))

            elif cmd == '/forget':
                confirm = input("  Delete ALL memories? [y/N] ").strip().lower()
                if confirm == 'y':
                    print(green(f"  {_forget_all()}"))

            elif cmd == '/history':
                if not conv_messages:
                    print(dim("  No conversation history yet."))
                else:
                    for m in conv_messages:
                        role = m.get('role','?')
                        content = m.get('content','')
                        if isinstance(content, list):
                            content = ' '.join(str(b.get('text','') or b.get('content',''))
                                               for b in content)
                        colour = cyan if role == 'user' else green
                        label  = 'you' if role == 'user' else 'devin'
                        preview = str(content)[:120].replace('\n',' ')
                        print(f"  {colour(label)}: {dim(preview)}")
                print()

            elif cmd == '/shell':
                if arg: print(tool_execute_shell(arg))
                else: print(yellow("  Usage: /shell <command>"))

            elif cmd == '/screenshot':
                result = tool_screenshot()
                print(f"  {result}")
                if not result.startswith('ERROR:') and provider:
                    ans = input("  Analyze with AI? [y/N] ").strip().lower()
                    if ans == 'y':
                        path = result.split(': ', 1)[-1].strip().split()[0]
                        print(tool_analyze_image(path, 'Describe everything visible on screen in detail.'))

            elif cmd == '/voice':
                text = tool_listen()
                if text.startswith('Heard:'):
                    task = text.replace('Heard:', '').strip()
                    print(dim(f"  Voice: {task}"))
                    if provider:
                        run_agent(task, provider, conv_messages=conv_messages)
                else:
                    print(red(f"  {text}"))

            elif cmd == '/repos':
                found = False
                for base in [_ROOT / 'external', _ROOT / 'repos', _ROOT / 'integrations']:
                    if base.exists():
                        repos = [d.name for d in sorted(base.iterdir()) if d.is_dir()]
                        if repos:
                            print(f"\n  {bold(base.name + '/')}: {', '.join(repos[:20])}")
                            found = True
                if not found:
                    print(dim("  No external repos found."))
                print()

            elif cmd == '/integrations':
                print(f"\n{tool_list_integrations()}\n")

            else:
                print(yellow(f"  Unknown command: {cmd}. Try /help"))
            continue

        # Agent task / conversation
        if provider is None:
            print(red("  No provider. Add an API key to .env."))
            continue

        try:
            result = run_agent(user_input, provider, conv_messages=conv_messages)
        except KeyboardInterrupt:
            print(yellow("\n  ⚡ Interrupted."))
        except Exception as e:
            print(red(f"\n  ⚠ Error: {e}"))

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    provider_name = ''
    model         = ''
    task_parts    = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in ('--provider', '-p') and i + 1 < len(args):
            provider_name = args[i+1]; i += 2
        elif a in ('--model', '-m') and i + 1 < len(args):
            model = args[i+1]; i += 2
        elif a.startswith('--provider='):
            provider_name = a.split('=',1)[1]; i += 1
        elif a.startswith('--model='):
            model = a.split('=',1)[1]; i += 1
        elif a in ('--help', '-h'):
            print(__doc__); sys.exit(0)
        elif a == '--chat':
            i += 1  # just drop it, REPL is always conversational
        else:
            task_parts.append(a); i += 1

    if task_parts:
        task = ' '.join(task_parts)
        try:
            provider = _pick_provider(provider_name, model)
        except ValueError as e:
            print(red(f"⚠  {e}")); sys.exit(1)
        print(dim(f"Provider: {provider.name}"))
        result = run_agent(task, provider)
        if result and not result.startswith("(task ended"):
            print(f"\n{green('Result:')} {result}")
        sys.exit(0)
    else:
        repl(provider_name, model)

if __name__ == '__main__':
    main()
