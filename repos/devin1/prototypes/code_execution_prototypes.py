"""
prototypes/code_execution_prototypes.py
=======================================
This module contains experimental prototypes for code execution functionalities, including
sandboxed environments, remote code execution, and script evaluation.
"""

import subprocess
import tempfile
import os
from contextlib import contextmanager

class CodeExecutionPrototypes:
    """
    A class to handle various code execution experiments, including sandboxing,
    script execution, and error handling.
    """

    @staticmethod
    def execute_python_code(code: str) -> dict:
        """
        Executes a Python script provided as a string in a controlled environment.

        Args:
            code (str): The Python code to execute.

        Returns:
            dict: Contains `stdout`, `stderr`, and `success` status.
        """
        try:
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True,
                timeout=10  # Prevents infinite loops or long execution.
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Execution timed out.", "success": False}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "success": False}

    @staticmethod
    @contextmanager
    def sandbox_environment():
        """
        Context manager to create a temporary, isolated environment for script execution.
        """
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            yield temp_dir
        finally:
            os.chdir(original_cwd)
            os.rmdir(temp_dir)

    @staticmethod
    def execute_in_sandbox(code: str) -> dict:
        """
        Executes code in a sandboxed environment to limit its scope and effects.

        Args:
            code (str): The Python code to execute.

        Returns:
            dict: Contains `stdout`, `stderr`, and `success` status.
        """
        with CodeExecutionPrototypes.sandbox_environment():
            return CodeExecutionPrototypes.execute_python_code(code)

    @staticmethod
    def execute_shell_command(command: str) -> dict:
        """
        Executes a shell command and returns the output.

        Args:
            command (str): The shell command to execute.

        Returns:
            dict: Contains `stdout`, `stderr`, and `success` status.
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Execution timed out.", "success": False}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "success": False}

# Example usage
if __name__ == "__main__":
    # Test Python execution
    code_snippet = "print('Hello from sandbox!')"
    result = CodeExecutionPrototypes.execute_python_code(code_snippet)
    print("Python Execution Result:", result)

    # Test shell execution
    shell_command = "echo 'Hello from shell!'"
    result = CodeExecutionPrototypes.execute_shell_command(shell_command)
    print("Shell Execution Result:", result)

    # Test sandbox execution
    sandbox_code = "import os; print('Sandbox cwd:', os.getcwd())"
    sandbox_result = CodeExecutionPrototypes.execute_in_sandbox(sandbox_code)
    print("Sandbox Execution Result:", sandbox_result)
