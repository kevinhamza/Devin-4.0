# Devin/security/audit_logs/action_auditor.py
# Purpose: A secure logger that creates a tamper-proof, blockchain-style
#          audit trail with post-quantum cryptographic signatures.

import logging
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

try:
    # This module integrates our PQC tool to sign the audit logs
    from quantum.post_quantum_crypto import PostQuantumCrypto
    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("ActionAuditor")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class ActionAuditor:
    """
    Manages a cryptographically secured, append-only audit log.
    """
    def __init__(self, log_file_path: Path, pqc_private_key: bytes, pqc_public_key: bytes):
        if not PQC_AVAILABLE:
            raise ImportError("PostQuantumCrypto module is required.")
        
        self.log_file = log_file_path
        self.pqc = PostQuantumCrypto()
        self.pqc_algo = "Dilithium3"
        self.private_key = pqc_private_key
        self.public_key = pqc_public_key
        
        # Initialize the log file with a genesis entry if it doesn't exist
        if not self.log_file.exists() or self.log_file.stat().st_size == 0:
            self._create_genesis_entry()

    def _hash_entry(self, entry: Dict[str, Any]) -> str:
        """Calculates the SHA256 hash of a log entry."""
        # We must sort the keys to ensure the hash is deterministic
        entry_string = json.dumps(entry, sort_keys=True).encode()
        return hashlib.sha256(entry_string).hexdigest()

    def _get_last_hash(self) -> str:
        """Reads the last entry from the log file to get its hash."""
        with open(self.log_file, 'r') as f:
            last_line = None
            for last_line in f:
                pass
            if last_line:
                return json.loads(last_line)['entry_hash']
        return "0" * 64 # Should only happen for genesis

    def _create_genesis_entry(self):
        """Creates the first entry in the log file."""
        genesis_entry = {
            "timestamp": str(datetime.now()),
            "action": "LOG_INITIALIZED",
            "parameters": {},
            "previous_hash": "0" * 64
        }
        entry_hash = self._hash_entry(genesis_entry)
        genesis_entry["entry_hash"] = entry_hash
        
        with open(self.log_file, 'w') as f:
            f.write(json.dumps(genesis_entry) + '\n')
        logger.info(f"Initialized new audit log at {self.log_file}")

    def log_action(self, tool_name: str, parameters: Dict[str, Any]):
        """Logs a new action to the secure audit trail."""
        previous_hash = self._get_last_hash()
        
        entry_data = {
            "timestamp": str(datetime.now()),
            "action": tool_name,
            "parameters": parameters,
            "previous_hash": previous_hash
        }
        
        entry_hash = self._hash_entry(entry_data)
        full_entry = {**entry_data, "entry_hash": entry_hash}
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(full_entry) + '\n')
        logger.info(f"Logged action '{tool_name}' with hash {entry_hash[:12]}...")

    def verify_log_chain(self) -> bool:
        """
        Verifies the integrity of the entire log chain.
        Returns True if valid, False otherwise.
        """
        logger.info(f"Verifying integrity of log chain in '{self.log_file}'...")
        with open(self.log_file, 'r') as f:
            previous_hash = "0" * 64
            for i, line in enumerate(f):
                try:
                    entry = json.loads(line)
                    entry_hash = entry.pop("entry_hash")
                    
                    # 1. Check if previous hash matches
                    if entry["previous_hash"] != previous_hash:
                        logger.error(f"Chain broken at entry {i+1}: 'previous_hash' does not match.")
                        return False
                        
                    # 2. Check if the entry's content hash is correct
                    recalculated_hash = self._hash_entry(entry)
                    if recalculated_hash != entry_hash:
                        logger.error(f"Chain broken at entry {i+1}: Content does not match hash.")
                        return False
                        
                    previous_hash = entry_hash
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Invalid log entry format at line {i+1}: {e}")
                    return False
        
        logger.info("Log chain integrity verified successfully.")
        return True

    def sign_log(self) -> bytes:
        """Creates a PQC signature for the current state of the entire log file."""
        log_content = self.log_file.read_bytes()
        logger.info("Signing log file with PQC signature...")
        return self.pqc.signature_sign_message(self.pqc_algo, self.private_key, log_content)

    def verify_log_signature(self, signature: bytes) -> bool:
        """Verifies a PQC signature against the current log file."""
        log_content = self.log_file.read_bytes()
        logger.info("Verifying PQC signature of log file...")
        is_valid = self.pqc.signature_verify(self.pqc_algo, self.public_key, log_content, signature)
        logger.info(f"Signature verification result: {is_valid}")
        return is_valid


# --- Example Usage ---
if __name__ == "__main__":
    if not PQC_AVAILABLE:
        print("\nERROR: The PostQuantumCrypto module is required for this demo.")
    else:
        print("=========================================================")
        print("=== Secure Audit Log Prototype ⛓️✍️ ===")
        print("=========================================================")
        
        log_file = Path("demo_audit.log")
        if log_file.exists(): log_file.unlink()
        
        try:
            # 1. Setup PQC keys for signing
            pqc = PostQuantumCrypto()
            pub_key, priv_key = pqc.signature_generate_keypair("Dilithium3")
            
            # 2. Initialize the auditor and log some actions
            auditor = ActionAuditor(log_file, priv_key, pub_key)
            auditor.log_action("network_scanner.scan_host", {"target": "192.168.1.1"})
            auditor.log_action("web_scanner.crawl", {"start_url": "http://example.com"})
            auditor.log_action("ai_composer.compose", {"content_type": "phishing_email"})
            
            print("\n--- 1. Verifying pristine log ---")
            assert auditor.verify_log_chain()
            
            # 3. Sign the log and verify the signature
            print("\n--- 2. Signing and Verifying Log ---")
            log_signature = auditor.sign_log()
            assert auditor.verify_log_signature(log_signature)
            
            # 4. SIMULATE A TAMPER
            print("\n--- 3. Simulating a Malicious Tamper ---")
            lines = log_file.read_text().splitlines()
            # Attacker tries to change a parameter in the second log entry
            tampered_entry = json.loads(lines[1])
            tampered_entry["parameters"]["target"] = "8.8.8.8" # Change the IP
            lines[1] = json.dumps(tampered_entry)
            log_file.write_text("\n".join(lines) + "\n")
            print("Log entry #2 has been maliciously altered.")

            # 5. Re-verify the chain and signature
            print("\n--- 4. Re-verifying the tampered log ---")
            print("\nVerifying chain integrity...")
            if not auditor.verify_log_chain():
                print("[SUCCESS] Tamper detected! The hash chain is broken.")
            
            print("\nVerifying PQC signature...")
            if not auditor.verify_log_signature(log_signature):
                print("[SUCCESS] Tamper detected! The PQC signature is no longer valid.")

        finally:
            if log_file.exists(): log_file.unlink()

    print("\n=========================================================")
    print("=== Secure Audit Log Prototype Complete ===")
    print("=========================================================")
