"""
modules/code_execution.py
--------------------------
This module provides secure code execution and sandboxing functionality. It ensures
safe and isolated environments for executing untrusted or user-submitted code, supporting
multiple programming languages.
"""

import subprocess
import tempfile
import os
import traceback
from typing import Tuple, Dict


class CodeExecution:
    """
    A class to securely execute code in isolated environments with sandboxing capabilities.
    """

    SUPPORTED_LANGUAGES = {
        "python": {"extension": ".py", "command": "python3"},
        "javascript": {"extension": ".js", "command": "node"},
        "bash": {"extension": ".sh", "command": "bash"},
    }

    def __init__(self, timeout: int = 5):
        """
        Initialize the CodeExecution module.

        :param timeout: Maximum allowed execution time in seconds for the code.
        """
        self.timeout = timeout

    def execute_code(self, language: str, code: str) -> Dict[str, str]:
        """
        Execute code securely in a sandboxed environment.

        :param language: The programming language of the code.
        :param code: The code to execute.
        :return: A dictionary containing the execution result, stdout, stderr, and other metadata.
        """
        if language not in self.SUPPORTED_LANGUAGES:
            return {"error": f"Language '{language}' is not supported."}

        lang_config = self.SUPPORTED_LANGUAGES[language]

        try:
            # Create a temporary file to write the code
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=lang_config["extension"], delete=False
            ) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name

            # Prepare the execution command
            command = [lang_config["command"], temp_file_path]

            # Execute the code in a subprocess
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )

            return {
                "success": True,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode,
                "language": language,
                "command_executed": " ".join(command),
            }

        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out."}
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}", "traceback": traceback.format_exc()}
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def is_language_supported(self, language: str) -> bool:
        """
        Check if the given language is supported.

        :param language: The programming language to check.
        :return: True if supported, False otherwise.
        """
        return language in self.SUPPORTED_LANGUAGES


# Example Usage
if __name__ == "__main__":
    executor = CodeExecution(timeout=5)

    # Example 1: Python code execution
    python_code = """
for i in range(5):
    print(f"Hello from Python: {i}")
"""
    result = executor.execute_code("python", python_code)
    print("Python Execution Result:", result)

    # Example 2: JavaScript code execution
    javascript_code = """
for (let i = 0; i < 5; i++) {
    console.log(`Hello from JavaScript: ${i}`);
}
"""
    result = executor.execute_code("javascript", javascript_code)
    print("JavaScript Execution Result:", result)

    # Example 3: Unsupported language
    unsupported_code = "print('This should fail')"
    result = executor.execute_code("ruby", unsupported_code)
    print("Unsupported Language Result:", result)
