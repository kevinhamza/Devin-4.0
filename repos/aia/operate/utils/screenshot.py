import pyautogui
from datetime import datetime
import os
from modules.error_handling import ErrorHandling


class ScreenshotUtility:
    """
    Utility for capturing and managing screenshots.
    """

    def __init__(self, screenshot_dir="screenshots"):
        """
        Initialize the ScreenshotUtility.
        :param screenshot_dir: Directory to store screenshots.
        """
        self.screenshot_dir = screenshot_dir
        self.error_handler = ErrorHandling()
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

    def capture_screenshot(self, filename=None):
        """
        Capture a screenshot and save it to the designated directory.
        :param filename: Optional filename for the screenshot.
        :return: Path to the saved screenshot.
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            print(f"Screenshot saved to {filepath}")
            return filepath
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to capture screenshot.")

    def capture_region(self, region, filename=None):
        """
        Capture a specific region of the screen.
        :param region: A tuple (x, y, width, height) defining the region.
        :param filename: Optional filename for the screenshot.
        :return: Path to the saved screenshot.
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"screenshot_region_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            screenshot = pyautogui.screenshot(region=region)
            screenshot.save(filepath)
            print(f"Region screenshot saved to {filepath}")
            return filepath
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to capture region screenshot.")

    def list_screenshots(self):
        """
        List all captured screenshots in the directory.
        :return: List of screenshot filenames.
        """
        try:
            screenshots = [
                f for f in os.listdir(self.screenshot_dir) if f.endswith(".png")
            ]
            print(f"Available screenshots: {screenshots}")
            return screenshots
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to list screenshots.")

    def delete_screenshot(self, filename):
        """
        Delete a specific screenshot.
        :param filename: Name of the screenshot file to delete.
        """
        try:
            filepath = os.path.join(self.screenshot_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Screenshot {filename} deleted.")
            else:
                print(f"Screenshot {filename} not found.")
        except Exception as e:
            self.error_handler.handle_exception(e, "Failed to delete screenshot.")


if __name__ == "__main__":
    utility = ScreenshotUtility()

    # Example: Capture a full screenshot
    utility.capture_screenshot()

    # Example: Capture a specific region
    region = (100, 100, 500, 400)
    utility.capture_region(region)

    # Example: List screenshots
    utility.list_screenshots()

    # Example: Delete a screenshot
    utility.delete_screenshot("example.png")
