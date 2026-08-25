# Devin/quantum/post_quantum_crypto.py
# Purpose: A toolkit for using post-quantum cryptographic algorithms for
#          key exchange and digital signatures via the Open Quantum Safe library.

import logging
import os
from typing import Optional, Tuple, List

try:
    # liboqs-python's own import-time code (oqs/oqs.py: _load_liboqs) tries
    # to auto-clone and build the liboqs C library if it can't find a
    # prebuilt copy, and when that second attempt also fails (e.g. no cmake
    # installed) it does `raise SystemExit(msg) from None` -- confirmed by
    # reading its actual source after `except Exception` alone turned out
    # not to catch this live: SystemExit is a BaseException, not an
    # Exception subclass, so it walked straight past a plain `except
    # Exception` and killed the whole process. Must catch BaseException
    # here specifically for that reason (this mirrors the existing
    # BaseException guard in modules/quantum_tools.py around the vault
    # loader, added for the same class of "third-party import raises
    # something more exotic than ImportError" problem).
    import oqs
    OQS_AVAILABLE = True
except BaseException as e:
    OQS_AVAILABLE = False
    logging.getLogger("PostQuantumCrypto").warning(f"liboqs-python unavailable ({e}); post-quantum crypto disabled.")

# Configure basic logging
logger = logging.getLogger("PostQuantumCrypto")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class PostQuantumCrypto:
    """
    Provides a high-level interface for Post-Quantum Cryptography (PQC)
    using the liboqs library.
    """
    def __init__(self):
        if not OQS_AVAILABLE:
            raise ImportError("The 'liboqs-python' package (imported as 'oqs') is required. 'pip install liboqs-python'")
        # liboqs-python renamed get_enabled_KEMs()/get_enabled_sigs() to
        # get_enabled_kem_mechanisms()/get_enabled_sig_mechanisms() -- fall
        # back to the old names for older installs.
        self.supported_kems = (
            oqs.get_enabled_kem_mechanisms() if hasattr(oqs, "get_enabled_kem_mechanisms")
            else oqs.get_enabled_KEMs()
        )
        self.supported_sigs = (
            oqs.get_enabled_sig_mechanisms() if hasattr(oqs, "get_enabled_sig_mechanisms")
            else oqs.get_enabled_sigs()
        )
        logger.info("Post-Quantum Crypto module initialized.")

    # --- Key Encapsulation Mechanism (KEM) Methods ---

    def kem_generate_keypair(self, algorithm: str) -> Optional[Tuple[bytes, bytes]]:
        """
        Generates a PQC public and secret key for a KEM algorithm.
        
        Args:
            algorithm: The name of the KEM algorithm (e.g., "Kyber768").

        Returns:
            A tuple containing (public_key, secret_key), or None on failure.
        """
        if algorithm not in self.supported_kems:
            logger.error(f"KEM algorithm '{algorithm}' not supported by this liboqs build.")
            return None
        
        with oqs.KeyEncapsulation(algorithm) as kem:
            public_key = kem.generate_keypair()
            secret_key = kem.export_secret_key()
            return public_key, secret_key

    def kem_encapsulate_secret(self, algorithm: str, public_key: bytes) -> Optional[Tuple[bytes, bytes]]:
        """
        Generates a shared secret and encapsulates it for the public key holder. (Client-side)

        Returns:
            A tuple containing (ciphertext, shared_secret), or None on failure.
        """
        if algorithm not in self.supported_kems: return None
        with oqs.KeyEncapsulation(algorithm) as kem:
            ciphertext, shared_secret = kem.encap_secret(public_key)
            return ciphertext, shared_secret

    def kem_decapsulate_secret(self, algorithm: str, secret_key: bytes, ciphertext: bytes) -> Optional[bytes]:
        """
        Decapsulates a ciphertext to retrieve the shared secret. (Server-side)

        Returns:
            The shared_secret, or None on failure.
        """
        if algorithm not in self.supported_kems: return None
        # The secret key must be supplied to the KeyEncapsulation constructor
        # (it's used internally for the decapsulation call, not passed to
        # decap_secret() directly).
        with oqs.KeyEncapsulation(algorithm, secret_key) as kem:
            shared_secret = kem.decap_secret(ciphertext)
            return shared_secret

    # --- Digital Signature Methods ---

    def signature_generate_keypair(self, algorithm: str) -> Optional[Tuple[bytes, bytes]]:
        """
        Generates a PQC public and secret key for a signature algorithm.

        Args:
            algorithm: The name of the signature algorithm (e.g., "Dilithium3").
        """
        if algorithm not in self.supported_sigs:
            logger.error(f"Signature algorithm '{algorithm}' not supported.")
            return None
        
        with oqs.Signature(algorithm) as sig:
            public_key = sig.generate_keypair()
            secret_key = sig.export_secret_key()
            return public_key, secret_key

    def signature_sign_message(self, algorithm: str, secret_key: bytes, message: bytes) -> Optional[bytes]:
        """Signs a message with a PQC secret key."""
        if algorithm not in self.supported_sigs: return None
        with oqs.Signature(algorithm) as sig:
            signature = sig.sign(message, secret_key)
            return signature

    def signature_verify(self, algorithm: str, public_key: bytes, message: bytes, signature: bytes) -> bool:
        """Verifies a signature against a message and public key."""
        if algorithm not in self.supported_sigs: return False
        with oqs.Signature(algorithm) as sig:
            is_valid = sig.verify(message, signature, public_key)
            return is_valid

# --- Example Usage ---
if __name__ == "__main__":
    if not OQS_AVAILABLE:
        print("\nERROR: The 'oqs' library is required for this demo.")
        print("Please run: pip install oqs")
    else:
        print("=========================================================")
        print("=== Post-Quantum Cryptography Prototype ⚛️️🔒 ===")
        print("=========================================================")
        
        pqc = PostQuantumCrypto()
        
        # --- 1. Key Encapsulation (KEM) Demo using Kyber ---
        print("\n--- 1. KEM Demo (CRYSTALS-Kyber) ---")
        kem_algo = "Kyber768"
        if kem_algo in pqc.supported_kems:
            print(f"Using KEM algorithm: {kem_algo}")
            
            # 1a. Server generates a key pair
            public_key, secret_key = pqc.kem_generate_keypair(kem_algo)
            print(f"Generated a {len(public_key)} byte public key and a {len(secret_key)} byte secret key.")
            
            # 1b. Client uses the public key to create and encapsulate a shared secret
            ciphertext, client_shared_secret = pqc.kem_encapsulate_secret(kem_algo, public_key)
            print("Client has generated and encapsulated a shared secret.")
            
            # 1c. Server uses its secret key to decapsulate and get the same shared secret
            server_shared_secret = pqc.kem_decapsulate_secret(kem_algo, secret_key, ciphertext)
            print("Server has decapsulated the ciphertext.")
            
            # 1d. Verify that both parties arrived at the same secret
            if client_shared_secret == server_shared_secret:
                print("\nSUCCESS! Client and Server derived the same shared secret.")
            else:
                print("\nFAILURE! Shared secrets do not match.")
        else:
            print(f"Skipping KEM demo: {kem_algo} is not supported by this build.")


        # --- 2. Digital Signature Demo using Dilithium ---
        print("\n\n--- 2. Digital Signature Demo (CRYSTALS-Dilithium) ---")
        sig_algo = "Dilithium3"
        if sig_algo in pqc.supported_sigs:
            print(f"Using Signature algorithm: {sig_algo}")
            message_to_sign = b"This is a message from the Devin project."
            
            # 2a. Signer generates a key pair
            signer_public_key, signer_secret_key = pqc.signature_generate_keypair(sig_algo)
            print(f"Generated a {len(signer_public_key)} byte public key and a {len(signer_secret_key)} byte secret key.")
            
            # 2b. Signer signs the message
            signature = pqc.signature_sign_message(sig_algo, signer_secret_key, message_to_sign)
            print(f"Message signed, producing a {len(signature)} byte signature.")
            
            # 2c. Verifier uses the public key to verify the signature
            is_valid = pqc.signature_verify(sig_algo, signer_public_key, message_to_sign, signature)
            print(f"\nVerifying original message... Is signature valid? -> {is_valid}")
            
            # 2d. Demonstrate that changing the message invalidates the signature
            tampered_message = b"This is a malicious message."
            is_valid_tampered = pqc.signature_verify(sig_algo, signer_public_key, tampered_message, signature)
            print(f"Verifying tampered message... Is signature valid? -> {is_valid_tampered}")

        else:
            print(f"Skipping Signature demo: {sig_algo} is not supported by this build.")
            
    print("\n=========================================================")
    print("=== Post-Quantum Crypto Prototype Complete ===")
    print("=========================================================")
