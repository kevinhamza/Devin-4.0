# Devin/recovery/quantum_self_repair/blockchain_rollback.py
# Purpose: A proof-of-concept blockchain for storing immutable, verifiable
#          recovery points, secured with post-quantum digital signatures.

import hashlib
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    # This module integrates our PQC tool to sign the recovery points
    from quantum.post_quantum_crypto import PostQuantumCrypto
    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False


# Configure basic logging
logger = logging.getLogger("BlockchainRollback")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


@dataclass
class RecoveryPoint:
    """Represents a single recovery point transaction."""
    snapshot_id: str
    snapshot_hash: str # SHA256 hash of the backup archive
    timestamp: str
    signature: Optional[str] = None # PQC signature (as hex)


class BlockchainRollback:
    """
    Manages a blockchain for storing immutable recovery points.
    """
    def __init__(self, difficulty: int = 4):
        if not PQC_AVAILABLE:
            raise ImportError("PostQuantumCrypto module is required. Ensure all project files are present.")
        
        self.chain: List[Dict[str, Any]] = []
        self.pending_recovery_points: List[RecoveryPoint] = []
        self.difficulty = difficulty
        
        # Initialize PQC for signing
        self.pqc = PostQuantumCrypto()
        self.pqc_algo = "Dilithium3"
        logger.info("Generating PQC keypair for the blockchain...")
        self.pqc_public_key, self.pqc_private_key = self.pqc.signature_generate_keypair(self.pqc_algo)
        
        # Create the genesis block
        self.create_block(previous_hash="1", proof=100)

    def create_block(self, proof: int, previous_hash: str) -> Dict[str, Any]:
        """Creates a new block and adds it to the chain."""
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.now()),
            'recovery_points': [rp.__dict__ for rp in self.pending_recovery_points],
            'proof': proof,
            'previous_hash': previous_hash or self.hash_block(self.chain[-1]),
        }
        self.pending_recovery_points = []
        self.chain.append(block)
        return block

    def get_last_block(self) -> Dict[str, Any]:
        """Returns the last block in the chain."""
        return self.chain[-1]

    @staticmethod
    def hash_block(block: Dict[str, Any]) -> str:
        """Hashes a block."""
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof: int) -> int:
        """Simple Proof of Work algorithm."""
        proof = 0
        while not self.is_valid_proof(last_proof, proof):
            proof += 1
        return proof

    def is_valid_proof(self, last_proof: int, proof: int) -> bool:
        """Validates the proof."""
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:self.difficulty] == "0" * self.difficulty

    def add_recovery_point(self, snapshot_id: str, snapshot_hash: str) -> int:
        """Adds a new, PQC-signed recovery point to the pending list."""
        timestamp = str(datetime.now())
        
        # Data to be signed
        data_to_sign = f"{snapshot_id}{snapshot_hash}{timestamp}".encode()
        
        # Sign with Dilithium
        signature_bytes = self.pqc.signature_sign_message(self.pqc_algo, self.pqc_private_key, data_to_sign)
        
        point = RecoveryPoint(
            snapshot_id=snapshot_id,
            snapshot_hash=snapshot_hash,
            timestamp=timestamp,
            signature=signature_bytes.hex() # Store signature as hex string
        )
        self.pending_recovery_points.append(point)
        return self.get_last_block()['index'] + 1

    def is_chain_valid(self) -> bool:
        """Validates the entire blockchain's integrity."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            prev_block = self.chain[i - 1]

            # 1. Check if the previous_hash link is correct
            if current_block['previous_hash'] != self.hash_block(prev_block):
                logger.error(f"Chain invalid: Hash link broken at block {current_block['index']}")
                return False
                
            # 2. Check if the proof of work for the previous block is valid
            if not self.is_valid_proof(prev_block['proof'], current_block['proof']):
                 logger.error(f"Chain invalid: Proof of work incorrect at block {current_block['index']}")
                 return False

            # 3. Check if all recovery point signatures in the current block are valid
            for rp_data in current_block['recovery_points']:
                rp = RecoveryPoint(**rp_data)
                data_to_verify = f"{rp.snapshot_id}{rp.snapshot_hash}{rp.timestamp}".encode()
                signature_bytes = bytes.fromhex(rp.signature)
                if not self.pqc.signature_verify(self.pqc_algo, self.pqc_public_key, data_to_verify, signature_bytes):
                    logger.error(f"Chain invalid: PQC signature invalid for snapshot '{rp.snapshot_id}' in block {current_block['index']}")
                    return False
        return True

# --- Example Usage ---
if __name__ == "__main__":
    if not PQC_AVAILABLE:
        print("\nERROR: The PostQuantumCrypto module is required for this demo.")
    else:
        print("=========================================================")
        print("=== PQC-Secured Blockchain Recovery Log Prototype ⛓️🛡️ ===")
        print("=========================================================")
        
        blockchain = BlockchainRollback(difficulty=4)
        
        # 1. Add some recovery points and "mine" blocks for them
        print("\n--- Adding and mining recovery points ---")
        blockchain.add_recovery_point("snap_001", "hash_of_snap_001_data")
        last_proof = blockchain.get_last_block()['proof']
        proof = blockchain.proof_of_work(last_proof)
        blockchain.create_block(proof, blockchain.hash_block(blockchain.get_last_block()))
        logger.info("Mined block for snap_001.")
        
        blockchain.add_recovery_point("snap_002", "hash_of_snap_002_data")
        last_proof = blockchain.get_last_block()['proof']
        proof = blockchain.proof_of_work(last_proof)
        blockchain.create_block(proof, blockchain.hash_block(blockchain.get_last_block()))
        logger.info("Mined block for snap_002.")

        print("\n--- Current Blockchain State ---")
        print(json.dumps(blockchain.chain, indent=2))
        
        # 2. Verify the integrity of the pristine chain
        print("\n--- Verifying Chain Integrity ---")
        if blockchain.is_chain_valid():
            print("[SUCCESS] The blockchain is valid and untampered.")
        else:
            print("[FAILURE] The blockchain is invalid.")
            
        # 3. Simulate a malicious tamper
        print("\n--- Simulating a Malicious Tamper ---")
        # Attacker tries to alter the hash of a past snapshot
        print("An attacker is trying to modify the data in Block 2...")
        blockchain.chain[1]['recovery_points'][0]['snapshot_hash'] = "malicious_fake_hash"
        
        # 4. Re-verify the chain
        print("\n--- Re-Verifying Chain Integrity After Tamper ---")
        if not blockchain.is_chain_valid():
            print("[SUCCESS] The tamper was detected! The blockchain is correctly reported as invalid.")
        else:
            print("[FAILURE] The tamper was NOT detected.")

        print("\n=========================================================")
        print("=== Blockchain Prototype Complete ===")
        print("=========================================================")
