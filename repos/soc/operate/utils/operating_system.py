import os
import platform
import subprocess
import time
import math

from operate.utils.misc import convert_percent_to_decimal

_IS_WAYLAND = os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
_YDOTOOL_SOCKET = os.environ.get("YDOTOOL_SOCKET", "/tmp/.ydotool_socket")


def _run_ydotool(*args):
    env = os.environ.copy()
    env["YDOTOOL_SOCKET"] = _YDOTOOL_SOCKET
    subprocess.run(["ydotool"] + list(args), env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _get_screen_size():
    try:
        import subprocess
        out = subprocess.check_output(["xdpyinfo"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if "dimensions:" in line:
                dims = line.split()[1]
                w, h = dims.split("x")
                return int(w), int(h)
    except Exception:
        pass
    return 1920, 1080


class OperatingSystem:
    def __init__(self):
        if not _IS_WAYLAND:
            try:
                import pyautogui
                self._pyautogui = pyautogui
            except ImportError:
                self._pyautogui = None
        else:
            self._pyautogui = None

        try:
            from pynput.mouse import Button, Controller as MouseController
            self._mouse = MouseController()
            self._mouse_button = Button
        except ImportError:
            self._mouse = None

    def write(self, content):
        try:
            content = content.replace("\\n", "\n")
            if _IS_WAYLAND:
                _run_ydotool("type", "--next-delay", "50", "--", content)
            elif self._pyautogui:
                for char in content:
                    self._pyautogui.write(char)
        except Exception as e:
            print("[OperatingSystem][write] error:", e)

    def press(self, keys):
        try:
            if _IS_WAYLAND:
                # Map common key names to ydotool key codes
                key_map = {
                    "enter": "enter", "return": "enter",
                    "tab": "tab", "escape": "esc", "space": "space",
                    "backspace": "backspace", "delete": "delete",
                    "ctrl": "ctrl", "alt": "alt", "shift": "shift",
                    "super": "super",
                    "up": "up", "down": "down", "left": "left", "right": "right",
                }
                mapped = [key_map.get(k.lower(), k.lower()) for k in keys]
                combo = "+".join(mapped)
                _run_ydotool("key", "--key-delay", "50", combo)
            elif self._pyautogui:
                for key in keys:
                    self._pyautogui.keyDown(key)
                time.sleep(0.1)
                for key in keys:
                    self._pyautogui.keyUp(key)
        except Exception as e:
            print("[OperatingSystem][press] error:", e)

    def mouse(self, click_detail):
        try:
            x = convert_percent_to_decimal(click_detail.get("x"))
            y = convert_percent_to_decimal(click_detail.get("y"))

            if click_detail and isinstance(x, float) and isinstance(y, float):
                self.click_at_percentage(x, y)

        except Exception as e:
            print("[OperatingSystem][mouse] error:", e)

    def click_at_percentage(self, x_percentage, y_percentage,
                            duration=0.2, circle_radius=50, circle_duration=0.5):
        try:
            if _IS_WAYLAND and self._mouse:
                screen_width, screen_height = _get_screen_size()
                x_pixel = int(screen_width * float(x_percentage))
                y_pixel = int(screen_height * float(y_percentage))
                self._mouse.position = (x_pixel, y_pixel)
                time.sleep(0.05)
                self._mouse.click(self._mouse_button.left, 1)
            elif self._pyautogui:
                screen_width, screen_height = self._pyautogui.size()
                x_pixel = int(screen_width * float(x_percentage))
                y_pixel = int(screen_height * float(y_percentage))
                self._pyautogui.moveTo(x_pixel, y_pixel, duration=duration)
                self._pyautogui.click(x_pixel, y_pixel)
        except Exception as e:
            print("[OperatingSystem][click_at_percentage] error:", e)
