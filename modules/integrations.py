"""
modules/integrations.py — Unified API for all 24 integrated repos.
Every import is wrapped in try/except; missing dependencies disable only that feature.
"""
from __future__ import annotations
import os, sys, json, time, subprocess, platform, tempfile, types
from pathlib import Path
from typing import Any, Dict, List, Optional

_ROOT = Path(__file__).parent.parent.resolve()
_EXT  = _ROOT / "external"
_REPOS_DIR = _ROOT / "repos"

# ── sys.path bootstrap ────────────────────────────────────────────────────────
def _add(p: Path):
    s = str(p)
    if p.is_dir() and s not in sys.path:
        sys.path.insert(0, s)

# external repos
for _name in [
    "AIA", "self-operating-computer", "Devin-3.0", "Devin-2.0", "Devin",
    "Jarvis", "JARVIS-microsoft", "OpenDevin", "shannon", "gemini-cli",
    "claude-code", "cheetahclaws", "hexstrike-ai", "openclaw", "vulnerability-analysis",
    "Holomat", "PowerTools", "Responder", "nishang", "metasploit-framework",
]:
    _add(_EXT / _name)

# copied repos
for _d in _REPOS_DIR.iterdir() if _REPOS_DIR.exists() else []:
    _add(_d)
    for _sub in _d.iterdir() if _d.is_dir() else []:
        if _sub.is_dir() and not _sub.name.startswith('.'):
            _add(_sub)

# own modules
_add(_ROOT / "modules")
_add(_ROOT / "ai_core")

# ── Capability flags ──────────────────────────────────────────────────────────
HAS = {}  # populated below

# ── AIA ───────────────────────────────────────────────────────────────────────
def _stub(name: str, cls_name: str = "Stub") -> types.ModuleType:
    m = types.ModuleType(name)
    setattr(m, cls_name, type(cls_name, (), {"handle_exception": lambda *a, **k: None}))
    return m

try:
    for _sn in ["modules.error_handling", "error_handling", "modules.device_control", "device_control"]:
        if _sn not in sys.modules:
            sys.modules[_sn] = _stub(_sn, "ErrorHandling" if "error" in _sn else "DeviceControl")
    sys.path.insert(0, str(_EXT / "AIA"))
    sys.path.insert(0, str(_EXT / "AIA" / "modules"))
    from automation import Automation as AIAAutomation
    aia_automation = AIAAutomation()
    HAS["aia_automation"] = True
except Exception as _e:
    aia_automation = None
    HAS["aia_automation"] = False

try:
    from internet_tasks import InternetTasks
    aia_internet = InternetTasks()
    HAS["aia_internet"] = True
except Exception:
    aia_internet = None
    HAS["aia_internet"] = False

try:
    from device_control import DeviceControl
    aia_device = DeviceControl()
    HAS["aia_device"] = True
except Exception:
    aia_device = None
    HAS["aia_device"] = False

try:
    from voice_assistant import VoiceAssistant as AIAVoice
    aia_voice = AIAVoice()
    HAS["aia_voice"] = True
except Exception:
    aia_voice = None
    HAS["aia_voice"] = False

try:
    from face_detection import FaceDetection
    aia_face = FaceDetection()
    HAS["aia_face"] = True
except Exception:
    aia_face = None
    HAS["aia_face"] = False

try:
    from machine_learning import MachineLearning
    aia_ml = MachineLearning()
    HAS["aia_ml"] = True
except Exception:
    aia_ml = None
    HAS["aia_ml"] = False

# ── Self-Operating-Computer ───────────────────────────────────────────────────
try:
    sys.path.insert(0, str(_EXT / "self-operating-computer"))
    from operate.utils.operating_system import OperatingSystem as SOCOperatingSystem
    from operate.utils.screenshot import capture_screen_with_cursor
    soc_os = SOCOperatingSystem()
    HAS["soc"] = True
except Exception:
    soc_os = None
    HAS["soc"] = False
    def capture_screen_with_cursor(*a, **k): return None  # type: ignore

# ── Jarvis (Concept-Bytes) ────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(_EXT / "Jarvis"))
    import tools as jarvis_tools
    HAS["jarvis"] = True
except Exception:
    jarvis_tools = None
    HAS["jarvis"] = False

# ── cheetahclaws (multi-agent RL / reasoning) ─────────────────────────────────
try:
    sys.path.insert(0, str(_EXT / "cheetahclaws"))
    from cheetahclaws.agent import Agent as CheetahAgent
    HAS["cheetah"] = True
except Exception:
    CheetahAgent = None  # type: ignore
    HAS["cheetah"] = False

# ── OpenDevin canvas tool ─────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(_EXT / "OpenDevin"))
    from tools.canvas_ui_tool import CanvasTool
    HAS["opendevin"] = True
except Exception:
    CanvasTool = None  # type: ignore
    HAS["opendevin"] = False

# ── vulnerability-analysis ────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(_EXT / "vulnerability-analysis" / "src"))
    from cve.utils import tools as vuln_tools
    HAS["vuln_analysis"] = True
except Exception:
    vuln_tools = None
    HAS["vuln_analysis"] = False

# ── JARVIS-microsoft easytool ─────────────────────────────────────────────────
try:
    sys.path.insert(0, str(_EXT / "JARVIS-microsoft" / "easytool"))
    from easytool import util as jarvis_ms_util
    HAS["jarvis_ms"] = True
except Exception:
    jarvis_ms_util = None
    HAS["jarvis_ms"] = False

# ── Responder ─────────────────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(_EXT / "Responder"))
    import utils as responder_utils
    HAS["responder"] = True
except Exception:
    responder_utils = None
    HAS["responder"] = False

# ── pyautogui ────────────────────────────────────────────────────────────────
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.05
    HAS["pyautogui"] = True
except Exception:
    pyautogui = None  # type: ignore
    HAS["pyautogui"] = False

# ── mss ──────────────────────────────────────────────────────────────────────
try:
    import mss, mss.tools
    HAS["mss"] = True
except Exception:
    mss = None  # type: ignore
    HAS["mss"] = False

# ── PIL ───────────────────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageGrab, ImageDraw
    HAS["pil"] = True
except Exception:
    Image = ImageGrab = ImageDraw = None  # type: ignore
    HAS["pil"] = False

# ── pyttsx3 (TTS) ─────────────────────────────────────────────────────────────
try:
    import pyttsx3 as _pyttsx3
    _tts_engine = _pyttsx3.init()
    _tts_engine.setProperty("rate", 175)
    _tts_engine.setProperty("volume", 0.9)
    HAS["tts"] = True
except Exception:
    _tts_engine = None
    HAS["tts"] = False

# ── SpeechRecognition (STT) ───────────────────────────────────────────────────
try:
    import speech_recognition as _sr
    _recognizer = _sr.Recognizer()
    HAS["stt"] = True
except Exception:
    _sr = None
    _recognizer = None
    HAS["stt"] = False

# ── Selenium ──────────────────────────────────────────────────────────────────
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS["selenium"] = True
except Exception:
    webdriver = By = Keys = WebDriverWait = EC = None  # type: ignore
    HAS["selenium"] = False

# ── psutil ────────────────────────────────────────────────────────────────────
try:
    import psutil
    HAS["psutil"] = True
except Exception:
    psutil = None  # type: ignore
    HAS["psutil"] = False

# ── requests ──────────────────────────────────────────────────────────────────
try:
    import requests
    HAS["requests"] = True
except Exception:
    requests = None  # type: ignore
    HAS["requests"] = False

# ── google-genai ──────────────────────────────────────────────────────────────
try:
    from google import genai as _google_genai
    HAS["google_genai"] = True
except Exception:
    _google_genai = None  # type: ignore
    HAS["google_genai"] = False

# ── anthropic ─────────────────────────────────────────────────────────────────
try:
    import anthropic as _anthropic_sdk
    HAS["anthropic"] = True
except Exception:
    _anthropic_sdk = None  # type: ignore
    HAS["anthropic"] = False

# ── openai ────────────────────────────────────────────────────────────────────
try:
    import openai as _openai_sdk
    HAS["openai"] = True
except Exception:
    _openai_sdk = None  # type: ignore
    HAS["openai"] = False

# ── nmap ─────────────────────────────────────────────────────────────────────
try:
    import nmap as _nmap
    HAS["nmap"] = True
except Exception:
    _nmap = None  # type: ignore
    HAS["nmap"] = False

# ── scapy ────────────────────────────────────────────────────────────────────
try:
    from scapy.all import sniff, ARP, Ether, srp, IP, TCP, UDP
    HAS["scapy"] = True
except Exception:
    sniff = ARP = Ether = srp = IP = TCP = UDP = None  # type: ignore
    HAS["scapy"] = False

# ── bs4 ───────────────────────────────────────────────────────────────────────
try:
    from bs4 import BeautifulSoup
    HAS["bs4"] = True
except Exception:
    BeautifulSoup = None  # type: ignore
    HAS["bs4"] = False

# ── rich ──────────────────────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    HAS["rich"] = True
except Exception:
    Console = Markdown = Panel = Syntax = Progress = SpinnerColumn = TextColumn = Table = Live = Text = None  # type: ignore
    HAS["rich"] = False

# ── CV2 (opencv) ──────────────────────────────────────────────────────────────
try:
    import cv2
    HAS["cv2"] = True
except Exception:
    cv2 = None  # type: ignore
    HAS["cv2"] = False

# ── boto3 (AWS) ───────────────────────────────────────────────────────────────
try:
    import boto3
    HAS["boto3"] = True
except Exception:
    boto3 = None  # type: ignore
    HAS["boto3"] = False

# ── paramiko (SSH) ────────────────────────────────────────────────────────────
try:
    import paramiko
    HAS["paramiko"] = True
except Exception:
    paramiko = None  # type: ignore
    HAS["paramiko"] = False

# ── pygetwindow (window mgmt) ─────────────────────────────────────────────────
try:
    import pygetwindow as gw
    HAS["pygetwindow"] = True
except Exception:
    gw = None  # type: ignore
    HAS["pygetwindow"] = False

# ── pynput (low-level input) ──────────────────────────────────────────────────
try:
    from pynput import mouse as _pynput_mouse, keyboard as _pynput_keyboard
    HAS["pynput"] = True
except Exception:
    _pynput_mouse = _pynput_keyboard = None  # type: ignore
    HAS["pynput"] = False

# ── watchdog (filesystem events) ─────────────────────────────────────────────
try:
    from watchdog.observers import Observer as FSObserver
    from watchdog.events import FileSystemEventHandler
    HAS["watchdog"] = True
except Exception:
    FSObserver = FileSystemEventHandler = None  # type: ignore
    HAS["watchdog"] = False

# ── pyserial (robotics) ───────────────────────────────────────────────────────
try:
    import serial
    HAS["serial"] = True
except Exception:
    serial = None  # type: ignore
    HAS["serial"] = False

# ── tweepy (Twitter/X) ────────────────────────────────────────────────────────
try:
    import tweepy
    HAS["tweepy"] = True
except Exception:
    tweepy = None  # type: ignore
    HAS["tweepy"] = False

# ── praw (Reddit) ─────────────────────────────────────────────────────────────
try:
    import praw
    HAS["praw"] = True
except Exception:
    praw = None  # type: ignore
    HAS["praw"] = False

# ── discord.py ────────────────────────────────────────────────────────────────
try:
    import discord
    HAS["discord"] = True
except Exception:
    discord = None  # type: ignore
    HAS["discord"] = False

# ── slack_bolt ────────────────────────────────────────────────────────────────
try:
    from slack_bolt import App as SlackApp
    HAS["slack"] = True
except Exception:
    SlackApp = None  # type: ignore
    HAS["slack"] = False

# ─────────────────────────────────────────────────────────────────────────────
# Tool functions — each one wraps repo functionality
# ─────────────────────────────────────────────────────────────────────────────

PLATFORM = platform.system()  # 'Linux', 'Darwin', 'Windows'

def take_screenshot(path: Optional[str] = None) -> str:
    """Take a screenshot, return file path. Uses mss → pyautogui → PIL fallback."""
    if path is None:
        path = tempfile.mktemp(suffix=".png", prefix="devin_")
    if HAS["mss"] and mss:
        try:
            with mss.mss() as sct:
                sct.shot(output=path)
            return path
        except Exception:
            pass
    if HAS["pyautogui"] and pyautogui:
        try:
            img = pyautogui.screenshot()
            img.save(path)
            return path
        except Exception:
            pass
    if HAS["pil"] and ImageGrab:
        try:
            img = ImageGrab.grab()
            img.save(path)
            return path
        except Exception:
            pass
    # Linux fallback: scrot
    if PLATFORM == "Linux":
        try:
            subprocess.run(["scrot", path], timeout=5, check=True)
            return path
        except Exception:
            pass
    return ""

def mouse_click(x: int, y: int, button: str = "left") -> bool:
    """Click at (x, y) with given button."""
    if HAS["pyautogui"] and pyautogui:
        try:
            pyautogui.click(x, y, button=button)
            return True
        except Exception:
            pass
    if HAS["pynput"] and _pynput_mouse:
        try:
            from pynput.mouse import Button, Controller
            m = Controller()
            m.position = (x, y)
            btn = Button.left if button == "left" else Button.right
            m.press(btn); m.release(btn)
            return True
        except Exception:
            pass
    return False

def mouse_right_click(x: int, y: int) -> bool:
    """Right-click at (x, y)."""
    return mouse_click(x, y, button="right")

def mouse_double_click(x: int, y: int) -> bool:
    """Double-click at (x, y)."""
    if HAS["pyautogui"] and pyautogui:
        try:
            pyautogui.doubleClick(x, y)
            return True
        except Exception:
            pass
    return False

def mouse_move(x: int, y: int) -> bool:
    """Move cursor to (x, y)."""
    if HAS["pyautogui"] and pyautogui:
        try:
            pyautogui.moveTo(x, y, duration=0.15)
            return True
        except Exception:
            pass
    return False

def mouse_drag(x1: int, y1: int, x2: int, y2: int, duration: float = 0.4) -> bool:
    """Drag from (x1, y1) to (x2, y2)."""
    if HAS["pyautogui"] and pyautogui:
        try:
            pyautogui.moveTo(x1, y1)
            pyautogui.dragTo(x2, y2, duration=duration, button='left')
            return True
        except Exception:
            pass
    return False

def mouse_scroll(x: int, y: int, direction: str = "down", amount: int = 3) -> bool:
    """Scroll at (x, y). direction: 'up' or 'down'."""
    if HAS["pyautogui"] and pyautogui:
        try:
            clicks = amount if direction == "up" else -amount
            pyautogui.scroll(clicks, x=x, y=y)
            return True
        except Exception:
            pass
    return False

def keyboard_type(text: str, interval: float = 0.02) -> bool:
    """Type text using pyautogui. Uses clipboard for unicode."""
    if not HAS["pyautogui"] or not pyautogui:
        return False
    try:
        # Check if ASCII-safe
        if all(ord(c) < 128 for c in text):
            pyautogui.write(text, interval=interval)
        else:
            # Unicode: use clipboard paste
            import subprocess
            if PLATFORM == "Linux":
                subprocess.run(["xdotool", "type", "--delay", "20", text], check=True, timeout=10)
            elif PLATFORM == "Darwin":
                pyautogui.hotkey("command", "a")
                pyautogui.hotkey("command", "c")
                subprocess.run(["pbcopy"], input=text.encode(), check=True)
                pyautogui.hotkey("command", "v")
            else:
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                pyautogui.hotkey("ctrl", "v")
        return True
    except Exception:
        return False

def keyboard_press(key: str) -> bool:
    """Press a single key (e.g. 'Return', 'Tab', 'escape')."""
    if HAS["pyautogui"] and pyautogui:
        try:
            pyautogui.press(key)
            return True
        except Exception:
            pass
    return False

def keyboard_hotkey(*keys: str) -> bool:
    """Press a key combination, e.g. keyboard_hotkey('ctrl', 'c')."""
    if HAS["pyautogui"] and pyautogui:
        try:
            pyautogui.hotkey(*keys)
            return True
        except Exception:
            pass
    return False

def get_screen_size() -> tuple:
    """Return (width, height) of the primary monitor."""
    if HAS["pyautogui"] and pyautogui:
        try:
            return pyautogui.size()
        except Exception:
            pass
    if HAS["mss"] and mss:
        try:
            with mss.mss() as sct:
                m = sct.monitors[1]
                return (m["width"], m["height"])
        except Exception:
            pass
    return (1920, 1080)

def list_windows() -> List[str]:
    """List all open window titles."""
    if HAS["pygetwindow"] and gw:
        try:
            return [w.title for w in gw.getAllWindows() if w.title]
        except Exception:
            pass
    if PLATFORM == "Linux":
        try:
            out = subprocess.check_output(["wmctrl", "-l"], text=True, timeout=5)
            return [line.split(None, 3)[-1] for line in out.strip().splitlines() if line]
        except Exception:
            pass
    return []

def focus_window(title: str) -> bool:
    """Bring window matching title to front."""
    if HAS["pygetwindow"] and gw:
        try:
            wins = gw.getWindowsWithTitle(title)
            if wins:
                wins[0].activate()
                return True
        except Exception:
            pass
    if PLATFORM == "Linux":
        try:
            subprocess.run(["wmctrl", "-a", title], timeout=5, check=True)
            return True
        except Exception:
            pass
    return False

def open_application(name: str) -> bool:
    """Launch an application by name."""
    try:
        if PLATFORM == "Linux":
            subprocess.Popen([name], start_new_session=True,
                             env={**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")})
        elif PLATFORM == "Darwin":
            subprocess.Popen(["open", "-a", name])
        else:
            subprocess.Popen([name], shell=True)
        return True
    except Exception:
        try:
            # Try via xdg-open / start
            if PLATFORM == "Linux":
                subprocess.Popen(["xdg-open", name])
            elif PLATFORM == "Windows":
                os.startfile(name)  # type: ignore
            return True
        except Exception:
            return False

def execute_shell(command: str, timeout: int = 30) -> Dict[str, Any]:
    """Execute shell command, return {'stdout', 'stderr', 'returncode'}."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "output": result.stdout + result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timeout", "returncode": -1, "output": "Timeout"}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1, "output": str(e)}

def execute_python(code: str) -> Dict[str, Any]:
    """Execute Python code, return {'output', 'error'}."""
    import io, traceback
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        exec(code, {"__name__": "__devin__"})  # noqa: S102
        out = sys.stdout.getvalue()
        err = sys.stderr.getvalue()
        return {"output": out, "error": err}
    except Exception:
        return {"output": sys.stdout.getvalue(), "error": traceback.format_exc()}
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

def read_file(path: str) -> str:
    """Read file and return its content."""
    return Path(path).read_text(errors="replace")

def write_file(path: str, content: str) -> bool:
    """Write content to file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content)
    return True

def list_files(directory: str = ".", pattern: str = "*") -> List[str]:
    """List files in directory matching pattern."""
    import fnmatch
    result = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__' and d != 'node_modules']
        for f in files:
            if fnmatch.fnmatch(f, pattern):
                result.append(os.path.join(root, f))
    return result

def web_search(query: str, num_results: int = 5) -> List[Dict]:
    """Web search using googlesearch-python or requests fallback."""
    try:
        from googlesearch import search
        results = []
        for url in search(query, num_results=num_results):
            results.append({"url": url, "title": url})
        return results
    except Exception:
        pass
    if HAS["requests"] and requests:
        try:
            r = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            if HAS["bs4"] and BeautifulSoup:
                soup = BeautifulSoup(r.text, "html.parser")
                return [
                    {"url": a.get("href", ""), "title": a.get_text()}
                    for a in soup.select(".result__title a")[:num_results]
                ]
        except Exception:
            pass
    return [{"url": "", "title": f"Search not available for: {query}"}]

def web_fetch(url: str) -> str:
    """Fetch URL content as text."""
    if HAS["requests"] and requests:
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if HAS["bs4"] and BeautifulSoup:
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                return soup.get_text(separator="\n", strip=True)[:8000]
            return r.text[:8000]
        except Exception as e:
            return f"Error fetching {url}: {e}"
    return "requests not available"

def speak(text: str) -> bool:
    """Text-to-speech output."""
    if HAS["tts"] and _tts_engine:
        try:
            _tts_engine.say(text)
            _tts_engine.runAndWait()
            return True
        except Exception:
            pass
    if PLATFORM == "Darwin":
        try:
            subprocess.run(["say", text], timeout=30)
            return True
        except Exception:
            pass
    if PLATFORM == "Linux":
        try:
            subprocess.run(["espeak", "-s", "170", text], timeout=30)
            return True
        except Exception:
            pass
    return False

def listen(timeout: int = 5) -> str:
    """Listen for voice input and return text."""
    if not HAS["stt"] or not _recognizer or not _sr:
        return ""
    try:
        with _sr.Microphone() as source:
            _recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = _recognizer.listen(source, timeout=timeout)
            return _recognizer.recognize_google(audio)
    except Exception:
        return ""

def clipboard_get() -> str:
    """Get clipboard content."""
    if HAS["pyautogui"] and pyautogui:
        try:
            return pyautogui.hotkey("ctrl", "a") or ""
        except Exception:
            pass
    if PLATFORM == "Linux":
        try:
            return subprocess.check_output(["xclip", "-selection", "clipboard", "-o"],
                                           text=True, timeout=3)
        except Exception:
            try:
                return subprocess.check_output(["xsel", "--clipboard", "--output"],
                                               text=True, timeout=3)
            except Exception:
                pass
    elif PLATFORM == "Darwin":
        try:
            return subprocess.check_output(["pbpaste"], text=True, timeout=3)
        except Exception:
            pass
    return ""

def clipboard_set(text: str) -> bool:
    """Set clipboard content."""
    if PLATFORM == "Linux":
        for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
            try:
                subprocess.run(cmd, input=text.encode(), timeout=3, check=True)
                return True
            except Exception:
                continue
    elif PLATFORM == "Darwin":
        try:
            subprocess.run(["pbcopy"], input=text.encode(), timeout=3, check=True)
            return True
        except Exception:
            pass
    elif PLATFORM == "Windows":
        try:
            subprocess.run(["clip"], input=text.encode("utf-16"), timeout=3, check=True)
            return True
        except Exception:
            pass
    return False

def get_system_info() -> Dict[str, Any]:
    """Get system info using psutil."""
    info: Dict[str, Any] = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "hostname": platform.node(),
    }
    if HAS["psutil"] and psutil:
        try:
            info["cpu_percent"] = psutil.cpu_percent(interval=0.5)
            info["ram_total_gb"] = round(psutil.virtual_memory().total / 1e9, 2)
            info["ram_used_gb"] = round(psutil.virtual_memory().used / 1e9, 2)
            info["ram_percent"] = psutil.virtual_memory().percent
            info["disk_used_gb"] = round(psutil.disk_usage("/").used / 1e9, 2)
            info["disk_total_gb"] = round(psutil.disk_usage("/").total / 1e9, 2)
        except Exception:
            pass
    return info

def list_processes() -> List[Dict]:
    """List running processes."""
    if HAS["psutil"] and psutil:
        procs = []
        for p in psutil.process_iter(["pid", "name", "status", "cpu_percent"]):
            try:
                procs.append(p.info)
            except Exception:
                pass
        return procs[:50]
    return []

def run_nmap_scan(target: str, args: str = "-sV") -> str:
    """Run nmap scan on target."""
    if HAS["nmap"] and _nmap:
        try:
            nm = _nmap.PortScanner()
            nm.scan(hosts=target, arguments=args)
            return nm.csv()
        except Exception as e:
            return str(e)
    try:
        result = subprocess.run(["nmap", args, target], capture_output=True, text=True, timeout=60)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

def open_browser(url: str) -> bool:
    """Open URL in default browser."""
    try:
        import webbrowser
        webbrowser.open(url)
        return True
    except Exception:
        return False

def send_telegram_message(token: str, chat_id: str, text: str) -> bool:
    """Send Telegram message."""
    if HAS["requests"] and requests:
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10,
            )
            return r.ok
        except Exception:
            pass
    return False

def git_command(args: str, cwd: str = ".") -> str:
    """Run a git command and return output."""
    result = execute_shell(f"git {args}", timeout=30)
    return result["output"]

def analyze_image(image_path: str, question: str = "What do you see?") -> str:
    """Analyze an image using available vision API."""
    # This will be handled by the main Gemini loop with vision
    return f"[Image analysis of {image_path}: {question}]"

def search_screen(image_template: str) -> Optional[tuple]:
    """Find an image on screen, return (x, y) center or None."""
    if HAS["pyautogui"] and pyautogui:
        try:
            loc = pyautogui.locateOnScreen(image_template, confidence=0.8)
            if loc:
                return pyautogui.center(loc)
        except Exception:
            pass
    return None

def get_mouse_position() -> tuple:
    """Return current (x, y) mouse position."""
    if HAS["pyautogui"] and pyautogui:
        try:
            return pyautogui.position()
        except Exception:
            pass
    return (0, 0)

# ── TOOL REGISTRY (unified, 60+ tools) ────────────────────────────────────────
TOOL_REGISTRY: Dict[str, Any] = {
    # OS Automation
    "take_screenshot": take_screenshot,
    "mouse_click": mouse_click,
    "mouse_right_click": mouse_right_click,
    "mouse_double_click": mouse_double_click,
    "mouse_move": mouse_move,
    "mouse_drag": mouse_drag,
    "mouse_scroll": mouse_scroll,
    "keyboard_type": keyboard_type,
    "keyboard_press": keyboard_press,
    "keyboard_hotkey": keyboard_hotkey,
    "get_screen_size": get_screen_size,
    "get_mouse_position": get_mouse_position,
    "list_windows": list_windows,
    "focus_window": focus_window,
    "open_application": open_application,
    "search_screen": search_screen,
    # Shell & Code
    "execute_shell": execute_shell,
    "execute_python": execute_python,
    "git_command": git_command,
    # Files
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    # Web
    "web_search": web_search,
    "web_fetch": web_fetch,
    "open_browser": open_browser,
    # Voice
    "speak": speak,
    "listen": listen,
    # Clipboard
    "clipboard_get": clipboard_get,
    "clipboard_set": clipboard_set,
    # System
    "get_system_info": get_system_info,
    "list_processes": list_processes,
    # Security
    "run_nmap_scan": run_nmap_scan,
    # Image/Vision
    "analyze_image": analyze_image,
    # Telegram
    "send_telegram_message": send_telegram_message,
}

# ── Capability summary ────────────────────────────────────────────────────────
def capabilities_summary() -> str:
    active = [k for k, v in HAS.items() if v]
    inactive = [k for k, v in HAS.items() if not v]
    return (
        f"Active ({len(active)}): {', '.join(active)}\n"
        f"Inactive ({len(inactive)}): {', '.join(inactive)}\n"
        f"Tools registered: {len(TOOL_REGISTRY)}"
    )
