import os
import zipfile
from datetime import datetime

# Directory containing logs
LOGS_DIR = "logs/"
BACKUP_DIR = "backups/"
BACKUP_FILENAME = "logs_backup.zip"

def create_logs_backup():
    if not os.path.exists(LOGS_DIR):
        print(f"[ERROR] Logs directory '{LOGS_DIR}' does not exist.")
        return

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    backup_path = os.path.join(BACKUP_DIR, BACKUP_FILENAME)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    new_backup_path = backup_path.replace(".zip", f"_{timestamp}.zip")

    try:
        with zipfile.ZipFile(new_backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for foldername, subfolders, filenames in os.walk(LOGS_DIR):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    arcname = os.path.relpath(file_path, LOGS_DIR)
                    zipf.write(file_path, arcname)
        print(f"[SUCCESS] Logs backup created: {new_backup_path}")
    except Exception as e:
        print(f"[ERROR] Failed to create logs backup: {e}")

if __name__ == "__main__":
    create_logs_backup()
