# Devin/cyber_range/capture_the_flag/flag_verifier.py
# Purpose: Handles the verification of submitted flags against correct challenge flags.

import os
import re
import hashlib
import logging
from typing import Optional, Tuple, Literal, Dict, Any

# Assume some configuration mechanism exists to get flag references
# from a central place (like the challenge definitions, potentially loaded
# from a file or database instead of being passed directly).
# For this example, we'll assume a dictionary simulating this lookup.
# In reality, CTFChallengeManager might pass the flag_reference here.

# --- Conceptual Flag Storage Lookup (Replace with actual Challenge Manager interaction) ---
# This simulates retrieving the 'flag_reference' string associated with a challenge ID.
# In a real system, this might involve querying the CTFChallengeManager instance.
CONCEPTUAL_FLAG_REFERENCES: Dict[str, str] = {
    "CTF-WEB101": "ENV:WEB_BEGINNER_FLAG",
    "CTF-PWN101": "HASH:sha256:a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3", # sha256 hash of "flag{simple_bof_pwned}"
    "CTF-CRY101": "VAULT:secret/ctf/crypto_subst", # Hypothetical Vault path
    "CTF-REV101": "REGEX:^flag\\{[A-Za-z0-9_]{16}\\}$", # Regex format check
    "CTF-STATIC": "STATIC:flag{hardcoded_example_flag_value}", # Direct string (less secure practice)
}
# --- End Conceptual Lookup ---


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FlagVerificationError(Exception):
    """Custom exception for flag verification issues."""
    pass

class FlagVerifier:
    """
    Verifies submitted flags against stored correct flag definitions.
    Handles different verification methods (string, hash, regex).
    Requires secure implementation for retrieving correct flag data.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the FlagVerifier.

        Args:
            config (Optional[Dict[str, Any]]): Configuration options, potentially
                                               including handles to secure stores like Vault.
        """
        self.config = config or {}
        # Conceptual: Initialize Vault client or other secure storage access here if needed
        # self.vault_client = self._initialize_vault(config.get('vault_config'))
        logger.info("FlagVerifier initialized.")

    def _get_correct_flag_data(self, challenge_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Retrieves the correct flag verification data (type and value/pattern/hash)
        based on the challenge ID using its reference string.

        *** CRITICAL SECURITY IMPLEMENTATION NEEDED ***
        This method MUST securely fetch the flag reference and potentially the flag
        value itself based on the reference type.

        Args:
            challenge_id (str): The ID of the challenge.

        Returns:
            Tuple[Optional[str], Optional[str]]: A tuple containing (verification_method, verification_data),
                                                 e.g., ('STATIC', 'flag{...}'), ('HASH', 'sha256:abc...'),
                                                 ('REGEX', '^flag\\{...\\}$'), ('ENV', 'FLAG_VAR_NAME'), etc.
                                                 Returns (None, None) if retrieval fails.
        """
        # Conceptual: Get reference string (replace with actual lookup)
        flag_reference = CONCEPTUAL_FLAG_REFERENCES.get(challenge_id)

        if not flag_reference:
            logger.error(f"No flag reference found for challenge ID '{challenge_id}'.")
            return None, None

        logger.debug(f"Retrieving flag data for challenge {challenge_id} using reference: {flag_reference}")

        parts = flag_reference.split(":", 1)
        if len(parts) != 2:
            logger.error(f"Invalid flag reference format for challenge {challenge_id}: {flag_reference}")
            return None, None

        method, data = parts
        method = method.upper() # Normalize method name

        # --- Placeholder Secure Retrieval Logic ---
        try:
            if method == "ENV":
                env_var_name = data
                flag_value = os.environ.get(env_var_name)
                if not flag_value:
                    raise FlagVerificationError(f"Environment variable '{env_var_name}' not set.")
                # Treat ENV vars as static strings for comparison
                return "STATIC", flag_value
            elif method == "VAULT":
                vault_path = data
                # Conceptual: Use initialized Vault client
                # flag_value = self.vault_client.read_secret(vault_path)
                # if not flag_value: raise FlagVerificationError("Secret not found in Vault.")
                logger.info(f"Conceptual: Reading flag from Vault path {vault_path}")
                # Return placeholder value for skeleton
                flag_value = f"flag{{dummy_vault_flag_{challenge_id.split('-')[1].lower()}}}"
                return "STATIC", flag_value # Treat Vault secrets as static strings
            elif method in ["STATIC", "HASH", "REGEX"]:
                # For these methods, the data part of the reference is the value itself
                return method, data
            else:
                raise FlagVerificationError(f"Unsupported flag reference method: {method}")
        except Exception as e:
            logger.error(f"Error retrieving flag data for challenge {challenge_id} (Ref: {flag_reference}): {e}")
            return None, None
        # --- End Placeholder Secure Retrieval Logic ---

    def _normalize_flag(self, flag: str) -> str:
        """Applies standard normalization (strip whitespace, common format)."""
        # Common practice: remove leading/trailing whitespace. Case sensitivity varies.
        # Many CTFs use case-insensitive flags or specific formats like flag{...}.
        # Defaulting to strip + lower case for simple string comparison.
        return flag.strip().lower()

    def verify_flag(self, challenge_id: str, submitted_flag: str) -> bool:
        """
        Verifies if the submitted flag is correct for the given challenge ID.

        Args:
            challenge_id (str): The ID of the challenge.
            submitted_flag (str): The flag string submitted by the user.

        Returns:
            bool: True if the flag is correct, False otherwise.
        """
        if not submitted_flag:
             logger.warning(f"Verification failed for {challenge_id}: Submitted flag is empty.")
             return False

        verification_method, verification_data = self._get_correct_flag_data(challenge_id)

        if verification_method is None or verification_data is None:
            logger.error(f"Verification failed for {challenge_id}: Could not retrieve correct flag data.")
            return False

        logger.info(f"Verifying flag for challenge '{challenge_id}' using method '{verification_method}'.")

        try:
            if verification_method == "STATIC":
                # Simple string comparison (case-insensitive after normalization)
                normalized_submitted = self._normalize_flag(submitted_flag)
                normalized_correct = self._normalize_flag(verification_data)
                is_correct = normalized_submitted == normalized_correct
                logger.debug(f"STATIC Compare: '{normalized_submitted}' == '{normalized_correct}' -> {is_correct}")
                return is_correct

            elif verification_method == "HASH":
                # Compare hash of submitted flag against stored hash
                hash_parts = verification_data.split(':', 1)
                if len(hash_parts) != 2:
                    raise FlagVerificationError(f"Invalid HASH format: {verification_data}")
                algo, correct_hash = hash_parts
                algo = algo.lower()
                correct_hash = correct_hash.lower()

                # Hash the submitted flag (raw bytes, usually UTF-8)
                submitted_bytes = submitted_flag.strip().encode('utf-8') # Use raw submission before normalize
                submitted_hash: Optional[str] = None
                if algo == 'sha256':
                    submitted_hash = hashlib.sha256(submitted_bytes).hexdigest()
                elif algo == 'md5': # MD5 generally discouraged, but might appear in CTFs
                    submitted_hash = hashlib.md5(submitted_bytes).hexdigest()
                # Add other algorithms if needed (sha1, sha512)
                else:
                    raise FlagVerificationError(f"Unsupported hash algorithm: {algo}")

                is_correct = submitted_hash == correct_hash
                logger.debug(f"HASH Compare ({algo}): '{submitted_hash}' == '{correct_hash}' -> {is_correct}")
                return is_correct

            elif verification_method == "REGEX":
                # Check if submitted flag matches the regex pattern
                pattern = verification_data
                # Use re.match to check if the pattern matches from the beginning of the string
                # Use re.fullmatch for exact match of the entire string (often preferred for flags)
                # Using strip() on submitted flag before matching.
                match = re.fullmatch(pattern, submitted_flag.strip())
                is_correct = match is not None
                logger.debug(f"REGEX Compare: Pattern='{pattern}', String='{submitted_flag.strip()}' -> {is_correct}")
                return is_correct

            else:
                # Should not happen if _get_correct_flag_data is correct
                raise FlagVerificationError(f"Internal error: Reached unknown verification method {verification_method}")

        except FlagVerificationError as e:
            logger.error(f"Flag verification error for challenge {challenge_id}: {e}")
            return False
        except Exception as e:
             logger.error(f"Unexpected error during flag verification for {challenge_id}: {e}")
             return False


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Flag Verifier Example ---")

    # Set dummy env var for testing ENV method
    os.environ["WEB_BEGINNER_FLAG"] = "flag{simple_login_bypass_yay}"

    verifier = FlagVerifier()

    # --- Test Cases ---
    challenge_web = "CTF-WEB101" # Uses ENV -> STATIC comparison
    challenge_pwn = "CTF-PWN101" # Uses HASH comparison
    challenge_rev = "CTF-REV101" # Uses REGEX comparison
    challenge_static = "CTF-STATIC" # Uses direct STATIC comparison

    print(f"\nVerifying flags for {challenge_web} (Correct: from ENV WEB_BEGINNER_FLAG)")
    print(f"  Submission 'flag{{simple_login_bypass_yay}}': {verifier.verify_flag(challenge_web, 'flag{simple_login_bypass_yay}')}") # Correct
    print(f"  Submission ' flag{{Simple_Login_Bypass_YAY}}  ': {verifier.verify_flag(challenge_web, ' flag{Simple_Login_Bypass_YAY}  ')}") # Correct (normalized)
    print(f"  Submission 'flag{{wrong}}': {verifier.verify_flag(challenge_web, 'flag{wrong}')}") # Incorrect

    print(f"\nVerifying flags for {challenge_pwn} (Correct hash of 'flag{{simple_bof_pwned}}')")
    print(f"  Submission 'flag{{simple_bof_pwned}}': {verifier.verify_flag(challenge_pwn, 'flag{simple_bof_pwned}')}") # Correct
    print(f"  Submission ' flag{{simple_bof_pwned}} ': {verifier.verify_flag(challenge_pwn, ' flag{simple_bof_pwned} ')}") # Correct (strip before hash)
    print(f"  Submission 'flag{{Simple_Bof_Pwned}}': {verifier.verify_flag(challenge_pwn, 'flag{Simple_Bof_Pwned}')}") # Incorrect (hash is case-sensitive)
    print(f"  Submission 'wrong': {verifier.verify_flag(challenge_pwn, 'wrong')}") # Incorrect

    print(f"\nVerifying flags for {challenge_rev} (Regex: ^flag\\{{[A-Za-z0-9_]{{16}}\\}}$ )")
    print(f"  Submission 'flag{{correct_fmt_1234}}': {verifier.verify_flag(challenge_rev, 'flag{correct_fmt_1234}')}") # Correct format (length 16)
    print(f"  Submission 'flag{{too_short}}': {verifier.verify_flag(challenge_rev, 'flag{too_short}')}") # Incorrect (length)
    print(f"  Submission 'flag{{invalid-char}}': {verifier.verify_flag(challenge_rev, 'flag{invalid-char}')}") # Incorrect (invalid char '-')
    print(f"  Submission ' flag{{needs_strip_123}} ': {verifier.verify_flag(challenge_rev, ' flag{needs_strip_123} ')}") # Correct (strip before match)

    print(f"\nVerifying flags for {challenge_static} (Correct: 'flag{{hardcoded_example_flag_value}}')")
    print(f"  Submission 'flag{{hardcoded_example_flag_value}}': {verifier.verify_flag(challenge_static, 'flag{hardcoded_example_flag_value}')}") # Correct
    print(f"  Submission 'FLAG{{HARDCODED_EXAMPLE_FLAG_VALUE}}': {verifier.verify_flag(challenge_static, 'FLAG{HARDCODED_EXAMPLE_FLAG_VALUE}')}") # Correct (normalized)


    # Clean up dummy env var
    del os.environ["WEB_BEGINNER_FLAG"]

    print("\n--- End Example ---")
