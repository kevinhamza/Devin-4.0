# # Devin/modules/encryption_tools.py
# # Purpose: Provides a suite of cryptographic utilities for hashing, encryption,
# #          decryption, and digital signatures.
# # Cryptographic utilities 🔐

# import logging
# import os
# import base64
# from typing import Optional, Tuple, Union

# # Configure basic logging
# logger = logging.getLogger("EncryptionTools")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class HashingTools:
#     """
#     Provides tools for creating cryptographic hashes.
#     Conceptually wraps 'cryptography.hazmat.primitives.hashes'.
#     """
#     def __init__(self):
#         logger.info("HashingTools initialized.")

#     def hash_data(self, data: bytes, algorithm: str = 'sha256') -> Optional[str]:
#         """
#         Conceptually hashes binary data using a specified algorithm.

#         Args:
#             data (bytes): The data to hash.
#             algorithm (str): The hashing algorithm (e.g., 'sha256', 'sha512').

#         Returns:
#             Optional[str]: The hexadecimal representation of the hash digest.
#         """
#         if algorithm.lower() not in ['sha256', 'sha512', 'blake2b']:
#             logger.error(f"Unsupported hash algorithm: {algorithm}")
#             return None
            
#         logger.info(f"CONCEPTUAL: Hashing {len(data)} bytes using '{algorithm.upper()}'.")
#         # In a real system:
#         # from cryptography.hazmat.primitives import hashes
#         # digest = hashes.Hash(hashes.SHA256())
#         # digest.update(data)
#         # return digest.finalize().hex()
        
#         # Simulate the hash output
#         # A simple hash of the data's properties for a deterministic-looking but fake hash
#         conceptual_hash = hex(hash((len(data), data[:16], algorithm)))[2:]
#         return conceptual_hash * (64 // len(conceptual_hash) + 1) # Make it look like a real hash length

# class SymmetricCryptoTools:
#     """
#     Provides tools for symmetric encryption and decryption (e.g., AES).
#     Conceptually wraps 'cryptography.fernet'.
#     """
#     def __init__(self, key: Optional[bytes] = None):
#         """
#         Initializes with a symmetric key. If no key is provided, one is generated.
#         """
#         if key:
#             self.key = key
#             logger.info("SymmetricCryptoTools initialized with an existing key.")
#         else:
#             self.key = self.generate_key()
#             logger.info("SymmetricCryptoTools initialized and generated a new symmetric key.")

#     @staticmethod
#     def generate_key() -> bytes:
#         """
#         Conceptually generates a new URL-safe base64-encoded 32-byte key.
#         Real-world equivalent: `cryptography.fernet.Fernet.generate_key()`
#         """
#         logger.info("CONCEPTUAL: Generating new Fernet symmetric key.")
#         # Fernet keys are 32 random bytes, base64 encoded.
#         return base64.urlsafe_b64encode(os.urandom(32))

#     def encrypt(self, plaintext: bytes) -> Optional[bytes]:
#         """Conceptually encrypts data using the symmetric key."""
#         logger.info(f"CONCEPTUAL: Encrypting {len(plaintext)} bytes of data using Fernet symmetric encryption.")
#         # Real-world:
#         # from cryptography.fernet import Fernet
#         # f = Fernet(self.key)
#         # return f.encrypt(plaintext)
        
#         # Simulate encryption: result is base64(plaintext + "::encrypted_by::" + key_signature)
#         # This is NOT secure, it's just a placeholder to make the data look different.
#         key_signature = self.key[:8]
#         encrypted_data = base64.b64encode(plaintext + b"::encrypted_by::" + key_signature)
#         return encrypted_data

#     def decrypt(self, ciphertext: bytes) -> Optional[bytes]:
#         """Conceptually decrypts data using the symmetric key."""
#         logger.info(f"CONCEPTUAL: Decrypting {len(ciphertext)} bytes of data using Fernet symmetric encryption.")
#         # Real-world:
#         # from cryptography.fernet import Fernet
#         # f = Fernet(self.key)
#         # try:
#         #     return f.decrypt(ciphertext)
#         # except InvalidToken:
#         #     return None
        
#         # Simulate decryption by reversing the conceptual encryption
#         try:
#             decoded_data = base64.b64decode(ciphertext)
#             key_signature = self.key[:8]
#             if decoded_data.endswith(b"::encrypted_by::" + key_signature):
#                 return decoded_data.removesuffix(b"::encrypted_by::" + key_signature)
#             else:
#                 logger.error("Decryption failed: conceptual ciphertext is malformed or key is incorrect.")
#                 return None
#         except Exception as e:
#             logger.error(f"Decryption failed: {e}")
#             return None

# class AsymmetricCryptoTools:
#     """
#     Provides tools for asymmetric cryptography (e.g., RSA).
#     Conceptually wraps 'cryptography.hazmat.primitives.asymmetric'.
#     """
#     def __init__(self, private_key_placeholder: Optional[str] = None):
#         if private_key_placeholder:
#             self.private_key = private_key_placeholder
#             self.public_key = f"public_key_derived_from_{private_key_placeholder[:20]}"
#             logger.info("AsymmetricCryptoTools initialized with an existing key pair.")
#         else:
#             self.private_key, self.public_key = self.generate_key_pair()
#             logger.info("AsymmetricCryptoTools initialized and generated a new RSA key pair.")

#     @staticmethod
#     def generate_key_pair(key_size: int = 2048) -> Tuple[str, str]:
#         """
#         Conceptually generates an RSA private/public key pair.
#         Real-world equivalent: Uses `cryptography.hazmat.primitives.asymmetric.rsa`.
#         """
#         logger.info(f"CONCEPTUAL: Generating new RSA {key_size}-bit key pair.")
#         # Simulate PEM-formatted keys
#         private_key_id = uuid.uuid4().hex
#         private_key = f"-----BEGIN CONCEPTUAL RSA PRIVATE KEY-----\n{private_key_id}\n-----END CONCEPTUAL RSA PRIVATE KEY-----"
#         public_key = f"-----BEGIN CONCEPTUAL PUBLIC KEY-----\npublic_for_{private_key_id}\n-----END CONCEPTUAL PUBLIC KEY-----"
#         return private_key, public_key

#     def sign_data(self, data: bytes) -> Optional[str]:
#         """
#         Conceptually creates a digital signature for data using the private key.
#         Real-world equivalent: `private_key.sign(data, padding, algorithm)`
#         """
#         logger.info(f"CONCEPTUAL: Signing {len(data)} bytes of data with private key using RSA-PSS and SHA256.")
#         # Simulate a signature
#         conceptual_signature = hex(hash((data, self.private_key)))[2:]
#         return base64.b64encode(conceptual_signature.encode('utf-8')).decode('utf-8')

#     def verify_signature(self, signature: str, data: bytes) -> bool:
#         """
#         Conceptually verifies a digital signature using the public key.
#         Real-world equivalent: `public_key.verify(signature, data, padding, algorithm)`
#         """
#         logger.info(f"CONCEPTUAL: Verifying signature for {len(data)} bytes of data with public key.")
#         # Simulate verification by re-calculating the conceptual signature
#         try:
#             expected_signature_b64 = base64.b64encode(hex(hash((data, self.private_key)))[2:].encode('utf-8')).decode('utf-8')
#             is_valid = (signature == expected_signature_b64)
#             logger.info(f"  Signature verification result: {'VALID' if is_valid else 'INVALID'}")
#             return is_valid
#         except Exception as e:
#             logger.error(f"  Signature verification failed with an error: {e}")
#             return False

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== Cryptographic Tools Module Prototype 🔐 ===")
#     print("=========================================================")

#     # --- 1. Hashing Demonstration ---
#     print("\n--- Hashing Tools ---")
#     hasher = HashingTools()
#     original_data = b"Devin needs to verify file integrity."
#     data_hash = hasher.hash_data(original_data, algorithm='sha256')
#     print(f"  Original Data: '{original_data.decode()}'")
#     print(f"  SHA-256 Hash (conceptual): {data_hash}")
#     print("")

#     # --- 2. Symmetric Encryption Demonstration ---
#     print("\n--- Symmetric (AES/Fernet) Crypto Tools ---")
#     # Initialize to generate a new key
#     symmetric_tool = SymmetricCryptoTools()
#     print(f"  Generated Symmetric Key (conceptual): {symmetric_tool.key.decode()[:20]}...")
    
#     secret_message = b"This is a secret plan for the task orchestrator."
#     print(f"  Plaintext: '{secret_message.decode()}'")
    
#     # Encrypt
#     encrypted_message = symmetric_tool.encrypt(secret_message)
#     print(f"  Encrypted (conceptual): {encrypted_message[:40]}...")
    
#     # Decrypt
#     decrypted_message = symmetric_tool.decrypt(encrypted_message)
#     print(f"  Decrypted: '{decrypted_message.decode() if decrypted_message else 'DECRYPTION FAILED'}'")
    
#     # Test decryption with a wrong key
#     wrong_key_tool = SymmetricCryptoTools()
#     failed_decryption = wrong_key_tool.decrypt(encrypted_message)
#     print(f"  Attempting decryption with wrong key: {'Success (this should not happen!)' if failed_decryption else 'DECRYPTION FAILED (Correct!)'}")
#     print("")

#     # --- 3. Asymmetric Encryption & Digital Signature Demonstration ---
#     print("\n--- Asymmetric (RSA) Crypto Tools ---")
#     asymmetric_tool = AsymmetricCryptoTools()
#     print(f"  Generated Private Key (conceptual):\n{asymmetric_tool.private_key}\n")
#     print(f"  Generated Public Key (conceptual):\n{asymmetric_tool.public_key}\n")
    
#     message_to_sign = b"This task was authorized by the user at " + str(datetime.now()).encode('utf-8')
#     print(f"  Message to Sign: '{message_to_sign.decode()}'")
    
#     # Sign data with private key
#     signature = asymmetric_tool.sign_data(message_to_sign)
#     print(f"  Digital Signature (conceptual): {signature}")
    
#     # Verify signature with public key
#     print("\n  Verifying with the correct public key...")
#     is_valid = asymmetric_tool.verify_signature(signature, message_to_sign)
    
#     # Tamper with the data and try to verify again
#     print("\n  Verifying with tampered data...")
#     tampered_message = message_to_sign + b" and I am altering the deal."
#     is_valid_tampered = asymmetric_tool.verify_signature(signature, tampered_message)
    
#     print("\n=========================================================")
#     print("=== Crypto Tools Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/encryption_tools.py
# Purpose: A functional, production-ready suite of cryptographic utilities for
#          hashing, encryption, decryption, and digital signatures.

import logging
import os
import base64
from typing import Optional, Tuple

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("EncryptionTools")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class HashingTools:
    """Provides tools for creating cryptographic hashes using hashlib."""
    def __init__(self):
        logger.info("HashingTools initialized.")

    def hash_data(self, data: bytes, algorithm: str = 'sha256') -> Optional[str]:
        """Hashes binary data using a specified algorithm."""
        try:
            hasher = hashlib.new(algorithm)
            hasher.update(data)
            return hasher.hexdigest()
        except ValueError:
            logger.error(f"Unsupported hash algorithm: {algorithm}")
            return None

class SymmetricCryptoTools:
    """Provides tools for symmetric encryption using cryptography.fernet."""
    def __init__(self, key: Optional[bytes] = None):
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError("Cryptography library is required. 'pip install cryptography'")
        
        self.key = key or Fernet.generate_key()
        self.fernet = Fernet(self.key)
        logger.info("SymmetricCryptoTools initialized.")

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypts data using the symmetric key."""
        return self.fernet.encrypt(plaintext)

    def decrypt(self, ciphertext: bytes) -> Optional[bytes]:
        """Decrypts data using the symmetric key."""
        try:
            return self.fernet.decrypt(ciphertext)
        except InvalidToken:
            logger.error("Decryption failed: Invalid token or incorrect key.")
            return None

class AsymmetricCryptoTools:
    """Provides tools for asymmetric cryptography (RSA)."""
    def __init__(self, private_key: Optional[rsa.RSAPrivateKey] = None):
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError("Cryptography library is required. 'pip install cryptography'")
        
        if private_key:
            self.private_key = private_key
        else:
            self.private_key = self.generate_private_key()
        
        self.public_key = self.private_key.public_key()
        logger.info("AsymmetricCryptoTools initialized.")

    @staticmethod
    def generate_private_key(key_size: int = 4096) -> rsa.RSAPrivateKey:
        """Generates a new RSA private key."""
        logger.info(f"Generating new {key_size}-bit RSA private key...")
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )

    def get_pem_keys(self) -> Tuple[bytes, bytes]:
        """Returns the private and public keys in PEM format."""
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return private_pem, public_pem

    def sign_data(self, data: bytes) -> bytes:
        """Creates a digital signature for data using the private key."""
        return self.private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

    def verify_signature(self, signature: bytes, data: bytes) -> bool:
        """Verifies a digital signature using the public key."""
        try:
            self.public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            logger.warning("Signature verification failed: Signature is invalid.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during verification: {e}")
            return False

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated Cryptographic Tools Prototype 🔐 ===")
    print("=========================================================")

    if not CRYPTOGRAPHY_AVAILABLE:
        print("\nERROR: The 'cryptography' library is required. 'pip install cryptography'")
    else:
        # --- 1. Hashing Demonstration ---
        print("\n--- 1. Hashing Tools ---")
        hasher = HashingTools()
        original_data = b"Devin must ensure the integrity of this data."
        data_hash = hasher.hash_data(original_data, algorithm='sha256')
        print(f"  Original Data: '{original_data.decode()}'")
        print(f"  SHA-256 Hash: {data_hash}")

        # --- 2. Symmetric Encryption Demonstration ---
        print("\n\n--- 2. Symmetric (AES/Fernet) Crypto Tools ---")
        symmetric_tool = SymmetricCryptoTools()
        secret_message = b"This is a secret message that is encrypted and authenticated."
        print(f"  Plaintext: '{secret_message.decode()}'")
        
        encrypted_message = symmetric_tool.encrypt(secret_message)
        print(f"  Encrypted Token (Ciphertext + Auth Tag): {base64.urlsafe_b64encode(encrypted_message).decode()[:60]}...")
        
        decrypted_message = symmetric_tool.decrypt(encrypted_message)
        print(f"  Decrypted: '{decrypted_message.decode()}'")
        assert secret_message == decrypted_message

        # --- 3. Asymmetric Digital Signature Demonstration ---
        print("\n\n--- 3. Asymmetric (RSA) Digital Signatures ---")
        asymmetric_tool = AsymmetricCryptoTools()
        message_to_sign = f"This action was authorized at {datetime.now(timezone.utc).isoformat()}".encode()
        print(f"  Message to Sign: '{message_to_sign.decode()}'")
        
        signature = asymmetric_tool.sign_data(message_to_sign)
        print(f"  Digital Signature (Base64): {base64.b64encode(signature).decode()[:60]}...")
        
        print("\n  Verifying with the correct public key and original message...")
        is_valid = asymmetric_tool.verify_signature(signature, message_to_sign)
        print(f"    -> Signature is VALID: {is_valid}")
        assert is_valid is True
        
        print("\n  Verifying with tampered data...")
        tampered_message = message_to_sign + b" (this part was added by an attacker)"
        is_valid_tampered = asymmetric_tool.verify_signature(signature, tampered_message)
        print(f"    -> Signature is VALID: {is_valid_tampered}")
        assert is_valid_tampered is False

    print("\n=========================================================")
    print("=== Crypto Tools Prototype Complete ===")
    print("=========================================================")
