# Devin/security/compliance/cfaa_checker.py
# Purpose: A safeguard module to help ensure actions comply with user-defined
#          Rules of Engagement (RoE), aiding in adherence to frameworks
#          like the Computer Fraud and Abuse Act (CFAA).

import logging
from datetime import datetime, timezone
from ipaddress import ip_address, ip_network
from typing import List, Optional
from dataclasses import dataclass, field

# Configure basic logging
logger = logging.getLogger("CFAAChecker")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

@dataclass
class RulesOfEngagement:
    """A data class to hold the rules for a security engagement."""
    project_name: str
    authorized_scopes: List[str]  # List of IPs or CIDR ranges
    denied_scopes: List[str] = field(default_factory=list)
    authorized_actions: List[str] = field(default_factory=list)
    start_time_utc: Optional[datetime] = None
    end_time_utc: Optional[datetime] = None

class CFAAChecker:
    """
    Checks if a proposed action is authorized under a given set of rules.
    """
    def __init__(self, roe: RulesOfEngagement):
        """Initializes the checker with a specific set of rules."""
        self.roe = roe
        self._parsed_auth_nets = [ip_network(s, strict=False) for s in self.roe.authorized_scopes]
        self._parsed_denied_nets = [ip_network(s, strict=False) for s in self.roe.denied_scopes]
        logger.info(f"CFAA Checker initialized for project: '{self.roe.project_name}'")

    def is_authorized(self, action: str, target: str) -> Tuple[bool, str]:
        """
        Performs a series of checks to determine if an action is permitted.

        Returns:
            A tuple of (is_authorized, reason_string).
        """
        logger.info(f"Checking authorization for action='{action}' on target='{target}'...")
        
        # 1. Check if the current time is within the engagement window
        now_utc = datetime.now(timezone.utc)
        if self.roe.start_time_utc and now_utc < self.roe.start_time_utc:
            reason = "Authorization Denied: The engagement window has not yet started."
            logger.warning(reason)
            return False, reason
        if self.roe.end_time_utc and now_utc > self.roe.end_time_utc:
            reason = "Authorization Denied: The engagement window has expired."
            logger.warning(reason)
            return False, reason

        # 2. Check if the action is explicitly authorized
        if self.roe.authorized_actions and action not in self.roe.authorized_actions:
            reason = f"Authorization Denied: Action '{action}' is not in the list of authorized actions."
            logger.warning(reason)
            return False, reason
            
        # 3. Check if the target is within scope
        try:
            target_ip = ip_address(target)
            
            # Check against deny list first
            if any(target_ip in net for net in self._parsed_denied_nets):
                reason = f"Authorization Denied: Target '{target}' is on the explicit deny list."
                logger.warning(reason)
                return False, reason
                
            # Check against allow list
            if not any(target_ip in net for net in self._parsed_auth_nets):
                reason = f"Authorization Denied: Target '{target}' is not within any authorized scope."
                logger.warning(reason)
                return False, reason

        except ValueError:
            # Handle non-IP targets like domain names (simple string match for this demo)
            if self.roe.denied_scopes and target in self.roe.denied_scopes:
                reason = f"Authorization Denied: Target '{target}' is on the explicit deny list."
                logger.warning(reason)
                return False, reason
            if self.roe.authorized_scopes and target not in self.roe.authorized_scopes:
                reason = f"Authorization Denied: Target '{target}' is not within any authorized scope."
                logger.warning(reason)
                return False, reason
        
        reason = f"Authorization Granted for action '{action}' on target '{target}'."
        logger.info(reason)
        return True, reason

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== CFAA Compliance Safeguard Prototype ⚖️🛡️ ===")
    print("=========================================================")
    
    # 1. Define the Rules of Engagement for a fictional pentest
    rules = RulesOfEngagement(
        project_name="Web Bank Corp Pentest",
        authorized_scopes=["192.168.1.0/24", "10.0.0.5"],
        denied_scopes=["192.168.1.254"], # e.g., a critical server
        authorized_actions=["port_scan", "web_crawl", "directory_bruteforce"],
        end_time_utc=datetime(2026, 1, 1, tzinfo=timezone.utc)
    )
    
    checker = CFAAChecker(roe=rules)
    
    print("--- Running Authorization Checks ---\n")
    
    # Test Case 1: Fully authorized action
    print("Test 1: A standard, in-scope port scan...")
    is_auth, reason = checker.is_authorized(action="port_scan", target="192.168.1.50")
    print(f"  Result: {reason}\n")
    assert is_auth is True

    # Test Case 2: Target is out of scope
    print("Test 2: A port scan on an out-of-scope server...")
    is_auth, reason = checker.is_authorized(action="port_scan", target="8.8.8.8")
    print(f"  Result: {reason}\n")
    assert is_auth is False
    
    # Test Case 3: Action is not authorized
    print("Test 3: An unauthorized action (exploit) on an in-scope server...")
    is_auth, reason = checker.is_authorized(action="run_exploit", target="192.168.1.50")
    print(f"  Result: {reason}\n")
    assert is_auth is False
    
    # Test Case 4: Target is explicitly denied
    print("Test 4: An authorized action on an explicitly denied server...")
    is_auth, reason = checker.is_authorized(action="web_crawl", target="192.168.1.254")
    print(f"  Result: {reason}\n")
    assert is_auth is False
    
    print("=========================================================")
    print("=== CFAA Safeguard Prototype Complete ===")
    print("=========================================================")
