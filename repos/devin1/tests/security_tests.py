"""
File: tests/security_tests.py
Description: Testing suite for security-related modules in the Devin project.
"""

import unittest
from modules.security_tools import SecurityTools
from modules.pentesting_tools import PentestingTools

class TestSecurityTools(unittest.TestCase):
    """Tests for the SecurityTools module."""

    def setUp(self):
        """Initialize SecurityTools instance for testing."""
        self.security = SecurityTools()

    def test_encryption(self):
        """Test data encryption and decryption."""
        data = "sensitive_data"
        encrypted = self.security.encrypt_data(data)
        decrypted = self.security.decrypt_data(encrypted)
        self.assertEqual(data, decrypted, "Decrypted data should match the original data.")

    def test_firewall_rules(self):
        """Test adding and validating firewall rules."""
        rule = {"action": "allow", "port": 8080, "protocol": "TCP"}
        self.security.add_firewall_rule(rule)
        rules = self.security.get_firewall_rules()
        self.assertIn(rule, rules, "Firewall rule should be added successfully.")

    def test_vulnerability_scan(self):
        """Test scanning for vulnerabilities."""
        target = "127.0.0.1"
        results = self.security.scan_for_vulnerabilities(target)
        self.assertTrue(isinstance(results, list), "Scan results should be a list.")
        self.assertTrue(len(results) >= 0, "Scan results should not be None.")

class TestPentestingTools(unittest.TestCase):
    """Tests for the PentestingTools module."""

    def setUp(self):
        """Initialize PentestingTools instance for testing."""
        self.pentesting = PentestingTools()

    def test_port_scan(self):
        """Test port scanning functionality."""
        target = "localhost"
        ports = self.pentesting.port_scan(target)
        self.assertTrue(isinstance(ports, list), "Port scan result should be a list.")
        self.assertTrue(all(isinstance(port, int) for port in ports), "Ports should be integers.")

    def test_brute_force(self):
        """Test brute force attack simulation."""
        credentials = {"username": "admin", "password": "1234"}
        result = self.pentesting.simulate_brute_force(credentials)
        self.assertTrue(isinstance(result, bool), "Brute force simulation should return a boolean.")

    def test_sql_injection(self):
        """Test SQL injection detection."""
        query = "SELECT * FROM users WHERE username='admin' AND password='1234' OR '1'='1';"
        result = self.pentesting.detect_sql_injection(query)
        self.assertTrue(result, "SQL injection should be detected.")

if __name__ == "__main__":
    unittest.main()
