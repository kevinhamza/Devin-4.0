# Devin/security/key_manager.py
# Purpose: A robust tool for generating and managing RSA cryptographic key
#          pairs and performing asymmetric encryption and decryption.

import logging
from pathlib import Path
from typing import Optional

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization, hashes
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("KeyManager")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class KeyManager:
    """
    Handles the lifecycle of RSA keys for asymmetric encryption.
    """
    def __init__(self):
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError("The 'cryptography' library is required. 'pip install cryptography'")
    
    def generate_rsa_keypair(self, private_key_path: Path, public_key_path: Path, key_size: int = 4096, password: Optional[str] = None):
        """
        Generates a new RSA private and public key pair and saves them to files.
        """
        logger.info(f"Generating a new {key_size}-bit RSA key pair...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        
        # Determine encryption algorithm for the private key
        encryption_algorithm = serialization.BestAvailableEncryption(password.encode()) if password else serialization.NoEncryption()

        # Serialize and save the private key
        pem_private = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm
        )
        with open(private_key_path, 'wb') as f:
            f.write(pem_private)
        logger.warning(f"Private key saved to: {private_key_path}")

        # Serialize and save the public key
        public_key = private_key.public_key()
        pem_public = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        with open(public_key_path, 'wb') as f:
            f.write(pem_public)
        logger.info(f"Public key saved to: {public_key_path}")

    def load_private_key(self, private_key_path: Path, password: Optional[str] = None):
        """Loads an RSA private key from a PEM file."""
        with open(private_key_path, 'rb') as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=password.encode() if password else None
            )

    def load_public_key(self, public_key_path: Path):
        """Loads an RSA public key from a PEM file."""
        with open(public_key_path, 'rb') as f:
            return serialization.load_pem_public_key(f.read())
            
    def encrypt(self, public_key, message: bytes) -> bytes:
        """Encrypts a message using the public key (RSA-OAEP)."""
        return public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def decrypt(self, private_key, ciphertext: bytes) -> bytes:
        """Decrypts a ciphertext using the private key."""
        return private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Cryptographic Key Manager Prototype 🔑🔐 ===")
    print("=========================================================")
    
    if not CRYPTOGRAPHY_AVAILABLE:
        print("\nERROR: The 'cryptography' library is required. 'pip install cryptography'")
    else:
        manager = KeyManager()
        priv_path = Path("demo_private_key.pem")
        pub_path = Path("demo_public_key.pem")
        
        try:
            # 1. Generate a key pair
            print("\n--- 1. Generating a new 2048-bit RSA key pair ---")
            manager.generate_rsa_keypair(priv_path, pub_path, key_size=2048)
            
            # 2. Encrypt a message with the public key
            print("\n--- 2. Encrypting a secret message ---")
            public_key = manager.load_public_key(pub_path)
            secret_message = b"This is a top secret message for Devin."
            print(f"Original message: {secret_message.decode()}")
            ciphertext = manager.encrypt(public_key, secret_message)
            print(f"Ciphertext (first 30 bytes): {ciphertext[:30].hex()}...")
            
            # 3. Decrypt the message with the private key
            print("\n--- 3. Decrypting the ciphertext ---")
            private_key = manager.load_private_key(priv_path)
            decrypted_message = manager.decrypt(private_key, ciphertext)
            print(f"Decrypted message: {decrypted_message.decode()}")
            
            # 4. Verification
            print("\n--- 4. Verification ---")
            assert secret_message == decrypted_message
            print("[SUCCESS] Decrypted message matches the original!")
            
        finally:
            # Clean up the demo key files
            if priv_path.exists(): priv_path.unlink()
            if pub_path.exists(): pub_path.unlink()
            
    print("\n=========================================================")
    print("=== Key Manager Prototype Complete ===")
    print("=========================================================")
