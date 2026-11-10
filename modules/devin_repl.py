#!/usr/bin/env python3
"""
Devin AGI 4.0 — Grok-style CLI with Agentic Tool Execution

All credentials via .env / environment variables only.
Never hardcode API keys.
"""
from __future__ import annotations
import os, sys, shutil, signal, subprocess, threading, time, json, re
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator, Tuple

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
    return shutil.get_terminal_size((120, 24)).columns

def _rows() -> int:
    return shutil.get_terminal_size((120, 24)).lines

_IS_TTY = sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    if not _IS_TTY:
        return text
    return f'\033[{code}m{text}\033[0m'

def _bg(code: str, text: str) -> str:
    if not _IS_TTY:
        return text
    return f'\033[{code}m{text}\033[0m'

# ANSI codes
CYAN_B  = '36;1'
CYAN    = '36'
WHITE_B = '37;1'
GRAY    = '2'
GRAY_B  = '90'
YELLOW  = '33'
GREEN   = '32'
RED     = '31'
MAGENTA = '35'
BLUE    = '34;1'
DIM     = '2'
BOLD    = '1'

# Background colors
BG_DARK  = '48;5;236'   # dark gray bg for user msg
BG_BLACK = '48;5;232'
BG_TOOL  = '48;5;234'   # slightly lighter for tool blocks

def _now_hhmm() -> str:
    return time.strftime('%I:%M %p').lstrip('0')

def _elapsed(start: float) -> str:
    s = time.time() - start
    if s < 60:
        return f'{s:.1f}s'
    return f'{int(s//60)}m {int(s%60)}s'

def _hr(w: int, char: str = '─') -> str:
    return char * max(w, 1)

def _tok_estimate(messages: List[Dict]) -> int:
    total = sum(len(m.get('content', '')) for m in messages)
    return total // 4  # rough chars-to-tokens


# ── AI Provider wrappers ───────────────────────────────────────────────────────

def _tools_to_openai_schema(tools: Dict) -> List[Dict]:
    """Convert devin tool registry to OpenAI-compatible function schema."""
    result = []
    for name, info in tools.items():
        props = {}
        for pname, pdesc in info.get('params', {}).items():
            props[pname] = {'type': 'string', 'description': str(pdesc)}
        result.append({
            'type': 'function',
            'function': {
                'name': name,
                'description': info.get('desc', ''),
                'parameters': {
                    'type': 'object',
                    'properties': props,
                    'required': list(props.keys()),
                },
            },
        })
    return result


def _tools_to_anthropic_schema(tools: Dict) -> List[Dict]:
    """Convert devin tool registry to Anthropic tool schema."""
    result = []
    for name, info in tools.items():
        props = {}
        for pname, pdesc in info.get('params', {}).items():
            props[pname] = {'type': 'string', 'description': str(pdesc)}
        result.append({
            'name': name,
            'description': info.get('desc', ''),
            'input_schema': {
                'type': 'object',
                'properties': props,
                'required': list(props.keys()),
            },
        })
    return result


class _BaseProvider:
    name = 'none'

    def available(self) -> bool:
        return False

    def stream(self, messages: List[Dict], system: str = '') -> Generator[str, None, None]:
        yield '[No provider available — set API key in .env]'

    def complete(self, messages: List[Dict], system: str = '') -> str:
        return ''.join(self.stream(messages, system))

    def call_with_tools(
        self, messages: List[Dict], tools: Dict, system: str = ''
    ) -> Dict:
        """
        Single LLM call with tool definitions. Returns:
          {"content": str, "tool_calls": [{"name": str, "arguments": dict}]}
        Default implementation uses streaming + ReAct text parsing (no native tool calls).
        Subclasses override for native tool calling.
        """
        full = self.complete(messages, system)
        action_name, inputs, _ = _parse_action(full)
        final_m = _FINAL_RE.search(full)
        if final_m:
            return {'content': final_m.group(1).strip(), 'tool_calls': []}
        if action_name:
            return {'content': '', 'tool_calls': [{'name': action_name, 'arguments': inputs or {}}]}
        return {'content': full.strip(), 'tool_calls': []}


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

    def call_with_tools(self, messages: List[Dict], tools: Dict, system: str = '') -> Dict:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self._key)
            anth_tools = _tools_to_anthropic_schema(tools)
            resp = client.messages.create(
                model=self._model, max_tokens=4096,
                system=system or 'You are Devin, an autonomous AI assistant.',
                messages=messages,
                tools=anth_tools,
            )
            content_text = ''
            tool_calls = []
            for block in resp.content:
                if hasattr(block, 'text'):
                    content_text += block.text
                elif getattr(block, 'type', '') == 'tool_use':
                    tool_calls.append({'name': block.name, 'arguments': block.input or {}})
            return {'content': content_text, 'tool_calls': tool_calls}
        except Exception as e:
            return {'content': f'[Claude tool call error: {e}]', 'tool_calls': []}


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

    def call_with_tools(self, messages: List[Dict], tools: Dict, system: str = '') -> Dict:
        try:
            import openai
            client = openai.OpenAI(api_key=self._key)
            all_msgs = ([{'role': 'system', 'content': system}] + messages) if system else messages
            oai_tools = _tools_to_openai_schema(tools)
            resp = client.chat.completions.create(
                model=self._model, messages=all_msgs,
                tools=oai_tools, tool_choice='auto',
            )
            msg = resp.choices[0].message
            tool_calls = []
            for tc in (msg.tool_calls or []):
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                tool_calls.append({'name': tc.function.name, 'arguments': args})
            return {'content': msg.content or '', 'tool_calls': tool_calls}
        except Exception as e:
            return {'content': f'[OpenAI tool call error: {e}]', 'tool_calls': []}


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
            from modules.hf_enhanced_provider import stream_chat as hf_stream
            all_msgs = ([{'role': 'system', 'content': system}] + messages) if system else messages
            model = self._model or _HF_MODELS[0]
            for chunk in hf_stream(all_msgs, model=model):
                yield chunk
            return
        except (ImportError, Exception):
            pass

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
                return
            except Exception:
                continue

        yield '[HuggingFace: all models unavailable. Check HF_TOKEN in .env]'


class _FCCProvider(_BaseProvider):
    name = 'free_claude'

    def __init__(self):
        self._base = (os.environ.get('FCC_BASE_URL') or '').rstrip('/')
        self._model = os.environ.get('FCC_MODEL', 'anthropic/open_router/qwen/qwen3-235b-a22b')

    def available(self) -> bool:
        return bool(self._base)

    def stream(self, messages: List[Dict], system: str = '') -> Generator[str, None, None]:
        import urllib.request as _ur
        import json as _json

        anth_msgs = [m for m in messages if m.get('role') != 'system']
        if not anth_msgs:
            anth_msgs = [{'role': 'user', 'content': ''}]

        body: Dict = {
            'model': self._model,
            'messages': anth_msgs,
            'max_tokens': 4096,
        }
        if system:
            body['system'] = system

        payload = _json.dumps(body).encode()
        try:
            req = _ur.Request(
                f'{self._base}/v1/messages',
                data=payload,
                headers={'Content-Type': 'application/json', 'anthropic-version': '2023-06-01'},
            )
            with _ur.urlopen(req, timeout=120) as resp:
                data = _json.loads(resp.read())
                for block in data.get('content', []):
                    if block.get('type') == 'text':
                        yield block.get('text', '')
        except Exception as e:
            yield f'[FCC server error: {e}]'


class _FreeClaudeSubprocProvider(_BaseProvider):
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


class _OllamaProvider(_BaseProvider):
    """Local Ollama LLM provider — no API key, fully offline."""
    name = 'ollama'

    def __init__(self):
        self._base = (os.environ.get('OLLAMA_BASE_URL') or 'http://localhost:11434').rstrip('/')
        self._model = os.environ.get('OLLAMA_MODEL') or 'qwen2.5:0.5b'

    def available(self) -> bool:
        try:
            import urllib.request as _ur
            with _ur.urlopen(f'{self._base}/api/tags', timeout=3) as r:
                data = json.loads(r.read())
                return bool(data.get('models'))
        except Exception:
            return False

    def _best_model(self) -> str:
        try:
            from modules.ollama_provider import _best_model as _bm
            return _bm()
        except Exception:
            return self._model

    def stream(self, messages: List[Dict], system: str = '') -> Generator[str, None, None]:
        try:
            from modules.ollama_provider import stream_chat
            for chunk in stream_chat(messages, system_prompt=system, model=self._best_model()):
                yield chunk
        except Exception as e:
            yield f'[Ollama error: {e}]'

    def call_with_tools(self, messages: List[Dict], tools: Dict, system: str = '') -> Dict:
        try:
            from modules.ollama_provider import chat_with_tools
            return chat_with_tools(messages, tools, system_prompt=system, model=self._best_model())
        except Exception as e:
            return {'content': f'[Ollama tool error: {e}]', 'tool_calls': []}


def _select_provider(forced: str = '') -> _BaseProvider:
    fcc = _FCCProvider()
    fcc_sub = _FreeClaudeSubprocProvider()
    ollama = _OllamaProvider()
    candidates = {
        'ollama': ollama,
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
        # Named provider not available — fall through to auto-select
    # Auto-select priority: Ollama (local) > Claude > Gemini > OpenAI > HF > FCC
    for p in [
        ollama,
        candidates['claude'],
        candidates['gemini'],
        candidates['openai'],
        candidates['hf'],
        fcc,
        fcc_sub,
    ]:
        if p.available():
            return p
    return ollama  # return Ollama even if unavailable — gives helpful error msg


# ── Tool registry ──────────────────────────────────────────────────────────────

def _build_agent_tools() -> Dict[str, Dict]:
    tools: Dict[str, Dict] = {}

    # OS/browser tools
    try:
        from modules.os_agent import get_os_agent
        agent = get_os_agent()

        def _screenshot_tool(**_):
            r = agent.screenshot('Describe the current screen state in detail')
            return f"Screenshot: {r.message}\nVision: {r.vision_result or 'no vision'}"

        def _click_tool(x: int = 0, y: int = 0, button: str = 'left', **_):
            r = agent.click(int(x), int(y), button)
            return f"Click at ({x},{y}): {'OK' if r.success else r.message}"

        def _type_text_tool(text: str = '', **_):
            r = agent.type_text(str(text))
            return f"Typed: {'OK' if r.success else r.message}"

        def _press_key_tool(key: str = '', **_):
            r = agent.press_key(str(key))
            return f"Key '{key}': {'OK' if r.success else r.message}"

        def _hotkey_tool(keys: str = '', **_):
            r = agent.hotkey(*str(keys).split('+'))
            return f"Hotkey '{keys}': {'OK' if r.success else r.message}"

        def _open_app_tool(name: str = '', **_):
            r = agent.open_application(str(name))
            return f"Open '{name}': {'OK — pid=' + str(r.data.get('pid','?')) if r.success else r.message}"

        def _navigate_tool(url: str = '', **_):
            r = agent.navigate_browser(str(url))
            return f"Navigate to '{url}': {'OK' if r.success else r.message}"

        def _browser_search_tool(query: str = '', **_):
            r = agent.browser_search(str(query))
            return f"Browser search '{query}': {'OK' if r.success else r.message}"

        def _click_element_tool(description: str = '', **_):
            r = agent.click_element(str(description))
            return f"Click '{description}': {'OK' if r.success else r.message}"

        def _observe_tool(**_):
            return agent.observe()

        tools['screenshot']     = {'fn': _screenshot_tool,  'desc': 'Take a screenshot and describe current screen', 'params': {}}
        tools['click']          = {'fn': _click_tool,        'desc': 'Click at pixel (x,y)', 'params': {'x': 'int', 'y': 'int', 'button': 'left|right|middle'}}
        tools['type_text']      = {'fn': _type_text_tool,    'desc': 'Type text via keyboard', 'params': {'text': 'string to type'}}
        tools['press_key']      = {'fn': _press_key_tool,    'desc': 'Press a key e.g. Return, Tab, Escape', 'params': {'key': 'key name'}}
        tools['hotkey']         = {'fn': _hotkey_tool,       'desc': 'Press hotkey combo e.g. ctrl+c', 'params': {'keys': 'e.g. ctrl+c'}}
        tools['open_app']       = {'fn': _open_app_tool,     'desc': 'Launch an application by name', 'params': {'name': 'app name'}}
        tools['navigate_browser']= {'fn': _navigate_tool,   'desc': 'Navigate browser to URL', 'params': {'url': 'URL'}}
        tools['browser_search'] = {'fn': _browser_search_tool, 'desc': 'Search for query in browser', 'params': {'query': 'search query'}}
        tools['click_element']  = {'fn': _click_element_tool,'desc': 'Click UI element by description', 'params': {'description': 'e.g. address bar'}}
        tools['observe_screen'] = {'fn': _observe_tool,      'desc': 'Observe current screen state', 'params': {}}
    except Exception:
        pass

    # Shell
    def _shell_tool(cmd: str = '', timeout: int = 30, **_):
        try:
            r = subprocess.run(str(cmd), shell=True, capture_output=True, text=True, timeout=int(timeout))
            out = (r.stdout or '')[:3000]
            err = (r.stderr or '')[:800]
            result = f"$ {cmd}\n{out}"
            if err:
                result += f"\nSTDERR: {err}"
            return result
        except subprocess.TimeoutExpired:
            return f"[timeout after {timeout}s: {cmd}]"
        except Exception as e:
            return f"[shell error: {e}]"

    def _read_file_tool(path: str = '', **_):
        try:
            p = Path(str(path))
            if not p.exists():
                return f"[file not found: {path}]"
            if p.stat().st_size > 100_000:
                return f"[file too large — use shell_run with head/tail]"
            return p.read_text(errors='replace')[:4000]
        except Exception as e:
            return f"[read error: {e}]"

    def _write_file_tool(path: str = '', content: str = '', **_):
        try:
            p = Path(str(path))
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(str(content))
            return f"Written {len(content)} chars to {path}"
        except Exception as e:
            return f"[write error: {e}]"

    def _list_dir_tool(path: str = '.', **_):
        try:
            p = Path(str(path))
            entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
            lines = []
            for e in entries[:60]:
                mark = '' if e.is_dir() else ''
                lines.append(f"  {mark} {e.name}{'/' if e.is_dir() else ''}")
            return '\n'.join(lines) or '(empty)'
        except Exception as e:
            return f"[list error: {e}]"

    tools['shell_run']  = {'fn': _shell_tool,    'desc': 'Run shell command, return stdout+stderr', 'params': {'cmd': 'command', 'timeout': 'seconds (default 30)'}}
    tools['read_file']  = {'fn': _read_file_tool, 'desc': 'Read file contents', 'params': {'path': 'file path'}}
    tools['write_file'] = {'fn': _write_file_tool,'desc': 'Write content to file', 'params': {'path': 'file path', 'content': 'content'}}
    tools['list_dir']   = {'fn': _list_dir_tool,  'desc': 'List directory contents', 'params': {'path': 'directory path (default .)'}}

    # Memory
    def _remember_tool(fact: str = '', **_):
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

    tools['remember'] = {'fn': _remember_tool, 'desc': 'Save fact to persistent memory', 'params': {'fact': 'fact to remember'}}
    tools['recall']   = {'fn': _recall_tool,   'desc': 'Recall memories, optionally filtered', 'params': {'query': 'search string (optional)'}}

    # System info
    try:
        import psutil

        def _sysinfo_tool(**_):
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return (f"CPU: {cpu}%  RAM: {mem.percent}% ({mem.used//1024//1024}MB/{mem.total//1024//1024}MB)"
                    f"  Disk: {disk.percent}% ({disk.used//1024//1024//1024}GB/{disk.total//1024//1024//1024}GB)")

        def _procs_tool(filter_name: str = '', **_):
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    info = p.info
                    if not filter_name or filter_name.lower() in info['name'].lower():
                        mem_mb = info.get('memory_info').rss // 1024 // 1024 if info.get('memory_info') else 0
                        procs.append(f"PID {info['pid']:>6}  {info['name']:<30}  {mem_mb}MB")
                except Exception:
                    pass
            return '\n'.join(procs[:40]) or 'No processes found'

        def _network_tool(**_):
            stats = psutil.net_io_counters()
            conns = psutil.net_connections()
            listening = [c for c in conns if c.status == 'LISTEN']
            return (f"Bytes sent: {stats.bytes_sent//1024//1024}MB  Recv: {stats.bytes_recv//1024//1024}MB\n"
                    f"Active connections: {len(conns)}  Listening ports: {[c.laddr.port for c in listening[:10]]}")

        tools['system_info']     = {'fn': _sysinfo_tool, 'desc': 'Get CPU/RAM/disk usage', 'params': {}}
        tools['list_processes']  = {'fn': _procs_tool,   'desc': 'List running processes', 'params': {'filter_name': 'optional name filter'}}
        tools['network_status']  = {'fn': _network_tool, 'desc': 'Get network IO and connections', 'params': {}}
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


# ── ReAct system prompt ────────────────────────────────────────────────────────

def _build_system_prompt(tools: Dict[str, Dict]) -> str:
    tool_lines = []
    for name, info in sorted(tools.items()):
        params = ', '.join(f'{k}: {v}' for k, v in info.get('params', {}).items())
        tool_lines.append(f"  - {name}({params}): {info['desc']}")
    tool_desc = '\n'.join(tool_lines)

    return f"""You are Devin, an autonomous AI agent running inside Devin AGI v4.0 on a real Linux system.
You can directly control the OS: run shell commands, navigate browsers, read/write files, monitor system, and more.

## Available Tools
{tool_desc}

## Response Format
You MUST follow this EXACT format in your responses:

Thought: [your reasoning about what to do next]
Action: tool_name
Action Input: {{"key": "value"}}

After observing the tool result, continue with more Thought/Action pairs until done.
When you have enough information to give a final answer:

Thought: I now have the complete answer
Final Answer: [your complete response to the user]

## Rules
1. ALWAYS use the Thought/Action/Action Input format when you need to do something
2. NEVER just describe what you would do — actually DO it via Action
3. For simple questions needing no tools, skip directly to: Thought: This is a simple question\nFinal Answer: [answer]
4. After each tool use, observe the result and decide the next step
5. Loop through as many steps as needed to fully complete the task
6. For security work: only operate on systems you own or have authorization to test
7. Be concise and action-oriented. Show real results, not hypothetical ones."""


# ── ReAct execution loop ───────────────────────────────────────────────────────

_ACTION_RE     = re.compile(r'Action:\s*(.+?)(?:\n|$)', re.IGNORECASE)
_INPUT_RE      = re.compile(r'Action\s+Input:\s*(.+?)(?=\nThought:|\nAction:|\nFinal Answer:|$)', re.IGNORECASE | re.DOTALL)
_FINAL_RE      = re.compile(r'Final\s+Answer:\s*(.+)', re.IGNORECASE | re.DOTALL)
_THOUGHT_RE    = re.compile(r'Thought:\s*(.+?)(?=\nAction:|\nFinal Answer:|$)', re.IGNORECASE | re.DOTALL)


def _parse_action(text: str) -> Tuple[Optional[str], Optional[Dict], Optional[str]]:
    """Parse one Thought/Action/Action Input block. Returns (action_name, inputs, thought)."""
    thought_m = _THOUGHT_RE.search(text)
    thought = thought_m.group(1).strip() if thought_m else None

    action_m = _ACTION_RE.search(text)
    if not action_m:
        return None, None, thought

    action_name = action_m.group(1).strip()
    input_m = _INPUT_RE.search(text)
    inputs: Dict = {}
    if input_m:
        raw = input_m.group(1).strip()
        try:
            inputs = json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract key=value or bare string
            inputs = {'cmd': raw} if action_name in ('shell_run',) else {'query': raw}
    return action_name, inputs, thought


def _run_tool(tools: Dict[str, Dict], name: str, inputs: Dict) -> str:
    name = name.strip().lower().replace('-', '_').replace(' ', '_')
    # Try exact match first, then prefix match
    fn_info = tools.get(name)
    if not fn_info:
        for k, v in tools.items():
            if name in k or k in name:
                fn_info = v
                name = k
                break
    if not fn_info:
        return f"[Unknown tool: {name}. Available: {', '.join(sorted(tools.keys()))}]"
    try:
        return str(fn_info['fn'](**inputs))
    except Exception as e:
        return f"[Tool error in {name}: {e}]"


# ── Grok-style UI renderer ─────────────────────────────────────────────────────

class GrokUI:
    """Renders grok-style CLI output."""

    def __init__(self, provider_name: str = 'devin'):
        self.provider_name = provider_name
        self._chars_sent = 0
        self._max_tokens = 200000  # rough estimate

    def _w(self) -> int:
        return _cols()

    def print_header(self, cwd: str, tokens: int) -> None:
        w = self._w()
        left = f'  \033[32mmain\033[0m \033[2m{cwd}\033[0m'
        right = f'\033[2m{tokens}K / {self._max_tokens//1000}K\033[0m'
        gap = w - len(cwd) - len('  main ') - len(f'{tokens}K / {self._max_tokens//1000}K') - 2
        print(f'{left}{" " * max(gap, 2)}{right}')

    def print_user_msg(self, text: str) -> None:
        w = self._w()
        ts = _now_hhmm()
        # Dark-bg row for user message
        prefix = '  ❯ '
        inner = text[:w - len(prefix) - len(ts) - 4]
        padlen = w - len(prefix) - len(inner) - len(ts) - 2
        if _IS_TTY:
            # dark background bar
            line = f'\033[{BG_DARK}m{prefix}\033[1m{inner}\033[0m\033[{BG_DARK}m{" " * max(padlen,1)}\033[2m{ts}\033[0m'
        else:
            line = f'{prefix}{inner}  {ts}'
        print(line)

    def print_thought(self, duration: float) -> None:
        print(_c(GRAY_B, f'  ◆ Thought for {duration:.1f}s'))

    def start_response(self, ts: str) -> None:
        """Print timestamp at start of response (grok shows it inline)."""
        pass  # We'll put timestamp at the end

    def stream_text(self, text: str, end: str = '') -> None:
        print(text, end=end, flush=True)

    def print_tool_header(self, tool_name: str, inputs: Dict) -> str:
        """Print collapsible tool call line. Returns the label for later."""
        # Summarize inputs
        if 'cmd' in inputs:
            summary = inputs['cmd'][:60]
        elif 'url' in inputs:
            summary = inputs['url'][:60]
        elif 'query' in inputs:
            summary = inputs['query'][:60]
        elif 'path' in inputs:
            summary = inputs['path'][:60]
        elif inputs:
            summary = str(list(inputs.values())[0])[:60]
        else:
            summary = ''

        label = f'{tool_name}: {summary}' if summary else tool_name
        if _IS_TTY:
            print(f'\033[{BG_TOOL}m  \033[36m›\033[0m\033[{BG_TOOL}m \033[2m{label}\033[0m')
        else:
            print(f'  › {label}')
        return label

    def print_tool_result(self, result: str, label: str, duration: float) -> None:
        lines = result.strip().splitlines()
        shown = lines[:8]  # show first 8 lines, collapse rest
        for ln in shown:
            print(_c(GRAY, f'    {ln}'))
        if len(lines) > 8:
            print(_c(GRAY, f'    … ({len(lines)-8} more lines)'))
        print(_c(DIM, f'  \033[2mRan {label.split(":")[0]} in {duration:.2f}s\033[0m'))

    def print_worked_for(self, duration: float) -> None:
        print()
        print(_c(GRAY, f'  Worked for {_elapsed(0 if duration >= 60 else 0)}'.replace('0.0s', f'{duration:.1f}s')))
        # simpler:
        s = duration
        if s < 60:
            print(_c(GRAY_B, f'\n  Worked for {s:.1f}s'))
        else:
            print(_c(GRAY_B, f'\n  Worked for {int(s//60)}m {int(s%60)}s'))

    def print_final(self, text: str, ts: str) -> None:
        # Print the response with timestamp at right of first line
        lines = text.strip().splitlines()
        if not lines:
            return
        w = self._w()
        first = lines[0]
        padlen = w - len('  ' + first) - len(ts) - 2
        if _IS_TTY and padlen > 0:
            print(f'  \033[0m{first}\033[{GRAY_B}m{" " * padlen}{ts}\033[0m')
        else:
            print(f'  {first}  {ts}')
        for ln in lines[1:]:
            print(f'  {ln}')

    def print_elapsed(self, seconds: float) -> None:
        print()
        if seconds < 60:
            print(_c(GRAY_B, f'  Worked for {seconds:.1f}s'))
        else:
            print(_c(GRAY_B, f'  Worked for {int(seconds//60)}m {int(seconds%60)}s'))

    def print_status_bar(self, provider: str, model_hint: str = '') -> None:
        w = self._w()
        shortcuts = 'Shift+Tab:mode  |  Ctrl+c:cancel  |  Ctrl+x:shortcuts'
        right = f'{provider} (medium)' if not model_hint else model_hint
        gap = w - len(shortcuts) - len(right) - 4
        print(_c(GRAY, f'  {shortcuts}{" " * max(gap,2)}{right}'))

    def print_input_prompt(self) -> str:
        return '  ❯ '

    def banner(self, provider_name: str, cwd: str) -> None:
        w = self._w()
        sep = _hr(w - 4)
        print()
        print(_c(CYAN_B, f'  ╭{sep}╮'))
        title = '  Devin AGI v4.0  ·  Autonomous OS-Controlling AI'
        prov  = f'[{provider_name}]'
        pad   = w - len(title) - len(prov) - 4
        print(_c(CYAN_B, '  │') + _c(WHITE_B, title) +
              ' ' * max(pad, 1) + _c(GRAY, prov) + _c(CYAN_B, ' │'))
        sub = '  Type /help for commands · /think <task> for agentic mode · Ctrl+D to exit'
        pad2 = w - len(sub) - 4
        print(_c(CYAN_B, '  │') + _c(GRAY, sub) + ' ' * max(pad2, 0) + _c(CYAN_B, '│'))
        print(_c(CYAN_B, f'  ╰{sep}╯'))
        print()


# ── Slash commands ─────────────────────────────────────────────────────────────

_SLASH_HELP = """
  Slash commands:
    /help              Show this help
    /clear             Clear screen + conversation history
    /status            System and module status
    /tools             List registered tools
    /screenshot        Take + show screenshot
    /memory            Show saved memories
    /remember <fact>   Save a fact to persistent memory
    /shell <cmd>       Run a shell command directly
    /git <args>        Run a git command
    /think <task>      Force agentic mode on a task
    /voice             Toggle voice mode
    /provider <p>      Switch provider (claude|gemini|openai|hf|free_claude|fcc)
    /model <m>         Set model for current provider
    /mem               Conversation memory stats
    /cwd               Show working directory
    /reset             Reset conversation history
    /exit  /q          Exit Devin
"""


# ── Main DevinREPL ─────────────────────────────────────────────────────────────

class DevinREPL:
    """Grok-style interactive REPL with agentic tool execution."""

    def __init__(self, devin_agi: Optional[Any] = None, provider_name: str = ''):
        self._agi = devin_agi
        self._provider = _select_provider(provider_name)
        self._history: List[Dict[str, str]] = []
        self._voice_mode = os.environ.get('DEVIN_VOICE_MODE') == '1'
        self._running = True
        self._tools = _build_agent_tools()
        self._system = _build_system_prompt(self._tools)
        self._ui = GrokUI(provider_name=self._provider.name)
        self._session = None
        self._use_pt = False
        self._setup_input()

    def _setup_input(self) -> None:
        try:
            from prompt_toolkit import PromptSession
            from prompt_toolkit.history import FileHistory
            from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
            from prompt_toolkit.styles import Style
            style = Style.from_dict({
                'prompt': '#00ffff bold',
                '': 'bg:#1a1a1a',
            })
            self._session = PromptSession(
                history=FileHistory(str(Path.home() / '.devin_history')),
                auto_suggest=AutoSuggestFromHistory(),
                enable_history_search=True,
                style=style,
                multiline=False,
            )
            self._use_pt = True
        except (ImportError, Exception):
            pass

    def _get_input(self, prompt: str) -> Optional[str]:
        if self._use_pt and self._session:
            try:
                from prompt_toolkit import print_formatted_text
                return self._session.prompt(prompt)
            except (KeyboardInterrupt, EOFError):
                return None
        try:
            return input(prompt)
        except (KeyboardInterrupt, EOFError):
            return None

    # ── Core: Agentic loop (native tool calling + ReAct fallback) ─────────────

    def _native_tool_loop(self, user_text: str) -> str:
        """
        Universal agentic tool-calling loop — works with ALL providers.
        Uses provider.call_with_tools() which dispatches to native tool calling
        (Claude/OpenAI/Ollama) or falls back to ReAct text parsing.
        """
        task_start = time.time()

        # Build conversation for this task
        loop_messages = []
        for m in self._history[-16:]:
            loop_messages.append({'role': m['role'], 'content': m.get('content', '')})
        loop_messages.append({'role': 'user', 'content': user_text})

        # Concise system prompt for tool calling (less ReAct scaffolding needed)
        system = (
            "You are Devin, an autonomous AI agent running on a real Linux system. "
            "Use the available tools to complete tasks. "
            "When asked to run a command, call shell_run. "
            "When asked about system state, call system_info or shell_run. "
            "When asked to open a URL or navigate, call navigate_browser. "
            "Always use tools — never just describe what you would do."
        )

        max_tool_rounds = 6
        all_observations = []
        final_content = ''
        seen_calls = set()  # prevent duplicate tool calls

        for step in range(max_tool_rounds):
            think_start = time.time()
            result = self._provider.call_with_tools(loop_messages, self._tools, system=system)
            think_dur = time.time() - think_start
            self._ui.print_thought(think_dur)

            tool_calls = result.get('tool_calls', [])
            content = result.get('content', '').strip()

            if not tool_calls:
                # No more tool calls — take the content as final answer
                if content and not content.startswith('Using tool:'):
                    final_content = content
                break

            # Execute each unique tool call
            executed_any = False
            tool_results_text = []
            for tc in tool_calls:
                tool_name = tc.get('name', '')
                tool_args = tc.get('arguments', {})

                # Deduplicate: skip if we already ran this exact call
                call_key = f'{tool_name}:{json.dumps(tool_args, sort_keys=True)}'
                if call_key in seen_calls:
                    continue
                seen_calls.add(call_key)
                executed_any = True

                tool_label = self._ui.print_tool_header(tool_name, tool_args)
                t_start = time.time()
                observation = _run_tool(self._tools, tool_name, tool_args)
                t_dur = time.time() - t_start
                self._ui.print_tool_result(observation, tool_label, t_dur)

                obs_line = f'{tool_name}: {observation}'
                all_observations.append(obs_line)
                tool_results_text.append(f'[{tool_name} result]\n{observation}')

            if not executed_any:
                break  # all tool calls were duplicates

            # Feed results back as a single user message (not per-tool)
            loop_messages.append({'role': 'assistant', 'content': content or 'Calling tools...'})
            loop_messages.append({
                'role': 'user',
                'content': '\n\n'.join(tool_results_text) + '\n\nWhat is your conclusion?',
            })

        # Build final answer from real data
        if not final_content:
            if all_observations:
                final_content = '\n'.join(all_observations[-8:])
            else:
                final_content = '[Task executed — no output captured]'

        return final_content

    def _react_loop(self, user_text: str) -> str:
        """
        Main agentic loop. Uses native tool calling for Ollama, ReAct text format otherwise.
        """
        task_start = time.time()
        self._history.append({'role': 'user', 'content': user_text})

        # Try native tool calling for all providers (each implements call_with_tools)
        try:
            final_answer = self._native_tool_loop(user_text)
            total_dur = time.time() - task_start
            ts = _now_hhmm()
            print()
            self._ui.print_final(final_answer, ts)
            self._ui.print_elapsed(total_dur)
            print()
            self._history.append({'role': 'assistant', 'content': final_answer})
            self._speak(final_answer)
            return final_answer
        except Exception:
            pass  # fall through to ReAct text loop

        # ReAct text-based fallback
        return self._react_text_loop(user_text, task_start)

    def _react_text_loop(self, user_text: str, task_start: float) -> str:
        """ReAct text-based loop for providers without native tool calling."""
        messages = list(self._history[-20:])
        max_steps = 15
        final_answer = ''

        for step in range(max_steps):
            think_start = time.time()
            full_response = ''
            try:
                for chunk in self._provider.stream(messages, self._system):
                    full_response += chunk
            except Exception as e:
                full_response = f"[Provider error: {e}]"
                break

            think_dur = time.time() - think_start
            self._ui.print_thought(think_dur)

            # Check for Final Answer first
            final_m = _FINAL_RE.search(full_response)
            if final_m:
                final_answer = final_m.group(1).strip()
                break

            # Parse action
            action_name, inputs, thought = _parse_action(full_response)

            if not action_name:
                # Treat whole response as final answer
                final_answer = full_response.strip()
                for prefix in ('Thought:', 'thought:'):
                    if final_answer.lower().startswith(prefix.lower()):
                        idx = final_answer.find('\n')
                        if idx > 0:
                            rest = final_answer[idx+1:].strip()
                            if rest:
                                final_answer = rest
                break

            # Execute tool
            tool_label = self._ui.print_tool_header(action_name, inputs or {})
            tool_start = time.time()
            observation = _run_tool(self._tools, action_name, inputs or {})
            tool_dur = time.time() - tool_start
            self._ui.print_tool_result(observation, tool_label, tool_dur)

            messages.append({'role': 'assistant', 'content': full_response})
            messages.append({'role': 'user', 'content': f'Observation: {observation}\nContinue.'})

        total_dur = time.time() - task_start

        if not final_answer:
            final_answer = '[No answer produced]'

        ts = _now_hhmm()
        print()
        self._ui.print_final(final_answer, ts)
        self._ui.print_elapsed(total_dur)
        print()

        self._history.append({'role': 'assistant', 'content': final_answer})
        self._speak(final_answer)
        return final_answer

    def _speak(self, text: str) -> None:
        if self._voice_mode and text:
            try:
                from main import CAPS
                if CAPS.voice and hasattr(CAPS.voice, 'speak'):
                    CAPS.voice.speak(text[:400])
            except Exception:
                pass

    # ── Slash command handler ──────────────────────────────────────────────────

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
            self._ui.banner(self._provider.name, os.getcwd())
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

        if cmd == '/think':
            if arg:
                self._react_loop(arg)
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
            tok = chars // 4
            mems = _load_memories()
            print(_c(GRAY, f'  Conversation: {n} messages, ~{tok}K tokens  |  Memories: {len(mems)} facts'))
            return True

        if cmd == '/voice':
            self._voice_mode = not self._voice_mode
            print(_c(YELLOW, f'  Voice mode: {"ON" if self._voice_mode else "OFF"}'))
            return True

        if cmd == '/provider':
            if arg:
                self._provider = _select_provider(arg.strip())
                self._system = _build_system_prompt(self._tools)
                self._ui.provider_name = self._provider.name
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

        print(_c(YELLOW, f'  Unknown command: {cmd}  (type /help)'))
        return True

    # ── Utility methods ────────────────────────────────────────────────────────

    def _shell(self, cmd: str) -> None:
        t = time.time()
        print(_c(GRAY, f'  $ {cmd}'))
        try:
            r = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=60)
            for ln in (r.stdout or '').splitlines():
                print(_c(GRAY, f'  {ln}'))
            for ln in (r.stderr or '').splitlines():
                print(_c(RED, f'  {ln}'))
        except subprocess.TimeoutExpired:
            print(_c(RED, '  [timeout]'))
        except Exception as e:
            print(_c(RED, f'  [error: {e}]'))
        print(_c(GRAY_B, f'  ({time.time()-t:.2f}s)'))

    def _do_screenshot(self) -> None:
        print(_c(CYAN, '  Taking screenshot…'))
        try:
            from modules.os_agent import get_os_agent
            agent = get_os_agent()
            r = agent.screenshot('Describe the current screen')
            if r.success:
                print(_c(GREEN, f'  ✓ {r.message}'))
                if r.vision_result and r.vision_result != '[Vision analysis unavailable — no AI provider configured]':
                    print(_c(GRAY, f'  Screen: {r.vision_result[:300]}'))
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

    def _show_status(self) -> None:
        print(_c(CYAN, f'\n  Provider: {self._provider.name}  Available: {self._provider.available()}'))
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
            ]
            for label, attr in rows:
                obj = getattr(CAPS, attr, None)
                mark = _c(GREEN, '●') + ' ready' if obj else _c(GRAY, '○') + ' not loaded'
                print(f'  {label:<22} {mark}')
        except Exception as e:
            print(_c(YELLOW, f'  Module status unavailable: {e}'))
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.3)
            mem = psutil.virtual_memory()
            print(_c(GRAY, f'\n  CPU: {cpu}%  RAM: {mem.percent}% ({mem.used//1024//1024}MB used)'))
        except ImportError:
            pass
        mems = _load_memories()
        print(_c(GRAY, f'  Memories: {len(mems)}  Conversation: {len(self._history)} messages'))
        print()

    def _show_tools(self) -> None:
        self._tools = _build_agent_tools()
        print(_c(CYAN, f'\n  Available tools ({len(self._tools)}):'))
        for name, info in sorted(self._tools.items()):
            desc = info.get('desc', '')[:55]
            params = ', '.join(info.get('params', {}).keys())
            print(_c(GRAY, f'  › {name:<26} {desc}'))
            if params:
                print(_c(GRAY, f'    {"params:":<24} {params}'))
        print()

    # ── Main REPL loop ─────────────────────────────────────────────────────────

    def run(self) -> None:
        self._ui.banner(self._provider.name, os.getcwd())
        cwd = os.getcwd()

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
                                self._react_loop(text)
                                continue
                    except Exception:
                        pass

                # Show token count in header area
                tok = _tok_estimate(self._history)
                if _IS_TTY:
                    print(_c(GRAY, f'  \033[2mmain {cwd}  {tok}K / 200K\033[0m'))

                line = self._get_input(self._ui.print_input_prompt())
                if line is None:
                    print()
                    break
                line = line.strip()
                if not line:
                    continue

                if line.startswith('/'):
                    self._handle_slash(line)
                    continue

                # Print user message block
                self._ui.print_user_msg(line)
                print()

                # Run the agentic ReAct loop
                self._react_loop(line)

                # Update shortcuts hint
                self._ui.print_status_bar(self._provider.name)
                print()

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
    get_repl(devin_agi).run()


if __name__ == '__main__':
    start_repl()
