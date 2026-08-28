# Devin/scripts/migrate_data.py
# Purpose: A script to handle data migrations between different versions
#          of the Devin project, ensuring data compatibility over time.

import logging
import time
from pathlib import Path
from typing import Optional
import shutil
import argparse

try:
    import pandas as pd
    import pyarrow # Required for feather
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("DataMigrator")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

class DataMigrator:
    """
    Manages and applies data migrations in a sequential, version-aware manner.
    """
    # The latest version of the data schema that this script supports.
    CURRENT_DATA_VERSION = 2

    def __init__(self, data_root_dir: str):
        if not PANDAS_AVAILABLE:
            raise ImportError("The 'pandas' and 'pyarrow' libraries are required. Run 'pip install pandas pyarrow'.")
        
        self.root_dir = Path(data_root_dir)
        self.version_file = self.root_dir / ".data_version"
        
        # A mapping of starting versions to the migration function to run
        self.migrations = {
            1: self._migrate_v1_to_v2
        }

    def _get_current_version(self) -> int:
        """Reads the version from the .data_version file."""
        if not self.version_file.exists():
            # If the file doesn't exist, we assume it's the oldest version.
            logger.warning("No .data_version file found. Assuming data is at version 1.")
            return 1
        return int(self.version_file.read_text().strip())

    def _update_version(self, new_version: int):
        """Updates the .data_version file to the new version."""
        logger.info(f"Updating data version to {new_version}.")
        self.version_file.write_text(str(new_version))

    def _migrate_v1_to_v2(self):
        """
        Migration from Version 1 to Version 2.
        - CONVERTS logs from CSV format to the more efficient Feather format.
        - RENAMES the 'value' column to 'metric_value' for clarity.
        """
        logger.info("--- Running migration from v1 (CSV logs) to v2 (Feather logs) ---")
        log_dir = self.root_dir / "robot_logs"
        if not log_dir.is_dir():
            logger.warning(f"Log directory '{log_dir}' not found. Nothing to migrate.")
            return
            
        csv_files = list(log_dir.glob("*.csv"))
        if not csv_files:
            logger.info("No legacy .csv log files found to migrate.")
            return
        
        logger.info(f"Found {len(csv_files)} legacy .csv files to convert.")
        for csv_file in csv_files:
            try:
                logger.info(f"  Processing '{csv_file.name}'...")
                df = pd.read_csv(csv_file)
                
                # --- Schema Transformation ---
                # Example: Rename a column for the new schema
                if 'value' in df.columns:
                    df.rename(columns={'value': 'metric_value'}, inplace=True)
                
                # --- Format Conversion ---
                feather_file = csv_file.with_suffix('.feather')
                df.to_feather(feather_file)
                
                # Optional: remove the old file after successful conversion
                # csv_file.unlink() 
                logger.info(f"    -> Successfully converted to '{feather_file.name}'.")
            except Exception as e:
                logger.error(f"Failed to migrate '{csv_file.name}': {e}")
                raise # Stop the migration process on failure

    def run_migrations(self):
        """
        Checks the current data version and runs all necessary migrations in order.
        """
        if not self.root_dir.is_dir():
            logger.error(f"Data root directory '{self.root_dir}' does not exist. Aborting.")
            return

        current_version = self._get_current_version()
        
        if current_version >= self.CURRENT_DATA_VERSION:
            logger.info(f"Data is already at the latest version ({current_version}). No migration needed.")
            return
        
        logger.info(f"Current data version is {current_version}. Target version is {self.CURRENT_DATA_VERSION}.")
        
        while current_version < self.CURRENT_DATA_VERSION:
            migration_func = self.migrations.get(current_version)
            if not migration_func:
                logger.error(f"No migration function found for version {current_version}. Aborting.")
                return
            
            try:
                migration_func()
                current_version += 1
                self._update_version(current_version)
            except Exception as e:
                logger.critical(f"A critical error occurred during migration from v{current_version-1} to v{current_version}. The process has been halted to prevent data corruption. Error: {e}")
                return
        
        logger.info("All data migrations completed successfully.")

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Data Migration Script Demo 🔄 ===")
    print("=========================================================")
    
    # --- 1. Create a temporary 'legacy' project structure for the demo ---
    DEMO_DIR = Path("./temp_migration_demo")
    if DEMO_DIR.exists(): shutil.rmtree(DEMO_DIR)
    LOG_DIR = DEMO_DIR / "robot_logs"
    LOG_DIR.mkdir(parents=True)
    
    # Create a fake version file indicating an old data version
    (DEMO_DIR / ".data_version").write_text("1")
    
    # Create some fake legacy (v1) CSV log files
    pd.DataFrame({
        "timestamp": [time.time() - 100, time.time() - 50],
        "value": [55.5, 60.2] # The old column name
    }).to_csv(LOG_DIR / "cpu_usage.csv", index=False)
    
    pd.DataFrame({
        "timestamp": [time.time() - 80],
        "value": [1024] # The old column name
    }).to_csv(LOG_DIR / "network_traffic.csv", index=False)

    print(f"Created a temporary legacy project at '{DEMO_DIR.resolve()}' with data version 1.")
    print("Legacy logs are in .csv format with a 'value' column.")
    
    # --- 2. Run the migrator on the demo directory ---
    input("\nPress Enter to run the data migration...")
    
    try:
        migrator = DataMigrator(data_root_dir=str(DEMO_DIR))
        migrator.run_migrations()
        
        # --- 3. Verify the results ---
        print("\n--- Verifying Migration Results ---")
        final_version = int((DEMO_DIR / ".data_version").read_text().strip())
        print(f"Final data version in file: {final_version}")
        assert final_version == DataMigrator.CURRENT_DATA_VERSION

        cpu_feather_path = LOG_DIR / "cpu_usage.feather"
        print(f"Checking for new file: '{cpu_feather_path.name}'... Exists: {cpu_feather_path.exists()}")
        assert cpu_feather_path.exists()

        # Check that the schema was updated
        migrated_df = pd.read_feather(cpu_feather_path)
        print(f"Checking for renamed column 'metric_value'... Exists: {'metric_value' in migrated_df.columns}")
        assert 'metric_value' in migrated_df.columns
        assert 'value' not in migrated_df.columns

    except Exception as e:
        logger.error(f"Demo failed to run: {e}", exc_info=True)
    finally:
        # --- 4. Clean up the temporary directory ---
        shutil.rmtree(DEMO_DIR)
        print("\nCleaned up temporary demo directory.")

    print("\n=========================================================")
    print("=== Data Migration Demo Complete ===")
    print("=========================================================")
