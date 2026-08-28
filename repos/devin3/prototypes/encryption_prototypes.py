# Devin/prototypes/encryption_prototypes.py
# Purpose: Prototype implementations for common cryptographic operations.

import os
import logging
from typing import Dict, Any, Optional, Tuple, Union

# --- Conceptual Imports for Cryptography Library ---
# Requires 'cryptography': pip install cryptography
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import hashes, padding as sym_padding # Padding often not needed for AEAD modes like GCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC # For deriving keys from passwords (example)
    from cryptography.hazmat.primitives.asymmetric import rsa, padding as asymmetric_padding
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    from cryptography.exceptions import InvalidTag # Specific exception for AEAD integrity failure
    CRYPTO_LIB_AVAILABLE = True
    print("Conceptual: Assuming 'cryptography' library is available.")
except ImportError:
    print("WARNING: 'cryptography' library not found (pip install cryptography). Encryption prototypes will be non-functional placeholders.")
    Cipher = None; algorithms = None; modes = None; hashes = None; PBKDF2HMAC = None # type: ignore
    rsa = None; asymmetric_padding = None; serialization = None; default_backend = None # type: ignore
    InvalidTag = None # type: ignore
    CRYPTO_LIB_AVAILABLE = False

import hashlib # Standard library for basic hashing included as well

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("EncryptionPrototypes")

# --- CRITICAL SECURITY WARNINGS ---
logger.critical("############################################################")
logger.critical("!!! CRYPTOGRAPHY WARNING !!!")
logger.critical("Improper use of cryptography can lead to severe security vulnerabilities.")
logger.critical("ALWAYS use standard, well-vetted libraries (like 'cryptography').")
logger.critical("NEVER implement cryptographic algorithms yourself.")
logger.critical("SECURE KEY MANAGEMENT IS PARAMOUNT AND NOT HANDLED HERE.")
logger.critical("Consult security experts for production cryptographic implementations.")
logger.critical("############################################################")


# --- Symmetric Encryption (AES-GCM) ---
# AES-GCM is generally recommended as it provides Authenticated Encryption
# with Associated Data (AEAD), meaning it ensures both confidentiality and integrity/authenticity.

def generate_aes_key(key_size_bytes: int = 32) -> Optional[bytes]:
    """
    Generates a cryptographically secure random key suitable for AES.

    Args:
        key_size_bytes (int): Desired key size in bytes (16 for AES-128, 24 for AES-192, 32 for AES-256).
                              Defaults to 32 bytes (AES-256).

    Returns:
        Optional[bytes]: The generated key, or None if generation fails.
    """
    logger.info(f"Generating new {key_size_bytes*8}-bit AES key...")
    if key_size_bytes not in [16, 24, 32]:
        logger.error("Invalid AES key size. Must be 16, 24, or 32 bytes.")
        return None
    try:
        key = os.urandom(key_size_bytes)
        logger.info(f"Generated {len(key)*8}-bit key successfully.")
        return key
    except Exception as e:
        logger.error(f"Failed to generate secure random key: {e}")
        return None

def encrypt_aes_gcm(key: bytes, plaintext: bytes, associated_data: Optional[bytes] = None) -> Optional[Dict[str, bytes]]:
    """
    Encrypts plaintext using AES-GCM (Authenticated Encryption).

    Args:
        key (bytes): The AES key (16, 24, or 32 bytes).
        plaintext (bytes): The data to encrypt.
        associated_data (Optional[bytes]): Optional additional authenticated data (AAD).
                                           This data is NOT encrypted but IS integrity-protected.
                                           It must be provided during decryption as well.

    Returns:
        Optional[Dict[str, bytes]]: A dictionary containing 'ciphertext', 'nonce' (IV), and 'tag'.
                                    Returns None on error.
    """
    if not CRYPTO_LIB_AVAILABLE:
        logger.error("Cannot encrypt: cryptography library not available.")
        return None
    if len(key) not in [16, 24, 32]:
        logger.error("Invalid AES key size for encryption.")
        return None
    if not isinstance(plaintext, bytes):
        logger.error("Plaintext must be bytes for encryption.")
        return None # Or try encoding? Safer to require bytes.

    logger.info(f"Encrypting {len(plaintext)} bytes using AES-GCM...")
    try:
        # 1. Generate a unique nonce (IV) for each encryption - NEVER REUSE WITH THE SAME KEY
        # GCM standard nonce size is 12 bytes (96 bits).
        nonce = os.urandom(12)

        # 2. Create AES-GCM Cipher context
        encryptor = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=default_backend()
        ).encryptor()

        # 3. Add Associated Data (AAD) if provided (integrity protected, not encrypted)
        if associated_data:
            if not isinstance(associated_data, bytes): raise TypeError("Associated data must be bytes.")
            logger.debug(f"  - Adding {len(associated_data)} bytes of associated data.")
            encryptor.authenticate_additional_data(associated_data)

        # 4. Encrypt plaintext
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        # 5. Get the authentication tag (appended by finalize(), or accessed via encryptor.tag)
        # The tag is crucial for integrity and authenticity verification during decryption.
        tag = encryptor.tag

        logger.info("  - Encryption successful.")
        result = {
            "ciphertext": ciphertext,
            "nonce": nonce,
            "tag": tag
        }
        # Include AAD in result if it was used, as it's needed for decryption
        if associated_data:
             result["aad"] = associated_data

        return result

    except Exception as e:
        logger.error(f"AES-GCM encryption failed: {e}")
        return None


def decrypt_aes_gcm(key: bytes, encrypted_data: Dict[str, bytes]) -> Optional[bytes]:
    """
    Decrypts ciphertext using AES-GCM, verifying integrity and authenticity.

    Args:
        key (bytes): The AES key (must match the one used for encryption).
        encrypted_data (Dict[str, bytes]): The dictionary returned by encrypt_aes_gcm,
                                           must contain 'ciphertext', 'nonce', and 'tag'.
                                           Must also contain 'aad' if it was used during encryption.

    Returns:
        Optional[bytes]: The original plaintext if decryption and verification succeed,
                         otherwise None (e.g., if the tag is invalid, indicating tampering or wrong key).
    """
    if not CRYPTO_LIB_AVAILABLE:
        logger.error("Cannot decrypt: cryptography library not available.")
        return None
    if len(key) not in [16, 24, 32]:
        logger.error("Invalid AES key size for decryption.")
        return None
    if not all(k in encrypted_data for k in ["ciphertext", "nonce", "tag"]):
        logger.error("Invalid encrypted data format: missing 'ciphertext', 'nonce', or 'tag'.")
        return None

    ciphertext = encrypted_data["ciphertext"]
    nonce = encrypted_data["nonce"]
    tag = encrypted_data["tag"]
    associated_data = encrypted_data.get("aad") # Get AAD if present

    logger.info(f"Decrypting {len(ciphertext)} bytes using AES-GCM...")

    try:
        # Create AES-GCM Cipher context
        decryptor = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag), # Pass the tag for verification
            backend=default_backend()
        ).decryptor()

        # Provide Associated Data (AAD) if it was used during encryption
        # THIS MUST MATCH THE AAD USED DURING ENCRYPTION EXACTLY.
        if associated_data:
            logger.debug(f"  - Verifying {len(associated_data)} bytes of associated data.")
            decryptor.authenticate_additional_data(associated_data)

        # Decrypt and verify authenticity tag simultaneously
        # If the tag is invalid (data tampered, wrong key, wrong AAD),
        # finalize() will raise an InvalidTag exception.
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        logger.info("  - Decryption and integrity verification successful.")
        return plaintext

    except InvalidTag:
        logger.error("DECRYPTION FAILED: Integrity check failed (Invalid Tag). Data may be corrupted, tampered with, or the key/nonce/AAD is incorrect.")
        return None
    except Exception as e:
        logger.error(f"AES-GCM decryption failed with unexpected error: {e}")
        return None

# Ensure logger and necessary conceptual imports/constants from Part 1 are available
import logging
logger = logging.getLogger("EncryptionPrototypes")
import os
from typing import Dict, Any, Optional, Tuple, Union
# Conceptual imports (ensure they are defined or guarded in Part 1)
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding as asymmetric_padding
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC # Example KDF
    from cryptography.hazmat.backends import default_backend
    from cryptography.exceptions import InvalidSignature
    CRYPTO_LIB_AVAILABLE = True # Assumes Part 1 confirmed availability
except ImportError:
    # Define dummies if needed for structure if Part 1 failed import
    hashes = None; serialization = None; rsa = None; asymmetric_padding = None; default_backend = None; InvalidSignature = Exception; PBKDF2HMAC = None # type: ignore
    CRYPTO_LIB_AVAILABLE = False

import hashlib


# --- Asymmetric Encryption (RSA with OAEP Padding) ---
# Good for encrypting small amounts of data (like symmetric keys) or for key exchange.
# Requires separate public (for encryption) and private (for decryption) keys.

# Key management (generation, storage, distribution) is CRITICAL and complex.
# These functions assume PEM-formatted keys are provided securely as strings.

def generate_rsa_key_pair_placeholder(key_size: int = 2048) -> Optional[Tuple[str, str]]:
    """
    Conceptually generates an RSA public/private key pair in PEM format.
    Requires 'cryptography' library.

    Args:
        key_size (int): Key size in bits (2048 or higher recommended).

    Returns:
        Optional[Tuple[str, str]]: (private_key_pem, public_key_pem), or None on error.
    """
    if not CRYPTO_LIB_AVAILABLE or not rsa:
        logger.error("Cannot generate RSA keys: cryptography library not available.")
        return None
    logger.info(f"Generating conceptual {key_size}-bit RSA key pair...")
    try:
        # --- Conceptual cryptography Call ---
        # private_key = rsa.generate_private_key(
        #     public_exponent=65537,
        #     key_size=key_size,
        #     backend=default_backend()
        # )
        # # Serialize private key to PEM (securely store this!)
        # # Use password protection for private key PEM in production
        # private_pem = private_key.private_bytes(
        #     encoding=serialization.Encoding.PEM,
        #     format=serialization.PrivateFormat.PKCS8,
        #     encryption_algorithm=serialization.NoEncryption() # Use BestAvailableEncryption(b'password') for protection
        # ).decode('utf-8')
        #
        # # Serialize public key to PEM (can be shared)
        # public_key = private_key.public_key()
        # public_pem = public_key.public_bytes(
        #     encoding=serialization.Encoding.PEM,
        #     format=serialization.PublicFormat.SubjectPublicKeyInfo
        # ).decode('utf-8')
        # --- End Conceptual ---

        # Simulate PEM output
        private_pem = f"-----BEGIN PRIVATE KEY-----\n(Conceptual {key_size}-bit RSA Private Key Data for simulation)\n-----END PRIVATE KEY-----"
        public_pem = f"-----BEGIN PUBLIC KEY-----\n(Conceptual {key_size}-bit RSA Public Key Data for simulation)\n-----END PUBLIC KEY-----"

        logger.info("  - Conceptual RSA key pair generated.")
        return private_pem, public_pem

    except Exception as e:
        logger.error(f"Error generating RSA key pair: {e}")
        return None

def encrypt_rsa_oaep(public_key_pem: str, plaintext: bytes) -> Optional[bytes]:
    """
    Encrypts small plaintext using RSA public key with OAEP padding.

    Args:
        public_key_pem (str): The recipient's public key in PEM format.
        plaintext (bytes): The data to encrypt (must be small enough for RSA key size and padding).

    Returns:
        Optional[bytes]: Encrypted ciphertext, or None on error.
    """
    if not CRYPTO_LIB_AVAILABLE or not serialization or not asymmetric_padding:
        logger.error("Cannot RSA encrypt: cryptography library not available.")
        return None
    logger.info(f"Encrypting {len(plaintext)} bytes using RSA-OAEP...")
    try:
        # --- Conceptual cryptography Call ---
        # public_key = serialization.load_pem_public_key(
        #     public_key_pem.encode('utf-8'),
        #     backend=default_backend()
        # )
        # if not isinstance(public_key, rsa.RSAPublicKey): raise TypeError("Not an RSA public key")
        #
        # # Check plaintext size against key size and padding limits
        # # OAEP with SHA256 uses 2*32 + 2 = 66 bytes overhead.
        # max_len = public_key.key_size // 8 - 2 * hashes.SHA256.digest_size - 2
        # if len(plaintext) > max_len:
        #     raise ValueError(f"Plaintext too long ({len(plaintext)} bytes) for RSA key size and OAEP padding (max: {max_len}).")
        #
        # ciphertext = public_key.encrypt(
        #     plaintext,
        #     asymmetric_padding.OAEP(
        #         mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
        #         algorithm=hashes.SHA256(),
        #         label=None
        #     )
        # )
        # --- End Conceptual ---

        # Simulate encryption
        if not isinstance(plaintext, bytes): raise TypeError("Plaintext must be bytes")
        ciphertext = b"(Simulated RSA Encrypted Data for: " + plaintext[:20] + b")"
        logger.info("  - Conceptual RSA encryption successful.")
        return ciphertext

    except Exception as e:
        logger.error(f"RSA encryption failed: {e}")
        return None

def decrypt_rsa_oaep(private_key_pem: str, ciphertext: bytes) -> Optional[bytes]:
    """
    Decrypts small ciphertext using RSA private key with OAEP padding.

    Args:
        private_key_pem (str): The recipient's private key in PEM format.
                               (Needs password if PEM is encrypted).
        ciphertext (bytes): The encrypted data to decrypt.

    Returns:
        Optional[bytes]: Original plaintext bytes, or None on error (e.g., wrong key, decryption failure).
    """
    if not CRYPTO_LIB_AVAILABLE or not serialization or not asymmetric_padding:
        logger.error("Cannot RSA decrypt: cryptography library not available.")
        return None
    logger.info(f"Decrypting {len(ciphertext)} bytes using RSA-OAEP...")
    try:
        # --- Conceptual cryptography Call ---
        # Load private key (handle password if PEM is encrypted)
        # private_key = serialization.load_pem_private_key(
        #     private_key_pem.encode('utf-8'),
        #     password=None, # Provide password bytes if key is encrypted: password=b'mypassword'
        #     backend=default_backend()
        # )
        # if not isinstance(private_key, rsa.RSAPrivateKey): raise TypeError("Not an RSA private key")
        #
        # plaintext = private_key.decrypt(
        #     ciphertext,
        #     asymmetric_padding.OAEP(
        #         mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
        #         algorithm=hashes.SHA256(),
        #         label=None
        #     )
        # )
        # --- End Conceptual ---

        # Simulate decryption
        if ciphertext.startswith(b"(Simulated RSA Encrypted Data for: "):
             plaintext = ciphertext[len(b"(Simulated RSA Encrypted Data for: "):-1]
             logger.info("  - Conceptual RSA decryption successful.")
             return plaintext
        else:
             raise ValueError("Invalid simulated ciphertext format")

    except ValueError as e: # Catch decryption errors (often padding errors indicate wrong key)
        logger.error(f"RSA decryption failed (likely wrong key or corrupted data): {e}")
        return None
    except Exception as e:
        logger.error(f"RSA decryption failed with unexpected error: {e}")
        return None


# --- Hashing (Standard Library) ---

def hash_data(data: bytes, algorithm: str = 'sha256') -> Optional[str]:
    """
    Calculates the cryptographic hash of data using hashlib.

    Args:
        data (bytes): The input data (as bytes).
        algorithm (str): Hash algorithm name (e.g., 'sha256', 'sha512', 'md5').
                         Defaults to 'sha256'.

    Returns:
        Optional[str]: The hexadecimal digest of the hash, or None if algorithm is invalid.
    """
    logger.info(f"Calculating {algorithm} hash for {len(data)} bytes...")
    if not isinstance(data, bytes):
        logger.error("Hashing requires input data as bytes.")
        return None
    try:
        hasher = hashlib.new(algorithm)
        hasher.update(data)
        hex_digest = hasher.hexdigest()
        logger.info(f"  - {algorithm.upper()} Hash: {hex_digest}")
        return hex_digest
    except ValueError:
        logger.error(f"Invalid hash algorithm name: {algorithm}")
        return None
    except Exception as e:
        logger.error(f"Hashing failed: {e}")
        return None


# --- Digital Signatures (RSA with PSS Padding) ---
# Provides authenticity and integrity. Uses public/private keys.

def sign_data_rsa_pss(private_key_pem: str, data: bytes) -> Optional[bytes]:
    """
    Creates a digital signature for data using an RSA private key and PSS padding.

    Args:
        private_key_pem (str): The signer's private key in PEM format.
        data (bytes): The data to sign.

    Returns:
        Optional[bytes]: The signature bytes, or None on error.
    """
    if not CRYPTO_LIB_AVAILABLE or not serialization or not asymmetric_padding or not hashes:
        logger.error("Cannot sign: cryptography library not available.")
        return None
    logger.info(f"Creating RSA-PSS signature for {len(data)} bytes...")
    if not isinstance(data, bytes): logger.error("Data to sign must be bytes."); return None

    try:
        # --- Conceptual cryptography Call ---
        # private_key = serialization.load_pem_private_key(private_key_pem.encode('utf-8'), password=None, backend=default_backend())
        # if not isinstance(private_key, rsa.RSAPrivateKey): raise TypeError("Not an RSA private key")
        #
        # signature = private_key.sign(
        #     data,
        #     asymmetric_padding.PSS(
        #         mgf=asymmetric_padding.MGF1(hashes.SHA256()),
        #         salt_length=asymmetric_padding.PSS.MAX_LENGTH # Recommended salt length
        #     ),
        #     hashes.SHA256() # Hash algorithm used on the data before signing
        # )
        # --- End Conceptual ---

        # Simulate signature
        signature = b"simulated_rsa_pss_signature_for_" + hashlib.sha256(data).digest()[:10]
        logger.info(f"  - Conceptual signature created (length {len(signature)} bytes).")
        return signature
    except Exception as e:
        logger.error(f"RSA signing failed: {e}")
        return None


def verify_signature_rsa_pss(public_key_pem: str, data: bytes, signature: bytes) -> bool:
    """
    Verifies a digital signature using an RSA public key and PSS padding.

    Args:
        public_key_pem (str): The signer's public key in PEM format.
        data (bytes): The original data that was signed.
        signature (bytes): The signature bytes to verify.

    Returns:
        bool: True if the signature is valid, False otherwise.
    """
    if not CRYPTO_LIB_AVAILABLE or not serialization or not asymmetric_padding or not hashes or not InvalidSignature:
        logger.error("Cannot verify signature: cryptography library not available.")
        return False
    logger.info(f"Verifying RSA-PSS signature for {len(data)} bytes...")
    if not isinstance(data, bytes) or not isinstance(signature, bytes):
        logger.error("Data and signature must be bytes for verification.")
        return False

    try:
        # --- Conceptual cryptography Call ---
        # public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'), backend=default_backend())
        # if not isinstance(public_key, rsa.RSAPublicKey): raise TypeError("Not an RSA public key")
        #
        # public_key.verify(
        #     signature,
        #     data,
        #     asymmetric_padding.PSS(
        #         mgf=asymmetric_padding.MGF1(hashes.SHA256()),
        #         salt_length=asymmetric_padding.PSS.MAX_LENGTH
        #     ),
        #     hashes.SHA256()
        # )
        # If verify() does not raise an exception, the signature is valid.
        # --- End Conceptual ---

        # Simulate verification based on simulated signature generation
        expected_signature = b"simulated_rsa_pss_signature_for_" + hashlib.sha256(data).digest()[:10]
        is_valid = signature == expected_signature
        if is_valid:
             logger.info("  - Signature VERIFIED successfully (Conceptual).")
        else:
             logger.warning("  - Signature VERIFICATION FAILED (Conceptual).")
        return is_valid

    except InvalidSignature:
        logger.warning("  - Signature VERIFICATION FAILED (InvalidSignature exception).")
        return False
    except Exception as e:
        logger.error(f"Error during signature verification: {e}")
        return False


# --- Main Execution Block ---
if __name__ == "__main__":
    print("===========================================")
    print("=== Running Encryption Prototypes ===")
    print("===========================================")
    print("(Note: Relies on conceptual implementations & 'cryptography' library)")
    print("*** Secure key management is NOT implemented here! ***")
    print("-" * 50)

    if not CRYPTO_LIB_AVAILABLE:
        print("\n'cryptography' library not found. Skipping examples.")
    else:
        # --- AES-GCM Demo ---
        print("\n--- [AES-GCM Symmetric Encryption] ---")
        aes_key = generate_aes_key(32) # Generate AES-256 key
        if aes_key:
            print(f"Generated AES Key (Hex): {aes_key.hex()}")
            plain_text = b"This is a secret message for Devin."
            aad = b"contextual_metadata_123" # Optional Associated Data
            print(f"Plaintext: {plain_text}")
            print(f"Associated Data: {aad}")

            encrypted = encrypt_aes_gcm(aes_key, plain_text, aad)
            if encrypted:
                print("Encrypted Data:")
                print(f"  Ciphertext (Hex): {encrypted['ciphertext'].hex()}")
                print(f"  Nonce (Hex): {encrypted['nonce'].hex()}")
                print(f"  Tag (Hex): {encrypted['tag'].hex()}")
                if 'aad' in encrypted: print(f"  AAD included (bytes): {encrypted['aad']}")

                # Decrypt
                print("\nDecrypting...")
                decrypted = decrypt_aes_gcm(aes_key, encrypted)
                if decrypted:
                    print(f"Decrypted Plaintext: {decrypted}")
                    assert decrypted == plain_text
                else:
                    print("Decryption failed (or tag verification failed).")

                # Tamper test (modify ciphertext slightly)
                print("\nTesting decryption with tampered ciphertext...")
                tampered_encrypted = encrypted.copy()
                tampered_encrypted["ciphertext"] = tampered_encrypted["ciphertext"][:-1] + b'X' # Change last byte
                decrypted_tampered = decrypt_aes_gcm(aes_key, tampered_encrypted)
                print(f"Decryption result for tampered data: {decrypted_tampered}") # Should be None
            else:
                print("Encryption failed.")
        else:
            print("Failed to generate AES key.")
        print("-" * 20)


        # --- RSA OAEP Demo ---
        print("\n--- [RSA-OAEP Asymmetric Encryption (Conceptual Keys)] ---")
        rsa_keys = generate_rsa_key_pair_placeholder(key_size=2048)
        if rsa_keys:
            private_pem, public_pem = rsa_keys
            # print("Generated Conceptual Private Key:\n", private_pem) # Sensitive
            print("Generated Conceptual Public Key:\n", public_pem)

            small_message = b"Secret symmetric key or short message"
            print(f"\nPlaintext: {small_message}")

            encrypted_rsa = encrypt_rsa_oaep(public_pem, small_message)
            if encrypted_rsa:
                print(f"Encrypted Data (RSA, Hex): {encrypted_rsa.hex()}")

                print("\nDecrypting (RSA)...")
                decrypted_rsa = decrypt_rsa_oaep(private_pem, encrypted_rsa)
                if decrypted_rsa:
                    print(f"Decrypted Plaintext: {decrypted_rsa}")
                    assert decrypted_rsa == small_message
                else:
                    print("RSA Decryption failed.")
            else:
                print("RSA Encryption failed.")
        else:
             print("Failed to generate conceptual RSA key pair.")
        print("-" * 20)

        # --- Hashing Demo ---
        print("\n--- [Hashing (SHA256)] ---")
        data_to_hash = b"This data needs integrity checking."
        print(f"Data: {data_to_hash}")
        data_hash = hash_data(data_to_hash, algorithm='sha256')
        if data_hash:
             print(f"SHA256 Hash: {data_hash}")
             # Verify hash
             print(f"Verification matches: {hash_data(data_to_hash, 'sha256') == data_hash}")
        else:
             print("Hashing failed.")
        print("-" * 20)

        # --- Digital Signature Demo ---
        print("\n--- [Digital Signature (RSA-PSS Conceptual Keys)] ---")
        if rsa_keys:
             private_pem_sig, public_pem_sig = rsa_keys # Reuse conceptual keys
             data_to_sign = b"This message must be authenticated."
             print(f"Data to Sign: {data_to_sign}")

             signature = sign_data_rsa_pss(private_pem_sig, data_to_sign)
             if signature:
                  print(f"Generated Signature (Hex): {signature.hex()}")

                  # Verify signature
                  print("\nVerifying signature with correct key and data...")
                  is_valid = verify_signature_rsa_pss(public_pem_sig, data_to_sign, signature)
                  print(f"Signature valid: {is_valid}")

                  # Verify with wrong data
                  print("\nVerifying signature with tampered data...")
                  is_valid_tampered = verify_signature_rsa_pss(public_pem_sig, data_to_sign + b"!", signature)
                  print(f"Signature valid (tampered data): {is_valid_tampered}") # Should be False
             else:
                  print("Signing failed.")
        else:
             print("Skipping signature demo as conceptual RSA keys failed.")
        print("-" * 20)

    print("\n===========================================")
    print("=== Encryption Prototypes Complete ===")
    print("===========================================")
