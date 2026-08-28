# Devin/tests/security/test_data_leakage.py
# Purpose: A test suite to detect and prevent accidental exposure of
#          sensitive information (e.g., API keys, passwords) in logs and outputs.

import unittest
import logging
import re
from unittest.mock import patch, MagicMock

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# --- Import the modules we are going to test ---
from modules.all_ais_modules import AIAgent
from modules.os_operations.other_operations import GenericRemoteShell
from modules.robotics.data_logger import DataLogger

# --- Suppress regular logging output during tests for clarity ---
# We will capture logs with mocks instead.
logging.disable(logging.CRITICAL)


class TestDataLeakage(unittest.TestCase):
    """
    Test suite focused on ensuring sensitive data is not leaked.
    """

    def setUp(self):
        """Define sensitive patterns to search for in test outputs."""
        self.sensitive_patterns = [
            # Pattern for OpenAI-like API keys (sk-...)
            re.compile(r"sk-[a-zA-Z0-9]{20,}"),
            # Pattern for Google-like API keys (AIza...)
            re.compile(r"AIza[0-9A-Za-z\-_]{20,}"),
            # Generic password pattern
            re.compile(r"password", re.IGNORECASE),
            # Generic private key pattern
            re.compile(r"-----BEGIN (RSA|OPENSSH) PRIVATE KEY-----"),
        ]
        self.dummy_password = "MySuperSecretPassword123!"
        self.dummy_openai_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        self.dummy_google_key = "AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    def assertNoSensitiveData(self, text_to_check: str, context: str):
        """
        Custom assertion to check a string against all sensitive patterns.
        Fails the test if any sensitive data is found.
        """
        for pattern in self.sensitive_patterns:
            if pattern.search(text_to_check):
                # A simple way to show the problematic text without leaking it in test logs
                found = pattern.search(text_to_check).group(0)
                redacted = found[:4] + "..." + found[-4:]
                self.fail(f"Sensitive data pattern found in {context}. Leaked data (redacted): '{redacted}'")

    @patch('logging.info')
    def test_ai_agent_initialization_does_not_log_keys(self, mock_logging_info: MagicMock):
        """
        Verify that initializing the AIAgent does not log full API keys.
        This test assumes the underlying modules have been modified to redact keys in logs.
        """
        # Note: This test would drive a change in the modules themselves to ensure they
        # log responsibly, e.g., logger.info(f"Using API key: {key[:5]}...{key[-4:]}")
        
        # We need to mock the child modules' initializers as well to avoid real API calls
        with patch('modules.chatgpt_module.ChatGPTModule'), \
             patch('modules.gemini_module.GeminiModule'), \
             patch('modules.perplexity_module.PerplexityModule'):
            
            AIAgent(
                openai_api_key=self.dummy_openai_key,
                gemini_api_key=self.dummy_google_key,
                perplexity_api_key="pplx-xxxxxxxx"
            )

        # Now, check every single message that was logged
        all_log_calls = ""
        for call in mock_logging_info.call_args_list:
            all_log_calls += str(call.args[0]) + "\n"
        
        # We expect the full keys to NOT be in the logs
        self.assertNotIn(self.dummy_openai_key, all_log_calls)
        self.assertNotIn(self.dummy_google_key, all_log_calls)
        self.assertIn("AIAgent initialization complete", all_log_calls) # Verify it ran
        
    @patch('logging.info')
    def test_generic_remote_shell_does_not_log_password(self, mock_logging_info: MagicMock):
        """
        Verify that initializing and using the GenericRemoteShell does not log the password.
        """
        # Mock the actual connection method to avoid network calls
        with patch('paramiko.SSHClient.connect'):
            shell = GenericRemoteShell(
                host="localhost",
                user="testuser",
                password=self.dummy_password
            )
            shell.connect()

        all_log_calls = ""
        for call in mock_logging_info.call_args_list:
            all_log_calls += str(call.args[0]) + "\n"
            
        self.assertNotIn(self.dummy_password, all_log_calls)
        self.assertIn("GenericRemoteShell configured", all_log_calls)

    def test_data_logger_correctly_writes_pre_sanitized_data(self):
        """
        Verify the DataLogger correctly writes data. This test emphasizes that
        the responsibility to sanitize data lies with the CALLER of the logger.
        """
        log_dir = Path("./temp_test_logs")
        log_dir.mkdir(exist_ok=True)
        
        # Use a mock for the actual file writing to capture the data
        with patch('pandas.DataFrame.to_feather') as mock_to_feather:
            logger_instance = DataLogger(log_directory=str(log_dir))
            logger_instance.start_logging()
            
            # The CALLER is responsible for sanitizing this data
            sensitive_record = {
                "user_id": 123,
                "action": "login",
                "ip_address": "192.168.1.1",
                "password_hash": "a1b2c3d4...", # Hashed is OK
                "session_token": self.dummy_openai_key # This should NOT be logged
            }
            
            # A secure caller would sanitize first:
            sanitized_record = {k: v for k, v in sensitive_record.items() if k != "session_token"}
            
            logger_instance.log("auth_event", sanitized_record)
            
            # Stop logging to force a flush
            logger_instance.stop_logging()

        # Check what was passed to the file writer
        self.assertTrue(mock_to_feather.called)
        # Get the DataFrame that was passed to to_feather
        df_to_write = mock_to_feather.call_args[0][0]
        
        # Convert the entire dataframe to a string and check for any leaks
        df_string = df_to_write.to_string()
        self.assertNoSensitiveData(df_string, "DataLogger output DataFrame")

        # Clean up
        import shutil
        shutil.rmtree(log_dir)

if __name__ == '__main__':
    # Re-enable logging for the test runner's output
    logging.disable(logging.NOTSET)
    unittest.main()
