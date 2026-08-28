import requests
from bs4 import BeautifulSoup
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, urljoin
import os
import shutil
import json

# Define constants for supported vulnerabilities
VULNERABILITIES = [
    "XSS", "SQL Injection", "Open Redirect", "Command Injection",
    "Sensitive Data Exposure", "Directory Traversal", "CSRF",
    "Broken Authentication", "File Inclusion", "Server Misconfigurations"
]

LOG_FILE = "scan_results.json"


def banner():
    print("""
    ==============================================
       Advanced Penetration Testing and Bug Hunting Tool
    ==============================================
    Disclaimer: Use responsibly and only on websites
    you have explicit permission to test.
    ==============================================
    """)


def fetch_urls(target_url):
    """Fetch all URLs from a target website."""
    try:
        response = requests.get(target_url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        base_url = "{0.scheme}://{0.netloc}".format(urlparse(target_url))
        urls = [urljoin(base_url, link.get('href')) for link in soup.find_all('a', href=True)]
        print(f"[+] Found {len(urls)} URLs on {target_url}")
        return urls
    except Exception as e:
        print(f"[-] Failed to fetch URLs: {e}")
        return []


def scan_ports(ip):
    """Scan open ports on a target IP."""
    print(f"\n[+] Scanning ports on {ip}...")
    open_ports = []
    for port in range(1, 65536):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            if result == 0:
                print(f"[+] Open port detected: {port}")
                open_ports.append(port)
            sock.close()
        except Exception as e:
            print(f"[-] Error scanning port {port}: {e}")
    return open_ports


def detect_vulnerabilities(url):
    """Comprehensive vulnerability detection."""
    vulns = {}
    try:
        response = requests.get(url, timeout=10)

        # Detect XSS
        xss_payload = "<script>alert('XSS')</script>"
        xss_test_url = f"{url}?q={xss_payload}"
        xss_response = requests.get(xss_test_url, timeout=10)
        if xss_payload in xss_response.text:
            vulns['XSS'] = True

        # Detect SQL Injection
        sql_payload = "' OR '1'='1"
        test_url = f"{url}?q={sql_payload}"
        test_response = requests.get(test_url, timeout=10)
        if re.search(r'error|mysql|syntax', test_response.text, re.IGNORECASE):
            vulns['SQL Injection'] = True

        # Detect Open Redirect
        redirect_payload = "//evil.com"
        test_url = f"{url}?next={redirect_payload}"
        if redirect_payload in requests.get(test_url, allow_redirects=False).headers.get('Location', ''):
            vulns['Open Redirect'] = True

        # Detect Command Injection
        cmd_injection_payload = "; ls"
        cmd_test_url = f"{url}?cmd={cmd_injection_payload}"
        cmd_response = requests.get(cmd_test_url, timeout=10)
        if "root" in cmd_response.text:
            vulns['Command Injection'] = True

        # Detect Directory Traversal
        traversal_payload = "../../etc/passwd"
        traversal_test_url = f"{url}?file={traversal_payload}"
        traversal_response = requests.get(traversal_test_url, timeout=10)
        if "root:x" in traversal_response.text:
            vulns['Directory Traversal'] = True

    except Exception as e:
        print(f"[-] Failed to check {url}: {e}")
    return vulns


def subdomain_enumeration(domain):
    """Enumerate subdomains using Assetfinder or manual fallback."""
    subdomains = []
    try:
        if shutil.which("assetfinder"):
            result = subprocess.run(['assetfinder', '--subs-only', domain], capture_output=True, text=True)
            subdomains = result.stdout.splitlines()
        else:
            print("[-] Assetfinder not found. Using fallback DNS brute-force.")
            with open('subdomains.txt') as f:
                for sub in f:
                    subdomains.append(f"{sub.strip()}.{domain}")
    except Exception as e:
        print(f"[-] Subdomain enumeration failed: {e}")
    for subdomain in subdomains:
        print(f"[+] Subdomain found: {subdomain}")
    return subdomains


def run_nmap_scan(ip):
    """Run an Nmap scan on a target IP."""
    print("\n[+] Running Nmap scan...")
    try:
        result = subprocess.check_output(["nmap", "-sV", ip], universal_newlines=True)
        print(result)
    except Exception as e:
        print(f"[-] Failed to run Nmap scan: {e}")


def write_log(data, filename=LOG_FILE):
    """Write scan results to a log file in JSON format."""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"[+] Results saved to {filename}")
    except Exception as e:
        print(f"[-] Failed to write log: {e}")


def main():
    banner()
    target = input("Enter target URL (e.g., https://example.com): ").strip()
    parsed_url = urlparse(target)
    domain = parsed_url.netloc or parsed_url.path
    ip = socket.gethostbyname(domain)

    print(f"\n[+] Target IP: {ip}")

    # Fetch URLs
    urls = fetch_urls(target)

    # Subdomain Enumeration
    subdomains = subdomain_enumeration(domain)

    # Port Scanning
    open_ports = scan_ports(ip)

    # Run Nmap Scan
    run_nmap_scan(ip)

    # Vulnerability Detection
    results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(detect_vulnerabilities, url): url for url in urls}
        for future in futures:
            url = futures[future]
            try:
                vulns = future.result()
                if vulns:
                    print(f"[!] Vulnerabilities detected on {url}: {vulns}")
                    results[url] = vulns
            except Exception as e:
                print(f"[-] Error checking {url}: {e}")

    # Save results to log
    write_log(results)


if __name__ == "__main__":
    main()
