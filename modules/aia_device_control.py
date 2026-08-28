import pyautogui
import os
import subprocess
import time
import platform
import psutil

class DeviceControl:

    def __init__(self, config):
        self.config = config

    def move_mouse(self, x, y):
        """Move the mouse to a specific position"""
        pyautogui.moveTo(x, y)

    def click(self, x, y):
        """Simulate a mouse click at the specified coordinates"""
        pyautogui.click(x, y)

    def scroll(self, direction, amount=10):
        """Scroll the mouse in the specified direction"""
        pyautogui.scroll(amount) if direction == "up" else pyautogui.scroll(-amount)

    def screenshot(self, save_path="screenshot.png"):
        """Capture a screenshot of the current screen"""
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)

    def open_application(self, app_name):
        """Open an application by name"""
        try:
            if self.os_name == "Windows":
                subprocess.run([app_name], check=True)
            elif self.os_name == "Linux":
                subprocess.run(["xdg-open", app_name], check=True)
            elif self.os_name == "Darwin":  # macOS
                subprocess.run(["open", app_name], check=True)
            print(f"{app_name} opened successfully.")
        except Exception as e:
            print(f"Error opening {app_name}: {e}")

    def get_system_metrics(self):
        """Get screen width and height"""
        if self.os_name == "Windows":
            try:
                from win32api import GetSystemMetrics
                screen_width = GetSystemMetrics(0)
                screen_height = GetSystemMetrics(1)
                return screen_width, screen_height
            except ImportError:
                print("win32api is not available on this system.")
        else:
            try:
                screen_width, screen_height = pyautogui.size()
                return screen_width, screen_height
            except Exception as e:
                print(f"Error retrieving screen size: {e}")
        return None, None

    def close_application(self, app_name):
        """Close an application by its name"""
        for process in psutil.process_iter():
            try:
                if app_name.lower() in process.name().lower():
                    process.terminate()
                    print(f"{app_name} closed successfully.")
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    def shutdown_system(self):
        """Shut down the computer"""
        if self.os_name == "Windows":
            os.system("shutdown /s /t 1")
        elif self.os_name == "Linux":
            os.system("shutdown now")
        elif self.os_name == "Darwin":
            os.system("sudo shutdown -h now")

    def restart_system(self):
        """Restart the computer"""
        if self.os_name == "Windows":
            os.system("shutdown /r /t 1")
        elif self.os_name == "Linux":
            os.system("reboot")
        elif self.os_name == "Darwin":
            os.system("sudo shutdown -r now")

    def lock_system(self):
        """Lock the computer"""
        if self.os_name == "Windows":
            os.system("rundll32.exe user32.dll,LockWorkStation")
        elif self.os_name == "Linux":
            os.system("gnome-screensaver-command -l")
        elif self.os_name == "Darwin":
            os.system("/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession -suspend")

if __name__ == "__main__":
    device_control = DeviceControl()
    device_control.move_mouse(100, 100)
    device_control.click(100, 100)
    device_control.scroll("up", 5)
    device_control.screenshot("screenshot_test.png")
    device_control.open_application("notepad" if platform.system() == "Windows" else "gedit")
    time.sleep(2)
    device_control.close_application("notepad" if platform.system() == "Windows" else "gedit")
