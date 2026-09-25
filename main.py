#!/usr/bin/env python3
"""
Devin AGI 4.0 — Comprehensive Unified Entry Point
===================================================
Dynamically loads EVERY Python file from EVERY first-party directory:

  modules/          + subdirs  ai_tools/, knowledge_retrieval/,
                               monitoring/, multimedia_tools/, ...
  servers/
  security/         + subdirs
  ai_core/          + subdirs
  singularity/      + subdirs
  cloud/
  ai_ethics/        + subdirs
  ai_integrations/
  chaos_engineering/
  community/
  cross_border_data_flow/
  cyber_law/
  cyber_range/      + subdirs
  databases/
  digital_twins/
  edge/             + subdirs
  enterprise/
  hexstrike-ai/
  mlops/            + subdirs
  monitoring/
  plugins/
  privacy/
  prototypes/
  quantum/
  recovery/
  scripts/
  threat_intel/     + subdirs
  xr_env/           + subdirs

Then delegates to agent.py for the interactive REPL / agentic loop.
Run directly:  python main.py
Or via devin:  ./devin --main
"""
from __future__ import annotations
import os, sys, json, time, platform, threading, subprocess, shutil, signal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# ── Bootstrap .env ────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent
_ENV  = _ROOT / '.env'
if _ENV.exists():
    for _l in _ENV.read_text().splitlines():
        _l = _l.strip()
        if _l and not _l.startswith('#') and '=' in _l:
            _k, _, _v = _l.partition('=')
            os.environ.setdefault(_k.strip(), _v.strip().strip('"\''))

# ── sys.path bootstrap — every directory that might contain importable code ──
def _add_path(p: Path):
    s = str(p)
    if p.is_dir() and s not in sys.path:
        sys.path.insert(0, s)

# Root + all first-party directories (recursive)
_FIRST_PARTY_ROOTS = [
    'modules', 'servers', 'security', 'ai_core', 'singularity', 'cloud',
    'ai_ethics', 'ai_integrations', 'chaos_engineering', 'community',
    'cross_border_data_flow', 'cyber_law', 'cyber_range', 'databases',
    'digital_twins', 'edge', 'edge_ai', 'enterprise', 'experimental',
    'hardware', 'hexstrike-ai', 'hmi', 'infra', 'legal', 'mlops',
    'monitoring', 'plugins', 'privacy', 'prototypes', 'quantum', 'recovery',
    'scripts', 'threat_intel', 'xr_env', 'repos', 'external',
]

_add_path(_ROOT)
for _base_name in _FIRST_PARTY_ROOTS:
    _base = _ROOT / _base_name
    _add_path(_base)
    if _base.is_dir():
        for _sub in _base.rglob('*'):
            if _sub.is_dir() and not _sub.name.startswith('.') \
                    and '__pycache__' not in str(_sub):
                _add_path(_sub)

import importlib as _il
import importlib.util as _ilu

# ═══════════════════════════════════════════════════════════════════════════════
# Universal dynamic module loader
# ═══════════════════════════════════════════════════════════════════════════════

def _load_file(path: Path, name: Optional[str] = None) -> Optional[Any]:
    """Load a single .py file. Returns module or None on any failure."""
    mod_name = name or path.stem
    try:
        spec = _ilu.spec_from_file_location(mod_name, str(path))
        if spec is None or spec.loader is None:
            return None
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)   # type: ignore
        sys.modules[mod_name] = mod
        return mod
    except BaseException:
        return None


def _discover_dir(directory: Path, skip_names=('__pycache__', '.git', 'node_modules',
                                                 'tests', 'test', 'docs')) -> Dict[str, Any]:
    """
    Recursively find and load every .py file in *directory*.
    Returns {relative_path_str: module_or_None}.
    Skips __init__.py (they're loaded implicitly) and example/demo files.
    """
    result: Dict[str, Any] = {}
    if not directory.is_dir():
        return result
    for pyfile in directory.rglob('*.py'):
        # skip __pycache__, hidden dirs, skipped names
        parts = set(pyfile.parts)
        if any(s in parts for s in skip_names):
            continue
        if pyfile.name == '__init__.py':
            continue
        rel = str(pyfile.relative_to(_ROOT))
        # use dotted module name: dir/sub/foo.py → dir.sub.foo
        mod_name = rel.replace(os.sep, '.').replace('/', '.')[:-3]
        mod = _load_file(pyfile, mod_name)
        result[rel] = mod
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# DevinAGI — loads every module in the entire repo
# ═══════════════════════════════════════════════════════════════════════════════

class DevinAGI:
    """
    Comprehensive loader: discovers and imports every Python file in
    every first-party directory.  Exposes property helpers for the
    most important capability objects.
    """

    # First-party directories to scan (relative to _ROOT)
    SCAN_DIRS: List[str] = [
        # Core capability modules
        'modules',
        # Background micro-services
        'servers',
        # Security, audit, compliance
        'security',
        # Cognitive architecture (memory, reasoning)
        'ai_core',
        # Goal system and self-improvement
        'singularity',
        # Cloud integrations (AWS, Azure, GCP)
        'cloud',
        # Fairness / ethics / transparency
        'ai_ethics',
        # External AI provider connectors
        'ai_integrations',
        # Chaos / resilience engineering
        'chaos_engineering',
        # Community tools (bug bounty, plugin marketplace)
        'community',
        # Data sovereignty (CCPA, GDPR, cross-border)
        'cross_border_data_flow',
        # Legal / cyber law tools
        'cyber_law',
        # Cyber range / CTF / red-blue team
        'cyber_range',
        # Database initialization / migration
        'databases',
        # Digital-twin simulations
        'digital_twins',
        # Edge computing (federated learning, IoT, TinyML)
        'edge',
        # Neuromorphic / swarm edge AI
        'edge_ai',
        # Enterprise (HIPAA, SOC2, SSO, licensing)
        'enterprise',
        # Experimental (consciousness, quantum AI)
        'experimental',
        # Hardware (robotics firmware, TPM, simulation)
        'hardware',
        # Hexstrike MCP / server tools
        'hexstrike-ai',
        # Human-machine interface (AR/VR, neural interface)
        'hmi',
        # Infrastructure (k8s, observability, tracing)
        'infra',
        # Legal compliance tools
        'legal',
        # ML operations (canary, drift, A/B testing)
        'mlops',
        # Monitoring dashboards, CPU/memory trackers
        'monitoring',
        # Plugin ecosystem
        'plugins',
        # Privacy tooling (differential privacy, data obfuscation)
        'privacy',
        # Prototype / experimental features
        'prototypes',
        # Post-quantum cryptography
        'quantum',
        # Disaster recovery, auto-rollback
        'recovery',
        # Utility scripts (DB init, firmware updates)
        'scripts',
        # Threat intelligence (MITRE ATT&CK, IOC, VirusTotal)
        'threat_intel',
        # XR / metaverse / spatial computing
        'xr_env',
    ]

    def __init__(self):
        self.modules: Dict[str, Optional[Any]] = {}
        self._load_all()

    # ── Discovery ─────────────────────────────────────────────────────────────

    def _load_all(self):
        for dir_name in self.SCAN_DIRS:
            directory = _ROOT / dir_name
            if not directory.is_dir():
                continue
            loaded = _discover_dir(directory)
            self.modules.update(loaded)

    # ── Named property accessors for key capability objects ───────────────────

    def _get_instance(self, attr: str, rel_path: str, class_name: str):
        if not hasattr(self, attr):
            mod = self.modules.get(rel_path)
            obj = None
            if mod and hasattr(mod, class_name):
                try:
                    obj = getattr(mod, class_name)()
                except Exception:
                    pass
            setattr(self, attr, obj)
        return getattr(self, attr)

    @property
    def long_term_memory(self):
        return self._get_instance('_ltm',
            'ai_core/cognitive_arch/long_term_memory.py', 'LongTermMemory')

    @property
    def working_memory(self):
        return self._get_instance('_wm',
            'ai_core/cognitive_arch/working_memory.py', 'WorkingMemory')

    @property
    def security_dashboard(self):
        return self._get_instance('_sec',
            'security/security_dashboard.py', 'SecurityDashboard')

    @property
    def tool_executor(self):
        return self._get_instance('_tex',
            'modules/tool_executor.py', 'ToolExecutor')

    @property
    def data_logger(self):
        return self._get_instance('_dlog',
            'modules/data_logger.py', 'DataLogger')

    @property
    def persistent_memory(self):
        return self._get_instance('_pmem',
            'modules/persistent_memory.py', 'PersistentMemory')

    @property
    def messaging_gateway(self):
        return self._get_instance('_msg',
            'modules/messaging_gateway.py', 'MessagingGateway')

    @property
    def desktop_automator(self):
        return self._get_instance('_desk',
            'modules/os_automation.py', 'DesktopAutomator')

    @property
    def keyboard_mouse(self):
        return self._get_instance('_kbm',
            'modules/keyboard_mouse_control.py', 'KeyboardMouseController')

    @property
    def task_orchestrator(self):
        return self._get_instance('_orch',
            'servers/task_orchestrator.py', 'TaskOrchestrator')

    # ── Status helpers ────────────────────────────────────────────────────────

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
        """Brief summary: how many files loaded per directory."""
        counts: Dict[str, Tuple[int, int]] = {}
        for path, mod in self.modules.items():
            top = path.split('/')[0]
            ok, total = counts.get(top, (0, 0))
            counts[top] = (ok + (1 if mod else 0), total + 1)
        lines = ['Capability summary (loaded/total per directory):']
        for d, (ok, tot) in sorted(counts.items()):
            bar = '█' * int(ok / max(tot, 1) * 10)
            lines.append(f'  {d:<28} {ok:>3}/{tot}  {bar}')
        return '\n'.join(lines)


# ── Singleton ─────────────────────────────────────────────────────────────────
_devin: Optional[DevinAGI] = None

def get_devin() -> DevinAGI:
    global _devin
    if _devin is None:
        _devin = DevinAGI()
    return _devin


# ── Banner ────────────────────────────────────────────────────────────────────
def _banner(devin: DevinAGI):
    IS_TTY = sys.stdout.isatty()
    def _c(code, t): return f'\033[{code}m{t}\033[0m' if IS_TTY else t
    w = shutil.get_terminal_size((80, 24)).columns
    line = '─' * (w - 2)
    print(_c('36;1', f'╭{line}╮'))
    print(_c('36;1', '│') + _c('1',  '  Devin AGI v4.0 — Fully Integrated OS Agent  ') + _c('36;1', ''))
    print(_c('36;1', '│') + _c('2',
          f'  Platform: {platform.system()}  ·  '
          f'Modules: {devin.loaded_count()}/{devin.total_count()}  ·  '
          f'Dirs: {len(devin.SCAN_DIRS)}') + _c('36;1', ''))
    print(_c('36;1', f'╰{line}╯') + '\n')


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    import argparse
    p = argparse.ArgumentParser(description='Devin AGI 4.0 — full module loader + agent REPL')
    p.add_argument('--status',    action='store_true', help='Print module status and exit')
    p.add_argument('--caps',      action='store_true', help='Print capability summary per directory')
    p.add_argument('--no-agent',  action='store_true', help='Stop after loading (do not launch REPL)')
    args, remaining = p.parse_known_args()

    devin = get_devin()

    if args.status:
        print(devin.status_report())
        sys.exit(0)

    if args.caps:
        print(devin.capability_summary())
        sys.exit(0)

    _banner(devin)

    if args.no_agent:
        print(f'Loaded {devin.loaded_count()}/{devin.total_count()} modules. REPL skipped (--no-agent).')
        sys.exit(0)

    # Delegate to agent.py for the full REPL / agentic loop
    agent_py = _ROOT / 'agent.py'
    if not agent_py.exists():
        print(f'ERROR: {agent_py} not found.')
        sys.exit(1)

    sys.argv = [str(agent_py)] + remaining
    exec(compile(agent_py.read_text(), str(agent_py), 'exec'), {
        '__file__': str(agent_py),
        '__name__': '__main__',
        '__doc__':  None,
    })


if __name__ == '__main__':
    main()
