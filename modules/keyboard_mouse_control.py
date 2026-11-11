# Devin/modules/keyboard_mouse_control.py
# Purpose: A functional, low-level interface for controlling and monitoring
#          keyboard and mouse peripherals.
#
# Backend selection (auto-detected at init):
#   Wayland + ydotoold running → ydotool (kernel uinput, works for all Wayland apps)
#   Otherwise                  → pynput _xorg (works for X11 / XWayland apps)

import logging
import os
import subprocess
import time
from typing import Tuple, Optional

try:
    from pynput import mouse as _mouse, keyboard as _keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    _mouse = None
    _keyboard = None

logger = logging.getLogger("PeripheralController")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)
logger.propagate = False

# ydotool key-name map (ydotool uses Linux key names)
_YDOTOOL_KEY_MAP = {
    'enter': 'enter', 'return': 'enter',
    'esc': 'esc', 'escape': 'esc',
    'shift': 'shift', 'ctrl': 'ctrl', 'alt': 'alt',
    'tab': 'tab', 'backspace': 'backspace', 'delete': 'delete',
    'space': 'space', 'up': 'up', 'down': 'down',
    'left': 'left', 'right': 'right',
    'home': 'home', 'end': 'end',
    'page_up': 'pageup', 'page_down': 'pagedown',
    'insert': 'insert', 'caps_lock': 'capslock',
    'super': 'super', 'cmd': 'super',
    'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4',
    'f5': 'f5', 'f6': 'f6', 'f7': 'f7', 'f8': 'f8',
    'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
}


def _ydotool_available() -> Optional[str]:
    """Return the ydotool socket path if ydotoold is running and accessible."""
    # Check common socket locations
    for sock in [
        os.environ.get('YDOTOOL_SOCKET', ''),
        '/tmp/.ydotool_socket',
        f'/run/user/{os.getuid()}/.ydotool_socket',
    ]:
        if sock and os.path.exists(sock):
            try:
                os.access(sock, os.W_OK)
                # Quick sanity test
                r = subprocess.run(
                    ['ydotool', 'type', '--next-delay', '1', ''],
                    env={**os.environ, 'YDOTOOL_SOCKET': sock},
                    capture_output=True, timeout=2,
                )
                if r.returncode == 0:
                    return sock
            except Exception:
                pass
    return None


class KeyboardMouseController:
    """
    Unified keyboard+mouse controller.
    On GNOME Wayland with ydotoold running: uses ydotool (kernel uinput).
    Otherwise falls back to pynput (X11/XWayland).
    Mouse always uses pynput (cursor position is Wayland-global).
    """

    def __init__(self):
        if not PYNPUT_AVAILABLE:
            raise ImportError("pynput is required: pip install pynput")
        self._mc = _mouse.Controller()
        self._kc = _keyboard.Controller()

        # Detect Wayland + ydotool
        self._ydotool_socket = _ydotool_available()
        self._use_ydotool = bool(self._ydotool_socket)
        if self._use_ydotool:
            logger.info(f"Keyboard backend: ydotool (socket={self._ydotool_socket})")
        else:
            logger.info("Keyboard backend: pynput _xorg")

        # pynput key map (used as fallback)
        self._key_map = {
            'enter': _keyboard.Key.enter, 'return': _keyboard.Key.enter,
            'esc': _keyboard.Key.esc, 'escape': _keyboard.Key.esc,
            'shift': _keyboard.Key.shift, 'ctrl': _keyboard.Key.ctrl,
            'alt': _keyboard.Key.alt, 'tab': _keyboard.Key.tab,
            'backspace': _keyboard.Key.backspace, 'delete': _keyboard.Key.delete,
            'space': _keyboard.Key.space, 'up': _keyboard.Key.up,
            'down': _keyboard.Key.down, 'left': _keyboard.Key.left,
            'right': _keyboard.Key.right, 'home': _keyboard.Key.home,
            'end': _keyboard.Key.end, 'page_up': _keyboard.Key.page_up,
            'page_down': _keyboard.Key.page_down, 'insert': _keyboard.Key.insert,
            'print_screen': _keyboard.Key.print_screen, 'caps_lock': _keyboard.Key.caps_lock,
            'cmd': _keyboard.Key.cmd, 'super': _keyboard.Key.cmd,
            'f1': _keyboard.Key.f1, 'f2': _keyboard.Key.f2, 'f3': _keyboard.Key.f3,
            'f4': _keyboard.Key.f4, 'f5': _keyboard.Key.f5, 'f6': _keyboard.Key.f6,
            'f7': _keyboard.Key.f7, 'f8': _keyboard.Key.f8, 'f9': _keyboard.Key.f9,
            'f10': _keyboard.Key.f10, 'f11': _keyboard.Key.f11, 'f12': _keyboard.Key.f12,
        }

    # ── Internal ydotool helpers ───────────────────────────────────────────────

    def _yd(self, *args):
        """Run a ydotool command with the detected socket."""
        env = {**os.environ, 'YDOTOOL_SOCKET': self._ydotool_socket}
        return subprocess.run(['ydotool'] + list(args), env=env, capture_output=True)

    # ── Mouse ─────────────────────────────────────────────────────────────────

    def get_mouse_position(self) -> Tuple[int, int]:
        return self._mc.position

    def move_to(self, x: int, y: int):
        self._mc.position = (x, y)

    def move_relative(self, dx: int, dy: int):
        self._mc.move(dx, dy)

    def click(self, button: str = 'left', count: int = 1):
        btn = getattr(_mouse.Button, button, _mouse.Button.left)
        self._mc.click(btn, count)

    def press_mouse(self, button: str = 'left'):
        btn = getattr(_mouse.Button, button, _mouse.Button.left)
        self._mc.press(btn)

    def release_mouse(self, button: str = 'left'):
        btn = getattr(_mouse.Button, button, _mouse.Button.left)
        self._mc.release(btn)

    def scroll(self, dx: int = 0, dy: int = -3):
        self._mc.scroll(dx, dy)

    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.3):
        self.move_to(x1, y1)
        self.press_mouse('left')
        steps = max(10, int(duration * 60))
        for i in range(1, steps + 1):
            nx = x1 + int((x2 - x1) * i / steps)
            ny = y1 + int((y2 - y1) * i / steps)
            self.move_to(nx, ny)
            time.sleep(duration / steps)
        self.release_mouse('left')

    # ── Keyboard ──────────────────────────────────────────────────────────────

    def _resolve_key(self, key: str):
        return self._key_map.get(key.lower(), key)

    def _yd_key_name(self, key: str) -> str:
        return _YDOTOOL_KEY_MAP.get(key.lower(), key.lower())

    def press_key(self, key: str):
        if self._use_ydotool:
            self._yd('key', '--key-delay', '10', f'{self._yd_key_name(key)}:1')
        else:
            self._kc.press(self._resolve_key(key))

    def release_key(self, key: str):
        if self._use_ydotool:
            self._yd('key', '--key-delay', '10', f'{self._yd_key_name(key)}:0')
        else:
            self._kc.release(self._resolve_key(key))

    def tap(self, key: str):
        """Press and release a key (single keystroke)."""
        if self._use_ydotool:
            self._yd('key', '--key-delay', '50', self._yd_key_name(key))
        else:
            k = self._resolve_key(key)
            self._kc.press(k)
            self._kc.release(k)

    def type_text(self, text: str, interval: float = 0.0):
        """Type a string of text character by character."""
        if self._use_ydotool:
            delay_ms = max(1, int(interval * 1000)) if interval else 50
            self._yd('type', '--next-delay', str(delay_ms), '--', text)
        else:
            if interval:
                for ch in text:
                    self._kc.type(ch)
                    time.sleep(interval)
            else:
                self._kc.type(text)

    def hotkey(self, *keys: str):
        """Press a keyboard shortcut (e.g. ctrl+c)."""
        if self._use_ydotool:
            # ydotool key accepts space-separated key names for combos
            combo = '+'.join(self._yd_key_name(k) for k in keys)
            self._yd('key', '--key-delay', '50', combo)
        else:
            resolved = [self._resolve_key(k) for k in keys]
            for k in resolved:
                self._kc.press(k)
            for k in reversed(resolved):
                self._kc.release(k)
