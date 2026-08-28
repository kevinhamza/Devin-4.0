# Devin/recovery/dna_storage_recovery.py
# Purpose: A simulation of a DNA data storage and recovery pipeline,
#          including data-to-DNA encoding, error simulation, and
#          error correction for perfect data restoration.

import logging
import random
from pathlib import Path
from typing import Optional

try:
    from reedsolo import RSCodec
    REEDSOLO_AVAILABLE = True
except ImportError:
    REEDSOLO_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("DNA_Storage")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class DNA_Storage:
    """
    Simulates encoding data into DNA, degrading it, and recovering it.
    """
    def __init__(self, ecc_bytes: int = 32):
        """
        Initializes the DNA storage simulator.
        
        Args:
            ecc_bytes: Number of error correction bytes to use. More bytes can
                       correct more errors but increases storage overhead.
        """
        if not REEDSOLO_AVAILABLE:
            raise ImportError("The 'reedsolo' library is required. 'pip install reedsolo'")
            
        self.rs = RSCodec(ecc_bytes)
        self.base_map = {"00": "A", "01": "C", "10": "G", "11": "T"}
        self.reverse_base_map = {v: k for k, v in self.base_map.items()}

    def encode_file_to_dna(self, file_path: Path) -> Optional[str]:
        """
        Reads a file, adds error correction, and encodes it into a DNA sequence.
        """
        logger.info(f"Encoding file '{file_path}' to DNA...")
        try:
            with open(file_path, "rb") as f:
                data = bytearray(f.read())
            
            # 1. Add Reed-Solomon error correction parity bytes
            encoded_data = self.rs.encode(data)
            
            # 2. Convert byte data to a string of bits
            bits = "".join(format(byte, '08b') for byte in encoded_data)
            
            # 3. Convert pairs of bits to DNA bases
            dna_sequence = "".join(self.base_map[bits[i:i+2]] for i in range(0, len(bits), 2))
            
            logger.info(f"Encoding complete. Original size: {len(data)} bytes. Encoded DNA length: {len(dna_sequence)} bases.")
            return dna_sequence
            
        except Exception as e:
            logger.error(f"Failed to encode file: {e}")
            return None

    def simulate_degradation(self, dna_sequence: str, error_rate: float = 0.01) -> str:
        """
        Introduces random errors into a DNA sequence to simulate physical degradation.
        """
        logger.warning(f"Simulating DNA degradation with an error rate of {error_rate * 100:.2f}%...")
        mutated_dna = list(dna_sequence)
        error_count = 0
        
        for i in range(len(mutated_dna)):
            if random.random() < error_rate:
                error_count += 1
                rand_val = random.random()
                if rand_val < 0.8: # 80% chance of substitution
                    mutated_dna[i] = random.choice("ACGT".replace(mutated_dna[i], ""))
                elif rand_val < 0.9: # 10% chance of deletion
                    mutated_dna[i] = ""
                else: # 10% chance of insertion
                    mutated_dna[i] += random.choice("ACGT")
        
        logger.warning(f"Degradation complete. Introduced {error_count} errors.")
        return "".join(mutated_dna)

    def decode_dna_to_file(self, dna_sequence: str, output_path: Path) -> bool:
        """
        Decodes a (potentially corrupted) DNA sequence, corrects errors, and writes to a file.
        """
        logger.info(f"Decoding DNA sequence to file '{output_path}'...")
        try:
            # 1. Convert DNA bases back to pairs of bits
            bits = "".join(self.reverse_base_map[base] for base in dna_sequence if base in self.reverse_base_map)
            
            # 2. Convert string of bits back to byte data
            #    This data is potentially corrupted at this stage.
            byte_data = bytearray(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
            
            # 3. Use Reed-Solomon to decode and correct errors
            logger.info("Applying Reed-Solomon error correction...")
            decoded_data, _, errata_pos = self.rs.decode(byte_data)
            if errata_pos:
                logger.warning(f"Corrected {len(errata_pos)} errors in the data.")
            else:
                logger.info("No errors detected or all errors corrected.")
            
            # 4. Write the original, corrected data to a file
            with open(output_path, "wb") as f:
                f.write(decoded_data)
                
            logger.info("Decoding and recovery successful.")
            return True

        except Exception as e:
            logger.error(f"Failed to decode DNA sequence. The data may be too corrupted. Error: {e}")
            return False

# --- Example Usage ---
if __name__ == "__main__":
    if not REEDSOLO_AVAILABLE:
        print("\nERROR: The 'reedsolo' library is required for this demo.")
        print("Please run: pip install reedsolo")
    else:
        print("=========================================================")
        print("=== DNA Data Storage & Recovery Simulator 🧬💾 ===")
        print("=========================================================")
        
        # 1. Setup a demo file and the storage system
        original_file = Path("original_data.txt")
        recovered_file = Path("recovered_data.txt")
        original_content = "This is a secret message stored in DNA. It must be recovered perfectly."
        original_file.write_text(original_content)
        
        # Use 32 bytes for error correction, which can fix up to 16 byte errors.
        dna_storage = DNA_Storage(ecc_bytes=32)
        
        try:
            # 2. Encode the file to a DNA sequence
            print(f"\n--- 1. Encoding '{original_file}' to DNA ---")
            dna_string = dna_storage.encode_file_to_dna(original_file)
            if dna_string:
                print(f"    First 100 bases: {dna_string[:100]}...")
                
                # 3. Simulate degradation over time
                print(f"\n--- 2. Simulating physical degradation (1% error rate) ---")
                corrupted_dna = dna_storage.simulate_degradation(dna_string, error_rate=0.01)
                
                # 4. Decode and recover the original file from the corrupted DNA
                print(f"\n--- 3. Decoding corrupted DNA and recovering the file ---")
                success = dna_storage.decode_dna_to_file(corrupted_dna, recovered_file)
                
                # 5. Verification
                if success and recovered_file.exists():
                    print("\n--- 4. Verification ---")
                    recovered_content = recovered_file.read_text()
                    print(f"  Original Content:  '{original_content}'")
                    print(f"  Recovered Content: '{recovered_content}'")
                    if original_content == recovered_content:
                        print("\n  [SUCCESS] The recovered data perfectly matches the original!")
                    else:
                        print("\n  [FAILURE] Data mismatch. The corruption was too severe to be corrected.")
                else:
                    print("\n  [FAILURE] Could not recover the file.")

        finally:
            # Clean up demo files
            if original_file.exists(): original_file.unlink()
            if recovered_file.exists(): recovered_file.unlink()

    print("\n=========================================================")
    print("=== DNA Storage Simulator Complete ===")
    print("=========================================================")
