# modules/jarvis_bridge.py
# Integrates Jarvis (Concept-Bytes) voice assistant patterns into Devin.
# Jarvis (external/Jarvis) is a lightweight Python voice assistant with:
# - Natural language to tool call translation
# - Speech recognition + TTS
# - Local assistant skills (weather, timer, math, etc.)

import logging
import sys
import os
import subprocess
from typing import Optional, Dict, Any

logger = logging.getLogger("JarvisBridge")

_JARVIS_DIR = os.path.join(os.path.dirname(__file__), "..", "external", "Jarvis")
_available = os.path.isdir(_JARVIS_DIR) and os.path.isfile(os.path.join(_JARVIS_DIR, "jarvis.py"))


class JarvisBridge:
    """
    Bridges Concept-Bytes Jarvis local assistant features into Devin.
    Provides voice recognition, TTS, and lightweight local tool execution.
    """

    def __init__(self):
        self._available = _available
        if self._available:
            logger.info("Jarvis bridge initialized (external/Jarvis).")

    def run_jarvis_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Run a command through Jarvis's assistant pipeline.
        Falls back to subprocess if Jarvis isn't directly importable.
        """
        if not self._available:
            return {"success": False, "output": "Jarvis not available in external/Jarvis"}

        try:
            result = subprocess.run(
                ["python3", os.path.join(_JARVIS_DIR, "assist.py"), command],
                capture_output=True, text=True, timeout=timeout,
                cwd=_JARVIS_DIR
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip() or result.stderr.strip(),
            }
        except Exception as e:
            return {"success": False, "output": str(e)}

    def list_skills(self) -> list:
        """List available Jarvis skills."""
        if not self._available:
            return []
        tools_file = os.path.join(_JARVIS_DIR, "tools.py")
        if not os.path.isfile(tools_file):
            return []
        try:
            with open(tools_file) as f:
                content = f.read()
            # Extract function names as rough "skills" list
            import re
            return re.findall(r'^def (\w+)', content, re.MULTILINE)
        except Exception:
            return []

    def status(self) -> Dict[str, Any]:
        return {
            "available": self._available,
            "path": _JARVIS_DIR,
            "skills": self.list_skills()[:10],
        }
