# Devin/reality_engine/web_crawler/darkweb_crawler.py
# Purpose: A robust web crawler for the Tor network, capable of scraping
#          .onion sites and managing its Tor identity.

import logging
import requests
import time
from urllib.parse import urljoin, urlparse

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from stem import Signal
    from stem.control import Controller
    STEM_AVAILABLE = True
except ImportError:
    STEM_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("DarkWebCrawler")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class DarkWebCrawler:
    """
    Crawls websites on the Tor network via a local SOCKS proxy.
    """
    def __init__(self, tor_proxy: str = "socks5h://127.0.0.1:9050", control_port: int = 9051, control_password: str = None):
        if not all([BS4_AVAILABLE, STEM_AVAILABLE, 'requests' in sys.modules]):
            raise ImportError("Required libraries missing. 'pip install beautifulsoup4 stem \"requests[socks]\"'")

        self.proxies = {'http': tor_proxy, 'https': tor_proxy}
        self.control_port = control_port
        self.control_password = control_password
        self.session = requests.Session()
        self.session.proxies = self.proxies

    def _get_tor_controller(self) -> Optional[Controller]:
        """Connects to the Tor control port."""
        try:
            controller = Controller.from_port(port=self.control_port)
            controller.authenticate(password=self.control_password)
            logger.info("Successfully connected to Tor control port.")
            return controller
        except Exception as e:
            logger.error(f"Failed to connect to Tor control port on port {self.control_port}. Is Tor running with it enabled? Error: {e}")
            return None

    def renew_tor_identity(self):
        """Requests a new Tor circuit, effectively changing the exit IP."""
        logger.warning("Requesting new Tor identity (new exit IP)...")
        with self._get_tor_controller() as controller:
            if controller:
                controller.signal(Signal.NEWNYM)
                logger.info("NEWNYM signal sent. Tor identity should be renewed.")
                time.sleep(controller.get_newnym_wait()) # Wait for the new circuit
                self.check_connection()

    def check_connection(self) -> bool:
        """Verifies the Tor connection and prints the current exit IP."""
        logger.info("Checking Tor connection...")
        try:
            # check.torproject.org is designed for this, but can be slow.
            # We use a faster alternative.
            response = self.session.get("https://api.ipify.org?format=json", timeout=30)
            ip = response.json()['ip']
            logger.warning(f"Tor connection is active. Current Exit IP: {ip}")
            return True
        except Exception as e:
            logger.error(f"Tor connection check failed. Is the Tor proxy running at {self.proxies['http']}? Error: {e}")
            return False

    def crawl(self, start_url: str, max_pages: int = 10):
        """
        Crawls a .onion site starting from a given URL.

        Yields:
            A tuple of (url, page_content_as_text) for each successfully crawled page.
        """
        if not ".onion" in start_url:
            logger.error("This crawler is intended for .onion sites.")
            return

        urls_to_visit = [start_url]
        visited_urls = set()
        pages_crawled = 0

        while urls_to_visit and pages_crawled < max_pages:
            url = urls_to_visit.pop(0)
            if url in visited_urls:
                continue
            
            logger.info(f"Crawling: {url}")
            try:
                response = self.session.get(url, timeout=60)
                response.raise_for_status()
                visited_urls.add(url)
                pages_crawled += 1

                soup = BeautifulSoup(response.text, 'html.parser')
                yield (url, soup)

                # Find new links to crawl
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # Handle relative links and ensure we stay on the same .onion domain
                    full_url = urljoin(url, href)
                    if urlparse(full_url).netloc == urlparse(start_url).netloc:
                        if full_url not in visited_urls:
                            urls_to_visit.append(full_url)

            except requests.RequestException as e:
                logger.error(f"Failed to fetch {url}: {e}")
                # Optional: Add logic to renew identity after several failures
                # self.renew_tor_identity()

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Dark Web Crawler Prototype 🕸️🛡️ ===")
    print("=========================================================")
    print("!!! PREREQUISITE: This tool requires the Tor Browser (or a standalone Tor client) to be running. !!!")
    
    try:
        crawler = DarkWebCrawler()
        
        # 1. Check Tor connection
        if crawler.check_connection():
            # 2. Crawl a well-known, safe .onion site (DuckDuckGo's onion service)
            # Do NOT use random .onion links you find.
            start_onion_url = "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/"
            print(f"\nStarting crawl of '{start_onion_url}'...")
            
            crawled_pages = 0
            for url, soup in crawler.crawl(start_onion_url, max_pages=5):
                crawled_pages += 1
                title = soup.title.string if soup.title else "No Title"
                print(f"  - Successfully crawled page #{crawled_pages}: '{title.strip()}'")

            print(f"\nCrawl complete. Visited {crawled_pages} pages.")
            
    except ImportError as e:
        logger.error(f"Initialization failed: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


    print("\n=========================================================")
    print("=== Dark Web Crawler Prototype Complete ===")
    print("=========================================================")
