# Devin/security/sandbox/docker_sandbox.py
# Purpose: Provides a secure environment for executing code and commands
#          within an isolated Docker container.

import logging
import docker
import tempfile
import shutil
from pathlib import Path
from typing import Tuple, Optional, List

# Configure basic logging
logger = logging.getLogger("DockerSandbox")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class DockerSandbox:
    """
    Manages the execution of scripts within isolated Docker containers.
    """
    def __init__(self):
        try:
            self.client = docker.from_env()
            # Check if Docker is running
            self.client.ping()
            logger.info("Docker client initialized successfully.")
        except ImportError:
            raise ImportError("The 'docker' library is required. 'pip install docker'")
        except Exception as e:
            logger.error("Docker daemon is not running or is not accessible.")
            logger.error("Please ensure Docker is installed and started.")
            raise ConnectionError(f"Could not connect to Docker daemon: {e}")

    def run_script_in_sandbox(
        self,
        script_content: str,
        image: str = "python:3.11-slim",
        timeout_sec: int = 120
    ) -> Tuple[str, List[Path]]:
        """
        Runs a script in a new Docker container and returns the output.

        Args:
            script_content: A string containing the Python code to execute.
            image: The Docker image to use for the container (e.g., 'python:3.11-slim').
            timeout_sec: Maximum execution time in seconds.

        Returns:
            A tuple containing (logs, output_files_list).
            - logs: The combined stdout and stderr from the container.
            - output_files_list: A list of Path objects for any files created by the script.
        """
        # Create a temporary directory on the host to act as the shared workspace
        with tempfile.TemporaryDirectory() as host_workspace:
            host_path = Path(host_workspace)
            script_path = host_path / "main.py"
            script_path.write_text(script_content)

            container_workspace = "/workspace"
            
            # The command to run inside the container. We redirect stderr to stdout.
            command = f"/bin/sh -c 'python {container_workspace}/main.py 2>&1'"

            logger.warning(f"Preparing to run script in a '{image}' container...")
            
            container = None
            try:
                # Run the container. This blocks until the container finishes.
                container = self.client.containers.run(
                    image=image,
                    command=command,
                    volumes={str(host_path): {'bind': container_workspace, 'mode': 'rw'}},
                    working_dir=container_workspace,
                    remove=True,  # Automatically remove the container on exit
                    detach=True,  # Detach to manage timeout manually
                )

                # Manually wait for the container with a timeout
                result = container.wait(timeout=timeout_sec)
                logs = container.logs().decode('utf-8')
                
                # Check for non-zero exit code
                if result.get('StatusCode', 0) != 0:
                    logger.error(f"Container exited with non-zero status code: {result.get('StatusCode')}")

                # Find any files created by the script in the workspace
                output_files = [p for p in host_path.iterdir() if p != script_path]
                
                logger.info("Sandbox execution finished.")
                return logs, output_files

            except docker.errors.ImageNotFound:
                logger.error(f"Docker image '{image}' not found. Please pull it first or check the name.")
                return f"Error: Docker image '{image}' not found.", []
            except docker.errors.ContainerError as e:
                logger.error(f"An error occurred inside the container: {e}")
                return str(e), []
            except Exception as e:
                # This could be a timeout from container.wait()
                if container:
                    container.kill() # Ensure container is stopped on timeout
                logger.error(f"An unexpected error occurred during sandbox execution: {e}")
                return f"Execution failed: {e}", []


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Docker Sandbox Execution Prototype 🐳📦 ===")
    print("=========================================================")
    print("!!! PREREQUISITE: This tool requires Docker to be installed and running. !!!")
    
    try:
        sandbox = DockerSandbox()
        
        # --- 1. Demo of a successful script that creates a file ---
        print("\n--- 1. Running a successful script that creates an output file ---")
        success_script = (
            "print('Hello from inside the sandbox!')\n"
            "with open('output.txt', 'w') as f:\n"
            "    f.write('This file was generated inside the container.')\n"
            "print('Successfully created output.txt.')\n"
        )
        logs_success, files_success = sandbox.run_script_in_sandbox(success_script)
        
        print("\nContainer Logs:")
        print("--------------------")
        print(logs_success.strip())
        print("--------------------")
        
        print("\nFiles created by the script:")
        if files_success:
            for f in files_success:
                print(f"  - {f.name} (Content: '{f.read_text()}')")
        else:
            print("  - None")

        # --- 2. Demo of a script that causes an error ---
        print("\n\n--- 2. Running a script that will raise an exception ---")
        error_script = (
            "import sys\n"
            "print('This script will now cause an error.')\n"
            "sys.exit(5)" # Exit with a non-zero status code
        )
        logs_error, _ = sandbox.run_script_in_sandbox(error_script)
        
        print("\nContainer Logs (showing error):")
        print("--------------------")
        print(logs_error.strip())
        print("--------------------")

    except (ImportError, ConnectionError) as e:
        logger.critical(f"Could not run demo: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during the demo: {e}", exc_info=True)

    print("\n=========================================================")
    print("=== Docker Sandbox Prototype Complete ===")
    print("=========================================================")
