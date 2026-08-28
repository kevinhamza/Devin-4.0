"""
modules/encryption_tools.py
---------------------------
This module provides cryptographic utilities for encryption, decryption, hashing, and digital signatures.
It supports both symmetric and asymmetric cryptographic algorithms.
"""

import hashlib
import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed


class SymmetricEncryption:
    """Handles symmetric encryption and decryption using AES."""

    @staticmethod
    def generate_key(key_size: int = 32) -> bytes:
        """
        Generate a random key for AES encryption.
        :param key_size: Size of the key in bytes (16, 24, or 32).
        :return: A random AES key.
        """
        return os.urandom(key_size)

    @staticmethod
    def encrypt(data: bytes, key: bytes) -> tuple:
        """
        Encrypt data using AES in CBC mode.
        :param data: The plaintext data to encrypt.
        :param key: The AES key.
        :return: A tuple of (IV, ciphertext).
        """
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        padded_data = data + b" " * (16 - len(data) % 16)
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return iv, ciphertext

    @staticmethod
    def decrypt(iv: bytes, ciphertext: bytes, key: bytes) -> bytes:
        """
        Decrypt data encrypted using AES in CBC mode.
        :param iv: Initialization vector.
        :param ciphertext: The encrypted data.
        :param key: The AES key.
        :return: The decrypted plaintext.
        """
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.strip()


class AsymmetricEncryption:
    """Handles asymmetric encryption and decryption using RSA."""

    @staticmethod
    def generate_key_pair(key_size: int = 2048):
        """
        Generate a new RSA key pair.
        :param key_size: The size of the RSA key.
        :return: A tuple of (private_key, public_key).
        """
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def encrypt(data: bytes, public_key) -> bytes:
        """
        Encrypt data using the public key.
        :param data: The plaintext data to encrypt.
        :param public_key: The RSA public key.
        :return: The encrypted data.
        """
        return public_key.encrypt(
            data,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )

    @staticmethod
    def decrypt(encrypted_data: bytes, private_key) -> bytes:
        """
        Decrypt data using the private key.
        :param encrypted_data: The encrypted data.
        :param private_key: The RSA private key.
        :return: The decrypted plaintext.
        """
        return private_key.decrypt(
            encrypted_data,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )


class Hashing:
    """Handles hashing and verification using various algorithms."""

    @staticmethod
    def generate_hash(data: bytes, algorithm: str = "sha256") -> str:
        """
        Generate a cryptographic hash of the given data.
        :param data: The data to hash.
        :param algorithm: Hashing algorithm (e.g., 'sha256', 'sha512').
        :return: The hexadecimal hash string.
        """
        hash_func = getattr(hashlib, algorithm)()
        hash_func.update(data)
        return hash_func.hexdigest()

    @staticmethod
    def verify_hash(data: bytes, expected_hash: str, algorithm: str = "sha256") -> bool:
        """
        Verify that the hash of the data matches the expected hash.
        :param data: The data to verify.
        :param expected_hash: The expected hash value.
        :param algorithm: Hashing algorithm used for verification.
        :return: True if hashes match, False otherwise.
        """
        return Hashing.generate_hash(data, algorithm) == expected_hash


class DigitalSignature:
    """Handles signing and verifying digital signatures."""

    @staticmethod
    def sign(data: bytes, private_key) -> bytes:
        """
        Sign data using the private key.
        :param data: The data to sign.
        :param private_key: The RSA private key.
        :return: The signature.
        """
        return private_key.sign(
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            Prehashed(hashes.SHA256()),
        )

    @staticmethod
    def verify(data: bytes, signature: bytes, public_key) -> bool:
        """
        Verify a digital signature using the public key.
        :param data: The data that was signed.
        :param signature: The digital signature.
        :param public_key: The RSA public key.
        :return: True if signature is valid, False otherwise.
        """
        try:
            public_key.verify(
                signature,
                data,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                Prehashed(hashes.SHA256()),
            )
            return True
        except Exception:
            return False
