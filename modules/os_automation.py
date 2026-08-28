"""
modules/os_automation.py — Real-user OS automation for Devin AGI
Combines pyautogui + xdotool + Xlib + pynput for full OS control.
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
from pathlib import Path

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


# ── Helpers ──────────────────────────────────────────────────────────────────

def _xdotool(*args, capture=True):
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
    out, _ = _xdotool('getdisplaygeometry')
    parts = out.split()
    return int(parts[0]), int(parts[1])


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
    """Capture full screen or region. Returns path or base64.
    Primary: XDG Screenshot portal via D-Bus (no dialog, no xdotool).
    Fallback: mss, pyautogui, scrot.
    """
    import shutil as _shutil
    import glob as _glob
    if save_path is None:
        save_path = tempfile.mktemp(suffix='.png', prefix='devin_shot_')

    def _file_ok(p):
        return p and os.path.exists(p) and os.path.getsize(p) > 10240

    # Primary: XDG Screenshot portal — works on GNOME Wayland, no dialog
    try:
        if _take_screenshot_portal(save_path) and _file_ok(save_path):
            pass  # success, fall through to return
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
            env = {**os.environ, 'DISPLAY': ':0'}
            cmd = ['scrot', save_path]
            if region:
                rx, ry, rw, rh = region
                cmd = ['scrot', '-a', f'{int(rx)},{int(ry)},{int(rw)},{int(rh)}', save_path]
            subprocess.run(cmd, capture_output=True, env=env, timeout=5)
        except Exception:
            pass

    if not _file_ok(save_path):
        return f"Screenshot failed — tried GNOME PrintScreen, mss, pyautogui, scrot"

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

def keyboard_type(text, interval=0.03, human_like=True):
    """Type text with human-like timing."""
    if HAS_PYAUTOGUI:
        if human_like:
            import random
            for ch in text:
                pyautogui.press(ch)
                time.sleep(interval + random.uniform(0, 0.02))
        else:
            pyautogui.typewrite(text, interval=interval)
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
    """Open an application by name."""
    cmd = app_name
    if args:
        cmd = f"{app_name} {args}"
    proc = subprocess.Popen(cmd, shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True)
    time.sleep(1.5)
    return f"Opened {app_name} (pid={proc.pid})"

def open_url_in_browser(url):
    """Open URL in default browser."""
    r, _ = _run(f'xdg-open "{url}"')
    time.sleep(1)
    return f"Opened {url} in browser"

def open_file(path):
    """Open a file with its default application."""
    r, _ = _run(f'xdg-open "{path}"')
    time.sleep(1)
    return f"Opened file: {path}"

def open_terminal():
    """Open a terminal emulator."""
    for term in ['gnome-terminal', 'xterm', 'konsole', 'xfce4-terminal', 'lxterminal']:
        try:
            subprocess.Popen([term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            return f"Opened {term}"
        except FileNotFoundError:
            continue
    return "No terminal emulator found"

def close_application(app_name):
    """Close application by name."""
    out, _ = _run(f'pkill -f "{app_name}"')
    return f"Closed {app_name}"


# ── Window Management ─────────────────────────────────────────────────────────

def list_windows():
    """List all open windows."""
    out, _ = _xdotool('search', '--onlyvisible', '--name', '.')
    if not out:
        # Alternative: wmctrl
        out2, _ = _run('wmctrl -l 2>/dev/null || xdotool search --onlyvisible --name "" 2>/dev/null')
        return out2
    # Get titles for each window id
    lines = []
    for wid in out.strip().split('\n')[:20]:
        name, _ = _xdotool('getwindowname', wid)
        if name:
            lines.append(f"{wid}: {name}")
    return '\n'.join(lines) if lines else out

def focus_window(window_name):
    """Focus window by name."""
    out, code = _xdotool('search', '--onlyvisible', '--name', window_name)
    if code == 0 and out:
        wid = out.strip().split('\n')[0]
        _xdotool('windowfocus', '--sync', wid)
        _xdotool('windowactivate', '--sync', wid)
        return f"Focused window: {window_name} (id={wid})"
    return f"Window not found: {window_name}"

def maximize_window(window_name=None):
    """Maximize current or named window."""
    if window_name:
        focus_window(window_name)
    keyboard_hotkey('super', 'Up')
    return "Window maximized"

def minimize_window():
    """Minimize active window."""
    keyboard_hotkey('super', 'Down')
    return "Window minimized"

def switch_to_window(window_name):
    """Switch to a window by partial name match."""
    return focus_window(window_name)

def get_active_window():
    """Get currently active window title."""
    out, _ = _xdotool('getactivewindow')
    if out:
        name, _ = _xdotool('getwindowname', out.strip())
        return f"Active: {name} (id={out.strip()})"
    return "No active window"

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
    out, _ = _run('xclip -selection clipboard -o 2>/dev/null || xsel --clipboard --output 2>/dev/null')
    return out

def clipboard_set(text):
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
    _run('xdg-screensaver lock 2>/dev/null || loginctl lock-session 2>/dev/null || gnome-screensaver-command -l 2>/dev/null')
    return "Screen locked"

def volume_up(steps=5):
    for _ in range(steps):
        keyboard_press('XF86AudioRaiseVolume')
    return f"Volume raised by {steps}"

def volume_down(steps=5):
    for _ in range(steps):
        keyboard_press('XF86AudioLowerVolume')
    return f"Volume lowered by {steps}"

def volume_mute():
    keyboard_press('XF86AudioMute')
    return "Volume muted"


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
    # Always capture actual output so Devin gets results back
    try:
        proc = subprocess.run(
            ['bash', '-c', command],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, 'DISPLAY': ':0'}
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
    cmd = f'nautilus "{path}"' if path else 'nautilus'
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
    'open_file_manager':lambda a: open_file_manager(a.get('path')),
    'speak':            lambda a: speak(a['text'], a.get('rate', 180), a.get('volume', 1.0)),
    'listen':           lambda a: listen(a.get('timeout', 5), a.get('phrase_limit', 15)),
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
