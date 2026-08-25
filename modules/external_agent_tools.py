# Devin/modules/external_agent_tools.py
# Purpose: Lets Devin delegate a task to another locally-installed coding
#          agent CLI (claude-code, gemini-cli) or drive a local OpenClaw
#          installation, the same way run_hexstrike_command dispatches to a
#          running hexstrike-ai server instead of reimplementing its ~150
#          tools in Python.
#
# claude-code and gemini-cli are Node/TypeScript CLIs, not Python libraries --
# there's nothing to import. The only real integration surface is their
# non-interactive one-shot mode (`claude -p "<prompt>"` /
# `gemini -p "<prompt>"`), invoked as a subprocess. Same story for openclaw:
# it's a TypeScript plugin platform run via its own CLI. If the binary isn't
# installed, these tools report that clearly instead of failing to import
# (matching the hexstrike-ai client's is_available() pattern).

import logging
import shutil
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ExternalAgentTools")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)
logger.propagate = False


class ExternalAgentTools:
    """Shells out to locally-installed external agent/platform CLIs."""

    def __init__(self, timeout: int = 300):
        self.timeout = timeout

    def _run(self, binary: str, args: List[str], cwd: Optional[str], install_hint: str) -> Dict[str, Any]:
        resolved = shutil.which(binary)
        if not resolved:
            return {
                "status": "error",
                "message": f"'{binary}' is not installed or not on PATH. {install_hint}",
            }
        try:
            result = subprocess.run(
                [resolved, *args],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if result.returncode != 0:
                return {
                    "status": "error",
                    "message": f"'{binary}' exited with code {result.returncode}.",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            return {"status": "success", "output": result.stdout, "stderr": result.stderr}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": f"'{binary}' timed out after {self.timeout}s."}
        except Exception as e:
            logger.error(f"Failed to run '{binary}': {e}")
            return {"status": "error", "message": str(e)}

    def delegate_to_claude_code(self, prompt: str, working_directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Delegates a coding/agentic task to a local Claude Code CLI
        installation in headless one-shot mode -- useful for complex,
        multi-file codebase work better handled by Claude Code's own
        tool-use loop than by Devin issuing individual file edits itself.
        """
        return self._run(
            "claude",
            ["-p", prompt],
            working_directory,
            "Install with: npm install -g @anthropic-ai/claude-code",
        )

    def delegate_to_gemini_cli(self, prompt: str, working_directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Delegates a task to a local Gemini CLI installation in headless
        one-shot mode.
        """
        return self._run(
            "gemini",
            ["-p", prompt],
            working_directory,
            "Install with: npm install -g @google/gemini-cli",
        )

    def run_openclaw_command(self, args: List[str]) -> Dict[str, Any]:
        """
        Runs a raw command against a local OpenClaw installation (plugin
        management, channel/messaging operations, gateway status, etc.) --
        pass the arguments as you would type them after 'openclaw', e.g.
        ['gateway', 'status'].
        """
        return self._run(
            "openclaw",
            args,
            None,
            "Install per https://github.com/openclaw/openclaw docs/install.",
        )
