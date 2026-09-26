"""
autonomous_core.py — Pure autonomous agent core for Devin.
Implements self-directed task execution, goal decomposition,
reflection, and long-horizon planning — the "brain" that makes
Devin behave like Claude Code.
"""
from __future__ import annotations

import json
import re
import time
import os
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    BLOCKED = 'blocked'


@dataclass
class SubTask:
    id: str
    goal: str
    status: TaskStatus = TaskStatus.PENDING
    result: str = ''
    tool_calls: int = 0
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    def complete(self, result: str):
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = time.time()

    def fail(self, reason: str):
        self.status = TaskStatus.FAILED
        self.result = reason
        self.completed_at = time.time()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'goal': self.goal,
            'status': self.status.value,
            'result': self.result[:200],
            'tool_calls': self.tool_calls,
        }


@dataclass
class Plan:
    goal: str
    subtasks: List[SubTask] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def add_subtask(self, goal: str) -> SubTask:
        st = SubTask(id=f'st_{len(self.subtasks)+1}', goal=goal)
        self.subtasks.append(st)
        return st

    def current(self) -> Optional[SubTask]:
        for st in self.subtasks:
            if st.status == TaskStatus.PENDING:
                return st
        return None

    def completed_count(self) -> int:
        return sum(1 for st in self.subtasks if st.status == TaskStatus.COMPLETED)

    def is_done(self) -> bool:
        return all(st.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
                   for st in self.subtasks)

    def progress_str(self) -> str:
        done = self.completed_count()
        total = len(self.subtasks)
        return f'{done}/{total} subtasks done'

    def summary(self) -> str:
        lines = [f'Goal: {self.goal}']
        for st in self.subtasks:
            icon = {'pending': '○', 'in_progress': '◎', 'completed': '●', 'failed': '✗', 'blocked': '⊘'}
            lines.append(f'  {icon.get(st.status.value, "?")} {st.goal[:60]}')
            if st.result:
                lines.append(f'     → {st.result[:80]}')
        return '\n'.join(lines)


# ── Task classification ───────────────────────────────────────────────────────

_CONVERSATIONAL_PATTERNS = re.compile(
    r'^(what|who|where|when|why|how|can you|tell me|explain|describe|'
    r'summarize|what is|what are|is it|are there|do you|does|will|'
    r'i think|i feel|thanks|hello|hi |hey |ok |sure|yes|no|'
    r'what\'s|how\'s|who\'s|where\'s)',
    re.IGNORECASE
)

_TASK_PATTERNS = re.compile(
    r'\b(create|build|write|make|generate|open|launch|start|run|execute|'
    r'install|download|upload|search|find|analyze|scan|fix|debug|'
    r'update|delete|move|copy|rename|compress|extract|deploy|monitor|'
    r'schedule|automate|send|configure|setup|convert|translate|summarize '
    r'this|check if|list all|show me|take a screenshot|click on|type in|'
    r'navigate to|browse to)\b',
    re.IGNORECASE
)

def classify_intent(text: str) -> str:
    """Return 'conversation' or 'task'."""
    t = text.strip()
    if len(t) < 20 and not _TASK_PATTERNS.search(t):
        return 'conversation'
    if _CONVERSATIONAL_PATTERNS.match(t) and not _TASK_PATTERNS.search(t):
        return 'conversation'
    return 'task'


# ── Goal decomposition ────────────────────────────────────────────────────────

def decompose_goal(goal: str, tools: List[str]) -> List[str]:
    """
    Decompose a complex goal into ordered subtasks using keyword analysis.
    Returns a list of subtask descriptions.
    """
    goal_lower = goal.lower()
    subtasks = []

    # Research/analysis tasks
    if any(w in goal_lower for w in ('find', 'search', 'look', 'research', 'discover')):
        subtasks.append(f'Search for information about: {goal[:100]}')
        subtasks.append('Analyze and organize search results')
        subtasks.append('Summarize findings')

    # File/code creation tasks
    elif any(w in goal_lower for w in ('write', 'create', 'build', 'generate', 'make', 'develop')):
        subtasks.append('Understand requirements and plan the implementation')
        if any(w in goal_lower for w in ('script', 'code', 'program', 'function', '.py', '.ts', '.js')):
            subtasks.append('Write the implementation code')
            subtasks.append('Test and verify the implementation')
        else:
            subtasks.append(f'Create: {goal[:100]}')
        subtasks.append('Verify result meets requirements')

    # System/OS tasks
    elif any(w in goal_lower for w in ('open', 'launch', 'start', 'run', 'execute')):
        subtasks.append(f'Execute the action: {goal[:100]}')
        subtasks.append('Confirm the action completed successfully')

    # Analysis tasks
    elif any(w in goal_lower for w in ('analyze', 'scan', 'audit', 'check', 'review', 'debug')):
        subtasks.append(f'Collect data for: {goal[:100]}')
        subtasks.append('Analyze the collected data')
        subtasks.append('Report findings and recommendations')

    # Installation/setup tasks
    elif any(w in goal_lower for w in ('install', 'setup', 'configure', 'deploy')):
        subtasks.append('Check prerequisites and current state')
        subtasks.append(f'Perform: {goal[:100]}')
        subtasks.append('Verify installation/setup succeeded')

    # Generic task
    else:
        subtasks.append(f'Plan approach for: {goal[:100]}')
        subtasks.append(f'Execute: {goal[:100]}')
        subtasks.append('Verify completion and clean up')

    return subtasks


# ── Reflection and self-correction ───────────────────────────────────────────

def should_retry(error: str, attempt: int, max_attempts: int = 3) -> Tuple[bool, str]:
    """
    Determine if a failed step should be retried and how.
    Returns (should_retry, hint_message).
    """
    if attempt >= max_attempts:
        return False, f'Exceeded max attempts ({max_attempts})'

    error_lower = error.lower()

    # Rate limit → retry with backoff
    if 'rate limit' in error_lower or '429' in error_lower:
        return True, f'Rate limited — waiting {2**attempt}s before retry'

    # Not found → try alternative approach
    if 'not found' in error_lower or 'no such file' in error_lower:
        return True, 'Resource not found — try searching or checking path'

    # Permission denied → try with sudo or different approach
    if 'permission' in error_lower or 'denied' in error_lower:
        return True, 'Permission denied — try a different approach or check sudo'

    # Timeout → retry once
    if 'timeout' in error_lower and attempt < 2:
        return True, 'Timeout — retrying once'

    # Network error → retry
    if any(w in error_lower for w in ('connection', 'network', 'timeout', 'unreachable')):
        return True, 'Network issue — retrying'

    # Don't retry on logic errors
    if any(w in error_lower for w in ('invalid', 'syntax', 'type error', 'unexpected')):
        return False, 'Logic error — needs a different approach'

    return False, 'Unknown error — stopping'


# ── Context compaction ────────────────────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    """Rough token estimate (4 chars ≈ 1 token)."""
    return len(text) // 4


def compact_messages(messages: List[Dict[str, Any]],
                      max_chars: int = 80_000,
                      keep_recent: int = 10) -> List[Dict[str, Any]]:
    """
    Compact a message history to stay within token limits.
    Keeps the most recent 'keep_recent' messages and summarizes older ones.
    """
    if not messages:
        return messages

    total = sum(len(str(m.get('content', ''))) for m in messages)
    if total <= max_chars:
        return messages

    # Always keep system messages at the start
    sys_msgs = [m for m in messages if m.get('role') == 'system']
    other = [m for m in messages if m.get('role') != 'system']

    # Keep last N messages intact
    recent = other[-keep_recent:] if len(other) > keep_recent else other
    older = other[:-keep_recent] if len(other) > keep_recent else []

    if not older:
        return messages

    # Build a summary of older messages
    summaries = []
    for m in older:
        role = m.get('role', 'unknown')
        content = m.get('content', '')
        if isinstance(content, list):
            # Handle Claude-style multi-block content
            text_parts = []
            for blk in content:
                if isinstance(blk, dict):
                    if blk.get('type') == 'text':
                        text_parts.append(blk.get('text', ''))
                    elif blk.get('type') == 'tool_use':
                        text_parts.append(f'[used tool: {blk.get("name","")}]')
                    elif blk.get('type') == 'tool_result':
                        text_parts.append(f'[tool result: {str(blk.get("content",""))[:100]}]')
            content = ' '.join(text_parts)
        summaries.append(f'[{role}]: {str(content)[:150]}')

    summary_msg = {
        'role': 'user',
        'content': (
            '[Context summary — older conversation compacted]\n' +
            '\n'.join(summaries[-20:]) +  # at most 20 older turns summarized
            '\n[End of summary. Recent conversation follows.]'
        )
    }

    return sys_msgs + [summary_msg] + recent


# ── Anti-loop detection ───────────────────────────────────────────────────────

class LoopDetector:
    """Detect and prevent repetitive tool call loops."""

    def __init__(self, warn_at: int = 3, hard_at: int = 5):
        self.warn_at = warn_at
        self.hard_at = hard_at
        self._counts: Dict[str, int] = {}
        self._history: List[str] = []

    def record(self, tool_name: str, args: Dict[str, Any]) -> Tuple[str, int]:
        """Record a tool call. Returns ('ok'|'warn'|'stop', count)."""
        key = f'{tool_name}:{json.dumps(args, sort_keys=True, default=str)[:100]}'
        self._counts[key] = self._counts.get(key, 0) + 1
        self._history.append(tool_name)
        count = self._counts[key]
        if count >= self.hard_at:
            return 'stop', count
        if count >= self.warn_at:
            return 'warn', count
        return 'ok', count

    def hint_message(self, tool_name: str, count: int) -> str:
        return (
            f'⚠ LOOP DETECTED: {tool_name!r} called {count}× with identical arguments. '
            f'You MUST change your approach. Try: (1) a completely different tool, '
            f'(2) call screenshot_and_analyze to re-assess the current state, '
            f'(3) decompose the task differently, or (4) ask for clarification.'
        )

    def reset(self):
        self._counts.clear()
        self._history.clear()

    def is_stuck(self, window: int = 5) -> bool:
        """Return True if the last N calls are all the same tool."""
        if len(self._history) < window:
            return False
        recent = self._history[-window:]
        return len(set(recent)) == 1


# ── Persistence nudge ─────────────────────────────────────────────────────────

NUDGE_MESSAGES = [
    'Execute the task now using available tools. Do not just describe — actually call a tool.',
    'You described what to do but haven\'t done it yet. Call the appropriate tool NOW to make real progress.',
    'ACTION REQUIRED: Use a tool to make measurable progress. '
    'If unsure, call think_and_plan first to clarify the approach, then execute.',
    'CRITICAL: Proceed with execution. You have the tools — use them now to complete the task.',
]

def get_nudge(attempt: int) -> str:
    idx = min(attempt, len(NUDGE_MESSAGES) - 1)
    return NUDGE_MESSAGES[idx]


# ── Autonomous task runner (orchestrator) ────────────────────────────────────

class AutonomousRunner:
    """
    Orchestrates multi-step task execution with planning,
    loop detection, context management, and self-correction.
    """

    def __init__(self, dispatch_tool_fn, provider, system_prompt: str = ''):
        self._dispatch = dispatch_tool_fn
        self._provider = provider
        self._system = system_prompt
        self.loop_detector = LoopDetector()
        self._stats: Dict[str, int] = {
            'steps': 0, 'tool_calls': 0, 'errors': 0, 'retries': 0
        }

    def run(self, goal: str, messages: List[Dict[str, Any]],
             max_steps: int = 100,
             on_step: Optional[Any] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Run the agentic loop for a goal.
        Returns (final_result, updated_messages).
        """
        from . import cc_interface as ui  # type: ignore

        messages = list(messages)
        messages.append({'role': 'user', 'content': goal})

        intent = classify_intent(goal)
        is_task = (intent == 'task')

        final_result = ''
        consecutive_errors = 0
        no_tool_pushes = 0
        MAX_CONSECUTIVE_ERRORS = 5
        MAX_NO_TOOL_PUSHES = 3

        step = 0
        while step < max_steps:
            step += 1
            self._stats['steps'] += 1

            # Context compaction
            messages = compact_messages(messages, max_chars=100_000, keep_recent=12)

            # Call provider
            try:
                text, calls = self._provider.call(messages, system=self._system)
                consecutive_errors = 0
            except KeyboardInterrupt:
                break
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    break
                self._stats['errors'] += 1
                wait = min(30, 2 ** consecutive_errors)
                time.sleep(wait)
                continue

            # Print assistant text
            if text and text.strip():
                clean = re.sub(r'^\s*\(acting\)\s*', '', text.strip(), flags=re.I)
                if clean:
                    if ui:
                        ui.print_response(clean)
                    else:
                        print(f'\nDevin  {clean}')

            # Build assistant message
            self._add_assistant_message(messages, text, calls)

            # No tool calls
            if not calls:
                if text.strip():
                    final_result = text.strip()
                if not is_task:
                    break
                # Check if done
                if self._looks_done(final_result):
                    break
                # Nudge
                if no_tool_pushes < MAX_NO_TOOL_PUSHES:
                    no_tool_pushes += 1
                    messages.append({'role': 'user', 'content': get_nudge(no_tool_pushes - 1)})
                    continue
                else:
                    break
                continue

            # Execute tools
            tool_results = []
            for call in calls:
                name = call['name']
                args = call.get('args', {})

                status, count = self.loop_detector.record(name, args)
                if status == 'stop':
                    hint = self.loop_detector.hint_message(name, count)
                    call['_loop_hint'] = hint
                elif status == 'warn':
                    pass  # just log

                result = self._dispatch(name, args)
                self._stats['tool_calls'] += 1
                if str(result).startswith('ERROR:'):
                    self._stats['errors'] += 1

                tool_results.append({
                    'call_id': call.get('id', f't{step}_{name}'),
                    'name': name,
                    'result': result,
                })

                # Task complete?
                if name == 'task_complete' or str(result).startswith('TASK_COMPLETE:'):
                    final_result = str(result).replace('TASK_COMPLETE:', '').strip()
                    return final_result, messages

            # Feed results back
            self._add_tool_results(messages, tool_results, calls)

        return final_result or '(completed)', messages

    def _add_assistant_message(self, messages: list, text: str, calls: list):
        from types import SimpleNamespace
        p = self._provider
        provider_type = type(p).__name__.lower()
        if 'claude' in provider_type:
            blocks = []
            if text:
                blocks.append({'type': 'text', 'text': text})
            for c in calls:
                blocks.append({'type': 'tool_use', 'id': c.get('id', 'x'),
                                'name': c['name'], 'input': c.get('args', {})})
            if blocks:
                messages.append({'role': 'assistant', 'content': blocks})
        else:
            if text or calls:
                messages.append({'role': 'assistant', 'content': text or ''})

    def _add_tool_results(self, messages: list, results: list, calls: list):
        provider_type = type(self._provider).__name__.lower()
        if 'claude' in provider_type:
            blocks = [
                {'type': 'tool_result', 'tool_use_id': r['call_id'], 'content': r['result']}
                for r in results
            ]
            messages.append({'role': 'user', 'content': blocks})
        elif any(t in provider_type for t in ('openai', 'huggingface', 'ollama')):
            for r in results:
                messages.append({'role': 'tool', 'tool_call_id': r['call_id'],
                                  'content': r['result']})
        else:
            combined = '\n\n'.join(f'[Tool: {r["name"]}]\n{r["result"]}' for r in results)
            messages.append({'role': 'user', 'content': combined})

    def _looks_done(self, text: str) -> bool:
        done_re = re.compile(
            r'\b(task (is )?complete|done\b|finished\b|completed\b|accomplished|'
            r'successfully (done|completed|finished)|all done|all steps (done|complete)|'
            r'i\'ve (completed|finished|done)|everything (is |has been )?(done|complete)|'
            r'result:|summary:|here (is|are) the|i (have|\'ve) (now )?(written|created|'
            r'saved|installed|opened|launched|built|run|executed|generated|deployed|'
            r'downloaded|uploaded|sent|configured))\b',
            re.IGNORECASE
        )
        return bool(done_re.search(text))

    @property
    def stats(self) -> Dict[str, int]:
        return dict(self._stats)
