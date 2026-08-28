"""
prototypes/encryption_prototypes.py

Module: Encryption Prototypes
Purpose: Provides experimental implementations for encryption and decryption mechanisms,
         designed to explore secure data handling techniques.
"""

import base64
from cryptography.fernet import Fernet
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os


class EncryptionPrototypes:
    """
    A collection of experimental encryption and decryption techniques for prototyping.
    """

    def __init__(self):
        self.symmetric_key = Fernet.generate_key()
        self.aes_key = get_random_bytes(32)  # AES 256-bit key
        self.aes_nonce = None

    # Fernet Encryption
    def fernet_encrypt(self, data: str) -> str:
        """
        Encrypts data using Fernet symmetric encryption.

        :param data: The plaintext data to encrypt.
        :return: Encrypted data as a string.
        """
        fernet = Fernet(self.symmetric_key)
        return fernet.encrypt(data.encode()).decode()

    def fernet_decrypt(self, token: str) -> str:
        """
        Decrypts data encrypted with Fernet encryption.

        :param token: The encrypted token to decrypt.
        :return: Decrypted plaintext data as a string.
        """
        fernet = Fernet(self.symmetric_key)
        return fernet.decrypt(token.encode()).decode()

    # AES Encryption
    def aes_encrypt(self, data: str) -> bytes:
        """
        Encrypts data using AES encryption.

        :param data: The plaintext data to encrypt.
        :return: Encrypted data as bytes.
        """
        cipher = AES.new(self.aes_key, AES.MODE_GCM)
        self.aes_nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())
        return ciphertext + tag

    def aes_decrypt(self, ciphertext: bytes) -> str:
        """
        Decrypts data encrypted with AES encryption.

        :param ciphertext: The encrypted data to decrypt.
        :return: Decrypted plaintext data as a string.
        """
        cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=self.aes_nonce)
        data = cipher.decrypt(ciphertext[:-16])  # Exclude the tag (last 16 bytes)
        return data.decode()

    # SHA-256 Hashing
    @staticmethod
    def sha256_hash(data: str) -> str:
        """
        Generates a SHA-256 hash of the provided data.

        :param data: The data to hash.
        :return: The SHA-256 hash as a hexadecimal string.
        """
        return sha256(data.encode()).hexdigest()

    # Base64 Encoding and Decoding
    @staticmethod
    def base64_encode(data: str) -> str:
        """
        Encodes data using Base64.

        :param data: The plaintext data to encode.
        :return: Base64 encoded string.
        """
        return base64.b64encode(data.encode()).decode()

    @staticmethod
    def base64_decode(encoded_data: str) -> str:
        """
        Decodes Base64 encoded data.

        :param encoded_data: The Base64 encoded string to decode.
        :return: Decoded plaintext string.
        """
        return base64.b64decode(encoded_data.encode()).decode()

    # Key Management
    def save_keys(self, directory: str):
        """
        Saves generated keys to a directory.

        :param directory: Directory path to save the keys.
        """
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, "fernet_key.key"), "wb") as f:
            f.write(self.symmetric_key)
        with open(os.path.join(directory, "aes_key.key"), "wb") as f:
            f.write(self.aes_key)

    def load_keys(self, directory: str):
        """
        Loads keys from a specified directory.

        :param directory: Directory path containing the keys.
        """
        with open(os.path.join(directory, "fernet_key.key"), "rb") as f:
            self.symmetric_key = f.read()
        with open(os.path.join(directory, "aes_key.key"), "rb") as f:
            self.aes_key = f.read()


# Example Usage
if __name__ == "__main__":
    encryption_tool = EncryptionPrototypes()

    # Fernet encryption example
    plaintext = "Confidential data"
    encrypted_data = encryption_tool.fernet_encrypt(plaintext)
    decrypted_data = encryption_tool.fernet_decrypt(encrypted_data)

    print(f"Original: {plaintext}")
    print(f"Encrypted (Fernet): {encrypted_data}")
    print(f"Decrypted (Fernet): {decrypted_data}")

    # AES encryption example
    aes_encrypted_data = encryption_tool.aes_encrypt(plaintext)
    aes_decrypted_data = encryption_tool.aes_decrypt(aes_encrypted_data)

    print(f"Encrypted (AES): {aes_encrypted_data}")
    print(f"Decrypted (AES): {aes_decrypted_data}")

    # SHA-256 hashing
    hashed_data = EncryptionPrototypes.sha256_hash(plaintext)
    print(f"SHA-256 Hash: {hashed_data}")

    # Base64 encoding/decoding
    base64_encoded = EncryptionPrototypes.base64_encode(plaintext)
    base64_decoded = EncryptionPrototypes.base64_decode(base64_encoded)

    print(f"Base64 Encoded: {base64_encoded}")
    print(f"Base64 Decoded: {base64_decoded}")
