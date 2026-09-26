"""
os_controller.py — Full OS control module for Devin.
Provides comprehensive keyboard, mouse, window, app, and clipboard control.
Works cross-platform: Linux (X11/Wayland), macOS, Windows.
Uses pyautogui (primary), pynput (fallback), xdotool (Linux), AppleScript (macOS).
"""
from __future__ import annotations

import os
import sys
import json
import subprocess
import platform
import time
from typing import Optional, Tuple, List

_PLATFORM = platform.system()
_IS_LINUX  = _PLATFORM == 'Linux'
_IS_MAC    = _PLATFORM == 'Darwin'
_IS_WIN    = _PLATFORM == 'Windows'
_HAS_DISPLAY = bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
                     or _IS_MAC or _IS_WIN)


# ── pyautogui wrapper ─────────────────────────────────────────────────────────

_pag = None
try:
    import pyautogui as _pag
    _pag.FAILSAFE = True
    _pag.PAUSE = 0.05
except Exception:
    _pag = None


# ── pynput wrapper ────────────────────────────────────────────────────────────

_kb_ctrl = None
_mouse_ctrl = None
try:
    from pynput.keyboard import Controller as _KbCtrl, Key as _Key
    from pynput.mouse import Controller as _MouseCtrl, Button as _Button
    _kb_ctrl = _KbCtrl()
    _mouse_ctrl = _MouseCtrl()
except Exception:
    pass


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_display() -> Optional[str]:
    if not _HAS_DISPLAY:
        return 'ERROR: No display available. GUI operations require a display.'
    return None


def _require_pag() -> Optional[str]:
    if _pag is None:
        return 'ERROR: pyautogui not installed. Run: pip install pyautogui pillow'
    return None


# ── Mouse control ─────────────────────────────────────────────────────────────

def tool_mouse_move(x: int, y: int, duration: float = 0.2) -> str:
    e = _require_display()
    if e: return e
    e = _require_pag()
    if e: return e
    _pag.moveTo(x, y, duration=duration)
    return f'Mouse moved to ({x}, {y})'


def tool_mouse_click(x: int = -1, y: int = -1, button: str = 'left',
                      clicks: int = 1, interval: float = 0.05) -> str:
    e = _require_display()
    if e: return e
    e = _require_pag()
    if e: return e
    btn = {'left': 'left', 'right': 'right', 'middle': 'middle'}.get(button.lower(), 'left')
    if x >= 0 and y >= 0:
        _pag.click(x, y, button=btn, clicks=clicks, interval=interval)
    else:
        _pag.click(button=btn, clicks=clicks, interval=interval)
    return f'Clicked {btn} button {clicks}× at ({x}, {y})'


def tool_mouse_double_click(x: int = -1, y: int = -1) -> str:
    return tool_mouse_click(x, y, 'left', 2)


def tool_mouse_right_click(x: int = -1, y: int = -1) -> str:
    return tool_mouse_click(x, y, 'right', 1)


def tool_mouse_drag(from_x: int, from_y: int, to_x: int, to_y: int,
                     duration: float = 0.5) -> str:
    e = _require_display()
    if e: return e
    e = _require_pag()
    if e: return e
    _pag.drag(from_x, from_y, to_x, to_y, duration=duration, button='left')
    return f'Dragged from ({from_x},{from_y}) to ({to_x},{to_y})'


def tool_mouse_scroll(x: int, y: int, amount: int = 3, direction: str = 'down') -> str:
    e = _require_display()
    if e: return e
    e = _require_pag()
    if e: return e
    clicks = -amount if direction.lower() == 'down' else amount
    _pag.scroll(clicks, x=x, y=y)
    return f'Scrolled {direction} {abs(amount)}× at ({x},{y})'


def tool_get_mouse_position() -> str:
    e = _require_display()
    if e: return e
    if _pag:
        x, y = _pag.position()
    elif _mouse_ctrl:
        pos = _mouse_ctrl.position
        x, y = int(pos[0]), int(pos[1])
    else:
        return 'ERROR: No mouse controller available'
    return f'Mouse position: ({x}, {y})'


# ── Keyboard control ──────────────────────────────────────────────────────────

def tool_keyboard_type(text: str, interval: float = 0.02) -> str:
    e = _require_display()
    if e: return e
    if _pag:
        _pag.typewrite(text, interval=interval)
    elif _kb_ctrl:
        _kb_ctrl.type(text)
    else:
        return 'ERROR: No keyboard controller available'
    return f'Typed: {text[:80]}'


def tool_keyboard_press(key: str) -> str:
    """Press a special key: enter, tab, escape, space, backspace, delete,
    ctrl+c, ctrl+v, ctrl+a, ctrl+z, ctrl+s, win, f1-f12, arrows, etc."""
    e = _require_display()
    if e: return e
    key_lower = key.lower().strip()
    if _pag:
        # Handle combos like ctrl+c
        if '+' in key_lower:
            parts = [p.strip() for p in key_lower.split('+')]
            _pag.hotkey(*parts)
        else:
            _pag.press(key_lower)
    elif _kb_ctrl:
        from pynput.keyboard import Key as PKey
        key_map = {
            'enter': PKey.enter, 'tab': PKey.tab, 'escape': PKey.esc,
            'backspace': PKey.backspace, 'delete': PKey.delete,
            'space': PKey.space, 'up': PKey.up, 'down': PKey.down,
            'left': PKey.left, 'right': PKey.right, 'home': PKey.home,
            'end': PKey.end, 'pageup': PKey.page_up, 'pagedown': PKey.page_down,
        }
        if key_lower in key_map:
            _kb_ctrl.press(key_map[key_lower])
            _kb_ctrl.release(key_map[key_lower])
        else:
            _kb_ctrl.type(key)
    else:
        # Fallback: xdotool on Linux
        if _IS_LINUX:
            result = subprocess.run(['xdotool', 'key', key_lower],
                                     capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return f'ERROR: {result.stderr}'
        else:
            return 'ERROR: No keyboard controller available'
    return f'Pressed key: {key}'


def tool_keyboard_hotkey(*keys: str) -> str:
    """Press a keyboard combination, e.g. ctrl+c, alt+f4, ctrl+shift+i."""
    e = _require_display()
    if e: return e
    combo = '+'.join(keys) if len(keys) > 1 else (keys[0] if keys else '')
    return tool_keyboard_press(combo)


# ── Screenshot ────────────────────────────────────────────────────────────────

def tool_screenshot(save_path: str = '', analyze: bool = False) -> str:
    e = _require_display()
    if e: return e
    e = _require_pag()
    if e: return e
    try:
        img = _pag.screenshot()
        if not save_path:
            import tempfile
            fd, save_path = tempfile.mkstemp(suffix='.png', prefix='devin_shot_')
            os.close(fd)
        img.save(save_path)
        w, h = img.size
        result = f'Screenshot saved: {save_path}  ({w}×{h})'
        if analyze:
            result += '\n' + _analyze_screenshot(save_path)
        return result
    except Exception as ex:
        return f'ERROR taking screenshot: {ex}'


def _analyze_screenshot(path: str) -> str:
    """Analyze screenshot using PIL to get basic info."""
    try:
        from PIL import Image
        img = Image.open(path)
        pixels = list(img.getdata())
        # Brightness-based summary
        if img.mode == 'RGB':
            avg = sum(sum(px) / 3 for px in pixels) / len(pixels)
            theme = 'dark' if avg < 128 else 'light'
        else:
            theme = 'unknown'
        return f'Theme: {theme}  Mode: {img.mode}  Size: {img.width}×{img.height}'
    except Exception:
        return ''


# ── Clipboard ─────────────────────────────────────────────────────────────────

def tool_clipboard_get() -> str:
    """Get current clipboard text."""
    if _pag:
        try:
            import pyperclip
            return pyperclip.paste() or '(clipboard empty)'
        except ImportError:
            pass
    # xclip / xsel on Linux
    if _IS_LINUX:
        for cmd in [['xclip', '-o', '-sel', 'clip'], ['xsel', '--clipboard', '--output']]:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    return r.stdout or '(clipboard empty)'
            except Exception:
                continue
    # pbpaste on macOS
    if _IS_MAC:
        try:
            r = subprocess.run(['pbpaste'], capture_output=True, text=True, timeout=5)
            return r.stdout or '(clipboard empty)'
        except Exception:
            pass
    return 'ERROR: No clipboard tool available. Install pyperclip: pip install pyperclip'


def tool_clipboard_set(text: str) -> str:
    """Set clipboard text."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return f'Clipboard set: {text[:80]}'
    except ImportError:
        pass
    if _IS_LINUX:
        for cmd in ['xclip', 'xsel']:
            try:
                args = [cmd, '-i', '-sel', 'clip'] if cmd == 'xclip' else [cmd, '--clipboard', '--input']
                subprocess.run(args, input=text, text=True, timeout=5)
                return f'Clipboard set via {cmd}'
            except Exception:
                continue
    if _IS_MAC:
        try:
            subprocess.run(['pbcopy'], input=text, text=True, timeout=5)
            return 'Clipboard set via pbcopy'
        except Exception:
            pass
    return 'ERROR: Cannot set clipboard. Install pyperclip: pip install pyperclip'


# ── Window management ─────────────────────────────────────────────────────────

def tool_get_active_window() -> str:
    """Get info about the currently active window."""
    if _IS_LINUX:
        try:
            wid = subprocess.run(['xdotool', 'getactivewindow'],
                                  capture_output=True, text=True, timeout=5)
            if wid.returncode == 0:
                name = subprocess.run(['xdotool', 'getwindowname', wid.stdout.strip()],
                                       capture_output=True, text=True, timeout=5)
                return f'Active window: {name.stdout.strip()} (id={wid.stdout.strip()})'
        except Exception:
            pass
    if _IS_MAC:
        try:
            r = subprocess.run(
                ['osascript', '-e', 'tell application "System Events" to get name of first process whose frontmost is true'],
                capture_output=True, text=True, timeout=5)
            return f'Active window: {r.stdout.strip()}'
        except Exception:
            pass
    return 'ERROR: Cannot get active window. Install xdotool on Linux.'


def tool_list_windows() -> str:
    """List all open windows."""
    if _IS_LINUX:
        try:
            r = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return r.stdout.strip() or 'No windows found'
        except Exception:
            pass
        try:
            r = subprocess.run(['xdotool', 'search', '--name', ''],
                                capture_output=True, text=True, timeout=5)
            return r.stdout.strip()[:2000] or 'No windows found'
        except Exception:
            pass
    if _IS_MAC:
        try:
            script = 'tell application "System Events" to get name of every window of every process whose visible is true'
            r = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
            return r.stdout.strip()[:2000]
        except Exception:
            pass
    return 'ERROR: Window listing unavailable. Install wmctrl or xdotool.'


def tool_focus_window(window_name: str) -> str:
    """Bring a window to the foreground by title substring."""
    if _IS_LINUX:
        try:
            r = subprocess.run(['wmctrl', '-a', window_name], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return f'Focused window: {window_name}'
        except Exception:
            pass
    if _IS_MAC:
        try:
            script = f'tell application "{window_name}" to activate'
            r = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=5)
            return f'Focused: {window_name}'
        except Exception:
            pass
    return f'ERROR: Cannot focus window "{window_name}"'


# ── Application launcher ──────────────────────────────────────────────────────

def tool_launch_app(app: str, args: str = '') -> str:
    """Launch an application by name or path."""
    if _IS_MAC:
        cmd = ['open', '-a', app]
        if args:
            cmd += ['--args'] + args.split()
    elif _IS_WIN:
        cmd = ['start', '', app] + (args.split() if args else [])
    else:
        # Linux: try direct exec, then xdg-open
        import shutil
        if shutil.which(app):
            cmd = [app] + (args.split() if args else [])
        else:
            cmd = ['xdg-open', app]

    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f'Launched: {app}'
    except Exception as ex:
        return f'ERROR launching {app}: {ex}'


# ── Screen resolution / info ──────────────────────────────────────────────────

def tool_screen_info() -> str:
    """Return screen resolution and info."""
    if _pag:
        w, h = _pag.size()
        x, y = _pag.position()
        return f'Screen: {w}×{h}  Cursor: ({x},{y})'
    if _IS_LINUX:
        try:
            r = subprocess.run(['xrandr', '--current'], capture_output=True, text=True, timeout=5)
            lines = [ln for ln in r.stdout.splitlines() if ' connected' in ln]
            return '\n'.join(lines[:5]) or 'xrandr: no connected displays'
        except Exception:
            pass
    return 'ERROR: Screen info unavailable'


# ── Convenience: find and click on-screen text ───────────────────────────────

def tool_click_on_text(text: str, confidence: float = 0.8) -> str:
    """Find text on screen using OCR and click it (requires pytesseract + Pillow)."""
    e = _require_display()
    if e: return e
    try:
        import pytesseract
        from PIL import ImageGrab
    except ImportError:
        return 'ERROR: Requires: pip install pytesseract Pillow  +  apt install tesseract-ocr'
    try:
        img = ImageGrab.grab()
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        for i, word in enumerate(data['text']):
            if text.lower() in word.lower() and int(data['conf'][i]) > 50:
                x = data['left'][i] + data['width'][i] // 2
                y = data['top'][i] + data['height'][i] // 2
                if _pag:
                    _pag.click(x, y)
                    return f'Clicked on "{word}" at ({x},{y})'
        return f'Text not found on screen: {text!r}'
    except Exception as ex:
        return f'ERROR: {ex}'


# ── Module exports ────────────────────────────────────────────────────────────

OS_TOOLS = {
    'mouse_move':        tool_mouse_move,
    'mouse_click':       tool_mouse_click,
    'mouse_double_click': tool_mouse_double_click,
    'mouse_right_click': tool_mouse_right_click,
    'mouse_drag':        tool_mouse_drag,
    'mouse_scroll':      tool_mouse_scroll,
    'get_mouse_pos':     tool_get_mouse_position,
    'keyboard_type':     tool_keyboard_type,
    'keyboard_press':    tool_keyboard_press,
    'keyboard_hotkey':   tool_keyboard_hotkey,
    'screenshot':        tool_screenshot,
    'clipboard_get':     tool_clipboard_get,
    'clipboard_set':     tool_clipboard_set,
    'get_active_window': tool_get_active_window,
    'list_windows':      tool_list_windows,
    'focus_window':      tool_focus_window,
    'launch_app':        tool_launch_app,
    'screen_info':       tool_screen_info,
    'click_on_text':     tool_click_on_text,
}
