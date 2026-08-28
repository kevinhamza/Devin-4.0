# Devin/edge/tinyML/tensorflow_lite_deploy.py
# Purpose: Handles deployment and basic remote testing of TFLite models on Raspberry Pi (or similar Linux edge devices) via SSH/SCP.

import os
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

# Attempt to import paramiko for SSH/SCP functionality
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    print("WARNING: 'paramiko' library not found (pip install paramiko). TFLiteDeployer will use non-functional placeholders.")
    paramiko = None # type: ignore
    PARAMIKO_AVAILABLE = False

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("TFLiteDeployer")


class TFLiteDeployer:
    """
    Manages deployment of TensorFlow Lite models to edge devices like Raspberry Pi
    using SSH and SCP for file transfer and command execution.

    Requires Paramiko library and configured SSH access to the target device.
    """

    DEFAULT_SSH_PORT = 22
    DEFAULT_REMOTE_PYTHON = "python3" # Python executable on target device

    def __init__(self,
                 host: str,
                 port: int = DEFAULT_SSH_PORT,
                 username: str = "pi", # Common default for Raspberry Pi
                 password: Optional[str] = None, # Less secure, use key_filename if possible
                 key_filename: Optional[str] = None, # Path to SSH private key file
                 remote_python_path: str = DEFAULT_REMOTE_PYTHON
                 ):
        """
        Initializes the TFLiteDeployer with target device connection details.

        Args:
            host (str): IP address or hostname of the target Raspberry Pi.
            port (int): SSH port on the target device.
            username (str): Username for SSH login.
            password (Optional[str]): Password for SSH login (use key_filename instead if possible).
            key_filename (Optional[str]): Path to the SSH private key file for authentication.
            remote_python_path (str): Path to the python3 executable on the remote device.

        *** Store credentials securely (e.g., load from env vars/secrets manager), do not hardcode. ***
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password # Store securely if used
        self.key_filename = key_filename # Store securely if used
        self.remote_python = remote_python_path
        self.ssh_client: Optional[Any] = None # Will hold paramiko.SSHClient instance

        if not PARAMIKO_AVAILABLE:
             logger.error("Paramiko library not installed. Deployment features will not work.")
        else:
             # Initialize SSH client but don't connect yet
             self.ssh_client = paramiko.SSHClient()
             # Automatically add host keys (less secure, better to manage known_hosts)
             # In production, use set_missing_host_key_policy(paramiko.WarningPolicy())
             # or load known host keys. AutoAddPolicy is convenient for testing.
             self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
             logger.info(f"TFLiteDeployer initialized for target {username}@{host}:{port}")


    def _connect(self) -> bool:
        """Establishes SSH connection using stored credentials."""
        if not self.ssh_client: return False
        if self.ssh_client.get_transport() and self.ssh_client.get_transport().is_active():
             # logger.debug("SSH connection already active.")
             return True # Already connected

        logger.info(f"Connecting to {self.username}@{self.host}:{self.port} via SSH...")
        try:
            # Prioritize key-based authentication
            if self.key_filename:
                 if not os.path.exists(self.key_filename):
                      logger.error(f"SSH key file not found: {self.key_filename}")
                      return False
                 # Example key types (add others if needed)
                 # key = paramiko.RSAKey.from_private_key_file(self.key_filename)
                 # key = paramiko.Ed25519Key.from_private_key_file(self.key_filename)
                 # key = paramiko.ECDSAKey.from_private_key_file(self.key_filename)
                 # Auto-detect key type is usually handled by connect() if key specified
                 self.ssh_client.connect(hostname=self.host, port=self.port, username=self.username, key_filename=self.key_filename, timeout=10)
                 logger.info("SSH connection successful (Key Auth).")
            elif self.password:
                 self.ssh_client.connect(hostname=self.host, port=self.port, username=self.username, password=self.password, timeout=10)
                 logger.info("SSH connection successful (Password Auth).")
            else:
                 logger.error("SSH connection failed: No password or key filename provided.")
                 return False
            return True
        except paramiko.AuthenticationException:
            logger.error("SSH Authentication failed. Check username/password/key.")
            return False
        except paramiko.SSHException as e:
            logger.error(f"SSH connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during SSH connection: {e}")
            return False

    def _disconnect(self):
        """Closes the SSH connection."""
        if self.ssh_client and self.ssh_client.get_transport() and self.ssh_client.get_transport().is_active():
            logger.info(f"Closing SSH connection to {self.host}...")
            self.ssh_client.close()

    def _execute_remote_command(self, command: str, timeout: int = 60) -> Tuple[Optional[int], str, str]:
        """Executes a command remotely via SSH and returns status, stdout, stderr."""
        if not self._connect(): return None, "", "SSH Connection Failed"
        logger.info(f"Executing remote command: {command}")
        stdout_data = ""
        stderr_data = ""
        exit_status = None
        try:
            # Use invoke_shell() for interactive sessions, exec_command for single commands
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            exit_status = stdout.channel.recv_exit_status() # Blocks until command finishes
            stdout_data = stdout.read().decode('utf-8', errors='ignore')
            stderr_data = stderr.read().decode('utf-8', errors='ignore')
            logger.debug(f"Remote command exit status: {exit_status}")
            if stdout_data: logger.debug(f"Remote stdout:\n{stdout_data.strip()}")
            if stderr_data: logger.warning(f"Remote stderr:\n{stderr_data.strip()}")
        except paramiko.SSHException as e:
             logger.error(f"SSH error during command execution: {e}")
             stderr_data = f"SSH Execution Error: {e}"
             exit_status = -1 # Indicate execution error
        except Exception as e:
             logger.error(f"Unexpected error executing remote command '{command}': {e}")
             stderr_data = f"Unexpected Execution Error: {e}"
             exit_status = -1
        # Keep connection open for potential subsequent commands
        # self._disconnect()
        return exit_status, stdout_data, stderr_data

    def _transfer_file_scp(self, local_path: str, remote_path: str) -> bool:
        """Transfers a local file to the remote device using SCP."""
        if not self._connect(): return False
        logger.info(f"Transferring '{local_path}' to {self.host}:{remote_path} via SCP...")
        try:
            # Paramiko's SFTP client is often used for SCP-like transfers
            sftp = self.ssh_client.open_sftp()
            # Ensure remote directory exists (conceptual - requires separate command execution)
            # remote_dir = os.path.dirname(remote_path)
            # self._execute_remote_command(f"mkdir -p {remote_dir}") # Might fail if perms wrong
            sftp.put(local_path, remote_path)
            sftp.close()
            logger.info("File transfer successful.")
            return True
        except Exception as e:
             logger.error(f"SCP file transfer failed: {e}")
             # Close SFTP if open
             try: sftp.close()
             except: pass
             return False


    # --- Public Deployment Methods ---

    def deploy_model(self, local_tflite_path: str, remote_deploy_path: str) -> bool:
        """
        Deploys the .tflite model file to the target device.

        Args:
            local_tflite_path (str): Path to the .tflite file on the host machine.
            remote_deploy_path (str): Full path (including filename) where the model
                                      should be saved on the target device.

        Returns:
            bool: True if deployment (file transfer) was successful, False otherwise.
        """
        logger.info("Starting model deployment...")
        if not os.path.exists(local_tflite_path):
             logger.error(f"Deployment failed: Local model file not found at '{local_tflite_path}'")
             return False
        if not PARAMIKO_AVAILABLE:
             logger.error("Deployment failed: Paramiko library not installed.")
             return False

        # Ensure remote directory exists (best effort)
        remote_dir = os.path.dirname(remote_deploy_path)
        if remote_dir and remote_dir != '.':
            logger.info(f"Ensuring remote directory exists: {remote_dir}")
            status, _, stderr = self._execute_remote_command(f"mkdir -p {remote_dir}")
            if status != 0:
                 logger.warning(f"Could not ensure remote directory exists (might fail): {stderr}")
                 # Proceed anyway, SCP might handle it or fail more clearly

        # Transfer the file
        success = self._transfer_file_scp(local_tflite_path, remote_deploy_path)
        # self._disconnect() # Keep connection open maybe? Or close after operation? Closing for now.
        self._disconnect()
        return success

    def install_tflite_runtime(self, package_name: str = "tflite-runtime", use_sudo: bool = False) -> bool:
        """
        Attempts to install the TensorFlow Lite runtime on the target device using pip.

        Args:
            package_name (str): Name of the runtime package (usually 'tflite-runtime', but might vary
                                e.g. on specific Python versions or custom builds).
            use_sudo (bool): Whether to prefix the pip command with 'sudo'.

        Returns:
            bool: True if the installation command executed with exit code 0, False otherwise.
        """
        logger.info(f"Attempting to install '{package_name}' on {self.host}...")
        if not PARAMIKO_AVAILABLE:
             logger.error("Install failed: Paramiko library not installed.")
             return False

        # Try pip3 first, then pip
        pip_cmds = [f"{self.remote_python} -m pip install {package_name}", f"pip3 install {package_name}", f"pip install {package_name}"]
        install_cmd = None
        # Check which pip command works
        for cmd_base in [f"{self.remote_python} -m pip", "pip3", "pip"]:
            status, _, _ = self._execute_remote_command(f"command -v {cmd_base}")
            if status == 0:
                 install_cmd = f"{cmd_base} install {package_name}"
                 break

        if not install_cmd:
             logger.error("Could not find suitable pip command (pip, pip3) on remote host.")
             self._disconnect()
             return False

        if use_sudo:
            install_cmd = f"sudo {install_cmd}"

        status, stdout, stderr = self._execute_remote_command(install_cmd)
        self._disconnect() # Close connection after command

        if status == 0:
            logger.info(f"'{package_name}' installation command executed successfully on {self.host}.")
            return True
        else:
            logger.error(f"Failed to install '{package_name}' on {self.host}. Exit Status: {status}\nStderr: {stderr}")
            return False

    def run_remote_inference_test(self, remote_model_path: str, remote_test_script_path: str, remote_input_data: Optional[str] = None) -> Optional[str]:
        """
        Runs a predefined inference test script on the remote device using the deployed model.

        Args:
            remote_model_path (str): Path to the .tflite model ON THE TARGET DEVICE.
            remote_test_script_path (str): Path to the Python inference script ON THE TARGET DEVICE.
                                           This script should take model/input paths as args and print results.
            remote_input_data (Optional[str]): Path to input data ON THE TARGET DEVICE, or simple string data
                                                to be passed as an argument (depends on the test script).

        Returns:
            Optional[str]: The standard output from the remote inference script if successful, else None.

        Note: Assumes a suitable Python environment and the 'tflite-runtime' are installed on the Pi,
              and that the `remote_test_script_path` exists and is executable.
        """
        logger.info(f"Running remote inference test using script: {remote_test_script_path}")
        if not PARAMIKO_AVAILABLE:
             logger.error("Remote test failed: Paramiko library not installed.")
             return None

        # Construct the command to run the script on the Raspberry Pi
        command = f"{self.remote_python} {remote_test_script_path} --model {remote_model_path}"
        if remote_input_data:
            # Pass input data path/string as argument (script needs to handle this)
            # Needs proper shell escaping if input data contains special chars
            command += f" --input \"{remote_input_data}\"" # Basic quoting

        status, stdout, stderr = self._execute_remote_command(command)
        self._disconnect() # Close connection

        if status == 0:
            logger.info("Remote inference test script executed successfully.")
            return stdout
        else:
            logger.error(f"Remote inference test script failed. Exit Status: {status}\nStderr: {stderr}")
            return None


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- TFLite Deployer Example (Conceptual) ---")

    # --- IMPORTANT ---
    # Replace with your actual Raspberry Pi connection details
    # For security, load these from environment variables or a secure config/secrets manager
    PI_HOST = os.environ.get("DEVIN_PI_HOST", "192.168.1.XX") # <<< REPLACE
    PI_USER = os.environ.get("DEVIN_PI_USER", "pi")
    # Use key-based auth if possible! Set ONE of these environment variables.
    PI_PASSWORD = os.environ.get("DEVIN_PI_PASSWORD") # <<< REPLACE/SET (Less Secure)
    PI_KEY_PATH = os.environ.get("DEVIN_PI_KEY_PATH") # <<< REPLACE/SET (More Secure)

    if PI_HOST == "192.168.1.XX":
         print("\nWARNING: Please set your Raspberry Pi's actual IP address in PI_HOST or environment variable.")
         # Exit if not configured? For now, allow to proceed but expect failure.
         # sys.exit(1)

    if not PI_PASSWORD and not PI_KEY_PATH:
         print("\nWARNING: Please set either DEVIN_PI_PASSWORD or DEVIN_PI_KEY_PATH environment variable for SSH authentication.")
         # sys.exit(1)

    # Assume a dummy .tflite file exists locally (created by edge_deploy.py conceptually)
    local_model = "./dummy_model_edge_v1.tflite"
    remote_model_dir = f"/home/{PI_USER}/devin_models"
    remote_model = f"{remote_model_dir}/deployed_model.tflite"
    remote_script = f"/home/{PI_USER}/devin_scripts/run_tflite_inference.py" # Assume this script exists on Pi

    # Create dummy local model file for example run
    if not os.path.exists(local_model):
        try:
            with open(local_model, "w") as f: f.write("dummy tflite binary data placeholder")
            print(f"Created dummy local model file: {local_model}")
        except IOError as e:
             print(f"Failed to create dummy model file: {e}")


    if PARAMIKO_AVAILABLE and (PI_PASSWORD or PI_KEY_PATH):
        deployer = TFLiteDeployer(
            host=PI_HOST,
            username=PI_USER,
            password=PI_PASSWORD, # Pass potentially None value
            key_filename=PI_KEY_PATH # Pass potentially None value
        )

        print("\nAttempting to install tflite-runtime on Pi (may require sudo)...")
        # Might need sudo depending on Pi's Python setup
        runtime_ok = deployer.install_tflite_runtime(use_sudo=True)
        print(f"Runtime installation command executed: {runtime_ok}")

        if os.path.exists(local_model):
            print("\nAttempting to deploy model to Pi...")
            deploy_ok = deployer.deploy_model(local_model, remote_model)
            print(f"Model deployment successful: {deploy_ok}")

            if deploy_ok:
                print("\nAttempting to run remote inference test...")
                # Assume remote_script takes an input image path for example
                # Need to ensure input data exists on Pi or transfer it first
                test_input = "/path/on/pi/to/test_image.jpg" # Example path on Pi
                inference_output = deployer.run_remote_inference_test(remote_model, remote_script, test_input)
                if inference_output is not None:
                    print("\nRemote Inference Script Output:")
                    print(inference_output)
                else:
                    print("\nRemote inference test failed or produced no output.")
        else:
            print("\nSkipping deployment/test as local model file doesn't exist.")

    else:
        print("\nSkipping example execution: Paramiko not installed or SSH credentials not configured.")


    # Cleanup dummy local file
    if os.path.exists(local_model): os.remove(local_model)

    print("\n--- End Example ---")
