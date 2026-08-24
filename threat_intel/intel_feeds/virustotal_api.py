# Devin/threat_intel/intel_feeds/virustotal_api.py
# Purpose: A robust client for the VirusTotal v3 API to gather real-time
#          threat intelligence on files, URLs, domains, and IPs.

import logging
import requests
import os
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import base64

# Configure basic logging
logger = logging.getLogger("VirusTotalClient")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

# --- Dataclasses for Structured Reports ---
@dataclass
class VTReport:
    """Base class for a VirusTotal report."""
    permalink: str
    scan_date: Optional[str]
    positives: int
    total: int
    raw_data: Dict[str, Any] = field(repr=False)

    @property
    def is_malicious(self) -> bool:
        return self.positives > 0

@dataclass
class FileReport(VTReport):
    sha256: str
    md5: str
    names: List[str]

@dataclass
class URLReport(VTReport):
    url: str

class VirusTotalClient:
    """
    A thread-safe, rate-limited client for the VirusTotal v3 API.
    """
    API_BASE_URL = "https://www.virustotal.com/api/v3"
    
    # Public API allows 4 requests per minute
    REQUEST_INTERVAL_SECONDS = 15.1

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("VIRUSTOTAL_API_KEY")
        if not self.api_key:
            raise ValueError("VirusTotal API key not provided or found in VIRUSTOTAL_API_KEY environment variable.")
        
        self.headers = {"x-apikey": self.api_key}
        self.last_request_time = 0
        self.rate_limit_lock = threading.Lock()

    def _make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Handles rate limiting, request execution, and basic error handling."""
        with self.rate_limit_lock:
            elapsed = time.monotonic() - self.last_request_time
            if elapsed < self.REQUEST_INTERVAL_SECONDS:
                sleep_time = self.REQUEST_INTERVAL_SECONDS - elapsed
                logger.debug(f"Rate limiting active. Sleeping for {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
            
            self.last_request_time = time.monotonic()

        try:
            response = requests.get(f"{self.API_BASE_URL}{endpoint}", headers=self.headers)
            if response.status_code == 429:
                logger.error("Rate limit exceeded. Please wait before making another request.")
                return None
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Resource not found at endpoint '{endpoint}'. It may not have been scanned before.")
            else:
                logger.error(f"HTTP error during VirusTotal request to '{endpoint}': {e}")
            return None
        except requests.RequestException as e:
            logger.error(f"Network error during VirusTotal request: {e}")
            return None

    def get_file_report(self, file_hash: str) -> Optional[FileReport]:
        """Retrieves the report for a given file hash (SHA256, SHA1, or MD5)."""
        logger.info(f"Querying VirusTotal for file hash: {file_hash}")
        data = self._make_request(f"/files/{file_hash}")
        if not data or 'data' not in data:
            return None
            
        attrs = data['data']['attributes']
        stats = attrs.get('last_analysis_stats', {})
        return FileReport(
            sha256=attrs.get('sha256'), md5=attrs.get('md5'),
            names=attrs.get('names', []),
            positives=stats.get('malicious', 0) + stats.get('suspicious', 0),
            total=sum(stats.values()),
            scan_date=attrs.get('last_analysis_date'),
            permalink=f"https://www.virustotal.com/gui/file/{attrs.get('sha256')}",
            raw_data=attrs
        )

    def get_url_report(self, url: str) -> Optional[URLReport]:
        """Retrieves the report for a given URL."""
        # VT API requires a specific URL identifier, which is the base64 encoded URL
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        logger.info(f"Querying VirusTotal for URL: {url}")
        data = self._make_request(f"/urls/{url_id}")
        if not data or 'data' not in data:
            return None
            
        attrs = data['data']['attributes']
        stats = attrs.get('last_analysis_stats', {})
        return URLReport(
            url=attrs.get('url'),
            positives=stats.get('malicious', 0) + stats.get('suspicious', 0),
            total=sum(stats.values()),
            scan_date=attrs.get('last_analysis_date'),
            permalink=f"https://www.virustotal.com/gui/url/{url_id}",
            raw_data=attrs
        )

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== VirusTotal Threat Intelligence Client Demo 🔬 ===")
    print("=========================================================")
    
    if not os.getenv("VIRUSTOTAL_API_KEY"):
        print("\nERROR: VIRUSTOTAL_API_KEY environment variable not set.")
        print("Please get a free API key from virustotal.com and set the environment variable.")
    else:
        client = VirusTotalClient()
        
        # --- 1. Look up a known malicious file hash (WannaCry) ---
        print("\n--- 1. Looking up a known MALICIOUS file hash (WannaCry ransomware) ---")
        wannacry_hash = "ed01ebfbc9eb5bbea545af4d01bf5f1071661840480439c6e5babe8e080e41aa"
        report = client.get_file_report(wannacry_hash)
        if report:
            print(f"  Malicious: {report.is_malicious}")
            print(f"  Detections: {report.positives} / {report.total}")
            print(f"  Common Name: {report.names[0] if report.names else 'N/A'}")
            print(f"  Link: {report.permalink}")
        
        time.sleep(1) # Add a small delay for clarity in output
        
        # --- 2. Look up a known safe file hash (putty.exe) ---
        print("\n--- 2. Looking up a known SAFE file hash (putty.exe) ---")
        putty_hash = "a3b3c88b4b5a3e14138612196194242642a8b3e83b3427f32fbf222a7d2b271d"
        report = client.get_file_report(putty_hash)
        if report:
            print(f"  Malicious: {report.is_malicious}")
            print(f"  Detections: {report.positives} / {report.total}")
            print(f"  Link: {report.permalink}")
            
        # --- 3. Look up a known malicious URL ---
        print("\n--- 3. Looking up a known PHISHING URL ---")
        # NOTE: Malicious URLs change frequently. This is an example.
        phishing_url = "http://185.159.82.162/GOGO/index.php"
        report = client.get_url_report(phishing_url)
        if report:
            print(f"  Malicious: {report.is_malicious}")
            print(f"  Detections: {report.positives} / {report.total}")
            print(f"  Link: {report.permalink}")

    print("\n=========================================================")
    print("=== VirusTotal Client Demo Complete ===")
    print("=========================================================")
