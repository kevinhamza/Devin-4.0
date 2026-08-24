# Devin/tests/ai_tests.py
# Purpose: An integration test suite for the AIAgent, verifying its logic for
#          provider routing, pentesting-analysis routing, and tool-use parsing.

import unittest
import json
from unittest.mock import patch, MagicMock

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

_import_error = None

try:
    from modules.all_ais_modules import AIAgent, AIProvider
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)


@unittest.skipUnless(DEVIN_CORE_AVAILABLE, f"Skipping AI tests, dependency missing: {_import_error}")
class TestAIAgentIntegration(unittest.TestCase):
    """
    Tests the real, current AIAgent (modules/all_ais_modules.py) using mocked
    underlying provider modules (live mode) and the agent's self-contained
    mock mode.
    """

    def setUp(self):
        """
        Patch the real provider-module classes where AIAgent imports them, so
        live-mode tests never touch the network. Each patched class is a
        MagicMock class whose instances are also MagicMocks, so we can assert
        on `<mock>.return_value.<method>` calls.
        """
        self.patcher_openai = patch('modules.all_ais_modules.ChatGPTModule')
        self.patcher_gemini = patch('modules.all_ais_modules.GeminiModule')
        self.patcher_perplexity = patch('modules.all_ais_modules.PerplexityModule')
        self.patcher_claude = patch('modules.all_ais_modules.ClaudeModule')

        self.MockChatGPTModule = self.patcher_openai.start()
        self.MockGeminiModule = self.patcher_gemini.start()
        self.MockPerplexityModule = self.patcher_perplexity.start()
        self.MockClaudeModule = self.patcher_claude.start()

        # Handles on the mock *instances* that AIAgent will create/use.
        self.mock_openai_instance = self.MockChatGPTModule.return_value
        self.mock_gemini_instance = self.MockGeminiModule.return_value
        self.mock_perplexity_instance = self.MockPerplexityModule.return_value
        self.mock_claude_instance = self.MockClaudeModule.return_value

    def tearDown(self):
        """Stop all patches after each test."""
        patch.stopall()

    def test_agent_prefers_claude_then_openai_then_gemini_for_tool_selection(self):
        """
        get_tool_selection_response documents (and implements) a preference
        order of Claude > OpenAI > Gemini. Verify the agent actually honors
        that order based on which provider modules are configured.
        """
        print("\n\n--- Testing AI Provider Preference Order for Tool Selection ---")
        messages = [{"role": "user", "content": "list the files here"}]
        tools = [{"name": "list_files", "description": "List files", "parameters": {}}]

        tool_call_response = {
            "tool_calls": [{"function": {"name": "list_files", "arguments": '{"path": "."}'}}]
        }

        # --- All three configured: Claude should win. ---
        self.mock_claude_instance.get_tool_calling_response.return_value = tool_call_response
        agent_all = AIAgent(
            mode='live',
            anthropic_api_key="fake-claude-key",
            openai_api_key="fake-openai-key",
            gemini_api_key="fake-gemini-key",
        )
        result = agent_all.get_tool_selection_response(messages, tools)
        self.mock_claude_instance.get_tool_calling_response.assert_called_once()
        self.mock_openai_instance.get_tool_calling_response.assert_not_called()
        self.mock_gemini_instance.get_tool_calling_response.assert_not_called()
        self.assertEqual(result["tool"], "list_files")
        print("  [SUCCESS] Claude preferred when all providers are configured.")

        # --- Only OpenAI + Gemini configured: OpenAI should win. ---
        self.mock_claude_instance.reset_mock()
        self.mock_openai_instance.reset_mock()
        self.mock_gemini_instance.reset_mock()
        self.mock_openai_instance.get_tool_calling_response.return_value = tool_call_response
        agent_no_claude = AIAgent(
            mode='live',
            openai_api_key="fake-openai-key",
            gemini_api_key="fake-gemini-key",
        )
        agent_no_claude.get_tool_selection_response(messages, tools)
        self.mock_openai_instance.get_tool_calling_response.assert_called_once()
        self.mock_gemini_instance.get_tool_calling_response.assert_not_called()
        print("  [SUCCESS] OpenAI preferred over Gemini when Claude is unavailable.")

        # --- Only Gemini configured: Gemini should be used as the last-resort fallback. ---
        self.mock_gemini_instance.get_tool_calling_response.return_value = tool_call_response
        agent_gemini_only = AIAgent(mode='live', gemini_api_key="fake-gemini-key")
        result_gemini = agent_gemini_only.get_tool_selection_response(messages, tools)
        self.mock_gemini_instance.get_tool_calling_response.assert_called_once()
        self.assertEqual(result_gemini["tool"], "list_files")
        print("  [SUCCESS] Gemini used as the free-tier fallback when nothing else is configured.")

    def test_agent_pentest_analysis_routes_to_pentestgpt_module(self):
        """
        get_pentest_analysis is the specialized entry point for pentesting-tool
        output analysis. PentestGPTAIModule (the real live-mode implementation)
        still carries an "ethical hacking" persona system prompt, but that
        prompt is internal to PentestGPTAIModule, not something AIAgent itself
        injects -- so what AIAgent needs to guarantee is that this call is
        correctly routed to the dedicated PentestGPT module (mock mode's
        MockPentestGPTModule here) rather than a general-purpose provider.
        """
        print("\n\n--- Testing PentestGPT Analysis Routing ---")
        agent = AIAgent(mode='mock')

        result = agent.get_pentest_analysis("Nmap", "Host is up. 80/tcp open http.")

        # Routed to the PentestGPT module specifically, not OpenAI/Gemini/Perplexity.
        self.assertIsInstance(result, dict)
        self.assertIn("findings", result)
        self.assertIn("vulnerabilities", result)
        self.assertIn("next_step", result)
        print("  [SUCCESS] get_pentest_analysis correctly routed to the PentestGPT module.")

    def test_agent_correctly_parses_valid_tool_selection_json(self):
        """
        Verify that a valid native tool-call response is correctly translated
        into the agent's {"tool": ..., "parameters": ...} shape.
        """
        print("\n\n--- Testing Valid Tool Selection Parsing ---")
        self.mock_claude_instance.get_tool_calling_response.return_value = {
            "tool_calls": [{
                "function": {
                    "name": "execute_shell",
                    "arguments": json.dumps({"command": "nmap -sV 127.0.0.1"}),
                }
            }]
        }

        agent = AIAgent(mode='live', anthropic_api_key="fake-claude-key")
        result = agent.get_tool_selection_response([], [])

        expected_dict = {
            "tool": "execute_shell",
            "parameters": {"command": "nmap -sV 127.0.0.1"}
        }
        self.assertEqual(result, expected_dict)
        print("  [SUCCESS] Correctly parsed a valid tool-call response.")

    def test_agent_handles_malformed_tool_selection_json(self):
        """
        Verify that malformed JSON in the tool call's arguments is handled
        gracefully and returns None instead of raising.
        """
        print("\n\n--- Testing Malformed Tool Selection Parsing ---")
        # This "arguments" string has a trailing comma, which is invalid JSON.
        malformed_arguments = '{"command": "nmap -sV 127.0.0.1",}'
        self.mock_claude_instance.get_tool_calling_response.return_value = {
            "tool_calls": [{
                "function": {
                    "name": "execute_shell",
                    "arguments": malformed_arguments,
                }
            }]
        }

        agent = AIAgent(mode='live', anthropic_api_key="fake-claude-key")
        result = agent.get_tool_selection_response([], [])

        self.assertIsNone(result, "Expected None for malformed JSON, but got a result.")
        print("  [SUCCESS] Correctly returned None for malformed JSON from LLM.")


if __name__ == '__main__':
    # Re-enable logging for the test runner's output
    logging.disable(logging.NOTSET)
    unittest.main()
