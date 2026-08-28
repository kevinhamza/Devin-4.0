# # Devin/modules/os_operations/linux_operations.py
# # Purpose: Provides a toolbox of high-level utilities for performing
# #          Linux-specific administrative and operational tasks.
# # Linux-specific utilities 🐧🔧

# import logging
# import subprocess
# import shlex
# import json
# import random
# from typing import Optional, Any, Dict, List, Literal

# # --- Important Libraries for a Real Implementation ---
# # This module heavily relies on running shell commands.
# # The 'subprocess' module is essential.
# #
# # from .compatibility_layer.linux_syscalls import LinuxSyscallWrapper

# # Configure basic logging
# logger = logging.getLogger("LinuxOperations")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# # --- Conceptual Placeholders for Imported Modules ---
# class ConceptualLinuxSyscalls:
#     """Represents the low-level Linux syscalls wrapper."""
#     def __init__(self):
#         logger.info("ConceptualLinuxSyscalls for LinuxUtils initialized.")
# # --- End of Conceptual Placeholders ---


# class LinuxUtils:
#     """
#     Provides a suite of high-level tools for Linux administration,
#     primarily by wrapping common command-line utilities.
#     """
#     def __init__(self, syscall_wrapper: Optional[Any] = None):
#         """
#         Initializes the Linux utilities.

#         Args:
#             syscall_wrapper: An instance of the low-level LinuxSyscallWrapper.
#         """
#         self.syscalls = syscall_wrapper or ConceptualLinuxSyscalls()
#         self.package_manager = self._detect_package_manager_conceptual()
#         logger.info(f"LinuxUtils initialized. Detected conceptual package manager: {self.package_manager}")

#     def _run_shell_command_conceptual(self, command: str, use_sudo: bool = False) -> Dict[str, Any]:
#         """Conceptually runs a shell command and captures the output."""
#         if use_sudo:
#             command = "sudo " + command
        
#         logger.info(f"CONCEPTUAL SHELL: Executing: `{command}`")
#         # In a real system:
#         # result = subprocess.run(shlex.split(command), capture_output=True, text=True)
#         # return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
        
#         # Simulate output
#         if "apt-get update" in command:
#             return {"stdout": "All packages are up to date.", "stderr": "", "exit_code": 0}
#         if "apt-get install" in command:
#             return {"stdout": "nginx is already the newest version.", "stderr": "", "exit_code": 0}
#         if "systemctl status" in command:
#             return {"stdout": "Active: active (running)", "stderr": "", "exit_code": 0}
#         if "ufw allow" in command:
#              return {"stdout": "Rule added", "stderr": "", "exit_code": 0}
        
#         return {"stdout": "Command executed successfully.", "stderr": "", "exit_code": 0}


#     def _detect_package_manager_conceptual(self) -> Literal['apt', 'yum', 'dnf', 'unknown']:
#         """Conceptually detects the system's package manager."""
#         logger.info("Detecting Linux distribution and package manager...")
#         # A real system would check for the existence of /etc/os-release and command binaries.
#         return random.choice(['apt', 'yum'])

#     # --- Package Management ---
#     def update_package_list(self) -> bool:
#         """Conceptually updates the list of available packages."""
#         logger.info("Requesting package list update...")
#         if self.package_manager == 'apt':
#             result = self._run_shell_command_conceptual("apt-get update", use_sudo=True)
#         elif self.package_manager in ['yum', 'dnf']:
#             result = self._run_shell_command_conceptual(f"{self.package_manager} check-update", use_sudo=True)
#         else:
#             logger.error("Unsupported package manager.")
#             return False
#         return result["exit_code"] == 0

#     def install_package(self, package_name: str) -> bool:
#         """Conceptually installs a software package."""
#         logger.info(f"Requesting installation of package '{package_name}'...")
#         if self.package_manager == 'apt':
#             result = self._run_shell_command_conceptual(f"apt-get install -y {package_name}", use_sudo=True)
#         elif self.package_manager in ['yum', 'dnf']:
#             result = self._run_shell_command_conceptual(f"{self.package_manager} install -y {package_name}", use_sudo=True)
#         else:
#             logger.error("Unsupported package manager.")
#             return False
        
#         logger.info(f"  Package '{package_name}' conceptually installed.")
#         return result["exit_code"] == 0

#     # --- Service Management (systemd) ---
#     def manage_service_conceptual(self, service_name: str, action: Literal['start', 'stop', 'enable', 'disable', 'status']) -> Dict[str, Any]:
#         """Conceptually manages a systemd service."""
#         logger.info(f"Requesting to '{action}' service '{service_name}'...")
#         result = self._run_shell_command_conceptual(f"systemctl {action} {service_name}", use_sudo=(action != 'status'))
#         logger.info(f"  Service '{service_name}' action '{action}' completed.")
#         return result

#     # --- Firewall Management ---
#     def add_firewall_rule_conceptual(self, rule: str) -> bool:
#         """
#         Conceptually adds a firewall rule using UFW (Uncomplicated Firewall).
        
#         Args:
#             rule (str): The UFW rule string (e.g., 'allow 80/tcp', 'allow from 1.2.3.4 to any port 22').
#         """
#         logger.info(f"Requesting to add firewall rule: '{rule}'")
#         result = self._run_shell_command_conceptual(f"ufw {rule}", use_sudo=True)
#         return result["exit_code"] == 0

#     # --- Log Management ---
#     def query_journalctl_conceptual(self, service_unit: str, lines: int = 20) -> List[str]:
#         """
#         Conceptually queries the systemd journal for logs from a specific service.
#         """
#         logger.info(f"Requesting last {lines} log lines for service '{service_unit}' from journalctl.")
#         # The -o json flag is great for machine-readable output.
#         cmd = f"journalctl -u {service_unit}.service -n {lines} --no-pager -o json"
#         result = self._run_shell_command_conceptual(cmd)
        
#         # Simulate JSON output from journalctl
#         log_entries = []
#         if result["exit_code"] == 0:
#             for i in range(lines):
#                 log_entry = {
#                     "__REALTIME_TIMESTAMP": str(int(time.time() * 1e6)),
#                     "_HOSTNAME": "devin-linux-box",
#                     "_SYSTEMD_UNIT": f"{service_unit}.service",
#                     "MESSAGE": f"Conceptual log message {i+1} for {service_unit}."
#                 }
#                 log_entries.append(json.dumps(log_entry))
#             return log_entries
#         return []


# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Linux Operations Utilities Prototype 🐧🔧 ===")
#     print("=========================================================")
    
#     linux_utils = LinuxUtils()

#     # --- 1. Package Management Demo ---
#     print("\n--- Running a conceptual package management workflow ---")
#     print("  Step 1: Updating package lists...")
#     linux_utils.update_package_list()
    
#     print("\n  Step 2: Installing 'nginx'...")
#     linux_utils.install_package("nginx")

#     # --- 2. Service Management Demo ---
#     print("\n\n--- Running a conceptual service management workflow for 'nginx' ---")
#     service = "nginx"
#     print(f"  Step 1: Enabling '{service}' to start on boot...")
#     linux_utils.manage_service_conceptual(service, "enable")
    
#     print(f"\n  Step 2: Starting '{service}'...")
#     linux_utils.manage_service_conceptual(service, "start")

#     print(f"\n  Step 3: Checking status of '{service}'...")
#     status_result = linux_utils.manage_service_conceptual(service, "status")
#     print(f"    -> Status Output: {status_result['stdout']}")

#     # --- 3. Firewall Management Demo ---
#     print("\n\n--- Adding a conceptual firewall rule for the web server ---")
#     rule = "allow 'Nginx Full'" # UFW has application profiles
#     rule_added = linux_utils.add_firewall_rule_conceptual(rule)
#     print(f"  Firewall rule '{rule}' was conceptually added: {rule_added}")
    
#     # --- 4. Log Querying Demo ---
#     print("\n\n--- Querying recent logs for the 'nginx' service ---")
#     nginx_logs = linux_utils.query_journalctl_conceptual("nginx", lines=3)
#     if nginx_logs:
#         print(f"  Found {len(nginx_logs)} conceptual log entries. Showing first one:")
#         # Parse the conceptual JSON log entry
#         first_log = json.loads(nginx_logs[0])
#         print(f"    - Host: {first_log['_HOSTNAME']}")
#         print(f"    - Message: {first_log['MESSAGE']}")
#     else:
#         print("  No conceptual logs found.")
    

#     print("\n=========================================================")
#     print("=== Linux Utilities Prototype Complete ===")
#     print("=========================================================")



# Devin/modules/os_operations/linux_operations.py
# Purpose: A functional, high-level toolbox for performing Linux-specific
#          administrative and operational tasks by wrapping shell commands.

import logging
import subprocess
import shlex
import json
import platform
from typing import Optional, Any, Dict, List, Literal

# --- Platform-specific check ---
IS_LINUX = platform.system() == "Linux"

# Configure basic logging
logger = logging.getLogger("LinuxOperations")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class LinuxUtils:
    """
    Provides a suite of high-level tools for Linux administration,
    primarily by wrapping common command-line utilities.
    """
    def __init__(self):
        if not IS_LINUX:
            logger.warning("Not running on Linux. LinuxUtils will be non-functional.")
            self.package_manager = 'unknown'
            return
        
        self.package_manager = self._detect_package_manager()
        logger.info(f"LinuxUtils initialized. Detected package manager: {self.package_manager}")

    def _run_shell_command(self, command: str, use_sudo: bool = False) -> Dict[str, Any]:
        """Runs a shell command and captures the output."""
        if not IS_LINUX:
            return {"stdout": "", "stderr": "Not on Linux", "exit_code": -1}
            
        if use_sudo:
            command = "sudo " + command
        
        logger.info(f"Executing: `{command}`")
        try:
            # Use shlex.split for security
            args = shlex.split(command)
            process = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=False # We handle the exit code manually
            )
            return {
                "stdout": process.stdout,
                "stderr": process.stderr,
                "exit_code": process.returncode
            }
        except Exception as e:
            logger.error(f"Failed to execute command '{command}': {e}")
            return {"stdout": "", "stderr": str(e), "exit_code": -1}

    def _detect_package_manager(self) -> Literal['apt', 'yum', 'dnf', 'unknown']:
        """Detects the system's primary package manager."""
        if shutil.which("apt"):
            return "apt"
        elif shutil.which("dnf"):
            return "dnf"
        elif shutil.which("yum"):
            return "yum"
        return "unknown"

    def install_package(self, package_name: str) -> bool:
        """Installs a software package."""
        logger.info(f"Requesting installation of package '{package_name}'...")
        if self.package_manager == 'apt':
            # Use -qq for quieter output, DEBIAN_FRONTEND to prevent interactive prompts
            cmd = f"DEBIAN_FRONTEND=noninteractive apt-get install -y -qq {package_name}"
            result = self._run_shell_command(cmd, use_sudo=True)
        elif self.package_manager in ['yum', 'dnf']:
            cmd = f"{self.package_manager} install -y {package_name}"
            result = self._run_shell_command(cmd, use_sudo=True)
        else:
            logger.error("Unsupported package manager.")
            return False
        
        if result["exit_code"] != 0:
            logger.error(f"Failed to install '{package_name}'. Stderr: {result['stderr']}")
            return False
        
        logger.info(f"Package '{package_name}' installed successfully.")
        return True

    def manage_service(self, service_name: str, action: Literal['start', 'stop', 'enable', 'disable', 'status']) -> Dict[str, Any]:
        """Manages a systemd service."""
        result = self._run_shell_command(f"systemctl {action} {service_name}", use_sudo=(action != 'status'))
        if result["exit_code"] != 0:
             logger.warning(f"Command 'systemctl {action} {service_name}' may have failed. Stderr: {result['stderr']}")
        return result

    def query_journalctl(self, service_unit: str, lines: int = 20) -> Optional[List[Dict]]:
        """Queries the systemd journal for logs and parses the JSON output."""
        cmd = f"journalctl -u {service_unit}.service -n {lines} --no-pager -o json"
        result = self._run_shell_command(cmd)
        
        if result["exit_code"] != 0:
            logger.error(f"journalctl query failed. Stderr: {result['stderr']}")
            return None
            
        # journalctl -o json outputs one JSON object per line
        log_entries = []
        for line in result["stdout"].strip().split('\n'):
            if line:
                try:
                    log_entries.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse journalctl JSON line: {line}")
        return log_entries

# --- Example Usage ---
if __name__ == "__main__":
    import shutil

    print("=========================================================")
    print("=== Integrated Linux Operations Utilities 🐧🔧 ===")
    print("=========================================================")
    
    if not IS_LINUX:
        print("This demo is only functional on a Linux operating system.")
    else:
        linux_utils = LinuxUtils()
        
        # --- 1. System Information ---
        print("\n--- 1. Detecting System Package Manager ---")
        print(f"  Detected Package Manager: {linux_utils.package_manager.upper()}")

        # --- 2. Service Management Demo ---
        print("\n\n--- 2. Checking Status of 'cron' (or 'crond') Service ---")
        # Cron service name can vary between distros
        cron_service_name = "cron" if shutil.which("cron") else "crond"
        status_result = linux_utils.manage_service(cron_service_name, "status")
        print(f"  Live status of '{cron_service_name}':")
        # Print a snippet of the status output
        status_output = status_result['stdout'].strip().split('\n')
        for line in status_output[:3]: # Print first 3 lines
            print(f"    {line}")
        if len(status_output) > 3: print("    ...")

        # --- 3. Log Querying Demo ---
        print(f"\n\n--- 3. Querying last 5 log entries for '{cron_service_name}' ---")
        cron_logs = linux_utils.query_journalctl(cron_service_name, lines=5)
        if cron_logs:
            print(f"  Found {len(cron_logs)} log entries. Showing latest one:")
            latest_log = cron_logs[-1]
            # Convert timestamp to human-readable
            ts = datetime.fromtimestamp(int(latest_log.get('__REALTIME_TIMESTAMP', 0)) / 1e6)
            print(f"    - Timestamp: {ts.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    - Hostname:  {latest_log.get('_HOSTNAME')}")
            print(f"    - Message:   {latest_log.get('MESSAGE')}")
        else:
            print("  No recent logs found for the service or journalctl failed.")

        # --- 4. Package Management Demo (informational, no actual install) ---
        print("\n\n--- 4. Demonstrating Package Management Command ---")
        package_to_install = "htop"
        print(f"  To install '{package_to_install}', this module would run the following command:")
        if linux_utils.package_manager == 'apt':
            print(f"    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq {package_to_install}")
        elif linux_utils.package_manager in ['yum', 'dnf']:
            print(f"    sudo {linux_utils.package_manager} install -y {package_to_install}")
        else:
            print("    No supported package manager found for this demonstration.")

    print("\n=========================================================")
    print("=== Linux Utilities Demo Complete ===")
    print("=========================================================")
