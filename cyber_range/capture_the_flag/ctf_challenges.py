# Devin/cyber_range/capture_the_flag/ctf_challenges.py
# Purpose: Defines and manages CTF challenges within the cyber range.

import os
import uuid
import datetime
import logging
from enum import Enum
from typing import Dict, Any, List, Optional, TypedDict, Union
from dataclasses import dataclass, field

# Conceptual imports for interacting with other cyber range components
# from ..resource_manager import ResourceManager # Manages VMs, containers, networks
# from ..scenario_manager import ScenarioManager # Manages overall state/setup

# --- Enums and Data Structures ---

class ChallengeCategory(str, Enum):
    WEB = "Web Exploitation"
    PWN = "Binary Exploitation / Pwnable"
    CRYPTO = "Cryptography"
    REVERSE = "Reverse Engineering"
    FORENSICS = "Digital Forensics"
    MISC = "Miscellaneous"
    OSINT = "Open Source Intelligence"

class ChallengeDifficulty(str, Enum):
    BEGINNER = "Beginner"
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    INSANE = "Insane"

class ChallengeStatus(str, Enum):
    STOPPED = "Stopped"
    STARTING = "Starting"
    RUNNING = "Running"
    STOPPING = "Stopping"
    ERROR = "Error"
    SOLVED = "Solved" # User-specific status might be tracked elsewhere (scoreboard)

@dataclass
class CTFChallenge:
    """Represents a single CTF challenge."""
    name: str
    description: str
    category: ChallengeCategory
    difficulty: ChallengeDifficulty
    points: int
    # --- Flag Handling (CRITICAL SECURITY NOTE) ---
    # DO NOT store real flags directly here. Use a secure retrieval method.
    # This placeholder might store a reference ID, hash, or env var name.
    flag_reference: str # e.g., "ENV:CHALLENGE_1_FLAG", "VAULT:secret/ctf/chal1", "HASH:sha256:abc..."
    # Alternatively, structure could load flag into memory from secure source on init.
    # (Field re-ordered below the required fields above -- dataclasses require
    # every field with a default to come after all fields without one.)
    id: str = field(default_factory=lambda: f"CTF-{uuid.uuid4().hex[:8].upper()}")

    # --- Environment Management ---
    # List of resource identifiers needed (VM templates, container images, network names)
    required_resources: List[str] = field(default_factory=list)
    # Current runtime status of the challenge environment
    current_status: ChallengeStatus = ChallengeStatus.STOPPED
    # Information needed to connect (IPs, ports, URLs) - populated when running
    connection_info: Dict[str, Any] = field(default_factory=dict)
    # Startup/provisioning hints or script reference
    provisioning_script: Optional[str] = None # e.g., path to an Ansible playbook or setup script

# --- CTF Challenge Manager ---

class CTFChallengeManager:
    """
    Manages the definition, lifecycle, and flag verification of CTF challenges.
    Interacts conceptually with ResourceManager and ScenarioManager.
    """

    def __init__(self, resource_manager: Optional[Any] = None, scenario_manager: Optional[Any] = None):
        """
        Initializes the CTFChallengeManager.

        Args:
            resource_manager: Instance of the ResourceManager (conceptual).
            scenario_manager: Instance of the ScenarioManager (conceptual).
        """
        # In a real implementation, these would be injected dependencies.
        self.resource_manager = resource_manager
        self.scenario_manager = scenario_manager
        self.challenges: Dict[str, CTFChallenge] = {} # {challenge_id: CTFChallenge_instance}
        self._load_challenges()
        logging.info(f"CTFChallengeManager initialized with {len(self.challenges)} challenges defined.")

    def _load_challenges(self):
        """
        Loads challenge definitions.
        (Conceptual: Should load from external files like YAML/JSON instead of hardcoding).
        """
        logging.info("Loading CTF challenge definitions...")
        # --- Hardcoded Examples (Replace with loading from files/DB) ---
        challenges_data = [
             {
                "name": "Web Beginner: Login Bypass",
                "description": "A simple web login form. Can you bypass the authentication? Find the flag on the dashboard page.",
                "category": ChallengeCategory.WEB, "difficulty": ChallengeDifficulty.BEGINNER, "points": 50,
                "flag_reference": "ENV:WEB_BEGINNER_FLAG", # Flag stored in env var WEB_BEGINNER_FLAG
                "required_resources": ["ctf-web-simple-login-container"],
                "provisioning_script": "scripts/setup_web_beginner.sh"
            },
            {
                "name": "Pwn Easy: Buffer Overflow 101",
                "description": "A basic C program vulnerable to a buffer overflow. Get shell access to read flag.txt.",
                "category": ChallengeCategory.PWN, "difficulty": ChallengeDifficulty.EASY, "points": 100,
                "flag_reference": "HASH:sha256:d0e8f5...", # Hypothetical hash reference
                "required_resources": ["ctf-pwn-bof101-container", "ctf-debug-tools-optional"],
            },
             {
                "name": "Crypto Medium: Simple Substitution",
                "description": "This ciphertext was encrypted with a simple substitution cipher. The flag format is flag{...}. Ciphertext provided in description.",
                "category": ChallengeCategory.CRYPTO, "difficulty": ChallengeDifficulty.MEDIUM, "points": 150,
                "flag_reference": "VAULT:secret/ctf/crypto_subst", # Flag stored in Vault
                "required_resources": [], # Crypto challenges often don't need runtime env
            },
            {
                "name": "Rev Hard: Obfuscated Binary",
                "description": "Reverse engineer this Linux binary to find the validation algorithm and determine the flag.",
                "category": ChallengeCategory.REVERSE, "difficulty": ChallengeDifficulty.HARD, "points": 300,
                "flag_reference": "FILE:/ctf_flags/rev_hard.flag", # Flag in a secure file path
                "required_resources": ["ctf-rev-hard-binary-file"], # Resource might just be the file itself
            }
            # Add more challenge definitions...
        ]

        for data in challenges_data:
            challenge = CTFChallenge(**data) # type: ignore[arg-type] # Okay for Dict->Dataclass
            self.challenges[challenge.id] = challenge
        logging.info(f"Loaded {len(self.challenges)} challenge definitions.")

    def _get_correct_flag(self, challenge_id: str) -> Optional[str]:
        """
        Retrieves the correct flag for a challenge ID from its secure location.

        *** CRITICAL SECURITY IMPLEMENTATION NEEDED ***
        This method MUST securely fetch the flag based on the 'flag_reference'
        stored in the challenge definition (e.g., from environment variables,
        a secrets manager like Vault, encrypted file, database).
        NEVER return hardcoded flags from here.

        Args:
            challenge_id (str): The ID of the challenge.

        Returns:
            Optional[str]: The correct flag string, or None if retrieval fails.
        """
        if challenge_id not in self.challenges:
            return None
        flag_ref = self.challenges[challenge_id].flag_reference
        logging.debug(f"Retrieving flag for challenge {challenge_id} using reference: {flag_ref}")

        # --- Placeholder Logic (Replace with secure retrieval) ---
        if flag_ref.startswith("ENV:"):
            var_name = flag_ref.split(":", 1)[1]
            flag = os.environ.get(var_name)
            if not flag: logging.error(f"Flag environment variable '{var_name}' not found for challenge {challenge_id}")
            return flag # Example: flag{dummy_flag_from_env_web_beginner}
        elif flag_ref.startswith("HASH:"):
            # In a real system, you wouldn't store the flag here. You'd hash the submission
            # and compare hashes. This is just a placeholder for structure.
            logging.warning("Flag retrieval via HASH ref is placeholder only. Comparing hashes is preferred.")
            return "flag{dummy_pwn_flag_for_hash_ref}"
        elif flag_ref.startswith("VAULT:"):
            secret_path = flag_ref.split(":", 1)[1]
            # Conceptual call to Vault client library
            # flag = vault_client.read_secret(secret_path)
            logging.info(f"Conceptual: Reading flag from Vault path {secret_path}")
            return "flag{dummy_crypto_flag_from_vault}"
        elif flag_ref.startswith("FILE:"):
             flag_path = flag_ref.split(":", 1)[1]
             try:
                 # Ensure path is restricted and secure
                 # with open(secure_flag_path(flag_path), 'r') as f: flag = f.read().strip()
                 logging.info(f"Conceptual: Reading flag from secure file path {flag_path}")
                 return "flag{dummy_rev_flag_from_file}"
             except Exception as e:
                 logging.error(f"Failed to read flag file {flag_path}: {e}")
                 return None
        else:
             logging.error(f"Unsupported flag reference type for challenge {challenge_id}: {flag_ref}")
             return None
        # --- End Placeholder Logic ---

    def list_challenges(self) -> List[Dict[str, Any]]:
        """Returns a list of summary information for all available challenges."""
        logging.info("Listing available CTF challenges...")
        summary_list = []
        for chal in self.challenges.values():
            summary_list.append({
                "id": chal.id,
                "name": chal.name,
                "category": chal.category.value,
                "difficulty": chal.difficulty.value,
                "points": chal.points,
                "status": chal.current_status.value # Reflect runtime status
            })
        return summary_list

    def get_challenge_details(self, challenge_id: str) -> Optional[CTFChallenge]:
        """Gets the full details of a specific challenge."""
        if challenge_id not in self.challenges:
            logging.warning(f"Challenge ID '{challenge_id}' not found.")
            return None
        return self.challenges[challenge_id]

    def start_challenge(self, challenge_id: str) -> Optional[Dict[str, Any]]:
        """
        Starts the environment for a specific CTF challenge.

        Args:
            challenge_id (str): The ID of the challenge to start.

        Returns:
            Optional[Dict[str, Any]]: Connection information (IPs, ports, URL) if successful, else None.
        """
        challenge = self.get_challenge_details(challenge_id)
        if not challenge:
            return None

        if challenge.current_status not in [ChallengeStatus.STOPPED, ChallengeStatus.ERROR]:
             logging.warning(f"Challenge '{challenge_id}' is already running or in transition state ({challenge.current_status}).")
             return challenge.connection_info # Return existing info if running

        logging.info(f"Starting environment for challenge: {challenge.name} ({challenge_id})...")
        challenge.current_status = ChallengeStatus.STARTING
        challenge.connection_info = {} # Clear old info

        # --- Placeholder: Interact with ResourceManager ---
        if self.resource_manager and challenge.required_resources:
            logging.info(f"  - Requesting resources: {challenge.required_resources}")
            try:
                # provision_result = self.resource_manager.provision(challenge.id, challenge.required_resources, challenge.provisioning_script)
                # Simulate successful provisioning with dummy connection info
                provision_result = {"status": "success", "outputs": {"ip_address": "10.10.10.5", "port": 8080, "url": f"http://10.10.10.5:8080"}}
                if provision_result and provision_result.get("status") == "success":
                    challenge.connection_info = provision_result.get("outputs", {})
                    challenge.current_status = ChallengeStatus.RUNNING
                    logging.info(f"Challenge '{challenge_id}' environment started successfully. Info: {challenge.connection_info}")
                    return challenge.connection_info
                else:
                     raise RuntimeError(f"Resource provisioning failed: {provision_result.get('message', 'Unknown error')}")
            except Exception as e:
                 logging.error(f"Failed to start environment for challenge '{challenge_id}': {e}")
                 challenge.current_status = ChallengeStatus.ERROR
                 return None
        elif not challenge.required_resources:
             logging.info(f"Challenge '{challenge_id}' requires no dynamic resources. Marking as running.")
             challenge.current_status = ChallengeStatus.RUNNING
             # Provide static info if applicable (e.g., ciphertext in description)
             challenge.connection_info = {"message": "No dynamic environment needed. See description."}
             return challenge.connection_info
        else:
             logging.error(f"Cannot start challenge '{challenge_id}': ResourceManager not available.")
             challenge.current_status = ChallengeStatus.ERROR
             return None
        # --- End Placeholder ---


    def stop_challenge(self, challenge_id: str) -> bool:
        """Stops the environment for a specific CTF challenge."""
        challenge = self.get_challenge_details(challenge_id)
        if not challenge:
            return False
        if challenge.current_status not in [ChallengeStatus.RUNNING, ChallengeStatus.ERROR]:
            logging.warning(f"Challenge '{challenge_id}' is not running or in error state ({challenge.current_status}). Cannot stop.")
            return challenge.current_status == ChallengeStatus.STOPPED # Return true if already stopped

        logging.info(f"Stopping environment for challenge: {challenge.name} ({challenge_id})...")
        challenge.current_status = ChallengeStatus.STOPPING

        # --- Placeholder: Interact with ResourceManager ---
        if self.resource_manager and challenge.required_resources:
            logging.info(f"  - Deprovisioning resources associated with challenge {challenge_id}")
            try:
                # success = self.resource_manager.deprovision(challenge.id) # Use challenge ID as instance identifier
                success = True # Simulate success
                if success:
                     logging.info(f"Challenge '{challenge_id}' environment stopped successfully.")
                else:
                     raise RuntimeError("Resource deprovisioning failed.")
            except Exception as e:
                 logging.error(f"Failed to stop environment for challenge '{challenge_id}': {e}")
                 # Even if deprovision fails, mark as stopped or error? Let's mark stopped.
                 challenge.current_status = ChallengeStatus.STOPPED # Or maybe ERROR?
                 challenge.connection_info = {}
                 return False # Indicate cleanup might have failed
        # --- End Placeholder ---

        challenge.current_status = ChallengeStatus.STOPPED
        challenge.connection_info = {}
        return True

    def submit_flag(self, challenge_id: str, submitted_flag: str, user_id: str = "default_user") -> bool:
        """
        Verifies a submitted flag against the correct flag for a challenge.

        Args:
            challenge_id (str): The ID of the challenge.
            submitted_flag (str): The flag submitted by the user.
            user_id (str): Identifier for the user submitting (for logging/scoreboard).

        Returns:
            bool: True if the flag is correct, False otherwise.
        """
        challenge = self.get_challenge_details(challenge_id)
        if not challenge:
            logging.warning(f"Flag submission failed: Challenge ID '{challenge_id}' not found.")
            return False

        # Optional: Check if challenge environment is running? Or allow flag submission anytime?
        # if challenge.current_status != ChallengeStatus.RUNNING:
        #    logging.warning(f"Flag submission for '{challenge_id}': Challenge not running.")
            # return False # Uncomment to enforce running state

        correct_flag = self._get_correct_flag(challenge_id)
        if correct_flag is None:
            logging.error(f"Flag submission check failed: Could not retrieve correct flag for challenge '{challenge_id}'.")
            return False

        logging.info(f"User '{user_id}' submitted flag for challenge '{challenge_id}'. Verifying...")

        # Normalize flags for comparison (e.g., remove whitespace, case-insensitive)
        normalized_submitted = submitted_flag.strip()
        normalized_correct = correct_flag.strip()

        # --- Comparison Logic (Adjust as needed) ---
        is_correct = normalized_submitted.lower() == normalized_correct.lower()
        # --- End Comparison ---

        if is_correct:
            logging.info(f"Correct flag submitted for challenge '{challenge_id}' by user '{user_id}'!")
            # Update challenge state locally if desired (though SOLVED is usually user-specific)
            # challenge.current_status = ChallengeStatus.SOLVED # Maybe not here, scoreboard handles this
            # --- Placeholder: Notify Scoreboard ---
            # self.scenario_manager.notify_solve(user_id, challenge_id, challenge.points)
            # --- End Placeholder ---
            return True
        else:
            logging.warning(f"Incorrect flag submitted for challenge '{challenge_id}' by user '{user_id}'. Submitted: '{submitted_flag}'")
            return False

# Example Usage (conceptual)
if __name__ == "__main__":
    # Create dummy managers for conceptual calls
    class DummyResourceManager:
        def provision(self, instance_id, resources, script): print(f"DummyRM: Provisioning {resources} for {instance_id}"); return {"status": "success", "outputs": {"ip_address": "10.0.0.1", "port": 1337}}
        def deprovision(self, instance_id): print(f"DummyRM: Deprovisioning {instance_id}"); return True
    class DummyScenarioManager:
        def notify_solve(self, user, chal_id, points): print(f"DummySM: User {user} solved {chal_id} for {points} pts!")

    print("\n--- CTF Challenge Manager Example ---")
    resource_mgr = DummyResourceManager()
    scenario_mgr = DummyScenarioManager() # type: ignore
    ctf_manager = CTFChallengeManager(resource_manager=resource_mgr, scenario_manager=scenario_mgr)

    # List challenges
    print("\nAvailable Challenges:")
    challenges = ctf_manager.list_challenges()
    for chal_summary in challenges:
        print(f"- ID: {chal_summary['id']}, Name: {chal_summary['name']}, Points: {chal_summary['points']}, Status: {chal_summary['status']}")

    # Get details for one challenge
    chal_id_to_test = challenges[0]['id'] if challenges else None # Get first challenge ID
    if chal_id_to_test:
        print(f"\nDetails for Challenge {chal_id_to_test}:")
        details = ctf_manager.get_challenge_details(chal_id_to_test)
        if details: print(details)

        # Start the challenge
        print(f"\nStarting Challenge {chal_id_to_test}...")
        conn_info = ctf_manager.start_challenge(chal_id_to_test)
        print(f"Connection Info: {conn_info}")
        print(f"Challenge Status: {ctf_manager.get_challenge_details(chal_id_to_test).current_status}") # type: ignore

        # Submit an incorrect flag
        print(f"\nSubmitting incorrect flag for {chal_id_to_test}...")
        result = ctf_manager.submit_flag(chal_id_to_test, "flag{wrong_flag_guess}", user_id="test_user")
        print(f"Submission Correct: {result}")

        # Submit the correct flag (using the placeholder retrieval)
        print(f"\nSubmitting correct flag for {chal_id_to_test}...")
        correct_placeholder = ctf_manager._get_correct_flag(chal_id_to_test) or "FLAG_NOT_FOUND"
        # Make it slightly different case for test
        submission_attempt = correct_placeholder.upper() if correct_placeholder else "INVALID"
        result = ctf_manager.submit_flag(chal_id_to_test, submission_attempt, user_id="test_user")
        print(f"Submission Correct: {result}")

        # Stop the challenge
        print(f"\nStopping Challenge {chal_id_to_test}...")
        stop_ok = ctf_manager.stop_challenge(chal_id_to_test)
        print(f"Stop successful: {stop_ok}")
        print(f"Challenge Status: {ctf_manager.get_challenge_details(chal_id_to_test).current_status}") # type: ignore


    print("\n--- End Example ---")
