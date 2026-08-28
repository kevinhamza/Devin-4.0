# Devin/modules/cloud_services_manager.py
# Purpose: A high-level manager for orchestrating complex, multi-step cloud
#          workflows, integrating user consent for dangerous actions.

import logging
from typing import Dict, Any

try:
    from modules.cloud_integration_module import CloudFacade
    from modules.user_interaction_module import UserInteractionManager
    from modules.cloud_integration_utilities import CloudProvider
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("CloudServicesManager")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

class CloudServicesManager:
    """
    Orchestrates high-level cloud tasks and integrates safety checks.
    """
    def __init__(self, cloud_facade: CloudFacade, uim: UserInteractionManager):
        """
        Initializes the manager with its dependencies.

        Args:
            cloud_facade (CloudFacade): The low-level client for cloud APIs.
            uim (UserInteractionManager): The module for user interaction and consent.
        """
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        
        self.facade = cloud_facade
        self.uim = uim
        logger.info("CloudServicesManager initialized.")

    def list_vms(self, provider: str) -> Any:
        """A simple pass-through to the facade for listing VMs."""
        provider_enum = CloudProvider[provider.upper()]
        return self.facade.list_vms(provider_enum)

    def stop_vm(self, provider: str, instance_id: str) -> Dict[str, Any]:
        """
        Stops a virtual machine after getting explicit user confirmation.
        This is a high-level workflow that adds a safety layer.
        """
        logger.info(f"Initiating workflow to stop VM '{instance_id}' in {provider.upper()}...")
        
        # --- Safety and Consent Step ---
        prompt = f"You are about to stop the virtual machine '{instance_id}' in {provider.upper()}."
        if not self.uim.ask_for_confirmation(prompt, is_dangerous=True):
            logger.warning("VM stop operation aborted by user.")
            return {"status": "aborted", "message": "User denied confirmation."}

        # --- Execution Step ---
        logger.info(f"User confirmed. Proceeding to stop VM '{instance_id}'...")
        provider_enum = CloudProvider[provider.upper()]
        result = self.facade.stop_vm(provider=provider_enum, instance_id=instance_id)

        if result and result.get("success"):
            self.uim.display_message(f"Successfully stopped VM '{instance_id}'.", level='success')
        else:
            self.uim.display_message(f"Failed to stop VM '{instance_id}'. Reason: {result.get('error')}", level='error')
            
        return result

# --- Example Usage ---
if __name__ == "__main__":
    from unittest.mock import MagicMock

    print("=========================================================")
    print("=== Cloud Services Manager Demo ☁️🔐 ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module is missing: {_import_error}")
    else:
        # 1. Create mock versions of the dependencies
        mock_facade = MagicMock(spec=CloudFacade)
        mock_facade.stop_vm.return_value = {"success": True, "instance_id": "i-12345"}
        
        mock_uim = MagicMock(spec=UserInteractionManager)
        
        # 2. Instantiate the real CloudServicesManager with the mocks
        cloud_manager = CloudServicesManager(cloud_facade=mock_facade, uim=mock_uim)
        
        # --- DEMO CASE 1: User CONFIRMS the action ---
        print("\n--- 1. Testing workflow where user CONFIRMS ---")
        mock_uim.ask_for_confirmation.return_value = True # Simulate user typing 'yes'
        
        cloud_manager.stop_vm(provider="AWS", instance_id="i-12345")
        
        # Verify that the dangerous action was called
        mock_facade.stop_vm.assert_called_once()
        print("--> User confirmed, and the stop_vm method was called as expected.")
        
        # --- DEMO CASE 2: User DENIES the action ---
        print("\n--- 2. Testing workflow where user DENIES ---")
        mock_facade.stop_vm.reset_mock() # Reset the call count for the next test
        mock_uim.ask_for_confirmation.return_value = False # Simulate user typing 'no'
        
        cloud_manager.stop_vm(provider="AWS", instance_id="i-67890")
        
        # Verify that the dangerous action was NOT called
        mock_facade.stop_vm.assert_not_called()
        print("--> User denied, and the stop_vm method was NOT called, as expected.")

    print("\n=========================================================")
    print("=== Cloud Services Manager Demo Complete ===")
    print("=========================================================")
