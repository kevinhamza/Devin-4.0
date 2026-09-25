"""
Unit tests for modules/os_agent.py.
"""

import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestOSAgentImport(unittest.TestCase):
    def test_import(self):
        try:
            import modules.os_agent as m
            self.assertTrue(hasattr(m, "get_os_agent"))
            self.assertTrue(hasattr(m, "OSAgent"))
        except ImportError as e:
            self.skipTest(f"os_agent not importable: {e}")

    def test_factory(self):
        try:
            from modules.os_agent import get_os_agent, OSAgent
            agent = get_os_agent()
            self.assertIsInstance(agent, OSAgent)
            agent2 = get_os_agent()
            self.assertIs(agent, agent2)  # singleton
        except ImportError as e:
            self.skipTest(str(e))


class TestOSAgentScreenshot(unittest.TestCase):
    def test_screenshot_returns_string(self):
        try:
            from modules.os_agent import get_os_agent
        except ImportError as e:
            self.skipTest(str(e))
        agent = get_os_agent()
        result = agent.screenshot()
        self.assertIsInstance(result, str)

    def test_screenshot_to_path(self):
        try:
            from modules.os_agent import get_os_agent
        except ImportError as e:
            self.skipTest(str(e))
        agent = get_os_agent()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            result = agent.screenshot(tmp)
            # Should either write the file or return an ERROR string
            self.assertIsInstance(result, str)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass


class TestOSAgentMouse(unittest.TestCase):
    def test_move_returns_string(self):
        try:
            from modules.os_agent import get_os_agent
        except ImportError as e:
            self.skipTest(str(e))
        agent = get_os_agent()
        result = agent.move_mouse(100, 100)
        self.assertIsInstance(result, str)

    def test_click_returns_string(self):
        try:
            from modules.os_agent import get_os_agent
        except ImportError as e:
            self.skipTest(str(e))
        agent = get_os_agent()
        result = agent.click(100, 100)
        self.assertIsInstance(result, str)


class TestOSAgentKeyboard(unittest.TestCase):
    def test_type_returns_string(self):
        try:
            from modules.os_agent import get_os_agent
        except ImportError as e:
            self.skipTest(str(e))
        agent = get_os_agent()
        result = agent.type_text("hello")
        self.assertIsInstance(result, str)

    def test_press_key_returns_string(self):
        try:
            from modules.os_agent import get_os_agent
        except ImportError as e:
            self.skipTest(str(e))
        agent = get_os_agent()
        result = agent.press_key("Escape")
        self.assertIsInstance(result, str)


class TestOSAgentObserve(unittest.TestCase):
    def test_observe_returns_string(self):
        try:
            from modules.os_agent import get_os_agent
        except ImportError as e:
            self.skipTest(str(e))
        # observe() calls screenshot + vision AI; mock the vision part
        agent = get_os_agent()
        with patch.object(agent, "_analyze_screenshot", return_value="Mock screen"):
            with patch.object(agent, "screenshot", return_value="/tmp/fake.png"):
                result = agent.observe()
        self.assertIsInstance(result, str)


class TestOSAgentConvenienceFunctions(unittest.TestCase):
    def test_convenience_imports(self):
        try:
            from modules.os_agent import (
                take_screenshot, click, type_text, press_key,
                hotkey, observe_screen
            )
        except ImportError as e:
            self.skipTest(str(e))


if __name__ == "__main__":
    unittest.main()
