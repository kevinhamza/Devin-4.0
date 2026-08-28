# Devin/tests/integration/test_automation_workflows.py
# Purpose: An end-to-end integration test for the full "Think-Act" loop,
#          verifying that the AIAgent and ToolExecutor can drive the
#          automation modules to perform complex workflows.

import unittest
import json
from unittest.mock import patch, MagicMock, call

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

_import_error = None

try:
    from modules.all_ais_modules import AIAgent, AIProvider
    from modules.tool_executor import ToolExecutor
    from modules.automation_tools import DesktopAutomator, WebAutomator
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)


def _tool_call_message(tool_name: str, parameters: dict) -> dict:
    """
    Builds a fake response in the shape ChatGPTModule.get_tool_calling_response
    actually returns: an OpenAI chat message dict (via response.model_dump())
    with a single native tool call.
    """
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{
            "id": "call_1",
            "type": "function",
            "function": {"name": tool_name, "arguments": json.dumps(parameters)},
        }],
    }


@unittest.skipUnless(DEVIN_CORE_AVAILABLE, f"Skipping integration tests, dependency missing: {_import_error}")
class TestEndToEndAutomation(unittest.TestCase):
    """
    Tests the full workflow from AI decision to automation execution.
    """

    def setUp(self):
        """
        Set up a complex mock environment that isolates the workflow logic.
        """
        # 1. Patch the lowest level: the hardware/browser interactors, and the
        # DEPS_AVAILABLE flag that gates whether DesktopAutomator wires up the
        # (mocked) KeyboardMouseController at all -- real selenium/pynput/
        # pyautogui aren't required to test the tool-dispatch logic.
        self.patcher_deps = patch('modules.automation_tools.DEPS_AVAILABLE', True)
        self.patcher_deps.start()
        self.patcher_pyautogui = patch('modules.automation_tools.pyautogui', MagicMock(), create=True)
        self.mock_pyautogui = self.patcher_pyautogui.start()
        self.mock_pyautogui.size.return_value = (1920, 1080)

        self.patcher_kbm = patch('modules.automation_tools.KeyboardMouseController')
        self.MockKBMController = self.patcher_kbm.start()
        self.mock_kbm_instance = self.MockKBMController.return_value

        self.patcher_browser = patch('modules.automation_tools.BrowserManager')
        self.MockBrowserManager = self.patcher_browser.start()
        self.mock_browser_instance = self.MockBrowserManager.return_value
        self.mock_driver = MagicMock()
        self.mock_browser_instance.get_driver.return_value = self.mock_driver

        # WebAutomator's locator-based methods reference selenium's `By`
        # class directly (e.g. By.TAG_NAME); stand in for it so those methods
        # work without selenium installed. The value matches selenium's real
        # By.TAG_NAME constant.
        class _FakeBy:
            TAG_NAME = "tag name"
        self.patcher_by = patch('modules.automation_tools.By', _FakeBy, create=True)
        self.patcher_by.start()

        # 2. Patch the external dependency: the AI Agent's underlying OpenAI
        # client. AIAgent wires this up as modules.all_ais_modules.ChatGPTModule
        # (not the separate, unrelated modules.ai_connector.OpenAIConnector).
        self.patcher_openai = patch('modules.all_ais_modules.ChatGPTModule')
        self.MockChatGPTModule = self.patcher_openai.start()
        self.mock_openai_instance = self.MockChatGPTModule.return_value

        # 3. Instantiate the REAL mid-level and high-level components
        self.desktop_automator = DesktopAutomator()
        self.web_automator = WebAutomator(browser_manager=self.mock_browser_instance)

        self.tool_executor = ToolExecutor(
            desktop_automator=self.desktop_automator,
            web_automator=self.web_automator
            # Other tools would be added here in a full run
        )
        self.agent = AIAgent(openai_api_key="fake-key")

    def tearDown(self):
        """Stop all patches after each test."""
        patch.stopall()

    def test_e2e_desktop_workflow_open_calculator(self):
        """
        Verify the full chain for a desktop automation task.
        User -> Agent (mocked LLM) -> ToolExecutor -> DesktopAutomator -> KBMController (mocked)
        """
        print("\n\n--- Testing E2E Desktop Workflow: 'Open Calculator' ---")
        user_prompt = "Please open the calculator for me."

        # 1. Configure the mock LLM to return a specific tool call
        self.mock_openai_instance.get_tool_calling_response.return_value = _tool_call_message(
            "open_application", {"app_name": "calculator"}
        )

        # 2. THINK: The agent formulates the plan
        tool_call_dict = self.agent.get_tool_selection_response([{"role": "user", "content": user_prompt}], [])

        # 3. ACT: The executor executes the plan
        self.tool_executor.execute_tool(tool_call_dict)

        # 4. VERIFY: Assert that the correct low-level keyboard actions were
        # invoked. open_application's hotkey choice is platform-dependent
        # (Win+R / Cmd+Space / Alt+F2), so just check a hotkey was sent.
        self.mock_kbm_instance.hotkey.assert_called_once()
        self.mock_kbm_instance.type_string.assert_called_once_with("calculator")
        self.mock_kbm_instance.press_key.assert_called_once_with('enter')
        print("  [SUCCESS] Correct sequence of low-level keyboard actions was executed.")

    def test_e2e_web_workflow_search_and_scrape(self):
        """
        Verify the full chain for a multi-step web automation task.
        """
        print("\n\n--- Testing E2E Web Workflow: 'Search and Scrape' ---")
        user_prompt = "Go to example.com and tell me the main heading."

        # --- Step 1: Navigate to URL ---
        self.mock_openai_instance.get_tool_calling_response.return_value = _tool_call_message(
            "navigate_to_url", {"url": "https://example.com"}
        )

        tool_call_1 = self.agent.get_tool_selection_response([], [])
        self.tool_executor.execute_tool(tool_call_1)

        # Verify the first action
        self.mock_driver.get.assert_called_once_with("https://example.com")
        print("  [SUCCESS] Step 1: Navigated to URL.")

        # --- Step 2: Scrape the heading ---
        self.mock_openai_instance.get_tool_calling_response.return_value = _tool_call_message(
            "scrape_text_from_elements", {"locator": ["tag name", "h1"]}
        )

        # Configure the mock driver to return a fake heading element.
        # Uses the literal Selenium locator string ("tag name") rather than
        # importing selenium.webdriver.common.by.By, since selenium isn't a
        # hard requirement for running this test (automation_tools.py treats
        # it as an optional dependency and degrades gracefully without it).
        mock_heading_element = MagicMock(text="Example Domain")
        self.mock_driver.find_elements.return_value = [mock_heading_element]

        tool_call_2 = self.agent.get_tool_selection_response([], [])
        result = self.tool_executor.execute_tool(tool_call_2)

        # Verify the second action and the final result. execute_tool wraps
        # the tool's return value in a {"status": ..., "result": ...} envelope.
        self.mock_driver.find_elements.assert_called_once_with("tag name", "h1")
        self.assertEqual(result, {"status": "success", "result": ["Example Domain"]})
        print("  [SUCCESS] Step 2: Scraped correct text from the page.")
        print("  [SUCCESS] Full web workflow completed successfully.")


if __name__ == '__main__':
    # Re-enable logging for the test runner's output
    logging.disable(logging.NOTSET)
    unittest.main()
