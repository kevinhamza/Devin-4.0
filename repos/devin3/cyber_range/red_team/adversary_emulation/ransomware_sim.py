# Devin/cyber_range/red_team/adversary_emulation/ransomware_sim.py
# Purpose: Simulates ransomware behavior patterns FOR TESTING DEFENSES ONLY.
# WARNING: DOES NOT PERFORM REAL ENCRYPTION. Actions are simulated safely.

import os
import glob
import time
import random
import uuid
import logging
import datetime
import json
from typing import Dict, List, Optional, Tuple

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("RansomwareSimulator")

# --- Configuration ---
# These should ideally be loaded from a scenario configuration
DEFAULT_TARGET_DIRS = ["./simulated_victim_files/documents", "./simulated_victim_files/pictures"] # SAFE TEST DIRECTORIES ONLY
DEFAULT_FILE_EXTENSIONS = ["*.txt", "*.docx", "*.jpg", "*.png", "*.pdf", "*.xls"] # Files to target
DEFAULT_EXCLUSION_DIRS = ["/windows", "/program files", "/program files (x86)", "/appdata", "/library", "/system", "/private/var", "/usr/bin"] # Critical dirs to avoid even searching
DEFAULT_EXCLUSION_FILES = ["desktop.ini", "thumbs.db", ".ds_store"]
SIMULATED_ENCRYPTED_EXTENSION = ".devin_encrypted_sim" # Extension added to simulated files
RANSOM_NOTE_FILENAME = "!!!_HOW_TO_DECRYPT_FILES_!!!.txt"
RANSOM_NOTE_TEMPLATE = """
===============================================================
WARNING: YOUR FILES HAVE BEEN SIMULATED AS ENCRYPTED by Devin Ransomware Defense Test!
===============================================================

This is a *simulation* run as part of a security test within the Devin Cyber Range.
Your actual files have NOT been encrypted with cryptographic algorithms.
Files targeted by this simulation have been renamed to end with '{encrypted_ext}'.

Simulation Details:
-------------------
Victim ID: {victim_id}
Simulation Start Time: {start_time}
Number of Files Targeted: {file_count}

Purpose:
--------
This simulation tests detection and response capabilities for ransomware-like behavior, including:
- File discovery patterns.
- Mass file renaming/modification activity (simulated).
- Creation of ransom notes.
- Simulated Command & Control (C2) communication attempts (logged only).

Recovery (Simulation Only):
---------------------------
To reverse the *simulated* changes (rename files back), use the cleanup function
associated with this simulation run or manually rename files by removing the
'{encrypted_ext}' extension.

*** If this were a real attack, your files would be inaccessible without a decryption key. ***

Contact Info (for Simulation/Test):
----------------------------------
Cyber Range Admin: security-admin@devin.example.com
Simulation ID: {simulation_id}

===============================================================
"""
SIMULATED_C2_URL = "http://dummy-c2-server.example.local/checkin" # Placeholder URL

class RansomwareSimulator:
    """
    Simulates the common stages of a ransomware attack for defense testing.

    *** DOES NOT PERFORM REAL ENCRYPTION. Uses safe renaming/placeholders. ***
    Focuses on file discovery, simulated modification, C2 check-in logging,
    and ransom note dropping patterns.
    """

    def __init__(self,
                 target_dirs: List[str] = DEFAULT_TARGET_DIRS,
                 target_extensions: List[str] = DEFAULT_FILE_EXTENSIONS,
                 exclusion_dirs: List[str] = DEFAULT_EXCLUSION_DIRS,
                 exclusion_files: List[str] = DEFAULT_EXCLUSION_FILES,
                 c2_url: str = SIMULATED_C2_URL,
                 encrypted_ext: str = SIMULATED_ENCRYPTED_EXTENSION,
                 note_filename: str = RANSOM_NOTE_FILENAME,
                 note_template: str = RANSOM_NOTE_TEMPLATE
                 ):
        self.target_dirs = [os.path.abspath(d) for d in target_dirs] # Use absolute paths
        self.target_extensions = target_extensions
        # Normalize exclusion paths for comparison
        self.exclusion_dirs = [os.path.abspath(d).lower() for d in exclusion_dirs]
        self.exclusion_files = [f.lower() for f in exclusion_files]
        self.c2_url = c2_url
        self.encrypted_ext = encrypted_ext
        self.note_filename = note_filename
        self.note_template = note_template
        self.victim_id = f"VICTIM-{uuid.uuid4().hex[:12].upper()}"
        self.simulation_id = f"SIM-{uuid.uuid4().hex[:8]}"
        self.processed_files: List[Tuple[str, str]] = [] # Store (original_path, renamed_path) for cleanup
        logger.info(f"RansomwareSimulator initialized (ID: {self.simulation_id}, Victim: {self.victim_id}). Targeting: {self.target_dirs}")
        logger.warning("*** SIMULATION ONLY - NO REAL ENCRYPTION WILL OCCUR ***")

    def _is_safe_to_target(self, file_path: str) -> bool:
        """Checks if a file path is safe to target (not in critical system dirs)."""
        abs_path = os.path.abspath(file_path).lower()
        if os.path.basename(abs_path).lower() in self.exclusion_files:
            return False
        for excluded_dir in self.exclusion_dirs:
            # Check if the file path starts with any of the excluded directories
            # Handle potential trailing slashes for robustness
            if abs_path.startswith(os.path.join(excluded_dir, '').lower()):
                logger.debug(f"Skipping excluded path: {file_path} (Matches: {excluded_dir})")
                return False
        return True

    def discover_files(self) -> List[str]:
        """Finds files matching target extensions in target directories, respecting exclusions."""
        logger.info("Starting file discovery phase...")
        discovered_files = []
        for target_dir in self.target_dirs:
            if not os.path.isdir(target_dir):
                 logger.warning(f"Target directory not found or not a directory: {target_dir}")
                 continue
            logger.info(f"  - Searching in: {target_dir}")
            for extension in self.target_extensions:
                # Use recursive globbing (**) - Requires Python 3.5+
                # Need to handle potential permission errors accessing directories
                try:
                    pattern = os.path.join(target_dir, "**", extension)
                    for file_path in glob.glob(pattern, recursive=True):
                        if os.path.isfile(file_path): # Ensure it's a file
                            if self._is_safe_to_target(file_path):
                                discovered_files.append(file_path)
                            # else: logger.debug(f"Skipping excluded file: {file_path}") # Can be verbose
                except OSError as e:
                     logger.warning(f"    - OS error while searching {target_dir} (permissions?): {e}")
                except Exception as e:
                     logger.error(f"    - Unexpected error searching {target_dir}: {e}")

        # Remove duplicates if somehow found via different patterns/paths
        discovered_files = sorted(list(set(discovered_files)))
        logger.info(f"File discovery complete. Found {len(discovered_files)} potential target files.")
        return discovered_files

    def _simulate_encryption(self, file_path: str) -> bool:
        """
        SIMULATES encryption by renaming the file. DOES NOT ENCRYPT.
        Optionally creates a placeholder marker file.
        """
        if not os.path.isfile(file_path): return False # File gone?
        renamed_path = file_path + self.encrypted_ext
        logger.info(f"  - Simulating encryption for: '{os.path.basename(file_path)}' -> '{os.path.basename(renamed_path)}'")
        try:
            # --- Action: Rename file ---
            os.rename(file_path, renamed_path)
            # --- Action: Create marker file (optional) ---
            # marker_file = file_path + ".encrypted_marker.txt"
            # with open(marker_file, "w") as f: f.write(f"Simulated encryption by {self.simulation_id}")
            self.processed_files.append((file_path, renamed_path)) # Log for cleanup
            return True
        except OSError as e:
            logger.error(f"    - Error simulating encryption (renaming) for '{file_path}': {e}")
            return False
        except Exception as e:
            logger.error(f"    - Unexpected error simulating encryption for '{file_path}': {e}")
            return False


    def _simulate_c2_checkin(self) -> bool:
        """Simulates contacting a Command & Control server. DOES NOT send real network traffic."""
        logger.info("Simulating C2 check-in...")
        # --- Placeholder: No Network Call ---
        # In a real attack, would send victim ID, system info, encryption key etc.
        checkin_data = {
            "victim_id": self.victim_id,
            "sim_id": self.simulation_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": "discovery_complete", # Example status update
            "hostname": os.uname().nodename if hasattr(os, 'uname') else 'unknown_host' # Example system info
        }
        logger.info(f"  - Conceptual Check-in Data: {checkin_data}")
        logger.info(f"  - Conceptual Target C2 URL: {self.c2_url}")
        logger.info(f"  - *** No actual network request sent. ***")
        # Simulate success/failure randomly or based on config
        success = random.choice([True, True, False]) # Simulate occasional failure
        logger.info(f"  - Simulated C2 Check-in Result: {'Success' if success else 'Failed'}")
        # --- End Placeholder ---
        return success


    def _drop_ransom_note(self, target_dir: str, file_count: int):
        """Creates the ransom note file in the specified directory."""
        note_path = os.path.join(target_dir, self.note_filename)
        logger.info(f"Dropping ransom note simulation in: '{target_dir}'")
        try:
            content = self.note_template.format(
                victim_id=self.victim_id,
                start_time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                file_count=file_count,
                encrypted_ext=self.encrypted_ext,
                simulation_id=self.simulation_id
            )
            with open(note_path, "w") as f:
                f.write(content)
            logger.info(f"  - Ransom note simulation file created: '{note_path}'")
        except IOError as e:
            logger.error(f"  - Failed to write ransom note to '{note_path}': {e}")
        except Exception as e:
            logger.error(f"  - Unexpected error writing ransom note: {e}")


    def run_simulation(self, max_files_to_process: Optional[int] = None, delay_ms: int = 10):
        """
        Executes the ransomware simulation stages.

        Args:
            max_files_to_process (Optional[int]): Limit the number of files to simulate encrypting.
                                                Defaults to all discovered files.
            delay_ms (int): Milliseconds to wait between simulating encryption of each file,
                            to mimic real-world pacing and potentially evade rate-based detection.
        """
        logger.warning(f"--- Starting Ransomware Simulation (ID: {self.simulation_id}) ---")
        start_time = datetime.datetime.now(datetime.timezone.utc)
        self.processed_files = [] # Reset for this run

        # 1. Initial C2 Check-in (Simulated)
        self._simulate_c2_checkin()

        # 2. File Discovery
        target_files = self.discover_files()
        if not target_files:
             logger.warning("Simulation ended: No target files found matching criteria.")
             return

        files_to_process = target_files
        if max_files_to_process is not None and max_files_to_process < len(target_files):
            logger.info(f"Limiting simulation to {max_files_to_process} files out of {len(target_files)} found.")
            files_to_process = random.sample(target_files, max_files_to_process) # Process a random subset

        # 3. Simulate Encryption Loop
        logger.info(f"Starting simulated encryption phase for {len(files_to_process)} files...")
        processed_count = 0
        failed_count = 0
        for file_path in files_to_process:
            if self._simulate_encryption(file_path):
                processed_count += 1
            else:
                failed_count += 1
            # Simulate attacker pacing / throttle
            if delay_ms > 0:
                 time.sleep(delay_ms / 1000.0)

        logger.info(f"Simulated encryption phase complete. Processed: {processed_count}, Failed: {failed_count}")

        # 4. Drop Ransom Notes
        # Drop in root of each target directory searched
        logger.info("Dropping ransom note simulations...")
        unique_base_dirs = set(os.path.dirname(p[0]) for p in self.processed_files) # Dirs where files were actually 'encrypted'
        for target_dir in self.target_dirs: # Also ensure note is in originally targeted dirs
             unique_base_dirs.add(target_dir)
        for note_dir in unique_base_dirs:
             # Check if dir still exists and is writable before dropping note
             if os.path.isdir(note_dir):
                  self._drop_ransom_note(note_dir, processed_count)
             else:
                  logger.warning(f"Skipping ransom note in '{note_dir}', directory no longer exists.")

        # 5. Final C2 Check-in (Simulated)
        logger.info("Simulating final C2 notification...")
        # In real attack, might exfiltrate keys or report success
        self._simulate_c2_checkin() # Re-use checkin simulation

        end_time = datetime.datetime.now(datetime.timezone.utc)
        duration = end_time - start_time
        logger.warning(f"--- Ransomware Simulation (ID: {self.simulation_id}) Finished ---")
        logger.warning(f"Duration: {duration}")
        logger.warning(f"Files Targeted/Renamed: {processed_count}")
        logger.warning("*** REMINDER: This was a simulation. No real encryption occurred. ***")


    def cleanup_simulation(self):
        """Reverses the simulated encryption (renames files back) and removes notes."""
        logger.warning(f"--- Cleaning Up Ransomware Simulation (ID: {self.simulation_id}) ---")
        renamed_count = 0
        rename_errors = 0
        note_removed_count = 0
        note_error_count = 0

        # Rename files back
        logger.info(f"Attempting to rename {len(self.processed_files)} files back to original names...")
        for original_path, renamed_path in reversed(self.processed_files): # Reverse order often safer
             if os.path.exists(renamed_path):
                 try:
                     os.rename(renamed_path, original_path)
                     renamed_count += 1
                 except OSError as e:
                     logger.error(f"  - Error renaming '{renamed_path}' back to '{original_path}': {e}")
                     rename_errors += 1
             else:
                 # Original file might already exist if rename failed or partially reverted?
                 if not os.path.exists(original_path):
                      logger.warning(f"  - Renamed file '{renamed_path}' not found, cannot revert.")
                      rename_errors += 1 # Count as error as state is inconsistent


        # Remove ransom notes (search target dirs)
        logger.info(f"Attempting to remove ransom notes ('{self.note_filename}')...")
        affected_dirs = set(os.path.dirname(p[0]) for p in self.processed_files)
        for target_dir in self.target_dirs: affected_dirs.add(target_dir) # Ensure check in original targets too

        for note_dir in affected_dirs:
             note_path = os.path.join(note_dir, self.note_filename)
             if os.path.exists(note_path):
                 try:
                     os.remove(note_path)
                     note_removed_count += 1
                 except OSError as e:
                     logger.error(f"  - Error removing ransom note '{note_path}': {e}")
                     note_error_count += 1

        logger.warning("--- Simulation Cleanup Finished ---")
        logger.warning(f"Files reverted: {renamed_count}, Rename errors: {rename_errors}")
        logger.warning(f"Notes removed: {note_removed_count}, Note removal errors: {note_error_count}")
        self.processed_files = [] # Clear processed list after cleanup attempt


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Ransomware Simulator Example (Conceptual - Safe Simulation) ---")

    # --- Setup Safe Test Environment ---
    sim_base_dir = "./simulated_victim_files"
    sim_doc_dir = os.path.join(sim_base_dir, "documents")
    sim_pic_dir = os.path.join(sim_base_dir, "pictures")
    if os.path.exists(sim_base_dir): shutil.rmtree(sim_base_dir) # Clean previous run
    os.makedirs(sim_doc_dir, exist_ok=True)
    os.makedirs(sim_pic_dir, exist_ok=True)
    # Create dummy files
    with open(os.path.join(sim_doc_dir, "report.docx"), "w") as f: f.write("doc content")
    with open(os.path.join(sim_doc_dir, "notes.txt"), "w") as f: f.write("text content")
    with open(os.path.join(sim_pic_dir, "cat.jpg"), "w") as f: f.write("jpeg content")
    with open(os.path.join(sim_pic_dir, "logo.png"), "w") as f: f.write("png content")
    with open(os.path.join(sim_pic_dir, "archive.zip"), "w") as f: f.write("zip content") # Will be ignored by default extensions
    print(f"Created dummy files/directories in: {sim_base_dir}")
    # --- End Setup ---

    simulator = RansomwareSimulator(
        target_dirs=[sim_doc_dir, sim_pic_dir], # Target ONLY the safe directories
        target_extensions=["*.txt", "*.docx", "*.jpg", "*.png"] # Target specific types
    )

    # Run the simulation
    simulator.run_simulation(max_files_to_process=10, delay_ms=50) # Limit files and add delay

    print("\n--- Simulation Effects (Check Filesystem): ---")
    print(f"Files in '{sim_doc_dir}': {os.listdir(sim_doc_dir)}")
    print(f"Files in '{sim_pic_dir}': {os.listdir(sim_pic_dir)}")

    # Clean up the simulation effects
    input("\nPress Enter to run cleanup simulation...") # Pause for inspection
    simulator.cleanup_simulation()

    print("\n--- After Cleanup (Check Filesystem): ---")
    print(f"Files in '{sim_doc_dir}': {os.listdir(sim_doc_dir)}")
    print(f"Files in '{sim_pic_dir}': {os.listdir(sim_pic_dir)}")

    # Final cleanup of test directory
    if os.path.exists(sim_base_dir): shutil.rmtree(sim_base_dir)

    print("\n--- End Example ---")
