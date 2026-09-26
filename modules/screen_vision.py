"""
screen_vision.py — Observation-Reasoning-Action-Verification loop for Devin.
Implements a structured GUI automation cycle: screenshot → AI analysis → action plan
→ execute → verify outcome. Works with any display (Linux X11/Wayland, macOS, Windows).
"""
from __future__ import annotations

import os
import re
import json
import time
import base64
import tempfile
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# ── Optional deps ─────────────────────────────────────────────────────────────

_pag = None
try:
    import pyautogui as _pag
    _pag.FAILSAFE = True
    _pag.PAUSE = 0.05
except Exception:
    pass

_PIL = None
try:
    from PIL import Image as _PIL
except Exception:
    pass


# ── State types ───────────────────────────────────────────────────────────────

class ActionType(str, Enum):
    CLICK       = 'click'
    DOUBLE_CLICK= 'double_click'
    RIGHT_CLICK = 'right_click'
    TYPE        = 'type'
    KEY         = 'key'
    SCROLL      = 'scroll'
    MOVE        = 'move'
    WAIT        = 'wait'
    SCREENSHOT  = 'screenshot'
    DONE        = 'done'
    FAIL        = 'fail'


@dataclass
class ScreenAction:
    action_type: ActionType
    x: Optional[int] = None
    y: Optional[int] = None
    text: Optional[str] = None
    key: Optional[str] = None
    amount: int = 3
    direction: str = 'down'
    wait_seconds: float = 0.5
    reason: str = ''


@dataclass
class ObservationFrame:
    timestamp: float
    screenshot_path: str
    width: int
    height: int
    description: str = ''
    elements: List[Dict] = field(default_factory=list)
    error: str = ''


@dataclass
class VisionCycle:
    goal: str
    observations: List[ObservationFrame] = field(default_factory=list)
    actions_taken: List[ScreenAction] = field(default_factory=list)
    current_state: str = ''
    completed: bool = False
    failed: bool = False
    failure_reason: str = ''
    max_steps: int = 30
    step: int = 0


# ── Screenshot helper ─────────────────────────────────────────────────────────

def _take_screenshot(path: str = '') -> Tuple[str, int, int, str]:
    """Take screenshot, return (path, width, height, error)."""
    if not path:
        fd, path = tempfile.mkstemp(suffix='.png', prefix='devin_vision_')
        os.close(fd)

    # Try pyautogui first
    if _pag is not None:
        try:
            img = _pag.screenshot()
            img.save(path)
            return path, img.width, img.height, ''
        except Exception as e:
            pass

    # Fallback: scrot on Linux
    import platform
    if platform.system() == 'Linux':
        import subprocess
        for tool in ['scrot', 'import', 'gnome-screenshot']:
            try:
                if tool == 'scrot':
                    r = subprocess.run(['scrot', path], capture_output=True, timeout=5)
                elif tool == 'import':
                    r = subprocess.run(['import', '-window', 'root', path], capture_output=True, timeout=5)
                elif tool == 'gnome-screenshot':
                    r = subprocess.run(['gnome-screenshot', '-f', path], capture_output=True, timeout=5)
                if r.returncode == 0 and os.path.exists(path):
                    if _PIL:
                        with _PIL.open(path) as img:
                            return path, img.width, img.height, ''
                    return path, 1920, 1080, ''
            except Exception:
                continue

    return '', 0, 0, 'No screenshot backend available (install pyautogui or scrot)'


def _image_to_base64(path: str) -> str:
    """Convert image file to base64 string for AI vision."""
    try:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception:
        return ''


# ── Screen element extraction (basic heuristic) ───────────────────────────────

def _describe_screenshot_basic(path: str) -> str:
    """Get basic visual description without AI (brightness, colors, resolution)."""
    if not _PIL:
        return f'Screenshot at {path}'
    try:
        with _PIL.open(path) as img:
            w, h = img.size
            # Sample pixels for dominant color detection
            sample = img.resize((32, 32)).convert('RGB')
            pixels = list(sample.getdata())
            avg_r = sum(p[0] for p in pixels) / len(pixels)
            avg_g = sum(p[1] for p in pixels) / len(pixels)
            avg_b = sum(p[2] for p in pixels) / len(pixels)
            brightness = (avg_r + avg_g + avg_b) / 3
            theme = 'dark' if brightness < 128 else 'light'
            return (f'Screen {w}x{h}, {theme} theme, '
                    f'avg color RGB({avg_r:.0f},{avg_g:.0f},{avg_b:.0f})')
    except Exception as e:
        return f'Screenshot at {path} (analysis failed: {e})'


# ── Action executor ───────────────────────────────────────────────────────────

def _execute_action(action: ScreenAction) -> str:
    """Execute a ScreenAction. Returns result string."""
    if action.action_type == ActionType.WAIT:
        time.sleep(action.wait_seconds)
        return f'Waited {action.wait_seconds}s'

    if action.action_type in (ActionType.CLICK, ActionType.DOUBLE_CLICK,
                               ActionType.RIGHT_CLICK, ActionType.MOVE):
        if _pag is None:
            return 'ERROR: pyautogui not available for mouse control'
        x, y = action.x or 0, action.y or 0
        if action.action_type == ActionType.MOVE:
            _pag.moveTo(x, y, duration=0.2)
            return f'Moved to ({x},{y})'
        elif action.action_type == ActionType.CLICK:
            _pag.click(x, y)
            return f'Clicked ({x},{y})'
        elif action.action_type == ActionType.DOUBLE_CLICK:
            _pag.doubleClick(x, y)
            return f'Double-clicked ({x},{y})'
        elif action.action_type == ActionType.RIGHT_CLICK:
            _pag.rightClick(x, y)
            return f'Right-clicked ({x},{y})'

    if action.action_type == ActionType.TYPE:
        if not action.text:
            return 'ERROR: no text to type'
        if _pag:
            _pag.typewrite(action.text, interval=0.02)
            return f'Typed: {action.text[:60]}'
        return 'ERROR: pyautogui not available for typing'

    if action.action_type == ActionType.KEY:
        if not action.key:
            return 'ERROR: no key specified'
        if _pag:
            if '+' in action.key:
                _pag.hotkey(*action.key.split('+'))
            else:
                _pag.press(action.key)
            return f'Pressed: {action.key}'
        return 'ERROR: pyautogui not available for key press'

    if action.action_type == ActionType.SCROLL:
        if _pag:
            clicks = -action.amount if action.direction == 'down' else action.amount
            x, y = action.x or 0, action.y or 0
            _pag.scroll(clicks, x=x, y=y)
            return f'Scrolled {action.direction} {action.amount}x at ({x},{y})'
        return 'ERROR: pyautogui not available for scroll'

    if action.action_type == ActionType.SCREENSHOT:
        path, w, h, err = _take_screenshot()
        if err:
            return f'ERROR: {err}'
        return f'Screenshot: {path} ({w}x{h})'

    if action.action_type == ActionType.DONE:
        return f'DONE: {action.reason}'

    if action.action_type == ActionType.FAIL:
        return f'FAILED: {action.reason}'

    return f'ERROR: unknown action type {action.action_type}'


# ── AI-driven observation parser ──────────────────────────────────────────────

def _parse_ai_action_response(response: str) -> Optional[ScreenAction]:
    """Parse AI response into a ScreenAction. Expects JSON block or structured text."""
    # Try JSON block first
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
    if not json_match:
        # Try raw JSON object
        json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', response, re.DOTALL)

    if json_match:
        try:
            data = json.loads(json_match.group(1) if '```' in json_match.group(0) else json_match.group(0))
            action_str = data.get('action', '').lower()
            try:
                action_type = ActionType(action_str)
            except ValueError:
                action_type = ActionType.WAIT

            return ScreenAction(
                action_type=action_type,
                x=data.get('x'),
                y=data.get('y'),
                text=data.get('text'),
                key=data.get('key'),
                amount=data.get('amount', 3),
                direction=data.get('direction', 'down'),
                wait_seconds=data.get('wait', 0.5),
                reason=data.get('reason', ''),
            )
        except Exception:
            pass

    # Fallback: keyword detection
    low = response.lower()
    if 'task complete' in low or 'goal achieved' in low or 'done' in low:
        return ScreenAction(ActionType.DONE, reason=response[:200])
    if 'cannot' in low or 'unable' in low or 'failed' in low or 'error' in low:
        return ScreenAction(ActionType.FAIL, reason=response[:200])

    return ScreenAction(ActionType.WAIT, wait_seconds=1.0, reason='Could not parse AI response')


# ── Main vision loop ──────────────────────────────────────────────────────────

def observe(save_path: str = '') -> ObservationFrame:
    """Take a screenshot and return an ObservationFrame."""
    path, w, h, err = _take_screenshot(save_path)
    if err:
        return ObservationFrame(
            timestamp=time.time(),
            screenshot_path='',
            width=0, height=0,
            error=err,
        )
    desc = _describe_screenshot_basic(path)
    return ObservationFrame(
        timestamp=time.time(),
        screenshot_path=path,
        width=w, height=h,
        description=desc,
    )


def build_vision_prompt(goal: str, frame: ObservationFrame, step: int,
                         history: List[str]) -> str:
    """Build the system/user prompt for the AI to reason about the screen."""
    hist_text = '\n'.join(f'  Step {i+1}: {h}' for i, h in enumerate(history[-5:]))
    prompt = f"""You are controlling a computer to achieve a goal. Observe the current screen state and decide the NEXT SINGLE action.

GOAL: {goal}

CURRENT SCREEN: {frame.description}
Screenshot: {frame.screenshot_path}
Step: {step}

RECENT ACTIONS:
{hist_text if hist_text else '  (none yet)'}

INSTRUCTIONS:
- Look at the screenshot carefully
- Determine what single action brings you closest to the goal
- Reply with a JSON block specifying the action

ACTION FORMAT (reply with exactly one JSON block):
```json
{{
  "action": "click|double_click|right_click|type|key|scroll|move|wait|screenshot|done|fail",
  "x": <screen x coordinate if needed>,
  "y": <screen y coordinate if needed>,
  "text": "<text to type if action=type>",
  "key": "<key name if action=key, e.g. enter, ctrl+a, tab>",
  "amount": <scroll amount if action=scroll>,
  "direction": "up|down",
  "wait": <seconds if action=wait>,
  "reason": "<brief explanation>"
}}
```

If the goal is achieved, use action="done". If it's impossible, use action="fail".
Output ONLY the JSON block, nothing else.
"""
    return prompt


def run_vision_cycle(
    goal: str,
    ai_call_fn=None,
    max_steps: int = 20,
    step_delay: float = 0.5,
    verbose: bool = True,
) -> VisionCycle:
    """
    Run a complete observation-reasoning-action-verification cycle.

    Args:
        goal: The natural language task to accomplish on screen
        ai_call_fn: Callable(prompt: str) -> str — the AI provider to use for reasoning
        max_steps: Maximum actions before giving up
        step_delay: Pause between steps
        verbose: Print progress

    Returns:
        VisionCycle with full history of what happened
    """
    cycle = VisionCycle(goal=goal, max_steps=max_steps)
    action_history: List[str] = []

    if verbose:
        print(f'\n[ScreenVision] Goal: {goal}')
        print(f'[ScreenVision] Max steps: {max_steps}')

    for step in range(max_steps):
        cycle.step = step + 1

        # OBSERVE
        frame = observe()
        cycle.observations.append(frame)

        if frame.error:
            cycle.failed = True
            cycle.failure_reason = f'Cannot observe screen: {frame.error}'
            if verbose:
                print(f'[ScreenVision] FAIL (observe): {frame.error}')
            break

        if verbose:
            print(f'[ScreenVision] Step {step+1}: {frame.description}')

        # UNDERSTAND + PLAN (via AI)
        if ai_call_fn is not None:
            prompt = build_vision_prompt(goal, frame, step + 1, action_history)
            try:
                ai_response = ai_call_fn(prompt)
            except Exception as e:
                ai_response = f'AI error: {e}'
        else:
            # No AI: just take a screenshot each step and stop
            ai_response = '{"action": "screenshot", "reason": "no AI provider configured"}'

        if verbose:
            print(f'[ScreenVision] AI: {ai_response[:120]}')

        # Parse action
        action = _parse_ai_action_response(ai_response)
        if action is None:
            action = ScreenAction(ActionType.WAIT, wait_seconds=1.0, reason='parse failed')

        cycle.actions_taken.append(action)

        # Terminal conditions
        if action.action_type == ActionType.DONE:
            cycle.completed = True
            cycle.current_state = action.reason or 'Goal achieved'
            if verbose:
                print(f'[ScreenVision] DONE: {cycle.current_state}')
            break

        if action.action_type == ActionType.FAIL:
            cycle.failed = True
            cycle.failure_reason = action.reason or 'AI reported failure'
            if verbose:
                print(f'[ScreenVision] FAIL: {cycle.failure_reason}')
            break

        # ACT
        result = _execute_action(action)
        action_history.append(f'{action.action_type.value}({action.reason}) → {result}')

        if verbose:
            print(f'[ScreenVision] Action: {action.action_type.value} → {result}')

        # VERIFY: wait for screen to settle
        time.sleep(step_delay)

    else:
        # Exceeded max steps
        cycle.failed = True
        cycle.failure_reason = f'Exceeded max steps ({max_steps})'
        if verbose:
            print(f'[ScreenVision] TIMEOUT after {max_steps} steps')

    return cycle


# ── Standalone tool functions (registered in agent.py TOOLS) ──────────────────

def tool_screen_observe(save_path: str = '') -> str:
    """Take a screenshot and return observation info."""
    frame = observe(save_path)
    if frame.error:
        return f'ERROR: {frame.error}'
    return (f'Screenshot: {frame.screenshot_path}\n'
            f'Size: {frame.width}x{frame.height}\n'
            f'Description: {frame.description}')


def tool_screen_find_element(description: str, screenshot_path: str = '') -> str:
    """
    Describe a UI element to find on screen.
    Returns approximate location description.
    Requires a screenshot path or takes one automatically.
    """
    if not screenshot_path:
        frame = observe()
        if frame.error:
            return f'ERROR: {frame.error}'
        screenshot_path = frame.screenshot_path

    if not os.path.exists(screenshot_path):
        return f'ERROR: Screenshot not found: {screenshot_path}'

    # Basic OCR attempt via pytesseract
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(screenshot_path)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        matches = []
        for i, word in enumerate(data['text']):
            if word and description.lower() in word.lower():
                conf = int(data['conf'][i])
                if conf > 30:
                    x = data['left'][i] + data['width'][i] // 2
                    y = data['top'][i] + data['height'][i] // 2
                    matches.append(f'"{word}" at ({x},{y}) conf={conf}%')
        if matches:
            return 'Found: ' + '; '.join(matches[:5])
        return f'Element not found: {description!r}'
    except ImportError:
        return f'OCR not available (pip install pytesseract). Screenshot: {screenshot_path}'
    except Exception as e:
        return f'ERROR: {e}'


def tool_screen_click_element(description: str) -> str:
    """Take a screenshot, find a UI element by description text, and click it."""
    frame = observe()
    if frame.error:
        return f'ERROR taking screenshot: {frame.error}'

    result = tool_screen_find_element(description, frame.screenshot_path)
    if result.startswith('Found:'):
        # Extract first coordinate pair
        coord_match = re.search(r'\((\d+),(\d+)\)', result)
        if coord_match and _pag:
            x, y = int(coord_match.group(1)), int(coord_match.group(2))
            _pag.click(x, y)
            return f'Clicked "{description}" at ({x},{y})'
        return f'Found element but could not click: {result}'
    return result


def tool_screen_wait_for(description: str, timeout: float = 10.0,
                          interval: float = 1.0) -> str:
    """Wait until a UI element matching description appears on screen."""
    start = time.time()
    while time.time() - start < timeout:
        frame = observe()
        if not frame.error:
            result = tool_screen_find_element(description, frame.screenshot_path)
            if result.startswith('Found:'):
                return f'Element appeared after {time.time()-start:.1f}s: {result}'
        time.sleep(interval)
    return f'Timeout after {timeout}s: element not found: {description!r}'


def tool_screen_automation_status() -> str:
    """Return current screen automation capability status."""
    lines = [
        f'pyautogui: {"✓ available" if _pag else "✗ not installed (pip install pyautogui)"}',
        f'Pillow: {"✓ available" if _PIL else "✗ not installed (pip install Pillow)"}',
    ]
    try:
        import pytesseract
        lines.append('pytesseract: ✓ available')
    except ImportError:
        lines.append('pytesseract: ✗ not installed (pip install pytesseract)')

    import platform
    p = platform.system()
    has_display = bool(
        os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
        or p in ('Darwin', 'Windows')
    )
    lines.append(f'Display: {"✓ detected" if has_display else "✗ no display (headless)"}')
    lines.append(f'Platform: {p}')
    return '\n'.join(lines)


# ── Module-level exports ───────────────────────────────────────────────────────

VISION_TOOLS = {
    'screen_observe':      tool_screen_observe,
    'screen_find_element': tool_screen_find_element,
    'screen_click_element':tool_screen_click_element,
    'screen_wait_for':     tool_screen_wait_for,
    'screen_status':       tool_screen_automation_status,
}
