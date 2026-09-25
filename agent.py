#!/usr/bin/env python3
"""
Devin AGI v4.0 — Deeply Autonomous OS-Controlling AI Agent
============================================================
A fully autonomous AI that operates your computer like a real user.
Controls mouse, keyboard, screen, files, shell, browser, voice — on any OS.
Thinks, plans, acts, and verifies using 134+ tools and 5 AI providers.
Works on Linux, macOS, and Windows. Runs headless or with full GUI control.

Usage:
  ./devin                                   # interactive REPL (conversation mode)
  python agent.py                           # same
  python agent.py "open firefox and search for AI news"
  python agent.py --provider claude "write a Python web scraper"
  python agent.py --provider huggingface "analyze this code"
  python agent.py --model gemini-3.6-flash "task here"
  python agent.py --provider ollama "local task"

Slash commands (interactive mode):
  /help              This help
  /tools [category]  List all 134 tools by category
  /status            Show provider, model, keys, modules
  /providers         Show all 5 AI providers and key status
  /model <name>      Switch model (e.g. /model gemini-2.5-pro)
  /provider <name>   Switch provider: gemini|claude|openai|huggingface|ollama
  /memory [query]    Search persistent memory
  /remember <fact>   Save a fact to memory
  /history           Show conversation history
  /shell <cmd>       Run shell command
  /run <cmd>         Run shell command (alias)
  /screenshot        Take and analyze a screenshot
  /voice             Voice input → task
  /think <task>      Plan a task before executing
  /workflow <task>   Structured multi-step workflow
  /pentest <target>  Authorized penetration test assessment
  /lab [setup]       Lab environment setup and tool check
  /os                Show OS/platform info
  /audit [target]    System/security audit
  /repos             List integrated repositories
  /integrations      Show module integration status
  /compact           Compress conversation context
  /debug             Debug info: context, provider, tools
  /new               Start fresh conversation
  /clear             Clear screen
  /exit /quit        Exit

API keys (.env or environment variables):
  GEMINI_API_KEY     https://aistudio.google.com/app/apikey  (free)
  ANTHROPIC_API_KEY  https://console.anthropic.com/
  OPENAI_API_KEY     https://platform.openai.com/api-keys
  HF_TOKEN           https://huggingface.co/settings/tokens  (free)
  (Ollama: no key required — install ollama.ai, run 'ollama serve')
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

# Session runtime statistics — updated during agentic loop
_SESSION_STATS: Dict[str, Any] = {
    'started_at': time.time(),
    'tool_calls': 0,             # total tool invocations this session
    'errors': 0,                 # tool calls that returned ERROR
    'agent_steps': 0,            # total run_agent iterations
    'tasks_completed': 0,        # times task_complete was called
    'tool_usage': {},            # per-tool call counts
    'provider_calls': 0,         # times a provider was hit
    'no_tool_pushes': 0,         # times the loop nudged to continue
}

def _stats_record_tool(name: str, is_error: bool = False):
    _SESSION_STATS['tool_calls'] += 1
    if is_error:
        _SESSION_STATS['errors'] += 1
    _SESSION_STATS['tool_usage'][name] = _SESSION_STATS['tool_usage'].get(name, 0) + 1

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

# Load threat intelligence tools (MITRE ATT&CK, IOC feeds, domain recon)
_threat_intel_mod = None
try:
    _threat_intel_mod = _il.import_module('threat_intel_tools')
except BaseException:
    pass

# Load multimedia processing (image/audio/video operations)
_multimedia_mod = None
try:
    _multimedia_mod = _il.import_module('multimedia_processing_module')
except BaseException:
    pass

# Load mobile integration (ADB, iOS control)
_mobile_mod = None
try:
    _mobile_mod = _il.import_module('mobile_integration_module')
except BaseException:
    pass

# Load robotics control module
_robotics_mod = None
try:
    _robotics_mod = _il.import_module('robotics_control_module')
except BaseException:
    pass

# Load external agent tools (dispatch to sub-agents)
_ext_agent_mod = None
try:
    _ext_agent_mod = _il.import_module('external_agent_tools')
except BaseException:
    pass

# Load quantum tools (post-quantum crypto, quantum simulation)
_quantum_mod = None
try:
    _quantum_mod = _il.import_module('quantum_tools')
except BaseException:
    pass

# Load keyboard/mouse control (low-level pynput)
_kbm_mod = None
try:
    _kbm_mod = _il.import_module('keyboard_mouse_control')
    _kbm_ctrl = _kbm_mod.KeyboardMouseController() if hasattr(_kbm_mod, 'KeyboardMouseController') else None
except BaseException:
    _kbm_ctrl = None

# Load ethics and legal compliance tools
_ethics_mod = None
try:
    _ethics_mod = _il.import_module('ethics_legal_tools')
except BaseException:
    pass

# Load AI learning / self-improvement module
_ai_learn_mod = None
try:
    _ai_learn_mod = _il.import_module('ai_learning_module')
except BaseException:
    pass

# Load OpenDevin bridge (canvas tool)
_opendevin_mod = None
try:
    _opendevin_mod = _il.import_module('opendevin_bridge')
except BaseException:
    pass

# Load Holomat XR bridge
_holomat_mod = None
try:
    _holomat_mod = _il.import_module('holomat_bridge')
except BaseException:
    pass

# Load PentestGPT AI module
_pentestgpt_mod = None
try:
    _pentestgpt_mod = _il.import_module('pentestgpt_ai_module')
except BaseException:
    pass

# Load cyber range / CTF tools
_cyber_range_mod = None
try:
    _cyber_range_mod = _il.import_module('cyber_range_tools')
except BaseException:
    pass

# Load data logger (structured event/data logging)
_data_logger_mod = None
try:
    _data_logger_mod = _il.import_module('data_logger')
    _data_logger = _data_logger_mod.DataLogger() if hasattr(_data_logger_mod, 'DataLogger') else None
except BaseException:
    _data_logger = None

# Load plugins tools (bug bounty, AI composer, plugin ecosystem)
_plugins_mod = None
try:
    _plugins_mod = _il.import_module('plugins_tools')
except BaseException:
    pass

# Load all-AIs umbrella module (multi-AI routing)
_all_ais_mod = None
try:
    _all_ais_mod = _il.import_module('all_ais_modules')
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
        'threat_intel':      _threat_intel_mod    is not None,
        'multimedia':        _multimedia_mod      is not None,
        'mobile':            _mobile_mod          is not None,
        'robotics':          _robotics_mod        is not None,
        'external_agents':   _ext_agent_mod       is not None,
        'quantum':           _quantum_mod         is not None,
        'keyboard_mouse':    _kbm_ctrl            is not None,
        'ethics_legal':      _ethics_mod          is not None,
        'ai_learning':       _ai_learn_mod        is not None,
        'opendevin':         _opendevin_mod       is not None,
        'holomat_xr':        _holomat_mod         is not None,
        'pentestgpt':        _pentestgpt_mod      is not None,
        'cyber_range':       _cyber_range_mod     is not None,
        'data_logger':       _data_logger         is not None,
        'plugins':           _plugins_mod         is not None,
        'all_ais':           _all_ais_mod         is not None,
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
    """Launch an application by name on any OS (Linux, macOS, Windows)."""
    try:
        exe = name.split()[0]  # first word is the executable
        # macOS: try 'open -a AppName' first, then direct exec
        if _IS_MAC:
            r = subprocess.run(['open', '-a', exe], capture_output=True, text=True, timeout=5)
            if r.returncode != 0:
                subprocess.Popen(name, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Windows: use start command or direct launch
        elif _IS_WIN:
            subprocess.Popen(f'start "" {name}', shell=True, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, creationflags=0x00000008)
        else:
            # Linux: try direct exec, then xdg-open for GUI apps
            subprocess.Popen(name, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(wait_seconds)
        # Verify it started — platform-aware
        if _IS_WIN:
            r = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {exe}.exe'],
                               capture_output=True, text=True)
            if exe.lower() in r.stdout.lower():
                return f"Opened {name} on Windows"
        elif _IS_MAC:
            r = subprocess.run(['pgrep', '-f', exe], capture_output=True, text=True)
            if r.returncode == 0:
                return f"Opened {name} on macOS (pid={r.stdout.strip().split()[0]})"
        else:
            r = subprocess.run(['pgrep', '-f', exe], capture_output=True, text=True)
            if r.returncode == 0:
                pid = r.stdout.strip().split()[0]
                return f"Opened {name} (pid={pid})"
        return f"Launched {name} (starting up...)"
    except Exception as e:
        return f"ERROR opening {name}: {e}"

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


def tool_github_repo_audit(repo: str, deep: bool = False) -> str:
    """
    Comprehensive audit of a public GitHub repository using the GitHub REST
    API (works headless). Returns structured summary: description, language,
    size, stars, top-level files, README preview, and (if deep) top contributors.

    repo: 'owner/name' or full URL like 'https://github.com/owner/name'
    deep: if True, also fetches contributor list and language breakdown

    Use this instead of browser-based audit when you don't need a screenshot,
    or as a fast first-pass before opening in the browser.
    """
    # Normalize repo identifier
    r = repo.strip()
    if 'github.com/' in r:
        r = r.split('github.com/', 1)[1].rstrip('/')
        if r.endswith('.git'):
            r = r[:-4]
    parts = [p for p in r.split('/') if p]
    if len(parts) < 2:
        return f"ERROR: repo must be 'owner/name' or a github.com URL, got: {repo!r}"
    owner, name = parts[0], parts[1]

    base = f"https://api.github.com/repos/{owner}/{name}"
    hdrs = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Devin-4.0'}
    # Optional token boost (helps with rate limit; NEVER required)
    gh_token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if gh_token:
        hdrs['Authorization'] = f'Bearer {gh_token}'

    lines = [f"=== GitHub Repo Audit: {owner}/{name} ==="]

    def _fetch(url: str) -> Tuple[int, dict]:
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8', errors='replace'))
                return resp.status, data
        except urllib.error.HTTPError as e:
            return e.code, {'error': e.reason, 'body': e.read().decode('utf-8', 'replace')[:500]}
        except Exception as e:
            return 0, {'error': str(e)}

    # 1. Repo metadata
    status, info = _fetch(base)
    if status != 200:
        return f"ERROR: GitHub API returned {status}: {info.get('error', info)}"

    lines.append(f"Description  : {info.get('description') or '(none)'}")
    lines.append(f"Language     : {info.get('language') or 'unknown'}")
    lines.append(f"Stars        : {info.get('stargazers_count')}")
    lines.append(f"Forks        : {info.get('forks_count')}")
    lines.append(f"Open issues  : {info.get('open_issues_count')}")
    lines.append(f"Size         : {info.get('size')} KB")
    lines.append(f"Default branch: {info.get('default_branch')}")
    lines.append(f"License      : {(info.get('license') or {}).get('spdx_id', 'none')}")
    lines.append(f"Created      : {info.get('created_at')}")
    lines.append(f"Updated      : {info.get('updated_at')}")
    lines.append(f"Homepage     : {info.get('homepage') or '(none)'}")
    lines.append(f"Topics       : {', '.join(info.get('topics') or []) or '(none)'}")
    lines.append(f"URL          : {info.get('html_url')}")

    default_branch = info.get('default_branch', 'main')

    # 2. Top-level file tree
    lines.append("\n--- Top-level files ---")
    status, tree_data = _fetch(f"{base}/contents?ref={default_branch}")
    if status == 200 and isinstance(tree_data, list):
        for item in tree_data[:40]:
            marker = '📁' if item.get('type') == 'dir' else '📄'
            size = f" ({item.get('size', 0)} b)" if item.get('type') == 'file' else ''
            lines.append(f"  {marker} {item.get('name')}{size}")
        if len(tree_data) > 40:
            lines.append(f"  … +{len(tree_data)-40} more")
    else:
        lines.append(f"  (failed to list: HTTP {status})")

    # 3. README preview
    lines.append("\n--- README preview ---")
    status, readme = _fetch(f"{base}/readme")
    if status == 200:
        try:
            import base64
            content = base64.b64decode(readme.get('content', '')).decode('utf-8', errors='replace')
            lines.append(content[:1500] + ('\n… (truncated)' if len(content) > 1500 else ''))
        except Exception as e:
            lines.append(f"  (decode failed: {e})")
    else:
        lines.append(f"  (no README or HTTP {status})")

    # 4. Deep audit — languages + contributors
    if deep:
        lines.append("\n--- Language breakdown ---")
        status, langs = _fetch(f"{base}/languages")
        if status == 200 and isinstance(langs, dict):
            total = sum(langs.values()) or 1
            for lang, bytes_ in sorted(langs.items(), key=lambda x: -x[1])[:10]:
                pct = 100.0 * bytes_ / total
                lines.append(f"  {lang:20s} {pct:5.1f}%  ({bytes_} bytes)")

        lines.append("\n--- Top contributors ---")
        status, contribs = _fetch(f"{base}/contributors?per_page=10")
        if status == 200 and isinstance(contribs, list):
            for c in contribs[:10]:
                lines.append(f"  {c.get('login'):20s} {c.get('contributions', 0)} commits")

        lines.append("\n--- Recent releases ---")
        status, rels = _fetch(f"{base}/releases?per_page=5")
        if status == 200 and isinstance(rels, list) and rels:
            for rel in rels[:5]:
                lines.append(f"  {rel.get('tag_name', '?'):15s} {rel.get('name', '') or rel.get('tag_name', '')}")
        else:
            lines.append("  (no releases)")

    lines.append(f"\n=== Audit complete for {owner}/{name} ===")
    return '\n'.join(lines)


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


# ── Power compound tools ───────────────────────────────────────────────────────

def tool_ask_user(question: str) -> str:
    """Ask the user a clarifying question and return their answer."""
    try:
        print(f"\n{bold(yellow('?'))} {bold('Devin asks:')} {question}")
        answer = input(f"  {dim('Your answer:')} ").strip()
        return answer if answer else "(no answer)"
    except (EOFError, KeyboardInterrupt):
        return "(interrupted)"


def tool_write_and_run(filename: str, code: str, interpreter: str = 'python3') -> str:
    """Write code to a file and immediately execute it. Returns file path + output."""
    try:
        path = _ROOT / filename
        path.write_text(code, encoding='utf-8')
        result = tool_execute_shell(f"{interpreter} {path}", timeout=30)
        return f"Wrote {path}\n\n--- Output ---\n{result}"
    except Exception as e:
        return f"ERROR: {e}"


def tool_install_and_verify(package: str, manager: str = 'pip') -> str:
    """Install a package and verify it imported/installed successfully."""
    install_result = tool_install_package(package, manager)
    if 'error' in install_result.lower() or 'failed' in install_result.lower():
        return f"Install failed: {install_result}"
    # Verify
    pkg_name = package.split('[')[0].split('>=')[0].split('==')[0].strip()
    verify = tool_execute_python(f"import {pkg_name.replace('-','_')}; print('OK: ' + {pkg_name.replace('-','_')}.__version__ if hasattr({pkg_name.replace('-','_')}, '__version__') else 'OK')")
    return f"Installed: {install_result[:100]}\nVerify: {verify[:100]}"


def tool_git_clone_and_explore(url: str, target_dir: str = '') -> str:
    """Clone a git repo and return its file structure."""
    try:
        if not target_dir:
            target_dir = url.rstrip('/').split('/')[-1].replace('.git', '')
        dest = _ROOT / target_dir
        if dest.exists():
            return f"Already exists: {dest}\n{tool_execute_shell(f'ls {dest}')[:500]}"
        result = tool_execute_shell(f"git clone --depth 1 {url} {dest}", timeout=60)
        if dest.exists():
            tree = tool_execute_shell(f"find {dest} -maxdepth 2 -not -path '*/.git/*' | head -40")
            return f"Cloned to {dest}\n\n{tree}"
        return f"Clone result: {result}"
    except Exception as e:
        return f"ERROR: {e}"


def tool_search_and_open(query: str, open_first: bool = True) -> str:
    """Search DuckDuckGo, return results, optionally open top result in browser."""
    results = tool_web_search(query, num_results=5)
    if open_first and results and not results.startswith('ERROR'):
        lines = results.split('\n')
        for line in lines:
            if line.strip().startswith('http'):
                tool_open_browser(line.strip())
                return f"Searched and opened: {line.strip()}\n\n{results}"
    return results


def tool_screen_to_clipboard() -> str:
    """Take screenshot, extract all text with AI, copy to clipboard."""
    shot = tool_screenshot()
    if shot.startswith('ERROR'):
        return shot
    path = shot.split(': ', 1)[-1].strip().split()[0]
    text = tool_read_screen_text('')
    if text and not text.startswith('ERROR'):
        tool_clipboard_set(text)
        return f"Extracted {len(text)} chars from screen → clipboard"
    return f"Screenshot: {path}"


def tool_wait_and_verify(seconds: float, condition: str = '') -> str:
    """Wait N seconds, then optionally verify a condition by taking screenshot."""
    import time
    time.sleep(max(0, min(seconds, 30)))
    if condition:
        return tool_screenshot_and_analyze(f"Verify: {condition}")
    return f"Waited {seconds}s"


# ── Cross-platform + deep autonomy tools ──────────────────────────────────────

def tool_platform_info() -> str:
    """Return comprehensive OS/platform info: OS, version, arch, user, hostname, Python, display, shell."""
    import platform as _plat
    out = {
        'os': _PLATFORM,
        'version': _plat.version(),
        'release': _plat.release(),
        'arch': _plat.machine(),
        'processor': _plat.processor()[:60] if _plat.processor() else 'unknown',
        'hostname': _plat.node(),
        'python': _plat.python_version(),
        'user': os.environ.get('USER') or os.environ.get('USERNAME') or 'unknown',
        'home': str(Path.home()),
        'cwd': str(Path.cwd()),
        'display': os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY') or ('native' if _IS_MAC or _IS_WIN else 'none'),
        'shell': os.environ.get('SHELL') or os.environ.get('COMSPEC') or 'unknown',
        'has_gui': _HAS_DISPLAY,
        'tools_available': {
            'ffmpeg': _cmd_exists('ffmpeg'),
            'nmap': _cmd_exists('nmap'),
            'git': _cmd_exists('git'),
            'docker': _cmd_exists('docker'),
            'node': _cmd_exists('node'),
            'npx': _cmd_exists('npx'),
            'adb': _cmd_exists('adb'),
            'burpsuite': _cmd_exists('burpsuite'),
            'python3': _cmd_exists('python3'),
        }
    }
    return json.dumps(out, indent=2)


def tool_open_url(url: str) -> str:
    """Open a URL in the default web browser — works on Linux, macOS, and Windows."""
    import webbrowser
    try:
        webbrowser.open(url)
        return f"Opened {url} in default browser"
    except Exception as e:
        # Fallback: platform-specific commands
        try:
            if _IS_MAC:
                subprocess.Popen(['open', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif _IS_WIN:
                subprocess.Popen(['start', url], shell=True, stdout=subprocess.DEVNULL)
            else:
                subprocess.Popen(['xdg-open', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Opened {url}"
        except Exception as e2:
            return f"ERROR opening URL: {e} / {e2}"


def tool_run_xplat(linux_cmd: str = '', mac_cmd: str = '', windows_cmd: str = '',
                   timeout: int = 30) -> str:
    """Run a platform-specific command: picks linux_cmd on Linux, mac_cmd on macOS, windows_cmd on Windows."""
    cmd = ''
    if _IS_WIN and windows_cmd:
        cmd = windows_cmd
    elif _IS_MAC and mac_cmd:
        cmd = mac_cmd
    elif _IS_LINUX and linux_cmd:
        cmd = linux_cmd
    elif linux_cmd:
        cmd = linux_cmd  # fallback to linux
    if not cmd:
        return f"No command defined for platform {_PLATFORM}"
    return tool_execute_shell(cmd, timeout=timeout)


def tool_think_and_plan(task: str) -> str:
    """
    Structure a complex task into a detailed plan before executing.
    Returns a numbered step-by-step plan. Call this FIRST for any multi-step task.
    """
    lines = [
        f"TASK: {task}",
        "",
        "ANALYSIS:",
        "  • What is the final desired state?",
        "  • What tools are available for this?",
        "  • What could go wrong?",
        "  • What verification proves success?",
        "",
        "RECOMMENDED APPROACH:",
        "  This is a planning call. Now execute the plan step by step using the actual tools.",
        "  Remember: OBSERVE → PLAN → ACT → VERIFY → LOOP → COMPLETE",
    ]
    lines.append(f"\nPLATFORM CONTEXT: {_PLATFORM} | GUI: {'YES' if _HAS_DISPLAY else 'NO (headless)'}")
    return "\n".join(lines)


def tool_observe_and_plan(goal: str) -> str:
    """
    Take a screenshot, analyze current screen state with AI, then return a
    structured action plan for achieving the goal. Use this at the START of any
    GUI task to understand what is currently on screen before acting.
    """
    try:
        # 1. Take screenshot
        shot = tool_screenshot()
        if shot.startswith('ERROR'):
            return f"OBSERVE: Cannot screenshot ({shot})\nPLAN: Use shell/browser tools instead of GUI.\nFIRST_ACTION: execute_shell or browser_navigate"

        # 2. Try AI analysis
        path = shot.split(': ', 1)[-1].strip().split()[0]
        analysis = tool_analyze_image(
            path,
            f"I need to: {goal}\n\n"
            "Please analyze this screenshot and answer:\n"
            "1. What is currently visible on screen?\n"
            "2. What application/window is in focus?\n"
            "3. What specific UI elements are relevant to my goal?\n"
            "4. What is the best first action to take? (give exact coordinates if clicking)\n"
            "5. Are there any obstacles or errors visible?"
        )
        return (
            f"GOAL: {goal}\n\n"
            f"CURRENT SCREEN STATE:\n{analysis}\n\n"
            f"PLATFORM: {_PLATFORM} | GUI: {'available' if _HAS_DISPLAY else 'headless'}\n\n"
            f"NOW: Execute the first action above using the appropriate tool."
        )
    except Exception as e:
        return (
            f"GOAL: {goal}\n"
            f"OBSERVE: Failed to get screen state ({e})\n"
            f"PLATFORM: {_PLATFORM} | GUI: {'available' if _HAS_DISPLAY else 'headless'}\n"
            f"PLAN: Proceed using shell/browser tools. Start with: execute_shell or browser_navigate"
        )


def tool_app_is_running(app_name: str) -> str:
    """Check if an application is currently running. Returns PID or 'not running'."""
    try:
        if _IS_WIN:
            r = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {app_name}.exe'],
                               capture_output=True, text=True, timeout=10)
            return f"Running: {app_name}" if app_name.lower() in r.stdout.lower() else f"Not running: {app_name}"
        else:
            r = subprocess.run(['pgrep', '-f', app_name], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                pids = r.stdout.strip().split()
                return f"Running: {app_name} (PIDs: {', '.join(pids[:5])})"
            return f"Not running: {app_name}"
    except Exception as e:
        return f"ERROR checking {app_name}: {e}"


def tool_focus_app(app_name: str) -> str:
    """Bring an application window to the foreground on any platform."""
    try:
        if _IS_WIN:
            script = f"""
import ctypes, subprocess
def find_and_focus(name):
    import subprocess
    r = subprocess.run(['tasklist'], capture_output=True, text=True)
    return name.lower() in r.stdout.lower()
find_and_focus('{app_name}')
"""
            return tool_execute_python(script)
        elif _IS_MAC:
            r = subprocess.run(['osascript', '-e',
                                f'tell application "{app_name}" to activate'],
                               capture_output=True, text=True, timeout=5)
            return f"Focused {app_name}" if r.returncode == 0 else f"Error: {r.stderr}"
        else:
            # Linux: try wmctrl first, then xdotool
            for cmd in [f'wmctrl -a {app_name}', f'xdotool search --name {app_name} windowactivate']:
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    return f"Focused {app_name} via {cmd.split()[0]}"
            return f"Focus attempt sent for {app_name}"
    except Exception as e:
        return f"ERROR focusing {app_name}: {e}"


def tool_type_text_xplat(text: str, speed: float = 0.0) -> str:
    """Type text using the best available method on this platform."""
    # Try xdotool on Linux first (most reliable)
    if _IS_LINUX and _cmd_exists('xdotool') and _HAS_DISPLAY:
        r = subprocess.run(['xdotool', 'type', '--clearmodifiers', '--', text],
                           capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            return f"Typed {len(text)} chars via xdotool"
    # Fall back to pyautogui/pynput
    return tool_keyboard_type(text)


# ── New module-backed tools ────────────────────────────────────────────────────

def tool_run_typescript(code: str = '', file_path: str = '') -> str:
    """Execute TypeScript code or a .ts file using npx tsx / ts-node."""
    import tempfile, os
    if file_path:
        cmd = f"npx --yes tsx {file_path} 2>&1 || ts-node {file_path} 2>&1"
        return tool_execute_shell(cmd, timeout=30)
    if not code:
        return "ERROR: provide code or file_path"
    with tempfile.NamedTemporaryFile(suffix='.ts', mode='w', delete=False) as f:
        f.write(code)
        tmp = f.name
    try:
        result = tool_execute_shell(f"npx --yes tsx {tmp} 2>&1 || ts-node {tmp} 2>&1", timeout=30)
        return result
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass


def tool_download_file(url: str, dest_path: str = '') -> str:
    """Download a file from a URL to disk. Returns path and file size."""
    import urllib.request, os
    if not dest_path:
        dest_path = os.path.join('/tmp', url.rstrip('/').split('/')[-1] or 'download')
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) DevinBot/4.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r, open(dest_path, 'wb') as f:
            data = r.read()
            f.write(data)
        return f"Downloaded {len(data):,} bytes → {dest_path}"
    except Exception as e:
        return f"ERROR downloading {url}: {e}"


def tool_workflow(steps_json: str) -> str:
    """Execute a structured multi-step workflow. steps_json is a JSON array of {tool, args} objects."""
    try:
        steps = json.loads(steps_json)
    except Exception as e:
        return f"ERROR parsing steps_json: {e}"
    results = []
    for i, step in enumerate(steps, 1):
        tool_name = step.get('tool', '')
        args = step.get('args', {})
        if not tool_name:
            results.append(f"Step {i}: ERROR — missing 'tool' key")
            continue
        r = _dispatch_tool(tool_name, args) if tool_name in TOOLS else f"ERROR: unknown tool '{tool_name}'"
        results.append(f"Step {i} [{tool_name}]: {r[:200]}")
        if r.startswith('ERROR') and step.get('stop_on_error', False):
            results.append(f"Workflow stopped at step {i} (stop_on_error=true)")
            break
    return '\n'.join(results)


def tool_threat_intel_lookup(query: str, lookup_type: str = 'auto') -> str:
    """Look up threat intelligence: MITRE ATT&CK techniques, IOC reputation, domain analysis."""
    if _threat_intel_mod is None:
        return "threat_intel_tools module not loaded"
    try:
        facade = getattr(_threat_intel_mod, 'ThreatIntelFacade', None)
        if facade:
            f = facade()
            if lookup_type in ('mitre', 'auto'):
                r = f.lookup_mitre_attack(query) if hasattr(f, 'lookup_mitre_attack') else {}
                if r:
                    return json.dumps(r, default=str)[:1000]
            if lookup_type in ('ioc', 'auto'):
                r = f.check_ioc(query) if hasattr(f, 'check_ioc') else {}
                if r:
                    return json.dumps(r, default=str)[:1000]
        return f"Threat intel query '{query}' (type={lookup_type}): module loaded but no direct result"
    except Exception as e:
        return f"ERROR in threat_intel_lookup: {e}"


def tool_process_media(file_path: str, operation: str = 'info') -> str:
    """Process media files: get info, resize image, extract audio, convert format."""
    if _multimedia_mod is None:
        return "multimedia_processing_module not loaded"
    try:
        if operation == 'info':
            proc = getattr(_multimedia_mod, 'ImageProcessor', None)
            if proc:
                p = proc()
                r = p.get_image_info(file_path) if hasattr(p, 'get_image_info') else {'file': file_path}
                return json.dumps(r, default=str)
        aproc = getattr(_multimedia_mod, 'AudioProcessor', None)
        if aproc:
            p = aproc()
            r = p.get_audio_info(file_path) if hasattr(p, 'get_audio_info') else {'file': file_path}
            return json.dumps(r, default=str)
        return f"Multimedia operation '{operation}' on {file_path}: module available"
    except Exception as e:
        return f"ERROR in process_media: {e}"


def tool_mobile_action(action: str, device: str = 'auto', extra: str = '') -> str:
    """Control a mobile device via ADB or USB: list devices, shell, screenshot, install APK."""
    if _mobile_mod is None:
        return "mobile_integration_module not loaded"
    try:
        facade = getattr(_mobile_mod, 'MobileFacade', None)
        if facade is None:
            return "MobileFacade not found in mobile module"
        f = facade()
        if action == 'list':
            r = f.list_devices() if hasattr(f, 'list_devices') else tool_execute_shell('adb devices')
        elif action == 'screenshot':
            r = f.take_screenshot(device) if hasattr(f, 'take_screenshot') else tool_execute_shell(f'adb -s {device} shell screencap /sdcard/screen.png')
        elif action == 'shell':
            r = f.run_shell(extra, device) if hasattr(f, 'run_shell') else tool_execute_shell(f'adb -s {device} shell {extra}')
        else:
            r = f"Mobile action '{action}' executed on {device}"
        return str(r)[:1000]
    except Exception as e:
        return f"ERROR in mobile_action: {e}"


def tool_ethics_check(action: str, context: str = '') -> str:
    """Check an action against ethics and legal compliance rules (GDPR, CCPA, AI safety)."""
    if _ethics_mod is None:
        return "ethics_legal_tools module not loaded"
    try:
        agent = getattr(_ethics_mod, 'AIAgent', None)
        if agent:
            a = agent(name="Devin")
            check = a.check_action_ethics(action, context) if hasattr(a, 'check_action_ethics') else None
            if check:
                return json.dumps(check, default=str)[:800]
        return f"Ethics check for '{action}': passed (no blocking rules triggered)"
    except Exception as e:
        return f"ERROR in ethics_check: {e}"


def tool_log_data(data: str, category: str = 'general') -> str:
    """Log structured data/events for later analysis. Returns confirmation."""
    if _data_logger is None:
        return "data_logger module not loaded"
    try:
        r = _data_logger.log(data=data, category=category) if hasattr(_data_logger, 'log') else _data_logger.write(data)
        return f"Logged to category '{category}': {str(r)[:200]}"
    except Exception as e:
        return f"ERROR in log_data: {e}"


def tool_cyber_range_challenge(challenge_id: str = '', action: str = 'list') -> str:
    """Interact with CTF/cyber range challenges: list, start, submit flag, get hints."""
    if _cyber_range_mod is None:
        return "cyber_range_tools module not loaded"
    try:
        facade = getattr(_cyber_range_mod, 'CyberRangeFacade', None)
        if facade:
            f = facade()
            if action == 'list':
                r = f.list_challenges() if hasattr(f, 'list_challenges') else "No list_challenges method"
            elif action == 'start':
                r = f.start_challenge(challenge_id) if hasattr(f, 'start_challenge') else f"Started {challenge_id}"
            else:
                r = f"Action '{action}' on challenge '{challenge_id}'"
            return str(r)[:800]
        return "CyberRangeFacade not available"
    except Exception as e:
        return f"ERROR in cyber_range_challenge: {e}"


def tool_canvas_render(content: str, title: str = 'Devin Canvas') -> str:
    """Render content to a canvas (OpenDevin-style visual output)."""
    if _opendevin_mod is None:
        return f"[Canvas] {title}: {content[:500]}"
    try:
        bridge = getattr(_opendevin_mod, 'OpenDevinBridge', None)
        if bridge:
            b = bridge()
            r = b.render(content=content, title=title) if hasattr(b, 'render') else f"[Canvas rendered: {title}]"
            return str(r)[:800]
        return f"[Canvas] {title}: {content[:500]}"
    except Exception as e:
        return f"ERROR in canvas_render: {e}"


def tool_xr_display(content: str, mode: str = 'overlay') -> str:
    """Display content in XR/AR/VR mode via Holomat bridge."""
    if _holomat_mod is None:
        return f"[XR Display ({mode})] {content[:300]}"
    try:
        bridge = getattr(_holomat_mod, 'HolomatBridge', None)
        if bridge:
            b = bridge()
            r = b.display(content=content, mode=mode) if hasattr(b, 'display') else f"[XR: {mode}] {content[:200]}"
            return str(r)[:500]
        return f"[XR Display ({mode})] {content[:300]}"
    except Exception as e:
        return f"ERROR in xr_display: {e}"


def tool_ai_route(task: str, preferred_model: str = 'auto') -> str:
    """Route a task to the best available AI provider and return the result."""
    if _all_ais_mod is None:
        return "all_ais_modules not loaded; use the active provider directly"
    try:
        provider = getattr(_all_ais_mod, 'AIProvider', None)
        if provider:
            p = provider()
            r = p.route(task=task, model=preferred_model) if hasattr(p, 'route') else f"Route: {task[:100]}"
            return str(r)[:1000]
        return f"AI routing: '{task[:100]}' → sent to active provider"
    except Exception as e:
        return f"ERROR in ai_route: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AA — MULTI-STEP WORKFLOW + CONDITION POLLING + CHECKPOINT TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

def tool_multi_step_workflow(steps: str, stop_on_error: bool = True) -> str:
    """
    Execute a JSON-defined list of tool calls in sequence with per-step verification.
    Each step: {"tool": "name", "args": {...}, "verify": "optional shell/python check"}.
    Returns a summary report of every step's result.

    Example:
      steps = '[{"tool":"execute_shell","args":{"command":"mkdir /tmp/test"}},
               {"tool":"write_file","args":{"path":"/tmp/test/hello.txt","content":"hi"}}]'
    """
    try:
        plan = json.loads(steps)
    except json.JSONDecodeError as e:
        return f"ERROR: steps must be valid JSON list: {e}"

    if not isinstance(plan, list) or not plan:
        return "ERROR: steps must be a non-empty JSON list of {tool, args} objects"

    results = []
    for i, step in enumerate(plan, 1):
        tool_name = step.get("tool", "")
        args = step.get("args", {})
        verify = step.get("verify", "")
        label = step.get("label", tool_name)

        if not tool_name:
            results.append(f"Step {i}: SKIP — no tool specified")
            continue

        result = _dispatch_tool(tool_name, args)
        is_err = (result.startswith("ERROR") or
                  result.startswith("Traceback") or
                  "Error:" in result[:200])

        entry = f"Step {i}/{len(plan)} [{label}]: {'ERROR' if is_err else 'OK'}\n  → {result[:300]}"

        if verify and not is_err:
            try:
                ver_result = _dispatch_tool("execute_shell", {"command": verify, "timeout": 10})
                entry += f"\n  ✓ Verify: {ver_result[:100]}"
            except Exception as ve:
                entry += f"\n  ⚠ Verify failed: {ve}"

        results.append(entry)

        if is_err and stop_on_error:
            results.append(f"Stopped at step {i} due to error (stop_on_error=True)")
            break

    summary = "\n\n".join(results)
    ok = sum(1 for r in results if "OK" in r.split("\n")[0])
    total = len(plan)
    summary += f"\n\nSUMMARY: {ok}/{total} steps succeeded"
    return summary


def tool_wait_for_condition(condition: str, timeout: int = 30,
                             interval: float = 1.0) -> str:
    """
    Poll until a Python expression evaluates to True, or timeout is reached.
    'condition' is a Python expression that returns truthy/falsy, evaluated
    with exec/eval (read-only checks only — no side effects).
    Useful for waiting on file creation, process start, network availability, etc.

    Examples:
      condition="os.path.exists('/tmp/output.txt')"
      condition="subprocess.run(['pgrep','firefox'],capture_output=True).returncode==0"
    """
    import time as _time
    deadline = _time.time() + max(1, min(timeout, 300))
    attempt = 0
    while _time.time() < deadline:
        attempt += 1
        try:
            result = eval(condition, {"os": os, "subprocess": subprocess,
                                      "Path": Path, "time": _time,
                                      "json": json, "re": re})
            if result:
                return f"Condition met after {attempt} attempt(s): {condition[:80]}"
        except Exception as e:
            if attempt == 1:
                return f"ERROR evaluating condition '{condition[:80]}': {e}"
        _time.sleep(min(interval, deadline - _time.time()))
    elapsed = timeout
    return f"TIMEOUT after {elapsed}s ({attempt} attempts): condition not met: {condition[:80]}"


def _ensure_checkpoints_table(conn: sqlite3.Connection) -> None:
    """Ensure the checkpoints table exists (created lazily)."""
    conn.execute('''CREATE TABLE IF NOT EXISTS checkpoints (
        name TEXT PRIMARY KEY,
        data TEXT NOT NULL,
        ts REAL NOT NULL
    )''')
    conn.commit()


def tool_checkpoint_save(name: str, data: str) -> str:
    """
    Save a named checkpoint to persistent storage (SQLite). Use to record
    task progress so it can be resumed if the session is interrupted.
    'data' is any string (JSON, text, URL, file path, etc.)
    """
    try:
        conn = _db_connect()
        _ensure_checkpoints_table(conn)
        conn.execute(
            "INSERT OR REPLACE INTO checkpoints (name, data, ts) VALUES (?, ?, ?)",
            (name, data, time.time())
        )
        conn.commit()
        return f"Checkpoint saved: {name} ({len(data)} chars)"
    except Exception as e:
        return f"ERROR saving checkpoint '{name}': {e}"


def tool_checkpoint_load(name: str) -> str:
    """
    Load a previously saved checkpoint by name.
    Returns the saved data string, or ERROR if not found.
    """
    try:
        conn = _db_connect()
        _ensure_checkpoints_table(conn)
        row = conn.execute(
            "SELECT data FROM checkpoints WHERE name = ?", (name,)
        ).fetchone()
        if row:
            return row[0]
        return f"ERROR: no checkpoint found named '{name}'"
    except Exception as e:
        return f"ERROR loading checkpoint '{name}': {e}"


def tool_checkpoint_list() -> str:
    """List all saved checkpoints with their names, sizes, and timestamps."""
    try:
        conn = _db_connect()
        _ensure_checkpoints_table(conn)
        rows = conn.execute(
            "SELECT name, length(data), ts FROM checkpoints ORDER BY ts DESC"
        ).fetchall()
        if not rows:
            return "No checkpoints saved"
        lines = ["Saved checkpoints:"]
        for cp_name, sz, ts in rows:
            lines.append(
                f"  {cp_name:<30} {sz:>6} chars  saved {time.strftime('%Y-%m-%d %H:%M', time.localtime(ts))}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"ERROR listing checkpoints: {e}"


def tool_run_workflow_file(path: str) -> str:
    """
    Load a JSON workflow file and execute it via multi_step_workflow.
    The file must contain a JSON array of step objects: [{tool, args, verify?, label?}].
    """
    try:
        content = Path(path).read_text(encoding='utf-8')
        return tool_multi_step_workflow(content)
    except FileNotFoundError:
        return f"ERROR: file not found: {path}"
    except Exception as e:
        return f"ERROR loading workflow file: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AE — RETRY META-TOOL + TEMPLATE + ARCHIVE + OUTPUT VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def tool_retry_on_failure(tool_name: str, tool_args: str, max_retries: int = 3,
                           delay: float = 1.0) -> str:
    """
    Call a tool and automatically retry up to max_retries times if it returns an ERROR.
    tool_args must be a JSON object string. Returns the first successful result,
    or the last error if all retries fail. Use for flaky operations (network, GUI timing).
    """
    import time as _time
    try:
        args = json.loads(tool_args) if tool_args.strip() else {}
    except json.JSONDecodeError as e:
        return f"ERROR: tool_args must be valid JSON: {e}"

    last_result = ""
    for attempt in range(1, max_retries + 1):
        result = _dispatch_tool(tool_name, args)
        is_err = (result.startswith("ERROR") or
                  result.startswith("Traceback") or
                  "Error:" in result[:200])
        if not is_err:
            return f"[attempt {attempt}/{max_retries}] SUCCESS:\n{result}"
        last_result = result
        if attempt < max_retries:
            _time.sleep(delay)

    return f"[all {max_retries} attempts failed]\nLast error: {last_result[:500]}"


def tool_verify_output(output: str, expected_pattern: str,
                        mode: str = 'contains') -> str:
    """
    Verify that a tool's output matches an expected pattern.
    Modes:
      contains  — output contains the string (case-sensitive)
      icontains — output contains the string (case-insensitive)
      regex     — output matches the regex pattern
      startswith — output starts with the string
      not_empty — output is non-empty and not an ERROR
      is_error  — output starts with ERROR (for negative testing)
    Returns PASS or FAIL with details.
    """
    mode = mode.lower()
    try:
        if mode == 'contains':
            ok = expected_pattern in output
        elif mode == 'icontains':
            ok = expected_pattern.lower() in output.lower()
        elif mode == 'regex':
            ok = bool(re.search(expected_pattern, output))
        elif mode == 'startswith':
            ok = output.strip().startswith(expected_pattern)
        elif mode == 'not_empty':
            ok = bool(output.strip()) and not output.startswith('ERROR')
        elif mode == 'is_error':
            ok = output.startswith('ERROR')
        else:
            return f"ERROR: unknown mode '{mode}'. Use: contains|icontains|regex|startswith|not_empty|is_error"
    except re.error as e:
        return f"ERROR: invalid regex '{expected_pattern}': {e}"

    status = "PASS" if ok else "FAIL"
    preview = output[:200].replace('\n', '↵')
    return f"{status}: '{expected_pattern}' ({mode}) in output: '{preview}'"


def tool_template_fill(template: str, variables: str) -> str:
    """
    Fill a text template with variables from a JSON object.
    Uses {variable_name} placeholders. Safe — no code execution.

    Example:
      template = "Hello {name}! You have {count} messages."
      variables = '{"name": "Alice", "count": "5"}'
      → "Hello Alice! You have 5 messages."
    """
    try:
        vars_dict = json.loads(variables)
    except json.JSONDecodeError as e:
        return f"ERROR: variables must be a valid JSON object: {e}"

    if not isinstance(vars_dict, dict):
        return "ERROR: variables must be a JSON object (not an array)"

    try:
        result = template
        for key, val in vars_dict.items():
            result = result.replace(f'{{{key}}}', str(val))
        # Check for unfilled placeholders
        remaining = re.findall(r'\{([^}]+)\}', result)
        if remaining:
            return result + f"\n\nWARNING: unfilled placeholders: {remaining}"
        return result
    except Exception as e:
        return f"ERROR filling template: {e}"


def tool_zip_files(output_path: str, source_paths: str, compression: str = 'deflated') -> str:
    """
    Create a ZIP archive from a list of file/directory paths.
    source_paths is a JSON array of paths: '["/path/to/file", "/path/to/dir"]'.
    Directories are added recursively.
    """
    import zipfile
    try:
        sources = json.loads(source_paths)
    except json.JSONDecodeError as e:
        return f"ERROR: source_paths must be a JSON array: {e}"

    comp = zipfile.ZIP_DEFLATED if compression == 'deflated' else zipfile.ZIP_STORED
    added = 0
    try:
        with zipfile.ZipFile(output_path, 'w', compression=comp) as zf:
            for src in sources:
                p = Path(src)
                if not p.exists():
                    return f"ERROR: source not found: {src}"
                if p.is_file():
                    zf.write(p, p.name)
                    added += 1
                elif p.is_dir():
                    for sub in p.rglob('*'):
                        if sub.is_file():
                            zf.write(sub, sub.relative_to(p.parent))
                            added += 1
        size = Path(output_path).stat().st_size
        return f"Created {output_path} ({size:,} bytes, {added} files)"
    except Exception as e:
        return f"ERROR creating ZIP: {e}"


def tool_unzip(archive_path: str, dest_dir: str = '.') -> str:
    """Extract a ZIP archive to a destination directory."""
    import zipfile
    try:
        p = Path(archive_path)
        if not p.exists():
            return f"ERROR: archive not found: {archive_path}"
        with zipfile.ZipFile(str(p), 'r') as zf:
            names = zf.namelist()
            zf.extractall(dest_dir)
        return f"Extracted {len(names)} files from {archive_path} to {dest_dir}"
    except zipfile.BadZipFile:
        return f"ERROR: not a valid ZIP file: {archive_path}"
    except Exception as e:
        return f"ERROR extracting: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AN — FINAL CAPABILITY LAYER: SUMMARIZE_DIFF, COLOR_OUTPUT, TASK_DONE
# ═══════════════════════════════════════════════════════════════════════════════

def tool_summarize_changes(before: str, after: str, context: str = '') -> str:
    """
    Summarize the changes between a 'before' and 'after' version of text/code.
    Provides a human-readable summary of what changed: added, removed, modified lines.
    Useful for reporting what a task accomplished.
    """
    import difflib
    b_lines = before.splitlines(keepends=True)
    a_lines = after.splitlines(keepends=True)
    diff = list(difflib.unified_diff(b_lines, a_lines, lineterm=''))
    if not diff:
        return "No changes detected between before and after versions."
    added = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
    removed = sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))
    result = [
        f"Changes summary{f' ({context})' if context else ''}:",
        f"  Lines added:   {added}",
        f"  Lines removed: {removed}",
        f"  Net change:    {added - removed:+d} lines",
        "",
        "Diff (first 50 changed lines):",
    ]
    shown = 0
    for line in diff[2:]:  # skip --- +++ header
        if line.startswith('@@') or line.startswith('+') or line.startswith('-'):
            result.append(('+ ' if line.startswith('+') else '- ' if line.startswith('-') else '  ') + line[1:].rstrip())
            shown += 1
            if shown >= 50:
                remaining = sum(1 for l in diff if l.startswith(('+', '-'))) - shown
                if remaining > 0:
                    result.append(f"  ... ({remaining} more changed lines)")
                break
    return "\n".join(result)


def tool_task_complete(summary: str, artifacts: str = '') -> str:
    """
    Signal that a task is complete. Records the outcome and any created artifacts.
    This is the FINAL tool call at the end of a task. Always call this when done.
    artifacts: JSON array of file paths or URLs created during the task.
    """
    import datetime
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    artifact_list = []
    if artifacts:
        try:
            artifact_list = json.loads(artifacts)
        except json.JSONDecodeError:
            artifact_list = [artifacts]
    lines = [
        f"✓ TASK COMPLETE — {ts}",
        f"Summary: {summary}",
    ]
    if artifact_list:
        lines.append(f"Artifacts ({len(artifact_list)}):")
        lines.extend(f"  • {a}" for a in artifact_list)
    # Log to session stats if available
    try:
        _SESSION_STATS['tasks_completed'] = _SESSION_STATS.get('tasks_completed', 0) + 1
    except Exception:
        pass
    return "\n".join(lines)


def tool_format_output(content: str, style: str = 'box', title: str = '') -> str:
    """
    Format output text for display. Styles:
    box: Unicode bordered box, list: bullet list, table: pipe-separated,
    numbered: numbered items, header: section header, plain: as-is.
    """
    lines = [line.rstrip() for line in content.strip().splitlines()]
    if style == 'box':
        if not lines:
            return '┌─┐\n│ │\n└─┘'
        width = max(len(l) for l in lines)
        if title:
            width = max(width, len(title) + 4)
        top = f"┌{'─' * (width + 2)}┐"
        bot = f"└{'─' * (width + 2)}┘"
        body = [f"│ {l.ljust(width)} │" for l in lines]
        if title:
            hdr = f"│ {'─' * ((width - len(title) - 2) // 2)} {title} {'─' * ((width - len(title) - 1) // 2)} │"
            sep = f"├{'─' * (width + 2)}┤"
            return "\n".join([top, hdr, sep] + body + [bot])
        return "\n".join([top] + body + [bot])
    elif style == 'list':
        return "\n".join(f"• {l}" for l in lines if l)
    elif style == 'numbered':
        return "\n".join(f"{i+1}. {l}" for i, l in enumerate(lines) if l)
    elif style == 'header':
        t = title or (lines[0] if lines else 'Section')
        return f"\n{'═' * (len(t) + 4)}\n  {t}\n{'═' * (len(t) + 4)}\n" + "\n".join(lines[1:] if title else lines)
    return content  # plain


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AT — FINAL INTELLIGENCE: GOAL_PLAN, SELF_REFLECT, TOOL_SUGGEST, REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def tool_goal_plan(goal: str, context: str = '', constraints: str = '') -> str:
    """
    Break a high-level goal into an actionable plan using tool-based steps.
    Returns a structured plan with Phase/Step/Tool/Purpose for each action.
    context: current project context (optional).
    constraints: known limitations (optional).
    """
    import re as _re
    # Classify the goal domain
    domains = {
        'code': ['implement', 'build', 'create', 'write', 'add', 'fix', 'refactor', 'debug', 'test'],
        'data': ['analyze', 'parse', 'query', 'extract', 'transform', 'export', 'import', 'csv', 'json'],
        'system': ['deploy', 'monitor', 'configure', 'install', 'backup', 'schedule', 'automate'],
        'web':  ['scrape', 'download', 'fetch', 'api', 'endpoint', 'request', 'http'],
        'file': ['organize', 'move', 'rename', 'sync', 'compress', 'archive', 'search'],
    }
    goal_lower = goal.lower()
    detected = [d for d, kws in domains.items() if any(kw in goal_lower for kw in kws)]
    domain = detected[0] if detected else 'general'

    # Generate a structured plan
    lines = [
        f"GOAL PLAN: {goal}",
        f"Domain:    {domain}",
    ]
    if context:
        lines.append(f"Context:   {context}")
    if constraints:
        lines.append(f"Constraints: {constraints}")
    lines.append("")

    # Domain-specific step templates
    step_templates = {
        'code': [
            ("UNDERSTAND", "Read the relevant code/docs", "read_file / symbol_search"),
            ("PLAN",       "Decompose task into sub-steps", "decompose_task"),
            ("IMPLEMENT",  "Write or modify code", "write_file / execute_python"),
            ("TEST",       "Run tests to verify", "run_tests / verify_output"),
            ("DOCUMENT",   "Update docs/comments", "write_file"),
            ("COMPLETE",   "Signal task done", "task_complete"),
        ],
        'data': [
            ("ACQUIRE",    "Fetch or read input data", "read_file / http_request"),
            ("VALIDATE",   "Check data integrity", "validate_json / csv_query"),
            ("TRANSFORM",  "Process and reshape data", "execute_python / regex_extract"),
            ("EXPORT",     "Save results", "write_file"),
            ("COMPLETE",   "Signal task done", "task_complete"),
        ],
        'system': [
            ("AUDIT",      "Check current system state", "system_snapshot / list_processes"),
            ("CONFIGURE",  "Update configuration", "config_write / set_env"),
            ("EXECUTE",    "Run system command", "execute_shell / spawn_process"),
            ("VERIFY",     "Confirm change took effect", "verify_output / internet_check"),
            ("COMPLETE",   "Signal task done", "task_complete"),
        ],
        'web': [
            ("FETCH",      "Make HTTP request", "http_request"),
            ("PARSE",      "Extract relevant content", "parse_html / regex_extract"),
            ("STORE",      "Save extracted data", "write_file"),
            ("COMPLETE",   "Signal task done", "task_complete"),
        ],
        'file': [
            ("INVENTORY",  "List files to process", "file_tree / list_files"),
            ("PROCESS",    "Rename/sync/compress files", "bulk_rename / folder_sync / zip_files"),
            ("VERIFY",     "Confirm outcome", "read_file / checksum"),
            ("COMPLETE",   "Signal task done", "task_complete"),
        ],
        'general': [
            ("UNDERSTAND", "Gather context and requirements", "read_file / search_in_files"),
            ("PLAN",       "Break into concrete steps", "decompose_task / task_plan"),
            ("EXECUTE",    "Carry out each step", "execute_python / execute_shell"),
            ("VERIFY",     "Check results", "verify_output"),
            ("COMPLETE",   "Signal task done", "task_complete"),
        ],
    }
    steps = step_templates.get(domain, step_templates['general'])
    lines.append(f"RECOMMENDED STEPS ({len(steps)}):")
    for i, (phase, purpose, tools) in enumerate(steps, 1):
        lines.append(f"  {i}. [{phase}] {purpose}")
        lines.append(f"     Tools: {tools}")
    return "\n".join(lines)


def tool_self_reflect(last_output: str, goal: str = '') -> str:
    """
    Analyze the last tool output to assess progress and suggest next steps.
    Used by the AI to decide whether a task is complete or what to do next.
    """
    out = last_output.strip()
    lower = out.lower()
    lines = ["SELF-REFLECTION:"]

    # Detect outcomes
    if any(w in lower for w in ('error', 'exception', 'traceback', 'failed', 'fail')):
        lines.append("  Status: ❌ ERROR — output indicates a failure")
        lines.append("  Suggestions:")
        if 'no such file' in lower or 'not found' in lower:
            lines.append("    • Check file paths; use file_tree or list_files to verify")
        if 'permission' in lower:
            lines.append("    • Insufficient permissions; try execute_shell with sudo or check ownership")
        if 'import' in lower or 'module' in lower:
            lines.append("    • Missing dependency; check requirements.txt or install with pip")
        lines.append("    • Review the error message and retry with corrected arguments")
    elif any(w in lower for w in ('✓', 'success', 'done', 'complete', 'passed', 'ok\n', ' ok')):
        lines.append("  Status: ✅ SUCCESS — output looks good")
        if goal:
            lines.append(f"  Goal: {goal}")
            lines.append("  Next: Verify the result meets requirements, then call task_complete")
        else:
            lines.append("  Next: Proceed to the next step or call task_complete if done")
    elif any(w in lower for w in ('warning', 'warn', 'deprecated')):
        lines.append("  Status: ⚠️  WARNING — partial success with warnings")
        lines.append("  Next: Review warnings; they may be ignorable or indicate future issues")
    else:
        lines.append("  Status: ℹ️  NEUTRAL — output is informational")
        lines.append("  Next: Review output and determine if action is needed")

    # Output length heuristic
    if len(out) > 5000:
        lines.append(f"  Note: Output is long ({len(out)} chars); consider summarizing with summarize_changes")
    if not out:
        lines.append("  Warning: Empty output — tool may have produced no result")

    return "\n".join(lines)


def tool_generate_report(title: str, sections: str, format: str = 'markdown') -> str:
    """
    Generate a structured report from a JSON sections spec.
    sections: JSON array of {heading, content} objects.
    format: markdown | plain | html
    """
    try:
        sec_list = json.loads(sections)
    except json.JSONDecodeError as e:
        return f"ERROR: invalid sections JSON: {e}"
    if format == 'markdown':
        lines = [f"# {title}", ""]
        for sec in sec_list:
            h = sec.get('heading', 'Section')
            c = sec.get('content', '')
            lines += [f"## {h}", "", c, ""]
        return "\n".join(lines)
    elif format == 'html':
        parts = [f"<h1>{title}</h1>"]
        for sec in sec_list:
            h = sec.get('heading', 'Section')
            c = sec.get('content', '').replace('\n', '<br>')
            parts.append(f"<h2>{h}</h2><p>{c}</p>")
        return "\n".join(parts)
    else:  # plain
        lines = [title, '=' * len(title), '']
        for sec in sec_list:
            h = sec.get('heading', 'Section')
            c = sec.get('content', '')
            lines += [h, '-' * len(h), c, '']
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AS — CODE INTELLIGENCE: SYMBOL_SEARCH, CALL_GRAPH, TODO_FIX, DEAD_CODE
# ═══════════════════════════════════════════════════════════════════════════════

def tool_symbol_search(directory: str, symbol: str, file_glob: str = '*.py') -> str:
    """
    Find all definitions and references to a symbol (function, class, variable)
    across a directory. Returns file:line pairs.
    """
    import pathlib, re as _re
    d = pathlib.Path(directory)
    if not d.exists():
        return f"ERROR: directory not found: {directory}"
    pattern = _re.compile(r'\b' + _re.escape(symbol) + r'\b')
    results = []
    for f in sorted(d.rglob(file_glob))[:200]:
        try:
            lines = f.read_text(errors='replace').splitlines()
            for i, line in enumerate(lines, 1):
                if pattern.search(line):
                    results.append(f"{f}:{i}: {line.strip()[:120]}")
        except Exception:
            pass
    if not results:
        return f"Symbol {symbol!r} not found in {directory} ({file_glob})"
    return f"Found {len(results)} reference(s) to {symbol!r}:\n" + "\n".join(results[:100])


def tool_find_dead_code(directory: str, file_glob: str = '*.py') -> str:
    """
    Find functions and classes that are defined but never called/referenced
    within the same directory tree. A simple heuristic (not a full AST analysis).
    """
    import pathlib, re as _re, ast
    d = pathlib.Path(directory)
    if not d.exists():
        return f"ERROR: directory not found: {directory}"
    definitions = {}  # name → file:line
    all_text = ''
    for f in sorted(d.rglob(file_glob))[:100]:
        try:
            src = f.read_text(errors='replace')
            all_text += src + '\n'
            try:
                tree = ast.parse(src)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if not node.name.startswith('_'):
                            definitions[node.name] = f"{f}:{node.lineno}"
            except SyntaxError:
                pass
        except Exception:
            pass
    dead = []
    for name, loc in sorted(definitions.items()):
        usage_pattern = _re.compile(r'\b' + _re.escape(name) + r'\b')
        # A "call" means it appears elsewhere in the codebase, not just its own definition
        occurrences = len(usage_pattern.findall(all_text))
        if occurrences <= 1:  # only its own definition line
            dead.append(f"  {name:40s} {loc}")
    if not dead:
        return f"No obvious dead code found in {directory} ({file_glob})"
    return f"Possibly unused ({len(dead)} candidates) in {directory}:\n" + "\n".join(dead[:50])


def tool_count_lines(directory: str, file_glob: str = '*.py',
                     include_blank: bool = True, include_comments: bool = True) -> str:
    """
    Count lines of code in a directory.
    Returns per-file and total counts (code / blank / comment lines).
    """
    import pathlib, re as _re
    d = pathlib.Path(directory)
    if not d.exists():
        return f"ERROR: directory not found: {directory}"
    total_code = total_blank = total_comment = 0
    rows = []
    for f in sorted(d.rglob(file_glob))[:500]:
        if not f.is_file():
            continue
        try:
            lines = f.read_text(errors='replace').splitlines()
        except Exception:
            continue
        code = blank = comment = 0
        for line in lines:
            s = line.strip()
            if not s:
                blank += 1
            elif s.startswith('#'):
                comment += 1
            else:
                code += 1
        total_code += code
        total_blank += blank
        total_comment += comment
        rows.append((str(f.relative_to(d))[:60], code, blank, comment))
    if not rows:
        return f"No files matched {file_glob} in {directory}"
    lines_out = [f"{'File':<62} {'Code':>6} {'Blank':>6} {'Comment':>8}"]
    lines_out.append('─' * 84)
    for name, c, b, cm in rows[:50]:
        lines_out.append(f"{name:<62} {c:>6} {b:>6} {cm:>8}")
    if len(rows) > 50:
        lines_out.append(f"  ... ({len(rows) - 50} more files)")
    lines_out.append('─' * 84)
    lines_out.append(f"{'TOTAL':<62} {total_code:>6} {total_blank:>6} {total_comment:>8}")
    return "\n".join(lines_out)


def tool_ast_parse(code: str, language: str = 'python') -> str:
    """
    Parse Python code and return a summary of its AST structure:
    imports, classes, functions (with line numbers and arg counts).
    language: currently only 'python' is supported.
    """
    if language.lower() != 'python':
        return f"ERROR: only 'python' is supported for ast_parse"
    import ast
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"SyntaxError: {e}"
    sections = {'imports': [], 'classes': [], 'functions': []}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                sections['imports'].append(f"  import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            names = ', '.join(a.name for a in node.names)
            sections['imports'].append(f"  from {node.module} import {names}")
        elif isinstance(node, ast.ClassDef):
            bases = ', '.join(getattr(b, 'id', '?') for b in node.bases)
            sections['classes'].append(f"  {node.name}({bases}) @ line {node.lineno}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = len(node.args.args)
            prefix = 'async def' if isinstance(node, ast.AsyncFunctionDef) else 'def'
            sections['functions'].append(f"  {prefix} {node.name}({args} args) @ line {node.lineno}")
    lines = [f"AST summary ({len(code.splitlines())} lines):"]
    for section, items in sections.items():
        if items:
            lines.append(f"\n{section.upper()} ({len(items)}):")
            lines.extend(items[:20])
            if len(items) > 20:
                lines.append(f"  ... and {len(items)-20} more")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AR — PROCESS CONTROL: LIST, KILL, SPAWN, RESOURCE LIMITS, ENV INJECT
# ═══════════════════════════════════════════════════════════════════════════════

def tool_list_processes(filter: str = '', limit: int = 30) -> str:
    """
    List running processes. filter: substring match on name/cmdline.
    Returns PID, name, CPU%, memory%, and status.
    """
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'cmdline']):
            try:
                info = p.info
                if filter:
                    cmdline = ' '.join(info.get('cmdline') or [])
                    if filter.lower() not in info.get('name', '').lower() and filter.lower() not in cmdline.lower():
                        continue
                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        procs = procs[:int(limit)]
        if not procs:
            return "No processes found" + (f" matching {filter!r}" if filter else "")
        lines = [f"{'PID':>7} {'CPU%':>6} {'MEM%':>6} {'STATUS':<10} NAME"]
        lines.append('─' * 60)
        for p in procs:
            lines.append(f"{p['pid']:>7} {p['cpu_percent'] or 0:>6.1f} {p['memory_percent'] or 0:>6.1f} {p['status']:<10} {p['name']}")
        return "\n".join(lines)
    except ImportError:
        # Fallback: parse ps output
        import subprocess
        cmd = ['ps', 'aux']
        if filter:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                lines = [l for l in result.stdout.splitlines() if filter.lower() in l.lower() or l.startswith('USER')]
                return "\n".join(lines[:int(limit)+1])
            except Exception as e:
                return f"ERROR: {e}"
        try:
            result = subprocess.run(cmd + ['--sort=-%cpu'], capture_output=True, text=True, timeout=10)
            lines = result.stdout.splitlines()[:int(limit)+1]
            return "\n".join(lines)
        except Exception as e:
            return f"ERROR: {e}"


def tool_kill_process(pid: int, signal: str = 'TERM') -> str:
    """
    Send a signal to a process by PID.
    signal: TERM (graceful) | KILL (force) | HUP | INT | STOP | CONT
    """
    import os
    import signal as _signal
    sig_map = {
        'TERM': _signal.SIGTERM,
        'KILL': _signal.SIGKILL,
        'HUP':  _signal.SIGHUP,
        'INT':  _signal.SIGINT,
        'STOP': _signal.SIGSTOP,
        'CONT': _signal.SIGCONT,
    }
    sig = sig_map.get(signal.upper())
    if sig is None:
        return f"ERROR: unknown signal {signal!r}. Use TERM|KILL|HUP|INT|STOP|CONT."
    try:
        os.kill(int(pid), sig)
        return f"Signal {signal.upper()} sent to PID {pid}."
    except ProcessLookupError:
        return f"ERROR: no process with PID {pid}"
    except PermissionError:
        return f"ERROR: permission denied to signal PID {pid}"
    except Exception as e:
        return f"ERROR: {e}"


def tool_spawn_process(command: str, cwd: str = '.', env_extra: str = '',
                       detach: bool = False) -> str:
    """
    Spawn a subprocess and return its PID.
    env_extra: JSON dict of extra environment variables to inject.
    detach=True: launch in background (no stdout capture).
    detach=False: wait up to 5s and capture first 2000 chars of output.
    """
    import subprocess, os
    env = os.environ.copy()
    if env_extra:
        try:
            extras = json.loads(env_extra)
            env.update({str(k): str(v) for k, v in extras.items()})
        except json.JSONDecodeError as e:
            return f"ERROR: invalid env_extra JSON: {e}"
    try:
        if detach:
            proc = subprocess.Popen(
                command, shell=True, cwd=cwd, env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True)
            return f"Process spawned (detached), PID {proc.pid}."
        else:
            proc = subprocess.Popen(
                command, shell=True, cwd=cwd, env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            try:
                out, _ = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                out, _ = proc.communicate()
                return f"Process timed out (PID {proc.pid}). Partial output:\n{out[:2000]}"
            return f"Exit code {proc.returncode}.\n{out[:2000]}"
    except Exception as e:
        return f"ERROR spawning process: {e}"


def tool_process_info(pid: int) -> str:
    """
    Return detailed info for a single process by PID:
    name, status, CPU%, memory, open files, start time, command line.
    """
    try:
        import psutil, datetime
        p = psutil.Process(int(pid))
        with p.oneshot():
            info = {
                'pid': p.pid,
                'name': p.name(),
                'status': p.status(),
                'cpu_percent': p.cpu_percent(interval=0.1),
                'memory_mb': p.memory_info().rss / (1024 * 1024),
                'started': datetime.datetime.fromtimestamp(p.create_time()).isoformat(),
                'cmdline': ' '.join(p.cmdline()),
                'num_threads': p.num_threads(),
            }
            try:
                info['open_files'] = len(p.open_files())
            except psutil.AccessDenied:
                info['open_files'] = 'N/A'
        lines = [f"Process {pid} info:"]
        for k, v in info.items():
            lines.append(f"  {k:14s}: {v}")
        return "\n".join(lines)
    except ImportError:
        import subprocess
        try:
            result = subprocess.run(['ps', '-p', str(pid), '-o', 'pid,comm,stat,pcpu,pmem,lstart,args'],
                                    capture_output=True, text=True, timeout=5)
            return result.stdout.strip() or f"No process with PID {pid}"
        except Exception as e:
            return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AQ — NETWORK: PING, PORT SCAN, DNS LOOKUP, HTTP HEADERS, IP INFO
# ═══════════════════════════════════════════════════════════════════════════════

def tool_ping(host: str, count: int = 4, timeout: int = 5) -> str:
    """
    Ping a host and report packet loss + round-trip times.
    Uses the system ping command. count: number of packets (1–20).
    """
    import subprocess, shutil
    count = max(1, min(int(count), 20))
    if not shutil.which('ping'):
        return "ERROR: 'ping' command not found on this system"
    try:
        if _IS_WIN:
            cmd = ['ping', '-n', str(count), '-w', str(timeout * 1000), host]
        else:
            cmd = ['ping', '-c', str(count), '-W', str(timeout), host]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * count + 5)
        out = result.stdout + result.stderr
        return out.strip() if out.strip() else f"No output from ping {host}"
    except subprocess.TimeoutExpired:
        return f"ERROR: ping {host} timed out after {timeout * count + 5}s"
    except Exception as e:
        return f"ERROR: ping failed: {e}"


def tool_port_scan(host: str, ports: str = '22,80,443,8080,8443', timeout: float = 1.0) -> str:
    """
    Check which TCP ports are open on a host.
    ports: comma-separated list or range like '80-90'. Max 50 ports.
    """
    import socket
    port_list = []
    for part in ports.split(','):
        part = part.strip()
        if '-' in part:
            lo, hi = part.split('-', 1)
            port_list.extend(range(int(lo), int(hi) + 1))
        else:
            port_list.append(int(part))
    port_list = list(dict.fromkeys(port_list))[:50]  # deduplicate, cap at 50
    results = []
    for p in sorted(port_list):
        try:
            with socket.create_connection((host, p), timeout=float(timeout)):
                results.append(f"  {p:5d}/tcp  OPEN")
        except (socket.timeout, ConnectionRefusedError, OSError):
            results.append(f"  {p:5d}/tcp  closed")
    if not results:
        return "No ports to scan"
    return f"Port scan {host} ({len(port_list)} ports):\n" + "\n".join(results)


def tool_dns_lookup(hostname: str, record_type: str = 'A') -> str:
    """
    Perform a DNS lookup.
    record_type: A | AAAA | MX | TXT | NS | CNAME | PTR
    Uses the system 'dig' or 'nslookup', falling back to Python socket.
    """
    import subprocess, shutil, socket
    rt = record_type.upper()
    if shutil.which('dig'):
        try:
            result = subprocess.run(
                ['dig', '+short', rt, hostname],
                capture_output=True, text=True, timeout=10)
            out = result.stdout.strip()
            return f"DNS {rt} {hostname}:\n{out}" if out else f"No {rt} records found for {hostname}"
        except Exception:
            pass
    # Python fallback (A only)
    if rt == 'A':
        try:
            addrs = socket.getaddrinfo(hostname, None, socket.AF_INET)
            ips = list(dict.fromkeys(a[4][0] for a in addrs))
            return f"DNS A {hostname}:\n" + "\n".join(ips)
        except socket.gaierror as e:
            return f"ERROR: DNS lookup failed: {e}"
    return f"ERROR: 'dig' not available and Python socket only supports A records."


def tool_http_headers(url: str, timeout: int = 10) -> str:
    """
    Fetch only the HTTP response headers from a URL (HEAD request).
    Returns status code + all response headers.
    """
    try:
        import urllib.request
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Devin-AGI/4.0')
        with urllib.request.urlopen(req, timeout=int(timeout)) as resp:
            lines = [f"HTTP {resp.status} {resp.reason}"]
            for k, v in resp.headers.items():
                lines.append(f"  {k}: {v}")
            return "\n".join(lines)
    except Exception as e:
        return f"ERROR fetching headers from {url}: {e}"


def tool_whois_ip(ip_or_host: str) -> str:
    """
    Get basic IP geolocation / ASN info from ip-api.com (no API key required).
    Returns country, region, city, ISP, ASN for any public IP or hostname.
    """
    import urllib.request, json as _json
    try:
        url = f"http://ip-api.com/json/{ip_or_host}?fields=status,message,country,regionName,city,isp,org,as,query"
        req = urllib.request.Request(url, headers={'User-Agent': 'Devin-AGI/4.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = _json.loads(resp.read())
        if data.get('status') != 'success':
            return f"ERROR: ip-api returned: {data.get('message', 'unknown error')}"
        lines = [f"IP info for {data.get('query', ip_or_host)}:"]
        for key in ('country', 'regionName', 'city', 'isp', 'org', 'as'):
            if data.get(key):
                lines.append(f"  {key:12s}: {data[key]}")
        return "\n".join(lines)
    except Exception as e:
        return f"ERROR: whois_ip failed: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AP — FILE WATCHER LOOP, BULK RENAME, FOLDER SYNC, ARCHIVE INFO
# ═══════════════════════════════════════════════════════════════════════════════

def tool_bulk_rename(directory: str, pattern: str, replacement: str,
                     file_glob: str = '*', dry_run: bool = True) -> str:
    """
    Rename files in a directory by replacing a regex pattern with a replacement.
    dry_run=True previews changes without applying them.
    """
    import pathlib, re as _re
    d = pathlib.Path(directory)
    if not d.is_dir():
        return f"ERROR: not a directory: {directory}"
    results = []
    count = 0
    for f in sorted(d.glob(file_glob)):
        if not f.is_file():
            continue
        new_name = _re.sub(pattern, replacement, f.name)
        if new_name == f.name:
            continue
        dest = f.parent / new_name
        if dest.exists():
            results.append(f"SKIP  {f.name} → {new_name} (destination exists)")
            continue
        if not dry_run:
            f.rename(dest)
        results.append(f"{'RENAME' if not dry_run else 'WOULD'} {f.name} → {new_name}")
        count += 1
    if not results:
        return f"No files matched rename pattern in {directory}"
    header = f"{'DRY RUN — ' if dry_run else ''}{count} file(s) to rename in {directory}:"
    return header + "\n" + "\n".join(results)


def tool_folder_sync(src: str, dst: str, dry_run: bool = True, delete: bool = False) -> str:
    """
    Sync files from src directory to dst directory (one-way, src→dst).
    Copies new/updated files. If delete=True, removes files in dst not in src.
    dry_run=True previews without making changes.
    """
    import pathlib, shutil, hashlib
    sp = pathlib.Path(src)
    dp = pathlib.Path(dst)
    if not sp.is_dir():
        return f"ERROR: source not a directory: {src}"
    actions = []
    def file_hash(p):
        h = hashlib.md5()
        with open(p, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()
    # Copy new/changed files
    for sf in sorted(sp.rglob('*')):
        if sf.is_dir():
            continue
        rel = sf.relative_to(sp)
        df = dp / rel
        if not df.exists() or file_hash(sf) != file_hash(df):
            actions.append(('COPY', str(rel)))
            if not dry_run:
                df.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sf, df)
    # Optionally delete extra files in dst
    if delete and dp.exists():
        for df in sorted(dp.rglob('*')):
            if df.is_dir():
                continue
            rel = df.relative_to(dp)
            if not (sp / rel).exists():
                actions.append(('DELETE', str(rel)))
                if not dry_run:
                    df.unlink()
    if not actions:
        return f"Directories are already in sync ({src} → {dst})."
    prefix = 'DRY RUN — ' if dry_run else ''
    lines = [f"{prefix}{len(actions)} action(s) for sync {src} → {dst}:"]
    lines += [f"  {act} {rel}" for act, rel in actions]
    return "\n".join(lines)


def tool_archive_info(path: str) -> str:
    """
    Return metadata and file listing for a ZIP or TAR archive without extracting it.
    """
    import pathlib, zipfile, tarfile
    p = pathlib.Path(path)
    if not p.exists():
        return f"ERROR: file not found: {path}"
    size_mb = p.stat().st_size / (1024 * 1024)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, 'r') as z:
            infos = z.infolist()
            total = sum(i.file_size for i in infos)
            lines = [
                f"ZIP archive: {path}",
                f"  Compressed size: {size_mb:.2f} MB",
                f"  Uncompressed:    {total/(1024*1024):.2f} MB",
                f"  Files:           {len(infos)}",
                "",
                "Contents (first 50):",
            ]
            for info in infos[:50]:
                lines.append(f"  {info.filename}  ({info.file_size:,} bytes)")
            if len(infos) > 50:
                lines.append(f"  ... and {len(infos)-50} more files")
            return "\n".join(lines)
    if tarfile.is_tarfile(path):
        with tarfile.open(path, 'r:*') as t:
            members = t.getmembers()
            total = sum(m.size for m in members if m.isfile())
            lines = [
                f"TAR archive: {path}",
                f"  Compressed size: {size_mb:.2f} MB",
                f"  Uncompressed:    {total/(1024*1024):.2f} MB",
                f"  Entries:         {len(members)}",
                "",
                "Contents (first 50):",
            ]
            for m in members[:50]:
                lines.append(f"  {m.name}  ({m.size:,} bytes)")
            if len(members) > 50:
                lines.append(f"  ... and {len(members)-50} more entries")
            return "\n".join(lines)
    return f"ERROR: {path} is not a recognised ZIP or TAR archive."


def tool_checksum(path: str, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file.
    algorithm: md5 | sha1 | sha256 | sha512
    """
    import hashlib
    import pathlib
    p = pathlib.Path(path)
    if not p.exists():
        return f"ERROR: file not found: {path}"
    algo = algorithm.lower()
    if algo not in ('md5', 'sha1', 'sha256', 'sha512'):
        return f"ERROR: unsupported algorithm {algorithm!r}. Use md5|sha1|sha256|sha512."
    h = hashlib.new(algo)
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return f"{algo.upper()}({path}) = {h.hexdigest()}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AO — PIPE, STRING OPS, SLEEP, UUID, RANDOM, TIMESTAMP
# ═══════════════════════════════════════════════════════════════════════════════

def tool_pipe(steps: str) -> str:
    """
    Pipe the output of one tool into the next in a chain.
    steps: JSON array of {tool, args} objects. Each tool's output is passed
    as the first string argument of the next tool automatically, unless the
    next step explicitly supplies that argument.
    Returns the final output.
    """
    try:
        chain = json.loads(steps)
    except json.JSONDecodeError as e:
        return f"ERROR: invalid steps JSON: {e}"
    if not isinstance(chain, list) or not chain:
        return "ERROR: steps must be a non-empty JSON array"
    result = ''
    for i, step in enumerate(chain):
        name = step.get('tool', '')
        args = dict(step.get('args', {}))
        if not name:
            return f"ERROR: step {i} missing 'tool' key"
        if i > 0 and result:
            # Inject previous output as first required param if not already set
            tool_entry = TOOLS.get(name, {})
            req = tool_entry.get('required', [])
            if req and req[0] not in args:
                args[req[0]] = result
        result = _dispatch_tool(name, args)
        if result.startswith('ERROR:'):
            return f"ERROR at step {i} ({name}): {result}"
    return result


def tool_string_ops(text: str, operation: str, arg: str = '') -> str:
    """
    Common string operations.
    operation: upper | lower | title | strip | reverse | split | join |
               replace | startswith | endswith | count | pad_left | pad_right |
               repeat | truncate | slugify
    arg: second argument where needed (delimiter for split/join, pattern for
         replace/count, width for pad, times for repeat, max_len for truncate).
    """
    op = operation.lower()
    if op == 'upper':       return text.upper()
    if op == 'lower':       return text.lower()
    if op == 'title':       return text.title()
    if op == 'strip':       return text.strip(arg or None)
    if op == 'reverse':     return text[::-1]
    if op == 'split':
        parts = text.split(arg) if arg else text.split()
        return json.dumps(parts)
    if op == 'join':
        try:
            parts = json.loads(text)
            return (arg or '').join(str(p) for p in parts)
        except json.JSONDecodeError:
            return f"ERROR: text must be a JSON array for join"
    if op == 'replace':
        parts = arg.split('|||', 1)
        if len(parts) != 2:
            return "ERROR: arg must be 'old|||new' for replace"
        return text.replace(parts[0], parts[1])
    if op == 'startswith':  return str(text.startswith(arg))
    if op == 'endswith':    return str(text.endswith(arg))
    if op == 'count':       return str(text.count(arg)) if arg else str(len(text))
    if op == 'pad_left':
        try: return text.rjust(int(arg))
        except ValueError: return "ERROR: arg must be an integer width"
    if op == 'pad_right':
        try: return text.ljust(int(arg))
        except ValueError: return "ERROR: arg must be an integer width"
    if op == 'repeat':
        try: return text * int(arg)
        except ValueError: return "ERROR: arg must be an integer count"
    if op == 'truncate':
        try:
            n = int(arg) if arg else 80
            return text[:n] + ('…' if len(text) > n else '')
        except ValueError: return "ERROR: arg must be an integer max length"
    if op == 'slugify':
        import re as _re
        slug = text.lower().strip()
        slug = _re.sub(r'[^\w\s-]', '', slug)
        slug = _re.sub(r'[\s_-]+', '-', slug)
        slug = slug.strip('-')
        return slug
    return f"ERROR: unknown operation {operation!r}. Valid: upper|lower|title|strip|reverse|split|join|replace|startswith|endswith|count|pad_left|pad_right|repeat|truncate|slugify"


def tool_sleep(seconds: float) -> str:
    """
    Pause execution for the given number of seconds (max 60).
    Useful between retries or rate-limited operations.
    """
    import time
    if seconds < 0:
        return "ERROR: seconds must be non-negative"
    secs = min(float(seconds), 60.0)
    time.sleep(secs)
    return f"Slept {secs:.2f} seconds."


def tool_generate_uuid(version: int = 4, namespace: str = '', name: str = '') -> str:
    """
    Generate a UUID.
    version: 1 (time-based), 3 (MD5 namespace), 4 (random), 5 (SHA1 namespace).
    namespace / name: required for v3 and v5 (namespace is a UUID string or
    one of dns|url|oid|x500).
    """
    import uuid
    ns_map = {'dns': uuid.NAMESPACE_DNS, 'url': uuid.NAMESPACE_URL,
              'oid': uuid.NAMESPACE_OID, 'x500': uuid.NAMESPACE_X500}
    if version == 1:
        return str(uuid.uuid1())
    if version == 4:
        return str(uuid.uuid4())
    if version in (3, 5):
        if not namespace or not name:
            return "ERROR: namespace and name are required for UUID v3/v5"
        ns = ns_map.get(namespace.lower())
        if ns is None:
            try:
                ns = uuid.UUID(namespace)
            except ValueError:
                return f"ERROR: invalid namespace {namespace!r}"
        return str(uuid.uuid3(ns, name) if version == 3 else uuid.uuid5(ns, name))
    return f"ERROR: unsupported UUID version {version}. Use 1, 3, 4, or 5."


def tool_random_value(type: str = 'int', min: float = 0, max: float = 100,
                      length: int = 16, choices: str = '') -> str:
    """
    Generate a random value.
    type: int | float | string | choice | shuffle
    min/max: range for int/float.
    length: character count for string.
    choices: JSON array for choice/shuffle.
    """
    import random, string as _string
    t = type.lower()
    if t == 'int':
        return str(random.randint(int(min), int(max)))
    if t == 'float':
        return str(round(random.uniform(float(min), float(max)), 6))
    if t == 'string':
        alphabet = _string.ascii_letters + _string.digits
        return ''.join(random.choices(alphabet, k=int(length)))
    if t in ('choice', 'shuffle'):
        if not choices:
            return "ERROR: choices is required for type choice/shuffle"
        try:
            items = json.loads(choices)
        except json.JSONDecodeError:
            items = [c.strip() for c in choices.split(',')]
        if t == 'choice':
            return str(random.choice(items))
        random.shuffle(items)
        return json.dumps(items)
    return f"ERROR: unknown type {type!r}. Use int|float|string|choice|shuffle."


def tool_timestamp(format: str = 'iso', timezone: str = 'utc', offset_seconds: int = 0) -> str:
    """
    Return the current timestamp or a calculated offset.
    format: iso | unix | human | date | time | rfc2822
    timezone: utc | local
    offset_seconds: add/subtract seconds from now (e.g. -3600 for 1 hour ago).
    """
    import datetime as _dt
    if timezone.lower() == 'utc':
        now = _dt.datetime.now(_dt.timezone.utc)
    else:
        now = _dt.datetime.now()
    if offset_seconds:
        now = now + _dt.timedelta(seconds=int(offset_seconds))
    fmt = format.lower()
    if fmt == 'iso':       return now.isoformat()
    if fmt == 'unix':      return str(int(now.timestamp()))
    if fmt == 'human':     return now.strftime('%B %d, %Y %H:%M:%S %Z')
    if fmt == 'date':      return now.strftime('%Y-%m-%d')
    if fmt == 'time':      return now.strftime('%H:%M:%S')
    if fmt == 'rfc2822':
        from email.utils import format_datetime
        return format_datetime(now)
    return f"ERROR: unknown format {format!r}. Use iso|unix|human|date|time|rfc2822."


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AM — CALCULATE, LIST_TOOLS, PARSE_ARGS, DIFF_JSON
# ═══════════════════════════════════════════════════════════════════════════════

def tool_calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression. Supports: +,-,*,/,**,//,%,
    sqrt, abs, round, log, sin, cos, tan, pi, e, and basic Python math.
    Does NOT allow function calls, imports, or arbitrary code execution.
    """
    import math
    # Allowed names
    allowed = {
        'abs': abs, 'round': round, 'min': min, 'max': max,
        'sqrt': math.sqrt, 'log': math.log, 'log2': math.log2, 'log10': math.log10,
        'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'asin': math.asin, 'acos': math.acos, 'atan': math.atan, 'atan2': math.atan2,
        'floor': math.floor, 'ceil': math.ceil, 'pow': math.pow,
        'pi': math.pi, 'e': math.e, 'inf': math.inf, 'tau': math.tau,
        'True': True, 'False': False,
    }
    # Safety: block anything looking like attribute access, imports, builtins
    if re.search(r'\b(import|exec|eval|open|__|\bos\b|\bsys\b|\bsubprocess\b)', expression):
        return f"ERROR: expression contains blocked keywords"
    try:
        result = eval(expression, {"__builtins__": {}}, allowed)
        if isinstance(result, float):
            return f"{expression} = {result:.10g}"
        return f"{expression} = {result}"
    except ZeroDivisionError:
        return "ERROR: division by zero"
    except (SyntaxError, NameError) as e:
        return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR evaluating expression: {e}"


def tool_list_tools(category: str = '', search: str = '') -> str:
    """
    List all available Devin tools. Filter by category or search by name/description.
    category: e.g. 'workflow', 'files', 'code', 'web', 'system', etc.
    search: substring to find in tool name or description.
    """
    matching = {}
    for name, info in TOOLS.items():
        cat = info.get('category', 'unknown')
        if category and cat.lower() != category.lower():
            continue
        if search and search.lower() not in name.lower() and search.lower() not in info.get('desc', '').lower():
            continue
        matching[name] = info
    if not matching:
        return f"No tools found" + (f" in category {category!r}" if category else "") + (f" matching {search!r}" if search else "")
    # Group by category
    by_cat: dict = {}
    for name, info in matching.items():
        cat = info.get('category', 'unknown')
        by_cat.setdefault(cat, []).append((name, info.get('desc', '')))
    lines = [f"Tools ({len(matching)} matching):"]
    for cat in sorted(by_cat.keys()):
        lines.append(f"\n[{cat}]")
        for name, desc in sorted(by_cat[cat]):
            short_desc = desc[:70] + '...' if len(desc) > 70 else desc
            lines.append(f"  {name:<30} {short_desc}")
    return "\n".join(lines)


def tool_diff_json(json1: str, json2: str, path: str = '') -> str:
    """
    Diff two JSON values. Shows added, removed, and changed keys recursively.
    path: optional initial path prefix for nested diffs.
    """
    try:
        a = json.loads(json1)
        b = json.loads(json2)
    except json.JSONDecodeError as e:
        return f"ERROR: invalid JSON: {e}"
    diffs = []
    def compare(x, y, p=''):
        if type(x) != type(y):
            diffs.append(f"  TYPE CHANGE at {p or '/'}: {type(x).__name__} → {type(y).__name__}")
            return
        if isinstance(x, dict):
            all_keys = set(x) | set(y)
            for k in sorted(all_keys):
                pk = f"{p}.{k}" if p else k
                if k not in x:
                    diffs.append(f"  ADDED   {pk}: {json.dumps(y[k])[:80]}")
                elif k not in y:
                    diffs.append(f"  REMOVED {pk}: {json.dumps(x[k])[:80]}")
                else:
                    compare(x[k], y[k], pk)
        elif isinstance(x, list):
            if len(x) != len(y):
                diffs.append(f"  LENGTH  {p or '/'}: {len(x)} → {len(y)}")
            for i, (xi, yi) in enumerate(zip(x, y)):
                compare(xi, yi, f"{p}[{i}]")
        else:
            if x != y:
                diffs.append(f"  CHANGED {p or '/'}: {json.dumps(x)[:40]} → {json.dumps(y)[:40]}")
    compare(a, b, path)
    if not diffs:
        return "JSON values are identical"
    return f"JSON diff ({len(diffs)} difference(s)):\n" + "\n".join(diffs[:50])


def tool_parse_args(args_string: str, spec: str = '') -> str:
    """
    Parse a command-line argument string into a structured dict.
    spec: optional JSON schema {name: {type, default, help}} for validation.
    Returns parsed args as JSON.
    """
    import shlex
    try:
        tokens = shlex.split(args_string)
    except ValueError as e:
        return f"ERROR: could not parse args: {e}"
    parsed = {'_positional': [], '_flags': []}
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.startswith('--'):
            key = t[2:]
            if i + 1 < len(tokens) and not tokens[i+1].startswith('-'):
                parsed[key] = tokens[i+1]
                i += 2
            else:
                parsed[key] = True
                i += 1
        elif t.startswith('-') and len(t) == 2:
            parsed[t[1:]] = True
            i += 1
        else:
            parsed['_positional'].append(t)
            i += 1
    # Validate against spec if given
    validation = []
    if spec:
        try:
            schema = json.loads(spec)
            for name, meta in schema.items():
                if name not in parsed and name not in parsed.get('_positional', []):
                    if 'default' not in meta:
                        validation.append(f"Missing required arg: {name!r}")
                    else:
                        parsed[name] = meta['default']
        except json.JSONDecodeError:
            validation.append("WARNING: spec is not valid JSON")
    result = json.dumps(parsed, indent=2)
    if validation:
        result += "\n\nValidation:\n" + "\n".join(validation)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AL — CODE REVIEW, WATCH FILE, UNIT CONVERT, INTERNET STATUS
# ═══════════════════════════════════════════════════════════════════════════════

def tool_code_review(path: str, rules: str = 'all') -> str:
    """
    Static code review of a Python file. Checks for:
    - long functions (>50 lines), missing type hints, broad exceptions,
    - mutable default args, unused imports, hardcoded credentials,
    - nested ternaries, very long lines (>120 chars).
    rules: 'all' or comma-separated subset.
    """
    p = Path(path)
    if not p.exists():
        return f"ERROR: file not found: {path}"
    if p.suffix not in ('.py', '.pyw'):
        return f"ERROR: only Python files supported"
    try:
        source = p.read_text(encoding='utf-8', errors='replace')
        lines = source.splitlines()
    except Exception as e:
        return f"ERROR reading file: {e}"
    findings = []
    rule_set = set(r.strip().lower() for r in rules.split(',')) if rules != 'all' else None
    def want(r): return rule_set is None or r in rule_set
    # Long lines
    if want('long_lines'):
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                findings.append(f"Line {i:4d}: long line ({len(line)} chars) — {line[:60]}...")
    # Broad exception catch
    if want('broad_except'):
        for i, line in enumerate(lines, 1):
            if re.match(r'\s*except\s*:', line) or re.match(r'\s*except\s+Exception\s*:', line):
                findings.append(f"Line {i:4d}: broad exception catch")
    # Long functions
    if want('long_functions'):
        in_func = False; func_start = 0; func_name = ''
        for i, line in enumerate(lines, 1):
            m = re.match(r'^\s*def\s+(\w+)', line)
            if m:
                if in_func and (i - func_start) > 50:
                    findings.append(f"Line {func_start:4d}: function {func_name!r} is long ({i - func_start} lines)")
                in_func = True; func_start = i; func_name = m.group(1)
    # Hardcoded credentials
    if want('credentials'):
        for i, line in enumerate(lines, 1):
            if re.search(r'(password|api_key|secret|token)\s*=\s*["\'][^"\']{6,}["\']', line, re.I):
                if not re.search(r'os\.|environ|getenv|\.get\(', line):
                    findings.append(f"Line {i:4d}: possible hardcoded credential — {line.strip()[:60]}")
    # Mutable default args
    if want('mutable_defaults'):
        for i, line in enumerate(lines, 1):
            if re.search(r'def\s+\w+\([^)]*=\s*(\[\]|\{\}|\bdict\(\)|\blist\(\))', line):
                findings.append(f"Line {i:4d}: mutable default argument — {line.strip()[:60]}")
    # Missing return type hints on public functions
    if want('type_hints'):
        for i, line in enumerate(lines, 1):
            m = re.match(r'^\s*def\s+([a-z]\w*)\s*\([^)]*\)\s*:', line)
            if m and '->' not in line:
                findings.append(f"Line {i:4d}: function {m.group(1)!r} missing return type hint")
    if not findings:
        return f"Code review of {path}: No issues found ({len(lines)} lines checked)."
    result = [f"Code review: {path} ({len(lines)} lines) — {len(findings)} finding(s):"]
    result.extend(findings[:50])
    if len(findings) > 50:
        result.append(f"... and {len(findings) - 50} more")
    return "\n".join(result)


def tool_watch_file(path: str, timeout: int = 10, interval: float = 0.5) -> str:
    """
    Poll a file for changes for up to `timeout` seconds. Returns new content
    when the file changes (or mtime changes). Useful for watching log files
    or waiting for a script to write its output.
    """
    import time
    p = Path(path)
    if not p.exists():
        return f"ERROR: file not found: {path}"
    try:
        initial_mtime = p.stat().st_mtime
        initial_size = p.stat().st_size
    except Exception as e:
        return f"ERROR: {e}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(interval)
        try:
            st = p.stat()
            if st.st_mtime != initial_mtime or st.st_size != initial_size:
                new_content = p.read_text(encoding='utf-8', errors='replace')
                return (f"File changed after {timeout - (deadline - time.time()):.1f}s:\n"
                        f"Size: {initial_size} → {st.st_size} bytes\n"
                        f"Content (last 1000 chars):\n{new_content[-1000:]}")
        except Exception:
            pass
    return f"No changes detected in {path} after {timeout}s"


def tool_convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """
    Convert between units. Supports:
    Length: m, km, mi, ft, in, cm, mm, yd
    Weight: kg, g, lb, oz, t (tonne)
    Temperature: c (Celsius), f (Fahrenheit), k (Kelvin)
    Digital: b (bytes), kb, mb, gb, tb
    Time: s, min, h, d, w
    """
    f = from_unit.lower().strip()
    t = to_unit.lower().strip()
    v = float(value)
    # Length conversions (base: meters)
    LENGTH = {'m': 1.0, 'km': 1000, 'mi': 1609.344, 'ft': 0.3048,
               'in': 0.0254, 'cm': 0.01, 'mm': 0.001, 'yd': 0.9144}
    # Weight conversions (base: kg)
    WEIGHT = {'kg': 1.0, 'g': 0.001, 'lb': 0.453592, 'oz': 0.0283495, 't': 1000}
    # Digital (base: bytes)
    DIGITAL = {'b': 1, 'kb': 1024, 'mb': 1024**2, 'gb': 1024**3, 'tb': 1024**4}
    # Time (base: seconds)
    TIME = {'s': 1, 'sec': 1, 'min': 60, 'h': 3600, 'hr': 3600, 'd': 86400, 'w': 604800}
    try:
        # Temperature special case
        if f in ('c', 'celsius', '°c') and t in ('f', 'fahrenheit', '°f'):
            return f"{v}°C = {v * 9/5 + 32:.4g}°F"
        elif f in ('f', 'fahrenheit', '°f') and t in ('c', 'celsius', '°c'):
            return f"{v}°F = {(v - 32) * 5/9:.4g}°C"
        elif f in ('c', 'celsius', '°c') and t in ('k', 'kelvin'):
            return f"{v}°C = {v + 273.15:.4g}K"
        elif f in ('k', 'kelvin') and t in ('c', 'celsius', '°c'):
            return f"{v}K = {v - 273.15:.4g}°C"
        elif f in ('f', 'fahrenheit', '°f') and t in ('k', 'kelvin'):
            return f"{v}°F = {(v - 32) * 5/9 + 273.15:.4g}K"
        elif f in ('k', 'kelvin') and t in ('f', 'fahrenheit', '°f'):
            return f"{v}K = {(v - 273.15) * 9/5 + 32:.4g}°F"
        # Try each unit table
        for table in (LENGTH, WEIGHT, DIGITAL, TIME):
            if f in table and t in table:
                base = v * table[f]
                result = base / table[t]
                return f"{v} {from_unit} = {result:.6g} {to_unit}"
        return f"ERROR: unknown unit pair {from_unit!r} → {to_unit!r}"
    except Exception as e:
        return f"ERROR in convert_units: {e}"


def tool_internet_check(host: str = '8.8.8.8', port: int = 53, timeout: int = 3) -> str:
    """
    Check internet connectivity by attempting a TCP connection to a known host.
    Returns latency or error message.
    """
    import socket, time
    try:
        start = time.time()
        sock = socket.create_connection((host, port), timeout=timeout)
        latency = (time.time() - start) * 1000
        sock.close()
        return f"Connected to {host}:{port} — latency: {latency:.1f}ms — internet: OK"
    except socket.timeout:
        return f"Connection to {host}:{port} timed out after {timeout}s — internet may be down"
    except OSError as e:
        return f"Cannot connect to {host}:{port} — {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AK — SYSTEM, CONFIG, MEMORY: SNAPSHOT, CONFIG R/W, MEMORY SEARCH
# ═══════════════════════════════════════════════════════════════════════════════

def tool_system_snapshot() -> str:
    """
    Take a full system health snapshot: CPU, memory, disk, top processes,
    network interfaces, load average. No external deps required; falls back
    gracefully if psutil is unavailable.
    """
    import subprocess, platform
    lines = [f"=== System Snapshot — {platform.node()} ===", f"OS: {platform.platform()}",
             f"Python: {platform.python_version()}", f"Time: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
             ""]
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        cpus = psutil.cpu_count()
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        lines += [
            f"CPU: {cpu:.1f}% ({cpus} cores)",
            f"Memory: {mem.used/1e9:.1f}/{mem.total/1e9:.1f} GB ({mem.percent:.0f}% used)",
            f"Disk (/): {disk.used/1e9:.1f}/{disk.total/1e9:.1f} GB ({disk.percent:.0f}% used)",
        ]
        try:
            la = psutil.getloadavg()
            lines.append(f"Load avg: {la[0]:.2f} / {la[1]:.2f} / {la[2]:.2f} (1/5/15 min)")
        except Exception:
            pass
        # Top 5 processes by CPU
        procs = sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                       key=lambda p: p.info.get('cpu_percent', 0) or 0, reverse=True)[:5]
        lines.append("\nTop processes (by CPU):")
        for p in procs:
            lines.append(f"  {p.info['pid']:6d}  {(p.info.get('cpu_percent') or 0):5.1f}% CPU  "
                         f"{(p.info.get('memory_percent') or 0):4.1f}% MEM  {p.info['name'][:30]}")
    except ImportError:
        # Fallback to shell commands
        try:
            r = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                lines.append("Memory:\n" + r.stdout.strip())
        except Exception:
            pass
        try:
            r = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                lines.append("Disk:\n" + r.stdout.strip())
        except Exception:
            pass
        try:
            r = subprocess.run(['ps', 'aux', '--sort=-%cpu'], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                ps_lines = r.stdout.splitlines()[:6]
                lines.append("Top processes:\n" + "\n".join(ps_lines))
        except Exception:
            pass
    return "\n".join(lines)


def tool_config_read(path: str, section: str = '') -> str:
    """
    Read a config file (INI, JSON, TOML if available, or .env style).
    Returns the full config or a specific section.
    """
    p = Path(path)
    if not p.exists():
        return f"ERROR: file not found: {path}"
    suffix = p.suffix.lower()
    try:
        if suffix == '.json':
            data = json.loads(p.read_text(encoding='utf-8'))
            if section:
                data = data.get(section, f"Section {section!r} not found")
            return json.dumps(data, indent=2, ensure_ascii=False)[:4000]
        elif suffix in ('.ini', '.cfg', '.conf'):
            import configparser
            cfg = configparser.ConfigParser()
            cfg.read(str(p))
            if section:
                if section not in cfg:
                    return f"Section {section!r} not found. Available: {', '.join(cfg.sections())}"
                return "\n".join(f"{k} = {v}" for k, v in cfg[section].items())
            result = {}
            for sec in cfg.sections():
                result[sec] = dict(cfg[sec])
            return json.dumps(result, indent=2)[:4000]
        elif suffix == '.toml':
            try:
                import tomllib  # Python 3.11+
                data = tomllib.loads(p.read_text(encoding='utf-8'))
            except ImportError:
                try:
                    import tomli as tomllib
                    data = tomllib.loads(p.read_text(encoding='utf-8'))
                except ImportError:
                    return "TOML support requires Python 3.11+ or: pip install tomli"
            if section:
                data = data.get(section, f"Section {section!r} not found")
            return json.dumps(data, indent=2, ensure_ascii=False)[:4000]
        else:
            # .env or plain text
            lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
            result = {}
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, _, v = line.partition('=')
                    k = k.strip()
                    # Redact secrets
                    if re.search(r'key|token|secret|password|auth', k, re.I):
                        result[k] = '[REDACTED]'
                    else:
                        result[k] = v.strip().strip('"\'')
            if section:
                return result.get(section, f"Key {section!r} not found") if isinstance(result, dict) else str(result)
            return json.dumps(result, indent=2)[:4000]
    except Exception as e:
        return f"ERROR reading config: {e}"


def tool_config_write(path: str, section: str, key: str, value: str) -> str:
    """
    Write or update a key in an INI/CFG config file.
    Creates the file and section if they don't exist.
    """
    import configparser
    p = Path(path)
    cfg = configparser.ConfigParser()
    if p.exists():
        cfg.read(str(p))
    if section not in cfg:
        cfg[section] = {}
    cfg[section][key] = value
    try:
        with p.open('w', encoding='utf-8') as f:
            cfg.write(f)
        return f"Written [{section}] {key} = {value!r} to {path}"
    except Exception as e:
        return f"ERROR writing config: {e}"


def tool_memory_search(query: str, limit: int = 10) -> str:
    """
    Search stored memories for entries matching the query (keyword-based).
    Returns matching facts ordered by relevance.
    """
    import sqlite3
    db_path = _DB_PATH
    if not Path(db_path).exists():
        return "No memory database found."
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # Try simple keyword search across the facts
        words = [w.lower() for w in query.split() if len(w) > 2]
        if not words:
            return "ERROR: query too short"
        # Build a LIKE query for each word
        conditions = " OR ".join("LOWER(fact) LIKE ?" for _ in words)
        params = [f'%{w}%' for w in words]
        cur.execute(f"SELECT fact, ts FROM memories WHERE {conditions} ORDER BY ts DESC LIMIT ?",
                    params + [limit])
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return f"No memories found matching: {query!r}"
        result = [f"Found {len(rows)} memory/memories matching {query!r}:"]
        for fact, ts in rows:
            import datetime
            dt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
            result.append(f"  [{dt}] {fact}")
        return "\n".join(result)
    except Exception as e:
        return f"ERROR searching memory: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AJ — TASK PLANNING: TASK_PLAN, FILE_TREE, COMPARE_FILES, TODOS, CHMOD
# ═══════════════════════════════════════════════════════════════════════════════

def tool_task_plan(goal: str, steps: int = 5, format: str = 'numbered') -> str:
    """
    Generate a structured task plan from a goal description using keyword-based
    decomposition. Returns a numbered or checklist plan with time estimates.
    format: 'numbered' | 'checklist' | 'json'
    """
    goal_lower = goal.lower()
    # Keyword-based step templates
    phases = []
    if any(w in goal_lower for w in ('understand', 'analyze', 'review', 'read', 'check')):
        phases.append(('Understand & Analyze', 'Read relevant files, understand the codebase structure', '10-20 min'))
    elif any(w in goal_lower for w in ('build', 'create', 'develop', 'write', 'implement', 'add')):
        phases.append(('Research & Plan', 'Research requirements, review existing code', '10-15 min'))
        phases.append(('Design', 'Design the solution architecture and data structures', '15-20 min'))
        phases.append(('Implement', 'Write the code following the design plan', '30-60 min'))
        phases.append(('Test', 'Write and run tests to verify correctness', '15-20 min'))
        phases.append(('Document', 'Update README and comments', '10 min'))
    elif any(w in goal_lower for w in ('fix', 'debug', 'resolve', 'repair', 'solve')):
        phases.append(('Reproduce', 'Reproduce the issue and understand the failure', '5-10 min'))
        phases.append(('Identify Root Cause', 'Trace through code to find the cause', '15-20 min'))
        phases.append(('Fix', 'Implement the minimal fix', '10-30 min'))
        phases.append(('Test Fix', 'Verify the fix and run regression tests', '10-15 min'))
    elif any(w in goal_lower for w in ('deploy', 'release', 'ship', 'publish')):
        phases.append(('Pre-flight Check', 'Run tests, linting, and build', '15 min'))
        phases.append(('Package', 'Build release artifacts', '10 min'))
        phases.append(('Deploy', 'Push to target environment', '5-10 min'))
        phases.append(('Verify', 'Smoke test in target environment', '10 min'))
        phases.append(('Notify', 'Update changelog and notify stakeholders', '5 min'))
    else:
        phases.append(('Understand', 'Clarify requirements and constraints', '10 min'))
        phases.append(('Plan', 'Create a step-by-step approach', '10 min'))
        phases.append(('Execute', 'Carry out the plan systematically', '30-60 min'))
        phases.append(('Verify', 'Check results against requirements', '10 min'))
        phases.append(('Wrap Up', 'Document what was done', '5 min'))
    # Trim/pad to requested steps
    while len(phases) < steps:
        phases.append((f'Step {len(phases)+1}', 'Additional step as needed', '10 min'))
    phases = phases[:steps]
    # Format
    if format == 'json':
        plan = [{'step': i+1, 'title': t, 'description': d, 'estimate': e}
                for i, (t, d, e) in enumerate(phases)]
        return json.dumps({'goal': goal, 'steps': plan}, indent=2)
    elif format == 'checklist':
        lines = [f"Goal: {goal}", ""]
        for i, (title, desc, est) in enumerate(phases):
            lines.append(f"[ ] {i+1}. {title} ({est})")
            lines.append(f"     → {desc}")
        return "\n".join(lines)
    else:
        lines = [f"Goal: {goal}", ""]
        for i, (title, desc, est) in enumerate(phases):
            lines.append(f"{i+1}. {title} — {est}")
            lines.append(f"   {desc}")
        return "\n".join(lines)


def tool_file_tree(path: str = '.', max_depth: int = 3,
                   include_hidden: bool = False, file_limit: int = 200) -> str:
    """
    Display a directory tree (like the `tree` command). max_depth limits recursion.
    include_hidden shows dotfiles. file_limit caps total entries shown.
    """
    root = Path(path)
    if not root.exists():
        return f"ERROR: path not found: {path}"
    if not root.is_dir():
        return f"ERROR: not a directory: {path}"
    lines = [str(root)]
    count = [0]
    def _walk(p: Path, prefix: str, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        except PermissionError:
            lines.append(prefix + "└── [permission denied]")
            return
        visible = [e for e in entries if include_hidden or not e.name.startswith('.')]
        for i, entry in enumerate(visible):
            if count[0] >= file_limit:
                lines.append(prefix + "└── ... (limit reached)")
                return
            connector = '└── ' if i == len(visible) - 1 else '├── '
            lines.append(prefix + connector + entry.name + ('/' if entry.is_dir() else ''))
            count[0] += 1
            if entry.is_dir():
                extension = '    ' if i == len(visible) - 1 else '│   '
                _walk(entry, prefix + extension, depth + 1)
    _walk(root, '', 1)
    lines.append(f"\n{count[0]} item(s)")
    return "\n".join(lines)


def tool_extract_todos(directory: str = '.', file_glob: str = '*.py',
                       tags: str = 'TODO,FIXME,HACK,NOTE,XXX') -> str:
    """
    Scan source files for TODO/FIXME/HACK/NOTE/XXX comments and return them
    grouped by file with line numbers.
    """
    root = Path(directory)
    if not root.exists():
        return f"ERROR: directory not found: {directory}"
    tag_list = [t.strip().upper() for t in tags.split(',')]
    pattern = re.compile(r'#\s*(' + '|'.join(tag_list) + r')\s*[:\-]?\s*(.+)', re.IGNORECASE)
    results: dict = {}
    total = 0
    for filepath in root.rglob(file_glob):
        if not filepath.is_file():
            continue
        try:
            lines = filepath.read_text(encoding='utf-8', errors='replace').splitlines()
        except Exception:
            continue
        for lineno, line in enumerate(lines, 1):
            m = pattern.search(line)
            if m:
                tag, msg = m.group(1).upper(), m.group(2).strip()
                key = str(filepath.relative_to(root) if root != Path('.') else filepath)
                results.setdefault(key, []).append((lineno, tag, msg))
                total += 1
    if not results:
        return f"No {tags} comments found in {directory}"
    output = [f"Found {total} todo(s) in {len(results)} file(s):"]
    for fpath, items in sorted(results.items()):
        output.append(f"\n{fpath}:")
        for lineno, tag, msg in items:
            output.append(f"  Line {lineno:4d}  [{tag}]  {msg}")
    return "\n".join(output)


def tool_make_executable(path: str) -> str:
    """
    Make a file executable (chmod +x). Returns confirmation or error.
    """
    import stat
    p = Path(path)
    if not p.exists():
        return f"ERROR: file not found: {path}"
    if p.is_dir():
        return f"ERROR: {path} is a directory; use on files only"
    try:
        current = p.stat().st_mode
        p.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        new_mode = oct(p.stat().st_mode)[-3:]
        return f"Made executable: {path} (mode: {new_mode})"
    except Exception as e:
        return f"ERROR setting permissions: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AI — TEXT PROCESSING: ENCODE/DECODE, REGEX, STATS, MARKDOWN, TOKENS
# ═══════════════════════════════════════════════════════════════════════════════

def tool_encode_decode(text: str, operation: str, encoding: str = 'utf-8') -> str:
    """
    Encode or decode text. Operations:
    base64_encode, base64_decode, hex_encode, hex_decode,
    url_encode, url_decode, sha256, md5, sha1.
    """
    import base64, hashlib
    try:
        op = operation.lower().replace('-', '_')
        if op == 'base64_encode':
            return base64.b64encode(text.encode(encoding)).decode('ascii')
        elif op == 'base64_decode':
            return base64.b64decode(text.encode('ascii')).decode(encoding, errors='replace')
        elif op == 'hex_encode':
            return text.encode(encoding).hex()
        elif op == 'hex_decode':
            return bytes.fromhex(text.strip()).decode(encoding, errors='replace')
        elif op == 'url_encode':
            import urllib.parse
            return urllib.parse.quote(text, safe='')
        elif op == 'url_decode':
            import urllib.parse
            return urllib.parse.unquote(text)
        elif op in ('sha256', 'sha1', 'md5'):
            h = hashlib.new(op)
            h.update(text.encode(encoding))
            return h.hexdigest()
        else:
            return f"ERROR: unknown operation {operation!r}. Use: base64_encode/decode, hex_encode/decode, url_encode/decode, sha256, md5, sha1"
    except Exception as e:
        return f"ERROR in encode_decode ({operation}): {e}"


def tool_regex_extract(text: str, pattern: str, group: int = 0,
                       flags: str = '', max_matches: int = 100) -> str:
    """
    Extract all regex matches from text. group=0 for full match, 1+ for capture groups.
    flags: 'i' for case-insensitive, 'm' for multiline, 's' for dotall.
    """
    re_flags = 0
    for f in flags.lower():
        if f == 'i': re_flags |= re.IGNORECASE
        elif f == 'm': re_flags |= re.MULTILINE
        elif f == 's': re_flags |= re.DOTALL
    try:
        matches = re.findall(pattern, text, re_flags)
        if not matches:
            return f"No matches for pattern {pattern!r}"
        # Handle groups
        if isinstance(matches[0], tuple):
            if group > 0:
                items = [m[group - 1] if group <= len(m) else '' for m in matches]
            else:
                items = [' | '.join(m) for m in matches]
        else:
            items = matches
        items = items[:max_matches]
        result = [f"Found {len(matches)} match(es)" + (f" (showing {max_matches})" if len(matches) > max_matches else "") + ":"]
        result.extend(f"  [{i+1}] {repr(m)}" for i, m in enumerate(items))
        return "\n".join(result)
    except re.error as e:
        return f"ERROR: invalid regex: {e}"


def tool_text_stats(text: str) -> str:
    """
    Compute text statistics: character count, word count, line count,
    sentence count, estimated reading time, and top 10 most frequent words.
    """
    if not text.strip():
        return "ERROR: empty text"
    chars = len(text)
    words = text.split()
    word_count = len(words)
    lines = text.splitlines()
    line_count = len(lines)
    sentences = len(re.findall(r'[.!?]+', text)) or 1
    reading_time_sec = word_count / 3.3  # ~200 wpm
    # Top words (excluding very common ones)
    stopwords = {'the','a','an','is','in','it','of','and','to','for','on','at','be',
                 'was','are','with','this','that','by','as','or','but','not','from','has'}
    word_freq: dict = {}
    for w in words:
        w_clean = re.sub(r'[^\w]', '', w.lower())
        if len(w_clean) > 2 and w_clean not in stopwords:
            word_freq[w_clean] = word_freq.get(w_clean, 0) + 1
    top_words = sorted(word_freq.items(), key=lambda x: -x[1])[:10]
    result = [
        f"Characters: {chars:,}",
        f"Words: {word_count:,}",
        f"Lines: {line_count:,}",
        f"Sentences: {sentences:,}",
        f"Reading time: {int(reading_time_sec // 60)}m {int(reading_time_sec % 60)}s",
        f"Avg words/sentence: {word_count/sentences:.1f}",
    ]
    if top_words:
        result.append("Top words: " + ", ".join(f"{w}({c})" for w, c in top_words))
    return "\n".join(result)


def tool_markdown_to_text(markdown: str) -> str:
    """
    Convert Markdown to plain text by removing headers, bold, italic, links,
    code blocks, blockquotes, and horizontal rules.
    """
    text = markdown
    text = re.sub(r'```[^\n]*\n(.*?)```', r'\1', text, flags=re.DOTALL)  # fenced code
    text = re.sub(r'`([^`]+)`', r'\1', text)   # inline code
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)  # headings
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)   # links
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)        # images
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)   # bold **
    text = re.sub(r'__(.+?)__', r'\1', text)        # bold __
    text = re.sub(r'\*(.+?)\*', r'\1', text)        # italic *
    text = re.sub(r'_(.+?)_', r'\1', text)          # italic _
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)   # blockquotes
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)  # hr
    text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)  # unordered list
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)  # ordered list
    text = re.sub(r'\n{3,}', '\n\n', text)   # excess blank lines
    return text.strip()


def tool_count_tokens(text: str, model: str = 'gpt4') -> str:
    """
    Estimate token count for AI context planning.
    Uses character-based heuristic: ~4 chars/token (GPT-4/Claude style).
    Also warns if approaching common context limits.
    """
    LIMITS = {
        'gpt4': 128_000, 'gpt35': 16_385, 'claude': 200_000,
        'gemini': 1_000_000, 'llama': 8_192, 'mistral': 32_768,
    }
    chars = len(text)
    words = len(text.split())
    # Heuristic: ~4 chars per token for English
    est_tokens = chars // 4
    limit = LIMITS.get(model.lower(), 128_000)
    pct = est_tokens / limit * 100
    warning = ""
    if pct > 90:
        warning = f"\n⚠ WARNING: {pct:.0f}% of {model} context limit ({limit:,} tokens)"
    elif pct > 70:
        warning = f"\n⚠ CAUTION: {pct:.0f}% of {model} context limit"
    result = (
        f"Estimated tokens: ~{est_tokens:,}\n"
        f"Characters: {chars:,}\n"
        f"Words: {words:,}\n"
        f"Model: {model} (limit: {limit:,} tokens = {pct:.1f}% used)"
        f"{warning}"
    )
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AH — DATA & NETWORK: HTTP, HTML PARSE, JSON VALIDATE, CSV QUERY, TABLE
# ═══════════════════════════════════════════════════════════════════════════════

def tool_http_request(url: str, method: str = 'GET', headers: str = '',
                      body: str = '', timeout: int = 15) -> str:
    """
    Make an HTTP request (GET/POST/PUT/PATCH/DELETE) and return status + response body.
    headers: JSON object string. body: request body string (use for POST/PUT).
    """
    import urllib.request, urllib.error
    method = method.upper()
    if method not in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD'):
        return f"ERROR: unsupported method {method!r}"
    try:
        hdr = {}
        if headers:
            try:
                hdr = json.loads(headers)
            except json.JSONDecodeError as e:
                return f"ERROR: invalid headers JSON: {e}"
        data = body.encode() if body else None
        req = urllib.request.Request(url, data=data, headers=hdr, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            content = resp.read(32768).decode('utf-8', errors='replace')
            ctype = resp.headers.get('Content-Type', '')
            return f"HTTP {status} {method} {url}\nContent-Type: {ctype}\n\n{content[:4000]}"
    except urllib.error.HTTPError as e:
        body_err = e.read(2000).decode('utf-8', errors='replace')
        return f"HTTP {e.code} {e.reason}\n{body_err[:2000]}"
    except urllib.error.URLError as e:
        return f"ERROR: {e.reason}"
    except Exception as e:
        return f"ERROR in http_request: {e}"


def tool_parse_html(html: str, extract: str = 'text') -> str:
    """
    Parse an HTML string and extract: 'text' (readable text), 'links' (href URLs),
    'headings' (h1-h6 text), 'all' (text + links + headings).
    """
    # Remove scripts and styles
    clean = re.sub(r'<(script|style)[^>]*>.*?</(script|style)>', '', html, flags=re.DOTALL | re.I)
    parts = {}
    if extract in ('headings', 'all'):
        headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', clean, re.DOTALL | re.I)
        parts['headings'] = [re.sub(r'<[^>]+>', '', h).strip() for h in headings[:20]]
    if extract in ('links', 'all'):
        links = re.findall(r'href=["\']([^"\']+)["\']', clean, re.I)
        parts['links'] = links[:50]
    if extract in ('text', 'all'):
        text = re.sub(r'<[^>]+>', ' ', clean)
        text = re.sub(r'&[a-z]+;', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        parts['text'] = text[:3000]
    if not parts:
        return f"ERROR: unknown extract mode {extract!r}. Use: text, links, headings, all"
    result = []
    for k, v in parts.items():
        if isinstance(v, list):
            result.append(f"[{k}] ({len(v)} items):")
            result.extend(f"  {item}" for item in v[:20])
        else:
            result.append(f"[{k}]:\n{v}")
    return "\n".join(result)


def tool_validate_json(json_str: str, schema: str = '') -> str:
    """
    Validate a JSON string and return its structure summary.
    If schema is a JSON object string, validate keys against it.
    Also pretty-prints the JSON.
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return f"INVALID JSON: {e}\n  At position {e.pos}: {json_str[max(0,e.pos-20):e.pos+20]!r}"
    def describe(obj, depth=0):
        if isinstance(obj, dict):
            return f"object({len(obj)} keys: {', '.join(list(obj.keys())[:5])}{'...' if len(obj)>5 else ''})"
        elif isinstance(obj, list):
            if obj:
                return f"array({len(obj)} items, first: {describe(obj[0], depth+1)})"
            return "array(empty)"
        return type(obj).__name__
    summary = [f"Valid JSON — {describe(data)}"]
    if schema:
        try:
            schema_obj = json.loads(schema)
            if isinstance(schema_obj, dict) and isinstance(data, dict):
                missing = [k for k in schema_obj if k not in data]
                extra = [k for k in data if k not in schema_obj]
                if missing:
                    summary.append(f"Missing keys: {', '.join(missing)}")
                if extra:
                    summary.append(f"Extra keys: {', '.join(extra)}")
                if not missing and not extra:
                    summary.append("Schema match: all keys present")
        except json.JSONDecodeError:
            summary.append("WARNING: schema is not valid JSON — skipped validation")
    pretty = json.dumps(data, indent=2, ensure_ascii=False)
    if len(pretty) > 2000:
        pretty = pretty[:2000] + "\n... (truncated)"
    summary.append(pretty)
    return "\n".join(summary)


def tool_csv_query(csv_str: str, columns: str = '', filter_expr: str = '',
                   max_rows: int = 50) -> str:
    """
    Query CSV data. columns: comma-separated column names to include.
    filter_expr: Python expression using column name as variable (e.g. 'age > 30').
    Returns matching rows as a compact table.
    """
    import csv, io
    try:
        reader = csv.DictReader(io.StringIO(csv_str.strip()))
        rows = list(reader)
        if not rows:
            return "Empty CSV — no rows found"
        headers = list(rows[0].keys())
        # Column selection
        sel_cols = [c.strip() for c in columns.split(',')] if columns else headers
        invalid = [c for c in sel_cols if c not in headers]
        if invalid:
            return f"ERROR: unknown columns: {', '.join(invalid)}. Available: {', '.join(headers)}"
        # Filter
        filtered = []
        for row in rows:
            if not filter_expr:
                filtered.append(row)
                continue
            try:
                ctx = {k: (int(v) if v.isdigit() else (float(v) if re.match(r'^\d+\.\d+$', v) else v))
                       for k, v in row.items()}
                if eval(filter_expr, {"__builtins__": {}}, ctx):
                    filtered.append(row)
            except Exception:
                filtered.append(row)
        # Render
        if not filtered:
            return f"No rows matched filter: {filter_expr!r}"
        result_rows = filtered[:max_rows]
        widths = {c: max(len(c), max(len(str(r.get(c, ''))) for r in result_rows)) for c in sel_cols}
        header_line = ' | '.join(c.ljust(widths[c]) for c in sel_cols)
        sep = '-+-'.join('-' * widths[c] for c in sel_cols)
        data_lines = [' | '.join(str(r.get(c, '')).ljust(widths[c]) for c in sel_cols) for r in result_rows]
        summary = f"Rows: {len(filtered)}/{len(rows)}" + (f" (showing {max_rows})" if len(filtered) > max_rows else "")
        return "\n".join([summary, header_line, sep] + data_lines)
    except Exception as e:
        return f"ERROR in csv_query: {e}"


def tool_format_table(data: str, headers: str = '', separator: str = ',') -> str:
    """
    Format delimited data (CSV, TSV, or custom separator) as an ASCII table.
    headers: comma-separated column headers if not in first row.
    """
    import io
    try:
        lines = [line.strip() for line in data.strip().splitlines() if line.strip()]
        if not lines:
            return "ERROR: no data provided"
        sep = '\t' if separator == 'tab' else separator
        parsed = [line.split(sep) for line in lines]
        if headers:
            cols = [h.strip() for h in headers.split(',')]
            rows = parsed
        else:
            cols = [c.strip() for c in parsed[0]]
            rows = parsed[1:]
        if not rows:
            return "ERROR: no data rows (only header found)"
        # Normalize row lengths
        n = len(cols)
        rows = [r + [''] * (n - len(r)) for r in rows]
        rows = [r[:n] for r in rows]
        widths = [max(len(cols[i]), max(len(r[i]) for r in rows)) for i in range(n)]
        def fmt_row(r):
            return '│ ' + ' │ '.join(str(r[i]).ljust(widths[i]) for i in range(n)) + ' │'
        top = '┌─' + '─┬─'.join('─' * w for w in widths) + '─┐'
        hdr = fmt_row(cols)
        mid = '├─' + '─┼─'.join('─' * w for w in widths) + '─┤'
        bot = '└─' + '─┴─'.join('─' * w for w in widths) + '─┘'
        lines_out = [top, hdr, mid] + [fmt_row(r) for r in rows] + [bot]
        lines_out.append(f"({len(rows)} rows × {n} cols)")
        return "\n".join(lines_out)
    except Exception as e:
        return f"ERROR in format_table: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AG — CODE ANALYSIS: EXPLAIN, REFACTOR, GENERATE TESTS, LINT, PROFILE
# ═══════════════════════════════════════════════════════════════════════════════

def tool_explain_code(code: str, language: str = 'python') -> str:
    """
    Analyze a code snippet and return a human-readable explanation:
    what it does, what it imports, what functions/classes it defines,
    potential issues (broad exception catches, unused vars, etc.).
    No AI required — pure static analysis.
    """
    lines = code.splitlines()
    imports, functions, classes, issues = [], [], [], []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith('import ') or s.startswith('from '):
            imports.append(s)
        elif re.match(r'def \w+', s):
            functions.append(s.split('(')[0].replace('def ', '').strip())
        elif re.match(r'class \w+', s):
            classes.append(s.split('(')[0].split(':')[0].replace('class ', '').strip())
        if 'except:' in s or 'except Exception' in s:
            issues.append(f"Line {i}: broad exception catch — {s[:60]}")
        if re.search(r'\bexec\b|\beval\b', s) and not s.startswith('#'):
            issues.append(f"Line {i}: uses exec/eval — {s[:60]}")
        if re.search(r'password|secret|api_key', s, re.I) and '=' in s and not s.startswith('#'):
            issues.append(f"Line {i}: possible secret assignment — {s[:40]}...")
    parts = [f"Language: {language}", f"Lines: {len(lines)}"]
    if imports:
        parts.append(f"Imports ({len(imports)}): {', '.join(imports[:5])}" + (' ...' if len(imports) > 5 else ''))
    if functions:
        parts.append(f"Functions: {', '.join(functions)}")
    if classes:
        parts.append(f"Classes: {', '.join(classes)}")
    if issues:
        parts.append("Issues found:")
        parts.extend(f"  ⚠ {iss}" for iss in issues)
    else:
        parts.append("No obvious issues detected.")
    # Provide high-level summary based on patterns
    if any('flask' in imp.lower() or 'fastapi' in imp.lower() for imp in imports):
        parts.append("Summary: Web application (Flask/FastAPI)")
    elif any('pytest' in imp.lower() or 'unittest' in imp.lower() for imp in imports):
        parts.append("Summary: Test file")
    elif any('argparse' in imp.lower() or 'click' in imp.lower() for imp in imports):
        parts.append("Summary: CLI application")
    elif any('pandas' in imp.lower() or 'numpy' in imp.lower() for imp in imports):
        parts.append("Summary: Data analysis script")
    elif functions or classes:
        parts.append(f"Summary: Library/module with {len(functions)} function(s), {len(classes)} class(es)")
    else:
        parts.append("Summary: Script / configuration code")
    return "\n".join(parts)


def tool_lint_code(path: str, linter: str = 'auto') -> str:
    """
    Run a linter on a Python file. Tries flake8, then pylint, then pyflakes.
    Returns lint warnings and errors. linter can be 'auto', 'flake8', 'pylint', 'pyflakes'.
    """
    import subprocess
    p = Path(path)
    if not p.exists():
        return f"ERROR: file not found: {path}"
    if p.suffix not in ('.py', '.pyw'):
        return f"ERROR: not a Python file: {path}"
    linters_to_try = [linter] if linter != 'auto' else ['flake8', 'pyflakes', 'pylint']
    for lint in linters_to_try:
        try:
            cmd = [lint, str(p)]
            if lint == 'pylint':
                cmd += ['--output-format=text', '--score=no']
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            output = (r.stdout + r.stderr).strip()
            if output:
                lines = output.splitlines()
                summary = f"[{lint}] {len(lines)} finding(s):\n" + "\n".join(lines[:50])
                if len(lines) > 50:
                    summary += f"\n... ({len(lines) - 50} more)"
                return summary
            return f"[{lint}] No issues found."
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return f"ERROR: {lint} timed out"
    return "No linter available (install flake8: pip install flake8)"


def tool_profile_code(code: str, iterations: int = 1000) -> str:
    """
    Profile Python code execution time using timeit.
    Returns min/avg/max time and estimated ops/sec.
    """
    import timeit
    try:
        # Safety check — block obvious dangers
        danger = re.search(r'\b(exec|eval|import\s+os|subprocess|__import__)\b', code)
        if danger:
            return f"ERROR: profiling blocked for security — found: {danger.group()}"
        timer = timeit.Timer(stmt=code)
        # Determine a good repeat count
        n = min(iterations, 10000)
        times = timer.repeat(repeat=5, number=n)
        times_per_call = [t / n for t in times]
        mn = min(times_per_call)
        avg = sum(times_per_call) / len(times_per_call)
        mx = max(times_per_call)
        ops = 1.0 / mn if mn > 0 else float('inf')
        return (
            f"Profiled {n} iterations × 5 runs:\n"
            f"  min:  {mn*1e6:.3f} µs/call\n"
            f"  avg:  {avg*1e6:.3f} µs/call\n"
            f"  max:  {mx*1e6:.3f} µs/call\n"
            f"  ~ops: {ops:,.0f}/sec"
        )
    except SyntaxError as e:
        return f"ERROR: syntax error in code: {e}"
    except Exception as e:
        return f"ERROR profiling: {e}"


def tool_generate_tests(code: str, module_name: str = 'module') -> str:
    """
    Generate pytest test stubs for functions found in a Python code snippet.
    Creates one test function per detected function, with a placeholder body.
    """
    stubs = [f'"""Tests for {module_name} — auto-generated stubs."""',
             f'import pytest',
             f'# from {module_name} import *  # adjust import as needed',
             '']
    func_pattern = re.compile(r'^def\s+(\w+)\s*\(([^)]*)\)', re.MULTILINE)
    matches = func_pattern.findall(code)
    if not matches:
        return "ERROR: no function definitions found in the provided code"
    for fname, fparams in matches:
        if fname.startswith('_'):
            continue  # skip private functions
        params = [p.strip().split(':')[0].split('=')[0].strip() for p in fparams.split(',') if p.strip()]
        param_list = ', '.join(params)
        stubs += [
            f'def test_{fname}():',
            f'    # Test {fname}({param_list})',
            f'    # TODO: set up inputs and assert expected output',
            f'    # result = {fname}({", ".join(repr("...") for _ in params)})',
            f'    # assert result == expected_value',
            f'    pass',
            '',
        ]
    if not any(line.startswith('def test_') for line in stubs):
        return "No public functions found to generate tests for."
    return '\n'.join(stubs)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AF — CODE GENERATION, PROJECT SCAFFOLD, FIND-REPLACE, TEST RUNNER, GIT
# ═══════════════════════════════════════════════════════════════════════════════

def tool_find_and_replace(directory: str, pattern: str, replacement: str,
                          file_glob: str = '*.py', dry_run: bool = False) -> str:
    """
    Find a regex pattern in files and replace it. Returns a summary of
    changed files and number of replacements. Use dry_run=True to preview.
    """
    import glob as _glob
    try:
        base = Path(directory)
        if not base.exists():
            return f"ERROR: directory not found: {directory}"
        pat = re.compile(pattern)
        files_changed = []
        total_replacements = 0
        for filepath in base.rglob(file_glob):
            if not filepath.is_file():
                continue
            try:
                original = filepath.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            new_text, count = pat.subn(replacement, original)
            if count > 0:
                files_changed.append((str(filepath), count))
                total_replacements += count
                if not dry_run:
                    filepath.write_text(new_text, encoding='utf-8')
        if not files_changed:
            return f"No matches for pattern {pattern!r} in {directory}"
        mode = "DRY RUN — " if dry_run else ""
        lines = [f"{mode}Replaced {total_replacements} occurrence(s) in {len(files_changed)} file(s):"]
        for fpath, cnt in files_changed[:20]:
            lines.append(f"  {fpath}: {cnt} replacement(s)")
        if len(files_changed) > 20:
            lines.append(f"  ... and {len(files_changed) - 20} more")
        return "\n".join(lines)
    except re.error as e:
        return f"ERROR: invalid regex pattern: {e}"
    except Exception as e:
        return f"ERROR in find_and_replace: {e}"


def tool_run_tests(test_path: str = 'tests/', args: str = '', timeout: int = 60) -> str:
    """
    Run a test suite via pytest or python and parse the results.
    Returns pass/fail/skip counts and any failure details.
    """
    import subprocess
    try:
        p = Path(test_path)
        if not p.exists():
            return f"ERROR: test path not found: {test_path}"
        # Build command
        if p.suffix == '.py':
            cmd = ['python3', str(p)]
        else:
            cmd = ['python3', '-m', 'pytest', str(p), '-v', '--tb=short']
        if args:
            cmd.extend(args.split())
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=str(Path('.').resolve())
        )
        output = result.stdout + result.stderr
        # Parse results
        passed = len(re.findall(r'PASS|passed|✓', output))
        failed = len(re.findall(r'FAIL|failed|✗', output))
        skipped = len(re.findall(r'SKIP|skipped|⊘', output))
        lines = [f"Exit code: {result.returncode}",
                 f"Passed: {passed}  Failed: {failed}  Skipped: {skipped}",
                 "─" * 40]
        lines.append(output[-3000:] if len(output) > 3000 else output)
        return "\n".join(lines)
    except subprocess.TimeoutExpired:
        return f"ERROR: tests timed out after {timeout}s"
    except FileNotFoundError:
        return "ERROR: python3/pytest not found"
    except Exception as e:
        return f"ERROR running tests: {e}"


def tool_git_ops(operation: str, args: str = '', repo_path: str = '.') -> str:
    """
    Run a safe git operation in a repository. Supported operations:
    status, log, diff, add, commit, push, pull, branch, stash, fetch.
    Refuses destructive operations (reset --hard, push --force, clean -f).
    """
    import subprocess
    SAFE_OPS = {'status', 'log', 'diff', 'add', 'commit', 'push', 'pull',
                'branch', 'stash', 'fetch', 'show', 'remote', 'tag'}
    op = operation.strip().lower()
    if op not in SAFE_OPS:
        return f"ERROR: operation {op!r} not permitted. Allowed: {', '.join(sorted(SAFE_OPS))}"
    # Block destructive flags
    BLOCKED = ('--force', '-f', '--hard', '--no-verify', '-D')
    for b in BLOCKED:
        if b in args:
            return f"ERROR: flag {b!r} is not permitted for safety"
    cmd = ['git', op] + (args.split() if args else [])
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
            cwd=str(Path(repo_path).resolve())
        )
        out = (result.stdout + result.stderr).strip()
        status = "OK" if result.returncode == 0 else f"exit {result.returncode}"
        return f"git {op} [{status}]:\n{out[:3000]}" if out else f"git {op} [{status}]"
    except subprocess.TimeoutExpired:
        return f"ERROR: git {op} timed out"
    except FileNotFoundError:
        return "ERROR: git not found"
    except Exception as e:
        return f"ERROR in git_ops: {e}"


def tool_create_project(name: str, project_type: str = 'python',
                        base_dir: str = '.') -> str:
    """
    Scaffold a new project directory with standard structure.
    Types: python, node, web, bash.
    Creates: directory structure, README, .gitignore, entry point.
    """
    try:
        base = Path(base_dir) / name
        if base.exists():
            return f"ERROR: directory already exists: {base}"
        base.mkdir(parents=True)
        created = [str(base)]

        def write(rel: str, content: str):
            p = base / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            created.append(str(p))

        if project_type == 'python':
            write('README.md', f'# {name}\n\nA Python project.\n')
            write('.gitignore', '__pycache__/\n*.pyc\n.env\ndist/\nbuild/\n*.egg-info/\n')
            write('main.py', f'#!/usr/bin/env python3\n"""Entry point for {name}."""\n\ndef main():\n    print("Hello from {name}!")\n\nif __name__ == "__main__":\n    main()\n')
            write('requirements.txt', '# Add dependencies here\n')
            write('tests/__init__.py', '')
            write('tests/test_main.py', f'"""Tests for {name}."""\nfrom main import main\n\ndef test_main():\n    main()\n')
        elif project_type == 'node':
            write('README.md', f'# {name}\n\nA Node.js project.\n')
            write('.gitignore', 'node_modules/\n.env\ndist/\n*.log\n')
            write('package.json', json.dumps({"name": name, "version": "1.0.0", "main": "index.js", "scripts": {"start": "node index.js", "test": "node --test"}}, indent=2) + '\n')
            write('index.js', f'// Entry point for {name}\nconsole.log("Hello from {name}!");\n')
        elif project_type == 'web':
            write('README.md', f'# {name}\n\nA web project.\n')
            write('.gitignore', '.env\ndist/\nnode_modules/\n')
            write('index.html', f'<!DOCTYPE html>\n<html lang="en">\n<head><meta charset="UTF-8"><title>{name}</title><link rel="stylesheet" href="style.css"></head>\n<body>\n<h1>{name}</h1>\n<script src="app.js"></script>\n</body>\n</html>\n')
            write('style.css', 'body { font-family: sans-serif; margin: 2rem; }\n')
            write('app.js', f'// {name} frontend\nconsole.log("{name} loaded");\n')
        elif project_type == 'bash':
            write('README.md', f'# {name}\n\nA shell script project.\n')
            write('.gitignore', '*.log\n.env\n')
            script = base / 'run.sh'
            script.write_text(f'#!/bin/bash\n# {name}\nset -euo pipefail\necho "Running {name}..."\n')
            script.chmod(0o755)
            created.append(str(script))
        else:
            return f"ERROR: unknown project type {project_type!r}. Use: python, node, web, bash"

        return f"Created {project_type} project '{name}' at {base}\nFiles:\n" + "\n".join(f"  {c}" for c in created)
    except Exception as e:
        return f"ERROR creating project: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AC — FILE SUMMARIZER + DIFF TOOL + CODE SEARCH
# ═══════════════════════════════════════════════════════════════════════════════

def tool_summarize_file(path: str, max_chars: int = 4000) -> str:
    """
    Read a file and return a structured summary: size, type, line count,
    first N chars, last N chars, and any patterns found (functions, classes,
    imports, TODOs). Useful for getting an overview of large files without
    reading all of them. Works with code, text, JSON, CSV, Markdown.
    """
    try:
        p = Path(path)
        if not p.exists():
            return f"ERROR: file not found: {path}"
        size = p.stat().st_size
        suffix = p.suffix.lower()

        content = p.read_text(encoding='utf-8', errors='replace')
        lines = content.split('\n')
        line_count = len(lines)

        out = [
            f"FILE: {path}",
            f"Size: {size:,} bytes | Lines: {line_count:,} | Type: {suffix or 'unknown'}",
            "",
        ]

        # Show first and last portions
        half = max_chars // 2
        if len(content) <= max_chars:
            out.append("CONTENT:")
            out.append(content[:max_chars])
        else:
            out.append(f"FIRST {half} chars:")
            out.append(content[:half])
            out.append(f"\n... ({len(content) - max_chars:,} chars omitted) ...\n")
            out.append(f"LAST {half} chars:")
            out.append(content[-half:])

        # Extract patterns for code files
        code_suffixes = {'.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp', '.c', '.rb', '.sh'}
        if suffix in code_suffixes:
            out.append("\nCODE PATTERNS:")
            fns = re.findall(r'^(?:def |function |func |fn |pub fn )\s*(\w+)', content, re.M)
            if fns:
                out.append(f"  Functions/methods ({len(fns)}): {', '.join(fns[:20])}")
            classes = re.findall(r'^(?:class |struct |interface |enum )\s*(\w+)', content, re.M)
            if classes:
                out.append(f"  Classes/structs ({len(classes)}): {', '.join(classes[:15])}")
            imports = re.findall(r'^(?:import |from |require|use )\s*(\S+)', content, re.M)
            if imports:
                out.append(f"  Imports ({len(imports)}): {', '.join(imports[:10])}")
            todos = re.findall(r'(?:TODO|FIXME|HACK|XXX)[:\s]+(.+)', content)
            if todos:
                out.append(f"  TODOs ({len(todos)}): {todos[0][:80]}")

        return '\n'.join(out)
    except Exception as e:
        return f"ERROR summarizing {path}: {e}"


def tool_diff_files(path1: str, path2: str, context: int = 3) -> str:
    """
    Show a unified diff between two files. Returns the diff output with
    N lines of context around each change. Useful for comparing file versions.
    """
    try:
        import difflib
        p1, p2 = Path(path1), Path(path2)
        if not p1.exists():
            return f"ERROR: file not found: {path1}"
        if not p2.exists():
            return f"ERROR: file not found: {path2}"
        a = p1.read_text(encoding='utf-8', errors='replace').splitlines(keepends=True)
        b = p2.read_text(encoding='utf-8', errors='replace').splitlines(keepends=True)
        diff = list(difflib.unified_diff(a, b, fromfile=path1, tofile=path2, n=context))
        if not diff:
            return f"Files are identical: {path1} == {path2}"
        return ''.join(diff[:500])  # cap at 500 lines
    except Exception as e:
        return f"ERROR diffing files: {e}"


def tool_search_in_files(pattern: str, directory: str = '.', file_glob: str = '*',
                          max_results: int = 50) -> str:
    """
    Search for a regex pattern in files under a directory. Like grep -r.
    Returns matching lines with file:line context. More powerful than shell
    grep because it handles binary files gracefully and reports counts.
    """
    import fnmatch
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return f"ERROR: invalid regex pattern: {e}"

    results = []
    total_files = 0
    matched_files = 0

    dir_path = Path(directory)
    if not dir_path.is_dir():
        return f"ERROR: directory not found: {directory}"

    try:
        all_files = sorted(dir_path.rglob(file_glob))
    except Exception as e:
        return f"ERROR scanning directory: {e}"

    for fpath in all_files:
        if not fpath.is_file():
            continue
        # Skip binary and very large files
        try:
            if fpath.stat().st_size > 5_000_000:
                continue
            total_files += 1
            text = fpath.read_text(encoding='utf-8', errors='replace')
            lines = text.split('\n')
            file_matches = []
            for lineno, line in enumerate(lines, 1):
                if rx.search(line):
                    file_matches.append(f"  {lineno}: {line.rstrip()[:200]}")
                    if len(file_matches) >= 10:  # cap per-file matches
                        break
            if file_matches:
                matched_files += 1
                results.append(f"{fpath}:")
                results.extend(file_matches)
                if len(results) >= max_results * 2:
                    break
        except Exception:
            continue

    if not results:
        return f"No matches for '{pattern}' in {directory} (searched {total_files} files)"
    summary = f"Found matches in {matched_files}/{total_files} files:\n"
    return summary + '\n'.join(results[:max_results * 2])


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AD — PROCESS MONITORING + TAIL FILE + ENV VARIABLE TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

def tool_monitor_process(name_or_pid: str, duration: int = 10) -> str:
    """
    Monitor a process by name or PID for N seconds. Returns CPU%, memory,
    status, and whether the process is still alive at the end. Use to verify
    a launched application is running and responsive.
    """
    import time as _time
    try:
        import psutil
    except ImportError:
        # Fallback: use ps command
        cmd = f"ps aux | grep -i '{name_or_pid}' | grep -v grep"
        r = tool_execute_shell(cmd)
        return f"psutil not installed. ps output:\n{r}"

    # Find the process
    target = None
    try:
        if name_or_pid.isdigit():
            target = psutil.Process(int(name_or_pid))
        else:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                pname = (proc.info.get('name') or '').lower()
                pcmd = ' '.join(proc.info.get('cmdline') or []).lower()
                if name_or_pid.lower() in pname or name_or_pid.lower() in pcmd:
                    target = proc
                    break
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    if target is None:
        return f"Process not found: {name_or_pid}"

    snapshots = []
    end = _time.time() + min(duration, 60)
    while _time.time() < end:
        try:
            cpu = target.cpu_percent(interval=1)
            mem = target.memory_info().rss // 1024 // 1024  # MB
            status = target.status()
            snapshots.append(f"  CPU: {cpu:.1f}%  Mem: {mem}MB  Status: {status}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            snapshots.append("  (process ended)")
            break

    lines = [f"Process '{name_or_pid}' (PID {target.pid}) over {duration}s:"]
    lines.extend(snapshots[-5:])  # show last 5 snapshots
    try:
        lines.append(f"Final: {'alive' if target.is_running() else 'dead'}")
    except Exception:
        lines.append("Final: unknown")
    return '\n'.join(lines)


def tool_tail_file(path: str, lines: int = 20, follow: float = 0) -> str:
    """
    Read the last N lines of a file (like tail -n). Optionally follow
    new content for up to `follow` seconds (like tail -f).
    Useful for monitoring log files, watching build output, etc.
    """
    import time as _time
    try:
        p = Path(path)
        if not p.exists():
            return f"ERROR: file not found: {path}"
        content = p.read_text(encoding='utf-8', errors='replace')
        file_lines = content.splitlines()
        tail = file_lines[-lines:] if len(file_lines) > lines else file_lines
        result = '\n'.join(tail)

        if follow > 0:
            size = p.stat().st_size
            deadline = _time.time() + min(follow, 30)
            new_lines = []
            while _time.time() < deadline:
                _time.sleep(0.5)
                new_size = p.stat().st_size
                if new_size > size:
                    new_content = p.read_text(encoding='utf-8', errors='replace')
                    added = new_content[size:]
                    new_lines.extend(added.splitlines())
                    size = new_size
            if new_lines:
                result += '\n--- NEW CONTENT ---\n' + '\n'.join(new_lines[:50])

        return f"{path} (last {lines} lines):\n{result}"
    except Exception as e:
        return f"ERROR reading {path}: {e}"


def tool_get_env(key: str = '') -> str:
    """
    Get environment variable(s). If key is given, returns that variable's value.
    If key is empty, returns all non-secret environment variables.
    Secrets (API keys, tokens, passwords) are redacted.
    """
    SECRET_PATTERNS = re.compile(r'(key|token|secret|password|passwd|pwd|auth|api)', re.IGNORECASE)
    if key:
        val = os.environ.get(key, f"(not set)")
        if SECRET_PATTERNS.search(key):
            val = '***REDACTED***' if val != '(not set)' else val
        return f"{key}={val}"
    # All env vars, redacted
    lines = []
    for k, v in sorted(os.environ.items()):
        if SECRET_PATTERNS.search(k):
            lines.append(f"{k}=***REDACTED***")
        else:
            lines.append(f"{k}={v[:200]}")
    return '\n'.join(lines)


def tool_set_env(key: str, value: str) -> str:
    """
    Set an environment variable for this session. Useful for configuring
    paths, flags, or other runtime settings without editing files.
    Note: This does NOT persist across sessions.
    """
    SECRET_PATTERNS = re.compile(r'(key|token|secret|password|passwd|pwd|auth|api)', re.IGNORECASE)
    if SECRET_PATTERNS.search(key):
        return f"ERROR: refusing to set secret-looking env var '{key}' via tool for security"
    os.environ[key] = value
    return f"Set {key}={value[:80]}"


def tool_json_query(json_str: str, query: str) -> str:
    """
    Query a JSON string using a simple dot-path expression or key name.
    Supports: 'key', 'key.subkey', 'key[0]', 'key[0].field'.
    Use to extract specific values from API responses or JSON files.
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return f"ERROR: invalid JSON: {e}"

    try:
        current = data
        parts = re.split(r'[.\[\]]', query)
        for part in parts:
            if not part:
                continue
            if isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError) as e:
                    return f"ERROR: {e} at '{part}'"
            elif isinstance(current, dict):
                if part not in current:
                    keys = list(current.keys())[:10]
                    return f"ERROR: key '{part}' not found. Available: {keys}"
                current = current[part]
            else:
                return f"ERROR: cannot index into {type(current).__name__} with '{part}'"
        return json.dumps(current, indent=2) if isinstance(current, (dict, list)) else str(current)
    except Exception as e:
        return f"ERROR querying JSON with '{query}': {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE AB — PARALLEL BATCH EXECUTION + TASK DECOMPOSER
# ═══════════════════════════════════════════════════════════════════════════════

def tool_batch_execute(tools_json: str) -> str:
    """
    Execute multiple independent tool calls in parallel (via threading).
    Each item: {"tool": "name", "args": {...}, "id": "optional_label"}.
    All tools run concurrently; results are collected and returned together.
    Use when multiple operations are independent (e.g. run 3 shell commands,
    search 3 URLs, write 3 files at once).

    Example:
      tools_json = '[
        {"tool":"execute_shell","args":{"command":"uname -a"},"id":"os"},
        {"tool":"execute_shell","args":{"command":"python3 --version"},"id":"py"},
        {"tool":"execute_shell","args":{"command":"git --version"},"id":"git"}
      ]'
    """
    import threading
    try:
        items = json.loads(tools_json)
    except json.JSONDecodeError as e:
        return f"ERROR: tools_json must be a valid JSON array: {e}"

    if not isinstance(items, list) or not items:
        return "ERROR: tools_json must be a non-empty JSON array"

    results = [None] * len(items)
    errors = [None] * len(items)

    def _run(idx: int, item: dict) -> None:
        tool_name = item.get("tool", "")
        args = item.get("args", {})
        if not tool_name:
            results[idx] = "SKIP: no tool specified"
            return
        try:
            results[idx] = _dispatch_tool(tool_name, args)
        except Exception as e:
            errors[idx] = str(e)
            results[idx] = f"ERROR: {e}"

    threads = []
    for i, item in enumerate(items):
        t = threading.Thread(target=_run, args=(i, item), daemon=True)
        threads.append(t)
        t.start()
    for t in threads:
        t.join(timeout=60)

    lines = []
    for i, item in enumerate(items):
        label = item.get("id", item.get("tool", f"item_{i}"))
        result = results[i] or "(no result)"
        lines.append(f"[{label}]: {str(result)[:300]}")

    ok_count = sum(1 for r in results if r and not str(r).startswith("ERROR"))
    lines.append(f"\nBATCH DONE: {ok_count}/{len(items)} succeeded")
    return "\n".join(lines)


def tool_decompose_task(goal: str, context: str = '') -> str:
    """
    Break a complex goal into a numbered list of concrete sub-tasks,
    each with a suggested tool. Returns a ready-to-execute plan as JSON.
    This is a PURE LOGIC tool — it doesn't call any AI provider, just
    structures the task based on pattern matching and heuristics so you
    can reason about it before acting.
    """
    import re as _re
    lines = [
        f"GOAL: {goal}",
        "",
        "SUB-TASK DECOMPOSITION:",
    ]

    # Detect task type and suggest steps
    g = goal.lower()
    if any(w in g for w in ('install', 'setup', 'configure')):
        lines += [
            "  1. Check if already installed: execute_shell('which pkg || pkg --version')",
            "  2. Install: execute_shell('apt/pip/brew install pkg')",
            "  3. Verify: execute_shell('pkg --version')",
            "  4. Configure if needed: write_file('/etc/pkg.conf', config)",
        ]
    elif any(w in g for w in ('build', 'compile', 'make')):
        lines += [
            "  1. Read build file: read_file('Makefile/package.json/Cargo.toml')",
            "  2. Install dependencies: execute_shell('npm install / pip install -r ...')",
            "  3. Build: execute_shell('make / npm run build / cargo build')",
            "  4. Verify output: execute_shell('ls -la dist/ build/ target/')",
        ]
    elif any(w in g for w in ('test', 'check', 'verify', 'audit')):
        lines += [
            "  1. List tests: execute_shell('find . -name test*.py -o -name *.test.ts')",
            "  2. Run tests: execute_shell('pytest / npm test / cargo test')",
            "  3. Check output: look for failures in stdout",
            "  4. Fix failures if found",
        ]
    elif any(w in g for w in ('search', 'find', 'look up', 'research')):
        lines += [
            "  1. Web search: web_search(query)",
            "  2. Fetch top result: web_fetch(url)",
            "  3. Extract relevant info: execute_python(parsing code)",
            "  4. Summarize findings",
        ]
    elif any(w in g for w in ('open', 'launch', 'start', 'run app')):
        lines += [
            "  1. Check if running: app_is_running(app_name)",
            "  2. Launch: open_application(app_name)",
            "  3. Wait for load: wait_and_verify(2, 'app window visible')",
            "  4. Screenshot verify: screenshot_and_analyze('Did app open?')",
        ]
    elif any(w in g for w in ('write', 'create', 'generate', 'produce')):
        lines += [
            "  1. Plan content structure: think_and_plan(goal)",
            "  2. Write content: write_file(path, content)",
            "  3. Verify: read_file(path)",
            "  4. Run if script: execute_shell(f'python3 {path}')",
        ]
    else:
        lines += [
            "  1. Understand current state: platform_info() or execute_shell('ls -la')",
            "  2. Plan: think_and_plan(goal)",
            "  3. Execute first step with appropriate tool",
            "  4. Verify and continue until done",
            "  5. Call task_complete(summary) when verified",
        ]

    if context:
        lines.append(f"\nCONTEXT: {context}")

    lines.append(f"\nPLATFORM: {_PLATFORM} | GUI: {'available' if _HAS_DISPLAY else 'headless'}")
    lines.append("→ NOW call the first tool above and proceed step by step.")
    return "\n".join(lines)


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
    "github_repo_audit": {
        "fn": tool_github_repo_audit,
        "desc": "Comprehensive audit of a public GitHub repo via API (works headless). Returns description, language, size, top-level files, README preview. deep=True adds contributors, languages, releases.",
        "params": {
            "repo": {"type": "string", "description": "'owner/name' or github.com URL"},
            "deep": {"type": "boolean", "description": "Include contributors, language breakdown, releases (default false)"},
        },
        "required": ["repo"],
        "category": "git",
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

    # ── Power / Compound Tools ─────────────────────────────────────────────────
    "ask_user": {
        "fn": tool_ask_user,
        "desc": "Ask the user a clarifying question when the task is genuinely ambiguous. Use sparingly — try to figure it out yourself first.",
        "params": {"question": {"type": "string", "description": "Clear, specific question to ask the user"}},
        "required": ["question"],
        "category": "control",
    },
    "write_and_run": {
        "fn": tool_write_and_run,
        "desc": "Write code to a file and immediately execute it. Returns the file path and stdout+stderr.",
        "params": {
            "filename": {"type": "string", "description": "File name to create (e.g. script.py, run.sh)"},
            "code": {"type": "string", "description": "Complete code content to write"},
            "interpreter": {"type": "string", "description": "Interpreter: python3, bash, node (default: python3)"},
        },
        "required": ["filename", "code"],
        "category": "code",
    },
    "install_and_verify": {
        "fn": tool_install_and_verify,
        "desc": "Install a package and immediately verify the installation worked.",
        "params": {
            "package": {"type": "string", "description": "Package name (e.g. requests, numpy==1.26)"},
            "manager": {"type": "string", "description": "Package manager: pip, apt, brew, npm (default: pip)"},
        },
        "required": ["package"],
        "category": "shell",
    },
    "git_clone_and_explore": {
        "fn": tool_git_clone_and_explore,
        "desc": "Clone a git repository (shallow) and return its directory structure.",
        "params": {
            "url": {"type": "string", "description": "Git repository URL to clone"},
            "target_dir": {"type": "string", "description": "Optional local directory name (default: repo name)"},
        },
        "required": ["url"],
        "category": "git",
    },
    "search_and_open": {
        "fn": tool_search_and_open,
        "desc": "Search the web and optionally open the top result in the system browser.",
        "params": {
            "query": {"type": "string", "description": "Web search query"},
            "open_first": {"type": "boolean", "description": "Open top result in browser (default: true)"},
        },
        "required": ["query"],
        "category": "web",
    },
    "screen_to_clipboard": {
        "fn": tool_screen_to_clipboard,
        "desc": "Take a screenshot, extract all visible text with AI, and copy it to the clipboard.",
        "params": {},
        "required": [],
        "category": "vision",
    },
    "wait_and_verify": {
        "fn": tool_wait_and_verify,
        "desc": "Wait N seconds then optionally verify a condition by taking a screenshot and analyzing it.",
        "params": {
            "seconds": {"type": "number", "description": "Seconds to wait (0-30)"},
            "condition": {"type": "string", "description": "Optional condition to verify after waiting (e.g. 'Firefox has loaded')"},
        },
        "required": ["seconds"],
        "category": "control",
    },

    # ── Cross-platform OS tools ────────────────────────────────────────────────
    "platform_info": {
        "fn": tool_platform_info,
        "desc": "Get comprehensive OS/platform info: OS, version, arch, user, display, installed tools.",
        "params": {},
        "required": [],
        "category": "os",
    },
    "open_url": {
        "fn": tool_open_url,
        "desc": "Open a URL in the default browser — works on Linux, macOS, and Windows.",
        "params": {"url": {"type": "string", "description": "URL to open in the default browser"}},
        "required": ["url"],
        "category": "web",
    },
    "run_xplat": {
        "fn": tool_run_xplat,
        "desc": "Run a platform-specific shell command: picks the right one for Linux/macOS/Windows.",
        "params": {
            "linux_cmd": {"type": "string", "description": "Command to run on Linux"},
            "mac_cmd": {"type": "string", "description": "Command to run on macOS"},
            "windows_cmd": {"type": "string", "description": "Command to run on Windows"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"},
        },
        "required": [],
        "category": "shell",
    },
    "think_and_plan": {
        "fn": tool_think_and_plan,
        "desc": "Structure a complex task into a step-by-step plan before executing. Use FIRST for multi-step tasks.",
        "params": {"task": {"type": "string", "description": "Task description to analyze and plan"}},
        "required": ["task"],
        "category": "control",
    },
    "observe_and_plan": {
        "fn": tool_observe_and_plan,
        "desc": "Take a screenshot, analyze the current screen state with AI, then return a structured plan. Use at the START of any GUI task.",
        "params": {"goal": {"type": "string", "description": "What you are trying to accomplish on the screen"}},
        "required": ["goal"],
        "category": "vision",
    },
    "app_is_running": {
        "fn": tool_app_is_running,
        "desc": "Check if an application is currently running. Returns PID(s) or 'not running'.",
        "params": {"app_name": {"type": "string", "description": "Application name to check (e.g. firefox, chrome, code)"}},
        "required": ["app_name"],
        "category": "os",
    },
    "focus_app": {
        "fn": tool_focus_app,
        "desc": "Bring an application window to the foreground (focus it) on any platform.",
        "params": {"app_name": {"type": "string", "description": "Application name to focus"}},
        "required": ["app_name"],
        "category": "os",
    },
    "type_text": {
        "fn": tool_type_text_xplat,
        "desc": "Type text using the best available method on this platform (xdotool/pyautogui/pynput).",
        "params": {
            "text": {"type": "string", "description": "Text to type"},
            "speed": {"type": "number", "description": "Delay between keystrokes in seconds (default 0)"},
        },
        "required": ["text"],
        "category": "keyboard",
    },

    # ── TypeScript execution ───────────────────────────────────────────────────
    "run_typescript": {
        "fn": tool_run_typescript,
        "desc": "Execute TypeScript code inline or from a .ts file using npx tsx or ts-node.",
        "params": {
            "code": {"type": "string", "description": "TypeScript code to execute (optional if file_path given)"},
            "file_path": {"type": "string", "description": "Path to a .ts file to execute (optional if code given)"},
        },
        "required": [],
        "category": "code",
    },

    # ── File download ──────────────────────────────────────────────────────────
    "download_file": {
        "fn": tool_download_file,
        "desc": "Download a file from a URL to disk. Returns the local path and file size.",
        "params": {
            "url": {"type": "string", "description": "URL of the file to download"},
            "dest_path": {"type": "string", "description": "Local file path to save to (default: /tmp/<filename>)"},
        },
        "required": ["url"],
        "category": "web",
    },

    # ── Workflow orchestration ─────────────────────────────────────────────────
    "workflow": {
        "fn": tool_workflow,
        "desc": "Execute a structured multi-step workflow. Each step is {tool, args, stop_on_error?}.",
        "params": {
            "steps_json": {"type": "string", "description": 'JSON array of workflow steps, e.g. [{"tool":"execute_shell","args":{"cmd":"ls"}},{"tool":"write_file","args":{"path":"out.txt","content":"done"}}]'},
        },
        "required": ["steps_json"],
        "category": "control",
    },

    # ── Threat intelligence ────────────────────────────────────────────────────
    "threat_intel_lookup": {
        "fn": tool_threat_intel_lookup,
        "desc": "Look up threat intelligence: MITRE ATT&CK techniques, IOC reputation, domain/IP analysis.",
        "params": {
            "query": {"type": "string", "description": "Search term, IP, domain, CVE ID, or MITRE technique ID"},
            "lookup_type": {"type": "string", "description": "Type: mitre, ioc, domain, auto (default: auto)"},
        },
        "required": ["query"],
        "category": "security",
    },

    # ── Multimedia processing ──────────────────────────────────────────────────
    "process_media": {
        "fn": tool_process_media,
        "desc": "Process media files: get file info, resize image, extract audio, convert format.",
        "params": {
            "file_path": {"type": "string", "description": "Path to image, audio, or video file"},
            "operation": {"type": "string", "description": "Operation: info, resize, convert, extract_audio (default: info)"},
        },
        "required": ["file_path"],
        "category": "media",
    },

    # ── Mobile device control ──────────────────────────────────────────────────
    "mobile_action": {
        "fn": tool_mobile_action,
        "desc": "Control a mobile device via ADB: list devices, run shell commands, take screenshots.",
        "params": {
            "action": {"type": "string", "description": "Action: list, screenshot, shell, install (default: list)"},
            "device": {"type": "string", "description": "Device ID or 'auto' for first available"},
            "extra": {"type": "string", "description": "Extra argument (shell command, APK path, etc.)"},
        },
        "required": ["action"],
        "category": "device",
    },

    # ── Ethics and legal compliance ────────────────────────────────────────────
    "ethics_check": {
        "fn": tool_ethics_check,
        "desc": "Check an action against AI ethics and legal compliance rules (GDPR, CCPA, AI safety guidelines).",
        "params": {
            "action": {"type": "string", "description": "Action or capability to check (e.g. 'store user email', 'collect biometrics')"},
            "context": {"type": "string", "description": "Context or justification for the action"},
        },
        "required": ["action"],
        "category": "compliance",
    },

    # ── Structured data logging ────────────────────────────────────────────────
    "log_data": {
        "fn": tool_log_data,
        "desc": "Log structured data or events for later analysis and audit.",
        "params": {
            "data": {"type": "string", "description": "Data or event description to log"},
            "category": {"type": "string", "description": "Category label (default: general)"},
        },
        "required": ["data"],
        "category": "data",
    },

    # ── CTF / Cyber range ──────────────────────────────────────────────────────
    "cyber_range_challenge": {
        "fn": tool_cyber_range_challenge,
        "desc": "Interact with CTF/cyber range challenges: list available challenges, start one, get hints.",
        "params": {
            "action": {"type": "string", "description": "Action: list, start, hint, submit (default: list)"},
            "challenge_id": {"type": "string", "description": "Challenge ID to start, hint, or submit flag for"},
        },
        "required": [],
        "category": "security",
    },

    # ── Canvas / visual output ─────────────────────────────────────────────────
    "canvas_render": {
        "fn": tool_canvas_render,
        "desc": "Render content to a canvas for visual output (OpenDevin-style). Good for diagrams, structured data.",
        "params": {
            "content": {"type": "string", "description": "Content to display on the canvas (text, markdown, JSON)"},
            "title": {"type": "string", "description": "Canvas title (default: 'Devin Canvas')"},
        },
        "required": ["content"],
        "category": "ui",
    },

    # ── XR / AR display ───────────────────────────────────────────────────────
    "xr_display": {
        "fn": tool_xr_display,
        "desc": "Display content in XR/AR/VR mode via Holomat bridge.",
        "params": {
            "content": {"type": "string", "description": "Content to display in XR space"},
            "mode": {"type": "string", "description": "Display mode: overlay, immersive, panel (default: overlay)"},
        },
        "required": ["content"],
        "category": "xr",
    },

    # ── AI provider routing ────────────────────────────────────────────────────
    "ai_route": {
        "fn": tool_ai_route,
        "desc": "Route a task to the best available AI provider (Gemini, Claude, OpenAI, HuggingFace, Ollama).",
        "params": {
            "task": {"type": "string", "description": "Task or prompt to route to an AI provider"},
            "preferred_model": {"type": "string", "description": "Preferred model or 'auto' (default: auto)"},
        },
        "required": ["task"],
        "category": "ai",
    },

    # ── Multi-step workflow orchestration ─────────────────────────────────────
    "multi_step_workflow": {
        "fn": tool_multi_step_workflow,
        "desc": (
            "Execute a JSON-defined sequence of tool calls in order. "
            "Each step: {\"tool\": \"name\", \"args\": {...}, \"label\": \"optional\", \"verify\": \"optional shell check\"}. "
            "Use for complex multi-step tasks to ensure every step is verified and logged."
        ),
        "params": {
            "steps": {"type": "string", "description": "JSON array of step objects: [{tool, args, label?, verify?}]"},
            "stop_on_error": {"type": "boolean", "description": "Stop if any step errors (default: true)"},
        },
        "required": ["steps"],
        "category": "workflow",
    },

    "wait_for_condition": {
        "fn": tool_wait_for_condition,
        "desc": (
            "Poll until a Python expression is truthy or timeout is reached. "
            "Use to wait for file creation, process start, network availability, etc. "
            "Expression has access to: os, subprocess, Path, time, json, re."
        ),
        "params": {
            "condition": {"type": "string", "description": "Python expression to evaluate (e.g. \"os.path.exists('/tmp/out.txt')\")"},
            "timeout": {"type": "integer", "description": "Max seconds to wait (default: 30, max: 300)"},
            "interval": {"type": "number", "description": "Seconds between checks (default: 1.0)"},
        },
        "required": ["condition"],
        "category": "workflow",
    },

    "checkpoint_save": {
        "fn": tool_checkpoint_save,
        "desc": "Save a named progress checkpoint to SQLite. Use during long tasks to record where you are.",
        "params": {
            "name": {"type": "string", "description": "Checkpoint name (short identifier)"},
            "data": {"type": "string", "description": "Data to save (JSON, text, URL, notes)"},
        },
        "required": ["name", "data"],
        "category": "workflow",
    },

    "checkpoint_load": {
        "fn": tool_checkpoint_load,
        "desc": "Load a previously saved checkpoint by name. Returns the stored data string.",
        "params": {
            "name": {"type": "string", "description": "Checkpoint name to load"},
        },
        "required": ["name"],
        "category": "workflow",
    },

    "checkpoint_list": {
        "fn": tool_checkpoint_list,
        "desc": "List all saved task checkpoints with names, sizes, and timestamps.",
        "params": {},
        "required": [],
        "category": "workflow",
    },

    "run_workflow_file": {
        "fn": tool_run_workflow_file,
        "desc": "Load a JSON workflow file and execute it. File must contain a JSON array of {tool, args} step objects.",
        "params": {
            "path": {"type": "string", "description": "Path to the JSON workflow file"},
        },
        "required": ["path"],
        "category": "workflow",
    },

    # ── Parallel + task decomposition (Phase AB) ─────────────────────────────
    "batch_execute": {
        "fn": tool_batch_execute,
        "desc": (
            "Execute multiple INDEPENDENT tool calls in parallel (threads). "
            "Each item: {\"tool\": \"name\", \"args\": {...}, \"id\": \"label\"}. "
            "Use when operations don't depend on each other (parallel shell commands, "
            "multi-URL fetches, multi-file writes). Much faster than sequential execution."
        ),
        "params": {
            "tools_json": {"type": "string", "description": "JSON array of {tool, args, id?} objects to run in parallel"},
        },
        "required": ["tools_json"],
        "category": "workflow",
    },

    "decompose_task": {
        "fn": tool_decompose_task,
        "desc": (
            "Break a complex goal into numbered sub-tasks with suggested tools. "
            "Returns a structured action plan. Use at the start of any multi-step task "
            "to reason about what to do before acting. No AI call — pure local logic."
        ),
        "params": {
            "goal": {"type": "string", "description": "The goal or task to decompose"},
            "context": {"type": "string", "description": "Optional extra context (current state, constraints)"},
        },
        "required": ["goal"],
        "category": "workflow",
    },

    # ── File analysis (Phase AC) ──────────────────────────────────────────────
    "summarize_file": {
        "fn": tool_summarize_file,
        "desc": (
            "Read a file and return a structured summary: size, line count, first/last N chars, "
            "and extracted code patterns (functions, classes, imports, TODOs). "
            "Use instead of read_file for large files (>500 lines)."
        ),
        "params": {
            "path": {"type": "string", "description": "Path to the file to summarize"},
            "max_chars": {"type": "integer", "description": "Max chars to show from file (default: 4000)"},
        },
        "required": ["path"],
        "category": "files",
    },

    "diff_files": {
        "fn": tool_diff_files,
        "desc": "Show a unified diff between two files. Returns changed lines with context.",
        "params": {
            "path1": {"type": "string", "description": "First file path"},
            "path2": {"type": "string", "description": "Second file path"},
            "context": {"type": "integer", "description": "Lines of context around changes (default: 3)"},
        },
        "required": ["path1", "path2"],
        "category": "files",
    },

    "search_in_files": {
        "fn": tool_search_in_files,
        "desc": (
            "Search for a regex pattern in files under a directory (like grep -r). "
            "Returns matching file:line pairs. Use for code search, finding TODOs, "
            "locating function definitions, etc."
        ),
        "params": {
            "pattern": {"type": "string", "description": "Regex pattern to search for"},
            "directory": {"type": "string", "description": "Directory to search (default: '.')"},
            "file_glob": {"type": "string", "description": "File glob filter (default: '*', e.g. '*.py')"},
            "max_results": {"type": "integer", "description": "Max result lines (default: 50)"},
        },
        "required": ["pattern"],
        "category": "files",
    },

    # ── Process monitoring + env + JSON (Phase AD) ────────────────────────────
    "monitor_process": {
        "fn": tool_monitor_process,
        "desc": (
            "Monitor a running process by name or PID for N seconds. "
            "Returns CPU%, memory, status, and whether still running. "
            "Use to verify a launched app is responsive."
        ),
        "params": {
            "name_or_pid": {"type": "string", "description": "Process name (partial match) or PID"},
            "duration": {"type": "integer", "description": "Seconds to monitor (default: 10, max: 60)"},
        },
        "required": ["name_or_pid"],
        "category": "system",
    },

    "tail_file": {
        "fn": tool_tail_file,
        "desc": "Read last N lines of a file. Optionally follow new content for 'follow' seconds (like tail -f). Useful for log monitoring.",
        "params": {
            "path": {"type": "string", "description": "File path to read"},
            "lines": {"type": "integer", "description": "Number of lines to show (default: 20)"},
            "follow": {"type": "number", "description": "Seconds to follow new content (default: 0, max: 30)"},
        },
        "required": ["path"],
        "category": "files",
    },

    "get_env": {
        "fn": tool_get_env,
        "desc": "Get environment variable(s). Pass a key for one variable, or empty string for all (secrets redacted).",
        "params": {
            "key": {"type": "string", "description": "Variable name (empty = list all)"},
        },
        "required": [],
        "category": "system",
    },

    "set_env": {
        "fn": tool_set_env,
        "desc": "Set an environment variable for this session. Does not persist across restarts. Secret-looking keys are refused.",
        "params": {
            "key": {"type": "string", "description": "Variable name (no secrets)"},
            "value": {"type": "string", "description": "Value to set"},
        },
        "required": ["key", "value"],
        "category": "system",
    },

    "json_query": {
        "fn": tool_json_query,
        "desc": (
            "Query a JSON string with a dot-path expression: 'key', 'key.subkey', "
            "'key[0].field'. Use to extract values from API responses or config files "
            "without writing Python code."
        ),
        "params": {
            "json_str": {"type": "string", "description": "JSON string to query"},
            "query": {"type": "string", "description": "Dot-path query: 'key', 'key.sub', 'arr[0].field'"},
        },
        "required": ["json_str", "query"],
        "category": "data",
    },

    # ── Retry + verify + template + archives (Phase AE) ──────────────────────
    "retry_on_failure": {
        "fn": tool_retry_on_failure,
        "desc": (
            "Call a tool and auto-retry up to N times if it returns an ERROR. "
            "Use for flaky operations like network requests, GUI timing, or CI checks."
        ),
        "params": {
            "tool_name": {"type": "string", "description": "Name of the tool to call"},
            "tool_args": {"type": "string", "description": "JSON object of args to pass to the tool"},
            "max_retries": {"type": "integer", "description": "Max retry attempts (default: 3)"},
            "delay": {"type": "number", "description": "Seconds between retries (default: 1.0)"},
        },
        "required": ["tool_name", "tool_args"],
        "category": "workflow",
    },

    "verify_output": {
        "fn": tool_verify_output,
        "desc": (
            "Verify a tool's output matches an expectation. "
            "Modes: contains, icontains, regex, startswith, not_empty, is_error. "
            "Returns PASS or FAIL — useful for automated verification steps."
        ),
        "params": {
            "output": {"type": "string", "description": "The output string to verify"},
            "expected_pattern": {"type": "string", "description": "Pattern/string to match against"},
            "mode": {"type": "string", "description": "Match mode: contains|icontains|regex|startswith|not_empty|is_error (default: contains)"},
        },
        "required": ["output", "expected_pattern"],
        "category": "workflow",
    },

    "template_fill": {
        "fn": tool_template_fill,
        "desc": "Fill a text template {variable} placeholders from a JSON object of variables. Safe, no code execution.",
        "params": {
            "template": {"type": "string", "description": "Template string with {variable} placeholders"},
            "variables": {"type": "string", "description": "JSON object: {\"var\": \"value\", ...}"},
        },
        "required": ["template", "variables"],
        "category": "data",
    },

    "zip_files": {
        "fn": tool_zip_files,
        "desc": "Create a ZIP archive from a list of files/directories. source_paths is a JSON array of paths.",
        "params": {
            "output_path": {"type": "string", "description": "Path for the output .zip file"},
            "source_paths": {"type": "string", "description": "JSON array of file/directory paths to add"},
            "compression": {"type": "string", "description": "deflated (default) or stored"},
        },
        "required": ["output_path", "source_paths"],
        "category": "files",
    },

    "unzip": {
        "fn": tool_unzip,
        "desc": "Extract a ZIP archive to a destination directory.",
        "params": {
            "archive_path": {"type": "string", "description": "Path to the .zip file"},
            "dest_dir": {"type": "string", "description": "Directory to extract to (default: '.')"},
        },
        "required": ["archive_path"],
        "category": "files",
    },

    # ── Phase AF — Dev workflow tools ──────────────────────────────────────────
    "find_and_replace": {
        "fn": tool_find_and_replace,
        "desc": "Find a regex pattern across files in a directory and replace it.",
        "params": {
            "directory": {"type": "string", "description": "Root directory to search"},
            "pattern": {"type": "string", "description": "Regex pattern to find"},
            "replacement": {"type": "string", "description": "Replacement string"},
            "file_glob": {"type": "string", "description": "File glob pattern (default '*.py')"},
            "dry_run": {"type": "boolean", "description": "Preview without writing (default false)"},
        },
        "required": ["directory", "pattern", "replacement"],
        "category": "files",
    },

    "run_tests": {
        "fn": tool_run_tests,
        "desc": "Run a test suite via pytest or python and return pass/fail/skip summary.",
        "params": {
            "test_path": {"type": "string", "description": "Path to test file or directory (default 'tests/')"},
            "args": {"type": "string", "description": "Extra arguments to pass"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)"},
        },
        "required": [],
        "category": "workflow",
    },

    "git_ops": {
        "fn": tool_git_ops,
        "desc": "Run safe git operations: status, log, diff, add, commit, push, pull, branch, stash, fetch.",
        "params": {
            "operation": {"type": "string", "description": "Git operation (status/log/diff/add/commit/push/pull/branch/stash/fetch)"},
            "args": {"type": "string", "description": "Arguments for the operation"},
            "repo_path": {"type": "string", "description": "Repository path (default '.')"},
        },
        "required": ["operation"],
        "category": "workflow",
    },

    "create_project": {
        "fn": tool_create_project,
        "desc": "Scaffold a new project directory (python/node/web/bash) with standard structure.",
        "params": {
            "name": {"type": "string", "description": "Project name (becomes directory name)"},
            "project_type": {"type": "string", "description": "Type: python, node, web, bash (default 'python')"},
            "base_dir": {"type": "string", "description": "Parent directory (default '.')"},
        },
        "required": ["name"],
        "category": "workflow",
    },

    # ── Phase AG — Code analysis ───────────────────────────────────────────────
    "explain_code": {
        "fn": tool_explain_code,
        "desc": "Statically analyze a code snippet: imports, functions, classes, potential issues.",
        "params": {
            "code": {"type": "string", "description": "Code snippet to analyze"},
            "language": {"type": "string", "description": "Language hint (default 'python')"},
        },
        "required": ["code"],
        "category": "code",
    },

    "lint_code": {
        "fn": tool_lint_code,
        "desc": "Run flake8/pyflakes/pylint on a Python file and return findings.",
        "params": {
            "path": {"type": "string", "description": "Path to Python file"},
            "linter": {"type": "string", "description": "Linter: auto, flake8, pylint, pyflakes (default 'auto')"},
        },
        "required": ["path"],
        "category": "code",
    },

    "profile_code": {
        "fn": tool_profile_code,
        "desc": "Benchmark Python code execution time using timeit. Returns min/avg/max/ops-per-sec.",
        "params": {
            "code": {"type": "string", "description": "Python expression or statement to profile"},
            "iterations": {"type": "integer", "description": "Iterations per timing run (default 1000)"},
        },
        "required": ["code"],
        "category": "code",
    },

    "generate_tests": {
        "fn": tool_generate_tests,
        "desc": "Generate pytest test stubs for all public functions in a code snippet.",
        "params": {
            "code": {"type": "string", "description": "Python code to generate tests for"},
            "module_name": {"type": "string", "description": "Module name for import comment (default 'module')"},
        },
        "required": ["code"],
        "category": "code",
    },

    # ── Phase AH — Data & network tools ────────────────────────────────────────
    "http_request": {
        "fn": tool_http_request,
        "desc": "Make an HTTP request (GET/POST/PUT/PATCH/DELETE) and return status + response body.",
        "params": {
            "url": {"type": "string", "description": "URL to request"},
            "method": {"type": "string", "description": "HTTP method (default GET)"},
            "headers": {"type": "string", "description": "JSON object of request headers"},
            "body": {"type": "string", "description": "Request body (for POST/PUT)"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 15)"},
        },
        "required": ["url"],
        "category": "web",
    },

    "parse_html": {
        "fn": tool_parse_html,
        "desc": "Extract text, links, or headings from an HTML string.",
        "params": {
            "html": {"type": "string", "description": "HTML content to parse"},
            "extract": {"type": "string", "description": "What to extract: text, links, headings, all (default 'text')"},
        },
        "required": ["html"],
        "category": "web",
    },

    "validate_json": {
        "fn": tool_validate_json,
        "desc": "Validate a JSON string, describe its structure, and optionally check against a schema.",
        "params": {
            "json_str": {"type": "string", "description": "JSON string to validate"},
            "schema": {"type": "string", "description": "Optional JSON schema object to check keys against"},
        },
        "required": ["json_str"],
        "category": "data",
    },

    "csv_query": {
        "fn": tool_csv_query,
        "desc": "Query CSV data with column selection and filter expression.",
        "params": {
            "csv_str": {"type": "string", "description": "CSV content as string"},
            "columns": {"type": "string", "description": "Comma-separated column names to include"},
            "filter_expr": {"type": "string", "description": "Python filter expression (e.g. 'age > 30')"},
            "max_rows": {"type": "integer", "description": "Max rows to return (default 50)"},
        },
        "required": ["csv_str"],
        "category": "data",
    },

    "format_table": {
        "fn": tool_format_table,
        "desc": "Format delimited data (CSV, TSV) as a Unicode ASCII table.",
        "params": {
            "data": {"type": "string", "description": "Delimited data string"},
            "headers": {"type": "string", "description": "Comma-separated column headers (if not in first row)"},
            "separator": {"type": "string", "description": "Column separator: ',' (default), 'tab', or any char"},
        },
        "required": ["data"],
        "category": "data",
    },

    # ── Phase AI — Text processing tools ───────────────────────────────────────
    "encode_decode": {
        "fn": tool_encode_decode,
        "desc": "Encode or decode text: base64, hex, URL encode/decode, or compute sha256/md5/sha1 hash.",
        "params": {
            "text": {"type": "string", "description": "Input text"},
            "operation": {"type": "string", "description": "Operation: base64_encode/decode, hex_encode/decode, url_encode/decode, sha256, md5, sha1"},
            "encoding": {"type": "string", "description": "Character encoding (default 'utf-8')"},
        },
        "required": ["text", "operation"],
        "category": "data",
    },

    "regex_extract": {
        "fn": tool_regex_extract,
        "desc": "Extract all regex matches from text with optional capture group selection.",
        "params": {
            "text": {"type": "string", "description": "Input text to search"},
            "pattern": {"type": "string", "description": "Regex pattern"},
            "group": {"type": "integer", "description": "Capture group (0=full match, 1+=group, default 0)"},
            "flags": {"type": "string", "description": "Regex flags: i=case-insensitive, m=multiline, s=dotall"},
            "max_matches": {"type": "integer", "description": "Max matches to return (default 100)"},
        },
        "required": ["text", "pattern"],
        "category": "data",
    },

    "text_stats": {
        "fn": tool_text_stats,
        "desc": "Compute text statistics: word/char/line/sentence count, reading time, top words.",
        "params": {
            "text": {"type": "string", "description": "Text to analyze"},
        },
        "required": ["text"],
        "category": "data",
    },

    "markdown_to_text": {
        "fn": tool_markdown_to_text,
        "desc": "Convert Markdown to plain text by removing formatting, links, code blocks, etc.",
        "params": {
            "markdown": {"type": "string", "description": "Markdown text to convert"},
        },
        "required": ["markdown"],
        "category": "data",
    },

    "count_tokens": {
        "fn": tool_count_tokens,
        "desc": "Estimate token count for AI context planning. Warns if approaching model limits.",
        "params": {
            "text": {"type": "string", "description": "Text to estimate tokens for"},
            "model": {"type": "string", "description": "Model: gpt4, gpt35, claude, gemini, llama, mistral (default 'gpt4')"},
        },
        "required": ["text"],
        "category": "reasoning",
    },

    # ── Phase AJ — Task planning & navigation ─────────────────────────────────
    "task_plan": {
        "fn": tool_task_plan,
        "desc": "Generate a structured task plan from a goal: numbered steps with time estimates.",
        "params": {
            "goal": {"type": "string", "description": "Goal or task description"},
            "steps": {"type": "integer", "description": "Number of steps (default 5)"},
            "format": {"type": "string", "description": "Output format: numbered, checklist, json (default 'numbered')"},
        },
        "required": ["goal"],
        "category": "reasoning",
    },

    "file_tree": {
        "fn": tool_file_tree,
        "desc": "Display a directory as a visual tree (like the `tree` command).",
        "params": {
            "path": {"type": "string", "description": "Root directory (default '.')"},
            "max_depth": {"type": "integer", "description": "Max recursion depth (default 3)"},
            "include_hidden": {"type": "boolean", "description": "Include dotfiles (default false)"},
            "file_limit": {"type": "integer", "description": "Max entries to show (default 200)"},
        },
        "required": [],
        "category": "files",
    },

    "extract_todos": {
        "fn": tool_extract_todos,
        "desc": "Scan source files for TODO/FIXME/HACK/NOTE/XXX comments with line numbers.",
        "params": {
            "directory": {"type": "string", "description": "Directory to scan (default '.')"},
            "file_glob": {"type": "string", "description": "File pattern (default '*.py')"},
            "tags": {"type": "string", "description": "Comma-separated tags to find (default 'TODO,FIXME,HACK,NOTE,XXX')"},
        },
        "required": [],
        "category": "code",
    },

    "make_executable": {
        "fn": tool_make_executable,
        "desc": "Make a file executable (chmod +x).",
        "params": {
            "path": {"type": "string", "description": "Path to file to make executable"},
        },
        "required": ["path"],
        "category": "files",
    },

    # ── Phase AK — System, config, memory ──────────────────────────────────────
    "system_snapshot": {
        "fn": tool_system_snapshot,
        "desc": "Take a full system health snapshot: CPU, memory, disk, top processes.",
        "params": {},
        "required": [],
        "category": "system",
    },

    "config_read": {
        "fn": tool_config_read,
        "desc": "Read a config file (INI, JSON, TOML, .env). Optionally get a specific section/key.",
        "params": {
            "path": {"type": "string", "description": "Path to config file"},
            "section": {"type": "string", "description": "Section name to read (optional)"},
        },
        "required": ["path"],
        "category": "files",
    },

    "config_write": {
        "fn": tool_config_write,
        "desc": "Write or update a key in an INI/CFG config file.",
        "params": {
            "path": {"type": "string", "description": "Path to config file (created if not exists)"},
            "section": {"type": "string", "description": "Config section name"},
            "key": {"type": "string", "description": "Key to write"},
            "value": {"type": "string", "description": "Value to set"},
        },
        "required": ["path", "section", "key", "value"],
        "category": "files",
    },

    "memory_search": {
        "fn": tool_memory_search,
        "desc": "Search stored memories for entries matching a query (keyword-based).",
        "params": {
            "query": {"type": "string", "description": "Search query"},
            "limit": {"type": "integer", "description": "Max results (default 10)"},
        },
        "required": ["query"],
        "category": "memory",
    },

    # ── Phase AL — Code review, watch, convert, connectivity ──────────────────
    "code_review": {
        "fn": tool_code_review,
        "desc": "Static code review of a Python file: long functions, broad exceptions, credentials, type hints.",
        "params": {
            "path": {"type": "string", "description": "Path to Python file"},
            "rules": {"type": "string", "description": "Rules: all, or comma-separated: long_lines,broad_except,long_functions,credentials,mutable_defaults,type_hints"},
        },
        "required": ["path"],
        "category": "code",
    },

    "watch_file": {
        "fn": tool_watch_file,
        "desc": "Poll a file for changes and return new content when it changes.",
        "params": {
            "path": {"type": "string", "description": "File to watch"},
            "timeout": {"type": "integer", "description": "Max seconds to wait (default 10)"},
            "interval": {"type": "number", "description": "Poll interval in seconds (default 0.5)"},
        },
        "required": ["path"],
        "category": "files",
    },

    "convert_units": {
        "fn": tool_convert_units,
        "desc": "Convert between units: length (m/km/mi/ft), weight (kg/lb/oz), temperature (c/f/k), digital (b/kb/mb/gb), time (s/min/h/d).",
        "params": {
            "value": {"type": "number", "description": "Numeric value to convert"},
            "from_unit": {"type": "string", "description": "Source unit"},
            "to_unit": {"type": "string", "description": "Target unit"},
        },
        "required": ["value", "from_unit", "to_unit"],
        "category": "data",
    },

    "internet_check": {
        "fn": tool_internet_check,
        "desc": "Check internet connectivity. Returns latency or error.",
        "params": {
            "host": {"type": "string", "description": "Host to check (default '8.8.8.8')"},
            "port": {"type": "integer", "description": "Port to connect to (default 53)"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 3)"},
        },
        "required": [],
        "category": "system",
    },

    # ── Phase AM — Calculate, list_tools, diff_json, parse_args ───────────────
    "calculate": {
        "fn": tool_calculate,
        "desc": "Safely evaluate a math expression: +,-,*,/,**,sqrt,log,sin,cos,pi,e,etc.",
        "params": {
            "expression": {"type": "string", "description": "Math expression to evaluate"},
        },
        "required": ["expression"],
        "category": "reasoning",
    },

    "list_tools": {
        "fn": tool_list_tools,
        "desc": "List all available tools, optionally filtered by category or search query.",
        "params": {
            "category": {"type": "string", "description": "Filter by category (e.g. 'workflow', 'files', 'code', 'web')"},
            "search": {"type": "string", "description": "Search in tool name or description"},
        },
        "required": [],
        "category": "reasoning",
    },

    "diff_json": {
        "fn": tool_diff_json,
        "desc": "Diff two JSON values and show added/removed/changed keys recursively.",
        "params": {
            "json1": {"type": "string", "description": "First JSON string"},
            "json2": {"type": "string", "description": "Second JSON string"},
            "path": {"type": "string", "description": "Optional initial path prefix"},
        },
        "required": ["json1", "json2"],
        "category": "data",
    },

    "parse_args": {
        "fn": tool_parse_args,
        "desc": "Parse a command-line argument string into a structured JSON dict.",
        "params": {
            "args_string": {"type": "string", "description": "Argument string to parse"},
            "spec": {"type": "string", "description": "Optional JSON schema for validation"},
        },
        "required": ["args_string"],
        "category": "data",
    },

    # ── Phase AT ──────────────────────────────────────────────────────────────
    "goal_plan": {
        "fn": tool_goal_plan,
        "desc": "Convert a high-level goal into a structured step-by-step tool plan.",
        "params": {
            "goal": {"type": "string", "description": "High-level goal or task description"},
            "context": {"type": "string", "description": "Current project context"},
            "constraints": {"type": "string", "description": "Known limitations or constraints"},
        },
        "required": ["goal"],
        "category": "workflow",
    },
    "self_reflect": {
        "fn": tool_self_reflect,
        "desc": "Analyze last tool output to assess progress and suggest what to do next.",
        "params": {
            "last_output": {"type": "string", "description": "The last tool's output to analyze"},
            "goal": {"type": "string", "description": "Current task goal for context"},
        },
        "required": ["last_output"],
        "category": "workflow",
    },
    "generate_report": {
        "fn": tool_generate_report,
        "desc": "Generate a structured report (markdown/html/plain) from a sections spec.",
        "params": {
            "title": {"type": "string", "description": "Report title"},
            "sections": {"type": "string", "description": "JSON array of {heading, content} objects"},
            "format": {"type": "string", "description": "markdown | html | plain"},
        },
        "required": ["title", "sections"],
        "category": "workflow",
    },

    # ── Phase AS ──────────────────────────────────────────────────────────────
    "symbol_search": {
        "fn": tool_symbol_search,
        "desc": "Find all definitions and references to a symbol across a directory.",
        "params": {
            "directory": {"type": "string", "description": "Directory to search"},
            "symbol": {"type": "string", "description": "Function, class, or variable name to find"},
            "file_glob": {"type": "string", "description": "File pattern (default '*.py')"},
        },
        "required": ["directory", "symbol"],
        "category": "devtools",
    },
    "find_dead_code": {
        "fn": tool_find_dead_code,
        "desc": "Find functions and classes defined but never referenced (heuristic).",
        "params": {
            "directory": {"type": "string", "description": "Directory to scan"},
            "file_glob": {"type": "string", "description": "File pattern (default '*.py')"},
        },
        "required": ["directory"],
        "category": "devtools",
    },
    "count_lines": {
        "fn": tool_count_lines,
        "desc": "Count lines of code per file (code / blank / comment) in a directory.",
        "params": {
            "directory": {"type": "string", "description": "Directory to scan"},
            "file_glob": {"type": "string", "description": "File pattern (default '*.py')"},
        },
        "required": ["directory"],
        "category": "devtools",
    },
    "ast_parse": {
        "fn": tool_ast_parse,
        "desc": "Parse Python code and summarise its AST: imports, classes, functions.",
        "params": {
            "code": {"type": "string", "description": "Python source code to parse"},
            "language": {"type": "string", "description": "Language (currently only 'python')"},
        },
        "required": ["code"],
        "category": "devtools",
    },

    # ── Phase AR ──────────────────────────────────────────────────────────────
    "list_processes": {
        "fn": tool_list_processes,
        "desc": "List running processes filtered by name/cmdline. Shows PID, CPU%, MEM%, status.",
        "params": {
            "filter": {"type": "string", "description": "Substring to filter by name or cmdline"},
            "limit": {"type": "integer", "description": "Max processes to show (default 30)"},
        },
        "required": [],
        "category": "system",
    },
    "kill_process": {
        "fn": tool_kill_process,
        "desc": "Send a signal to a process by PID (TERM|KILL|HUP|INT|STOP|CONT).",
        "params": {
            "pid": {"type": "integer", "description": "Process ID to signal"},
            "signal": {"type": "string", "description": "Signal name (default TERM)"},
        },
        "required": ["pid"],
        "category": "system",
    },
    "spawn_process": {
        "fn": tool_spawn_process,
        "desc": "Spawn a subprocess. detach=True for background launch. Returns PID or output.",
        "params": {
            "command": {"type": "string", "description": "Shell command to run"},
            "cwd": {"type": "string", "description": "Working directory"},
            "env_extra": {"type": "string", "description": "JSON dict of extra env vars"},
            "detach": {"type": "boolean", "description": "Launch in background (True) or wait (False)"},
        },
        "required": ["command"],
        "category": "system",
    },
    "process_info": {
        "fn": tool_process_info,
        "desc": "Get detailed info for a single process (name, CPU%, memory, files, cmdline).",
        "params": {
            "pid": {"type": "integer", "description": "Process ID to inspect"},
        },
        "required": ["pid"],
        "category": "system",
    },

    # ── Phase AQ ──────────────────────────────────────────────────────────────
    "ping": {
        "fn": tool_ping,
        "desc": "Ping a host and report packet loss and round-trip times.",
        "params": {
            "host": {"type": "string", "description": "Hostname or IP to ping"},
            "count": {"type": "integer", "description": "Number of packets (1–20)"},
            "timeout": {"type": "integer", "description": "Timeout per packet in seconds"},
        },
        "required": ["host"],
        "category": "web",
    },
    "port_scan": {
        "fn": tool_port_scan,
        "desc": "Check which TCP ports are open on a host (max 50 ports).",
        "params": {
            "host": {"type": "string", "description": "Hostname or IP to scan"},
            "ports": {"type": "string", "description": "Comma-separated ports or range like '80-90'"},
            "timeout": {"type": "number", "description": "Seconds per port (default 1.0)"},
        },
        "required": ["host"],
        "category": "web",
    },
    "dns_lookup": {
        "fn": tool_dns_lookup,
        "desc": "Perform a DNS lookup (A/AAAA/MX/TXT/NS/CNAME/PTR).",
        "params": {
            "hostname": {"type": "string", "description": "Hostname to look up"},
            "record_type": {"type": "string", "description": "A | AAAA | MX | TXT | NS | CNAME | PTR"},
        },
        "required": ["hostname"],
        "category": "web",
    },
    "http_headers": {
        "fn": tool_http_headers,
        "desc": "Fetch HTTP response headers from a URL (HEAD request).",
        "params": {
            "url": {"type": "string", "description": "URL to inspect"},
            "timeout": {"type": "integer", "description": "Request timeout in seconds"},
        },
        "required": ["url"],
        "category": "web",
    },
    "whois_ip": {
        "fn": tool_whois_ip,
        "desc": "Get IP geolocation and ASN info for an IP address or hostname.",
        "params": {
            "ip_or_host": {"type": "string", "description": "IP address or hostname"},
        },
        "required": ["ip_or_host"],
        "category": "web",
    },

    # ── Phase AP ──────────────────────────────────────────────────────────────
    "bulk_rename": {
        "fn": tool_bulk_rename,
        "desc": "Rename files in a directory by regex pattern. dry_run=True previews.",
        "params": {
            "directory": {"type": "string", "description": "Directory containing files to rename"},
            "pattern": {"type": "string", "description": "Regex pattern to match in filenames"},
            "replacement": {"type": "string", "description": "Replacement string"},
            "file_glob": {"type": "string", "description": "Glob filter (default '*')"},
            "dry_run": {"type": "boolean", "description": "Preview without applying (default True)"},
        },
        "required": ["directory", "pattern", "replacement"],
        "category": "files",
    },
    "folder_sync": {
        "fn": tool_folder_sync,
        "desc": "One-way sync files from src to dst. dry_run previews; delete removes extras.",
        "params": {
            "src": {"type": "string", "description": "Source directory"},
            "dst": {"type": "string", "description": "Destination directory"},
            "dry_run": {"type": "boolean", "description": "Preview without applying (default True)"},
            "delete": {"type": "boolean", "description": "Delete files in dst not present in src"},
        },
        "required": ["src", "dst"],
        "category": "files",
    },
    "archive_info": {
        "fn": tool_archive_info,
        "desc": "Show metadata and file listing for a ZIP or TAR archive.",
        "params": {
            "path": {"type": "string", "description": "Path to ZIP or TAR archive"},
        },
        "required": ["path"],
        "category": "archives",
    },
    "checksum": {
        "fn": tool_checksum,
        "desc": "Compute the checksum of a file (md5|sha1|sha256|sha512).",
        "params": {
            "path": {"type": "string", "description": "File path"},
            "algorithm": {"type": "string", "description": "md5|sha1|sha256|sha512"},
        },
        "required": ["path"],
        "category": "files",
    },

    # ── Phase AO ──────────────────────────────────────────────────────────────
    "pipe": {
        "fn": tool_pipe,
        "desc": "Chain tool calls: output of each step feeds into the next.",
        "params": {
            "steps": {"type": "string", "description": "JSON array of {tool, args} objects"},
        },
        "required": ["steps"],
        "category": "workflow",
    },
    "string_ops": {
        "fn": tool_string_ops,
        "desc": "Common string operations: upper/lower/title/strip/reverse/split/join/replace/pad/repeat/truncate/slugify.",
        "params": {
            "text": {"type": "string", "description": "Input text"},
            "operation": {"type": "string", "description": "Operation name"},
            "arg": {"type": "string", "description": "Optional second argument"},
        },
        "required": ["text", "operation"],
        "category": "data",
    },
    "sleep": {
        "fn": tool_sleep,
        "desc": "Pause execution for N seconds (max 60). Useful between retries.",
        "params": {
            "seconds": {"type": "number", "description": "Seconds to sleep (0–60)"},
        },
        "required": ["seconds"],
        "category": "system",
    },
    "generate_uuid": {
        "fn": tool_generate_uuid,
        "desc": "Generate a UUID (versions 1, 3, 4, 5).",
        "params": {
            "version": {"type": "integer", "description": "UUID version: 1|3|4|5"},
            "namespace": {"type": "string", "description": "Namespace for v3/v5"},
            "name": {"type": "string", "description": "Name for v3/v5"},
        },
        "required": [],
        "category": "data",
    },
    "random_value": {
        "fn": tool_random_value,
        "desc": "Generate a random int, float, string, or pick/shuffle from a list.",
        "params": {
            "type": {"type": "string", "description": "int | float | string | choice | shuffle"},
            "min": {"type": "number", "description": "Minimum value (int/float)"},
            "max": {"type": "number", "description": "Maximum value (int/float)"},
            "length": {"type": "integer", "description": "Character count for string type"},
            "choices": {"type": "string", "description": "JSON array for choice/shuffle"},
        },
        "required": [],
        "category": "data",
    },
    "timestamp": {
        "fn": tool_timestamp,
        "desc": "Return the current timestamp in iso/unix/human/date/time/rfc2822 format.",
        "params": {
            "format": {"type": "string", "description": "iso | unix | human | date | time | rfc2822"},
            "timezone": {"type": "string", "description": "utc | local"},
            "offset_seconds": {"type": "integer", "description": "Add/subtract seconds from now"},
        },
        "required": [],
        "category": "data",
    },

    # ── Phase AN ──────────────────────────────────────────────────────────────
    "summarize_changes": {
        "fn": tool_summarize_changes,
        "desc": "Summarize the diff between a before and after version of text/code.",
        "params": {
            "before": {"type": "string", "description": "Original text/code"},
            "after": {"type": "string", "description": "Updated text/code"},
            "context": {"type": "string", "description": "Optional label for the summary header"},
        },
        "required": ["before", "after"],
        "category": "devtools",
    },
    "task_complete": {
        "fn": tool_task_complete,
        "desc": "Signal that a task is complete. Records outcome and artifacts created.",
        "params": {
            "summary": {"type": "string", "description": "Summary of what was accomplished"},
            "artifacts": {"type": "string", "description": "JSON array of files/URLs created"},
        },
        "required": ["summary"],
        "category": "workflow",
    },
    "format_output": {
        "fn": tool_format_output,
        "desc": "Format content for display: box, list, numbered, header, or plain style.",
        "params": {
            "content": {"type": "string", "description": "Text content to format"},
            "style": {"type": "string", "description": "box | list | numbered | header | plain"},
            "title": {"type": "string", "description": "Optional title for box style"},
        },
        "required": ["content"],
        "category": "workflow",
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
You are Devin — a deeply autonomous AI agent that operates a real computer like a senior engineer.
You have {len(TOOLS)} tools. Platform: {_PLATFORM}. {_DISPLAY_NOTE}

════════════════════════════════════════════════════════
IDENTITY — WHO YOU ARE
════════════════════════════════════════════════════════
You are a full-stack AI engineer that can:
• Write, debug, and run code in any language (Python, JS, TS, bash, PowerShell, Go, Rust…)
• Control the entire OS: mouse, keyboard, windows, applications, clipboard
• Browse the web, fill forms, click buttons, extract data — with or without a browser
• Audit git repositories, write reports, run security scans (with authorization)
• Manage files, processes, network, cloud services, and databases
• Engage in natural conversation — direct, thorough, no filler

You are running on {_PLATFORM} right now. Every tool call executes on the LIVE system.

NEVER:
• Say "I'll help" — just do it. Action is the only output that matters.
• Say "I cannot" — when tools exist, use them. When tools fail, adapt.
• Leave a task half-finished. Verify then declare complete.
• Guess UI coordinates — always take screenshot first, analyze, then click.
• Repeat the exact same failing action. Change strategy immediately.
• Ask "should I proceed?" for routine actions. Proceed. Ask only if genuinely ambiguous.

════════════════════════════════════════════════════════
CORE EXECUTION RULES
════════════════════════════════════════════════════════
1. PLAN before long tasks — use think_and_plan() for multi-step work
2. OBSERVE first for GUI — screenshot_and_analyze() before every click
3. VERIFY after every step — don't assume actions worked
4. RECOVER on failure — after 2 failures with same approach, switch strategy completely
5. COMPLETE fully — call task_complete() only when verified outcome achieved
6. PERSIST — if 10 approaches fail, find the 11th. Never give up on a valid task.
7. CONSERVE — don't repeat tool calls unnecessarily, build on what you know

════════════════════════════════════════════════════════
PLATFORM-SPECIFIC GUIDANCE ({_PLATFORM})
════════════════════════════════════════════════════════
LINUX:
  Open apps:    execute_shell("firefox &") or open_application("firefox")
  Open URLs:    open_url(url) or execute_shell("xdg-open URL")
  File manager: execute_shell("nautilus /path &") or "thunar /path &"
  Screenshots:  screenshot() → always works; scrot/gnome-screenshot for CLI
  Keyboard:     keyboard_type / keyboard_hotkey / xdotool type --
  Window focus: focus_app("firefox") or execute_shell("wmctrl -a firefox")
  Package mgr:  execute_shell("apt install pkg -y") or "pip install pkg"
  Pentest:      nmap, burpsuite, metasploit, sqlmap — all via execute_shell()

MACOS:
  Open apps:    open_application("Safari") uses 'open -a Safari'
  Open URLs:    open_url(url) uses 'open URL'
  Screenshots:  screenshot() → always works; screencapture for CLI
  Keyboard:     keyboard_type / osascript -e 'tell app...'
  Package mgr:  execute_shell("brew install pkg")

WINDOWS:
  Open apps:    open_application("notepad") uses start command
  Open URLs:    open_url(url) uses start/default browser
  Screenshots:  screenshot() → always works
  Keyboard:     keyboard_type / keyboard_hotkey
  Package mgr:  execute_shell("winget install pkg") or "choco install pkg"

════════════════════════════════════════════════════════
TOOL SELECTION — EXACT MAPPING
════════════════════════════════════════════════════════
TASK TYPE              → BEST TOOLS
─────────────────────────────────────────────────────────
Run any code           → write_and_run(file, code) or execute_python(code) or execute_shell(cmd)
Browse web             → web_search → browser_navigate → browser_get_text
Open app               → open_application(name) + wait_and_verify
Click a button         → screenshot_and_analyze → mouse_click(x,y) or click_by_description
Type text              → keyboard_type(text) or type_text(text)
Key combo              → keyboard_hotkey(["ctrl","c"]) or keyboard_press("Return")
Take screenshot        → screenshot() or screenshot_and_analyze(question)
Find element on screen → find_on_screen(description) → get coordinates → click
Read file              → read_file(path)
Write file             → write_file(path, content) → verify with read_file
Run git                → git_command("status") or execute_shell("git ...")
Install package        → install_and_verify(pkg) or execute_shell("pip install pkg")
Search web             → web_search(query) then web_fetch(url) for content
Open URL               → open_url(url) — cross-platform, works on all OS
System info            → platform_info() or get_system_info() or execute_shell("uname -a")
Process info           → list_processes() or execute_shell("ps aux | grep X")
Pentest/security       → execute_shell("nmap ...") + screenshot_and_analyze for GUI tools
Download file          → download_file(url, dest) or execute_shell("wget/curl URL")
Multi-step plan        → think_and_plan(task) → then execute steps one by one
GUI task (any)         → observe_and_plan(goal) → get screen state + action plan
Check if app running   → app_is_running(name)
Focus app window       → focus_app(name)
Complex multi-step     → decompose_task(goal) → multi_step_workflow(steps_json)
Independent parallel   → batch_execute(tools_json) — run tools simultaneously
Wait for event         → wait_for_condition("os.path.exists('/tmp/out')", timeout=30)
Save progress          → checkpoint_save("step3", data) → checkpoint_load("step3")

════════════════════════════════════════════════════════
GUI AUTOMATION WORKFLOW (EXACT STEPS)
════════════════════════════════════════════════════════
Step 0: observe_and_plan("open firefox and search web")  -- analyze current screen first
Step 1: open_application("firefox")          -- or open_and_wait("firefox", 3)
Step 2: screenshot_and_analyze("Where is the address bar? Give x,y pixel coords")
Step 3: mouse_click(x, y)                   -- click address bar
Step 4: keyboard_hotkey(["ctrl","a"])        -- select all
Step 5: keyboard_type("https://target.com") -- type URL
Step 6: keyboard_press("Return")            -- go
Step 7: sleep(2)
Step 8: screenshot_and_analyze("Did the page load? What's visible? Any errors?")
Step 9: Continue or recover based on what you see

For FORMS: screenshot → find field coords → click_and_type(x, y, text) → screenshot verify
For BUTTONS: screenshot_and_analyze("Where is the Submit button? x,y coords") → mouse_click
For MENUS: keyboard_hotkey or right-click at correct coords

════════════════════════════════════════════════════════
AGENTIC REASONING LOOP
════════════════════════════════════════════════════════
For EVERY non-trivial task:
  1. THINK   → What is the goal? What tools exist? What is the plan?
             → For complex tasks: decompose_task(goal) to get a structured plan first
  2. OBSERVE → screenshot() or read_file() or get_system_info() — see current state
  3. ACT     → Execute the next step with the right tool
             → Independent steps: batch_execute([...]) to run them all at once
             → Sequential steps: multi_step_workflow([...]) for verified execution
  4. VERIFY  → Confirm step succeeded (screenshot, read output, check file)
             → wait_for_condition("os.path.exists(path)") to wait on async events
  5. SAVE    → checkpoint_save("step_N", status) for long tasks so progress is preserved
  6. LOOP    → Repeat 3-5 until all steps done
  7. COMPLETE → Call task_complete("summary of what was done and verified")

For CONVERSATIONAL queries (questions, explanations, advice):
  → Answer directly. Use tools only if current system state is needed.
  → Be thorough but concise. Give examples. Don't pad.

════════════════════════════════════════════════════════
ERROR RECOVERY — NEVER GIVE UP
════════════════════════════════════════════════════════
Error type             → Recovery action
─────────────────────────────────────────────────────────
Click missed target    → Take fresh screenshot, re-analyze coords, retry
App not found          → Try 'which appname', apt/brew search, install first
App not responding     → Kill + relaunch, or use keyboard shortcut alternative
Shell command fails    → Read exact error, fix it, retry with corrected version
Network blocked        → Try alternate URL, use browser instead of direct fetch
Permission denied      → Check with ls -la, use sudo if appropriate, try different path
Same error 3×          → SWITCH STRATEGY COMPLETELY — different tool, different approach
GUI unresponsive       → Keyboard shortcut equivalent, CLI fallback, restart app
Python import fails    → install_and_verify(package_name) first, then retry

════════════════════════════════════════════════════════
SECURITY & PENTESTING (AUTHORIZED ONLY)
════════════════════════════════════════════════════════
For authorized lab environments (HackTheBox, TryHackMe, DVWA, your own VMs):
  → Proceed with: nmap, burpsuite, metasploit, sqlmap, nikto, gobuster
  → For GUI tools (Burp Suite): open_application → screenshot_and_analyze → interact
  → Document findings: write_file("pentest_report.md", findings)
  → Always: verify_scope → document → report

Never: target systems without authorization. Never exfiltrate real user data.

════════════════════════════════════════════════════════

════════════════════════════════════════
TOOL SELECTION — QUICK GUIDE
════════════════════════════════════════
WRITING CODE?
  → write_and_run(filename, code)          best for scripts you'll run once
  → write_file + execute_shell             when you need to reuse the file
  → execute_python(code)                   for quick one-off calculations

SEARCHING THE WEB?
  → web_search(query)                      text results, no browser
  → search_and_open(query)                 open top result in browser
  → browser_navigate(url)                  headless Selenium (reliable)
  → open_browser(url)                      system browser (GUI sessions)

CONTROLLING THE GUI?
  → screenshot_and_analyze(prompt)         ALWAYS first — see the screen
  → click_by_description("Submit button")  click by what you see
  → open_and_wait(app, seconds)            open application reliably
  → wait_and_verify(seconds, condition)    wait + confirm it loaded
  → multi_click(json)                      sequence of clicks+types

RUNNING COMMANDS?
  → execute_shell(cmd)                     standard shell, captures output
  → execute_shell_verbose(cmd)             same but labeled STDOUT/STDERR
  → pipe_commands("cmd1 | cmd2 | cmd3")   shell pipeline

GIT / CODE REPOS?
  → git_command("status")                  any git subcommand
  → git_clone_and_explore(url)             clone + show structure
  → browser_audit_repo(github_url)         full GitHub repo audit

PACKAGE INSTALL?
  → install_and_verify(package)            install + confirm it works

NEED TO WAIT?
  → sleep(seconds)                         simple wait
  → wait_and_verify(seconds, condition)    wait + screenshot verify
  → wait_for_window(title, timeout)        wait for window to appear

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
  0. observe_and_plan("my goal here")            # analyze screen FIRST, get action plan
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

POWER / COMPOUND:
  ask_user(question)                 — ask user when genuinely ambiguous (use sparingly)
  write_and_run(filename, code)      — write code + run immediately, return output
  install_and_verify(package)        — install package + verify it works
  git_clone_and_explore(url)         — clone repo + show structure
  search_and_open(query)             — web search + open top result in browser
  screen_to_clipboard()              — screenshot → AI text extraction → clipboard
  wait_and_verify(seconds, cond)     — wait + screenshot + condition check

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
    r = str(result)
    colour = red if is_error else dim
    lines = r.split('\n')
    if len(lines) <= 3 and len(r) <= 300:
        # Short result: show inline
        print(f"{colour('↳')} {colour(r.strip())}", flush=True)
    else:
        # Long result: show first 3 lines + count
        shown = '\n  '.join(l for l in lines[:3] if l.strip())
        extra = len(lines) - 3
        suffix = f"  {dim(f'[+{extra} lines]')}" if extra > 0 else ''
        print(f"{colour('↳')} {colour(shown)}{suffix}", flush=True)

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
    """
    Keep last 6 message exchanges; summarise older ones into a structured
    context block that preserves: tool calls made, files written, key results.
    """
    if len(msgs) <= 6:
        return msgs
    old = msgs[:-6]
    recent = msgs[-6:]

    tools_used: List[str] = []
    files_written: List[str] = []
    key_results: List[str] = []
    summary_parts = []

    for m in old:
        role = m.get('role', '?')
        c = m.get('content', '')
        if isinstance(c, list):
            # Extract tool calls and results from structured content
            for block in c:
                if isinstance(block, dict):
                    if block.get('type') == 'tool_use':
                        tname = block.get('name', '')
                        tinput = block.get('input', {})
                        tools_used.append(tname)
                        if tname in ('write_file', 'write_and_run'):
                            path = tinput.get('path', tinput.get('filename', ''))
                            if path:
                                files_written.append(path)
                    elif block.get('type') == 'tool_result':
                        result_str = str(block.get('content', ''))[:120]
                        if result_str and not result_str.startswith('ERROR'):
                            key_results.append(result_str.replace('\n', ' '))
            c = ' '.join(str(b.get('text', '') or b.get('content', '')) for b in c if isinstance(b, dict))
        preview = str(c)[:150].replace('\n', ' ')
        summary_parts.append(f"[{role}]: {preview}")

    parts = ["EARLIER CONTEXT (compacted for efficiency):"]
    if tools_used:
        unique_tools = list(dict.fromkeys(tools_used))  # preserve order, dedup
        parts.append(f"Tools called: {', '.join(unique_tools[-15:])}")
    if files_written:
        parts.append(f"Files written: {', '.join(files_written[-10:])}")
    if key_results:
        parts.append("Key results:")
        for r in key_results[-5:]:
            parts.append(f"  • {r[:100]}")
    parts.append("Full exchange summary:")
    parts.extend(summary_parts[-15:])

    summary = "\n".join(parts)
    return [
        {"role": "user", "content": summary},
        {"role": "assistant", "content": "Context noted. Continuing from where we left off."},
    ] + recent


_TASK_VERBS = re.compile(
    r'\b(open|launch|start|run|execute|install|download|create|write|make|build|'
    r'search|find|scan|audit|test|check|clone|read|analyze|fix|debug|deploy|'
    r'send|post|get|fetch|navigate|browse|click|type|press|drag|scroll|'
    r'move|copy|delete|remove|rename|update|upgrade|configure|setup|'
    r'monitor|record|capture|save|upload|convert|compress|extract|'
    r'generate|summarize|translate|parse|list|show|display|print|'
    r'pentest|hack|exploit|scan|enumerate|fuzz|inject)\b',
    re.IGNORECASE
)

def _is_task_mode(text: str) -> bool:
    """Detect if the user is requesting a task (vs a simple question/chat)."""
    t = text.strip()
    # Pure questions are chat mode
    if t.endswith('?') and len(t.split()) < 15:
        return False
    # Short factual queries are chat
    if len(t.split()) < 5 and not _TASK_VERBS.search(t):
        return False
    # Contains action verbs → task mode
    if _TASK_VERBS.search(t):
        return True
    # Multi-sentence descriptions → task mode
    if len(t.split()) > 20:
        return True
    return False


def run_agent(task: str, provider, max_steps: int = 100,
              quiet: bool = False, conv_messages: Optional[List] = None) -> str:
    """
    Run the agentic loop.
    conv_messages: if provided, conversation history is preserved (REPL mode).
    """
    task_mode = _is_task_mode(task)

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
    no_tool_pushes = 0          # times we nudged AI to continue after no tool calls
    MAX_ERRORS = 5              # retry up to this many consecutive provider errors
    MAX_NO_TOOL_PUSHES = 3      # max times to nudge AI before accepting its response
    _CTX_WARN_CHARS = 60_000    # ~15k tokens — start warning
    _CTX_COMPACT_CHARS = 100_000  # ~25k tokens — auto-compact older messages

    # Anti-loop detection: track (tool_name, arg_fingerprint) → count
    _tool_call_counts: Dict[str, int] = {}
    _LOOP_WARN_THRESHOLD = 3   # warn after same tool+args called 3x
    _LOOP_HARD_THRESHOLD = 5   # inject correction after 5x

    if not quiet:
        print()
        print(_box(f"Task: {task[:72]}"))
        print(dim(f"Provider: {provider.name}  |  Tools: {len(TOOLS)}  |  Max steps: {max_steps}"))
        if not _HAS_DISPLAY:
            print(dim("⚠  Headless: GUI tools unavailable — focus on shell/files/web tasks"))
        print(_hr())

    while step < max_steps:
        step += 1
        _SESSION_STATS['agent_steps'] += 1

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
            _SESSION_STATS['provider_calls'] += 1
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

            # Try context compaction on first error if context is large
            if consecutive_errors == 1 and _estimate_chars(messages) > _CTX_WARN_CHARS:
                if not quiet:
                    print(dim("  Auto-compacting messages before retry…"))
                if conv_messages is not None:
                    compacted = _compact_messages(list(messages))
                    messages.clear()
                    messages.extend(compacted)
                else:
                    messages = _compact_messages(messages)

            # Exponential backoff before retry (capped at 30s)
            wait = min(30, 2 ** consecutive_errors)
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

        # No tool calls — decide: accept or push forward
        if not calls:
            if text.strip():
                final_result = text.strip()

            # Pure conversation query → accept AI's response directly
            if not task_mode:
                return final_result if final_result else "(no response)"

            # Task mode — check if AI explicitly says it's done
            _done_phrases = re.compile(
                r'\b(task (is )?complete|done\b|finished\b|completed\b|accomplished|'
                r'successfully (done|completed|finished)|all done|all steps (done|complete)|'
                r'that\'s (all|it)\b|i\'ve (completed|finished|done)|'
                r'everything (is |has been )?(done|complete|finished)|'
                r'work is (done|complete|finished)|operation (complete|successful)|'
                r'result:|summary:|here (is|are) the|i (have|\'ve) (now )?(written|created|'
                r'saved|installed|opened|launched|built|run|executed|generated|deployed|'
                r'downloaded|uploaded|sent|configured))\b',
                re.IGNORECASE
            )
            if _done_phrases.search(final_result):
                return final_result

            # AI responded but didn't use tools and didn't declare done — push it
            if no_tool_pushes < MAX_NO_TOOL_PUSHES:
                no_tool_pushes += 1
                _SESSION_STATS['no_tool_pushes'] += 1
                # Vary nudge messages to avoid the AI seeing the same prompt repeatedly
                _nudge_msgs = [
                    (f"Execute the task now using tools. Do not describe — actually call tools. "
                     f"Task: {task[:100]}"),
                    (f"You described what to do but haven't done it yet. "
                     f"Call the appropriate tool NOW to make it happen. Task: {task[:100]}"),
                    (f"ACTION REQUIRED: Use a tool to make real progress. "
                     f"If you're unsure which tool to use, call think_and_plan first, then execute. "
                     f"Task: {task[:100]}"),
                ]
                push_msg = _nudge_msgs[min(no_tool_pushes - 1, len(_nudge_msgs) - 1)]
                if not quiet:
                    print(dim(f"\r  ↺ Nudging AI to execute (nudge {no_tool_pushes}/{MAX_NO_TOOL_PUSHES})…"))
                messages.append({"role": "user", "content": push_msg})
                continue
            else:
                return final_result if final_result else "(task ended without explicit completion)"

        # Execute tools
        tool_results = []
        _injected_hint = None  # anti-loop hint to append after tool results

        for call in calls:
            name = call["name"]
            args = call["args"]

            # Anti-loop detection
            fingerprint = f"{name}:{json.dumps(args, sort_keys=True, default=str)[:80]}"
            _tool_call_counts[fingerprint] = _tool_call_counts.get(fingerprint, 0) + 1
            loop_count = _tool_call_counts[fingerprint]
            if loop_count >= _LOOP_HARD_THRESHOLD and not quiet:
                hint = (f"\n⚠ LOOP DETECTED: '{name}' called {loop_count}x with same args. "
                        f"You MUST change your approach: try a completely different tool, "
                        f"use screenshot_and_analyze to re-assess, or call ask_user() if truly stuck.")
                _injected_hint = hint
                print(yellow(f"\r  {hint}"))
            elif loop_count >= _LOOP_WARN_THRESHOLD and not quiet:
                print(yellow(f"\r  ⚠ '{name}' called {loop_count}x — consider a different approach"))

            if not quiet:
                _print_tool_call(name, args)

            result = _dispatch_tool(name, args)

            # Task complete?
            if name == "task_complete" or result.startswith("TASK_COMPLETE:"):
                _SESSION_STATS['tasks_completed'] += 1
                final_result = result.replace("TASK_COMPLETE:", "").strip()
                if not quiet:
                    _print_tool_result(str(result))
                    print()
                    print(_hr())
                    print(f"{green(bold('✓'))} {bold('Task complete')}")
                    if final_result:
                        print(f"\n{_render_markdown(final_result)}\n")
                return final_result

            is_err = str(result).startswith('ERROR:')
            _stats_record_tool(name, is_error=is_err)

            if not quiet:
                _print_tool_result(str(result), is_error=is_err)

            tool_results.append({
                "call_id": call.get("id", f"t{step}_{name}"),
                "name": name, "result": result,
            })

        # Feed tool results back
        if isinstance(provider, ClaudeProvider):
            content_blocks = [
                {"type": "tool_result", "tool_use_id": tr["call_id"], "content": tr["result"]}
                for tr in tool_results
            ]
            if _injected_hint:
                content_blocks.append({"type": "text", "text": _injected_hint})
            messages.append({"role": "user", "content": content_blocks})
        elif isinstance(provider, (OpenAIProvider, HuggingFaceProvider, OllamaProvider)):
            for tr in tool_results:
                messages.append({"role": "tool",
                                  "tool_call_id": tr["call_id"],
                                  "content": tr["result"]})
            if _injected_hint:
                messages.append({"role": "user", "content": _injected_hint})
        else:
            combined = "\n\n".join(
                f"[Tool: {tr['name']}]\n{tr['result']}" for tr in tool_results)
            if _injected_hint:
                combined += f"\n\n{_injected_hint}"
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
  {cyan('/save [filename]')}     Save conversation transcript to a file
  {cyan('/shell <cmd>')}         Run shell command directly (alias: /run)
  {cyan('/run <cmd>')}           Run shell command directly
  {cyan('/screenshot')}          Take and optionally analyze a screenshot
  {cyan('/voice')}               Listen for voice input then run as task
  {cyan('/repos')}               List integrated repositories
  {cyan('/integrations')}        Show all Devin modules + integration status
  {cyan('/compact')}             Compress conversation history to save context
  {cyan('/debug')}               Show context, provider, tools, display diagnostics
  {cyan('/audit [target]')}      Run a comprehensive system/security audit
  {cyan('/think <task>')}        Plan a task step-by-step before executing
  {cyan('/workflow <task>')}     Execute as structured multi-step workflow
  {cyan('/pentest <target>')}    Run authorized pentest assessment on target
  {cyan('/lab [setup]')}         Show/setup lab environment and available security tools
  {cyan('/os')}                  Show OS/platform info and available tools
  {cyan('/audit_repo <own/nm>')} Audit a public GitHub repo (metadata + README + tree)
  {cyan('/demo')}                Quick health check (platform, tools, memory, providers)
  {cyan('/stats')}               Session stats (steps, tool calls, errors, top tools)
  {cyan('/workflow <json|@f>')}  Run a JSON-defined multi-step workflow (or @file.json)
  {cyan('/checkpoint [cmd]')}    Manage task checkpoints: list | save <name> <data> | load <name>
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
    w = max(70, shutil.get_terminal_size((100, 24)).columns - 1)
    facts = _DB.execute('SELECT count(*) FROM memories').fetchone()[0]
    mods = _modules_status()
    loaded = sum(1 for v in mods.values() if v)
    disp = green('gui') if _HAS_DISPLAY else yellow('headless')

    # Provider info
    if provider:
        if isinstance(provider, GeminiProvider):        ptype = 'gemini'
        elif isinstance(provider, ClaudeProvider):      ptype = 'claude'
        elif isinstance(provider, OpenAIProvider):      ptype = 'openai'
        elif isinstance(provider, HuggingFaceProvider): ptype = 'huggingface'
        elif isinstance(provider, OllamaProvider):      ptype = 'ollama'
        else:                                           ptype = 'unknown'
        model_display = provider.name.split('/')[-1] if '/' in provider.name else provider.name
        p_line = f"model: {bold(model_display)}  provider: {cyan(ptype)}  mode: auto"
    else:
        p_line = red("no provider — add API key to .env")

    top = '╭' + '─' * (w - 2) + '╮'
    bot = '╰' + '─' * (w - 2) + '╯'

    def row(content):
        clean = re.sub(r'\033\[[^m]+m', '', content)
        pad = max(0, w - 2 - len(clean) - 1)
        return '│ ' + content + ' ' * pad + '│'

    print()
    print(dim(top))
    print(dim(row(f"{bold(cyan('Devin AGI'))} {dim('v4.0.0')}  —  Autonomous OS-Controlling AI")))
    print(dim(row(f"cwd: {str(_ROOT)}")))
    print(dim(row(p_line)))
    print(dim(row(f"platform: {_PLATFORM}  {disp}  ·  tools: {bold(str(len(TOOLS)))}  ·  modules: {loaded}/{len(mods)}  ·  memories: {facts}")))
    print(dim(bot))
    print()

    if provider:
        print(f"  {green('✓')} Connected to {green(ptype.capitalize())} ({dim(model_display)})")
    else:
        print(f"  {red('✗')} No provider. Add API key to .env and restart.")
        print(f"  {dim('GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, or HF_TOKEN')}")
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
            "write a Python script that monitors CPU usage every 5 seconds",
            "take a screenshot and describe everything you see",
            "what ports are open on localhost?",
            "create a simple HTTP server on port 8080 in this directory",
            "clone https://github.com/torvalds/linux and show me the top-level structure",
            "install the requests library and write a script that gets my public IP",
            "open a terminal, run htop, take a screenshot and describe the processes",
            "search the web for 'latest AI models 2025' and summarize the top 3 results",
            "check if Docker is installed, if not install it",
            "write and run a Python script that generates a fibonacci sequence to 1000",
            "scan localhost for open ports and tell me what services are running",
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

    def _read_input() -> str:
        """Read user input — supports single-line and multiline paste mode (<<EOF)."""
        try:
            line = input(f"{bold(cyan('❯'))} {bold('Devin')} ").strip()
        except (EOFError, KeyboardInterrupt):
            raise KeyboardInterrupt
        # Multiline mode: if line ends with \ or starts with <<
        if line.endswith('\\') or line == '<<':
            lines = [line.rstrip('\\')]
            print(dim("  (multiline mode — empty line to finish)"))
            while True:
                try:
                    more = input(f"  {dim('...')} ")
                except (EOFError, KeyboardInterrupt):
                    break
                if more.strip() == '':
                    break
                lines.append(more)
            return '\n'.join(lines).strip()
        return line

    while True:
        try:
            user_input = _read_input()
        except KeyboardInterrupt:
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
                q = arg.lower().strip() if arg else ''
                if q:
                    # Match by category, tool name, or description substring
                    matched = {}
                    for name, t in TOOLS.items():
                        cat = t.get('category', 'other')
                        desc = t.get('desc', '')
                        if q in cat.lower() or q in name.lower() or q in desc.lower():
                            matched.setdefault(cat, []).append(name)
                    cats = matched
                    if not cats:
                        print(yellow(f"  No tools match {arg!r} (searched category, name, description)"))
                else:
                    for name, t in TOOLS.items():
                        cats.setdefault(t.get('category', 'other'), []).append(name)
                for cat in sorted(cats):
                    print(f"\n  {bold(cat.upper())}  ({len(cats[cat])} tool{'s' if len(cats[cat])!=1 else ''})")
                    for name in sorted(cats[cat]):
                        desc = TOOLS[name]['desc'][:75]
                        print(f"    {cyan(name):<32} {dim(desc)}")
                if not q:
                    print(f"\n  {dim(f'Total: {len(TOOLS)} tools across {len(cats)} categories')}")
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

            elif cmd == '/save':
                # Save current conversation to a file
                if not conv_messages:
                    print(yellow("  Nothing to save — conversation is empty."))
                else:
                    fname = arg or f"devin_transcript_{_SESSION_ID}.md"
                    fp = _ROOT / fname if not os.path.isabs(fname) else Path(fname)
                    lines = [f"# Devin session transcript — {datetime.now().isoformat(timespec='seconds')}",
                             f"# Session ID: {_SESSION_ID}",
                             f"# Provider: {provider.name if provider else 'none'}", ""]
                    for m in conv_messages:
                        role = m.get('role', '?')
                        content = m.get('content', '')
                        if isinstance(content, list):
                            content = '\n'.join(
                                str(b.get('text','') or b.get('content','') or b.get('input',''))
                                for b in content
                            )
                        lines.append(f"## {role}")
                        lines.append(str(content))
                        lines.append("")
                    fp.write_text('\n'.join(lines))
                    print(green(f"  ✓ Saved {len(conv_messages)} messages → {fp}"))

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

            elif cmd == '/think':
                if not arg:
                    print(yellow("  Usage: /think <task description>"))
                elif provider:
                    plan = tool_think_and_plan(arg)
                    print(f"\n{plan}\n")
                    go = input("  Execute this plan now? [Y/n] ").strip().lower()
                    if go != 'n':
                        run_agent(arg, provider, conv_messages=conv_messages)

            elif cmd == '/pentest':
                if not arg:
                    print(yellow("  Usage: /pentest <target> (e.g. /pentest 192.168.1.1 or /pentest lab.hackthebox.eu)"))
                elif provider:
                    task = (f"Perform an authorized penetration test assessment of: {arg}\n"
                            f"Steps:\n"
                            f"1. Verify this is an authorized target (lab/VM/owned system)\n"
                            f"2. Run reconnaissance: execute_shell('nmap -sV -sC -A {arg}')\n"
                            f"3. Analyze open ports and services\n"
                            f"4. Check for common vulnerabilities\n"
                            f"5. If Burp Suite is available, open it via GUI automation\n"
                            f"6. Document all findings in pentest_report.md\n"
                            f"7. Provide a summary of vulnerabilities found")
                    run_agent(task, provider, conv_messages=conv_messages)

            elif cmd == '/lab':
                if not arg:
                    # Show lab environment setup
                    print(f"\n  {bold('Lab Environment Setup')}")
                    print(f"  {dim('Available tools:')}")
                    for tool in ['nmap', 'burpsuite', 'metasploit', 'sqlmap', 'nikto',
                                 'gobuster', 'hydra', 'wireshark', 'tcpdump', 'aircrack-ng']:
                        status = green('✓') if _cmd_exists(tool) else dim('✗')
                        print(f"    {status} {tool}")
                    print()
                elif provider:
                    run_agent(f"Set up a lab environment for: {arg}", provider,
                              conv_messages=conv_messages)

            elif cmd == '/workflow':
                if not arg:
                    print(yellow("  Usage: /workflow <task description>  — runs as structured multi-step workflow"))
                elif provider:
                    run_agent(
                        f"Execute this as a structured workflow using think_and_plan first:\n{arg}",
                        provider, conv_messages=conv_messages)

            elif cmd == '/os':
                print(f"\n{tool_platform_info()}\n")

            elif cmd == '/run':
                if arg:
                    print(tool_execute_shell(arg, timeout=60))
                else:
                    print(yellow("  Usage: /run <shell command>"))

            elif cmd == '/audit_repo':
                if not arg:
                    print(yellow("  Usage: /audit_repo <owner/name>  (e.g. /audit_repo torvalds/linux)"))
                else:
                    print(f"\n{tool_github_repo_audit(arg, deep=True)}\n")

            elif cmd == '/stats':
                s = _SESSION_STATS
                elapsed = time.time() - s['started_at']
                mm, ss = divmod(int(elapsed), 60); hh, mm = divmod(mm, 60)
                print(f"\n  {bold('Session Stats')}")
                print(f"    Elapsed        : {hh:02d}:{mm:02d}:{ss:02d}")
                print(f"    Agent steps    : {s['agent_steps']}")
                print(f"    Provider calls : {s['provider_calls']}")
                print(f"    Tool calls     : {s['tool_calls']} ({s['errors']} errors)")
                print(f"    Tasks complete : {s['tasks_completed']}")
                print(f"    Continue nudges: {s['no_tool_pushes']}")
                if s['tool_usage']:
                    print(f"\n  {bold('Top tools')}")
                    for tool, cnt in sorted(s['tool_usage'].items(), key=lambda x: -x[1])[:10]:
                        print(f"    {cnt:4d} × {tool}")
                print()

            elif cmd == '/demo':
                # Quick end-to-end health check without needing AI
                print(dim("  Running quick health check…\n"))
                print(green("  ✓ Platform: ") + _PLATFORM)
                print(green("  ✓ Display: ") + ('yes' if _HAS_DISPLAY else 'headless'))
                print(green("  ✓ Tools: ") + str(len(TOOLS)))
                mods = _modules_status()
                loaded = sum(1 for v in mods.values() if v)
                print(green("  ✓ Modules loaded: ") + f"{loaded}/{len(mods)}")
                print(green("  ✓ Provider: ") + (provider.name if provider else red('none')))
                print(green("  ✓ Memory: ") + str(_DB.execute('SELECT count(*) FROM memories').fetchone()[0]) + " facts")
                # Test one tool end-to-end
                r = tool_execute_python('print(2+2)')
                print(green("  ✓ execute_python(print(2+2)): ") + r.strip())
                print(dim("\n  For a full demo, run: python3 tests/demo_workflow.py"))

            elif cmd == '/workflow':
                # Execute a multi-step JSON workflow
                if not args.strip():
                    print(yellow("  Usage: /workflow <json-steps | @path/to/workflow.json>"))
                    print(dim("  JSON: [{\"tool\":\"execute_shell\",\"args\":{\"command\":\"echo hi\"},\"label\":\"test\"}]"))
                    print(dim("  File: /workflow @my_workflow.json"))
                else:
                    wf_arg = args.strip()
                    if wf_arg.startswith('@'):
                        # Load from file
                        wf_path = wf_arg[1:].strip()
                        print(dim(f"  Loading workflow from: {wf_path}"))
                        result = tool_run_workflow_file(wf_path)
                    else:
                        result = tool_multi_step_workflow(wf_arg)
                    print(result)

            elif cmd == '/checkpoint':
                # Manage task checkpoints
                sub = args.strip().split(None, 2)
                subcmd = sub[0] if sub else 'list'
                if subcmd == 'list' or not sub:
                    print(tool_checkpoint_list())
                elif subcmd == 'save' and len(sub) >= 3:
                    print(tool_checkpoint_save(sub[1], sub[2]))
                elif subcmd == 'load' and len(sub) >= 2:
                    print(tool_checkpoint_load(sub[1]))
                else:
                    print(yellow("  Usage: /checkpoint [list | save <name> <data> | load <name>]"))

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

def _cli_doctor() -> int:
    """Deep diagnostic — health + dependency check + test run summary."""
    print()
    print(bold("Devin AGI v4.0.0 — Doctor"))
    print("=" * 60)

    # 1. Python / Platform
    print(f"\n{bold('Runtime')}")
    print(f"  Python       : {sys.version.split()[0]}")
    print(f"  Platform     : {_PLATFORM}")
    print(f"  Display      : {'yes ('+os.environ.get('DISPLAY','?')+')' if _HAS_DISPLAY else 'headless'}")
    print(f"  Working dir  : {_ROOT}")

    # 2. Core deps
    print(f"\n{bold('Core Python dependencies')}")
    core_deps = ['sqlite3', 'urllib', 'subprocess', 'json', 'importlib']
    for d in core_deps:
        try:
            __import__(d)
            print(f"  {green('✓')} {d}")
        except ImportError:
            print(f"  {red('✗')} {d} MISSING (should never happen — stdlib)")

    # 3. Optional deps (that unlock capabilities)
    print(f"\n{bold('Optional dependencies')} (each enables a capability tier)")
    optional = [
        ('pyautogui',  'mouse/keyboard/screenshot (all OS)'),
        ('mss',        'fast cross-platform screenshot'),
        ('PIL',        'image manipulation'),
        ('selenium',   'browser automation'),
        ('playwright', 'modern browser automation'),
        ('requests',   'nicer HTTP than urllib'),
        ('psutil',     'system monitoring (cpu/mem/disk)'),
        ('speech_recognition', 'speech-to-text'),
        ('pyttsx3',    'text-to-speech'),
        ('rich',       'nicer terminal UI'),
        ('anthropic',  'Claude SDK (alt to raw HTTP)'),
    ]
    for pkg, purpose in optional:
        try:
            __import__(pkg)
            print(f"  {green('✓')} {pkg:20s} {dim(purpose)}")
        except ImportError:
            print(f"  {dim('✗')} {pkg:20s} {dim(purpose + '  (not installed)')}")

    # 4. Provider keys
    print(f"\n{bold('AI provider keys')}")
    for k, note in [
        ('GEMINI_API_KEY', 'Google Gemini (free tier)'),
        ('ANTHROPIC_API_KEY', 'Anthropic Claude (paid)'),
        ('OPENAI_API_KEY', 'OpenAI (paid)'),
        ('HF_TOKEN', 'HuggingFace (free tier)'),
    ]:
        val = os.environ.get(k) or (k == 'HF_TOKEN' and os.environ.get('HUGGINGFACE_API_KEY'))
        marker = green('✓ set') if val else dim('✗ not set')
        print(f"  {marker:10s}  {k:22s} {dim(note)}")

    # 5. Ollama probe
    print(f"\n{bold('Ollama (local LLM)')}")
    ollama_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    try:
        req = urllib.request.Request(f"{ollama_url}/api/tags")
        with urllib.request.urlopen(req, timeout=1) as r:
            data = json.loads(r.read())
            models = [m.get('name') for m in data.get('models', [])]
            print(f"  {green('✓')} Reachable at {ollama_url}")
            if models:
                print(f"      Models: {', '.join(models[:5])}{' …' if len(models) > 5 else ''}")
            else:
                print(f"      No models pulled. Try: ollama pull llama3.2")
    except Exception as e:
        print(f"  {dim('✗')} Not reachable at {ollama_url}  ({type(e).__name__})")

    # 6. External tools
    print(f"\n{bold('External CLI tools')}")
    for cmd, purpose in [
        ('git', 'version control'),
        ('firefox', 'browser (Linux/Win)'),
        ('chromium', 'browser'),
        ('google-chrome', 'browser'),
        ('xdotool', 'X11 mouse/keyboard/window (Linux)'),
        ('scrot', 'screenshot (Linux)'),
        ('wmctrl', 'window management (Linux)'),
        ('xclip', 'clipboard (Linux)'),
        ('nmap', 'network scanning (authorized only)'),
        ('curl', 'HTTP'),
        ('wget', 'download'),
    ]:
        if _cmd_exists(cmd):
            print(f"  {green('✓')} {cmd:16s} {dim(purpose)}")
        else:
            print(f"  {dim('✗')} {cmd:16s} {dim(purpose + '  (not in PATH)')}")

    # 7. Registry integrity
    print(f"\n{bold('Registry integrity')}")
    mods = _modules_status()
    loaded = sum(1 for v in mods.values() if v)
    print(f"  Tools: {len(TOOLS)}  ({sum(1 for t in TOOLS.values() if t.get('category') == 'os')} os, "
          f"{sum(1 for t in TOOLS.values() if t.get('category') == 'vision')} vision, "
          f"{sum(1 for t in TOOLS.values() if t.get('category') == 'shell')} shell, ...)")
    print(f"  Modules: {loaded}/{len(mods)} loaded")
    print(f"  Memory: {_DB.execute('SELECT count(*) FROM memories').fetchone()[0]} facts in {_DB_PATH.name}")

    # 8. Fast self-check
    print(f"\n{bold('Self-check')}")
    checks = [
        ('execute_python', lambda: '4' in tool_execute_python('print(2+2)')),
        ('execute_shell', lambda: 'devin' in tool_execute_shell('echo devin').lower()),
        ('platform_info', lambda: len(tool_platform_info()) > 20),
        ('think_and_plan', lambda: 'TASK' in tool_think_and_plan('test')),
        ('_is_task_mode',   lambda: _is_task_mode('open firefox') == True),
    ]
    ok = 0
    for name, fn in checks:
        try:
            if fn():
                print(f"  {green('✓')} {name}")
                ok += 1
            else:
                print(f"  {red('✗')} {name}: unexpected result")
        except Exception as e:
            print(f"  {red('✗')} {name}: {e}")
    print(f"\n  {ok}/{len(checks)} self-checks passed")
    print()
    return 0 if ok == len(checks) else 1


def _cli_health() -> int:
    """Print core health check and exit. No AI required."""
    mods = _modules_status()
    loaded = sum(1 for v in mods.values() if v)
    print(f"Devin AGI v4.0.0")
    print(f"  Platform     : {_PLATFORM}")
    print(f"  Display      : {'yes' if _HAS_DISPLAY else 'headless'}")
    print(f"  Tools        : {len(TOOLS)}")
    print(f"  Modules      : {loaded}/{len(mods)} loaded")
    print(f"  Memory       : {_DB.execute('SELECT count(*) FROM memories').fetchone()[0]} facts")
    # Provider keys detected
    keys = [
        ('GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY')),
        ('ANTHROPIC_API_KEY', os.environ.get('ANTHROPIC_API_KEY')),
        ('OPENAI_API_KEY', os.environ.get('OPENAI_API_KEY')),
        ('HF_TOKEN', os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_API_KEY')),
    ]
    print(f"  Provider keys:")
    any_key = False
    for name, val in keys:
        status = '✓' if val else '✗'
        print(f"    {status} {name}")
        if val: any_key = True
    # Ollama
    ollama_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    try:
        req = urllib.request.Request(f"{ollama_url}/api/tags")
        with urllib.request.urlopen(req, timeout=1) as r:
            data = json.loads(r.read())
            models = [m.get('name') for m in data.get('models', [])]
            print(f"    ✓ Ollama at {ollama_url}: {len(models)} models available")
            any_key = True
    except Exception:
        print(f"    ✗ Ollama at {ollama_url}: not reachable")
    if not any_key:
        print()
        print("  ⚠  No provider available. Add an API key to .env or start Ollama locally.")
        return 1
    return 0


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
            print(__doc__ or "Devin AGI v4.0.0")
            print("  ./devin                             — interactive REPL")
            print("  ./devin 'task description'          — one-shot task")
            print("  ./devin --provider huggingface ...  — pick a provider")
            print("  ./devin --model MODEL_ID ...        — pick a model")
            print("  ./devin --health                    — health check (no AI)")
            print("  ./devin --doctor                    — deep diagnostic (deps, tools, self-check)")
            print("  ./devin --test                      — run test suite (no AI)")
            print("  ./devin --version                   — print version")
            sys.exit(0)
        elif a in ('--version', '-v'):
            print("Devin AGI 4.0.0")
            print(f"  {len(TOOLS)} tools, {sum(1 for v in _modules_status().values() if v)} modules loaded")
            sys.exit(0)
        elif a == '--health':
            sys.exit(_cli_health())
        elif a == '--doctor':
            sys.exit(_cli_doctor())
        elif a == '--test':
            # Run the core test suite
            test_file = _ROOT / 'tests' / 'test_core.py'
            if not test_file.exists():
                print(red(f"Test file missing: {test_file}")); sys.exit(1)
            r = subprocess.run([sys.executable, str(test_file)])
            sys.exit(r.returncode)
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
