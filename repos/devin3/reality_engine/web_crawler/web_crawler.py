# Devin/reality_engine/web_crawler/web_crawler.py
# Purpose: A high-performance, multi-threaded, and polite web crawler for
#          mapping and scraping websites on the clear web.

import logging
import requests
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
import threading

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("WebCrawler")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class WebCrawler:
    """
    A polite, multi-threaded web crawler.
    """
    def __init__(self, user_agent: str = "Devin-WebCrawler/1.0", request_delay_sec: float = 1.0):
        if not BS4_AVAILABLE:
            raise ImportError("BeautifulSoup4 is required. 'pip install beautifulsoup4'")
        
        self.user_agent = user_agent
        self.headers = {'User-Agent': self.user_agent}
        self.request_delay = request_delay_sec
        
        self.robot_parser = RobotFileParser()
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        self.visited_urls = set()
        self.lock = threading.Lock()

    def _fetch_page(self, url: str) -> tuple[str, str, bool]:
        """Fetches a single page and returns its URL, content, and success status."""
        time.sleep(self.request_delay) # Rate limiting
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return url, response.text, True
            else:
                logger.warning(f"Failed to fetch {url} with status code {response.status_code}")
                return url, "", False
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return url, "", False

    def crawl(self, start_url: str, max_pages: int = 50, num_workers: int = 4):
        """
        Crawls a website starting from a given URL.

        Yields:
            A tuple of (url, soup_object) for each successfully crawled page.
        """
        base_url = f"{urlparse(start_url).scheme}://{urlparse(start_url).netloc}"
        
        # Fetch and parse robots.txt
        robots_url = urljoin(base_url, "robots.txt")
        try:
            self.robot_parser.set_url(robots_url)
            self.robot_parser.read()
            logger.info(f"Successfully read robots.txt from {robots_url}")
        except Exception as e:
            logger.warning(f"Could not read or parse robots.txt: {e}")

        urls_to_visit = deque([start_url])
        self.visited_urls = {start_url}

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(self._fetch_page, start_url)}
            
            while futures and len(self.visited_urls) < max_pages:
                for future in as_completed(futures):
                    url, content, success = future.result()
                    futures.remove(future)

                    if success:
                        soup = BeautifulSoup(content, 'html.parser')
                        yield (url, soup)

                        # Find new links to add to the queue
                        new_links_found = 0
                        for link in soup.find_all('a', href=True):
                            full_url = urljoin(base_url, link['href']).split('#')[0] # Remove fragments
                            
                            with self.lock:
                                # Check scope, robots.txt, and if already visited
                                if urlparse(full_url).netloc == urlparse(base_url).netloc and \
                                   self.robot_parser.can_fetch(self.user_agent, full_url) and \
                                   full_url not in self.visited_urls:
                                    
                                    self.visited_urls.add(full_url)
                                    urls_to_visit.append(full_url)
                                    new_links_found += 1

                        logger.info(f"Parsed {url}, found {new_links_found} new links.")

                    # Replenish the futures pool
                    while urls_to_visit and len(futures) < num_workers and len(self.visited_urls) + len(futures) < max_pages:
                        next_url = urls_to_visit.popleft()
                        futures.add(executor.submit(self._fetch_page, next_url))
                    
                    # Break the inner loop to process newly added futures
                    break
        
        logger.warning(f"Crawl finished. Visited {len(self.visited_urls)} unique pages.")


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== High-Performance Web Crawler Prototype 🕸️🚀 ===")
    print("=========================================================")

    try:
        crawler = WebCrawler(num_workers=5)
        
        # Use 'books.toscrape.com', a website designed for web scraping practice.
        start_url = "http://books.toscrape.com/"
        
        print(f"Starting crawl of '{start_url}' (max 25 pages)...")
        
        crawled_count = 0
        for url, soup in crawler.crawl(start_url, max_pages=25):
            crawled_count += 1
            title = soup.title.string.strip() if soup.title else "No Title"
            print(f"  [{crawled_count:02d}] Crawled: {url}  (Title: {title})")

    except ImportError as e:
        logger.error(f"Initialization failed: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

    print("\n=========================================================")
    print("=== Web Crawler Prototype Complete ===")
    print("=========================================================")
