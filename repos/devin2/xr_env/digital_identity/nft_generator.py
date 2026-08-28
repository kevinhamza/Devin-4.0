# Devin/xr_env/digital_identity/nft_generator.py
# Purpose: A self-contained system for generating unique digital assets and
#          simulating the process of minting them as NFTs for blockchain identity.

import logging
import json
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple
from PIL import Image, ImageDraw

# Configure basic logging
logger = logging.getLogger("NFTGenerator")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

@dataclass
class NFTReceipt:
    """Represents the successful result of a simulated NFT mint."""
    token_id: int
    owner_address: str
    metadata_ipfs_url: str
    image_ipfs_url: str
    transaction_hash: str

class MockIPFSUploader:
    """Simulates uploading a file to IPFS."""
    def __init__(self, storage_dir: str = "mock_ipfs_storage"):
        self.storage_path = Path(storage_dir)
        self.storage_path.mkdir(exist_ok=True)
        logger.info(f"Mock IPFS storage initialized at: '{self.storage_path.resolve()}'")

    def upload(self, file_content: bytes, filename: str) -> str:
        """Saves a file locally and returns a fake IPFS URL."""
        # Generate a fake but realistic-looking IPFS hash
        fake_hash = "Qm" + "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=44))
        
        (self.storage_path / filename).write_bytes(file_content)
        
        ipfs_url = f"ipfs://{fake_hash}/{filename}"
        logger.info(f"Simulated upload of '{filename}'. IPFS URL: {ipfs_url}")
        return ipfs_url

class MockBlockchainMinter:
    """Simulates minting an NFT on a blockchain."""
    def __init__(self, ledger_file: str = "mock_blockchain_ledger.json"):
        self.ledger_path = Path(ledger_file)
        self.token_id_counter = self._load_last_token_id()

    def _load_last_token_id(self) -> int:
        if not self.ledger_path.exists():
            return 0
        with open(self.ledger_path, 'r') as f:
            data = json.load(f)
            return len(data.get("tokens", []))

    def mint_nft(self, owner_address: str, metadata_ipfs_url: str) -> Tuple[int, str]:
        """Creates a new token, adds it to the ledger, and returns its ID and a fake transaction hash."""
        self.token_id_counter += 1
        new_token_id = self.token_id_counter
        
        # Generate a fake but realistic-looking transaction hash
        tx_hash = "0x" + "".join(random.choices("abcdef0123456789", k=64))
        
        new_token_record = {
            "token_id": new_token_id,
            "owner": owner_address,
            "metadata_uri": metadata_ipfs_url,
            "tx_hash": tx_hash
        }
        
        ledger_data = {"tokens": []}
        if self.ledger_path.exists():
            with open(self.ledger_path, 'r') as f:
                ledger_data = json.load(f)
        
        ledger_data["tokens"].append(new_token_record)
        
        with open(self.ledger_path, 'w') as f:
            json.dump(ledger_data, f, indent=2)
        
        logger.info(f"Simulated MINT successful for Token ID {new_token_id}. TxHash: {tx_hash}")
        return new_token_id, tx_hash

class NFTGenerator:
    """The main orchestrator for creating a complete, mintable NFT asset."""
    def __init__(self, uploader: MockIPFSUploader, minter: MockBlockchainMinter):
        self.uploader = uploader
        self.minter = minter
        self.colors = ["#FF5733", "#33FF57", "#3357FF", "#F1C40F", "#9B59B6", "#E74C3C"]

    def _generate_generative_art(self, asset_id: str) -> Tuple[Image.Image, List[Dict]]:
        """Creates a simple piece of generative art using Pillow."""
        img = Image.new('RGB', (500, 500), color=random.choice(self.colors))
        draw = ImageDraw.Draw(img)
        
        traits = [{"trait_type": "background_color", "value": img.getpixel((0,0))}]
        
        # Draw some random shapes
        shape_count = random.randint(2, 5)
        for _ in range(shape_count):
            shape_type = random.choice(['rectangle', 'ellipse'])
            pos = [random.randint(50, 450), random.randint(50, 450), random.randint(50, 450), random.randint(50, 450)]
            shape_color = random.choice(self.colors)
            if shape_type == 'rectangle':
                draw.rectangle(pos, fill=shape_color)
            else:
                draw.ellipse(pos, fill=shape_color)
        
        traits.append({"trait_type": "shape_count", "value": shape_count})
        return img, traits

    def create_nft_for_identity(self, owner_address: str, name: str, description: str) -> NFTReceipt:
        """Runs the full pipeline from art generation to simulated minting."""
        logger.info(f"--- Starting NFT generation process for '{name}' ---")
        
        # 1. Create the Asset
        asset_id = "devin_id_" + "".join(random.choices("0123456789", k=6))
        image, traits = self._generate_generative_art(asset_id)
        
        # 2. "Upload" the Asset to IPFS
        from io import BytesIO
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        image_bytes = img_byte_arr.getvalue()
        image_ipfs_url = self.uploader.upload(image_bytes, f"{asset_id}.png")

        # 3. Create the Metadata
        metadata = {
            "name": name,
            "description": description,
            "image": image_ipfs_url,
            "attributes": traits
        }
        metadata_bytes = json.dumps(metadata, indent=2).encode('utf-8')

        # 4. "Upload" the Metadata to IPFS
        metadata_ipfs_url = self.uploader.upload(metadata_bytes, f"{asset_id}.json")

        # 5. "Mint" the NFT on the Blockchain
        token_id, tx_hash = self.minter.mint_nft(owner_address, metadata_ipfs_url)
        
        logger.info(f"--- NFT generation process for '{name}' complete! ---")
        return NFTReceipt(
            token_id=token_id,
            owner_address=owner_address,
            metadata_ipfs_url=metadata_ipfs_url,
            image_ipfs_url=image_ipfs_url,
            transaction_hash=tx_hash
        )

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== NFT Generator & Blockchain Identity Demo 🖼️🔗 ===")
    print("=========================================================")
    
    try:
        # 1. Initialize the simulated services
        ipfs_uploader = MockIPFSUploader()
        blockchain_minter = MockBlockchainMinter()
        
        # 2. Initialize the main generator
        nft_generator = NFTGenerator(uploader=ipfs_uploader, minter=blockchain_minter)
        
        # 3. Create a new NFT to represent a user's digital identity
        user_wallet = "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B" # Example address
        receipt = nft_generator.create_nft_for_identity(
            owner_address=user_wallet,
            name="Devin User Identity #1",
            description="A unique, procedurally generated identity token for the Devin AGI ecosystem."
        )
        
        # 4. Print the final result
        print("\n--- NFT Minting Receipt ---")
        print(f"  Status:         SUCCESS")
        print(f"  Owner:          {receipt.owner_address}")
        print(f"  Token ID:       {receipt.token_id}")
        print(f"  Image IPFS URL: {receipt.image_ipfs_url}")
        print(f"  Metadata URL:   {receipt.metadata_ipfs_url}")
        print(f"  Tx Hash:        {receipt.transaction_hash}")

        print("\nCheck the 'mock_ipfs_storage' and 'mock_blockchain_ledger.json' files to see the results.")

    except ImportError:
        print("\nERROR: The 'Pillow' library is required. Please run: pip install Pillow")
    except Exception as e:
        logger.error(f"Demo failed to run: {e}", exc_info=True)
    
    print("\n=========================================================")
    print("=== NFT Generator Demo Complete ===")
    print("=========================================================")
