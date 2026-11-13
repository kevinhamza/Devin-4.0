"""
Unit tests for modules/os_agent.py.

These run against a fake desktop. The real backends move the real pointer and press
real keys, so a test suite must never be allowed to reach them.
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import os_automation as oa  # noqa: E402
from modules import os_agent  # noqa: E402
from modules.os_agent import ActionResult, OSAgent, get_os_agent  # noqa: E402


class FakeDesktop:
    """Records what it was asked to do instead of doing it."""
    backend = 'fake'

    def __init__(self, changes=True):
        self.calls = []
        self.changes = changes

    def size(self):
        return (1280, 720)

    def capture(self):
        from PIL import Image
        return Image.new('RGB', (1280, 720), (30, 30, 30))

    def elements(self, budget=1.5, limit=160):
        return {'window': 'Fake Window', 'app': 'fake', 'elements': [
            {'role': 'push button', 'name': 'OK', 'x': 600, 'y': 400, 'w': 80, 'h': 30},
            {'role': 'entry', 'name': 'Search', 'x': 200, 'y': 100, 'w': 400, 'h': 30, 'focused': True},
        ]}

    def settle(self, **kw):
        return {'stable': True, 'changed': self.changes, 'change': 0.1 if self.changes else 0.0, 'waited': 0.0}

    def mark(self):
        self.calls.append(('mark',))

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, *args))
        return record


class OSAgentTestCase(unittest.TestCase):
    def setUp(self):
        self.desk = FakeDesktop()
        patcher = patch.object(oa, 'get_desktop', return_value=self.desk)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.agent = OSAgent()


class TestFactory(unittest.TestCase):
    def test_singleton(self):
        self.assertIsInstance(get_os_agent(), OSAgent)
        self.assertIs(get_os_agent(), get_os_agent())

    def test_convenience_functions_exist(self):
        for name in ('take_screenshot', 'click', 'type_text', 'press_key', 'hotkey', 'observe_screen', 'run_task'):
            self.assertTrue(callable(getattr(os_agent, name)), name)


class TestSeeing(OSAgentTestCase):
    def test_screenshot_saves_to_given_path(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'shot.png')
            result = self.agent.screenshot(path)
            self.assertTrue(result.success)
            self.assertTrue(os.path.getsize(path) > 0)
            self.assertEqual(result.screenshot_after, path)

    def test_observe_lists_what_is_on_screen(self):
        text = self.agent.observe()
        self.assertIn('Fake Window', text)
        self.assertIn('"OK"', text)
        self.assertIn('keyboard focus', text)

    def test_find_element_returns_centre(self):
        self.assertEqual(self.agent.find_element('ok'), (640, 415))
        self.assertIsNone(self.agent.find_element('no such thing'))


class TestActing(OSAgentTestCase):
    def test_click_reaches_the_desktop(self):
        result = self.agent.click(100, 200)
        self.assertIsInstance(result, ActionResult)
        self.assertIn(('click', 100, 200, 'left', 1), self.desk.calls)
        self.assertTrue(result.data['changed'])

    def test_click_reports_when_nothing_happened(self):
        self.desk.changes = False
        result = self.agent.click(100, 200)
        self.assertFalse(result.data['changed'])
        self.assertIn('nothing changed', result.message)

    def test_type_and_keys(self):
        self.agent.type_text('hello')
        self.agent.press_key('Escape')
        self.agent.hotkey('ctrl', 'l')
        names = [c[0] for c in self.desk.calls]
        self.assertEqual(names.count('type'), 1)
        self.assertIn(('key', 'Escape'), self.desk.calls)
        self.assertIn(('key', 'ctrl+l'), self.desk.calls)

    def test_click_element_by_name(self):
        self.assertTrue(self.agent.click_element('OK').success)
        self.assertIn(('click', 640, 415, 'left', 1), self.desk.calls)
        self.assertFalse(self.agent.click_element('missing').success)

    def test_history_is_recorded(self):
        self.agent.move_mouse(5, 5)
        self.assertEqual(self.agent.get_history()[-1]['action'], 'move_mouse')
        self.assertIn('move_mouse', self.agent.last_action_summary())


class TestKeyNames(unittest.TestCase):
    def test_combos_are_normalised(self):
        self.assertEqual(oa.split_combo('Ctrl+Shift+T'), ['ctrl', 'shift', 't'])
        self.assertEqual(oa.split_combo('Enter'), ['return'])
        self.assertEqual(oa.split_combo('PgDn'), ['page_down'])
        self.assertEqual(oa.normalize_key('Esc'), 'escape')

    def test_keysyms(self):
        self.assertEqual(oa.keysym_for('enter'), 0xFF0D)
        self.assertEqual(oa.char_keysym('a'), ord('a'))
        self.assertEqual(oa.char_keysym('\n'), 0xFF0D)
        self.assertEqual(oa.char_keysym('€'), 0x01000000 + ord('€'))


if __name__ == '__main__':
    unittest.main()
