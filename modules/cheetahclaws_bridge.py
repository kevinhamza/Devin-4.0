# modules/cheetahclaws_bridge.py
# Bridges CheetahClaws patterns (AgentState, streaming events, compaction)
# into Devin's main tool execution system.
#
# CheetahClaws (external/cheetahclaws) is a Python-native AI assistant with:
# - Multi-provider streaming (same provider cascade pattern as Devin)
# - AgentState: immutable turn tracking, token accounting
# - PermissionRequest / ToolStart / ToolEnd event stream
# - Smart history compaction with token-aware pruning
# - Circuit-breaker per-provider to handle transient failures

import logging
import sys
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Generator

logger = logging.getLogger("CheetahClawsBridge")

_CHEETAHCLAWS_DIR = os.path.join(os.path.dirname(__file__), "..", "external", "cheetahclaws")
_available = False

if os.path.isdir(_CHEETAHCLAWS_DIR) and os.path.isdir(os.path.join(_CHEETAHCLAWS_DIR, "cheetahclaws")):
    if _CHEETAHCLAWS_DIR not in sys.path:
        sys.path.insert(0, _CHEETAHCLAWS_DIR)
    try:
        from cheetahclaws.agent import AgentState, ToolStart, ToolEnd, TurnDone, PermissionRequest
        from cheetahclaws.compaction import estimate_tokens, get_context_limit
        _available = True
        logger.info("CheetahClaws bridge: native module loaded.")
    except ImportError as e:
        logger.warning(f"CheetahClaws native import failed, using stubs: {e}")


# ── Stub implementations (used when CheetahClaws isn't importable) ──────────

@dataclass
class _AgentState:
    messages: list = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_cache_write_tokens: int = 0
    turn_count: int = 0

@dataclass
class _ToolStart:
    name: str
    inputs: dict

@dataclass
class _ToolEnd:
    name: str
    result: str
    permitted: bool = True

@dataclass
class _TurnDone:
    input_tokens: int
    output_tokens: int

@dataclass
class _PermissionRequest:
    tool_name: str
    inputs: dict


if not _available:
    AgentState = _AgentState
    ToolStart = _ToolStart
    ToolEnd = _ToolEnd
    TurnDone = _TurnDone
    PermissionRequest = _PermissionRequest

    def estimate_tokens(messages: List[Dict]) -> int:
        return sum(len(str(m.get("content", ""))) // 4 for m in messages)

    def get_context_limit(model: str) -> int:
        return 200000


class CheetahClawsBridge:
    """
    Thin wrapper that exposes CheetahClaws' session-state and compaction
    logic to Devin's main loop without requiring full CheetahClaws init.
    """

    def __init__(self):
        self.state = AgentState()
        self._available = _available

    def update_tokens(self, input_tokens: int, output_tokens: int) -> None:
        self.state.total_input_tokens += input_tokens
        self.state.total_output_tokens += output_tokens
        self.state.turn_count += 1

    def estimate_token_usage(self, messages: List[Dict]) -> int:
        return estimate_tokens(messages)

    def context_limit(self, model: str = "claude-sonnet-4-6") -> int:
        return get_context_limit(model)

    def should_compact(self, messages: List[Dict], model: str = "claude-sonnet-4-6", threshold: float = 0.75) -> bool:
        used = self.estimate_token_usage(messages)
        limit = self.context_limit(model)
        return (used / limit) > threshold if limit > 0 else False

    def session_summary(self) -> Dict[str, Any]:
        return {
            "turns": self.state.turn_count,
            "total_input_tokens": self.state.total_input_tokens,
            "total_output_tokens": self.state.total_output_tokens,
            "total_tokens": self.state.total_input_tokens + self.state.total_output_tokens,
            "cheetahclaws_native": self._available,
        }
