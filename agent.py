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
  HF_TOKEN           https://huggingface.co/settings/tokens  (free)
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
except BaseException:
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
except BaseException:
    pass

# Load os_automation module (enhanced OS control)
_os_auto_mod = None
try:
    _os_auto_mod = _il.import_module('os_automation')
except BaseException:
    pass

# Load persistent_memory module (enhanced memory with categories/tags)
_pmem_mod = None
try:
    _pmem_mod = _il.import_module('persistent_memory')
    _pmem = _pmem_mod.PersistentMemory() if hasattr(_pmem_mod, 'PersistentMemory') else None
except BaseException:
    _pmem = None

# Load messaging_gateway module (Telegram/Discord/Slack)
_msg_mod = None
try:
    _msg_mod = _il.import_module('messaging_gateway')
except BaseException:
    pass

# Load integration_hub (all 24 external repos)
_hub_mod = None
try:
    _hub_mod = _il.import_module('integration_hub')
except BaseException:
    pass

# Load cheetahclaws_bridge (token tracking, compaction)
_cc_bridge = None
try:
    _ccmod = _il.import_module('cheetahclaws_bridge')
    _cc_bridge = _ccmod.CheetahClawsBridge() if hasattr(_ccmod, 'CheetahClawsBridge') else None
except BaseException:
    pass

# Load browser automation (Selenium/Playwright)
_browser_mod = None
_browser_instance = None
try:
    _browser_mod = _il.import_module('browser')
except BaseException:
    pass

# Load system monitor
_sysmon_mod = None
try:
    _sysmon_mod = _il.import_module('system_monitor')
except BaseException:
    pass

# Load code_execution module
_code_exec_mod = None
try:
    _code_exec_mod = _il.import_module('code_execution')
except BaseException:
    pass

# Load scheduler
_scheduler_mod = None
try:
    _scheduler_mod = _il.import_module('scheduler')
except BaseException:
    pass

# Load encryption tools
_crypto_mod = None
try:
    _crypto_mod = _il.import_module('encryption_tools')
except BaseException:
    pass

# Load cloud integration
_cloud_mod = None
try:
    _cloud_mod = _il.import_module('cloud_integration_module')
except BaseException:
    pass

# Load Jarvis tools
_jarvis_tools_mod = None
try:
    _jarvis_tools_mod = _il.import_module('jarvis_tools')
except BaseException:
    pass

# Load cheetah providers (multi-model streaming)
_cheetah_providers_mod = None
try:
    _cheetah_providers_mod = _il.import_module('cheetah_providers')
except BaseException:
    pass

# Load Ollama module (local LLM)
_ollama_mod = None
try:
    _ollama_mod = _il.import_module('ollama_module')
except BaseException:
    pass

# Load social media API
_social_mod = None
try:
    _social_mod = _il.import_module('social_media_api')
except BaseException:
    pass

# Load analytics module
_analytics_mod = None
try:
    _analytics_mod = _il.import_module('analytics_module')
except BaseException:
    pass

# Load automation tools (advanced automation patterns)
_auto_tools_mod = None
try:
    _auto_tools_mod = _il.import_module('automation_tools')
except BaseException:
    pass

# Load AI connector (multi-AI routing)
_ai_connector_mod = None
try:
    _ai_connector_mod = _il.import_module('ai_connector')
except BaseException:
    pass

# Load email tools
_email_mod = None
try:
    _email_mod = _il.import_module('email_tools')
except BaseException:
    pass

# Load repo tools (git operations, GitHub API)
_repo_tools_mod = None
try:
    _repo_tools_mod = _il.import_module('repo_tools')
except BaseException:
    pass

# Load cheetah security (security assessment tools)
_cheetah_sec_mod = None
try:
    _cheetah_sec_mod = _il.import_module('cheetah_security')
except BaseException:
    pass

# Load pentesting module (authorized security testing)
_pentest_mod = None
try:
    _pentest_mod = _il.import_module('pentesting_module')
except BaseException:
    pass

# Load privacy tools
_privacy_mod = None
try:
    _privacy_mod = _il.import_module('privacy_tools')
except BaseException:
    pass

# Load resilience tools
_resilience_mod = None
try:
    _resilience_mod = _il.import_module('resilience_tools')
except BaseException:
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
        'analytics':         _analytics_mod       is not None,
        'automation_tools':  _auto_tools_mod      is not None,
        'ai_connector':      _ai_connector_mod    is not None,
        'email_tools':       _email_mod           is not None,
        'repo_tools':        _repo_tools_mod      is not None,
        'cheetah_security':  _cheetah_sec_mod     is not None,
        'pentest':           _pentest_mod         is not None,
        'privacy':           _privacy_mod         is not None,
        'resilience':        _resilience_mod      is not None,
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

def tool_list_memories(query: str = '') -> str:
    """List stored memories, optionally filtered by query."""
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
        fn = getattr(_browser_instance, 'navigate', None) or getattr(_browser_instance, 'open_url', None)
        if callable(fn):
            return str(fn(url))
        return "ERROR: navigate/open_url not available"
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
        fn = getattr(_browser_instance, 'type_text', None) or getattr(_browser_instance, 'type_in', None)
        if callable(fn):
            return str(fn(selector, text))
        return "ERROR: type_text/type_in not available"
    except Exception as e:
        return f"ERROR: {e}"

def tool_browser_get_text(selector: str = '') -> str:
    """Get page text or text of an element by CSS selector."""
    global _browser_instance
    if _browser_instance is None:
        return "ERROR: browser not started."
    try:
        fn = (getattr(_browser_instance, 'get_text', None) or
              getattr(_browser_instance, 'get_page_text', None) or
              getattr(_browser_instance, 'page_source', None))
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

# ── Window control extras ─────────────────────────────────────────────────────

def tool_get_active_window() -> str:
    """Return the title of the currently active/focused window."""
    try:
        if _cmd_exists('xdotool'):
            r = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'],
                               capture_output=True, text=True, timeout=5)
            return r.stdout.strip() or "(unknown)"
        if _IS_MAC:
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            r = subprocess.run(['osascript', '-e', script],
                               capture_output=True, text=True, timeout=5)
            return r.stdout.strip() or "(unknown)"
        if _IS_WIN:
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetForegroundWindow()  # type: ignore
                buf = ctypes.create_unicode_buffer(512)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, 512)  # type: ignore
                return buf.value or "(unknown)"
            except Exception as e:
                return f"ERROR: {e}"
        return "ERROR: No tool to get active window"
    except Exception as e:
        return f"ERROR: {e}"

def tool_resize_window(width: int, height: int, title: str = '') -> str:
    """Resize a window. If title is empty, resizes the active window."""
    try:
        if _cmd_exists('wmctrl'):
            if title:
                cmd = ['wmctrl', '-r', title, '-e', f'0,-1,-1,{width},{height}']
            else:
                cmd = ['wmctrl', '-r', ':ACTIVE:', '-e', f'0,-1,-1,{width},{height}']
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return f"Resized to {width}x{height}" if r.returncode == 0 else f"ERROR: {r.stderr.strip()}"
        if _cmd_exists('xdotool'):
            wid = ''
            if title:
                r = subprocess.run(['xdotool', 'search', '--name', title],
                                   capture_output=True, text=True, timeout=5)
                wid = r.stdout.strip().split('\n')[0]
            else:
                r = subprocess.run(['xdotool', 'getactivewindow'],
                                   capture_output=True, text=True, timeout=5)
                wid = r.stdout.strip()
            if wid:
                subprocess.run(['xdotool', 'windowsize', wid, str(width), str(height)], timeout=5)
                return f"Resized window {wid} to {width}x{height}"
        return "ERROR: wmctrl or xdotool required for window resize"
    except Exception as e:
        return f"ERROR: {e}"

def tool_move_window(x: int, y: int, title: str = '') -> str:
    """Move a window to position (x, y). If title is empty, moves the active window."""
    try:
        if _cmd_exists('wmctrl'):
            ref = title if title else ':ACTIVE:'
            r = subprocess.run(['wmctrl', '-r', ref, '-e', f'0,{x},{y},-1,-1'],
                               capture_output=True, text=True, timeout=5)
            return f"Moved window to ({x},{y})" if r.returncode == 0 else f"ERROR: {r.stderr.strip()}"
        if _cmd_exists('xdotool'):
            if title:
                r = subprocess.run(['xdotool', 'search', '--name', title],
                                   capture_output=True, text=True, timeout=5)
                wid = r.stdout.strip().split('\n')[0]
            else:
                r = subprocess.run(['xdotool', 'getactivewindow'],
                                   capture_output=True, text=True, timeout=5)
                wid = r.stdout.strip()
            if wid:
                subprocess.run(['xdotool', 'windowmove', wid, str(x), str(y)], timeout=5)
                return f"Moved window to ({x},{y})"
        return "ERROR: wmctrl or xdotool required"
    except Exception as e:
        return f"ERROR: {e}"

def tool_send_notification(title: str, body: str) -> str:
    """Send a desktop notification."""
    try:
        if _cmd_exists('notify-send'):
            subprocess.run(['notify-send', title, body], timeout=5)
            return f"Notification sent: {title}"
        if _IS_MAC:
            script = f'display notification "{body}" with title "{title}"'
            subprocess.run(['osascript', '-e', script], timeout=5)
            return f"Notification sent: {title}"
        if _IS_WIN:
            # PowerShell toast notification
            ps = (f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, '
                  f'ContentType = WindowsRuntime] | Out-Null; '
                  f'$template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02; '
                  f'$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template); '
                  f'$xml.GetElementsByTagName("text")[0].InnerText = "{title}"; '
                  f'$xml.GetElementsByTagName("text")[1].InnerText = "{body}"; '
                  f'$notif = [Windows.UI.Notifications.ToastNotification]::new($xml); '
                  f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Devin").Show($notif)')
            subprocess.run(['powershell', '-Command', ps], capture_output=True, timeout=10)
            return f"Notification sent: {title}"
        return "ERROR: No notification tool available"
    except Exception as e:
        return f"ERROR: {e}"

def tool_type_text_at(x: int, y: int, text: str) -> str:
    """Click at (x,y) then immediately type text — single compound operation."""
    click_result = tool_mouse_click(x, y)
    if click_result.startswith('ERROR:'):
        return click_result
    time.sleep(0.1)
    return tool_keyboard_type(text)

def tool_press_key_at(x: int, y: int, key: str) -> str:
    """Click at (x,y) then press a key. Useful for form submission."""
    click_result = tool_mouse_click(x, y)
    if click_result.startswith('ERROR:'):
        return click_result
    time.sleep(0.1)
    return tool_keyboard_press(key)

def tool_select_all_copy() -> str:
    """Select all text in the focused element and copy to clipboard."""
    tool_keyboard_hotkey(['ctrl', 'a'])
    time.sleep(0.05)
    tool_keyboard_hotkey(['ctrl', 'c'])
    time.sleep(0.1)
    return tool_clipboard_get()

def tool_right_click_menu(x: int, y: int, option_text: str = '') -> str:
    """Right-click at (x,y) then optionally click a menu item by text."""
    result = tool_mouse_right_click(x, y)
    if result.startswith('ERROR:'):
        return result
    if option_text:
        time.sleep(0.3)
        # Try to find and click the option via screenshot analysis
        shot = tool_screenshot()
        if shot.startswith('ERROR:'):
            return f"Right-clicked at ({x},{y}). Could not find menu item '{option_text}' (no screenshot)."
        return f"Right-clicked at ({x},{y}). Menu should be open — use find_on_screen('{option_text}') then click it."
    return result

def tool_scroll_to_element(element_description: str) -> str:
    """Take screenshot, locate an element, scroll until visible, then click."""
    shot = tool_screenshot()
    if shot.startswith('ERROR:'):
        return shot
    path = shot.split(': ')[-1].strip().split()[0]
    analysis = tool_analyze_image(path, f"Is '{element_description}' visible on screen? If yes, give its exact (x,y) pixel coordinates. If not visible, say NOT_VISIBLE.")
    if 'NOT_VISIBLE' in analysis.upper():
        tool_mouse_scroll(960, 540, 'down', 5)
        return f"Scrolled down — '{element_description}' was not visible. Take another screenshot to check."
    return analysis

def tool_wait_and_click(element_description: str, timeout: int = 10) -> str:
    """Wait for an element to appear on screen, then click it."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = tool_find_on_screen(element_description)
        if not result.startswith('ERROR:') and 'not found' not in result.lower():
            # Parse coordinates from result
            m = re.search(r'(\d+)[,\s]+(\d+)', result)
            if m:
                x, y = int(m.group(1)), int(m.group(2))
                return tool_mouse_click(x, y)
        time.sleep(1)
    return f"ERROR: '{element_description}' not found on screen after {timeout}s"

def tool_run_script(script_path: str, interpreter: str = '') -> str:
    """Run a script file (.sh, .py, .js, .ps1, .bat) with the appropriate interpreter."""
    p = Path(script_path)
    if not p.exists():
        return f"ERROR: File not found: {script_path}"
    ext = p.suffix.lower()
    interp_map = {
        '.py':  ['python3'],
        '.sh':  ['bash'],
        '.js':  ['node'],
        '.ps1': ['powershell', '-ExecutionPolicy', 'Bypass', '-File'],
        '.bat': ['cmd', '/c'],
        '.rb':  ['ruby'],
        '.pl':  ['perl'],
    }
    if interpreter:
        cmd = [interpreter, str(p)]
    else:
        interp = interp_map.get(ext)
        if not interp:
            return f"ERROR: Unknown script type {ext}. Pass interpreter= explicitly."
        cmd = interp + [str(p)]
    return tool_execute_shell(' '.join(cmd), cwd=str(p.parent), timeout=60)

def tool_network_info() -> str:
    """Get network interfaces, IP addresses, and connectivity info."""
    results = []
    if _IS_WIN:
        r = tool_execute_shell('ipconfig /all', timeout=10)
    else:
        for cmd in ['ip addr', 'ifconfig -a']:
            if _cmd_exists(cmd.split()[0]):
                r = tool_execute_shell(cmd, timeout=10)
                results.append(r)
                break
        # Check connectivity
        ping_target = '8.8.8.8'
        ping_cmd = f'ping -c 1 -W 2 {ping_target}' if not _IS_WIN else f'ping -n 1 {ping_target}'
        r2 = tool_execute_shell(ping_cmd, timeout=10)
        results.append(f"Internet: {'ONLINE' if 'ttl' in r2.lower() or 'time' in r2.lower() else 'OFFLINE/blocked'}")
        return '\n'.join(results)
    return r

def tool_install_package(package: str, manager: str = '') -> str:
    """Install a Python package (pip) or system package (apt/brew/choco)."""
    if not manager:
        manager = 'pip'  # default
    if manager == 'pip':
        return tool_execute_shell(f'{sys.executable} -m pip install {package}', timeout=120)
    if manager in ('apt', 'apt-get'):
        return tool_execute_shell(f'sudo apt-get install -y {package}', timeout=120)
    if manager == 'brew':
        return tool_execute_shell(f'brew install {package}', timeout=120)
    if manager == 'choco':
        return tool_execute_shell(f'choco install {package} -y', timeout=120)
    if manager == 'npm':
        return tool_execute_shell(f'npm install -g {package}', timeout=120)
    return f"ERROR: Unknown manager {manager!r}. Use: pip, apt, brew, choco, npm"

def tool_context_info() -> str:
    """Return info about the current conversation/context state."""
    return json.dumps({
        "platform": _PLATFORM,
        "has_display": _HAS_DISPLAY,
        "has_pyautogui": _HAS_PAG,
        "cwd": str(Path.cwd()),
        "root": str(_ROOT),
        "memory_count": _DB.execute('SELECT count(*) FROM memories').fetchone()[0],
        "tools_available": len(TOOLS) if 'TOOLS' in globals() else 'loading',
        "modules": _modules_status(),
    }, indent=2)

# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED OS AUTOMATION TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

def tool_screenshot_and_analyze(prompt: str = '') -> str:
    """Take a screenshot and immediately analyze it with AI. Returns description + coordinates."""
    shot = tool_screenshot()
    if shot.startswith('ERROR'):
        return shot
    path = shot.split(': ', 1)[-1].strip().split()[0]
    q = prompt or ('Describe every UI element visible on screen. For each: name it, '
                   'give its (x, y) center pixel coordinates, and describe its purpose. '
                   'List any text fields, buttons, menus, and the window title.')
    return f"Screenshot: {shot}\n\nAnalysis:\n{tool_analyze_image(path, q)}"


def tool_click_by_description(description: str, screenshot_path: str = '') -> str:
    """Find a UI element by description in the current screen and click it.
    Takes a screenshot if none provided, analyzes it, extracts coordinates, and clicks."""
    if not _HAS_DISPLAY:
        return 'ERROR: No display available'
    # Take screenshot
    shot_result = tool_screenshot()
    if shot_result.startswith('ERROR'):
        return shot_result
    path = shot_result.split(': ', 1)[-1].strip().split()[0]
    # Ask AI to find the element and return its coordinates
    analysis = tool_analyze_image(
        path,
        f"Find the UI element described as: '{description}'. "
        "Reply with ONLY the x,y pixel coordinates in this exact format: COORDS:x,y "
        "where x and y are integers. If not found, reply: NOT_FOUND"
    )
    m = re.search(r'COORDS:\s*(\d+)\s*,\s*(\d+)', analysis, re.IGNORECASE)
    if m:
        x, y = int(m.group(1)), int(m.group(2))
        return tool_mouse_click(x, y)
    return f'ERROR: Could not find "{description}" on screen. AI response: {analysis[:200]}'


def tool_observe_and_act(goal: str) -> str:
    """High-level: take screenshot, analyze current state toward goal, and suggest next action.
    Returns a JSON with {state, next_action, reasoning}."""
    shot = tool_screenshot()
    if shot.startswith('ERROR'):
        return json.dumps({"state": "headless", "next_action": "use_shell", "reasoning": "No display"})
    path = shot.split(': ', 1)[-1].strip().split()[0]
    analysis = tool_analyze_image(path,
        f"Goal: {goal}\n"
        "Analyze the current screen state. Reply as JSON with keys:\n"
        "- state: brief description of what is currently on screen\n"
        "- goal_achieved: true/false\n"
        "- next_action: the single most important next action to take\n"
        "- coordinates: {{x: N, y: N}} if a click is needed, otherwise null\n"
        "- reasoning: one sentence explaining why"
    )
    return analysis


def tool_browser_audit_repo(repo_url: str) -> str:
    """Open a GitHub repository in the browser and perform a full visual audit.
    Takes screenshots, navigates through key pages, and returns findings."""
    results = []
    results.append(f"Starting audit of: {repo_url}")

    # Try Selenium/Playwright first
    nav = tool_browser_navigate(repo_url)
    results.append(f"Navigation: {nav}")

    time.sleep(3)
    # Get page text
    text = tool_browser_get_text()
    results.append(f"Page content (first 2000 chars):\n{text[:2000]}")

    # Navigate to key sections
    for path, desc in [('/blob/main/README.md', 'README'), ('/tree/main', 'File tree')]:
        url2 = repo_url.rstrip('/') + path
        r = tool_browser_navigate(url2)
        time.sleep(2)
        content = tool_browser_get_text()
        results.append(f"\n{desc} ({url2}):\n{content[:1500]}")

    # Take a screenshot of final state
    shot = tool_browser_screenshot()
    results.append(f"\nFinal screenshot: {shot}")
    return '\n'.join(results)


def tool_type_and_submit(text: str, submit_key: str = 'Return') -> str:
    """Type text and immediately press a submit key (Enter, Tab, etc.)."""
    r1 = tool_keyboard_type(text)
    time.sleep(0.2)
    r2 = tool_keyboard_press(submit_key)
    return f"Typed: {r1} | Submitted: {r2}"


def tool_click_and_verify(x: int, y: int, expected: str = '') -> str:
    """Click at coordinates, take a screenshot, and verify the expected outcome."""
    click_result = tool_mouse_click(x, y)
    time.sleep(0.8)
    shot = tool_screenshot()
    if shot.startswith('ERROR'):
        return f"Click: {click_result} | Verify: no display"
    path = shot.split(': ', 1)[-1].strip().split()[0]
    if expected:
        analysis = tool_analyze_image(path, f"Does the screen now show '{expected}'? Reply: YES or NO and why.")
        return f"Click: {click_result} | Screenshot: {shot} | Verify: {analysis}"
    return f"Click: {click_result} | Screenshot: {shot}"


def tool_open_and_wait(app_name: str, wait_seconds: float = 3.0, window_title: str = '') -> str:
    """Open an application, wait for it to load, and verify it's open."""
    open_result = tool_open_application(app_name, wait_seconds=0.5)
    time.sleep(wait_seconds)
    if window_title:
        focus = tool_focus_window(window_title)
        return f"{open_result} | {focus}"
    # Take screenshot to confirm
    shot = tool_screenshot()
    if shot.startswith('ERROR'):
        return open_result
    path = shot.split(': ', 1)[-1].strip().split()[0]
    verify = tool_analyze_image(path, f"Is {app_name} visible and open on screen? Reply: YES or NO")
    return f"{open_result} | Loaded: {verify.strip()}"


def tool_search_web_open(query: str, browser: str = 'firefox') -> str:
    """Open a browser and search for a query. Full automation: launch → navigate → search."""
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
    # Try browser automation first
    nav = tool_browser_navigate(url)
    if 'ERROR' not in nav:
        time.sleep(2)
        content = tool_browser_get_text()
        return f"Searched for: {query}\nBrowser: {nav}\nResults preview:\n{content[:2000]}"
    # Fallback: open GUI browser if display available
    if _HAS_DISPLAY:
        open_result = tool_open_and_wait(browser, wait_seconds=3.0)
        time.sleep(1)
        # Use keyboard shortcut to focus address bar
        tool_keyboard_hotkey(['ctrl', 'l'])
        time.sleep(0.3)
        tool_keyboard_type(url)
        tool_keyboard_press('Return')
        time.sleep(3)
        shot = tool_screenshot()
        return f"Opened {browser}: {open_result}\nNavigated to: {url}\nScreenshot: {shot}"
    # Last resort: web fetch
    return tool_web_fetch(url)


def tool_read_screen_text(region: str = '') -> str:
    """Take a screenshot and extract all readable text from the screen using AI."""
    shot = tool_screenshot()
    if shot.startswith('ERROR'):
        return shot
    path = shot.split(': ', 1)[-1].strip().split()[0]
    prompt = "Extract and transcribe ALL text visible on the screen. Include every word, number, and label."
    if region:
        prompt = f"Extract ALL text from the {region} area of the screen."
    return tool_analyze_image(path, prompt)


def tool_get_window_info(title: str = '') -> str:
    """Get detailed info about window(s): title, size, position, state."""
    active = tool_get_active_window()
    windows = tool_list_windows()
    if _HAS_PAG:
        try:
            sz = _pag.size()
            screen_info = f"Screen: {sz.width}x{sz.height}"
        except Exception:
            screen_info = tool_get_screen_size()
    else:
        screen_info = tool_get_screen_size()
    return f"Active window: {active}\nAll windows: {windows}\n{screen_info}"


def tool_execute_shell_interactive(command: str, timeout: int = 60) -> str:
    """Run a shell command and return both stdout and stderr clearly separated."""
    try:
        proc = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(Path.cwd())
        )
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        parts = []
        if out:
            parts.append(f"STDOUT:\n{out[:4000]}")
        if err:
            parts.append(f"STDERR:\n{err[:2000]}")
        if proc.returncode != 0:
            parts.append(f"EXIT CODE: {proc.returncode}")
        return '\n'.join(parts) if parts else "(no output)"
    except subprocess.TimeoutExpired:
        return f"TIMEOUT after {timeout}s"
    except Exception as e:
        return f"ERROR: {e}"


def tool_file_tree(path: str = '.', depth: int = 3) -> str:
    """Show directory tree up to given depth."""
    try:
        r = subprocess.run(['find', path, '-maxdepth', str(depth), '-not', '-path', '*/.*'],
                           capture_output=True, text=True, timeout=10)
        lines = sorted(r.stdout.strip().splitlines())
        return '\n'.join(lines[:200]) or "(empty)"
    except Exception:
        try:
            base = Path(path)
            result = []
            for item in sorted(base.rglob('*')):
                try:
                    rel = item.relative_to(base)
                    parts = rel.parts
                    if len(parts) <= depth and not any(p.startswith('.') for p in parts):
                        indent = '  ' * (len(parts) - 1)
                        result.append(f"{indent}{item.name}{'/' if item.is_dir() else ''}")
                except Exception:
                    pass
            return '\n'.join(result[:200]) or "(empty)"
        except Exception as e:
            return f"ERROR: {e}"


def tool_diff_files(path1: str, path2: str) -> str:
    """Show unified diff between two files."""
    try:
        r = subprocess.run(['diff', '-u', path1, path2], capture_output=True, text=True)
        return r.stdout[:4000] or "(no differences)"
    except Exception as e:
        return f"ERROR: {e}"


def tool_pipe_commands(commands: str) -> str:
    """Execute a shell pipeline and return output. E.g. 'cat file.txt | grep error | sort'"""
    return tool_execute_shell(commands)


def tool_check_port(host: str = 'localhost', port: int = 80) -> str:
    """Check if a TCP port is open on host."""
    import socket
    try:
        with socket.create_connection((host, port), timeout=3):
            return f"Port {host}:{port} is OPEN"
    except Exception as e:
        return f"Port {host}:{port} is CLOSED/unreachable: {e}"


def tool_read_url_content(url: str, selector: str = '') -> str:
    """Fetch a URL and extract clean text content. Optionally filter by CSS selector via browser."""
    if selector and _browser_instance:
        try:
            tool_browser_navigate(url)
            time.sleep(2)
            return tool_browser_get_text(selector)
        except Exception:
            pass
    return tool_web_fetch(url, max_chars=6000)


def tool_save_output(content: str, filename: str = '') -> str:
    """Save content to a file. Auto-generates filename with timestamp if not provided."""
    if not filename:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"devin_output_{ts}.txt"
    path = Path(filename) if Path(filename).is_absolute() else _ROOT / 'data' / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return f"Saved {len(content)} chars to: {path}"


def tool_multi_click(actions: str) -> str:
    """Execute a sequence of clicks/keys from a JSON array.
    Format: [{"type":"click","x":100,"y":200}, {"type":"key","key":"Return"}, {"type":"type","text":"hello"}]"""
    try:
        steps = json.loads(actions)
    except Exception:
        return "ERROR: actions must be valid JSON array"
    results = []
    for step in steps:
        t = step.get('type', '')
        try:
            if t == 'click':
                r = tool_mouse_click(step['x'], step['y'])
            elif t == 'dclick':
                r = tool_mouse_double_click(step['x'], step['y'])
            elif t == 'rclick':
                r = tool_mouse_right_click(step['x'], step['y'])
            elif t == 'type':
                r = tool_keyboard_type(step['text'])
            elif t == 'key':
                r = tool_keyboard_press(step['key'])
            elif t == 'hotkey':
                r = tool_keyboard_hotkey(step['keys'])
            elif t == 'sleep':
                time.sleep(float(step.get('seconds', 0.5)))
                r = f"slept {step.get('seconds', 0.5)}s"
            elif t == 'screenshot':
                r = tool_screenshot()
            else:
                r = f"unknown step type: {t}"
            results.append(f"[{t}] {r}")
        except Exception as e:
            results.append(f"[{t}] ERROR: {e}")
    return '\n'.join(results)


def tool_pen_test_recon(target: str) -> str:
    """Basic reconnaisance on an authorized target: port scan, HTTP headers, robots.txt.
    ONLY use on systems you own or have explicit written permission to test."""
    if not target:
        return "ERROR: target required"
    results = [f"Recon on: {target} (authorized target assumed)"]
    # HTTP headers
    try:
        url = target if target.startswith('http') else f"http://{target}"
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=5) as r:
            results.append(f"\nHTTP headers:\n" + '\n'.join(f"  {k}: {v}" for k, v in r.headers.items()))
    except Exception as e:
        results.append(f"\nHTTP: {e}")
    # robots.txt
    try:
        robots_url = (target.rstrip('/') if target.startswith('http') else f"http://{target}") + '/robots.txt'
        robots = tool_web_fetch(robots_url, max_chars=500)
        results.append(f"\nrobots.txt:\n{robots}")
    except Exception:
        pass
    # Port check on common ports
    import socket
    host = re.sub(r'^https?://', '', target).split('/')[0].split(':')[0]
    open_ports = []
    for port in [80, 443, 8080, 8443, 22, 21, 3306, 5432]:
        try:
            with socket.create_connection((host, port), timeout=1):
                open_ports.append(port)
        except Exception:
            pass
    results.append(f"\nOpen ports (quick scan): {open_ports}")
    return '\n'.join(results)


def tool_system_security_check() -> str:
    """Run local system security checks: listening ports, running services, sudo config."""
    checks = []
    for cmd, label in [
        ("ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null", "Listening ports"),
        ("ps aux --sort=-%cpu | head -20", "Top processes by CPU"),
        ("find /etc -name '*.conf' -newer /etc/passwd 2>/dev/null | head -10", "Recently modified configs"),
        ("last | head -10", "Recent logins"),
        ("uname -r", "Kernel version"),
    ]:
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            checks.append(f"\n{label}:\n{r.stdout.strip()[:500]}")
        except Exception as e:
            checks.append(f"\n{label}: {e}")
    return '\n'.join(checks)


def tool_send_email(to: str, subject: str, body: str) -> str:
    """Send email using configured email integration."""
    if _email_mod:
        try:
            fn = getattr(_email_mod, 'send_email', None) or getattr(_email_mod, 'SendEmail', None)
            if fn:
                return str(fn(to=to, subject=subject, body=body))
        except Exception as e:
            return f"ERROR: {e}"
    return "ERROR: email_tools module not available"


def tool_analyze_data(data: str, analysis_type: str = 'summary') -> str:
    """Analyze data using the analytics module. Types: summary, stats, patterns, anomalies."""
    if _analytics_mod:
        try:
            fn = (getattr(_analytics_mod, 'analyze', None) or
                  getattr(_analytics_mod, 'analyze_data', None) or
                  getattr(_analytics_mod, 'run_analysis', None))
            if fn:
                return str(fn(data=data, analysis_type=analysis_type))
        except Exception as e:
            return f"Analytics error: {e}"
    # Fallback: basic Python stats
    import statistics
    lines = [l.strip() for l in str(data).split('\n') if l.strip()]
    numbers = []
    for l in lines:
        try: numbers.append(float(l))
        except: pass
    if numbers:
        return (f"Lines: {len(lines)}  Numbers found: {len(numbers)}\n"
                f"Min: {min(numbers):.2f}  Max: {max(numbers):.2f}  "
                f"Mean: {statistics.mean(numbers):.2f}  "
                f"Stdev: {statistics.stdev(numbers):.2f if len(numbers)>1 else 'n/a'}")
    return f"Lines: {len(lines)}  Words: {sum(len(l.split()) for l in lines)}  Chars: {len(data)}"


def tool_schedule_task(task: str, delay_seconds: float = 0, recurring: bool = False) -> str:
    """Schedule a task to run after a delay. Uses scheduler module if available."""
    if _scheduler_mod:
        try:
            fn = (getattr(_scheduler_mod, 'schedule_task', None) or
                  getattr(_scheduler_mod, 'add_task', None))
            if fn:
                return str(fn(task=task, delay=delay_seconds, recurring=recurring))
        except Exception as e:
            return f"Scheduler error: {e}"
    # Simple fallback: just sleep and note
    return f"Scheduled: '{task[:60]}' (delay={delay_seconds}s) — run with execute_shell or execute_python"


def tool_repo_info(repo_path: str = '.') -> str:
    """Get detailed git repo information: status, log, branches, remotes."""
    if _repo_tools_mod:
        try:
            fn = (getattr(_repo_tools_mod, 'get_repo_info', None) or
                  getattr(_repo_tools_mod, 'repo_status', None))
            if fn:
                return str(fn(repo_path=repo_path))
        except Exception as e:
            return f"repo_tools error: {e}"
    # Fallback to git commands
    parts = []
    for cmd in ['git -C "{p}" log --oneline -5'.format(p=repo_path),
                'git -C "{p}" status --short'.format(p=repo_path),
                'git -C "{p}" branch -a'.format(p=repo_path)]:
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            parts.append(r.stdout.strip()[:300])
        except Exception:
            pass
    return '\n'.join(parts) or "Not a git repo or git not available"


def tool_security_scan(target: str, scan_type: str = 'basic') -> str:
    """Run an authorized security scan. scan_type: basic | ports | web | full.
    Only use on systems you own or have explicit written authorization to test."""
    if _cheetah_sec_mod:
        try:
            fn = (getattr(_cheetah_sec_mod, 'run_scan', None) or
                  getattr(_cheetah_sec_mod, 'security_scan', None))
            if fn:
                return str(fn(target=target, scan_type=scan_type))
        except Exception as e:
            return f"cheetah_security error: {e}"
    if _pentest_mod:
        try:
            fn = (getattr(_pentest_mod, 'run_pentest', None) or
                  getattr(_pentest_mod, 'scan', None))
            if fn:
                return str(fn(target=target))
        except Exception as e:
            return f"pentest error: {e}"
    # Fallback to basic nmap
    return tool_pen_test_recon(target)


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

    # ── Window extras ──────────────────────────────────────────────────────────
    "get_active_window": {
        "fn": tool_get_active_window,
        "desc": "Get the title of the currently active/focused window.",
        "params": {},
        "required": [],
        "category": "windows",
    },
    "resize_window": {
        "fn": tool_resize_window,
        "desc": "Resize a window to the given width and height.",
        "params": {
            "width":  {"type": "integer", "description": "Target width in pixels"},
            "height": {"type": "integer", "description": "Target height in pixels"},
            "title":  {"type": "string",  "description": "Window title substring (empty = active window)"},
        },
        "required": ["width", "height"],
        "category": "windows",
    },
    "move_window": {
        "fn": tool_move_window,
        "desc": "Move a window to position (x, y) on screen.",
        "params": {
            "x":     {"type": "integer", "description": "X position"},
            "y":     {"type": "integer", "description": "Y position"},
            "title": {"type": "string",  "description": "Window title substring (empty = active window)"},
        },
        "required": ["x", "y"],
        "category": "windows",
    },
    "send_notification": {
        "fn": tool_send_notification,
        "desc": "Send a desktop notification (notify-send on Linux, osascript on macOS, PowerShell on Windows).",
        "params": {
            "title": {"type": "string", "description": "Notification title"},
            "body":  {"type": "string", "description": "Notification body text"},
        },
        "required": ["title", "body"],
        "category": "apps",
    },

    # ── Compound mouse+keyboard ────────────────────────────────────────────────
    "type_text_at": {
        "fn": tool_type_text_at,
        "desc": "Click at (x,y) then immediately type text. Single compound action.",
        "params": {
            "x":    {"type": "integer", "description": "Click X coordinate"},
            "y":    {"type": "integer", "description": "Click Y coordinate"},
            "text": {"type": "string",  "description": "Text to type"},
        },
        "required": ["x", "y", "text"],
        "category": "keyboard",
    },
    "press_key_at": {
        "fn": tool_press_key_at,
        "desc": "Click at (x,y) then press a key. Useful for clicking an input then pressing Enter.",
        "params": {
            "x":   {"type": "integer", "description": "Click X coordinate"},
            "y":   {"type": "integer", "description": "Click Y coordinate"},
            "key": {"type": "string",  "description": "Key to press (e.g. Return, Escape, Tab)"},
        },
        "required": ["x", "y", "key"],
        "category": "keyboard",
    },
    "select_all_copy": {
        "fn": tool_select_all_copy,
        "desc": "Press Ctrl+A then Ctrl+C and return clipboard content. Useful for reading all text in a focused window.",
        "params": {},
        "required": [],
        "category": "clipboard",
    },
    "wait_and_click": {
        "fn": tool_wait_and_click,
        "desc": "Wait for an element to appear on screen (by description), then click it.",
        "params": {
            "element_description": {"type": "string",  "description": "Description of what to look for"},
            "timeout":             {"type": "integer", "description": "Max seconds to wait (default 10)"},
        },
        "required": ["element_description"],
        "category": "vision",
    },
    "scroll_to_element": {
        "fn": tool_scroll_to_element,
        "desc": "Take screenshot, check if element is visible; if not, scroll down and report.",
        "params": {
            "element_description": {"type": "string", "description": "What to look for on screen"},
        },
        "required": ["element_description"],
        "category": "vision",
    },

    # ── Script execution ───────────────────────────────────────────────────────
    "run_script": {
        "fn": tool_run_script,
        "desc": "Run a script file (.py, .sh, .js, .ps1, .bat, .rb, .pl). Auto-detects interpreter from extension.",
        "params": {
            "script_path":  {"type": "string", "description": "Path to script file"},
            "interpreter":  {"type": "string", "description": "Override interpreter (optional)"},
        },
        "required": ["script_path"],
        "category": "shell",
    },

    # ── Network ────────────────────────────────────────────────────────────────
    "network_info": {
        "fn": tool_network_info,
        "desc": "Get network interface info, IP addresses, and internet connectivity status.",
        "params": {},
        "required": [],
        "category": "system",
    },

    # ── Package installation ───────────────────────────────────────────────────
    "install_package": {
        "fn": tool_install_package,
        "desc": "Install a package using pip, apt, brew, choco, or npm.",
        "params": {
            "package": {"type": "string", "description": "Package name to install"},
            "manager": {"type": "string", "description": "Package manager: pip (default), apt, brew, choco, npm"},
        },
        "required": ["package"],
        "category": "shell",
    },

    # ── Context info ───────────────────────────────────────────────────────────
    "context_info": {
        "fn": tool_context_info,
        "desc": "Return current environment info: platform, display, modules, memory count, tools.",
        "params": {},
        "required": [],
        "category": "system",
    },
    # ── Convenience aliases ────────────────────────────────────────────────
    "shell": {
        "fn": tool_execute_shell,
        "desc": "Alias for execute_shell — run a shell command",
        "params": {"command": {"type": "string", "description": "Shell command to run"}},
        "required": ["command"],
        "category": "shell",
    },
    "take_screenshot": {
        "fn": tool_screenshot,
        "desc": "Alias for screenshot — capture the screen",
        "params": {"path": {"type": "string", "description": "Optional save path"}},
        "required": [],
        "category": "vision",
    },
    "list_memories": {
        "fn": tool_list_memories,
        "desc": "List stored memories, optionally filtered by query",
        "params": {"query": {"type": "string", "description": "Optional filter query"}},
        "required": [],
        "category": "memory",
    },
    # ── Advanced OS automation ─────────────────────────────────────────────
    "screenshot_and_analyze": {
        "fn": tool_screenshot_and_analyze,
        "desc": "Take screenshot and immediately analyze it with AI. Returns description + UI element coordinates.",
        "params": {"prompt": {"type": "string", "description": "What to look for or analyze"}},
        "required": [],
        "category": "vision",
    },
    "click_by_description": {
        "fn": tool_click_by_description,
        "desc": "Find a UI element by text/description and click it automatically using screenshot + AI.",
        "params": {"description": {"type": "string", "description": "Description of element to click, e.g. 'address bar', 'Submit button', 'Firefox icon'"}},
        "required": ["description"],
        "category": "vision",
    },
    "observe_and_act": {
        "fn": tool_observe_and_act,
        "desc": "Take screenshot, analyze current screen state toward a goal, and return next recommended action with coordinates.",
        "params": {"goal": {"type": "string", "description": "The goal you are trying to achieve"}},
        "required": ["goal"],
        "category": "vision",
    },
    "click_and_verify": {
        "fn": tool_click_and_verify,
        "desc": "Click at coordinates, take screenshot, and verify expected outcome.",
        "params": {
            "x": {"type": "integer", "description": "X coordinate"},
            "y": {"type": "integer", "description": "Y coordinate"},
            "expected": {"type": "string", "description": "What you expect to see after clicking"},
        },
        "required": ["x", "y"],
        "category": "mouse",
    },
    "type_and_submit": {
        "fn": tool_type_and_submit,
        "desc": "Type text and immediately press a submit key (Return/Tab/etc).",
        "params": {
            "text": {"type": "string", "description": "Text to type"},
            "submit_key": {"type": "string", "description": "Key to press after typing: Return, Tab, Escape"},
        },
        "required": ["text"],
        "category": "keyboard",
    },
    "open_and_wait": {
        "fn": tool_open_and_wait,
        "desc": "Open an application, wait for it to fully load, and verify it opened.",
        "params": {
            "app_name": {"type": "string", "description": "Application to open"},
            "wait_seconds": {"type": "number", "description": "Seconds to wait for load"},
            "window_title": {"type": "string", "description": "Expected window title to focus"},
        },
        "required": ["app_name"],
        "category": "apps",
    },
    "search_web_open": {
        "fn": tool_search_web_open,
        "desc": "Open browser and search the web. Full automation: launch → navigate → search.",
        "params": {
            "query": {"type": "string", "description": "Search query"},
            "browser": {"type": "string", "description": "Browser to use: firefox, chromium, chrome"},
        },
        "required": ["query"],
        "category": "browser",
    },
    "read_screen_text": {
        "fn": tool_read_screen_text,
        "desc": "Take screenshot and extract all readable text from screen using AI.",
        "params": {"region": {"type": "string", "description": "Optional: region to read (top, bottom, left, right, center)"}},
        "required": [],
        "category": "vision",
    },
    "get_window_info": {
        "fn": tool_get_window_info,
        "desc": "Get detailed info about windows: titles, positions, sizes.",
        "params": {"title": {"type": "string", "description": "Optional window title filter"}},
        "required": [],
        "category": "windows",
    },
    "execute_shell_verbose": {
        "fn": tool_execute_shell_interactive,
        "desc": "Run shell command with clearly separated stdout/stderr output and exit code.",
        "params": {
            "command": {"type": "string", "description": "Shell command to run"},
            "timeout": {"type": "integer", "description": "Timeout in seconds"},
        },
        "required": ["command"],
        "category": "shell",
    },
    "file_tree": {
        "fn": tool_file_tree,
        "desc": "Show directory tree structure up to specified depth.",
        "params": {
            "path": {"type": "string", "description": "Directory path to scan"},
            "depth": {"type": "integer", "description": "Maximum depth (default 3)"},
        },
        "required": [],
        "category": "files",
    },
    "diff_files": {
        "fn": tool_diff_files,
        "desc": "Show unified diff between two files.",
        "params": {
            "path1": {"type": "string", "description": "First file path"},
            "path2": {"type": "string", "description": "Second file path"},
        },
        "required": ["path1", "path2"],
        "category": "files",
    },
    "check_port": {
        "fn": tool_check_port,
        "desc": "Check if a TCP port is open on a host.",
        "params": {
            "host": {"type": "string", "description": "Hostname or IP"},
            "port": {"type": "integer", "description": "Port number"},
        },
        "required": ["host", "port"],
        "category": "network",
    },
    "read_url_content": {
        "fn": tool_read_url_content,
        "desc": "Fetch a URL and return clean readable text content.",
        "params": {
            "url": {"type": "string", "description": "URL to fetch"},
            "selector": {"type": "string", "description": "Optional CSS selector to extract specific content"},
        },
        "required": ["url"],
        "category": "web",
    },
    "save_output": {
        "fn": tool_save_output,
        "desc": "Save content to a file with optional filename (auto-timestamped if not provided).",
        "params": {
            "content": {"type": "string", "description": "Content to save"},
            "filename": {"type": "string", "description": "Output filename (optional)"},
        },
        "required": ["content"],
        "category": "files",
    },
    "multi_click": {
        "fn": tool_multi_click,
        "desc": 'Execute sequence of clicks/keys/types from JSON array. E.g. [{"type":"click","x":100,"y":200},{"type":"type","text":"hello"},{"type":"key","key":"Return"}]',
        "params": {"actions": {"type": "string", "description": "JSON array of actions: [{type,x,y}, {type,text}, {type,key}, {type,keys}, {type,seconds}]"}},
        "required": ["actions"],
        "category": "mouse",
    },
    "browser_audit_repo": {
        "fn": tool_browser_audit_repo,
        "desc": "Open a GitHub repository in the browser and perform a full visual audit including README, file tree, and key pages.",
        "params": {"repo_url": {"type": "string", "description": "GitHub repository URL"}},
        "required": ["repo_url"],
        "category": "browser",
    },
    "pen_test_recon": {
        "fn": tool_pen_test_recon,
        "desc": "Basic recon on an AUTHORIZED target: HTTP headers, robots.txt, open ports. ONLY use on systems you own or have explicit written permission to test.",
        "params": {"target": {"type": "string", "description": "Target hostname or URL (must be authorized)"}},
        "required": ["target"],
        "category": "security",
    },
    "system_security_check": {
        "fn": tool_system_security_check,
        "desc": "Run local system security checks: listening ports, top processes, recent logins, kernel version.",
        "params": {},
        "required": [],
        "category": "security",
    },

    # ── Email ──────────────────────────────────────────────────────────────────
    "send_email": {
        "fn": tool_send_email,
        "desc": "Send an email using the configured email integration.",
        "params": {
            "to": {"type": "string", "description": "Recipient email address"},
            "subject": {"type": "string", "description": "Email subject line"},
            "body": {"type": "string", "description": "Email body text"},
        },
        "required": ["to", "subject", "body"],
        "category": "integrations",
    },

    # ── Analytics ──────────────────────────────────────────────────────────────
    "analyze_data": {
        "fn": tool_analyze_data,
        "desc": "Analyze data: summary statistics, trends, correlation, or anomaly detection.",
        "params": {
            "data": {"type": "string", "description": "Data as JSON string, CSV text, or description"},
            "analysis_type": {"type": "string", "description": "One of: summary, trends, correlation, anomaly (default: summary)"},
        },
        "required": ["data"],
        "category": "data",
    },

    # ── Scheduling ─────────────────────────────────────────────────────────────
    "schedule_task": {
        "fn": tool_schedule_task,
        "desc": "Schedule a shell command or task to run after a delay (optionally recurring).",
        "params": {
            "task": {"type": "string", "description": "Shell command or task description to run"},
            "delay_seconds": {"type": "number", "description": "Seconds to wait before running (default 0)"},
            "recurring": {"type": "boolean", "description": "Whether to repeat the task (default false)"},
        },
        "required": ["task"],
        "category": "scheduling",
    },

    # ── Repository ─────────────────────────────────────────────────────────────
    "repo_info": {
        "fn": tool_repo_info,
        "desc": "Get info about a git repository: branch, recent commits, status, remotes.",
        "params": {
            "repo_path": {"type": "string", "description": "Path to git repo (default: current directory)"},
        },
        "required": [],
        "category": "git",
    },

    # ── Security Scan ──────────────────────────────────────────────────────────
    "security_scan": {
        "fn": tool_security_scan,
        "desc": "Run a security scan on a target file, directory, or URL. Requires explicit authorization.",
        "params": {
            "target": {"type": "string", "description": "File path, directory, or URL to scan"},
            "scan_type": {"type": "string", "description": "Scan type: basic, ports, files, web (default: basic)"},
        },
        "required": ["target"],
        "category": "security",
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
    MODELS = FALLBACK_MODELS  # alias for external access

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

# ─── Ollama (local) ───────────────────────────────────────────────────────────

class OllamaProvider:
    """Local LLM via Ollama (https://ollama.com). No API key required."""

    def __init__(self, base_url: str = '', model: str = 'llama3.2'):
        self.base_url = (base_url or os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')).rstrip('/')
        self.model    = model
        self.name     = f"ollama/{model}"

    def call(self, messages: list, system: str = '') -> Tuple[str, List[dict]]:
        msgs: List[dict] = []
        if system:
            msgs.append({"role": "system", "content": system})
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, list):
                content = " ".join(str(b.get("text") or b.get("content") or "") for b in content)
            msgs.append({"role": m["role"], "content": content})

        body = {"model": self.model, "messages": msgs, "stream": False,
                "options": {"num_predict": 4096}}
        hdrs = {"Content-Type": "application/json"}
        url  = f"{self.base_url}/api/chat"

        for attempt in range(3):
            try:
                resp = _http_post(url, hdrs, body, timeout=120)
                msg  = resp.get("message", {})
                text = msg.get("content", "")
                # Ollama doesn't support native tool calling — use ReAct parsing
                pattern = re.compile(r'<tool_call>(.*?)</tool_call>', re.DOTALL)
                calls = []
                for m in pattern.finditer(text):
                    try:
                        obj = json.loads(m.group(1).strip())
                        if isinstance(obj, dict) and 'name' in obj:
                            calls.append({'name': obj['name'],
                                          'args': obj.get('args', {})})
                    except Exception:
                        pass
                clean = pattern.sub('', text).strip()
                return clean, calls
            except Exception as e:
                if attempt < 2:
                    time.sleep(2); continue
                raise ValueError(f"Ollama error: {e}")
        raise ValueError("Ollama: max retries exceeded")

# ─── HuggingFace ──────────────────────────────────────────────────────────────

class HuggingFaceProvider:
    """
    HuggingFace Inference API provider using the OpenAI-compatible endpoint.
    Supports function calling for capable models (LLaMA-3, Qwen, Mixtral).
    Falls back to ReAct-style text parsing for models without native tool support.
    """
    URL = "https://api-inference.huggingface.co/v1/chat/completions"
    # Best free-tier models ordered by capability
    MODELS = [
        'Qwen/Qwen2.5-72B-Instruct',             # best free reasoning + code
        'meta-llama/Llama-3.3-70B-Instruct',     # latest Meta, excellent instruction following
        'meta-llama/Meta-Llama-3.1-70B-Instruct',# Meta 70B stable
        'deepseek-ai/DeepSeek-R1-Distill-Llama-70B',  # reasoning distill
        'Qwen/Qwen2.5-Coder-32B-Instruct',       # best for code tasks
        'mistralai/Mistral-Nemo-Instruct-2407',  # compact capable model
        'mistralai/Mixtral-8x7B-Instruct-v0.1',  # MOE model
        'meta-llama/Meta-Llama-3.1-8B-Instruct', # fast small model
        'microsoft/Phi-3.5-mini-instruct',        # tiny but capable
    ]
    # Models known to support native function/tool calling
    TOOL_CALL_MODELS = {
        'Qwen/Qwen2.5-72B-Instruct',
        'Qwen/Qwen2.5-Coder-32B-Instruct',
        'meta-llama/Llama-3.3-70B-Instruct',
        'meta-llama/Meta-Llama-3.1-70B-Instruct',
        'meta-llama/Meta-Llama-3.1-8B-Instruct',
    }
    # ReAct-style tool call markers for text-parsing fallback
    _CALL_OPEN  = '<tool_call>'
    _CALL_CLOSE = '</tool_call>'

    def __init__(self, api_key: str, model: str = ''):
        self.api_key = api_key
        self.model   = model or self.MODELS[0]
        self.name    = f"huggingface/{self.model.split('/')[-1]}"

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _react_system_suffix(self) -> str:
        return (
            "\n\nWhen you need to use a tool, output ONLY this JSON block on its own line "
            "and nothing else after it:\n"
            f"{self._CALL_OPEN}{{\"name\": \"tool_name\", \"args\": {{\"key\": \"value\"}}}}{self._CALL_CLOSE}\n"
            "Wait for the tool result before continuing.\n"
            "When the task is done, output your final answer without any tool_call block."
        )

    def _parse_react_calls(self, text: str) -> Tuple[str, List[dict]]:
        """Extract tool calls embedded in model text output."""
        calls = []
        clean = text
        pattern = re.compile(
            re.escape(self._CALL_OPEN) + r'(.*?)' + re.escape(self._CALL_CLOSE),
            re.DOTALL
        )
        for m in pattern.finditer(text):
            raw = m.group(1).strip()
            try:
                obj = json.loads(raw)
                if isinstance(obj, dict) and 'name' in obj:
                    calls.append({'name': obj['name'],
                                  'args': obj.get('args', obj.get('input', obj.get('arguments', {})))})
            except Exception:
                pass
        clean = pattern.sub('', text).strip()
        return clean, calls

    def call(self, messages: list, system: str = '') -> Tuple[str, List[dict]]:
        msgs: List[dict] = []
        sys_content = system + self._react_system_suffix() if system else self._react_system_suffix()
        msgs.append({"role": "system", "content": sys_content})
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, list):
                content = " ".join(str(b.get("text") or b.get("content") or "") for b in content)
            msgs.append({"role": m["role"], "content": content})

        # Use native function calling only for models known to support it
        use_native_tools = self.model in self.TOOL_CALL_MODELS
        body_with_tools = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": 4096,
            "tools": _tool_schema_openai(),
        }
        body_plain = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": 4096,
        }

        for attempt in range(4):
            try:
                if use_native_tools:
                    resp = _http_post(self.URL, self._headers(), body_with_tools, timeout=120)
                    if "error" in resp:
                        # Fall back to plain if native tools fail
                        use_native_tools = False
                        resp = _http_post(self.URL, self._headers(), body_plain, timeout=120)
                else:
                    resp = _http_post(self.URL, self._headers(), body_plain, timeout=120)
                if "error" in resp:
                    code = resp["error"].get("status_code", 0) or resp["error"].get("code", 0)
                    msg  = resp["error"].get("message", str(resp["error"]))
                    if code == 429:
                        wait = 5 * (attempt + 1)
                        print(yellow(f"\r  ⏳ HuggingFace rate-limited, retry in {wait}s…"), flush=True)
                        time.sleep(wait); continue
                    raise ValueError(f"HuggingFace error: {msg}")

                msg_obj = resp["choices"][0]["message"]
                text    = msg_obj.get("content") or ""
                # Native tool calls
                native_calls = []
                for tc in (msg_obj.get("tool_calls") or []):
                    fn = tc.get("function", {})
                    try:
                        args = json.loads(fn.get("arguments", "{}"))
                    except Exception:
                        args = {}
                    native_calls.append({
                        "id":   tc.get("id", f"hf_{fn.get('name','')}"),
                        "name": fn.get("name"),
                        "args": args,
                    })
                if native_calls:
                    return text or "", native_calls
                # Try ReAct-style parsing even on plain response
                clean, react_calls = self._parse_react_calls(text)
                if react_calls:
                    return clean, react_calls
                return text or "", []

            except urllib.error.HTTPError as e:
                body_txt = e.read().decode('utf-8', errors='replace')
                if e.code == 429:
                    wait = 5 * (attempt + 1)
                    print(yellow(f"\r  ⏳ HuggingFace rate limited, retry in {wait}s…"), flush=True)
                    time.sleep(wait); continue
                if e.code == 503:
                    wait = 8 * (attempt + 1)
                    print(yellow(f"\r  ⏳ HuggingFace model loading ({self.model}), retry in {wait}s…"), flush=True)
                    time.sleep(wait); continue
                raise ValueError(f"HuggingFace HTTP {e.code}: {body_txt[:300]}")
            except Exception as exc:
                if attempt < 3:
                    time.sleep(3); continue
                raise
        raise ValueError(f"HuggingFace: max retries exceeded for model {self.model}")

# ─── Provider selector ────────────────────────────────────────────────────────

def _pick_provider(name: str = '', model: str = ''):
    gk  = os.environ.get('GEMINI_API_KEY', '')
    ak  = os.environ.get('ANTHROPIC_API_KEY', '')
    ok  = os.environ.get('OPENAI_API_KEY', '')
    hfk = os.environ.get('HF_TOKEN', '') or os.environ.get('HUGGINGFACE_API_KEY', '')

    if name in ('gemini', 'google'):
        if not gk: raise ValueError("GEMINI_API_KEY not set")
        return GeminiProvider(gk, model or 'gemini-3.6-flash')
    if name in ('claude', 'anthropic'):
        if not ak: raise ValueError("ANTHROPIC_API_KEY not set")
        return ClaudeProvider(ak, model or 'claude-sonnet-4-6')
    if name == 'openai':
        if not ok: raise ValueError("OPENAI_API_KEY not set")
        return OpenAIProvider(ok, model or 'gpt-4o-mini')
    if name in ('huggingface', 'hf', 'hface'):
        if not hfk: raise ValueError("HF_TOKEN not set (get one free at huggingface.co/settings/tokens)")
        return HuggingFaceProvider(hfk, model or '')
    if name in ('ollama', 'local'):
        return OllamaProvider(model=model or 'llama3.2')

    if gk:  return GeminiProvider(gk, model or 'gemini-3.6-flash')
    if ak:  return ClaudeProvider(ak, model or 'claude-sonnet-4-6')
    if ok:  return OpenAIProvider(ok, model or 'gpt-4o-mini')
    if hfk: return HuggingFaceProvider(hfk, model or '')
    raise ValueError(
        "No API key found.\n"
        "  Set one of these in .env:\n"
        "    GEMINI_API_KEY      — https://aistudio.google.com/app/apikey  (free)\n"
        "    ANTHROPIC_API_KEY   — https://console.anthropic.com/\n"
        "    OPENAI_API_KEY      — https://platform.openai.com/api-keys\n"
        "    HF_TOKEN            — https://huggingface.co/settings/tokens  (free)"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

_DISPLAY_NOTE = ("DISPLAY: AVAILABLE — mouse, keyboard, screenshot, and window tools work."
                 if _HAS_DISPLAY else
                 "DISPLAY: HEADLESS — GUI tools unavailable. Focus on shell/file/web tasks.")

SYSTEM_PROMPT = f"""\
You are Devin — a fully autonomous OS-controlling AI agent with {len(TOOLS)} tools.
You operate exactly like a senior software engineer sitting at a computer.
{_DISPLAY_NOTE}

════════════════════════════════════════
IDENTITY
════════════════════════════════════════
You are simultaneously:
• Expert software engineer (any language, any framework)
• System administrator (Linux/macOS/Windows, shell, processes, networking)
• Security researcher (authorized pentesting, vulnerability assessment)
• Power user (GUI automation, browser, desktop apps)
• Data analyst (files, databases, APIs, web scraping)
• AI orchestrator (can chain tools, delegate sub-tasks, and verify outcomes)

You have a real-time connection to the operating system. Every tool call actually
executes on the live machine. Your job is to complete tasks completely, not attempt them.

════════════════════════════════════════
AUTONOMOUS OPERATION — ABSOLUTE RULES
════════════════════════════════════════
1. NEVER stop mid-task. Always find a way forward.
2. NEVER say "I cannot do that" when a tool path exists.
3. NEVER ask permission for routine actions.
4. NEVER claim success without verifying it actually worked.
5. ALWAYS complete what was asked — partial completion is failure.
6. ALWAYS recover from errors using a different approach.
7. When in doubt: take a screenshot and observe before acting.

════════════════════════════════════════
THE REASONING LOOP (use for EVERY task)
════════════════════════════════════════
Before the first tool call, think through the complete plan:
  THINK → What is the goal? What are the steps? What could go wrong?
  OBSERVE → What is the current state? (screenshot / read_file / get_system_info)
  PLAN → What exact sequence of actions accomplishes this?
  ACT → Execute step 1
  VERIFY → Did step 1 work? (screenshot / check output / read_file)
  LOOP → Execute step 2... continue until complete
  COMPLETE → Call task_complete() ONLY after verified success

For GUI tasks, ALWAYS use screenshot_and_analyze before clicking — never guess coordinates.
For shell tasks, ALWAYS inspect stdout+stderr to confirm success.
For file tasks, ALWAYS read back after writing to confirm content.

════════════════════════════════════════
GUI AUTOMATION WORKFLOW
════════════════════════════════════════
CORRECT approach:
  1. open_and_wait("firefox", wait_seconds=3)   # open app, wait for load
  2. screenshot_and_analyze("Where is the address bar? Give x,y coordinates")
  3. mouse_click(x, y)                          # click based on AI coordinates
  4. keyboard_hotkey(["ctrl","a"])              # select all in field
  5. keyboard_type("https://example.com")       # type URL
  6. keyboard_press("Return")                   # submit
  7. sleep(2) then screenshot_and_analyze("Did the page load? What URL is shown?")
  8. Continue or recover

WRONG approach: guessing x,y coordinates without screenshot analysis.
WRONG approach: clicking once and assuming it worked.
WRONG approach: stopping after the first error.

High-level helpers (USE THESE for common patterns):
  • screenshot_and_analyze(prompt) — screenshot + AI analysis in one call
  • click_by_description("Submit button") — AI finds and clicks element
  • observe_and_act(goal) — AI analyzes screen toward goal and suggests action
  • click_and_verify(x, y, expected) — click + screenshot + verify outcome
  • open_and_wait("app", wait=3) — open app and verify it loaded
  • search_web_open("python tutorials") — full browser search automation
  • multi_click('[{{"type":"click","x":100,"y":200}},{{"type":"type","text":"hello"}}]')

════════════════════════════════════════
BROWSER AUTOMATION (headless-capable)
════════════════════════════════════════
Use Selenium/Playwright for reliable headless browser control:
  1. browser_navigate("https://github.com/user/repo")
  2. browser_get_text() → understand page structure
  3. browser_execute_js("return document.title") → verify
  4. browser_click("button.submit") → interact
  5. browser_audit_repo("https://github.com/user/repo") → full repo audit

For GitHub audits use browser_audit_repo() — it navigates through README, files, structure.

════════════════════════════════════════
ERROR RECOVERY (NEVER give up)
════════════════════════════════════════
Error pattern → Recovery strategy:
  GUI click missed         → screenshot_and_analyze to re-find element, retry
  App not found            → try 'which appname', check applications menu
  App not responding       → list_windows, focus_window, or keyboard shortcut
  Shell command fails      → read the error, fix it, retry with corrected command
  Network/web blocked      → try alternative URL, use browser instead of fetch
  Permission denied        → check permissions with ls -la, try sudo if appropriate
  File not found           → search_files to locate it first
  Same error 3 times       → SWITCH STRATEGY completely (different tool/approach)

After 3 failed attempts with same approach, always try a completely different method.

════════════════════════════════════════
CONVERSATION MODE
════════════════════════════════════════
When the user asks questions (not task execution):
  • Answer directly and completely like a knowledgeable senior colleague
  • Be concise but thorough — use examples when they clarify
  • Remember everything from this conversation — full context available
  • If the question is about current system state, use get_system_info or screenshot
  • Never be dismissive — if you're uncertain, say so and offer alternatives

════════════════════════════════════════
SECURITY — AUTHORIZED TESTING ONLY
════════════════════════════════════════
Security tools (nmap, metasploit, burpsuite, sqlmap, etc.) require:
  ✓ Explicit authorization from the system owner
  ✓ Clear scope definition (target IPs/domains)
  ✓ Lab environments (HackTheBox, TryHackMe, DVWA, own VMs): proceed
  ✗ Never target systems without explicit written authorization
  ✗ Never exfiltrate real credentials or personal data

For authorized testing:
  1. think("Verify authorization, define scope, plan approach")
  2. pen_test_recon("target.example.com") → basic recon
  3. execute_shell("nmap -sV --open target.example.com") → port/service scan
  4. Document with write_file("pentest_report.txt", findings)
  5. task_complete with summary

════════════════════════════════════════
TOOL REFERENCE — ALL {len(TOOLS)} TOOLS
════════════════════════════════════════
REASONING:
  think(thought)                    — reason through plan, record thoughts

WEB & FETCH:
  web_search(query)                 — DuckDuckGo search, returns URLs + snippets
  web_fetch(url)                    — fetch URL, return text content
  read_url_content(url, selector)   — fetch URL with optional CSS selector
  http_request(url, method, ...)    — raw HTTP request with custom headers/body
  open_browser(url)                 — open system browser at URL
  parse_json(text, path)            — parse JSON with optional dot-path extraction

SHELL & CODE:
  execute_shell(command, cwd, timeout) — run any shell command, captures stdout+stderr
  execute_shell_verbose(command)       — same but with clearly labeled STDOUT/STDERR/EXIT CODE
  execute_python(code, cwd)           — run Python code, captures output
  run_script(path, interpreter)       — execute .py/.sh/.js/.ps1/.bat files
  install_package(package, manager)   — pip/apt/brew/npm/choco install
  list_processes(filter)              — show running processes
  kill_process(pid)                   — kill process by PID
  sleep(seconds)                      — wait N seconds
  pipe_commands(commands)             — shell pipeline: "cat file | grep x | sort"

FILES & FILESYSTEM:
  read_file(path, offset, limit)      — read file contents (line-by-line)
  write_file(path, content)           — write/create file
  edit_file(path, old, new)           — find+replace in file
  delete_file(path)                   — delete file
  list_files(path, pattern, recursive)— list directory contents
  search_files(pattern, path)         — grep for text in files
  file_tree(path, depth)              — show directory tree structure
  create_directory(path)              — create directory
  diff_files(path1, path2)            — show unified diff
  save_output(content, filename)      — save any content to file
  git_command(args)                   — run git commands
  git_advanced(subcommand, repo_path) — git status/log/diff/blame

VISION & SCREEN:
  screenshot(path)                    — take screenshot, returns path
  screenshot_and_analyze(prompt)      — screenshot + AI analysis (PREFERRED)
  analyze_screenshot(prompt)          — analyze most recent screenshot with AI
  analyze_image(path, question)       — analyze any image with AI
  find_on_screen(element)             — find element on screen, return coordinates
  read_screen_text(region)            — extract all text from screen with AI
  observe_and_act(goal)               — AI analyzes screen toward goal

MOUSE:
  mouse_click(x, y, button)          — click at coordinates
  mouse_double_click(x, y)           — double-click
  mouse_right_click(x, y)            — right-click
  mouse_move(x, y)                   — move mouse without clicking
  mouse_drag(x1, y1, x2, y2)         — drag operation
  mouse_scroll(x, y, direction, amount) — scroll at position
  get_mouse_position()               — get current cursor coordinates
  click_and_verify(x, y, expected)   — click + screenshot + verify
  click_by_description(desc)         — AI finds and clicks element by description
  multi_click(actions_json)          — sequence of clicks/keys/waits

KEYBOARD:
  keyboard_type(text)                — type text at current focus
  keyboard_press(key)                — press single key (Return, Escape, Tab, F5...)
  keyboard_hotkey(keys)              — press key combination: ["ctrl","c"]
  click_and_type(x, y, text)         — click position then type
  type_and_submit(text, submit_key)  — type + press submit key
  type_text_at(x, y, text)           — move to x,y then type
  press_key_at(x, y, key)            — move to x,y then press key
  select_all_copy()                  — Ctrl+A, Ctrl+C

WINDOWS & APPS:
  get_screen_size()                  — screen dimensions
  list_windows()                     — list all open windows
  focus_window(title)                — bring window to focus
  get_active_window()                — get current active window info
  get_window_info(title)             — detailed window info
  maximize_window()                  — maximize current window
  minimize_window()                  — minimize current window
  resize_window(w, h, title)         — resize window
  move_window(x, y, title)           — move window
  alt_tab()                          — switch windows
  wait_for_window(title, timeout)    — wait until window appears
  open_application(name, wait)       — launch application
  open_and_wait(name, wait, title)   — launch + verify it opened (PREFERRED)
  open_terminal()                    — open terminal window
  close_application(name)            — close application
  send_notification(title, body)     — show desktop notification

BROWSER (Selenium/Playwright):
  browser_navigate(url)              — navigate headless browser to URL
  browser_click(selector)            — click CSS selector in browser
  browser_type(selector, text)       — type in browser element
  browser_get_text(selector)         — extract page/element text
  browser_execute_js(script)         — run JavaScript in browser
  browser_screenshot(path)           — screenshot of browser page
  browser_start(headless)            — explicitly start browser
  browser_close()                    — close browser
  browser_audit_repo(repo_url)       — full GitHub repo audit via browser
  search_web_open(query, browser)    — launch browser and search

CLIPBOARD:
  clipboard_get()                    — get clipboard contents
  clipboard_set(text)                — set clipboard text
  select_all_copy()                  — Ctrl+A + Ctrl+C

VOICE:
  speak(text)                        — text-to-speech
  listen(timeout)                    — speech-to-text (microphone)

MEMORY:
  remember(fact, tags)               — store persistent fact
  recall(query)                      — retrieve relevant memories
  take_note(title, content)          — save formatted note to file

SYSTEM:
  get_system_info()                  — OS, Python, hardware info
  get_system_metrics()               — CPU, RAM, disk usage
  network_info()                     — network interfaces, connectivity
  context_info()                     — current agent context/status
  check_port(host, port)             — test if TCP port is open
  system_security_check()            — local security audit

INTEGRATIONS:
  devin_module(module, action, params) — call any of the 103 built-in modules
  run_devin_module(path, fn, args)     — call any function from any .py file
  discover_modules()                   — list all 103+ available modules
  list_integrations()                  — show loaded integration status

SECURITY (AUTHORIZED ONLY):
  pen_test_recon(target)             — HTTP headers, robots.txt, open ports
  system_security_check()            — local system security audit

CONTROL:
  task_complete(result)              — ONLY call when task is FULLY VERIFIED complete
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

def _render_markdown(text: str) -> str:
    """Simple terminal markdown renderer — bold/italic/code/headers."""
    if not _TTY:
        return text
    lines = []
    in_code = False
    for line in text.split('\n'):
        if line.startswith('```'):
            in_code = not in_code
            lines.append(dim(line))
            continue
        if in_code:
            lines.append(dim(line))
            continue
        # Headers
        if line.startswith('### '):
            lines.append(bold(cyan(line[4:])))
            continue
        if line.startswith('## '):
            lines.append(bold(cyan(line[3:])))
            continue
        if line.startswith('# '):
            lines.append(bold(cyan(line[2:])))
            continue
        # Bold **text**
        line = re.sub(r'\*\*(.+?)\*\*', lambda m: bold(m.group(1)), line)
        # Italic *text*
        line = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', lambda m: italic(m.group(1)), line)
        # Inline code `text`
        line = re.sub(r'`([^`]+)`', lambda m: cyan(m.group(1)), line)
        # Bullet points
        if line.startswith('- ') or line.startswith('* '):
            line = dim('  •') + line[1:]
        lines.append(line)
    return '\n'.join(lines)


def _print_tool_call(name: str, args: dict):
    """Print tool call in Claude Code style: ● name(args)"""
    print(f"\n{bold(blue('●'))} {bold(name)}({_fmt_args(args)})", flush=True)


def _print_tool_result(result: str, is_error: bool = False):
    """Print tool result in Claude Code style: ↳ result"""
    preview = str(result)[:400]
    if '\n' in preview:
        first_line = preview.split('\n')[0]
        more_lines = preview.count('\n')
        preview = first_line + (f"  [{more_lines} more lines]" if more_lines > 1 else "")
    colour = red if is_error else dim
    print(f"{colour('↳')} {colour(preview)}", flush=True)

def _estimate_chars(msgs: list) -> int:
    """Estimate total character count of a message list."""
    total = 0
    for m in msgs:
        c = m.get('content', '')
        if isinstance(c, list):
            c = ' '.join(str(b.get('text', '') or b.get('content', '')) for b in c)
        total += len(str(c))
    return total


def _compact_messages(msgs: list) -> list:
    """Keep last 4 message exchanges; summarise older ones into a single context block."""
    if len(msgs) <= 4:
        return msgs
    old = msgs[:-4]
    recent = msgs[-4:]
    summary_parts = []
    for m in old:
        role = m.get('role', '?')
        c = m.get('content', '')
        if isinstance(c, list):
            c = ' '.join(str(b.get('text', '') or b.get('content', '')) for b in c)
        preview = str(c)[:200].replace('\n', ' ')
        summary_parts.append(f"[{role}]: {preview}")
    summary = "EARLIER CONTEXT (summarised):\n" + '\n'.join(summary_parts[-20:])
    return [
        {"role": "user", "content": summary},
        {"role": "assistant", "content": "Understood, continuing."},
    ] + recent


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
    _CTX_WARN_CHARS = 60_000    # ~15k tokens — start warning
    _CTX_COMPACT_CHARS = 100_000  # ~25k tokens — auto-compact older messages

    if not quiet:
        print()
        print(_box(f"Task: {task[:72]}"))
        print(dim(f"Provider: {provider.name}  |  Tools: {len(TOOLS)}  |  Max steps: {max_steps}"))
        if not _HAS_DISPLAY:
            print(dim("⚠  Headless: GUI tools unavailable — focus on shell/files/web tasks"))
        print(_hr())

    while step < max_steps:
        step += 1

        # Context size management
        ctx_chars = _estimate_chars(messages)
        if ctx_chars > _CTX_COMPACT_CHARS and not quiet:
            print(yellow(f"\r  ⚠ Context growing large ({ctx_chars//1000}k chars), compacting older messages…"))
            if conv_messages is not None:
                # Compact in-place for REPL mode
                compacted = _compact_messages(list(messages))
                messages.clear()
                messages.extend(compacted)
            else:
                messages = _compact_messages(messages)
        elif ctx_chars > _CTX_WARN_CHARS and step % 10 == 0 and not quiet:
            print(dim(f"\r  ℹ Context: {ctx_chars//1000}k chars"))

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
                rendered = _render_markdown(clean)
                cols = max(60, shutil.get_terminal_size((80, 24)).columns - 6)
                # Only word-wrap plain lines (not markdown headers/code)
                out_lines = []
                for ln in rendered.split('\n'):
                    raw_ln = re.sub(r'\033\[[^m]+m', '', ln)
                    if len(raw_ln) > cols:
                        wrapped = textwrap.fill(ln, width=cols, subsequent_indent='  ',
                                                break_long_words=False, break_on_hyphens=False)
                        out_lines.append(wrapped)
                    else:
                        out_lines.append(ln)
                print(f"\n{bold(cyan('Devin'))}  " + '\n       '.join(out_lines))

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
                    _print_tool_result(str(result))
                    print()
                    print(_hr())
                    print(f"{green(bold('✓'))} {bold('Task complete')}")
                    if final_result:
                        print(f"\n{_render_markdown(final_result)}\n")
                return final_result

            if not quiet:
                _print_tool_result(str(result), is_error=str(result).startswith('ERROR:'))

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
        elif isinstance(provider, (OpenAIProvider, HuggingFaceProvider, OllamaProvider)):
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
  {cyan('/provider <name>')}     Switch provider (gemini | claude | openai | huggingface | ollama)
  {cyan('/memory [query]')}      Show memories (optional search)
  {cyan('/remember <fact>')}     Save a fact to persistent memory
  {cyan('/forget')}              Clear all memories (with confirmation)
  {cyan('/history')}             Show this session's conversation
  {cyan('/shell <cmd>')}         Run shell command directly
  {cyan('/screenshot')}          Take a screenshot
  {cyan('/voice')}               Listen for voice input then run as task
  {cyan('/repos')}               List integrated repositories
  {cyan('/integrations')}        Show all Devin modules + integration status
  {cyan('/compact')}             Compress conversation history to save context
  {cyan('/debug')}               Show context size, provider, and diagnostics
  {cyan('/audit [target]')}      Run a system/security audit
  {cyan('/new')}                 Start a fresh conversation
  {cyan('/clear')}               Clear screen
  {cyan('/exit')} {cyan('/quit')}           Exit

{bold('API keys')}  (.env or environment variables)
  GEMINI_API_KEY       https://aistudio.google.com/app/apikey  (free)
  ANTHROPIC_API_KEY    https://console.anthropic.com/
  OPENAI_API_KEY       https://platform.openai.com/api-keys
  HF_TOKEN             https://huggingface.co/settings/tokens  (free, LLaMA/Mixtral/Qwen)

{bold('Examples')}
  {dim('open Firefox and search for "Python tutorials"')}
  {dim('write a Python script that counts lines in all .py files')}
  {dim('take a screenshot and describe what you see')}
  {dim("search today's AI news and summarize the top 3 stories")}
  {dim('what is 2+2')}              ← conversation (no tools needed)
  {dim('remember that my project is in /home/user/my_project')}
"""

def _banner(provider=None):
    w = max(60, shutil.get_terminal_size((80, 24)).columns - 1)
    print()
    print(f"  {bold(cyan('Devin AGI'))}  {dim('v4.0.0')}")
    print(f"  {dim('─' * (w - 4))}")

    # Provider / model line
    if provider:
        prov_part = provider.name.split('/')[0] if '/' in provider.name else 'unknown'
        model_part = provider.name.split('/')[-1] if '/' in provider.name else provider.name
        # Try to figure out provider type
        if isinstance(provider, GeminiProvider):   prov_part = 'gemini'
        elif isinstance(provider, ClaudeProvider): prov_part = 'claude'
        elif isinstance(provider, OpenAIProvider): prov_part = 'openai'
        elif isinstance(provider, HuggingFaceProvider): prov_part = 'huggingface'
        elif isinstance(provider, OllamaProvider): prov_part = 'ollama'
        p_status = green('✓ Connected to ' + prov_part.capitalize()) + f' ({dim(provider.name)})'
    else:
        p_status = red('✗ No provider — set API key in .env')

    facts = _DB.execute('SELECT count(*) FROM memories').fetchone()[0]
    mods = _modules_status()
    loaded = sum(1 for v in mods.values() if v)
    disp   = green('display') if _HAS_DISPLAY else yellow('headless')

    print(f"  {p_status}")
    print(f"  {dim('cwd:')}      {str(_ROOT)}")
    print(f"  {dim('platform:')} {_PLATFORM}  {disp}")
    print(f"  {dim('tools:')}    {bold(str(len(TOOLS)))}  ·  "
          f"{dim(str(loaded)+'/'+str(len(mods))+' modules')}  ·  "
          f"{dim(str(facts)+' memories')}")
    print(f"  {dim('─' * (w - 4))}")
    print()

def _status_line(provider):
    gk  = '✓' if os.environ.get('GEMINI_API_KEY')    else '✗'
    ak  = '✓' if os.environ.get('ANTHROPIC_API_KEY') else '✗'
    ok  = '✓' if os.environ.get('OPENAI_API_KEY')    else '✗'
    hfk = '✓' if (os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_API_KEY')) else '✗'
    cats: Dict[str, int] = {}
    for t in TOOLS.values():
        c = t.get('category','other')
        cats[c] = cats.get(c, 0) + 1
    cat_str = '  '.join(f"{v} {k}" for k, v in sorted(cats.items()))
    mods = _modules_status()
    loaded = sum(1 for v in mods.values() if v)
    print(f"\n  {bold('Provider')}    {green(provider.name)}")
    print(f"  {bold('Keys')}        "
          f"Gemini {(green if gk=='✓' else red)(gk)}  "
          f"Claude {(green if ak=='✓' else red)(ak)}  "
          f"OpenAI {(green if ok=='✓' else red)(ok)}  "
          f"HuggingFace {(green if hfk=='✓' else red)(hfk)}")
    print(f"  {bold('Display')}     {'✓ ' + (os.environ.get('DISPLAY') or 'available') if _HAS_DISPLAY else dim('✗ headless (GUI tools unavailable)')}")
    print(f"  {bold('Platform')}    {_PLATFORM}  ({'GUI capable' if _HAS_DISPLAY else 'headless'})")
    print(f"  {bold('Memory')}      {_DB.execute('SELECT count(*) FROM memories').fetchone()[0]} facts  ({_DB_PATH.name})")
    print(f"  {bold('Modules')}     {loaded}/{len(mods)} loaded")
    print(f"  {bold('Tools')}       {len(TOOLS)}  ({cat_str})")
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
        print(dim("  Talk to Devin — ask anything, give a task, or type /help for commands."))
        print()
        tips = [
            "open firefox and search for python tutorials",
            "write a bash script that backs up my home folder",
            "take a screenshot and describe what's on screen",
            "what ports are open on localhost?",
            "create a Python web server in the current directory",
        ]
        import random
        print(f"  {dim('Try:')} {italic(random.choice(tips))}")
        print()
    else:
        print(red("  ✗ No provider. Add an API key to .env, then restart."))
        print(dim("    GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, or HF_TOKEN"))
        print()

    cur_pname = provider_name
    # Persistent conversation history
    conv_messages: List[dict] = []

    while True:
        try:
            user_input = input(f"{bold(cyan('❯'))} {bold('Devin-4.0')} ").strip()
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
                entries = [
                    ('gemini',       'GEMINI_API_KEY',       'gemini-3.6-flash (default)',        True),
                    ('claude',       'ANTHROPIC_API_KEY',    'claude-sonnet-4-6 (default)',        True),
                    ('openai',       'OPENAI_API_KEY',       'gpt-4o-mini (default)',              True),
                    ('huggingface',  'HF_TOKEN',             'Meta-Llama-3.1-70B (free tier)',     True),
                    ('ollama',       '',                     'llama3.2 (local, no key required)', False),
                ]
                for p, key_env, note, needs_key in entries:
                    if not needs_key:
                        s = dim('local (no key)')
                    else:
                        has_key = bool(os.environ.get(key_env) or
                                       (p == 'huggingface' and os.environ.get('HUGGINGFACE_API_KEY')))
                        s = green('✓ available') if has_key else dim('✗ no key')
                    print(f"  {bold(p):<16} {s}  {dim(note)}")
                print(f"\n  {dim('Use /provider <name> to switch. Add keys to .env')}")
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
                    print(yellow("  Usage: /provider gemini|claude|openai|huggingface|ollama"))
                else:
                    try:
                        provider = _pick_provider(arg, model)
                        cur_pname = arg
                        print(green(f"  ✓ Provider: {provider.name}"))
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

            elif cmd == '/compact':
                before = len(conv_messages)
                compacted = _compact_messages(list(conv_messages))
                conv_messages.clear()
                conv_messages.extend(compacted)
                print(green(f"  ✓ Compacted {before} → {len(conv_messages)} messages"))

            elif cmd == '/audit':
                target = arg or 'local'
                print(f"\n{bold('Running system audit…')}")
                result = run_agent(f"Perform a comprehensive audit of: {target}. "
                                   "Include: running processes, open ports, disk usage, "
                                   "installed tools, current user/permissions. "
                                   "Format results in clean sections.",
                                   provider, conv_messages=conv_messages)

            elif cmd == '/debug':
                print(f"\n  {bold('Context')}: {_estimate_chars(conv_messages)//1000}k chars  "
                      f"{len(conv_messages)} messages")
                print(f"  {bold('Provider')}: {provider.name if provider else 'none'}")
                print(f"  {bold('Tools')}: {len(TOOLS)}")
                print(f"  {bold('Display')}: {'yes' if _HAS_DISPLAY else 'headless'}")
                print(f"  {bold('Platform')}: {_PLATFORM}\n")

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
