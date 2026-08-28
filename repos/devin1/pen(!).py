import requests
from bs4 import BeautifulSoup
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, urljoin
import json
import os
import shutil

# Define constants for supported vulnerabilities
VULNERABILITIES = [
    "XSS", "SQL Injection", "Open Redirect", "Command Injection",
    "Sensitive Data Exposure", "Directory Traversal", "CSRF",
    "Broken Authentication", "File Inclusion", "Server Misconfigurations",
    "XXE", "LDAP Injection", "NoSQL Injection", "SSRF", "RCE"
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


def detect_xss(url):
    """Detect Cross-Site Scripting vulnerabilities."""
    try:
        xss_payload = "<script>alert('XSS')</script>"
        test_url = f"{url}?q={xss_payload}"
        response = requests.get(test_url, timeout=10)
        if xss_payload in response.text:
            return True
    except Exception as e:
        print(f"[-] XSS detection failed for {url}: {e}")
    return False


def detect_sql_injection(url):
    """Detect SQL Injection vulnerabilities."""
    try:
        sql_payload = "' OR '1'='1"
        test_url = f"{url}?q={sql_payload}"
        response = requests.get(test_url, timeout=10)
        if re.search(r'error|mysql|syntax', response.text, re.IGNORECASE):
            return True
    except Exception as e:
        print(f"[-] SQL Injection detection failed for {url}: {e}")
    return False


def detect_open_redirect(url):
    """Detect Open Redirect vulnerabilities."""
    try:
        redirect_payload = "//evil.com"
        test_url = f"{url}?next={redirect_payload}"
        response = requests.get(test_url, allow_redirects=False, timeout=10)
        if response.status_code in [301, 302] and 'Location' in response.headers:
            if redirect_payload in response.headers['Location']:
                return True
    except Exception as e:
        print(f"[-] Open Redirect detection failed for {url}: {e}")
    return False


def detect_command_injection(url):
    """Detect Command Injection vulnerabilities."""
    try:
        cmd_payload = "; ls"
        test_url = f"{url}?cmd={cmd_payload}"
        response = requests.get(test_url, timeout=10)
        if "root" in response
return True
    except Exception as e:
        print(f"[-] Command Injection detection failed for {url}: {e}")
    return False


def detect_directory_traversal(url):
    """Detect Directory Traversal vulnerabilities."""
    try:
        traversal_payload = "../../etc/passwd"
        test_url = f"{url}?file={traversal_payload}"
        response = requests.get(test_url, timeout=10)
        if "root:x" in response.text:
            return True
    except Exception as e:
        print(f"[-] Directory Traversal detection failed for {url}: {e}")
    return False


def detect_vulnerabilities(url):
    """Comprehensive vulnerability detection."""
    vulns = {}
    if detect_xss(url):
        vulns['XSS'] = True
    if detect_sql_injection(url):
        vulns['SQL Injection'] = True
    if detect_open_redirect(url):
        vulns['Open Redirect'] = True
    if detect_command_injection(url):
        vulns['Command Injection'] = True
    if detect_directory_traversal(url):
        vulns['Directory Traversal'] = True
    # Add more vulnerability checks here if needed
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
            # Implement basic DNS brute-force here (not recommended for large-scale scans)
            # Example:
            # with open('subdomains.txt') as f:
            #     for sub in f:
            #         subdomains.append(f"{sub.strip()}.{domain}")
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
        print(f"[-] Failed to write log file: {e}")


def main():
    banner()
    target_url = input("Enter the target URL: ")
    ip = input("Enter the target IP address: ")  # Get IP address for port scanning and Nmap

    # Fetch initial URLs
    urls = fetch_urls(target_url)

    # Perform vulnerability scans concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(detect_vulnerabilities, urls))

    # Enumerate subdomains
    subdomains = subdomain_enumeration(urlparse(target_url).netloc)

    # Scan ports on the target IP
    open_ports = scan_ports(ip)

    # Run Nmap scan
    run_nmap_scan(ip)

    # Create a dictionary to store scan results
    scan_data = {
        'target_url': target_url,
        'subdomains': subdomains,
        'open_ports': open_ports,
        'vulnerabilities': {url: vulns for url, vulns in zip(urls, results)}
    }

    # Write results to a log file
    write_log(scan_data)

if __name__ == "__main__":
    main()
