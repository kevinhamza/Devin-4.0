# Devin/security/ethical_enforcer/human_override/dna_biometric_auth.py
# Purpose: A simulation of a DNA-based biometric challenge-response
#          protocol for high-security authorization.

import logging
import json
import hashlib
import os
import random
from pathlib import Path
from typing import Dict, Tuple

# Configure basic logging
logger = logging.getLogger("DNA_Auth")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class DNA_BiometricAuth:
    """
    Simulates a DNA-based challenge-response authentication system.
    """
    def __init__(self, authorized_genome_hashes_path: Path):
        """
        Args:
            authorized_genome_hashes_path: Path to the JSON file storing the
                                           enrolled genomic hash data.
        """
        self.hashes_path = authorized_genome_hashes_path
        self._enrolled_data: Dict[str, str] = self._load_hashes()

    def _load_hashes(self) -> Dict[str, str]:
        """Loads the enrolled hash data from the JSON file."""
        if self.hashes_path.is_file():
            with open(self.hashes_path, 'r') as f:
                return json.load(f)
        return {}

    def enroll_genome(self, genome_file_path: Path, num_challenges: int = 200):
        """
        (One-time setup) Reads a reference genome and creates a set of
        secret challenge-response hashes from it.
        """
        logger.warning(f"ENROLLMENT: Reading reference genome from '{genome_file_path}'...")
        try:
            with open(genome_file_path, 'r') as f:
                genome = f.read().strip()
            
            if not all(c in 'ACGT' for c in genome):
                raise ValueError("Genome file contains invalid characters (must be A, C, G, T).")
            
            genome_hashes = {}
            genome_length = len(genome)
            segment_length = 256 # Use a fixed length for segments
            
            if genome_length < segment_length * num_challenges:
                 raise ValueError("Genome is too small for the number of challenges.")

            logger.info(f"Generating {num_challenges} secure genomic hashes...")
            # Generate non-overlapping random segments
            positions = random.sample(range(0, genome_length - segment_length, segment_length), num_challenges)
            
            for pos in positions:
                segment = genome[pos:pos+segment_length]
                segment_hash = hashlib.sha256(segment.encode()).hexdigest()
                # The key is the start position of the segment
                genome_hashes[str(pos)] = segment_hash
            
            with open(self.hashes_path, 'w') as f:
                json.dump(genome_hashes, f)
            
            self._enrolled_data = genome_hashes
            logger.warning(f"ENROLLMENT COMPLETE. Secure hash file saved to '{self.hashes_path}'.")

        except Exception as e:
            logger.error(f"Enrollment failed: {e}")

    def create_challenge(self, num_segments: int = 5) -> Dict[str, int]:
        """
        Generates a random challenge for the user to respond to.

        Returns:
            A dictionary where keys are the start positions and values are the
            required lengths of the DNA segments.
        """
        if not self._enrolled_data:
            raise RuntimeError("No genome has been enrolled. Cannot create a challenge.")
            
        logger.info(f"Creating a new challenge with {num_segments} segments...")
        challenge_positions = random.sample(list(self._enrolled_data.keys()), num_segments)
        # For this simulation, we use a fixed segment length
        return {pos: 256 for pos in challenge_positions}

    def verify_response(self, challenge: Dict[str, int], user_genome_file_path: Path) -> bool:
        """
        Verifies a user's genomic sample against a given challenge.
        """
        logger.info(f"Verifying response from '{user_genome_file_path}'...")
        try:
            with open(user_genome_file_path, 'r') as f:
                user_genome = f.read().strip()
                
            for pos_str, length in challenge.items():
                pos = int(pos_str)
                # Extract the segment from the user's provided genome
                user_segment = user_genome[pos:pos+length]
                
                # Hash it
                user_segment_hash = hashlib.sha256(user_segment.encode()).hexdigest()
                
                # Compare it to the enrolled, trusted hash
                if self._enrolled_data.get(pos_str) != user_segment_hash:
                    logger.error(f"Verification FAILED: Hash mismatch for segment at position {pos}.")
                    return False
            
            logger.info("Verification SUCCESS: All challenge segments matched.")
            return True

        except Exception as e:
            logger.error(f"Verification process failed due to an error: {e}")
            return False


def generate_dummy_genome(file_path: Path, length: int = 1_000_000):
    """Helper function to create a large, random DNA sequence file."""
    with open(file_path, 'w') as f:
        f.write("".join(random.choice("ACGT") for _ in range(length)))

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== DNA Biometric Authentication Simulator 🧬🔐 ===")
    print("=========================================================")

    # 1. Setup demo environment
    ceo_genome_file = Path("ceo_genome.txt")
    user_sample_file = Path("user_sample.txt")
    imposter_sample_file = Path("imposter_sample.txt")
    hashes_file = Path("ceo_genome.hashes.json")

    try:
        # 2. Generate dummy genomes
        print("\n--- 1. Generating simulated genomic data ---")
        generate_dummy_genome(ceo_genome_file)
        # For the demo, the authentic user provides a perfect copy
        shutil.copy(ceo_genome_file, user_sample_file)
        # The imposter provides a different genome
        generate_dummy_genome(imposter_sample_file)
        print("Created reference genome, authentic sample, and imposter sample.")
        
        # 3. Enroll the CEO's genome
        auth_system = DNA_BiometricAuth(hashes_file)
        auth_system.enroll_genome(ceo_genome_file)
        
        # 4. Create an authentication challenge
        challenge = auth_system.create_challenge()
        print(f"\n--- 2. Generated Authentication Challenge ---")
        print("The system requests the DNA sequences for the following segments (pos: length):")
        print(challenge)
        
        # 5. Verify the authentic user
        print("\n--- 3. Verifying the AUTHENTIC user's response ---")
        is_valid_user = auth_system.verify_response(challenge, user_sample_file)
        if is_valid_user:
            print("[SUCCESS] Biometric identity of the authentic user has been confirmed.")
        else:
            print("[FAILURE] Authentic user could not be verified.")

        # 6. Verify the imposter
        print("\n--- 4. Verifying the IMPOSTER's response ---")
        is_valid_imposter = auth_system.verify_response(challenge, imposter_sample_file)
        if not is_valid_imposter:
            print("[SUCCESS] Imposter was correctly identified and rejected.")
        else:
            print("[FAILURE] Imposter was incorrectly verified as authentic.")

    finally:
        # 7. Clean up demo files
        for f in [ceo_genome_file, user_sample_file, imposter_sample_file, hashes_file]:
            if f.exists():
                f.unlink()
        print("\nCleaned up demo files.")
    
    print("\n=========================================================")
    print("=== DNA Biometric Auth Simulator Complete ===")
    print("=========================================================")
