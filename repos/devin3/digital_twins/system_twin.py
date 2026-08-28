# Devin/digital_twins/system_twin.py
# Purpose: Represents a digital twin of a system or infrastructure component.

import logging
import datetime
import random
from typing import Dict, List, Optional, Any, Literal

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("SystemDigitalTwin")

# --- Data Structures (Examples) ---
# These could be more detailed using dataclasses or Pydantic if needed

SystemState = Dict[str, Any] # Holds dynamic state like CPU load, service status etc.
SystemConfiguration = Dict[str, Any] # Holds static config like OS, hardware, installed software

class SystemDigitalTwin:
    """
    Represents a virtual replica (Digital Twin) of a system.

    Stores static configuration and dynamic state information.
    Can be used for simulation, analysis, or providing context to AI agents.
    The fidelity of the twin depends on the detail in the initial configuration
    and the sophistication of state update logic.
    """

    def __init__(self, twin_id: str, initial_config: SystemConfiguration):
        """
        Initializes the System Digital Twin.

        Args:
            twin_id (str): A unique identifier for this digital twin instance.
            initial_config (SystemConfiguration): A dictionary containing the static
                                                  configuration of the system being twinned.
        """
        if not twin_id or not initial_config:
            raise ValueError("twin_id and initial_config are required.")

        self.twin_id: str = twin_id
        self.configuration: SystemConfiguration = initial_config # Static properties
        self.current_state: SystemState = {} # Dynamic properties
        self.last_state_update_utc: Optional[str] = None
        self.creation_time_utc: str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        logger.info(f"Initializing SystemDigitalTwin '{self.twin_id}' (Type: {self.configuration.get('type', 'Unknown')})...")
        self._initialize_state()
        logger.info(f"SystemDigitalTwin '{self.twin_id}' initialized.")

    def _initialize_state(self):
        """Sets the initial dynamic state based on configuration."""
        logger.debug(f"[{self.twin_id}] Initializing dynamic state...")
        self.current_state = {
            "status": "running", # Default initial status
            "cpu_load_percent": round(random.uniform(1.0, 10.0), 2), # Initial low load
            "memory_usage_percent": round(random.uniform(5.0, 25.0), 2),
            "disk_usage_percent": round(random.uniform(10.0, 60.0), 2),
            "running_services": self.configuration.get("default_services", []), # Services running by default
            "network_connections_active": random.randint(5, 50),
            "security_posture": "baseline", # e.g., baseline, compromised_user, compromised_root
            "pending_updates": 0,
            # Add other relevant dynamic state variables
        }
        self.last_state_update_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        logger.debug(f"[{self.twin_id}] Initial state: {self.current_state}")

    def get_configuration(self, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Retrieves static configuration data.

        Args:
            key (Optional[str]): The specific configuration key to retrieve.
                                 If None, returns the entire configuration dictionary.
            default (Any): Default value to return if the key is not found.

        Returns:
            Any: The requested configuration value or the entire configuration dict.
        """
        if key:
            return self.configuration.get(key, default)
        else:
            return self.configuration.copy() # Return a copy

    def get_state(self, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Retrieves dynamic state data.

        Args:
            key (Optional[str]): The specific state key to retrieve.
                                 If None, returns the entire state dictionary.
            default (Any): Default value to return if the key is not found.

        Returns:
            Any: The requested state value or the entire state dict.
        """
        if key:
            return self.current_state.get(key, default)
        else:
            return self.current_state.copy() # Return a copy

    def update_state(self, state_changes: Dict[str, Any]):
        """
        Updates the dynamic state of the digital twin with new values.

        Args:
            state_changes (Dict[str, Any]): A dictionary of state keys and their new values to update.
        """
        if not isinstance(state_changes, dict):
             logger.error(f"[{self.twin_id}] Invalid state update format. Expected dict, got {type(state_changes)}.")
             return

        logger.info(f"[{self.twin_id}] Updating state with changes: {state_changes}")
        updated = False
        for key, value in state_changes.items():
             if key in self.current_state:
                 if self.current_state[key] != value:
                      self.current_state[key] = value
                      updated = True
             else:
                  # Allow adding new state variables if needed? Or restrict to initialized keys? Allowing for now.
                  logger.debug(f"[{self.twin_id}] Adding new state key '{key}'.")
                  self.current_state[key] = value
                  updated = True

        if updated:
             self.last_state_update_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
             logger.debug(f"[{self.twin_id}] State updated. New state keys: {list(self.current_state.keys())}")
        else:
             logger.debug(f"[{self.twin_id}] No state changes applied.")

    def check_vulnerability(self, cve_id: str) -> bool:
        """Checks if a specific CVE is listed in the twin's configuration."""
        vulns = self.configuration.get("vulnerabilities", [])
        is_vulnerable = cve_id in vulns
        logger.debug(f"[{self.twin_id}] Checking vulnerability {cve_id}: {'Present' if is_vulnerable else 'Not Present'}")
        return is_vulnerable

    # --- Conceptual Simulation Methods ---
    # These methods would contain more complex logic in a real simulation engine

    def simulate_time_passing(self, seconds: float):
        """Simulates the effect of time passing on the system's state (e.g., load changes)."""
        logger.debug(f"[{self.twin_id}] Simulating {seconds} seconds passing...")
        # Example: Randomly fluctuate load slightly over time
        load_change = random.uniform(-0.5, 0.5) * (seconds / 10) # Small change based on time passed
        mem_change = random.uniform(-1.0, 1.0) * (seconds / 10)
        new_load = max(0.1, min(100.0, self.current_state.get("cpu_load_percent", 5.0) + load_change))
        new_mem = max(1.0, min(100.0, self.current_state.get("memory_usage_percent", 10.0) + mem_change))
        self.update_state({
            "cpu_load_percent": round(new_load, 2),
            "memory_usage_percent": round(new_mem, 2),
            })

    def simulate_event(self, event_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates the occurrence of an internal or external event affecting the twin.
        *** Placeholder Implementation ***
        """
        logger.info(f"[{self.twin_id}] Simulating event: Type='{event_type}', Params='{params}'")
        state_changes = {}
        result_message = f"Event '{event_type}' processed conceptually."

        # --- Add simple rule-based state changes based on event type ---
        if event_type == "HIGH_LOAD_REQUEST":
            state_changes["cpu_load_percent"] = round(min(100.0, self.get_state("cpu_load_percent", 10.0) + random.uniform(10, 30)), 2)
            state_changes["network_connections_active"] = self.get_state("network_connections_active", 20) + random.randint(10, 50)
            result_message = "Simulated high load applied."
        elif event_type == "PATCH_APPLIED":
            state_changes["pending_updates"] = max(0, self.get_state("pending_updates", 1) - 1)
            cve_fixed = params.get("cve_id")
            if cve_fixed:
                # Conceptually remove vulnerability from config (though config is static ideally)
                # More realistically, update a 'patched_vulnerabilities' list in the state
                state_changes.setdefault("patched_cves", []).append(cve_fixed)
                result_message = f"Simulated patch applied for {cve_fixed}."
            else:
                 result_message = "Simulated generic patch applied."
        elif event_type == "SERVICE_CRASH":
             service_name = params.get("service_name")
             if service_name:
                  running = self.current_state.setdefault("running_services", [])
                  if service_name in running: running.remove(service_name)
                  state_changes["running_services"] = running
                  state_changes["status"] = "degraded" # Example status change
                  result_message = f"Simulated crash of service '{service_name}'."
             else: result_message = "Service crash event ignored (no service name)."
        # --- End simple rules ---

        if state_changes:
             self.update_state(state_changes)

        return {"status": "processed", "message": result_message, "state_changes_applied": state_changes}


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- System Digital Twin Example (Conceptual) ---")

    # Example configuration for a web server twin
    web_server_config: SystemConfiguration = {
        "twin_id": "webserver-prod-01",
        "type": "web_server",
        "os": "Ubuntu 22.04 LTS",
        "cpu_cores": 4,
        "memory_gb": 16,
        "disk_gb": 100,
        "ip_address": "10.1.2.3",
        "network_config": {"open_ports": [80, 443, 22]},
        "installed_software": [
            {"name": "nginx", "version": "1.18.0"},
            {"name": "python", "version": "3.10"},
            {"name": "openssh-server", "version": "8.9p1"}
        ],
        "default_services": ["nginx", "ssh"],
        "vulnerabilities": ["CVE-2021-XXXX", "CVE-2022-YYYY"], # Example known vulns
    }

    # Create the twin
    twin = SystemDigitalTwin(twin_id="webserver-prod-01", initial_config=web_server_config)

    # Get some info
    print(f"\nTwin OS: {twin.get_configuration('os')}")
    print(f"Twin Initial Status: {twin.get_state('status')}")
    print(f"Twin Initial CPU Load: {twin.get_state('cpu_load_percent')}%")
    print(f"Is twin vulnerable to CVE-2021-XXXX? {twin.check_vulnerability('CVE-2021-XXXX')}")
    print(f"Is twin vulnerable to CVE-2023-ZZZZ? {twin.check_vulnerability('CVE-2023-ZZZZ')}")

    # Simulate time passing and events
    print("\nSimulating time and events...")
    twin.simulate_time_passing(seconds=30)
    print(f"CPU load after 30s sim: {twin.get_state('cpu_load_percent')}%")

    event_result = twin.simulate_event("HIGH_LOAD_REQUEST", params={})
    print(f"Event Result: {event_result.get('message')}")
    print(f"CPU load after high load event: {twin.get_state('cpu_load_percent')}%")

    patch_result = twin.simulate_event("PATCH_APPLIED", params={"cve_id": "CVE-2021-XXXX"})
    print(f"Event Result: {patch_result.get('message')}")
    print(f"Patched CVEs in state: {twin.get_state('patched_cves')}")

    crash_result = twin.simulate_event("SERVICE_CRASH", params={"service_name": "nginx"})
    print(f"Event Result: {crash_result.get('message')}")
    print(f"Running services after crash: {twin.get_state('running_services')}")
    print(f"Twin Status after crash: {twin.get_state('status')}")

    print("\nFinal Twin State:")
    print(json.dumps(twin.get_state(), indent=2))


    print("\n--- End Example ---")
