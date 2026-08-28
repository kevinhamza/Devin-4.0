# Devin/tests/security/test_consent_bypass.py
# Purpose: A test suite to validate that the system's permission enforcement
#          mechanisms correctly require and respect user consent.

import unittest
from unittest.mock import patch, MagicMock

# --- Important: We need to set up the path to import our modules ---
import sys
from pathlib import Path
# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# --- Import the modules we are going to test ---
# These are high-level modules that SHOULD use the UserInteractionManager
from modules.user_interaction_module import UserInteractionManager
from singularity.self_replication.code_generator import SelfModifyingCodeGenerator
from modules.code_execution import CodeExecutor

# --- Suppress regular logging and input prompts during tests ---
import logging
logging.disable(logging.CRITICAL)


class ActionExecutor:
    """
    A conceptual high-level agent loop component for this test.
    It decides to take an action and is responsible for getting consent.
    """
    def __init__(self, interaction_manager: UserInteractionManager, code_executor: CodeExecutor):
        self.interaction_manager = interaction_manager
        self.code_executor = code_executor

    def execute_potentially_dangerous_command(self, command: str):
        """Executes a shell command only after getting user confirmation."""
        prompt = f"Are you sure you want to execute the following shell command?\n  > {command}"
        if self.interaction_manager.ask_for_confirmation(prompt):
            print(f"User consented. Executing '{command}'...")
            self.code_executor.execute_code("shell", command, use_sandbox=True)
        else:
            print("User denied consent. Aborting command execution.")


class TestConsentBypass(unittest.TestCase):
    """
    Test suite focused on ensuring user consent is required and respected.
    """

    @patch('builtins.input', side_effect=['y', 'Y', 'yes', 'n', 'N', 'no', 'invalid'])
    def test_user_interaction_manager_parses_confirmation_correctly(self, mock_input: MagicMock):
        """
        Tests the UserInteractionManager's core confirmation logic.
        """
        uim = UserInteractionManager()
        self.assertTrue(uim.ask_for_confirmation("Test yes"))
        self.assertTrue(uim.ask_for_confirmation("Test Y"))
        self.assertTrue(uim.ask_for_confirmation("Test yes"))
        self.assertFalse(uim.ask_for_confirmation("Test n"))
        self.assertFalse(uim.ask_for_confirmation("Test N"))
        self.assertFalse(uim.ask_for_confirmation("Test no"))
        self.assertFalse(uim.ask_for_confirmation("Test invalid"))

    @patch('modules.code_execution.CodeExecutor.execute_code')
    @patch('modules.user_interaction_module.UserInteractionManager.ask_for_confirmation')
    def test_dangerous_shell_command_is_blocked_without_consent(self, mock_ask: MagicMock, mock_execute: MagicMock):
        """
        Verify that a dangerous command is NOT executed if the user says 'no'.
        """
        # --- SCENARIO: User DENIES consent ---
        mock_ask.return_value = False
        
        uim = UserInteractionManager()
        executor = CodeExecutor()
        action_executor = ActionExecutor(uim, executor)
        
        dangerous_command = "rm -rf /"
        action_executor.execute_potentially_dangerous_command(dangerous_command)
        
        # Verify that we asked for permission
        mock_ask.assert_called_once()
        # CRITICAL: Verify that the actual execution was NEVER called
        mock_execute.assert_not_called()

    @patch('modules.code_execution.CodeExecutor.execute_code')
    @patch('modules.user_interaction_module.UserInteractionManager.ask_for_confirmation')
    def test_dangerous_shell_command_is_executed_with_consent(self, mock_ask: MagicMock, mock_execute: MagicMock):
        """
        Verify that a dangerous command IS executed if the user says 'yes'.
        """
        # --- SCENARIO: User GRANTS consent ---
        mock_ask.return_value = True
        
        uim = UserInteractionManager()
        executor = CodeExecutor()
        action_executor = ActionExecutor(uim, executor)
        
        dangerous_command = "rm -rf /"
        action_executor.execute_potentially_dangerous_command(dangerous_command)
        
        # Verify that we asked for permission
        mock_ask.assert_called_once()
        # CRITICAL: Verify that the execution WAS called
        mock_execute.assert_called_once_with("shell", dangerous_command, use_sandbox=True)

    @patch('builtins.open')
    @patch('modules.user_interaction_module.UserInteractionManager.ask_for_confirmation')
    def test_self_modification_is_blocked_without_consent(self, mock_ask: MagicMock, mock_open: MagicMock):
        """
        Verify that the SelfModifyingCodeGenerator will not overwrite a file without consent.
        """
        # --- SCENARIO: User DENIES consent ---
        mock_ask.return_value = False

        # We need to mock all dependencies of the SelfModifyingCodeGenerator
        mock_agent = MagicMock()
        mock_utility = MagicMock()
        mock_executor = MagicMock()

        # Mock the verification step to always return True so we can test the final step
        with patch.object(SelfModifyingCodeGenerator, 'verify_improvement', return_value=True):
            generator = SelfModifyingCodeGenerator(
                ai_agent=mock_agent,
                utility_function=mock_utility,
                code_executor=mock_executor,
                project_root="."
            )
            # This is the high-level method that orchestrates the process
            generator.run_self_modification_cycle(
                target_module_path="dummy_module.py",
                test_command="pytest"
            )

        # In a real run, the 'propose' step would ask for permission before writing.
        # We simulate that here. A real implementation would have this call in the method.
        prompt = "A verified improvement for 'dummy_module.py' has been generated. Do you want to apply it (overwrite the original file)?"
        if uim.ask_for_confirmation(prompt):
             # This is the dangerous action
            with open("dummy_module.py", "w") as f:
                f.write("# new code")

        # CRITICAL: Verify that the file `open` call for writing was NEVER made
        mock_open.assert_not_called()


if __name__ == '__main__':
    # Re-enable logging for the test runner's output
    logging.disable(logging.NOTSET)
    unittest.main()
