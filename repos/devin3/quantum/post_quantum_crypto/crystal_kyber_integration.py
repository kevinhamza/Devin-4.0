# Devin/quantum/post_quantum_crypto/crystal_kyber_integration.py
# Purpose: A dedicated implementation for the CRYSTALS-Kyber Post-Quantum
#          Key Encapsulation Mechanism (KEM), the NIST standard.

import logging
from typing import Tuple, Optional

try:
    # PyKyber provides a direct implementation of the NIST standard
    from kyber import Kyber512, Kyber768, Kyber1024
    PYKYBER_AVAILABLE = True
except ImportError:
    PYKYBER_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("KyberIntegration")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class KyberKEM:
    """
    A wrapper for the CRYSTALS-Kyber Key Encapsulation Mechanism.
    """
    def __init__(self, security_level: int = 768):
        """
        Initializes the Kyber wrapper for a specific security level.
        
        Args:
            security_level (int): The desired security level. Must be 512, 768, or 1024.
        """
        if not PYKYBER_AVAILABLE:
            raise ImportError("The 'PyKyber' library is required. 'pip install pykyber'")
            
        if security_level == 512:
            self.kyber_instance = Kyber512
        elif security_level == 768:
            self.kyber_instance = Kyber768
        elif security_level == 1024:
            self.kyber_instance = Kyber1024
        else:
            raise ValueError("Invalid security level. Must be 512, 768, or 1024.")
        
        logger.info(f"KyberKEM initialized with security level: {security_level}")

    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generates a new public and private key pair.

        Returns:
            A tuple containing (public_key, private_key).
        """
        public_key, private_key = self.kyber_instance.keygen()
        logger.info("Generated new Kyber key pair.")
        return public_key, private_key

    def encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """
        Generates a shared secret and a ciphertext for a given public key.
        This is typically performed by the client.

        Args:
            public_key: The recipient's public key.

        Returns:
            A tuple containing (ciphertext, shared_secret).
        """
        logger.info("Encapsulating shared secret...")
        ciphertext, shared_secret = self.kyber_instance.enc(public_key)
        return ciphertext, shared_secret

    def decapsulate(self, private_key: bytes, ciphertext: bytes) -> bytes:
        """
        Derives the shared secret from a ciphertext using a private key.
        This is typically performed by the server/recipient.

        Args:
            private_key: The recipient's private key.
            ciphertext: The ciphertext received from the client.
        
        Returns:
            The derived shared secret.
        """
        logger.info("Decapsulating ciphertext...")
        shared_secret = self.kyber_instance.dec(ciphertext, private_key)
        return shared_secret


# --- Example Usage ---
if __name__ == "__main__":
    if not PYKYBER_AVAILABLE:
        print("\nERROR: The 'PyKyber' library is required for this demo.")
        print("Please run: pip install pykyber")
    else:
        print("=========================================================")
        print("=== CRYSTALS-Kyber KEM Demonstration ⚛️🔑 ===")
        print("=========================================================")
        print("This demo shows a full key exchange using the NIST standard PQC algorithm.")
        
        try:
            # 1. Initialize the KEM with a specific security level (NIST Level 3)
            kem = KyberKEM(security_level=768)
            
            # 2. (Server-side) Generate a key pair
            print("\nStep 1: The 'Server' generates a public and private key pair.")
            public_key, private_key = kem.generate_keypair()
            print(f"  - Public Key Size:  {len(public_key)} bytes")
            print(f"  - Private Key Size: {len(private_key)} bytes")
            
            # 3. (Client-side) Use the server's public key to create a shared secret
            #    and a ciphertext to send back to the server.
            print("\nStep 2: The 'Client' receives the public key and encapsulates a secret.")
            ciphertext, client_shared_secret = kem.encapsulate(public_key)
            print(f"  - Generated Ciphertext Size:   {len(ciphertext)} bytes")
            print(f"  - Client's Shared Secret Size: {len(client_shared_secret)} bytes")
            
            # 4. (Server-side) Use the private key to decapsulate the ciphertext
            #    and arrive at the same shared secret.
            print("\nStep 3: The 'Server' uses its private key to decapsulate the ciphertext.")
            server_shared_secret = kem.decapsulate(private_key, ciphertext)
            print("  - Secret successfully derived by the server.")
            
            # 5. Verification
            print("\nStep 4: Verification.")
            if client_shared_secret == server_shared_secret:
                print("  [SUCCESS] The client's and server's shared secrets match perfectly!")
            else:
                print("  [FAILURE] The shared secrets do not match. The exchange failed.")
            
        except Exception as e:
            logger.error(f"An error occurred during the demo: {e}")

        print("\n=========================================================")
        print("=== Kyber KEM Demonstration Complete ===")
        print("=========================================================")
