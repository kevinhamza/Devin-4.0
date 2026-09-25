"""
Browser agent for Devin-4.0.
Playwright/Selenium browser automation with vision-guided element finding.
"""

import os
import sys
import time
import tempfile
import base64
import json
import re
from typing import Optional, Dict, List, Any, Tuple

_IS_LINUX = sys.platform.startswith("linux")
_IS_MAC = sys.platform == "darwin"
_IS_WIN = sys.platform.startswith("win")

_HAS_PLAYWRIGHT = False
try:
    from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
    _HAS_PLAYWRIGHT = True
except ImportError:
    pass

_HAS_SELENIUM = False
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    _HAS_SELENIUM = True
except ImportError:
    pass

_HAS_BS4 = False
try:
    from bs4 import BeautifulSoup
    _HAS_BS4 = True
except ImportError:
    pass


def _analyze_screenshot_for_element(
    screenshot_path: str,
    element_description: str,
    context: str = "",
) -> str:
    """Ask vision AI to find a UI element; returns JSON with coordinates."""
    prompt = (
        f"Look at this browser screenshot. Find the UI element: '{element_description}'. "
        f"{'Context: ' + context + '. ' if context else ''}"
        'Return JSON: {"found": true/false, "x": <pixel_x>, "y": <pixel_y>, '
        '"confidence": 0-1, "description": "what you see"}. '
        "x and y should be the pixel center of the element."
    )

    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            from PIL import Image
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            img = Image.open(screenshot_path)
            response = model.generate_content([prompt, img])
            return response.text
        except Exception:
            pass

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic
            with open(screenshot_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            client = anthropic.Anthropic(api_key=anthropic_key)
            msg = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=256,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_data}},
                        {"type": "text", "text": prompt},
                    ]
                }]
            )
            return msg.content[0].text
        except Exception:
            pass

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            with open(screenshot_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            client = openai.OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model="gpt-4o",
                max_tokens=256,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}},
                        {"type": "text", "text": prompt},
                    ]
                }]
            )
            return resp.choices[0].message.content
        except Exception:
            pass

    return '{"found": false, "error": "no vision provider available"}'


def _parse_element_coords(vision_response: str) -> Optional[Tuple[int, int]]:
    for pattern in [r"\{[^{}]+\}", r"\{.*?\}"]:
        for m in re.finditer(pattern, vision_response, re.DOTALL):
            try:
                data = json.loads(m.group())
                if data.get("found") and "x" in data and "y" in data:
                    return int(data["x"]), int(data["y"])
            except (json.JSONDecodeError, ValueError):
                pass
    return None


class BrowserAgent:
    """
    Browser automation using Playwright (preferred) or Selenium as fallback.
    Vision-guided element finding for robust interaction.
    """

    def __init__(
        self,
        backend: str = "auto",
        headless: bool = False,
        browser_type: str = "chromium",
        timeout: int = 30000,
        user_agent: Optional[str] = None,
    ):
        self.backend = backend
        self.headless = headless
        self.browser_type = browser_type
        self.timeout = timeout
        self.user_agent = user_agent

        self._pw = None
        self._pw_browser = None
        self._pw_context = None
        self._pw_page = None
        self._selenium_driver = None

        self._init_browser()

    def _init_browser(self) -> None:
        if self.backend in ("playwright", "auto") and _HAS_PLAYWRIGHT:
            try:
                self._pw = sync_playwright().start()
                browser_launcher = getattr(self._pw, self.browser_type, self._pw.chromium)
                self._pw_browser = browser_launcher.launch(headless=self.headless)
                ctx_kwargs: Dict = {"viewport": {"width": 1280, "height": 900}}
                if self.user_agent:
                    ctx_kwargs["user_agent"] = self.user_agent
                self._pw_context = self._pw_browser.new_context(**ctx_kwargs)
                self._pw_page = self._pw_context.new_page()
                self._pw_page.set_default_timeout(self.timeout)
                self.backend = "playwright"
                return
            except Exception:
                if self._pw:
                    try:
                        self._pw.stop()
                    except Exception:
                        pass
                    self._pw = None

        if self.backend in ("selenium", "auto") and _HAS_SELENIUM:
            try:
                opts = webdriver.ChromeOptions()
                if self.headless:
                    opts.add_argument("--headless=new")
                opts.add_argument("--no-sandbox")
                opts.add_argument("--disable-dev-shm-usage")
                opts.add_argument("--window-size=1280,900")
                if self.user_agent:
                    opts.add_argument(f"--user-agent={self.user_agent}")
                self._selenium_driver = webdriver.Chrome(options=opts)
                self._selenium_driver.implicitly_wait(self.timeout // 1000)
                self.backend = "selenium"
                return
            except Exception:
                pass

        self.backend = "none"

    # --- Navigation ---

    def navigate(self, url: str) -> str:
        if self.backend == "playwright" and self._pw_page:
            try:
                self._pw_page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
                return f"Navigated to {url}"
            except Exception as e:
                return f"ERROR: navigation failed: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                self._selenium_driver.get(url)
                return f"Navigated to {url}"
            except Exception as e:
                return f"ERROR: navigation failed: {e}"
        return "ERROR: no browser backend available"

    def get_url(self) -> str:
        if self.backend == "playwright" and self._pw_page:
            return self._pw_page.url
        if self.backend == "selenium" and self._selenium_driver:
            return self._selenium_driver.current_url
        return "ERROR: no browser"

    def get_title(self) -> str:
        if self.backend == "playwright" and self._pw_page:
            return self._pw_page.title()
        if self.backend == "selenium" and self._selenium_driver:
            return self._selenium_driver.title
        return "ERROR: no browser"

    def go_back(self) -> str:
        if self.backend == "playwright" and self._pw_page:
            try:
                self._pw_page.go_back(timeout=self.timeout)
                return "Navigated back"
            except Exception as e:
                return f"ERROR: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                self._selenium_driver.back()
                return "Navigated back"
            except Exception as e:
                return f"ERROR: {e}"
        return "ERROR: no browser"

    def go_forward(self) -> str:
        if self.backend == "playwright" and self._pw_page:
            try:
                self._pw_page.go_forward(timeout=self.timeout)
                return "Navigated forward"
            except Exception as e:
                return f"ERROR: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                self._selenium_driver.forward()
                return "Navigated forward"
            except Exception as e:
                return f"ERROR: {e}"
        return "ERROR: no browser"

    def refresh(self) -> str:
        if self.backend == "playwright" and self._pw_page:
            try:
                self._pw_page.reload(timeout=self.timeout)
                return "Page refreshed"
            except Exception as e:
                return f"ERROR: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                self._selenium_driver.refresh()
                return "Page refreshed"
            except Exception as e:
                return f"ERROR: {e}"
        return "ERROR: no browser"

    # --- Screenshot ---

    def screenshot(self, path: Optional[str] = None) -> str:
        if path is None:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                path = f.name
        if self.backend == "playwright" and self._pw_page:
            try:
                self._pw_page.screenshot(path=path, full_page=False)
                return path
            except Exception as e:
                return f"ERROR: screenshot failed: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                self._selenium_driver.save_screenshot(path)
                return path
            except Exception as e:
                return f"ERROR: screenshot failed: {e}"
        return "ERROR: no browser"

    # --- DOM interaction ---

    def click(self, selector: str) -> str:
        if self.backend == "playwright" and self._pw_page:
            try:
                self._pw_page.click(selector, timeout=self.timeout)
                return f"Clicked: {selector}"
            except Exception as e:
                return f"ERROR: click failed: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                el = WebDriverWait(self._selenium_driver, self.timeout // 1000).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                el.click()
                return f"Clicked: {selector}"
            except Exception as e:
                return f"ERROR: click failed: {e}"
        return "ERROR: no browser"

    def click_at(self, x: int, y: int) -> str:
        if self.backend == "playwright" and self._pw_page:
            try:
                self._pw_page.mouse.click(x, y)
                return f"Clicked at ({x}, {y})"
            except Exception as e:
                return f"ERROR: click_at failed: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                action = ActionChains(self._selenium_driver)
                action.move_by_offset(x, y).click().perform()
                return f"Clicked at ({x}, {y})"
            except Exception as e:
                return f"ERROR: click_at failed: {e}"
        return "ERROR: no browser"

    def type_text(self, selector: str, text: str, clear_first: bool = True) -> str:
        if self.backend == "playwright" and self._pw_page:
            try:
                if clear_first:
                    self._pw_page.fill(selector, text, timeout=self.timeout)
                else:
                    self._pw_page.type(selector, text, timeout=self.timeout)
                return f"Typed into {selector}"
            except Exception as e:
                return f"ERROR: type failed: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                el = WebDriverWait(self._selenium_driver, self.timeout // 1000).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if clear_first:
                    el.clear()
                el.send_keys(text)
                return f"Typed into {selector}"
            except Exception as e:
                return f"ERROR: type failed: {e}"
        return "ERROR: no browser"

    def press_key(self, key: str) -> str:
        if self.backend == "playwright" and self._pw_page:
            try:
                self._pw_page.keyboard.press(key)
                return f"Pressed {key}"
            except Exception as e:
                return f"ERROR: key press failed: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                ActionChains(self._selenium_driver).send_keys(key).perform()
                return f"Pressed {key}"
            except Exception as e:
                return f"ERROR: key press failed: {e}"
        return "ERROR: no browser"

    def select_option(self, selector: str, value: str) -> str:
        if self.backend == "playwright" and self._pw_page:
            try:
                self._pw_page.select_option(selector, value=value, timeout=self.timeout)
                return f"Selected {value} in {selector}"
            except Exception as e:
                return f"ERROR: select failed: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                from selenium.webdriver.support.ui import Select
                el = self._selenium_driver.find_element(By.CSS_SELECTOR, selector)
                Select(el).select_by_value(value)
                return f"Selected {value} in {selector}"
            except Exception as e:
                return f"ERROR: select failed: {e}"
        return "ERROR: no browser"

    def scroll(self, x: int = 0, y: int = 500) -> str:
        if self.backend == "playwright" and self._pw_page:
            try:
                self._pw_page.mouse.wheel(x, y)
                return f"Scrolled ({x}, {y})"
            except Exception as e:
                return f"ERROR: scroll failed: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                self._selenium_driver.execute_script(f"window.scrollBy({x}, {y})")
                return f"Scrolled ({x}, {y})"
            except Exception as e:
                return f"ERROR: scroll failed: {e}"
        return "ERROR: no browser"

    # --- Content extraction ---

    def get_text(self, selector: str = "body") -> str:
        if self.backend == "playwright" and self._pw_page:
            try:
                return self._pw_page.inner_text(selector, timeout=self.timeout)
            except Exception as e:
                return f"ERROR: get_text failed: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                el = self._selenium_driver.find_element(By.CSS_SELECTOR, selector)
                return el.text
            except Exception as e:
                return f"ERROR: get_text failed: {e}"
        return "ERROR: no browser"

    def get_html(self, selector: str = "html") -> str:
        if self.backend == "playwright" and self._pw_page:
            try:
                return self._pw_page.inner_html(selector, timeout=self.timeout)
            except Exception as e:
                return f"ERROR: get_html failed: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                el = self._selenium_driver.find_element(By.CSS_SELECTOR, selector)
                return el.get_attribute("innerHTML") or ""
            except Exception as e:
                return f"ERROR: get_html failed: {e}"
        return "ERROR: no browser"

    def get_page_source(self) -> str:
        if self.backend == "playwright" and self._pw_page:
            try:
                return self._pw_page.content()
            except Exception as e:
                return f"ERROR: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                return self._selenium_driver.page_source
            except Exception as e:
                return f"ERROR: {e}"
        return "ERROR: no browser"

    def extract_links(self) -> List[Dict]:
        html = self.get_page_source()
        if html.startswith("ERROR:"):
            return []
        if _HAS_BS4:
            soup = BeautifulSoup(html, "html.parser")
            return [
                {"text": a.get_text(strip=True), "href": a["href"]}
                for a in soup.find_all("a", href=True)
            ]
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
        return [{"href": h} for h in hrefs]

    def execute_js(self, script: str, *args) -> Any:
        if self.backend == "playwright" and self._pw_page:
            try:
                return self._pw_page.evaluate(script, *args)
            except Exception as e:
                return f"ERROR: JS execution failed: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                return self._selenium_driver.execute_script(script, *args)
            except Exception as e:
                return f"ERROR: JS execution failed: {e}"
        return "ERROR: no browser"

    # --- Vision-guided interaction ---

    def find_and_click(self, element_description: str) -> str:
        """Take screenshot, use vision AI to find element, click it."""
        shot_path = self.screenshot()
        if shot_path.startswith("ERROR:"):
            return f"ERROR: could not take screenshot: {shot_path}"
        vision_resp = _analyze_screenshot_for_element(shot_path, element_description)
        coords = _parse_element_coords(vision_resp)
        try:
            os.unlink(shot_path)
        except OSError:
            pass
        if coords:
            return self.click_at(coords[0], coords[1])
        return self._fallback_click_by_text(element_description)

    def _fallback_click_by_text(self, text: str) -> str:
        if self.backend == "playwright" and self._pw_page:
            for attempt in [
                lambda: self._pw_page.get_by_text(text).first.click(timeout=self.timeout),
                lambda: self._pw_page.get_by_role("button", name=text).click(timeout=self.timeout),
                lambda: self._pw_page.get_by_label(text).click(timeout=self.timeout),
            ]:
                try:
                    attempt()
                    return f"Clicked element: {text}"
                except Exception:
                    pass
        if self.backend == "selenium" and self._selenium_driver:
            try:
                el = self._selenium_driver.find_element(
                    By.XPATH, f"//*[contains(text(), '{text}')]"
                )
                el.click()
                return f"Clicked element: {text}"
            except Exception:
                pass
        return f"ERROR: could not find element: {text}"

    def find_and_type(self, element_description: str, text: str) -> str:
        """Take screenshot, use vision AI to find input field, type text."""
        shot_path = self.screenshot()
        if shot_path.startswith("ERROR:"):
            return f"ERROR: could not take screenshot: {shot_path}"
        vision_resp = _analyze_screenshot_for_element(
            shot_path, element_description, context="input field"
        )
        coords = _parse_element_coords(vision_resp)
        try:
            os.unlink(shot_path)
        except OSError:
            pass
        if coords:
            x, y = coords
            result = self.click_at(x, y)
            if result.startswith("ERROR:"):
                return result
            time.sleep(0.2)
            if self.backend == "playwright" and self._pw_page:
                try:
                    self._pw_page.keyboard.type(text)
                    return f"Typed into element at ({x}, {y})"
                except Exception as e:
                    return f"ERROR: type failed: {e}"
        return f"ERROR: could not find input: {element_description}"

    def wait_for(self, selector: str, timeout: Optional[int] = None) -> str:
        t = timeout or self.timeout
        if self.backend == "playwright" and self._pw_page:
            try:
                self._pw_page.wait_for_selector(selector, timeout=t)
                return f"Element appeared: {selector}"
            except Exception as e:
                return f"ERROR: wait_for failed: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                WebDriverWait(self._selenium_driver, t // 1000).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                return f"Element appeared: {selector}"
            except Exception as e:
                return f"ERROR: wait_for failed: {e}"
        return "ERROR: no browser"

    def wait_for_navigation(self, timeout: Optional[int] = None) -> str:
        t = timeout or self.timeout
        if self.backend == "playwright" and self._pw_page:
            try:
                self._pw_page.wait_for_load_state("networkidle", timeout=t)
                return "Navigation complete"
            except Exception as e:
                return f"ERROR: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            time.sleep(2)
            return "Navigation complete (approximated)"
        return "ERROR: no browser"

    # --- Tabs ---

    def new_tab(self, url: Optional[str] = None) -> str:
        if self.backend == "playwright" and self._pw_context:
            try:
                page = self._pw_context.new_page()
                self._pw_page = page
                if url:
                    page.goto(url, timeout=self.timeout)
                return f"Opened new tab{' to ' + url if url else ''}"
            except Exception as e:
                return f"ERROR: new tab failed: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                self._selenium_driver.execute_script("window.open('');")
                self._selenium_driver.switch_to.window(self._selenium_driver.window_handles[-1])
                if url:
                    self._selenium_driver.get(url)
                return f"Opened new tab{' to ' + url if url else ''}"
            except Exception as e:
                return f"ERROR: new tab failed: {e}"
        return "ERROR: no browser"

    # --- Cookies ---

    def get_cookies(self) -> List[Dict]:
        if self.backend == "playwright" and self._pw_context:
            try:
                return self._pw_context.cookies()
            except Exception:
                return []
        if self.backend == "selenium" and self._selenium_driver:
            try:
                return self._selenium_driver.get_cookies()
            except Exception:
                return []
        return []

    def set_cookie(self, name: str, value: str, domain: str = "") -> str:
        if self.backend == "playwright" and self._pw_context:
            try:
                cookie: Dict = {"name": name, "value": value}
                if domain:
                    cookie["domain"] = domain
                self._pw_context.add_cookies([cookie])
                return f"Set cookie: {name}"
            except Exception as e:
                return f"ERROR: {e}"
        if self.backend == "selenium" and self._selenium_driver:
            try:
                cookie = {"name": name, "value": value}
                if domain:
                    cookie["domain"] = domain
                self._selenium_driver.add_cookie(cookie)
                return f"Set cookie: {name}"
            except Exception as e:
                return f"ERROR: {e}"
        return "ERROR: no browser"

    # --- Cleanup ---

    def close(self) -> str:
        try:
            if self._pw_page:
                self._pw_page.close()
            if self._pw_context:
                self._pw_context.close()
            if self._pw_browser:
                self._pw_browser.close()
            if self._pw:
                self._pw.stop()
            if self._selenium_driver:
                self._selenium_driver.quit()
            return "Browser closed"
        except Exception as e:
            return f"ERROR: close failed: {e}"

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def status(self) -> str:
        lines = [f"Browser Agent ({self.backend}):"]
        if self.backend == "none":
            lines.append("  No backend available. Install playwright or selenium.")
        else:
            try:
                lines.append(f"  URL: {self.get_url()}")
                lines.append(f"  Title: {self.get_title()}")
            except Exception:
                lines.append("  Browser open (no active page)")
        return "\n".join(lines)


_browser_instance: Optional[BrowserAgent] = None


def get_browser_agent(**kwargs) -> BrowserAgent:
    global _browser_instance
    if _browser_instance is None:
        _browser_instance = BrowserAgent(**kwargs)
    return _browser_instance


def browser_navigate(url: str) -> str:
    return get_browser_agent().navigate(url)


def browser_screenshot(path: Optional[str] = None) -> str:
    return get_browser_agent().screenshot(path)


def browser_click(selector: str) -> str:
    return get_browser_agent().click(selector)


def browser_type(selector: str, text: str) -> str:
    return get_browser_agent().type_text(selector, text)


def browser_get_text(selector: str = "body") -> str:
    return get_browser_agent().get_text(selector)


def browser_find_and_click(description: str) -> str:
    return get_browser_agent().find_and_click(description)


def browser_execute_js(script: str) -> Any:
    return get_browser_agent().execute_js(script)
