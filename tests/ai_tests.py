# Devin/tests/ai_tests.py
# Purpose: An integration test suite for the AIAgent, verifying its logic for
#          provider routing, persona management, and tool-use parsing.

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
    from modules.ai_connector import AIRequest, AIResponse
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
    Tests the AIAgent's internal logic using mocked AI connectors.
    """

    def setUp(self):
        """
        Set up mocks for all AI connectors before each test.
        This isolates the AIAgent from real network calls.
        """
        # We patch the class in the module where it's *imported*
        self.patcher_openai = patch('modules.all_ais_modules.OpenAIConnector')
        self.patcher_gemini = patch('modules.all_ais_modules.GeminiConnector')
        self.patcher_perplexity = patch('modules.all_ais_modules.PerplexityConnector')

        self.MockOpenAIConnector = self.patcher_openai.start()
        self.MockGeminiConnector = self.patcher_gemini.start()
        self.MockPerplexityConnector = self.patcher_perplexity.start()

        # Get a handle on the mock *instances* that will be created
        self.mock_openai_instance = self.MockOpenAIConnector.return_value
        self.mock_gemini_instance = self.MockGeminiConnector.return_value
        self.mock_perplexity_instance = self.MockPerplexityConnector.return_value

        # Instantiate the AIAgent. It will now be initialized with our mocks.
        self.agent = AIAgent(
            openai_api_key="fake-key",
            gemini_api_key="fake-key",
            perplexity_api_key="fake-key"
        )

    def tearDown(self):
        """Stop all patches after each test."""
        patch.stopall()

    def test_agent_routes_to_correct_provider(self):
        """
        Verify that the agent calls the correct connector based on the provider enum.
        """
        print("\n\n--- Testing AI Provider Routing ---")
        messages = [{"role": "user", "content": "test"}]
        
        # Configure mocks to return their name
        self.mock_openai_instance.get_chat_completion.return_value = AIResponse("OpenAI Response", True)
        self.mock_gemini_instance.get_chat_completion.return_value = AIResponse("Gemini Response", True)
        self.mock_perplexity_instance.get_chat_completion.return_value = AIResponse("Perplexity Response", True)

        # Test OpenAI routing
        self.agent.get_general_chat_response(messages, provider=AIProvider.OPENAI)
        self.mock_openai_instance.get_chat_completion.assert_called_once()
        self.mock_gemini_instance.get_chat_completion.assert_not_called()
        self.mock_perplexity_instance.get_chat_completion.assert_not_called()
        print("  [SUCCESS] Correctly routed to OpenAI.")

        # Test Gemini routing
        self.mock_openai_instance.reset_mock() # Reset call counts
        self.agent.get_general_chat_response(messages, provider=AIProvider.GEMINI)
        self.mock_openai_instance.get_chat_completion.assert_not_called()
        self.mock_gemini_instance.get_chat_completion.assert_called_once()
        self.mock_perplexity_instance.get_chat_completion.assert_not_called()
        print("  [SUCCESS] Correctly routed to Gemini.")

    def test_agent_injects_correct_pentesting_persona(self):
        """
        Verify that get_pentesting_chat_response prepends the correct system prompt.
        """
        print("\n\n--- Testing Pentesting Persona Injection ---")
        user_messages = [{"role": "user", "content": "scan the target"}]
        
        # We don't care about the response, only what was sent
        self.mock_openai_instance.get_chat_completion.return_value = AIResponse("OK", True)
        
        self.agent.get_pentesting_chat_response(user_messages)
        
        # Check that the connector was called
        self.mock_openai_instance.get_chat_completion.assert_called_once()
        
        # Get the AIRequest object that was passed to the mock connector
        sent_request: AIRequest = self.mock_openai_instance.get_chat_completion.call_args[0][0]
        sent_messages = sent_request.messages
        
        # Assert that the first message is now a system prompt
        self.assertEqual(sent_messages[0]['role'], 'system')
        # Assert that the system prompt contains keywords for the pentesting persona
        system_prompt = sent_messages[0]['content']
        self.assertIn("ethical hacker", system_prompt.lower())
        self.assertIn("penetration testing", system_prompt.lower())
        self.assertIn("Metasploit", system_prompt)
        # Assert that the user's message is still there
        self.assertEqual(sent_messages[1], user_messages[0])
        print("  [SUCCESS] Correctly prepended the pentesting system prompt.")

    def test_agent_correctly_parses_valid_tool_selection_json(self):
        """
        Verify that a valid JSON string for a tool call is correctly parsed.
        """
        print("\n\n--- Testing Valid Tool Selection Parsing ---")
        valid_json_response = json.dumps({
            "tool": "execute_shell",
            "parameters": {"command": "nmap -sV 127.0.0.1"}
        })
        self.mock_openai_instance.get_chat_completion.return_value = AIResponse(valid_json_response, True)
        
        result = self.agent.get_tool_selection_response([], [])
        
        expected_dict = {
            "tool": "execute_shell",
            "parameters": {"command": "nmap -sV 127.0.0.1"}
        }
        self.assertEqual(result, expected_dict)
        print("  [SUCCESS] Correctly parsed valid JSON from LLM.")

    def test_agent_handles_malformed_tool_selection_json(self):
        """
        Verify that malformed JSON from the LLM is handled gracefully and returns None.
        """
        print("\n\n--- Testing Malformed Tool Selection Parsing ---")
        # This JSON has a trailing comma, which is invalid
        malformed_json_response = '{"tool": "execute_shell", "parameters": {"command": "nmap -sV 127.0.0.1"},}'
        self.mock_openai_instance.get_chat_completion.return_value = AIResponse(malformed_json_response, True)
        
        result = self.agent.get_tool_selection_response([], [])
        
        self.assertIsNone(result, "Expected None for malformed JSON, but got a result.")
        print("  [SUCCESS] Correctly returned None for malformed JSON from LLM.")

if __name__ == '__main__':
    # Re-enable logging for the test runner's output
    logging.disable(logging.NOTSET)
    unittest.main()
