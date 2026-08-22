# # Devin/modules/os_operations/windows_operations.py
# # Purpose: Provides a toolbox of high-level utilities for performing
# #          Windows-specific administrative and operational tasks.
# # Windows-specific utilities 🪟🔧

# import logging
# import subprocess
# import json
# import random
# from typing import Optional, Any, Dict, List

# # --- Important Libraries for a Real Implementation ---
# # This module would rely on the pywin32, wmi, and other libraries.
# #
# # import wmi
# # import win32evtlog
# # import win32com.client
# # from .compatibility_layer.win32_api import Win32APIWrapper

# # Configure basic logging
# logger = logging.getLogger("WindowsOperations")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# # --- Conceptual Placeholders for Imported Modules ---
# class ConceptualWin32API:
#     """Represents the low-level Win32 API wrapper."""
#     def __init__(self):
#         logger.info("ConceptualWin32API for WindowsUtils initialized.")
# # --- End of Conceptual Placeholders ---

# class WindowsUtils:
#     """
#     Provides a suite of high-level tools for Windows administration, building
#     upon the low-level Win32 API wrapper.
#     """
#     def __init__(self, win32_api_wrapper: Optional[Any] = None):
#         """
#         Initializes the Windows utilities.

#         Args:
#             win32_api_wrapper: An instance of the low-level Win32APIWrapper.
#         """
#         self.win32_api = win32_api_wrapper or ConceptualWin32API()
#         # In a real system: self.wmi_client = wmi.WMI()
#         self.wmi_client_conceptual = "<Conceptual WMI Client>"
#         logger.info("WindowsUtils initialized.")

#     def execute_powershell_conceptual(self, script_block: str) -> Dict[str, Any]:
#         """
#         Conceptually executes a PowerShell script block and captures its output.
#         PowerShell is powerful because its output can be structured (JSON).

#         Returns:
#             A dictionary with stdout, stderr, and a list of deserialized objects.
#         """
#         # We append | ConvertTo-Json to get structured data back.
#         command = ["powershell.exe", "-Command", f"& {{ {script_block} }} | ConvertTo-Json"]
#         logger.info(f"CONCEPTUAL POWERSHELL: Executing script block: '{script_block}'")
        
#         # In a real system, you'd use subprocess.run()
#         # For simulation, we'll craft a plausible response.
#         if "Get-Process" in script_block:
#             stdout_json = json.dumps([
#                 {"ProcessName": "powershell", "Id": 1234},
#                 {"ProcessName": "chrome", "Id": 5678},
#             ])
#             return {"stdout": stdout_json, "stderr": "", "objects": json.loads(stdout_json), "exit_code": 0}
#         elif "Get-Service" in script_block:
#              stdout_json = json.dumps({"Name": "wuauserv", "Status": "Running"})
#              return {"stdout": stdout_json, "stderr": "", "objects": json.loads(stdout_json), "exit_code": 0}
#         else:
#             return {"stdout": "", "stderr": "Command not recognized in simulation.", "objects": [], "exit_code": 1}

#     def query_wmi_conceptual(self, wmi_query: str) -> List[Dict[str, Any]]:
#         """
#         Conceptually executes a WMI query to get detailed system information.
#         Example query: "SELECT * FROM Win32_OperatingSystem"

#         Returns:
#             A list of dictionaries, where each dictionary represents a WMI object.
#         """
#         logger.info(f"CONCEPTUAL WMI: Executing query: '{wmi_query}'")
#         # In a real system: self.wmi_client.query(wmi_query)
        
#         if "Win32_BIOS" in wmi_query:
#             return [{"Manufacturer": "Dell Inc.", "SerialNumber": "ABC123XYZ", "Version": "1.10.0"}]
#         elif "Win32_DiskDrive" in wmi_query:
#             return [{"Model": "Samsung SSD 970 EVO Plus", "Size": "1000202273280", "Partitions": 2}]
#         else:
#             logger.warning("  WMI query not recognized in simulation.")
#             return []

#     def read_event_log_conceptual(self, log_name: str, event_type_filter: str = "Error", count: int = 10) -> List[Dict[str, Any]]:
#         """
#         Conceptually reads recent events from a Windows Event Log.

#         Args:
#             log_name (str): The name of the log to read (e.g., 'System', 'Application').
#             event_type_filter (str): Filter for event types like 'Error', 'Warning'.
#         """
#         logger.info(f"CONCEPTUAL EVTLOG: Reading last {count} '{event_type_filter}' events from the '{log_name}' log.")
#         # Real-world implementation is complex, involving win32evtlog handles and looping.
        
#         events = []
#         for i in range(random.randint(0, count)):
#             events.append({
#                 "RecordNumber": 12345 + i,
#                 "TimeGenerated": "2025-06-11T10:30:00",
#                 "SourceName": "Service Control Manager" if log_name == "System" else "Application Error",
#                 "EventType": event_type_filter.upper(),
#                 "EventID": 7034 if log_name == "System" else 1000,
#                 "Data": "The XY Service terminated unexpectedly."
#             })
#         return events

#     def add_firewall_rule_conceptual(self, rule_name: str, port: int, protocol: str = "TCP", action: str = "Allow", direction: str = "Inbound") -> bool:
#         """
#         Conceptually adds a new rule to the Windows Defender Firewall.
#         """
#         logger.info(f"CONCEPTUAL FIREWALL: Adding new {direction} rule '{rule_name}' for {protocol} port {port} (Action: {action}).")
#         # This can be done with PowerShell ('New-NetFirewallRule') or by interacting with COM objects.
#         ps_command = f"New-NetFirewallRule -DisplayName '{rule_name}' -Direction {direction} -Action {action} -Protocol {protocol} -LocalPort {port}"
#         logger.info(f"  Underlying PowerShell command (conceptual): {ps_command}")
#         return True


# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Windows Operations Utilities Prototype 🪟🔧 ===")
#     print("=========================================================")
    
#     win_utils = WindowsUtils()

#     # --- 1. PowerShell Integration Demo ---
#     print("\n--- Executing a PowerShell command to get processes ---")
#     ps_result = win_utils.execute_powershell_conceptual("Get-Process -Name 'chrome', 'powershell'")
#     if ps_result["exit_code"] == 0:
#         print("  PowerShell execution successful. Parsed objects:")
#         for process_obj in ps_result["objects"]:
#             print(f"    - Process: {process_obj.get('ProcessName')}, PID: {process_obj.get('Id')}")
#     else:
#         print(f"  PowerShell execution failed: {ps_result['stderr']}")
    
#     # --- 2. WMI Query Demo ---
#     print("\n\n--- Querying WMI for BIOS information ---")
#     wmi_bios_info = win_utils.query_wmi_conceptual("SELECT * FROM Win32_BIOS")
#     if wmi_bios_info:
#         print("  WMI query successful. BIOS info:")
#         for key, value in wmi_bios_info[0].items():
#             print(f"    - {key}: {value}")
#     else:
#         print("  WMI query failed to return data.")

#     # --- 3. Event Log Reading Demo ---
#     print("\n\n--- Reading 'Error' events from the 'System' Event Log ---")
#     error_events = win_utils.read_event_log_conceptual("System", event_type_filter="Error", count=5)
#     if error_events:
#         print(f"  Found {len(error_events)} conceptual error events. Showing first one:")
#         first_event = error_events[0]
#         for key, value in first_event.items():
#             print(f"    - {key}: {value}")
#     else:
#         print("  No conceptual error events found.")
        
#     # --- 4. Firewall Management Demo ---
#     print("\n\n--- Adding a conceptual Firewall Rule ---")
#     rule_added = win_utils.add_firewall_rule_conceptual(
#         rule_name="Allow Devin Web Server",
#         port=8080,
#         protocol="TCP",
#         action="Allow",
#         direction="Inbound"
#     )
#     print(f"  Firewall rule 'Allow Devin Web Server' was conceptually added: {rule_added}")
    

#     print("\n=========================================================")
#     print("=== Windows Utilities Prototype Complete ===")
#     print("=========================================================")





# Devin/modules/os_operations/windows_operations.py
# Purpose: A functional, high-level toolbox for performing Windows-specific
#          administrative and operational tasks using PowerShell and Win32 APIs.

import logging
import subprocess
import json
import platform
from typing import Optional, Any, Dict, List

try:
    from modules.os_operations.compatibility_layer.win32_api import Win32APIWrapper
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# --- Platform-specific check ---
IS_WINDOWS = platform.system() == "Windows"

# Configure basic logging
logger = logging.getLogger("WindowsOperations")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class WindowsUtils:
    """
    Provides a suite of high-level tools for Windows administration, primarily
    by leveraging PowerShell for its structured data output.
    """
    def __init__(self):
        if not IS_WINDOWS:
            logger.warning("Not running on Windows. WindowsUtils will be non-functional.")
            return
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        
        self.win32_api = Win32APIWrapper()
        logger.info("WindowsUtils initialized with live bindings.")

    def execute_powershell(self, script_block: str, as_json: bool = True) -> Dict[str, Any]:
        """
        Executes a PowerShell script block and captures its output.

        Args:
            script_block (str): The PowerShell commands to execute.
            as_json (bool): If True, appends '| ConvertTo-Json' to get structured output.

        Returns:
            A dictionary with stdout, stderr, exit_code, and parsed 'objects' if as_json is True.
        """
        if not IS_WINDOWS:
            return {"stdout": "", "stderr": "Not on Windows", "objects": [], "exit_code": -1}

        command_to_run = script_block
        if as_json:
            # -Depth 5 is a good default for complex objects
            command_to_run = f"& {{ {script_block} }} | ConvertTo-Json -Compress -Depth 5"

        try:
            # Using -NoProfile and -ExecutionPolicy Bypass for better script compatibility
            process = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command_to_run],
                capture_output=True,
                text=True,
                check=False # We check the returncode manually
            )
            
            objects = None
            if as_json and process.stdout and process.returncode == 0:
                try:
                    objects = json.loads(process.stdout)
                except json.JSONDecodeError:
                    logger.warning(f"PowerShell output was not valid JSON, returning raw stdout.")

            return {
                "stdout": process.stdout,
                "stderr": process.stderr,
                "objects": objects,
                "exit_code": process.returncode
            }
        except FileNotFoundError:
            return {"stdout": "", "stderr": "powershell.exe not found in PATH.", "objects": [], "exit_code": -1}
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "objects": [], "exit_code": -1}

    def query_wmi(self, wmi_query: str) -> Optional[List[Dict[str, Any]]]:
        """Executes a WMI query and returns the structured result."""
        ps_command = f"Get-WmiObject -Query \"{wmi_query}\""
        result = self.execute_powershell(ps_command)
        
        if result["exit_code"] == 0 and result["objects"] is not None:
            # If a single object is returned, PowerShell's JSON conversion doesn't wrap it in a list
            return result["objects"] if isinstance(result["objects"], list) else [result["objects"]]
        logger.error(f"WMI query failed. Stderr: {result['stderr']}")
        return None

    def read_event_log(self, log_name: str, count: int = 10, level: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Reads recent events from a Windows Event Log."""
        ps_command = f"Get-WinEvent -LogName '{log_name}' -MaxEvents {count}"
        if level:
            # Levels: 1=Critical, 2=Error, 3=Warning, 4=Information, 5=Verbose
            level_map = {"critical": 1, "error": 2, "warning": 3, "information": 4}
            level_num = level_map.get(level.lower())
            if level_num:
                ps_command += f" | Where-Object {{ $_.Level -eq {level_num} }}"

        # Select specific properties for a clean output
        ps_command += " | Select-Object TimeCreated, Id, LevelDisplayName, Message"
        result = self.execute_powershell(ps_command)
        
        if result["exit_code"] == 0 and result["objects"] is not None:
            return result["objects"] if isinstance(result["objects"], list) else [result["objects"]]
        logger.error(f"Reading event log failed. Stderr: {result['stderr']}")
        return None

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Windows Operations Utilities 🪟🔧 ===")
    print("=========================================================")

    if not IS_WINDOWS:
        print("This demo is only functional on a Windows operating system.")
    else:
        try:
            win_utils = WindowsUtils()

            # --- 1. PowerShell Integration Demo ---
            print("\n--- 1. Executing PowerShell to get top 3 CPU-intensive processes ---")
            ps_script = "Get-Process | Sort-Object CPU -Descending | Select-Object -First 3 ProcessName, Id, CPU"
            ps_result = win_utils.execute_powershell(ps_script)
            if ps_result["exit_code"] == 0 and ps_result["objects"]:
                print("  PowerShell execution successful. Parsed objects:")
                for process_obj in ps_result["objects"]:
                    print(f"    - Process: {process_obj.get('ProcessName')}, PID: {process_obj.get('Id')}, CPU: {process_obj.get('CPU')}")
            else:
                print(f"  PowerShell execution failed: {ps_result['stderr']}")

            # --- 2. WMI Query Demo ---
            print("\n\n--- 2. Querying WMI for Operating System information ---")
            wmi_os_info = win_utils.query_wmi("SELECT Caption, Version, OSArchitecture, NumberOfUsers FROM Win32_OperatingSystem")
            if wmi_os_info:
                print("  WMI query successful. OS info:")
                for key, value in wmi_os_info[0].items():
                    # WMI often returns properties with PSComputerName etc., we can filter them
                    if not key.startswith("PS"):
                        print(f"    - {key}: {value}")
            else:
                print("  WMI query failed to return data.")

            # --- 3. Event Log Reading Demo ---
            print("\n\n--- 3. Reading last 5 'Error' events from the 'Application' Log ---")
            error_events = win_utils.read_event_log("Application", count=5, level="Error")
            if error_events:
                print(f"  Found {len(error_events)} 'Error' events. Showing first one:")
                first_event = error_events[0]
                # The message can be very long, so we truncate it
                message = first_event.get("Message", "")
                message_short = (message[:150] + '...') if len(message) > 150 else message
                print(f"    - Time: {first_event.get('TimeCreated')}")
                print(f"    - ID: {first_event.get('Id')}")
                print(f"    - Message: {message_short.replace(chr(10), ' ')}") # remove newlines for display
            else:
                print("  No recent 'Error' events found in the 'Application' log.")

        except (ImportError, RuntimeError, ConnectionError) as e:
            print(f"\nAn error occurred during initialization: {e}")
            print("Please ensure you are on Windows and have run 'pip install pywin32'.")

    print("\n=========================================================")
    print("=== Windows Utilities Demo Complete ===")
    print("=========================================================")
