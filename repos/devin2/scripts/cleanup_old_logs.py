# scripts/cleanup_old_logs.py
import argparse
from pathlib import Path
import time

def cleanup(log_dir, days_to_keep):
    print(f"Scanning '{log_dir}' for logs older than {days_to_keep} days...")
    retention_seconds = days_to_keep * 86400
    now = time.time()
    files_deleted = 0
    
    for f in Path(log_dir).glob('*.feather'):
        if (now - f.stat().st_mtime) > retention_seconds:
            print(f"  - Deleting old log file: {f.name}")
            f.unlink()
            files_deleted += 1
            
    print(f"\nCleanup complete. Deleted {files_deleted} old log file(s).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up old log files.")
    parser.add_argument("--dir", default="robot_logs", help="The log directory to clean.")
    parser.add_argument("--keep-days", type=int, default=30, help="Number of days of logs to keep.")
    args = parser.parse_args()
    cleanup(args.dir, args.keep_days)
