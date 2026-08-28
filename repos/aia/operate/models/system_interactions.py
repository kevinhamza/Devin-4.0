import os
import psutil
import pyautogui
import subprocess
import time
import platform
import logging
from typing import Optional


class SystemInteraction:
    """
    Handles system interactions like keyboard control, mouse movement, process management,
    and file handling. Integrates system-level operations to allow the assistant to automate tasks
    and interact with the underlying OS and environment.
    """

    def __init__(self):
        self.logger = logging.getLogger("SystemInteraction")
        self.logger.setLevel(logging.DEBUG)
        self.system_info = self.get_system_info()

    def get_system_info(self) -> dict:
        """Fetch system information like OS, CPU, RAM, etc."""
        info = {
            "OS": platform.system(),
            "OS_version": platform.version(),
            "CPU": platform.processor(),
            "RAM": psutil.virtual_memory().total,
            "Disk": psutil.disk_usage('/').total,
        }
        self.logger.debug(f"System Info: {info}")
        return info

    def open_application(self, app_name: str) -> bool:
        """Open an application by its name (e.g., 'notepad', 'calculator')."""
        try:
            subprocess.Popen(app_name)
            self.logger.info(f"Opened application: {app_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to open application {app_name}: {e}")
            return False

    def kill_application(self, app_name: str) -> bool:
        """Kill a running application by name."""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if app_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    self.logger.info(f"Killed application: {app_name}")
                    return True
            self.logger.warning(f"Application {app_name} not found.")
            return False
        except Exception as e:
            self.logger.error(f"Failed to kill application {app_name}: {e}")
            return False

    def control_mouse(self, action: str, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        Control mouse actions like moving, clicking, and scrolling.
        Action can be one of ['move', 'click', 'scroll'].
        """
        try:
            if action == "move" and x is not None and y is not None:
                pyautogui.moveTo(x, y)
                self.logger.info(f"Moved mouse to ({x}, {y})")
            elif action == "click":
                pyautogui.click()
                self.logger.info("Mouse clicked.")
            elif action == "scroll" and x is not None:
                pyautogui.scroll(x)
                self.logger.info(f"Scrolled by {x}.")
            else:
                self.logger.error(f"Invalid action or missing parameters: {action}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Failed to control mouse: {e}")
            return False

    def control_keyboard(self, text: str) -> bool:
        """Simulate keyboard input."""
        try:
            pyautogui.write(text)
            self.logger.info(f"Typed: {text}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to type: {e}")
            return False

    def capture_screenshot(self, save_path: str) -> bool:
        """Capture a screenshot and save it to the specified path."""
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(save_path)
            self.logger.info(f"Screenshot saved to {save_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return False

    def execute_system_command(self, command: str) -> str:
        """Execute a system command and return the output."""
        try:
            result = subprocess.check_output(command, shell=True, text=True)
            self.logger.info(f"Executed command: {command}")
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to execute command: {e}")
            return f"Error: {e}"

    def shutdown_system(self) -> bool:
        """Shutdown the system."""
        try:
            if platform.system() == "Windows":
                subprocess.run(["shutdown", "/s", "/f", "/t", "0"])
            elif platform.system() == "Darwin":
                subprocess.run(["sudo", "shutdown", "-h", "now"])
            elif platform.system() == "Linux":
                subprocess.run(["sudo", "shutdown", "-h", "now"])
            else:
                self.logger.error("Unsupported OS for shutdown.")
                return False
            self.logger.info("System is shutting down.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown system: {e}")
            return False


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    system_interaction = SystemInteraction()

    # Opening an application
    system_interaction.open_application("notepad")

    # Killing an application
    system_interaction.kill_application("notepad")

    # Mouse control
    system_interaction.control_mouse("move", 100, 200)
    system_interaction.control_mouse("click")

    # Keyboard control
    system_interaction.control_keyboard("Hello World!")

    # Capture screenshot
    system_interaction.capture_screenshot("screenshot.png")

    # Execute system command
    output = system_interaction.execute_system_command("dir")
    print(output)

    # Shutdown system
    system_interaction.shutdown_system()
