#!/usr/bin/env python3
"""
Devin AGI 4.0 — Claude Code-style Interactive REPL

All credentials via .env / environment variables only.
Never hardcode API keys.
"""
from __future__ import annotations
import os, sys, shutil, signal, subprocess, threading, time, json
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator

ROOT = Path(__file__).resolve().parent.parent
_ENV = ROOT / '.env'
if _ENV.exists():
    for _l in _ENV.read_text().splitlines():
        _l = _l.strip()
        if _l and not _l.startswith('#') and '=' in _l:
            _k, _, _v = _l.partition('=')
            os.environ.setdefault(_k.strip(), _v.strip().strip('"\''))


# ── Terminal helpers ───────────────────────────────────────────────────────────
def _cols() -> int:
    return shutil.get_terminal_size((80, 24)).columns

_IS_TTY = sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    if not _IS_TTY:
        return text
    return f'\033[{code}m{text}\033[0m'

CYAN_B = '36;1'
CYAN   = '36'
WHITE_B = '37;1'
GRAY   = '2'
YELLOW = '33'
GREEN  = '32'
RED    = '31'
MAGENTA = '35'


# ── AI Provider wrappers ───────────────────────────────────────────────────────

class _BaseProvider:
    name = 'none'
    def available(self) -> bool: return False
    def stream(self, messages: List[Dict], system: str = '') -> Generator[str, None, None]:
        yield '[No provider available — set API key in .env]'


class _GeminiProvider(_BaseProvider):
    name = 'gemini'

    def __init__(self):
        self._key = os.environ.get('GEMINI_API_KEY', '') or os.environ.get('GOOGLE_API_KEY', '')
        self._model = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash-exp')
        self._client_cache = None

    def available(self) -> bool:
        return bool(self._key)

    def _client(self):
        if self._client_cache:
            return self._client_cache
        try:
            import google.genai as genai
            c = genai.Client(api_key=self._key)
            self._client_cache = ('new', c)
            return self._client_cache
        except (ImportError, Exception):
            pass
        try:
            import google.generativeai as genai
            genai.configure(api_key=self._key)
            m = genai.GenerativeModel(self._model)
            self._client_cache = ('old', m)
            return self._client_cache
        except (ImportError, Exception):
            return None

    def stream(self, messages: List[Dict], system: str = '') -> Generator[str, None, None]:
        info = self._client()
        if not info:
            yield '[Gemini SDK not installed: pip install google-genai]'
            return
        sdk, client = info
        last = messages[-1].get('content', '') if messages else ''
        try:
            if sdk == 'new':
                from google.genai import types as gt
                cfg = gt.GenerateContentConfig(
                    system_instruction=system or None,
                    temperature=0.7,
                )
                for chunk in client.models.generate_content_stream(
                    model=self._model, contents=last, config=cfg
                ):
                    if chunk.text:
                        yield chunk.text
            else:
                history = []
                for msg in messages[:-1]:
                    history.append({
                        'role': 'model' if msg.get('role') == 'assistant' else 'user',
                        'parts': [msg.get('content', '')],
                    })
                chat = client.start_chat(history=history)
                for chunk in chat.send_message(last, stream=True):
                    if chunk.text:
                        yield chunk.text
        except Exception as e:
            yield f'\n[Gemini error: {e}]'


class _ClaudeProvider(_BaseProvider):
    name = 'claude'

    def __init__(self):
        self._key = os.environ.get('ANTHROPIC_API_KEY', '')
        self._model = os.environ.get('CLAUDE_MODEL', 'claude-opus-4-5')

    def available(self) -> bool:
        return bool(self._key)

    def stream(self, messages: List[Dict], system: str = '') -> Generator[str, None, None]:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self._key)
            with client.messages.stream(
                model=self._model, max_tokens=4096,
                system=system or 'You are Devin, an autonomous AI assistant.',
                messages=messages,
            ) as s:
                for text in s.text_stream:
                    yield text
        except Exception as e:
            yield f'[Claude error: {e}]'


class _OpenAIProvider(_BaseProvider):
    name = 'openai'

    def __init__(self):
        self._key = os.environ.get('OPENAI_API_KEY', '')
        self._model = os.environ.get('OPENAI_MODEL', 'gpt-4o')

    def available(self) -> bool:
        return bool(self._key)

    def stream(self, messages: List[Dict], system: str = '') -> Generator[str, None, None]:
        try:
            import openai
            client = openai.OpenAI(api_key=self._key)
            all_msgs = ([{'role': 'system', 'content': system}] + messages) if system else messages
            for chunk in client.chat.completions.create(
                model=self._model, messages=all_msgs, stream=True
            ):
                d = chunk.choices[0].delta
                if d.content:
                    yield d.content
        except Exception as e:
            yield f'[OpenAI error: {e}]'


# HF model fallback chain — best reasoning first
_HF_MODELS = [
    'Qwen/Qwen2.5-72B-Instruct',
    'meta-llama/Meta-Llama-3.1-70B-Instruct',
    'mistralai/Mixtral-8x7B-Instruct-v0.1',
    'mistralai/Mistral-7B-Instruct-v0.3',
    'HuggingFaceH4/zephyr-7b-beta',
]


class _HFProvider(_BaseProvider):
    name = 'huggingface'

    def __init__(self):
        self._key = os.environ.get('HF_TOKEN', '') or os.environ.get('HUGGINGFACE_API_KEY', '')
        self._model = os.environ.get('HF_MODEL', '')

    def available(self) -> bool:
        return bool(self._key)

    def stream(self, messages: List[Dict], system: str = '') -> Generator[str, None, None]:
        try:
            # Try the enhanced provider first (supports model fallback)
            from modules.hf_enhanced_provider import stream_chat as hf_stream
            all_msgs = ([{'role': 'system', 'content': system}] + messages) if system else messages
            model = self._model or _HF_MODELS[0]
            for chunk in hf_stream(all_msgs, model=model):
                yield chunk
            return
        except (ImportError, Exception):
            pass

        # Direct fallback using HF Router OpenAI-compatible endpoint
        import urllib.request as _ur
        import json as _json

        all_msgs = ([{'role': 'system', 'content': system}] + messages) if system else messages
        models_to_try = [self._model] if self._model else _HF_MODELS

        for model_id in models_to_try:
            try:
                payload = _json.dumps({
                    'model': model_id,
                    'messages': all_msgs,
                    'stream': True,
                    'max_tokens': 2048,
                }).encode()
                req = _ur.Request(
                    'https://router.huggingface.co/v1/chat/completions',
                    data=payload,
                    headers={
                        'Authorization': f'Bearer {self._key}',
                        'Content-Type': 'application/json',
                    },
                )
                with _ur.urlopen(req, timeout=90) as resp:
                    for raw in resp:
                        line = raw.decode('utf-8', errors='replace').strip()
                        if not line.startswith('data:'):
                            continue
                        chunk_str = line[5:].strip()
                        if chunk_str == '[DONE]':
                            return
                        try:
                            chunk = _json.loads(chunk_str)
                            delta = chunk['choices'][0]['delta']
                            if delta.get('content'):
                                yield delta['content']
                        except Exception:
                            pass
                return  # success
            except Exception:
                continue

        yield '[HuggingFace: all models unavailable. Check HF_TOKEN in .env]'


class _FCCProvider(_BaseProvider):
    """Free Claude Code server — OpenAI-compatible HTTP proxy at FCC_BASE_URL."""
    name = 'free_claude'

    def __init__(self):
        self._base = (os.environ.get('FCC_BASE_URL') or '').rstrip('/')
        self._model = os.environ.get('FCC_MODEL', 'claude-opus-4-5')

    def available(self) -> bool:
        return bool(self._base)

    def stream(self, messages: List[Dict], system: str = '') -> Generator[str, None, None]:
        import urllib.request as _ur
        import json as _json

        all_msgs = ([{'role': 'system', 'content': system}] + messages) if system else messages
        payload = _json.dumps({
            'model': self._model,
            'messages': all_msgs,
            'stream': True,
            'max_tokens': 4096,
        }).encode()
        try:
            req = _ur.Request(
                f'{self._base}/v1/chat/completions',
                data=payload,
                headers={'Content-Type': 'application/json'},
            )
            with _ur.urlopen(req, timeout=120) as resp:
                for raw in resp:
                    line = raw.decode('utf-8', errors='replace').strip()
                    if not line.startswith('data:'):
                        continue
                    chunk_str = line[5:].strip()
                    if chunk_str == '[DONE]':
                        return
                    try:
                        chunk = _json.loads(chunk_str)
                        delta = chunk['choices'][0]['delta']
                        if delta.get('content'):
                            yield delta['content']
                    except Exception:
                        pass
        except Exception as e:
            yield f'[FCC server error: {e}]'


class _FreeClaudeSubprocProvider(_BaseProvider):
    """Free Claude via subprocess/session (no FCC_BASE_URL needed)."""
    name = 'free_claude_sub'

    def available(self) -> bool:
        try:
            from modules.free_claude_provider import is_available
            return is_available()
        except Exception:
            return False

    def stream(self, messages: List[Dict], system: str = '') -> Generator[str, None, None]:
        try:
            from modules.free_claude_provider import chat as fc_chat
            text, _ = fc_chat(messages, system=system)
            yield text
        except Exception as e:
            yield f'[free-claude-code unavailable: {e}]'


def _select_provider(forced: str = '') -> _BaseProvider:
    fcc = _FCCProvider()
    fcc_sub = _FreeClaudeSubprocProvider()
    candidates = {
        'gemini': _GeminiProvider(),
        'claude': _ClaudeProvider(),
        'openai': _OpenAIProvider(),
        'hf': _HFProvider(),
        'huggingface': _HFProvider(),
        'free_claude': fcc if fcc.available() else fcc_sub,
        'fcc': fcc,
    }
    name = (forced or os.environ.get('DEVIN_PROVIDER', '')).lower().strip()
    if name and name in candidates:
        p = candidates[name]
        if p.available():
            return p
    # Auto-select: Claude → Gemini → OpenAI → HF → FCC server → free-claude subprocess
    for p in [
        candidates['claude'],
        candidates['gemini'],
        candidates['openai'],
        candidates['hf'],
        fcc,
        fcc_sub,
    ]:
        if p.available():
            return p
    # Nothing available — return FCC so user sees helpful message
    return fcc


# ── System prompt ──────────────────────────────────────────────────────────────

_SYSTEM = """You are Devin, a powerful autonomous AI agent running inside Devin AGI v4.0.

You can reason, plan, and act to complete complex tasks on a real computer — exactly like a
senior software engineer combined with a security researcher would. You control the OS through
screenshots, mouse, keyboard, and shell commands.

Your core capabilities:
- **OS Control**: take screenshots, move/click mouse, type, press keys, manage windows
- **Browser Automation**: open URLs, search, fill forms, extract data from web pages
- **Shell Execution**: run any shell command, scripts, tools
- **Code**: write, run, and debug Python/TypeScript/Bash/any language
- **File System**: read, write, organize files and directories
- **System Monitor**: check CPU, memory, disk, processes, network
- **Memory**: store and recall facts across sessions
- **Security tools**: authorized vulnerability scanning, pentesting (with explicit permission only)
- **AI Reasoning**: break down complex problems, think step-by-step

Operating principles:
1. **Think before acting**: analyze the task, plan steps
2. **Observe**: use screenshot/shell to understand current state
3. **Act incrementally**: one step at a time, verify each step worked
4. **Recover**: if something fails, diagnose and try an alternative
5. **Complete**: report exactly what happened, not what should have happened

For security work: only operate on systems you own or have explicit written authorization to test.
Format responses in Markdown. Be concise, direct, and action-oriented."""

_SLASH_HELP = """
  Slash commands:
    /help              Show this help
    /clear             Clear screen + conversation history
    /status            System and module status
    /tools             List registered tools
    /screenshot        Take + show current screenshot description
    /memory            Show saved memories
    /remember <fact>   Save a fact to persistent memory
    /shell <cmd>       Run a shell command directly
    /git <args>        Run a git command
    /repos             List integrated repositories
    /think <task>      Run full agentic reasoning loop on a task
    /voice             Toggle voice mode
    /provider <p>      Switch AI provider (claude|gemini|openai|hf|free_claude|fcc)
    /model <m>         Set model for current provider
    /mem               Conversation memory stats
    /cwd               Show working directory
    /reset             Reset conversation history
    /exit  /q          Exit Devin
"""


# ── Agentic tool registration ──────────────────────────────────────────────────

def _build_agent_tools():
    """Build the tool registry for the agentic reasoning engine."""
    tools = {}

    # OS tools
    try:
        from modules.os_agent import get_os_agent
        agent = get_os_agent()

        def _screenshot_tool(**_):
            r = agent.screenshot('Describe the current screen state in detail')
            return f"Screenshot: {r.message}\nVision: {r.vision_result or 'no vision'}"

        def _click_tool(x: int, y: int, button: str = 'left', **_):
            r = agent.click(int(x), int(y), button)
            return f"Click at ({x},{y}): {'OK' if r.success else r.message}"

        def _type_text_tool(text: str, **_):
            r = agent.type_text(str(text))
            return f"Typed '{text}': {'OK' if r.success else r.message}"

        def _press_key_tool(key: str, **_):
            r = agent.press_key(str(key))
            return f"Key '{key}': {'OK' if r.success else r.message}"

        def _hotkey_tool(keys: str, **_):
            r = agent.hotkey(*str(keys).split('+'))
            return f"Hotkey '{keys}': {'OK' if r.success else r.message}"

        def _open_app_tool(name: str, **_):
            r = agent.open_application(str(name))
            return f"Open '{name}': {'OK — pid=' + str(r.data.get('pid','?')) if r.success else r.message}"

        def _navigate_tool(url: str, **_):
            r = agent.navigate_browser(str(url))
            return f"Navigate to '{url}': {'OK' if r.success else r.message}"

        def _browser_search_tool(query: str, **_):
            r = agent.browser_search(str(query))
            return f"Browser search '{query}': {'OK' if r.success else r.message}"

        def _find_click_tool(description: str, **_):
            r = agent.click_element(str(description))
            return f"Click element '{description}': {'OK' if r.success else r.message}"

        def _observe_screen(**_):
            return agent.observe()

        tools['screenshot'] = {'fn': _screenshot_tool, 'description': 'Take a screenshot and describe the current screen', 'params': {}}
        tools['click'] = {'fn': _click_tool, 'description': 'Click at pixel coordinates', 'params': {'x': 'x coordinate', 'y': 'y coordinate', 'button': 'left|right|middle'}}
        tools['type_text'] = {'fn': _type_text_tool, 'description': 'Type text using keyboard', 'params': {'text': 'text to type'}}
        tools['press_key'] = {'fn': _press_key_tool, 'description': 'Press a keyboard key (e.g. Return, Tab, Escape)', 'params': {'key': 'key name'}}
        tools['hotkey'] = {'fn': _hotkey_tool, 'description': 'Press a keyboard hotkey combo (e.g. ctrl+c)', 'params': {'keys': 'keys joined by + e.g. ctrl+c'}}
        tools['open_application'] = {'fn': _open_app_tool, 'description': 'Launch an application by name', 'params': {'name': 'application name e.g. firefox, chrome, terminal'}}
        tools['navigate_browser'] = {'fn': _navigate_tool, 'description': 'Navigate browser to a URL', 'params': {'url': 'URL to navigate to'}}
        tools['browser_search'] = {'fn': _browser_search_tool, 'description': 'Search for a query in the browser', 'params': {'query': 'search query'}}
        tools['click_element'] = {'fn': _find_click_tool, 'description': 'Find and click a UI element by description', 'params': {'description': 'element description e.g. "address bar" or "submit button"'}}
        tools['observe_screen'] = {'fn': _observe_screen, 'description': 'Take a screenshot and return description of current screen state', 'params': {}}
    except Exception as e:
        pass

    # Shell tools
    def _shell_tool(cmd: str, timeout: int = 30, **_):
        try:
            r = subprocess.run(str(cmd), shell=True, capture_output=True, text=True, timeout=int(timeout))
            out = (r.stdout or '')[:2000]
            err = (r.stderr or '')[:500]
            return f"$ {cmd}\n{out}" + (f"\nSTDERR: {err}" if err else "")
        except subprocess.TimeoutExpired:
            return f"[timeout after {timeout}s: {cmd}]"
        except Exception as e:
            return f"[shell error: {e}]"

    def _read_file_tool(path: str, **_):
        try:
            p = Path(str(path))
            if not p.exists():
                return f"[file not found: {path}]"
            if p.stat().st_size > 100_000:
                return f"[file too large: {p.stat().st_size} bytes — use shell_run with head/tail]"
            return p.read_text(errors='replace')[:3000]
        except Exception as e:
            return f"[read error: {e}]"

    def _write_file_tool(path: str, content: str, **_):
        try:
            p = Path(str(path))
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(str(content))
            return f"Written {len(content)} chars to {path}"
        except Exception as e:
            return f"[write error: {e}]"

    tools['shell_run'] = {'fn': _shell_tool, 'description': 'Execute a shell command and return stdout', 'params': {'cmd': 'shell command', 'timeout': 'seconds (default 30)'}}
    tools['read_file'] = {'fn': _read_file_tool, 'description': 'Read a file and return its contents', 'params': {'path': 'file path'}}
    tools['write_file'] = {'fn': _write_file_tool, 'description': 'Write content to a file', 'params': {'path': 'file path', 'content': 'content to write'}}

    # Memory tools
    def _remember_tool(fact: str, **_):
        try:
            _save_memory(str(fact))
            return f"Remembered: {fact}"
        except Exception as e:
            return f"[memory error: {e}]"

    def _recall_tool(query: str = '', **_):
        try:
            mems = _load_memories()
            if not mems:
                return "No memories stored."
            if query:
                q = query.lower()
                mems = [m for m in mems if q in m.get('content', '').lower()]
            return '\n'.join(f"- {m['content']}" for m in mems[-20:]) or "No matching memories."
        except Exception as e:
            return f"[recall error: {e}]"

    tools['remember'] = {'fn': _remember_tool, 'description': 'Save a fact to persistent memory', 'params': {'fact': 'fact to remember'}}
    tools['recall'] = {'fn': _recall_tool, 'description': 'Recall stored memories, optionally filtered by query', 'params': {'query': 'optional search string'}}

    # System monitor
    try:
        import psutil

        def _sysinfo(**_):
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return (f"CPU: {cpu}%  RAM: {mem.percent}% ({mem.used//1024//1024}MB/{mem.total//1024//1024}MB)"
                    f"  Disk: {disk.percent}% ({disk.used//1024//1024//1024}GB/{disk.total//1024//1024//1024}GB)")

        def _list_processes(filter_name: str = '', **_):
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    info = p.info
                    if not filter_name or filter_name.lower() in info['name'].lower():
                        procs.append(f"PID {info['pid']:>6}  {info['name']}")
                except Exception:
                    pass
            return '\n'.join(procs[:30]) or 'No processes found'

        tools['system_info'] = {'fn': _sysinfo, 'description': 'Get system CPU/RAM/disk usage', 'params': {}}
        tools['list_processes'] = {'fn': _list_processes, 'description': 'List running processes', 'params': {'filter_name': 'optional name filter'}}
    except ImportError:
        pass

    return tools


# ── Memory helpers ─────────────────────────────────────────────────────────────

_MEMORY_FILE = ROOT / '.devin_memories.json'


def _load_memories() -> List[Dict]:
    try:
        if _MEMORY_FILE.exists():
            return json.loads(_MEMORY_FILE.read_text())
    except Exception:
        pass
    return []


def _save_memory(content: str) -> None:
    mems = _load_memories()
    mems.append({'content': content, 'ts': time.strftime('%Y-%m-%d %H:%M')})
    _MEMORY_FILE.write_text(json.dumps(mems, indent=2))


# ── Agentic reasoning loop ─────────────────────────────────────────────────────

def _run_agentic_task(task: str, on_step=None) -> str:
    """Run the full reasoning→tool→verify loop on a task."""
    try:
        from modules.reasoning_engine import get_reasoning_engine
        engine = get_reasoning_engine()

        # Register tools
        tools = _build_agent_tools()
        for name, info in tools.items():
            engine.register_tool(name, info['fn'], info['description'], info.get('params'))

        result = engine.think(task)
        return result.answer
    except Exception as e:
        return f"[Agentic error: {e}]"


# ── DevinREPL ──────────────────────────────────────────────────────────────────

class DevinREPL:
    """Claude Code-style interactive REPL for Devin AGI 4.0."""

    def __init__(self, devin_agi: Optional[Any] = None, provider_name: str = ''):
        self._agi = devin_agi
        self._provider = _select_provider(provider_name)
        self._history: List[Dict[str, str]] = []
        self._voice_mode = os.environ.get('DEVIN_VOICE_MODE') == '1'
        self._running = True
        self._session = None
        self._use_pt = False
        self._setup_input()

    def _setup_input(self) -> None:
        try:
            from prompt_toolkit import PromptSession
            from prompt_toolkit.history import FileHistory
            from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
            from prompt_toolkit.styles import Style
            style = Style.from_dict({'prompt': 'ansicyan bold'})
            self._session = PromptSession(
                history=FileHistory(str(Path.home() / '.devin_history')),
                auto_suggest=AutoSuggestFromHistory(),
                enable_history_search=True,
                style=style,
            )
            self._use_pt = True
        except (ImportError, Exception):
            pass

    def _get_input(self, prompt: str) -> Optional[str]:
        if self._use_pt and self._session:
            try:
                return self._session.prompt(prompt)
            except (KeyboardInterrupt, EOFError):
                return None
        try:
            return input(prompt)
        except (KeyboardInterrupt, EOFError):
            return None

    def _banner(self) -> None:
        w = _cols()
        sep = '─' * max(w - 4, 4)
        print()
        print(_c(CYAN_B, f'  ╭{sep}╮'))
        title = '  Devin AGI v4.0  ·  Autonomous OS-Controlling AI'
        prov  = f'[{self._provider.name}]'
        pad   = w - len(title) - len(prov) - 4
        print(_c(CYAN_B, '  │') + _c(WHITE_B, title) +
              ' ' * max(pad, 1) + _c(GRAY, prov) + _c(CYAN_B, ' │'))
        sub = '  Type /help for commands · /think <task> for agentic mode · Ctrl+D to exit'
        pad2 = w - len(sub) - 4
        print(_c(CYAN_B, '  │') + _c(GRAY, sub) + ' ' * max(pad2, 0) + _c(CYAN_B, '│'))
        print(_c(CYAN_B, f'  ╰{sep}╯'))
        print()

    def _handle_slash(self, line: str) -> bool:
        parts = line.strip().split(None, 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ''

        if cmd in ('/exit', '/q', '/quit'):
            self._running = False
            print(_c(CYAN, '\n  Goodbye.\n'))
            return True

        if cmd == '/help':
            print(_c(CYAN, _SLASH_HELP))
            return True

        if cmd == '/clear':
            os.system('clear' if os.name == 'posix' else 'cls')
            self._history.clear()
            self._banner()
            return True

        if cmd == '/reset':
            self._history.clear()
            print(_c(YELLOW, '  Conversation history cleared.'))
            return True

        if cmd == '/status':
            self._show_status()
            return True

        if cmd == '/tools':
            self._show_tools()
            return True

        if cmd == '/screenshot':
            self._do_screenshot()
            return True

        if cmd == '/memory':
            self._show_memory()
            return True

        if cmd == '/remember':
            if arg:
                try:
                    _save_memory(arg)
                    print(_c(GREEN, f'  ✓ Remembered: {arg}'))
                except Exception as e:
                    print(_c(RED, f'  [Error: {e}]'))
            else:
                print(_c(YELLOW, '  Usage: /remember <fact>'))
            return True

        if cmd == '/repos':
            self._show_repos()
            return True

        if cmd == '/think':
            if arg:
                self._run_task(arg)
            else:
                print(_c(YELLOW, '  Usage: /think <task description>'))
            return True

        if cmd == '/shell':
            if arg:
                self._shell(arg)
            else:
                print(_c(YELLOW, '  Usage: /shell <cmd>'))
            return True

        if cmd == '/git':
            if arg:
                self._shell(f'git {arg}')
            else:
                print(_c(YELLOW, '  Usage: /git <args>'))
            return True

        if cmd == '/mem':
            n = len(self._history)
            chars = sum(len(m.get('content', '')) for m in self._history)
            mems = _load_memories()
            print(_c(GRAY, f'  Conversation: {n} messages, {chars} chars  |  Memories: {len(mems)} facts'))
            return True

        if cmd == '/voice':
            self._voice_mode = not self._voice_mode
            print(_c(YELLOW, f'  Voice mode: {"ON" if self._voice_mode else "OFF"}'))
            return True

        if cmd == '/provider':
            if arg:
                self._provider = _select_provider(arg.strip())
                print(_c(YELLOW, f'  Provider switched to: {self._provider.name}'))
            else:
                print(_c(GRAY, f'  Current provider: {self._provider.name}'))
            return True

        if cmd == '/model':
            if arg:
                env_map = {
                    'gemini': 'GEMINI_MODEL', 'claude': 'CLAUDE_MODEL',
                    'openai': 'OPENAI_MODEL', 'hf': 'HF_MODEL', 'huggingface': 'HF_MODEL',
                }
                k = env_map.get(self._provider.name)
                if k:
                    os.environ[k] = arg.strip()
                    self._provider = _select_provider(self._provider.name)
                    print(_c(YELLOW, f'  Model set to: {arg.strip()}'))
                else:
                    print(_c(YELLOW, f'  Cannot set model for provider: {self._provider.name}'))
            else:
                print(_c(GRAY, '  Usage: /model <model-name>'))
            return True

        if cmd == '/cwd':
            print(_c(GRAY, f'  {os.getcwd()}'))
            return True

        # Unknown slash command
        print(_c(YELLOW, f'  Unknown command: {cmd}  (type /help)'))
        return True

    def _shell(self, cmd: str) -> None:
        print(_c(GRAY, f'  $ {cmd}'))
        try:
            r = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=30)
            for ln in (r.stdout or '').splitlines():
                print(_c(GRAY, f'  {ln}'))
            for ln in (r.stderr or '').splitlines():
                print(_c(RED, f'  {ln}'))
        except subprocess.TimeoutExpired:
            print(_c(RED, '  [timeout]'))
        except Exception as e:
            print(_c(RED, f'  [error: {e}]'))

    def _do_screenshot(self) -> None:
        print(_c(CYAN, '  Taking screenshot…'))
        try:
            from modules.os_agent import get_os_agent
            agent = get_os_agent()
            r = agent.screenshot('Describe the current screen')
            if r.success:
                print(_c(GREEN, f'  ✓ {r.message}'))
                if r.screenshot_before:
                    print(_c(GRAY, f'  Saved: {r.screenshot_before}'))
                if r.vision_result and r.vision_result != '[Vision analysis unavailable — no AI provider configured]':
                    print(_c(GRAY, f'  Screen: {r.vision_result[:200]}'))
            else:
                print(_c(RED, f'  ✗ {r.message}'))
        except Exception as e:
            print(_c(RED, f'  [screenshot error: {e}]'))

    def _show_memory(self) -> None:
        mems = _load_memories()
        if not mems:
            print(_c(GRAY, '  No memories stored. Use /remember <fact> to save one.'))
            return
        print(_c(CYAN, f'\n  Memories ({len(mems)}):'))
        for m in mems[-20:]:
            ts = m.get('ts', '')
            content = m.get('content', '')
            print(_c(GRAY, f'  [{ts}] {content}'))
        print()

    def _show_repos(self) -> None:
        repos_dir = ROOT / 'repos'
        print(_c(CYAN, '\n  Integrated repositories:'))
        if repos_dir.exists():
            for d in sorted(repos_dir.iterdir()):
                if d.is_dir():
                    mark = _c(GREEN, '●') if (d / '.git').exists() or any(d.iterdir()) else _c(GRAY, '○')
                    print(f'  {mark} {d.name}')
        # Also show repos from integration matrix if it exists
        matrix = ROOT / 'docs' / 'INTEGRATION_MATRIX.md'
        if matrix.exists():
            print(_c(GRAY, f'\n  See docs/INTEGRATION_MATRIX.md for full details'))
        print()

    def _run_task(self, task: str) -> None:
        print(_c(MAGENTA, f'\n  ⚙ Agentic mode: {task[:60]}{"…" if len(task) > 60 else ""}'))
        print(_c(CYAN, '  ' + '─' * (_cols() - 4)))
        try:
            result = _run_agentic_task(task, on_step=lambda s: print(_c(GRAY, f'  ↳ {s}')))
            print()
            print(_c(WHITE_B, '  Result:'))
            print(result)
            print()
            self._history.append({'role': 'user', 'content': f'[Task] {task}'})
            self._history.append({'role': 'assistant', 'content': result})
        except Exception as e:
            print(_c(RED, f'\n  [Task error: {e}]'))

    def _show_status(self) -> None:
        print(_c(CYAN, f'\n  Provider: {self._provider.name}  Available: {self._provider.available()}'))

        # Module status from main
        try:
            from main import CAPS, get_devin
            d = get_devin()
            print(_c(CYAN, f'  Modules: {d.loaded_count()}/{d.total_count()} loaded'))
            rows = [
                ('OS Agent',       'os_agent'),
                ('Reasoning',      'reasoning'),
                ('Conversation',   'conversation'),
                ('System Monitor', 'system_monitor'),
                ('Voice Engine',   'voice'),
                ('Browser Agent',  'browser'),
                ('HF Provider',    'hf_provider'),
                ('Free Claude',    'free_claude'),
            ]
            for label, attr in rows:
                obj = getattr(CAPS, attr, None)
                mark = _c(GREEN, '●') + ' ready' if obj else _c(GRAY, '○') + ' not loaded'
                print(f'  {label:<22} {mark}')
        except Exception as e:
            print(_c(YELLOW, f'  Module status unavailable: {e}'))

        # System info
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.3)
            mem = psutil.virtual_memory()
            print(_c(GRAY, f'\n  CPU: {cpu}%  RAM: {mem.percent}% ({mem.used//1024//1024}MB used)'))
        except ImportError:
            pass

        # Memory
        mems = _load_memories()
        print(_c(GRAY, f'  Memories: {len(mems)}  Conversation: {len(self._history)} messages'))
        print()

    def _show_tools(self) -> None:
        tools = _build_agent_tools()
        print(_c(CYAN, f'\n  Available tools ({len(tools)}):'))
        for name, info in sorted(tools.items()):
            desc = info.get('description', '')[:55]
            params = ', '.join(info.get('params', {}).keys())
            print(_c(GRAY, f'  ⏺ {name:<26} {desc}'))
            if params:
                print(_c(GRAY, f'    {"params:":<24} {params}'))
        print()

    def _stream_response(self, user_text: str) -> str:
        self._history.append({'role': 'user', 'content': user_text})
        messages = self._history[-30:]
        full = ''
        print()
        print(_c(CYAN_B, '  Devin'))
        print(_c(CYAN, '  ' + '─' * max(_cols() - 4, 4)))
        try:
            for chunk in self._provider.stream(messages, _SYSTEM):
                full += chunk
                print(chunk, end='', flush=True)
        except Exception as e:
            print(_c(RED, f'\n  [Error: {e}]'))
            full = str(e)
        print('\n')
        if full:
            self._history.append({'role': 'assistant', 'content': full})
        if self._voice_mode and full:
            try:
                from main import CAPS
                if CAPS.voice and hasattr(CAPS.voice, 'speak'):
                    CAPS.voice.speak(full[:400])
            except Exception:
                pass
        return full

    def run(self) -> None:
        self._banner()
        prompt = '  > '
        while self._running:
            try:
                if self._voice_mode:
                    try:
                        from main import CAPS
                        if CAPS.voice and hasattr(CAPS.voice, 'listen_once'):
                            print(_c(GRAY, '  [Listening…]'))
                            text = CAPS.voice.listen_once()
                            if text:
                                print(_c(WHITE_B, f'  You: {text}'))
                                self._stream_response(text)
                                continue
                    except Exception:
                        pass
                line = self._get_input(prompt)
                if line is None:
                    print()
                    break
                line = line.strip()
                if not line:
                    continue
                if line.startswith('/'):
                    self._handle_slash(line)
                    continue
                self._stream_response(line)
            except KeyboardInterrupt:
                print(_c(YELLOW, '\n  (Ctrl+D or /exit to quit)'))
            except Exception as e:
                print(_c(RED, f'\n  [REPL error: {e}]'))
        print(_c(GRAY, '  Session ended.\n'))


# ── Public API ─────────────────────────────────────────────────────────────────

_repl: Optional[DevinREPL] = None


def get_repl(devin_agi: Optional[Any] = None) -> DevinREPL:
    global _repl
    if _repl is None:
        _repl = DevinREPL(devin_agi=devin_agi)
    return _repl


def start_repl(devin_agi: Optional[Any] = None) -> None:
    """Start the Devin REPL. Called by main.py."""
    get_repl(devin_agi).run()


if __name__ == '__main__':
    start_repl()
