# scripts/initialize_db.py
from pathlib import Path
import json

def initialize():
    print("--- Initializing Devin Project Directories and Files ---")
    
    dirs_to_create = [
        "robot_logs",
        "intel_cache",
        "mock_ipfs_storage",
        "models"
    ]
    for d in dirs_to_create:
        Path(d).mkdir(exist_ok=True)
        print(f"  Ensured directory exists: ./{d}")
        
    files_to_touch = {
        "mock_blockchain_ledger.json": {"tokens": []}
    }
    for f, content in files_to_touch.items():
        if not Path(f).exists():
            with open(f, 'w') as fp:
                json.dump(content, fp, indent=2)
            print(f"  Created initial file: ./{f}")

    print("--- Initialization Complete ---")

if __name__ == "__main__":
    initialize()
