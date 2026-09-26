#!/usr/bin/env python3
"""
Devin AGI 4.0 — Comprehensive Unified Entry Point
===================================================
Dynamically loads EVERY Python file from EVERY first-party directory,
explicitly bootstraps all capability modules, then delegates to the
DevinREPL (Claude Code-style interface) or agent.py.

Usage:
  python main.py                  # Full module load + DevinREPL
  python main.py "do something"    # One-shot prompt
  python main.py --status         # Print per-file module load status
  python main.py --caps           # Capability summary per directory
  python main.py --voice          # REPL in voice command mode
  python main.py --provider hf    # Force HuggingFace provider
  python main.py --no-agent       # Load modules only, skip REPL
  python main.py --test           # Run 40 core tests via agent.py
  DEVIN_USE_CLASSIC_REPL=1 python main.py  # Use agent.py REPL instead
"""
from __future__ import annotations
import os, sys, json, time, platform, threading, subprocess, shutil, signal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# ── Bootstrap .env ──────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
_ENV  = ROOT / '.env'
if _ENV.exists():
    for _l in _ENV.read_text().splitlines():
        _l = _l.strip()
        if _l and not _l.startswith('#') and '=' in _l:
            _k, _, _v = _l.partition('=')
            os.environ.setdefault(_k.strip(), _v.strip().strip('"\'' ))

# ── sys.path bootstrap ────────────────────────────────────────────────────────────────────────
def _add_path(p: Path) -> None:
    s = str(p)
    if p.is_dir() and s not in sys.path:
        sys.path.insert(0, s)

_FIRST_PARTY = [
    'modules', 'servers', 'security', 'ai_core', 'singularity', 'cloud',
    'ai_ethics', 'ai_integrations', 'ai_models', 'api_gateway',
    'chaos_engineering', 'community', 'config', 'cross_border_data_flow',
    'cyber_law', 'cyber_range', 'data', 'databases', 'digital_twins',
    'edge', 'edge_ai', 'enterprise', 'experimental', 'external',
    'hardware', 'hexstrike-ai', 'hmi', 'infra', 'legal', 'mlops',
    'monitoring', 'notes', 'plugins', 'privacy', 'prototypes',
    'quantum', 'reality_engine', 'recovery', 'repos',
    'scripts', 'self-operating-computer', 'singularity',
    'threat_intel', 'web', 'xr_env',
]

_add_path(ROOT)
for _base_name in _FIRST_PARTY:
    _base = ROOT / _base_name
    _add_path(_base)
    if _base.is_dir():
        for _sub in _base.rglob('*'):
            if _sub.is_dir() and not _sub.name.startswith('.') \
                    and '__pycache__' not in str(_sub) \
                    and 'node_modules' not in str(_sub):
                _add_path(_sub)

import importlib as _il
import importlib.util as _ilu

# ═══════════════════════════════════════════════════════════════════════════════
# Universal dynamic module loader
# ═══════════════════════════════════════════════════════════════════════════════

_SKIP_DIRS = frozenset({
    '__pycache__', '.git', 'node_modules', '.venv', 'venv', 'env',
    '.mypy_cache', '.pytest_cache', 'dist', 'build', '.tox',
})

def _load_file(path: Path, mod_name: Optional[str] = None) -> Optional[Any]:
    name = mod_name or path.stem
    try:
        spec = _ilu.spec_from_file_location(name, str(path))
        if spec is None or spec.loader is None:
            return None
        mod = _ilu.module_from_spec(spec)
        sys.modules.setdefault(name, mod)
        spec.loader.exec_module(mod)  # type: ignore
        sys.modules[name] = mod
        return mod
    except BaseException:
        return None


def _discover_dir(directory: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    if not directory.is_dir():
        return result
    for pyfile in directory.rglob('*.py'):
        parts = set(pyfile.parts)
        if any(s in parts for s in _SKIP_DIRS):
            continue
        if pyfile.name == '__init__.py':
            continue
        rel = str(pyfile.relative_to(ROOT))
        mod_name = rel.replace(os.sep, '.').replace('/', '.')[:-3]
        mod = _load_file(pyfile, mod_name)
        result[rel] = mod
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Capability bootstrap
# ═══════════════════════════════════════════════════════════════════════════════

class _Capabilities:
    os_agent       = None
    reasoning      = None
    conversation   = None
    hf_provider    = None
    free_claude    = None
    system_monitor = None
    voice          = None
    browser        = None


CAPS = _Capabilities()


def _bootstrap_capabilities() -> None:
    # OS Agent
    try:
        from modules.os_agent import get_os_agent
        CAPS.os_agent = get_os_agent()
    except BaseException:
        pass

    # Reasoning Engine
    try:
        from modules.reasoning_engine import get_reasoning_engine  # type: ignore
        CAPS.reasoning = get_reasoning_engine()
    except BaseException:
        try:
            from modules.reasoning_engine import get_engine
            CAPS.reasoning = get_engine()
        except BaseException:
            pass

    # Conversation Engine
    try:
        from modules.conversation_engine import get_conversation_engine
        CAPS.conversation = get_conversation_engine()
    except BaseException:
        pass

    # HuggingFace provider
    try:
        from modules import hf_enhanced_provider
        CAPS.hf_provider = hf_enhanced_provider
    except BaseException:
        pass

    # Free Claude provider
    try:
        from modules import free_claude_provider
        CAPS.free_claude = free_claude_provider
    except BaseException:
        pass

    # System Monitor
    try:
        from modules.system_monitor_enhanced import get_system_monitor
        CAPS.system_monitor = get_system_monitor()
    except BaseException:
        pass

    # Voice Engine
    try:
        from modules.voice_engine import get_voice_engine
        CAPS.voice = get_voice_engine()
    except BaseException:
        pass

    # Browser Agent (lazy)
    try:
        from modules import browser_agent as _ba_mod
        CAPS.browser = _ba_mod
    except BaseException:
        pass

    # Wire OS tools into reasoning engine
    if CAPS.reasoning and CAPS.os_agent:
        try:
            oa = CAPS.os_agent

            def _r(result) -> str:
                if hasattr(result, 'vision_result') and result.vision_result:
                    return result.vision_result
                if hasattr(result, 'message'):
                    return result.message
                return str(result)

            CAPS.reasoning.register_tool(
                'screenshot',
                lambda prompt='Describe the screen': _r(oa.screenshot(str(prompt))),
                'Take a screenshot and describe what is on screen')
            CAPS.reasoning.register_tool(
                'click',
                lambda x=0, y=0, button='left': _r(oa.click(int(x), int(y), str(button))),
                'Click at pixel coordinates (x, y)')
            CAPS.reasoning.register_tool(
                'type_text',
                lambda text='': _r(oa.type_text(str(text))),
                'Type text on keyboard')
            CAPS.reasoning.register_tool(
                'press_key',
                lambda key='': _r(oa.press_key(str(key))),
                'Press a keyboard key')
            CAPS.reasoning.register_tool(
                'hotkey',
                lambda keys='ctrl+c': _r(oa.hotkey(*str(keys).split('+'))),
                'Keyboard shortcut')
            CAPS.reasoning.register_tool(
                'observe_screen',
                oa.observe,
                'Describe current screen state')
            CAPS.reasoning.register_tool(
                'open_app',
                lambda app_name='': _r(oa.open_application(str(app_name))),
                'Open application by name')
        except BaseException:
            pass

    if CAPS.reasoning and CAPS.system_monitor:
        try:
            CAPS.reasoning.register_tool('system_status', CAPS.system_monitor.summary,
                                          'System resource summary')
        except BaseException:
            pass

    if CAPS.reasoning and CAPS.voice:
        try:
            CAPS.reasoning.register_tool('speak',  CAPS.voice.speak,       'Speak text aloud')
            CAPS.reasoning.register_tool('listen', CAPS.voice.listen_once, 'Listen for voice input')
        except BaseException:
            pass

    # Register CAPS in sys.modules so agent.py can access singletons
    try:
        import types as _types
        _caps_mod = _types.ModuleType('_devin_caps')
        _caps_mod.os_agent       = CAPS.os_agent        # type: ignore
        _caps_mod.reasoning      = CAPS.reasoning       # type: ignore
        _caps_mod.conversation   = CAPS.conversation    # type: ignore
        _caps_mod.system_monitor = CAPS.system_monitor  # type: ignore
        _caps_mod.voice          = CAPS.voice           # type: ignore
        _caps_mod.browser        = CAPS.browser         # type: ignore
        _caps_mod.hf_provider    = CAPS.hf_provider     # type: ignore
        _caps_mod.free_claude    = CAPS.free_claude     # type: ignore
        sys.modules['_devin_caps'] = _caps_mod
    except BaseException:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# DevinAGI — loads every module in the entire repo
# ═══════════════════════════════════════════════════════════════════════════════

class DevinAGI:
    SCAN_DIRS: List[str] = [
        'modules', 'servers', 'security', 'ai_core', 'singularity', 'cloud',
        'ai_ethics', 'ai_integrations', 'ai_models', 'api_gateway',
        'chaos_engineering', 'community', 'config', 'cross_border_data_flow',
        'cyber_law', 'cyber_range', 'data', 'databases', 'digital_twins',
        'edge', 'edge_ai', 'enterprise', 'experimental', 'external',
        'hardware', 'hexstrike-ai', 'hmi', 'infra', 'legal', 'mlops',
        'monitoring', 'notes', 'plugins', 'privacy', 'prototypes',
        'quantum', 'reality_engine', 'recovery',
        'scripts', 'singularity',
        'threat_intel', 'web', 'xr_env',
    ]

    def __init__(self):
        self.modules: Dict[str, Optional[Any]] = {}
        self._load_all()
        _bootstrap_capabilities()

    def _load_all(self) -> None:
        for dir_name in self.SCAN_DIRS:
            directory = ROOT / dir_name
            if not directory.is_dir():
                continue
            self.modules.update(_discover_dir(directory))

    @property
    def os_agent(self):        return CAPS.os_agent
    @property
    def reasoning(self):       return CAPS.reasoning
    @property
    def conversation(self):    return CAPS.conversation
    @property
    def system_monitor(self):  return CAPS.system_monitor
    @property
    def voice(self):           return CAPS.voice
    @property
    def browser(self):
        if CAPS.browser and hasattr(CAPS.browser, 'get_browser_agent'):
            return CAPS.browser.get_browser_agent()
        return None

    def _get_instance(self, attr, rel_path, class_name):
        if not hasattr(self, '_' + attr):
            mod = self.modules.get(rel_path)
            obj = None
            if mod and hasattr(mod, class_name):
                try:
                    obj = getattr(mod, class_name)()
                except Exception:
                    pass
            setattr(self, '_' + attr, obj)
        return getattr(self, '_' + attr)

    @property
    def long_term_memory(self):
        return self._get_instance('ltm',
            'ai_core/cognitive_arch/long_term_memory.py', 'LongTermMemory')

    @property
    def working_memory(self):
        return self._get_instance('wm',
            'ai_core/cognitive_arch/working_memory.py', 'WorkingMemory')

    @property
    def keyboard_mouse(self):
        return self._get_instance('kbm',
            'modules/keyboard_mouse_control.py', 'KeyboardMouseController')

    @property
    def tool_executor(self):
        return self._get_instance('tex', 'modules/tool_executor.py', 'ToolExecutor')

    @property
    def persistent_memory(self):
        return self._get_instance('pmem',
            'modules/persistent_memory.py', 'PersistentMemory')

    def loaded_count(self) -> int:
        return sum(1 for v in self.modules.values() if v is not None)

    def total_count(self) -> int:
        return len(self.modules)

    def status_report(self) -> str:
        loaded = self.loaded_count()
        total  = self.total_count()
        lines  = [f'DevinAGI: {loaded}/{total} modules loaded\n']
        for path, mod in sorted(self.modules.items()):
            mark = '✓' if mod is not None else '✗'
            lines.append(f'  {mark}  {path}')
        return '\n'.join(lines)

    def capability_summary(self) -> str:
        counts: Dict[str, Tuple[int, int]] = {}
        for path, mod in self.modules.items():
            top = path.split('/')[0]
            ok, total = counts.get(top, (0, 0))
            counts[top] = (ok + (1 if mod else 0), total + 1)
        lines = ['Capability summary (loaded/total per directory):']
        for d, (ok, tot) in sorted(counts.items()):
            pct = ok / max(tot, 1)
            bar = '█' * int(pct * 10) + '░' * (10 - int(pct * 10))
            lines.append(f'  {d:<32} {ok:>3}/{tot:<3}  {bar}  {pct*100:.0f}%')
        lines.append('')
        lines.append('Active capability modules:')
        lines.append(f'  os_agent       : {"ready" if CAPS.os_agent else "not loaded"}')
        lines.append(f'  reasoning      : {"ready" if CAPS.reasoning else "not loaded"}')
        lines.append(f'  conversation   : {"ready" if CAPS.conversation else "not loaded"}')
        lines.append(f'  system_monitor : {"ready" if CAPS.system_monitor else "not loaded"}')
        lines.append(f'  voice_engine   : {"ready" if CAPS.voice else "not loaded"}')
        lines.append(f'  browser_agent  : {"ready" if CAPS.browser else "not loaded"}')
        lines.append(f'  hf_provider    : {"ready" if CAPS.hf_provider else "not loaded"}')
        lines.append(f'  free_claude    : {"ready" if CAPS.free_claude else "not loaded"}')
        return '\n'.join(lines)


# ── Singleton ───────────────────────────────────────────────────────────────────────────
_devin: Optional[DevinAGI] = None


def get_devin() -> DevinAGI:
    global _devin
    if _devin is None:
        _devin = DevinAGI()
    return _devin


# ── Banner ──────────────────────────────────────────────────────────────────────────────
def _banner(devin: DevinAGI) -> None:
    IS_TTY = sys.stdout.isatty()
    def _c(code: str, t: str) -> str:
        return f'\033[{code}m{t}\033[0m' if IS_TTY else t
    w = shutil.get_terminal_size((80, 24)).columns
    line = '─' * (w - 2)
    print(_c('36;1', f'╭{line}╮'))
    print(_c('36;1', '│') + _c('1;37',
          '  Devin AGI v4.0 — Autonomous OS-Controlling AI  ') + _c('36;1', ''))
    print(_c('36;1', '│') + _c('2',
          f'  Platform: {platform.system()} {platform.release()}  ·  '
          f'Python {platform.python_version()}  ·  '
          f'Modules: {devin.loaded_count()}/{devin.total_count()}  ·  '
          f'Dirs: {len(devin.SCAN_DIRS)}') + _c('36;1', ''))
    caps_str = '  '
    for label, obj in [
        ('OS', CAPS.os_agent), ('Reason', CAPS.reasoning),
        ('Chat', CAPS.conversation), ('Monitor', CAPS.system_monitor),
        ('Voice', CAPS.voice), ('Browser', CAPS.browser),
    ]:
        mark = '✅' if obj else '⚪'
        caps_str += f'{mark}{label}  '
    print(_c('36;1', '│') + caps_str + _c('36;1', ''))
    print(_c('36;1', f'╰{line}╯') + '\n')


# ── Entry point ─────────────────────────────────────────────────────────────────────────────
def main():
    import argparse
    p = argparse.ArgumentParser(
        description='Devin AGI 4.0 — full module loader + agent REPL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument('prompt',       nargs='?',          help='One-shot prompt (skip REPL)')
    p.add_argument('--status',     action='store_true', help='Print module load status and exit')
    p.add_argument('--caps',       action='store_true', help='Print capability summary per directory')
    p.add_argument('--no-agent',   action='store_true', help='Load modules only, skip REPL')
    p.add_argument('--test',       action='store_true', help='Run core test suite via agent.py')
    p.add_argument('--voice',      action='store_true', help='Start REPL in voice command mode')
    p.add_argument('--provider',   default='',          help='Force AI provider: claude|gemini|openai|hf|ollama|free')
    args, remaining = p.parse_known_args()

    if args.provider:
        os.environ['DEVIN_PROVIDER'] = args.provider
    if args.voice:
        os.environ['DEVIN_VOICE_MODE'] = '1'

    devin = get_devin()

    if args.status:
        print(devin.status_report())
        sys.exit(0)

    if args.caps:
        print(devin.capability_summary())
        sys.exit(0)

    if args.no_agent:
        _banner(devin)
        print(f'Loaded {devin.loaded_count()}/{devin.total_count()} modules. REPL skipped (--no-agent).')
        sys.exit(0)

    _banner(devin)

    agent_py = ROOT / 'agent.py'
    if not agent_py.exists():
        print(f'ERROR: {agent_py} not found.')
        sys.exit(1)

    # ── Route to DevinREPL (default) or agent.py (───────────────────────────────────────
    # DevinREPL is the default interactive mode.
    # Set DEVIN_USE_CLASSIC_REPL=1 to use agent.py's built-in REPL instead.
    if not args.test and not args.prompt and not os.environ.get('DEVIN_USE_CLASSIC_REPL'):
        try:
            from modules.devin_repl import start_repl
            start_repl(devin)
            sys.exit(0)
        except BaseException:
            pass  # Fall through to agent.py on any failure

    # ── Delegate to agent.py (──────────────────────────────────────────────────────────
    agent_argv = [str(agent_py)]
    if args.test:
        agent_argv.append('--test')
    elif args.prompt:
        agent_argv.append(args.prompt)
    agent_argv.extend(remaining)
    sys.argv = agent_argv

    exec_globals = {
        '__file__':  str(agent_py),
        '__name__':  '__main__',
        '__doc__':   None,
        '_DEVIN_OS_AGENT':        CAPS.os_agent,
        '_DEVIN_REASONING':       CAPS.reasoning,
        '_DEVIN_CONVERSATION':    CAPS.conversation,
        '_DEVIN_SYSTEM_MONITOR':  CAPS.system_monitor,
        '_DEVIN_VOICE':           CAPS.voice,
        '_DEVIN_BROWSER_MOD':     CAPS.browser,
        '_DEVIN_HF_PROVIDER':     CAPS.hf_provider,
        '_DEVIN_FREE_CLAUDE':     CAPS.free_claude,
        '_DEVIN_AGI':             devin,
        'sys': sys,
        'os':  os,
    }
    exec(compile(agent_py.read_text(encoding='utf-8'), str(agent_py), 'exec'), exec_globals)


if __name__ == '__main__':
    main()
