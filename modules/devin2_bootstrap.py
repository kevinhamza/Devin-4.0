# Devin/bootstrap.py
# Purpose: A pre-flight check script to ensure the system is ready to run.

import os
import sys
import shutil
import importlib.util

print("--- Running Devin AGI System Readiness Bootstrap ---")

# --- Helper Functions ---
def check_dependency(name, import_name=None, check_command=None):
    """Checks for a Python library or an external command."""
    print(f"[ ] Checking for {name}...", end="")
    import_name = import_name or name.lower()
    try:
        if check_command:
            if not shutil.which(check_command):
                raise ImportError
        else:
            if not importlib.util.find_spec(import_name):
                raise ImportError
        print("\r[✅]")
        return True
    except ImportError:
        print(f"\r[❌] - MISSING. Please install '{name}' or ensure it's in your PATH.")
        return False

def check_env_var(var_name):
    """Checks if a required environment variable is set."""
    print(f"[ ] Checking for environment variable {var_name}...", end="")
    if os.getenv(var_name):
        print("\r[✅]")
        return True
    else:
        print(f"\r[❌] - NOT SET. Please set {var_name} in your .env file.")
        return False

# --- Main Checks ---
print("\n--- Checking Python Dependencies ---")
checks = {
    "requests": check_dependency("Requests"),
    "numpy": check_dependency("NumPy"),
    "pandas": check_dependency("Pandas"),
    "scikit-learn": check_dependency("scikit-learn", "sklearn"),
    "ultralytics": check_dependency("Ultralytics"),
    "Pillow": check_dependency("Pillow", "PIL"),
    "python-dotenv": check_dependency("python-dotenv", "dotenv"),
}

print("\n--- Checking External Tools ---")
checks["adb"] = check_dependency("Android Debug Bridge", check_command="adb")
checks["ros2"] = check_dependency("ROS 2", check_command="ros2")

print("\n--- Checking API Credentials ---")
from dotenv import load_dotenv
load_dotenv()
checks["OPENAI_API_KEY"] = check_env_var("OPENAI_API_KEY")
checks["VIRUSTOTAL_API_KEY"] = check_env_var("VIRUSTOTAL_API_KEY")

# --- Final Report ---
print("\n--- System Readiness Report ---")
if all(checks.values()):
    print("✅ All checks passed. System is ready to launch.")
    sys.exit(0)
else:
    print("❌ Some checks failed. Please resolve the issues listed above before running main.py.")
    sys.exit(1)
