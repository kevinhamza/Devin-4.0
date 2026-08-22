# Devin/recovery/auto_rollback.py
# Purpose: A system for creating filesystem snapshots and automatically
#          reverting to a known-good state if an update or change fails.

import logging
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any

# Configure basic logging
logger = logging.getLogger("AutoRollback")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class AutoRollback:
    """
    Manages filesystem snapshots and rollbacks for system resilience.
    """
    def __init__(self, snapshot_dir: Path):
        self.snapshot_dir = Path(snapshot_dir)
        self.manifest_path = self.snapshot_dir / "manifest.json"
        
        # Ensure the snapshot directory exists
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        """Loads the snapshot manifest file."""
        if self.manifest_path.is_file():
            with open(self.manifest_path, 'r') as f:
                return json.load(f)
        return {"snapshots": {}}

    def _save_manifest(self):
        """Saves the current manifest to the file."""
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)

    def create_snapshot(self, target_path: Path, reason: str = "Pre-update snapshot") -> Optional[str]:
        """
        Creates a compressed archive of a file or directory.

        Args:
            target_path: The file or directory to create a snapshot of.
            reason: A description of why the snapshot is being created.

        Returns:
            The unique snapshot ID if successful, otherwise None.
        """
        if not target_path.exists():
            logger.error(f"Cannot create snapshot. Path does not exist: {target_path}")
            return None

        snapshot_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        archive_name = f"{snapshot_id}"
        archive_path = self.snapshot_dir / archive_name
        
        logger.info(f"Creating snapshot '{snapshot_id}' for '{target_path}'...")
        
        try:
            # Use shutil to create a zip archive
            archive_format = "zip"
            if target_path.is_dir():
                shutil.make_archive(str(archive_path), archive_format, str(target_path))
            else: # It's a single file
                # make_archive works on directories, so we create a temporary dir
                temp_dir = self.snapshot_dir / f"temp_{snapshot_id}"
                temp_dir.mkdir()
                shutil.copy(target_path, temp_dir / target_path.name)
                shutil.make_archive(str(archive_path), archive_format, str(temp_dir))
                shutil.rmtree(temp_dir)
            
            # Record the snapshot in the manifest
            snapshot_info = {
                "timestamp": datetime.now().isoformat(),
                "original_path": str(target_path.resolve()),
                "archive_path": str(archive_path.resolve()) + f".{archive_format}",
                "reason": reason,
                "type": "dir" if target_path.is_dir() else "file"
            }
            self.manifest["snapshots"][snapshot_id] = snapshot_info
            self._save_manifest()
            
            logger.info(f"Snapshot created successfully: {snapshot_info['archive_path']}")
            return snapshot_id

        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            return None

    def rollback(self, snapshot_id: str) -> bool:
        """
        Reverts a file or directory to a specific snapshot.
        """
        snapshot_info = self.manifest["snapshots"].get(snapshot_id)
        if not snapshot_info:
            logger.error(f"Rollback failed: Snapshot ID '{snapshot_id}' not found in manifest.")
            return False
            
        original_path = Path(snapshot_info["original_path"])
        archive_path = Path(snapshot_info["archive_path"])
        
        logger.warning(f"Starting rollback of '{original_path}' to snapshot '{snapshot_id}'...")
        
        try:
            # 1. Remove the current (broken) state
            if original_path.exists():
                if original_path.is_dir():
                    shutil.rmtree(original_path)
                else:
                    original_path.unlink()
            
            # 2. Unpack the archive to restore the old state
            if snapshot_info["type"] == "dir":
                 shutil.unpack_archive(str(archive_path), str(original_path))
            else: # It was a single file
                # We need to unpack to the parent directory
                original_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.unpack_archive(str(archive_path), original_path.parent)

            logger.warning("Rollback completed successfully.")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}", exc_info=True)
            return False

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Auto-Rollback & System Resilience Prototype 🔄🔧 ===")
    print("=========================================================")
    
    # --- Setup a demo environment ---
    demo_root = Path("./rollback_demo")
    snapshot_dir = demo_root / "snapshots"
    project_dir = demo_root / "project"
    config_file = project_dir / "config.txt"
    
    # Clean up previous runs
    if demo_root.exists():
        shutil.rmtree(demo_root)
    
    project_dir.mkdir(parents=True)
    original_content = "version=1\nsetting=stable"
    config_file.write_text(original_content)
    
    try:
        # --- 1. Initialize the rollback system ---
        rollback_system = AutoRollback(snapshot_dir=snapshot_dir)
        print("Original file content:")
        print(config_file.read_text())
        
        # --- 2. Create a snapshot before making a change ---
        print("\n--- Step 1: Creating snapshot before update ---")
        snapshot_id = rollback_system.create_snapshot(config_file, reason="Pre-v2-update")
        if not snapshot_id:
            raise RuntimeError("Failed to create snapshot, aborting demo.")
            
        # --- 3. Simulate a broken update ---
        print("\n--- Step 2: Applying a 'broken' update ---")
        broken_content = "version=2\nsetting=corrupted!!!!"
        config_file.write_text(broken_content)
        print("Updated file content:")
        print(config_file.read_text())
        
        # --- 4. Simulate a failed health check ---
        print("\n--- Step 3: Running a health check ---")
        def health_check(file_path):
            content = file_path.read_text()
            return "corrupted" not in content

        if not health_check(config_file):
            logger.error("Health check FAILED! The new update is broken.")
            
            # --- 5. Initiate Rollback ---
            print("\n--- Step 4: Initiating automatic rollback ---")
            success = rollback_system.rollback(snapshot_id)
            if success:
                print("\n--- Step 5: Verifying restored content ---")
                restored_content = config_file.read_text()
                print("Restored file content:")
                print(restored_content)
                assert restored_content == original_content
                print("\n[SUCCESS] File has been successfully restored to its previous state.")
        else:
            print("[SUCCESS] Health check passed. No rollback needed.")

    finally:
        # --- Clean up demo environment ---
        if demo_root.exists():
            shutil.rmtree(demo_root)
        logger.info("Cleaned up demo environment.")


    print("\n=========================================================")
    print("=== Auto-Rollback Prototype Complete ===")
    print("=========================================================")
