# # Devin/modules/os_operations/universal_operations.py
# # Purpose: Provides a single, cross-platform interface for OS operations,
# #          abstracting away the differences between Windows, Linux, and macOS.
# # Cross-platform OS operations 🌐

# import logging
# import sys
# import platform
# import time
# from typing import Optional, Any, Dict, List, Union

# # --- Important Libraries for a Real Implementation ---
# # This module would rely on the other modules in the compatibility_layer.
# #
# # from .compatibility_layer.win32_api import Win32APIWrapper
# # from .compatibility_layer.linux_syscalls import LinuxSyscallWrapper
# # from .compatibility_layer.macos_metal import MetalWrapper
# #
# # import numpy as np # For CPU fallback in accelerated_compute

# # Configure basic logging
# logger = logging.getLogger("UniversalOSOps")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)


# # --- Conceptual Placeholders for Imported Compatibility Modules ---
# class ConceptualWin32API:
#     def get_windows_version_ex_conceptual(self) -> Dict:
#         return {"ProductName": "Windows 11 Pro", "BuildNumber": 22631}
#     def query_service_status_conceptual(self, name: str) -> Dict:
#         return {"ServiceName": name, "Status": "SERVICE_RUNNING", "State": 4}

# class ConceptualLinuxSyscalls:
#     def uname_conceptual(self) -> Dict:
#         return {"sysname": "Linux", "release": "6.2.0-generic", "machine": "x86_64"}
#     def stat_file_conceptual(self, path: str) -> Dict:
#         return {"st_size": 1024, "st_mode": 33188} # mode for a regular file

# class ConceptualMetalWrapper:
#     def __init__(self):
#         self.device_found = True
#     def execute_kernel_conceptual(self, *args, **kwargs) -> bool:
#         logger.info("METAL: Executing conceptual GPU kernel...")
#         return True
# # --- End of Conceptual Placeholders ---


# class UniversalOSOperator:
#     """
#     Provides a high-level, cross-platform API for OS interactions.
#     It detects the current OS and uses the appropriate compatibility layer
#     module to perform the requested action.
#     """
#     def __init__(self):
#         self.os_type = platform.system().lower() # 'windows', 'linux', or 'darwin' for macOS
#         self.platform_api: Optional[Any] = None
#         self.gpu_accelerator: Optional[Any] = None
        
#         logger.info(f"UniversalOSOperator initialized. Detected OS: {self.os_type.capitalize()}")

#         # --- This is the core of the abstraction layer ---
#         # It instantiates the correct low-level wrapper based on the OS.
#         if self.os_type == "windows":
#             logger.info("Loading Windows compatibility layer (Win32API)...")
#             self.platform_api = ConceptualWin32API()
#         elif self.os_type == "linux":
#             logger.info("Loading Linux compatibility layer (Syscalls)...")
#             self.platform_api = ConceptualLinuxSyscalls()
#         elif self.os_type == "darwin": # macOS
#             logger.info("Loading POSIX compatibility layer for macOS (Linux Syscalls)...")
#             # macOS is POSIX-compliant, so it can use many of the same tools as Linux
#             self.platform_api = ConceptualLinuxSyscalls()
#             logger.info("Loading macOS GPU acceleration layer (Metal)...")
#             self.gpu_accelerator = ConceptualMetalWrapper()
#         else:
#             logger.error(f"Unsupported operating system: {self.os_type}. Limited functionality.")

#     def get_detailed_os_version(self) -> Dict[str, Any]:
#         """Gets detailed OS and kernel version information in a standardized format."""
#         logger.info("Requesting detailed OS version...")
#         if self.os_type == "windows" and self.platform_api:
#             raw_info = self.platform_api.get_windows_version_ex_conceptual()
#             return {"os": "Windows", "version": raw_info.get("ProductName"), "build": raw_info.get("BuildNumber")}
#         elif self.os_type in ["linux", "darwin"] and self.platform_api:
#             raw_info = self.platform_api.uname_conceptual()
#             return {"os": raw_info.get("sysname"), "kernel_release": raw_info.get("release"), "architecture": raw_info.get("machine")}
#         else:
#             # Fallback to standard library
#             return {"os": self.os_type, "version": platform.release()}

#     def check_service_status(self, service_name: str) -> Dict[str, Any]:
#         """
#         Checks the status of a system service (daemon on Linux).
#         This is primarily a Windows concept but can be mapped.
#         """
#         logger.info(f"Requesting status for service '{service_name}'...")
#         if self.os_type == "windows" and self.platform_api:
#             return self.platform_api.query_service_status_conceptual(service_name)
#         elif self.os_type in ["linux", "darwin"]:
#             # On Linux, you'd typically use `systemctl is-active <service_name>`
#             logger.info(f"CONCEPTUAL: Running 'systemctl is-active {service_name}'")
#             status = random.choice(["active", "inactive", "failed"])
#             return {"ServiceName": service_name, "Status": status.upper()}
#         else:
#             return {"error": "Unsupported OS for service status"}

#     def accelerated_compute_conceptual(self, data_array: Any, operation: str = "vector_add") -> Any:
#         """
#         Performs a computationally intensive task, using GPU acceleration if available.

#         Args:
#             data_array: A conceptual NumPy array of data.
#             operation (str): The name of the operation to perform.

#         Returns:
#             The result of the computation.
#         """
#         logger.info(f"Requesting accelerated compute for operation '{operation}'...")
        
#         # Use macOS Metal if available
#         if self.os_type == "darwin" and self.gpu_accelerator and self.gpu_accelerator.device_found:
#             logger.info("macOS Metal device found. Offloading computation to GPU...")
#             success = self.gpu_accelerator.execute_kernel_conceptual()
#             if success:
#                 return "<Result computed on Apple M-series GPU>"
        
#         # Fallback to CPU for other OSes or if Metal is not available
#         logger.info("GPU acceleration not available or not applicable. Falling back to CPU.")
#         # In a real system, you'd use a library like NumPy here.
#         # import numpy as np
#         # result = np.sum(data_array) # Example operation
#         logger.info("CONCEPTUAL NUMPY: Performing computation on CPU...")
#         time.sleep(0.2) # Simulate CPU work
#         return "<Result computed on CPU>"

#     def run_as_administrator_conceptual(self, command: str) -> bool:
#         """
#         Conceptually executes a command with elevated privileges.
#         """
#         logger.info(f"Requesting to run command with administrator privileges: '{command}'")
#         if self.os_type == "windows":
#             logger.info("CONCEPTUAL: Triggering UAC prompt for elevation...")
#             # This would involve using ShellExecuteEx with the 'runas' verb.
#         elif self.os_type in ["linux", "darwin"]:
#             logger.info(f"CONCEPTUAL: Prepending 'sudo' to command: 'sudo {command}'")
#             # This would require the user to have sudo privileges and potentially enter a password.
#         else:
#             logger.error("Privilege elevation not supported on this OS.")
#             return False
            
#         logger.info("  Conceptual command executed with elevated privileges.")
#         return True


# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Universal OS Operator Prototype 🌐 ===")
#     print("=========================================================")
    
#     # The operator automatically detects the OS it's running on.
#     operator = UniversalOSOperator()

#     print(f"\n--- Detected OS: {operator.os_type.upper()} ---")

#     # --- 1. Get Detailed OS Version (Platform-Specific) ---
#     print("\n--- Getting Detailed OS Information ---")
#     version_info = operator.get_detailed_os_version()
#     print("  Standardized OS Info:")
#     for key, value in version_info.items():
#         print(f"    - {key.replace('_', ' ').title()}: {value}")
        
#     # --- 2. Check Service Status (Platform-Specific) ---
#     print("\n\n--- Checking Service Status ---")
#     # Choose a service name appropriate for the detected OS
#     service_to_check = "wuauserv" if operator.os_type == 'windows' else 'cron'
#     service_status = operator.check_service_status(service_to_check)
#     print(f"  Conceptual status of '{service_to_check}':")
#     if "error" in service_status:
#         print(f"    {service_status['error']}")
#     else:
#         for key, value in service_status.items():
#             print(f"    - {key}: {value}")

#     # --- 3. Run Accelerated Compute (Platform-Specific) ---
#     print("\n\n--- Performing Accelerated Computation ---")
#     # This will demonstrate the GPU path on macOS and the CPU fallback on others.
#     conceptual_data = [1] * 1000000 # A large conceptual array
#     compute_result = operator.accelerated_compute_conceptual(conceptual_data)
#     print(f"  Result: {compute_result}")

#     # --- 4. Run Privileged Command (Platform-Specific) ---
#     print("\n\n--- Running a Command as Administrator ---")
#     command_to_run = "apt-get update" if operator.os_type == 'linux' else "ipconfig /flushdns"
#     privilege_success = operator.run_as_administrator_conceptual(command_to_run)
#     print(f"  Privileged command execution was conceptually successful: {privilege_success}")


#     print("\n=========================================================")
#     print("=== Universal Operator Prototype Complete ===")
#     print("=========================================================")




# # Devin/modules/os_operations/universal_operations.py
# # Purpose: Provides a single, cross-platform interface for OS operations,
# #          abstracting away OS differences by using the correct compatibility layer.

# import logging
# import platform
# import subprocess
# from typing import Optional, Any, Dict

# try:
#     # --- Import the REAL, integrated compatibility layer modules ---
#     from modules.os_operations.compatibility_layer.win32_api import Win32APIWrapper
#     from modules.os_operations.compatibility_layer.linux_syscalls import LinuxSyscallWrapper
#     from modules.os_operations.compatibility_layer.macos_metal import MetalWrapper
#     import numpy as np
#     DEVIN_CORE_AVAILABLE = True
# except ImportError as e:
#     DEVIN_CORE_AVAILABLE = False
#     _import_error = e

# # Configure basic logging
# logger = logging.getLogger("UniversalOSOps")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)


# class UniversalOSOperator:
#     """
#     Provides a high-level, cross-platform API for OS interactions by delegating
#     to the appropriate OS-specific compatibility layer.
#     """
#     def __init__(self):
#         if not DEVIN_CORE_AVAILABLE:
#             raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        
#         self.os_type = platform.system()
#         self.platform_api: Optional[Any] = None
#         self.gpu_accelerator: Optional[Any] = None
        
#         logger.info(f"UniversalOSOperator initialized. Detected OS: {self.os_type}")

#         # --- Strategy Pattern: Instantiate the correct low-level wrapper ---
#         if self.os_type == "Windows":
#             try:
#                 self.platform_api = Win32APIWrapper()
#             except (ImportError, RuntimeError) as e:
#                 logger.error(f"Failed to load Windows compatibility layer: {e}")
#         elif self.os_type == "Linux":
#             try:
#                 self.platform_api = LinuxSyscallWrapper()
#             except (ImportError, RuntimeError) as e:
#                 logger.error(f"Failed to load Linux compatibility layer: {e}")
#         elif self.os_type == "Darwin": # macOS
#             try:
#                 # macOS is POSIX-compliant, so many Linux tools work
#                 self.platform_api = LinuxSyscallWrapper()
#                 self.gpu_accelerator = MetalWrapper()
#             except (ImportError, RuntimeError) as e:
#                 logger.error(f"Failed to load macOS compatibility layer(s): {e}")
#         else:
#             logger.error(f"Unsupported operating system: {self.os_type}. Limited functionality.")

#     def get_detailed_os_version(self) -> Dict[str, Any]:
#         """Gets detailed OS and kernel version information in a standardized format."""
#         if self.os_type == "Windows" and self.platform_api:
#             # This is a conceptual method as win32api.GetVersionEx is deprecated
#             # We'll use the registry reader for a real, reliable result.
#             prod_name = self.platform_api.read_registry_key("HKEY_LOCAL_MACHINE", "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", "ProductName")
#             build = self.platform_api.read_registry_key("HKEY_LOCAL_MACHINE", "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", "CurrentBuild")
#             return {"os": "Windows", "product_name": prod_name, "build": build}
#         elif self.os_type in ["Linux", "Darwin"] and self.platform_api:
#             return self.platform_api.uname()
#         return {"os": self.os_type, "version": platform.release()}

#     def check_service_status(self, service_name: str) -> Dict[str, Any]:
#         """Checks the status of a system service or daemon."""
#         if self.os_type == "Windows" and self.platform_api:
#             return self.platform_api.query_service_status(service_name)
#         elif self.os_type == "Linux":
#             try:
#                 # Use systemctl for modern Linux distributions
#                 result = subprocess.run(['systemctl', 'is-active', service_name], capture_output=True, text=True)
#                 status = result.stdout.strip()
#                 return {"ServiceName": service_name, "Status": status.upper()}
#             except FileNotFoundError:
#                 return {"error": "systemctl not found. Cannot check service status."}
#         elif self.os_type == "Darwin":
#              try:
#                 # Use launchctl for macOS
#                 result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
#                 if service_name in result.stdout:
#                     return {"ServiceName": service_name, "Status": "LOADED"} # Simplified
#                 else:
#                     return {"ServiceName": service_name, "Status": "NOT_LOADED"}
#              except FileNotFoundError:
#                 return {"error": "launchctl not found. Cannot check service status."}
#         return {"error": "Unsupported OS for service status"}

#     def accelerated_vector_add(self, vec_a: np.ndarray, vec_b: np.ndarray) -> Optional[np.ndarray]:
#         """Performs vector addition, using GPU acceleration if available."""
#         if self.os_type == "Darwin" and self.gpu_accelerator:
#             logger.info("macOS Metal device found. Offloading vector addition to GPU...")
#             try:
#                 pipeline = self.gpu_accelerator.compile_shader(self.gpu_accelerator.VECTOR_ADD_SHADER, "vector_add")
#                 buffer_a = self.gpu_accelerator.device.newBufferWithBytes_length_options_(vec_a, vec_a.nbytes, 0)
#                 buffer_b = self.gpu_accelerator.device.newBufferWithBytes_length_options_(vec_b, vec_b.nbytes, 0)
#                 result_buffer = self.gpu_accelerator.device.newBufferWithLength_options_(vec_a.nbytes, 0)
                
#                 self.gpu_accelerator.execute_kernel(pipeline, [buffer_a, buffer_b, result_buffer], (len(vec_a), 1, 1))
#                 return self.gpu_accelerator.read_numpy_from_buffer(result_buffer, vec_a.dtype)
#             except Exception as e:
#                 logger.error(f"Metal execution failed, falling back to CPU. Error: {e}")
        
#         logger.info("GPU acceleration not available. Performing vector addition on CPU with NumPy.")
#         return np.add(vec_a, vec_b)


# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Integrated Universal OS Operator 🌐 ===")
#     print("=========================================================")
    
#     if not DEVIN_CORE_AVAILABLE:
#         print(f"\nERROR: A core Devin module is missing. Error: {_import_error}")
#     else:
#         operator = UniversalOSOperator()
#         print(f"\n--- Detected OS: {operator.os_type} ---")

#         # --- 1. Get Detailed OS Version ---
#         print("\n--- 1. Getting Detailed OS Information ---")
#         version_info = operator.get_detailed_os_version()
#         print("  Live OS Info:")
#         for key, value in version_info.items():
#             print(f"    - {key.replace('_', ' ').title()}: {value}")
            
#         # --- 2. Check a common service/daemon status ---
#         print("\n\n--- 2. Checking a Common Service Status ---")
#         service_to_check = "wuauserv" if operator.os_type == 'Windows' else 'cron' if operator.os_type == 'Linux' else 'com.apple.WindowServer'
#         service_status = operator.check_service_status(service_to_check)
#         print(f"  Live status of '{service_to_check}':")
#         for key, value in service_status.items():
#             print(f"    - {key}: {value}")

#         # --- 3. Run Accelerated Compute ---
#         print("\n\n--- 3. Performing Accelerated Vector Addition ---")
#         # Create two large NumPy arrays
#         data_size = 1000000
#         vector1 = np.random.rand(data_size).astype(np.float32)
#         vector2 = np.random.rand(data_size).astype(np.float32)
        
#         result_vector = operator.accelerated_vector_add(vector1, vector2)
        
#         if result_vector is not None:
#             # Verify the result is correct by comparing with a pure CPU operation
#             expected_result = np.add(vector1, vector2)
#             if np.allclose(result_vector, expected_result):
#                 print("  [SUCCESS] The computation result is correct.")
#                 print(f"  Result vector (first 5 elements): {result_vector[:5]}")
#             else:
#                 print("  [FAILURE] The computation result is incorrect.")
#         else:
#             print("  [FAILURE] The computation failed to produce a result.")

#     print("\n=========================================================")
#     print("=== Universal Operator Demo Complete ===")
#     print("=========================================================")
    
# Devin/modules/os_operations/universal_operations.py
# Purpose: A universal, cross-platform interface for common OS operations.

import logging
import platform
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np

# --- Platform-Specific Compatibility Layers ---
# These are the real, functional low-level wrappers for each OS.
# We fall back to inert stub classes if the compatibility layer can't be
# imported (e.g. on a minimal install), so the operator still constructs.
try:
    from .compatibility_layer.win32_api import Win32APIWrapper
    from .compatibility_layer.linux_syscalls import LinuxSyscallWrapper
    from .compatibility_layer.macos_metal import MetalWrapper
except ImportError:
    class Win32APIWrapper: pass
    class LinuxSyscallWrapper: pass
    class MetalWrapper: pass

# Configure basic logging
logger = logging.getLogger("UniversalOSOps")
# (Logger setup omitted for brevity)

class UniversalOSOperator:
    """
    Provides a single, consistent API for OS interactions across platforms.
    """
    def __init__(self):
        self.os_type = platform.system()
        self.platform_api = None
        self.gpu_accelerator = None
        logger.info(f"UniversalOSOperator initialized. Detected OS: {self.os_type}")
        self._load_compatibility_layers()

    def _load_compatibility_layers(self):
        """Loads the appropriate low-level modules for the detected OS."""
        if self.os_type == "Windows":
            try:
                self.platform_api = Win32APIWrapper()
            except Exception as e:
                logger.error(f"Failed to load Windows compatibility layer: {e}")
        elif self.os_type == "Linux":
            self.platform_api = LinuxSyscallWrapper()
        elif self.os_type == "Darwin": # macOS
            self.platform_api = LinuxSyscallWrapper() # For POSIX compatibility
            self.gpu_accelerator = MetalWrapper()

    def get_detailed_os_version(self) -> Dict[str, Any]:
        """
        Gets detailed OS and kernel version information in a standardized format,
        dispatching to the correct platform-specific compatibility layer.
        """
        logger.info("Requesting detailed OS version...")
        if self.os_type == "Windows" and self.platform_api:
            prod_name = self.platform_api.read_registry_key(
                "HKEY_LOCAL_MACHINE",
                "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
                "ProductName",
            )
            build = self.platform_api.read_registry_key(
                "HKEY_LOCAL_MACHINE",
                "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
                "CurrentBuild",
            )
            return {"os": "Windows", "product_name": prod_name, "build": build}
        elif self.os_type in ["Linux", "Darwin"] and self.platform_api:
            raw_info = self.platform_api.uname()
            if raw_info:
                return {
                    "os": raw_info.get("sysname"),
                    "kernel_release": raw_info.get("release"),
                    "architecture": raw_info.get("machine"),
                }
            return {"os": self.os_type, "version": platform.release()}
        else:
            return {"os": self.os_type, "version": platform.release()}

    def accelerated_vector_add(self, vec_a: "np.ndarray", vec_b: "np.ndarray") -> Optional["np.ndarray"]:
        """
        Performs vector addition, using macOS Metal GPU acceleration when
        available, and falling back to a NumPy CPU implementation otherwise.
        """
        if self.os_type == "Darwin" and self.gpu_accelerator:
            logger.info("macOS Metal device found. Offloading vector addition to GPU...")
            try:
                pipeline = self.gpu_accelerator.compile_shader(
                    self.gpu_accelerator.VECTOR_ADD_SHADER, "vector_add"
                )
                buffer_a = self.gpu_accelerator.device.newBufferWithBytes_length_options_(
                    vec_a, vec_a.nbytes, 0
                )
                buffer_b = self.gpu_accelerator.device.newBufferWithBytes_length_options_(
                    vec_b, vec_b.nbytes, 0
                )
                result_buffer = self.gpu_accelerator.device.newBufferWithLength_options_(
                    vec_a.nbytes, 0
                )

                self.gpu_accelerator.execute_kernel(
                    pipeline, [buffer_a, buffer_b, result_buffer], (len(vec_a), 1, 1)
                )
                return self.gpu_accelerator.read_numpy_from_buffer(result_buffer, vec_a.dtype)
            except Exception as e:
                logger.error(f"Metal execution failed, falling back to CPU. Error: {e}")

        logger.info("GPU acceleration not available. Performing vector addition on CPU with NumPy.")
        return np.add(vec_a, vec_b)

    # --- NEW METHOD TO FIX THE CRASH ---
    def list_directory(self, path: str) -> Dict[str, List[Dict]]:
        """
        Lists the contents of a directory in a structured format.
        """
        try:
            p = Path(path)
            if not p.is_dir():
                return {"error": f"Path '{path}' is not a valid directory."}
            
            contents = {"files": [], "directories": []}
            for item in p.iterdir():
                item_info = {"name": item.name, "path": str(item.resolve())}
                if item.is_dir():
                    contents["directories"].append(item_info)
                else:
                    item_info["size_bytes"] = item.stat().st_size
                    contents["files"].append(item_info)
            return contents
        except FileNotFoundError:
            return {"error": f"Directory not found: '{path}'"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}

    def read_file(self, path: str) -> Dict[str, str]:
        """Reads the content of a text file."""
        try:
            content = Path(path).read_text(encoding='utf-8')
            return {"status": "success", "content": content}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def write_file(self, path: str, content: str) -> Dict[str, str]:
        """Writes content to a text file."""
        try:
            Path(path).write_text(content, encoding='utf-8')
            return {"status": "success", "message": f"Successfully wrote to {path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Add other high-level OS methods here...
