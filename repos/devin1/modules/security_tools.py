"""
security_tools.py

This module provides advanced security and protection utilities for the Devin project.
"""

import hashlib
import hmac
import os
from cryptography.fernet import Fernet
from typing import Optional

class SecurityTools:
    """
    A collection of security tools for encryption, hashing, and integrity checks.
    """

    def __init__(self):
        self.symmetric_key = os.getenv("SYMMETRIC_KEY", Fernet.generate_key())
        self.fernet = Fernet(self.symmetric_key)

    def generate_hash(self, data: str, algorithm: str = "sha256") -> str:
        """
        Generate a hash for the provided data using the specified algorithm.

        Args:
            data (str): The input data to hash.
            algorithm (str): The hashing algorithm (default: 'sha256').

        Returns:
            str: The hexadecimal hash.
        """
        try:
            hash_func = getattr(hashlib, algorithm)
            return hash_func(data.encode()).hexdigest()
        except AttributeError:
            raise ValueError(f"Unsupported hashing algorithm: {algorithm}")

    def verify_hash(self, data: str, hash_value: str, algorithm: str = "sha256") -> bool:
        """
        Verify if a hash matches the provided data.

        Args:
            data (str): The original data.
            hash_value (str): The hash to verify against.
            algorithm (str): The hashing algorithm (default: 'sha256').

        Returns:
            bool: True if the hash matches, otherwise False.
        """
        return self.generate_hash(data, algorithm) == hash_value

    def encrypt_data(self, data: str) -> str:
        """
        Encrypt the provided data using symmetric encryption.

        Args:
            data (str): The data to encrypt.

        Returns:
            str: The encrypted data as a base64-encoded string.
        """
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt the provided encrypted data.

        Args:
            encrypted_data (str): The base64-encoded encrypted data.

        Returns:
            str: The decrypted data.
        """
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    def create_hmac(self, key: str, data: str, algorithm: str = "sha256") -> str:
        """
        Generate a HMAC for the provided data.

        Args:
            key (str): The secret key.
            data (str): The data to authenticate.
            algorithm (str): The hashing algorithm (default: 'sha256').

        Returns:
            str: The HMAC as a hexadecimal string.
        """
        try:
            hash_func = getattr(hashlib, algorithm)
            return hmac.new(key.encode(), data.encode(), hash_func).hexdigest()
        except AttributeError:
            raise ValueError(f"Unsupported hashing algorithm: {algorithm}")

    def verify_hmac(self, key: str, data: str, hmac_value: str, algorithm: str = "sha256") -> bool:
        """
        Verify a HMAC against the provided data.

        Args:
            key (str): The secret key.
            data (str): The data to verify.
            hmac_value (str): The HMAC to verify against.
            algorithm (str): The hashing algorithm (default: 'sha256').

        Returns:
            bool: True if the HMAC matches, otherwise False.
        """
        return self.create_hmac(key, data, algorithm) == hmac_value

    def generate_symmetric_key(self) -> str:
        """
        Generate a new symmetric encryption key.

        Returns:
            str: The base64-encoded key.
        """
        new_key = Fernet.generate_key()
        return new_key.decode()

if __name__ == "__main__":
    tools = SecurityTools()
    data = "Sensitive information"
    
    # Example usage of the tools
    print("Original Data:", data)

    # Hashing
    hash_value = tools.generate_hash(data)
    print("Hash Value:", hash_value)

    # Encryption
    encrypted_data = tools.encrypt_data(data)
    print("Encrypted Data:", encrypted_data)

    # Decryption
    decrypted_data = tools.decrypt_data(encrypted_data)
    print("Decrypted Data:", decrypted_data)

    # HMAC
    secret_key = "securekey"
    hmac_value = tools.create_hmac(secret_key, data)
    print("Generated HMAC:", hmac_value)

    # Verify HMAC
    is_valid_hmac = tools.verify_hmac(secret_key, data, hmac_value)
    print("Is HMAC Valid?:", is_valid_hmac)
