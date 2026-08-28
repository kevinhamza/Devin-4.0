# Devin/security/sandbox/vm_sandbox.py
# Purpose: Provides a high-isolation sandbox by running tasks inside a
#          disposable VirtualBox virtual machine.

import logging
import subprocess
import shutil
from pathlib import Path
import time
from typing import List, Tuple, Optional
import uuid

# Configure basic logging
logger = logging.getLogger("VMSandbox")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class VMSandbox:
    """
    Manages the execution of tasks within an isolated VirtualBox VM.
    """
    def __init__(self, base_vm_name: str, snapshot_name: str, shared_folder_host: Path, guest_credentials: Tuple[str, str]):
        """
        Initializes the VM Sandbox controller.

        Args:
            base_vm_name: The name of the clean, template VirtualBox VM.
            snapshot_name: The name of the clean snapshot to clone from.
            shared_folder_host: The path on the HOST machine that is the shared folder.
            guest_credentials: A tuple of (username, password) for the GUEST OS.
        """
        self.base_vm_name = base_vm_name
        self.snapshot_name = snapshot_name
        self.shared_folder_host = Path(shared_folder_host)
        self.guest_user, self.guest_pass = guest_credentials
        
        if not shutil.which("VBoxManage"):
            raise FileNotFoundError("`VBoxManage` command not found. Is VirtualBox installed and in your system's PATH?")
        
        self.shared_folder_host.mkdir(exist_ok=True)

    def _run_command(self, args: List[str], timeout: int = 300) -> Tuple[bool, str]:
        """A wrapper for running VBoxManage commands."""
        command = ["VBoxManage"] + args
        logger.debug(f"Executing command: {' '.join(command)}")
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=True)
            return True, result.stdout
        except FileNotFoundError:
            logger.error("VBoxManage not found.")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(command)}")
            logger.error(f"Stderr: {e.stderr}")
            return False, e.stderr
        except subprocess.TimeoutExpired:
            logger.error("VBoxManage command timed out.")
            return False, "Command timed out."

    def run_script_in_vm(self, script_content: str, guest_script_path: str, guest_executable: str) -> Optional[str]:
        """
        Manages the full lifecycle of a disposable VM for running a script.

        Args:
            script_content: The content of the script to run.
            guest_script_path: The full path where the script will be inside the GUEST's shared folder.
            guest_executable: The executable to run the script inside the GUEST (e.g., "C:\\Python39\\python.exe" or "/usr/bin/python3").
        """
        clone_name = f"{self.base_vm_name}-clone-{uuid.uuid4().hex[:8]}"
        host_script_path = self.shared_folder_host / Path(guest_script_path).name
        
        logger.warning(f"--- Starting VM Sandbox Task for clone '{clone_name}' ---")
        
        try:
            # 1. Write the script to the host's shared folder
            host_script_path.write_text(script_content)
            
            # 2. Clone the VM from the clean snapshot
            logger.info(f"Cloning '{self.base_vm_name}' from snapshot '{self.snapshot_name}'...")
            success, _ = self._run_command(["clonevm", self.base_vm_name, "--snapshot", self.snapshot_name, "--name", clone_name, "--register"])
            if not success: return None

            # 3. Start the cloned VM
            logger.info(f"Starting VM '{clone_name}' in headless mode...")
            success, _ = self._run_command(["startvm", clone_name, "--type", "headless"])
            if not success: return None
            
            # 4. Wait for Guest Additions to be ready
            logger.info("Waiting for Guest OS and Additions to become responsive...")
            for i in range(20): # Wait up to 100 seconds
                time.sleep(5)
                success, out = self._run_command(["guestcontrol", clone_name, "run", "--exe", "cmd.exe" if "C:" in guest_executable else "/bin/echo", "--username", self.guest_user, "--password", self.guest_pass, "--", "/c", "echo", "ready"], timeout=10)
                if success:
                    logger.info("Guest OS is ready.")
                    break
            else:
                logger.error("Guest OS did not become responsive in time.")
                return None

            # 5. Execute the script
            logger.warning(f"Executing script inside the VM...")
            success, logs = self._run_command([
                "guestcontrol", clone_name, "run",
                "--exe", guest_executable,
                "--username", self.guest_user, "--password", self.guest_pass,
                "--", guest_script_path
            ])
            
            return logs

        finally:
            # 6. Cleanup: Power off and delete the clone
            logger.warning(f"--- Cleaning up clone '{clone_name}' ---")
            self._run_command(["controlvm", clone_name, "poweroff"], timeout=60)
            time.sleep(2) # Give time for poweroff to settle
            self._run_command(["unregistervm", clone_name, "--delete"], timeout=120)
            if host_script_path.exists():
                host_script_path.unlink()

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Virtual Machine Sandbox Prototype 🖥️📦 ===")
    print("=========================================================")
    print("!!! CRITICAL PREREQUISITES !!!")
    print("1. Oracle VirtualBox must be installed and `VBoxManage` must be in your PATH.")
    print("2. You must have a base VM with a clean snapshot.")
    print("3. Guest Additions MUST be installed in the guest OS.")
    print("4. A shared folder must be configured between the host and guest.")
    print("\nThis demo performs a 'dry run', printing the commands it would execute.")
    
    # --- USER-CONFIGURABLE PLACEHOLDERS ---
    # Replace these with your actual VM details to run a live test.
    BASE_VM_NAME = "Win10-Base"
    SNAPSHOT_NAME = "CleanInstall"
    # This path must exist on your host machine and be configured as a shared folder in the VM.
    SHARED_FOLDER_PATH = Path("./vbox_share")
    # Credentials for an account inside the GUEST OS.
    GUEST_CREDENTIALS = ("devin_user", "password123")
    # Path to the python executable INSIDE the GUEST OS.
    GUEST_PYTHON_PATH = "C:\\Python39\\python.exe"
    GUEST_SCRIPT_PATH = "C:\\Users\\devin_user\\Desktop\\main.py" # Assumes shared folder is mapped to Desktop
    
    print("\n--- Dry Run Configuration ---")
    print(f"  Base VM Name:       {BASE_VM_NAME}")
    print(f"  Snapshot Name:      {SNAPSHOT_NAME}")
    print(f"  Host Shared Folder: {SHARED_FOLDER_PATH.resolve()}")
    print("-----------------------------\n")

    print("The following is a sequence of `VBoxManage` commands that this module")
    print("would run to execute a script in a disposable VM clone.\n")
    
    clone_uuid = uuid.uuid4().hex[:8]
    clone_name = f"{BASE_VM_NAME}-clone-{clone_uuid}"

    print(f"1. Clone VM:\n   VBoxManage clonevm {BASE_VM_NAME} --snapshot {SNAPSHOT_NAME} --name {clone_name} --register\n")
    print(f"2. Start VM:\n   VBoxManage startvm {clone_name} --type headless\n")
    print("3. Wait for Guest Additions to be ready (polls with echo command)...\n")
    print(f"4. Execute Script:\n   VBoxManage guestcontrol {clone_name} run --exe {GUEST_PYTHON_PATH} --username {GUEST_CREDENTIALS[0]} --password **** -- {GUEST_SCRIPT_PATH}\n")
    print(f"5. Power Off VM:\n   VBoxManage controlvm {clone_name} poweroff\n")
    print(f"6. Delete VM:\n   VBoxManage unregistervm {clone_name} --delete\n")
    
    print("To perform a live run, configure the placeholders in this script and uncomment the following lines:")
    # try:
    #     sandbox = VMSandbox(BASE_VM_NAME, SNAPSHOT_NAME, SHARED_FOLDER_PATH, GUEST_CREDENTIALS)
    #     script = "import platform; print(f'Hello from a sandboxed VM! OS: {platform.system()} {platform.release()}')"
    #     output = sandbox.run_script_in_vm(script, GUEST_SCRIPT_PATH, GUEST_PYTHON_PATH)
    #     if output:
    #         print("\n--- LIVE RUN OUTPUT ---")
    #         print(output)
    # except Exception as e:
    #     logger.error(f"Live run failed. Please check your configuration. Error: {e}")

    print("\n=========================================================")
    print("=== VM Sandbox Prototype Complete ===")
    print("=========================================================")
