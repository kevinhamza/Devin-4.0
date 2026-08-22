# Devin/prototypes/code_execution_prototypes.py
# Purpose: Prototype implementations for securely executing code snippets.

import logging
import os
import sys
import subprocess
import shlex # For safe command string splitting
import tempfile
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple, Literal, TypedDict

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("CodeExecutionPrototype")

# --- CRITICAL SECURITY WARNINGS ---
logger.critical("###################################################################")
logger.critical("!!! EXTREME SECURITY RISK: ARBITRARY CODE EXECUTION PROTOTYPE !!!")
logger.critical("This module outlines concepts for code execution. Real implementation")
logger.critical("REQUIRES ROBUST, SECURE SANDBOXING (e.g., Docker, Firecracker, gVisor).")
logger.critical("Executing untrusted code directly via subprocess is DANGEROUS.")
logger.critical("All code execution must be subject to strict user permissions and auditing.")
logger.critical("###################################################################")

# --- Data Structures ---

class ExecutionResult(TypedDict):
    """Structure to hold the result of a code execution attempt."""
    stdout: Optional[str]
    stderr: Optional[str]
    return_code: Optional[int]
    duration_sec: float
    error_message: Optional[str] # For errors in the execution framework itself
    timed_out: bool

# --- Code Execution Prototype Class ---

class CodeExecutionPrototype:
    """
    Conceptual prototype for executing code snippets in various languages.
    Prioritizes outlining sandboxing concepts (e.g., via Docker).
    """

    DEFAULT_TIMEOUT_SEC = 60 # Default execution timeout
    # Conceptual map of languages to suitable Docker images for sandboxing
    DEFAULT_DOCKER_IMAGE_MAP = {
        "python": "python:3.11-slim",
        "javascript": "node:18-slim", # For Node.js
        "bash": "ubuntu:latest", # Or a minimal image with bash
        "sh": "busybox:latest", # Minimal shell
        "powershell": "mcr.microsoft.com/powershell:latest"
    }

    def __init__(self,
                 default_timeout: int = DEFAULT_TIMEOUT_SEC,
                 use_docker_sandbox_by_default: bool = True, # Strongly recommend True for security
                 docker_image_map: Optional[Dict[str, str]] = None):
        """
        Initializes the CodeExecutionPrototype.

        Args:
            default_timeout (int): Default timeout in seconds for code execution.
            use_docker_sandbox_by_default (bool): If True, conceptual Docker execution
                                                 will be the preferred path for safety.
            docker_image_map (Optional[Dict[str, str]]): Mapping of language names
                                                         to Docker images for sandboxing.
        """
        self.default_timeout = default_timeout
        # Although Docker is safer, acknowledge user preference for Devin's operation model
        # by potentially allowing local subprocess as the path taken if specified.
        # However, we strongly log warnings if Docker isn't used.
        self.use_docker_by_default = use_docker_sandbox_by_default
        self.docker_image_map = docker_image_map if docker_image_map is not None else self.DEFAULT_DOCKER_IMAGE_MAP

        if self.use_docker_by_default:
            logger.info(f"CodeExecutionPrototype initialized. Defaulting to Docker sandboxing (conceptual).")
            self._docker_available = self._check_docker_availability_conceptual()
            if not self._docker_available:
                 logger.warning("Docker check failed. Will fallback to INSECURE local subprocess execution.")
                 # Fallback if Docker preferred but unavailable? Or fail? Let's fallback with warning.
                 self.use_docker_by_default = False # Force fallback for this instance
        else:
            logger.warning("CodeExecutionPrototype initialized WITHOUT Docker sandboxing by default. "
                           "Subprocess execution is INSECURE for untrusted code.")
            self._docker_available = False # Assume unavailable if not default


    def _check_docker_availability_conceptual(self) -> bool:
        """Conceptual check if Docker client/daemon is available."""
        logger.info("Conceptual check for Docker availability...")
        # In reality, use 'docker' library:
        # try:
        #     import docker
        #     client = docker.from_env()
        #     client.ping() # Check if daemon is running
        #     logger.info("  - Docker daemon appears to be running.")
        #     return True
        # except ImportError:
        #     logger.warning("  - Docker SDK for Python not installed (`pip install docker`). Cannot use Docker sandbox.")
        #     return False
        # except Exception as e: # Catches errors like Docker daemon not running
        #     logger.warning(f"  - Docker not available or not running: {e}")
        #     logger.warning("    Docker-based sandboxing will fail.")
        #     return False
        # Simulate check - assume available for prototype if docker sandbox is preferred initially
        if self.use_docker_by_default:
            logger.info("  - Conceptual Docker check passed.")
            return True
        logger.info("  - Conceptual Docker check skipped (not default).")
        return False


    def _execute_with_subprocess(self,
                                 command_list: List[str],
                                 input_str: Optional[str] = None,
                                 timeout: Optional[int] = None,
                                 cwd: Optional[str] = None,
                                 env_vars: Optional[Dict[str,str]] = None) -> ExecutionResult:
        """
        Helper to execute a command using subprocess.run.
        This is the fallback if Docker is not used, and is INSECURE for untrusted code.
        """
        exec_timeout = timeout if timeout is not None else self.default_timeout
        start_time = time.monotonic()
        error_msg = None
        timed_out_flag = False
        stdout, stderr = None, None
        return_code = -1 # Default to error

        try:
            logger.debug(f"Executing (subprocess): {' '.join(shlex.quote(arg) for arg in command_list)}")
            # Combine with current environment variables if new ones are passed
            current_env = os.environ.copy()
            if env_vars:
                current_env.update(env_vars)

            process = subprocess.run(
                command_list,
                input=input_str,
                capture_output=True,
                text=True, # Decode stdout/stderr as text using default encoding
                encoding=sys.getdefaultencoding(), # Be explicit, though text=True often handles it
                errors='replace', # Handle potential decoding errors
                timeout=exec_timeout,
                cwd=cwd,
                env=current_env,
                check=False # Don't raise for non-zero, capture it
            )
            stdout = process.stdout
            stderr = process.stderr
            return_code = process.returncode
        except FileNotFoundError:
            stderr = f"Command not found: {command_list[0]}. Ensure the executable (python, node, bash, etc.) is in the system PATH."
            error_msg = stderr
            logger.error(stderr)
        except subprocess.TimeoutExpired:
            stderr = f"Command timed out after {exec_timeout} seconds."
            error_msg = stderr
            timed_out_flag = True
            logger.error(stderr)
        except Exception as e:
            stderr = f"Unexpected error executing command: {e}"
            error_msg = stderr
            logger.exception("Error in _execute_with_subprocess") # Log full traceback

        duration_sec = time.monotonic() - start_time
        logger.debug(f"Subprocess Result: RC={return_code}, Timeout={timed_out_flag}, Duration={duration_sec:.3f}s")
        return ExecutionResult(
            stdout=stdout, stderr=stderr, return_code=return_code,
            duration_sec=duration_sec, error_message=error_msg, timed_out=timed_out_flag
        )

    def _execute_in_docker_placeholder(self,
                                       language_key: str,
                                       code_to_execute: str,
                                       input_str: Optional[str] = None,
                                       timeout: Optional[int] = None,
                                       container_script_name: str = "script_to_run"
                                       ) -> ExecutionResult:
        """
        Conceptual placeholder for executing code within a Docker container.
        This is the PREFERRED method for security.
        """
        exec_timeout = timeout if timeout is not None else self.default_timeout
        start_time = time.monotonic()
        logger.info(f"Preparing conceptual Docker execution for language: {language_key}")
        logger.warning("Executing DOCKER PLACEHOLDER - Simulating only. Requires Docker setup.")

        docker_image = self.docker_image_map.get(language_key)
        if not docker_image:
            err_msg = f"No Docker image configured for language '{language_key}'."
            logger.error(err_msg)
            return ExecutionResult(stdout=None, stderr=err_msg, return_code=-1,
                                   duration_sec=time.monotonic() - start_time,
                                   error_message="Configuration error.", timed_out=False)

        result: ExecutionResult = {
            "stdout": None, "stderr": None, "return_code": -1,
            "duration_sec": 0.0, "error_message": None, "timed_out": False
        }

        # --- Placeholder: Docker Execution Logic ---
        # This block simulates the steps without actually running Docker
        temp_dir_host = None
        try:
            # 1. Create temp directory on host
            temp_dir_host = tempfile.mkdtemp(prefix="devin_docker_exec_")
            logger.debug(f"  - Created host temp dir: {temp_dir_host}")

            # 2. Write code to temp file
            script_extension = ".py" if language_key == "python" else ".js" if language_key == "javascript" else ".sh"
            host_script_path = os.path.join(temp_dir_host, f"{container_script_name}{script_extension}")
            with open(host_script_path, "w", encoding="utf-8") as f:
                f.write(code_to_execute)
            logger.debug(f"  - Wrote code to: {host_script_path}")

            # 3. Write input to temp file if provided
            host_input_path = None
            container_input_redirect = ""
            if input_str is not None:
                host_input_path = os.path.join(temp_dir_host, "input.txt")
                with open(host_input_path, "w", encoding="utf-8") as f:
                    f.write(input_str)
                container_input_redirect = "< /sandbox/input.txt" # Redirect stdin inside container
                logger.debug(f"  - Wrote stdin to: {host_input_path}")

            # 4. Construct conceptual docker run command
            container_sandbox_path = "/sandbox"
            # Mount needs careful consideration of read-only vs read-write if script needs to create files
            # Using read-only for code/input is safer. Need separate writable mount for output if script writes files.
            volume_mount = f"{os.path.abspath(temp_dir_host)}:{container_sandbox_path}:ro" # Read-only mount

            # Resource limits (adjust as needed)
            memory_limit = "256m"
            cpu_limit = "0.5"

            # Determine interpreter and script path inside container
            container_script_path = f"{container_sandbox_path}/{container_script_name}{script_extension}"
            interpreter = ""
            if language_key == "python": interpreter = "python"
            elif language_key == "javascript": interpreter = "node"
            elif language_key == "bash": interpreter = "bash"
            elif language_key == "sh": interpreter = "sh"
            elif language_key == "powershell": interpreter = "pwsh" # Assumes PowerShell core image

            if not interpreter: raise ValueError(f"Unsupported language for Docker execution: {language_key}")

            # Assemble the command to run *inside* the container
            # Redirect stdin if input file exists
            command_inside_container = f"{interpreter} {container_script_path} {container_input_redirect}"

            # Assemble the full docker run command
            docker_command = [
                "docker", "run",
                "--rm", # Remove container automatically after exit
                # Security settings:
                "--read-only", # Make container filesystem read-only (except for explicit mounts)
                "--network", "none", # Disable networking by default unless required
                "--memory", memory_limit, # Limit memory
                "--cpus", cpu_limit, # Limit CPU usage
                # Add --cap-drop ALL --security-opt no-new-privileges for more security?
                # Volume mount:
                "-v", volume_mount,
                # Working directory inside container:
                "-w", container_sandbox_path,
                # Image to use:
                docker_image,
                # Command to run (use 'sh -c' to handle redirection etc.):
                "sh", "-c", command_inside_container
            ]

            # 5. Execute the docker run command using subprocess helper
            logger.info(f"  - Conceptually running Docker command (timeout={exec_timeout}s)...")
            # NOTE: The timeout here applies to the *docker run* command itself, which includes
            # container startup time. Need separate mechanism for timeout *inside* the container.
            docker_result = self._execute_with_subprocess(docker_command, input_str=None, timeout=exec_timeout + 10) # Add buffer for docker overhead

            # 6. Capture results
            result = ExecutionResult(
                 stdout=docker_result['stdout'], stderr=docker_result['stderr'], return_code=docker_result['return_code'],
                 duration_sec=time.monotonic() - start_time, error_message=docker_result['error_message'], timed_out=docker_result['timed_out']
            )

        except Exception as e:
             logger.exception("Error during conceptual Docker execution preparation or execution.")
             result = ExecutionResult(stdout=None, stderr=str(e), return_code=-1,
                                      duration_sec=time.monotonic() - start_time,
                                      error_message=f"Docker Execution Framework Error: {e}", timed_out=False)
        finally:
            # 7. Clean up host temporary directory
            if temp_dir_host and os.path.exists(temp_dir_host):
                try:
                    shutil.rmtree(temp_dir_host)
                    logger.debug(f"  - Removed host temp dir: {temp_dir_host}")
                except Exception as e:
                    logger.error(f"  - Error cleaning up host temp dir {temp_dir_host}: {e}")
        # --- End Placeholder ---

        logger.info(f"Conceptual Docker execution finished. RC: {result['return_code']}, Timeout: {result['timed_out']}")
        return result


    def execute_python_code(self,
                            code: str,
                            input_str: Optional[str] = None,
                            timeout: Optional[int] = None,
                            env_vars: Optional[Dict[str,str]] = None
                            ) -> ExecutionResult:
        """
        Executes a Python code snippet securely (ideally using Docker sandbox).

        Args:
            code (str): The Python code string.
            input_str (Optional[str]): String to pass to the script's stdin.
            timeout (Optional[int]): Execution timeout in seconds.
            env_vars (Optional[Dict[str,str]]): Environment variables for execution.

        Returns:
            ExecutionResult: Dictionary containing stdout, stderr, return code, etc.
        """
        exec_timeout = timeout if timeout is not None else self.default_timeout
        logger.info(f"Attempting to execute Python code...")

        if self.use_docker_by_default and self._docker_available:
             return self._execute_in_docker_placeholder(
                 language_key="python",
                 code_to_execute=code,
                 input_str=input_str,
                 timeout=exec_timeout,
                 container_script_name="script.py"
             )
        else:
            logger.warning("Executing Python locally via subprocess - INSECURE for untrusted code.")
            # Write code to temp file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding='utf-8') as tmp_py_file:
                tmp_py_file.write(code)
                tmp_py_file_path = tmp_py_file.name
            logger.debug(f"  - Python code written to temporary file: {tmp_py_file_path}")

            try:
                # Use sys.executable to ensure running with the same Python interpreter
                result = self._execute_with_subprocess(
                    [sys.executable, tmp_py_file_path],
                    input_str=input_str,
                    timeout=exec_timeout,
                    env_vars=env_vars
                )
            finally:
                # Clean up temp file
                try:
                    os.remove(tmp_py_file_path)
                    logger.debug(f"  - Temporary Python file deleted: {tmp_py_file_path}")
                except OSError as e:
                    logger.error(f"  - Error deleting temporary Python file {tmp_py_file_path}: {e}")
            return result

# Ensure logger and ExecutionResult TypedDict are available from Part 1
import logging
logger = logging.getLogger("CodeExecutionPrototype") # Ensure logger is accessible

from typing import Dict, Any, List, Optional, Tuple, Literal, TypedDict
import os
import sys
import subprocess
import shlex
import tempfile
import uuid
import time

# If ExecutionResult was defined in Part 1, it should be available.
# For clarity if this part is viewed standalone, here's a reminder:
class ExecutionResult(TypedDict):
    stdout: Optional[str]
    stderr: Optional[str]
    return_code: Optional[int]
    duration_sec: float
    error_message: Optional[str]
    timed_out: bool

class CodeExecutionPrototype:
    # (Assume __init__, _check_docker_availability_conceptual,
    #  _execute_with_subprocess, _execute_in_docker_placeholder,
    #  and execute_python_code from Part 1 are defined here)

    def execute_javascript_code(self,
                                code: str,
                                input_str: Optional[str] = None,
                                timeout: Optional[int] = None,
                                node_path: str = "node", # Path to Node.js executable
                                env_vars: Optional[Dict[str,str]] = None
                                ) -> ExecutionResult:
        """
        Executes a JavaScript code snippet using Node.js.

        Args:
            code (str): The JavaScript code string to execute.
            input_str (Optional[str]): String to pass to the script's stdin.
            timeout (Optional[int]): Execution timeout in seconds. Uses default if None.
            node_path (str): Path to the Node.js executable.
            env_vars (Optional[Dict[str,str]]): Environment variables to set for execution.

        Returns:
            ExecutionResult: Dictionary containing stdout, stderr, return code, etc.
        """
        exec_timeout = timeout if timeout is not None else self.default_timeout
        start_time = time.monotonic()
        logger.info(f"Attempting to execute JavaScript code (Node.js)...")
        logger.warning("SECURITY: Executing JavaScript via subprocess locally. Ensure Node.js is secure and code is trusted or heavily sandboxed in production.")

        if self.use_docker_by_default and self.docker_image_map.get("javascript"):
            logger.info("  - Routing JavaScript execution to conceptual Docker sandbox...")
            return self._execute_in_docker_placeholder(
                language_key="javascript",
                code_to_execute=code,
                input_str=input_str,
                timeout=exec_timeout,
                container_script_name="script.js" # Example name
            )
        else:
            logger.info("  - Executing JavaScript locally using Node.js via subprocess.")
            # Create a temporary file to write the JS code
            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding='utf-8') as tmp_js_file:
                tmp_js_file.write(code)
                tmp_js_file_path = tmp_js_file.name
            logger.debug(f"  - JavaScript code written to temporary file: {tmp_js_file_path}")

            try:
                result = self._execute_with_subprocess(
                    [node_path, tmp_js_file_path],
                    input_str=input_str,
                    timeout=exec_timeout,
                    env_vars=env_vars
                )
            finally:
                # Clean up the temporary file
                try:
                    os.remove(tmp_js_file_path)
                    logger.debug(f"  - Temporary JavaScript file deleted: {tmp_js_file_path}")
                except OSError as e:
                    logger.error(f"  - Error deleting temporary JavaScript file {tmp_js_file_path}: {e}")
            return result


    def execute_shell_command(self,
                              command_str: str,
                              shell_type: Literal['bash', 'sh', 'powershell', 'cmd'] = 'bash',
                              timeout: Optional[int] = None,
                              cwd: Optional[str] = None,
                              env_vars: Optional[Dict[str,str]] = None
                              ) -> ExecutionResult:
        """
        Executes a shell command or script.

        *** EXTREME SECURITY WARNING: Executing arbitrary shell commands received
        *** from an AI or external input is EXCEPTIONALLY DANGEROUS. This method
        *** MUST be protected by stringent permissions, sanitization (if possible,
        *** but hard for general commands), and preferably run in a deeply
        *** isolated sandbox. User permission alone for Devin to call this is
        *** insufficient if the command_str itself is untrusted.
        *** Consider this primarily for Devin executing *pre-defined* or
        *** *strictly validated* commands.

        Args:
            command_str (str): The shell command string to execute.
            shell_type (Literal): The type of shell to use ('bash', 'sh', 'powershell', 'cmd').
            timeout (Optional[int]): Execution timeout in seconds.
            cwd (Optional[str]): Current working directory for the command.
            env_vars (Optional[Dict[str,str]]): Environment variables to set.

        Returns:
            ExecutionResult: Dictionary containing stdout, stderr, return code, etc.
        """
        exec_timeout = timeout if timeout is not None else self.default_timeout
        start_time = time.monotonic()
        logger.info(f"Attempting to execute shell command ({shell_type})...")
        logger.critical(f"  - COMMAND: {command_str[:200]}{'...' if len(command_str) > 200 else ''}")
        logger.critical("  - !!! EXTREME SECURITY WARNING: EXECUTING ARBITRARY SHELL COMMAND !!!")
        logger.critical("  - !!! ENSURE THIS IS HEAVILY SANDBOXED AND PERMISSIONED !!!")

        if self.use_docker_by_default and self.docker_image_map.get(shell_type):
             logger.info("  - Routing shell command execution to conceptual Docker sandbox...")
             # Docker execution needs to handle the command string passed to the shell inside the container
             # This is slightly different from just running a script file.
             # The `_execute_in_docker_placeholder` needs to be adapted or a new one created.
             # For now, let's make a conceptual call assuming it handles "-c" style execution.
             # This typically involves writing the command_str to a temporary script inside the container
             # or passing it directly if the container entrypoint is a shell.
             return self._execute_in_docker_placeholder(
                 language_key=shell_type,
                 code_to_execute=command_str, # Pass command as "code" to be run by shell
                 input_str=None, # Shell commands usually don't take stdin this way directly
                 timeout=exec_timeout,
                 container_script_name="run_command.sh" # Docker placeholder will wrap this
             )
        else:
            logger.info(f"  - Executing shell command ({shell_type}) locally via subprocess.")
            shell_executable_path: Optional[str] = None
            command_args: List[str] = []

            if shell_type == 'bash':
                shell_executable_path = shutil.which("bash") or "bash"
                command_args = [shell_executable_path, "-c", command_str]
            elif shell_type == 'sh':
                shell_executable_path = shutil.which("sh") or "sh"
                command_args = [shell_executable_path, "-c", command_str]
            elif shell_type == 'powershell':
                # pwsh for PowerShell 7+, powershell for Windows PowerShell 5.1
                shell_executable_path = shutil.which("pwsh") or shutil.which("powershell") or "powershell"
                command_args = [shell_executable_path, "-NoProfile", "-Command", command_str]
            elif shell_type == 'cmd':
                if sys.platform != "win32":
                    return ExecutionResult(stdout=None, stderr="Cannot execute 'cmd' on non-Windows.", return_code=-1,
                                           duration_sec=time.monotonic()-start_time, error_message="Platform error.", timed_out=False)
                shell_executable_path = os.environ.get("COMSPEC", "cmd.exe")
                command_args = [shell_executable_path, "/C", command_str]
            else:
                return ExecutionResult(stdout=None, stderr=f"Unsupported shell type: {shell_type}", return_code=-1,
                                       duration_sec=time.monotonic()-start_time, error_message="Configuration error.", timed_out=False)

            return self._execute_with_subprocess(command_args, input_str=None, timeout=exec_timeout, cwd=cwd, env_vars=env_vars)

# --- Main Execution Block (Example Usage) ---
if __name__ == "__main__":
    print("=================================================")
    print("=== Running Code Execution Prototypes ===")
    print("=================================================")
    print("(Note: Relies on conceptual implementations & local tools like Python/Node.js)")
    print("*** SECURITY WARNING: Direct subprocess execution is INSECURE for untrusted code! ***")
    print("-" * 50)

    # Instantiate with default (conceptual Docker preferred, fallback to local subprocess)
    # To force local subprocess for this example: use_docker_sandbox_by_default=False
    code_executor = CodeExecutionPrototype(use_docker_sandbox_by_default=False)


    # --- Python Execution Example (from Part 1 conceptually) ---
    print("\n--- [Python Execution Example] ---")
    python_code = """
import sys
import os
print("Hello from Python!")
print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}")
print(f"Current working directory: {os.getcwd()}")
# Simulate reading stdin if provided
# try:
#     indata = sys.stdin.read()
#     if indata:
#         print(f"Received from stdin: {indata.strip()}")
# except Exception:
#     pass # No stdin
print("Python script finished.")
    """
    py_result = code_executor.execute_python_code(python_code, timeout=10)
    print("Python Execution Result:")
    print(f"  Return Code: {py_result['return_code']}")
    print(f"  Stdout:\n{py_result['stdout'] or ''}")
    if py_result['stderr']: print(f"  Stderr:\n{py_result['stderr']}")
    if py_result['error_message']: print(f"  Framework Error: {py_result['error_message']}")
    print(f"  Duration: {py_result['duration_sec']:.3f}s, Timed Out: {py_result['timed_out']}")

    # --- JavaScript (Node.js) Execution Example ---
    print("\n--- [JavaScript (Node.js) Execution Example] ---")
    js_code = """
    console.log("Hello from JavaScript (Node.js)!");
    console.log(`Node.js version: ${process.version}`);
    console.log(`Current working directory: ${process.cwd()}`);
    // Simulate reading stdin
    // process.stdin.on('data', (data) => {
    //   console.log(`Received from stdin: ${data.toString().trim()}`);
    // });
    console.log("JavaScript script finished.");
    """
    js_result = code_executor.execute_javascript_code(js_code, timeout=10)
    print("JavaScript Execution Result:")
    print(f"  Return Code: {js_result['return_code']}")
    print(f"  Stdout:\n{js_result['stdout'] or ''}")
    if js_result['stderr']: print(f"  Stderr:\n{js_result['stderr']}")
    if js_result['error_message']: print(f"  Framework Error: {js_result['error_message']}")
    print(f"  Duration: {js_result['duration_sec']:.3f}s, Timed Out: {js_result['timed_out']}")

    # --- Shell Command Execution Example ---
    print("\n--- [Shell Command Execution Example] ---")
    # Use a safe, simple command for demonstration
    shell_cmd_to_run = "echo Hello from shell prototype && (python --version || python3 --version)" # Try python then python3
    shell_type_to_use: Literal['bash', 'sh', 'powershell', 'cmd'] = 'bash' # Default to bash
    if sys.platform == "win32":
        shell_cmd_to_run = "echo Hello from shell prototype && ver" # Windows specific safe command
        shell_type_to_use = 'cmd'

    shell_result = code_executor.execute_shell_command(shell_cmd_to_run, shell_type=shell_type_to_use, timeout=10)
    print(f"Shell Command ({shell_type_to_use}) Execution Result:")
    print(f"  Return Code: {shell_result['return_code']}")
    print(f"  Stdout:\n{shell_result['stdout'] or ''}")
    if shell_result['stderr']: print(f"  Stderr:\n{shell_result['stderr']}")
    if shell_result['error_message']: print(f"  Framework Error: {shell_result['error_message']}")
    print(f"  Duration: {shell_result['duration_sec']:.3f}s, Timed Out: {shell_result['timed_out']}")


    print("\n=================================================")
    print("=== Code Execution Prototypes Complete ===")
    print("=================================================")
