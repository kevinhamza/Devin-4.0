"""
modules/screen_vision.py — the universal computer-use loop.

One loop for every application, with nothing app-specific in it:

    LOOK    take a screenshot and list what is on it
    THINK   the local model reasons about the task and writes the next actions,
            as far ahead as it can foresee
    ACT     real pointer and keyboard, one action at a time, at a human pace
    CHECK   after EVERY action: wait for the screen to settle, take a new screenshot
            and compare it with what the action was supposed to do
    …the moment the screen disagrees with the plan, the remaining plan is thrown
      away and the model is shown the new screen. "done" is only accepted after the
      claim has been checked against the screen.

Why a plan instead of one model call per click: a small local model on a laptop CPU
reads a few tokens per second, so every call costs minutes, and such a model is far
better at laying out the steps of a task than at picking one action from a list.
The checking after each action costs no model time at all — it is done here, from the
screenshot. A fast, strong model simply writes shorter plans and looks more often.

What the model gets to see:
  * a numbered text list of on-screen elements, gathered from the accessibility tree
    and from OCR of the screenshot (`tesseract`);
  * a vision model also receives the screenshot itself — always when it is fast and
    strong; a small slow one only when the screenshot has almost no readable text,
    because it judges the text far better than a shrunken picture (see DEVIN_EYES).

    from modules.screen_vision import ComputerAgent
    result = ComputerAgent(on_event=print).run('open the calculator and compute 12*7')

Environment:
    DEVIN_MAX_STEPS      most actions per task (default 40)
    DEVIN_MAX_THINKS     most times the model may be consulted per task (default 10)
    DEVIN_PROFILE        lean | full | auto   — short prompts for slow models (auto: measured)
    DEVIN_EYES           auto | always | never — when a vision model is sent the screenshot
    DEVIN_THINK          auto | on | off      — the model's own "thinking" phase
    DEVIN_ALLOW_SHELL    1 lets Devin run commands directly instead of through a terminal window
    DEVIN_TRACE          1 writes every prompt, reply and outcome to $XDG_RUNTIME_DIR/devin/trace.jsonl
"""
from __future__ import annotations

import csv
import difflib
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

try:
    from modules import os_automation as oa
    from modules import ollama_provider as llm
except ImportError:  # loaded as a top-level module
    import os_automation as oa  # type: ignore
    import ollama_provider as llm  # type: ignore


# ══════════════════════════════════════════════════════════════════════════════
# LOOK
# ══════════════════════════════════════════════════════════════════════════════

_INPUT_ROLES = {'entry', 'password text', 'text', 'search bar', 'combo box', 'spin button'}
_ROLE_NAMES = {'push button': 'button', 'toggle button': 'button', 'password text': 'password field',
               'entry': 'input', 'text': 'input', 'search bar': 'input', 'page tab': 'tab',
               'menu item': 'menu item', 'check menu item': 'menu item', 'radio menu item': 'menu item',
               'check box': 'checkbox', 'radio button': 'radio', 'combo box': 'dropdown',
               'list item': 'item', 'tree item': 'item', 'table cell': 'cell', 'document web': 'page',
               'spin button': 'number input', 'tool bar': 'toolbar'}


def _norm(text: str) -> str:
    """Lower-case letters and digits only, single spaces: for comparing labels."""
    return re.sub(r'[^a-z0-9]+', ' ', str(text).lower()).strip()


def _norm_title(title: str) -> str:
    """A window title without the decoration some programs animate in front of it."""
    return re.sub(r'^[^\w@~/]+', '', title or '').strip().lower()


def _clip(text: str, n: int) -> str:
    text = str(text).replace('\n', ' ')
    return text if len(text) <= n else text[:n - 1] + '…'


@dataclass
class Element:
    id: int
    role: str
    name: str
    x: int
    y: int
    w: int
    h: int
    value: str = ''
    focused: bool = False
    source: str = 'a11y'  # 'a11y' or 'ocr'
    shell: bool = False   # belongs to the desktop itself (top bar, dock, launcher), not to a window

    @property
    def center(self) -> Tuple[int, int]:
        return self.x + self.w // 2, self.y + self.h // 2

    @property
    def kind(self) -> str:
        return _ROLE_NAMES.get(self.role, self.role)

    @property
    def typable(self) -> bool:
        return self.role in _INPUT_ROLES

    @property
    def key(self) -> Tuple[str, str]:
        return self.kind, self.name.lower()

    def line(self, compact: bool = False) -> str:
        cx, cy = self.center
        if compact:  # every token counts on a slow local model
            kind = '' if self.kind == 'label' else self.kind + ' '   # plain text on screen: just its name
            text = f'{self.id} {kind}"{_clip(self.name, 28)}"'
            if self.value and self.value != self.name:
                text += f' ="{_clip(self.value, 30)}"'
            return text + (' FOCUS' if self.focused else '')
        text = f'[{self.id}] {self.kind} "{self.name}" ({cx},{cy})'
        if self.value and self.value != self.name:
            text += f' contains "{self.value[:60]}"'
        if self.focused:
            text += ' <- keyboard focus'
        return text


@dataclass
class Observation:
    image: Any
    width: int
    height: int
    window: str = ''
    app: str = ''
    elements: List[Element] = field(default_factory=list)
    seconds: float = 0.0
    rect: Tuple[int, ...] = ()    # x, y, width, height of the window in front, when known
    launcher_open: bool = False   # the desktop's app search / overview is showing instead of a window

    @property
    def has_window(self) -> bool:
        """Is an application window in front (even one that does not tell its name)?"""
        return bool(self.window) or (bool(self.rect) and not self.launcher_open)

    def scene(self) -> Tuple[str, Tuple[int, ...]]:
        """Identifies the window in front: its application and where it sits (to the nearest 40
        pixels). A page changing inside a window keeps the scene; a dialog, a chooser or
        another program is a new one."""
        return self.app, tuple(v // 40 for v in self.rect)

    def element(self, eid: Any) -> Optional[Element]:
        try:
            eid = int(eid)
        except (TypeError, ValueError):
            return None
        for e in self.elements:
            if e.id == eid:
                return e
        return None

    def front(self, own: bool = False) -> str:
        """One line saying which window has the keyboard."""
        if self.window:
            if own:
                return (f'FRONT WINDOW: "{_clip(self.window, 40)}" - the terminal Devin itself runs in. '
                        'Do not type or press keys here; open the app the TASK needs.')
            app = f' ({self.app})' if self.app and _norm(self.app) not in _norm(self.window) else ''
            return f'FRONT WINDOW: "{_clip(self.window, 60)}"{app}'
        if self.launcher_open:
            return 'FRONT WINDOW: none - the app search is open (type an app name, then click its icon)'
        if self.rect:
            return 'FRONT WINDOW: an application window (it does not tell its name; see what is on it below)'
        return 'FRONT WINDOW: none (empty desktop)'

    def focused_input(self) -> Optional[Element]:
        """The field the keyboard is in, when the screen says so."""
        fields = [e for e in self.elements if e.focused and e.typable]
        if fields:
            return fields[0]
        anything = [e for e in self.elements if e.focused]
        return anything[0] if anything else None

    def shows(self, text: str) -> bool:
        """Is this text readable somewhere on the screen? (tolerant of OCR slips)"""
        want = _norm(text)
        if not want:
            return True
        probe = want[:14]
        joined = ' '.join(_norm(e.name + ' ' + e.value) for e in self.elements)
        if probe in joined:
            return True
        squeezed = joined.replace(' ', '')
        if probe.replace(' ', '') in squeezed:
            return True
        first = want.split()[0]
        if len(first) >= 4:
            for word in set(joined.split()):
                if abs(len(word) - len(first)) <= 2 and difflib.SequenceMatcher(None, word, first).ratio() >= 0.8:
                    return True
        return False

    def top(self, limit: int = 0, focus: str = '', hidden: Iterable[Tuple[str, str]] = (),
            brief: bool = False) -> List[Element]:
        """The `limit` elements most likely to matter, in reading order.

        Kept, in this order of preference: fields that can be typed into and whatever has
        the keyboard; anything whose text shares a word with `focus` (the task and the
        current thought); real controls of the window in front; the desktop's own
        launcher and dock entries; short labels; long passages of text; the top bar;
        bare numbers and symbols.
        """
        hidden = set(hidden)
        items = [e for e in self.elements if e.key not in hidden]
        words = set(re.findall(r'[a-z0-9]{3,}', focus.lower())) - _FILLER
        if brief:
            # Paragraphs read off the pixels (a document, a terminal's scrollback) are not
            # things to click; on a slow model each one costs seconds for nothing.
            items = [e for e in items if e.source != 'ocr' or len(e.name.split()) <= 4
                     or any(w in e.name.lower() for w in words)]
        if not limit or len(items) <= limit:
            return items

        def weight(e: Element):
            name = (e.name + ' ' + e.value).lower()
            if e.typable or e.focused:
                rank = 0
            elif (words and any(w in name for w in words)) or (e.shell and _LAUNCHERS.match(e.name.strip())):
                rank = 1
            elif e.shell and e.y < 40:
                rank = 6                      # clock, meters and menus in the top bar
            elif e.source == 'a11y' and e.role != 'label':
                rank = 2 if not e.shell else 3
            elif not re.search(r'[a-z]{3,}', name):
                rank = 7
            else:
                rank = 4 if len(name.split()) <= 4 else 5
            return rank, e.y, e.x
        chosen = sorted(items, key=weight)[:limit]
        return sorted(chosen, key=lambda e: e.id)

    def describe(self, compact: bool = False, limit: int = 0, focus: str = '',
                 hidden: Iterable[Tuple[str, str]] = (), own: bool = False) -> str:
        items = self.top(limit, focus, hidden, brief=compact)
        if compact:
            if not items:
                return self.front(own) + '\nON SCREEN: nothing readable.'
            return (self.front(own) + '\nON SCREEN (each can be clicked by its name):\n'
                    + '\n'.join(e.line(True) for e in items))
        head = f'SCREEN {self.width}x{self.height}'
        if self.window or self.app:
            head += f' - window in front: "{self.window or "?"}"' + (f' ({self.app})' if self.app else '')
        if not items:
            return head + '\n(no readable elements on screen)'
        return head + '\n' + '\n'.join(e.line() for e in items)

    def marked(self, items: Optional[List[Element]] = None):
        """The screenshot with each listed element boxed and numbered (for vision models)."""
        from PIL import ImageDraw, ImageFont
        img = self.image.copy()
        draw = ImageDraw.Draw(img, 'RGBA')
        try:
            font = ImageFont.load_default(size=12)
        except TypeError:
            font = ImageFont.load_default()
        palette = [(255, 64, 64), (64, 160, 255), (80, 220, 100), (255, 170, 0), (200, 100, 255), (0, 210, 210)]
        for e in (self.elements if items is None else items):
            color = palette[e.id % len(palette)]
            draw.rectangle([e.x, e.y, e.x + e.w, e.y + e.h], outline=color + (255,), width=1)
            label = str(e.id)
            tw = int(draw.textlength(label, font=font)) + 4
            lx, ly = e.x, max(0, e.y - 13)
            draw.rectangle([lx, ly, lx + tw, ly + 13], fill=color + (235,))
            draw.text((lx + 2, ly), label, fill=(0, 0, 0, 255), font=font)
        return img

    def small(self, side: int = 336):
        """A reduced copy of the screenshot: enough to recognise what is on screen, cheap to read."""
        img = self.image.copy()
        img.thumbnail((side, side))
        return img

    def save(self, path: str, marked: bool = False) -> str:
        (self.marked() if marked else self.image).save(path)
        return path


def ocr_available() -> bool:
    return bool(shutil.which('tesseract'))


def ocr_lines(image, scale: float = 1.0) -> List[Dict[str, Any]]:
    """Text found in the pixels, one entry per phrase, with its box in screen coordinates."""
    if not ocr_available():
        return []
    from PIL import ImageOps, ImageStat
    gray = image.convert('L')
    if ImageStat.Stat(gray).mean[0] < 110:  # dark theme: tesseract wants dark text on light
        gray = ImageOps.invert(gray)
    big = gray if scale == 1.0 else gray.resize((int(gray.width * scale), int(gray.height * scale)))
    buf = io.BytesIO()
    big.save(buf, 'PNG')
    try:
        # One thread is the fastest setting for tesseract on a screenshot-sized image.
        r = subprocess.run(['tesseract', 'stdin', 'stdout', '--psm', '11', '-l', 'eng', 'tsv'],
                           input=buf.getvalue(), capture_output=True, timeout=30,
                           env={**os.environ, 'OMP_THREAD_LIMIT': '1'})
    except (subprocess.TimeoutExpired, OSError):
        return []
    if r.returncode != 0:
        return []
    words: List[Dict[str, Any]] = []
    reader = csv.DictReader(io.StringIO(r.stdout.decode('utf-8', 'replace')), delimiter='\t',
                            quoting=csv.QUOTE_NONE)
    for row in reader:
        text = (row.get('text') or '').strip()
        try:
            conf = float(row.get('conf') or -1)
            if not text or conf < 60:
                continue
            words.append({'key': (row['block_num'], row['par_num'], row['line_num']), 'text': text,
                          'x': int(row['left']) / scale, 'y': int(row['top']) / scale,
                          'w': int(row['width']) / scale, 'h': int(row['height']) / scale})
        except (KeyError, ValueError):
            continue
    # Join neighbouring words on the same line into phrases; a wide gap starts a new one.
    phrases: List[Dict[str, Any]] = []
    for wd in words:
        last = phrases[-1] if phrases else None
        if (last and last['key'] == wd['key'] and wd['x'] - (last['x'] + last['w']) < max(14, last['h'] * 1.2)
                and abs(wd['y'] - last['y']) < last['h']):
            right = max(last['x'] + last['w'], wd['x'] + wd['w'])
            bottom = max(last['y'] + last['h'], wd['y'] + wd['h'])
            last['y'] = min(last['y'], wd['y'])
            last['w'], last['h'] = right - last['x'], bottom - last['y']
            last['text'] += ' ' + wd['text']
        else:
            phrases.append(dict(wd))
    return [{'role': 'label', 'name': p['text'][:80], 'x': int(p['x']), 'y': int(p['y']),
             'w': max(1, int(p['w'])), 'h': max(1, int(p['h']))}
            for p in phrases if _wordlike(p['text'])]


def _wordlike(text: str) -> bool:
    """True for real labels ('Images', 'Sign in', '84'); False for OCR debris ('oo', '(SED', 'GD')."""
    clean = re.sub(r'[^A-Za-z0-9]', '', text)
    if clean.isdigit():
        return True
    words = re.findall(r'[A-Za-z]{3,}', text)
    if not words:
        return False
    # debris is typically one short all-caps or vowel-less scrap
    return any(re.search(r'[aeiouyAEIOUY]', w) and not (len(w) <= 3 and w.isupper()) for w in words)


def _overlaps(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    ax, ay = a['x'] + a['w'] / 2, a['y'] + a['h'] / 2
    return b['x'] - 4 <= ax <= b['x'] + b['w'] + 4 and b['y'] - 4 <= ay <= b['y'] + b['h'] + 4


def look(desktop: Optional[oa.Desktop] = None, max_elements: int = 140, use_ocr: Optional[bool] = None,
         a11y_budget: float = 1.5, focus: str = '') -> Observation:
    """Take a screenshot and list everything nameable on it.

    Two readers run at the same time on the same instant of the screen: the
    accessibility tree (exact names, roles and which field has the keyboard) and OCR of
    the pixels (everything the tree does not know about: web pages, canvases, terminals).
    `Observation.top()` later picks what to show a model; nothing is thrown away here
    unless there are more than `max_elements`.
    """
    d = desktop or oa.get_desktop()
    t0 = time.monotonic()
    image = d.capture()
    if use_ocr is None:
        use_ocr = ocr_available()
    ocr_result: List[Dict[str, Any]] = []
    reader = None
    if use_ocr:
        reader = threading.Thread(target=lambda: ocr_result.extend(ocr_lines(image)), daemon=True)
        reader.start()
    info = d.elements(budget=a11y_budget, limit=max_elements * 2)
    raw: List[Dict[str, Any]] = []
    for e in info.get('elements', []):
        e = dict(e, source='a11y')
        role = e['role']
        # A "text" node is a field when it can be edited or holds the keyboard; otherwise
        # it is just words on the screen (the desktop shell draws all its labels this way).
        typable = role in _INPUT_ROLES - {'text'} or (role == 'text' and (e.get('editable') or e.get('focused')))
        if role == 'text':
            e['role'] = 'entry' if typable else 'label'
        if not typable and not e.get('name') and e.get('value'):
            e['name'], e['value'] = e['value'], ''      # a label: its text is its name
            e['role'] = 'label'
        if e.get('name') or typable:
            raw.append(e)
    # The app search / overview has a field of its own to type into; a plain desktop with a
    # window in front does not.
    launcher_open = any(e.get('shell') and e['role'] in _INPUT_ROLES for e in raw)
    rect = list(info.get('rect') or [])
    if not info.get('window') and not launcher_open:
        rect = list(info.get('top_rect') or [])     # a window is in front but does not say its name
    if not info.get('window') and not rect:
        launcher_open = True
    if reader is not None:
        reader.join(timeout=35)
        if not launcher_open and len(rect) == 4 and rect[2] > 80 and rect[3] > 80:
            # Text read off the pixels counts only inside the window in front. Whatever shows
            # around a smaller window belongs to windows behind it and cannot be clicked there.
            x0, y0, x1, y1 = rect[0] - 6, rect[1] - 6, rect[0] + rect[2] + 6, rect[1] + rect[3] + 6
            ocr_result = [ln for ln in ocr_result
                          if x0 <= ln['x'] + ln['w'] / 2 <= x1 and y0 <= ln['y'] + ln['h'] / 2 <= y1]
        for line in ocr_result:
            key = re.sub(r'\W', '', line['name'].lower())[:10]
            same = [e for e in raw if (_overlaps(line, e) or _overlaps(e, line))
                    and key and key in re.sub(r'\W', '', (e['name'] + e.get('value', '')).lower())]
            if not same:
                raw.append(dict(line, source='ocr'))
    # one entry per label per place
    seen, unique = set(), []
    for e in raw:
        k = (e['name'].lower(), e['x'] // 20, e['y'] // 12)
        if k not in seen:
            seen.add(k)
            unique.append(e)
    raw = unique

    w, h = image.size
    raw = [e for e in raw if e['w'] < w * 0.98 or e['h'] < h * 0.9 or e['role'] in _INPUT_ROLES]
    raw.sort(key=lambda e: (e['y'] // 12, e['x']))
    elements = [Element(id=i, role=e['role'], name=e.get('name', ''), x=e['x'], y=e['y'], w=e['w'], h=e['h'],
                        value=e.get('value', ''), focused=bool(e.get('focused')), source=e['source'],
                        shell=bool(e.get('shell')))
                for i, e in enumerate(raw, start=1)]
    obs = Observation(image=image, width=w, height=h, window=info.get('window', ''),
                      app=info.get('app', ''), elements=elements, seconds=time.monotonic() - t0,
                      rect=tuple(int(v) for v in rect) if not launcher_open else (),
                      launcher_open=launcher_open)
    if len(elements) > max_elements:
        obs.elements = obs.top(max_elements, focus)
    return obs


_FILLER = {'the', 'and', 'for', 'icon', 'button', 'link', 'tab', 'item', 'option', 'field', 'box',
           'with', 'this', 'that', 'into', 'from', 'click', 'open', 'show', 'then'}
_CONTROLS = {'button', 'link', 'input', 'tab', 'menu item', 'menu', 'checkbox', 'radio', 'dropdown',
             'item', 'icon', 'switch', 'password field', 'number input'}


def match_element(elements: List[Element], label: str) -> Optional[Element]:
    """The element a person would mean by `label` ('Images', 'the Sign in button', 'Search')."""
    exact = str(label).strip().lower()
    if not exact:
        return None
    for e in elements:                       # "=", "+", "×": labels with no letters at all
        if e.name.strip().lower() == exact:
            if e.kind in _CONTROLS or not re.search(r'[a-z0-9]', exact):
                return e
    want = _norm(label)
    if not want:
        return None
    trimmed = ' '.join(w for w in want.split() if w not in _FILLER)
    wants = [want] + ([trimmed] if trimmed and trimmed != want else [])
    best: Optional[Element] = None
    best_score = 0.0
    for e in elements:
        score = 0.0
        # What a field currently contains is not its label: text just typed into a search box
        # must not make the box itself the best match for the thing being searched for.
        for have, weight in ((_norm(e.name), 1.0), (_norm(e.value), 0.0 if e.typable else 0.7)):
            if not have or not weight:
                continue
            for w in wants:
                if have == w:
                    s = 1.0
                elif have.startswith(w) or (w.startswith(have) and len(have) >= 4):
                    s = 0.9 * (0.7 + 0.3 * min(len(w), len(have)) / max(len(w), len(have)))
                elif w in have:
                    s = 0.8 * (0.6 + 0.4 * len(w) / len(have))
                else:
                    wt, ht = set(w.split()), set(have.split())
                    overlap = len(wt & ht) / len(wt)
                    s = 0.72 * overlap if overlap >= 0.6 else 0.0
                    if not s:
                        # the same name written with or without spaces: "Burp Suite Community" / "burpsuite"
                        a, b = w.replace(' ', ''), have.replace(' ', '')
                        short, long = (a, b) if len(a) <= len(b) else (b, a)
                        if len(short) >= 5 and (long.startswith(short) or (len(short) >= 7 and short in long)):
                            s = 0.7 * (0.75 + 0.25 * len(short) / len(long))
                    if not s and abs(len(w) - len(have)) <= 3:      # OCR slip: "lmages" for "Images"
                        ratio = difflib.SequenceMatcher(None, w, have).ratio()
                        s = 0.75 * ratio if ratio >= 0.8 else 0.0
                score = max(score, s * weight)
        if not score:
            continue
        if e.kind in _CONTROLS and e.source == 'a11y':
            score += 0.06                    # a real control beats the same words in a paragraph
        if e.shell and e.y < 40:
            score -= 0.04
        if score > best_score:
            best, best_score = e, score
    return best if best_score >= 0.55 else None


# ══════════════════════════════════════════════════════════════════════════════
# THINK
# ══════════════════════════════════════════════════════════════════════════════

# Only what a person can do at the desk: point, click, type, press keys, scroll, drag, wait.
# There is deliberately no "open application" action — Devin opens programs by pressing
# keys and clicking on the screen like anyone else.
ACTIONS = ('click', 'type', 'key', 'scroll', 'drag', 'shell', 'wait', 'done', 'fail')


def shell_allowed() -> bool:
    """Off by default: Devin works the way a person does, through windows, pointer and keys.
    With DEVIN_ALLOW_SHELL=1 it may also run commands directly without a terminal window."""
    return os.environ.get('DEVIN_ALLOW_SHELL', '0').strip().lower() in ('1', 'true', 'yes', 'on')


def action_names() -> List[str]:
    return [a for a in ACTIONS if a != 'shell' or shell_allowed()]


LEAN_PROMPT = """You are Devin. You do the user's TASK on this {os} desktop with the mouse and keyboard, like a person. Reply with a THINK line, then actions, one per line:
click "name"        (click the item with that name)
type "text" ENTER   (type it; ENTER is optional and presses Enter too)
key escape          (press a key: enter, tab, alt+tab ...)
done "what the screen shows"   (last line, only when the whole TASK is finished)
To open an app: {open_rule}. Typing goes to the window in front: open the right app and click a field first. If a question, dialog or chooser is in the way, answer it first by clicking one of its options.
Example, task "write hello in the text editor":
THINK: The editor is not open; open it, then type.
{open_example}
type "hello"
done "the text editor shows hello\""""

FULL_PROMPT = """You are Devin. You operate this {os} computer for the user with the mouse and keyboard, like a person sitting in front of it.

Every turn you are shown the task, what is on the screen right now, and what you have already done. Think about where things stand, then write the next actions.

Reply format — plain text, no JSON:
THINK: one or two sentences: what the screen shows, and what has to happen next.
then one action per line, as many as you are sure of from this screen (often just one or two):
key NAME                 press a key or shortcut: enter, escape, tab, ctrl+l, ctrl+t, alt+tab, alt+f4, super …
type "text"              type on the keyboard into whatever has keyboard focus; write ENTER after it to also press Enter
click "name"             click the element showing that text
click N                  click element number N from the SCREEN list (only as the first action of a reply){xy_hint}
double-click "name"      right-click "name"
scroll down 3            scroll the window (up or down, a number of notches)
drag X,Y to X2,Y2
{shell_line}wait 2                   wait seconds while something loads
done "result"            the task is complete: say what the screen shows, or answer the user's question
fail "reason"            the task is impossible

Rules:
- Only act on what is really on the screen. After an action that changes the screen a lot, stop writing actions: you will be shown the new screen.
- Work the way a person does: move the mouse to things and click them; use the keyboard for text and for shortcuts you are sure of.
- To open an application or switch to one: {open_rule}. Then check that it is in front.
- Typing goes to the window in front. Put the keyboard in the right field first by clicking it.
- If a dialog, a question, a chooser or anything unexpected is in the way, deal with it first: pick the sensible option or close it, then go on with the task.
- If an action changed nothing or went wrong, do NOT repeat it. Try a different way.
- Keep going until the task is really finished. Do not stop half way and do not give up after one failed try.
- Use "done" only when the screen in front of you SHOWS the finished result. Your claim will be checked against the screen."""

_SHELL_ON = ('shell COMMAND            run a terminal command and read its output (files, system information, '
             'installing tools); not for programs that have a window\n')
_TERMINAL_RULE = ('\n- To run a command, do it like a person: open the Terminal application, type the command '
                  'with ENTER, then read the result on the screen.')

VERIFY_SYSTEM = ('You check whether a computer task was carried out, judging from the screenshot and the screen '
                 'text you are given. Judge only what the TASK asked for, nothing extra. Answer YES when the screen '
                 'shows it; answer NO when the screen does not show it.')

LEAN_CTX = 2048   # a lean call is ~400 tokens; a small window keeps the model's memory use down
_speed: Dict[str, float] = {}   # measured prompt-reading speed per model, tokens per second


def lean_profile(model: str) -> bool:
    """Slow local models get a short prompt and a short list; fast ones get everything."""
    choice = os.environ.get('DEVIN_PROFILE', 'auto').strip().lower()
    if choice in ('lean', 'full'):
        return choice == 'lean'
    if model in _speed:
        return _speed[model] < 150
    return not model.endswith('cloud')


def _os_name() -> str:
    name = {'Linux': 'Linux', 'Darwin': 'macOS', 'Windows': 'Windows'}.get(oa.PLATFORM, oa.PLATFORM)
    desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').split(':')[-1]
    return f'{name} ({desktop})' if desktop else name


_LAUNCHERS = re.compile(r'^(activities|applications|application launcher|app launcher|launcher|start|'
                        r'show applications|menu|whisker menu)$', re.I)


def launcher_label(obs: Optional[Observation]) -> str:
    """The name of this desktop's launcher button as it appears on the screen, or ''."""
    if obs is not None:
        for e in obs.elements:
            if e.y < 70 or e.y > obs.height - 70 or e.shell:
                if _LAUNCHERS.match(e.name.strip()):
                    return e.name.strip()
    return ''


def _open_rule(obs: Optional[Observation]) -> Tuple[str, str]:
    """(the rule in words, the same thing as example action lines) for opening an application."""
    button = launcher_label(obs)
    first = f'click "{button}"' if button else 'key super'
    return (f'{first}, type its name, click its icon',
            f'{first}\ntype "text editor"\nclick "Text Editor"')


def lean_system_prompt(obs: Optional[Observation] = None) -> str:
    rule, example = _open_rule(obs)
    text = LEAN_PROMPT.format(os=_os_name(), open_rule=rule, open_example=example)
    if shell_allowed():
        text += '\nshell COMMAND runs a terminal command directly and shows you its output.'
    return text


def system_prompt(vision: bool, obs: Optional[Observation] = None) -> str:
    xy = '\nclick X,Y                click at screenshot pixel X,Y when the thing has no label' if vision else ''
    text = FULL_PROMPT.format(os=_os_name(), xy_hint=xy, shell_line=_SHELL_ON if shell_allowed() else '',
                              open_rule=_open_rule(obs)[0])
    if not shell_allowed():
        text += _TERMINAL_RULE
    if vision:
        text += ('\n- You are given the screenshot itself. Look at it carefully before you decide; '
                 'the numbered boxes on it match the numbers in the SCREEN list.')
    return text


def _unquote(text: str) -> str:
    text = text.strip()
    for a, b in (('"', '"'), ("'", "'"), ('“', '”'), ('`', '`')):
        if len(text) >= 2 and text.startswith(a) and text.endswith(b):
            return text[1:-1]
    return text.strip('"“”')


def _is_key(combo: str) -> bool:
    """True when every part of 'ctrl+shift+t' is a key that exists."""
    parts = oa.split_combo(combo)
    if len(parts) == 1 and len(parts[0]) == 1 and not parts[0].isalnum():
        return False                        # a stray dash or dot is punctuation, not a key press
    return bool(parts) and all(len(k) == 1 or k in oa._KEYS for k in parts)


_ENTER_TAIL = re.compile(r'^[\s,+;]*(?:(?:and|then)\s+)?(?:press\s+|hit\s+)?(?:the\s+)?enter(?:\s+key)?[\s.]*$', re.I)
_VERBS = ('double-click', 'double click', 'doubleclick', 'right-click', 'right click', 'rightclick',
          'middle-click', 'click', 'type', 'write', 'key', 'press', 'hotkey', 'scroll', 'wait', 'drag',
          'done', 'fail', 'shell', 'run', '$')


def parse_action(line: str, obs: Optional[Observation] = None) -> Optional[Dict[str, Any]]:
    """One action line → {'action': …}. Returns None for anything that is not an action."""
    line = line.strip().strip('`').strip()
    line = re.sub(r'^(?:\d+\s*[.):]|[-*•>])\s+', '', line)                  # "1. key super", "- key super"
    line = re.sub(r'^(?:do|action|next|step\s*\d*)\s*[:\-]\s*', '', line, flags=re.I)
    low = line.lower()
    verb = next((v for v in _VERBS if low == v or low.startswith(v + ' ') or low.startswith(v + ':')
                 or (v in ('done', 'fail', 'click', 'type', 'key') and low.startswith(v + '"'))), None)
    if verb is None:
        bare = low.strip(' .')
        if re.fullmatch(r'[a-z0-9_+]{2,24}', bare) and _is_key(bare) and (
                '+' in bare or oa.normalize_key(bare) in oa._KEYS):
            return {'action': 'key', 'keys': bare}      # a line that is just "enter" or "ctrl+l"
        return None
    rest = line[len(verb):].lstrip(' :').strip()

    if 'click' in verb:
        button = ('double' if verb.startswith('double') else 'right' if verb.startswith('right')
                  else 'middle' if verb.startswith('middle') else 'left')
        rest = re.sub(r'^(?:on|at)\s+', '', rest, flags=re.I)
        m = re.fullmatch(r'\(?\s*(\d{1,4})\s*[, ]\s*(\d{1,4})\s*\)?', rest)
        if m:
            return {'action': 'click', 'x': int(m.group(1)), 'y': int(m.group(2)), 'button': button}
        m = re.fullmatch(r'(?:item\s+|id\s+|#|\[)?(\d{1,3})\]?', rest, re.I)
        if m:
            el = obs.element(m.group(1)) if obs is not None else None
            a: Dict[str, Any] = {'action': 'click', 'id': int(m.group(1)), 'button': button}
            if el is not None and el.name:
                a['target'] = el.name       # the number is only good for this screenshot; the name lasts
            return a
        m = re.match(r'^(["“\'])(.+?)["”\']', rest)
        target = m.group(2) if m else _unquote(rest)
        if not m and len(target.split()) > 6:
            return None                     # a sentence that happens to start with "click"
        return {'action': 'click', 'target': target, 'button': button} if target else None

    if verb in ('type', 'write'):
        enter = False
        m = re.match(r'^(["“])(.*)["”](.*)$', rest, re.S) or re.match(r"^(')(.*)'(.*)$", rest, re.S)
        if m:
            text, tail = m.group(2), m.group(3)
            enter = bool(_ENTER_TAIL.match(tail) or re.search(r'\benter\b', tail[:24], re.I))
        else:
            text = rest
            m2 = re.match(r'^(.*?)\s+ENTER\s*$', rest, re.S)
            if m2:
                text, enter = m2.group(1), True
            if len(text.split()) > 8 or text.rstrip().endswith('.'):
                return None                 # a sentence that happens to start with "type"
        return {'action': 'type', 'text': text, 'enter': enter} if text else None

    if verb in ('key', 'press', 'hotkey'):
        keys = _unquote(rest).lower()
        keys = re.sub(r'\b(the|keys?|shortcut|button)\b', ' ', keys)
        keys = re.sub(r'\s*\+\s*', '+', keys).strip(' .')
        good: List[str] = []
        for part in re.split(r'[\s,;]+', keys):     # "enter to search" → enter; "ctrl+a, backspace" → both
            part = part.strip('"\'.')
            if not part or part == 'then':
                continue
            if not _is_key(part):
                break
            good.append(part)
        return {'action': 'key', 'keys': ', '.join(good)} if good else None

    if verb == 'scroll':
        m = re.search(r'\b(up|down|left|right)\b', rest, re.I)
        n = re.search(r'\d+', rest)
        return {'action': 'scroll', 'direction': m.group(1).lower() if m else 'down',
                'amount': int(n.group(0)) if n else 5}

    if verb == 'wait':
        n = re.search(r'\d+(?:\.\d+)?', rest)
        return {'action': 'wait', 'seconds': float(n.group(0)) if n else 2.0}

    if verb == 'drag':
        nums = [int(v) for v in re.findall(r'\d{1,4}', rest)]
        return ({'action': 'drag', 'x': nums[0], 'y': nums[1], 'x2': nums[2], 'y2': nums[3]}
                if len(nums) >= 4 else None)

    if verb in ('done', 'fail'):
        return {'action': verb, 'answer': _unquote(rest)}

    if verb in ('shell', 'run', '$'):
        return {'action': 'shell', 'command': _unquote(rest)} if rest and shell_allowed() else None
    return None


_SEVERAL = re.compile(r'\s+(?:-+|–|—|;|,|->|→|(?:and\s+)?then)\s+(?=(?:key|type|click|press|scroll|wait|done|'
                      r'double-click|right-click)\b)', re.I)


def parse_reply(text: str, obs: Optional[Observation] = None, limit: int = 10) -> Tuple[str, List[Dict[str, Any]]]:
    """A model reply → (the thought, the list of actions). Stops at done/fail."""
    thought = ''
    actions: List[Dict[str, Any]] = []
    lines: List[str] = []
    for raw in str(text).splitlines():      # 'key super - type "x" ENTER' is two actions
        lines.extend(_SEVERAL.split(raw))
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('```'):
            continue
        m = re.match(r'^\**(?:think|thought|thinking|plan|reasoning)\**\s*[:\-]\s*(.*)$', line, re.I)
        if m:
            thought = thought or m.group(1).strip()
            continue
        a = parse_action(line, obs)
        if a is None:
            if not thought and not actions:
                thought = line          # a model that skipped the "THINK:" label
            continue
        if a['action'] == 'click' and 'id' in a and 'target' not in a and actions:
            break                       # a bare number refers to a screen that will be gone by then
        if (a['action'] == 'key' and oa.normalize_key(a['keys']) == 'return' and actions
                and actions[-1]['action'] == 'type' and not actions[-1].get('enter')):
            actions[-1]['enter'] = True     # type "x" followed by a line "enter" is one gesture
            continue
        actions.append(a)
        if a['action'] in ('done', 'fail') or len(actions) >= limit:
            break
    return thought, actions


def describe_action(a: Dict[str, Any]) -> str:
    """How an action is shown to the user and remembered in the history."""
    kind = a.get('action')
    if kind == 'click':
        verb = {'double': 'double-click', 'right': 'right-click', 'middle': 'middle-click'}.get(
            a.get('button') or 'left', 'click')
        if a.get('target'):
            return f'{verb} "{_clip(a["target"], 40)}"'
        if a.get('x') is not None:
            return f'{verb} ({a["x"]},{a["y"]})'
        return f'{verb} item {a.get("id")}'
    if kind == 'type':
        return f'type "{_clip(a.get("text", ""), 48)}"' + (' + Enter' if a.get('enter') else '')
    if kind == 'key':
        return f'press {a.get("keys", "")}'
    if kind == 'scroll':
        return f'scroll {a.get("direction", "down")} {a.get("amount", 5)}'
    if kind == 'wait':
        return f'wait {a.get("seconds", 2):g}s'
    if kind == 'drag':
        return f'drag ({a.get("x")},{a.get("y")}) to ({a.get("x2")},{a.get("y2")})'
    if kind == 'shell':
        return '$ ' + _clip(a.get('command', ''), 70)
    if kind in ('done', 'fail'):
        return f'{kind}: {_clip(a.get("answer", ""), 60)}'
    return str(kind)


# ══════════════════════════════════════════════════════════════════════════════
# ACT
# ══════════════════════════════════════════════════════════════════════════════

_DANGEROUS = re.compile(
    r'(\brm\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*[rf][a-zA-Z]*\s+(/|~|\$HOME)(\s|$|/\*)|\bmkfs\b|\bdd\b[^|;&]*\bof=/dev/'
    r'|\b(shutdown|reboot|poweroff|halt)\b|:\(\)\s*\{|>\s*/dev/sd|\bchmod\s+-R\s+0?777\s+/(\s|$)'
    r'|\bgit\s+push\b.*--force|\bwipefs\b|\bparted\b|\bfdisk\b)')

_TERMINALS = re.compile(r'terminal|konsole|kgx|ptyxis|alacritty|kitty|xterm|tilix|wezterm|foot|console|terminator',
                        re.I)
# Things that end the session or take the machine away from the user. Devin does not touch
# them — not by click, key or typed command — unless the task itself asks for exactly that.
# (Learned the hard way: a small model, lost on an unexpected screen, wandered into the
# system menu and restarted the computer in the middle of a task.)
_SESSION_ENDERS = re.compile(r'\b(restart|reboot|power ?off|shut ?down|log ?out|sign ?out|suspend|hibernate|'
                             r'switch user|lock screen|factory reset)\b', re.I)
_SESSION_KEYS = {'ctrl+alt+delete', 'ctrl+alt+backspace', 'super+l', 'ctrl+alt+l'}
_SESSION_COMMANDS = re.compile(
    r'(^|[;&|]\s*)\s*(sudo\s+)?(reboot|shutdown|poweroff|halt|init\s+[06]\b|telinit\s+[06]\b|'
    r'systemctl\s+(reboot|poweroff|halt|suspend|hibernate|kexec)|gnome-session-quit|loginctl\s+(terminate|kill)|'
    r'pkill\s+(-\S+\s+)*(gnome-shell|-u)|killall\s+(-\S+\s+)*gnome-shell)', re.I)
_ENDING_DIALOG = re.compile(r'(will|is going to) (restart|power off|shut down|log out|be logged out)[^|]{0,60}'
                            r'(automatically|second)', re.I)

# Keys that put the keyboard into a text field (address bar, new tab, find, search…).
_FOCUS_KEYS = {'ctrl+l', 'ctrl+t', 'ctrl+k', 'ctrl+e', 'ctrl+f', 'ctrl+n', 'alt+d', 'f6', 'tab', 'shift+tab',
               'ctrl+shift+t', 'ctrl+shift+n', 'ctrl+alt+t', '/'}
_WINDOW_CLOSERS = {'alt+f4', 'ctrl+q', 'ctrl+shift+q', 'super+q'}
_TAB_CLOSERS = {'ctrl+d', 'ctrl+c', 'ctrl+z', 'ctrl+w', 'ctrl+shift+w', 'ctrl+backslash'}
_NEW_TERMINAL = {'ctrl+shift+t', 'ctrl+shift+n', 'ctrl+alt+t'}
_HARMLESS_KEYS = {'escape', 'tab', 'shift+tab', 'up', 'down', 'left', 'right', 'home', 'end', 'page_up',
                  'page_down', 'ctrl+a', 'ctrl+c', 'ctrl+l', 'ctrl+f', 'shift', 'ctrl', 'alt'}


def _known(scene: Tuple[str, Tuple[int, ...]], seen: Iterable[Tuple[str, Tuple[int, ...]]]) -> bool:
    """Has this window been in front before? A window that only now tells its name, in the
    same place as an unnamed one seen earlier, is the same window."""
    app, place = scene
    for other_app, other_place in seen:
        if place == other_place and (app == other_app or not app or not other_app):
            return True
    return False


@dataclass
class Step:
    n: int
    action: str
    summary: str
    thought: str = ''
    outcome: str = ''
    changed: Optional[bool] = None
    think_seconds: float = 0.0
    act_seconds: float = 0.0
    problem: str = ''


@dataclass
class TaskResult:
    success: bool
    answer: str
    steps: List[Step] = field(default_factory=list)
    screenshot: str = ''
    seconds: float = 0.0
    stopped: bool = False
    tokens: int = 0
    thinks: int = 0


class ComputerAgent:
    """Runs one task to completion on the real desktop."""

    def __init__(self, desktop: Optional[oa.Desktop] = None, model: Optional[str] = None,
                 on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
                 confirm: Optional[Callable[[str], bool]] = None,
                 max_steps: Optional[int] = None, cwd: Optional[str] = None,
                 max_thinks: Optional[int] = None):
        self._desktop = desktop
        self.model = model
        self.on_event = on_event or (lambda e: None)
        self.confirm = confirm
        self.max_steps = max_steps or int(os.environ.get('DEVIN_MAX_STEPS', '40'))
        self.max_thinks = max_thinks or int(os.environ.get('DEVIN_MAX_THINKS', '10'))
        self.cwd = cwd or os.getcwd()
        self._stop = threading.Event()
        self._host: Optional[Dict[str, Any]] = None       # the terminal Devin itself runs in
        self._last_real: Tuple[str, str] = ('', '')        # last real window seen in front
        self._task = ''                                    # what the user asked for, for the safety checks
        self._armed = False       # a click or a focus shortcut has just put the keyboard somewhere on purpose

    @property
    def desktop(self) -> oa.Desktop:
        if self._desktop is None:
            self._desktop = oa.get_desktop()
        return self._desktop

    def stop(self) -> None:
        self._stop.set()

    def _emit(self, kind: str, **data: Any) -> None:
        try:
            self.on_event({'type': kind, **data})
        except Exception:
            pass

    @staticmethod
    def _trace(kind: str, **data: Any) -> None:
        if os.environ.get('DEVIN_TRACE', '').strip().lower() not in ('1', 'true', 'yes', 'on'):
            return
        try:
            with open(oa._tmp_path('trace.jsonl'), 'a', encoding='utf-8') as f:
                f.write(json.dumps({'t': round(time.time(), 2), 'kind': kind, **data}, default=str) + '\n')
        except OSError:
            pass

    # ── seeing ──
    def _observe(self, focus: str = '') -> Observation:
        obs = look(self.desktop, focus=focus)
        if obs.window:
            self._last_real = (obs.app, _norm_title(obs.window))
        return obs

    def _steady(self, obs: Observation, focus: str = '') -> Observation:
        """Make sure the screenshot the model is about to reason over shows a finished screen.

        Thinking costs a slow model a minute or more, and a screenshot of a half-drawn window
        makes that minute worthless. So watch the screen for a second first: if it is still
        changing (a page loading, a window opening), wait until it is quiet and look again.
        """
        d = self.desktop
        for _ in range(3):
            if self._stop.is_set():
                break
            d.mark()
            state = d.settle(quiet=0.8, timeout=8, expect=1.0)
            if not state.get('changed'):
                break
            obs = self._observe(focus)
        return obs

    @staticmethod
    def _eyes(vision: bool, lean: bool, purpose: str, obs: Observation, struggling: bool = False) -> bool:
        """Should the screenshot itself go to the model this time?"""
        mode = os.environ.get('DEVIN_EYES', 'auto').strip().lower()
        if not vision or mode == 'never':
            return False
        if mode == 'always' or not lean:
            return True
        # A small local model reads a shrunken screenshot badly (measured: it called a full-screen
        # calculator "a blank workspace") and pays about 20 seconds for it. The text read off
        # the same screenshot serves it better, so the picture goes along only when there
        # is almost no text to go on.
        return len(obs.elements) < 6

    @staticmethod
    def _thinking(lean: bool) -> Optional[bool]:
        mode = os.environ.get('DEVIN_THINK', 'auto').strip().lower()
        if mode in ('on', '1', 'true', 'yes'):
            return True
        if mode in ('off', '0', 'false', 'no'):
            return False
        return False if lean else None

    # ── the model writes the next actions ──
    def _think(self, task: str, obs: Observation, steps: List[Step], context: str, model: str,
               vision: bool, note: str = '', hidden: Iterable[Tuple[str, str]] = (),
               struggling: bool = False) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        lean = lean_profile(model)
        focus = task + ' ' + (steps[-1].thought if steps else '')
        own = self._at_home(obs)
        if lean:
            shown = obs.top(12, focus, hidden, brief=True)
            parts = [f'TASK: {task}', obs.describe(compact=True, limit=12, focus=focus, hidden=hidden, own=own)]
            if steps:
                # what went wrong is spelled out once, under PROBLEM, not twice
                parts.append('DONE SO FAR:\n' + '\n'.join(
                    f'{s.n}. {s.summary} -> ' + ('did not work' if s.problem and s is steps[-1] and note
                                                 else _clip(s.outcome, 90)) for s in steps[-5:]))
            if note:
                parts.append(('NOTE: ' if note.startswith('A new window') else 'PROBLEM: ') + _clip(note, 330))
            system, joiner, max_tokens = lean_system_prompt(obs), '\n', 170
        else:
            shown = obs.top(60, focus, hidden)
            parts = [f'TASK: {task}']
            if context:
                parts.append(f'CONTEXT: {context}')
            parts.append(obs.describe(limit=60, focus=focus, hidden=hidden))
            parts.append('DONE SO FAR:\n' + '\n'.join(f'{s.n}. {s.summary} -> {s.outcome}' for s in steps[-10:])
                         if steps else 'DONE SO FAR: nothing yet.')
            if note:
                parts.append('PROBLEM: ' + note)
            parts.append('What now?')
            system, joiner, max_tokens = system_prompt(vision, obs), '\n\n', 500
        message: Dict[str, Any] = {'role': 'user', 'content': joiner.join(parts)}
        if self._eyes(vision, lean, 'think', obs, struggling):
            message['images'] = [obs.small() if lean else (obs.marked(shown) if shown else obs.image)]

        def complete(text: str) -> bool:
            # Stop the model the moment its plan is whole: every extra token costs time.
            if not text.endswith('\n'):
                return False
            lines = [ln.strip().lower() for ln in text.strip().splitlines() if ln.strip()]
            if lines and re.match(r'^(?:\d+[.)]\s*|[-*]\s*)?(done|fail)\b', lines[-1]):
                return True
            return len(lines) >= 14

        raw = llm.chat_text([message], system=system, model=model, temperature=0.1, max_tokens=max_tokens,
                            think=self._thinking(lean), num_ctx=LEAN_CTX if lean else None, until=complete)
        if raw.get('prompt_tps'):
            first_measure = model not in _speed
            _speed[model] = raw['prompt_tps']
            if first_measure:
                self._emit('speed', model=model, tps=raw['prompt_tps'], lean=lean_profile(model))
        thought, actions = parse_reply(raw['content'], obs)
        if not thought and raw.get('thinking'):
            thought = raw['thinking'].strip().splitlines()[-1][:200]
        self._trace('think', prompt=message['content'], image=bool(message.get('images')),
                    reply=raw['content'], seconds=round(raw.get('seconds', 0), 1),
                    actions=[describe_action(a) for a in actions])
        return thought, actions, raw

    def _verify(self, task: str, obs: Observation, steps: List[Step], claim: str,
                model: str, vision: bool) -> Tuple[bool, str, Dict[str, Any]]:
        """Check a "done" claim against what the screen actually shows."""
        lean = lean_profile(model)
        did = '\n'.join(f'{s.n}. {s.summary} -> {_clip(s.outcome, 110)}'
                        for s in steps[-(5 if lean else 10):]) or '(no actions were taken)'
        screen = obs.describe(compact=True, limit=12, focus=task + ' ' + claim) if lean else obs.describe(limit=60)
        prompt = (f'TASK: {task}\n{screen}\nACTIONS TAKEN:\n{did}\n'
                  f'The assistant says the task is finished: "{_clip(claim, 200)}"\n'
                  'Does the screen show what the TASK asked for? (If the TASK only asked a question, does the '
                  'claim answer it?) Write one short sentence saying what the screen shows. Then, on a new '
                  'line, write exactly VERDICT: YES or VERDICT: NO.')
        message: Dict[str, Any] = {'role': 'user', 'content': prompt}
        if self._eyes(vision, lean, 'verify', obs):
            message['images'] = [obs.small(448) if lean else obs.image]

        def complete(text: str) -> bool:
            return bool(re.search(r'VERDICT\W{0,4}(YES|NO)\b', text, re.I))

        raw = llm.chat_text([message], system=VERIFY_SYSTEM, model=model, temperature=0.0, max_tokens=90,
                            think=False, num_ctx=LEAN_CTX if lean else None, until=complete)
        text = raw['content'].strip()
        m = re.search(r'VERDICT\W{0,4}(YES|NO)\b', text, re.I)
        if m:   # the reasoning comes first, so the verdict follows from it
            ok, reason = m.group(1).lower() == 'yes', text[:m.start()].strip()
        else:
            m = re.match(r'\W*(yes|no)\b[\s,.:;\-—]*(.*)$', text, re.I | re.S)
            if m:
                ok, reason = m.group(1).lower() == 'yes', m.group(2).strip()
            else:  # no clear verdict is not a confirmation
                ok, reason = False, text
        self._trace('verify', prompt=prompt, image=bool(message.get('images')), reply=text, ok=ok)
        return ok, _clip(reason.splitlines()[0] if reason else '', 220), raw

    # ── one action ──
    def _shell(self, command: str) -> str:
        if _DANGEROUS.search(command):
            if not (self.confirm and self.confirm(command)):
                return 'REFUSED: this command can destroy data and was not approved by the user'
        elif os.environ.get('DEVIN_PERMISSION_MODE', 'auto').lower() == 'ask':
            if not (self.confirm and self.confirm(command)):
                return 'REFUSED: the user did not approve this command'
        timeout = float(os.environ.get('DEVIN_SHELL_TIMEOUT', '120'))
        proc = subprocess.Popen(command, shell=True, cwd=self.cwd, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                errors='replace', start_new_session=True)
        try:
            out, _ = proc.communicate(timeout=timeout)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except OSError:
                pass
            out, _ = proc.communicate()
            code = f'timeout after {int(timeout)}s'
        out = (out or '').strip()
        if len(out) > 2500:
            out = out[:800] + f'\n… ({len(out) - 2300} characters skipped) …\n' + out[-1500:]
        return f'exit {code}\n{out}' if out else f'exit {code} (no output)'

    @staticmethod
    def _key_parts(keys: str) -> List[str]:
        """'ctrl+a, backspace' → ['ctrl+a', 'backspace']: the shortcuts to press, in order."""
        return [p.strip() for p in re.split(r'\s*(?:,|;|\bthen\b)\s*', keys) if p.strip()]

    @classmethod
    def _combos(cls, keys: str) -> List[str]:
        """The same, with key names normalised ('Enter' → 'return') for comparing."""
        return ['+'.join(oa.split_combo(p)) for p in cls._key_parts(keys)]

    def _set_host(self, obs: Observation) -> None:
        """Remember the terminal Devin was started from, so it never types into itself."""
        self._host = None
        if os.environ.get('DEVIN_PROTECT_TERMINAL', '1').strip().lower() in ('0', 'false', 'no', 'off'):
            return
        if obs.window and _TERMINALS.search(obs.app + ' ' + obs.window):
            self._host = {'app': obs.app, 'title': _norm_title(obs.window), 'left': False}

    def _at_home(self, obs: Observation) -> bool:
        """Is the window in front the terminal Devin was started from, with nothing else opened yet?"""
        h = self._host
        return bool(h and not h['left'] and obs.window and obs.app == h['app']
                    and _norm_title(obs.window) == h['title'])

    def _host_hidden(self, obs: Observation) -> Set[Tuple[str, str]]:
        """What must not be offered to the model: everything inside Devin's own terminal while
        it is still in front (its text repeats the task and this conversation — none of it
        is something to click), and afterwards any button that would close that terminal."""
        h = self._host
        if not h or obs.app != h['app'] or not obs.window:
            return set()
        if self._at_home(obs):
            return {e.key for e in obs.elements if not e.shell}
        return {e.key for e in obs.elements if e.name.strip().lower() in ('close', 'quit', 'close window', 'close tab')
                and not e.shell}

    def _keyboard_ready(self, obs: Observation) -> bool:
        """Is it known where typed text will go? Letters sent to a window with no text field in
        focus are not harmless: in many programs single keys are commands."""
        if obs.launcher_open or self._armed:
            return True
        return any(e.focused and e.typable for e in obs.elements)

    def _forbidden(self, text: str) -> bool:
        """Would this click/command end the session, when the task did not ask for that?"""
        return bool(_SESSION_ENDERS.search(text or '')) and not _SESSION_ENDERS.search(self._task)

    def _never_offered(self, obs: Observation) -> Set[Tuple[str, str]]:
        """Kept out of the list shown to the model: anything that ends the session, and the
        desktop's own status menus in the top bar (clock, network, power…) — a task is done
        in applications, and those menus are where restart and power-off live."""
        task_words = set(re.findall(r'[a-z0-9]{4,}', self._task.lower()))
        out: Set[Tuple[str, str]] = set()
        for e in obs.elements:
            name = e.name.strip()
            if self._forbidden(name):
                out.add(e.key)
            elif self._desktop_chrome(e, obs):
                if e.y >= 40 or not any(w in name.lower() for w in task_words):
                    out.add(e.key)
        return out

    @staticmethod
    def _desktop_chrome(e: Element, obs: Observation) -> bool:
        """Top-bar items and notification pop-ups: part of the desktop, drawn over the top of
        the screen, and not something a task is done with (the launcher button excepted)."""
        if not e.shell or _LAUNCHERS.match(e.name.strip()):
            return False
        return e.y < 40 or (e.y < 130 and not obs.launcher_open and not e.typable)

    def _defuse(self, obs: Observation) -> str:
        """If a restart / power-off / log-out dialog is counting down on screen and the task did
        not ask for it, cancel it at once. Returns what happened, or ''."""
        if _SESSION_ENDERS.search(self._task):
            return ''
        texts = ' | '.join(e.name for e in obs.elements)
        names = {e.name.strip().lower() for e in obs.elements if e.shell or e.kind == 'button'}
        if _ENDING_DIALOG.search(texts) or ('cancel' in names and names & {'restart', 'power off', 'log out',
                                                                             'shut down', 'restart…', 'power off…'}):
            try:
                self.desktop.key('escape')
                self.desktop.settle(quiet=0.4, timeout=3, expect=1.0)
            except oa.DesktopError:
                pass
            return ('a restart / power-off / log-out dialog had opened; it was cancelled. Never open the system '
                    'menu or click anything that restarts, shuts down or logs out')
        return ''

    def _safety(self, a: Dict[str, Any]) -> str:
        """Why this action is refused whatever window is in front, or ''."""
        kind = a.get('action')
        refusal = ('BLOCKED: that would restart, shut down, lock or log out of the computer, and the TASK does '
                   'not ask for it. Do the TASK inside the applications instead.')
        if kind == 'click' and self._forbidden(a.get('target') or ''):
            return refusal
        if kind == 'key' and not _SESSION_ENDERS.search(self._task):
            if any(c in _SESSION_KEYS for c in self._combos(a.get('keys') or '')):
                return refusal
        if kind == 'type':
            text = a.get('text') or ''
            if _SESSION_COMMANDS.search(text) and not _SESSION_ENDERS.search(self._task):
                return refusal
            if a.get('enter') and _DANGEROUS.search(text) and not (self.confirm and self.confirm(text)):
                return 'BLOCKED: this command can destroy data and was not approved by the user.'
        return ''

    def _targets(self, obs: Observation) -> List[Element]:
        """The elements a click may land on."""
        task_words = set(re.findall(r'[a-z0-9]{4,}', self._task.lower()))

        def ok(e: Element) -> bool:
            if not self._desktop_chrome(e, obs):
                return True
            return e.y < 40 and any(w in e.name.lower() for w in task_words)   # only if the task names it
        if self._at_home(obs):
            return [e for e in obs.elements if e.shell and ok(e)]   # only the desktop itself: dock, launcher
        return [e for e in obs.elements if ok(e)]

    def _guard(self, a: Dict[str, Any], obs: Observation) -> str:
        """Why this action must not be carried out, or ''."""
        unsafe = self._safety(a)
        if unsafe:
            return unsafe
        typing = a.get('action') == 'type' or (a.get('action') == 'key' and any(
            len(c) == 1 for c in self._combos(a.get('keys') or '')))
        if typing and not self._keyboard_ready(obs) and not self._at_home(obs):
            return ('BLOCKED: nothing was typed, because no text field has the keyboard. Click the field you '
                    'want to type into first (in a web browser that is the address bar at the top), then type.')
        h = self._host
        if not h or not obs.window or obs.app != h['app']:
            return ''
        kind = a.get('action')
        combos = self._combos(a.get('keys') or '') if kind == 'key' else []
        if any(c in _WINDOW_CLOSERS for c in combos) or (
                kind == 'click' and _norm(a.get('target') or '') in ('close', 'quit', 'close window', 'x')):
            return 'BLOCKED: that would close the terminal Devin itself is running in. Leave that window alone.'
        if h['left']:
            return ''
        if _norm_title(obs.window) != h['title']:
            h['left'] = True          # another terminal window or tab is in front now
            return ''
        hint = ('The keyboard is still in the terminal that runs Devin itself. Open the application the task '
                f'needs first: {_open_rule(obs)[0]}. For a terminal of your own: key ctrl+shift+t.')
        if kind == 'type':
            return 'BLOCKED: nothing was typed. ' + hint
        if kind == 'key':
            if any(c in _TAB_CLOSERS for c in combos):
                return 'BLOCKED: that key would stop Devin itself. ' + hint
            if all('super' in c.split('+') or c == 'alt+tab' or c in _NEW_TERMINAL for c in combos):
                return ''
            return 'BLOCKED: no key was pressed. ' + hint
        return ''

    def _locate(self, a: Dict[str, Any], obs: Observation) -> Tuple[Optional[Tuple[int, int]], str, Observation]:
        """Where to click for this action: (point, what it is called, the screenshot used)."""
        if a.get('x') is not None and a.get('y') is not None and not a.get('target'):
            return (int(a['x']), int(a['y'])), f'({int(a["x"])},{int(a["y"])})', obs
        target = a.get('target') or ''
        for attempt in range(3):
            el = None
            allowed = self._targets(obs)
            if a.get('id') is not None and attempt == 0:
                numbered = obs.element(a['id'])
                if numbered is not None and numbered in allowed and (
                        not target or _norm(numbered.name) == _norm(target)):
                    el = numbered
            if el is None and target:
                el = match_element(allowed, target)
            if el is not None:
                a['_shell'] = el.shell
                return el.center, f'"{_clip(el.name or el.kind, 40)}"', obs
            if not target or attempt == 2 or self._stop.is_set():
                break
            # Not there yet — a page may still be loading. Look again shortly.
            self._stop.wait(1.2)
            obs = self._observe(target)
        return None, target or f'item {a.get("id")}', obs

    def _act(self, a: Dict[str, Any], obs: Observation) -> Tuple[str, str, Optional[Dict[str, Any]], Observation]:
        """Carry out one action. Returns (summary, result text, settle info or None, screenshot used)."""
        d = self.desktop
        kind = a.get('action')
        summary = describe_action(a)
        blocked = self._guard(a, obs)
        if blocked:
            return summary, blocked, None, obs

        if kind == 'click':
            point, what, obs = self._locate(a, obs)
            button = a.get('button') or 'left'
            verb = {'double': 'double-click', 'right': 'right-click', 'middle': 'middle-click'}.get(button, 'click')
            if point is None:
                if a.get('id') is not None and not a.get('target'):
                    return f'{verb} item {a["id"]}', f'ERROR: there is no element with id {a["id"]} on the screen', None, obs
                named = _norm(' '.join(w for w in _norm(what).split() if w not in _FILLER))
                if named and obs.window and button == 'left' and all(
                        w in _norm(obs.app + ' ' + obs.window) for w in named.split()):
                    return (f'{verb} "{_clip(what, 40)}"',
                            f'no click needed: "{_clip(obs.window, 40)}" is already the window in front', None, obs)
                allowed = {id(e) for e in self._targets(obs)}
                names = ' | '.join(_clip(e.name, 24) for e in obs.top(40, what, brief=True)
                                   if e.name and id(e) in allowed)[:260]
                return (f'{verb} "{_clip(what, 40)}"',
                        f'ERROR: nothing on the screen is labelled "{_clip(what, 40)}". What is there: {names}', None, obs)
            x, y = point
            if self._forbidden(what):
                return (f'{verb} {what}', 'BLOCKED: that would restart, shut down, lock or log out of the computer, '
                                          'and the TASK does not ask for it.', None, obs)
            named = _norm(what)
            if (a.get('_shell') and obs.window and button == 'left' and named
                    and named in _norm(obs.app + ' ' + obs.window) and not _LAUNCHERS.match(what.strip('"'))):
                return (f'{verb} {what}', f'no click needed: "{_clip(obs.window, 40)}" is already the window in front',
                        None, obs)
            d.click(x, y, 'left' if button == 'double' else button, 2 if button == 'double' else 1)
            return f'{verb} {what}', f'clicked at ({x},{y})', d.settle(quiet=0.5, timeout=8, expect=1.5), obs

        if kind == 'type':
            text = a.get('text') or ''
            if not text:
                return 'type (nothing)', 'ERROR: there was no text to type', None, obs
            # Small models sometimes "type" the name of a key. Nobody means the letters e-n-t-e-r.
            if text.strip().lower() in ('enter', 'return', 'tab', 'escape', 'esc', 'backspace'):
                key = text.strip().lower()
                a['action'], a['keys'] = 'key', key
                d.key(key)
                return f'press {key}', f'pressed {key}', d.settle(quiet=0.6, timeout=10, expect=1.5), obs
            box = obs.focused_input()
            already = (box is not None and box.typable and _norm(text)
                       and _norm(box.value).endswith(_norm(text)))
            if already and not a.get('enter'):
                # A re-plan often repeats "type the name" although the field still holds it from
                # the first try; typing again would turn "burpsuite" into "burpsuiteburpsuite".
                return summary, f'no typing needed: the field already reads "{_clip(box.value, 40)}"', None, obs
            if not already:
                d.type(text)
            if a.get('enter'):
                d.settle(quiet=0.45, timeout=3, expect=0.8)   # let the field (and any suggestions) catch up
                d.key('enter')
                return (summary, f'typed {len(text)} characters and pressed Enter',
                        d.settle(quiet=0.8, timeout=14, expect=3.5), obs)
            return summary, f'typed {len(text)} characters', d.settle(quiet=0.35, timeout=4, expect=1.2), obs

        if kind == 'key':
            parts = self._key_parts(a.get('keys') or '')
            if not parts:
                return 'press (nothing)', 'ERROR: no key was named', None, obs
            for i, combo in enumerate(parts):
                if i:
                    d.settle(quiet=0.3, timeout=3, expect=0.6)
                d.key(combo)
            settle = d.settle(quiet=0.6, timeout=10, expect=1.5)
            if self._host and any(c in _NEW_TERMINAL for c in self._combos(a['keys'])) and settle.get('changed'):
                self._host['left'] = True
            return f'press {", ".join(parts)}', f'pressed {", ".join(parts)}', settle, obs

        if kind == 'scroll':
            direction = a.get('direction') or 'down'
            amount = max(1, min(int(a.get('amount') or 5), 15))
            dy = amount if direction == 'down' else -amount if direction == 'up' else 0
            dx = amount if direction == 'right' else -amount if direction == 'left' else 0
            d.scroll(dy=dy, dx=dx, x=obs.width // 2, y=obs.height // 2)
            return f'scroll {direction} {amount}', f'scrolled {direction}', d.settle(quiet=0.4, timeout=5, expect=1.0), obs

        if kind == 'drag':
            try:
                x1, y1, x2, y2 = (int(a[k]) for k in ('x', 'y', 'x2', 'y2'))
            except (KeyError, TypeError, ValueError):
                return 'drag', 'ERROR: drag needs two points: drag X,Y to X2,Y2', None, obs
            d.drag(x1, y1, x2, y2)
            return summary, 'dragged', d.settle(quiet=0.5, timeout=6, expect=1.2), obs

        if kind == 'shell':
            command = (a.get('command') or '').strip()
            if not command:
                return '$', 'ERROR: no command was given', None, obs
            return summary, self._shell(command), None, obs

        if kind == 'wait':
            seconds = max(0.2, min(float(a.get('seconds') or 2), 30))
            d.mark()
            self._stop.wait(seconds)
            return f'wait {seconds:g}s', f'waited {seconds:g}s', d.settle(quiet=0.4, timeout=4, expect=0.0), obs

        return str(kind), f'ERROR: unknown action {kind!r}', None, obs

    # ── after the action: what does the screen say? ──
    @staticmethod
    def _submits(a: Dict[str, Any]) -> bool:
        """Could this action have started a program or opened something?"""
        kind = a.get('action')
        if kind == 'click':
            return True
        if kind == 'type':
            return bool(a.get('enter'))
        if kind == 'key':
            return bool(re.search(r'\b(enter|return)\b', a.get('keys') or ''))
        return False

    def _look_after(self, a: Dict[str, Any], before: Observation, settle: Optional[Dict[str, Any]],
                    came_from: Tuple[str, str], focus: str) -> Observation:
        """The screenshot that shows the result of an action — taken when the result is really there."""
        d = self.desktop
        if settle is not None and settle.get('changed') and not settle.get('stable', True):
            d.settle(quiet=0.8, timeout=6, expect=0.0)       # still loading: give it one more moment
        if self._submits(a) and before.launcher_open and not self._stop.is_set():
            # Something was started from the launcher. A program needs a few seconds before its
            # window exists; until then the window that was in front before is in front again.
            # Acting now would send the next keystrokes to the wrong window.
            end = time.monotonic() + 9.0
            while time.monotonic() < end and not self._stop.is_set():
                info = d.elements(budget=0.3, limit=1)
                now = (info.get('app', ''), _norm_title(info.get('window', '')))
                if info.get('window') and now != came_from:
                    # The window exists; its contents are drawn a moment (sometimes seconds)
                    # later. Wait until it has stopped changing before looking at it.
                    d.mark()
                    d.settle(quiet=1.0, timeout=12, expect=3.5)
                    break
                self._stop.wait(0.4)
            return self._observe(focus)
        obs = self._observe(focus)
        if before.window and not obs.window and not obs.launcher_open and not self._stop.is_set():
            # The window that was in front is gone and nothing has taken its place yet: one
            # window closing and the next one opening (a chooser giving way to the program
            # itself). Keystrokes sent now would land nowhere, or in the wrong place.
            end = time.monotonic() + 6.0
            while time.monotonic() < end and not self._stop.is_set():
                if d.elements(budget=0.3, limit=1).get('window'):
                    break
                self._stop.wait(0.4)
            d.mark()
            d.settle(quiet=1.0, timeout=12, expect=3.0)
            obs = self._observe(focus)
        return obs

    def _effect(self, a: Dict[str, Any], summary: str, result: str, settle: Optional[Dict[str, Any]],
                before: Observation, after: Observation, came_from: Tuple[str, str]
                ) -> Tuple[str, Optional[bool], str]:
        """Compare the screen before and after. Returns (outcome, changed, problem or '')."""
        kind = a.get('action')
        if result.startswith(('ERROR', 'BLOCKED', 'REFUSED')):
            return result, False, result.split(': ', 1)[-1]
        if kind == 'shell' or result.startswith(('no click needed', 'no typing needed')):
            return result, None, ''
        changed: Optional[bool] = bool(settle.get('changed')) if settle is not None else None
        notes: List[str] = []
        problem = ''
        was = (before.app, _norm_title(before.window))
        now = (after.app, _norm_title(after.window))
        if now != was:
            changed = True
            notes.append(f'now in front: "{_clip(after.window, 50)}"' if after.window
                         else 'the app search is open now' if after.launcher_open
                         else 'another window is in front now' if after.has_window
                         else 'no window in front now (empty desktop)')
            if self._submits(a) and before.launcher_open and after.window and now == came_from:
                asked = _norm(a.get('text') or a.get('target') or '')
                here = _norm(after.app + ' ' + after.window)
                if not asked or not any(w in here for w in asked.split() if len(w) >= 3):
                    problem = (f'no new window came to the front: "{_clip(after.window, 40)}" is in front, '
                               'as before. What was asked for did not open')
        if kind == 'type':
            text = (a.get('text') or '').strip()
            box = after.focused_input()
            probe = _norm(text)[:24]
            if box is not None and probe and probe in _norm(box.value + ' ' + box.name):
                notes.append(f'the field now reads "{_clip(box.value or box.name, 40)}"')
            elif not a.get('enter'):
                if after.shows(text):
                    notes.append('the text is on the screen')
                elif not problem:
                    problem = ('the typed text is not visible anywhere: no text field had the keyboard. '
                               'Click the field, or open the right window, first')
        if not notes:
            if changed is False:
                notes.append('nothing happened')
                dull = kind == 'key' and all(c in _HARMLESS_KEYS for c in self._combos(a.get('keys') or ''))
                if kind in ('click', 'type', 'key', 'drag') and not dull and not problem:
                    problem = f'{summary} changed nothing on the screen'
            elif settle is not None and not settle.get('stable', True):
                notes.append('the screen changed and is still moving (loading or video)')
            elif changed:
                pct = (settle or {}).get('change', 0) * 100
                notes.append('the screen changed' if pct >= 1 else 'the screen changed slightly')
            else:
                notes.append(result)
        outcome = '; '.join(notes)
        if problem and problem not in outcome:
            outcome += f'; PROBLEM: {problem}'
        return outcome, changed, problem

    # ── the loop ──
    def run(self, task: str, context: str = '') -> TaskResult:
        started = time.monotonic()
        steps: List[Step] = []
        tokens = 0
        thinks = 0
        self._task = task
        self._armed = False
        model = self.model or llm.pick_agent_model()
        vision = llm.supports_vision(model)
        queue: List[Dict[str, Any]] = []   # actions the model has planned and not yet carried out
        note = ''                  # what went wrong, handed to the model with the next screenshot
        thought = ''
        rejected_done = 0          # "done" claims the screen did not support
        gave_up = 0                # times the model tried to quit
        trouble = 0                # problems in a row
        empty = 0                  # replies with no usable action
        clean_run = 0              # actions carried out without a problem since the last plan
        auto_checks = 0            # times the screen was checked without the model claiming "done"
        seen: Set[Any] = set()     # windows that have been in front during this task
        failed: Dict[Any, int] = {}        # action signature → times it went wrong
        dead: Set[Tuple[str, str]] = set()  # elements that did nothing when clicked on this screen

        def finish(success: bool, answer: str, stopped: bool = False) -> TaskResult:
            shot = ''
            try:
                shot = oa._tmp_path('last_screen.png')
                self.desktop.capture().save(shot)
            except Exception:
                shot = ''
            result = TaskResult(success=success, answer=answer, steps=steps, screenshot=shot,
                                seconds=time.monotonic() - started, stopped=stopped, tokens=tokens, thinks=thinks)
            self._trace('finish', success=success, answer=answer, steps=len(steps), thinks=thinks,
                        seconds=round(result.seconds, 1))
            self._emit('finish', result=result)
            return result

        # LOOK
        try:
            obs = self._observe(task)
        except oa.DesktopError as e:
            return finish(False, f'I cannot see the screen: {e}')
        self._set_host(obs)
        if obs.has_window:
            seen.add(obs.scene())
        self._trace('start', task=task, model=model, vision=vision, front=obs.front())

        while True:
            if self._stop.is_set():
                return finish(False, 'Stopped.', stopped=True)
            if len(steps) >= self.max_steps:
                return finish(False, f'I used all {self.max_steps} steps and the task is still not finished.')

            # The plan ran through without a problem but did not end in "done". Small models
            # reach the goal and then keep fiddling, so look at the screen now: if the task
            # is finished, stop here.
            if not queue and clean_run and auto_checks < 3 and not note:
                auto_checks += 1
                clean_run = 0
                self._emit('verify_start', n=len(steps) + 1)
                try:
                    obs = self._steady(obs, task)
                    ok, reason, vraw = self._verify(task, obs, steps,
                                                    'All planned steps were carried out without a problem.',
                                                    model, vision)
                    tokens += vraw.get('tokens_in', 0) + vraw.get('tokens_out', 0)
                except (llm.OllamaError, oa.DesktopError):
                    ok, reason = False, ''
                self._emit('verify', n=len(steps) + 1, complete=ok, reason=reason, tokens=tokens)
                if ok:
                    return finish(True, reason or steps[-1].outcome)
                if reason:
                    note = f'The task is not finished yet: {reason}'

            # THINK — only when there is no plan left, or the screen did not follow the plan
            if not queue:
                if thinks >= self.max_thinks:
                    last = steps[-1].outcome if steps else 'nothing was done'
                    return finish(False, f'I planned {thinks} times and still could not finish. Last result: {last}')
                thinks += 1
                try:
                    obs = self._steady(obs, task + ' ' + thought)
                except oa.DesktopError as e:
                    return finish(False, f'I lost sight of the screen: {e}')
                self._emit('look', n=len(steps) + 1, window=obs.window, app=obs.app, elements=len(obs.elements),
                           seconds=obs.seconds, vision=vision, thinks=thinks)
                t0 = time.monotonic()
                hidden = dead | self._host_hidden(obs) | self._never_offered(obs)
                try:
                    thought, queue, raw = self._think(task, obs, steps, context, model, vision, note,
                                                      hidden, struggling=trouble >= 2)
                except llm.OllamaError as e:
                    return finish(False, f'The model failed: {e}')
                think_s = time.monotonic() - t0
                tokens += raw.get('tokens_in', 0) + raw.get('tokens_out', 0)
                self._emit('think', n=len(steps) + 1, seconds=think_s, thought=thought, tokens=tokens,
                           plan=[describe_action(a) for a in queue], replanned=bool(note),
                           action=queue[0]['action'] if queue else None)
                note = ''
                if self._stop.is_set():
                    return finish(False, 'Stopped.', stopped=True)
                if not queue:
                    empty += 1
                    if empty >= 3:
                        return finish(False, 'The model did not give me any action I could carry out. '
                                             f'Its last reply was: {_clip(raw.get("content", "").strip(), 160) or "(empty)"}')
                    note = ('Your reply contained no action lines. Write actions exactly like: click "name"   or   '
                            'type "text" ENTER   or   key enter   or   done "result".')
                    continue
                empty = 0
            else:
                think_s = 0.0

            a = queue.pop(0)
            kind = a.get('action')

            if kind == 'done':
                claim = (a.get('answer') or thought or 'Done.').strip()
                # Never take "done" on trust: check it against the screen.
                self._emit('verify_start', n=len(steps) + 1)
                try:
                    obs = self._steady(obs, task + ' ' + claim)
                    ok, reason, vraw = self._verify(task, obs, steps, claim, model, vision)
                    tokens += vraw.get('tokens_in', 0) + vraw.get('tokens_out', 0)
                except oa.DesktopError as e:
                    return finish(False, f'I lost sight of the screen: {e}')
                except llm.OllamaError as e:
                    return finish(False, f'I believe this is finished ("{claim}"), but the model stopped '
                                         f'answering before I could check the screen: {e}')
                self._emit('verify', n=len(steps) + 1, complete=ok, reason=reason, tokens=tokens)
                if ok:
                    return finish(True, claim)
                rejected_done += 1
                steps.append(Step(n=len(steps) + 1, action='done', summary='claimed the task was done',
                                  thought=thought, outcome=f'REJECTED - the screen does not show it: {reason}',
                                  changed=False, think_seconds=think_s))
                # A small model that is told "not done" tends to start changing things at random.
                # It gets one more try; a stronger model gets more.
                if rejected_done >= (3 if lean_profile(model) else 4):
                    did = '; '.join(s.summary for s in steps if s.action not in ('done', 'fail'))[-300:]
                    return finish(False, 'I could not get the screen to show this task as finished. '
                                         + (f'What I did: {did}. ' if did else '')
                                         + (f'In front now: "{obs.window}". ' if obs.window else '')
                                         + f'Last check of the screen: {reason}')
                queue.clear()
                clean_run = 0
                note = (f'You said the task was done, but a check of the screen says it is NOT: {reason} '
                        'Do only what is really missing, then done. Change nothing else.')
                try:
                    obs = self._observe(task)
                except oa.DesktopError as e:
                    return finish(False, f'I cannot see the screen: {e}')
                continue

            if kind == 'fail':
                why = (a.get('answer') or thought or 'I could not do that.').strip()
                gave_up += 1
                if gave_up >= 3:
                    return finish(False, why)
                steps.append(Step(n=len(steps) + 1, action='fail', summary='wanted to give up', thought=thought,
                                  outcome=f'not accepted: {why}', changed=False, think_seconds=think_s))
                self._emit('retry', n=len(steps), reason=why)
                queue.clear()
                note = ('Do not give up yet. There is another way: a different application, the keyboard '
                        'instead of the mouse, a menu, the launcher, or scrolling to find it. Try it now.')
                continue

            # ACT
            n = len(steps) + 1
            t1 = time.monotonic()
            came_from = self._last_real
            self._emit('act_start', n=n, action=kind, summary=describe_action(a), decision=a)
            try:
                summary, result, settle, before = self._act(a, obs)
            except oa.DesktopError as e:
                summary, result, settle, before = describe_action(a), f'ERROR: {e}', None, obs
            except Exception as e:  # a bad argument from the model must not kill the task
                summary, result, settle, before = describe_action(a), f'ERROR: {type(e).__name__}: {e}', None, obs

            # CHECK — a fresh screenshot after every action, compared with the one before
            try:
                after = self._look_after(a, before, settle, came_from, task + ' ' + thought)
            except oa.DesktopError as e:
                return finish(False, f'I lost sight of the screen: {e}')
            outcome, changed, problem = self._effect(a, summary, result, settle, before, after, came_from)
            defused = self._defuse(after)
            if defused:
                problem = defused
                outcome += f'; PROBLEM: {defused}'
                try:
                    after = self._observe(task)
                except oa.DesktopError as e:
                    return finish(False, f'I lost sight of the screen: {e}')
            if not result.startswith(('ERROR', 'BLOCKED', 'REFUSED', 'no click needed')):
                if a.get('action') == 'click':
                    self._armed = True                  # the pointer was put somewhere on purpose
                elif a.get('action') == 'key':
                    combos = self._combos(a.get('keys') or '')
                    self._armed = bool(combos) and combos[-1] in _FOCUS_KEYS
                elif a.get('action') == 'type':
                    self._armed = not a.get('enter')    # after Enter the page moves on; focus is unknown again
            if not _known(after.scene(), {before.scene()}) or after.launcher_open != before.launcher_open:
                if a.get('action') != 'click':
                    self._armed = False                 # another window: nothing has been clicked in it yet
            step = Step(n=n, action=str(kind), summary=summary, thought=thought, outcome=outcome, changed=changed,
                        think_seconds=think_s, act_seconds=time.monotonic() - t1, problem=problem)
            steps.append(step)
            self._trace('act', n=n, summary=summary, outcome=outcome, front=after.front())
            self._emit('act', n=n, step=step)
            if changed and (settle or {}).get('change', 0) >= 0.05 or after.window != before.window:
                dead.clear()           # a different screen: everything may work again
            obs = after

            if not problem:
                trouble = 0
                clean_run += 1
                if after.has_window and not _known(after.scene(), seen):
                    # A window that was not there when the plan was written. The plan could not
                    # know what it shows (a chooser, a dialog, a different layout…), so do not
                    # carry on blind: look at it and think again. Only "done" may still follow.
                    seen.add(after.scene())
                    if any(q.get('action') != 'done' for q in queue):
                        title = after.window or 'an application window'
                        self._emit('retry', n=n, reason=f'a new window appeared: "{title}"',
                                   dropped=len(queue), new_window=title)
                        queue.clear()
                        clean_run = 0
                        note = (f'A new window is in front now: "{_clip(title, 50)}". Read what it shows. '
                                'If it asks a question, answer it by clicking one of its options. '
                                'Then continue the TASK.')
                continue
            clean_run = 0
            if after.has_window:
                seen.add(after.scene())

            # The screen did not follow the plan. Throw the rest of the plan away and think
            # again, with the new screenshot and with what went wrong.
            trouble += 1
            dropped = len(queue)
            queue.clear()
            sig = (kind, _norm(a.get('target') or ''), a.get('id') if not a.get('target') else None,
                   a.get('x'), a.get('y'), a.get('text'), a.get('keys'), a.get('command'))
            failed[sig] = failed.get(sig, 0) + 1
            if kind == 'click' and changed is False and not result.startswith(('ERROR', 'BLOCKED')):
                el = match_element(before.elements, a.get('target') or '') if a.get('target') else before.element(a.get('id'))
                if el is not None:
                    dead.add(el.key)   # clicking it does nothing here: do not offer it again
            if trouble >= 6:
                return finish(False, f'I kept running into problems (last: {problem}) and could not finish.')
            note = problem
            if kind == 'click' and failed[sig] < 2:
                note += '. Choose a different item from the ON SCREEN list'
            if failed[sig] >= 2:
                note += (f'. You have tried "{summary}" {failed[sig]} times and it is not getting anywhere. '
                         'Do something clearly different: another element, a keyboard shortcut, scrolling, '
                         'or opening the right application first.')
            self._emit('retry', n=n, reason=problem, dropped=dropped)


# ══════════════════════════════════════════════════════════════════════════════
# Small helpers used by the rest of Devin
# ══════════════════════════════════════════════════════════════════════════════

def run_task(task: str, on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
             max_steps: Optional[int] = None, model: Optional[str] = None) -> TaskResult:
    return ComputerAgent(on_event=on_event, max_steps=max_steps, model=model).run(task)


def describe_screen(question: str = 'Describe what is on the screen.', model: Optional[str] = None) -> str:
    """What is on screen, in words. A vision model looks at the pixels; others read the element list."""
    obs = look()
    model = model or llm.pick_agent_model()
    lean = lean_profile(model)
    text = obs.describe(compact=True, limit=16, focus=question) if lean else obs.describe(limit=70)
    message: Dict[str, Any] = {'role': 'user', 'content': f'{text}\n\n{question}'}
    if llm.supports_vision(model):
        message['images'] = [obs.small(448) if lean else obs.image]
    try:
        return llm.chat([message], model=model, max_tokens=200 if lean else 500, think=False if lean else None,
                        num_ctx=LEAN_CTX if lean else None,
                        system='You describe a computer screen accurately and briefly. '
                               'Only mention what is actually listed or visible.')['content'].strip()
    except llm.OllamaError:
        return obs.describe(limit=40)


# Names kept for callers written against the previous version of this module.
def observe(save_path: str = '') -> Observation:
    obs = look()
    if save_path:
        obs.save(save_path)
    return obs


def run_vision_cycle(goal: str, ai_call_fn: Any = None, max_steps: int = 20, step_delay: float = 0.5,
                     verbose: bool = False) -> TaskResult:
    def show(e: Dict[str, Any]) -> None:
        if verbose and e['type'] == 'act':
            print(f'  {e["step"].n}. {e["step"].summary} -> {e["step"].outcome}')
    return ComputerAgent(on_event=show, max_steps=max_steps).run(goal)


def tool_screen_observe(save_path: str = '') -> str:
    return observe(save_path).describe(limit=70)


def tool_screen_find_element(description: str, screenshot_path: str = '') -> str:
    obs = look()
    needle = str(description).lower()
    hits = [e for e in obs.elements if needle in (e.name + ' ' + e.value).lower()]
    if not hits:
        best = match_element(obs.elements, description)
        hits = [best] if best is not None else []
    return ('Found: ' + '; '.join(e.line() for e in hits[:5])) if hits else f'Not on screen: {description!r}'


def tool_screen_click_element(description: str) -> str:
    el = match_element(look().elements, description)
    if el is None:
        return f'Not on screen: {description!r}'
    oa.get_desktop().click(*el.center)
    return f'Clicked {el.line()}'


def tool_screen_wait_for(description: str, timeout: float = 10.0, interval: float = 1.0) -> str:
    end = time.monotonic() + float(timeout)
    while time.monotonic() < end:
        found = tool_screen_find_element(description)
        if found.startswith('Found'):
            return found
        time.sleep(float(interval))
    return f'Timed out after {timeout}s waiting for {description!r}'


def tool_screen_automation_status() -> str:
    s = oa.status()
    lines = [f'{k}: {v}' for k, v in s.items()]
    lines.append(f'ocr (tesseract): {"yes" if ocr_available() else "no"}')
    try:
        lines.append(f'model: {llm.describe_model(llm.pick_agent_model())}')
    except Exception:
        lines.append('model: Ollama not reachable')
    return '\n'.join(lines)


VISION_TOOLS = {
    'screen_observe': tool_screen_observe,
    'screen_find_element': tool_screen_find_element,
    'screen_click_element': tool_screen_click_element,
    'screen_wait_for': tool_screen_wait_for,
    'screen_status': tool_screen_automation_status,
}

for _alias in ('screen_vision', 'modules.screen_vision'):
    sys.modules.setdefault(_alias, sys.modules[__name__])
