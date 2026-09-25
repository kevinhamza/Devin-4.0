#!/usr/bin/env python3
"""
Devin AGI 4.0 — Capability Bootstrap
======================================
Pre-flight check + capability module initialization.
Always exits 0: warnings are printed but the REPL is never blocked.

Usage:
  python bootstrap.py            # Check deps + init all capability modules
  python bootstrap.py --quiet    # Only print errors
  python bootstrap.py --fix      # Auto-install missing pip packages
"""
from __future__ import annotations
import os, sys, shutil, subprocess, importlib.util
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent

# Load .env
_ENV = ROOT / '.env'
if _ENV.exists():
    for _l in _ENV.read_text().splitlines():
        _l = _l.strip()
        if _l and not _l.startswith('#') and '=' in _l:
            _k, _, _v = _l.partition('=')
            os.environ.setdefault(_k.strip(), _v.strip().strip('"\''  ))

QUIET = '--quiet' in sys.argv
FIX   = '--fix'   in sys.argv


def _c(code: str, t: str) -> str:
    return f'\033[{code}m{t}\033[0m' if sys.stdout.isatty() else t


def _ok(msg: str) -> None:
    if not QUIET:
        print(_c('32', f'  ✅  {msg}'))


def _warn(msg: str) -> None:
    print(_c('33', f'  ⚠  {msg}'))


def _err(msg: str) -> None:
    print(_c('31', f'  ❌  {msg}'))


def _head(msg: str) -> None:
    if not QUIET:
        print(_c('36;1', f'\n── {msg} ──'))


# ───────────────────────────────────────────────────────────────────────────────
def _check_pkg(import_name: str, pip_name: Optional[str] = None, optional: bool = False) -> bool:
    avail = importlib.util.find_spec(import_name) is not None
    label = pip_name or import_name
    if avail:
        _ok(label)
        return True
    msg = f'{label} not installed'
    if optional:
        _warn(f'{msg} (optional — some features degraded)')
    else:
        _err(f'{msg} — run: pip install {label}')
    if FIX:
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', label],
                check=True, capture_output=True,
            )
            _ok(f'{label} installed')
            return True
        except Exception as e:
            _err(f'Auto-install failed: {e}')
    return False


def _check_cmd(cmd: str, optional: bool = True) -> bool:
    avail = shutil.which(cmd) is not None
    if avail:
        _ok(cmd)
    elif optional:
        _warn(f'{cmd} not in PATH (optional)')
    else:
        _err(f'{cmd} not found in PATH')
    return avail


def _check_env(var: str, required: bool = False) -> bool:
    val = os.environ.get(var, '')
    if val:
        masked = val[:4] + '***' + val[-2:] if len(val) > 8 else '***'
        _ok(f'{var} = {masked}')
        return True
    if required:
        _err(f'{var} not set — add it to .env')
    else:
        _warn(f'{var} not set (optional)')
    return False


# ───────────────────────────────────────────────────────────────────────────────
def run_checks() -> Dict[str, bool]:
    results: Dict[str, bool] = {}

    _head('Core Python dependencies')
    for pkg in ['requests', 'pathlib']:
        results[pkg] = _check_pkg(pkg, optional=True)
    results['PIL'] = _check_pkg('PIL', 'Pillow', optional=True)
    results['numpy'] = _check_pkg('numpy', optional=True)

    _head('OS automation')
    results['pynput']     = _check_pkg('pynput', optional=True)
    results['pyperclip']  = _check_pkg('pyperclip', optional=True)
    results['mss']        = _check_pkg('mss', optional=True)
    results['psutil']     = _check_pkg('psutil', optional=True)

    _head('AI providers')
    hf_token      = _check_env('HF_TOKEN')
    anthropic_key = _check_env('ANTHROPIC_API_KEY')
    gemini_key    = _check_env('GEMINI_API_KEY') or _check_env('GOOGLE_API_KEY')
    openai_key    = _check_env('OPENAI_API_KEY')
    results['HF_TOKEN']          = hf_token
    results['ANTHROPIC_API_KEY'] = anthropic_key
    results['GEMINI_API_KEY']    = gemini_key
    results['OPENAI_API_KEY']    = openai_key

    if not any([hf_token, anthropic_key, gemini_key, openai_key]):
        _warn('No AI provider key set.  Set HF_TOKEN in .env for free HuggingFace models.')
    else:
        if anthropic_key:
            _ok('LLM provider: Claude (Anthropic)')
        elif gemini_key:
            _ok('LLM provider: Gemini (Google)')
        elif openai_key:
            _ok('LLM provider: OpenAI')
        elif hf_token:
            _ok('LLM provider: HuggingFace (free tier)')

    _head('Voice')
    results['pyttsx3']  = _check_pkg('pyttsx3', optional=True)
    results['gtts']     = _check_pkg('gtts', optional=True)
    results['sr']       = _check_pkg('speech_recognition', 'SpeechRecognition', optional=True)
    results['whisper']  = _check_pkg('whisper', 'openai-whisper', optional=True)
    results['pyaudio']  = _check_pkg('pyaudio', optional=True)

    _head('Browser automation')
    results['playwright'] = _check_pkg('playwright', optional=True)
    results['selenium']   = _check_pkg('selenium', optional=True)
    results['bs4']        = _check_pkg('bs4', 'beautifulsoup4', optional=True)

    _head('External CLI tools (optional)')
    for cmd in ['espeak', 'mpg123', 'xdotool', 'wmctrl', 'scrot', 'adb']:
        _check_cmd(cmd, optional=True)

    return results


# ───────────────────────────────────────────────────────────────────────────────
def init_capabilities() -> Dict[str, bool]:
    """Initialize all capability modules. Returns {name: success}."""
    if not QUIET:
        print(_c('36;1', '\n── Initializing capability modules ──'))
    status: Dict[str, bool] = {}

    # Add ROOT to sys.path so modules/ is importable
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    if str(ROOT / 'modules') not in sys.path:
        sys.path.insert(0, str(ROOT / 'modules'))

    _cap_modules = [
        ('os_agent',              'modules.os_agent',              'get_os_agent'),
        ('reasoning_engine',      'modules.reasoning_engine',      'get_reasoning_engine'),
        ('conversation_engine',   'modules.conversation_engine',   'get_conversation_engine'),
        ('hf_enhanced_provider',  'modules.hf_enhanced_provider',  None),
        ('free_claude_provider',  'modules.free_claude_provider',  'is_available'),
        ('system_monitor',        'modules.system_monitor_enhanced', 'get_system_monitor'),
        ('voice_engine',          'modules.voice_engine',          'get_voice_engine'),
        ('browser_agent',         'modules.browser_agent',         None),
        ('all_ais_modules',       'modules.all_ais_modules',       'capability_map'),
    ]

    for name, mod_path, fn_name in _cap_modules:
        try:
            mod = importlib.import_module(mod_path)
            if fn_name and hasattr(mod, fn_name):
                result = getattr(mod, fn_name)()
                _ok(f'{name} → {type(result).__name__}')
            else:
                _ok(f'{name} (module loaded)')
            status[name] = True
        except BaseException as e:
            _warn(f'{name}: {str(e)[:80]}')
            status[name] = False

    return status


# Needed for _check_env return value
from typing import Optional  # noqa: E402


def main() -> None:
    if not QUIET:
        print(_c('1;37', '\nDevin AGI 4.0 — System Bootstrap'))
        print(_c('2', f'  Python {sys.version.split()[0]}  ·  {sys.platform}\n'))

    dep_results = run_checks()
    cap_results = init_capabilities()

    if not QUIET:
        n_ok  = sum(1 for v in cap_results.values() if v)
        n_tot = len(cap_results)
        print(_c('36;1', '\n── Summary ──'))
        print(f'  Capability modules: {n_ok}/{n_tot} ready')
        print()
        if n_ok == 0:
            _warn('No capability modules loaded. Check that modules/ exists and deps are installed.')
        elif n_ok < n_tot // 2:
            _warn('Many modules not loaded. Run: pip install -r requirements.txt')
        else:
            _ok(f'{n_ok}/{n_tot} capability modules ready — Devin is good to go!')
        print()

    # Always exit 0 — never block the REPL
    sys.exit(0)


if __name__ == '__main__':
    main()
