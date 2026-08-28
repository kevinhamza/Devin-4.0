# Devin/security/encryption/hardware_vault.py
# Purpose: A simulation of a hardware-backed vault (like a TPM) for
#          ultra-secure key generation and data sealing.

import logging
import json
import os
from typing import Optional, Tuple, Dict
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

# Configure basic logging
logger = logging.getLogger("HardwareVault")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False


class _TpmSimulator:
    """
    An internal class that simulates the cryptographic functions of a TPM.
    This is a software-backed simulation and does not use real hardware.
    """
    def __init__(self):
        # The Storage Root Key (SRK) is the TPM's master key. In a real TPM,
        # this is fused into the hardware. Here, we generate it once.
        self._storage_root_key = AESGCM.generate_key(bit_length=256)
        self._aesgcm = AESGCM(self._storage_root_key)
        self._wrapped_keys: Dict[str, bytes] = {}
        logger.info("TPM Simulator created with a new ephemeral Storage Root Key.")

    def seal(self, data: bytes) -> bytes:
        """Simulates sealing data to the TPM."""
        nonce = os.urandom(12)
        encrypted_data = self._aesgcm.encrypt(nonce, data, None)
        # In a real TPM, the blob format is more complex. Here we just join them.
        return nonce + encrypted_data
        
    def unseal(self, sealed_blob: bytes) -> bytes:
        """Simulates unsealing data from the TPM."""
        nonce = sealed_blob[:12]
        encrypted_data = sealed_blob[12:]
        return self._aesgcm.decrypt(nonce, encrypted_data, None)

    def create_wrapped_rsa_key(self) -> Tuple[bytes, bytes]:
        """
        Simulates creating an RSA key pair where the private key is
        wrapped (encrypted) by the TPM's Storage Root Key.
        """
        # 1. Generate the RSA key pair in memory
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        
        # 2. Serialize the private key to PEM format (as bytes)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # 3. "Wrap" the private key by encrypting it with the SRK
        wrapped_private_key_blob = self.seal(private_pem)
        
        # 4. Serialize the public key (which can be public)
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return public_pem, wrapped_private_key_blob


class HardwareVault:
    """
    A high-level interface for a simulated Hardware Security Module (TPM).
    """
    def __init__(self, use_simulator: bool = True):
        if not use_simulator:
            raise NotImplementedError("Interfacing with a real hardware TPM is not yet implemented in this module.")
        
        self._backend = _TpmSimulator()
        logger.warning("HardwareVault initialized in SIMULATION MODE.")

    def generate_wrapped_rsa_key(self) -> Tuple[bytes, bytes]:
        """
        Generates a new RSA key pair protected by the vault.

        Returns:
            A tuple of (public_key_pem, wrapped_private_key_blob).
            The private key is encrypted and can only be used by this vault instance.
        """
        return self._backend.create_wrapped_rsa_key()

    def seal_data(self, data: bytes) -> bytes:
        """
        Seals a small amount of data to the vault.

        Returns:
            An encrypted blob of data that can only be unsealed by this vault.
        """
        return self._backend.seal(data)

    def unseal_data(self, sealed_blob: bytes) -> bytes:
        """Unseals data that was previously sealed to this vault."""
        return self._backend.unseal(sealed_blob)


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Hardware Security Vault (TPM) Simulator 🤖🛡️ ===")
    print("=========================================================")
    print("This demo simulates a TPM to provide hardware-backed security for")
    print("key generation and data sealing, all in software.\n")
    
    try:
        # 1. Initialize the vault
        vault = HardwareVault()
        
        # 2. Seal a top-secret password
        print("--- 1. Data Sealing Demonstration ---")
        secret_password = b"quantum-bacon-is-the-best-bacon"
        print(f"Original secret: {secret_password.decode()}")
        
        sealed_blob = vault.seal_data(secret_password)
        print(f"Sealed data blob (encrypted): {sealed_blob.hex()[:60]}...")
        
        # This will fail if the blob is tampered with or the key is wrong
        unsealed_password = vault.unseal_data(sealed_blob)
        print(f"Unsealed secret: {unsealed_password.decode()}")
        
        assert secret_password == unsealed_password
        print("[SUCCESS] Data was successfully sealed and unsealed.\n")
        
        # 3. Generate a wrapped RSA key
        print("--- 2. Wrapped Key Generation Demonstration ---")
        print("Generating an RSA key pair. The private key will be encrypted by the vault.")
        
        public_key_pem, wrapped_private_key_blob = vault.generate_wrapped_rsa_key()
        
        print("\nPublic Key (can be shared freely):")
        print(public_key_pem.decode())
        
        print(f"Wrapped Private Key Blob (Encrypted, safe to store):")
        print(f"{wrapped_private_key_blob.hex()[:80]}...")
        
        # To prove it works, we unseal the private key to use it.
        # In a real TPM application, you would pass the blob to a "sign" or "decrypt"
        # function and never unseal the key itself in the application.
        unsealed_private_pem = vault.unseal_data(wrapped_private_key_blob)
        private_key = serialization.load_pem_private_key(unsealed_private_pem, password=None)
        
        print("\n[SUCCESS] Unsealed the private key blob for use, proving the concept.")

    except ImportError:
        print("\nERROR: The 'cryptography' library is required. 'pip install cryptography'")
    except Exception as e:
        logger.error(f"An error occurred during the demo: {e}", exc_info=True)


    print("\n=========================================================")
    print("=== Hardware Vault Simulation Complete ===")
    print("=========================================================")
