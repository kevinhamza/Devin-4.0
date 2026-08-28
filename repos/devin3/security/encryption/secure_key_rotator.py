# Devin/security/encryption/secure_key_rotator.py
# Purpose: A framework for automatically rotating secrets like API keys on a
#          schedule, using a pluggable provider architecture.

import logging
import json
import uuid
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from abc import ABC, abstractmethod


# Configure basic logging
logger = logging.getLogger("KeyRotator")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class BaseKeyProvider(ABC):
    """Abstract Base Class for a key provider.
    Defines the interface for rotating a key with a specific service."""
    
    @abstractmethod
    def rotate_key(self, old_key: str) -> Optional[str]:
        """
        Performs the key rotation logic for a specific service.
        
        Args:
            old_key: The current, active key that needs to be replaced.
            
        Returns:
            The new, active key if rotation was successful, otherwise None.
        """
        pass


class SecureKeyRotator:
    """
    Manages the scheduled rotation of a key using a given provider.
    """
    def __init__(
        self,
        provider: BaseKeyProvider,
        vault_path: Path,
        key_name: str,
        rotation_interval_days: int
    ):
        self.provider = provider
        self.vault_path = vault_path
        self.key_name = key_name
        self.rotation_interval = timedelta(days=rotation_interval_days)
        
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
    def _load_vault(self) -> Dict:
        if self.vault_path.is_file():
            with open(self.vault_path, 'r') as f:
                return json.load(f)
        return {}
        
    def _save_vault(self, vault_data: Dict):
        with open(self.vault_path, 'w') as f:
            json.dump(vault_data, f, indent=2)

    def _rotation_loop(self):
        """The main background loop that checks if the key needs rotation."""
        while not self._stop_event.is_set():
            vault = self._load_vault()
            key_info = vault.get(self.key_name)
            
            if not key_info or 'last_rotated' not in key_info:
                logger.warning(f"Key '{self.key_name}' not found in vault or missing rotation date. Skipping.")
                self._stop_event.wait(self.rotation_interval.total_seconds())
                continue

            last_rotated_time = datetime.fromisoformat(key_info['last_rotated'])
            
            if datetime.now() > last_rotated_time + self.rotation_interval:
                logger.warning(f"Key '{self.key_name}' has expired. Initiating rotation...")
                old_key = key_info['key']
                
                new_key = self.provider.rotate_key(old_key)
                
                if new_key:
                    key_info['key'] = new_key
                    key_info['last_rotated'] = datetime.now().isoformat()
                    self._save_vault(vault)
                    logger.warning(f"SUCCESS: Key '{self.key_name}' was rotated and vault updated.")
                else:
                    logger.error(f"FAILURE: Rotation failed for key '{self.key_name}'. Check provider logs.")
            
            # Wait for the next check interval
            self._stop_event.wait(3600) # Check once per hour

    def start(self):
        """Starts the key rotator service in a background thread."""
        logger.info(f"Starting SecureKeyRotator service for '{self.key_name}'. Checking every hour.")
        self._thread = threading.Thread(target=self._rotation_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the key rotator service."""
        logger.info("Stopping SecureKeyRotator service.")
        self._stop_event.set()
        if self._thread:
            self._thread.join()

# --- Example Usage with a Mock Provider ---

class MockAPIService:
    """A mock of an external API service (e.g., AWS, GitHub) for demonstration."""
    def __init__(self, initial_key: str):
        self.active_keys = {initial_key: "ACTIVE"}
        
    def create_new_key(self, old_key_to_deprecate: str) -> Optional[str]:
        if self.active_keys.get(old_key_to_deprecate) == "ACTIVE":
            self.active_keys[old_key_to_deprecate] = "INACTIVE"
            new_key = f"mock-key-{uuid.uuid4().hex[:12]}"
            self.active_keys[new_key] = "ACTIVE"
            logger.info(f"(Mock Service) Deprecated '{old_key_to_deprecate[:15]}...' and created new key '{new_key[:15]}...'")
            return new_key
        else:
            logger.error(f"(Mock Service) Invalid or inactive key provided for deprecation: {old_key_to_deprecate}")
            return None

class MockServiceRotator(BaseKeyProvider):
    """An example implementation of a key provider for our mock service."""
    def __init__(self, api_service: MockAPIService):
        self.service = api_service
        
    def rotate_key(self, old_key: str) -> Optional[str]:
        return self.service.create_new_key(old_key)


if __name__ == "__main__":
    print("=========================================================")
    print("=== Secure Key Rotator Prototype 🔄🔑 ===")
    print("=========================================================")
    
    # 1. Setup the demo environment
    demo_vault_path = Path("secure_vault.json")
    initial_key = f"mock-key-{uuid.uuid4().hex[:12]}"
    
    # Create a vault file with a key that is very old, forcing an immediate rotation
    stale_date = (datetime.now() - timedelta(days=90)).isoformat()
    vault_content = {
        "my_app_api_key": {
            "key": initial_key,
            "last_rotated": stale_date
        }
    }
    with open(demo_vault_path, 'w') as f:
        json.dump(vault_content, f, indent=2)
        
    # Instantiate our mock service and the rotator for it
    mock_api = MockAPIService(initial_key=initial_key)
    mock_provider = MockServiceRotator(api_service=mock_api)

    rotator = None
    try:
        # 2. Initialize and start the rotator
        # We set the rotation interval to 30 days, but it will rotate immediately
        # because the key in the vault is 90 days old.
        rotator = SecureKeyRotator(
            provider=mock_provider,
            vault_path=demo_vault_path,
            key_name="my_app_api_key",
            rotation_interval_days=30
        )
        
        print(f"Initial key in vault: {initial_key}")
        rotator.start()
        
        # 3. Wait for the rotation to happen
        print("\nRotator is running. It will detect the stale key and rotate it momentarily...")
        time.sleep(2) # Give the thread a moment to run
        
        # 4. Verify the result
        with open(demo_vault_path, 'r') as f:
            final_vault_content = json.load(f)
        
        final_key = final_vault_content["my_app_api_key"]["key"]
        print(f"Final key in vault:   {final_key}")
        
        print("\n--- Verification ---")
        if final_key != initial_key:
            print("[SUCCESS] The API key was successfully rotated and the vault was updated.")
        else:
            print("[FAILURE] The API key was not rotated.")
        
    finally:
        # 5. Clean up
        if rotator:
            rotator.stop()
        if demo_vault_path.exists():
            demo_vault_path.unlink()

    print("\n=========================================================")
    print("=== Key Rotator Prototype Complete ===")
    print("=========================================================")
