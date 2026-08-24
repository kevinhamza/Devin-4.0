# Devin/modules/reality_xr_tools.py
# Purpose: A high-level facade that orchestrates Devin's "reality engine" tools
#          (clear-web crawling/scraping, geolocation, local IoT control, and
#          authorized dark-web/OSINT monitoring) into one cohesive interface
#          for the AGI.

import logging
import os
from typing import Any, Dict, List, Optional

# --- Import the low-level reality-engine tools this facade will manage ---
from reality_engine.web_crawler.web_crawler import WebCrawler
from reality_engine.web_crawler.ai_governed_scraper import AIGovernedScraper
from reality_engine.physical_world.satellite_api import SatelliteAPI
from reality_engine.physical_world.iot_controller import IoTController, TINUTUYA_AVAILABLE
from reality_engine.web_crawler.darkweb_crawler import DarkWebCrawler

# Configure basic logging
logger = logging.getLogger("RealityEngineFacade")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False


class RealityEngineFacade:
    """
    A single, simplified interface to Devin's clear-web, physical-world, and
    (authorized) dark-web reconnaissance toolchain.

    Every underlying tool degrades gracefully: if an optional dependency is
    missing, or an external service/daemon isn't running, the corresponding
    method logs a warning and returns None/raises a clear error rather than
    taking down the whole facade (and, via main.py, the whole assistant).
    """

    def __init__(self, iot_config_path: Optional[str] = None):
        """
        Initializes all underlying reality-engine tools.

        Args:
            iot_config_path (Optional[str]): Path to the Tuya IoT device
                credentials JSON file (see IoTController). Defaults to
                'devices.json' in the current working directory if not given.
        """
        # --- Clear-web crawler (requires beautifulsoup4) ---
        self.web_crawler: Optional[WebCrawler] = None
        try:
            self.web_crawler = WebCrawler()
        except ImportError as e:
            logger.warning(f"WebCrawler unavailable: {e}")

        # --- AI-governed structured scraper (requires beautifulsoup4 + openai + OPENAI_API_KEY) ---
        # ai_governed_scraper.AIGovernedScraper.__init__ calls os.getenv() without
        # importing 'os' when no explicit key is passed, which raises a NameError
        # instead of the intended ValueError whenever OPENAI_API_KEY isn't set.
        # We are not directly fixing that file (out of scope for this facade), so
        # we catch broadly here -- any failure to construct it just means the
        # AI-governed scraping capability is unavailable, same as a missing key.
        self.ai_scraper: Optional[AIGovernedScraper] = None
        try:
            self.ai_scraper = AIGovernedScraper(openai_api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            logger.warning(f"AIGovernedScraper unavailable: {e}")

        # --- Geolocation / satellite API client (requires geopy) ---
        self.satellite_api: Optional[SatelliteAPI] = None
        try:
            self.satellite_api = SatelliteAPI()
        except ImportError as e:
            logger.warning(f"SatelliteAPI unavailable: {e}")

        # --- Local IoT (Tuya) controller (requires tinytuya + a devices.json) ---
        self.iot_controller: Optional[IoTController] = None
        try:
            from pathlib import Path
            cfg = Path(iot_config_path) if iot_config_path else Path("devices.json")
            self.iot_controller = IoTController(config_path=cfg)
        except ImportError as e:
            logger.warning(f"IoTController unavailable: {e}")

        # --- Dark-web crawler (requires stem + requests[socks] + a local Tor daemon) ---
        # AUTHORIZED USE ONLY. See crawl_dark_web_page()/check_dark_web_tor_connection()
        # docstrings below. This will simply fail to construct/connect when no local
        # Tor SOCKS proxy (127.0.0.1:9050) is running, which is the expected case in
        # most environments -- that is treated as "unavailable", not an error.
        self.darkweb_crawler: Optional[DarkWebCrawler] = None
        try:
            self.darkweb_crawler = DarkWebCrawler()
        except ImportError as e:
            logger.warning(f"DarkWebCrawler unavailable: {e}")

        logger.info("RealityEngineFacade initialized.")

    # ------------------------------------------------------------------
    # Clear-web crawling & scraping
    # ------------------------------------------------------------------

    def crawl_website(self, start_url: str, max_pages: int = 25, num_workers: int = 4) -> List[Dict[str, Any]]:
        """
        Politely, multi-threadedly crawls a public website starting at start_url,
        respecting robots.txt and staying within the site's domain.

        Args:
            start_url (str): The URL to start crawling from (e.g. "https://example.com/").
            max_pages (int): Maximum number of unique pages to visit.
            num_workers (int): Number of concurrent fetch threads.

        Returns:
            List[Dict[str, Any]]: One entry per crawled page: {"url": str, "title": str, "text": str}.
        """
        if not self.web_crawler:
            logger.error("crawl_website called but WebCrawler is unavailable.")
            return []

        results: List[Dict[str, Any]] = []
        for url, soup in self.web_crawler.crawl(start_url, max_pages=max_pages, num_workers=num_workers):
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            text = " ".join(soup.get_text(separator=" ").split())
            results.append({"url": url, "title": title, "text": text[:5000]})
        return results

    def extract_structured_data(self, url: str, data_schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Uses an LLM to scrape a single webpage and extract structured data
        matching a caller-supplied JSON schema (e.g. product listings, article
        metadata). Requires OPENAI_API_KEY to be set.

        Args:
            url (str): The page to scrape.
            data_schema (Dict[str, Any]): A JSON-schema-like dict describing the
                shape of the data to extract (see AIGovernedScraper for examples).

        Returns:
            Optional[Dict[str, Any]]: The extracted data, or None on failure.
        """
        if not self.ai_scraper:
            logger.error("extract_structured_data called but AIGovernedScraper is unavailable (missing openai/bs4 or OPENAI_API_KEY).")
            return None
        return self.ai_scraper.extract_structured_data(url, data_schema)

    # ------------------------------------------------------------------
    # Physical-world geolocation
    # ------------------------------------------------------------------

    def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Converts a physical address to latitude/longitude coordinates."""
        if not self.satellite_api:
            logger.error("geocode_address called but SatelliteAPI is unavailable (missing geopy).")
            return None
        return self.satellite_api.geocode_address(address)

    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Converts latitude/longitude coordinates to a physical address."""
        if not self.satellite_api:
            logger.error("reverse_geocode called but SatelliteAPI is unavailable (missing geopy).")
            return None
        return self.satellite_api.reverse_geocode(latitude, longitude)

    def get_iss_location(self) -> Optional[Dict[str, Any]]:
        """Gets the current real-time location of the International Space Station."""
        if not self.satellite_api:
            logger.error("get_iss_location called but SatelliteAPI is unavailable (missing geopy).")
            return None
        return self.satellite_api.get_iss_location()

    def geolocate_ip_address(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Gets the approximate geolocation (city/country/ISP) of a public IP address."""
        if not self.satellite_api:
            logger.error("geolocate_ip_address called but SatelliteAPI is unavailable (missing geopy).")
            return None
        return self.satellite_api.geocode_ip_address(ip_address)

    # ------------------------------------------------------------------
    # Local IoT device control (Tuya)
    # ------------------------------------------------------------------

    def discover_iot_devices(self, scan_duration_sec: int = 10) -> str:
        """
        Scans the local network for Tuya smart-home devices and logs what it finds
        (IP, device ID, product key, protocol version) so they can be added to the
        IoT config file. This is a broadcast/UDP scan of the local LAN only.

        Args:
            scan_duration_sec (int): How long to listen for device broadcasts.

        Returns:
            str: A human-readable status message (details are logged).
        """
        if not TINUTUYA_AVAILABLE:
            return "IoT discovery is unavailable: the 'tinytuya' library is not installed."
        IoTController.discover_devices(scan_duration=scan_duration_sec)
        return f"Discovery scan completed ({scan_duration_sec}s). See logs for discovered devices."

    def get_iot_device_status(self, device_name: str) -> Optional[Dict[str, Any]]:
        """Gets the full status of a configured local IoT device by its configured name."""
        if not self.iot_controller:
            logger.error("get_iot_device_status called but IoTController is unavailable (missing tinytuya).")
            return None
        return self.iot_controller.get_status(device_name)

    def set_iot_device_power(self, device_name: str, turn_on: bool) -> str:
        """
        Turns a configured local IoT device (outlet, switch, bulb) on or off.

        Args:
            device_name (str): The device's name as configured in the IoT config file.
            turn_on (bool): True to turn the device on, False to turn it off.
        """
        if not self.iot_controller:
            return "IoTController is unavailable (missing tinytuya)."
        if turn_on:
            self.iot_controller.turn_on(device_name)
            return f"Sent ON command to '{device_name}'."
        else:
            self.iot_controller.turn_off(device_name)
            return f"Sent OFF command to '{device_name}'."

    def set_iot_bulb_color(self, device_name: str, r: int, g: int, b: int) -> str:
        """Sets the RGB color of a configured smart bulb (0-255 per channel)."""
        if not self.iot_controller:
            return "IoTController is unavailable (missing tinytuya)."
        self.iot_controller.set_color(device_name, r, g, b)
        return f"Sent color ({r},{g},{b}) command to '{device_name}'."

    # ------------------------------------------------------------------
    # Dark-web / Tor monitoring -- AUTHORIZED OSINT / THREAT-INTEL ONLY
    # ------------------------------------------------------------------
    #
    # These methods exist for defensive, authorized use cases such as monitoring
    # known breach/leak/paste sites for mentions of an organization's own assets
    # (domains, credentials, brand names) as part of threat-intelligence work.
    # They are NOT for open-ended browsing of arbitrary .onion links. The caller
    # must always supply the exact target URL explicitly -- this facade defines
    # no default target and will not suggest or wander to other onion sites.
    #
    # Requires a local Tor daemon exposing a SOCKS proxy on 127.0.0.1:9050 (and,
    # for identity renewal, a control port on 9051). Most environments will not
    # have Tor running, in which case these methods fail closed (return an error
    # message / empty results) rather than raising.

    def check_dark_web_tor_connection(self) -> Dict[str, Any]:
        """
        AUTHORIZED THREAT-INTEL USE ONLY. Verifies whether a local Tor SOCKS proxy
        (127.0.0.1:9050) is reachable, without crawling anything. Useful as a
        pre-flight check before attempting crawl_dark_web_page(). Requires the
        caller to flag this tool `is_dangerous=True` when registered, since it
        exercises the Tor network stack.

        Returns:
            Dict[str, Any]: {"available": bool, "connected": bool, "message": str}.
        """
        if not self.darkweb_crawler:
            return {"available": False, "connected": False, "message": "DarkWebCrawler is unavailable (missing stem/requests[socks], or Tor not running)."}
        connected = self.darkweb_crawler.check_connection()
        return {"available": True, "connected": connected, "message": "Tor connection verified." if connected else "Tor proxy not reachable at 127.0.0.1:9050."}

    def crawl_dark_web_page(self, onion_url: str, max_pages: int = 5) -> List[Dict[str, str]]:
        """
        AUTHORIZED THREAT-INTEL / OSINT USE ONLY -- e.g. monitoring a known
        breach-data or leak-paste .onion site for mentions of an organization's
        own domains/credentials as part of sanctioned security monitoring. This
        is NOT a general-purpose dark-web browser: it only ever visits the exact
        onion_url the caller supplies (and same-domain links found on it) --
        there is no default target and it will not be used to explore arbitrary
        or unknown onion sites.

        Requires a local Tor daemon (SOCKS proxy on 127.0.0.1:9050). If Tor is
        not running -- the common case in most environments -- this returns an
        empty list rather than raising. The caller MUST flag this tool
        `is_dangerous=True` when registering it as an agent tool.

        Args:
            onion_url (str): The exact .onion URL to crawl (must be supplied by
                the caller; there is no default).
            max_pages (int): Maximum number of pages to visit on that .onion domain.

        Returns:
            List[Dict[str, str]]: One entry per crawled page: {"url": str, "title": str, "text": str}.
        """
        if not self.darkweb_crawler:
            logger.error("crawl_dark_web_page called but DarkWebCrawler is unavailable (missing deps or Tor not running).")
            return []
        if ".onion" not in onion_url:
            logger.error("crawl_dark_web_page requires a .onion URL.")
            return []

        results: List[Dict[str, str]] = []
        for url, soup in self.darkweb_crawler.crawl(onion_url, max_pages=max_pages):
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            text = " ".join(soup.get_text(separator=" ").split())
            results.append({"url": url, "title": title, "text": text[:5000]})
        return results

    def renew_dark_web_tor_identity(self) -> str:
        """
        AUTHORIZED THREAT-INTEL USE ONLY. Requests a new Tor circuit (new exit
        IP) from the local Tor control port. Only needed for sustained,
        authorized monitoring sessions (e.g. rotating identity between batches
        of leak-site checks). Requires the local Tor control port (9051) to be
        enabled with the configured control_password. The caller MUST flag this
        tool `is_dangerous=True` when registering it as an agent tool.

        Returns:
            str: A human-readable status message.
        """
        if not self.darkweb_crawler:
            return "DarkWebCrawler is unavailable (missing deps or Tor not running)."
        try:
            self.darkweb_crawler.renew_tor_identity()
            return "Requested a new Tor identity (see logs for the resulting exit IP)."
        except Exception as e:
            logger.error(f"Failed to renew Tor identity: {e}")
            return f"Failed to renew Tor identity: {e}"


# --- Example Usage ---
if __name__ == "__main__":
    import json
    print("=========================================================")
    print("=== Reality Engine / XR Reconnaissance Facade Demo ===")
    print("=========================================================")

    facade = RealityEngineFacade()

    print("\n--- ISS Location ---")
    print(json.dumps(facade.get_iss_location(), indent=2))

    print("\n--- Dark-web Tor connection check (expected unavailable in most sandboxes) ---")
    print(json.dumps(facade.check_dark_web_tor_connection(), indent=2))

    print("\n=========================================================")
    print("=== Demo Complete ===")
    print("=========================================================")
