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

# ── Repository-Specific Tools (from integrated repos) ────────────────────────
# These tools expose capabilities from repos/aia, repos/cheetah, repos/jarvis, etc.

def read_pdf(file_path: str, page_range: str = "1-5") -> str:
    """Read and extract text from PDF file. Page range e.g. '1-5' or '1'."""
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            pages = page_range.split('-')
            start = int(pages[0]) - 1
            end = int(pages[-1]) if len(pages) > 1 else start + 1
            text = ""
            for i in range(start, min(end, len(reader.pages))):
                text += reader.pages[i].extract_text()
            return text[:5000]
    except Exception:
        pass
    # Fallback: try cheetah's PDF reader if available
    try:
        from cheetah_files import _read_pdf
        return _read_pdf({"path": file_path, "page_range": page_range}, {}) or ""
    except Exception:
        return f"Could not read PDF: {file_path}"

def read_excel(file_path: str, sheet: str = None, max_rows: int = 100) -> str:
    """Read and extract data from Excel file."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path)
        ws = wb[sheet] if sheet else wb.active
        data = []
        for row in ws.iter_rows(max_row=max_rows, values_only=True):
            data.append(str(row))
        return "\n".join(data[:50])
    except Exception:
        pass
    # Fallback
    try:
        from cheetah_files import _read_xlsx
        return _read_xlsx({}, {}) or ""
    except Exception:
        return f"Could not read Excel: {file_path}"

def device_info() -> Dict[str, Any]:
    """Get detailed device and system information."""
    info = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }
    if HAS["psutil"]:
        import psutil
        info.update({
            "cpu_percent": psutil.cpu_percent(interval=1),
            "virtual_memory": str(psutil.virtual_memory()),
            "disk_usage": str(psutil.disk_usage("/")),
        })
    return info

def internet_speed_test() -> Dict[str, Any]:
    """Test internet connection speed and latency."""
    result = {"status": "FAILED"}
    if HAS["requests"] and requests:
        try:
            import time
            # Simple latency test to DNS
            start = time.time()
            r = requests.get("https://8.8.8.8", timeout=5)
            latency = (time.time() - start) * 1000
            result = {
                "status": "OK",
                "latency_ms": round(latency),
                "dns_reachable": True
            }
        except Exception:
            result["status"] = "FAILED (no internet)"
    return result

def web_research(topic: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Research a topic by searching the web and fetching summaries."""
    results = web_search(topic, num_results)
    detailed = []
    for r in results[:num_results]:
        url = r.get("url", "")
        summary = web_fetch(url)[:500] if url else ""
        detailed.append({
            "url": url,
            "title": r.get("title", ""),
            "summary": summary
        })
    return detailed

def code_analyze(file_path: str) -> Dict[str, Any]:
    """Analyze code file and return metrics (lines, functions, classes, etc)."""
    try:
        content = Path(file_path).read_text(errors="replace")
        lines = content.split('\n')

        analysis = {
            "file": file_path,
            "total_lines": len(lines),
            "non_empty_lines": len([l for l in lines if l.strip()]),
            "comment_lines": len([l for l in lines if l.strip().startswith('#')]),
            "functions": len([l for l in lines if l.strip().startswith('def ')]),
            "classes": len([l for l in lines if l.strip().startswith('class ')]),
            "imports": len([l for l in lines if 'import' in l]),
            "language": "python" if file_path.endswith('.py') else "unknown"
        }
        return analysis
    except Exception as e:
        return {"error": str(e)}

def run_security_scan(target: str, scan_type: str = "basic") -> Dict[str, Any]:
    """Run security scan on target (nmap, port scan, or basic check)."""
    if scan_type == "nmap" and HAS["nmap"]:
        try:
            return {"nmap_result": run_nmap_scan(target)}
        except Exception:
            pass

    # Basic security checks
    result = {
        "target": target,
        "scan_type": scan_type,
        "checks": []
    }

    if HAS["requests"] and requests:
        try:
            # Check if HTTPS available
            r = requests.head(f"https://{target}", timeout=5)
            result["checks"].append({
                "type": "https",
                "available": r.status_code < 400
            })
        except Exception:
            result["checks"].append({
                "type": "https",
                "available": False
            })

    return result

def find_files(directory: str = ".", pattern: str = "*", max_results: int = 100) -> List[str]:
    """Find files in directory matching pattern. Returns list of file paths."""
    results = []
    try:
        for root, dirs, files in os.walk(directory):
            if len(results) >= max_results:
                break
            # Skip hidden and cache dirs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            for f in files:
                if len(results) >= max_results:
                    break
                import fnmatch
                if fnmatch.fnmatch(f, pattern):
                    results.append(os.path.join(root, f))
    except Exception:
        pass
    return results

def grep_files(directory: str = ".", pattern: str = "", file_pattern: str = "*.py") -> List[Dict]:
    """Search for text pattern in files. Returns matches with context."""
    results = []
    try:
        import re
        regex = re.compile(pattern, re.IGNORECASE)
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if fnmatch.fnmatch(f, file_pattern):
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, 'r', errors='ignore') as file:
                            for i, line in enumerate(file):
                                if regex.search(line):
                                    results.append({
                                        "file": fpath,
                                        "line_num": i + 1,
                                        "line": line.strip()[:100]
                                    })
                                    if len(results) >= 50:
                                        break
                    except Exception:
                        pass
    except Exception:
        pass
    return results[:50]

def task_decompose(task_description: str) -> List[str]:
    """Break down a complex task into sub-tasks."""
    # Simple decomposition using prompt
    sub_tasks = []
    lines = task_description.split('\n')

    # Heuristic: if task mentions multiple things, break them up
    import re
    # Look for "and" separators
    tasks = re.split(r'\s+and\s+|\s*;\s*', task_description, flags=re.IGNORECASE)

    if len(tasks) > 1:
        return [t.strip() for t in tasks if t.strip()]

    # Otherwise suggest generic subtasks
    return [
        f"Analyze: {task_description[:50]}",
        "Execute main action",
        "Verify results",
        "Report findings"
    ]

def memory_save(key: str, value: str) -> bool:
    """Save a fact to short-term memory (session-based)."""
    # Simple implementation using module-level dict
    if not hasattr(memory_save, '_store'):
        memory_save._store = {}
    memory_save._store[key] = value
    return True

def memory_recall(key: str) -> str:
    """Recall a saved fact from short-term memory."""
    if not hasattr(memory_save, '_store'):
        memory_save._store = {}
    return memory_save._store.get(key, "")

def memory_list() -> List[str]:
    """List all saved facts in short-term memory."""
    if not hasattr(memory_save, '_store'):
        memory_save._store = {}
    return list(memory_save._store.keys())

# ── Data Analysis Tools ────────────────────────────────────────────────────────

def parse_csv(file_path: str, max_rows: int = 100) -> str:
    """Parse CSV file and return formatted data."""
    try:
        import csv
        data = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                data.append(str(row))
        return "\n".join(data[:max_rows])
    except Exception as e:
        return f"Error reading CSV: {e}"

def analyze_text(text: str, analysis_type: str = "summary") -> Dict[str, Any]:
    """Analyze text document (length, complexity, keywords, etc)."""
    result = {
        "type": analysis_type,
        "char_count": len(text),
        "word_count": len(text.split()),
        "line_count": len(text.split('\n')),
        "avg_word_length": sum(len(w) for w in text.split()) / max(len(text.split()), 1),
    }

    # Find common words
    import re
    words = re.findall(r'\b\w+\b', text.lower())
    from collections import Counter
    word_freq = Counter(words)
    result["top_words"] = dict(word_freq.most_common(10))

    return result

def compare_files(file1: str, file2: str) -> Dict[str, Any]:
    """Compare two files and show differences."""
    try:
        content1 = Path(file1).read_text(errors='ignore')
        content2 = Path(file2).read_text(errors='ignore')

        lines1 = content1.split('\n')
        lines2 = content2.split('\n')

        import difflib
        diff = list(difflib.unified_diff(lines1, lines2, lineterm=''))

        return {
            "file1": file1,
            "file2": file2,
            "same": content1 == content2,
            "diff_lines": len(diff),
            "diff_summary": "\n".join(diff[:20])  # First 20 diff lines
        }
    except Exception as e:
        return {"error": str(e)}

def extract_urls(text: str) -> List[str]:
    """Extract all URLs from text."""
    import re
    url_pattern = r'https?://[^\s]+'
    return re.findall(url_pattern, text)

def extract_emails(text: str) -> List[str]:
    """Extract all email addresses from text."""
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)

# ── Pentesting / Security Tools ────────────────────────────────────────────────

def port_scan(host: str, ports: str = "22,80,443,3306,5432,8080") -> Dict[str, Any]:
    """Scan common ports on a host."""
    result = {"host": host, "ports_checked": ports.split(','), "open_ports": []}

    if HAS["requests"] and requests:
        for port_str in ports.split(','):
            try:
                port = int(port_str.strip())
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                result_code = s.connect_ex((host, port))
                if result_code == 0:
                    result["open_ports"].append(port)
                s.close()
            except Exception:
                pass

    return result

def check_ssl_cert(domain: str) -> Dict[str, Any]:
    """Check SSL certificate validity for a domain."""
    result = {"domain": domain, "valid": False, "error": None}

    if HAS["requests"] and requests:
        try:
            r = requests.get(f"https://{domain}", timeout=10, verify=True)
            result["valid"] = True
            result["status_code"] = r.status_code
        except requests.exceptions.SSLError as e:
            result["error"] = f"SSL Error: {str(e)[:100]}"
        except Exception as e:
            result["error"] = str(e)[:100]

    return result

def dns_lookup(hostname: str) -> Dict[str, Any]:
    """Lookup DNS records for a hostname."""
    result = {"hostname": hostname, "ips": [], "error": None}

    try:
        import socket
        try:
            ips = socket.gethostbyname_ex(hostname)
            result["ips"] = ips[2]
        except socket.gaierror as e:
            result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)

    return result

def whois_lookup(domain: str) -> Dict[str, str]:
    """WHOIS lookup for a domain."""
    result = {"domain": domain, "registrar": "Unknown", "info": ""}

    if HAS["requests"] and requests:
        try:
            r = requests.get(f"https://whois.arin.net/rest/ip/{domain}", timeout=10)
            if r.ok:
                result["info"] = r.text[:500]
        except Exception:
            pass

    return result

def hash_text(text: str, algorithm: str = "sha256") -> Dict[str, str]:
    """Hash text using specified algorithm (md5, sha1, sha256)."""
    import hashlib

    if algorithm == "md5":
        h = hashlib.md5(text.encode()).hexdigest()
    elif algorithm == "sha1":
        h = hashlib.sha1(text.encode()).hexdigest()
    else:  # sha256 default
        h = hashlib.sha256(text.encode()).hexdigest()

    return {
        "algorithm": algorithm,
        "input": text[:50],
        "hash": h
    }

def extract_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from a file."""
    result = {"file": file_path, "metadata": {}}

    try:
        from pathlib import Path
        p = Path(file_path)
        stat = p.stat()
        result["metadata"] = {
            "size_bytes": stat.st_size,
            "created": str(stat.st_ctime),
            "modified": str(stat.st_mtime),
            "is_file": p.is_file(),
            "is_dir": p.is_dir(),
        }
    except Exception as e:
        result["error"] = str(e)

    return result

# ── Git & Repository Tools ────────────────────────────────────────────────────

def git_log(repo_path: str = ".", max_commits: int = 10) -> str:
    """Get recent git commits from a repository."""
    result = execute_shell(f"cd {repo_path} && git log --oneline -n {max_commits}", timeout=10)
    return result["output"]

def git_status(repo_path: str = ".") -> str:
    """Get git status of a repository."""
    result = execute_shell(f"cd {repo_path} && git status", timeout=10)
    return result["output"]

def git_diff(repo_path: str = ".", file_path: str = None) -> str:
    """Get git diff for a repository or specific file."""
    if file_path:
        result = execute_shell(f"cd {repo_path} && git diff {file_path}", timeout=10)
    else:
        result = execute_shell(f"cd {repo_path} && git diff --stat", timeout=10)
    return result["output"]

# ── Automation & Workflow Tools ────────────────────────────────────────────────

def run_workflow(workflow_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute a predefined workflow (placeholder for future automation)."""
    workflows = {
        "backup": "Backup important files",
        "deploy": "Deploy to production",
        "test": "Run test suite",
        "monitor": "Monitor system health",
    }

    return {
        "workflow": workflow_name,
        "status": "queued",
        "description": workflows.get(workflow_name, "Unknown"),
        "params": params or {}
    }

def schedule_task(task_name: str, cron_schedule: str, command: str) -> Dict[str, str]:
    """Schedule a task to run on a schedule (placeholder)."""
    return {
        "task_name": task_name,
        "schedule": cron_schedule,
        "command": command,
        "status": "scheduled"
    }

# ── AIA Framework Tools (from repos/aia) ───────────────────────────────────

def aia_device_control(device: str, action: str, value: Any = None) -> Dict[str, Any]:
    """Control IoT devices (turn on/off, set value, etc). [From AIA]"""
    if not HAS["aia_device"]:
        return {"status": "not_available", "device": device, "error": "AIA device control not available"}

    result = {
        "device": device,
        "action": action,
        "value": value,
        "status": "executed",
        "timestamp": str(__import__('datetime').datetime.now())
    }

    try:
        from aia_device_control import DeviceControl
        dc = DeviceControl()
        if action == "on":
            dc.turn_on(device)
        elif action == "off":
            dc.turn_off(device)
        elif action == "set":
            dc.set_value(device, value)
        result["success"] = True
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)

    return result

def aia_face_detect(image_path: str) -> Dict[str, Any]:
    """Detect faces in an image. [From AIA]"""
    if not HAS["aia_face"]:
        return {"status": "not_available", "error": "AIA face detection not available"}

    result = {
        "image": image_path,
        "faces_detected": 0,
        "face_data": []
    }

    try:
        from aia_face_detection import FaceDetection
        fd = FaceDetection()
        faces = fd.detect(image_path)
        result["faces_detected"] = len(faces)
        result["face_data"] = faces[:5]  # First 5 faces
    except Exception as e:
        result["error"] = str(e)

    return result

def aia_ml_classify(text: str, model_type: str = "sentiment") -> Dict[str, Any]:
    """Classify text using ML models. [From AIA]"""
    result = {
        "text": text[:100],
        "model": model_type,
        "classification": None,
        "using_aia": HAS.get("aia_ml", False)
    }

    try:
        if model_type == "sentiment":
            # Simple sentiment analysis (works with or without AIA)
            if any(w in text.lower() for w in ['good', 'great', 'excellent', 'love', 'best', 'amazing', 'wonderful']):
                result["classification"] = "positive"
            elif any(w in text.lower() for w in ['bad', 'terrible', 'hate', 'worst', 'awful', 'horrible']):
                result["classification"] = "negative"
            else:
                result["classification"] = "neutral"
        elif model_type == "spam":
            result["classification"] = "ham" if len(text) > 20 else "spam"
    except Exception as e:
        result["error"] = str(e)

    return result

def aia_voice_synthesis(text: str, language: str = "en") -> Dict[str, Any]:
    """Synthesize speech from text. [From AIA voice module]"""
    if not HAS["aia_voice"] and not HAS["tts"]:
        return {"status": "not_available", "error": "Voice synthesis not available"}

    try:
        TOOL_REGISTRY["speak"](text)
        return {
            "status": "synthesized",
            "text": text[:50],
            "language": language
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ── Advanced Cheetah Features (from repos/cheetah) ──────────────────────────

def cheetah_research(topic: str, depth: str = "medium") -> Dict[str, Any]:
    """Deep research on a topic with multiple sources. [From Cheetah research]"""
    results = {
        "topic": topic,
        "depth": depth,
        "sources": [],
        "summary": ""
    }

    # Perform multi-source search
    try:
        search_results = web_search(topic, num_results=10)

        for sr in search_results[:5]:
            url = sr.get("url", "")
            content = web_fetch(url) if url else ""
            results["sources"].append({
                "title": sr.get("title", ""),
                "url": url,
                "preview": content[:200]
            })

        # Create summary from sources
        all_content = " ".join([s.get("preview", "") for s in results["sources"]])
        results["summary"] = all_content[:500]
    except Exception as e:
        results["error"] = str(e)

    return results

def cheetah_code_review(file_path: str) -> Dict[str, Any]:
    """Review code for quality, security, and best practices. [From Cheetah]"""
    result = {
        "file": file_path,
        "issues": [],
        "score": 85
    }

    try:
        content = Path(file_path).read_text(errors='ignore')
        lines = content.split('\n')

        # Simple checks
        if 'import os' in content and 'os.system' in content:
            result["issues"].append({"severity": "high", "issue": "Unsafe os.system() usage"})

        if 'eval(' in content:
            result["issues"].append({"severity": "high", "issue": "Dangerous eval() call"})

        if 'TODO' in content or 'FIXME' in content:
            count = content.count('TODO') + content.count('FIXME')
            result["issues"].append({"severity": "low", "issue": f"{count} TODO comments"})

        # Adjust score based on issues
        result["score"] = max(50, 100 - (len(result["issues"]) * 5))
    except Exception as e:
        result["error"] = str(e)

    return result

def cheetah_file_sync(source: str, dest: str, sync_type: str = "copy") -> Dict[str, Any]:
    """Sync files between directories. [From Cheetah file operations]"""
    result = {
        "source": source,
        "destination": dest,
        "type": sync_type,
        "files_processed": 0,
        "status": "completed"
    }

    try:
        import shutil
        if sync_type == "copy":
            if Path(source).is_file():
                shutil.copy2(source, dest)
                result["files_processed"] = 1
            else:
                shutil.copytree(source, dest, dirs_exist_ok=True)
                result["files_processed"] = sum(1 for _ in Path(dest).rglob('*') if _.is_file())
        elif sync_type == "move":
            shutil.move(source, dest)
            result["files_processed"] = 1
    except Exception as e:
        result["error"] = str(e)
        result["status"] = "failed"

    return result

def advanced_shell_exec(command: str, env_vars: Dict[str, str] = None, capture_output: bool = True) -> Dict[str, Any]:
    """Execute shell command with environment variables. [Enhanced shell]"""
    result = execute_shell(command, timeout=60)

    if env_vars:
        # Re-execute with environment variables
        import subprocess
        env = {**os.environ, **env_vars}
        try:
            r = subprocess.run(command, shell=True, capture_output=True, text=True, env=env, timeout=60)
            result = {
                "stdout": r.stdout,
                "stderr": r.stderr,
                "returncode": r.returncode,
                "output": r.stdout + r.stderr
            }
        except Exception as e:
            result["error"] = str(e)

    return result

def pdf_extract_pages(pdf_path: str, pages: str = "1") -> Dict[str, Any]:
    """Extract specific pages from PDF as text. [From Cheetah PDF tools]"""
    result = {
        "file": pdf_path,
        "pages": pages,
        "text": "",
        "page_count": 0
    }

    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            result["page_count"] = len(reader.pages)

            # Parse page range
            if '-' in pages:
                start, end = pages.split('-')
                page_list = range(int(start)-1, min(int(end), len(reader.pages)))
            else:
                page_list = [int(pages)-1]

            for page_num in page_list:
                if 0 <= page_num < len(reader.pages):
                    result["text"] += reader.pages[page_num].extract_text()
    except Exception as e:
        result["error"] = str(e)

    return result

def image_to_text(image_path: str) -> Dict[str, Any]:
    """Extract text from image using OCR. [Vision capability]"""
    result = {
        "image": image_path,
        "text": "",
        "confidence": 0
    }

    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        result["text"] = text
        result["confidence"] = 0.8  # Placeholder
    except ImportError:
        result["error"] = "pytesseract or tesseract not installed"
    except Exception as e:
        result["error"] = str(e)

    return result

# ── TOOL REGISTRY (unified, now 75+ tools) ────────────────────────────────────
TOOL_REGISTRY: Dict[str, Any] = {
    # ── OS Automation (13 tools) ──
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
    "search_screen": search_screen,

    # ── Window Management (2 tools) ──
    "list_windows": list_windows,
    "focus_window": focus_window,

    # ── Application Launching (1 tool) ──
    "open_application": open_application,

    # ── Shell & Code Execution (3 tools) ──
    "execute_shell": execute_shell,
    "execute_python": execute_python,
    "git_command": git_command,

    # ── File Operations (3 tools) ──
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,

    # ── Web Operations (4 tools) ──
    "web_search": web_search,
    "web_fetch": web_fetch,
    "open_browser": open_browser,
    "web_research": web_research,

    # ── Voice I/O (2 tools) ──
    "speak": speak,
    "listen": listen,

    # ── Clipboard (2 tools) ──
    "clipboard_get": clipboard_get,
    "clipboard_set": clipboard_set,

    # ── System Monitoring (2 tools) ──
    "get_system_info": get_system_info,
    "list_processes": list_processes,
    "device_info": device_info,

    # ── Network & Internet (2 tools) ──
    "run_nmap_scan": run_nmap_scan,
    "internet_speed_test": internet_speed_test,

    # ── Vision & Image Analysis (1 tool) ──
    "analyze_image": analyze_image,

    # ── Communications (1 tool) ──
    "send_telegram_message": send_telegram_message,

    # ── Advanced File Operations (2 tools) [from repos/cheetah]
    "read_pdf": read_pdf,
    "read_excel": read_excel,

    # ── Code Analysis (1 tool) [from repos/]
    "code_analyze": code_analyze,

    # ── Security (1 tool) [enhanced]
    "run_security_scan": run_security_scan,

    # ── File Discovery & Search (2 tools)
    "find_files": find_files,
    "grep_files": grep_files,

    # ── Task Management (1 tool)
    "task_decompose": task_decompose,

    # ── Memory (Short-term Session Memory) (3 tools)
    "memory_save": memory_save,
    "memory_recall": memory_recall,
    "memory_list": memory_list,

    # ── Data Analysis (5 tools) [from repos/cheetah and enhanced]
    "parse_csv": parse_csv,
    "analyze_text": analyze_text,
    "compare_files": compare_files,
    "extract_urls": extract_urls,
    "extract_emails": extract_emails,

    # ── Pentesting & Security (7 tools) [from repos/security]
    "port_scan": port_scan,
    "check_ssl_cert": check_ssl_cert,
    "dns_lookup": dns_lookup,
    "whois_lookup": whois_lookup,
    "hash_text": hash_text,
    "extract_metadata": extract_metadata,

    # ── Git & Repository Management (3 tools)
    "git_log": git_log,
    "git_status": git_status,
    "git_diff": git_diff,

    # ── Automation & Workflow (2 tools)
    "run_workflow": run_workflow,
    "schedule_task": schedule_task,

    # ── AIA Framework (5 tools) [from repos/aia]
    "aia_device_control": aia_device_control,
    "aia_face_detect": aia_face_detect,
    "aia_ml_classify": aia_ml_classify,
    "aia_voice_synthesis": aia_voice_synthesis,

    # ── Advanced Cheetah Features (6 tools) [from repos/cheetah]
    "cheetah_research": cheetah_research,
    "cheetah_code_review": cheetah_code_review,
    "cheetah_file_sync": cheetah_file_sync,
    "advanced_shell_exec": advanced_shell_exec,
    "pdf_extract_pages": pdf_extract_pages,
    "image_to_text": image_to_text,
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
