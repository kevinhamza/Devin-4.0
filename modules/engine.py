"""
modules/engine.py — Devin AGI Core Engine.

Unified reasoning + tool execution engine.
- Uses Gemini API for LLM reasoning (with fallback model chain)
- Executes all OS, web, file, shell, security, voice tools
- Persistent JSON memory
- Integrates all external repos via repo_tools.py
- Full mouse/keyboard automation via os_automation.py
"""

import os
import sys
import json
import time
import subprocess
import threading
import tempfile
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any

ROOT = Path(__file__).parent.parent

# ── Gemini API ────────────────────────────────────────────────────────────────

try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False
    genai = None

GEMINI_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-2.0-flash',
    'gemini-1.5-flash',
    'gemini-1.5-flash-8b',
    'gemini-1.5-pro',
]

# ── OS automation ─────────────────────────────────────────────────────────────

_AUTOMATION_SCRIPT = ROOT / 'modules' / 'os_automation.py'
_VENV_PY = ROOT / 'venv' / 'bin' / 'python3'
_PYTHON = str(_VENV_PY) if _VENV_PY.exists() else 'python3'


def _run_automation(action: str, args: dict = None, timeout: int = 15) -> dict:
    """Call os_automation.py subprocess."""
    payload = json.dumps({'action': action, 'args': args or {}})
    try:
        env = dict(os.environ)
        if platform.system() == 'Linux' and not env.get('DISPLAY'):
            env['DISPLAY'] = ':0'
        out = subprocess.check_output(
            [_PYTHON, str(_AUTOMATION_SCRIPT), payload],
            timeout=timeout, env=env,
            stderr=subprocess.STDOUT
        )
        return json.loads(out.decode().strip())
    except subprocess.TimeoutExpired:
        return {'ok': False, 'error': f'Timeout after {timeout}s'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


# ── Memory ────────────────────────────────────────────────────────────────────

class Memory:
    def __init__(self, path: str = None):
        self.path = path or str(ROOT / 'data' / 'memory.json')
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._data: List[dict] = []
        self._load()

    def _load(self):
        try:
            with open(self.path) as f:
                self._data = json.load(f)
        except Exception:
            self._data = []

    def _save(self):
        try:
            with open(self.path, 'w') as f:
                json.dump(self._data[-500:], f, indent=2)
        except Exception:
            pass

    def add(self, role: str, content: str):
        self._data.append({
            'role': role,
            'content': content,
            'ts': time.time(),
        })
        self._save()

    def recent(self, n: int = 20) -> List[dict]:
        return self._data[-n:]

    def search(self, query: str, n: int = 5) -> List[dict]:
        q = query.lower()
        matches = [m for m in self._data if q in m.get('content', '').lower()]
        return matches[-n:]

    def clear(self):
        self._data = []
        self._save()


# ── Tool implementations ───────────────────────────────────────────────────────

def _tool_screenshot(args: dict) -> str:
    r = _run_automation('screenshot', args, timeout=12)
    return r.get('result', r.get('error', 'Screenshot failed'))


def _tool_mouse_click(args: dict) -> str:
    r = _run_automation('mouse_click', {'x': args['x'], 'y': args['y'],
                                         'button': args.get('button', 'left'),
                                         'double': args.get('double', False)})
    return r.get('result', r.get('error', 'Click failed'))


def _tool_mouse_move(args: dict) -> str:
    r = _run_automation('mouse_move', {'x': args['x'], 'y': args['y']})
    return r.get('result', r.get('error', 'Move failed'))


def _tool_type(args: dict) -> str:
    r = _run_automation('type', {'text': args['text'],
                                  'human_like': args.get('human_like', True)})
    return r.get('result', r.get('error', 'Type failed'))


def _tool_hotkey(args: dict) -> str:
    r = _run_automation('hotkey', {'keys': args['keys']})
    return r.get('result', r.get('error', 'Hotkey failed'))


def _tool_press(args: dict) -> str:
    r = _run_automation('press', {'key': args['key']})
    return r.get('result', r.get('error', 'Press failed'))


def _tool_open_app(args: dict) -> str:
    r = _run_automation('open_app', {'name': args['name'], 'args': args.get('args')}, timeout=10)
    return r.get('result', r.get('error', 'Open app failed'))


def _tool_open_url(args: dict) -> str:
    r = _run_automation('open_url', {'url': args['url']}, timeout=10)
    return r.get('result', r.get('error', 'Open URL failed'))


def _tool_shell(args: dict) -> str:
    cmd = args.get('command', '')
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return (result.stdout + result.stderr).strip() or f'(exit {result.returncode})'
    except subprocess.TimeoutExpired:
        return 'Command timed out after 30s'
    except Exception as e:
        return f'Shell error: {e}'


def _tool_read_file(args: dict) -> str:
    try:
        path = args['path']
        with open(path) as f:
            return f.read()[:5000]
    except Exception as e:
        return f'Read error: {e}'


def _tool_write_file(args: dict) -> str:
    try:
        path = args['path']
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w') as f:
            f.write(args['content'])
        return f'Written: {path}'
    except Exception as e:
        return f'Write error: {e}'


def _tool_list_files(args: dict) -> str:
    try:
        path = args.get('path', '.')
        entries = os.listdir(path)
        return '\n'.join(sorted(entries)[:100])
    except Exception as e:
        return f'List error: {e}'


def _tool_web_search(args: dict) -> str:
    query = args.get('query', '')
    try:
        import requests
        r = requests.get(
            'https://api.duckduckgo.com/',
            params={'q': query, 'format': 'json', 'no_redirect': 1},
            timeout=10
        )
        data = r.json()
        abstract = data.get('AbstractText', '')
        related = [t.get('Text', '') for t in data.get('RelatedTopics', [])[:5]]
        return (abstract + '\n' + '\n'.join(related)).strip() or f'Search: {query} (no results)'
    except Exception as e:
        return f'Search error: {e}'


def _tool_web_fetch(args: dict) -> str:
    url = args.get('url', '')
    try:
        import requests
        r = requests.get(url, timeout=15, headers={'User-Agent': 'DevinAGI/4.0'})
        text = r.text[:4000]
        # Strip HTML tags minimally
        import re
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        return f'Fetch error: {e}'


def _tool_browser_search(args: dict) -> str:
    """Open browser and search using selenium."""
    try:
        sys.path.insert(0, str(ROOT))
        from modules.browser import BrowserAutomation
        with BrowserAutomation(headless=False) as br:
            br.start()
            return br.search_google(args.get('query', ''))
    except Exception as e:
        return _tool_open_url({'url': f"https://google.com/search?q={args.get('query','')}"})


def _tool_system_info(args: dict) -> str:
    r = _run_automation('system_info', {}, timeout=10)
    return str(r.get('result', r.get('error', '')))


def _tool_list_windows(args: dict) -> str:
    r = _run_automation('list_windows', {})
    return str(r.get('result', r.get('error', '')))


def _tool_focus_window(args: dict) -> str:
    r = _run_automation('focus_window', {'name': args['name']})
    return str(r.get('result', r.get('error', '')))


def _tool_scroll(args: dict) -> str:
    r = _run_automation('mouse_scroll', {
        'x': args.get('x', 683), 'y': args.get('y', 400),
        'direction': args.get('direction', 'down'),
        'amount': args.get('amount', 3),
    })
    return str(r.get('result', r.get('error', '')))


def _tool_clipboard_get(args: dict) -> str:
    r = _run_automation('clipboard_get', {})
    return str(r.get('result', r.get('error', '')))


def _tool_clipboard_set(args: dict) -> str:
    r = _run_automation('clipboard_set', {'text': args['text']})
    return str(r.get('result', r.get('error', '')))


def _tool_speak(args: dict) -> str:
    sys.path.insert(0, str(ROOT))
    from modules.voice import speak
    ok = speak(args.get('text', ''))
    return 'Spoken' if ok else 'TTS unavailable'


def _tool_listen(args: dict) -> str:
    sys.path.insert(0, str(ROOT))
    from modules.voice import listen
    return listen(timeout=args.get('timeout', 8)) or '(no speech detected)'


def _tool_aia_weather(args: dict) -> str:
    from modules.repo_tools import AIAInternetTasks
    return AIAInternetTasks.get_weather(args.get('location', 'London'))


def _tool_run_python(args: dict) -> str:
    code = args.get('code', '')
    try:
        buf = {}
        exec(compile(code, '<devin>', 'exec'), buf)  # nosec
        return str(buf.get('_result', '(executed)'))
    except Exception as e:
        return f'Python error: {e}'


def _tool_soc_click(args: dict) -> str:
    from modules.repo_tools import SelfOperatingComputer
    ok = SelfOperatingComputer.click_at_percentage(args['x'], args['y'])
    return 'Clicked' if ok else 'SOC click failed'


def _tool_nmap_scan(args: dict) -> str:
    from modules.repo_tools import SecurityTools
    return SecurityTools.nmap_scan(args['target'], args.get('options', '-sV'))


def _tool_drag(args: dict) -> str:
    r = _run_automation('mouse_drag', {
        'x1': args['x1'], 'y1': args['y1'],
        'x2': args['x2'], 'y2': args['y2'],
        'duration': args.get('duration', 0.5),
    })
    return str(r.get('result', r.get('error', '')))


def _tool_volume(args: dict) -> str:
    action = args.get('action', 'up')
    if action == 'set':
        r = _run_automation('volume_set', {'level': args.get('level', 50)})
    elif action == 'mute':
        r = _run_automation('volume_mute', {})
    elif action == 'down':
        r = _run_automation('volume_down', {'steps': args.get('steps', 5)})
    else:
        r = _run_automation('volume_up', {'steps': args.get('steps', 5)})
    return str(r.get('result', r.get('error', '')))


# ── Tool registry ─────────────────────────────────────────────────────────────

TOOLS: Dict[str, dict] = {
    'take_screenshot': {
        'fn': _tool_screenshot,
        'desc': 'Take a screenshot of the current screen. Returns path.',
        'params': {'path': 'optional save path', 'region': 'optional [x,y,w,h]'},
    },
    'mouse_click': {
        'fn': _tool_mouse_click,
        'desc': 'Click mouse at (x, y). button: left/right/middle. double: true/false.',
        'params': {'x': 'int', 'y': 'int', 'button': 'str', 'double': 'bool'},
    },
    'mouse_move': {
        'fn': _tool_mouse_move,
        'desc': 'Move mouse cursor to (x, y).',
        'params': {'x': 'int', 'y': 'int'},
    },
    'mouse_drag': {
        'fn': _tool_drag,
        'desc': 'Drag from (x1,y1) to (x2,y2).',
        'params': {'x1': 'int', 'y1': 'int', 'x2': 'int', 'y2': 'int'},
    },
    'mouse_scroll': {
        'fn': _tool_scroll,
        'desc': 'Scroll at position. direction: up/down.',
        'params': {'x': 'int', 'y': 'int', 'direction': 'str', 'amount': 'int'},
    },
    'keyboard_type': {
        'fn': _tool_type,
        'desc': 'Type text as if keyboard input.',
        'params': {'text': 'str', 'human_like': 'bool'},
    },
    'keyboard_hotkey': {
        'fn': _tool_hotkey,
        'desc': 'Press a key combination. e.g. ["ctrl","c"]',
        'params': {'keys': 'list[str]'},
    },
    'keyboard_press': {
        'fn': _tool_press,
        'desc': 'Press a single key. e.g. Return, Tab, Escape, F5.',
        'params': {'key': 'str'},
    },
    'open_application': {
        'fn': _tool_open_app,
        'desc': 'Open an application by name.',
        'params': {'name': 'str', 'args': 'optional str'},
    },
    'open_url': {
        'fn': _tool_open_url,
        'desc': 'Open URL in default browser.',
        'params': {'url': 'str'},
    },
    'browser_search': {
        'fn': _tool_browser_search,
        'desc': 'Open browser and search Google using Selenium.',
        'params': {'query': 'str'},
    },
    'execute_shell': {
        'fn': _tool_shell,
        'desc': 'Run a shell command and return output.',
        'params': {'command': 'str'},
    },
    'read_file': {
        'fn': _tool_read_file,
        'desc': 'Read a file and return its contents.',
        'params': {'path': 'str'},
    },
    'write_file': {
        'fn': _tool_write_file,
        'desc': 'Write content to a file.',
        'params': {'path': 'str', 'content': 'str'},
    },
    'list_files': {
        'fn': _tool_list_files,
        'desc': 'List files in a directory.',
        'params': {'path': 'optional str'},
    },
    'web_search': {
        'fn': _tool_web_search,
        'desc': 'Search the web using DuckDuckGo.',
        'params': {'query': 'str'},
    },
    'web_fetch': {
        'fn': _tool_web_fetch,
        'desc': 'Fetch and return text content from a URL.',
        'params': {'url': 'str'},
    },
    'system_info': {
        'fn': _tool_system_info,
        'desc': 'Get CPU, RAM, disk, OS information.',
        'params': {},
    },
    'list_windows': {
        'fn': _tool_list_windows,
        'desc': 'List all open windows on the desktop.',
        'params': {},
    },
    'focus_window': {
        'fn': _tool_focus_window,
        'desc': 'Focus a window by name.',
        'params': {'name': 'str'},
    },
    'clipboard_get': {
        'fn': _tool_clipboard_get,
        'desc': 'Get clipboard contents.',
        'params': {},
    },
    'clipboard_set': {
        'fn': _tool_clipboard_set,
        'desc': 'Set clipboard contents.',
        'params': {'text': 'str'},
    },
    'speak': {
        'fn': _tool_speak,
        'desc': 'Speak text aloud using TTS.',
        'params': {'text': 'str'},
    },
    'listen': {
        'fn': _tool_listen,
        'desc': 'Listen for speech and return transcribed text.',
        'params': {'timeout': 'optional int'},
    },
    'get_weather': {
        'fn': _tool_aia_weather,
        'desc': 'Get weather for a location using AIA.',
        'params': {'location': 'str'},
    },
    'run_python': {
        'fn': _tool_run_python,
        'desc': 'Execute Python code. Store result in _result variable.',
        'params': {'code': 'str'},
    },
    'soc_click_pct': {
        'fn': _tool_soc_click,
        'desc': 'Click at screen percentage coordinates (0.0–1.0) using self-operating-computer.',
        'params': {'x': 'float 0-1', 'y': 'float 0-1'},
    },
    'nmap_scan': {
        'fn': _tool_nmap_scan,
        'desc': 'Run nmap port scan on target. Requires authorization.',
        'params': {'target': 'str', 'options': 'optional str'},
    },
    'volume_control': {
        'fn': _tool_volume,
        'desc': 'Control system volume. action: up/down/mute/set. level: 0-100 for set.',
        'params': {'action': 'str', 'steps': 'optional int', 'level': 'optional int'},
    },
}


def _tools_schema() -> str:
    """Compact tool listing for system prompt."""
    lines = []
    for name, info in TOOLS.items():
        params = ', '.join(f'{k}: {v}' for k, v in info.get('params', {}).items())
        lines.append(f'- {name}({params}): {info["desc"]}')
    return '\n'.join(lines)


# ── Gemini LLM ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are Devin, a super-intelligent AGI assistant with full control of this computer.
You can see the screen, control the mouse and keyboard, open apps, search the web, write code,
manage files, and do anything a power user or senior engineer can do.

## Available tools (call via JSON):
{_tools_schema()}

## How to call a tool:
Respond with a JSON block anywhere in your reply:
```json
{{"tool": "tool_name", "args": {{"key": "value"}}}}
```
You can call multiple tools in sequence. After each tool result, continue reasoning.

## Rules:
1. Always take_screenshot first before clicking GUI elements.
2. Complete tasks end-to-end. Do not stop after one step.
3. After opening an app, wait ~1.5s then screenshot to confirm.
4. For typing: use keyboard_type after clicking the target field.
5. NEVER output tool calls as plain text [Tool: ...] — use the JSON format above.
6. Be concise in text. Do the work, don't just describe it.
7. Security tools require explicit user authorization.
"""


class DevinEngine:
    """
    Core AGI engine: LLM reasoning + tool execution + memory.
    """

    def __init__(self, api_key: str = None, verbose: bool = False):
        self.api_key = api_key or GEMINI_KEY
        self.verbose = verbose
        self.memory = Memory()
        self._model = None
        self._model_name = None
        self._setup_gemini()

    def _setup_gemini(self):
        if not _GENAI_AVAILABLE:
            return
        try:
            genai.configure(api_key=self.api_key)
            for m in GEMINI_MODELS:
                try:
                    self._model = genai.GenerativeModel(
                        model_name=m,
                        system_instruction=SYSTEM_PROMPT,
                        generation_config={'max_output_tokens': 8192, 'temperature': 0.3},
                    )
                    self._model_name = m
                    break
                except Exception:
                    continue
        except Exception as e:
            if self.verbose:
                print(f'Gemini setup error: {e}')

    def _call_llm(self, messages: list) -> str:
        """Call Gemini with retry across models."""
        if not self._model:
            return 'LLM not available — check GEMINI_API_KEY'

        history = []
        for m in messages:
            role = 'model' if m['role'] == 'assistant' else 'user'
            history.append({'role': role, 'parts': [m['content']]})

        if not history or history[-1]['role'] != 'user':
            return '(nothing to respond to)'

        last_user = history[-1]
        prior = history[:-1]

        for attempt, model_name in enumerate(GEMINI_MODELS):
            try:
                if attempt > 0:
                    self._model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=SYSTEM_PROMPT,
                        generation_config={'max_output_tokens': 8192, 'temperature': 0.3},
                    )
                chat = self._model.start_chat(history=prior)
                resp = chat.send_message(last_user['parts'][0])
                return resp.text
            except Exception as e:
                err = str(e).lower()
                if any(x in err for x in ['429', 'quota', 'rate', '503', 'unavailable']):
                    time.sleep(1.5 * (attempt + 1))
                    continue
                break
        return 'LLM error — all models exhausted'

    def _extract_tool_calls(self, text: str) -> List[dict]:
        """Extract ```json {...} ``` tool call blocks from LLM text."""
        import re
        calls = []
        # Match ```json ... ``` blocks
        for m in re.finditer(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL):
            try:
                obj = json.loads(m.group(1))
                if 'tool' in obj:
                    calls.append(obj)
            except Exception:
                pass
        # Also match bare {"tool": ...} patterns
        if not calls:
            for m in re.finditer(r'\{[^{}]*"tool"\s*:[^{}]*\}', text, re.DOTALL):
                try:
                    obj = json.loads(m.group(0))
                    if 'tool' in obj:
                        calls.append(obj)
                except Exception:
                    pass
        return calls

    def _execute_tool(self, tool_name: str, args: dict) -> str:
        """Execute a named tool and return string result."""
        info = TOOLS.get(tool_name)
        if not info:
            return f'Unknown tool: {tool_name}'
        try:
            return str(info['fn'](args))
        except Exception as e:
            return f'Tool error ({tool_name}): {e}'

    def run(self, user_input: str, max_steps: int = 25) -> str:
        """
        Full agentic loop: reason → act → observe → repeat.
        Returns the final text response.
        """
        self.memory.add('user', user_input)

        # Build conversation context from recent memory
        messages = []
        for m in self.memory.recent(30):
            messages.append({'role': m['role'], 'content': m['content']})

        step = 0
        last_text = ''
        tool_loop_guard: Dict[str, int] = {}

        while step < max_steps:
            step += 1
            response_text = self._call_llm(messages)
            last_text = response_text

            # Extract tool calls
            calls = self._extract_tool_calls(response_text)

            # Print thinking text (stripped of JSON blocks)
            import re
            display_text = re.sub(r'```(?:json)?\s*\{.*?\}\s*```', '', response_text, flags=re.DOTALL).strip()
            if display_text:
                yield ('text', display_text)

            if not calls:
                # No tools — final response
                self.memory.add('assistant', response_text)
                break

            # Execute tools
            tool_results = []
            for call in calls:
                tool_name = call.get('tool', '')
                args = call.get('args', {})

                # Loop guard
                sig = f'{tool_name}:{json.dumps(args, sort_keys=True)}'
                tool_loop_guard[sig] = tool_loop_guard.get(sig, 0) + 1
                if tool_loop_guard[sig] >= 3:
                    yield ('warning', f'Loop detected: {tool_name} repeating. Stopping.')
                    return

                yield ('tool_call', tool_name, args)
                result = self._execute_tool(tool_name, args)
                yield ('tool_result', result)
                tool_results.append(f'[{tool_name}] → {result}')

            # Add assistant turn + tool results to conversation
            messages.append({'role': 'assistant', 'content': response_text})
            messages.append({'role': 'user', 'content': 'Tool results:\n' + '\n'.join(tool_results)})
            self.memory.add('assistant', response_text)
            self.memory.add('user', 'Tool results:\n' + '\n'.join(tool_results))

        yield ('done', last_text)
