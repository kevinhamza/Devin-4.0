# Devin/cyber_range/scenario_manager.py
# Purpose: Manages the overall state and progression of cyber range scenarios.

import os
import json
import uuid
import datetime
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, TypedDict
from dataclasses import dataclass, field, asdict

# Conceptual imports for dependencies
# from .resource_manager import ResourceManager # Manages VMs, containers
# from .capture_the_flag.ctf_challenge_manager import CTFChallengeManager # To link flags/events

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Enums and Data Structures ---

class ScenarioStatus(str, Enum):
    NOT_STARTED = "Not Started" # Definition loaded, but no instance running
    INITIALIZING = "Initializing" # Instance created, resources being provisioned
    RUNNING = "Running" # Resources provisioned, scenario active
    PAUSED = "Paused" # Resources suspended (conceptual)
    COMPLETED = "Completed" # Objectives met successfully
    FAILED = "Failed" # Objectives not met or critical error
    STOPPING = "Stopping" # Resources being deprovisioned
    STOPPED = "Stopped" # Instance stopped, resources cleaned up
    ERROR = "Error" # Unrecoverable error state

@dataclass
class ScenarioDefinition:
    """Defines the static properties of a cyber range scenario."""
    id: str
    name: str
    description: str
    objectives: List[str]
    estimated_duration_min: int
    difficulty: Literal['Beginner', 'Intermediate', 'Advanced', 'Expert']
    # List of resource identifiers needed (VM templates, container images, network names)
    required_resources: List[str] = field(default_factory=list)
    # Definition of stages or trigger points (conceptual)
    stages: Optional[List[Dict[str, Any]]] = None # e.g., {'name': 'Stage 1', 'trigger': 'flag:CTF-WEB101'}
    # Path to setup script (conceptual)
    setup_script: Optional[str] = None

@dataclass
class ScenarioInstance:
    """Represents a running or completed instance of a scenario."""
    instance_id: str
    scenario_id: str # Links back to ScenarioDefinition
    user_id: str # User who started this instance
    start_time_utc: str
    end_time_utc: Optional[str] = None
    status: ScenarioStatus = ScenarioStatus.INITIALIZING
    current_stage: Optional[str] = None # Name of the current stage from definition
    # Stores dynamic data like provisioned resource details (IPs, URLs), state variables
    instance_data: Dict[str, Any] = field(default_factory=dict)

# --- Scenario Manager ---

class ScenarioManager:
    """
    Manages the definition, lifecycle, and state of cyber range scenarios.
    Interacts with ResourceManager to handle underlying infrastructure.
    """
    DEFAULT_DEFINITIONS_PATH = "./cyber_range/scenarios/" # Directory containing scenario JSON/YAML files
    DEFAULT_INSTANCE_STATE_PATH = "./data/cyber_range_instances.json" # File to persist instance states

    def __init__(self,
                 resource_manager: Optional[Any] = None, # ResourceManager instance
                 ctf_challenge_manager: Optional[Any] = None, # CTFChallengeManager instance
                 definitions_path: Optional[str] = None,
                 instance_state_path: Optional[str] = None):
        """
        Initializes the ScenarioManager.

        Args:
            resource_manager: Instance of the ResourceManager (conceptual).
            ctf_challenge_manager: Instance of CTFChallengeManager (conceptual).
            definitions_path (Optional[str]): Path to scenario definition files/directory.
            instance_state_path (Optional[str]): Path to file for persisting instance state.
        """
        self.resource_manager = resource_manager
        self.ctf_challenge_manager = ctf_challenge_manager
        self.definitions_path = definitions_path or self.DEFAULT_DEFINITIONS_PATH
        self.instance_state_path = instance_state_path or self.DEFAULT_INSTANCE_STATE_PATH

        # Stores loaded scenario definitions: {scenario_id: ScenarioDefinition}
        self.scenario_definitions: Dict[str, ScenarioDefinition] = {}
        # Stores active or recently stopped scenario instances: {instance_id: ScenarioInstance}
        self.active_instances: Dict[str, ScenarioInstance] = {}

        self._load_scenario_definitions()
        self._load_instance_state()
        logger.info(f"ScenarioManager initialized. Loaded {len(self.scenario_definitions)} definitions. Tracking {len(self.active_instances)} instances.")

    def _load_scenario_definitions(self):
        """Loads scenario definitions from the specified path (conceptual)."""
        logger.info(f"Loading scenario definitions from '{self.definitions_path}'...")
        # In reality: Scan directory for .json/.yaml files, parse them, validate,
        # and create ScenarioDefinition objects.
        # For skeleton: Add a few dummy definitions.
        dummy_defs = [
            ScenarioDefinition(id="basic_web_pentest", name="Basic Web Pentest", description="Scan and exploit a simple vulnerable web app.", objectives=["Find flag in /flag.txt", "Gain root access"], estimated_duration_min=60, difficulty='Beginner', required_resources=["vuln_webapp_container", "kali_tools_container"], setup_script="setup_basic_web.sh"),
            ScenarioDefinition(id="ad_compromise", name="Active Directory Compromise", description="Enumerate and compromise a small Active Directory lab.", objectives=["Obtain Domain Admin hash", "Retrieve domain_secrets.txt"], estimated_duration_min=180, difficulty='Intermediate', required_resources=["ad_dc_vm", "ad_client_win10_vm", "kali_tools_vm", "ad_network"], stages=[{'name': 'Initial Access', 'trigger': 'flag:CTF-AD-USER'}, {'name': 'Privilege Escalation', 'trigger': 'flag:CTF-AD-ADMIN'}]),
        ]
        for definition in dummy_defs:
            self.scenario_definitions[definition.id] = definition
        logger.info(f"Loaded {len(self.scenario_definitions)} dummy scenario definitions.")
        # Add error handling for file parsing/validation

    def _load_instance_state(self):
        """Loads active/recent scenario instance states from the JSON file."""
        if not os.path.exists(self.instance_state_path):
            logger.info(f"Instance state file '{self.instance_state_path}' not found. Starting fresh.")
            self.active_instances = {}
            return
        try:
            with open(self.instance_state_path, 'r') as f:
                raw_data = json.load(f)
                # Deserialize back into ScenarioInstance objects
                self.active_instances = {iid: ScenarioInstance(**idata) for iid, idata in raw_data.items()}
            logger.info(f"Loaded state for {len(self.active_instances)} scenario instances from '{self.instance_state_path}'.")
            # Optional: Perform cleanup/validation of loaded states (e.g., check for stale 'STARTING' states)
        except (IOError, json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to load or parse instance state from '{self.instance_state_path}': {e}. Resetting instance state.")
            self.active_instances = {}

    def _save_instance_state(self):
        """Saves the current state of active instances to the JSON file."""
        # Needs proper locking mechanism if accessed concurrently. DB is better.
        try:
            os.makedirs(os.path.dirname(self.instance_state_path), exist_ok=True)
            data_to_save = {iid: asdict(instance) for iid, instance in self.active_instances.items()}
            with open(self.instance_state_path, 'w') as f:
                json.dump(data_to_save, f, indent=2)
            # logger.debug(f"Saved state for {len(self.active_instances)} instances.")
        except IOError as e:
            logger.error(f"Failed to save instance state to '{self.instance_state_path}': {e}")

    def list_available_scenarios(self) -> List[Dict[str, Any]]:
        """Returns a list of summary information for all defined scenarios."""
        logger.info("Listing available scenarios...")
        summary_list = []
        for definition in self.scenario_definitions.values():
            summary_list.append({
                "id": definition.id,
                "name": definition.name,
                "description": definition.description,
                "difficulty": definition.difficulty,
                "estimated_duration_min": definition.estimated_duration_min,
            })
        return summary_list

    def get_scenario_details(self, scenario_id: str) -> Optional[ScenarioDefinition]:
        """Gets the full definition of a specific scenario."""
        definition = self.scenario_definitions.get(scenario_id)
        if not definition:
            logger.warning(f"Scenario definition ID '{scenario_id}' not found.")
        return definition

    def start_scenario(self, scenario_id: str, user_id: str) -> Optional[ScenarioInstance]:
        """
        Starts a new instance of a specific scenario for a user.

        Args:
            scenario_id (str): The ID of the scenario definition to start.
            user_id (str): The ID of the user starting the scenario.

        Returns:
            Optional[ScenarioInstance]: The created instance object if successful, else None.
        """
        definition = self.get_scenario_details(scenario_id)
        if not definition:
            return None

        logger.info(f"User '{user_id}' attempting to start scenario '{definition.name}' ({scenario_id})...")

        # --- Check Dependencies ---
        if not self.resource_manager:
            logger.error(f"Cannot start scenario '{scenario_id}': ResourceManager is not available.")
            return None

        # --- Create Instance Record ---
        instance_id = f"SCN-INST-{uuid.uuid4().hex[:12].upper()}"
        start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        instance = ScenarioInstance(
            instance_id=instance_id,
            scenario_id=scenario_id,
            user_id=user_id,
            start_time_utc=start_time,
            status=ScenarioStatus.INITIALIZING,
            current_stage=definition.stages[0]['name'] if definition.stages else None
        )
        self.active_instances[instance_id] = instance
        self._save_instance_state()
        logger.info(f"Created scenario instance '{instance_id}'. Status: {instance.status}")

        # --- Provision Resources (Conceptual Call) ---
        try:
            logger.info(f"Instance '{instance_id}': Requesting resources: {definition.required_resources}")
            # result = self.resource_manager.provision(
            #     instance_id=instance_id,
            #     resource_identifiers=definition.required_resources,
            #     setup_script=definition.setup_script,
            #     context={'scenario_name': definition.name, 'user_id': user_id}
            # )
            # Simulate success
            result = {"status": "success", "outputs": {"kali_vm_ip": "10.20.30.5", "vuln_webapp_url": "http://10.20.30.6:80"}}
            logger.info(f"Instance '{instance_id}': Resource Manager result: {result}")

            if result and result.get("status") == "success":
                instance.instance_data = result.get("outputs", {})
                instance.status = ScenarioStatus.RUNNING
                self._save_instance_state()
                logger.info(f"Scenario instance '{instance_id}' started successfully. Status: {instance.status}")
                return instance
            else:
                raise RuntimeError(f"Resource provisioning failed: {result.get('message', 'Unknown RM error')}")

        except Exception as e:
            logger.error(f"Failed during startup of scenario instance '{instance_id}': {e}")
            instance.status = ScenarioStatus.FAILED # Or ERROR
            instance.end_time_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
            instance.instance_data['error_message'] = str(e)
            # Attempt cleanup? This can be complex.
            # self.stop_scenario_instance(instance_id, force_cleanup=True) # Avoid recursion
            logger.info(f"Attempting cleanup for failed instance '{instance_id}'...")
            if self.resource_manager:
                 # self.resource_manager.deprovision(instance_id) # Best effort cleanup
                 logger.info(f"  - Conceptual: Called resource_manager.deprovision({instance_id})")
            self._save_instance_state()
            return None


    def get_scenario_instance_status(self, instance_id: str) -> Optional[ScenarioInstance]:
        """Gets the current state and details of a specific scenario instance."""
        instance = self.active_instances.get(instance_id)
        if not instance:
            logger.warning(f"Scenario instance ID '{instance_id}' not found.")
            # Optional: Check historical/archived instances?
        return instance

    def stop_scenario_instance(self, instance_id: str) -> bool:
        """
        Stops a running scenario instance and cleans up its resources.

        Args:
            instance_id (str): The ID of the scenario instance to stop.

        Returns:
            bool: True if stopping process initiated successfully, False otherwise.
                  Note: Resource cleanup happens asynchronously potentially.
        """
        instance = self.get_scenario_instance_status(instance_id)
        if not instance:
            return False # Already stopped or doesn't exist

        if instance.status in [ScenarioStatus.STOPPING, ScenarioStatus.STOPPED, ScenarioStatus.COMPLETED, ScenarioStatus.FAILED]:
            logger.warning(f"Scenario instance '{instance_id}' is already stopped or in a final state ({instance.status}).")
            return True # Considered success if already stopped/completed

        logger.info(f"Attempting to stop scenario instance '{instance_id}'...")
        instance.status = ScenarioStatus.STOPPING
        instance.end_time_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._save_instance_state() # Mark as stopping immediately

        # --- Deprovision Resources (Conceptual Call) ---
        success = False
        if self.resource_manager:
            try:
                logger.info(f"Instance '{instance_id}': Requesting deprovisioning...")
                # deprovision_ok = self.resource_manager.deprovision(instance_id=instance_id)
                deprovision_ok = True # Simulate success
                if deprovision_ok:
                    logger.info(f"Instance '{instance_id}': Resource deprovisioning successful.")
                    success = True
                else:
                    logger.error(f"Instance '{instance_id}': Resource deprovisioning failed.")
            except Exception as e:
                logger.error(f"Error during deprovisioning for instance '{instance_id}': {e}")
                # Instance might be left in ERROR state, requires manual cleanup?
                instance.status = ScenarioStatus.ERROR
                instance.instance_data['error_message'] = f"Deprovisioning failed: {e}"
                self._save_instance_state()
                return False # Indicate failure
        else:
            logger.warning(f"Cannot deprovision resources for instance '{instance_id}': ResourceManager not available.")
            # If no resources, consider stopping successful immediately.
            success = True # No resources to clean up

        # Update final state
        # Determine if COMPLETED or just STOPPED based on objectives/events? Requires more logic.
        # Defaulting to STOPPED for now.
        instance.status = ScenarioStatus.STOPPED
        logger.info(f"Scenario instance '{instance_id}' marked as {instance.status}.")
        # Optional: Move to an archive instead of just updating active_instances?
        # For now, just save the final state.
        self._save_instance_state()
        return success

    def record_event(self, instance_id: str, event_type: str, event_data: Dict[str, Any]):
        """
        Records an event relevant to a scenario instance (e.g., flag captured).
        This can trigger state changes or progress checks.
        """
        instance = self.get_scenario_instance_status(instance_id)
        if not instance or instance.status != ScenarioStatus.RUNNING:
             logger.warning(f"Received event '{event_type}' for non-running/non-existent instance '{instance_id}'. Ignoring.")
             return

        logger.info(f"Received event '{event_type}' for instance '{instance_id}': {event_data}")
        instance.instance_data.setdefault('events', []).append(
            {'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'type': event_type, 'data': event_data}
        )

        # --- Placeholder: Scenario Progression Logic ---
        # Check if this event triggers a stage change or completion based on definition.stages
        # definition = self.get_scenario_details(instance.scenario_id)
        # if definition and definition.stages:
        #     next_stage = check_triggers(instance, definition.stages, event_type, event_data)
        #     if next_stage: instance.current_stage = next_stage
        #     if check_completion(instance, definition.objectives, definition.stages):
        #          instance.status = ScenarioStatus.COMPLETED
        #          # Maybe trigger stop?
        # --- End Placeholder ---

        self._save_instance_state() # Save event log and potential status changes


# Example Usage (conceptual)
if __name__ == "__main__":
    # Create dummy managers for conceptual calls
    class DummyResourceManager:
        def provision(self, instance_id, resource_identifiers, setup_script, context): print(f"DummyRM: Provisioning {resource_identifiers} for {instance_id}"); return {"status": "success", "outputs": {"vm_ip": "10.0.0.10", "url": "http://10.0.0.10"}}
        def deprovision(self, instance_id): print(f"DummyRM: Deprovisioning {instance_id}"); return True
    class DummyCTFManager:
        def check_challenge_status(self, chal_id): return ChallengeStatus.RUNNING # Dummy

    print("\n--- Scenario Manager Example ---")
    # Use temporary files
    temp_defs_path = "./temp_scenario_defs/" # Directory for scenario definitions
    temp_instance_path = "./temp_scenario_instances.json"
    if os.path.exists(temp_defs_path): shutil.rmtree(temp_defs_path)
    if os.path.exists(temp_instance_path): os.remove(temp_instance_path)
    os.makedirs(temp_defs_path, exist_ok=True)
    # Create dummy definition file (in reality, manager loads existing)
    with open(os.path.join(temp_defs_path, "basic_web_pentest.json"), 'w') as f: json.dump(asdict(ScenarioDefinition(id="basic_web_pentest", name="Basic Web Pentest", description="...", objectives=["..."], estimated_duration_min=60, difficulty='Beginner', required_resources=["vm1"])), f)

    resource_mgr = DummyResourceManager()
    ctf_mgr = DummyCTFManager() # type: ignore

    manager = ScenarioManager(
        resource_manager=resource_mgr,
        ctf_challenge_manager=ctf_mgr, # type: ignore
        definitions_path=temp_defs_path, # Point to dummy defs
        instance_state_path=temp_instance_path
    )

    # List available scenarios
    print("\nAvailable Scenarios:")
    scenarios = manager.list_available_scenarios()
    for s in scenarios: print(f"- {s['name']} ({s['id']})")

    # Start a scenario instance
    if scenarios:
        scenario_id_to_start = scenarios[0]['id']
        print(f"\nStarting scenario instance for '{scenario_id_to_start}' by user 'test_user'...")
        instance = manager.start_scenario(scenario_id_to_start, user_id="test_user")

        if instance:
            instance_id = instance.instance_id
            print(f"Instance '{instance_id}' started. Status: {instance.status}")
            print(f"Instance Data (Connection Info): {instance.instance_data}")

            # Get instance status
            print(f"\nGetting status for instance '{instance_id}'...")
            status_instance = manager.get_scenario_instance_status(instance_id)
            if status_instance: print(f"Status: {status_instance.status}, Started: {status_instance.start_time_utc}")

            # Record a conceptual event
            print(f"\nRecording event for instance '{instance_id}'...")
            manager.record_event(instance_id, "flag_captured", {"challenge_id": "CTF-WEB101", "points": 50})
            updated_instance = manager.get_scenario_instance_status(instance_id)
            if updated_instance: print(f"Instance events: {updated_instance.instance_data.get('events')}")


            # Stop the instance
            print(f"\nStopping instance '{instance_id}'...")
            stop_ok = manager.stop_scenario_instance(instance_id)
            print(f"Stop initiated successfully: {stop_ok}")
            final_status_instance = manager.get_scenario_instance_status(instance_id) # May still be active if state not removed
            if final_status_instance: print(f"Final recorded status: {final_status_instance.status}, End Time: {final_status_instance.end_time_utc}")
            else: print(f"Instance '{instance_id}' removed from active list.")

        else:
            print(f"Failed to start scenario '{scenario_id_to_start}'.")

    # Check persistence
    print("\nReloading manager to check instance persistence...")
    del manager
    manager_reloaded = ScenarioManager(instance_state_path=temp_instance_path)
    print(f"Number of instances loaded after reload: {len(manager_reloaded.active_instances)}")
    # Instance should be marked STOPPED or removed depending on implementation


    # Clean up temp files/dirs
    if os.path.exists(temp_defs_path): shutil.rmtree(temp_defs_path)
    if os.path.exists(temp_instance_path): os.remove(temp_instance_path)


    print("\n--- End Example ---")
