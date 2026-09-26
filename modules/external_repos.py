#!/usr/bin/env python3
"""
Devin AGI 4.0 — External Repository Integration Registry

Unified access point for all 23 integrated external repositories.
Each bridge is loaded gracefully — missing repos never crash Devin.
"""
from __future__ import annotations
import os, sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

ROOT = Path(__file__).resolve().parent.parent


def _try_import(mod_name: str, attr: str = '') -> Optional[Any]:
    """Import a module (and optionally an attribute) with graceful failure."""
    try:
        import importlib
        mod = importlib.import_module(mod_name)
        return getattr(mod, attr) if attr else mod
    except BaseException:
        return None


def _load_bridge(rel_path: str) -> Optional[Any]:
    """Load a bridge module by path relative to repo root."""
    try:
        import importlib.util as ilu
        p = ROOT / rel_path
        if not p.exists():
            return None
        spec = ilu.spec_from_file_location(p.stem, str(p))
        if not spec or not spec.loader:
            return None
        mod = ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        return mod
    except BaseException:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
class ExternalRepoRegistry:
    """
    Registry of all external repos integrated into Devin AGI 4.0.

    Each entry provides:
      - bridge: the loaded bridge module (or None if unavailable)
      - status: 'loaded' | 'unavailable'
      - description: one-line summary
    """

    # Mapping: name -> (bridge_module_path, description)
    _REPOS: Dict[str, tuple] = {
        # AI Coding & Agent frameworks
        'gemini-cli':             ('modules/Gemini_module.py',       'Google Gemini CLI integration'),
        'claude-code':            ('modules/claude_module.py',        'Anthropic Claude Code integration'),
        'self-operating-computer':('modules/os_agent.py',             'Self-operating computer / OS control'),
        'openclaw':               ('modules/integration_hub.py',      'OpenClaw multi-agent framework'),
        'opendevin':              ('modules/opendevin_bridge.py',      'OpenDevin autonomous coding agent'),
        'cheetahclaws':           ('modules/cheetahclaws_bridge.py',   'CheetahClaws fast tool execution'),
        # AIA family
        'aia':                    ('modules/aia_automation.py',        'AIA automation suite'),
        'aia-voice':              ('modules/aia_voice_assistant.py',   'AIA voice assistant'),
        'aia-ml':                 ('modules/aia_machine_learning.py',  'AIA machine learning tools'),
        'aia-social':             ('modules/aia_social_media.py',      'AIA social media automation'),
        # Devin legacy versions
        'devin-1':                ('modules/devin1_bootstrap.py',      'Devin 1.0 legacy bootstrap'),
        'devin-2':                ('modules/devin2_bootstrap.py',      'Devin 2.0 legacy bootstrap'),
        'devin-3':                ('modules/devin3_bootstrap.py',      'Devin 3.0 legacy bootstrap'),
        # Specialised agents
        'jarvis':                 ('modules/jarvis_bridge.py',         'Jarvis home automation / IoT agent'),
        'holomat':                ('modules/holomat_bridge.py',        'Holomat holographic interface'),
        'shannon':                ('modules/pentesting_module.py',     'Shannon pentest pipeline (authorised use)'),
        'hexstrike-ai':           ('modules/pentestgpt_ai_module.py',  'HexStrike AI security assistant'),
        # Security / pentesting
        'airgorah':               ('modules/pentesting_tools/airgorah_tools.py', 'Airgorah WiFi audit tool'),
        'vulnerability-analysis': ('modules/vuln_analysis_main.py',   'Vulnerability analysis pipeline'),
        'hackability':            ('modules/hackability_functions.php', 'Hackability web audit (PHP bridge)'),
        'responder':              ('modules/os_automation.py',         'Responder LLMNR/NBT-NS bridge'),
        'nishang':                ('modules/pentesting_module.py',     'Nishang PowerShell pentest bridge'),
        'powertools':             ('modules/platform_ops_tools.py',    'PowerTools system utilities'),
        # Community
        'moltbots':               ('modules/integrations.py',          'MoltBots community bots'),
    }

    def __init__(self):
        self._bridges: Dict[str, Optional[Any]] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        for name, (path, _desc) in self._REPOS.items():
            if path.endswith('.php'):
                self._bridges[name] = None  # PHP modules cannot be directly imported
                continue
            self._bridges[name] = _load_bridge(path)
        self._loaded = True

    def get(self, name: str) -> Optional[Any]:
        """Return bridge module for *name*, or None."""
        self._ensure_loaded()
        return self._bridges.get(name)

    def call(self, repo: str, fn: str, *args, **kwargs) -> Any:
        """
        Call function *fn* on bridge for *repo*.
        Returns error string on failure.
        """
        self._ensure_loaded()
        bridge = self._bridges.get(repo)
        if bridge is None:
            return f'ERROR: repo "{repo}" not available'
        func = getattr(bridge, fn, None)
        if func is None:
            return f'ERROR: {repo}.{fn} not found'
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return f'ERROR: {repo}.{fn} raised {e}'

    def status(self) -> str:
        self._ensure_loaded()
        lines = [f'External repository integrations ({len(self._REPOS)} total):\n']
        loaded = 0
        for name, (path, desc) in sorted(self._REPOS.items()):
            bridge = self._bridges.get(name)
            ok = bridge is not None
            if ok:
                loaded += 1
            mark = '✓' if ok else '✗'
            lines.append(f'  {mark}  {name:<30} {desc}')
        lines.append(f'\n  Loaded: {loaded}/{len(self._REPOS)}')
        return '\n'.join(lines)

    def list_available(self) -> List[str]:
        self._ensure_loaded()
        return [name for name, bridge in self._bridges.items() if bridge is not None]


# ── Convenience functions ─────────────────────────────────────────────────────────────

_registry: Optional[ExternalRepoRegistry] = None


def get_registry() -> ExternalRepoRegistry:
    global _registry
    if _registry is None:
        _registry = ExternalRepoRegistry()
    return _registry


def repo_status() -> str:
    return get_registry().status()


def call_repo(repo: str, fn: str, *args, **kwargs) -> Any:
    return get_registry().call(repo, fn, *args, **kwargs)


if __name__ == '__main__':
    print(repo_status())
