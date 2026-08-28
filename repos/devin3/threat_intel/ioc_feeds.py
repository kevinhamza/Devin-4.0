# Devin/threat_intel/ioc_feeds.py
# Purpose: A manager for downloading, caching, and querying open-source
#          Indicator of Compromise (IOC) feeds.

import logging
import requests
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
import pandas as pd

# Configure basic logging
logger = logging.getLogger("IOCFeedManager")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

# --- Default Feed Definitions ---
# A curated list of reputable, free threat intelligence feeds.
DEFAULT_FEEDS = {
    "ip": [
        {
            "name": "FeodoTracker_IP_Blocklist",
            "url": "https://feodotracker.abuse.ch/downloads/ipblocklist.csv",
            "format": "csv",
            "comment_char": "#",
            "column": "dst_ip"
        }
    ],
    "domain": [
        {
            "name": "URLhaus_Malicious_URLs",
            "url": "https://urlhaus.abuse.ch/downloads/csv_online/",
            "format": "csv",
            "comment_char": "#",
            "column": "url" # We will parse the domain from this
        }
    ],
    "hash": [] # MD5, SHA1, SHA256
}

class IOCManager:
    """
    Manages a local, queryable database of IOCs from various feeds.
    """
    def __init__(self, cache_dir: str = "intel_cache", cache_duration_hours: int = 24):
        self.cache_path = Path(cache_dir)
        self.cache_path.mkdir(exist_ok=True)
        self.cache_duration_sec = cache_duration_hours * 3600
        
        self.malicious_ips: Set[str] = set()
        self.malicious_domains: Set[str] = set()
        self.malicious_hashes: Set[str] = set()
        logger.info("IOCManager initialized.")

    def _fetch_and_cache(self, feed_name: str, url: str) -> Optional[Path]:
        """Downloads a feed if the local cache is stale or missing."""
        feed_cache_path = self.cache_path / f"{feed_name}.feed"
        
        if feed_cache_path.exists():
            if time.time() - feed_cache_path.stat().st_mtime < self.cache_duration_sec:
                logger.debug(f"Using recent cache for feed '{feed_name}'.")
                return feed_cache_path
        
        logger.info(f"Fetching fresh feed for '{feed_name}' from {url}...")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            feed_cache_path.write_text(response.text, encoding='utf-8')
            return feed_cache_path
        except requests.RequestException as e:
            logger.error(f"Failed to download feed '{feed_name}': {e}")
            return None

    def load_feeds(self, feed_definitions: Dict = DEFAULT_FEEDS):
        """Loads all defined feeds into the in-memory database."""
        for ioc_type, feeds in feed_definitions.items():
            for feed in feeds:
                feed_path = self._fetch_and_cache(feed['name'], feed['url'])
                if not feed_path: continue

                try:
                    df = pd.read_csv(feed_path, comment=feed.get('comment_char'), on_bad_lines='skip')
                    
                    if feed['column'] not in df.columns:
                        logger.warning(f"Column '{feed['column']}' not in feed '{feed['name']}'. Skipping.")
                        continue
                        
                    iocs = df[feed['column']].dropna().astype(str).tolist()
                    
                    if ioc_type == 'ip':
                        self.malicious_ips.update(iocs)
                    elif ioc_type == 'hash':
                        self.malicious_hashes.update(iocs)
                    elif ioc_type == 'domain':
                        # Special handling for URLs to extract just the domain
                        from urllib.parse import urlparse
                        domains = {urlparse(ioc).netloc for ioc in iocs if urlparse(ioc).netloc}
                        self.malicious_domains.update(domains)
                        
                except Exception as e:
                    logger.error(f"Failed to parse feed '{feed['name']}': {e}")
        
        logger.info(f"Feeds loaded. Total IOCs: {len(self.malicious_ips)} IPs, {len(self.malicious_domains)} domains, {len(self.malicious_hashes)} hashes.")

    def is_ip_malicious(self, ip_address: str) -> bool:
        """Checks if an IP address is in the malicious database."""
        return ip_address in self.malicious_ips

    def is_domain_malicious(self, domain: str) -> bool:
        """Checks if a domain is in the malicious database."""
        return domain in self.malicious_domains

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== IOC Feed Manager Demo ⚔️ ===")
    print("=========================================================")
    
    try:
        manager = IOCManager()
        manager.load_feeds()
        
        if manager.malicious_ips and manager.malicious_domains:
            # --- Test IP Addresses ---
            print("\n--- Checking IP Addresses ---")
            known_good_ip = "8.8.8.8"
            known_bad_ip = list(manager.malicious_ips)[0] # Get a real one from the feed
            
            print(f"  Checking known-good IP '{known_good_ip}': Malicious = {manager.is_ip_malicious(known_good_ip)}")
            print(f"  Checking known-bad IP '{known_bad_ip}': Malicious = {manager.is_ip_malicious(known_bad_ip)}")

            # --- Test Domains ---
            print("\n--- Checking Domains ---")
            known_good_domain = "google.com"
            known_bad_domain = list(manager.malicious_domains)[0] # Get a real one from the feed
            
            print(f"  Checking known-good domain '{known_good_domain}': Malicious = {manager.is_domain_malicious(known_good_domain)}")
            print(f"  Checking known-bad domain '{known_bad_domain}': Malicious = {manager.is_domain_malicious(known_bad_domain)}")

    except Exception as e:
        logger.error(f"Demo failed to run. Check your internet connection. Error: {e}", exc_info=True)

    print("\n=========================================================")
    print("=== IOC Feed Manager Demo Complete ===")
    print("=========================================================")
