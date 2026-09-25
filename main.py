#!/usr/bin/env python3
"""
Devin AGI 4.0 — Comprehensive Unified Entry Point
===================================================
Imports capabilities from ALL files in the entire repo:
  modules/  (104 Python files)  — core capabilities, AI providers, automation
  servers/  (12 files)          — background Flask micro-services
  security/ (14 files)          — security dashboard, audit, compliance
  ai_core/  (6 files)           — cognitive architecture, reasoning
  singularity/ (4 files)        — goal system, self-replication
  cloud/    (4 files)           — AWS, Azure, GCP, private cloud

Then delegates to agent.py's REPL for the interactive loop.
Run directly:  python main.py
Or via devin launcher: ./devin --main
"""

from __future__ import annotations
import os, sys, json, time, platform, threading, subprocess, textwrap, re, shutil, signal
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

# ── sys.path: add ALL directories that may contain importable code ────────────
def _add_path(p: Path):
    s = str(p)
    if p.is_dir() and s not in sys.path:
        sys.path.insert(0, s)

_add_path(_ROOT)
for _base in [
    _ROOT / 'modules',
    _ROOT / 'ai_core',
    _ROOT / 'ai_core' / 'cognitive_arch',
    _ROOT / 'ai_core' / 'neurosymbolic',
    _ROOT / 'ai_core' / 'self_improvement',
    _ROOT / 'security',
    _ROOT / 'servers',
    _ROOT / 'singularity',
    _ROOT / 'singularity' / 'goal_system',
    _ROOT / 'singularity' / 'self_replication',
    _ROOT / 'cloud',
    _ROOT / 'repos',
    _ROOT / 'external',
]:
    _add_path(_base)
    if _base.is_dir():
        for _sub in _base.iterdir():
            if _sub.is_dir() and not _sub.name.startswith('.'):
                _add_path(_sub)

import importlib as _il
import importlib.util as _ilu

# ── Graceful import helper ────────────────────────────────────────────────────
def _try_import(name: str, file: Optional[Path] = None):
    """Import a module by name or file path. Returns module or None."""
    try:
        if file and file.exists():
            spec = _ilu.spec_from_file_location(name, str(file))
            if spec:
                mod = _ilu.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore
                sys.modules[name] = mod
                return mod
        return _il.import_module(name)
    except BaseException:
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# LOAD ALL MODULES — every import is wrapped in try/except
# ═══════════════════════════════════════════════════════════════════════════════

class DevinAGI:
    """
    Comprehensive Devin AGI loader.
    Imports capabilities from every file in the repo and exposes them
    through a unified interface.  Delegates interaction to agent.py.
    """

    def __init__(self):
        self.modules: Dict[str, Any] = {}
        self._load_all()

    # ── modules/ ──────────────────────────────────────────────────────────────

    def _load_all(self):
        m = self.modules
        _md = _ROOT / 'modules'

        # Primary integrations (loads all 24 external repos)
        m['integrations']          = _try_import('modules.integrations',
                                                  _md / 'integrations.py')

        # AI providers
        m['Gemini_module']         = _try_import('Gemini_module',         _md / 'Gemini_module.py')
        m['claude_module']         = _try_import('claude_module',         _md / 'claude_module.py')
        m['chatgpt_module']        = _try_import('chatgpt_module',        _md / 'chatgpt_module.py')
        m['ollama_module']         = _try_import('ollama_module',         _md / 'ollama_module.py')
        m['hf_provider']           = _try_import('hf_provider',           _md / 'hf_provider.py')
        m['perplexity_module']     = _try_import('perplexity_module',     _md / 'perplexity_module.py')
        m['all_ais_modules']       = _try_import('all_ais_modules',       _md / 'all_ais_modules.py')
        m['all_otherais_modules']  = _try_import('all_otherais_modules',  _md / 'all_otherais_modules.py')
        m['ai_connector']          = _try_import('ai_connector',          _md / 'ai_connector.py')
        m['cheetah_providers']     = _try_import('cheetah_providers',     _md / 'cheetah_providers.py')

        # OS automation / GUI control
        m['os_automation']         = _try_import('os_automation',         _md / 'os_automation.py')
        m['keyboard_mouse_control']= _try_import('keyboard_mouse_control',_md / 'keyboard_mouse_control.py')
        m['automation_tools']      = _try_import('automation_tools',      _md / 'automation_tools.py')
        m['automation_module']     = _try_import('automation_module',     _md / 'automation_module.py')
        m['platform_ops_tools']    = _try_import('platform_ops_tools',    _md / 'platform_ops_tools.py')

        # Browser & web
        m['browser']               = _try_import('browser',               _md / 'browser.py')
        m['cheetah_browser']       = _try_import('cheetah_browser',       _md / 'cheetah_browser.py')
        m['cheetah_web']           = _try_import('cheetah_web',           _md / 'cheetah_web.py')
        m['aia_internet_tasks']    = _try_import('aia_internet_tasks',    _md / 'aia_internet_tasks.py')

        # Memory & storage
        m['persistent_memory']     = _try_import('persistent_memory',     _md / 'persistent_memory.py')
        m['data_logger']           = _try_import('data_logger',           _md / 'data_logger.py')

        # Voice
        m['voice']                 = _try_import('voice',                 _md / 'voice.py')
        m['aia_voice_assistant']   = _try_import('aia_voice_assistant',   _md / 'aia_voice_assistant.py')

        # Shell, code, file execution
        m['code_execution']        = _try_import('code_execution',        _md / 'code_execution.py')
        m['tool_executor']         = _try_import('tool_executor',         _md / 'tool_executor.py')
        m['cheetah_shell']         = _try_import('cheetah_shell',         _md / 'cheetah_shell.py')
        m['cheetah_files']         = _try_import('cheetah_files',         _md / 'cheetah_files.py')
        m['cheetah_notebook']      = _try_import('cheetah_notebook',      _md / 'cheetah_notebook.py')
        m['repo_tools']            = _try_import('repo_tools',            _md / 'repo_tools.py')

        # System monitoring
        m['system_monitor']        = _try_import('system_monitor',        _md / 'system_monitor.py')
        m['system_monitor_module'] = _try_import('system_monitor_module', _md / 'system_monitor_module.py')

        # Cloud
        m['cloud_integration_module']  = _try_import('cloud_integration_module',
                                                       _md / 'cloud_integration_module.py')
        m['cloud_services_manager']    = _try_import('cloud_services_manager',
                                                       _md / 'cloud_services_manager.py')
        m['cloud_integration_services']= _try_import('cloud_integration_services',
                                                       _md / 'cloud_integration_services.py')
        m['cloud_integration_utilities']= _try_import('cloud_integration_utilities',
                                                        _md / 'cloud_integration_utilities.py')
        m['cloud_tools']               = _try_import('cloud_tools',          _md / 'cloud_tools.py')

        # Messaging / notifications
        m['messaging_gateway']     = _try_import('messaging_gateway',     _md / 'messaging_gateway.py')
        m['email_tools']           = _try_import('email_tools',           _md / 'email_tools.py')

        # Social media
        m['social_media_api']      = _try_import('social_media_api',      _md / 'social_media_api.py')
        m['aia_social_media']      = _try_import('aia_social_media',      _md / 'aia_social_media.py')

        # Security & pentesting
        m['pentesting_module']     = _try_import('pentesting_module',     _md / 'pentesting_module.py')
        m['pentestgpt_ai_module']  = _try_import('pentestgpt_ai_module',  _md / 'pentestgpt_ai_module.py')
        m['cyber_range_tools']     = _try_import('cyber_range_tools',     _md / 'cyber_range_tools.py')
        m['cheetah_security']      = _try_import('cheetah_security',      _md / 'cheetah_security.py')
        m['threat_intel_tools']    = _try_import('threat_intel_tools',    _md / 'threat_intel_tools.py')
        m['vulnerability_main']    = _try_import('vuln_analysis_main',    _md / 'vuln_analysis_main.py')
        m['vulnerability_cli']     = _try_import('vuln_analysis_cli',     _md / 'vuln_analysis_cli.py')
        m['privacy_tools']         = _try_import('privacy_tools',         _md / 'privacy_tools.py')
        m['resilience_tools']      = _try_import('resilience_tools',      _md / 'resilience_tools.py')
        m['encryption_tools']      = _try_import('encryption_tools',      _md / 'encryption_tools.py')
        m['ethics_legal_tools']    = _try_import('ethics_legal_tools',    _md / 'ethics_legal_tools.py')
        m['access_control']        = _try_import('access_control',        _md / 'access_control.py')
        m['plugins_tools']         = _try_import('plugins_tools',         _md / 'plugins_tools.py')
        m['quantum_tools']         = _try_import('quantum_tools',         _md / 'quantum_tools.py')

        # Mobile / IoT / device
        m['mobile_integration_module'] = _try_import('mobile_integration_module',
                                                       _md / 'mobile_integration_module.py')
        m['aia_device_control']    = _try_import('aia_device_control',    _md / 'aia_device_control.py')
        m['robotics_control_module']= _try_import('robotics_control_module',
                                                   _md / 'robotics_control_module.py')

        # XR / immersive
        m['xr_tools']              = _try_import('xr_tools',              _md / 'xr_tools.py')
        m['reality_xr_tools']      = _try_import('reality_xr_tools',      _md / 'reality_xr_tools.py')
        m['holomat_bridge']        = _try_import('holomat_bridge',        _md / 'holomat_bridge.py')
        m['holomat_home_screen']   = _try_import('holomat_home_screen',   _md / 'holomat_home_screen.py')
        m['holomat_run']           = _try_import('holomat_run',           _md / 'holomat_run.py')
        m['opendevin_bridge']      = _try_import('opendevin_bridge',      _md / 'opendevin_bridge.py')
        m['canvas_server']         = _try_import('canvas_server',         _md / 'canvas_server.py')

        # AI learning / self-improvement
        m['ai_learning_module']    = _try_import('ai_learning_module',    _md / 'ai_learning_module.py')
        m['aia_machine_learning']  = _try_import('aia_machine_learning',  _md / 'aia_machine_learning.py')

        # Vision / multimedia
        m['face_recognition_tools']= _try_import('face_recognition_tools',_md / 'face_recognition_tools.py')
        m['aia_face_detection']    = _try_import('aia_face_detection',    _md / 'aia_face_detection.py')
        m['multimedia_processing_module'] = _try_import('multimedia_processing_module',
                                                          _md / 'multimedia_processing_module.py')

        # Data retrieval / analytics
        m['aia_data_retrieval']    = _try_import('aia_data_retrieval',    _md / 'aia_data_retrieval.py')
        m['analytics_module']      = _try_import('analytics_module',      _md / 'analytics_module.py')
        m['cheetah_research']      = _try_import('cheetah_research',      _md / 'cheetah_research.py')

        # Agent / orchestration
        m['cheetah_agent']         = _try_import('cheetah_agent',         _md / 'cheetah_agent.py')
        m['cheetah_compaction']    = _try_import('cheetah_compaction',    _md / 'cheetah_compaction.py')
        m['cheetah_context']       = _try_import('cheetah_context',       _md / 'cheetah_context.py')
        m['cheetahclaws_bridge']   = _try_import('cheetahclaws_bridge',   _md / 'cheetahclaws_bridge.py')
        m['external_agent_tools']  = _try_import('external_agent_tools',  _md / 'external_agent_tools.py')
        m['user_interaction_module']= _try_import('user_interaction_module',
                                                   _md / 'user_interaction_module.py')
        m['engine']                = _try_import('engine',                _md / 'engine.py')
        m['scheduler']             = _try_import('scheduler',             _md / 'scheduler.py')
        m['integration_hub']       = _try_import('integration_hub',       _md / 'integration_hub.py')

        # AI conversation
        m['ai_conversation_module']= _try_import('ai_conversation_module',_md / 'ai_conversation_module.py')

        # Legacy Devin bridges
        m['devin1_bootstrap']      = _try_import('devin1_bootstrap',      _md / 'devin1_bootstrap.py')
        m['devin1_core_service']   = _try_import('devin1_core_service',   _md / 'devin1_core_service.py')
        m['devin1_chatmain']       = _try_import('devin1_chatmain',       _md / 'devin1_chatmain.py')
        m['devin2_bootstrap']      = _try_import('devin2_bootstrap',      _md / 'devin2_bootstrap.py')
        m['devin3_bootstrap']      = _try_import('devin3_bootstrap',      _md / 'devin3_bootstrap.py')

        # Jarvis
        m['jarvis_main']           = _try_import('jarvis_main',           _md / 'jarvis_main.py')
        m['jarvis_tools']          = _try_import('jarvis_tools',          _md / 'jarvis_tools.py')
        m['jarvis_bridge']         = _try_import('jarvis_bridge',         _md / 'jarvis_bridge.py')

        # AIA automation
        m['aia_automation']        = _try_import('aia_automation',        _md / 'aia_automation.py')

        # ── servers/ ──────────────────────────────────────────────────────────
        _sv = _ROOT / 'servers'
        m['cloud_integration_server']   = _try_import('cloud_integration_server',
                                                        _sv / 'cloud_integration_server.py')
        m['analytics_server']           = _try_import('analytics_server',
                                                        _sv / 'analytics_server.py')
        m['ai_learning_server']         = _try_import('ai_learning_server',
                                                        _sv / 'ai_learning_server.py')
        m['ai_conversation_server']     = _try_import('ai_conversation_server',
                                                        _sv / 'ai_conversation_server.py')
        m['automation_server']          = _try_import('automation_server',
                                                        _sv / 'automation_server.py')
        m['device_control_server']      = _try_import('device_control_server',
                                                        _sv / 'device_control_server.py')
        m['mobile_integration_server']  = _try_import('mobile_integration_server',
                                                        _sv / 'mobile_integration_server.py')
        m['multimedia_processing_server']= _try_import('multimedia_processing_server',
                                                         _sv / 'multimedia_processing_server.py')
        m['pentesting_server']          = _try_import('pentesting_server',
                                                        _sv / 'pentesting_server.py')
        m['system_monitor_server']      = _try_import('system_monitor_server',
                                                        _sv / 'system_monitor_server.py')
        m['task_orchestrator']          = _try_import('task_orchestrator',
                                                        _sv / 'task_orchestrator.py')

        # ── security/ ─────────────────────────────────────────────────────────
        _sec = _ROOT / 'security'
        m['security_dashboard']    = _try_import('security_dashboard',
                                                  _sec / 'security_dashboard.py')
        m['key_manager']           = _try_import('key_manager',
                                                  _sec / 'key_manager.py')
        m['action_auditor']        = _try_import('action_auditor',
                                                  _sec / 'audit_logs' / 'action_auditor.py')
        m['log_verifier']          = _try_import('log_verifier',
                                                  _sec / 'audit_logs' / 'log_verifier.py')
        m['three_laws']            = _try_import('three_laws_compliance',
                                                  _sec / 'ethical_enforcer' / 'three_laws_compliance.py')
        m['ransomware_detector']   = _try_import('ransomware_detector',
                                                  _sec / 'incident_response' / 'ransomware_detector.py')
        m['soar_workflows']        = _try_import('soar_workflows',
                                                  _sec / 'incident_response' / 'soar_workflows.py')
        m['adversarial_defense']   = _try_import('adversarial_defense',
                                                  _sec / 'ai_security' / 'adversarial_defense.py')
        m['docker_sandbox']        = _try_import('docker_sandbox',
                                                  _sec / 'sandbox' / 'docker_sandbox.py')
        m['gdpr_checker']          = _try_import('gdpr_checker',
                                                  _sec / 'compliance' / 'gdpr_checker.py')
        m['cfaa_checker']          = _try_import('cfaa_checker',
                                                  _sec / 'compliance' / 'cfaa_checker.py')

        # ── ai_core/ ──────────────────────────────────────────────────────────
        _ac = _ROOT / 'ai_core'
        m['long_term_memory']      = _try_import('long_term_memory',
                                                  _ac / 'cognitive_arch' / 'long_term_memory.py')
        m['working_memory']        = _try_import('working_memory',
                                                  _ac / 'cognitive_arch' / 'working_memory.py')
        m['reasoning_engine']      = _try_import('reasoning_engine',
                                                  _ac / 'cognitive_arch' / 'reasoning_engine.py')
        m['neural_bridge']         = _try_import('neural_bridge',
                                                  _ac / 'neurosymbolic' / 'neural_bridge.py')
        m['symbolic_rules']        = _try_import('symbolic_rules',
                                                  _ac / 'neurosymbolic' / 'symbolic_rules.py')
        m['curriculum_learning']   = _try_import('curriculum_learning',
                                                  _ac / 'self_improvement' / 'curriculum_learning.py')
        m['reward_modeling']       = _try_import('reward_modeling',
                                                  _ac / 'self_improvement' / 'reward_modeling.py')

        # ── singularity/ ──────────────────────────────────────────────────────
        _sg = _ROOT / 'singularity'
        m['ethics_constraints']    = _try_import('ethics_constraints',
                                                  _sg / 'goal_system' / 'ethics_constraints.py')
        m['utility_function']      = _try_import('utility_function',
                                                  _sg / 'goal_system' / 'utility_function.py')
        m['code_generator']        = _try_import('code_generator',
                                                  _sg / 'self_replication' / 'code_generator.py')
        m['knowledge_distillation']= _try_import('knowledge_distillation',
                                                  _sg / 'self_replication' / 'knowledge_distillation.py')

        # ── cloud/ ────────────────────────────────────────────────────────────
        _cl = _ROOT / 'cloud'
        m['aws_integration']       = _try_import('aws_integration',    _cl / 'aws_integration.py')
        m['azure_integration']     = _try_import('azure_integration',  _cl / 'azure_integration.py')
        m['gcp_integration']       = _try_import('gcp_integration',    _cl / 'gcp_integration.py')
        m['private_cloud']         = _try_import('private_cloud_integration',
                                                  _cl / 'private_cloud_integration.py')

    # ── Convenience accessors ─────────────────────────────────────────────────

    def get(self, name: str) -> Optional[Any]:
        return self.modules.get(name)

    def loaded_count(self) -> int:
        return sum(1 for v in self.modules.values() if v is not None)

    def total_count(self) -> int:
        return len(self.modules)

    def status_report(self) -> str:
        loaded = self.loaded_count()
        total  = self.total_count()
        lines  = [f"DevinAGI modules: {loaded}/{total} loaded\n"]
        for name, mod in sorted(self.modules.items()):
            mark = '✓' if mod is not None else '✗'
            lines.append(f"  {mark}  {name}")
        return '\n'.join(lines)

    # ── Long-term memory (ai_core) ────────────────────────────────────────────

    @property
    def long_term_memory(self):
        mod = self.modules.get('long_term_memory')
        if mod and hasattr(mod, 'LongTermMemory'):
            if not hasattr(self, '_ltm'):
                try:
                    self._ltm = mod.LongTermMemory()
                except Exception:
                    self._ltm = None
            return self._ltm
        return None

    @property
    def working_memory(self):
        mod = self.modules.get('working_memory')
        if mod and hasattr(mod, 'WorkingMemory'):
            if not hasattr(self, '_wm'):
                try:
                    self._wm = mod.WorkingMemory()
                except Exception:
                    self._wm = None
            return self._wm
        return None

    # ── Security dashboard ────────────────────────────────────────────────────

    @property
    def security_dashboard(self):
        mod = self.modules.get('security_dashboard')
        if mod and hasattr(mod, 'SecurityDashboard'):
            if not hasattr(self, '_sec_dash'):
                try:
                    self._sec_dash = mod.SecurityDashboard()
                except Exception:
                    self._sec_dash = None
            return self._sec_dash
        return None

    # ── Messaging gateway ─────────────────────────────────────────────────────

    @property
    def messaging_gateway(self):
        mod = self.modules.get('messaging_gateway')
        if mod and hasattr(mod, 'MessagingGateway'):
            if not hasattr(self, '_msg_gw'):
                try:
                    self._msg_gw = mod.MessagingGateway()
                except Exception:
                    self._msg_gw = None
            return self._msg_gw
        return None

    # ── Tool executor ─────────────────────────────────────────────────────────

    @property
    def tool_executor(self):
        mod = self.modules.get('tool_executor')
        if mod and hasattr(mod, 'ToolExecutor'):
            if not hasattr(self, '_tex'):
                try:
                    self._tex = mod.ToolExecutor()
                except Exception:
                    self._tex = None
            return self._tex
        return None

    # ── Data logger ──────────────────────────────────────────────────────────

    @property
    def data_logger(self):
        mod = self.modules.get('data_logger')
        if mod and hasattr(mod, 'DataLogger'):
            if not hasattr(self, '_dlog'):
                try:
                    self._dlog = mod.DataLogger()
                except Exception:
                    self._dlog = None
            return self._dlog
        return None

    # ── Desktop automator ─────────────────────────────────────────────────────

    @property
    def desktop_automator(self):
        mod = self.modules.get('os_automation')
        if mod and hasattr(mod, 'DesktopAutomator'):
            if not hasattr(self, '_desk'):
                try:
                    self._desk = mod.DesktopAutomator()
                except Exception:
                    self._desk = None
            return self._desk
        return None

    # ── Persistent memory ─────────────────────────────────────────────────────

    @property
    def persistent_memory(self):
        mod = self.modules.get('persistent_memory')
        if mod and hasattr(mod, 'PersistentMemory'):
            if not hasattr(self, '_pmem'):
                try:
                    self._pmem = mod.PersistentMemory()
                except Exception:
                    self._pmem = None
            return self._pmem
        return None


# ── Singleton instance ────────────────────────────────────────────────────────
_devin: Optional[DevinAGI] = None

def get_devin() -> DevinAGI:
    global _devin
    if _devin is None:
        _devin = DevinAGI()
    return _devin


# ── Banner ────────────────────────────────────────────────────────────────────
def _print_startup_banner(devin: DevinAGI):
    w = shutil.get_terminal_size((80, 24)).columns
    IS_TTY = sys.stdout.isatty()
    def _c(code, t): return f'\033[{code}m{t}\033[0m' if IS_TTY else t

    line = '─' * (w - 2)
    loaded = devin.loaded_count()
    total  = devin.total_count()

    print(_c('36;1', f'╭{line}╮'))
    print(_c('36;1', '│') + _c('1', '  Devin AGI v4.0  ') +
          _c('2', f'·  {platform.system()}  ·  fully integrated') + _c('36;1', ''))
    print(_c('36;1', '│') + _c('2', f'  modules loaded: {loaded}/{total}  ·  agent.py: active') +
          _c('36;1', ''))
    print(_c('36;1', f'╰{line}╯') + '\n')


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description='Devin AGI 4.0 — full module loader')
    parser.add_argument('--status', action='store_true', help='Show module status and exit')
    parser.add_argument('--no-agent', action='store_true',
                        help='Stop after loading modules (do not launch agent REPL)')
    args, remaining = parser.parse_known_args()

    # Load all modules
    devin = get_devin()

    if args.status:
        print(devin.status_report())
        sys.exit(0)

    _print_startup_banner(devin)

    if args.no_agent:
        print(f"Loaded {devin.loaded_count()}/{devin.total_count()} modules. (--no-agent: REPL skipped)")
        sys.exit(0)

    # Delegate to agent.py's main() for the full REPL / agentic loop
    agent_py = _ROOT / 'agent.py'
    if not agent_py.exists():
        print(f"ERROR: {agent_py} not found. Run agent.py directly.")
        sys.exit(1)

    # Pass through any remaining CLI args to agent.py
    sys.argv = [str(agent_py)] + remaining
    exec(compile(agent_py.read_text(), str(agent_py), 'exec'), {
        '__file__': str(agent_py),
        '__name__': '__main__',
        '__doc__':  None,
    })


if __name__ == '__main__':
    main()
