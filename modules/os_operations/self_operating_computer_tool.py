# Devin/modules/os_operations/self_operating_computer_tool.py
# Purpose: Exposes the vendored self-operating-computer project as a real
#          Devin tool, so the agent can operate the screen (click, type,
#          navigate UIs) by looking at it, instead of only the blind
#          coordinate-based DesktopAutomator.

import logging
import os
import sys
from typing import Optional

logger = logging.getLogger("SelfOperatingComputerTool")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)
logger.propagate = False

_VENDOR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "self-operating-computer")

SOC_AVAILABLE = os.path.isdir(_VENDOR_DIR)
if SOC_AVAILABLE and _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)

# Models self-operating-computer's Config.validation() will accept without
# prompting for a key, keyed by which env var makes each usable -- mirrors
# AIAgent's own Claude > OpenAI > Gemini(free) preference order so this
# tool picks whichever provider Devin is already configured with.
_MODEL_BY_ENV_KEY = [
    ("ANTHROPIC_API_KEY", "claude-3"),
    ("OPENAI_API_KEY", "gpt-4-with-ocr"),
    ("GOOGLE_API_KEY", "gemini-pro-vision"),
]


def _pick_available_model() -> Optional[str]:
    for env_key, model in _MODEL_BY_ENV_KEY:
        if os.getenv(env_key):
            return model
    return None


def operate_computer(objective: str, model: Optional[str] = None) -> dict:
    """
    Drives the real screen (mouse, keyboard, screenshots) toward `objective`
    using self-operating-computer's vision-based operate loop, instead of
    requiring the caller to already know exact on-screen coordinates.

    Requires a real display (X11/Wayland/macOS/Windows desktop session) --
    this cannot do anything meaningful in a headless container.
    """
    if not SOC_AVAILABLE:
        return {"status": "error", "message": "self-operating-computer is not vendored in this installation."}

    chosen_model = model or _pick_available_model()
    if not chosen_model:
        return {
            "status": "error",
            "message": "No AI provider configured (need ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY).",
        }

    try:
        from operate.operate import main as operate_main
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import self-operating-computer: {e}"}

    logger.info(f"Operating computer toward objective '{objective}' using model '{chosen_model}'...")
    try:
        operate_main(chosen_model, terminal_prompt=objective, voice_mode=False, verbose_mode=False)
        return {"status": "success", "result": f"Objective attempted via self-operating-computer ({chosen_model})."}
    except Exception as e:
        logger.error(f"self-operating-computer failed: {e}", exc_info=True)
        return {"status": "error", "message": f"self-operating-computer failed: {e}"}
