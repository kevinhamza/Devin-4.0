"""
cc_interface.py — Claude Code-style terminal interface for Devin.
Provides rich terminal rendering: boxes, diff views, file edit display,
streaming output, permission prompts, and the full Claude Code UX.
"""
from __future__ import annotations

import os
import sys
import re
import shutil
import textwrap
import threading
import itertools
import time
from typing import Optional, List, Dict, Any
from pathlib import Path

_TTY = sys.stdout.isatty()

# ── ANSI colors ───────────────────────────────────────────────────────────────

def _c(code: str, t: str) -> str:
    return f'\033[{code}m{t}\033[0m' if _TTY else t

def cyan(t):    return _c('36;1', t)
def green(t):   return _c('32;1', t)
def yellow(t):  return _c('33;1', t)
def red(t):     return _c('31;1', t)
def bold(t):    return _c('1', t)
def dim(t):     return _c('2', t)
def blue(t):    return _c('34;1', t)
def magenta(t): return _c('35;1', t)
def italic(t):  return _c('3', t)
def white(t):   return _c('37', t)

def _cols() -> int:
    return max(60, shutil.get_terminal_size((80, 24)).columns - 1)

def _strip_ansi(s: str) -> str:
    return re.sub(r'\033\[[^m]+m', '', s)

# ── Box drawing ───────────────────────────────────────────────────────────────

def banner(title: str = 'Devin AGI', subtitle: str = 'v4.0.0',
           model: str = '', provider: str = '', cwd: str = '',
           tools: int = 0, memories: int = 0) -> str:
    w = _cols()
    line = '─' * (w - 2)
    rows = []
    rows.append(cyan('╭' + line + '╮'))
    rows.append(cyan('│ ') + bold(cyan(' Devin AGI ')) + dim(subtitle) + ' — Autonomous OS-Controlling AI')
    if cwd:
        rows.append(cyan('│ ') + dim(' cwd: ') + white(cwd))
    if model and provider:
        rows.append(cyan('│ ') + dim(' model: ') + cyan(model) + dim('  provider: ') + white(provider) + dim('  mode: ') + green('auto'))
    if tools:
        rows.append(cyan('│ ') + dim(f' tools: {tools}') + (dim(f'  memories: {memories}') if memories else ''))
    rows.append(cyan('╰' + line + '╯'))
    return '\n'.join(rows)

def box(title: str, char: str = '─') -> str:
    w = _cols()
    clean = _strip_ansi(title)
    pad = max(0, w - len(clean) - 4)
    return dim(char * 2) + ' ' + bold(title) + ' ' + dim(char * pad)

def hr(char: str = '─', width: int = 0) -> str:
    w = width or _cols()
    return dim(char * w)

# ── Spinner ───────────────────────────────────────────────────────────────────

_SPIN_CHARS = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

class Spinner:
    def __init__(self, label: str = 'Devin is thinking…'):
        self.label = label
        self._active = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self, label: str = '') -> None:
        if label:
            self.label = label
        self._active.set()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        cycle = itertools.cycle(_SPIN_CHARS)
        while self._active.is_set():
            frame = next(cycle)
            if _TTY:
                sys.stdout.write(f'\r  {dim(frame)} {dim(self.label)}  ')
                sys.stdout.flush()
            time.sleep(0.08)

    def stop(self) -> None:
        self._active.clear()
        if self._thread:
            self._thread.join(timeout=0.3)
        if _TTY:
            sys.stdout.write('\r' + ' ' * (len(self.label) + 10) + '\r')
            sys.stdout.flush()

    def update(self, label: str) -> None:
        self.label = label

# ── Markdown renderer ─────────────────────────────────────────────────────────

def render_markdown(text: str, width: int = 0) -> str:
    if not _TTY:
        return text
    w = width or _cols()
    lines_in = text.split('\n')
    out: List[str] = []
    in_code = False
    code_lang = ''

    for ln in lines_in:
        # Code fence
        m_fence = re.match(r'^```(\w+)?$', ln)
        if m_fence:
            if not in_code:
                in_code = True
                code_lang = m_fence.group(1) or ''
                hdr = dim(f' {code_lang} ') if code_lang else ''
                out.append(dim('┌─' + ('─' if not hdr else '') + (f' {code_lang} ' if code_lang else '') + '─' * max(0, 20 - len(code_lang))))
            else:
                in_code = False
                code_lang = ''
                out.append(dim('└' + '─' * 22))
            continue

        if in_code:
            out.append(dim('│ ') + white(ln))
            continue

        # Headers
        if ln.startswith('### '):
            out.append(bold(cyan('### ' + ln[4:])))
        elif ln.startswith('## '):
            out.append(bold(cyan('## ' + ln[3:])))
        elif ln.startswith('# '):
            out.append(bold(cyan('# ' + ln[2:])))
        # Horizontal rule
        elif re.match(r'^---+$', ln):
            out.append(dim('─' * min(w, 60)))
        # Unordered list
        elif re.match(r'^[*\-] ', ln):
            content = _inline_fmt(ln[2:])
            out.append(dim('  • ') + content)
        # Ordered list
        elif re.match(r'^\d+\. ', ln):
            m2 = re.match(r'^(\d+)\. (.*)', ln)
            if m2:
                out.append(cyan(f'  {m2.group(1)}.') + ' ' + _inline_fmt(m2.group(2)))
            else:
                out.append(_inline_fmt(ln))
        # Blockquote
        elif ln.startswith('> '):
            out.append(dim('│ ') + italic(ln[2:]))
        else:
            out.append(_inline_fmt(ln))

    return '\n'.join(out)

def _inline_fmt(text: str) -> str:
    if not _TTY:
        return text
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', lambda m: bold(m.group(1)), text)
    # Italic
    text = re.sub(r'\*(.+?)\*', lambda m: italic(m.group(1)), text)
    # Inline code
    text = re.sub(r'`([^`]+)`', lambda m: cyan(m.group(1)), text)
    # Links — show title only
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', lambda m: cyan(m.group(1)), text)
    return text

# ── Tool call display ─────────────────────────────────────────────────────────

def print_tool_call(name: str, args: Dict[str, Any], step: int = 0) -> None:
    label = f'  {cyan("⚙")} {bold(name)}'
    # Show first arg inline for common tools
    first_val = ''
    key_order = ['path', 'file_path', 'command', 'url', 'query', 'fact', 'code', 'text']
    for k in key_order:
        if k in args:
            v = str(args[k])[:80]
            first_val = f' {dim(k + "=")} {v}'
            break
    if not first_val and args:
        k = next(iter(args))
        first_val = f' {dim(k + "=")} {str(args[k])[:80]}'
    print(label + first_val)

def print_tool_result(result: str, is_error: bool = False) -> None:
    lines = result.strip().split('\n')
    max_lines = 12
    color = red if is_error else dim
    prefix = '  ✗ ' if is_error else '  '
    if len(lines) <= max_lines:
        for ln in lines:
            print(color(prefix) + (red(ln) if is_error else dim(ln)))
    else:
        for ln in lines[:max_lines]:
            print(color(prefix) + (red(ln) if is_error else dim(ln)))
        print(dim(f'  … {len(lines) - max_lines} more lines'))

# ── File edit display (diff-style) ────────────────────────────────────────────

def print_file_edit(path: str, old_lines: List[str], new_lines: List[str], max_context: int = 5) -> None:
    """Print a git-style diff of a file edit."""
    import difflib
    diff = list(difflib.unified_diff(old_lines, new_lines,
                                      fromfile=f'a/{path}', tofile=f'b/{path}',
                                      n=max_context, lineterm=''))
    if not diff:
        print(dim(f'  (no changes to {path})'))
        return
    print()
    print(dim(f'  Edit: {path}'))
    for line in diff[:80]:
        if line.startswith('+++') or line.startswith('---'):
            print(dim(f'  {line}'))
        elif line.startswith('@@'):
            print(cyan(f'  {line}'))
        elif line.startswith('+'):
            print(green(f'  {line}'))
        elif line.startswith('-'):
            print(red(f'  {line}'))
        else:
            print(dim(f'  {line}'))

# ── Conversation prompt ───────────────────────────────────────────────────────

def prompt(label: str = 'Devin') -> str:
    """Read a line of input with a Claude Code-style prompt."""
    prompt_str = f'\n{bold(cyan("❯"))} {bold(label)} '
    try:
        return input(prompt_str).strip()
    except (EOFError, KeyboardInterrupt):
        raise KeyboardInterrupt

def print_response(text: str, label: str = 'Devin') -> None:
    """Print the assistant's response with proper formatting."""
    if not text.strip():
        return
    rendered = render_markdown(text)
    prefix = f'\n{bold(cyan(label))}  '
    continuation = '       '
    # Word-wrap long lines
    out_lines = []
    for ln in rendered.split('\n'):
        raw = _strip_ansi(ln)
        w = _cols()
        if len(raw) > w:
            wrapped = textwrap.fill(ln, width=w, subsequent_indent=continuation,
                                     break_long_words=False, break_on_hyphens=False)
            out_lines.append(wrapped)
        else:
            out_lines.append(ln)
    print(prefix + (f'\n{continuation}').join(out_lines))

def print_info(msg: str) -> None:
    print(dim(f'  ℹ {msg}'))

def print_success(msg: str) -> None:
    print(green(f'  ✓ {msg}'))

def print_error(msg: str) -> None:
    print(red(f'  ✗ {msg}'))

def print_warning(msg: str) -> None:
    print(yellow(f'  ⚠ {msg}'))

# ── Permission prompt ─────────────────────────────────────────────────────────

def confirm_action(action: str, detail: str = '') -> bool:
    """Ask user to confirm a potentially dangerous action."""
    print()
    print(yellow(f'  ⚠  Permission required'))
    print(f'     {bold(action)}')
    if detail:
        print(dim(f'     {detail}'))
    try:
        ans = input(f'  Allow? [{green("y")}/{red("n")}] ').strip().lower()
        return ans in ('y', 'yes')
    except (EOFError, KeyboardInterrupt):
        return False

# ── Status display ────────────────────────────────────────────────────────────

def print_status(provider_name: str, model: str, tools: int,
                  loaded_modules: int, total_modules: int, memories: int,
                  platform: str, has_display: bool) -> None:
    print()
    print(f'  {bold("Provider")}    {green(provider_name)}')
    print(f'  {bold("Model")}       {cyan(model)}')
    print(f'  {bold("Tools")}       {tools}')
    print(f'  {bold("Modules")}     {loaded_modules}/{total_modules} loaded')
    print(f'  {bold("Memory")}      {memories} facts')
    print(f'  {bold("Platform")}    {platform}  {"GUI" if has_display else dim("headless")}')
    print()

# ── Progress bar ─────────────────────────────────────────────────────────────

def progress_bar(current: int, total: int, width: int = 30, label: str = '') -> str:
    if total <= 0:
        return ''
    pct = min(1.0, current / total)
    filled = int(pct * width)
    bar = green('█' * filled) + dim('░' * (width - filled))
    pct_str = f'{int(pct * 100)}%'
    return f'  [{bar}] {pct_str}' + (f' {dim(label)}' if label else '')

# ── Thinking display ──────────────────────────────────────────────────────────

def print_thinking(thought: str, collapsed: bool = True) -> None:
    """Display extended thinking block."""
    if collapsed:
        lines = thought.strip().split('\n')
        preview = lines[0][:80] + ('…' if len(lines[0]) > 80 or len(lines) > 1 else '')
        print(dim(f'  💭 {italic(preview)}'))
    else:
        print(dim('  💭 Thinking:'))
        for ln in thought.split('\n')[:20]:
            print(dim(f'     {ln}'))

# ── Session summary ───────────────────────────────────────────────────────────

def print_session_stats(stats: Dict[str, Any]) -> None:
    elapsed = time.time() - stats.get('started_at', time.time())
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    print()
    print(bold('Session Stats'))
    print(hr())
    print(f'  Duration:       {mins}m {secs}s')
    print(f'  Agent steps:    {stats.get("agent_steps", 0)}')
    print(f'  Tool calls:     {stats.get("tool_calls", 0)}')
    print(f'  Errors:         {stats.get("errors", 0)}')
    print(f'  Tasks done:     {stats.get("tasks_completed", 0)}')
    top_tools = sorted(stats.get('tool_usage', {}).items(), key=lambda x: x[1], reverse=True)[:5]
    if top_tools:
        print(f'  Top tools:      ' + '  '.join(f'{n}({c})' for n, c in top_tools))
    print()
