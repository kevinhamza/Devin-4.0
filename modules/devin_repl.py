"""
modules/devin_repl.py — Devin's terminal interface.

A conversation in the terminal: shaded `❯` bars for what you said, `◆ Thought for 1.2s`
lines with Devin's reasoning and the plan it wrote, one `›` row per action it takes on
the computer together with what the screenshot showed afterwards, a live status line,
and a bordered input box with the model name on its lower edge.

Three modes, cycled with Shift+Tab:
    auto    Devin decides whether to just answer or to operate the computer
    agent   every message is a task carried out with the mouse, keyboard and shell
    chat    conversation only; the computer is never touched

Run `./devin`, or `./devin "open the calculator and compute 12*7"` for a single task.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules import ollama_provider as llm  # noqa: E402

VERSION = '4.0'
MODES = ('auto', 'agent', 'chat')
_TTY = sys.stdout.isatty()


# ══════════════════════════════════════════════════════════════════════════════
# Terminal drawing
# ══════════════════════════════════════════════════════════════════════════════

def _cols() -> int:
    return max(40, shutil.get_terminal_size((100, 30)).columns)


def _sgr(code: str, text: str) -> str:
    return f'\033[{code}m{text}\033[0m' if _TTY else text


DIM, BOLD = '2', '1'
GRAY = '38;5;245'
FAINT = '38;5;240'
WHITE = '38;5;255'
CYAN = '38;5;80'
BLUE = '38;5;75'
GREEN = '38;5;114'
YELLOW = '38;5;179'
RED = '38;5;203'
BG_USER = '48;5;236'
BG_ROW = '48;5;234'

_ANSI = re.compile(r'\033\[[0-9;]*m')


def _width(text: str) -> int:
    """Printed width of a string (wide characters count double)."""
    plain = _ANSI.sub('', text)
    try:
        from wcwidth import wcswidth
        w = wcswidth(plain)
        return w if w >= 0 else len(plain)
    except Exception:
        return len(plain)


def _clip(text: str, width: int) -> str:
    text = text.replace('\n', ' ')
    if _width(text) <= width:
        return text
    out = ''
    for ch in text:
        if _width(out + ch) > width - 1:
            break
        out += ch
    return out + '…'


def _clock() -> str:
    return time.strftime('%I:%M %p').lstrip('0')


def _duration(seconds: float) -> str:
    if seconds < 60:
        return f'{seconds:.1f}s'
    return f'{int(seconds // 60)}m {int(seconds % 60)}s'


def _kilo(n: int) -> str:
    return f'{n / 1000:.1f}k' if n < 100_000 else f'{n // 1000}k'


def _wrap(text: str, width: int) -> List[str]:
    import textwrap
    lines: List[str] = []
    for para in text.split('\n'):
        lines.extend(textwrap.wrap(para, width, break_long_words=True, replace_whitespace=False) or [''])
    return lines


class Status:
    """The live `⠋ Responding… 8.5s` line. Everything else prints through `write()`."""

    FRAMES = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._label = ''
        self._since = 0.0
        self._task_since = 0.0
        self._tokens = 0
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._drawn = False

    def start(self, label: str) -> None:
        with self._lock:
            self._label, self._since = label, time.monotonic()
            if not self._running:
                self._task_since = self._since
                self._running = True
                if _TTY:
                    self._thread = threading.Thread(target=self._spin, daemon=True)
                    self._thread.start()

    def label(self, label: str, tokens: Optional[int] = None) -> None:
        with self._lock:
            if label != self._label:
                self._label, self._since = label, time.monotonic()
            if tokens is not None:
                self._tokens = tokens

    def stop(self) -> None:
        with self._lock:
            self._running = False
            self._erase()
        t, self._thread = self._thread, None
        if t is not None and t is not threading.current_thread():
            t.join(timeout=0.5)

    def _erase(self) -> None:
        if self._drawn and _TTY:
            sys.stdout.write('\r\033[2K')
            sys.stdout.flush()
            self._drawn = False

    def _draw(self) -> None:
        now = time.monotonic()
        frame = self.FRAMES[int(now * 10) % len(self.FRAMES)]
        left = f'  {frame} {self._label} {now - self._since:.1f}s'
        right = f'{int(now - self._task_since)}s'
        if self._tokens:
            right += f' ↓{_kilo(self._tokens)}'
        right += ' [ctrl+c stop]'
        gap = max(1, _cols() - _width(left) - _width(right) - 1)
        sys.stdout.write('\r\033[2K' + _sgr(GRAY, left) + ' ' * gap + _sgr(FAINT, right))
        sys.stdout.flush()
        self._drawn = True

    def _spin(self) -> None:
        while True:
            with self._lock:
                if not self._running:
                    return
                self._draw()
            time.sleep(0.1)

    def write(self, text: str = '') -> None:
        """Print a line above the status line."""
        with self._lock:
            self._erase()
            sys.stdout.write(text + '\n')
            sys.stdout.flush()
            if self._running and _TTY:
                self._draw()

    def raw(self, text: str) -> None:
        """Print without a newline (streaming). The status line must be stopped."""
        with self._lock:
            self._erase()
            sys.stdout.write(text)
            sys.stdout.flush()


class UI:
    def __init__(self) -> None:
        self.status = Status()

    def out(self, text: str = '') -> None:
        self.status.write(text)

    def header(self, model_label: str, backend: str) -> None:
        w = _cols()
        title = f' Devin {VERSION} '
        self.out()
        self.out(_sgr(FAINT, '╭─') + _sgr(BOLD, title) + _sgr(FAINT, '─' * max(1, w - len(title) - 4) + '╮'))
        for line in (f'brain  {model_label}', f'hands  {backend}',
                     'Tell me what to do on this computer. Shift+Tab switches mode, /help lists commands.'):
            body = _clip(line, w - 4)
            self.out(_sgr(FAINT, '│ ') + _sgr(GRAY, body) + ' ' * max(0, w - 4 - _width(body)) + _sgr(FAINT, ' │'))
        self.out(_sgr(FAINT, '╰' + '─' * (w - 2) + '╯'))

    def topline(self, tokens: int, context: int) -> None:
        w = _cols()
        branch = _git_branch()
        cwd = str(Path.cwd()).replace(str(Path.home()), '~', 1)
        left_plain = f'  {branch} {cwd}' if branch else f'  {cwd}'
        left = (f'  {_sgr(GREEN, branch)} {_sgr(GRAY, cwd)}' if branch else f'  {_sgr(GRAY, cwd)}')
        right = f'{tokens / 1000:.1f}K / {context // 1000}K'
        gap = max(1, w - _width(left_plain) - len(right) - 1)
        self.out(left + ' ' * gap + _sgr(GRAY, right))

    def user(self, text: str) -> None:
        w = _cols()
        stamp = _clock()
        lines = _wrap(text, w - 8 - len(stamp))
        pad = _sgr(BG_USER, ' ' * w)
        self.out()
        self.out(pad)
        for i, line in enumerate(lines):
            head = '  ❯ ' if i == 0 else '    '
            tail = stamp if i == 0 else ''
            fill = ' ' * max(1, w - _width(head) - _width(line) - len(tail) - 1)
            if _TTY:
                self.out(f'\033[{BG_USER}m{head}\033[1m{line}\033[22m{fill}\033[{GRAY}m{tail} \033[0m')
            else:
                self.out(f'{head}{line}')
        self.out(pad)
        self.out()

    def thought(self, seconds: float, text: str = '', plan: Optional[List[str]] = None) -> None:
        line = f'  ◆ {_sgr(BOLD, "Thought")} for {_duration(seconds)}'
        self.out(_sgr(GRAY, line))
        if text:
            for part in _wrap(text, _cols() - 8)[:4]:
                self.out(_sgr(GRAY, f'    {part}'))
        if plan:
            for i, step in enumerate(plan, start=1):
                self.out(_sgr(FAINT, f'    {i}. {_clip(step, _cols() - 10)}'))

    def row(self, text: str, detail: str = '', ok: Optional[bool] = None) -> None:
        w = _cols()
        mark = '›'
        color = GRAY if ok is None else (GREEN if ok else YELLOW)
        body = _clip(text, w - 6)
        fill = ' ' * max(0, w - 4 - _width(body))
        if _TTY:
            self.out(f'\033[{BG_ROW}m  \033[{color}m{mark}\033[0m\033[{BG_ROW}m \033[1m{body}\033[22m{fill}\033[0m')
        else:
            self.out(f'  {mark} {body}')
        if detail:
            for part in _wrap(detail, w - 8)[:6]:
                self.out(_sgr(FAINT, f'    {part}'))

    def answer(self, text: str) -> None:
        text = text.strip() or '(no reply)'
        w = _cols()
        stamp = _clock()
        self.out()
        rendered = _markdown(text, w - 6 - len(stamp))
        for i, line in enumerate(rendered):
            if i == 0:
                gap = max(2, w - 2 - _width(line) - len(stamp) - 1)
                self.out(f'  {line}' + ' ' * gap + _sgr(GRAY, stamp))
            else:
                self.out(f'  {line}')

    def worked(self, seconds: float) -> None:
        self.out()
        self.out(_sgr(GRAY, f'  Worked for {_duration(seconds)}'))

    def note(self, text: str, color: str = GRAY) -> None:
        for line in text.split('\n'):
            for part in (_wrap(line, _cols() - 4) if len(line) > _cols() - 4 else [line]):
                self.out(_sgr(color, f'  {part}'))

    def error(self, text: str) -> None:
        self.note(text, RED)


def _markdown(text: str, width: int) -> List[str]:
    """Light markdown → terminal lines: bullets, bold, inline code, headings, code blocks."""
    out: List[str] = []
    in_code = False
    for raw in text.split('\n'):
        if raw.strip().startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            out.append(_sgr(CYAN, '  ' + raw))
            continue
        line = raw.rstrip()
        indent = ''
        m = re.match(r'^(\s*)([-*•]|\d+[.)])\s+(.*)$', line)
        if m:
            bullet = '•' if m.group(2) in '-*•' else m.group(2)
            indent = m.group(1) + ' ' * (len(bullet) + 1)
            line = f'{m.group(1)}{bullet} {m.group(3)}'
        heading = re.match(r'^#{1,6}\s+(.*)$', line)
        if heading:
            line = f'**{heading.group(1)}**'
        wrapped = _wrap(line, width) if line else ['']
        for i, part in enumerate(wrapped):
            if i:
                part = indent + part
            part = re.sub(r'\*\*(.+?)\*\*', lambda mm: _sgr(BOLD, mm.group(1)), part)
            part = re.sub(r'`([^`]+)`', lambda mm: _sgr(CYAN, mm.group(1)), part)
            out.append(part)
    return out or ['']


def _git_branch() -> str:
    try:
        head = Path.cwd() / '.git' / 'HEAD'
        if head.exists():
            ref = head.read_text().strip()
            return ref.rsplit('/', 1)[-1] if ref.startswith('ref:') else ref[:7]
    except OSError:
        pass
    return ''


# ══════════════════════════════════════════════════════════════════════════════
# Deciding what a message needs
# ══════════════════════════════════════════════════════════════════════════════

CHAT_SYSTEM = """You are Devin, an AI assistant that lives on the user's computer.

You can operate this computer yourself: you take screenshots, move the mouse, click, and type on the keyboard like a person. Right now you are only talking, so answer the user directly and briefly. Think the question through before you answer, and say so plainly when you are not sure.

If the user asks you to do something on the computer, never say you are unable to. Say you will do it and that they can press Shift+Tab to switch to agent mode, or start the message with /do."""


_ACT = re.compile(
    r"\b(open|launch|start|run|close|quit|click|type|press|scroll|search|google|browse|go to|visit|play|"
    r"watch|download|install|uninstall|create|delete|rename|move|copy|save|screenshot|show me|find|look up|"
    r"turn (?:on|off)|switch to|maximi[sz]e|minimi[sz]e|log ?in|sign ?in|update|upgrade|scan)\b")
_TALK = re.compile(
    r"^(hi+|hey+|hello|yo|thanks?|thank you|ok(ay)?|yup|yes|yeah|no|nope|why|bye|good (morning|evening|night)|"
    r"how are|who are|what are you|what can you|what is|what's|what are|what does|how does|how do i|explain|"
    r"define|tell me about|who (is|was))\b")


def quick_route(message: str) -> Optional[str]:
    """'computer' / 'chat' when the wording makes it obvious, else None (ask the model)."""
    low = message.strip().lower()
    acts = bool(_ACT.search(low))
    if _TALK.match(low) and not (acts and re.match(r'^(ok(ay)?|yes|yeah|yup|hey+|hi+|hello)\b', low)):
        return 'chat'
    if acts:
        return 'computer'
    if len(low.split()) <= 2:
        return 'chat'
    return None


def route(message: str, history: List[Dict[str, str]], model: str) -> str:
    """'computer' or 'chat' for one message."""
    quick = quick_route(message)
    if quick:
        return quick
    prompt = ('Is the user asking you to DO something on their computer (open, click, search, play, files, '
              'settings, run or install software, read the screen), or only to TALK (greeting, question, '
              f'explanation, writing)?\nMessage: "{message[:300]}"\nAnswer with one word: computer or chat.')
    try:
        r = llm.chat_text([{'role': 'user', 'content': prompt}], model=model, max_tokens=6, temperature=0.0,
                          until=lambda t: bool(re.search(r'\b(computer|chat)\b', t, re.I)))
        return 'computer' if 'computer' in r['content'].lower() else 'chat'
    except llm.OllamaError:
        return 'chat'


# ══════════════════════════════════════════════════════════════════════════════
# The REPL
# ══════════════════════════════════════════════════════════════════════════════

HELP = """Commands
  /do <task>        carry out a task on the computer with the mouse and keyboard
  /chat <message>   just answer, do not touch the computer
  /look             describe what is on the screen right now
  /model [name]     show or switch the Ollama model   ·   /models lists installed ones
  /eyes [auto|always|never]   when the screenshot itself is sent to the model (now {eyes})
  /pull <name>      download a model through Ollama
  /mode [auto|agent|chat]
  /steps <n>        most actions Devin may take per task (now {steps})
  /shell [on|off]   let Devin also run commands directly, without a terminal window (now {shell})
  /doctor           check screen capture, input control and the model
  /clear            clear the screen and forget the conversation
  !<command>        run a shell command yourself
  /exit             quit

Keys
  Shift+Tab  switch mode      Ctrl+C  stop the current task      Ctrl+D  quit
  Esc Enter  new line in the input box"""


class DevinREPL:
    def __init__(self, devin_agi: Any = None, provider_name: str = '') -> None:
        self.ui = UI()
        self.history: List[Dict[str, str]] = []
        self.mode = os.environ.get('DEVIN_MODE_DEFAULT', 'auto')
        if self.mode not in MODES:
            self.mode = 'auto'
        self.model = ''          # answers in conversation
        self.agent_model = ''    # operates the computer (must be able to see when one can)
        self.tokens = 0
        self._printed = True     # something was written since the last status bar
        self.max_steps = int(os.environ.get('DEVIN_MAX_STEPS', '40'))
        self._agent: Any = None
        self._session: Any = None
        self._running = True
        self._task_tokens = 0

    # ── model ──
    def _ensure_model(self) -> bool:
        if self.model:
            return True
        if not llm.is_available():
            self.ui.error('Ollama is not answering at ' + llm._base())
            self.ui.note('Start it with:  ollama serve      then pull a model, e.g.:  ollama pull gemma4:e2b')
            return False
        self.model = llm.pick_model()
        self.agent_model = llm.pick_agent_model()
        return True

    def _model_label(self) -> str:
        if not self.model:
            return 'no model'
        if self.mode == 'chat' or not self.agent_model or self.agent_model == self.model:
            return f'ollama/{self.model}'
        if self.mode == 'agent':
            return f'ollama/{self.agent_model}'
        return f'ollama/{self.agent_model} acts · {self.model} chats'

    def _context(self) -> int:
        return (llm.model_info(self.model)['context'] if self.model else 0) or 8192

    def _capable(self) -> bool:
        """Can this model be trusted to decide by itself to operate the computer?"""
        if not self.agent_model:
            return False
        info = llm.model_info(self.agent_model)
        size_ok = info['params_b'] == 0 or info['params_b'] >= 2  # 0 = size unknown (cloud)
        return 'vision' in info['capabilities'] and size_ok

    # ── input ──
    def _build_session(self) -> None:
        if not (sys.stdin.isatty() and _TTY):
            return
        try:
            from prompt_toolkit import PromptSession
            from prompt_toolkit.history import FileHistory
            from prompt_toolkit.key_binding import KeyBindings
            from prompt_toolkit.styles import Style
        except Exception:
            return
        kb = KeyBindings()

        @kb.add('s-tab')
        def _(event) -> None:
            self.mode = MODES[(MODES.index(self.mode) + 1) % len(MODES)]
            event.app.invalidate()

        @kb.add('c-x')
        def _(event) -> None:
            event.app.exit(result='/help')

        style = Style.from_dict({
            'frame': '#5f5f5f', 'prompt': '#d0d0d0 bold', 'hint': '#808080', 'hintkey': '#d0d0d0 bold',
            'model': '#808080', 'placeholder': '#5f5f5f', 'bottom-toolbar': 'noreverse bg:default',
            'mode-auto': '#5fd7d7', 'mode-agent': '#87d787', 'mode-chat': '#d7af5f',
        })
        self._session = PromptSession(
            history=FileHistory(str(Path.home() / '.devin_history')), key_bindings=kb, style=style,
            erase_when_done=True, reserve_space_for_menu=0, multiline=False, mouse_support=False)

    def _prompt_parts(self):
        w = _cols()
        top = [('class:frame', '╭' + '─' * (w - 2) + '╮\n'), ('class:frame', '│ '), ('class:prompt', '❯ ')]
        label = f' {self._model_label()} ({self.mode}) '
        label = _clip(label, w - 6)
        bottom = [('class:frame', '╰' + '─' * max(1, w - 3 - _width(label))), ('class:model', label),
                  ('class:frame', '─╯\n'),
                  ('class:hintkey', ' Shift+Tab'), ('class:hint', ':mode '), (f'class:mode-{self.mode}', self.mode),
                  ('class:hint', '  │  '), ('class:hintkey', 'Ctrl+c'), ('class:hint', ':cancel  │  '),
                  ('class:hintkey', 'Ctrl+x'), ('class:hint', ':shortcuts')]
        return top, bottom

    def _read(self) -> Optional[str]:
        self._flush_stdin()
        if self._printed:
            self.ui.topline(self.tokens, self._context())
            self._printed = False
        if self._session is None:
            try:
                return input('❯ ' if _TTY else '')
            except (EOFError, KeyboardInterrupt):
                return None
        try:
            return self._session.prompt(
                lambda: self._prompt_parts()[0],
                bottom_toolbar=lambda: self._prompt_parts()[1],
                rprompt=[('class:frame', '│')],
                placeholder=lambda: [('class:placeholder', {
                    'auto': 'Ask anything, or tell me what to do on this computer',
                    'agent': 'Describe a task — I will do it with the mouse and keyboard',
                    'chat': 'Chat only — I will not touch the computer'}[self.mode])],
                prompt_continuation=lambda width, line, soft: [('class:frame', '│   ')])
        except KeyboardInterrupt:
            return ''
        except EOFError:
            return None

    @staticmethod
    def _flush_stdin() -> None:
        """Drop keystrokes that landed in this terminal while Devin was driving the keyboard."""
        try:
            import termios
            if sys.stdin.isatty():
                termios.tcflush(sys.stdin, termios.TCIFLUSH)
        except Exception:
            pass

    # ── chat ──
    def chat(self, message: str) -> str:
        self.history.append({'role': 'user', 'content': message})
        self.ui.status.start('Responding…')
        started = time.monotonic()
        text = ''
        thinking = ''
        first: Optional[float] = None
        try:
            gen = llm.stream(self.history[-16:], system=CHAT_SYSTEM, model=self.model)
            while True:
                try:
                    kind, piece = next(gen)
                except StopIteration as stop:
                    stats = stop.value or {}
                    self.tokens += stats.get('tokens_in', 0) + stats.get('tokens_out', 0)
                    break
                if kind == 'thinking':
                    thinking += piece
                    continue
                if first is None:
                    first = time.monotonic() - started
                text += piece
                self.ui.status.label('Responding…', self.tokens + len(text) // 4)
        except llm.OllamaError as e:
            self.ui.status.stop()
            self.ui.error(str(e))
            self.history.pop()
            return ''
        except KeyboardInterrupt:
            self.ui.status.stop()
            self.ui.note('Stopped.', YELLOW)
            self.history.pop()
            return ''
        self.ui.status.stop()
        self.ui.thought(first or (time.monotonic() - started), thinking.strip()[:300])
        self.ui.answer(text)
        self.ui.worked(time.monotonic() - started)
        self.history.append({'role': 'assistant', 'content': text})
        return text

    # ── computer ──
    def _confirm(self, command: str) -> bool:
        self.ui.status.stop()
        self.ui.note(f'Devin wants to run:  {command}', YELLOW)
        try:
            answer = input('  Allow? [y/N] ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ''
        self.ui.status.start('Working…')
        return answer in ('y', 'yes')

    def _on_event(self, e: Dict[str, Any]) -> None:
        kind = e['type']
        if kind == 'look':
            first = e.get('thinks', 1) == 1
            self.ui.status.label('Looked at the screen. Planning…' if first
                                 else 'Looked at the new screen. Thinking again…', self.tokens)
        elif kind == 'think':
            self.tokens = self._task_tokens + e.get('tokens', 0)
            plan = e.get('plan') or []
            self.ui.thought(e['seconds'], e.get('thought', ''), plan if len(plan) > 1 else None)
        elif kind == 'speed':
            if e.get('tps', 0) < 60:
                self.ui.note(f'{e["model"]} reads about {e["tps"]:.0f} tokens a second on this machine, so each '
                             f'time I stop to think takes around {_duration(450 / max(e["tps"], 0.5) + 25)}. '
                             'Acting and checking the screen in between is fast.', FAINT)
        elif kind == 'act_start':
            self.ui.status.label(f'{e.get("summary") or e["action"]}…', self.tokens)
        elif kind == 'act':
            step = e['step']
            failed = step.outcome.startswith(('ERROR', 'REFUSED', 'BLOCKED')) or bool(step.problem)
            ok = False if (failed or step.changed is False) else (True if step.changed else None)
            self.ui.row(step.summary, step.outcome, ok)
            self.ui.status.label('Checked the screenshot. Next action…', self.tokens)
        elif kind == 'verify_start':
            self.ui.status.label('Checking the result against the screen…', self.tokens)
        elif kind == 'verify':
            self.tokens = self._task_tokens + e.get('tokens', 0)
            if e['complete']:
                self.ui.row('Checked the screen: the task is complete', e.get('reason', ''), True)
            else:
                self.ui.row('Checked the screen: not finished yet, continuing', e.get('reason', ''), False)
                self.ui.status.label('Looking at the screen…', self.tokens)
        elif kind == 'retry':
            dropped = e.get('dropped', 0)
            if e.get('new_window'):
                self.ui.row(f'A new window appeared: "{_clip(e["new_window"], 50)}" — reading it before going on')
            else:
                self.ui.row('The screen did not follow the plan — looking again and re-planning'
                            if dropped else 'That did not work — trying another way', '', False)

    def do(self, task: str) -> Any:
        from modules import screen_vision as sv
        from modules import os_automation as oa
        self.history.append({'role': 'user', 'content': task})
        started = time.monotonic()
        self._task_tokens = self.tokens
        context = ' | '.join(f'{m["role"]}: {m["content"][:120]}' for m in self.history[-5:-1])
        self.ui.status.start('Looking at the screen…')
        agent = sv.ComputerAgent(model=self.agent_model or self.model, on_event=self._on_event,
                                 confirm=self._confirm, max_steps=self.max_steps, cwd=os.getcwd())
        self._agent = agent
        try:
            result = agent.run(task, context=context)
        except KeyboardInterrupt:
            agent.stop()
            self.ui.status.stop()
            self.ui.note('Stopped.', YELLOW)
            self.history.append({'role': 'assistant', 'content': '(stopped by the user)'})
            return None
        except oa.DesktopError as e:
            self.ui.status.stop()
            self.ui.error(f'I cannot control this desktop: {e}')
            self.history.pop()
            return None
        finally:
            self._agent = None
        self.ui.status.stop()
        if result.success:
            self.ui.answer(result.answer)
        else:
            self.ui.out()
            self.ui.note(result.answer, YELLOW)
        if result.steps and result.screenshot:
            self.ui.note(f'screen saved: {result.screenshot}', FAINT)
        self.ui.worked(time.monotonic() - started)
        self.history.append({'role': 'assistant', 'content': result.answer})
        return result

    # ── one message ──
    def handle(self, line: str) -> None:
        line = line.strip()
        if not line:
            return
        self._printed = True
        if line.startswith('!'):
            self._shell(line[1:].strip())
            return
        if line.startswith('/'):
            self._slash(line)
            return
        self.ui.user(line)
        if not self._ensure_model():
            return
        mode = self.mode
        if mode == 'auto' and not self._capable():
            # A model that cannot see or plan must never start clicking on its own
            # because it misread a greeting. Acting stays an explicit choice: /do.
            mode = 'chat'
        if mode == 'auto':
            self.ui.status.start('Reading…')
            try:
                mode = 'agent' if route(line, self.history, self.model) == 'computer' else 'chat'
            except KeyboardInterrupt:
                self.ui.status.stop()
                return
            self.ui.status.stop()
        if mode == 'agent':
            self.do(line)
        else:
            self.chat(line)

    def _shell(self, command: str) -> None:
        if not command:
            return
        self.ui.row(f'$ {command}')
        try:
            r = subprocess.run(command, shell=True, text=True, capture_output=True, timeout=300)
            for ln in ((r.stdout or '') + (r.stderr or '')).rstrip().split('\n')[-40:]:
                self.ui.note(ln, FAINT)
        except subprocess.TimeoutExpired:
            self.ui.error('timed out after 300s')
        except KeyboardInterrupt:
            self.ui.note('Stopped.', YELLOW)

    def _slash(self, line: str) -> None:
        cmd, _, arg = line.partition(' ')
        cmd, arg = cmd.lower(), arg.strip()
        ui = self.ui
        if cmd in ('/exit', '/quit', '/q'):
            self._running = False
        elif cmd in ('/help', '/?'):
            ui.out()
            from modules import screen_vision as sv
            ui.note(HELP.format(steps=self.max_steps, shell='on' if sv.shell_allowed() else 'off',
                                eyes=os.environ.get('DEVIN_EYES', 'auto')))
        elif cmd == '/clear':
            self.history.clear()
            self.tokens = 0
            if _TTY:
                sys.stdout.write('\033[2J\033[3J\033[H')
            self._banner()
        elif cmd == '/mode':
            if arg in MODES:
                self.mode = arg
            ui.note(f'mode: {self.mode}')
        elif cmd == '/shell':
            if arg in ('on', 'off'):
                os.environ['DEVIN_ALLOW_SHELL'] = '1' if arg == 'on' else '0'
            from modules import screen_vision as sv
            ui.note('direct shell commands: ' + ('on' if sv.shell_allowed() else
                                                'off (mouse and keyboard only)'))
        elif cmd == '/eyes':
            if arg in ('auto', 'always', 'never'):
                os.environ['DEVIN_EYES'] = arg
            ui.note('screenshot sent to the model: ' + os.environ.get('DEVIN_EYES', 'auto')
                    + '   (auto = always for a fast model; for a slow one only when the screen has almost no readable text)')
        elif cmd == '/steps':
            if arg.isdigit() and int(arg) > 0:
                self.max_steps = int(arg)
            ui.note(f'steps per task: {self.max_steps}')
        elif cmd == '/models':
            names = llm.list_models()
            if not names:
                ui.error('No models installed (or Ollama is not running).')
            for name in names:
                role = ('  ← works the computer' if name == self.agent_model else '') + \
                       ('  ← chat' if name == self.model and self.model != self.agent_model else '')
                ui.note(('● ' if name in (self.model, self.agent_model) else '  ') + llm.describe_model(name) + role)
        elif cmd == '/model':
            if arg:
                installed = llm.list_models()
                match = [m for m in installed if m == arg or m.split(':')[0] == arg]
                if not match:
                    ui.error(f'{arg} is not installed. Get it with:  /pull {arg}')
                    return
                self.model = match[0]
                os.environ['OLLAMA_MODEL'] = self.model
                self.agent_model = llm.pick_agent_model()
            if self._ensure_model():
                ui.note(f'chat: {llm.describe_model(self.model)}')
                ui.note(f'works the computer: {llm.describe_model(self.agent_model)}')
                self._warn_if_weak()
        elif cmd == '/pull':
            if not arg:
                ui.note('usage: /pull <model>, for example /pull gemma4:e2b')
                return
            self._pull(arg)
        elif cmd in ('/look', '/screenshot', '/screen'):
            self._look(arg)
        elif cmd == '/doctor':
            self.doctor()
        elif cmd == '/do':
            if arg and self._ensure_model():
                ui.user(arg)
                self.do(arg)
        elif cmd == '/chat':
            if arg and self._ensure_model():
                ui.user(arg)
                self.chat(arg)
        else:
            ui.note(f'Unknown command {cmd}. Type /help.', YELLOW)

    def _pull(self, name: str) -> None:
        self.ui.status.start(f'Downloading {name}…')
        def progress(status: str, done: int, total: int) -> None:
            pct = f' {done * 100 // total}%' if total else ''
            self.ui.status.label(f'{name}: {status}{pct}')
        try:
            ok = llm.pull_model(name, progress)
        except KeyboardInterrupt:
            ok = False
        self.ui.status.stop()
        if ok:
            self.ui.note(f'{name} is ready. Switch with:  /model {name}', GREEN)
        else:
            self.ui.error(f'Could not download {name} (check the name, your disk space and `ollama signin`).')

    def _look(self, question: str) -> None:
        from modules import screen_vision as sv
        from modules import os_automation as oa
        if not self._ensure_model():
            return
        self.ui.status.start('Looking at the screen…')
        try:
            obs = sv.look()
            path = obs.save(oa._tmp_path('look.png'), marked=bool(obs.elements))
            text = sv.describe_screen(question or 'Describe what is on the screen.', self.agent_model or self.model)
        except oa.DesktopError as e:
            self.ui.status.stop()
            self.ui.error(str(e))
            return
        except KeyboardInterrupt:
            self.ui.status.stop()
            return
        self.ui.status.stop()
        self.ui.row(f'Looked at the screen — {len(obs.elements)} elements, window "{obs.window}"')
        self.ui.answer(text)
        self.ui.note(f'screenshot: {path}', FAINT)

    def doctor(self) -> bool:
        """Check everything Devin needs and say plainly what is missing."""
        from modules import os_automation as oa
        from modules import screen_vision as sv
        ui = self.ui
        ok_all = True

        def line(ok: Optional[bool], label: str, detail: str = '') -> None:
            mark = _sgr(GREEN, '✓') if ok else (_sgr(YELLOW, '!') if ok is None else _sgr(RED, '✗'))
            ui.out(f'  {mark} {label}' + (_sgr(GRAY, f'  {detail}') if detail else ''))

        ui.out()
        s = oa.status()
        backend = s.get('backend')
        ok_all &= bool(backend)
        line(bool(backend), 'mouse and keyboard control',
             f'{backend} · screen {s.get("screen", "?")}' if backend else s.get('error', '').split('\n')[0])
        if backend:
            try:
                t = time.monotonic()
                img = oa.get_desktop().capture()
                from PIL import ImageStat
                bright = ImageStat.Stat(img.convert('L')).mean[0]
                line(bright > 2, 'screen capture', f'{img.width}x{img.height} in {time.monotonic() - t:.2f}s'
                     + ('' if bright > 2 else ' — the image is black'))
                ok_all &= bright > 2
            except Exception as e:
                line(False, 'screen capture', str(e))
                ok_all = False
        yd = s.get('ydotool_socket')
        line(True if yd else None, 'ydotool daemon',
             yd or ('not running — optional on GNOME; needed on other Wayland desktops'
                    if s.get('ydotool_installed') else 'not installed — sudo apt install ydotool'))
        line(True if sv.ocr_available() else None, 'on-screen text reading (OCR)',
             'tesseract' if sv.ocr_available() else 'not installed — sudo apt install tesseract-ocr')
        if llm.is_available():
            model = self.agent_model or llm.pick_agent_model()
            info = llm.model_info(model)
            vision = 'vision' in info['capabilities']
            strong = vision and info['params_b'] >= 2 or info['params_b'] == 0
            line(True if strong else None, 'model that works the computer', llm.describe_model(model)
                 + ('' if strong else ' — too small / cannot see the screen; see /help → /pull'))
            chat = self.model or llm.pick_model()
            if chat != model:
                line(True, 'model for conversation', llm.describe_model(chat))
        else:
            line(False, 'model', f'Ollama is not answering at {llm._base()}')
            ok_all = False
        power = oa.power_state()
        if power['percent'] is not None:
            if power['on_battery']:
                line(None, 'power', f'on battery ({power["percent"]}%) — laptops slow the CPU on battery, '
                                    'so the model thinks slower; plug in for full speed')
            else:
                line(True, 'power', f'plugged in ({power["percent"]}%)')
        ui.out()
        return ok_all

    def _warn_if_weak(self) -> None:
        if not self.agent_model:
            return
        try:
            from modules import os_automation as oa
            power = oa.power_state()
            if power['on_battery']:
                self.ui.note(f'On battery ({power["percent"]}%): the CPU runs slower, so I think slower. '
                             'Plug in the charger for full speed.', YELLOW)
        except Exception:
            pass
        if self._capable():
            return
        info = llm.model_info(self.agent_model)
        vision = 'vision' in info['capabilities']
        small = 0 < info['params_b'] < 2
        why = []
        if not vision:
            why.append('it cannot see screenshots, only a text list of what is on screen')
        if small:
            why.append('it is too small to plan multi-step tasks reliably')
        self.ui.note(f'Heads-up: {self.agent_model} will struggle to operate the computer — '
                     + ' and '.join(why) + '.', YELLOW)
        self.ui.note('So in auto mode I will only talk. To make me act anyway, start the message with /do.', YELLOW)
        self.ui.note('For real control install a model that can see, for example:  /pull bonsai-2:4b', YELLOW)

    def _banner(self) -> None:
        backend = 'not connected yet'
        try:
            from modules import os_automation as oa
            s = oa.status()
            backend = (f'{s["backend"]} · screen {s.get("screen", "?")} · real mouse and keyboard'
                       if s.get('backend') else 'unavailable — run /doctor')
        except Exception:
            pass
        if not self.model:
            label = 'Ollama not reachable'
        elif self.agent_model and self.agent_model != self.model:
            label = (f'{llm.describe_model(self.agent_model)} works the computer  ·  '
                     f'{self.model} for conversation')
        else:
            label = llm.describe_model(self.model)
        self.ui.header(label, backend)
        self._warn_if_weak()

    def run(self) -> None:
        self._ensure_model()
        self._build_session()
        if self._session is not None:
            # A clean page: the banner at the top, the input box right under it.
            sys.stdout.write('\033[2J\033[3J\033[H')
            sys.stdout.flush()
        self._banner()
        while self._running:
            line = self._read()
            if line is None:
                break
            try:
                self.handle(line)
            except KeyboardInterrupt:
                self.ui.status.stop()
                self.ui.note('Stopped.', YELLOW)
            except Exception as e:  # never drop the user back to a shell mid-conversation
                self.ui.status.stop()
                self.ui.error(f'{type(e).__name__}: {e}')
        self.ui.status.stop()
        self.ui.note('Bye.')

    def run_once(self, prompt: str, force: str = '') -> int:
        """Handle a single message and exit (./devin "…")."""
        if not self._ensure_model():
            return 1
        if force in ('agent', 'chat'):
            self.mode = force
        self.handle(prompt)
        return 0


_repl: Optional[DevinREPL] = None


def get_repl(devin_agi: Any = None) -> DevinREPL:
    global _repl
    if _repl is None:
        _repl = DevinREPL(devin_agi=devin_agi)
    return _repl


def start_repl(devin_agi: Any = None) -> None:
    get_repl(devin_agi).run()


if __name__ == '__main__':
    start_repl()
