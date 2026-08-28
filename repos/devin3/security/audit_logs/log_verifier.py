# Devin/security/audit_logs/log_verifier.py
# Purpose: A command-line tool for verifying the cryptographic integrity
#          of an audit log file created by the ActionAuditor.

import logging
import argparse
from pathlib import Path
import json
import hashlib

try:
    # This tool uses the verification logic from our existing modules
    from security.audit_logs.action_auditor import ActionAuditor
    from quantum.post_quantum_crypto import PostQuantumCrypto
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e


# Configure basic logging
logger = logging.getLogger("LogVerifier")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class LogVerifier:
    """
    A standalone verifier for Devin's audit logs.
    This class encapsulates the static verification logic, mirroring the
    ActionAuditor for consistency.
    """

    @staticmethod
    def _hash_entry(entry: dict) -> str:
        """Calculates the SHA256 hash of a log entry."""
        entry_string = json.dumps(entry, sort_keys=True).encode()
        return hashlib.sha256(entry_string).hexdigest()

    @staticmethod
    def verify_log_chain(log_file_path: Path) -> bool:
        """
        Verifies the integrity of the entire log chain.
        Returns True if valid, False otherwise.
        """
        if not log_file_path.is_file():
            logger.error(f"Log file not found at: {log_file_path}")
            return False

        logger.info(f"Verifying integrity of log chain in '{log_file_path}'...")
        with open(log_file_path, 'r') as f:
            previous_hash = "0" * 64
            for i, line in enumerate(f):
                try:
                    entry = json.loads(line)
                    # The hash is calculated on the entry *before* the hash was added
                    entry_hash = entry.pop("entry_hash")
                    
                    if entry["previous_hash"] != previous_hash:
                        logger.critical(f"CHAIN TAMPER DETECTED at entry {i+1}: 'previous_hash' does not match the hash of the preceding block.")
                        return False
                        
                    recalculated_hash = LogVerifier._hash_entry(entry)
                    if recalculated_hash != entry_hash:
                        logger.critical(f"CHAIN TAMPER DETECTED at entry {i+1}: The entry's content has been altered.")
                        return False
                        
                    previous_hash = entry_hash
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Invalid log entry format at line {i+1}: {e}")
                    return False
        
        logger.info("Log chain integrity is VALID.")
        return True

    @staticmethod
    def verify_log_signature(public_key_path: Path, log_file_path: Path, signature_path: Path) -> bool:
        """Verifies a PQC signature against the current log file."""
        if not all([p.is_file() for p in [public_key_path, log_file_path, signature_path]]):
            logger.error("One or more required files (key, log, signature) not found.")
            return False

        logger.info("Verifying PQC signature of log file...")
        pqc = PostQuantumCrypto()
        
        # Load keys and data
        public_key = public_key_path.read_bytes()
        log_content = log_file_path.read_bytes()
        signature = signature_path.read_bytes()

        is_valid = pqc.signature_verify("Dilithium3", public_key, log_content, signature)
        
        if is_valid:
            logger.info("PQC signature is VALID.")
        else:
            logger.critical("SIGNATURE INVALID! The log file's authenticity cannot be verified.")
        return is_valid


def main():
    """Main function to run the command-line tool."""
    if not DEVIN_CORE_AVAILABLE:
        logger.critical(f"Could not import a core Devin module. Ensure all project files are present. Error: {_import_error}")
        return

    parser = argparse.ArgumentParser(
        description="A command-line tool to verify the cryptographic integrity of Devin's audit logs.",
        epilog="Example: python -m security.audit_logs.log_verifier demo_audit.log --check-chain"
    )
    parser.add_argument("logfile", type=Path, help="Path to the audit log file to verify.")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-chain", action="store_true", help="Verify the integrity of the internal hash chain.")
    group.add_argument("--check-signature", action="store_true", help="Verify the PQC digital signature of the log file.")
    
    parser.add_argument("--public-key", type=Path, help="Path to the PQC public key file (required for --check-signature).")
    parser.add_argument("--signature", type=Path, help="Path to the PQC signature file (required for --check-signature).")

    args = parser.parse_args()

    if args.check_chain:
        if LogVerifier.verify_log_chain(args.logfile):
            print("\nRESULT: [SUCCESS] Log chain integrity is intact.")
        else:
            print("\nRESULT: [FAILURE] The log file has been tampered with or is corrupt.")

    elif args.check_signature:
        if not args.public_key or not args.signature:
            parser.error("--public-key and --signature are required for --check-signature.")
        
        if LogVerifier.verify_log_signature(args.public_key, args.logfile, args.signature):
            print("\nRESULT: [SUCCESS] The log file's PQC signature is valid.")
        else:
            print("\nRESULT: [FAILURE] The log file's signature is invalid or the file has been tampered with.")

if __name__ == "__main__":
    # To run this tool, you would use the command line. For example:
    # 1. Create a dummy log first with the auditor:
    #    (This is for setup, not part of the verifier itself)
    #    from security.audit_logs.action_auditor import ActionAuditor
    #    from quantum.post_quantum_crypto import PostQuantumCrypto
    #    from pathlib import Path
    #    pqc = PostQuantumCrypto()
    #    pub_k, priv_k = pqc.signature_generate_keypair("Dilithium3")
    #    Path("mykey.pub").write_bytes(pub_k)
    #    Path("mykey.priv").write_bytes(priv_k)
    #    auditor = ActionAuditor(Path("audit.log"), priv_k, pub_k)
    #    auditor.log_action("test", {})
    #    sig = auditor.sign_log()
    #    Path("audit.log.sig").write_bytes(sig)
    #
    # 2. Then run the verifier from your terminal:
    #    python -m security.audit_logs.log_verifier audit.log --check-chain
    #    python -m security.audit_logs.log_verifier audit.log --check-signature --public-key mykey.pub --signature audit.log.sig
    
    main()
