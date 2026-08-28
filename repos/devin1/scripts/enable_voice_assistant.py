"""
enable_voice_assistant.py
--------------------------
This script ensures that Devin Voice Assistant is automatically enabled on system startup. 
It configures the necessary system settings, creates startup entries, and initializes the 
voice assistant service to ensure continuous functionality across PC and other operating systems.

Supported Features:
- Cross-platform support for Windows, macOS, and Linux.
- Dynamic generation of startup scripts.
- Robust error handling.
- Log management for tracking execution and issues.
"""

import os
import sys
import logging
import platform
import subprocess

# Configure logging
logging.basicConfig(
    filename="enable_voice_assistant.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_platform():
    """
    Returns the name of the current platform.
    """
    return platform.system().lower()

def create_startup_entry():
    """
    Creates a startup entry for Devin Voice Assistant based on the platform.
    """
    logging.info("Creating startup entry for Devin Voice Assistant.")
    platform_name = get_platform()

    try:
        if platform_name == "windows":
            create_windows_startup_entry()
        elif platform_name == "darwin":
            create_macos_startup_entry()
        elif platform_name == "linux":
            create_linux_startup_entry()
        else:
            logging.error(f"Unsupported platform: {platform_name}")
            print(f"Platform '{platform_name}' is not supported.")
    except Exception as e:
        logging.error(f"Failed to create startup entry: {e}")
        print(f"An error occurred: {e}")

def create_windows_startup_entry():
    """
    Creates a startup entry for Windows.
    """
    logging.info("Configuring startup entry for Windows.")
    startup_path = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    script_path = os.path.abspath("main.py")

    try:
        with open(os.path.join(startup_path, "enable_voice_assistant.bat"), "w") as f:
            f.write(f"@echo off\npython \"{script_path}\"\n")
        logging.info("Windows startup entry created successfully.")
        print("Devin Voice Assistant is now configured to start on Windows startup.")
    except Exception as e:
        logging.error(f"Failed to create Windows startup entry: {e}")
        raise

def create_macos_startup_entry():
    """
    Creates a startup entry for macOS.
    """
    logging.info("Configuring startup entry for macOS.")
    plist_content = f"""
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.devin.voiceassistant</string>
        <key>ProgramArguments</key>
        <array>
            <string>{sys.executable}</string>
            <string>{os.path.abspath("main.py")}</string>
        </array>
        <key>RunAtLoad</key>
        <true/>
        <key>StandardErrorPath</key>
        <string>/tmp/devin_va_err.log</string>
        <key>StandardOutPath</key>
        <string>/tmp/devin_va_out.log</string>
    </dict>
    </plist>
    """
    plist_path = os.path.expanduser("~/Library/LaunchAgents/com.devin.voiceassistant.plist")

    try:
        with open(plist_path, "w") as plist_file:
            plist_file.write(plist_content.strip())
        subprocess.run(["launchctl", "load", plist_path], check=True)
        logging.info("macOS startup entry created successfully.")
        print("Devin Voice Assistant is now configured to start on macOS startup.")
    except Exception as e:
        logging.error(f"Failed to create macOS startup entry: {e}")
        raise

def create_linux_startup_entry():
    """
    Creates a startup entry for Linux.
    """
    logging.info("Configuring startup entry for Linux.")
    desktop_entry_content = f"""
    [Desktop Entry]
    Type=Application
    Exec={sys.executable} {os.path.abspath("main.py")}
    Hidden=false
    NoDisplay=false
    X-GNOME-Autostart-enabled=true
    Name=Devin Voice Assistant
    Comment=Start Devin Voice Assistant on login
    """
    autostart_dir = os.path.expanduser("~/.config/autostart")
    os.makedirs(autostart_dir, exist_ok=True)
    desktop_entry_path = os.path.join(autostart_dir, "devin_voice_assistant.desktop")

    try:
        with open(desktop_entry_path, "w") as desktop_file:
            desktop_file.write(desktop_entry_content.strip())
        logging.info("Linux startup entry created successfully.")
        print("Devin Voice Assistant is now configured to start on Linux startup.")
    except Exception as e:
        logging.error(f"Failed to create Linux startup entry: {e}")
        raise

def check_permissions():
    """
    Checks if the script has the necessary permissions to execute.
    """
    if os.name != "nt" and os.geteuid() != 0:
        logging.warning("Script is not running with elevated privileges.")
        print("Warning: Elevated permissions are required for some startup configurations.")

def main():
    """
    Main function to enable Devin Voice Assistant on startup.
    """
    logging.info("Starting enable_voice_assistant script.")
    check_permissions()
    create_startup_entry()
    logging.info("Devin Voice Assistant startup configuration complete.")

if __name__ == "__main__":
    main()
