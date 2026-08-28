# Devin/plugins/gaming_assistant.py
# Purpose: A toolkit for GUI automation and enhancing gaming workflows by
#          analyzing the screen and controlling the mouse and keyboard.

import logging
import time
from pathlib import Path
from typing import Optional, Tuple

try:
    import pyautogui
    # PyAutoGUI requires an OS-specific backend for screenshots, e.g., Pillow, scrot.
    # We will assume a compatible one is installed.
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    import cv2 # OpenCV is a dependency for pyautogui's image recognition
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("GamingAssistant")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class GamingAssistant:
    """
    Provides tools for screen analysis and GUI automation.
    """
    def __init__(self):
        if not PYAUTOGUI_AVAILABLE or not OPENCV_AVAILABLE:
            raise ImportError("PyAutoGUI and opencv-python are required. 'pip install pyautogui opencv-python'")
        
        # Configure PyAutoGUI's failsafe (move mouse to top-left to abort)
        pyautogui.FAILSAFE = True
        logger.info("Gaming Assistant initialized. Move mouse to top-left corner to trigger failsafe and stop execution.")

    # --- Screen Analysis Methods ---

    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None, save_path: Optional[Path] = None) -> Optional[Path]:
        """
        Captures the screen or a specific region.
        
        Args:
            region (tuple, optional): A tuple (left, top, width, height) of the region to capture.
            save_path (Path, optional): The path to save the screenshot. If None, a temporary path is used.

        Returns:
            The Path object where the screenshot was saved.
        """
        if save_path is None:
            save_path = Path(f"screenshot_{int(time.time())}.png")
        
        try:
            screenshot = pyautogui.screenshot(region=region)
            screenshot.save(save_path)
            logger.info(f"Screenshot captured and saved to {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return None

    def find_on_screen(self, template_image_path: Path, confidence: float = 0.8) -> Optional[Tuple[int, int, int, int]]:
        """
        Finds a template image on the screen and returns its bounding box.
        
        Args:
            template_image_path (Path): Path to the image to find.
            confidence (float): The confidence level for matching (requires grayscale).

        Returns:
            A tuple (left, top, width, height) of the found image's location, or None.
        """
        if not template_image_path.is_file():
            logger.error(f"Template image not found: {template_image_path}")
            return None
        try:
            location = pyautogui.locateOnScreen(str(template_image_path), confidence=confidence)
            if location:
                logger.info(f"Found '{template_image_path.name}' at location: {location}")
                return location
            else:
                logger.info(f"Could not find '{template_image_path.name}' on screen.")
                return None
        except Exception as e:
            # pyautogui.ImageNotFoundException is a common one here
            logger.warning(f"Error while searching for image: {e}")
            return None

    # --- Automation Methods ---

    def click_location(self, x: int, y: int, duration: float = 0.2, button: str = 'left'):
        """Moves to and clicks a specific screen coordinate."""
        logger.info(f"Clicking at ({x}, {y})")
        pyautogui.moveTo(x, y, duration=duration)
        pyautogui.click(button=button)

    def press_key(self, key: str, presses: int = 1):
        """Presses a single key."""
        logger.info(f"Pressing key: '{key}' ({presses}x)")
        pyautogui.press(key, presses=presses)

    def type_string(self, text: str, interval: float = 0.05):
        """Types out a string of text."""
        logger.info(f"Typing: '{text}'")
        pyautogui.write(text, interval=interval)

    # --- High-Level Workflow Methods ---

    def click_image(self, template_image_path: Path, confidence: float = 0.8) -> bool:
        """Finds a template image on screen and clicks its center."""
        location = self.find_on_screen(template_image_path, confidence)
        if location:
            center_point = pyautogui.center(location)
            self.click_location(center_point.x, center_point.y)
            return True
        return False

    def perform_repetitive_click(self, template_image_path: Path, interval_sec: int, run_duration_sec: int):
        """Repeatedly finds and clicks an image for a total duration."""
        logger.warning(f"Starting repetitive click task on '{template_image_path.name}' for {run_duration_sec} seconds.")
        start_time = time.time()
        while time.time() - start_time < run_duration_sec:
            logger.info("Searching for image to click...")
            if self.click_image(template_image_path):
                logger.info(f"Clicked successfully. Waiting {interval_sec} seconds.")
            else:
                logger.info("Image not found on this attempt.")
            
            time.sleep(interval_sec)
        logger.warning("Repetitive click task finished.")


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Gaming Assistant & GUI Automator Prototype 🎮🤖 ===")
    print("=========================================================")
    print("!!! WARNING: This script takes control of your mouse and keyboard. !!!")
    print("!!! To stop execution at any time, move your mouse to the top-left corner of the screen. !!!")
    
    if not PYAUTOGUI_AVAILABLE or not OPENCV_AVAILABLE:
        print("\nERROR: Missing one or more required libraries. Please run:")
        print("pip install pyautogui opencv-python")
    else:
        assistant = GamingAssistant()
        
        # --- Demo: Finding and clicking an image ---
        print("\n--- Demo: Find and Click ---")
        print("This demo will take a screenshot of a small region of your screen.")
        print("Please position your mouse over something you want Devin to click (e.g., a desktop icon, the Start button).")
        input("Press Enter when your mouse is in position...")
        
        # Capture a small template image around the current mouse position
        template_path = Path("click_template.png")
        mouse_x, mouse_y = pyautogui.position()
        capture_region = (mouse_x - 25, mouse_y - 25, 50, 50) # 50x50 box around cursor
        
        if assistant.capture_screen(region=capture_region, save_path=template_path):
            print(f"Template image saved as '{template_path}'. Now attempting to find and click it.")
            print("Keep your hands off the mouse for the next 5 seconds...")
            time.sleep(5)
            
            if assistant.click_image(template_path):
                print("\nSUCCESS! The assistant found and clicked the image.")
            else:
                print("\nFAILURE. The assistant could not find the image on screen.")
        
            # Clean up the template file
            if template_path.exists():
                template_path.unlink()
        else:
            print("Failed to capture the template image.")

    print("\n=========================================================")
    print("=== Gaming Assistant Prototype Complete ===")
    print("=========================================================")
