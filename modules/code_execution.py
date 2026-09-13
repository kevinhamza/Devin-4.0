# # Devin/modules/code_execution.py
# # Purpose: Provides a secure environment for executing code snippets in various languages.
# #          Uses conceptual sandboxing to ensure safety.
# # Secure code execution 🛡️‍💻

# import logging
# import uuid
# import time
# import random
# from enum import Enum, auto
# from dataclasses import dataclass, field
# from typing import List, Dict, Any, Optional, Tuple

# # Configure basic logging
# logger = logging.getLogger("CodeExecutor")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class ExecutionStatus(Enum):
#     """Represents the outcome of a code execution task."""
#     SUCCESS = auto()
#     RUNTIME_ERROR = auto()
#     TIMEOUT = auto()
#     SETUP_ERROR = auto()
#     FORBIDDEN = auto() # For actions blocked by the sandbox

# class SandboxStatus(Enum):
#     """Represents the state of a conceptual sandbox."""
#     INACTIVE = auto()
#     CREATING = auto()
#     READY = auto()
#     RUNNING_CODE = auto()
#     DESTROYED = auto()

# @dataclass
# class CodeExecutionResult:
#     """Holds the results of a single code execution."""
#     status: ExecutionStatus
#     exit_code: Optional[int] = None
#     stdout: str = ""
#     stderr: str = ""
#     execution_time_ms: float = 0.0
#     logs: List[str] = field(default_factory=list) # Logs from the sandbox/executor itself

# @dataclass
# class SandboxEnvironment:
#     """
#     Represents a conceptual isolated environment (e.g., a Docker container) for code execution.
#     """
#     id: str = field(default_factory=lambda: f"sandbox-{uuid.uuid4().hex[:8]}")
#     status: SandboxStatus = SandboxStatus.INACTIVE
#     language: str # e.g., 'python', 'javascript', 'shell'
#     image_name: str # e.g., 'python:3.9-slim', 'node:16'
    
#     def __post_init__(self):
#         logger.info(f"Conceptual sandbox '{self.id}' defined for language '{self.language}'.")

# class CodeExecutor:
#     """
#     Manages the secure execution of code snippets within sandboxed environments.
#     """
#     def __init__(self, sandbox_pool_size: int = 2, default_timeout_sec: int = 30):
#         """
#         Initializes the CodeExecutor.

#         Args:
#             sandbox_pool_size (int): The number of sandboxes to keep warm for faster execution.
#             default_timeout_sec (int): The default timeout for code execution.
#         """
#         self.default_timeout = default_timeout_sec
#         # In a real system, this would manage a pool of actual Docker containers or VMs.
#         self.sandbox_pool_conceptual: Dict[str, SandboxEnvironment] = {}
#         logger.info(f"CodeExecutor initialized with default timeout {self.default_timeout}s.")
#         logger.warning("All code execution is CONCEPTUAL and simulates a secure sandboxed environment.")

#     def _get_sandbox_conceptual(self, language: str) -> SandboxEnvironment:
#         """
#         Gets a ready sandbox for a specific language, creating one if needed.
#         """
#         # Look for an available sandbox in the conceptual pool
#         for sandbox in self.sandbox_pool_conceptual.values():
#             if sandbox.language == language and sandbox.status == SandboxStatus.READY:
#                 logger.info(f"Reusing warm sandbox '{sandbox.id}' for '{language}'.")
#                 return sandbox

#         # If none available, create a new one
#         logger.info(f"No warm sandbox for '{language}'. Creating a new one...")
#         image_map = {"python": "python:3.9-slim", "javascript": "node:16", "shell": "ubuntu:22.04"}
#         image = image_map.get(language, "ubuntu:22.04") # Default to a basic shell
        
#         new_sandbox = SandboxEnvironment(language=language, image_name=image)
#         new_sandbox.status = SandboxStatus.CREATING
#         # Simulate time to pull image and start container
#         logger.info(f"CONCEPTUAL: Running 'docker run -d --name {new_sandbox.id} {image}'...")
#         time.sleep(0.2)
#         new_sandbox.status = SandboxStatus.READY
#         self.sandbox_pool_conceptual[new_sandbox.id] = new_sandbox
#         logger.info(f"  Conceptual sandbox '{new_sandbox.id}' is now READY.")
#         return new_sandbox
        
#     def execute_code(self,
#                      language: str,
#                      code: str,
#                      timeout_sec: Optional[int] = None) -> CodeExecutionResult:
#         """
#         Executes a block of code in a secure, isolated sandbox.

#         Args:
#             language (str): The programming language ('python', 'javascript', 'shell').
#             code (str): The source code to execute.
#             timeout_sec (Optional[int]): A specific timeout for this execution.

#         Returns:
#             CodeExecutionResult: An object containing all results of the execution.
#         """
#         execution_timeout = timeout_sec or self.default_timeout
#         start_time = time.monotonic()
        
#         try:
#             sandbox = self._get_sandbox_conceptual(language)
#             sandbox.status = SandboxStatus.RUNNING_CODE
#         except Exception as e:
#             logger.error(f"Failed to get or create sandbox: {e}")
#             return CodeExecutionResult(status=ExecutionStatus.SETUP_ERROR, stderr=f"Sandbox setup failed: {e}")

#         logger.info(f"Executing {language} code in sandbox '{sandbox.id}' (timeout: {execution_timeout}s)...")
        
#         # --- This is the core simulation ---
#         # In a real system, this would be a complex call like:
#         # `docker exec <sandbox_id> <interpreter> -c "<code>"`
#         # We simulate the outcome instead.
        
#         # Simulate different outcomes based on code content
#         if "infinite loop" in code.lower():
#             status, exit_code, stdout, stderr = self._simulate_timeout(execution_timeout)
#         elif "error" in code.lower() or "exception" in code.lower():
#             status, exit_code, stdout, stderr = self._simulate_runtime_error(language)
#         elif "network.connect" in code.lower(): # Simulate a sandboxed security violation
#              status, exit_code, stdout, stderr = self._simulate_forbidden_action()
#         else:
#             status, exit_code, stdout, stderr = self._simulate_success(language, code)
        
#         execution_time_ms = (time.monotonic() - start_time) * 1000
#         sandbox.status = SandboxStatus.READY # Mark sandbox as ready for next use

#         result = CodeExecutionResult(
#             status=status,
#             exit_code=exit_code,
#             stdout=stdout,
#             stderr=stderr,
#             execution_time_ms=execution_time_ms
#         )
#         logger.info(f"Execution finished in {result.execution_time_ms:.2f}ms with status: {result.status.name}")
#         return result

#     def _simulate_success(self, language: str, code: str) -> Tuple[ExecutionStatus, int, str, str]:
#         logger.debug("  Simulating successful execution.")
#         stdout = f"--- Simulated Output for {language} ---\nHello from the secure sandbox!\n"
#         if "import os" in code:
#             stdout += "Conceptual listdir: ['file1.txt', 'subdir']\n"
#         return ExecutionStatus.SUCCESS, 0, stdout, ""

#     def _simulate_runtime_error(self, language: str) -> Tuple[ExecutionStatus, int, str, str]:
#         logger.debug("  Simulating runtime error.")
#         stderr = ""
#         if language == "python":
#             stderr = "Traceback (most recent call last):\n  File \"<stdin>\", line 1, in <module>\nZeroDivisionError: division by zero"
#         elif language == "javascript":
#             stderr = "ReferenceError: nonExistentVariable is not defined\n    at <anonymous>:1:1"
#         else: # shell
#             stderr = "/bin/sh: 1: non_existent_command: not found"
#         return ExecutionStatus.RUNTIME_ERROR, 1, "", stderr

#     def _simulate_timeout(self, timeout_sec: int) -> Tuple[ExecutionStatus, int, str, str]:
#         logger.debug("  Simulating execution timeout.")
#         time.sleep(0.1) # Simulate running up to the timeout
#         stderr = f"Execution timed out after {timeout_sec} seconds."
#         return ExecutionStatus.TIMEOUT, -1, "Process started but did not complete...", stderr

#     def _simulate_forbidden_action(self) -> Tuple[ExecutionStatus, int, str, str]:
#         logger.debug("  Simulating forbidden action due to sandbox rules.")
#         stderr = "Operation not permitted: Network access is disabled in this sandbox."
#         return ExecutionStatus.FORBIDDEN, 137, "", stderr

#     def cleanup_sandboxes(self):
#         """Conceptually destroys all active sandboxes."""
#         logger.info(f"Cleaning up {len(self.sandbox_pool_conceptual)} conceptual sandboxes...")
#         for sandbox_id in list(self.sandbox_pool_conceptual.keys()):
#             logger.info(f"  CONCEPTUAL: Running 'docker stop {sandbox_id} && docker rm {sandbox_id}'")
#             self.sandbox_pool_conceptual[sandbox_id].status = SandboxStatus.DESTROYED
#         self.sandbox_pool_conceptual.clear()
#         logger.info("All sandboxes cleaned up.")

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Secure Code Executor Module Prototype 🛡️‍💻 ===")
#     print("=========================================================")
    
#     executor = CodeExecutor(default_timeout_sec=5)

#     def run_and_print(lang: str, code: str):
#         print(f"\n--- Executing {lang.upper()} Code ---")
#         print(f"Code:\n```\n{code}\n```")
#         result = executor.execute_code(lang, code)
#         print(f"Result Status: {result.status.name}")
#         print(f"Exit Code: {result.exit_code}")
#         if result.stdout:
#             print(f"STDOUT:\n{result.stdout}")
#         if result.stderr:
#             print(f"STDERR:\n{result.stderr}")
#         print("-" * (20 + len(lang)))

#     # 1. Successful Python execution
#     python_success_code = "import os\nprint('Running ls conceptually...')\nprint(os.listdir('.'))"
#     run_and_print("python", python_success_code)

#     # 2. Python execution with a runtime error
#     python_error_code = "x = 1 / 0 # This will raise a ZeroDivisionError"
#     run_and_print("python", python_error_code)

#     # 3. Successful JavaScript execution
#     js_success_code = "console.log(`Node.js version: ${process.version}`);\nconsole.log('Script finished.');"
#     run_and_print("javascript", js_success_code)

#     # 4. Successful Shell execution
#     shell_success_code = "echo 'Hello from the shell sandbox!'\nls -l"
#     run_and_print("shell", shell_success_code)

#     # 5. Execution that times out
#     timeout_code = "# This is a conceptual infinite loop\nwhile True:\n  pass"
#     run_and_print("python", timeout_code)
    
#     # 6. Execution that is forbidden by sandbox rules
#     forbidden_code = "# Trying to access network\nimport socket\nsocket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('google.com', 80))"
#     run_and_print("python", forbidden_code)

#     # 7. Cleanup
#     print("\n--- Cleaning up conceptual resources ---")
#     executor.cleanup_sandboxes()

#     print("\n=========================================================")
#     print("=== Code Executor Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/code_execution.py
# Purpose: Provides a functional, dual-mode engine for executing code
#          either directly on the host or within a secure Docker sandbox.

import logging
import os
import uuid
import time
import subprocess
import tempfile
from pathlib import Path
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

try:
    from security.sandbox.docker_sandbox import DockerSandbox
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("CodeExecutor")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class ExecutionStatus(Enum):
    SUCCESS = auto()
    RUNTIME_ERROR = auto()
    TIMEOUT = auto()
    SETUP_ERROR = auto()

@dataclass
class CodeExecutionResult:
    status: ExecutionStatus
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0.0


class CodeExecutor:
    """
    Manages the execution of code snippets, with an option for sandboxing.
    """
    def __init__(self, default_timeout_sec: int = 60):
        self.default_timeout = default_timeout_sec
        self.docker_sandbox = None
        if DOCKER_AVAILABLE:
            try:
                self.docker_sandbox = DockerSandbox()
            except ConnectionError as e:
                logger.warning(f"Docker sandbox unavailable, falling back to unsandboxed execution: {e}")
        logger.info("CodeExecutor initialized.")
        if not self.docker_sandbox:
            logger.warning("DockerSandbox module not available. Sandboxed execution will be disabled.")

    def execute_code(
        self,
        language: str,
        code: str,
        use_sandbox: bool = False,
        timeout_sec: Optional[int] = None
    ) -> CodeExecutionResult:
        """
        Executes a block of code either directly or in a sandbox.
        """
        if use_sandbox:
            if not self.docker_sandbox:
                return CodeExecutionResult(status=ExecutionStatus.SETUP_ERROR, stderr="Sandboxed execution requested, but DockerSandbox is not available.")
            return self._execute_in_sandbox(language, code, timeout_sec)
        else:
            return self._execute_directly(language, code, timeout_sec)

    def _execute_in_sandbox(self, language: str, code: str, timeout: Optional[int]) -> CodeExecutionResult:
        logger.warning(f"Executing {language} code in a SECURE DOCKER SANDBOX...")
        start_time = time.monotonic()
        
        # Map our language to a suitable Docker image
        image_map = {"python": "python:3.11-slim", "javascript": "node:18-slim", "shell": "ubuntu:22.04"}
        image = image_map.get(language, "ubuntu:22.04")

        logs, _ = self.docker_sandbox.run_script_in_sandbox(
            script_content=code,
            image=image,
            timeout_sec=timeout or self.default_timeout
        )
        
        # Simple heuristic to determine success from logs, as Docker run captures both stdout/stderr
        # A more robust solution might inspect the container's exit code before removal.
        # For now, we assume an error if common error strings are present.
        error_indicators = ["Traceback", "Error:", "Exception:", "command not found"]
        is_error = any(indicator in logs for indicator in error_indicators)

        return CodeExecutionResult(
            status=ExecutionStatus.RUNTIME_ERROR if is_error else ExecutionStatus.SUCCESS,
            exit_code=1 if is_error else 0, # Placeholder exit code
            stdout=logs if not is_error else "",
            stderr=logs if is_error else "",
            execution_time_ms=(time.monotonic() - start_time) * 1000
        )

    def _execute_directly(self, language: str, code: str, timeout: Optional[int]) -> CodeExecutionResult:
        logger.warning(f"Executing {language} code DIRECTLY ON HOST...")
        start_time = time.monotonic()
        
        interpreter_map = {"python": "python", "javascript": "node", "shell": "bash"}
        file_ext_map = {"python": ".py", "javascript": ".js", "shell": ".sh"}
        
        interpreter = interpreter_map.get(language)
        if not interpreter:
            return CodeExecutionResult(status=ExecutionStatus.SETUP_ERROR, stderr=f"Unsupported language for direct execution: {language}")

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=file_ext_map[language]) as tmp_file:
            tmp_file.write(code)
            tmp_file_path = tmp_file.name

        try:
            result = subprocess.run(
                [interpreter, tmp_file_path],
                capture_output=True,
                text=True,
                timeout=timeout or self.default_timeout,
            )
            status = ExecutionStatus.SUCCESS if result.returncode == 0 else ExecutionStatus.RUNTIME_ERROR
            
            return CodeExecutionResult(
                status=status,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time_ms=(time.monotonic() - start_time) * 1000
            )
        except subprocess.TimeoutExpired:
            return CodeExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                stderr=f"Execution timed out after {timeout or self.default_timeout} seconds.",
                execution_time_ms=(time.monotonic() - start_time) * 1000
            )
        except FileNotFoundError:
             return CodeExecutionResult(
                status=ExecutionStatus.SETUP_ERROR,
                stderr=f"Interpreter '{interpreter}' not found. Is it installed and in your PATH?",
                execution_time_ms=(time.monotonic() - start_time) * 1000
            )
        finally:
            os.unlink(tmp_file_path)

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Dual-Mode Code Executor Prototype 🛡️‍💻 ===")
    print("=========================================================")
    
    executor = CodeExecutor()

    def run_and_print(lang: str, code: str, sandbox: bool):
        mode = "SANDBOXED" if sandbox else "DIRECT"
        print(f"\n--- Executing {lang.upper()} Code ({mode}) ---")
        result = executor.execute_code(lang, code, use_sandbox=sandbox)
        print(f"  Status: {result.status.name}")
        print(f"  Exit Code: {result.exit_code}")
        if result.stdout: print(f"  STDOUT:\n---\n{result.stdout.strip()}\n---")
        if result.stderr: print(f"  STDERR:\n---\n{result.stderr.strip()}\n---")
    
    python_code = "import os\nprint('Hello from Python!')\nprint(f'Current Directory: {os.getcwd()}')\nprint(f'Files: {os.listdir(os.getcwd())}')"
    python_error_code = "print('This will fail')\nx = 1 / 0"

    # --- 1. Direct Execution ---
    print("\n\n*** DEMONSTRATING DIRECT (NON-SANDBOXED) EXECUTION ***")
    run_and_print("python", python_code, sandbox=False)
    run_and_print("python", python_error_code, sandbox=False)
    
    # --- 2. Sandboxed Execution ---
    if executor.docker_sandbox:
        print("\n\n*** DEMONSTRATING SANDBOXED (DOCKER) EXECUTION ***")
        print("!!! PREREQUISITE: Docker must be installed and running. !!!")
        run_and_print("python", python_code, sandbox=True)
        run_and_print("python", python_error_code, sandbox=True)
    else:
        print("\n\n*** SKIPPING SANDBOXED DEMO: DockerSandbox module not available. ***")

    print("\n=========================================================")
    print("=== Code Executor Prototype Complete ===")
    print("=========================================================")
