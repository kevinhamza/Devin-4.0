# Devin/modules/threat_intel_tools.py
# Purpose: A facade exposing Devin's read-only threat-intelligence lookup
#          tools (MITRE ATT&CK, VirusTotal, open-source IOC feeds, attack
#          surface/subdomain recon) as agent-callable tools.
#
# Scope note: this deliberately wraps only lookup/recon components -- the
# same risk tier as the already-wired PentestingFacade.run_full_pentest_scan
# (port scanning + subdomain enumeration against a domain the caller
# specifies). It intentionally does NOT wrap threat_intel/malware_analysis/
# sandbox.py (executes arbitrary, potentially-malicious files) or anything
# under cyber_range/'s red-team/adversary-emulation/ransomware-simulator
# content as a live autonomous tool -- those stay unwired here.

import logging
from typing import Any, Dict, List, Optional

try:
    from threat_intel.intel_feeds.mitre_attack import MitreAttackDB
    MITRE_AVAILABLE = True
except Exception as e:
    MITRE_AVAILABLE = False
    _mitre_import_error = e

try:
    from threat_intel.intel_feeds.virustotal_api import VirusTotalClient
    VT_AVAILABLE = True
except Exception as e:
    VT_AVAILABLE = False
    _vt_import_error = e

try:
    from threat_intel.ioc_feeds import IOCManager
    IOC_AVAILABLE = True
except Exception as e:
    IOC_AVAILABLE = False
    _ioc_import_error = e

try:
    from threat_intel.attack_surface_analysis import AttackSurfaceAnalyzer, SubdomainEnumerator
    from modules.pentesting_tools.network_scanning_tools import NetworkScanner
    ATTACK_SURFACE_AVAILABLE = True
except Exception as e:
    ATTACK_SURFACE_AVAILABLE = False
    _attack_surface_import_error = e

logger = logging.getLogger("ThreatIntelFacade")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False


class ThreatIntelFacade:
    """A single interface to Devin's read-only threat-intelligence lookup tools."""

    def __init__(self):
        self.mitre: Optional["MitreAttackDB"] = None
        if MITRE_AVAILABLE:
            try:
                self.mitre = MitreAttackDB()
            except Exception as e:
                logger.warning(f"MITRE ATT&CK DB unavailable: {e}")
        else:
            logger.warning(f"MITRE ATT&CK DB unavailable: {_mitre_import_error}")

        self.virustotal: Optional["VirusTotalClient"] = None
        if VT_AVAILABLE:
            try:
                self.virustotal = VirusTotalClient()
            except Exception as e:
                logger.warning(f"VirusTotal client unavailable (is VIRUSTOTAL_API_KEY set?): {e}")
        else:
            logger.warning(f"VirusTotal client unavailable: {_vt_import_error}")

        self.iocs: Optional["IOCManager"] = None
        if IOC_AVAILABLE:
            try:
                self.iocs = IOCManager()
            except Exception as e:
                logger.warning(f"IOC feed manager unavailable: {e}")
        else:
            logger.warning(f"IOC feed manager unavailable: {_ioc_import_error}")

        self.attack_surface: Optional["AttackSurfaceAnalyzer"] = None
        if ATTACK_SURFACE_AVAILABLE:
            try:
                self.attack_surface = AttackSurfaceAnalyzer(
                    network_scanner=NetworkScanner(),
                    subdomain_enumerator=SubdomainEnumerator(),
                )
            except Exception as e:
                logger.warning(f"Attack surface analyzer unavailable: {e}")
        else:
            logger.warning(f"Attack surface analyzer unavailable: {_attack_surface_import_error}")

        logger.info("ThreatIntelFacade initialized.")

    def lookup_mitre_technique(self, technique_id: str) -> Dict[str, Any]:
        """Looks up a MITRE ATT&CK technique by ID (e.g. 'T1059.003') and returns its name, description and tactics."""
        if not self.mitre:
            return {"error": "MITRE ATT&CK DB is not available."}
        result = self.mitre.get_technique_by_id(technique_id)
        return result or {"error": f"Technique '{technique_id}' not found."}

    def find_mitre_techniques_for_tactic(self, tactic_shortname: str) -> List[Dict[str, Any]]:
        """Lists MITRE ATT&CK techniques associated with a tactic (e.g. 'initial-access', 'persistence')."""
        if not self.mitre:
            return [{"error": "MITRE ATT&CK DB is not available."}]
        return self.mitre.find_techniques_for_tactic(tactic_shortname)

    def get_mitre_mitigations(self, technique_id: str) -> List[Dict[str, Any]]:
        """Gets recommended defensive mitigations for a MITRE ATT&CK technique ID."""
        if not self.mitre:
            return [{"error": "MITRE ATT&CK DB is not available."}]
        return self.mitre.get_mitigations_for_technique(technique_id)

    def check_file_hash_reputation(self, file_hash: str) -> Dict[str, Any]:
        """Checks a file hash (MD5/SHA1/SHA256) against VirusTotal for known-malicious verdicts. Requires VIRUSTOTAL_API_KEY."""
        if not self.virustotal:
            return {"error": "VirusTotal client is not configured (set VIRUSTOTAL_API_KEY)."}
        report = self.virustotal.get_file_report(file_hash)
        if not report:
            return {"error": f"No VirusTotal report found for hash '{file_hash}'."}
        return {"is_malicious": report.is_malicious(), "hash": file_hash}

    def check_url_reputation(self, url: str) -> Dict[str, Any]:
        """Checks a URL against VirusTotal for known-malicious verdicts. Requires VIRUSTOTAL_API_KEY."""
        if not self.virustotal:
            return {"error": "VirusTotal client is not configured (set VIRUSTOTAL_API_KEY)."}
        report = self.virustotal.get_url_report(url)
        if not report:
            return {"error": f"No VirusTotal report found for URL '{url}'."}
        return {"is_malicious": report.is_malicious(), "url": url}

    def check_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Checks an IP address against open-source indicator-of-compromise (IOC) feeds."""
        if not self.iocs:
            return {"error": "IOC feed manager is not available."}
        return {"ip_address": ip_address, "is_known_malicious": self.iocs.is_ip_malicious(ip_address)}

    def check_domain_reputation(self, domain: str) -> Dict[str, Any]:
        """Checks a domain against open-source indicator-of-compromise (IOC) feeds."""
        if not self.iocs:
            return {"error": "IOC feed manager is not available."}
        return {"domain": domain, "is_known_malicious": self.iocs.is_domain_malicious(domain)}

    def analyze_attack_surface(self, domain: str) -> Dict[str, Any]:
        """Enumerates subdomains and scans common ports for a domain the caller controls or is authorized to assess, returning an attack-surface report."""
        if not self.attack_surface:
            return {"error": "Attack surface analyzer is not available."}
        report = self.attack_surface.analyze(domain)
        return report.__dict__ if hasattr(report, "__dict__") else report
