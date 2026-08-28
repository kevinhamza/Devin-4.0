# Devin/security/incident_response/forensics_triage/disk_forensics.py
# Purpose: A wrapper for The Sleuth Kit (TSK) to automate the forensic
#          analysis of disk images.

import logging
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any

# Configure basic logging
logger = logging.getLogger("DiskForensics")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class DiskForensics:
    """
    A programmatic interface to The Sleuth Kit (TSK) command-line tools.
    """
    def __init__(self, disk_image_path: Path):
        """
        Initializes the Disk Forensics tool.

        Args:
            disk_image_path: The path to the disk image file to be analyzed.
        """
        self.disk_image_path = disk_image_path
        
        # Check for TSK tools
        self.tsk_tools = {"mmls", "fls", "icat", "istat"}
        for tool in self.tsk_tools:
            if not shutil.which(tool):
                raise FileNotFoundError(f"TSK tool '{tool}' not found. Is The Sleuth Kit installed and in your system's PATH?")

        if not self.disk_image_path.is_file():
            raise FileNotFoundError(f"Disk image file not found at: {self.disk_image_path}")
        
        logger.info("DiskForensics tool initialized.")

    def _run_tsk_command(self, command: List[str]) -> Tuple[bool, str, str]:
        """A generic wrapper for running TSK commands."""
        logger.debug(f"Executing command: {' '.join(command)}")
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"Command failed with exit code {result.returncode}: {' '.join(command)}")
                logger.error(f"Stderr: {result.stderr}")
                return False, "", result.stderr
            return True, result.stdout, result.stderr
        except FileNotFoundError:
            logger.error(f"Command '{command[0]}' not found.")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return False, "", str(e)

    def list_partitions(self) -> Optional[List[Dict[str, Any]]]:
        """Runs `mmls` to list partitions in the disk image."""
        logger.info(f"Listing partitions for '{self.disk_image_path.name}'...")
        success, stdout, _ = self._run_tsk_command(["mmls", str(self.disk_image_path)])
        
        if not success:
            return None
        
        partitions = []
        lines = stdout.strip().split('\n')
        header_line_index = -1
        for i, line in enumerate(lines):
            if line.startswith("Slot"):
                header_line_index = i
                break
        
        if header_line_index == -1: return []

        for line in lines[header_line_index + 2:]: # Skip header and separator
            parts = line.split(maxsplit=4)
            if len(parts) >= 4:
                partitions.append({
                    "slot": parts[0],
                    "start_sector": int(parts[1]),
                    "end_sector": int(parts[2]),
                    "length_sectors": int(parts[3]),
                    "description": parts[4].strip() if len(parts) > 4 else ""
                })
        return partitions

    def list_files(self, partition_offset: int, recursive: bool = False) -> Optional[List[Dict[str, Any]]]:
        """Runs `fls` to list files in a given partition."""
        logger.info(f"Listing files from partition starting at sector {partition_offset}...")
        command = ["fls", "-o", str(partition_offset)]
        if recursive:
            command.append("-r")
        command.append(str(self.disk_image_path))
        
        success, stdout, _ = self._run_tsk_command(command)
        if not success: return None
        
        files = []
        for line in stdout.strip().split('\n'):
            parts = line.split('|')
            if len(parts) == 2:
                metadata, filename = parts
                meta_parts = metadata.split()
                # r/r * 2-1: file.txt
                # d/d * 3: folder
                file_type, _, inode = meta_parts[0].split()
                inode = inode.rstrip(':')
                files.append({
                    "type": file_type,
                    "inode": inode,
                    "name": filename
                })
        return files

    def recover_file(self, partition_offset: int, inode: str, output_path: Path) -> bool:
        """Runs `icat` to recover a file by its inode."""
        logger.info(f"Recovering file with inode {inode} to '{output_path}'...")
        command = ["icat", "-o", str(partition_offset), str(self.disk_image_path), inode]
        try:
            with open(output_path, "wb") as f_out:
                result = subprocess.run(command, stdout=f_out, stderr=subprocess.PIPE, check=True)
            logger.info("File recovered successfully.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to recover file with inode {inode}.")
            logger.error(f"Stderr: {e.stderr.decode()}")
            return False

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Disk Forensics (The Sleuth Kit) Prototype 💾🕵️ ===")
    print("=========================================================")
    print("!!! CRITICAL PREREQUISITES !!!")
    print("1. You must install The Sleuth Kit from: https://www.sleuthkit.org/")
    print("2. The TSK tools (mmls, fls, icat) must be in your system's PATH.")
    print("3. You must have a disk image file to analyze.")
    
    # --- USER-CONFIGURABLE PLACEHOLDERS ---
    # Replace with the actual path to your disk image to run a live test.
    # A safe sample can be found in many CTF challenges, e.g., the 4n6-ir.com samples page.
    DISK_IMAGE_PATH = Path("./sample_disk.dd")
    
    print("\nThis demo performs a 'dry run', printing the commands it would execute.")
    print("To perform a live run, configure the DISK_IMAGE_PATH above.\n")

    print("--- Dry Run Configuration ---")
    print(f"  Disk Image Path: {DISK_IMAGE_PATH.resolve()}")
    print("-----------------------------\n")

    print("Example commands that this module would run:\n")
    print(f"1. To list partitions:\n   mmls {DISK_IMAGE_PATH}\n")
    print(f"2. To list files in a partition (e.g., at offset 2048):\n   fls -o 2048 {DISK_IMAGE_PATH}\n")
    print(f"3. To recover a file (e.g., with inode 15) from that partition:\n   icat -o 2048 {DISK_IMAGE_PATH} 15 > recovered_file.dat\n")
    
    # --- LIVE RUN BLOCK (Commented out by default) ---
    # if all(shutil.which(tool) for tool in ["mmls", "fls", "icat"]) and DISK_IMAGE_PATH.exists():
    #     logger.warning("--- STARTING LIVE RUN ---")
    #     try:
    #         forensics = DiskForensics(DISK_IMAGE_PATH)
    #         
    #         # 1. Get partitions
    #         partitions = forensics.list_partitions()
    #         if partitions:
    #             print(f"\n--- Found {len(partitions)} Partitions ---")
    #             for p in partitions:
    #                 print(f"  - Slot: {p['slot']}, Start: {p['start_sector']}, Size: {p['length_sectors']}, Desc: {p['description']}")
    #             
    #             # 2. List files from the first usable partition
    #             # This assumes the first non-empty partition is the one of interest
    #             first_partition_offset = next((p['start_sector'] for p in partitions if 'fs' in p['description'].lower()), None)
    #             if first_partition_offset:
    #                 files = forensics.list_files(first_partition_offset)
    #                 if files:
    #                     print(f"\n--- Found {len(files)} files/dirs in partition at offset {first_partition_offset} (Top 10) ---")
    #                     for f in files[:10]:
    #                         # Look for a deleted file to recover
    #                         if '*' in f['inode']:
    #                             print(f"  - [DELETED] {f['name']} (inode: {f['inode']})")
    #                         else:
    #                             print(f"  - {f['name']} (inode: {f['inode']})")
    #     except Exception as e:
    #         logger.error(f"Live run failed: {e}")
    # else:
    #     logger.error("Live run skipped. Please configure DISK_IMAGE_PATH and ensure TSK is in your PATH.")

    print("\n=========================================================")
    print("=== Disk Forensics Prototype Complete ===")
    print("=========================================================")
