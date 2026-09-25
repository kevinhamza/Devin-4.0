"""
Unit tests for modules/reasoning_engine.py.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestReasoningEngineImport(unittest.TestCase):
    def test_import(self):
        try:
            import modules.reasoning_engine as m
            self.assertTrue(hasattr(m, "get_reasoning_engine"))
            self.assertTrue(hasattr(m, "ReasoningEngine"))
            self.assertTrue(hasattr(m, "think"))
        except ImportError as e:
            self.skipTest(str(e))

    def test_singleton(self):
        try:
            from modules.reasoning_engine import get_reasoning_engine, ReasoningEngine
        except ImportError as e:
            self.skipTest(str(e))
        engine = get_reasoning_engine()
        engine2 = get_reasoning_engine()
        self.assertIs(engine, engine2)


class TestReasoningEngineToolRegistration(unittest.TestCase):
    def test_register_tool(self):
        try:
            from modules.reasoning_engine import get_reasoning_engine
        except ImportError as e:
            self.skipTest(str(e))
        engine = get_reasoning_engine()
        engine.register_tool(
            name="test_add",
            fn=lambda a, b: str(int(a) + int(b)),
            description="Add two numbers",
            params={"a": "first number", "b": "second number"},
        )
        self.assertIn("test_add", engine._tools)


class TestReasoningEngineThink(unittest.TestCase):
    def _mock_provider(self, text="The answer is 4.", tool_calls=None):
        return MagicMock(return_value=(text, tool_calls or [], "mock-model"))

    def test_think_returns_result(self):
        try:
            from modules.reasoning_engine import get_reasoning_engine, ReasoningResult
        except ImportError as e:
            self.skipTest(str(e))
        engine = get_reasoning_engine()
        with patch("modules.reasoning_engine._call_best_available", self._mock_provider()):
            result = engine.think("What is 2+2?")
        self.assertIsInstance(result, ReasoningResult)
        self.assertIsInstance(result.answer, str)

    def test_think_with_tool_call(self):
        try:
            from modules.reasoning_engine import get_reasoning_engine, ReasoningResult
        except ImportError as e:
            self.skipTest(str(e))
        engine = get_reasoning_engine()
        called = []

        def calc(expression):
            called.append(expression)
            return "42"

        engine.register_tool(
            name="calc",
            fn=calc,
            description="Calculate expression",
            params={"expression": "math expression"},
        )
        # First call returns a tool call, second returns final answer
        responses = [
            ("Let me calculate.", [{"name": "calc", "input": {"expression": "6*7"}}], "mock"),
            ("The answer is 42.", [], "mock"),
        ]
        iter_resp = iter(responses)
        with patch("modules.reasoning_engine._call_best_available", side_effect=lambda *a, **kw: next(iter_resp)):
            result = engine.think("What is 6 times 7?")
        self.assertIsInstance(result, ReasoningResult)


class TestReasoningEngineChat(unittest.TestCase):
    def test_chat_returns_string(self):
        try:
            from modules.reasoning_engine import get_reasoning_engine
        except ImportError as e:
            self.skipTest(str(e))
        engine = get_reasoning_engine()
        with patch(
            "modules.reasoning_engine._call_best_available",
            return_value=("Hello, I am Devin.", [], "mock"),
        ):
            reply = engine.chat("Hello!")
        self.assertIsInstance(reply, str)
        self.assertTrue(len(reply) > 0)


class TestReasoningEngineDataclasses(unittest.TestCase):
    def test_thought_step(self):
        try:
            from modules.reasoning_engine import ThoughtStep
        except ImportError as e:
            self.skipTest(str(e))
        step = ThoughtStep(
            thought="I need to calculate.",
            action="calc",
            action_input={"expression": "2+2"},
            observation="4",
            is_final=False,
        )
        self.assertEqual(step.action, "calc")

    def test_reasoning_result(self):
        try:
            from modules.reasoning_engine import ReasoningResult
        except ImportError as e:
            self.skipTest(str(e))
        result = ReasoningResult(
            answer="4",
            steps=[],
            tool_calls=[],
            model_used="mock",
            success=True,
            error=None,
        )
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()
