"""
modules/browser.py — Cross-platform browser automation for Devin AGI.
Primary: Selenium. Fallback: Playwright. Fallback: pyautogui + webbrowser.
"""

import os
import sys
import time
import webbrowser
import tempfile

# ── Selenium ──────────────────────────────────────────────────────────────────

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

# ── Playwright ────────────────────────────────────────────────────────────────

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


def _make_chrome_driver(headless: bool = False):
    opts = ChromeOptions()
    if headless:
        opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    try:
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        svc = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=svc, options=opts)
    except Exception:
        return webdriver.Chrome(options=opts)


def _make_firefox_driver(headless: bool = False):
    opts = FirefoxOptions()
    if headless:
        opts.add_argument('--headless')
    try:
        from selenium.webdriver.firefox.service import Service
        from webdriver_manager.firefox import GeckoDriverManager
        svc = Service(GeckoDriverManager().install())
        return webdriver.Firefox(service=svc, options=opts)
    except Exception:
        return webdriver.Firefox(options=opts)


class BrowserAutomation:
    """
    Unified browser automation using Selenium → Playwright → pyautogui.
    All methods return strings (success message or error).
    """

    def __init__(self, headless: bool = False, browser: str = 'auto'):
        self.headless = headless
        self.browser_pref = browser
        self._driver = None
        self._pw = None
        self._pw_page = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> str:
        """Start browser session."""
        if HAS_SELENIUM:
            try:
                if self.browser_pref in ('chrome', 'auto'):
                    self._driver = _make_chrome_driver(self.headless)
                elif self.browser_pref == 'firefox':
                    self._driver = _make_firefox_driver(self.headless)
                else:
                    self._driver = _make_chrome_driver(self.headless)
                return f'Browser started (Selenium/{self.browser_pref})'
            except Exception as e:
                self._driver = None
                # Try Firefox as fallback
                try:
                    self._driver = _make_firefox_driver(self.headless)
                    return 'Browser started (Selenium/Firefox)'
                except Exception:
                    pass

        if HAS_PLAYWRIGHT:
            try:
                self._pw = sync_playwright().start()
                b = self._pw.chromium.launch(headless=self.headless)
                self._pw_page = b.new_page()
                return 'Browser started (Playwright/Chromium)'
            except Exception as e:
                self._pw = None

        return 'Browser: using webbrowser module (no Selenium/Playwright)'

    def stop(self):
        """Close browser."""
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None
        if self._pw:
            try:
                self._pw.stop()
            except Exception:
                pass
            self._pw = None
            self._pw_page = None

    # ── Navigation ────────────────────────────────────────────────────────────

    def open_url(self, url: str) -> str:
        """Navigate to URL."""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        if self._driver:
            try:
                self._driver.get(url)
                time.sleep(1)
                return f'Navigated to: {url}'
            except Exception as e:
                return f'Navigation error: {e}'
        if self._pw_page:
            try:
                self._pw_page.goto(url)
                return f'Navigated to: {url}'
            except Exception as e:
                return f'Navigation error: {e}'
        webbrowser.open(url)
        time.sleep(1.5)
        return f'Opened in system browser: {url}'

    def get_current_url(self) -> str:
        if self._driver:
            return self._driver.current_url
        if self._pw_page:
            return self._pw_page.url
        return 'unknown'

    def get_title(self) -> str:
        if self._driver:
            return self._driver.title
        if self._pw_page:
            return self._pw_page.title()
        return 'unknown'

    def get_page_text(self) -> str:
        if self._driver:
            try:
                return self._driver.find_element(By.TAG_NAME, 'body').text[:3000]
            except Exception:
                pass
        if self._pw_page:
            try:
                return self._pw_page.inner_text('body')[:3000]
            except Exception:
                pass
        return ''

    # ── Interaction ───────────────────────────────────────────────────────────

    def click(self, selector: str, by: str = 'css') -> str:
        """Click element by CSS selector, xpath, or text."""
        by_map = {
            'css': By.CSS_SELECTOR if HAS_SELENIUM else None,
            'xpath': By.XPATH if HAS_SELENIUM else None,
            'id': By.ID if HAS_SELENIUM else None,
            'text': By.LINK_TEXT if HAS_SELENIUM else None,
            'name': By.NAME if HAS_SELENIUM else None,
        }
        if self._driver:
            try:
                b = by_map.get(by, By.CSS_SELECTOR)
                el = WebDriverWait(self._driver, 10).until(
                    EC.element_to_be_clickable((b, selector))
                )
                el.click()
                return f'Clicked: {selector}'
            except Exception as e:
                return f'Click failed: {e}'
        if self._pw_page:
            try:
                self._pw_page.click(selector)
                return f'Clicked: {selector}'
            except Exception as e:
                return f'Click failed: {e}'
        return 'No browser session active'

    def type_in(self, selector: str, text: str, by: str = 'css', clear_first: bool = True) -> str:
        """Type text into element."""
        if self._driver:
            try:
                b = {'css': By.CSS_SELECTOR, 'xpath': By.XPATH, 'id': By.ID,
                     'name': By.NAME}.get(by, By.CSS_SELECTOR)
                el = WebDriverWait(self._driver, 10).until(
                    EC.presence_of_element_located((b, selector))
                )
                if clear_first:
                    el.clear()
                el.send_keys(text)
                return f'Typed into {selector}: {text[:40]}'
            except Exception as e:
                return f'Type failed: {e}'
        if self._pw_page:
            try:
                if clear_first:
                    self._pw_page.fill(selector, text)
                else:
                    self._pw_page.type(selector, text)
                return f'Typed into {selector}: {text[:40]}'
            except Exception as e:
                return f'Type failed: {e}'
        return 'No browser session active'

    def press_key(self, key: str) -> str:
        """Press keyboard key (Enter, Tab, Escape, etc.)."""
        if self._driver:
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                key_map = {
                    'enter': Keys.ENTER, 'tab': Keys.TAB, 'escape': Keys.ESCAPE,
                    'backspace': Keys.BACKSPACE, 'delete': Keys.DELETE,
                    'up': Keys.ARROW_UP, 'down': Keys.ARROW_DOWN,
                    'left': Keys.ARROW_LEFT, 'right': Keys.ARROW_RIGHT,
                    'f5': Keys.F5, 'ctrl+a': Keys.CONTROL + 'a',
                    'ctrl+c': Keys.CONTROL + 'c', 'ctrl+v': Keys.CONTROL + 'v',
                }
                k = key_map.get(key.lower(), key)
                ActionChains(self._driver).send_keys(k).perform()
                return f'Pressed: {key}'
            except Exception as e:
                return f'Key press failed: {e}'
        if self._pw_page:
            try:
                self._pw_page.keyboard.press(key.capitalize())
                return f'Pressed: {key}'
            except Exception as e:
                return f'Key press failed: {e}'
        return 'No browser session active'

    def search_google(self, query: str) -> str:
        """Navigate to Google and search."""
        result = self.open_url('https://www.google.com')
        time.sleep(1)
        r2 = self.type_in('input[name="q"]', query)
        time.sleep(0.3)
        r3 = self.press_key('enter')
        time.sleep(1.5)
        return f'Google search: {query} — {r3}'

    def screenshot(self, path: str = None) -> str:
        """Take screenshot of current browser state."""
        if path is None:
            path = os.path.join(tempfile.gettempdir(), f'devin_browser_{int(time.time())}.png')
        if self._driver:
            try:
                self._driver.save_screenshot(path)
                return path
            except Exception as e:
                return f'Screenshot failed: {e}'
        if self._pw_page:
            try:
                self._pw_page.screenshot(path=path)
                return path
            except Exception as e:
                return f'Screenshot failed: {e}'
        return 'No browser session active'

    def execute_script(self, script: str) -> str:
        """Execute JavaScript in browser."""
        if self._driver:
            try:
                result = self._driver.execute_script(script)
                return str(result)
            except Exception as e:
                return f'JS error: {e}'
        if self._pw_page:
            try:
                result = self._pw_page.evaluate(script)
                return str(result)
            except Exception as e:
                return f'JS error: {e}'
        return 'No browser session active'

    def scroll(self, direction: str = 'down', amount: int = 300) -> str:
        """Scroll page."""
        delta = amount if direction == 'down' else -amount
        return self.execute_script(f'window.scrollBy(0, {delta})')

    def wait_for(self, selector: str, timeout: int = 10) -> bool:
        """Wait for element to appear."""
        if self._driver:
            try:
                WebDriverWait(self._driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                return True
            except Exception:
                return False
        if self._pw_page:
            try:
                self._pw_page.wait_for_selector(selector, timeout=timeout * 1000)
                return True
            except Exception:
                return False
        return False

    def find_text(self, text: str) -> bool:
        """Check if text appears anywhere on the page."""
        body = self.get_page_text()
        return text.lower() in body.lower()

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


# ── Convenience one-shot functions ────────────────────────────────────────────

def open_and_screenshot(url: str, headless: bool = True) -> str:
    """Open URL, wait, take screenshot, close. Returns screenshot path."""
    with BrowserAutomation(headless=headless) as br:
        br.open_url(url)
        time.sleep(2)
        return br.screenshot()


def search_and_extract(query: str, engine: str = 'google') -> str:
    """Open browser, search, return page text."""
    with BrowserAutomation(headless=True) as br:
        if engine == 'google':
            br.search_google(query)
        else:
            br.open_url(f'https://duckduckgo.com/?q={query.replace(" ", "+")}')
        time.sleep(2)
        return br.get_page_text()
