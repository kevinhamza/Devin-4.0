# modules/holomat_bridge.py
# Integrates Holomat (holographic/spatial computing patterns) into Devin.
# Holomat (external/Holomat) provides:
# - Spatial audio and display interfaces
# - Mixed reality content generation
# - Physical simulation integration

import logging
import os
import subprocess
from typing import Dict, Any

logger = logging.getLogger("HolomatBridge")

_HOLOMAT_DIR = os.path.join(os.path.dirname(__file__), "..", "external", "Holomat")
_available = os.path.isdir(_HOLOMAT_DIR) and len(os.listdir(_HOLOMAT_DIR)) > 0


class HolomatBridge:
    """
    Bridges Holomat spatial computing capabilities into Devin.
    Provides spatial display, mixed reality, and holographic output.
    """

    def __init__(self):
        self._available = _available
        if self._available:
            logger.info(f"Holomat bridge initialized ({_HOLOMAT_DIR}).")

    def run_holomat(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        if not self._available:
            return {"success": False, "output": "Holomat not found in external/Holomat"}

        scripts = os.path.join(_HOLOMAT_DIR)
        main_file = None
        for f in ["main.py", "holomat.py", "assist.py"]:
            candidate = os.path.join(scripts, f)
            if os.path.isfile(candidate):
                main_file = candidate
                break

        if not main_file:
            return {"success": False, "output": f"No main script found in {scripts}"}

        try:
            result = subprocess.run(
                ["python3", main_file, command],
                capture_output=True, text=True, timeout=timeout, cwd=scripts
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip() or result.stderr.strip(),
            }
        except Exception as e:
            return {"success": False, "output": str(e)}

    def status(self) -> Dict[str, Any]:
        return {
            "available": self._available,
            "path": _HOLOMAT_DIR,
        }
