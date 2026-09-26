#!/usr/bin/env python3
"""
Devin AGI 4.0 — Claude Code-style Interactive REPL

All credentials via .env / environment variables only.
Never hardcode API keys.
"""
from __future__ import annotations
import os, sys, shutil, signal, subprocess, threading, time
from pathlib import Path
from typing import Any, Dict, List, Optional, Generator

ROOT = Path(__file__).resolve().parent.parent
_ENV = ROOT / '.env'
if _ENV.exists():
    for _l in _ENV.read_text().splitlines():
        _l = _l.strip()
        if _l and not _l.startswith('#') and '=' in _l:
            _k, _, _v = _l.partition('=')
            os.environ.setdefault(_k.strip(), _v.strip().strip('"\'' ))


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


# ── AI Provider wrappers ───────────────────────────────────────────────────────

class _BaseProvider:
    name = 'none'
    def available(self) -> bool: return False
    def stream(self, messages: List[Dict], system: str = '') -> Generator[str, None, None]:
        yield '[No provider available]'


class _GeminiProvider(_BaseProvider):
    name = 'gemini'

    def __init__(self):
        self._key = os.environ.get('GEMINI_API_KEY', '')
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


class _HFProvider(_BaseProvider):
    name = 'huggingface'

    def __init__(self):
        self._key = os.environ.get('HF_TOKEN', '')
        self._model = os.environ.get('HF_MODEL', 'mistralai/Mixtral-8x7B-Instruct-v0.1')

    def available(self) -> bool:
        return bool(self._key)

    def stream(self, messages: List[Dict], system: str = '') -> Generator[str, None, None]:
        try:
            from huggingface_hub import InferenceClient
            client = InferenceClient(token=self._key)
            all_msgs = ([{'role': 'system', 'content': system}] + messages) if system else messages
            for chunk in client.chat.completions.create(
                model=self._model, messages=all_msgs, stream=True, max_tokens=2048
            ):
                d = chunk.choices[0].delta
                if d.content:
                    yield d.content
        except Exception as e:
            yield f'[HuggingFace error: {e}]'


def _select_provider(forced: str = '') -> _BaseProvider:
    candidates = {
        'gemini': _GeminiProvider(),
        'claude': _ClaudeProvider(),
        'openai': _OpenAIProvider(),
        'hf': _HFProvider(),
        'huggingface': _HFProvider(),
    }
    name = forced or os.environ.get('DEVIN_PROVIDER', '')
    if name and name in candidates:
        return candidates[name]
    for p in [candidates['gemini'], candidates['claude'], candidates['openai'], candidates['hf']]:
        if p.available():
            return p
    return candidates['hf']


# ── System prompt ──────────────────────────────────────────────────────────────

_SYSTEM = """You are Devin, an autonomous AI assistant running inside Devin AGI v4.0.

You have access to OS control tools (mouse, keyboard, screenshots), a reasoning engine,
voice I/O, browser automation, and a comprehensive system monitor.

You can perform virtually any computer task: browse the web, write and run code,
control applications, analyze files, and more.

For security/pentesting: only operate on systems you own or have explicit written
authorization to test. Never target systems without permission.

Be concise, direct, and action-oriented. Format responses in Markdown."""

_SLASH_HELP = """
  Slash commands:
    /help          Show this help
    /clear         Clear screen + conversation history
    /tools         List registered tools
    /status        System / module status
    /shell <cmd>   Run a shell command
    /git <args>    Run git command
    /mem           Conversation memory stats
    /voice         Toggle voice mode
    /provider <p>  Switch provider (gemini|claude|openai|hf)
    /model <m>     Set model for current provider
    /cwd           Show working directory
    /reset         Reset conversation history
    /exit  /q      Exit Devin
"""


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
            self._session = PromptSession(
                history=FileHistory(str(Path.home() / '.devin_history')),
                auto_suggest=AutoSuggestFromHistory(),
                enable_history_search=True,
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
        sep = '─' * (w - 4)
        print()
        print(_c(CYAN_B, f'  ╭{sep}╮'))
        title = '  Devin AGI v4.0  ·  Autonomous OS-Controlling AI'
        prov  = f'[{self._provider.name}]'
        pad   = w - len(title) - len(prov) - 4
        print(_c(CYAN_B, '  │') + _c(WHITE_B, title) +
              ' ' * max(pad, 1) + _c(GRAY, prov) + _c(CYAN_B, ' │'))
        sub = '  Type /help for commands · Ctrl+D to exit'
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
            print(_c(YELLOW, '  History cleared.'))
            return True

        if cmd == '/status':
            self._show_status()
            return True

        if cmd == '/tools':
            self._show_tools()
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
            print(_c(GRAY, f'  Messages: {n}  Characters: {chars}'))
            return True

        if cmd == '/voice':
            self._voice_mode = not self._voice_mode
            print(_c(YELLOW, f'  Voice mode: {"ON" if self._voice_mode else "OFF"}'))
            return True

        if cmd == '/provider':
            if arg:
                self._provider = _select_provider(arg.strip())
                print(_c(YELLOW, f'  Provider: {self._provider.name}'))
            else:
                print(_c(GRAY, f'  Current: {self._provider.name}'))
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
                    print(_c(YELLOW, f'  Model: {arg.strip()}'))
                else:
                    print(_c(YELLOW, '  Cannot set model for this provider'))
            else:
                print(_c(GRAY, '  Usage: /model <name>'))
            return True

        if cmd == '/cwd':
            print(_c(GRAY, f'  {os.getcwd()}'))
            return True

        return False

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

    def _show_status(self) -> None:
        try:
            from main import CAPS, get_devin
            d = get_devin()
            print(_c(CYAN, f'\n  Modules: {d.loaded_count()}/{d.total_count()} loaded'))
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
            print(_c(YELLOW, f'  Status unavailable: {e}'))
        print()

    def _show_tools(self) -> None:
        try:
            from main import CAPS
            if CAPS.reasoning and hasattr(CAPS.reasoning, '_tools'):
                tools = CAPS.reasoning._tools
                print(_c(CYAN, f'\n  Reasoning tools ({len(tools)}):'))
                for name, info in sorted(tools.items()):
                    desc = (info.get('desc', '') if isinstance(info, dict) else '')[:55]
                    print(_c(GRAY, f'  ⏺ {name:<28} {desc}'))
        except Exception:
            pass
        print()

    def _stream_response(self, user_text: str) -> str:
        self._history.append({'role': 'user', 'content': user_text})
        messages = self._history[-30:]
        full = ''
        print()
        print(_c(CYAN_B, '  Devin'))
        print(_c(CYAN, '  ' + '─' * (_cols() - 4)))
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
        prompt = _c(CYAN_B, '  > ')
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
