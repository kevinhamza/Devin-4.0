"""
modules/os_agent.py — object-style access to Devin's computer control.

`OSAgent` is a thin facade. The real work lives in two places:

    modules/os_automation.py   pointer, keyboard, screen capture  (the hands and eyes)
    modules/screen_vision.py   look → think → act → check loop     (the universal agent)

Nothing here knows about any particular application: there are no pixel
coordinates, no per-site helpers. Anything that needs judgement ("search the web
for…", "open that link") goes through `run_task`, where the model looks at the
screen and decides each click and keystroke itself.
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    from modules import os_automation as oa
except ImportError:  # loaded as a top-level module
    import os_automation as oa  # type: ignore


@dataclass
class ActionResult:
    success: bool
    message: str
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    vision_result: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    # Names used by older callers.
    @property
    def vision_analysis(self) -> Optional[str]:
        return self.vision_result

    @property
    def after_screenshot(self) -> Optional[str]:
        return self.screenshot_after

    def __str__(self) -> str:
        return self.message


def _sv():
    try:
        from modules import screen_vision
    except ImportError:
        import screen_vision  # type: ignore
    return screen_vision


class OSAgent:
    """See the screen and operate the mouse and keyboard."""

    def __init__(self, vision_provider: Any = None, take_verification_shots: bool = True):
        self._vision_provider = vision_provider
        self._verify = take_verification_shots
        self._history: List[Dict[str, Any]] = []

    @property
    def desktop(self) -> oa.Desktop:
        return oa.get_desktop()

    # ── bookkeeping ──
    def _done(self, action: str, params: Dict[str, Any], message: str, settle: Optional[Dict[str, Any]] = None,
              success: bool = True, **extra: Any) -> ActionResult:
        data: Dict[str, Any] = dict(extra)
        if settle is not None:
            data['changed'] = bool(settle.get('changed'))
            data['stable'] = bool(settle.get('stable', True))
            message += ' — the screen changed' if data['changed'] else ' — nothing changed on the screen'
        result = ActionResult(success, message, data=data)
        self._history.append({'action': action, 'params': params, 'success': success,
                              'message': message, 'ts': time.time()})
        return result

    def _guard(self, action: str, params: Dict[str, Any], fn) -> ActionResult:
        try:
            return fn()
        except oa.DesktopError as e:
            return self._done(action, params, f'{action} failed: {e}', success=False)

    # ── seeing ──
    def _analyze_screenshot(self, image_path: str, prompt: str) -> str:
        """Describe a saved screenshot with the caller's provider, or with the local model."""
        if self._vision_provider is not None:
            return str(self._vision_provider(image_path, prompt))
        return _sv().describe_screen(prompt)

    def screenshot(self, prompt_or_path: str = '') -> ActionResult:
        """Capture the screen. Pass a file path to save it there, or a question to have it described."""
        def go() -> ActionResult:
            arg = str(prompt_or_path or '')
            is_path = arg.lower().endswith(('.png', '.jpg', '.jpeg')) or (os.sep in arg and ' ' not in arg)
            obs = _sv().look(self.desktop)
            path = arg if is_path else oa._tmp_path(f'shot_{int(time.time() * 1000)}.png')
            obs.save(path)
            description = obs.describe()
            if arg and not is_path:
                description = self._analyze_screenshot(path, arg)
            result = self._done('screenshot', {'arg': arg}, f'Screenshot saved: {path}')
            result.screenshot_before = result.screenshot_after = path
            result.vision_result = description
            return result
        return self._guard('screenshot', {}, go)

    def observe(self, prompt: str = '') -> str:
        """What is on the screen right now, as text. With a question, the model answers it."""
        result = self.screenshot(prompt)
        if getattr(result, 'vision_result', None):
            return str(result.vision_result)
        return str(getattr(result, 'message', result))

    def find_element(self, description: str) -> Optional[Tuple[int, int]]:
        """Centre of the first on-screen element whose name contains `description`."""
        needle = str(description).lower()
        try:
            for e in _sv().look(self.desktop).elements:
                if needle in (e.name + ' ' + e.value).lower():
                    return e.center
        except oa.DesktopError:
            pass
        return None

    # ── pointer ──
    def click(self, x: int, y: int, button: str = 'left', count: int = 1) -> ActionResult:
        def go() -> ActionResult:
            self.desktop.click(x, y, button, count)
            return self._done('click', {'x': x, 'y': y, 'button': button, 'count': count},
                              f'Clicked {button} at ({int(x)},{int(y)})',
                              self.desktop.settle(quiet=0.5, timeout=8, expect=1.5) if self._verify else None)
        return self._guard('click', {'x': x, 'y': y}, go)

    def double_click(self, x: int, y: int) -> ActionResult:
        return self.click(x, y, count=2)

    def right_click(self, x: int, y: int) -> ActionResult:
        return self.click(x, y, button='right')

    def move_mouse(self, x: int, y: int) -> ActionResult:
        def go() -> ActionResult:
            self.desktop.move(x, y)
            return self._done('move_mouse', {'x': x, 'y': y}, f'Moved the pointer to ({int(x)},{int(y)})')
        return self._guard('move_mouse', {'x': x, 'y': y}, go)

    def scroll(self, x: int, y: int, direction: str = 'down', amount: int = 3) -> ActionResult:
        def go() -> ActionResult:
            n = abs(int(amount))
            self.desktop.scroll(dy=n if direction == 'down' else -n if direction == 'up' else 0,
                                dx=n if direction == 'right' else -n if direction == 'left' else 0, x=x, y=y)
            return self._done('scroll', {'direction': direction, 'amount': n}, f'Scrolled {direction} {n}',
                              self.desktop.settle(quiet=0.4, timeout=5, expect=1.0) if self._verify else None)
        return self._guard('scroll', {}, go)

    def drag(self, x1: int, y1: int, x2: int, y2: int) -> ActionResult:
        def go() -> ActionResult:
            self.desktop.drag(x1, y1, x2, y2)
            return self._done('drag', {'from': (x1, y1), 'to': (x2, y2)},
                              f'Dragged ({int(x1)},{int(y1)}) to ({int(x2)},{int(y2)})',
                              self.desktop.settle(quiet=0.5, timeout=6, expect=1.2) if self._verify else None)
        return self._guard('drag', {}, go)

    def click_element(self, description: str) -> ActionResult:
        spot = self.find_element(description)
        if spot is None:
            return self._done('click_element', {'description': description},
                              f'Nothing on screen is called "{description}"', success=False)
        return self.click(*spot)

    # ── keyboard ──
    def type_text(self, text: str, interval: Optional[float] = None) -> ActionResult:
        def go() -> ActionResult:
            self.desktop.type(str(text), interval)
            return self._done('type_text', {'text': str(text)[:200]}, f'Typed {len(str(text))} characters',
                              self.desktop.settle(quiet=0.3, timeout=4, expect=1.0) if self._verify else None)
        return self._guard('type_text', {}, go)

    def press_key(self, key: str) -> ActionResult:
        def go() -> ActionResult:
            self.desktop.key(str(key))
            return self._done('press_key', {'key': key}, f'Pressed {key}',
                              self.desktop.settle(quiet=0.5, timeout=8, expect=1.2) if self._verify else None)
        return self._guard('press_key', {'key': key}, go)

    def hotkey(self, *keys: str) -> ActionResult:
        return self.press_key('+'.join(keys))

    def type_into(self, field_description: str, text: str) -> ActionResult:
        clicked = self.click_element(field_description)
        return self.type_text(text) if clicked.success else clicked

    # ── clipboard ──
    def get_clipboard(self) -> str:
        return oa.clipboard_get()

    def set_clipboard(self, text: str) -> ActionResult:
        oa.clipboard_set(text)
        return self._done('set_clipboard', {}, f'Clipboard set ({len(str(text))} characters)')

    def paste_clipboard(self) -> ActionResult:
        return self.hotkey('super' if oa.PLATFORM == 'Darwin' else 'ctrl', 'v')

    # ── windows and applications ──
    def open_application(self, name: str) -> ActionResult:
        def go() -> ActionResult:
            self.desktop.mark()
            message = oa.open_application(str(name))
            if message.startswith('No installed application'):
                return self._done('open_application', {'name': name}, message, success=False)
            return self._done('open_application', {'name': name}, message,
                              self.desktop.settle(quiet=0.8, timeout=15, expect=10, min_change=0.02))
        return self._guard('open_application', {'name': name}, go)

    open_app_by_name = open_application

    def focus_window(self, title: str) -> ActionResult:
        message = oa.focus_window(title)
        return self._done('focus_window', {'title': title}, message, success=message.startswith('Focused'))

    def list_windows(self) -> List[Dict[str, Any]]:
        return [{'title': line} for line in oa.list_windows().splitlines() if line.strip()]

    def close_window(self) -> ActionResult:
        return self.hotkey('alt', 'f4')

    def minimize_window(self) -> ActionResult:
        return self.hotkey('super', 'h')

    def maximize_window(self) -> ActionResult:
        return self.hotkey('super', 'up')

    def dismiss_dialog(self, *_: Any, **__: Any) -> bool:
        return self.press_key('escape').success

    # ── anything that needs judgement: hand it to the universal loop ──
    def run_task(self, goal: str, max_steps: Optional[int] = None, on_event: Any = None) -> ActionResult:
        """Carry out a task by looking at the screen and choosing each action with the model."""
        result = _sv().ComputerAgent(desktop=self.desktop, on_event=on_event, max_steps=max_steps).run(str(goal))
        out = ActionResult(result.success, result.answer, screenshot_after=result.screenshot or None,
                           vision_result=result.answer,
                           data={'steps': [f'{s.n}. {s.summary} -> {s.outcome}' for s in result.steps],
                                 'seconds': result.seconds})
        self._history.append({'action': 'run_task', 'params': {'goal': goal}, 'success': result.success,
                              'message': result.answer, 'ts': time.time()})
        return out

    def navigate_browser(self, url: str) -> ActionResult:
        return self.run_task(f'Open the web page {url} in the web browser.')

    def browser_address_bar(self, url: str) -> ActionResult:
        return self.run_task(f'In the web browser that is open, go to the address {url}.')

    def browser_search(self, query: str, images: bool = False) -> ActionResult:
        what = 'pictures of' if images else ''
        return self.run_task(f'Use the web browser to search the web for {what} {query}.'.replace('  ', ' '))

    def youtube_search(self, query: str) -> ActionResult:
        return self.run_task(f'Open YouTube in the web browser and search it for {query}.')

    def execute_task_with_vision(self, task: str, steps: Optional[List[Dict[str, Any]]] = None,
                                 max_retries: int = 0) -> str:
        """Run a scripted list of steps, or — with no steps — let the model work the task out."""
        if not steps:
            return self.run_task(task).message
        lines = []
        for i, step in enumerate(steps, start=1):
            action = step.get('action', '')
            try:
                if action in ('click', 'double_click', 'right_click'):
                    r = getattr(self, action)(step['x'], step['y'])
                elif action == 'type_text':
                    r = self.type_text(step['text'])
                elif action == 'press_key':
                    r = self.press_key(step['key'])
                elif action == 'hotkey':
                    r = self.hotkey(*step['keys'])
                elif action == 'scroll':
                    r = self.scroll(step.get('x', 0), step.get('y', 0), step.get('direction', 'down'),
                                    step.get('amount', 3))
                elif action == 'drag':
                    r = self.drag(step['x1'], step['y1'], step['x2'], step['y2'])
                elif action == 'open_application':
                    r = self.open_application(step['name'])
                elif action == 'wait':
                    time.sleep(float(step.get('seconds', 1)))
                    r = ActionResult(True, f'Waited {step.get("seconds", 1)}s')
                elif action == 'screenshot':
                    r = self.screenshot(step.get('prompt', ''))
                elif action in ('find_and_click', 'click_element'):
                    r = self.click_element(step['description'])
                elif action == 'type_into':
                    r = self.type_into(step['field'], step['text'])
                else:
                    r = ActionResult(False, f'Unknown action: {action}')
            except KeyError as e:
                r = ActionResult(False, f'{action} is missing {e}')
            lines.append(f'  {"ok" if r.success else "FAILED"}  step {i}: {action} — {r.message}')
        good = sum(1 for line in lines if line.startswith('  ok'))
        return f"Task '{task}': {good}/{len(lines)} steps succeeded\n" + '\n'.join(lines)

    # ── history ──
    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()

    def last_action_summary(self) -> str:
        if not self._history:
            return 'No actions taken yet'
        last = self._history[-1]
        return f'{last["action"]} -> {"ok" if last["success"] else "failed"}: {last["message"]}'


_agent: Optional[OSAgent] = None


def get_os_agent(vision_provider: Any = None) -> OSAgent:
    global _agent
    if _agent is None:
        _agent = OSAgent(vision_provider=vision_provider)
    return _agent


def take_screenshot(prompt: str = '') -> ActionResult:
    return get_os_agent().screenshot(prompt)


def click(x: int, y: int, button: str = 'left') -> ActionResult:
    return get_os_agent().click(x, y, button)


def type_text(text: str) -> ActionResult:
    return get_os_agent().type_text(text)


def press_key(key: str) -> ActionResult:
    return get_os_agent().press_key(key)


def hotkey(*keys: str) -> ActionResult:
    return get_os_agent().hotkey(*keys)


def open_app(name: str) -> ActionResult:
    return get_os_agent().open_application(name)


def observe_screen() -> str:
    return get_os_agent().observe()


def run_task(goal: str) -> ActionResult:
    return get_os_agent().run_task(goal)


for _alias in ('os_agent', 'modules.os_agent'):
    sys.modules.setdefault(_alias, sys.modules[__name__])
