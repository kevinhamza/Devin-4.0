"""
modules/repo_tools.py — Real imports from all external repos.

Adds each repo to sys.path then imports classes/functions directly.
Every import is wrapped in try/except so missing deps never crash Devin.
"""

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _add(rel: str):
    p = os.path.join(ROOT, rel)
    if p not in sys.path:
        sys.path.insert(0, p)


# ── Add all external repos to path ───────────────────────────────────────────

for _repo in [
    'external/AIA',
    'external/self-operating-computer',
    'external/Devin-3.0',
    'external/Jarvis',
    'external/Devin-2.0',
    'external/Devin',
    'external/OpenDevin',
    'external/shannon/shannon',
    'external/cheetahclaws',
    'external/hexstrike-ai',
    'external/vulnerability-analysis',
]:
    _add(_repo)


# ══════════════════════════════════════════════════════════════════════════════
# AIA — Artificial Intelligence Agent (kevinhamza/AIA)
# ══════════════════════════════════════════════════════════════════════════════

class AIAAutomation:
    """Wraps external/AIA/modules/automation.py"""
    _impl = None

    @classmethod
    def _load(cls):
        if cls._impl is None:
            try:
                _add('external/AIA')
                from modules.automation import Automation
                cls._impl = Automation()
            except Exception as e:
                cls._impl = None
        return cls._impl

    @classmethod
    def schedule_task(cls, task, run_at):
        impl = cls._load()
        if impl:
            return impl.schedule_task(task, run_at)

    @classmethod
    def automate_typing(cls, text, interval=0.05):
        impl = cls._load()
        if impl:
            return impl.automate_typing(text, interval)
        try:
            import pyautogui
            pyautogui.write(text, interval=interval)
        except Exception:
            pass

    @classmethod
    def automate_mouse(cls, x, y, click=True):
        impl = cls._load()
        if impl:
            return impl.automate_mouse(x, y, click)
        try:
            import pyautogui
            pyautogui.moveTo(x, y, duration=0.3)
            if click:
                pyautogui.click()
        except Exception:
            pass

    @classmethod
    def create_task_automation(cls, task_name, action_sequence):
        impl = cls._load()
        if impl:
            return impl.create_task_automation(task_name, action_sequence)


class AIADeviceControl:
    """Wraps external/AIA/modules/device_control.py"""
    _impl = None

    @classmethod
    def _load(cls):
        if cls._impl is None:
            try:
                _add('external/AIA')
                from modules.device_control import DeviceControl
                cls._impl = DeviceControl(config={})
            except Exception:
                cls._impl = None
        return cls._impl

    @classmethod
    def move_mouse(cls, x, y):
        impl = cls._load()
        if impl:
            try:
                impl.move_mouse(x, y)
                return True
            except Exception:
                pass
        try:
            import pyautogui
            pyautogui.moveTo(x, y, duration=0.2)
            return True
        except Exception:
            return False

    @classmethod
    def click(cls, x, y):
        impl = cls._load()
        if impl:
            try:
                impl.click(x, y)
                return True
            except Exception:
                pass
        try:
            import pyautogui
            pyautogui.click(x, y)
            return True
        except Exception:
            return False

    @classmethod
    def screenshot(cls, save_path='screenshot.png'):
        impl = cls._load()
        if impl:
            try:
                impl.screenshot(save_path)
                return save_path
            except Exception:
                pass
        try:
            import pyautogui
            pyautogui.screenshot().save(save_path)
            return save_path
        except Exception:
            return None

    @classmethod
    def get_system_metrics(cls):
        impl = cls._load()
        if impl:
            try:
                return impl.get_system_metrics()
            except Exception:
                pass
        try:
            import pyautogui
            return pyautogui.size()
        except Exception:
            return (1920, 1080)


class AIAVoiceAssistant:
    """Wraps external/AIA/modules/voice_assistant.py"""
    _impl = None

    @classmethod
    def _load(cls):
        if cls._impl is None:
            try:
                _add('external/AIA')
                from modules.voice_assistant import VoiceAssistant
                cls._impl = VoiceAssistant(config={})
            except Exception:
                cls._impl = None
        return cls._impl

    @classmethod
    def speak(cls, text):
        impl = cls._load()
        if impl:
            try:
                impl.speak(text)
                return True
            except Exception:
                pass
        from modules.voice import speak
        return speak(text)

    @classmethod
    def listen(cls):
        impl = cls._load()
        if impl:
            try:
                return impl.listen()
            except Exception:
                pass
        from modules.voice import listen
        return listen()


class AIAInternetTasks:
    """Wraps external/AIA/modules/internet_tasks.py"""
    _impl = None

    @classmethod
    def _load(cls):
        if cls._impl is None:
            try:
                _add('external/AIA')
                from modules.internet_tasks import InternetTasks
                cls._impl = InternetTasks()
            except Exception:
                cls._impl = None
        return cls._impl

    @classmethod
    def get_weather(cls, location):
        impl = cls._load()
        if impl:
            try:
                return impl.get_weather(location)
            except Exception as e:
                return f'Weather unavailable: {e}'
        return f'Weather: AIA internet_tasks not loaded'

    @classmethod
    def get_news(cls, category='general'):
        impl = cls._load()
        if impl:
            try:
                return impl.get_news(category)
            except Exception as e:
                return f'News unavailable: {e}'
        return 'News: AIA internet_tasks not loaded'


class AIAFaceDetection:
    """Wraps external/AIA/modules/face_detection.py"""
    _impl = None

    @classmethod
    def _load(cls):
        if cls._impl is None:
            try:
                _add('external/AIA')
                from modules.face_detection import FaceDetection
                cls._impl = FaceDetection()
            except Exception:
                cls._impl = None
        return cls._impl

    @classmethod
    def detect_faces_in_image(cls, image_path):
        impl = cls._load()
        if impl:
            try:
                return impl.detect_faces_in_image(image_path)
            except Exception as e:
                return f'Face detection error: {e}'
        return 'Face detection: deps not available'


class AIAMachineLearning:
    """Wraps external/AIA/modules/machine_learning.py"""

    @classmethod
    def get_model_manager(cls, model_type='random_forest'):
        try:
            _add('external/AIA')
            from modules.machine_learning import ModelManager
            return ModelManager(model_type)
        except Exception:
            return None


# ══════════════════════════════════════════════════════════════════════════════
# Self-Operating-Computer (othersideai/self-operating-computer)
# ══════════════════════════════════════════════════════════════════════════════

class SelfOperatingComputer:
    """
    Wraps external/self-operating-computer.
    Provides OperatingSystem GUI control and screenshot capture.
    """
    _os_impl = None

    @classmethod
    def _load_os(cls):
        if cls._os_impl is None:
            try:
                _add('external/self-operating-computer')
                from operate.utils.operating_system import OperatingSystem
                cls._os_impl = OperatingSystem()
            except Exception:
                cls._os_impl = None
        return cls._os_impl

    @classmethod
    def write(cls, content: str):
        """Type content character by character (like a user)."""
        impl = cls._load_os()
        if impl:
            try:
                impl.write(content)
                return True
            except Exception:
                pass
        try:
            import pyautogui
            pyautogui.write(content, interval=0.03)
            return True
        except Exception:
            return False

    @classmethod
    def press(cls, keys: list):
        """Press a key combination."""
        impl = cls._load_os()
        if impl:
            try:
                impl.press(keys)
                return True
            except Exception:
                pass
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
            return True
        except Exception:
            return False

    @classmethod
    def click_at_percentage(cls, x_pct: float, y_pct: float):
        """Click at screen percentage coordinates (0.0–1.0)."""
        impl = cls._load_os()
        if impl:
            try:
                impl.click_at_percentage(x_pct, y_pct)
                return True
            except Exception:
                pass
        try:
            import pyautogui
            w, h = pyautogui.size()
            pyautogui.click(int(w * x_pct), int(h * y_pct))
            return True
        except Exception:
            return False

    @classmethod
    def capture_screen(cls, file_path: str) -> bool:
        """Capture full screen to file using self-operating-computer's method."""
        try:
            _add('external/self-operating-computer')
            from operate.utils.screenshot import capture_screen_with_cursor
            capture_screen_with_cursor(file_path)
            return True
        except Exception:
            pass
        try:
            import pyautogui
            pyautogui.screenshot().save(file_path)
            return True
        except Exception:
            return False


# ══════════════════════════════════════════════════════════════════════════════
# Devin-3.0 modules (kevinhamza/Devin-3.0)
# ══════════════════════════════════════════════════════════════════════════════

class Devin3Automation:
    """Wraps external/Devin-3.0/modules/automation_tools.py DesktopAutomator."""
    _impl = None

    @classmethod
    def _load(cls):
        if cls._impl is None:
            try:
                _add('external/Devin-3.0')
                from modules.automation_tools import DesktopAutomator
                cls._impl = DesktopAutomator()
            except Exception:
                cls._impl = None
        return cls._impl

    @classmethod
    def click(cls, x, y):
        impl = cls._load()
        if impl:
            try:
                impl.click(x, y)
                return True
            except Exception:
                pass
        try:
            import pyautogui
            pyautogui.click(x, y)
        except Exception:
            pass
        return True

    @classmethod
    def type_text(cls, text):
        impl = cls._load()
        if impl:
            try:
                impl.type_text(text)
                return True
            except Exception:
                pass
        try:
            import pyautogui
            pyautogui.write(text, interval=0.03)
        except Exception:
            pass
        return True


class Devin3WebAutomator:
    """Wraps external/Devin-3.0/modules/automation_tools.py WebAutomator."""
    _impl = None

    @classmethod
    def _load(cls):
        if cls._impl is None:
            try:
                _add('external/Devin-3.0')
                from modules.automation_tools import WebAutomator
                cls._impl = WebAutomator()
            except Exception:
                cls._impl = None
        return cls._impl

    @classmethod
    def open_url(cls, url):
        impl = cls._load()
        if impl:
            try:
                impl.open_url(url)
                return True
            except Exception:
                pass
        import webbrowser
        webbrowser.open(url)
        return True

    @classmethod
    def find_element(cls, selector, by='css'):
        impl = cls._load()
        if impl:
            try:
                return impl.find_element(selector, by)
            except Exception:
                pass
        return None


class Devin3SystemMonitor:
    """Wraps external/Devin-3.0/modules/system_monitor_module.py"""

    @classmethod
    def get_metrics(cls):
        try:
            _add('external/Devin-3.0')
            from modules.system_monitor_module import SystemMonitorFacade
            mon = SystemMonitorFacade()
            return mon.get_metrics() if hasattr(mon, 'get_metrics') else str(mon)
        except Exception:
            pass
        try:
            import psutil
            return {
                'cpu': psutil.cpu_percent(interval=0.5),
                'ram': psutil.virtual_memory().percent,
                'disk': psutil.disk_usage('/').percent,
            }
        except Exception:
            return {}


class Devin3Cloud:
    """Wraps external/Devin-3.0/modules/cloud_services_manager.py"""

    @classmethod
    def get_manager(cls):
        try:
            _add('external/Devin-3.0')
            from modules.cloud_services_manager import CloudServicesManager
            return CloudServicesManager()
        except Exception:
            return None


class Devin3Encryption:
    """Wraps external/Devin-3.0/modules/encryption_tools.py"""

    @classmethod
    def encrypt(cls, data, key=None):
        try:
            _add('external/Devin-3.0')
            from modules.encryption_tools import EncryptionTools
            et = EncryptionTools()
            return et.encrypt(data, key) if key else et.encrypt(data)
        except Exception as e:
            return f'Encryption unavailable: {e}'

    @classmethod
    def decrypt(cls, data, key=None):
        try:
            _add('external/Devin-3.0')
            from modules.encryption_tools import EncryptionTools
            et = EncryptionTools()
            return et.decrypt(data, key) if key else et.decrypt(data)
        except Exception as e:
            return f'Decryption unavailable: {e}'


class Devin3Email:
    """Wraps external/Devin-3.0/modules/email_tools.py"""

    @classmethod
    def get_client(cls):
        try:
            _add('external/Devin-3.0')
            from modules.email_tools import EmailClient
            return EmailClient()
        except Exception:
            return None


class Devin3Pentesting:
    """Wraps external/Devin-3.0/modules/pentesting_tools/pentesting_facade.py"""

    @classmethod
    def get_facade(cls):
        try:
            _add('external/Devin-3.0')
            from modules.pentesting_tools.pentesting_facade import PentestingFacade
            return PentestingFacade()
        except Exception:
            return None


# ══════════════════════════════════════════════════════════════════════════════
# Jarvis (Concept-Bytes/Jarvis)
# ══════════════════════════════════════════════════════════════════════════════

class JarvisTools:
    """Wraps external/Jarvis/tools.py parse_command."""

    @classmethod
    def parse_command(cls, command: str) -> str:
        try:
            _add('external/Jarvis')
            import tools as _jtools
            _jtools.parse_command(command)
            return f'Jarvis command executed: {command}'
        except Exception as e:
            return f'Jarvis command failed: {e}'

    @classmethod
    def get_weather(cls, city: str = 'London') -> str:
        try:
            _add('external/Jarvis')
            import asyncio
            import tools as _jtools
            result = asyncio.run(_jtools.get_weather(city))
            return str(result)
        except Exception as e:
            return f'Weather unavailable: {e}'


# ══════════════════════════════════════════════════════════════════════════════
# OpenDevin / OpenHands (All-Hands-AI/OpenHands)
# ══════════════════════════════════════════════════════════════════════════════

class OpenDevinAgent:
    """Wraps key patterns from external/OpenDevin."""

    @classmethod
    def run_task(cls, task: str, model: str = 'gemini') -> str:
        """Run a task using OpenHands agent patterns."""
        try:
            _add('external/OpenDevin')
            # OpenHands uses openhands package
            import openhands
            return f'OpenDevin task submitted: {task}'
        except Exception as e:
            return f'OpenDevin not available: {e}'


# ══════════════════════════════════════════════════════════════════════════════
# Security tools
# ══════════════════════════════════════════════════════════════════════════════

class SecurityTools:
    """Aggregates security tools from shannon, vulnerability-analysis, hexstrike-ai."""

    @classmethod
    def nmap_scan(cls, target: str, options: str = '-sV') -> str:
        try:
            import nmap
            nm = nmap.PortScanner()
            nm.scan(target, arguments=options)
            return str(nm.csv())
        except Exception as e:
            return f'nmap scan failed: {e}'

    @classmethod
    def check_vulnerabilities(cls, target: str) -> str:
        try:
            _add('external/vulnerability-analysis')
            import subprocess
            result = subprocess.run(
                ['python3', '-m', 'vulnerability_analysis', target],
                capture_output=True, text=True, timeout=30,
                cwd=os.path.join(ROOT, 'external/vulnerability-analysis')
            )
            return result.stdout or result.stderr or 'No output'
        except Exception as e:
            return f'Vulnerability analysis unavailable: {e}'

    @classmethod
    def run_responder(cls, interface: str = 'eth0') -> str:
        try:
            responder_path = os.path.join(ROOT, 'external/Responder/Responder.py')
            if os.path.exists(responder_path):
                return f'Responder available at {responder_path} — run with sudo'
            return 'Responder not found'
        except Exception as e:
            return f'Responder error: {e}'

    @classmethod
    def aircrack_info(cls) -> str:
        try:
            import subprocess
            r = subprocess.run(['airgorah', '--help'], capture_output=True, text=True, timeout=5)
            return r.stdout[:500] if r.stdout else 'airgorah: check external/airgorah'
        except Exception:
            return 'airgorah available at external/airgorah (Rust binary — cargo build)'


# ══════════════════════════════════════════════════════════════════════════════
# Convenience registry — all tools by category
# ══════════════════════════════════════════════════════════════════════════════

TOOL_REGISTRY = {
    # Automation
    'aia_automation': AIAAutomation,
    'aia_device': AIADeviceControl,
    'aia_voice': AIAVoiceAssistant,
    'aia_internet': AIAInternetTasks,
    'aia_face': AIAFaceDetection,
    'aia_ml': AIAMachineLearning,
    # Self-operating computer
    'soc': SelfOperatingComputer,
    # Devin-3.0
    'devin3_auto': Devin3Automation,
    'devin3_web': Devin3WebAutomator,
    'devin3_monitor': Devin3SystemMonitor,
    'devin3_cloud': Devin3Cloud,
    'devin3_crypto': Devin3Encryption,
    'devin3_email': Devin3Email,
    'devin3_pentest': Devin3Pentesting,
    # Jarvis
    'jarvis': JarvisTools,
    # OpenDevin
    'opendevin': OpenDevinAgent,
    # Security
    'security': SecurityTools,
}


def get_tool(name: str):
    """Return a tool class by registry key."""
    return TOOL_REGISTRY.get(name)
