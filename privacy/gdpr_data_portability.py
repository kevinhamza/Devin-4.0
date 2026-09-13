# Devin/privacy/gdpr_data_portability.py
# Purpose: A tool to export user-related data from the system's various
#          data stores into standard, machine-readable formats (JSON, CSV),
#          complying with data portability rights like GDPR.

import logging
import sqlite3
import json
import csv
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

# Import the manager to create a demo database
try:
    from modules.pentesting_tools.vulnerability_management import VulnerabilityManager
    CAN_CREATE_DEMO_DB = True
except ImportError:
    CAN_CREATE_DEMO_DB = False


# Configure basic logging
logger = logging.getLogger("DataPortability")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class DataPortabilityTool:
    """
    Handles the exporting of user/project data from various sources.
    """
    def __init__(self, db_paths: Dict[str, Path]):
        """
        Initializes the tool with paths to various data sources.
        
        Args:
            db_paths (Dict[str, Path]): A map of data source names to their DB file paths.
                                        Example: {'vuln_db': Path('vuln_management.db')}
        """
        self.db_paths = db_paths
        self.conn_map = {}

    def _connect_db(self, db_name: str) -> Optional[sqlite3.Connection]:
        """Connects to a specified SQLite database."""
        db_path = self.db_paths.get(db_name)
        if not db_path or not db_path.is_file():
            logger.error(f"Database file for '{db_name}' not found at {db_path}")
            return None
        
        if db_name not in self.conn_map:
            try:
                self.conn_map[db_name] = sqlite3.connect(db_path)
            except Exception as e:
                logger.error(f"Failed to connect to database '{db_name}': {e}")
                return None
        
        return self.conn_map[db_name]

    def _fetch_vulnerability_data(self, project_id: int) -> Optional[Dict]:
        """Fetches all data for a project from the vulnerability management DB."""
        conn = self._connect_db('vuln_db')
        if not conn: return None
        
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Fetch project details
        project_row = cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not project_row:
            logger.warning(f"No project found with ID {project_id}")
            return None
        
        project_details = dict(project_row)
        
        # Fetch associated vulnerabilities
        vuln_rows = cursor.execute("SELECT * FROM vulnerabilities WHERE project_id = ?", (project_id,)).fetchall()
        vulnerabilities = [dict(row) for row in vuln_rows]
        
        return {"project_details": project_details, "vulnerabilities": vulnerabilities}

    def _create_zip_archive(self, source_dir: Path, output_zip_path: Path):
        """Creates a zip archive from a directory of exported files."""
        logger.info(f"Creating ZIP archive at {output_zip_path}...")
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.glob('**/*'):
                if file_path.is_file():
                    zipf.write(file_path, file_path.relative_to(source_dir))
        logger.info("Archive created successfully.")

    def export_project_data(self, project_id: int, output_dir: Path):
        """
        Exports all data for a given project ID and packages it into a zip file.
        """
        logger.warning(f"--- Starting data export for Project ID: {project_id} ---")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Fetch data from the vulnerability database
        vuln_data = self._fetch_vulnerability_data(project_id)
        
        if not vuln_data:
            logger.error("Data export failed: Could not retrieve data.")
            return

        # 2. Write data to respective files
        # Write project details to JSON
        details_path = output_dir / "project_details.json"
        with open(details_path, 'w') as f:
            json.dump(vuln_data['project_details'], f, indent=2, default=str)
        logger.info(f"Exported project details to {details_path}")

        # Write vulnerabilities to CSV
        vulns_path = output_dir / "vulnerabilities.csv"
        vulnerabilities = vuln_data['vulnerabilities']
        if vulnerabilities:
            with open(vulns_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=vulnerabilities[0].keys())
                writer.writeheader()
                writer.writerows(vulnerabilities)
            logger.info(f"Exported {len(vulnerabilities)} vulnerabilities to {vulns_path}")

        # 3. Create a final ZIP archive
        zip_path = output_dir.parent / f"project_{project_id}_export.zip"
        self._create_zip_archive(output_dir, zip_path)
        
        logger.warning(f"--- Data export complete for Project ID: {project_id} ---")

    def close_connections(self):
        """Closes any open database connections."""
        for conn in self.conn_map.values():
            conn.close()
        self.conn_map = {}

# --- Example Usage ---
if __name__ == "__main__":
    if not CAN_CREATE_DEMO_DB:
        print("\nERROR: Cannot run demo without VulnerabilityManager. Please ensure all modules are present.")
    else:
        print("=========================================================")
        print("=== GDPR Data Portability Prototype 🏛️📦 ===")
        print("=========================================================")
        
        # 1. Setup a dummy database for the demo
        db_file = Path("portability_demo.db")
        if db_file.exists(): db_file.unlink()
        
        manager = VulnerabilityManager(db_path=db_file)
        project_id = manager.create_project(name="Project Excalibur", targets="api.example.com")
        manager.add_vulnerability(project_id, "Critical RCE in API", "...", "Critical", "CVE-2025-1111")
        manager.add_vulnerability(project_id, "Missing HSTS Header", "...", "Medium")
        manager.conn.close() # Close the manager's connection so our tool can connect
        
        logger.info(f"Created demo database '{db_file}' with project ID {project_id}.")
        
        # 2. Initialize and run the export tool
        output_dir = Path("./data_export")
        tool = None
        try:
            db_paths = {'vuln_db': db_file}
            tool = DataPortabilityTool(db_paths=db_paths)
            tool.export_project_data(project_id=project_id, output_dir=output_dir)
            
            # 3. Verify the output
            print("\n--- Verification ---")
            zip_file = Path(f"project_{project_id}_export.zip")
            if zip_file.exists():
                print(f"[SUCCESS] Final archive created: {zip_file}")
            else:
                print("[FAILURE] Final archive was not created.")

        finally:
            # 4. Clean up
            if tool: tool.close_connections()
            if db_file.exists(): db_file.unlink()
            if output_dir.exists():
                import shutil
                shutil.rmtree(output_dir)
            if 'zip_file' in locals() and zip_file.exists():
                zip_file.unlink()
            logger.info("Cleaned up demo files.")

        print("\n=========================================================")
        print("=== Data Portability Prototype Complete ===")
        print("=========================================================")
