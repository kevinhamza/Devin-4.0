# Devin/enterprise/license_manager.py
# Purpose: Validates user licenses or subscription tiers for premium features/limits.

import os
import json
import logging
import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass, field, asdict

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("LicenseManager")

# --- Enums and Data Structures ---

class LicenseTier(Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    TRIAL = "trial"

@dataclass
class LicenseInfo:
    """Represents the details of a user's license or subscription."""
    license_id: str
    # Identifier linking the license (can be user ID, org ID, API key hash, etc.)
    identifier: str
    tier: LicenseTier
    status: Literal["active", "expired", "cancelled", "trialing"] = "active"
    # Expiry date in UTC ISO format string. None means non-expiring (or handled by status).
    expiry_utc: Optional[str] = None
    # List of specific feature keys enabled by this license (overrides/supplements tier defaults)
    features_enabled: List[str] = field(default_factory=list)
    # Specific usage limits associated with this license
    usage_limits: Dict[str, Union[int, float]] = field(default_factory=lambda: {
        "max_api_calls_per_day": 1000, # Example default limits for FREE tier maybe
        "max_concurrent_tasks": 2,
        "max_model_tokens_per_request": 4096
    })
    issued_utc: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    last_validated_utc: Optional[str] = None # When was it last checked against source?

# --- Feature to Tier Mapping (Conceptual) ---
# Defines which features require which minimum license tier(s).
# This could be loaded from configuration as well.
FEATURE_TIER_MAP: Dict[str, List[LicenseTier]] = {
    "basic_chat": [LicenseTier.FREE, LicenseTier.PRO, LicenseTier.ENTERPRISE, LicenseTier.TRIAL],
    "code_completion": [LicenseTier.PRO, LicenseTier.ENTERPRISE, LicenseTier.TRIAL],
    "advanced_pentesting_tools": [LicenseTier.PRO, LicenseTier.ENTERPRISE],
    "run_custom_plugins": [LicenseTier.PRO, LicenseTier.ENTERPRISE],
    "high_concurrency": [LicenseTier.ENTERPRISE],
    "sso_integration": [LicenseTier.ENTERPRISE],
    "priority_support": [LicenseTier.ENTERPRISE],
    "unlimited_history": [LicenseTier.PRO, LicenseTier.ENTERPRISE],
    # Add more features and map them to tiers
}

# --- License Manager Class ---

class LicenseManager:
    """
    Manages and validates user licenses/subscriptions.

    Conceptual implementation using an in-memory dictionary loaded from a file.
    Production systems should use a database or external licensing service API.
    """
    DEFAULT_LICENSE_DATA_PATH = "./data/license_data.json" # Example path

    def __init__(self, license_data_path: Optional[str] = None):
        """
        Initializes the LicenseManager.

        Args:
            license_data_path (Optional[str]): Path to the JSON file containing license data.
                                               If None, uses default or empty.
        """
        self.license_path = license_data_path or self.DEFAULT_LICENSE_DATA_PATH
        # Stores license info keyed by the identifier (user_id, api_key_hash, etc.)
        self.licenses: Dict[str, LicenseInfo] = {}
        self._load_licenses()
        logger.info(f"LicenseManager initialized. Loaded {len(self.licenses)} licenses from {self.license_path or 'in-memory default'}.")

    def _load_licenses(self):
        """Loads license data from the specified source (conceptual JSON load)."""
        logger.info(f"Conceptual: Loading license data from '{self.license_path}'...")
        # --- Placeholder: Load from secure DB or Licensing API ---
        # This simple file load is NOT suitable for production.
        if os.path.exists(self.license_path):
            try:
                with open(self.license_path, 'r') as f:
                    raw_data = json.load(f)
                    # Deserialize into LicenseInfo objects
                    self.licenses = {}
                    for identifier, data in raw_data.items():
                        try:
                            # Convert tier string to Enum
                            data['tier'] = LicenseTier(data.get('tier', 'free'))
                            self.licenses[identifier] = LicenseInfo(**data)
                        except (ValueError, TypeError) as deser_e:
                            logger.error(f"Skipping invalid license data for identifier '{identifier}': {deser_e} - Data: {data}")
                logger.info(f"Loaded {len(self.licenses)} licenses.")
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load licenses from '{self.license_path}': {e}. Starting empty.")
                self.licenses = {}
        else:
            logger.warning(f"License data file not found: '{self.license_path}'. Using empty/default licenses.")
            # Add a default free license maybe?
            # self.licenses["guest_user"] = LicenseInfo(license_id="LIC-FREE-001", identifier="guest_user", tier=LicenseTier.FREE, status="active")
        # --- End Placeholder ---

    def _save_licenses(self):
        """Conceptual saving of license state (Not typically done here - usually managed externally)."""
        if not self.license_path: return
        logger.info(f"Conceptual: Saving license data to '{self.license_path}'...")
        try:
            data_to_save = {ident: asdict(lic) for ident, lic in self.licenses.items()}
            # Convert enums back to strings
            for ident in data_to_save:
                 if isinstance(data_to_save[ident].get('tier'), Enum):
                      data_to_save[ident]['tier'] = data_to_save[ident]['tier'].value
            with open(self.license_path, 'w') as f: json.dump(data_to_save, f, indent=2)
        except IOError as e: logger.error(f"Failed to save license data: {e}")


    def _get_license_by_identifier(self, identifier: str) -> Optional[LicenseInfo]:
        """Internal helper to find license info."""
        # TODO: Add periodic refresh from source via `_load_licenses` or external check?
        return self.licenses.get(identifier)

    def validate_license(self, identifier: str) -> Optional[LicenseInfo]:
        """
        Validates if an active license exists for the given identifier and is not expired.

        Args:
            identifier (str): The user ID, API key hash, or other identifier linked to the license.

        Returns:
            Optional[LicenseInfo]: The valid LicenseInfo object if found and active, otherwise None.
        """
        logger.debug(f"Validating license for identifier: {identifier}")
        license_info = self._get_license_by_identifier(identifier)

        if not license_info:
            logger.debug(f"  - Validation Failed: No license found for identifier.")
            return None

        if license_info.status != "active":
            logger.debug(f"  - Validation Failed: License status is '{license_info.status}'.")
            return None

        # Check expiry date if present
        if license_info.expiry_utc:
            try:
                expiry_dt = datetime.datetime.fromisoformat(license_info.expiry_utc.replace('Z', '+00:00'))
                now_dt = datetime.datetime.now(datetime.timezone.utc)
                if now_dt > expiry_dt:
                    logger.warning(f"  - Validation Failed: License '{license_info.license_id}' for '{identifier}' expired on {license_info.expiry_utc}.")
                    # Optionally update status in persistent store here
                    # license_info.status = "expired"
                    # self._save_licenses() # If managing state locally
                    return None # Expired
            except ValueError:
                logger.error(f"  - Validation Error: Invalid expiry date format '{license_info.expiry_utc}' for license '{license_info.license_id}'.")
                return None # Treat invalid date as invalid license

        # If we reach here, the license is considered valid and active
        logger.debug(f"  - Validation Successful: Found active license ID '{license_info.license_id}', Tier '{license_info.tier.value}'.")
        # Optionally update last validated timestamp
        # license_info.last_validated_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return license_info

    def check_feature_access(self, identifier: str, feature_key: str) -> bool:
        """
        Checks if the valid license associated with the identifier grants access to a specific feature.

        Args:
            identifier (str): The user ID, API key hash, etc.
            feature_key (str): The unique key identifying the feature (must match keys in FEATURE_TIER_MAP).

        Returns:
            bool: True if access is granted, False otherwise.
        """
        logger.debug(f"Checking feature '{feature_key}' access for identifier: {identifier}")
        valid_license = self.validate_license(identifier)

        if not valid_license:
            logger.debug("  - Access Denied: No valid license found.")
            return False

        # Check direct feature enablement on license first
        if feature_key in valid_license.features_enabled:
            logger.debug(f"  - Access Granted: Feature '{feature_key}' explicitly enabled on license '{valid_license.license_id}'.")
            return True

        # Check if the license tier grants access based on the map
        required_tiers = FEATURE_TIER_MAP.get(feature_key)
        if not required_tiers:
            logger.warning(f"  - Access Denied: Feature '{feature_key}' not defined in FEATURE_TIER_MAP.")
            return False # Feature unknown or requires no specific tier? Default deny.

        if valid_license.tier in required_tiers:
            logger.debug(f"  - Access Granted: License tier '{valid_license.tier.value}' meets requirement for feature '{feature_key}' (Needs: {required_tiers}).")
            return True
        else:
            logger.debug(f"  - Access Denied: License tier '{valid_license.tier.value}' does not meet requirement for feature '{feature_key}' (Needs: {required_tiers}).")
            return False

    def get_usage_limit(self, identifier: str, limit_key: str, default_value: int = 0) -> Union[int, float]:
        """
        Gets a specific usage limit (e.g., max API calls) for the identifier's valid license.

        Args:
            identifier (str): The user ID, API key hash, etc.
            limit_key (str): The key for the specific limit (e.g., "max_api_calls_per_day").
            default_value (int): Value to return if no valid license or specific limit is found.

        Returns:
            Union[int, float]: The configured limit value, or the default value.
        """
        logger.debug(f"Getting usage limit '{limit_key}' for identifier: {identifier}")
        valid_license = self.validate_license(identifier)
        limit = default_value
        if valid_license and valid_license.usage_limits:
            limit = valid_license.usage_limits.get(limit_key, default_value)

        logger.debug(f"  - Resolved limit for '{limit_key}': {limit}")
        return limit


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- License Manager Example (Conceptual) ---")

    # Create dummy license data file
    dummy_license_file = "./temp_license_data.json"
    dummy_data = {
        "user_admin_01": {
            "license_id": "LIC-ENT-001", "identifier": "user_admin_01", "tier": "enterprise",
            "status": "active", "expiry_utc": None, "features_enabled": [],
            "usage_limits": {"max_api_calls_per_day": 100000, "max_concurrent_tasks": 50}
        },
        "user_pro_01": {
            "license_id": "LIC-PRO-007", "identifier": "user_pro_01", "tier": "pro",
            "status": "active", "expiry_utc": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).isoformat() + "Z",
            "features_enabled": ["beta_feature_X"],
            "usage_limits": {"max_api_calls_per_day": 10000, "max_concurrent_tasks": 10}
        },
        "user_free_01": {
             "license_id": "LIC-FREE-111", "identifier": "user_free_01", "tier": "free",
             "status": "active", "expiry_utc": None, "features_enabled": [],
             "usage_limits": {"max_api_calls_per_day": 500, "max_concurrent_tasks": 1} # Stricter limits
        },
        "expired_user": {
            "license_id": "LIC-PRO-EXP", "identifier": "expired_user", "tier": "pro",
            "status": "active", # Status should ideally be updated based on expiry
            "expiry_utc": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat() + "Z",
             "usage_limits": {"max_api_calls_per_day": 10000, "max_concurrent_tasks": 10}
        }
    }
    try:
        with open(dummy_license_file, 'w') as f: json.dump(dummy_data, f, indent=2)
    except IOError as e: print(f"Error writing dummy license file: {e}")


    # Initialize manager
    license_manager = LicenseManager(license_data_path=dummy_license_file)

    # --- Test Validation ---
    print("\nValidating licenses:")
    print(f"Admin user valid? {'Yes' if license_manager.validate_license('user_admin_01') else 'No'}")
    print(f"Pro user valid? {'Yes' if license_manager.validate_license('user_pro_01') else 'No'}")
    print(f"Free user valid? {'Yes' if license_manager.validate_license('user_free_01') else 'No'}")
    print(f"Expired user valid? {'Yes' if license_manager.validate_license('expired_user') else 'No'}") # Should be No
    print(f"Unknown user valid? {'Yes' if license_manager.validate_license('unknown_user') else 'No'}")

    # --- Test Feature Access ---
    print("\nChecking feature access:")
    print(f"Admin access 'basic_chat'? {license_manager.check_feature_access('user_admin_01', 'basic_chat')}") # Yes (Enterprise)
    print(f"Admin access 'sso_integration'? {license_manager.check_feature_access('user_admin_01', 'sso_integration')}") # Yes (Enterprise)
    print(f"Pro user access 'code_completion'? {license_manager.check_feature_access('user_pro_01', 'code_completion')}") # Yes (Pro)
    print(f"Pro user access 'sso_integration'? {license_manager.check_feature_access('user_pro_01', 'sso_integration')}") # No (Pro)
    print(f"Free user access 'basic_chat'? {license_manager.check_feature_access('user_free_01', 'basic_chat')}") # Yes (Free)
    print(f"Free user access 'code_completion'? {license_manager.check_feature_access('user_free_01', 'code_completion')}") # No (Free)
    print(f"Expired user access 'code_completion'? {license_manager.check_feature_access('expired_user', 'code_completion')}") # No (Expired)

    # --- Test Usage Limits ---
    print("\nGetting usage limits:")
    print(f"Admin concurrent tasks: {license_manager.get_usage_limit('user_admin_01', 'max_concurrent_tasks', 1)}")
    print(f"Pro concurrent tasks: {license_manager.get_usage_limit('user_pro_01', 'max_concurrent_tasks', 1)}")
    print(f"Free concurrent tasks: {license_manager.get_usage_limit('user_free_01', 'max_concurrent_tasks', 1)}")
    print(f"Unknown user concurrent tasks: {license_manager.get_usage_limit('unknown_user', 'max_concurrent_tasks', 1)}") # Uses default
    print(f"Pro user max API calls: {license_manager.get_usage_limit('user_pro_01', 'max_api_calls_per_day', 0)}")

    # Cleanup dummy file
    if os.path.exists(dummy_license_file): os.remove(dummy_license_file)

    print("\n--- End Example ---")
