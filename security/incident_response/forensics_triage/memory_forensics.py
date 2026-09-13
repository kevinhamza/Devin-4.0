# Devin/security/incident_response/forensics_triage/memory_forensics.py
# Purpose: A wrapper for the Volatility 3 Framework to automate the analysis
#          of memory images for digital forensics and incident response.

import logging
import subprocess
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any

# Configure basic logging
logger = logging.getLogger("MemoryForensics")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class MemoryForensics:
    """
    A programmatic interface to the Volatility 3 Framework.
    """
    def __init__(self, volatility_path: Path, memory_image_path: Path):
        """
        Initializes the Memory Forensics tool.

        Args:
            volatility_path: The path to the 'vol.py' executable of Volatility 3.
            memory_image_path: The path to the memory image file to be analyzed.
        """
        self.vol_py_path = volatility_path
        self.mem_image_path = memory_image_path
        
        if not self.vol_py_path.is_file():
            raise FileNotFoundError(f"Volatility executable not found at: {self.vol_py_path}")
        if not self.mem_image_path.is_file():
            raise FileNotFoundError(f"Memory image file not found at: {self.mem_image_path}")
        
        logger.info("MemoryForensics tool initialized.")

    def _run_volatility_plugin(self, plugin: str, extra_args: Optional[List[str]] = None) -> Optional[List[Dict[str, Any]]]:
        """
        A generic method to run a Volatility 3 plugin and parse its JSON output.
        """
        output_dir = Path("./volatility_output")
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir()

        command = [
            "python", str(self.vol_py_path),
            "-f", str(self.mem_image_path),
            "--output-dir", str(output_dir),
            plugin
        ]
        if extra_args:
            command.extend(extra_args)
            
        logger.warning(f"Running Volatility plugin: {plugin}...")
        try:
            # Volatility prints its progress to stderr, so we capture stdout for JSON path
            result = subprocess.run(command, capture_output=True, text=True, timeout=600, check=True)
            
            # Volatility 3's JSON renderer creates a file from the plugin name
            json_file_name = plugin.replace('.', '_') + ".json"
            json_output_path = output_dir / json_file_name

            if not json_output_path.is_file():
                logger.error(f"Volatility ran but did not produce the expected JSON output file: {json_output_path}")
                return None
            
            with open(json_output_path, 'r') as f:
                data = json.load(f)

            # The actual data is a list of dictionaries under the 'values' key of each treegrid row
            parsed_data = []
            for row in data['treegrid']['rows']:
                parsed_data.append(row['values'])

            return parsed_data

        except subprocess.CalledProcessError as e:
            logger.error(f"Volatility plugin '{plugin}' failed.")
            logger.error(f"Stderr: {e.stderr}")
            return None
        except FileNotFoundError:
            logger.error("'python' command not found. Is Python installed and in your PATH?")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None
        finally:
            if output_dir.exists():
                shutil.rmtree(output_dir)

    def list_processes(self) -> Optional[List[Dict]]:
        """Runs the windows.pslist plugin to list running processes."""
        return self._run_volatility_plugin("windows.pslist.PsList")

    def list_network_connections(self) -> Optional[List[Dict]]:
        """Runs the windows.netscan plugin to find network artifacts."""
        return self._run_volatility_plugin("windows.netscan.NetScan")

    def extract_command_history(self) -> Optional[List[Dict]]:
        """Runs the windows.cmdline plugin to show process command line arguments."""
        return self._run_volatility_plugin("windows.cmdline.CmdLine")

    def scan_for_malware_injection(self) -> Optional[List[Dict]]:
        """Runs the windows.malfind plugin to find suspicious process memory regions."""
        return self._run_volatility_plugin("windows.malfind.Malfind")


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Memory Forensics (Volatility) Prototype 🧠🔬 ===")
    print("=========================================================")
    print("!!! CRITICAL PREREQUISITES !!!")
    print("1. You must download the Volatility 3 framework from: https://github.com/volatilityfoundation/volatility3")
    print("2. You must have a memory image file to analyze. A safe sample can be found at the Volatility sample page.")
    
    # --- USER-CONFIGURABLE PLACEHOLDERS ---
    # Replace these with the actual paths on your system to run a live test.
    VOLATILITY_PATH = Path("./volatility3/vol.py")
    MEMORY_IMAGE_PATH = Path("./memdump.raw")
    
    print("\nThis demo performs a 'dry run', printing the commands it would execute")
    print("if the above paths were correctly configured.\n")
    
    print("--- Dry Run Configuration ---")
    print(f"  Volatility Path:   {VOLATILITY_PATH.resolve()}")
    print(f"  Memory Image Path: {MEMORY_IMAGE_PATH.resolve()}")
    print("-----------------------------\n")

    # This is a "dry run" showing the commands that would be executed.
    # To perform a live run, ensure the paths above are correct and uncomment
    # the code block below.
    
    print("Example commands that this module would run:\n")
    print(f"1. To list processes:\n   python {VOLATILITY_PATH} -f {MEMORY_IMAGE_PATH} windows.pslist.PsList\n")
    print(f"2. To list network connections:\n   python {VOLATILITY_PATH} -f {MEMORY_IMAGE_PATH} windows.netscan.NetScan\n")
    print(f"3. To scan for malware:\n   python {VOLATILITY_PATH} -f {MEMORY_IMAGE_PATH} windows.malfind.Malfind\n")
    
    # --- LIVE RUN BLOCK (Commented out by default) ---
    # if VOLATILITY_PATH.exists() and MEMORY_IMAGE_PATH.exists():
    #     logger.warning("--- STARTING LIVE RUN ---")
    #     try:
    #         forensics = MemoryForensics(VOLATILITY_PATH, MEMORY_IMAGE_PATH)
    #         
    #         # Get and print process list
    #         processes = forensics.list_processes()
    #         if processes:
    #             print(f"\n--- Found {len(processes)} Processes (Top 5) ---")
    #             for p in processes[:5]:
    #                 print(f"  - PID: {p.get('PID', 'N/A')}, PPID: {p.get('PPID', 'N/A')}, Name: {p.get('ImageFileName', 'N/A')}")
    #
    #         # Get and print network connections
    #         net_connections = forensics.list_network_connections()
    #         if net_connections:
    #             print(f"\n--- Found {len(net_connections)} Network Connections (Top 5) ---")
    #             for conn in net_connections[:5]:
    #                 print(f"  - Proto: {conn.get('Proto', 'N/A')}, Local: {conn.get('LocalAddr')}:{conn.get('LocalPort')}, "
    #                       f"Remote: {conn.get('ForeignAddr')}:{conn.get('ForeignPort')}, State: {conn.get('State', 'N/A')}")
    #     except Exception as e:
    #         logger.error(f"Live run failed: {e}")
    # else:
    #     logger.error("Live run skipped. Please configure VOLATILITY_PATH and MEMORY_IMAGE_PATH.")
    
    print("\n=========================================================")
    print("=== Memory Forensics Prototype Complete ===")
    print("=========================================================")
