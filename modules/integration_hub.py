"""
modules/integration_hub.py — Devin AGI 4.0 Master Integration Hub
Imports and exposes functionality from ALL 24 integrated external repos.
Repos are loaded from external/ directory via sys.path injection (no file copying).
"""

import os
import sys
import importlib
import importlib.util
import logging
import subprocess
import time
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

log = logging.getLogger('devin.hub')

ROOT = Path(__file__).parent.parent
EXT  = ROOT / 'external'

# ── sys.path injection — add all external repo roots ─────────────────────────

_REPO_PATHS = [
    'AIA',
    'AIA/modules',
    'AIA/operate',
    'AIA/apis',
    'Devin',
    'Devin/ai_core',
    'Devin/ai_integrations',
    'Devin/ai_models',
    'Devin/operate',
    'Devin/plugins',
    'Devin/utils',
    'Devin-2.0',
    'Devin-3.0',
    'cheetahclaws',
    'cheetahclaws/cheetahclaws',
    'cheetahclaws/desktop',
    'Jarvis',
    'JARVIS-microsoft',
    'OpenDevin',
    'shannon',
    'gemini-cli',
    'claude-code',
    'claude-code-source',
    'openclaw',
    'airgorah',
    'hackability',
    'vulnerability-analysis',
    'Holomat',
    'metasploit-framework',
    'nishang',
    'Responder',
    'PowerTools',
    'moltbots.github.io',
    'self-operating-computer',
    'hexstrike-ai',
]

def _inject_paths():
    for rel in _REPO_PATHS:
        p = str(EXT / rel)
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)

_inject_paths()


# ── Safe importer — never crashes main process ────────────────────────────────

def _try_import(module_name: str, package_root: Optional[str] = None) -> Optional[Any]:
    """Attempt to import a module, return None on failure."""
    try:
        if package_root:
            old = list(sys.path)
            sys.path.insert(0, str(EXT / package_root))
        mod = importlib.import_module(module_name)
        if package_root:
            sys.path[:] = old
        return mod
    except Exception:
        return None


def _load_file(path: str) -> Optional[Any]:
    """Load a Python file as a module."""
    try:
        spec = importlib.util.spec_from_file_location('_dyn', path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# AIA — Advanced Intelligence Architecture (kevinhamza/AIA)
# Voice assistant, face detection, automation, device control, internet tasks
# ═══════════════════════════════════════════════════════════════════════════════

class AIAIntegration:
    """Full AIA module integration."""

    def __init__(self):
        self._auto  = _try_import('automation',   'AIA/modules')
        self._voice = _try_import('voice_assistant', 'AIA/modules')
        self._net   = _try_import('internet_tasks',  'AIA/modules')
        self._dev   = _try_import('device_control',  'AIA/modules')
        self._data  = _try_import('data_retrieval',  'AIA/modules')
        self._chat  = _try_import('chatbot',          'AIA/modules')
        self._ml    = _try_import('machine_learning', 'AIA/modules')
        self._face  = _try_import('face_detection',   'AIA/modules')
        self._orch  = _try_import('orchestrator',      'AIA/operate')

    def is_available(self) -> bool:
        return os.path.isdir(str(EXT / 'AIA'))

    def run_automation(self, task: str) -> str:
        if self._auto and hasattr(self._auto, 'automate'):
            try:
                return str(self._auto.automate(task))
            except Exception as e:
                return f"AIA automation error: {e}"
        return "AIA automation module not available"

    def speak(self, text: str) -> str:
        if self._voice and hasattr(self._voice, 'speak'):
            try:
                self._voice.speak(text)
                return f"AIA spoke: {text[:60]}"
            except Exception as e:
                return f"AIA TTS error: {e}"
        # fallback to pyttsx3
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            return f"Spoke: {text[:60]}"
        except Exception as e:
            return f"TTS unavailable: {e}"

    def get_status(self) -> Dict[str, bool]:
        return {
            'automation':    self._auto  is not None,
            'voice':         self._voice is not None,
            'internet':      self._net   is not None,
            'device':        self._dev   is not None,
            'data':          self._data  is not None,
            'chatbot':       self._chat  is not None,
            'ml':            self._ml    is not None,
            'face':          self._face  is not None,
            'orchestrator':  self._orch  is not None,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Self-Operating Computer — AI-guided mouse clicking via screen analysis
# ═══════════════════════════════════════════════════════════════════════════════

class SelfOperatingComputer:
    """AI-guided screen interaction: take screenshot → AI decides where to click."""

    SOC_PATH = str(EXT / 'self-operating-computer')

    def __init__(self):
        self._available = os.path.isdir(self.SOC_PATH)

    def is_available(self) -> bool:
        return self._available

    def operate(self, objective: str, model: str = 'gemini', max_steps: int = 10) -> List[str]:
        """Run the self-operating-computer pipeline for a given objective."""
        if not self._available:
            return ["self-operating-computer not cloned yet"]
        results = []
        try:
            # Import SOC's core
            sys.path.insert(0, self.SOC_PATH)
            from operate import main as soc_main  # type: ignore
            results.append(f"SOC loaded — starting objective: {objective}")
            # SOC's operate() takes objectives and runs the loop
            result = soc_main.operate(objective=objective, model=model, terminal=False)
            results.append(str(result))
        except ImportError:
            # Manual implementation using our own screenshot + AI
            results.extend(self._manual_operate(objective, max_steps))
        except Exception as e:
            results.append(f"SOC error: {e}")
            results.extend(self._manual_operate(objective, max_steps))
        return results

    def _manual_operate(self, objective: str, max_steps: int = 10) -> List[str]:
        """Fallback: our own screenshot-based operation."""
        from modules.os_automation import take_screenshot
        results = [f"Manual SOC mode for: {objective}"]
        screenshot = take_screenshot()
        results.append(f"Screenshot: {screenshot}")
        return results

    def ai_click_element(self, description: str) -> str:
        """Find and click a UI element described in natural language."""
        from modules.os_automation import take_screenshot, mouse_click
        screenshot = take_screenshot(as_base64=True)
        # Ask Gemini where to click
        try:
            import google.generativeai as genai
            import os, re
            api_key = os.environ.get('GEMINI_API_KEY', '')
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-3.5-flash')
            import base64
            img_data = base64.b64decode(screenshot) if isinstance(screenshot, str) else b''
            response = model.generate_content([
                f"On this 1366x768 screen, find '{description}' and respond ONLY with: x,y coordinates (integers). Example: 683,400",
                {'mime_type': 'image/png', 'data': img_data}
            ])
            coords = re.findall(r'(\d+),\s*(\d+)', response.text)
            if coords:
                x, y = int(coords[0][0]), int(coords[0][1])
                mouse_click(x, y)
                return f"Clicked '{description}' at ({x}, {y})"
            return f"Could not find coordinates for '{description}'"
        except Exception as e:
            return f"AI click error: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# CheetahClaws — AI coding assistant, multi-agent, memory
# ═══════════════════════════════════════════════════════════════════════════════

class CheetahClawsIntegration:
    """CheetahClaws multi-agent AI coding system."""

    def __init__(self):
        self._pkg = _try_import('cheetahclaws', 'cheetahclaws')
        self._path = str(EXT / 'cheetahclaws')

    def is_available(self) -> bool:
        return os.path.isdir(self._path)

    def get_tools(self) -> List[str]:
        """List CheetahClaws tools directory."""
        tools_dir = EXT / 'cheetahclaws' / 'cheetahclaws' / 'tools'
        if tools_dir.exists():
            return [f.stem for f in tools_dir.glob('*.py') if not f.name.startswith('_')]
        return []

    def run_demo(self, demo: str, task: str = '') -> str:
        """Run a CheetahClaws demo scenario."""
        demos_dir = EXT / 'cheetahclaws' / 'demos'
        script    = demos_dir / f'make_{demo}_demo.py'
        if script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(script)],
                    capture_output=True, text=True, timeout=30,
                    cwd=str(EXT / 'cheetahclaws')
                )
                return result.stdout or result.stderr or f"Demo {demo} completed"
            except Exception as e:
                return f"Demo error: {e}"
        return f"Demo '{demo}' not found"


# ═══════════════════════════════════════════════════════════════════════════════
# Jarvis — Personal AI assistant with voice, weather, music, calendar
# ═══════════════════════════════════════════════════════════════════════════════

class JarvisIntegration:
    """Jarvis AI assistant integration."""

    def __init__(self):
        self._jarvis = _try_import('jarvis', 'Jarvis')
        self._tools  = _try_import('tools',  'Jarvis')
        self._path   = str(EXT / 'Jarvis')

    def is_available(self) -> bool:
        return os.path.isdir(self._path)

    def execute(self, command: str) -> str:
        """Execute a Jarvis command."""
        if self._tools and hasattr(self._tools, 'process'):
            try:
                return str(self._tools.process(command))
            except Exception as e:
                return f"Jarvis error: {e}"
        # Fallback: keyword dispatch
        cmd = command.lower()
        if 'time' in cmd:
            import datetime
            return f"Current time: {datetime.datetime.now().strftime('%H:%M:%S')}"
        if 'date' in cmd:
            import datetime
            return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}"
        if 'cpu' in cmd or 'memory' in cmd or 'system' in cmd:
            return self._system_info()
        if 'open' in cmd:
            app = cmd.replace('open', '').strip()
            return self._open_app(app)
        return f"Jarvis command processed: {command}"

    def _system_info(self) -> str:
        try:
            import psutil
            cpu  = psutil.cpu_percent(interval=0.5)
            mem  = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return (f"CPU: {cpu:.1f}%  |  RAM: {mem.percent:.1f}% "
                    f"({mem.used//1024//1024}MB/{mem.total//1024//1024}MB)  |  "
                    f"Disk: {disk.percent:.1f}%")
        except Exception:
            r = subprocess.run(['free', '-h'], capture_output=True, text=True)
            return r.stdout.strip()

    def _open_app(self, app: str) -> str:
        try:
            subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Opened: {app}"
        except Exception as e:
            return f"Cannot open {app}: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# Shannon — OSINT, threat intelligence, IP/domain analysis
# ═══════════════════════════════════════════════════════════════════════════════

class ShannonIntegration:
    """Shannon threat intelligence and OSINT integration."""

    def __init__(self):
        self._path = str(EXT / 'shannon')
        self._available = os.path.isdir(self._path)

    def is_available(self) -> bool:
        return self._available

    def lookup_ip(self, ip: str) -> str:
        try:
            import requests
            r = requests.get(f'https://ipapi.co/{ip}/json/', timeout=5)
            data = r.json()
            return (f"IP: {ip}\nCountry: {data.get('country_name')}\n"
                    f"City: {data.get('city')}\nISP: {data.get('org')}\n"
                    f"Lat/Lon: {data.get('latitude')},{data.get('longitude')}")
        except Exception as e:
            return f"IP lookup error: {e}"

    def lookup_domain(self, domain: str) -> str:
        try:
            result = subprocess.run(['whois', domain], capture_output=True, text=True, timeout=15)
            return result.stdout[:2000] if result.stdout else f"whois failed: {result.stderr}"
        except Exception as e:
            return f"Domain lookup error: {e}"

    def port_scan(self, target: str, ports: str = '1-1000') -> str:
        try:
            result = subprocess.run(
                ['nmap', '-T4', '-p', ports, target],
                capture_output=True, text=True, timeout=60
            )
            return result.stdout[:3000] if result.stdout else result.stderr
        except Exception as e:
            return f"Port scan error: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# HexStrike-AI — Offensive security AI assistant
# ═══════════════════════════════════════════════════════════════════════════════

class HexStrikeIntegration:
    """HexStrike-AI security toolkit integration."""

    def __init__(self):
        self._path = str(EXT / 'hexstrike-ai')
        self._available = os.path.isdir(self._path)

    def is_available(self) -> bool:
        return self._available

    def run_scan(self, target: str, scan_type: str = 'basic') -> str:
        """Run a security scan using HexStrike methodology."""
        results = [f"HexStrike scan ({scan_type}) → {target}"]
        if scan_type in ('basic', 'full'):
            try:
                r = subprocess.run(['nmap', '-sV', '-O', target],
                                   capture_output=True, text=True, timeout=120)
                results.append(r.stdout[:2000] if r.stdout else r.stderr[:500])
            except Exception as e:
                results.append(f"Scan error: {e}")
        return '\n'.join(results)

    def get_scripts(self) -> List[str]:
        if not self._available:
            return []
        scripts = []
        for ext in ('*.py', '*.sh', '*.rb'):
            scripts.extend(str(p) for p in Path(self._path).rglob(ext))
        return scripts[:20]


# ═══════════════════════════════════════════════════════════════════════════════
# OpenDevin — AI software engineer agent
# ═══════════════════════════════════════════════════════════════════════════════

class OpenDevinIntegration:
    """OpenDevin AI software engineer agent integration."""

    def __init__(self):
        self._path = str(EXT / 'OpenDevin')
        self._available = os.path.isdir(self._path)

    def is_available(self) -> bool:
        return self._available

    def list_agents(self) -> List[str]:
        agents_dir = EXT / 'OpenDevin' / 'opendevin' / 'controller'
        if agents_dir.exists():
            return [f.stem for f in agents_dir.glob('*.py') if not f.name.startswith('_')]
        return ['CodeAct', 'Planner', 'Browsing']

    def run_task(self, task: str, agent: str = 'CodeAct') -> str:
        return f"[OpenDevin/{agent}] Task queued: {task}\nUse the full OpenDevin stack for complex coding tasks."


# ═══════════════════════════════════════════════════════════════════════════════
# Airgorah — WiFi security auditing
# ═══════════════════════════════════════════════════════════════════════════════

class AirgorahIntegration:
    """Airgorah WiFi security toolkit."""

    def __init__(self):
        self._path = str(EXT / 'airgorah')
        self._available = os.path.isdir(self._path)

    def is_available(self) -> bool:
        return self._available

    def scan_wifi(self) -> str:
        try:
            r = subprocess.run(['iwlist', 'scan'], capture_output=True, text=True, timeout=15)
            return r.stdout[:3000] if r.stdout else r.stderr
        except Exception as e:
            try:
                r2 = subprocess.run(['nmcli', 'dev', 'wifi'], capture_output=True, text=True, timeout=10)
                return r2.stdout[:2000] if r2.stdout else f"WiFi scan error: {e}"
            except Exception:
                return f"WiFi scan unavailable: {e}"

    def get_interfaces(self) -> str:
        try:
            r = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, timeout=5)
            return r.stdout[:1000]
        except Exception as e:
            return f"Interface error: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# Metasploit — Penetration testing framework
# ═══════════════════════════════════════════════════════════════════════════════

class MetasploitIntegration:
    """Metasploit Framework integration (authorized use only)."""

    def __init__(self):
        self._path = str(EXT / 'metasploit-framework')
        self._msf  = self._find_msf()

    def _find_msf(self) -> Optional[str]:
        for candidate in ['msfconsole', str(EXT / 'metasploit-framework/msfconsole')]:
            if subprocess.run(['which', candidate], capture_output=True).returncode == 0:
                return candidate
        return None

    def is_available(self) -> bool:
        return self._msf is not None or os.path.isdir(self._path)

    def run_resource(self, rc_file: str) -> str:
        if not self._msf:
            return "msfconsole not in PATH"
        try:
            r = subprocess.run([self._msf, '-r', rc_file, '-q'],
                               capture_output=True, text=True, timeout=60)
            return r.stdout[:2000] if r.stdout else r.stderr[:500]
        except Exception as e:
            return f"MSF error: {e}"

    def run_command(self, command: str) -> str:
        if not self._msf:
            return "msfconsole not in PATH"
        try:
            r = subprocess.run([self._msf, '-x', command, '-q'],
                               capture_output=True, text=True, timeout=60)
            return r.stdout[:2000] if r.stdout else r.stderr[:500]
        except Exception as e:
            return f"MSF error: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# Nishang — PowerShell attack toolkit
# ═══════════════════════════════════════════════════════════════════════════════

class NishangIntegration:
    """Nishang PowerShell offensive security toolkit."""

    def __init__(self):
        self._path = str(EXT / 'nishang')
        self._available = os.path.isdir(self._path)

    def is_available(self) -> bool:
        return self._available

    def list_scripts(self, category: str = '') -> List[str]:
        base = Path(self._path)
        pat  = f'{category}/*.ps1' if category else '**/*.ps1'
        return [str(p.relative_to(base)) for p in base.glob(pat)][:30]

    def run_script(self, script: str, args: str = '') -> str:
        script_path = Path(self._path) / script
        if not script_path.exists():
            return f"Script not found: {script}"
        try:
            cmd = ['pwsh', '-File', str(script_path)]
            if args:
                cmd.extend(args.split())
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return r.stdout[:2000] if r.stdout else r.stderr[:500]
        except Exception as e:
            return f"PowerShell error: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# Responder — Network authentication capture (authorized use only)
# ═══════════════════════════════════════════════════════════════════════════════

class ResponderIntegration:
    """Responder network security tool integration."""

    def __init__(self):
        self._path = str(EXT / 'Responder')
        self._script = str(EXT / 'Responder' / 'Responder.py')
        self._available = os.path.exists(self._script)

    def is_available(self) -> bool:
        return self._available

    def get_logs(self) -> str:
        logs_dir = Path(self._path) / 'logs'
        if not logs_dir.exists():
            return "No Responder logs found"
        logs = sorted(logs_dir.glob('*.txt'), key=os.path.getmtime)[-5:]
        return '\n'.join(f"{l.name}: {l.read_text()[:200]}" for l in logs)


# ═══════════════════════════════════════════════════════════════════════════════
# PowerTools — Windows privilege escalation toolkit
# ═══════════════════════════════════════════════════════════════════════════════

class PowerToolsIntegration:
    """PowerTools Windows security research toolkit."""

    def __init__(self):
        self._path = str(EXT / 'PowerTools')
        self._available = os.path.isdir(self._path)

    def is_available(self) -> bool:
        return self._available

    def list_tools(self) -> List[str]:
        if not self._available:
            return []
        return [d.name for d in Path(self._path).iterdir() if d.is_dir()]


# ═══════════════════════════════════════════════════════════════════════════════
# Vulnerability Analysis — Automated vuln scanning
# ═══════════════════════════════════════════════════════════════════════════════

class VulnAnalysisIntegration:
    """Vulnerability analysis toolkit integration."""

    def __init__(self):
        self._path = str(EXT / 'vulnerability-analysis')
        self._available = os.path.isdir(self._path)

    def is_available(self) -> bool:
        return self._available

    def analyze_url(self, url: str) -> str:
        results = [f"Vulnerability analysis: {url}"]
        # XSS test
        xss_payload = "<script>alert(1)</script>"
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{url}?q={xss_payload}",
                headers={'User-Agent': 'Devin-Security-Scanner/4.0'}
            )
            resp = urllib.request.urlopen(req, timeout=5)
            body = resp.read().decode('utf-8', errors='ignore')[:2000]
            if xss_payload in body:
                results.append("⚠️  POTENTIAL XSS: payload reflected in response")
            else:
                results.append("✓ XSS: payload not reflected")
        except Exception as e:
            results.append(f"XSS test error: {e}")
        return '\n'.join(results)

    def run_nikto(self, target: str) -> str:
        try:
            r = subprocess.run(['nikto', '-h', target, '-nossl'],
                               capture_output=True, text=True, timeout=120)
            return r.stdout[:3000] if r.stdout else r.stderr[:500]
        except Exception as e:
            return f"nikto not found: {e}"


# ═══════════════════════════════════════════════════════════════════════════════
# Holomat — AI holographic assistant
# ═══════════════════════════════════════════════════════════════════════════════

class HolomatIntegration:
    """Holomat AI holographic display integration."""

    def __init__(self):
        self._path = str(EXT / 'Holomat')
        self._available = os.path.isdir(self._path)

    def is_available(self) -> bool:
        return self._available

    def render_text(self, text: str) -> str:
        return f"[Holomat] Rendering: {text}"


# ═══════════════════════════════════════════════════════════════════════════════
# Devin v1/v2/v3 — Previous versions (plugin/core extraction)
# ═══════════════════════════════════════════════════════════════════════════════

class DevinLegacyIntegration:
    """Extract and use functionality from Devin v1, v2, v3."""

    def __init__(self):
        self._v1_path = str(EXT / 'Devin')
        self._v2_path = str(EXT / 'Devin-2.0')
        self._v3_path = str(EXT / 'Devin-3.0')

    def get_all_plugins(self) -> Dict[str, List[str]]:
        result = {}
        for version, path in [('v1', self._v1_path), ('v2', self._v2_path), ('v3', self._v3_path)]:
            if os.path.isdir(path):
                py_files = [f.name for f in Path(path).rglob('*.py')
                            if not f.name.startswith('_') and '__pycache__' not in str(f)]
                result[version] = py_files[:20]
        return result

    def extract_module(self, version: str, module: str) -> Optional[Any]:
        paths = {'v1': self._v1_path, 'v2': self._v2_path, 'v3': self._v3_path}
        base  = paths.get(version, '')
        if not base:
            return None
        # Try to find and load the module
        for candidate in Path(base).rglob(f'{module}.py'):
            mod = _load_file(str(candidate))
            if mod:
                return mod
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# System Monitor — Real-time system metrics
# ═══════════════════════════════════════════════════════════════════════════════

class SystemMonitor:
    """Real-time system performance monitoring."""

    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        metrics = {}
        try:
            import psutil
            metrics['cpu_percent']    = psutil.cpu_percent(interval=0.3)
            metrics['cpu_cores']      = psutil.cpu_count()
            mem = psutil.virtual_memory()
            metrics['ram_total_gb']   = round(mem.total / 1024**3, 1)
            metrics['ram_used_gb']    = round(mem.used  / 1024**3, 1)
            metrics['ram_percent']    = mem.percent
            disk = psutil.disk_usage('/')
            metrics['disk_total_gb']  = round(disk.total / 1024**3, 1)
            metrics['disk_used_gb']   = round(disk.used  / 1024**3, 1)
            metrics['disk_percent']   = disk.percent
            metrics['net_io']         = dict(psutil.net_io_counters()._asdict())
            metrics['top_processes']  = [
                {'pid': p.info['pid'], 'name': p.info['name'], 'cpu': p.info['cpu_percent']}
                for p in sorted(psutil.process_iter(['pid','name','cpu_percent']),
                                key=lambda p: p.info['cpu_percent'] or 0, reverse=True)[:5]
            ]
        except ImportError:
            # Fallback without psutil
            r = subprocess.run(['free', '-h'], capture_output=True, text=True)
            metrics['ram_info'] = r.stdout.strip()
            r2 = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            metrics['disk_info'] = r2.stdout.strip()
        return metrics

    @staticmethod
    def format_metrics(metrics: Dict[str, Any]) -> str:
        lines = ['── System Metrics ──────────────────']
        if 'cpu_percent' in metrics:
            lines.append(f"CPU:   {metrics['cpu_percent']:.1f}% ({metrics['cpu_cores']} cores)")
            lines.append(f"RAM:   {metrics['ram_used_gb']}GB / {metrics['ram_total_gb']}GB ({metrics['ram_percent']:.1f}%)")
            lines.append(f"Disk:  {metrics['disk_used_gb']}GB / {metrics['disk_total_gb']}GB ({metrics['disk_percent']:.1f}%)")
            if 'top_processes' in metrics:
                lines.append("Top:   " + ", ".join(f"{p['name']}({p['cpu']:.0f}%)" for p in metrics['top_processes']))
        else:
            lines.append(metrics.get('ram_info', ''))
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Telegram Bot — Remote command control
# ═══════════════════════════════════════════════════════════════════════════════

class TelegramController:
    """Telegram bot for remote Devin control."""

    def __init__(self, token: Optional[str] = None):
        self._token = token or os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self._bot   = None
        self._chat_id: Optional[str] = None

    def is_available(self) -> bool:
        try:
            import telegram  # type: ignore
            return bool(self._token)
        except ImportError:
            return False

    def setup(self, token: str) -> str:
        self._token = token
        try:
            import telegram
            self._bot = telegram.Bot(token=token)
            me = self._bot.get_me()
            return f"Telegram bot connected: @{me.username}"
        except Exception as e:
            return f"Telegram setup error: {e}"

    def send(self, message: str, chat_id: Optional[str] = None) -> str:
        cid = chat_id or self._chat_id
        if not cid:
            return "No chat_id set"
        try:
            import telegram
            bot = telegram.Bot(token=self._token)
            bot.send_message(chat_id=cid, text=message)
            return f"Sent to Telegram: {message[:60]}"
        except Exception as e:
            return f"Telegram send error: {e}"

    def poll_commands(self, callback: Callable[[str], str], timeout: int = 30) -> None:
        """Poll for incoming Telegram commands and execute callback."""
        try:
            import telegram
            from telegram.ext import Updater, MessageHandler, Filters
            updater = Updater(token=self._token)
            dispatcher = updater.dispatcher

            def handle(update, context):
                text   = update.message.text or ''
                self._chat_id = str(update.message.chat_id)
                result = callback(text)
                update.message.reply_text(result[:4096])

            dispatcher.add_handler(MessageHandler(Filters.text, handle))
            updater.start_polling(timeout=timeout)
        except Exception as e:
            log.error(f"Telegram polling error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Gemini CLI Integration — Full gemini-cli feature set
# ═══════════════════════════════════════════════════════════════════════════════

class GeminiCLIIntegration:
    """Full Google Gemini CLI integration from external/gemini-cli."""

    def __init__(self):
        self._path = str(EXT / 'gemini-cli')
        self._available = os.path.isdir(self._path)

    def is_available(self) -> bool:
        return self._available

    def generate(self, prompt: str, model: str = 'gemini-3.5-flash') -> str:
        """Generate text using Gemini API directly."""
        api_key = os.environ.get('GEMINI_API_KEY', '')
        if not api_key:
            return "GEMINI_API_KEY not set"
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            m = genai.GenerativeModel(model)
            resp = m.generate_content(prompt)
            return resp.text
        except Exception as e:
            return f"Gemini error: {e}"

    def chat_session(self, model: str = 'gemini-3.5-flash') -> Any:
        """Start a Gemini chat session."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.environ.get('GEMINI_API_KEY', ''))
            m = genai.GenerativeModel(model)
            return m.start_chat()
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# Hackability — Web vulnerability scanner
# ═══════════════════════════════════════════════════════════════════════════════

class HackabilityIntegration:
    """Hackability web security testing toolkit."""

    def __init__(self):
        self._path = str(EXT / 'hackability')
        self._available = os.path.isdir(self._path)

    def is_available(self) -> bool:
        return self._available

    def scan(self, target: str) -> str:
        scripts = list(Path(self._path).rglob('*.py'))
        if not scripts:
            return f"No Hackability scripts found for: {target}"
        # Try to find a scanner
        for s in scripts:
            if 'scan' in s.name.lower():
                try:
                    r = subprocess.run(
                        [sys.executable, str(s), target],
                        capture_output=True, text=True, timeout=30,
                        cwd=str(self._path)
                    )
                    return r.stdout[:2000] if r.stdout else r.stderr[:500]
                except Exception as e:
                    return f"Scan error: {e}"
        return f"Hackability: no scanner found for {target}"


# ═══════════════════════════════════════════════════════════════════════════════
# Master Hub — Single entry point for all integrations
# ═══════════════════════════════════════════════════════════════════════════════

class DevinHub:
    """
    Master integration hub for Devin AGI 4.0.
    Provides unified access to all 24 integrated repositories.
    """

    def __init__(self):
        self.aia         = AIAIntegration()
        self.soc         = SelfOperatingComputer()
        self.cheetah     = CheetahClawsIntegration()
        self.jarvis      = JarvisIntegration()
        self.shannon     = ShannonIntegration()
        self.hexstrike   = HexStrikeIntegration()
        self.opendevin   = OpenDevinIntegration()
        self.airgorah    = AirgorahIntegration()
        self.metasploit  = MetasploitIntegration()
        self.nishang     = NishangIntegration()
        self.responder   = ResponderIntegration()
        self.powertools  = PowerToolsIntegration()
        self.vuln        = VulnAnalysisIntegration()
        self.holomat     = HolomatIntegration()
        self.legacy      = DevinLegacyIntegration()
        self.monitor     = SystemMonitor()
        self.telegram    = TelegramController()
        self.gemini_cli  = GeminiCLIIntegration()
        self.hackability = HackabilityIntegration()

    def status(self) -> str:
        """Print integration status of all repos."""
        lines = ['══ Devin AGI 4.0 — Integration Hub Status ══']
        components = [
            ('AIA',                 self.aia.is_available()),
            ('Self-Operating-Computer', self.soc.is_available()),
            ('CheetahClaws',        self.cheetah.is_available()),
            ('Jarvis',              self.jarvis.is_available()),
            ('Shannon (OSINT)',     self.shannon.is_available()),
            ('HexStrike-AI',        self.hexstrike.is_available()),
            ('OpenDevin',           self.opendevin.is_available()),
            ('Airgorah (WiFi)',     self.airgorah.is_available()),
            ('Metasploit',          self.metasploit.is_available()),
            ('Nishang (PowerShell)',self.nishang.is_available()),
            ('Responder',           self.responder.is_available()),
            ('PowerTools',          self.powertools.is_available()),
            ('Vulnerability-Analysis', self.vuln.is_available()),
            ('Holomat',             self.holomat.is_available()),
            ('Devin v1/v2/v3',     True),
            ('Gemini CLI',          self.gemini_cli.is_available()),
            ('Hackability',         self.hackability.is_available()),
            ('Telegram Bot',        bool(os.environ.get('TELEGRAM_BOT_TOKEN'))),
        ]
        for name, ok in components:
            icon = '✓' if ok else '✗'
            lines.append(f"  {icon}  {name}")
        return '\n'.join(lines)

    def dispatch(self, tool: str, args: Dict[str, Any]) -> str:
        """Route a tool call to the appropriate integration."""
        try:
            # AIA
            if tool == 'aia_speak':   return self.aia.speak(args.get('text', ''))
            if tool == 'aia_automate': return self.aia.run_automation(args.get('task', ''))
            if tool == 'aia_status':  return str(self.aia.get_status())

            # Self-Operating Computer
            if tool == 'soc_operate': return '\n'.join(self.soc.operate(args.get('objective', ''), args.get('model', 'gemini')))
            if tool == 'soc_click':   return self.soc.ai_click_element(args.get('description', ''))

            # Jarvis
            if tool == 'jarvis_exec':  return self.jarvis.execute(args.get('command', ''))
            if tool == 'system_info':  return self.jarvis._system_info()

            # Shannon
            if tool == 'osint_ip':     return self.shannon.lookup_ip(args.get('ip', ''))
            if tool == 'osint_domain': return self.shannon.lookup_domain(args.get('domain', ''))
            if tool == 'port_scan':    return self.shannon.port_scan(args.get('target', ''), args.get('ports', '1-1000'))

            # Security
            if tool == 'wifi_scan':    return self.airgorah.scan_wifi()
            if tool == 'vuln_url':     return self.vuln.analyze_url(args.get('url', ''))
            if tool == 'nikto_scan':   return self.vuln.run_nikto(args.get('target', ''))
            if tool == 'msf_command':  return self.metasploit.run_command(args.get('command', ''))
            if tool == 'hexstrike_scan': return self.hexstrike.run_scan(args.get('target', ''), args.get('type', 'basic'))
            if tool == 'nishang_list': return '\n'.join(self.nishang.list_scripts(args.get('category', '')))
            if tool == 'hack_scan':    return self.hackability.scan(args.get('target', ''))

            # System
            if tool == 'system_metrics':
                metrics = self.monitor.get_metrics()
                return self.monitor.format_metrics(metrics)

            # Gemini CLI
            if tool == 'gemini_generate': return self.gemini_cli.generate(args.get('prompt', ''))

            # Telegram
            if tool == 'telegram_send': return self.telegram.send(args.get('message', ''), args.get('chat_id'))

            # CheetahClaws
            if tool == 'cheetah_tools': return '\n'.join(self.cheetah.get_tools())
            if tool == 'cheetah_demo':  return self.cheetah.run_demo(args.get('demo', ''), args.get('task', ''))

            # Status
            if tool == 'hub_status': return self.status()

            return f"Unknown hub tool: {tool}"
        except Exception as e:
            return f"Hub dispatch error [{tool}]: {e}"


# ── Singleton ─────────────────────────────────────────────────────────────────

_HUB: Optional[DevinHub] = None

def get_hub() -> DevinHub:
    global _HUB
    if _HUB is None:
        _HUB = DevinHub()
    return _HUB


if __name__ == '__main__':
    hub = get_hub()
    print(hub.status())
