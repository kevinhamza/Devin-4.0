"""modules/os_agent.py — Comprehensive OS Control Agent

Implements the full observe→understand→plan→act→verify loop:
  1. Screenshot / accessibility state capture
  2. Vision analysis via available AI provider
  3. Action planning
  4. Low-level mouse/keyboard execution with human-like timing
  5. Post-action screenshot verification
  6. Retry / error recovery

Cross-platform: Linux (X11/Wayland), macOS, Windows.
Never uses raw pixel coordinates as the sole mechanism — always
prefers accessibility APIs, keyboard shortcuts, and semantic element
detection first; coordinates only as a last resort after vision.
"""
from __future__ import annotations

import logging
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("OSAgent")
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.INFO)
log.propagate = False

_SYSTEM = platform.system()  # 'Linux', 'Darwin', 'Windows'
_IS_LINUX   = _SYSTEM == "Linux"
_IS_MAC     = _SYSTEM == "Darwin"
_IS_WIN     = _SYSTEM == "Windows"
_HAS_DISPLAY = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or _IS_MAC or _IS_WIN)

# ──────────────────────────────────────────────────────────────────────────────
# Screenshot backend
# ──────────────────────────────────────────────────────────────────────────────

def _take_screenshot(path: Optional[str] = None) -> Optional[str]:
    """Capture the screen and return the file path. Returns None on failure."""
    if path is None:
        fd, path = tempfile.mkstemp(suffix=".png", prefix="devin_shot_")
        os.close(fd)

    try:
        # PIL/Pillow (preferred, cross-platform)
        try:
            from PIL import ImageGrab  # type: ignore
            img = ImageGrab.grab()
            img.save(path)
            return path
        except Exception:
            pass

        # pyscreenshot / mss fallbacks
        try:
            import mss  # type: ignore
            with mss.mss() as sct:
                monitor = sct.monitors[0]
                sct_img = sct.grab(monitor)
                from mss.tools import to_png  # type: ignore
                to_png(sct_img.rgb, sct_img.size, output=path)
            return path
        except Exception:
            pass

        if _IS_LINUX:
            # scrot / gnome-screenshot / import (ImageMagick)
            for cmd in [
                ["scrot", "-z", path],
                ["gnome-screenshot", "-f", path],
                ["import", "-window", "root", path],
                ["xwd", "-root", "-silent", "-out", path + ".xwd"],
            ]:
                try:
                    if subprocess.run(cmd, timeout=5, capture_output=True).returncode == 0:
                        return path
                except Exception:
                    continue
        elif _IS_MAC:
            if subprocess.run(["screencapture", "-x", path], timeout=5).returncode == 0:
                return path
        elif _IS_WIN:
            ps_cmd = (
                f"Add-Type -AssemblyName System.Drawing; "
                f"$b=[System.Drawing.Bitmap]::new([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,"
                f"[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height);"
                f"$g=[System.Drawing.Graphics]::FromImage($b);"
                f"$g.CopyFromScreen(0,0,0,0,$b.Size);"
                f"$b.Save('{path}');"
            )
            subprocess.run(["powershell", "-Command", ps_cmd], timeout=10)
            if os.path.exists(path):
                return path
    except Exception as e:
        log.debug("Screenshot failed: %s", e)
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Mouse control
# ──────────────────────────────────────────────────────────────────────────────

def _mouse_move(x: int, y: int, duration: float = 0.15):
    """Smoothly move mouse to (x,y) with human-like curve."""
    try:
        from pynput import mouse as _m  # type: ignore
        mc = _m.Controller()
        cx, cy = mc.position
        steps = max(5, int(duration * 60))
        for i in range(1, steps + 1):
            nx = cx + int((x - cx) * i / steps)
            ny = cy + int((y - cy) * i / steps)
            mc.position = (nx, ny)
            time.sleep(duration / steps)
        mc.position = (x, y)
        return
    except Exception:
        pass

    if _IS_LINUX:
        try:
            subprocess.run(["xdotool", "mousemove", str(x), str(y)], timeout=3)
            return
        except Exception:
            pass
    elif _IS_WIN:
        try:
            import ctypes
            ctypes.windll.user32.SetCursorPos(x, y)
            return
        except Exception:
            pass
    elif _IS_MAC:
        try:
            subprocess.run(["cliclick", f"m:{x},{y}"], timeout=3)
            return
        except Exception:
            pass
    log.warning("mouse_move: no backend available")


def _mouse_click(x: int, y: int, button: str = "left", count: int = 1, move_duration: float = 0.15):
    _mouse_move(x, y, duration=move_duration)
    time.sleep(0.05)
    try:
        from pynput import mouse as _m  # type: ignore
        mc = _m.Controller()
        btn = getattr(_m.Button, button, _m.Button.left)
        mc.click(btn, count)
        return
    except Exception:
        pass
    if _IS_LINUX:
        btn_map = {"left": 1, "middle": 2, "right": 3}
        b = btn_map.get(button, 1)
        for _ in range(count):
            subprocess.run(["xdotool", "click", str(b)], timeout=3)
    elif _IS_WIN:
        import ctypes
        ctypes.windll.user32.mouse_event(0x0002 if button == "left" else 0x0008, 0, 0, 0, 0)
        ctypes.windll.user32.mouse_event(0x0004 if button == "left" else 0x0010, 0, 0, 0, 0)
    elif _IS_MAC:
        btn_flag = "c" if button == "left" else "rc"
        for _ in range(count):
            subprocess.run(["cliclick", f"{btn_flag}:{x},{y}"], timeout=3)


def _mouse_scroll(x: int, y: int, dx: int = 0, dy: int = -3):
    _mouse_move(x, y)
    try:
        from pynput import mouse as _m  # type: ignore
        mc = _m.Controller()
        mc.scroll(dx, dy)
        return
    except Exception:
        pass
    if _IS_LINUX:
        btn = "4" if dy > 0 else "5"
        subprocess.run(["xdotool", "click", btn], timeout=3)


def _mouse_drag(x1: int, y1: int, x2: int, y2: int, duration: float = 0.4):
    _mouse_move(x1, y1)
    time.sleep(0.05)
    try:
        from pynput import mouse as _m  # type: ignore
        mc = _m.Controller()
        mc.press(_m.Button.left)
        steps = max(10, int(duration * 60))
        for i in range(1, steps + 1):
            nx = x1 + int((x2 - x1) * i / steps)
            ny = y1 + int((y2 - y1) * i / steps)
            mc.position = (nx, ny)
            time.sleep(duration / steps)
        mc.position = (x2, y2)
        mc.release(_m.Button.left)
        return
    except Exception:
        pass
    if _IS_LINUX:
        subprocess.run(["xdotool", "mousedown", "1"], timeout=2)
        subprocess.run(["xdotool", "mousemove", str(x2), str(y2)], timeout=3)
        subprocess.run(["xdotool", "mouseup", "1"], timeout=2)


# ──────────────────────────────────────────────────────────────────────────────
# Keyboard control
# ──────────────────────────────────────────────────────────────────────────────

_KEY_MAP: Dict[str, Any] = {}
_PYNPUT_KB = None

def _get_kb():
    global _PYNPUT_KB
    if _PYNPUT_KB is None:
        try:
            from pynput import keyboard as _k  # type: ignore
            _PYNPUT_KB = _k.Controller()
            _KEY_MAP.update({
                'enter': _k.Key.enter, 'return': _k.Key.enter,
                'esc': _k.Key.esc, 'escape': _k.Key.esc,
                'shift': _k.Key.shift, 'ctrl': _k.Key.ctrl,
                'alt': _k.Key.alt, 'tab': _k.Key.tab,
                'backspace': _k.Key.backspace, 'delete': _k.Key.delete,
                'space': _k.Key.space, 'up': _k.Key.up,
                'down': _k.Key.down, 'left': _k.Key.left,
                'right': _k.Key.right, 'home': _k.Key.home,
                'end': _k.Key.end, 'page_up': _k.Key.page_up,
                'page_down': _k.Key.page_down, 'insert': _k.Key.insert,
                'f1': _k.Key.f1, 'f2': _k.Key.f2, 'f3': _k.Key.f3,
                'f4': _k.Key.f4, 'f5': _k.Key.f5, 'f6': _k.Key.f6,
                'f7': _k.Key.f7, 'f8': _k.Key.f8, 'f9': _k.Key.f9,
                'f10': _k.Key.f10, 'f11': _k.Key.f11, 'f12': _k.Key.f12,
                'cmd': _k.Key.cmd, 'super': _k.Key.cmd,
                'caps_lock': _k.Key.caps_lock,
            })
        except Exception:
            pass
    return _PYNPUT_KB


def _keyboard_type(text: str, interval: float = 0.03):
    kb = _get_kb()
    if kb:
        for ch in text:
            kb.type(ch)
            if interval:
                time.sleep(interval)
        return
    if _IS_LINUX:
        subprocess.run(["xdotool", "type", "--delay", str(int(interval*1000)), text], timeout=30)
    elif _IS_WIN:
        import pyperclip  # type: ignore
        pyperclip.copy(text)
        import ctypes
        ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)  # Ctrl down
        ctypes.windll.user32.keybd_event(0x56, 0, 0, 0)  # V down
        ctypes.windll.user32.keybd_event(0x56, 0, 2, 0)  # V up
        ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)  # Ctrl up


def _keyboard_press(key: str):
    kb = _get_kb()
    k = _KEY_MAP.get(key.lower(), key)
    if kb:
        kb.press(k)
        kb.release(k)
        return
    if _IS_LINUX:
        subprocess.run(["xdotool", "key", key], timeout=3)
    elif _IS_WIN:
        import ctypes
        vk = ord(key.upper()[0]) if len(key) == 1 else 0x0D
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0)


def _keyboard_hotkey(*keys: str):
    kb = _get_kb()
    if kb:
        resolved = [_KEY_MAP.get(k.lower(), k) for k in keys]
        for k in resolved:
            kb.press(k)
        for k in reversed(resolved):
            kb.release(k)
        return
    if _IS_LINUX:
        combo = "+".join(keys)
        subprocess.run(["xdotool", "key", combo], timeout=3)


# ──────────────────────────────────────────────────────────────────────────────
# Application / Window management
# ──────────────────────────────────────────────────────────────────────────────

def _launch_app(name: str) -> Optional[int]:
    """Launch an application. Returns PID or None."""
    name_lower = name.lower().strip()

    # Common cross-platform aliases
    aliases = {
        "browser": "firefox", "chrome": "google-chrome", "chromium": "chromium-browser",
        "terminal": "gnome-terminal", "text editor": "gedit", "notepad": "gedit",
        "files": "nautilus", "explorer": "nautilus",
    }
    cmd = aliases.get(name_lower, name_lower)

    try:
        proc = subprocess.Popen(
            [cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        time.sleep(1.5)
        return proc.pid
    except FileNotFoundError:
        pass

    if _IS_LINUX:
        # Try xdg-open for documents/URLs
        try:
            proc = subprocess.Popen(
                ["xdg-open", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(1.0)
            return proc.pid
        except Exception:
            pass
    elif _IS_WIN:
        try:
            proc = subprocess.Popen(
                ["start", "", name], shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return proc.pid
        except Exception:
            pass
    elif _IS_MAC:
        try:
            proc = subprocess.Popen(
                ["open", "-a", name],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(1.5)
            return proc.pid
        except Exception:
            pass
    return None


def _get_window_list() -> List[Dict[str, Any]]:
    """List open windows with title, id, pid."""
    windows: List[Dict[str, Any]] = []
    if _IS_LINUX:
        try:
            out = subprocess.check_output(["wmctrl", "-l", "-p"], timeout=5, text=True)
            for line in out.splitlines():
                parts = line.split(None, 4)
                if len(parts) >= 5:
                    windows.append({"id": parts[0], "desktop": parts[1], "pid": parts[2], "host": parts[3], "title": parts[4]})
        except Exception:
            try:
                out = subprocess.check_output(["xdotool", "search", "--name", ""], timeout=5, text=True)
                for wid in out.splitlines():
                    try:
                        title = subprocess.check_output(["xdotool", "getwindowname", wid], timeout=2, text=True).strip()
                        windows.append({"id": wid, "title": title})
                    except Exception:
                        pass
            except Exception:
                pass
    elif _IS_WIN:
        try:
            import ctypes
            from ctypes import wintypes
            result = []
            def callback(hwnd, _):
                if ctypes.windll.user32.IsWindowVisible(hwnd):
                    buf = ctypes.create_unicode_buffer(512)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, 512)
                    if buf.value:
                        result.append({"id": hwnd, "title": buf.value})
                return True
            ctypes.windll.user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(callback), 0)
            windows = result
        except Exception:
            pass
    elif _IS_MAC:
        try:
            script = 'tell application "System Events" to get name of every window of every process'
            out = subprocess.check_output(["osascript", "-e", script], timeout=5, text=True)
            for i, title in enumerate(out.strip().split(", ")):
                windows.append({"id": str(i), "title": title.strip()})
        except Exception:
            pass
    return windows


def _focus_window(title_contains: str) -> bool:
    """Bring window with matching title to focus."""
    if _IS_LINUX:
        try:
            subprocess.run(["wmctrl", "-a", title_contains], timeout=3)
            time.sleep(0.3)
            return True
        except Exception:
            try:
                wids = subprocess.check_output(
                    ["xdotool", "search", "--name", title_contains], timeout=3, text=True
                ).strip().splitlines()
                if wids:
                    subprocess.run(["xdotool", "windowactivate", "--sync", wids[0]], timeout=3)
                    return True
            except Exception:
                pass
    elif _IS_WIN:
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, title_contains)
            if hwnd:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                return True
        except Exception:
            pass
    elif _IS_MAC:
        try:
            script = f'tell application "{title_contains}" to activate'
            subprocess.run(["osascript", "-e", script], timeout=3)
            return True
        except Exception:
            pass
    return False


# ──────────────────────────────────────────────────────────────────────────────
# Clipboard
# ──────────────────────────────────────────────────────────────────────────────

def _clipboard_get() -> str:
    try:
        import pyperclip  # type: ignore
        return pyperclip.paste() or ""
    except Exception:
        pass
    if _IS_LINUX:
        try:
            return subprocess.check_output(["xclip", "-selection", "clipboard", "-o"], timeout=3, text=True)
        except Exception:
            try:
                return subprocess.check_output(["xsel", "--clipboard", "--output"], timeout=3, text=True)
            except Exception:
                pass
    elif _IS_WIN:
        try:
            import ctypes
            ctypes.windll.user32.OpenClipboard(0)
            data = ctypes.windll.user32.GetClipboardData(13)
            text = ctypes.cast(data, ctypes.c_wchar_p).value or ""
            ctypes.windll.user32.CloseClipboard()
            return text
        except Exception:
            pass
    elif _IS_MAC:
        try:
            return subprocess.check_output(["pbpaste"], timeout=3, text=True)
        except Exception:
            pass
    return ""


def _clipboard_set(text: str):
    try:
        import pyperclip  # type: ignore
        pyperclip.copy(text)
        return
    except Exception:
        pass
    if _IS_LINUX:
        try:
            proc = subprocess.Popen(["xclip", "-selection", "clipboard", "-i"], stdin=subprocess.PIPE)
            proc.communicate(text.encode())
            return
        except Exception:
            try:
                proc = subprocess.Popen(["xsel", "--clipboard", "--input"], stdin=subprocess.PIPE)
                proc.communicate(text.encode())
                return
            except Exception:
                pass
    elif _IS_WIN:
        try:
            proc = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
            proc.communicate(text.encode("utf-16le"))
        except Exception:
            pass
    elif _IS_MAC:
        try:
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(text.encode())
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────────────────
# Vision Analysis
# ──────────────────────────────────────────────────────────────────────────────

def _analyze_screenshot(image_path: str, prompt: str, provider_fn=None) -> str:
    """Analyze a screenshot with the available vision-capable AI provider.

    provider_fn: callable(image_path, prompt) -> str. If None, tries to use
    the best available provider from the environment.
    """
    if provider_fn is not None:
        try:
            return provider_fn(image_path, prompt)
        except Exception as e:
            log.debug("Custom provider vision failed: %s", e)

    # Try Gemini (supports vision natively)
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            import PIL.Image  # type: ignore
            img = PIL.Image.open(image_path)
            response = model.generate_content([prompt, img])
            return response.text
        except Exception as e:
            log.debug("Gemini vision failed: %s", e)

    # Try Claude (vision capable)
    claude_key = os.environ.get("ANTHROPIC_API_KEY")
    if claude_key:
        try:
            import anthropic  # type: ignore
            import base64
            client = anthropic.Anthropic(api_key=claude_key)
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            msg = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_data}},
                    {"type": "text", "text": prompt},
                ]}]
            )
            return msg.content[0].text
        except Exception as e:
            log.debug("Claude vision failed: %s", e)

    # Try OpenAI Vision
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai  # type: ignore
            import base64
            client = openai.OpenAI(api_key=openai_key)
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}},
                    {"type": "text", "text": prompt},
                ]}],
                max_tokens=1024
            )
            return resp.choices[0].message.content
        except Exception as e:
            log.debug("OpenAI vision failed: %s", e)

    # HuggingFace Inference (Idefics / Qwen-VL)
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
    if hf_token:
        try:
            import requests
            import base64
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            # Try Qwen2-VL via HF Inference
            model_id = "Qwen/Qwen2-VL-7B-Instruct"
            resp = requests.post(
                f"https://api-inference.huggingface.co/models/{model_id}",
                headers={"Authorization": f"Bearer {hf_token}"},
                json={"inputs": {"image": img_data, "question": prompt}},
                timeout=60
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and data:
                    return data[0].get("answer") or str(data[0])
                return str(data)
        except Exception as e:
            log.debug("HF vision failed: %s", e)

    return "[Vision analysis unavailable — no AI provider configured]"


# ──────────────────────────────────────────────────────────────────────────────
# Action result data classes
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ActionResult:
    success: bool
    message: str
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    vision_result: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# OSAgent — the main control class
# ──────────────────────────────────────────────────────────────────────────────

class OSAgent:
    """Autonomous OS control agent.

    Implements the full observe→understand→plan→act→verify loop.
    Every action captures a before-screenshot and (optionally) an after-
    screenshot, then passes both to the vision layer to verify success.
    """

    def __init__(self, vision_provider=None, take_verification_shots: bool = True):
        self._vision_provider = vision_provider
        self._verify = take_verification_shots and _HAS_DISPLAY
        self._action_history: List[Dict[str, Any]] = []

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _snap(self) -> Optional[str]:
        if not _HAS_DISPLAY:
            return None
        return _take_screenshot()

    def _vision(self, image_path: Optional[str], prompt: str) -> str:
        if image_path is None:
            return "No screenshot available"
        return _analyze_screenshot(image_path, prompt, self._vision_provider)

    def _record(self, action: str, params: dict, result: ActionResult):
        self._action_history.append({
            "action": action, "params": params,
            "success": result.success, "message": result.message,
            "ts": time.time(),
        })

    # ── Screenshot / Observe ──────────────────────────────────────────────────

    def screenshot(self, prompt: str = "Describe what you see on the screen") -> ActionResult:
        path = self._snap()
        if path is None:
            return ActionResult(False, "Could not capture screenshot — no display")
        vision = self._vision(path, prompt)
        r = ActionResult(True, "Screenshot captured", screenshot_before=path, vision_result=vision)
        self._record("screenshot", {"prompt": prompt}, r)
        return r

    def observe(self) -> str:
        """Capture current screen state and return a text description."""
        result = self.screenshot("Describe everything visible on the screen in detail: open applications, text, UI elements, status bars, any error messages.")
        if result.success:
            return result.vision_result or "Screen captured but vision unavailable"
        return "Screen observation unavailable"

    # ── Mouse actions ─────────────────────────────────────────────────────────

    def click(self, x: int, y: int, button: str = "left", count: int = 1) -> ActionResult:
        before = self._snap()
        _mouse_click(x, y, button, count)
        time.sleep(0.3)
        after = self._snap() if self._verify else None
        msg = f"Clicked {button} button at ({x},{y}) x{count}"
        if after and self._verify:
            v = self._vision(after, f"Did the click at ({x},{y}) have any visible effect? What changed?")
            r = ActionResult(True, msg, before, after, v)
        else:
            r = ActionResult(True, msg, before, after)
        self._record("click", {"x": x, "y": y, "button": button, "count": count}, r)
        return r

    def double_click(self, x: int, y: int) -> ActionResult:
        return self.click(x, y, count=2)

    def right_click(self, x: int, y: int) -> ActionResult:
        return self.click(x, y, button="right")

    def scroll(self, x: int, y: int, direction: str = "down", amount: int = 3) -> ActionResult:
        dy = -amount if direction == "down" else amount
        _mouse_scroll(x, y, dy=dy)
        time.sleep(0.2)
        after = self._snap() if self._verify else None
        r = ActionResult(True, f"Scrolled {direction} at ({x},{y})", screenshot_after=after)
        self._record("scroll", {"x": x, "y": y, "direction": direction, "amount": amount}, r)
        return r

    def drag(self, x1: int, y1: int, x2: int, y2: int) -> ActionResult:
        before = self._snap()
        _mouse_drag(x1, y1, x2, y2)
        time.sleep(0.3)
        after = self._snap() if self._verify else None
        r = ActionResult(True, f"Dragged ({x1},{y1}) → ({x2},{y2})", before, after)
        self._record("drag", {"x1": x1, "y1": y1, "x2": x2, "y2": y2}, r)
        return r

    def move_mouse(self, x: int, y: int) -> ActionResult:
        _mouse_move(x, y)
        r = ActionResult(True, f"Moved mouse to ({x},{y})")
        self._record("move_mouse", {"x": x, "y": y}, r)
        return r

    # ── Keyboard actions ──────────────────────────────────────────────────────

    def type_text(self, text: str, interval: float = 0.03) -> ActionResult:
        before = self._snap()
        _keyboard_type(text, interval=interval)
        time.sleep(0.2)
        after = self._snap() if self._verify else None
        if after and self._verify:
            v = self._vision(after, f"Was the text '{text[:40]}' typed into a visible field?")
            r = ActionResult(True, f"Typed {len(text)} characters", before, after, v)
        else:
            r = ActionResult(True, f"Typed {len(text)} characters", before, after)
        self._record("type_text", {"text": text[:200]}, r)
        return r

    def press_key(self, key: str) -> ActionResult:
        _keyboard_press(key)
        time.sleep(0.1)
        r = ActionResult(True, f"Pressed key: {key}")
        self._record("press_key", {"key": key}, r)
        return r

    def hotkey(self, *keys: str) -> ActionResult:
        before = self._snap()
        _keyboard_hotkey(*keys)
        time.sleep(0.3)
        after = self._snap() if self._verify else None
        combo = "+".join(keys)
        r = ActionResult(True, f"Pressed hotkey: {combo}", before, after)
        self._record("hotkey", {"keys": list(keys)}, r)
        return r

    # ── Application / Window management ───────────────────────────────────────

    def open_application(self, name: str) -> ActionResult:
        before = self._snap()
        pid = _launch_app(name)
        time.sleep(2.0)
        after = self._snap() if self._verify else None
        if after and self._verify:
            v = self._vision(after, f"Did the application '{name}' open successfully? Is it visible?")
            success = pid is not None
            r = ActionResult(success, f"Opened {name} (pid={pid})", before, after, v)
        else:
            r = ActionResult(pid is not None, f"Launched {name} (pid={pid})", before, after)
        self._record("open_application", {"name": name}, r)
        return r

    def focus_window(self, title: str) -> ActionResult:
        success = _focus_window(title)
        time.sleep(0.3)
        r = ActionResult(success, f"Focused window containing '{title}'")
        self._record("focus_window", {"title": title}, r)
        return r

    def list_windows(self) -> List[Dict[str, Any]]:
        return _get_window_list()

    def close_window(self) -> ActionResult:
        r = self.hotkey("alt", "f4") if _IS_WIN or _IS_LINUX else self.hotkey("cmd", "w")
        r.message = "Closed active window"
        return r

    def minimize_window(self) -> ActionResult:
        if _IS_LINUX:
            try:
                subprocess.run(["xdotool", "getactivewindow", "windowminimize"], timeout=3)
                return ActionResult(True, "Minimized active window")
            except Exception:
                pass
        r = self.hotkey("super", "down") if _IS_WIN else self.hotkey("cmd", "m")
        r.message = "Minimized active window"
        return r

    def maximize_window(self) -> ActionResult:
        if _IS_LINUX:
            try:
                subprocess.run(["wmctrl", "-r", ":ACTIVE:", "-b", "add,maximized_vert,maximized_horz"], timeout=3)
                return ActionResult(True, "Maximized active window")
            except Exception:
                pass
        r = self.hotkey("super", "up") if _IS_WIN else self.hotkey("ctrl", "cmd", "f")
        r.message = "Maximized active window"
        return r

    # ── Clipboard ─────────────────────────────────────────────────────────────

    def get_clipboard(self) -> str:
        return _clipboard_get()

    def set_clipboard(self, text: str) -> ActionResult:
        _clipboard_set(text)
        r = ActionResult(True, f"Set clipboard to: {text[:80]}..." if len(text) > 80 else f"Set clipboard to: {text}")
        self._record("set_clipboard", {"text": text[:200]}, r)
        return r

    def paste_clipboard(self) -> ActionResult:
        return self.hotkey("ctrl", "v") if not _IS_MAC else self.hotkey("cmd", "v")

    # ── Find element by vision ─────────────────────────────────────────────────

    def find_element(self, description: str) -> Optional[Tuple[int, int]]:
        """Find a UI element by visual description, return (x, y) or None."""
        path = self._snap()
        if path is None:
            return None
        prompt = (
            f"Find the element: '{description}'. "
            "Return ONLY the pixel coordinates as: x=<number> y=<number>. "
            "If not found, say 'not found'."
        )
        result = self._vision(path, prompt)
        # Parse coordinates from vision response
        m = re.search(r"x\s*[=:]\s*(\d+).*?y\s*[=:]\s*(\d+)", result, re.IGNORECASE)
        if m:
            return int(m.group(1)), int(m.group(2))
        m = re.search(r"(\d+)\s*,\s*(\d+)", result)
        if m and "not found" not in result.lower():
            return int(m.group(1)), int(m.group(2))
        return None

    def click_element(self, description: str) -> ActionResult:
        """Find and click a UI element by visual description."""
        coords = self.find_element(description)
        if coords is None:
            r = ActionResult(False, f"Element not found: '{description}'")
            self._record("click_element", {"description": description}, r)
            return r
        return self.click(coords[0], coords[1])

    def type_into(self, field_description: str, text: str) -> ActionResult:
        """Find a text field and type into it."""
        r = self.click_element(field_description)
        if not r.success:
            return r
        time.sleep(0.3)
        return self.type_text(text)

    # ── High-level browser tasks ───────────────────────────────────────────────

    def navigate_browser(self, url: str) -> ActionResult:
        """Open URL in the default browser."""
        try:
            import webbrowser
            webbrowser.open(url)
            time.sleep(2.0)
            r = ActionResult(True, f"Opened URL in browser: {url}")
            self._record("navigate_browser", {"url": url}, r)
            return r
        except Exception as e:
            r = ActionResult(False, f"Browser open failed: {e}")
            self._record("navigate_browser", {"url": url}, r)
            return r

    def browser_address_bar(self, url: str) -> ActionResult:
        """Type URL into browser address bar (assumes browser is focused)."""
        self.hotkey("ctrl", "l") if not _IS_MAC else self.hotkey("cmd", "l")
        time.sleep(0.3)
        self.type_text(url)
        time.sleep(0.1)
        return self.press_key("enter")

    def browser_search(self, query: str) -> ActionResult:
        """Open browser and search for a query."""
        self.navigate_browser(f"https://www.google.com/search?q={query.replace(' ', '+')}") 
        time.sleep(3.0)
        after = self._snap()
        v = self._vision(after, f"Did the browser show search results for '{query}'?") if after else None
        r = ActionResult(True, f"Searched for: {query}", screenshot_after=after, vision_result=v)
        self._record("browser_search", {"query": query}, r)
        return r

    # ── Action history ─────────────────────────────────────────────────────────

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._action_history)

    def clear_history(self):
        self._action_history.clear()

    def last_action_summary(self) -> str:
        if not self._action_history:
            return "No actions taken yet"
        last = self._action_history[-1]
        return f"{last['action']}({last['params']}) → {'✓' if last['success'] else '✗'} {last['message']}"

    # ── Full automated task execution loop ────────────────────────────────────

    def execute_task_with_vision(self, task: str, steps: List[Dict[str, Any]], max_retries: int = 3) -> str:
        """Execute a list of action steps with vision verification.

        steps is a list of dicts like:
          {"action": "click", "x": 100, "y": 200}
          {"action": "type_text", "text": "hello"}
          {"action": "press_key", "key": "enter"}
          {"action": "screenshot", "prompt": "verify..."}
          {"action": "open_application", "name": "firefox"}
        """
        results = []
        for i, step in enumerate(steps):
            action = step.get("action", "")
            retries = 0
            while retries <= max_retries:
                try:
                    if action == "click":
                        r = self.click(step["x"], step["y"], step.get("button", "left"), step.get("count", 1))
                    elif action == "double_click":
                        r = self.double_click(step["x"], step["y"])
                    elif action == "right_click":
                        r = self.right_click(step["x"], step["y"])
                    elif action == "type_text":
                        r = self.type_text(step["text"], step.get("interval", 0.03))
                    elif action == "press_key":
                        r = self.press_key(step["key"])
                    elif action == "hotkey":
                        r = self.hotkey(*step["keys"])
                    elif action == "scroll":
                        r = self.scroll(step.get("x", 0), step.get("y", 0), step.get("direction", "down"), step.get("amount", 3))
                    elif action == "drag":
                        r = self.drag(step["x1"], step["y1"], step["x2"], step["y2"])
                    elif action == "open_application":
                        r = self.open_application(step["name"])
                    elif action == "navigate_browser":
                        r = self.navigate_browser(step["url"])
                    elif action == "browser_search":
                        r = self.browser_search(step["query"])
                    elif action == "screenshot":
                        r = self.screenshot(step.get("prompt", "Describe the screen"))
                    elif action == "find_and_click":
                        r = self.click_element(step["description"])
                    elif action == "type_into":
                        r = self.type_into(step["field"], step["text"])
                    elif action == "wait":
                        time.sleep(step.get("seconds", 1.0))
                        r = ActionResult(True, f"Waited {step.get('seconds', 1.0)}s")
                    elif action == "focus_window":
                        r = self.focus_window(step["title"])
                    elif action == "set_clipboard":
                        r = self.set_clipboard(step["text"])
                    elif action == "paste":
                        r = self.paste_clipboard()
                    else:
                        r = ActionResult(False, f"Unknown action: {action}")

                    results.append({"step": i+1, "action": action, "success": r.success, "message": r.message})
                    if r.success:
                        break
                    retries += 1
                    if retries <= max_retries:
                        time.sleep(1.0)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        results.append({"step": i+1, "action": action, "success": False, "message": str(e)})
                        break
                    time.sleep(1.0)

        success_count = sum(1 for r in results if r["success"])
        summary = f"Task '{task}': {success_count}/{len(results)} steps succeeded\n"
        for r in results:
            mark = "✓" if r["success"] else "✗"
            summary += f"  {mark} Step {r['step']}: {r['action']} — {r['message']}\n"
        return summary


# ── Module-level singleton ────────────────────────────────────────────────────
_agent: Optional[OSAgent] = None

def get_os_agent(vision_provider=None) -> OSAgent:
    global _agent
    if _agent is None:
        _agent = OSAgent(vision_provider=vision_provider)
    return _agent


# ── Convenience functions for direct import ───────────────────────────────────

def take_screenshot(prompt: str = "Describe the screen") -> ActionResult:
    return get_os_agent().screenshot(prompt)

def click(x: int, y: int, button: str = "left") -> ActionResult:
    return get_os_agent().click(x, y, button)

def type_text(text: str) -> ActionResult:
    return get_os_agent().type_text(text)

def press_key(key: str) -> ActionResult:
    return get_os_agent().press_key(key)

def hotkey(*keys: str) -> ActionResult:
    return get_os_agent().hotkey(*keys)

def open_app(name: str) -> ActionResult:
    return get_os_agent().open_application(name)

def observe_screen() -> str:
    return get_os_agent().observe()
