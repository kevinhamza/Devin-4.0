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

try:
    from modules.all_ais_modules import AIAgent, AIProvider
    from modules.ai_connector import AIResponse
    from modules.tool_executor import ToolExecutor
    from modules.automation_tools import DesktopAutomator, WebAutomator
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)


@unittest.skipUnless(DEVIN_CORE_AVAILABLE, f"Skipping integration tests, dependency missing: {_import_error}")
class TestEndToEndAutomation(unittest.TestCase):
    """
    Tests the full workflow from AI decision to automation execution.
    """

    def setUp(self):
        """
        Set up a complex mock environment that isolates the workflow logic.
        """
        # 1. Patch the lowest level: the hardware/browser interactors
        self.patcher_kbm = patch('modules.automation_tools.KeyboardMouseController')
        self.MockKBMController = self.patcher_kbm.start()
        self.mock_kbm_instance = self.MockKBMController.return_value

        self.patcher_browser = patch('modules.automation_tools.BrowserManager')
        self.MockBrowserManager = self.patcher_browser.start()
        self.mock_browser_instance = self.MockBrowserManager.return_value
        self.mock_driver = MagicMock()
        self.mock_browser_instance.get_driver.return_value = self.mock_driver
        
        # 2. Patch the external dependency: the AI connectors
        self.patcher_openai = patch('modules.all_ais_modules.OpenAIConnector')
        self.MockOpenAIConnector = self.patcher_openai.start()
        self.mock_openai_instance = self.MockOpenAIConnector.return_value
        
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
        
        # 1. Configure the mock LLM to return a specific plan
        ai_plan = {
            "tool": "open_application",
            "parameters": {"app_name": "calculator"}
        }
        self.mock_openai_instance.get_chat_completion.return_value = AIResponse(json.dumps(ai_plan), True)
        
        # 2. THINK: The agent formulates the plan
        tool_call_dict = self.agent.get_tool_selection_response([{"role": "user", "content": user_prompt}], [])
        
        # 3. ACT: The executor executes the plan
        self.tool_executor.execute_tool(tool_call_dict)
        
        # 4. VERIFY: Assert that the correct low-level methods were called in order
        self.mock_kbm_instance.hotkey.assert_called_once_with('cmd', 'r') # or 'win'
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
        # Configure the mock LLM for the first step
        ai_plan_1 = {"tool": "navigate_to_url", "parameters": {"url": "https://example.com"}}
        self.mock_openai_instance.get_chat_completion.return_value = AIResponse(json.dumps(ai_plan_1), True)
        
        tool_call_1 = self.agent.get_tool_selection_response([], [])
        self.tool_executor.execute_tool(tool_call_1)
        
        # Verify the first action
        self.mock_driver.get.assert_called_once_with("https://example.com")
        print("  [SUCCESS] Step 1: Navigated to URL.")

        # --- Step 2: Scrape the heading ---
        # Configure the mock LLM for the second step
        ai_plan_2 = {"tool": "scrape_text_from_elements", "parameters": {"locator": ["tag name", "h1"]}}
        self.mock_openai_instance.get_chat_completion.return_value = AIResponse(json.dumps(ai_plan_2), True)
        
        # Configure the mock driver to return a fake heading element
        from selenium.webdriver.common.by import By
        mock_heading_element = MagicMock(text="Example Domain")
        self.mock_driver.find_elements.return_value = [mock_heading_element]

        tool_call_2 = self.agent.get_tool_selection_response([], [])
        result = self.tool_executor.execute_tool(tool_call_2)
        
        # Verify the second action and the final result
        self.mock_driver.find_elements.assert_called_once_with(By.TAG_NAME, "h1")
        self.assertEqual(result, ["Example Domain"])
        print("  [SUCCESS] Step 2: Scraped correct text from the page.")
        print("  [SUCCESS] Full web workflow completed successfully.")


if __name__ == '__main__':
    # Re-enable logging for the test runner's output
    logging.disable(logging.NOTSET)
    unittest.main()
