# Devin/modules/automation_tools.py
# Purpose: A comprehensive suite of tools for high-level automation of
#          desktop GUI applications and web browsers.

import logging
import time
import platform
from typing import Optional, List, Tuple
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.remote.webelement import WebElement
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from pynput.keyboard import Key, Controller as KeyboardController
    from pynput.mouse import Button, Controller as MouseController
    import pyautogui
    DEPS_AVAILABLE = True
    _import_error = None
except ImportError as e:
    DEPS_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("AutomationTools")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False


class KeyboardMouseController:
    """Low-level wrapper for pynput keyboard and mouse control."""
    def __init__(self):
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
    
    def type_string(self, text: str, interval_secs: float = 0.01):
        """Types a string with a small delay between characters."""
        for char in text:
            self.keyboard.type(char)
            time.sleep(interval_secs)

    def press_key(self, key_name: str):
        key = getattr(Key, key_name, key_name)
        self.keyboard.press(key)

    def release_key(self, key_name: str):
        key = getattr(Key, key_name, key_name)
        self.keyboard.release(key)
        
    def hotkey(self, *key_names):
        """Presses and releases a combination of keys (e.g., for shortcuts)."""
        keys = [getattr(Key, k, k) for k in key_names]
        for k in keys:
            self.keyboard.press(k)
        for k in reversed(keys):
            self.keyboard.release(k)

    def move_mouse(self, x: int, y: int, duration: float = 0.2):
        """Moves the mouse to the specified screen coordinates."""
        pyautogui.moveTo(x, y, duration=duration)

    def click(self, button: str = 'left'):
        """Performs a mouse click."""
        btn = Button.left if button == 'left' else Button.right
        self.mouse.click(btn, 1)


class BrowserManager:
    """Manages the lifecycle of a Selenium WebDriver instance."""
    def __init__(self, browser_type: str = 'chrome'):
        if not DEPS_AVAILABLE:
            logger.warning(f"Browser automation features are unavailable: {_import_error}")
        self.driver = None
        self.browser_type = browser_type

    def open_browser(self):
        if self.driver is None:
            if not DEPS_AVAILABLE: raise ImportError(f"Dependencies missing: {_import_error}")
            logger.info(f"Opening {self.browser_type} browser...")
            if self.browser_type == 'chrome':
                self.driver = webdriver.Chrome()
            elif self.browser_type == 'firefox':
                self.driver = webdriver.Firefox()
            self.driver.maximize_window()
    
    def get_driver(self):
        if self.driver is None:
            self.open_browser()
        return self.driver

    def close_browser(self):
        if self.driver:
            logger.info("Closing browser.")
            self.driver.quit()
            self.driver = None


class DesktopAutomator:
    """High-level facade for controlling the desktop environment."""
    def __init__(self):
        if not DEPS_AVAILABLE:
            logger.warning(f"Desktop automation features are unavailable: {_import_error}")
            self.kbm = None
            self.screen_width, self.screen_height = (1920, 1080)
        else:
            self.kbm = KeyboardMouseController()
            self.screen_width, self.screen_height = pyautogui.size()
            logger.info(f"DesktopAutomator initialized. Screen size: {self.screen_width}x{self.screen_height}.")

    def open_application(self, app_name: str):
        """Opens an application using the OS-native 'Run' or 'Spotlight' dialog."""
        if not self.kbm: return
        logger.info(f"Opening application: '{app_name}'")
        sys_platform = platform.system()
        if sys_platform == "Windows":
            self.kbm.hotkey('cmd', 'r') # Windows Key + R
        elif sys_platform == "Darwin": # macOS
            self.kbm.hotkey('cmd', 'space') # Command + Space for Spotlight
        else: # Linux
            self.kbm.hotkey('alt', 'f2') # Alt+F2 is common for Run dialogs
        
        time.sleep(0.5)
        self.kbm.type_string(app_name)
        time.sleep(0.2)
        self.kbm.press_key('enter')
        self.kbm.release_key('enter')

    def move_mouse_to(self, x: int, y: int, duration_sec: float = 0.5):
        if DEPS_AVAILABLE:
            pyautogui.moveTo(x, y, duration=duration_sec, tween=pyautogui.easeInOutQuad)

    def mouse_click(self, button: str = 'left', clicks: int = 1, interval_sec: float = 0.1):
        if DEPS_AVAILABLE:
            pyautogui.click(button=button, clicks=clicks, interval=interval_sec)

    def type_text(self, text: str, interval_chars_sec: float = 0.05):
        if DEPS_AVAILABLE:
            pyautogui.write(text, interval=interval_chars_sec)

    def take_screenshot(self, output_path: str = "screenshot.png", region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """Takes a screenshot of the entire screen or a specific region."""
        if not DEPS_AVAILABLE: return "Error: Screenshot unavailable."
        filepath = Path(output_path)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        pyautogui.screenshot(str(filepath), region=region)
        logger.info(f"Screenshot saved to {filepath.resolve()}")
        return str(filepath.resolve())

    def find_and_click_image(self, image_path: str, confidence: float = 0.9) -> bool:
        """Finds an image on the screen and clicks on its center."""
        if not DEPS_AVAILABLE: return False
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if location:
                logger.info(f"Found image '{image_path}' on screen at {location}. Clicking.")
                self.kbm.move_mouse(location.x, location.y)
                self.kbm.click()
                return True
            else:
                logger.warning(f"Image '{image_path}' not found on screen.")
                return False
        except Exception as e:
            logger.error(f"Error during image search for '{image_path}': {e}")
            return False


class WebAutomator:
    """High-level facade for controlling a web browser."""
    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        self.browser = browser_manager or BrowserManager()

    def navigate_to_url(self, url: str):
        """Navigates the browser to a specific URL."""
        driver = self.browser.get_driver()
        if not driver: return {"status": "error", "message": "Browser unavailable."}
        driver.get(url)
        return {"status": "success", "message": f"Navigated to {url}"}

    def scrape_visible_text(self) -> str:
        """Scrapes all the visible text content from the current web page."""
        logger.info("Scraping visible text from the current page...")
        try:
            driver = self.browser.get_driver()
            if not driver: return "Error: Browser unavailable."
            body_element = driver.find_element(By.TAG_NAME, 'body')
            return body_element.text
        except Exception as e:
            logger.error(f"Failed to scrape visible text: {e}")
            return f"Error: Could not scrape page. Reason: {e}"

    def scrape_text_from_elements(self, locator: Tuple[str, str]) -> List[str]:
        """Returns the text of every element matching a locator, e.g. ('tag name', 'h1')."""
        try:
            driver = self.browser.get_driver()
            if not driver: return []
            by = getattr(By, locator[0].upper().replace(" ", "_"))
            elements = driver.find_elements(by, locator[1])
            return [element.text for element in elements]
        except Exception as e:
            logger.error(f"Could not scrape elements {locator}: {e}")
            return []

    def find_and_click(self, locator: Tuple[str, str], timeout: int = 10) -> bool:
        """Waits for an element to be clickable and then clicks it."""
        try:
            driver = self.browser.get_driver()
            if not driver: return False
            wait = WebDriverWait(driver, timeout)
            by = getattr(By, locator[0].upper().replace(" ", "_"))
            element = wait.until(EC.element_to_be_clickable((by, locator[1])))
            element.click()
            logger.info(f"Clicked on element located by {locator}")
            return True
        except Exception as e:
            logger.error(f"Could not find or click element {locator}: {e}")
            return False

    def find_and_type(self, locator: Tuple[str, str], text: str, timeout: int = 10) -> bool:
        """Waits for an element, clears it, and types text into it."""
        try:
            driver = self.browser.get_driver()
            if not driver: return False
            wait = WebDriverWait(driver, timeout)
            by = getattr(By, locator[0].upper().replace(" ", "_"))
            element = wait.until(EC.visibility_of_element_located((by, locator[1])))
            element.clear()
            element.send_keys(text)
            logger.info(f"Typed text into element located by {locator}")
            return True
        except Exception as e:
            logger.error(f"Could not find or type in element {locator}: {e}")
            return False

    def close_browser(self):
        """Closes the browser instance."""
        self.browser.close_browser()
        return {"status": "success", "message": "Browser closed."}
