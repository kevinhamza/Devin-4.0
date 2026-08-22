# Devin/tests/automation_tests.py
# Purpose: An integration test suite for the automation stack, verifying that
#          high-level workflows correctly orchestrate low-level tools.

import unittest
from unittest.mock import patch, MagicMock, call

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

_import_error = None

try:
    from modules.automation_tools import DesktopAutomator, WebAutomator
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# --- Suppress regular logging output during tests for clarity ---
import logging
logging.disable(logging.CRITICAL)


@unittest.skipUnless(DEVIN_CORE_AVAILABLE, f"Skipping automation tests, dependency missing: {_import_error}")
class TestAutomationIntegration(unittest.TestCase):
    """
    Tests the high-level logic of the DesktopAutomator and WebAutomator
    using mocked low-level controllers.
    """

    @patch('modules.automation_tools.KeyboardMouseController')
    def test_desktop_automator_open_and_type_workflow(self, MockKBMController):
        """
        Verify the workflow for opening an app and typing into it.
        """
        print("\n\n--- Testing DesktopAutomator 'Open & Type' Workflow ---")
        mock_kbm_instance = MockKBMController.return_value
        
        # Instantiate the real DesktopAutomator, which gets the mock controller
        desktop_automator = DesktopAutomator()
        
        # Define the high-level workflow
        app_name = "notepad"
        text_to_type = "Hello from Devin!"
        
        # --- Execute the high-level command ---
        desktop_automator.open_application_and_type(app_name, text_to_type)
        
        # --- Verify the sequence of low-level calls ---
        # We expect a sequence like: Win+R, type "notepad", press Enter, type "Hello..."
        expected_calls = [
            # Open Run dialog (assuming Windows for this test)
            call.hotkey('cmd', 'r'),
            # Type the application name
            call.type_string(app_name),
            # Press Enter to launch
            call.press_key('enter'),
            call.release_key('enter'),
            # Type the content
            call.type_string(text_to_type)
        ]
        
        # Check if the mock's methods were called in the expected sequence
        mock_kbm_instance.assert_has_calls(expected_calls, any_order=False)
        print("  [SUCCESS] Correct sequence of keyboard actions was called.")

    @patch('modules.automation_tools.BrowserManager')
    def test_web_automator_login_workflow(self, MockBrowserManager):
        """
        Verify the workflow for logging into a website.
        """
        print("\n\n--- Testing WebAutomator 'Login' Workflow ---")
        mock_browser_instance = MockBrowserManager.return_value
        # We also need to mock the underlying selenium webdriver
        mock_driver = MagicMock()
        mock_browser_instance.get_driver.return_value = mock_driver

        # Instantiate the real WebAutomator
        web_automator = WebAutomator(browser_manager=mock_browser_instance)
        
        # --- Configure the mocks for the find_element calls ---
        mock_username_field = MagicMock()
        mock_password_field = MagicMock()
        mock_submit_button = MagicMock()
        
        mock_driver.find_element.side_effect = [
            mock_username_field,
            mock_password_field,
            mock_submit_button
        ]

        # --- Execute the high-level command ---
        url = "https://example.com/login"
        username = "devin_user"
        password = "password123"
        web_automator.login_to_website(
            url=url,
            username=username,
            password=password,
            username_locator=('id', 'username'),
            password_locator=('id', 'password'),
            submit_locator=('id', 'submit')
        )

        # --- Verify the sequence of low-level calls ---
        # 1. Verify we navigated to the correct URL
        mock_driver.get.assert_called_once_with(url)
        print("  [SUCCESS] Navigated to the correct URL.")
        
        # 2. Verify we found the elements and interacted with them
        from selenium.webdriver.common.by import By
        mock_driver.find_element.assert_has_calls([
            call(By.ID, 'username'),
            call(By.ID, 'password'),
            call(By.ID, 'submit')
        ])
        print("  [SUCCESS] Located all necessary web elements.")
        
        mock_username_field.send_keys.assert_called_once_with(username)
        mock_password_field.send_keys.assert_called_once_with(password)
        mock_submit_button.click.assert_called_once()
        print("  [SUCCESS] Correctly filled fields and clicked submit.")

    @patch('modules.automation_tools.BrowserManager')
    def test_web_automator_scrape_data_workflow(self, MockBrowserManager):
        """
        Verify the workflow for scraping data from a web page.
        """
        print("\n\n--- Testing WebAutomator 'Scrape Data' Workflow ---")
        mock_browser_instance = MockBrowserManager.return_value
        mock_driver = MagicMock()
        mock_browser_instance.get_driver.return_value = mock_driver

        web_automator = WebAutomator(browser_manager=mock_browser_instance)

        # Configure the mock to return a list of mock elements
        mock_elements = [
            MagicMock(text="Product A"),
            MagicMock(text="Product B"),
            MagicMock(text="Product C"),
        ]
        mock_driver.find_elements.return_value = mock_elements

        # Execute the high-level command
        from selenium.webdriver.common.by import By
        results = web_automator.scrape_text_from_elements(('xpath', "//div[@class='product']"))

        # Verify the results
        mock_driver.find_elements.assert_called_once_with(By.XPATH, "//div[@class='product']")
        self.assertEqual(results, ["Product A", "Product B", "Product C"])
        print("  [SUCCESS] Correctly scraped and returned text from elements.")


if __name__ == '__main__':
    # Re-enable logging for the test runner's output
    logging.disable(logging.NOTSET)
    unittest.main()
