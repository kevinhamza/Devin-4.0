# Devin/recovery/disaster_recovery.py
# Purpose: A system for creating and restoring full backups of the application's
#          critical data to recover from major failures or crashes.

import logging
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List

# Configure basic logging
logger = logging.getLogger("DisasterRecovery")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class DisasterRecovery:
    """
    Manages full-system backups and restores for the Devin project.
    """
    def __init__(self, config_path: Path, backup_location: Path, retention_days: int = 7):
        """
        Initializes the disaster recovery system.

        Args:
            config_path: Path to the backup_config.json file.
            backup_location: Directory where backup archives will be stored.
            retention_days: How many days to keep old backups.
        """
        self.config_path = config_path
        self.backup_location = backup_location
        self.retention_days = retention_days
        
        if not self.config_path.is_file():
            raise FileNotFoundError(f"Backup config file not found at: {self.config_path}")
            
        self.backup_items = self._load_config()
        self.backup_location.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> List[str]:
        """Loads the list of files/directories to back up from the config file."""
        with open(self.config_path, 'r') as f:
            config = json.load(f)
            return config.get("paths_to_backup", [])

    def _enforce_retention_policy(self):
        """Deletes backups older than the retention period."""
        logger.info(f"Enforcing retention policy ({self.retention_days} days)...")
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for backup_file in self.backup_location.glob("devin_backup_*.tar.gz"):
            try:
                # Extract timestamp from filename like 'devin_backup_YYYYMMDD_HHMMSS.tar.gz'
                timestamp_str = backup_file.stem.split('_')[-2] + '_' + backup_file.stem.split('_')[-1]
                backup_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                if backup_date < cutoff_date:
                    logger.warning(f"Deleting old backup: {backup_file.name}")
                    backup_file.unlink()
            except (ValueError, IndexError):
                logger.warning(f"Could not parse date from backup file: {backup_file.name}")

    def create_backup(self) -> Optional[Path]:
        """
        Creates a full backup of all items specified in the config.
        
        Returns:
            The path to the newly created backup archive, or None on failure.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"devin_backup_{timestamp}"
        staging_dir = self.backup_location / f"staging_{timestamp}"
        
        try:
            logger.warning("--- Starting Full System Backup ---")
            staging_dir.mkdir()
            
            # 1. Copy all specified items to the staging area
            for item_path_str in self.backup_items:
                item_path = Path(item_path_str)
                if not item_path.exists():
                    logger.warning(f"Skipping '{item_path}': not found.")
                    continue
                
                dest_path = staging_dir / item_path.name
                logger.info(f"Staging '{item_path}' for backup...")
                if item_path.is_dir():
                    shutil.copytree(item_path, dest_path)
                else:
                    shutil.copy2(item_path, dest_path)
            
            # 2. Create a compressed archive of the staging area
            archive_path_base = self.backup_location / backup_name
            archive_path = Path(shutil.make_archive(str(archive_path_base), 'gztar', str(staging_dir)))
            logger.info(f"Successfully created backup archive: {archive_path}")
            
            # 3. Enforce retention policy for old backups
            self._enforce_retention_policy()
            
            logger.warning("--- System Backup Complete ---")
            return archive_path

        except Exception as e:
            logger.error(f"Backup creation failed: {e}", exc_info=True)
            return None
        finally:
            # 4. Clean up the staging directory
            if staging_dir.exists():
                shutil.rmtree(staging_dir)

    def restore_from_backup(self, backup_archive: Optional[Path] = None) -> bool:
        """
        Restores the system state from a backup archive.
        
        Args:
            backup_archive: The specific archive to restore. If None, the latest one is used.
        """
        if backup_archive is None:
            logger.info("No specific backup provided. Finding the latest...")
            backups = sorted(self.backup_location.glob("devin_backup_*.tar.gz"), reverse=True)
            if not backups:
                logger.error("Restore failed: No backups found.")
                return False
            backup_archive = backups[0]
        
        if not backup_archive.is_file():
            logger.error(f"Restore failed: Backup file not found at {backup_archive}")
            return False
            
        logger.warning(f"--- Starting Restore from '{backup_archive.name}' ---")
        quarantine_dir = self.backup_location / f"quarantine_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        quarantine_dir.mkdir()

        try:
            # 1. Safely move current data to a quarantine directory
            logger.info(f"Moving current data to quarantine at {quarantine_dir}...")
            for item_path_str in self.backup_items:
                item_path = Path(item_path_str)
                if item_path.exists():
                    shutil.move(str(item_path), str(quarantine_dir / item_path.name))
            
            # 2. Unpack the backup archive to the application root
            logger.info(f"Unpacking archive to restore files...")
            shutil.unpack_archive(str(backup_archive), Path(".")) # Unpack to current working directory
            
            logger.warning("--- Restore Complete ---")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}", exc_info=True)
            return False

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Disaster Recovery & Backup Prototype 🗄️💾 ===")
    print("=========================================================")
    
    # --- 1. Setup a dummy application environment for the demo ---
    demo_root = Path("./dr_demo_app")
    if demo_root.exists(): shutil.rmtree(demo_root)
    
    backup_dir = demo_root / "backups"
    config_dir = demo_root / "config"
    data_dir = demo_root / "data"
    
    # Create the directories
    backup_dir.mkdir(parents=True)
    config_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)
    
    # Create some dummy data files
    (data_dir / "vuln_db.sqlite").write_text("Original Vulnerability Data")
    (config_dir / "settings.json").write_text('{"theme": "dark"}')
    
    # Create the backup configuration file
    backup_config_file = demo_root / "backup_config.json"
    backup_config_content = {
        "paths_to_backup": [
            str(config_dir),
            str(data_dir)
        ]
    }
    with open(backup_config_file, 'w') as f:
        json.dump(backup_config_content, f)

    try:
        dr_system = DisasterRecovery(config_path=backup_config_file, backup_location=backup_dir)

        # --- 2. Create a backup ---
        print("\n--- Step 1: Creating a full backup of the demo app's data ---")
        backup_file_path = dr_system.create_backup()
        if backup_file_path:
            print(f"Backup created at: {backup_file_path}")
        else:
            raise RuntimeError("Backup creation failed, aborting demo.")

        # --- 3. Simulate a disaster ---
        print("\n--- Step 2: Simulating a disaster (deleting the data directory) ---")
        shutil.rmtree(data_dir)
        print(f"'{data_dir}' has been deleted. Health check: Exists? -> {data_dir.exists()}")

        # --- 4. Restore from the backup ---
        print("\n--- Step 3: Restoring from the latest backup ---")
        dr_system.restore_from_backup()
        
        # --- 5. Verify the restore ---
        print("\n--- Step 4: Verifying the restore ---")
        restored_data_file = data_dir / "vuln_db.sqlite"
        print(f"Checking for restored file: '{restored_data_file}'... Exists? -> {restored_data_file.is_file()}")
        if restored_data_file.is_file():
            print(f"  Content: '{restored_data_file.read_text()}'")
            print("\n[SUCCESS] The system was successfully restored from the backup.")
        else:
            print("\n[FAILURE] The system could not be restored.")

    finally:
        # --- Clean up the demo environment ---
        if demo_root.exists():
            shutil.rmtree(demo_root)
        logger.info("Cleaned up demo environment.")

    print("\n=========================================================")
    print("=== Disaster Recovery Prototype Complete ===")
    print("=========================================================")
