# Devin/threat_intel/attack_surface_analysis.py
# Purpose: A tool to automate attack surface analysis by performing
#          subdomain enumeration and port scanning on a target domain.

import logging
import socket
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import concurrent.futures

try:
    from modules.pentesting_tools.network_scanning_tools import NetworkScanner
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("AttackSurfaceAnalyzer")
# (Logger setup omitted for brevity)

@dataclass
class AttackSurfaceReport:
    """A structured report of the attack surface analysis."""
    root_domain: str
    subdomains: List[Dict[str, str]] = field(default_factory=list)
    open_ports_by_ip: Dict[str, List[int]] = field(default_factory=dict)

class SubdomainEnumerator:
    """A simple tool to find subdomains using a wordlist."""
    def __init__(self, wordlist: Optional[List[str]] = None):
        if wordlist:
            self.wordlist = wordlist
        else:
            # A small, common wordlist
            self.wordlist = ["www", "api", "dev", "test", "staging", "mail", "ftp", "vpn", "blog"]
            
    def find_subdomains(self, domain: str) -> Set[str]:
        """Attempts to resolve a list of common subdomains."""
        logger.info(f"Starting subdomain enumeration for '{domain}'...")
        found_subdomains = set()
        
        def check_subdomain(sub):
            full_domain = f"{sub}.{domain}"
            try:
                socket.gethostbyname(full_domain)
                logger.info(f"  Found subdomain: {full_domain}")
                return full_domain
            except socket.error:
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_sub = {executor.submit(check_subdomain, sub): sub for sub in self.wordlist}
            for future in concurrent.futures.as_completed(future_to_sub):
                result = future.result()
                if result:
                    found_subdomains.add(result)
        
        logger.info(f"Subdomain enumeration complete. Found {len(found_subdomains)} subdomains.")
        return found_subdomains

class AttackSurfaceAnalyzer:
    """Orchestrates reconnaissance tools to map a target's attack surface."""
    def __init__(self, network_scanner: NetworkScanner, subdomain_enumerator: SubdomainEnumerator):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        
        self.scanner = network_scanner
        self.enumerator = subdomain_enumerator
        
    def analyze(self, domain: str) -> AttackSurfaceReport:
        """Runs the full analysis workflow."""
        logger.info(f"--- Starting Attack Surface Analysis for {domain} ---")
        report = AttackSurfaceReport(root_domain=domain)
        
        # 1. Enumerate Subdomains
        subdomains = self.enumerator.find_subdomains(domain)
        
        # 2. Resolve IPs
        unique_ips = set()
        for sub in subdomains:
            try:
                ip = socket.gethostbyname(sub)
                unique_ips.add(ip)
                report.subdomains.append({"subdomain": sub, "ip": ip})
            except socket.error:
                report.subdomains.append({"subdomain": sub, "ip": "Resolution Failed"})
        
        # 3. Scan ports for each unique IP
        logger.info(f"Found {len(unique_ips)} unique IP addresses to scan.")
        common_ports = [21, 22, 25, 80, 110, 143, 443, 3306, 3389, 5900, 8080, 8443]
        for ip in unique_ips:
            logger.info(f"Scanning common ports on {ip}...")
            scan_result = self.scanner.scan_host(ip, common_ports)
            open_ports = list(scan_result.open_ports.keys())
            if open_ports:
                report.open_ports_by_ip[ip] = open_ports
        
        logger.info("--- Attack Surface Analysis Complete ---")
        return report

# --- Example Usage ---
if __name__ == "__main__":
    import json
    print("=========================================================")
    print("=== Attack Surface Analyzer Demo 🎯 ===")
    print("=========================================================")
    
    # Use a target that is explicitly provided for scanning
    target_domain = "scanme.nmap.org"
    
    try:
        # 1. Initialize tools
        scanner = NetworkScanner()
        enumerator = SubdomainEnumerator(wordlist=["www", "api", "nmap", "scanme"])
        
        # 2. Initialize and run the analyzer
        analyzer = AttackSurfaceAnalyzer(network_scanner=scanner, subdomain_enumerator=enumerator)
        report = analyzer.analyze(target_domain)
        
        # 3. Print the report
        print("\n--- Final Attack Surface Report ---")
        print(json.dumps(report.__dict__, indent=2))
        
    except Exception as e:
        logger.error(f"Demo failed to run. Check internet connection. Error: {e}", exc_info=True)

    print("\n=========================================================")
    print("=== Attack Surface Analyzer Demo Complete ===")
    print("=========================================================")
