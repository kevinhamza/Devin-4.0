"""
modules/os_automation.py — Devin's hands and eyes: real pointer, real keyboard, real screen.

One small API (`get_desktop()`) that works the same on every backend:

    d = get_desktop()
    img = d.capture()                  # PIL image of the screen as it is right now
    d.click(640, 360)                  # moves the pointer there and clicks
    d.type('hello world')              # real key presses into the focused field
    d.key('ctrl+l')                    # shortcuts
    d.settle()                         # blocks until the screen stops changing

Backends, picked automatically (override with DEVIN_INPUT_BACKEND):

  gnome     GNOME (Wayland or X11). Talks to Mutter's RemoteDesktop/ScreenCast D-Bus
            interfaces — the same ones GNOME Remote Desktop uses. No root needed.
            Exact absolute pointer positioning, damage-driven screen frames (no
            shutter flash, no files in ~/Pictures), accessibility-tree element list.
  ydotool   Any Wayland compositor. Needs the ydotoold daemon (uinput access).
  xdotool   Plain X11 sessions.
  pyautogui macOS / Windows.

The GNOME backend needs PyGObject, which lives in the *system* Python, not in the
project venv — so this same file doubles as a tiny helper process:
`/usr/bin/python3 os_automation.py --gnome-helper`. Only the standard library is
imported at module level for that reason.
"""
from __future__ import annotations

import atexit
import base64
import io
import json
import math
import os
import platform
import random
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from typing import Any, Dict, List, Optional, Tuple

PLATFORM = platform.system()  # 'Linux', 'Darwin', 'Windows'


class DesktopError(RuntimeError):
    """Raised when the desktop cannot be seen or controlled."""


# ══════════════════════════════════════════════════════════════════════════════
# Key names
# ══════════════════════════════════════════════════════════════════════════════

# name → (X11 keysym, Linux evdev keycode)
_KEYS: Dict[str, Tuple[int, int]] = {
    'return': (0xFF0D, 28), 'tab': (0xFF09, 15), 'escape': (0xFF1B, 1),
    'backspace': (0xFF08, 14), 'delete': (0xFFFF, 111), 'insert': (0xFF63, 110),
    'space': (0x0020, 57), 'home': (0xFF50, 102), 'end': (0xFF57, 107),
    'page_up': (0xFF55, 104), 'page_down': (0xFF56, 109),
    'up': (0xFF52, 103), 'down': (0xFF54, 108), 'left': (0xFF51, 105), 'right': (0xFF53, 106),
    'ctrl': (0xFFE3, 29), 'shift': (0xFFE1, 42), 'alt': (0xFFE9, 56), 'super': (0xFFEB, 125),
    'menu': (0xFF67, 127), 'print': (0xFF61, 99), 'caps_lock': (0xFFE5, 58),
    'volume_up': (0x1008FF13, 115), 'volume_down': (0x1008FF11, 114), 'volume_mute': (0x1008FF12, 113),
}
for _i, _code in enumerate((59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 87, 88), start=1):
    _KEYS[f'f{_i}'] = (0xFFBD + _i, _code)

_KEY_ALIASES = {
    'enter': 'return', 'esc': 'escape', 'del': 'delete', 'bksp': 'backspace', 'ins': 'insert',
    'control': 'ctrl', 'ctl': 'ctrl', 'option': 'alt', 'win': 'super', 'windows': 'super',
    'cmd': 'super', 'command': 'super', 'meta': 'super', 'pgup': 'page_up', 'pageup': 'page_up',
    'pgdn': 'page_down', 'pagedown': 'page_down', 'spacebar': 'space', 'prtsc': 'print',
    'printscreen': 'print', 'capslock': 'caps_lock', 'arrowup': 'up', 'arrowdown': 'down',
    'arrowleft': 'left', 'arrowright': 'right', 'volumeup': 'volume_up', 'volumedown': 'volume_down',
    'volumemute': 'volume_mute', 'xf86audioraisevolume': 'volume_up',
    'xf86audiolowervolume': 'volume_down', 'xf86audiomute': 'volume_mute',
}

# evdev keycodes for the characters ydotool's `key` needs in shortcuts (US layout)
_EVDEV_CHARS = {c: k for c, k in zip('1234567890-=', range(2, 14))}
_EVDEV_CHARS.update({c: k for c, k in zip('qwertyuiop[]', range(16, 28))})
_EVDEV_CHARS.update({c: k for c, k in zip("asdfghjkl;'`", range(30, 42))})
_EVDEV_CHARS.update({c: k for c, k in zip('\\zxcvbnm,./', range(43, 54))})

_SHIFTED = dict(zip('~!@#$%^&*()_+{}|:"<>?', "`1234567890-=[]\\;',./"))


def evdev_key_for(ch: str) -> Optional[Tuple[int, bool]]:
    """(keycode, needs_shift) for one character on a US keyboard, or None."""
    if ch == '\n':
        return 28, False
    if ch == '\t':
        return 15, False
    if ch == ' ':
        return 57, False
    if ch in _SHIFTED:
        return _EVDEV_CHARS[_SHIFTED[ch]], True
    if ch.isalpha() and ch.isupper() and ch.lower() in _EVDEV_CHARS:
        return _EVDEV_CHARS[ch.lower()], True
    if ch in _EVDEV_CHARS:
        return _EVDEV_CHARS[ch], False
    return None


_BUTTONS = {'left': 272, 'right': 273, 'middle': 274}  # evdev BTN_*


def normalize_key(name: str) -> str:
    """'Enter' → 'return', 'Ctrl' → 'ctrl', 'A' → 'a'. Single characters pass through."""
    n = str(name).strip()
    if len(n) == 1:
        return n
    n = n.lower().replace(' ', '_').replace('-', '_')
    n = _KEY_ALIASES.get(n, _KEY_ALIASES.get(n.replace('_', ''), n))
    if n not in _KEYS and n.replace('_', '') in _KEYS:
        n = n.replace('_', '')
    return n


def split_combo(combo: str) -> List[str]:
    """'Ctrl+Shift+T' → ['ctrl', 'shift', 't'].  '+' alone is the plus key."""
    combo = str(combo).strip()
    if combo in ('+', ''):
        return [combo] if combo else []
    parts = [p for p in combo.replace(' + ', '+').split('+')]
    keys = [normalize_key(p) for p in parts if p != '']
    if len(keys) > 1:  # in a shortcut, "T" means the t key
        keys = [k.lower() if len(k) == 1 else k for k in keys]
    if combo.endswith('++'):
        keys.append('+')
    return keys


def keysym_for(key: str) -> int:
    key = normalize_key(key)
    if key in _KEYS:
        return _KEYS[key][0]
    if len(key) == 1:
        return char_keysym(key)
    raise DesktopError(f'unknown key: {key!r}')


def char_keysym(ch: str) -> int:
    if ch == '\n':
        return 0xFF0D
    if ch == '\t':
        return 0xFF09
    cp = ord(ch)
    return cp if 0x20 <= cp <= 0xFF else 0x01000000 + cp


# ══════════════════════════════════════════════════════════════════════════════
# GNOME helper process (runs under the system Python — needs PyGObject)
# ══════════════════════════════════════════════════════════════════════════════

_RD = 'org.gnome.Mutter.RemoteDesktop'
_SC = 'org.gnome.Mutter.ScreenCast'

_A11Y_ROLES = {
    'push button', 'button', 'toggle button', 'entry', 'password text', 'text', 'link',
    'menu item', 'check menu item', 'radio menu item', 'check box', 'radio button',
    'combo box', 'page tab', 'list item', 'icon', 'menu', 'search bar', 'slider',
    'spin button', 'tree item', 'table cell', 'document web', 'heading', 'image',
    'tool bar', 'switch',
}
_A11Y_TEXT_ROLES = {'entry', 'password text', 'text', 'search bar', 'combo box', 'spin button'}


def _gnome_helper_main() -> int:
    """Serve desktop requests as JSON lines on stdin → JSON line (+ raw bytes) on stdout."""
    out = sys.stdout.buffer
    sys.stdout = sys.stderr  # nothing but protocol frames may reach the real stdout

    def reply(obj: Dict[str, Any], blob: bytes = b'') -> None:
        if blob:
            obj['bytes'] = len(blob)
        out.write(json.dumps(obj).encode() + b'\n')
        if blob:
            out.write(blob)
        out.flush()

    try:
        import gi
        gi.require_version('Gst', '1.0')
        from gi.repository import Gio, GLib, Gst
    except Exception as e:  # PyGObject / GStreamer missing
        reply({'ok': False, 'fatal': True, 'error': f'PyGObject/GStreamer unavailable: {e}'})
        return 2

    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

    def call(dest, path, iface, method, args=None, timeout=5000):
        return bus.call_sync(dest, path, iface, method, args, None,
                             Gio.DBusCallFlags.NONE, timeout, None)

    # ── Session: RemoteDesktop (input) + ScreenCast (frames, absolute pointer) ──
    state: Dict[str, Any] = {'node': None, 'closed': False}
    try:
        (rd_path,) = call(_RD, '/org/gnome/Mutter/RemoteDesktop', _RD, 'CreateSession').unpack()
        session_id = call(_RD, rd_path, 'org.freedesktop.DBus.Properties', 'Get',
                          GLib.Variant('(ss)', (_RD + '.Session', 'SessionId'))).unpack()[0]
        (sc_path,) = call(_SC, '/org/gnome/Mutter/ScreenCast', _SC, 'CreateSession',
                          GLib.Variant('(a{sv})', ({'remote-desktop-session-id':
                                                    GLib.Variant('s', session_id)},))).unpack()
        (stream_path,) = call(_SC, sc_path, _SC + '.Session', 'RecordMonitor',
                              GLib.Variant('(sa{sv})', ('', {'cursor-mode': GLib.Variant('u', 0)}))).unpack()

        def on_stream(_c, _s, _p, _i, _sig, params):
            state['node'] = params.unpack()[0]

        def on_closed(*_a):
            state['closed'] = True

        bus.signal_subscribe(_SC, _SC + '.Stream', 'PipeWireStreamAdded', stream_path,
                             None, Gio.DBusSignalFlags.NONE, on_stream)
        bus.signal_subscribe(_RD, _RD + '.Session', 'Closed', rd_path,
                             None, Gio.DBusSignalFlags.NONE, on_closed)
        call(_RD, rd_path, _RD + '.Session', 'Start')
    except Exception as e:
        reply({'ok': False, 'fatal': True, 'error': f'Mutter remote-desktop session failed: {e}'})
        return 3

    ctx = GLib.MainContext.default()
    deadline = time.monotonic() + 5.0
    while state['node'] is None and time.monotonic() < deadline:
        ctx.iteration(False)
        time.sleep(0.01)
    if state['node'] is None:
        reply({'ok': False, 'fatal': True, 'error': 'ScreenCast stream never appeared'})
        return 4

    # ── Frames: PipeWire → appsink. Mutter only sends a frame when the screen changes,
    #    so "no new frame" literally means "nothing moved". ──
    Gst.init(None)
    try:
        import numpy as np
    except Exception:
        np = None

    frame: Dict[str, Any] = {'data': None, 'w': 0, 'h': 0, 'n': 0, 't': 0.0, 'major': 0.0, 'thumb': None}
    flock = threading.Lock()
    mark: Dict[str, Any] = {'thumb': None, 't': 0.0, 'ambient': None}
    ambient: Dict[str, Any] = {'mask': None, 'collect': True}

    def set_mark() -> None:
        """Snapshot the screen just before an action; settle() measures change against it.

        Regions that kept flickering while nothing was being done (learned since the
        last settle) are frozen into a mask and ignored, so a ticking clock is never
        mistaken for the effect of a click.
        """
        with flock:
            mark['thumb'] = frame['thumb']
            mark['t'] = time.monotonic()
            if ambient['collect']:
                amb = ambient['mask']
                frozen = None
                if amb is not None and amb.any() and amb.mean() < 0.35:
                    frozen = amb.copy()
                    for dy in (-2, -1, 0, 1, 2):
                        for dx in (-2, -1, 0, 1, 2):
                            frozen |= np.roll(np.roll(amb, dy, axis=0), dx, axis=1)
                mark['ambient'] = frozen
                ambient['collect'] = False

    def change_since_mark() -> float:
        with flock:
            a, b, frozen = mark['thumb'], frame['thumb'], mark['ambient']
        if np is None or a is None or b is None or a.shape != b.shape:
            return -1.0
        diff = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2) > 8
        if frozen is not None and frozen.shape == diff.shape:
            diff &= ~frozen
        return float(diff.mean())

    def resume_ambient() -> None:
        with flock:
            ambient['mask'] = None
            ambient['collect'] = True

    def on_sample(sink):
        sample = sink.emit('pull-sample')
        if sample is None:
            return Gst.FlowReturn.OK
        st = sample.get_caps().get_structure(0)
        w, h = st.get_value('width'), st.get_value('height')
        buf = sample.get_buffer()
        ok, info = buf.map(Gst.MapFlags.READ)
        if not ok:
            return Gst.FlowReturn.OK
        try:
            data = bytes(info.data)
        finally:
            buf.unmap(info)
        now = time.monotonic()
        changed = 1.0
        thumb = None
        with flock:
            if np is not None and len(data) >= w * h * 4:
                # Subsampled copy: cheap way to tell a blinking caret from a page load.
                thumb = np.frombuffer(data, dtype=np.uint8, count=w * h * 4).reshape(h, w, 4)[::4, ::4, :3].copy()
                prev = frame['thumb']
                if prev is not None and prev.shape == thumb.shape:
                    diff = np.abs(thumb.astype(np.int16) - prev.astype(np.int16)).max(axis=2) > 8
                    if ambient['collect']:
                        # Nobody is acting right now, so whatever moves is the desktop's own
                        # flicker: clock, CPU meter, caret, a playing video.
                        amb = ambient['mask']
                        if amb is None or amb.shape != diff.shape:
                            ambient['mask'] = diff.copy()
                        else:
                            amb |= diff
                    frozen = mark['ambient']
                    if frozen is not None and frozen.shape == diff.shape:
                        diff = diff & ~frozen
                    changed = float(diff.mean())
            frame.update(data=data, w=w, h=h, n=frame['n'] + 1, t=now, thumb=thumb)
            if changed >= 0.004:  # more than a caret/clock tick
                frame['major'] = now
        return Gst.FlowReturn.OK

    pipeline = Gst.parse_launch(
        f'pipewiresrc path={state["node"]} do-timestamp=true ! videoconvert ! '
        'video/x-raw,format=RGBx ! appsink name=sink emit-signals=true max-buffers=2 drop=true sync=false')
    pipeline.get_by_name('sink').connect('new-sample', on_sample)
    pipeline.set_state(Gst.State.PLAYING)

    deadline = time.monotonic() + 6.0
    while frame['data'] is None and time.monotonic() < deadline:
        ctx.iteration(False)
        time.sleep(0.02)

    session = _RD + '.Session'
    pointer = {'x': None, 'y': None}

    def notify(method: str, sig: str, *args) -> None:
        call(_RD, rd_path, session, method, GLib.Variant(sig, args), 2000)

    def move_to(x: float, y: float, duration: float = 0.0) -> None:
        """Glide the pointer to (x, y). A negative duration means "at a human pace":
        longer trips take longer, and the path bends slightly the way a hand's does."""
        x, y = float(x), float(y)
        sx, sy = pointer['x'], pointer['y']
        if sx is None:  # first move of the session: Wayland does not say where the pointer is
            sx, sy = frame['w'] / 2.0, frame['h'] / 2.0
            notify('NotifyPointerMotionAbsolute', '(sdd)', stream_path, sx, sy)
        dist = math.hypot(x - sx, y - sy)
        if duration < 0:
            duration = 0.0 if dist < 3 else max(0.16, min(0.75, 0.12 + dist / 1700.0))
        if duration > 0 and dist >= 3:
            steps = max(2, min(45, int(duration * 60)))
            bend = dist * 0.05 * (1 if (int(x) + int(y)) % 2 else -1)
            nx, ny = -(y - sy) / dist, (x - sx) / dist  # unit vector across the path
            for i in range(1, steps):
                t = i / steps
                e = t * t * (3 - 2 * t)  # ease in/out
                arc = math.sin(math.pi * e) * bend
                notify('NotifyPointerMotionAbsolute', '(sdd)', stream_path,
                       sx + (x - sx) * e + nx * arc, sy + (y - sy) * e + ny * arc)
                time.sleep(duration / steps)
        notify('NotifyPointerMotionAbsolute', '(sdd)', stream_path, x, y)
        pointer['x'], pointer['y'] = x, y

    def button(name: str, down: bool) -> None:
        notify('NotifyPointerButton', '(ib)', _BUTTONS.get(name, 272), down)

    def keysym(sym: int, down: bool) -> None:
        notify('NotifyKeyboardKeysym', '(ub)', int(sym), down)

    def settle(quiet: float, timeout: float, minimum: float, expect: float,
               min_change: float) -> Dict[str, Any]:
        try:
            return _settle(quiet, timeout, minimum, expect, min_change)
        finally:
            resume_ambient()  # the screen is at rest again: start learning its flicker

    def _settle(quiet: float, timeout: float, minimum: float, expect: float,
                min_change: float) -> Dict[str, Any]:
        start = time.monotonic()
        since = mark['t'] if 0 < start - mark['t'] < 60 else start
        time.sleep(max(0.0, minimum))
        while True:
            now = time.monotonic()
            with flock:
                last_major = frame['major']
            change = change_since_mark()
            began = change >= min_change if change >= 0 else last_major > since
            waited = round(now - start, 2)
            if not began:
                # Nothing has moved yet. Give the action `expect` seconds to show an effect.
                if now - start >= expect:
                    return {'stable': True, 'changed': False, 'change': round(max(change, 0.0), 4),
                            'waited': waited}
            elif now - max(last_major, since) >= quiet:
                return {'stable': True, 'changed': True, 'change': round(max(change, 0.0), 4), 'waited': waited}
            if now - start >= timeout:
                return {'stable': False, 'changed': began, 'change': round(max(change, 0.0), 4), 'waited': waited}
            time.sleep(0.03)

    # ── Accessibility tree → clickable elements in screen coordinates ──
    atspi: Dict[str, Any] = {'mod': None, 'tried': False}

    def get_atspi():
        if not atspi['tried']:
            atspi['tried'] = True
            try:
                # Apps (Chrome, Electron, Qt) only publish their UI tree once this is on.
                call('org.a11y.Bus', '/org/a11y/bus', 'org.freedesktop.DBus.Properties', 'Set',
                     GLib.Variant('(ssv)', ('org.a11y.Status', 'IsEnabled', GLib.Variant('b', True))))
            except Exception:
                pass
            try:
                gi.require_version('Atspi', '2.0')
                from gi.repository import Atspi
                Atspi.init()
                try:
                    Atspi.set_timeout(400, 2000)
                except Exception:
                    pass
                atspi['mod'] = Atspi
            except Exception:
                atspi['mod'] = None
        return atspi['mod']

    def elements(budget: float, limit: int) -> Dict[str, Any]:
        Atspi = get_atspi()
        if Atspi is None:
            return {'elements': [], 'window': '', 'app': '', 'note': 'accessibility unavailable'}
        t0 = time.monotonic()
        clock = {'end': t0 + budget}
        desk = Atspi.get_desktop(0)
        shell, active, active_app = None, None, ''
        win_rects: List[Tuple[int, int, int, int]] = []
        for i in range(desk.get_child_count()):
            try:
                app = desk.get_child_at_index(i)
                name = app.get_name() or ''
                if name == 'gnome-shell':
                    shell = app
                    continue
                for j in range(app.get_child_count()):
                    win = app.get_child_at_index(j)
                    if win is not None and win.get_state_set().contains(Atspi.StateType.ACTIVE):
                        active, active_app = win, name
            except Exception:
                continue

        found: List[Dict[str, Any]] = []
        seen = set()

        def add(node, role, ox, oy, ctype, shell_item=False):
            try:
                e = node.get_extents(ctype)
            except Exception:
                return
            if e.width < 4 or e.height < 4:
                return
            x, y = e.x + ox, e.y + oy
            if x + e.width <= 0 or y + e.height <= 0 or x >= frame['w'] or y >= frame['h']:
                return
            name = (node.get_name() or '').strip()
            value = ''
            if role in _A11Y_TEXT_ROLES:
                try:
                    value = (Atspi.Text.get_text(node, 0, 120) or '').strip()
                except Exception:
                    value = ''
            if not name:
                try:
                    name = (node.get_description() or '').strip()
                except Exception:
                    name = ''
            if not name and not value and role not in _A11Y_TEXT_ROLES:
                return
            key = (role, name, x // 4, y // 4)
            if key in seen:
                return
            seen.add(key)
            item = {'role': role, 'name': name[:80], 'x': int(x), 'y': int(y),
                    'w': int(e.width), 'h': int(e.height)}
            if value:
                item['value'] = value[:120]
            try:
                states = node.get_state_set()
                if states.contains(Atspi.StateType.FOCUSED):
                    item['focused'] = True
                if states.contains(Atspi.StateType.EDITABLE):
                    item['editable'] = True
            except Exception:
                pass
            if shell_item:
                item['shell'] = True
            found.append(item)

        def window_rects(root):
            # Shallow pass over the shell: just where the windows are, bottom to top.
            queue = [(root, 0)]
            while queue and time.monotonic() < clock['end']:
                node, depth = queue.pop(0)
                try:
                    if (node.get_name() or '') == 'Wayland window':
                        e = node.get_extents(Atspi.CoordType.SCREEN)
                        if e.width > 1 and e.height > 1:
                            win_rects.append((e.x, e.y, e.width, e.height))
                        continue
                    if depth < 5:
                        for k in range(min(node.get_child_count(), 200)):
                            child = node.get_child_at_index(k)
                            if child is not None:
                                queue.append((child, depth + 1))
                except Exception:
                    continue

        def walk(root, ox, oy, cap, ctype, shell_item=False):
            queue = [root]
            while queue and len(found) < cap and time.monotonic() < clock['end']:
                node = queue.pop(0)
                try:
                    role = node.get_role_name()
                    states = node.get_state_set()
                    if node is not root and not states.contains(Atspi.StateType.SHOWING):
                        if role not in ('application', 'window', 'frame', 'panel', 'filler'):
                            continue
                    if role in _A11Y_ROLES:
                        add(node, role, ox, oy, ctype, shell_item)
                    if role == 'panel' and (node.get_name() or '') == 'Wayland window':
                        continue  # window contents belong to the app, not the shell
                    for k in range(min(node.get_child_count(), 400)):
                        child = node.get_child_at_index(k)
                        if child is not None:
                            queue.append(child)
                except Exception:
                    continue

        title = ''
        rect: List[int] = []
        if shell is not None:
            clock['end'] = t0 + budget * 0.2
            window_rects(shell)
        if active is not None:
            clock['end'] = t0 + budget * 0.75  # the window in front matters most
            ox = oy = 0
            try:
                title = active.get_name() or ''
                e = active.get_extents(Atspi.CoordType.SCREEN)
                ox, oy = max(e.x, 0), max(e.y, 0)
                # On Wayland an app only knows positions relative to its own window. The
                # shell knows where each window really is: take the top-most one whose
                # size fits (its rectangle may include an invisible shadow border).
                for rx, ry, rw, rh in reversed(win_rects):
                    mx, my = rw - e.width, rh - e.height
                    if 0 <= mx <= 160 and 0 <= my <= 160:
                        ox, oy = rx + mx // 2, ry + my // 2
                        break
                if e.width > 1 and e.height > 1:
                    rect = [int(ox), int(oy), int(e.width), int(e.height)]   # where the window is on screen
            except Exception:
                pass
            walk(active, ox, oy, limit, Atspi.CoordType.WINDOW)
        if shell is not None:  # top bar, dock, overview — with whatever time is left
            clock['end'] = t0 + budget
            walk(shell, 0, 0, len(found) + max(20, limit // 3), Atspi.CoordType.SCREEN, True)
        # Some programs (Chrome, at times) do not say which of their windows is active. The
        # shell still knows where the top-most window is.
        top = [int(v) for v in win_rects[-1]] if win_rects else []
        return {'elements': found, 'window': title, 'app': active_app, 'rect': rect, 'top_rect': top}

    # ── Request loop ──
    reply({'ok': True, 'ready': True, 'w': frame['w'], 'h': frame['h'],
           'frames': frame['data'] is not None})

    for raw in sys.stdin.buffer:
        try:
            req = json.loads(raw)
        except Exception:
            continue
        op = req.get('op')
        try:
            while ctx.iteration(False):
                pass
            if state['closed']:
                reply({'ok': False, 'fatal': True, 'error': 'the desktop session was closed'})
                break
            if op == 'ping':
                reply({'ok': True, 'w': frame['w'], 'h': frame['h'], 'frames': frame['n']})
            elif op == 'frame':
                with flock:
                    data, w, h, n = frame['data'], frame['w'], frame['h'], frame['n']
                if data is None:
                    reply({'ok': False, 'error': 'no frame received from the compositor yet'})
                else:
                    reply({'ok': True, 'w': w, 'h': h, 'n': n}, data[:w * h * 4])
            elif op == 'settle':
                reply({'ok': True, **settle(float(req.get('quiet', 0.5)), float(req.get('timeout', 8)),
                                            float(req.get('min', 0.12)), float(req.get('expect', 1.2)),
                                            float(req.get('min_change', 0.0002)))})
            elif op == 'mark':
                set_mark()
                reply({'ok': True})
            elif op == 'move':
                move_to(req['x'], req['y'], float(req.get('duration', 0)))
                reply({'ok': True})
            elif op == 'click':
                move_to(req['x'], req['y'], float(req.get('duration', -1)))
                time.sleep(0.11)
                set_mark()  # after the pointer arrived: hover effects are not the click's effect
                for i in range(int(req.get('count', 1))):
                    if i:
                        time.sleep(0.09)
                    button(req.get('button', 'left'), True)
                    time.sleep(0.06)
                    button(req.get('button', 'left'), False)
                reply({'ok': True})
            elif op == 'drag':
                move_to(req['x1'], req['y1'], -1)
                time.sleep(0.1)
                set_mark()
                button('left', True)
                time.sleep(0.12)
                move_to(req['x2'], req['y2'], float(req.get('duration', 0.5)))
                time.sleep(0.12)
                button('left', False)
                reply({'ok': True})
            elif op == 'scroll':
                if req.get('x') is not None:
                    move_to(req['x'], req['y'], -1)
                    time.sleep(0.05)
                set_mark()
                for axis, steps in ((0, int(req.get('dy', 0))), (1, int(req.get('dx', 0)))):
                    for _ in range(abs(steps)):
                        notify('NotifyPointerAxisDiscrete', '(ui)', axis, 1 if steps > 0 else -1)
                        time.sleep(0.025)
                reply({'ok': True})
            elif op == 'keys':  # press all in order, release in reverse
                syms = [int(s) for s in req['syms']]
                set_mark()
                for s in syms:
                    keysym(s, True)
                    time.sleep(0.02)
                time.sleep(0.03)
                for s in reversed(syms):
                    keysym(s, False)
                    time.sleep(0.01)
                reply({'ok': True})
            elif op == 'keydown':
                keysym(req['sym'], True)
                reply({'ok': True})
            elif op == 'keyup':
                keysym(req['sym'], False)
                reply({'ok': True})
            elif op == 'type':
                gap = float(req.get('interval', 0.045))
                set_mark()
                for s in req['syms']:
                    keysym(s, True)
                    time.sleep(0.008)
                    keysym(s, False)
                    # a person's keystrokes are uneven, with a beat after each word
                    time.sleep(gap * random.uniform(0.55, 1.45) * (1.6 if s == 0x20 else 1.0))
                reply({'ok': True})
            elif op == 'elements':
                reply({'ok': True, **elements(float(req.get('budget', 1.5)), int(req.get('limit', 160)))})
            elif op == 'quit':
                reply({'ok': True})
                break
            else:
                reply({'ok': False, 'error': f'unknown op {op!r}'})
        except Exception as e:
            reply({'ok': False, 'error': f'{type(e).__name__}: {e}'})

    try:
        pipeline.set_state(Gst.State.NULL)
        call(_RD, rd_path, session, 'Stop')
    except Exception:
        pass
    return 0


# ══════════════════════════════════════════════════════════════════════════════
# Backends
# ══════════════════════════════════════════════════════════════════════════════

def _pil():
    try:
        from PIL import Image
        return Image
    except Exception as e:
        raise DesktopError('Pillow is required for screenshots (pip install pillow)') from e


def _run(cmd: List[str], timeout: float = 10, env: Optional[dict] = None,
         input_bytes: Optional[bytes] = None) -> Tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, env=env, input=input_bytes)
        return r.returncode, (r.stdout or b'').decode('utf-8', 'replace').strip()
    except FileNotFoundError:
        return 127, ''
    except subprocess.TimeoutExpired:
        return 124, ''


class _Backend:
    name = 'none'
    native_settle = False

    def size(self) -> Tuple[int, int]: raise NotImplementedError
    def capture(self): raise NotImplementedError
    def move(self, x: int, y: int, duration: float = 0.15) -> None: raise NotImplementedError
    def click(self, x: int, y: int, button: str = 'left', count: int = 1) -> None: raise NotImplementedError
    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> None: raise NotImplementedError
    def scroll(self, x: Optional[int], y: Optional[int], dy: int = 0, dx: int = 0) -> None: raise NotImplementedError
    def keys(self, keys: List[str]) -> None: raise NotImplementedError
    def type_ascii(self, text: str, interval: float) -> None: raise NotImplementedError
    def key_down(self, key: str) -> None: raise NotImplementedError
    def key_up(self, key: str) -> None: raise NotImplementedError
    def elements(self, budget: float = 1.5, limit: int = 160) -> Dict[str, Any]:
        return {'elements': [], 'window': '', 'app': ''}
    def settle(self, quiet: float, timeout: float, minimum: float, expect: float,
               min_change: float) -> Dict[str, Any]: raise NotImplementedError
    def mark(self) -> None: pass
    def close(self) -> None: pass


class _GnomeBackend(_Backend):
    """Mutter RemoteDesktop + ScreenCast through the helper process."""
    name = 'gnome'
    native_settle = True

    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.RLock()
        self._size = (0, 0)
        self._start()

    @staticmethod
    def available() -> bool:
        if PLATFORM != 'Linux' or not shutil.which('gdbus') or not _system_python():
            return False
        code, out = _run(['gdbus', 'call', '--session', '--dest', 'org.freedesktop.DBus',
                          '--object-path', '/org/freedesktop/DBus',
                          '--method', 'org.freedesktop.DBus.NameHasOwner', _RD], timeout=4)
        return code == 0 and 'true' in out

    def _start(self) -> None:
        py = _system_python()
        if not py:
            raise DesktopError('system Python with PyGObject not found (apt install python3-gi)')
        self._proc = subprocess.Popen(
            [py, os.path.abspath(__file__), '--gnome-helper'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            start_new_session=True)
        hello = self._read()
        if not hello.get('ok'):
            self.close()
            raise DesktopError(hello.get('error', 'GNOME desktop helper failed to start'))
        self._size = (int(hello.get('w') or 0), int(hello.get('h') or 0))

    def _read(self) -> Dict[str, Any]:
        assert self._proc and self._proc.stdout
        line = self._proc.stdout.readline()
        if not line:
            raise DesktopError('GNOME desktop helper exited')
        msg = json.loads(line)
        n = int(msg.get('bytes') or 0)
        if n:
            buf = bytearray()
            while len(buf) < n:
                chunk = self._proc.stdout.read(n - len(buf))
                if not chunk:
                    raise DesktopError('GNOME desktop helper closed mid-frame')
                buf.extend(chunk)
            msg['blob'] = bytes(buf)
        return msg

    def _call(self, op: str, _retry: bool = True, **kw) -> Dict[str, Any]:
        with self._lock:
            try:
                if self._proc is None or self._proc.poll() is not None:
                    self._start()
                assert self._proc and self._proc.stdin
                self._proc.stdin.write(json.dumps({'op': op, **kw}).encode() + b'\n')
                self._proc.stdin.flush()
                msg = self._read()
            except (BrokenPipeError, DesktopError, OSError, ValueError):
                self.close()
                if _retry:
                    return self._call(op, _retry=False, **kw)
                raise DesktopError('lost the connection to the GNOME desktop session')
            if msg.get('fatal'):
                self.close()
                if _retry:
                    return self._call(op, _retry=False, **kw)
            if not msg.get('ok'):
                raise DesktopError(msg.get('error', f'{op} failed'))
            return msg

    def size(self):
        if not all(self._size):
            m = self._call('ping')
            self._size = (int(m['w']), int(m['h']))
        return self._size

    def capture(self):
        m = self._call('frame')
        w, h = int(m['w']), int(m['h'])
        self._size = (w, h)
        return _pil().frombuffer('RGBX', (w, h), m['blob'], 'raw', 'RGBX', 0, 1).convert('RGB')

    def settle(self, quiet, timeout, minimum, expect, min_change):
        m = self._call('settle', quiet=quiet, timeout=timeout, min=minimum, expect=expect,
                       min_change=min_change)
        return {k: m[k] for k in ('stable', 'changed', 'change', 'waited') if k in m}

    def mark(self):
        self._call('mark')

    def move(self, x, y, duration=0.15):
        self._call('move', x=x, y=y, duration=duration)

    def click(self, x, y, button='left', count=1):
        self._call('click', x=x, y=y, button=button, count=count)

    def drag(self, x1, y1, x2, y2, duration=0.5):
        self._call('drag', x1=x1, y1=y1, x2=x2, y2=y2, duration=duration)

    def scroll(self, x, y, dy=0, dx=0):
        self._call('scroll', x=x, y=y, dy=dy, dx=dx)

    def keys(self, keys):
        self._call('keys', syms=[keysym_for(k) for k in keys])

    def key_down(self, key):
        self._call('keydown', sym=keysym_for(key))

    def key_up(self, key):
        self._call('keyup', sym=keysym_for(key))

    def type_ascii(self, text, interval):
        self._call('type', syms=[char_keysym(c) for c in text], interval=interval)

    def elements(self, budget=1.5, limit=160):
        try:
            m = self._call('elements', budget=budget, limit=limit)
            return {'elements': m.get('elements', []), 'window': m.get('window', ''), 'app': m.get('app', ''),
                    'rect': m.get('rect') or [], 'top_rect': m.get('top_rect') or []}
        except DesktopError:
            return {'elements': [], 'window': '', 'app': ''}

    def close(self):
        p, self._proc = self._proc, None
        if p is None:
            return
        try:
            if p.poll() is None and p.stdin:
                p.stdin.write(b'{"op":"quit"}\n')
                p.stdin.flush()
                p.wait(timeout=1.5)
        except Exception:
            pass
        try:
            if p.poll() is None:
                p.kill()
        except Exception:
            pass


def _system_python() -> Optional[str]:
    """A Python that can `import gi` (PyGObject ships with the distro, not with pip)."""
    cached = getattr(_system_python, '_v', False)
    if cached is not False:
        return cached
    found = None
    for py in (os.environ.get('DEVIN_SYSTEM_PYTHON'), '/usr/bin/python3', sys.executable):
        if py and os.path.exists(py):
            code, _ = _run([py, '-c', 'import gi'], timeout=8)
            if code == 0:
                found = py
                break
    _system_python._v = found  # type: ignore[attr-defined]
    return found


class _ShellScreenshots:
    """Screen capture for backends that only inject input."""

    def _portal(self):
        # XDG desktop portal: works on every Wayland desktop, but flashes the screen.
        py = _system_python()
        if not py:
            return None
        script = (
            "import sys,gi\n"
            "from gi.repository import Gio,GLib\n"
            "b=Gio.bus_get_sync(Gio.BusType.SESSION,None);l=GLib.MainLoop();r={}\n"
            "t='devin%d'%__import__('os').getpid()\n"
            "h='/org/freedesktop/portal/desktop/request/%s/%s'%(b.get_unique_name()[1:].replace('.','_'),t)\n"
            "def cb(c,s,p,i,g,v):\n r['v']=v.unpack();l.quit()\n"
            "b.signal_subscribe('org.freedesktop.portal.Desktop','org.freedesktop.portal.Request','Response',h,None,0,cb)\n"
            "b.call_sync('org.freedesktop.portal.Desktop','/org/freedesktop/portal/desktop',"
            "'org.freedesktop.portal.Screenshot','Screenshot',GLib.Variant('(sa{sv})',('',"
            "{'handle_token':GLib.Variant('s',t),'interactive':GLib.Variant('b',False)})),None,0,8000,None)\n"
            "GLib.timeout_add(10000,l.quit);l.run()\n"
            "v=r.get('v')\n"
            "print(v[1]['uri'] if v and v[0]==0 else '')\n")
        code, out = _run([py, '-c', script], timeout=15)
        uri = out.splitlines()[-1] if out else ''
        if code != 0 or not uri.startswith('file://'):
            return None
        from urllib.parse import unquote
        path = unquote(uri[7:])
        try:
            img = _pil().open(path).convert('RGB')
            img.load()
            return img
        finally:
            try:
                os.remove(path)  # the portal drops a copy in ~/Pictures every time
            except OSError:
                pass

    def _grab(self):
        Image = _pil()
        wayland = bool(os.environ.get('WAYLAND_DISPLAY'))
        if wayland:
            if shutil.which('grim'):
                code, _ = _run(['grim', '-t', 'ppm', _tmp_path('grim.ppm')])
                if code == 0:
                    return Image.open(_tmp_path('grim.ppm')).convert('RGB')
            img = self._portal()
            if img is not None:
                return img
            raise DesktopError('no Wayland screenshot method worked (install grim, or use GNOME)')
        try:
            import mss
            with mss.mss() as sct:
                mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                shot = sct.grab(mon)
                return Image.frombytes('RGB', shot.size, shot.rgb)
        except Exception:
            pass
        if shutil.which('scrot'):
            p = _tmp_path('scrot.png')
            code, _ = _run(['scrot', '-o', p])
            if code == 0:
                return Image.open(p).convert('RGB')
        raise DesktopError('no screenshot method worked (pip install mss, or apt install scrot)')

    def capture(self):
        img = self._grab()
        self._size = img.size
        return img

    def size(self):
        s = getattr(self, '_size', None)
        if not s:
            s = self.capture().size
        return s


class _YdotoolBackend(_ShellScreenshots, _Backend):
    """Kernel-level input through ydotoold (works on any Wayland compositor)."""
    name = 'ydotool'

    def __init__(self):
        self._sock = ydotool_socket()
        if not self._sock:
            raise DesktopError(ydotool_help())
        self._abs = None       # evdev absolute pointer, created on first use
        self._abs_failed = False

    def _abs_pointer(self):
        """An absolute pointing device of our own, like the tablet a virtual machine uses.

        ydotool can only send *relative* motion, which the desktop then accelerates, so
        "move to 400,300" lands somewhere else. An absolute device has no acceleration:
        the coordinates it reports are the coordinates the pointer goes to. It needs the
        same /dev/uinput access that ydotoold itself needs.
        """
        if self._abs is not None or self._abs_failed:
            return self._abs
        try:
            from evdev import AbsInfo, UInput, ecodes as e
            w, h = self.size()
            caps = {e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
                    e.EV_ABS: [(e.ABS_X, AbsInfo(0, 0, w - 1, 0, 0, 0)),
                               (e.ABS_Y, AbsInfo(0, 0, h - 1, 0, 0, 0))]}
            self._abs = UInput(caps, name='devin-pointer')
            time.sleep(0.6)  # give the compositor time to notice the new device
        except Exception:
            self._abs_failed = True
            self._abs = None
        return self._abs

    def close(self):
        dev, self._abs = self._abs, None
        if dev is not None:
            try:
                dev.close()
            except Exception:
                pass

    @staticmethod
    def available() -> bool:
        return PLATFORM == 'Linux' and bool(shutil.which('ydotool')) and bool(ydotool_socket())

    def _yd(self, *args: str) -> None:
        env = {**os.environ, 'YDOTOOL_SOCKET': self._sock or ''}
        code, out = _run(['ydotool', *args], timeout=30, env=env)
        if code != 0:
            raise DesktopError(f'ydotool {args[0]} failed: {out or "exit %d" % code}')

    def _code(self, key: str) -> int:
        key = normalize_key(key)
        if key in _KEYS:
            return _KEYS[key][1]
        if len(key) == 1 and key.lower() in _EVDEV_CHARS:
            return _EVDEV_CHARS[key.lower()]
        raise DesktopError(f'ydotool cannot press {key!r}')

    def move(self, x, y, duration=0.15):
        dev = self._abs_pointer()
        if dev is not None:
            from evdev import ecodes as e
            dev.write(e.EV_ABS, e.ABS_X, int(x))
            dev.write(e.EV_ABS, e.ABS_Y, int(y))
            dev.syn()
            time.sleep(0.03)
            return
        # Fallback without python-evdev: slam into the corner, then walk out in small
        # steps. Pointer acceleration makes this approximate.
        self._yd('mousemove', '-x', '-10000', '-y', '-10000')
        remaining_x, remaining_y = int(x), int(y)
        while remaining_x or remaining_y:
            sx = max(-40, min(40, remaining_x))
            sy = max(-40, min(40, remaining_y))
            self._yd('mousemove', '-x', str(sx), '-y', str(sy))
            remaining_x -= sx
            remaining_y -= sy

    def click(self, x, y, button='left', count=1):
        self.move(x, y)
        time.sleep(0.06)
        code = {'left': '0xC0', 'right': '0xC1', 'middle': '0xC2'}.get(button, '0xC0')
        for i in range(count):
            if i:
                time.sleep(0.09)
            self._yd('click', code)

    def drag(self, x1, y1, x2, y2, duration=0.5):
        self.move(x1, y1)
        self._yd('click', '0x40')
        time.sleep(0.12)
        steps = 12
        for i in range(1, steps + 1):
            self._yd('mousemove', '-x', str(int((x2 - x1) / steps)), '-y', str(int((y2 - y1) / steps)))
            time.sleep(duration / steps)
        self._yd('click', '0x80')

    def scroll(self, x, y, dy=0, dx=0):
        if x is not None:
            self.move(x, y)
        if dy:
            self._yd('mousemove', '-w', '-x', '0', '-y', str(-dy))
        if dx:
            self._yd('mousemove', '-w', '-x', str(dx), '-y', '0')

    def keys(self, keys):
        codes = [self._code(k) for k in keys]
        seq = [f'{c}:1' for c in codes] + [f'{c}:0' for c in reversed(codes)]
        self._yd('key', '-d', '25', *seq)

    def key_down(self, key):
        self._yd('key', f'{self._code(key)}:1')

    def key_up(self, key):
        self._yd('key', f'{self._code(key)}:0')

    def type_ascii(self, text, interval):
        # Not `ydotool type`: at speed it loses track of Shift and capitalises the wrong
        # letters. Every character here is an explicit key press, and Shift is pressed
        # and released around each character that needs it, with a pause between every
        # event so the desktop can never see them out of order.
        events: List[str] = []
        for ch in text:
            key = evdev_key_for(ch)
            if key is None:
                continue
            code, shift = key
            if shift:
                events.append('42:1')
            events += [f'{code}:1', f'{code}:0']
            if shift:
                events.append('42:0')
        delay = str(max(20, int(interval * 1000)))
        start = 0
        while start < len(events):
            end = min(start + 120, len(events))
            # never end a batch while Shift is still held
            while end < len(events) and events[start:end].count('42:1') != events[start:end].count('42:0'):
                end += 1
            self._yd('key', '-d', delay, *events[start:end])
            start = end


class _XdotoolBackend(_ShellScreenshots, _Backend):
    """Plain X11 sessions."""
    name = 'xdotool'

    @staticmethod
    def available() -> bool:
        return (PLATFORM == 'Linux' and bool(shutil.which('xdotool'))
                and bool(os.environ.get('DISPLAY')) and not os.environ.get('WAYLAND_DISPLAY'))

    def _x(self, *args: str) -> str:
        code, out = _run(['xdotool', *args], timeout=30)
        if code != 0:
            raise DesktopError(f'xdotool {args[0]} failed')
        return out

    @staticmethod
    def _name(key: str) -> str:
        key = normalize_key(key)
        names = {'return': 'Return', 'tab': 'Tab', 'escape': 'Escape', 'backspace': 'BackSpace',
                 'delete': 'Delete', 'insert': 'Insert', 'home': 'Home', 'end': 'End',
                 'page_up': 'Page_Up', 'page_down': 'Page_Down', 'up': 'Up', 'down': 'Down',
                 'left': 'Left', 'right': 'Right', 'ctrl': 'ctrl', 'shift': 'shift', 'alt': 'alt',
                 'super': 'super', 'space': 'space', 'menu': 'Menu', 'print': 'Print',
                 'caps_lock': 'Caps_Lock', 'volume_up': 'XF86AudioRaiseVolume',
                 'volume_down': 'XF86AudioLowerVolume', 'volume_mute': 'XF86AudioMute'}
        if key in names:
            return names[key]
        return key.upper() if key.startswith('f') and key[1:].isdigit() else key

    def move(self, x, y, duration=0.15):
        self._x('mousemove', '--sync', str(int(x)), str(int(y)))

    def click(self, x, y, button='left', count=1):
        self.move(x, y)
        time.sleep(0.05)
        b = {'left': '1', 'middle': '2', 'right': '3'}.get(button, '1')
        self._x('click', '--repeat', str(count), '--delay', '90', b)

    def drag(self, x1, y1, x2, y2, duration=0.5):
        self.move(x1, y1)
        self._x('mousedown', '1')
        time.sleep(0.12)
        self.move(x2, y2)
        time.sleep(0.12)
        self._x('mouseup', '1')

    def scroll(self, x, y, dy=0, dx=0):
        if x is not None:
            self.move(x, y)
        for btn, n in (('5' if dy > 0 else '4', abs(dy)), ('7' if dx > 0 else '6', abs(dx))):
            if n:
                self._x('click', '--repeat', str(n), '--delay', '25', btn)

    def keys(self, keys):
        self._x('key', '--clearmodifiers', '+'.join(self._name(k) for k in keys))

    def key_down(self, key):
        self._x('keydown', self._name(key))

    def key_up(self, key):
        self._x('keyup', self._name(key))

    def type_ascii(self, text, interval):
        self._x('type', '--clearmodifiers', '--delay', str(max(1, int(interval * 1000))), '--', text)


class _PyAutoGuiBackend(_Backend):
    """macOS and Windows."""
    name = 'pyautogui'

    def __init__(self):
        try:
            import pyautogui
        except Exception as e:
            raise DesktopError(f'pyautogui unavailable: {e}') from e
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.02
        self._p = pyautogui

    @staticmethod
    def available() -> bool:
        return PLATFORM in ('Darwin', 'Windows')

    def _name(self, key: str) -> str:
        key = normalize_key(key)
        return {'return': 'enter', 'escape': 'esc', 'page_up': 'pageup', 'page_down': 'pagedown',
                'super': 'command' if PLATFORM == 'Darwin' else 'win', 'caps_lock': 'capslock',
                'print': 'printscreen', 'volume_up': 'volumeup', 'volume_down': 'volumedown',
                'volume_mute': 'volumemute'}.get(key, key)

    def size(self):
        s = self._p.size()
        return int(s.width), int(s.height)

    def capture(self):
        return self._p.screenshot().convert('RGB')

    def move(self, x, y, duration=0.15):
        self._p.moveTo(x, y, duration=duration)

    def click(self, x, y, button='left', count=1):
        self._p.click(x, y, button=button, clicks=count, interval=0.09)

    def drag(self, x1, y1, x2, y2, duration=0.5):
        self._p.moveTo(x1, y1, duration=0.15)
        self._p.dragTo(x2, y2, duration=duration, button='left')

    def scroll(self, x, y, dy=0, dx=0):
        if x is not None:
            self._p.moveTo(x, y)
        if dy:
            self._p.scroll(-dy * 3)
        if dx:
            self._p.hscroll(dx * 3)

    def keys(self, keys):
        self._p.hotkey(*[self._name(k) for k in keys])

    def key_down(self, key):
        self._p.keyDown(self._name(key))

    def key_up(self, key):
        self._p.keyUp(self._name(key))

    def type_ascii(self, text, interval):
        self._p.write(text, interval=interval)


# ══════════════════════════════════════════════════════════════════════════════
# ydotool helpers
# ══════════════════════════════════════════════════════════════════════════════

def ydotool_socket() -> Optional[str]:
    """Path of a ydotoold socket this user can write to, or None."""
    runtime = os.environ.get('XDG_RUNTIME_DIR') or f'/run/user/{os.getuid()}'
    for sock in (os.environ.get('YDOTOOL_SOCKET'), f'{runtime}/.ydotool_socket', '/tmp/.ydotool_socket'):
        if sock and os.path.exists(sock) and os.access(sock, os.W_OK):
            return sock
    return None


def ydotool_help() -> str:
    if not shutil.which('ydotool'):
        return 'ydotool is not installed:  sudo apt install ydotool'
    return ('ydotoold is not running for this user. Run once:\n'
            '  sudo usermod -aG input "$USER"            # permanent, from next login\n'
            '  sudo setfacl -m "u:$USER:rw" /dev/uinput  # works right now\n'
            '  systemctl --user reset-failed ydotool; systemctl --user enable --now ydotool')


# ══════════════════════════════════════════════════════════════════════════════
# Desktop — the public object
# ══════════════════════════════════════════════════════════════════════════════

def _tmp_dir() -> str:
    base = os.environ.get('XDG_RUNTIME_DIR') or '/tmp'
    d = os.path.join(base, 'devin')  # tmpfs: screenshots never touch the disk
    os.makedirs(d, exist_ok=True)
    return d


def _tmp_path(name: str) -> str:
    return os.path.join(_tmp_dir(), name)


class Desktop:
    """See the screen and operate the pointer and keyboard."""

    def __init__(self, backend: Optional[str] = None):
        self._b = self._pick(backend or os.environ.get('DEVIN_INPUT_BACKEND', ''))
        self._thumb = None
        atexit.register(self.close)

    @staticmethod
    def _pick(want: str) -> _Backend:
        want = want.strip().lower()
        table = {'gnome': _GnomeBackend, 'ydotool': _YdotoolBackend,
                 'xdotool': _XdotoolBackend, 'pyautogui': _PyAutoGuiBackend}
        if want:
            if want not in table:
                raise DesktopError(f'unknown backend {want!r} (choose: {", ".join(table)})')
            return table[want]()
        errors = []
        for name in ('gnome', 'xdotool', 'ydotool', 'pyautogui'):
            cls = table[name]
            try:
                if cls.available():
                    return cls()
            except DesktopError as e:
                errors.append(f'{name}: {e}')
        hint = ''
        if PLATFORM == 'Linux' and os.environ.get('WAYLAND_DISPLAY'):
            hint = '\n' + ydotool_help()
        raise DesktopError('no way to control this desktop was found.' +
                           ''.join(f'\n  {e}' for e in errors) + hint)

    @property
    def backend(self) -> str:
        return self._b.name

    def close(self) -> None:
        try:
            self._b.close()
        except Exception:
            pass

    # ── seeing ──
    def size(self) -> Tuple[int, int]:
        return self._b.size()

    def capture(self):
        """The screen right now, as an RGB PIL image."""
        return self._b.capture()

    def mark(self) -> None:
        """Remember the screen as it is now; the next settle() reports change against it.
        Every input method calls this itself — call it by hand only before non-input
        actions such as launching a program."""
        if self._b.native_settle:
            self._b.mark()
        else:
            try:
                self._thumb = self._gray_thumb()
            except DesktopError:
                self._thumb = None

    def _gray_thumb(self) -> bytes:
        return self.capture().convert('L').resize((192, 108)).tobytes()

    @staticmethod
    def _diff(a: bytes, b: bytes) -> float:
        return sum(1 for p, q in zip(a, b) if abs(p - q) > 8) / max(1, len(a))

    def settle(self, quiet: float = 0.5, timeout: float = 8.0, minimum: float = 0.12,
               expect: float = 1.2, min_change: float = 0.0002) -> Dict[str, Any]:
        """Wait for the last action to take effect and for the screen to stop moving.

        The action gets `expect` seconds to change something. Once the screen has
        changed, wait until it has been still for `quiet` seconds (a blinking caret
        or the clock does not count as movement). Never waits longer than `timeout`.
        `min_change` is how much of the screen must differ before it counts as an
        effect: the default catches a single typed word; use ~0.02 when waiting for
        a whole window to appear.

        Returns {'stable', 'changed', 'change', 'waited'}:
          changed=False  the action had no visible effect at all
          stable=False   still moving at the timeout (video, spinner, slow page)
          change         fraction of the screen that differs from before the action
        """
        if self._b.native_settle:
            return self._b.settle(quiet, timeout, minimum, expect, min_change)
        start = time.monotonic()
        time.sleep(minimum)
        base = self._thumb
        last = None
        last_move = start
        began = False
        while True:
            cur = self._gray_thumb()
            now = time.monotonic()
            if last is not None and self._diff(cur, last) >= 0.004:
                last_move = now
            total = self._diff(cur, base) if base else 0.0
            began = total >= max(min_change, 0.0005)
            last = cur
            waited = round(now - start, 2)
            if not began:
                if now - start >= expect:
                    return {'stable': True, 'changed': False, 'change': 0.0, 'waited': waited}
            elif now - last_move >= quiet:
                return {'stable': True, 'changed': True, 'change': round(total, 4), 'waited': waited}
            if now - start >= timeout:
                return {'stable': False, 'changed': began, 'change': round(total, 4), 'waited': waited}
            time.sleep(0.1)

    def elements(self, budget: float = 1.5, limit: int = 160) -> Dict[str, Any]:
        """Named, clickable things on screen from the accessibility tree (may be empty)."""
        return self._b.elements(budget, limit)

    def _premark(self) -> None:
        if not self._b.native_settle:  # the GNOME helper marks inside each input op
            self.mark()

    # ── pointer ──
    def _clamp(self, x: Any, y: Any) -> Tuple[int, int]:
        w, h = self.size()
        return max(0, min(int(round(float(x))), w - 1)), max(0, min(int(round(float(y))), h - 1))

    def move(self, x: Any, y: Any, duration: float = 0.2) -> None:
        self._b.move(*self._clamp(x, y), duration)

    def click(self, x: Any, y: Any, button: str = 'left', count: int = 1) -> None:
        self._premark()
        self._b.click(*self._clamp(x, y), button, max(1, int(count)))

    def drag(self, x1: Any, y1: Any, x2: Any, y2: Any, duration: float = 0.5) -> None:
        self._premark()
        self._b.drag(*self._clamp(x1, y1), *self._clamp(x2, y2), duration)

    def scroll(self, dy: int = 0, dx: int = 0, x: Any = None, y: Any = None) -> None:
        """Positive dy scrolls down, positive dx scrolls right (wheel notches)."""
        if x is not None and y is not None:
            x, y = self._clamp(x, y)
        else:
            x = y = None
        self._premark()
        self._b.scroll(x, y, int(dy), int(dx))

    # ── keyboard ──
    def key(self, combo: str) -> None:
        """Press a key or shortcut: 'enter', 'ctrl+l', 'ctrl+shift+t', 'alt+f4', 'a'."""
        keys = split_combo(combo)
        if not keys:
            raise DesktopError('empty key')
        self._premark()
        self._b.keys(keys)

    def key_down(self, key: str) -> None:
        self._b.key_down(normalize_key(key))

    def key_up(self, key: str) -> None:
        self._b.key_up(normalize_key(key))

    def type(self, text: str, interval: Optional[float] = None) -> None:
        """Type text into whatever has keyboard focus, one real key press per character,
        at the pace of a person typing (DEVIN_TYPE_INTERVAL seconds per key, default 0.045).
        A long text speeds up so that it never takes more than about eight seconds.

        Characters that are not on the keyboard layout (accents, CJK, emoji) are
        pasted through the clipboard instead, so nothing is silently dropped.
        """
        if interval is None:
            try:
                interval = float(os.environ.get('DEVIN_TYPE_INTERVAL', '0.045'))
            except ValueError:
                interval = 0.045
            interval = max(0.004, min(interval, 8.0 / max(1, len(str(text)))))
        self._premark()
        run = ''
        for ch in str(text):
            if ch in '\n\t' or 0x20 <= ord(ch) < 0x7F:
                run += ch
                continue
            if run:
                self._b.type_ascii(run, interval)
                run = ''
            self._paste(ch)
        if run:
            self._b.type_ascii(run, interval)

    def _paste(self, text: str) -> None:
        old = clipboard_get()
        clipboard_set(text)
        time.sleep(0.12)
        self._b.keys(['super' if PLATFORM == 'Darwin' else 'ctrl', 'v'])
        time.sleep(0.15)
        if old:
            clipboard_set(old)


_desktop: Optional[Desktop] = None
_desktop_lock = threading.Lock()


def get_desktop() -> Desktop:
    global _desktop
    with _desktop_lock:
        if _desktop is None:
            _desktop = Desktop()
        return _desktop


def reset_desktop() -> None:
    global _desktop
    with _desktop_lock:
        if _desktop is not None:
            _desktop.close()
        _desktop = None


# ══════════════════════════════════════════════════════════════════════════════
# Clipboard, applications, system helpers
# ══════════════════════════════════════════════════════════════════════════════

def clipboard_get() -> str:
    if PLATFORM == 'Darwin':
        return _run(['pbpaste'])[1]
    if PLATFORM == 'Windows':
        return _run(['powershell', '-NoProfile', '-Command', 'Get-Clipboard'])[1]
    for cmd in (['wl-paste', '--no-newline'], ['xclip', '-selection', 'clipboard', '-o'],
                ['xsel', '--clipboard', '--output']):
        if shutil.which(cmd[0]):
            code, out = _run(cmd, timeout=3)
            if code == 0:
                return out
    return ''


def clipboard_set(text: str) -> str:
    data = str(text).encode()
    if PLATFORM == 'Darwin':
        _run(['pbcopy'], input_bytes=data)
    elif PLATFORM == 'Windows':
        _run(['clip'], input_bytes=str(text).encode('utf-16le'))
    else:
        for cmd in (['wl-copy'], ['xclip', '-selection', 'clipboard', '-i'], ['xsel', '--clipboard', '--input']):
            if shutil.which(cmd[0]):
                # xclip stays alive to serve the selection; do not wait for it to exit
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL, start_new_session=True)
                try:
                    p.communicate(data, timeout=2)
                except subprocess.TimeoutExpired:
                    pass
                break
    return f'Clipboard set ({len(text)} chars)'


def launch(command: str) -> str:
    """Start a program detached from Devin. `command` is a shell command line.

    On systemd desktops the program becomes a transient user unit, exactly like an
    app started from the desktop itself — it outlives Devin and the terminal.
    """
    if PLATFORM == 'Linux' and shutil.which('systemd-run'):
        env = [f'--setenv={k}={os.environ[k]}' for k in
               ('PATH', 'DISPLAY', 'WAYLAND_DISPLAY', 'XAUTHORITY', 'XDG_CURRENT_DESKTOP',
                'XDG_SESSION_TYPE', 'LANG', 'HOME') if os.environ.get(k)]
        code, _ = _run(['systemd-run', '--user', '--collect', '--quiet', '--same-dir', *env,
                        '--', '/bin/sh', '-c', command], timeout=8)
        if code == 0:
            return f'started: {command}'
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                            start_new_session=True)
    return f'started pid {proc.pid}: {command}'


def installed_apps(query: str = '') -> List[Dict[str, str]]:
    """Desktop applications known to the system (from .desktop files)."""
    apps: Dict[str, Dict[str, str]] = {}
    dirs = [os.path.expanduser('~/.local/share/applications'), '/usr/local/share/applications',
            '/usr/share/applications', '/var/lib/flatpak/exports/share/applications',
            '/var/lib/snapd/desktop/applications']
    for d in dirs:
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        for fn in names:
            if not fn.endswith('.desktop'):
                continue
            entry: Dict[str, str] = {}
            try:
                with open(os.path.join(d, fn), encoding='utf-8', errors='replace') as f:
                    section = ''
                    for line in f:
                        line = line.strip()
                        if line.startswith('['):
                            section = line
                        elif section == '[Desktop Entry]' and '=' in line:
                            k, _, v = line.partition('=')
                            if k in ('Name', 'Exec', 'NoDisplay', 'Type', 'Keywords', 'GenericName'):
                                entry.setdefault(k, v)
            except OSError:
                continue
            if entry.get('Type', 'Application') != 'Application' or entry.get('NoDisplay') == 'true':
                continue
            if entry.get('Name') and entry.get('Exec'):
                exe = ' '.join(t for t in entry['Exec'].split() if not t.startswith('%'))
                apps.setdefault(entry['Name'].lower(), {
                    'name': entry['Name'], 'exec': exe, 'id': fn[:-8],
                    'keywords': (entry.get('Keywords', '') + ' ' + entry.get('GenericName', '')).lower()})
    result = list(apps.values())
    q = query.strip().lower()
    if q:
        def score(a):
            n = a['name'].lower()
            if n == q or a['id'].lower() == q:
                return 0
            if n.startswith(q):
                return 1
            if q in n or q in a['id'].lower():
                return 2
            if q in a['exec'].lower():
                return 3
            if q in a['keywords']:
                return 4
            return 9
        result = sorted((a for a in result if score(a) < 9), key=score)
    return result


def open_application(app_name: str, args: Optional[str] = None) -> str:
    """Launch an installed application by name ('chrome', 'files', 'text editor', a binary…)."""
    name = str(app_name).strip()
    if PLATFORM == 'Darwin':
        return launch(f'open -a "{name}"' + (f' --args {args}' if args else ''))
    if PLATFORM == 'Windows':
        return launch(f'start "" "{name}"' + (f' {args}' if args else ''))
    matches = installed_apps(name)
    if matches:
        return launch(matches[0]['exec'] + (f' {args}' if args else '')) + f'  ({matches[0]["name"]})'
    binary = name.split()[0] if name else ''
    if binary and shutil.which(binary):
        return launch(name + (f' {args}' if args else ''))
    return f'No installed application matches {name!r}'


def open_url_in_browser(url: str) -> str:
    try:
        webbrowser.open(url)
    except Exception:
        launch(f'xdg-open "{url}"')
    return f'Opened {url}'


def open_file(path: str) -> str:
    path = os.path.expanduser(str(path))
    if PLATFORM == 'Windows':
        os.startfile(path)  # type: ignore[attr-defined]
    else:
        launch(f'{"open" if PLATFORM == "Darwin" else "xdg-open"} "{path}"')
    return f'Opened {path}'


def open_terminal() -> str:
    for term in ('gnome-terminal', 'kgx', 'konsole', 'xfce4-terminal', 'alacritty', 'kitty', 'xterm'):
        if shutil.which(term):
            return launch(term)
    return open_application('Terminal')


def open_file_manager(path: Optional[str] = None) -> str:
    return open_file(path or '~')


def close_application(app_name: str) -> str:
    code, _ = _run(['pkill', '-f', str(app_name)])
    return f'Closed {app_name}' if code == 0 else f'No process matched {app_name}'


def get_system_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {'platform': PLATFORM, 'os': platform.platform()}
    try:
        import psutil
        m = psutil.virtual_memory()
        d = psutil.disk_usage('/' if PLATFORM != 'Windows' else 'C:\\')
        info.update(cpu_percent=psutil.cpu_percent(interval=0.3), cpu_count=psutil.cpu_count(),
                    ram_total_gb=round(m.total / 1e9, 1), ram_used_percent=m.percent,
                    disk_total_gb=round(d.total / 1e9, 1), disk_used_percent=d.percent)
    except Exception:
        pass
    return info


def get_running_processes(top_n: int = 20) -> str:
    code, out = _run(['ps', 'aux', '--sort=-%cpu'], timeout=5)
    return '\n'.join(out.splitlines()[:top_n + 1]) if code == 0 else ''


# ══════════════════════════════════════════════════════════════════════════════
# Function-style API (kept for the rest of the codebase)
# ══════════════════════════════════════════════════════════════════════════════

def take_screenshot(save_path: Optional[str] = None, region: Optional[Tuple[int, int, int, int]] = None,
                    as_base64: bool = False):
    """Capture the screen (or `region` = x, y, w, h). Returns the saved path, or base64 PNG."""
    img = get_desktop().capture()
    if region:
        x, y, w, h = (int(v) for v in region)
        img = img.crop((x, y, x + w, y + h))
    if as_base64:
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        return base64.b64encode(buf.getvalue()).decode()
    if save_path is None:
        save_path = _tmp_path(f'shot_{int(time.time() * 1000)}.png')
    img.save(save_path)
    return save_path


def get_screen_size() -> str:
    w, h = get_desktop().size()
    return f'{w}x{h}'


def mouse_move(x, y, duration: float = 0.2) -> str:
    get_desktop().move(x, y, duration)
    return f'Mouse moved to ({int(x)}, {int(y)})'


def mouse_click(x, y, button: str = 'left', double: bool = False, clicks: int = 1) -> str:
    get_desktop().click(x, y, button, 2 if double else clicks)
    return f'{"Double-clicked" if double else "Clicked"} {button} at ({int(x)}, {int(y)})'


def mouse_right_click(x, y) -> str:
    return mouse_click(x, y, button='right')


def mouse_drag(x1, y1, x2, y2, duration: float = 0.5, button: str = 'left') -> str:
    get_desktop().drag(x1, y1, x2, y2, duration)
    return f'Dragged from ({int(x1)},{int(y1)}) to ({int(x2)},{int(y2)})'


def mouse_scroll(x, y, direction: str = 'down', amount: int = 3) -> str:
    n = abs(int(amount))
    dy = n if direction == 'down' else -n if direction == 'up' else 0
    dx = n if direction == 'right' else -n if direction == 'left' else 0
    get_desktop().scroll(dy=dy, dx=dx, x=x, y=y)
    return f'Scrolled {direction} {n} at ({int(x)},{int(y)})'


def keyboard_type(text: str, interval: Optional[float] = None, human_like: bool = True) -> str:
    get_desktop().type(text, interval)
    return f'Typed {len(str(text))} chars'


def keyboard_press(key: str) -> str:
    get_desktop().key(key)
    return f'Pressed {key}'


def keyboard_hotkey(*keys: str) -> str:
    combo = '+'.join(keys)
    get_desktop().key(combo)
    return f'Pressed {combo}'


def keyboard_key_down(key: str) -> None:
    get_desktop().key_down(key)


def keyboard_key_up(key: str) -> None:
    get_desktop().key_up(key)


def human_click_and_type(x, y, text: str, clear_first: bool = True) -> str:
    d = get_desktop()
    d.click(x, y)
    d.settle(quiet=0.25, timeout=2)
    if clear_first:
        d.key('ctrl+a')
        time.sleep(0.05)
    d.type(text)
    return f'Clicked ({int(x)},{int(y)}) and typed {len(str(text))} chars'


def get_active_window() -> str:
    info = get_desktop().elements(budget=0.4, limit=1)
    title = info.get('window') or ''
    app = info.get('app') or ''
    return f'Active: {title or "(unknown)"}' + (f' [{app}]' if app else '')


def list_windows() -> str:
    if shutil.which('wmctrl') and not os.environ.get('WAYLAND_DISPLAY'):
        code, out = _run(['wmctrl', '-l'])
        if code == 0 and out:
            return out
    return get_active_window()


def focus_window(window_name: str) -> str:
    if not os.environ.get('WAYLAND_DISPLAY') and shutil.which('xdotool'):
        code, out = _run(['xdotool', 'search', '--onlyvisible', '--name', str(window_name)])
        if code == 0 and out:
            _run(['xdotool', 'windowactivate', '--sync', out.splitlines()[0]])
            return f'Focused {window_name}'
    return ('Wayland does not let programs raise windows by name — switch with the keyboard '
            '(alt+tab) or click the window, then check the screen.')


def maximize_window(window_name: Optional[str] = None) -> str:
    return keyboard_hotkey('super', 'up')


def minimize_window() -> str:
    return keyboard_hotkey('super', 'h')


def close_current_window() -> str:
    return keyboard_hotkey('alt', 'f4')


def alt_tab(times: int = 1) -> str:
    d = get_desktop()
    d.key_down('alt')
    try:
        for _ in range(max(1, int(times))):
            d.key('tab')
            time.sleep(0.15)
    finally:
        d.key_up('alt')
    return f'Alt-tabbed {times} time(s)'


def search_and_open(app_name: str) -> str:
    """Open an app the way a person does: launcher key, type the name, Enter."""
    d = get_desktop()
    d.key('super')
    d.settle(quiet=0.4, timeout=4)
    d.type(str(app_name))
    d.settle(quiet=0.5, timeout=4)
    d.key('enter')
    d.settle(quiet=0.6, timeout=10)
    return f'Opened {app_name} from the launcher'


def get_mouse_position() -> Dict[str, int]:
    if PLATFORM == 'Linux' and not os.environ.get('WAYLAND_DISPLAY') and shutil.which('xdotool'):
        code, out = _run(['xdotool', 'getmouselocation'])
        if code == 0:
            parts = dict(p.split(':') for p in out.split() if ':' in p)
            return {'x': int(parts.get('x', 0)), 'y': int(parts.get('y', 0))}
    return {'x': -1, 'y': -1}  # Wayland does not expose the pointer position


def copy_selected() -> str:
    keyboard_hotkey('ctrl', 'c')
    time.sleep(0.15)
    return clipboard_get()


def paste() -> str:
    return keyboard_hotkey('ctrl', 'v')


def show_desktop() -> str:
    return keyboard_hotkey('super', 'd')


def volume_up(steps: int = 5) -> str:
    for _ in range(steps):
        get_desktop().key('volume_up')
    return f'Volume raised by {steps}'


def volume_down(steps: int = 5) -> str:
    for _ in range(steps):
        get_desktop().key('volume_down')
    return f'Volume lowered by {steps}'


def volume_mute() -> str:
    get_desktop().key('volume_mute')
    return 'Volume mute toggled'


def power_state() -> Dict[str, Any]:
    """{'on_battery': bool, 'percent': int or None}. Laptops slow the CPU down on battery,
    and a local model thinks at CPU speed, so this is worth telling the user."""
    out: Dict[str, Any] = {'on_battery': False, 'percent': None}
    base = '/sys/class/power_supply'
    try:
        for name in sorted(os.listdir(base)):
            try:
                with open(os.path.join(base, name, 'type')) as f:
                    if f.read().strip() != 'Battery':
                        continue
                with open(os.path.join(base, name, 'status')) as f:
                    out['on_battery'] = f.read().strip() == 'Discharging'
                with open(os.path.join(base, name, 'capacity')) as f:
                    out['percent'] = int(f.read().strip())
                break
            except (OSError, ValueError):
                continue
    except OSError:
        pass
    return out


def status() -> Dict[str, Any]:
    """What this machine offers for desktop control — used by `devin --doctor`."""
    info: Dict[str, Any] = {
        'platform': PLATFORM,
        'session': os.environ.get('XDG_SESSION_TYPE', ''),
        'desktop': os.environ.get('XDG_CURRENT_DESKTOP', ''),
        'gnome_remote_desktop': _GnomeBackend.available(),
        'ydotool_installed': bool(shutil.which('ydotool')),
        'ydotool_socket': ydotool_socket(),
        'xdotool': _XdotoolBackend.available(),
    }
    try:
        d = get_desktop()
        info['backend'] = d.backend
        info['screen'] = '%dx%d' % d.size()
    except DesktopError as e:
        info['backend'] = None
        info['error'] = str(e)
    return info


ACTIONS = {
    'screenshot':     lambda a: take_screenshot(a.get('path'), a.get('region')),
    'screenshot_b64': lambda a: take_screenshot(as_base64=True),
    'screen_size':    lambda a: get_screen_size(),
    'mouse_move':     lambda a: mouse_move(a['x'], a['y'], a.get('duration', 0.2)),
    'mouse_click':    lambda a: mouse_click(a['x'], a['y'], a.get('button', 'left'), a.get('double', False)),
    'mouse_right_click': lambda a: mouse_right_click(a['x'], a['y']),
    'mouse_drag':     lambda a: mouse_drag(a['x1'], a['y1'], a['x2'], a['y2'], a.get('duration', 0.5)),
    'mouse_scroll':   lambda a: mouse_scroll(a['x'], a['y'], a.get('direction', 'down'), a.get('amount', 3)),
    'type':           lambda a: keyboard_type(a['text'], a.get('interval')),
    'hotkey':         lambda a: keyboard_hotkey(*a['keys']),
    'press':          lambda a: keyboard_press(a['key']),
    'click_and_type': lambda a: human_click_and_type(a['x'], a['y'], a['text'], a.get('clear', True)),
    'open_app':       lambda a: open_application(a['name'], a.get('args')),
    'open_url':       lambda a: open_url_in_browser(a['url']),
    'open_file':      lambda a: open_file(a['path']),
    'open_terminal':  lambda a: open_terminal(),
    'close_app':      lambda a: close_application(a['name']),
    'active_window':  lambda a: get_active_window(),
    'list_windows':   lambda a: list_windows(),
    'elements':       lambda a: get_desktop().elements(),
    'clipboard_get':  lambda a: clipboard_get(),
    'clipboard_set':  lambda a: clipboard_set(a['text']),
    'settle':         lambda a: get_desktop().settle(a.get('quiet', 0.5), a.get('timeout', 8)),
    'system_info':    lambda a: get_system_info(),
    'status':         lambda a: status(),
}


# One module object no matter which name it was imported under (one desktop session).
for _alias in ('os_automation', 'modules.os_automation'):
    sys.modules.setdefault(_alias, sys.modules[__name__])


if __name__ == '__main__':
    if '--gnome-helper' in sys.argv:
        sys.exit(_gnome_helper_main())
    if len(sys.argv) < 2:
        print(json.dumps({'ok': False, 'error': 'usage: os_automation.py \'{"action": "...", "args": {...}}\'',
                          'actions': sorted(ACTIONS)}))
        sys.exit(1)
    try:
        req = json.loads(sys.argv[1])
        fn = ACTIONS.get(req.get('action'))
        if fn is None:
            print(json.dumps({'ok': False, 'error': f'unknown action {req.get("action")!r}',
                              'actions': sorted(ACTIONS)}))
            sys.exit(1)
        print(json.dumps({'ok': True, 'result': fn(req.get('args') or {})}, default=str))
    except Exception as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}))
        sys.exit(1)
