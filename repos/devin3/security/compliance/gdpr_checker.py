# Devin/security/compliance/gdpr_checker.py
# Purpose: An automated tool to scan websites for common technical indicators
#          related to GDPR compliance.

import logging
import re
from typing import Dict, Any, List, Set

try:
    from bs4 import BeautifulSoup
    from reality_engine.web_crawler.web_crawler import WebCrawler
    from privacy.data_obfuscation import DataObfuscator
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e


# Configure basic logging
logger = logging.getLogger("GDPR_Checker")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class GDPR_Checker:
    """
    Crawls a website and checks for common GDPR-related technical markers.
    """
    def __init__(self):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        
        self.crawler = WebCrawler()
        self.pii_detector = DataObfuscator()
        
        # Heuristic patterns for detection
        self.privacy_policy_patterns = re.compile(r'privacy policy|privacy statement|data protection', re.IGNORECASE)
        self.cookie_consent_patterns = re.compile(r'cookie consent|manage cookies|accept cookies|we use cookies', re.IGNORECASE)
        self.pii_form_fields = re.compile(r'email|phone|password|address|name|username|dob|birthdate', re.IGNORECASE)

    def _check_privacy_policy_link(self, soup: BeautifulSoup) -> bool:
        """Checks for the presence of a link to a privacy policy."""
        return bool(soup.find('a', string=self.privacy_policy_patterns))

    def _check_cookie_consent_banner(self, soup: BeautifulSoup) -> bool:
        """Uses heuristics to check for a cookie consent banner."""
        body_text = soup.get_text().lower()
        return bool(self.cookie_consent_patterns.search(body_text))

    def _check_for_pii_in_text(self, soup: BeautifulSoup) -> List[str]:
        """Scans the visible text of a page for PII."""
        text = soup.get_text()
        pii_results = self.pii_detector.analyze_pii(text)
        return list(set([result.entity_type for result in pii_results]))

    def _analyze_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Finds data collection forms and analyzes them."""
        forms_found = []
        for form in soup.find_all('form'):
            is_pii_form = False
            has_consent_checkbox = False
            
            # Check for input fields that likely collect PII
            pii_inputs = form.find_all('input', {'name': self.pii_form_fields})
            if pii_inputs:
                is_pii_form = True

            # Check for a consent checkbox within the form
            consent_checkbox = form.find('input', {'type': 'checkbox', 'name': re.compile(r'consent|terms|agree', re.I)})
            if consent_checkbox:
                has_consent_checkbox = True
            
            if is_pii_form:
                forms_found.append({
                    "form_action": form.get('action', 'N/A'),
                    "has_consent_checkbox": has_consent_checkbox
                })
        return forms_found

    def audit_website(self, start_url: str, max_pages: int = 10) -> Dict[str, Any]:
        """
        Runs the full audit on a website.
        """
        logger.warning(f"Starting GDPR compliance audit for {start_url} (up to {max_pages} pages)...")
        results = {}
        
        for url, soup in self.crawler.crawl(start_url, max_pages=max_pages):
            logger.info(f"Auditing page: {url}")
            page_results = {
                "privacy_policy_link_found": self._check_privacy_policy_link(soup),
                "cookie_consent_banner_found": self._check_cookie_consent_banner(soup),
                "pii_in_text": self._check_for_pii_in_text(soup),
                "data_collection_forms": self._analyze_forms(soup),
            }
            results[url] = page_results
            
        logger.warning("Audit complete.")
        return results

    @staticmethod
    def generate_summary(results: Dict[str, Any]) -> str:
        """Generates a human-readable summary of the audit results."""
        summary = "--- GDPR Technical Audit Summary ---\n"
        
        # Aggregate findings
        policy_found = any(res['privacy_policy_link_found'] for res in results.values())
        cookie_banner_found = any(res['cookie_consent_banner_found'] for res in results.values())
        
        summary += f"\n[Overall Findings]\n"
        summary += f"- Privacy Policy Link: {'Found' if policy_found else 'NOT FOUND'}\n"
        summary += f"- Cookie Consent Banner: {'Likely Present' if cookie_banner_found else 'NOT DETECTED'}\n"
        
        summary += "\n[Page-Specific Issues]\n"
        issues_found = False
        for url, res in results.items():
            page_issues = []
            if res['pii_in_text']:
                page_issues.append(f"PII detected in text: {res['pii_in_text']}")
            for form in res['data_collection_forms']:
                if not form['has_consent_checkbox']:
                    page_issues.append(f"Data collection form found without a consent checkbox (action: {form['form_action']})")
            
            if page_issues:
                issues_found = True
                summary += f"  - URL: {url}\n"
                for issue in page_issues:
                    summary += f"    - {issue}\n"

        if not issues_found:
            summary += "  - No major page-specific issues detected in the scanned pages.\n"
            
        return summary


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== GDPR Compliance Checker Prototype 📜🇪🇺 ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module is missing. Please ensure all project files are present. Error: {_import_error}")
        print("You may also need to run 'python -m spacy download en_core_web_lg' for PII detection.")
    else:
        # Use 'books.toscrape.com', which is a good, simple example site.
        TARGET_URL = "http://books.toscrape.com/"
        
        try:
            checker = GDPR_Checker()
            audit_results = checker.audit_website(TARGET_URL, max_pages=10)
            
            # Print the summary
            summary = checker.generate_summary(audit_results)
            print(summary)
            
        except Exception as e:
            logger.error(f"An error occurred during the demo: {e}", exc_info=True)
            print("\nPlease ensure you have run 'pip install -r requirements.txt' and downloaded the spaCy model.")
    
    print("\n=========================================================")
    print("=== GDPR Checker Prototype Complete ===")
    print("=========================================================")
