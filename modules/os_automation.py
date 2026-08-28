"""
modules/os_automation.py — Real-user OS automation for Devin AGI
Cross-platform: Linux (xdotool + XDG portal), macOS (screencapture + osascript), Windows (pyautogui + PIL).
Runs as a subprocess server or called directly from tool executor.
"""

import os
import sys
import time
import json
import subprocess
import threading
import platform
import tempfile
import base64
import webbrowser
from pathlib import Path

PLATFORM = platform.system()  # 'Linux', 'Darwin', 'Windows'

# Only set DISPLAY on Linux (needed for X11/XWayland apps)
if PLATFORM == 'Linux':
    os.environ.setdefault('DISPLAY', ':0')

try:
    import pyautogui
    pyautogui.FAILSAFE = False  # disable move-to-corner failsafe
    pyautogui.PAUSE = 0.05
    HAS_PYAUTOGUI = True
except Exception:
    HAS_PYAUTOGUI = False

try:
    import pynput.mouse as pmouse
    import pynput.keyboard as pkeyboard
    HAS_PYNPUT = True
except Exception:
    HAS_PYNPUT = False

try:
    from PIL import Image, ImageGrab
    import io
    HAS_PIL = True
except Exception:
    HAS_PIL = False

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except Exception:
    HAS_CV2 = False

try:
    import mss
    import mss.tools
    HAS_MSS = True
except Exception:
    HAS_MSS = False

try:
    import pygetwindow as gw
    HAS_GW = True
except Exception:
    HAS_GW = False


# ── Helpers ──────────────────────────────────────────────────────────────────

def _xdotool(*args, capture=True):
    if PLATFORM != 'Linux':
        return '', 1
    r = subprocess.run(['xdotool'] + list(args),
                       capture_output=capture, text=True)
    return r.stdout.strip(), r.returncode

def _run(cmd, timeout=30):
    r = subprocess.run(cmd, shell=True, capture_output=True,
                       text=True, timeout=timeout)
    out = (r.stdout + r.stderr).strip()
    return out, r.returncode

def _screen_size():
    if HAS_PYAUTOGUI:
        s = pyautogui.size()
        return s.width, s.height
    if PLATFORM == 'Linux':
        out, _ = _xdotool('getdisplaygeometry')
        parts = out.split()
        if len(parts) >= 2:
            return int(parts[0]), int(parts[1])
    return 1920, 1080  # safe fallback


# ── Screenshot ───────────────────────────────────────────────────────────────

def _take_screenshot_portal(save_path):
    """Take screenshot via XDG Screenshot portal (dbus-fast). No dialog, no xdotool needed."""
    import asyncio, random, string, shutil as _shutil
    try:
        from dbus_fast.aio import MessageBus
        from dbus_fast import BusType, Variant
        from dbus_fast.message import Message
    except ImportError:
        return False

    async def _do():
        bus = await MessageBus(bus_type=BusType.SESSION).connect()
        token = 'devin' + ''.join(random.choices(string.ascii_lowercase, k=6))
        sender = bus.unique_name.replace('.', '_').lstrip(':')
        request_path = f'/org/freedesktop/portal/desktop/request/{sender}/{token}'

        done = asyncio.Event()
        result = {}

        def on_msg(msg):
            if getattr(msg, 'member', None) == 'Response' and getattr(msg, 'path', None) == request_path:
                result['code'] = msg.body[0] if msg.body else -1
                raw_uri = (msg.body[1] or {}).get('uri', '')
                # dbus_fast wraps values in Variant — extract the string
                result['uri'] = raw_uri.value if hasattr(raw_uri, 'value') else str(raw_uri)
                done.set()

        bus.add_message_handler(on_msg)
        await bus.call(Message(
            destination='org.freedesktop.DBus', path='/org/freedesktop/DBus',
            interface='org.freedesktop.DBus', member='AddMatch',
            signature='s',
            body=[f"type='signal',interface='org.freedesktop.portal.Request',path='{request_path}'"]
        ))

        introspect = await bus.introspect('org.freedesktop.portal.Desktop', '/org/freedesktop/portal/desktop')
        proxy = bus.get_proxy_object('org.freedesktop.portal.Desktop', '/org/freedesktop/portal/desktop', introspect)
        iface = proxy.get_interface('org.freedesktop.portal.Screenshot')
        await iface.call_screenshot('', {'interactive': Variant('b', False), 'handle_token': Variant('s', token)})

        try:
            await asyncio.wait_for(done.wait(), timeout=8.0)
        except asyncio.TimeoutError:
            bus.disconnect()
            return False

        bus.disconnect()
        uri = result.get('uri', '')
        if result.get('code') == 0 and uri.startswith('file://'):
            src = uri[7:]
            if os.path.exists(src) and os.path.getsize(src) > 1000:
                _shutil.copy2(src, save_path)
                try:
                    os.remove(src)  # delete GNOME's copy to save disk space
                except Exception:
                    pass
                return True
        return False

    try:
        return asyncio.run(_do())
    except Exception:
        return False


def take_screenshot(save_path=None, region=None, as_base64=False):
    """Capture full screen or region. Returns path or base64. Cross-platform."""
    if save_path is None:
        save_path = os.path.join(tempfile.gettempdir(), f'devin_shot_{int(time.time())}.png')

    def _file_ok(p):
        return p and os.path.exists(p) and os.path.getsize(p) > 10240

    if PLATFORM == 'Linux':
        # Primary: XDG Screenshot portal — works on GNOME Wayland, no dialog
        try:
            if _take_screenshot_portal(save_path) and _file_ok(save_path):
                pass
        except Exception:
            pass

        # Secondary: mss
        if not _file_ok(save_path) and HAS_MSS:
            try:
                with mss.MSS() as sct:
                    mon = {'left': int(region[0]), 'top': int(region[1]),
                           'width': int(region[2]), 'height': int(region[3])} if region else (
                        sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0])
                    shot = sct.grab(mon)
                    mss.tools.to_png(shot.rgb, shot.size, output=save_path)
            except Exception:
                pass

        # Tertiary: pyautogui
        if not _file_ok(save_path) and HAS_PYAUTOGUI:
            try:
                img = (pyautogui.screenshot(region=tuple(region)) if region else pyautogui.screenshot())
                img.save(save_path)
            except Exception:
                pass

        # Quaternary: scrot
        if not _file_ok(save_path):
            try:
                cmd = ['scrot', save_path]
                if region:
                    rx, ry, rw, rh = region
                    cmd = ['scrot', '-a', f'{int(rx)},{int(ry)},{int(rw)},{int(rh)}', save_path]
                subprocess.run(cmd, capture_output=True, env={**os.environ, 'DISPLAY': ':0'}, timeout=5)
            except Exception:
                pass

    elif PLATFORM == 'Darwin':
        # macOS: screencapture -x (silent, no shutter sound)
        if not _file_ok(save_path):
            try:
                cmd = ['screencapture', '-x', save_path]
                if region:
                    rx, ry, rw, rh = [int(v) for v in region]
                    cmd = ['screencapture', '-x', '-R', f'{rx},{ry},{rw},{rh}', save_path]
                subprocess.run(cmd, capture_output=True, timeout=10)
            except Exception:
                pass

        # Fallback: pyautogui / PIL
        if not _file_ok(save_path) and HAS_PYAUTOGUI:
            try:
                img = (pyautogui.screenshot(region=tuple(region)) if region else pyautogui.screenshot())
                img.save(save_path)
            except Exception:
                pass

        if not _file_ok(save_path) and HAS_PIL:
            try:
                img = ImageGrab.grab(bbox=tuple(region) if region else None)
                img.save(save_path)
            except Exception:
                pass

    else:  # Windows
        # PIL ImageGrab is the most reliable on Windows
        if HAS_PIL:
            try:
                bbox = (int(region[0]), int(region[1]),
                        int(region[0]) + int(region[2]),
                        int(region[1]) + int(region[3])) if region else None
                img = ImageGrab.grab(bbox=bbox)
                img.save(save_path)
            except Exception:
                pass

        if not _file_ok(save_path) and HAS_PYAUTOGUI:
            try:
                img = (pyautogui.screenshot(region=tuple(region)) if region else pyautogui.screenshot())
                img.save(save_path)
            except Exception:
                pass

        if not _file_ok(save_path) and HAS_MSS:
            try:
                with mss.MSS() as sct:
                    mon = {'left': int(region[0]), 'top': int(region[1]),
                           'width': int(region[2]), 'height': int(region[3])} if region else (
                        sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0])
                    shot = sct.grab(mon)
                    mss.tools.to_png(shot.rgb, shot.size, output=save_path)
            except Exception:
                pass

    if not _file_ok(save_path):
        return f"Screenshot failed on {PLATFORM} — tried all available methods"

    size = os.path.getsize(save_path)
    if as_base64:
        with open(save_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return f"{save_path} ({size // 1024}KB)"


# ── Mouse ────────────────────────────────────────────────────────────────────

def mouse_move(x, y, duration=0.2):
    """Move mouse to (x, y) with smooth movement."""
    if HAS_PYAUTOGUI:
        pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeInOutQuad)
    else:
        _xdotool('mousemove', '--sync', str(x), str(y))
    return f"Mouse moved to ({x}, {y})"

def mouse_click(x, y, button='left', double=False, clicks=1):
    """Click at (x, y). button: left/right/middle."""
    mouse_move(x, y, duration=0.15)
    time.sleep(0.05)
    if HAS_PYAUTOGUI:
        n = 2 if double else clicks
        pyautogui.click(x, y, button=button, clicks=n,
                        interval=0.1 if double else 0.0)
    else:
        btn_map = {'left': '1', 'middle': '2', 'right': '3'}
        b = btn_map.get(button, '1')
        if double:
            _xdotool('click', '--repeat', '2', b)
        else:
            _xdotool('click', b)
    action = "Double-clicked" if double else "Clicked"
    return f"{action} {button} at ({x}, {y})"

def mouse_right_click(x, y):
    return mouse_click(x, y, button='right')

def mouse_drag(x1, y1, x2, y2, duration=0.5, button='left'):
    """Drag from (x1,y1) to (x2,y2)."""
    if HAS_PYAUTOGUI:
        pyautogui.moveTo(x1, y1, duration=0.2)
        pyautogui.dragTo(x2, y2, duration=duration, button=button)
    else:
        _xdotool('mousemove', str(x1), str(y1))
        _xdotool('mousedown', '1')
        _xdotool('mousemove', '--sync', str(x2), str(y2))
        _xdotool('mouseup', '1')
    return f"Dragged from ({x1},{y1}) to ({x2},{y2})"

def mouse_scroll(x, y, direction='down', amount=3):
    """Scroll at position."""
    if HAS_PYAUTOGUI:
        pyautogui.moveTo(x, y)
        delta = -amount if direction == 'down' else amount
        pyautogui.scroll(delta)
    else:
        btn = '5' if direction == 'down' else '4'
        _xdotool('mousemove', str(x), str(y))
        for _ in range(amount):
            _xdotool('click', btn)
    return f"Scrolled {direction} {amount} times at ({x},{y})"

def get_mouse_position():
    if HAS_PYAUTOGUI:
        p = pyautogui.position()
        return {'x': p.x, 'y': p.y}
    out, _ = _xdotool('getmouselocation')
    parts = dict(p.split(':') for p in out.split())
    return {'x': int(parts.get('x', 0)), 'y': int(parts.get('y', 0))}


# ── Keyboard ─────────────────────────────────────────────────────────────────

def _type_via_clipboard(text):
    """Paste text via clipboard — handles unicode on all platforms."""
    old = None
    try:
        old = clipboard_get()
    except Exception:
        pass
    clipboard_set(text)
    time.sleep(0.05)
    if PLATFORM == 'Darwin':
        keyboard_hotkey('command', 'v')
    else:
        keyboard_hotkey('ctrl', 'v')
    time.sleep(0.05)
    if old is not None:
        try:
            clipboard_set(old)
        except Exception:
            pass

def keyboard_type(text, interval=0.03, human_like=True):
    """Type text. Uses write() for ASCII, clipboard paste for unicode."""
    if not text:
        return "Typed 0 chars"

    # Split into ASCII-safe and non-ASCII chunks
    ascii_safe = all(ord(c) < 128 for c in text)

    if HAS_PYAUTOGUI and ascii_safe:
        if human_like:
            import random
            # pyautogui.write() handles regular printable chars correctly
            for ch in text:
                try:
                    pyautogui.write(ch, interval=0)
                except Exception:
                    pass
                time.sleep(interval + random.uniform(0, 0.02))
        else:
            pyautogui.write(text, interval=interval)
    elif HAS_PYAUTOGUI:
        # Non-ASCII: use clipboard paste for reliability on all platforms
        _type_via_clipboard(text)
    else:
        _xdotool('type', '--clearmodifiers', '--delay', str(int(interval * 1000)), text)
    return f"Typed {len(text)} chars"

def keyboard_hotkey(*keys):
    """Press key combo e.g. ctrl+c, alt+tab, super+d."""
    key_list = list(keys)
    if HAS_PYAUTOGUI:
        pyautogui.hotkey(*key_list)
    else:
        combined = '+'.join(key_list)
        _xdotool('key', combined)
    return f"Pressed: {'+'.join(key_list)}"

def keyboard_press(key):
    """Press a single key."""
    if HAS_PYAUTOGUI:
        pyautogui.press(key)
    else:
        _xdotool('key', key)
    return f"Pressed key: {key}"

def keyboard_key_down(key):
    if HAS_PYAUTOGUI:
        pyautogui.keyDown(key)
    else:
        _xdotool('keydown', key)

def keyboard_key_up(key):
    if HAS_PYAUTOGUI:
        pyautogui.keyUp(key)
    else:
        _xdotool('keyup', key)

def type_in_terminal(text):
    """Focus terminal and type."""
    time.sleep(0.1)
    keyboard_type(text + '\n')


# ── Applications ──────────────────────────────────────────────────────────────

def open_application(app_name, args=None):
    """Open an application by name. Cross-platform."""
    if PLATFORM == 'Darwin':
        cmd = f'open -a "{app_name}"' + (f' --args {args}' if args else '')
    elif PLATFORM == 'Windows':
        cmd = f'start "" "{app_name}"' + (f' {args}' if args else '')
    else:
        cmd = app_name + (f' {args}' if args else '')
    proc = subprocess.Popen(cmd, shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True)
    time.sleep(1.5)
    return f"Opened {app_name} (pid={proc.pid})"

def open_url_in_browser(url):
    """Open URL in default browser. Cross-platform."""
    try:
        webbrowser.open(url)
        time.sleep(1)
        return f"Opened {url} in browser"
    except Exception:
        pass
    if PLATFORM == 'Linux':
        _run(f'xdg-open "{url}"')
    elif PLATFORM == 'Darwin':
        _run(f'open "{url}"')
    elif PLATFORM == 'Windows':
        _run(f'start "" "{url}"')
    time.sleep(1)
    return f"Opened {url} in browser"

def open_file(path):
    """Open a file with its default application. Cross-platform."""
    if PLATFORM == 'Windows':
        try:
            os.startfile(path)
            return f"Opened file: {path}"
        except Exception:
            pass
        _run(f'start "" "{path}"')
    elif PLATFORM == 'Darwin':
        _run(f'open "{path}"')
    else:
        _run(f'xdg-open "{path}"')
    time.sleep(1)
    return f"Opened file: {path}"

def open_terminal():
    """Open a terminal emulator. Cross-platform."""
    if PLATFORM == 'Darwin':
        try:
            subprocess.Popen(['open', '-a', 'Terminal'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            return "Opened Terminal (macOS)"
        except Exception:
            pass
        try:
            subprocess.Popen(['open', '-a', 'iTerm'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            return "Opened iTerm"
        except Exception:
            return "No terminal found on macOS"
    elif PLATFORM == 'Windows':
        for term in ['wt.exe', 'cmd.exe']:
            try:
                subprocess.Popen([term], creationflags=subprocess.CREATE_NEW_CONSOLE)
                time.sleep(1)
                return f"Opened {term}"
            except Exception:
                continue
        return "No terminal found on Windows"
    else:
        for term in ['gnome-terminal', 'xterm', 'konsole', 'xfce4-terminal', 'lxterminal', 'alacritty', 'kitty']:
            try:
                subprocess.Popen([term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
                return f"Opened {term}"
            except FileNotFoundError:
                continue
        return "No terminal emulator found"

def close_application(app_name):
    """Close application by name. Cross-platform."""
    if PLATFORM == 'Windows':
        _run(f'taskkill /F /IM "{app_name}.exe" 2>nul || taskkill /F /IM "{app_name}" 2>nul')
    elif PLATFORM == 'Darwin':
        _run(f'pkill -f "{app_name}" 2>/dev/null || osascript -e \'quit app "{app_name}"\'')
    else:
        _run(f'pkill -f "{app_name}"')
    return f"Closed {app_name}"


# ── Window Management ─────────────────────────────────────────────────────────

def list_windows():
    """List all open windows. Cross-platform (pygetwindow → platform fallbacks)."""
    if HAS_GW:
        try:
            titles = [t for t in gw.getAllTitles() if t.strip()]
            return '\n'.join(titles[:30]) if titles else "No windows found"
        except Exception:
            pass
    if PLATFORM == 'Linux':
        out, _ = _xdotool('search', '--onlyvisible', '--name', '.')
        if out:
            lines = []
            for wid in out.strip().split('\n')[:20]:
                name, _ = _xdotool('getwindowname', wid)
                if name:
                    lines.append(f"{wid}: {name}")
            return '\n'.join(lines) if lines else out
        out2, _ = _run('wmctrl -l 2>/dev/null')
        return out2 or "No windows found"
    elif PLATFORM == 'Darwin':
        out, _ = _run("osascript -e 'tell application \"System Events\" to get name of every process whose visible is true'")
        return out or "No windows found"
    elif PLATFORM == 'Windows':
        out, _ = _run('powershell -NoProfile -command "Get-Process | Where-Object {$_.MainWindowTitle -ne \'\'} | Select-Object -ExpandProperty MainWindowTitle"')
        return out or "No windows found"
    return "Window listing not supported on this platform"

def focus_window(window_name):
    """Focus window by partial name. Cross-platform (pygetwindow → platform fallbacks)."""
    if HAS_GW:
        try:
            matches = gw.getWindowsWithTitle(window_name)
            if not matches:
                # partial match
                all_wins = gw.getAllWindows()
                matches = [w for w in all_wins if window_name.lower() in (w.title or '').lower()]
            if matches:
                w = matches[0]
                w.restore()
                w.activate()
                return f"Focused: {w.title}"
        except Exception:
            pass
    if PLATFORM == 'Linux':
        out, code = _xdotool('search', '--onlyvisible', '--name', window_name)
        if code == 0 and out:
            wid = out.strip().split('\n')[0]
            _xdotool('windowfocus', '--sync', wid)
            _xdotool('windowactivate', '--sync', wid)
            return f"Focused: {window_name} (id={wid})"
        return f"Window not found: {window_name}"
    elif PLATFORM == 'Darwin':
        _run(f"osascript -e 'tell application \"{window_name}\" to activate' 2>/dev/null || true")
        return f"Focused: {window_name}"
    elif PLATFORM == 'Windows':
        # Use taskmgr-style focus: find process by window title and bring to front
        ps_cmd = (
            "Add-Type -Name W -Namespace A -Member "
            "'[DllImport(\"user32.dll\")]public static extern bool SetForegroundWindow(IntPtr h);';"
            "$p=Get-Process|Where-Object{$_.MainWindowTitle -like '*" + window_name + "*'}|"
            "Select-Object -First 1;"
            "if($p){[A.W]::SetForegroundWindow($p.MainWindowHandle)}"
        )
        _run('powershell -NoProfile -command "' + ps_cmd + '"')
        return f"Focused: {window_name}"
    return "Focus not supported on this platform"

def maximize_window(window_name=None):
    """Maximize window. Cross-platform."""
    if window_name:
        focus_window(window_name)
    if HAS_GW:
        try:
            w = gw.getActiveWindow()
            if w:
                w.maximize()
                return "Window maximized"
        except Exception:
            pass
    if PLATFORM == 'Windows':
        keyboard_hotkey('win', 'up')
    elif PLATFORM == 'Darwin':
        # macOS doesn't have a universal maximize shortcut; use green button simulation
        _run("osascript -e 'tell application \"System Events\" to keystroke \"f\" using {control down, command down}'")
    else:
        keyboard_hotkey('super', 'up')
    return "Window maximized"

def minimize_window():
    """Minimize active window. Cross-platform."""
    if HAS_GW:
        try:
            w = gw.getActiveWindow()
            if w:
                w.minimize()
                return "Window minimized"
        except Exception:
            pass
    if PLATFORM == 'Windows':
        keyboard_hotkey('win', 'down')
    elif PLATFORM == 'Darwin':
        keyboard_hotkey('command', 'm')
    else:
        keyboard_hotkey('super', 'down')
    return "Window minimized"

def switch_to_window(window_name):
    """Switch to a window by partial name match."""
    return focus_window(window_name)

def get_active_window():
    """Get currently active window title. Cross-platform."""
    if HAS_GW:
        try:
            w = gw.getActiveWindow()
            if w:
                return f"Active: {w.title}"
        except Exception:
            pass
    if PLATFORM == 'Linux':
        out, _ = _xdotool('getactivewindow')
        if out:
            name, _ = _xdotool('getwindowname', out.strip())
            return f"Active: {name} (id={out.strip()})"
        return "No active window"
    elif PLATFORM == 'Darwin':
        out, _ = _run("osascript -e 'tell application \"System Events\" to get name of first process whose frontmost is true'")
        return f"Active: {out}"
    elif PLATFORM == 'Windows':
        out, _ = _run('powershell -NoProfile -command "(Get-Process | Where-Object {$_.MainWindowTitle -ne \'\'} | Sort-Object StartTime -Descending | Select-Object -First 1 -ExpandProperty MainWindowTitle)"')
        return f"Active: {out}"
    return "Unknown active window"

def get_screen_size():
    w, h = _screen_size()
    return f"{w}x{h}"


# ── Screen Search (image matching) ────────────────────────────────────────────

def find_on_screen(image_path, confidence=0.8):
    """Find image on screen, return (x,y) center or None."""
    if HAS_PYAUTOGUI and HAS_CV2:
        try:
            loc = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if loc:
                return pyautogui.center(loc)
        except Exception:
            pass
    # Manual cv2 template matching
    if HAS_CV2:
        screenshot = take_screenshot()
        screen = cv2.imread(screenshot)
        template = cv2.imread(image_path)
        if screen is None or template is None:
            return None
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= confidence:
            h, w = template.shape[:2]
            cx = max_loc[0] + w // 2
            cy = max_loc[1] + h // 2
            return cx, cy
    return None

def click_image(image_path, confidence=0.8, double=False):
    """Find image on screen and click it."""
    loc = find_on_screen(image_path, confidence)
    if loc:
        x, y = loc
        return mouse_click(int(x), int(y), double=double)
    return f"Image not found on screen: {image_path}"

def wait_for_image(image_path, timeout=10, confidence=0.8):
    """Wait for image to appear on screen."""
    start = time.time()
    while time.time() - start < timeout:
        loc = find_on_screen(image_path, confidence)
        if loc:
            return f"Found at {loc}"
        time.sleep(0.5)
    return f"Timeout waiting for: {image_path}"


# ── Clipboard ─────────────────────────────────────────────────────────────────

def clipboard_get():
    """Get clipboard contents. Cross-platform."""
    if PLATFORM == 'Darwin':
        out, _ = _run('pbpaste')
        return out
    elif PLATFORM == 'Windows':
        try:
            import tkinter as _tk
            root = _tk.Tk()
            root.withdraw()
            data = root.clipboard_get()
            root.destroy()
            return data
        except Exception:
            pass
        out, _ = _run('powershell -command "Get-Clipboard"')
        return out
    else:
        out, _ = _run('xclip -selection clipboard -o 2>/dev/null || xsel --clipboard --output 2>/dev/null')
        return out

def clipboard_set(text):
    """Set clipboard contents. Cross-platform."""
    if PLATFORM == 'Darwin':
        p = subprocess.Popen('pbcopy', stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        p.communicate(text.encode())
    elif PLATFORM == 'Windows':
        try:
            import tkinter as _tk
            root = _tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
        except Exception:
            _run(f'powershell -command "Set-Clipboard -Value \'{text}\'"')
    else:
        p = subprocess.Popen('xclip -selection clipboard', shell=True,
                             stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        p.communicate(text.encode())
    return f"Clipboard set: {text[:50]}"

def copy_selected():
    keyboard_hotkey('ctrl', 'c')
    time.sleep(0.1)
    return clipboard_get()

def paste():
    keyboard_hotkey('ctrl', 'v')
    return "Pasted"


# ── Desktop Interaction ───────────────────────────────────────────────────────

def show_desktop():
    keyboard_hotkey('super', 'd')
    return "Desktop shown"

def lock_screen():
    """Lock the screen. Cross-platform."""
    if PLATFORM == 'Darwin':
        _run('pmset displaysleepnow 2>/dev/null || osascript -e \'tell application "System Events" to keystroke "q" using {command down, control down}\'')
    elif PLATFORM == 'Windows':
        _run('rundll32.exe user32.dll,LockWorkStation')
    else:
        _run('loginctl lock-session 2>/dev/null || xdg-screensaver lock 2>/dev/null || gnome-screensaver-command -l 2>/dev/null')
    return "Screen locked"

def _volume_set_windows(level):
    """Set Windows volume 0-100 using pycaw or nircmd."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(max(0.0, min(1.0, level / 100.0)), None)
        return True
    except Exception:
        pass
    try:
        subprocess.run(['nircmd.exe', 'setsysvolume', str(int(level / 100 * 65535))], capture_output=True)
        return True
    except Exception:
        return False

def volume_up(steps=5):
    """Raise volume. Cross-platform."""
    if PLATFORM == 'Windows':
        for _ in range(steps):
            keyboard_press('volumeup')
        return f"Volume raised by {steps}"
    elif PLATFORM == 'Darwin':
        for _ in range(steps):
            _run('osascript -e "set volume output volume ((output volume of (get volume settings)) + 6)"')
        return f"Volume raised by {steps}"
    else:
        for _ in range(steps):
            keyboard_press('XF86AudioRaiseVolume')
        _run('pactl set-sink-volume @DEFAULT_SINK@ +10% 2>/dev/null')
        return f"Volume raised by {steps}"

def volume_down(steps=5):
    """Lower volume. Cross-platform."""
    if PLATFORM == 'Windows':
        for _ in range(steps):
            keyboard_press('volumedown')
        return f"Volume lowered by {steps}"
    elif PLATFORM == 'Darwin':
        for _ in range(steps):
            _run('osascript -e "set volume output volume ((output volume of (get volume settings)) - 6)"')
        return f"Volume lowered by {steps}"
    else:
        for _ in range(steps):
            keyboard_press('XF86AudioLowerVolume')
        _run('pactl set-sink-volume @DEFAULT_SINK@ -10% 2>/dev/null')
        return f"Volume lowered by {steps}"

def volume_mute():
    """Toggle mute. Cross-platform."""
    if PLATFORM == 'Windows':
        keyboard_press('volumemute')
    elif PLATFORM == 'Darwin':
        _run('osascript -e "set volume with output muted"')
    else:
        keyboard_press('XF86AudioMute')
        _run('pactl set-sink-mute @DEFAULT_SINK@ toggle 2>/dev/null')
    return "Volume muted"

def volume_set(level):
    """Set volume to exact level 0-100. Cross-platform."""
    level = max(0, min(100, int(level)))
    if PLATFORM == 'Windows':
        if not _volume_set_windows(level):
            return f"Volume set failed (install pycaw or nircmd)"
    elif PLATFORM == 'Darwin':
        _run(f'osascript -e "set volume output volume {level}"')
    else:
        _run(f'pactl set-sink-volume @DEFAULT_SINK@ {level}% 2>/dev/null || amixer set Master {level}% 2>/dev/null')
    return f"Volume set to {level}%"


# ── System Info ──────────────────────────────────────────────────────────────

def get_system_info():
    """Return CPU, RAM, disk, OS info. Cross-platform."""
    info = {'platform': PLATFORM, 'os': platform.platform()}
    try:
        import psutil
        info['cpu_percent'] = psutil.cpu_percent(interval=0.5)
        info['cpu_count'] = psutil.cpu_count()
        m = psutil.virtual_memory()
        info['ram_total_gb'] = round(m.total / 1e9, 1)
        info['ram_used_percent'] = m.percent
        d = psutil.disk_usage('/' if PLATFORM != 'Windows' else 'C:\\')
        info['disk_total_gb'] = round(d.total / 1e9, 1)
        info['disk_used_percent'] = d.percent
    except ImportError:
        if PLATFORM == 'Windows':
            out, _ = _run('wmic cpu get loadpercentage /value')
            info['cpu_raw'] = out
        elif PLATFORM == 'Darwin':
            out, _ = _run('top -l 1 -n 0 | grep "CPU usage"')
            info['cpu_raw'] = out
        else:
            out, _ = _run('uptime')
            info['cpu_raw'] = out
    return info

def get_running_processes(top_n=20):
    """List top processes by CPU. Cross-platform."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append(p.info)
            except Exception:
                pass
        procs.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)
        lines = [f"PID={p['pid']} CPU={p.get('cpu_percent',0):.1f}% MEM={p.get('memory_percent',0):.1f}% {p['name']}"
                 for p in procs[:top_n]]
        return '\n'.join(lines)
    except ImportError:
        pass
    if PLATFORM == 'Windows':
        out, _ = _run('tasklist /FO TABLE /NH')
    elif PLATFORM == 'Darwin':
        out, _ = _run('ps aux -r | head -20')
    else:
        out, _ = _run('ps aux --sort=-%cpu | head -20')
    return out

def screenshot_all_monitors():
    """Capture all monitors and return list of file paths."""
    paths = []
    if HAS_MSS:
        try:
            with mss.MSS() as sct:
                for i, mon in enumerate(sct.monitors[1:], 1):  # skip monitors[0] (all-in-one)
                    p = os.path.join(tempfile.gettempdir(), f'devin_mon{i}_{int(time.time())}.png')
                    shot = sct.grab(mon)
                    mss.tools.to_png(shot.rgb, shot.size, output=p)
                    if os.path.exists(p) and os.path.getsize(p) > 1000:
                        paths.append(p)
        except Exception:
            pass
    if not paths:
        p = take_screenshot()
        if isinstance(p, str) and 'failed' not in p:
            paths.append(p.split(' ')[0])
    return paths


# ── Task Automation ───────────────────────────────────────────────────────────

def human_click_and_type(x, y, text, clear_first=True):
    """Click on field and type text, like a real user."""
    mouse_click(x, y)
    time.sleep(0.1)
    if clear_first:
        keyboard_hotkey('ctrl', 'a')
        time.sleep(0.05)
    keyboard_type(text, human_like=True)
    return f"Clicked ({x},{y}) and typed: {text[:40]}"

def run_shell_in_terminal(command):
    """Execute command (capturing output) AND show it visually in a terminal."""
    shell = 'cmd' if PLATFORM == 'Windows' else 'bash'
    shell_flag = '/c' if PLATFORM == 'Windows' else '-c'
    try:
        proc = subprocess.run(
            [shell, shell_flag, command],
            capture_output=True, text=True, timeout=30,
            env=os.environ.copy()
        )
        output = (proc.stdout + proc.stderr).strip()
        if not output:
            output = f"(exited with code {proc.returncode})"
    except subprocess.TimeoutExpired:
        output = f"Command timed out after 30s: {command}"
    except Exception as e:
        output = f"Error running command: {e}"

    # Also show in GUI terminal (visual effect, best-effort)
    try:
        open_terminal()
        time.sleep(1.2)
        keyboard_type(command)
        time.sleep(0.1)
        keyboard_press('Return')
        time.sleep(0.5)
    except Exception:
        pass

    return f"$ {command}\n{output}"

def search_and_open(app_name):
    """Use desktop search (Activities/launcher) to open an app."""
    keyboard_press('super')
    time.sleep(0.8)
    keyboard_type(app_name)
    time.sleep(1.0)
    keyboard_press('Return')
    time.sleep(1.5)
    return f"Searched and opened: {app_name}"

def alt_tab(times=1):
    """Switch windows with Alt+Tab."""
    keyboard_key_down('alt')
    for _ in range(times):
        keyboard_press('Tab')
        time.sleep(0.2)
    keyboard_key_up('alt')
    return f"Alt-tabbed {times} time(s)"

def close_current_window():
    keyboard_hotkey('alt', 'F4')
    return "Closed active window"


# ── Composite Real-User Actions ───────────────────────────────────────────────

def open_file_manager(path=None):
    """Open file manager at path. Cross-platform."""
    if PLATFORM == 'Darwin':
        cmd = f'open "{path}"' if path else 'open ~'
        _run(cmd)
        return f"Opened Finder: {path or '~'}"
    elif PLATFORM == 'Windows':
        target = f'"{path}"' if path else ''
        subprocess.Popen(f'explorer {target}', shell=True)
        time.sleep(1)
        return f"Opened Explorer: {path or 'Home'}"
    else:
        for fm in ['nautilus', 'thunar', 'nemo', 'dolphin', 'pcmanfm']:
            arg = f'"{path}"' if path else ''
            try:
                subprocess.Popen(f'{fm} {arg}', shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
                return f"Opened file manager: {fm} {arg}"
            except Exception:
                continue
        return "No file manager found"

def take_annotated_screenshot(annotation=None):
    """Take screenshot, optionally save with label."""
    path = take_screenshot()
    return {'path': path, 'annotation': annotation}

def full_browser_automation(url, actions=None):
    """Open browser, navigate, perform actions."""
    open_url_in_browser(url)
    time.sleep(2)
    results = [f"Opened: {url}"]
    if actions:
        for action in actions:
            atype = action.get('type')
            if atype == 'click':
                r = mouse_click(action['x'], action['y'])
            elif atype == 'type':
                r = keyboard_type(action['text'])
            elif atype == 'hotkey':
                r = keyboard_hotkey(*action['keys'])
            elif atype == 'wait':
                time.sleep(action.get('seconds', 1))
                r = f"Waited {action.get('seconds',1)}s"
            elif atype == 'screenshot':
                r = take_screenshot()
            else:
                r = f"Unknown action: {atype}"
            results.append(r)
    return '\n'.join(str(r) for r in results)


# ── Voice I/O (pyttsx3 + SpeechRecognition) ──────────────────────────────────

def speak(text, rate=180, volume=1.0):
    """Speak text using pyttsx3 TTS engine."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)
        engine.say(str(text))
        engine.runAndWait()
        engine.stop()
        return f"Spoke: {text[:60]}"
    except Exception as e:
        # Fallback: use espeak
        try:
            subprocess.run(['espeak', str(text)], capture_output=True, timeout=10)
            return f"Spoke via espeak: {text[:60]}"
        except Exception:
            return f"TTS failed: {e}"

def listen(timeout=5, phrase_time_limit=15, language='en-US'):
    """Listen for voice input and return transcribed text."""
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        r.energy_threshold = 300
        r.dynamic_energy_threshold = True
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            except sr.WaitTimeoutError:
                return "No speech detected (timeout)"
        try:
            text = r.recognize_google(audio, language=language)
            return text
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            # Try local whisper if available
            try:
                import whisper
                import tempfile, soundfile
                tmp = tempfile.mktemp(suffix='.wav')
                with open(tmp, 'wb') as f:
                    f.write(audio.get_wav_data())
                model = whisper.load_model('tiny')
                result = model.transcribe(tmp)
                os.remove(tmp)
                return result['text'].strip()
            except Exception:
                return f"Speech recognition error: {e}"
    except Exception as e:
        return f"Listen failed: {e}"


# ── CLI dispatch ──────────────────────────────────────────────────────────────

ACTIONS = {
    'screenshot':       lambda a: take_screenshot(a.get('path'), a.get('region')),
    'screenshot_b64':   lambda a: take_screenshot(as_base64=True),
    'mouse_move':       lambda a: mouse_move(a['x'], a['y'], a.get('duration', 0.2)),
    'mouse_click':      lambda a: mouse_click(a['x'], a['y'], a.get('button','left'), a.get('double', False)),
    'mouse_right_click':lambda a: mouse_right_click(a['x'], a['y']),
    'mouse_drag':       lambda a: mouse_drag(a['x1'],a['y1'],a['x2'],a['y2'],a.get('duration',0.5)),
    'mouse_scroll':     lambda a: mouse_scroll(a['x'],a['y'],a.get('direction','down'),a.get('amount',3)),
    'mouse_position':   lambda a: get_mouse_position(),
    'type':             lambda a: keyboard_type(a['text'], a.get('interval', 0.03), a.get('human_like', True)),
    'hotkey':           lambda a: keyboard_hotkey(*a['keys']),
    'press':            lambda a: keyboard_press(a['key']),
    'open_app':         lambda a: open_application(a['name'], a.get('args')),
    'open_url':         lambda a: open_url_in_browser(a['url']),
    'open_file':        lambda a: open_file(a['path']),
    'open_terminal':    lambda a: open_terminal(),
    'close_app':        lambda a: close_application(a['name']),
    'list_windows':     lambda a: list_windows(),
    'focus_window':     lambda a: focus_window(a['name']),
    'active_window':    lambda a: get_active_window(),
    'maximize':         lambda a: maximize_window(a.get('name')),
    'minimize':         lambda a: minimize_window(),
    'alt_tab':          lambda a: alt_tab(a.get('times', 1)),
    'close_window':     lambda a: close_current_window(),
    'screen_size':      lambda a: get_screen_size(),
    'clipboard_get':    lambda a: clipboard_get(),
    'clipboard_set':    lambda a: clipboard_set(a['text']),
    'copy':             lambda a: copy_selected(),
    'paste':            lambda a: paste(),
    'click_and_type':   lambda a: human_click_and_type(a['x'], a['y'], a['text'], a.get('clear', True)),
    'search_open':      lambda a: search_and_open(a['name']),
    'show_desktop':     lambda a: show_desktop(),
    'find_on_screen':   lambda a: str(find_on_screen(a['image'], a.get('confidence', 0.8))),
    'click_image':      lambda a: click_image(a['image'], a.get('confidence', 0.8), a.get('double', False)),
    'wait_for_image':   lambda a: wait_for_image(a['image'], a.get('timeout', 10)),
    'run_in_terminal':  lambda a: run_shell_in_terminal(a['command']),
    'browser_auto':     lambda a: full_browser_automation(a['url'], a.get('actions')),
    'volume_up':        lambda a: volume_up(a.get('steps', 5)),
    'volume_down':      lambda a: volume_down(a.get('steps', 5)),
    'volume_mute':      lambda a: volume_mute(),
    'volume_set':       lambda a: volume_set(a['level']),
    'open_file_manager':lambda a: open_file_manager(a.get('path')),
    'speak':            lambda a: speak(a['text'], a.get('rate', 180), a.get('volume', 1.0)),
    'listen':           lambda a: listen(a.get('timeout', 5), a.get('phrase_limit', 15)),
    'system_info':      lambda a: get_system_info(),
    'processes':        lambda a: get_running_processes(a.get('top', 20)),
    'screenshot_all':   lambda a: screenshot_all_monitors(),
    'type_unicode':     lambda a: (_type_via_clipboard(a['text']), f"Pasted {len(a['text'])} chars")[1],
}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: os_automation.py <json_action>'}))
        sys.exit(1)
    try:
        req = json.loads(sys.argv[1])
        action = req.get('action')
        args = req.get('args', {})
        if action not in ACTIONS:
            print(json.dumps({'error': f'Unknown action: {action}', 'available': list(ACTIONS.keys())}))
            sys.exit(1)
        result = ACTIONS[action](args)
        print(json.dumps({'ok': True, 'result': result}))
    except Exception as e:
        print(json.dumps({'ok': False, 'error': str(e)}))
        sys.exit(1)
