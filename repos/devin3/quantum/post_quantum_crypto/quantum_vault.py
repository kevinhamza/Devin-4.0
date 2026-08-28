# Devin/quantum/post_quantum_crypto/quantum_vault.py
# Purpose: A secure credential vault using a hybrid Post-Quantum (Kyber)
#          and classical (AES-GCM) encryption scheme.

import logging
import json
import os
import base64
from pathlib import Path
from typing import Dict, Optional

# --- Import other Devin modules ---
try:
    from quantum.post_quantum_crypto.crystal_kyber_integration import KyberKEM
    KYBER_AVAILABLE = True
except ImportError:
    KYBER_AVAILABLE = False

# --- Core encryption library ---
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("QuantumVault")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class QuantumVault:
    """
    Manages the encryption and decryption of secrets using a PQC hybrid scheme.
    """
    def __init__(self, vault_path: Path, kem_security_level: int = 768):
        if not all([KYBER_AVAILABLE, CRYPTOGRAPHY_AVAILABLE]):
            raise ImportError("Required libraries missing. 'pip install pykyber cryptography'")
            
        self.vault_path = vault_path
        self.kem = KyberKEM(security_level=kem_security_level)
        self.vault_data: Dict[str, str] = self._load_vault()

    def _load_vault(self) -> Dict[str, str]:
        """Loads the encrypted vault from a JSON file."""
        if self.vault_path.is_file():
            with open(self.vault_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_vault(self):
        """Saves the current state of the vault to its JSON file."""
        with open(self.vault_path, 'w') as f:
            json.dump(self.vault_data, f, indent=2)

    def encrypt_secret(self, public_key: bytes, plaintext: str) -> str:
        """
        Encrypts a plaintext string using the PQC hybrid scheme.

        Returns:
            A single base64-encoded string containing all necessary components.
        """
        # 1. Use Kyber to establish a secure, one-time symmetric key
        kyber_ciphertext, shared_secret = self.kem.encapsulate(public_key)
        
        # 2. Use that shared secret to encrypt the data with AES-GCM
        aesgcm = AESGCM(shared_secret)
        nonce = os.urandom(12) # Generate a random 12-byte nonce
        aes_ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        
        # 3. Bundle all parts and base64-encode for easy storage
        # We store kyber_ciphertext, nonce, and the aes_ciphertext
        b64_kyber_ct = base64.b64encode(kyber_ciphertext).decode('utf-8')
        b64_nonce = base64.b64encode(nonce).decode('utf-8')
        b64_aes_ct = base64.b64encode(aes_ciphertext).decode('utf-8')
        
        # Join with a separator that is not in the base64 character set
        return f"{b64_kyber_ct}:{b64_nonce}:{b64_aes_ct}"

    def decrypt_secret(self, private_key: bytes, encrypted_blob: str) -> Optional[str]:
        """
        Decrypts a secret from the vault using the PQC hybrid scheme.
        """
        try:
            # 1. Unpack the bundled, base64-encoded data
            b64_kyber_ct, b64_nonce, b64_aes_ct = encrypted_blob.split(':')
            kyber_ciphertext = base64.b64decode(b64_kyber_ct)
            nonce = base64.b64decode(b64_nonce)
            aes_ciphertext = base64.b64decode(b64_aes_ct)
            
            # 2. Use Kyber private key to derive the one-time symmetric key
            shared_secret = self.kem.decapsulate(private_key, kyber_ciphertext)
            
            # 3. Use that key to decrypt the data with AES-GCM
            aesgcm = AESGCM(shared_secret)
            decrypted_bytes = aesgcm.decrypt(nonce, aes_ciphertext, None)
            
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed! The data may be corrupt or the key incorrect. Error: {e}")
            return None

    def add_item(self, public_key: bytes, item_name: str, item_value: str):
        """Encrypts and adds an item to the vault."""
        logger.info(f"Adding '{item_name}' to the vault...")
        encrypted_blob = self.encrypt_secret(public_key, item_value)
        self.vault_data[item_name] = encrypted_blob
        self._save_vault()

    def get_item(self, private_key: bytes, item_name: str) -> Optional[str]:
        """Retrieves and decrypts an item from the vault."""
        logger.info(f"Retrieving '{item_name}' from the vault...")
        encrypted_blob = self.vault_data.get(item_name)
        if not encrypted_blob:
            logger.warning(f"Item '{item_name}' not found in vault.")
            return None
        return self.decrypt_secret(private_key, encrypted_blob)


# --- Example Usage ---
if __name__ == "__main__":
    if not all([KYBER_AVAILABLE, CRYPTOGRAPHY_AVAILABLE]):
        print("\nERROR: Missing required libraries. Please run: pip install pykyber cryptography")
    else:
        print("=========================================================")
        print("=== Quantum-Resistant Vault Prototype ⚛️️🛡️ ===")
        print("=========================================================")
        
        # --- File paths for the demo ---
        vault_file = Path("my_secure_vault.json")
        pub_key_file = Path("vault_key.pub")
        priv_key_file = Path("vault_key.priv")
        
        try:
            # 1. Generate master keys for the vault (a one-time setup)
            print("\nStep 1: Generating a new Post-Quantum key pair for the vault...")
            kem = KyberKEM()
            public_key, private_key = kem.generate_keypair()
            # In a real app, you would save these securely. For the demo, we just hold them in memory.
            print("Key pair generated successfully.")
            
            # 2. Initialize the vault
            vault = QuantumVault(vault_path=vault_file)
            
            # 3. Add a secret to the vault
            print("\nStep 2: Adding a secret API key to the vault...")
            secret_to_store = "openai_sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            vault.add_item(public_key, item_name="openai_api_key", item_value=secret_to_store)
            print("Secret has been encrypted and stored.")
            
            # Show the encrypted content in the vault file
            with open(vault_file, 'r') as f:
                print("\nEncrypted content in vault file:")
                print(f.read())
            
            # 4. Retrieve and decrypt the secret from the vault
            print("\nStep 3: Retrieving and decrypting the secret...")
            retrieved_secret = vault.get_item(private_key, "openai_api_key")
            
            if retrieved_secret:
                print(f"  - Decrypted value: '{retrieved_secret}'")
            else:
                print("  - Failed to retrieve secret.")
                
            # 5. Verification
            print("\nStep 4: Verifying data integrity...")
            if retrieved_secret == secret_to_store:
                print("  [SUCCESS] The retrieved secret matches the original!")
            else:
                print("  [FAILURE] Data mismatch after decryption.")

        finally:
            # Clean up demo files
            for f in [vault_file, pub_key_file, priv_key_file]:
                if f.exists():
                    f.unlink()

    print("\n=========================================================")
    print("=== Quantum Vault Prototype Complete ===")
    print("=========================================================")
