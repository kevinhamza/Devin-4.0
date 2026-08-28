# Devin/cyber_range/blue_team/soc_playbooks.py
# Purpose: Defines and manages defensive Security Operations Center (SOC) playbooks/workflows.

import os
import json
import uuid
import datetime
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, TypedDict, Literal
from dataclasses import dataclass, field, asdict

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("SOCPlaybookManager")

# --- Enums and Data Structures ---

class PlaybookSeverity(str, Enum):
    INFO = "Informational"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class PlaybookActionType(str, Enum):
    # Data Gathering / Enrichment
    LOG_QUERY = "log_query" # Query SIEM or log sources
    ENDPOINT_QUERY = "endpoint_query" # Query EDR for process list, connections etc.
    THREAT_INTEL_LOOKUP = "threat_intel_lookup" # Check IP/hash/domain against TI feeds
    USER_INFO_LOOKUP = "user_info_lookup" # Get info about involved user from directory/HR system
    # Analysis
    AI_ANALYZE_LOGS = "ai_analyze_logs" # Send logs to an AI for summary/anomaly detection
    AI_ANALYZE_ARTIFACT = "ai_analyze_artifact" # Send file hash/URL to AI/Sandbox
    MANUAL_ANALYSIS_TASK = "manual_analysis_task" # Create task for human analyst
    # Response / Containment Actions (USE WITH EXTREME CAUTION)
    ISOLATE_HOST = "isolate_host" # Network isolation via EDR/Firewall
    DISABLE_USER_ACCOUNT = "disable_user_account" # Disable account in AD/IDP
    BLOCK_IP_HASH = "block_ip_hash" # Add indicator to blocklists (Firewall, Proxy, EDR)
    RESET_PASSWORD = "reset_password" # Trigger password reset for user
    DELETE_EMAIL = "delete_email" # For phishing response, via email gateway API
    # Notification / Reporting
    NOTIFY_TEAM = "notify_team" # Send alert to Slack/Teams/Email
    CREATE_TICKET = "create_ticket" # Create incident ticket in ITSM/SOAR
    GENERATE_REPORT = "generate_report" # Compile findings into a report

class PlaybookExecutionStatus(str, Enum):
    PENDING = "Pending" # Triggered, not yet started
    RUNNING = "Running"
    PAUSED_FOR_INPUT = "Paused - Awaiting Input"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"

@dataclass
class PlaybookStep:
    """Represents a single step within a playbook."""
    id: str # Unique identifier within the playbook (e.g., "step_1", "isolate_if_confirmed")
    name: str # User-friendly name for the step
    description: Optional[str] = None
    action_type: PlaybookActionType
    # Parameters specific to the action_type
    # e.g., for LOG_QUERY: {'query': '...', 'timeframe': '...'}
    # e.g., for ISOLATE_HOST: {'hostname_or_ip': '...'}
    action_params: Dict[str, Any] = field(default_factory=dict)
    # IDs of the next step(s) based on outcome
    # Can be simple (just one next step) or conditional ({'if_malicious': 'isolate', 'if_benign': 'close'})
    # Using simple success/failure for this skeleton
    on_success_next_step_id: Optional[str] = None
    on_failure_next_step_id: Optional[str] = None # Go here if action fails or condition not met
    # If both are None, this is potentially an end state for a branch.

@dataclass
class PlaybookDefinition:
    """Defines the static structure of a playbook."""
    id: str # Unique playbook identifier (e.g., "phishing_triage_v1", "malware_containment_v2")
    name: str # User-friendly name
    description: str
    severity: PlaybookSeverity # Typical severity this playbook addresses
    # Conditions that trigger this playbook (conceptual - simple keywords for now)
    trigger_conditions: List[str] # e.g., ["alert:PhishingEmailDetected", "severity:high", "source:EmailGateway"]
    # Steps defined, keyed by step ID for easy lookup and branching
    steps: Dict[str, PlaybookStep] = field(default_factory=dict)
    start_step_id: Optional[str] = None # ID of the first step to execute

@dataclass
class PlaybookExecutionInstance:
    """Tracks the runtime state of a specific playbook execution."""
    instance_id: str = field(default_factory=lambda: f"PB-EXEC-{uuid.uuid4().hex[:12].upper()}")
    playbook_id: str
    playbook_name: str # Denormalized for easier display
    triggering_event: Dict[str, Any] # The alert or data that triggered this playbook
    start_time_utc: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    end_time_utc: Optional[str] = None
    status: PlaybookExecutionStatus = PlaybookExecutionStatus.PENDING
    current_step_id: Optional[str] = None
    step_results: List[Dict[str, Any]] = field(default_factory=list) # Log of step executions and outcomes
    context: Dict[str, Any] = field(default_factory=dict) # Runtime data shared between steps
    error_message: Optional[str] = None


# --- Playbook Manager ---

class SOCPlaybookManager:
    """
    Manages the definition, loading, triggering, and conceptual execution of SOC playbooks.

    Interacts conceptually with logging systems, security tools, and notification services.
    """
    DEFAULT_DEFINITIONS_PATH = "./cyber_range/blue_team/playbooks/" # Dir containing playbook JSON/YAML files
    DEFAULT_INSTANCE_STATE_PATH = "./data/soc_playbook_executions.json"

    def __init__(self,
                 definitions_path: Optional[str] = None,
                 instance_state_path: Optional[str] = None,
                 action_executor: Optional[Any] = None): # Dependency for executing actions
        """
        Initializes the SOCPlaybookManager.

        Args:
            definitions_path (Optional[str]): Path to playbook definition files/directory.
            instance_state_path (Optional[str]): Path to file for persisting execution state.
            action_executor (Optional[Any]): Conceptual object/service responsible for
                                             executing the actions defined in playbook steps
                                             (e.g., running log queries, calling EDR APIs).
        """
        self.definitions_path = definitions_path or self.DEFAULT_DEFINITIONS_PATH
        self.instance_state_path = instance_state_path or self.DEFAULT_INSTANCE_STATE_PATH
        self.action_executor = action_executor # Store dependency

        # Stores loaded playbook definitions: {playbook_id: PlaybookDefinition}
        self.playbook_definitions: Dict[str, PlaybookDefinition] = {}
        # Stores active or recent playbook executions: {instance_id: PlaybookExecutionInstance}
        self.active_executions: Dict[str, PlaybookExecutionInstance] = {}

        self._load_playbook_definitions()
        self._load_execution_state()
        logger.info(f"SOCPlaybookManager initialized. Loaded {len(self.playbook_definitions)} definitions. Tracking {len(self.active_executions)} executions.")

        if not self.action_executor:
             logger.warning("Action Executor not provided. Playbook execution steps will only be logged conceptually.")

    def _load_playbook_definitions(self):
        """Loads playbook definitions from source (conceptual)."""
        logger.info(f"Loading playbook definitions from '{self.definitions_path}'...")
        # In reality: Scan directory for .json/.yaml files, parse, validate schema, create objects.
        # For skeleton: Add hardcoded examples. Ensure steps are keyed by ID.
        dummy_defs = [
            PlaybookDefinition(
                id="phishing_triage_v1", name="Phishing Email Triage",
                description="Initial analysis and triage of a reported phishing email.",
                severity=PlaybookSeverity.MEDIUM,
                trigger_conditions=["alert:PhishingReported", "source:UserSubmission"],
                start_step_id="step1_get_details",
                steps={
                    "step1_get_details": PlaybookStep(id="step1_get_details", name="Get Email Headers & Body", description="Extract headers, body, attachments from original email.", action_type=PlaybookActionType.DATA_ENRICHMENT, action_params={'source': 'email_gateway', 'query_field': 'message_id', 'output_vars': ['email_headers', 'email_body', 'attachments']}, on_success_next_step_id="step2_analyze_links", on_failure_next_step_id="step_fail"),
                    "step2_analyze_links": PlaybookStep(id="step2_analyze_links", name="Analyze URLs/Attachments", description="Check links/attachment hashes against threat intel.", action_type=PlaybookActionType.THREAT_INTEL_LOOKUP, action_params={'inputs': ['email_body', 'attachments'], 'output_vars': ['suspicious_indicators']}, on_success_next_step_id="step3_notify", on_failure_next_step_id="step_fail"),
                    "step3_notify": PlaybookStep(id="step3_notify", name="Notify SOC Analyst", description="Send findings to analyst for review.", action_type=PlaybookActionType.NOTIFY_TEAM, action_params={'channel': '#soc-alerts', 'summary': 'Phishing triage results ready', 'details_var': 'suspicious_indicators'}, on_success_next_step_id="step_end"),
                    "step_fail": PlaybookStep(id="step_fail", name="Handle Failure", description="Log failure.", action_type=PlaybookActionType.NOTIFY_TEAM, action_params={'channel': '#soc-errors', 'summary': 'Playbook failed'}, on_success_next_step_id="step_end"),
                    "step_end": PlaybookStep(id="step_end", name="End Playbook", description="Final step.", action_type=PlaybookActionType.MANUAL_REVIEW_TASK, action_params={'assignee': 'soc_level_1'}) # End state
                }
            ),
            PlaybookDefinition(
                id="malware_alert_host_isolate_v1", name="Malware Alert - Host Isolation",
                description="Isolate host upon confirmed malware detection alert.",
                severity=PlaybookSeverity.HIGH,
                trigger_conditions=["alert:MalwareConfirmed", "source:EDR"],
                start_step_id="step1_isolate",
                steps={
                    "step1_isolate": PlaybookStep(id="step1_isolate", name="Isolate Host", description="Use EDR/Firewall to isolate the affected host from the network.", action_type=PlaybookActionType.ISOLATE_HOST, action_params={'hostname_var': 'alert_hostname'}, on_success_next_step_id="step2_ticket", on_failure_next_step_id="step_fail_isolate"),
                    "step2_ticket": PlaybookStep(id="step2_ticket", name="Create Incident Ticket", description="Create ticket in ITSM/SOAR.", action_type=PlaybookActionType.CREATE_TICKET, action_params={'severity': 'High', 'summary': 'Malware Detected - Host Isolated', 'details_var': 'alert_details'}, on_success_next_step_id="step_end"),
                    "step_fail_isolate": PlaybookStep(id="step_fail_isolate", name="Isolation Failure Alert", description="Notify team about isolation failure.", action_type=PlaybookActionType.NOTIFY_TEAM, action_params={'channel': '#soc-critical', 'summary': 'HOST ISOLATION FAILED'}, on_success_next_step_id="step_end"),
                    "step_end": PlaybookStep(id="step_end", name="End Playbook", description="Playbook finished.", action_type=PlaybookActionType.MANUAL_REVIEW_TASK, action_params={'assignee': 'soc_level_2_incident_response'})
                }
            ),
            # Add more playbook definitions...
        ]
        for definition in dummy_defs:
            # Validate start_step_id exists
            if definition.start_step_id and definition.start_step_id not in definition.steps:
                 logger.error(f"Playbook '{definition.id}': Start step ID '{definition.start_step_id}' not found in steps definition. Skipping playbook.")
                 continue
            # Basic validation of next step IDs
            valid = True
            for step_id, step in definition.steps.items():
                if step.on_success_next_step_id and step.on_success_next_step_id not in definition.steps:
                    logger.error(f"Playbook '{definition.id}', Step '{step_id}': Success next step ID '{step.on_success_next_step_id}' not found.")
                    valid = False; break
                if step.on_failure_next_step_id and step.on_failure_next_step_id not in definition.steps:
                     logger.error(f"Playbook '{definition.id}', Step '{step_id}': Failure next step ID '{step.on_failure_next_step_id}' not found.")
                     valid = False; break
            if valid:
                 self.playbook_definitions[definition.id] = definition
            else:
                 logger.error(f"Playbook '{definition.id}' has invalid step transitions. Skipping.")

        logger.info(f"Loaded {len(self.playbook_definitions)} valid playbook definitions (Conceptual).")


    def _load_execution_state(self):
        """Loads active/recent playbook execution states from the JSON file."""
        if not os.path.exists(self.instance_state_path):
            logger.info(f"Execution state file '{self.instance_state_path}' not found. Starting fresh.")
            self.active_executions = {}
            return
        try:
            with open(self.instance_state_path, 'r') as f:
                raw_data = json.load(f)
                # Deserialize back into objects (enum conversion needed)
                self.active_executions = {}
                for iid, idata in raw_data.items():
                     idata['status'] = PlaybookExecutionStatus(idata.get('status', 'FAILED')) # Convert string back to Enum
                     self.active_executions[iid] = PlaybookExecutionInstance(**idata)
            logger.info(f"Loaded state for {len(self.active_executions)} playbook executions from '{self.instance_state_path}'.")
        except (IOError, json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error(f"Failed to load or parse execution state from '{self.instance_state_path}': {e}. Resetting state.")
            self.active_executions = {}

    def _save_execution_state(self):
        """Saves the current state of active executions to the JSON file."""
        # Needs proper locking mechanism if accessed concurrently. DB is better.
        try:
            os.makedirs(os.path.dirname(self.instance_state_path), exist_ok=True)
            # Serialize objects to dictionaries for JSON (enum needs conversion)
            data_to_save = {iid: asdict(instance) for iid, instance in self.active_executions.items()}
            # Convert enums to strings within the dict
            for iid in data_to_save:
                if isinstance(data_to_save[iid].get('status'), Enum):
                     data_to_save[iid]['status'] = data_to_save[iid]['status'].value
            with open(self.instance_state_path, 'w') as f:
                json.dump(data_to_save, f, indent=2)
            # logger.debug(f"Saved state for {len(self.active_executions)} executions.")
        except IOError as e:
            logger.error(f"Failed to save execution state to '{self.instance_state_path}': {e}")


    def list_playbooks(self) -> List[Dict[str, Any]]:
        """Returns summary information for all loaded playbook definitions."""
        return [
            {"id": p.id, "name": p.name, "description": p.description, "severity": p.severity.value}
            for p in self.playbook_definitions.values()
        ]

    def get_playbook_definition(self, playbook_id: str) -> Optional[PlaybookDefinition]:
        """Gets the full definition of a specific playbook."""
        pb = self.playbook_definitions.get(playbook_id)
        if not pb: logger.warning(f"Playbook definition ID '{playbook_id}' not found.")
        return pb

    def _check_trigger_conditions(self, alert_data: Dict[str, Any], conditions: List[str]) -> bool:
        """Checks if alert data matches the playbook's trigger conditions (conceptual)."""
        # Simple conceptual check: assumes conditions are strings like "key:value" or just "keyword"
        # A real implementation would need a more robust condition engine (e.g., parsing alert fields).
        if not conditions: # If no conditions, playbook might be manually triggered only
            return False
        match_count = 0
        for condition in conditions:
            condition_lower = condition.lower()
            found_match = False
            # Check simple keywords
            if ":" not in condition_lower:
                for key, value in alert_data.items():
                     if condition_lower in str(value).lower():
                         found_match = True; break
            # Check key:value pairs (basic equality check)
            else:
                 try:
                     key, expected_value = condition_lower.split(":", 1)
                     actual_value = str(alert_data.get(key, "")).lower()
                     if actual_value == expected_value:
                         found_match = True
                 except Exception:
                     logger.warning(f"Could not parse trigger condition: {condition}") # Malformed condition
            if found_match:
                 match_count += 1

        # Trigger if ALL conditions are met (adjust logic if ANY match is desired)
        return match_count == len(conditions)


    def trigger_playbook(self, alert_data: Dict[str, Any]) -> Optional[str]:
        """
        Finds and initiates the execution of a playbook based on trigger conditions in alert data.

        Args:
            alert_data (Dict[str, Any]): The alert details that might trigger a playbook.

        Returns:
            Optional[str]: The instance ID of the started playbook execution, or None if no matching playbook found.
        """
        logger.info(f"Checking for playbook triggers based on alert: {alert_data.get('alert_name', 'Unnamed Alert')}")
        matched_playbook_id = None
        highest_severity = -1 # Find highest severity match

        for pb_id, definition in self.playbook_definitions.items():
            if self._check_trigger_conditions(alert_data, definition.trigger_conditions):
                 severity_map = {PlaybookSeverity.INFO:0, PlaybookSeverity.LOW:1, PlaybookSeverity.MEDIUM:2, PlaybookSeverity.HIGH:3, PlaybookSeverity.CRITICAL:4}
                 current_severity = severity_map.get(definition.severity, -1)
                 logger.info(f"  - Alert matches trigger for playbook '{pb_id}' (Severity: {definition.severity.value})")
                 if current_severity > highest_severity:
                      highest_severity = current_severity
                      matched_playbook_id = pb_id

        if matched_playbook_id:
            logger.info(f"Selected highest severity matching playbook: '{matched_playbook_id}'")
            definition = self.playbook_definitions[matched_playbook_id]
            instance = PlaybookExecutionInstance(
                playbook_id=matched_playbook_id,
                playbook_name=definition.name,
                triggering_event=alert_data,
                status=PlaybookExecutionStatus.PENDING,
                current_step_id=definition.start_step_id,
                context=alert_data.copy() # Initialize context with alert data
            )
            self.active_executions[instance.instance_id] = instance
            self._save_execution_state()
            logger.info(f"Created playbook execution instance: {instance.instance_id}")

            # --- Trigger Execution ---
            # Option 1: Execute immediately (synchronous or background task)
            self.execute_playbook(instance.instance_id)
            # Option 2: Add to a queue for a separate executor process (more robust)
            # self.execution_queue.put(instance.instance_id)

            return instance.instance_id
        else:
            logger.info("No matching playbook found for the given alert data.")
            return None


    def execute_playbook(self, instance_id: str):
        """
        Executes the steps of a triggered playbook instance.
        This could run synchronously, in a background thread, or via a task queue.
        This conceptual version runs synchronously.
        """
        instance = self.active_executions.get(instance_id)
        if not instance:
             logger.error(f"Cannot execute playbook: Instance ID '{instance_id}' not found.")
             return
        if instance.status not in [PlaybookExecutionStatus.PENDING, PlaybookExecutionStatus.RUNNING, PlaybookExecutionStatus.PAUSED_FOR_INPUT]:
             logger.warning(f"Playbook instance '{instance_id}' is not in a runnable state (Status: {instance.status}).")
             return

        logger.info(f"--- Starting/Resuming Playbook Execution: {instance.playbook_name} ({instance_id}) ---")
        instance.status = PlaybookExecutionStatus.RUNNING
        if instance.current_step_id is None: # Should have start_step_id from definition
             playbook_def = self.get_playbook_definition(instance.playbook_id)
             instance.current_step_id = playbook_def.start_step_id if playbook_def else None
             if not instance.current_step_id:
                  instance.status = PlaybookExecutionStatus.FAILED
                  instance.error_message = "Playbook definition invalid or missing start step ID."
                  logger.error(instance.error_message)
                  self._save_execution_state()
                  return

        playbook_def = self.get_playbook_definition(instance.playbook_id)
        if not playbook_def:
            instance.status = PlaybookExecutionStatus.FAILED
            instance.error_message = f"Playbook definition '{instance.playbook_id}' not found during execution."
            logger.error(instance.error_message)
            self._save_execution_state()
            return

        max_steps = 50 # Add safeguard against infinite loops
        step_count = 0

        while instance.current_step_id and instance.status == PlaybookExecutionStatus.RUNNING and step_count < max_steps:
            step_count += 1
            step_definition = playbook_def.steps.get(instance.current_step_id)

            if not step_definition:
                instance.status = PlaybookExecutionStatus.FAILED
                instance.error_message = f"Invalid step ID '{instance.current_step_id}' encountered."
                logger.error(instance.error_message + f" (Instance: {instance_id})")
                break

            logger.info(f"Executing Step [{step_count}/{max_steps}]: '{step_definition.name}' ({instance.current_step_id}) for instance '{instance_id}'")
            step_start_time = datetime.datetime.now(datetime.timezone.utc)
            step_success = False
            step_result_data = None
            step_error = None

            try:
                # --- Execute the actual step action ---
                step_success, step_result_data = self._execute_step(instance, step_definition)
                # --- Action executed ---
            except Exception as e:
                logger.exception(f"Error executing step '{instance.current_step_id}' for instance '{instance_id}'.")
                step_success = False
                step_error = str(e)
                instance.status = PlaybookExecutionStatus.FAILED
                instance.error_message = f"Error in step '{step_definition.name}': {step_error}"

            step_end_time = datetime.datetime.now(datetime.timezone.utc)
            step_duration = (step_end_time - step_start_time).total_seconds()

            # Log step result
            instance.step_results.append({
                "step_id": instance.current_step_id,
                "step_name": step_definition.name,
                "action_type": step_definition.action_type.value,
                "params": step_definition.action_params, # Be careful logging sensitive params
                "start_time": step_start_time.isoformat(),
                "end_time": step_end_time.isoformat(),
                "duration_sec": round(step_duration, 3),
                "success": step_success,
                "result_data": step_result_data, # Be careful logging large/sensitive data
                "error": step_error
            })

            # Determine next step
            if instance.status == PlaybookExecutionStatus.RUNNING: # Check if step execution failed the playbook
                 if step_success:
                     instance.current_step_id = step_definition.on_success_next_step_id
                 else:
                     instance.current_step_id = step_definition.on_failure_next_step_id

                 if instance.current_step_id is None:
                     # Reached an end state for this branch
                     logger.info(f"Playbook branch ending after step '{step_definition.id}' (Success: {step_success}).")
                     # Consider overall playbook complete only if *all* branches end successfully? Complex logic needed.
                     # Simple: Assume completed if last executed step succeeded and has no 'next'.
                     if step_success:
                         instance.status = PlaybookExecutionStatus.COMPLETED
                     else:
                         # If a step fails and has no failure path, mark playbook failed?
                         instance.status = PlaybookExecutionStatus.FAILED
                         instance.error_message = instance.error_message or f"Terminal step '{step_definition.id}' failed."
            # Persist state after each step? Or less frequently? Saving after each step for resilience.
            self._save_execution_state()

        # Final status update after loop finishes or breaks
        if instance.status == PlaybookExecutionStatus.RUNNING:
            # If loop finished due to max_steps or other break without setting final state
            if step_count >= max_steps:
                 instance.error_message = f"Exceeded maximum step limit ({max_steps})."
                 logger.error(instance.error_message + f" (Instance: {instance_id})")
            else:
                 instance.error_message = "Execution stopped unexpectedly."
                 logger.warning(instance.error_message + f" (Instance: {instance_id})")
            instance.status = PlaybookExecutionStatus.FAILED

        instance.end_time_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        logger.info(f"--- Playbook Execution Finished: {instance.playbook_name} ({instance_id}) --- Status: {instance.status.value}")
        self._save_execution_state()


    def _execute_step(self, instance: PlaybookExecutionInstance, step: PlaybookStep) -> Tuple[bool, Optional[Dict]]:
        """
        Executes the action defined in a playbook step. CONCEPTUAL.
        Relies on self.action_executor dependency.
        """
        logger.info(f"  Executing action: {step.action_type.value} for step '{step.name}'")
        params = step.action_params.copy()

        # --- Conceptual: Resolve template variables in params from instance.context ---
        # Example: if param value is "{{alert_hostname}}", replace it with instance.context['alert_hostname']
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                 var_name = value[2:-2].strip()
                 resolved_value = instance.context.get(var_name)
                 if resolved_value is not None:
                      params[key] = resolved_value
                 else:
                      logger.warning(f"    - Could not resolve variable '{var_name}' in step params.")
                      # Fail step? Or proceed with placeholder? Let's proceed for now.
                      # return False, {"error": f"Unresolved variable {var_name}"}

        logger.debug(f"    - Resolved Params: {params}")
        # --- End Conceptual Variable Resolution ---

        if not self.action_executor:
             logger.warning("  - Skipping action execution: No action executor provided (Simulation).")
             # Simulate success or failure based on action type for testing flow
             simulated_success = random.choice([True, True, False]) if step.action_type != PlaybookActionType.MANUAL_ANALYSIS_TASK else True
             simulated_result = {"message": f"Simulated execution for {step.action_type.value}", "success": simulated_success}
             return simulated_success, simulated_result

        # --- Placeholder: Call actual action executor ---
        try:
            # result = self.action_executor.execute(step.action_type.value, params, instance.context)
            # Assume executor returns dict with 'success': bool and 'data': Any
            # Simulate call
            sim_result_data = {"output": f"output of {step.action_type.value}", "items_found": random.randint(0,5)}
            sim_success = random.choice([True, True, False]) if step.action_type != PlaybookActionType.MANUAL_ANALYSIS_TASK else True

            if sim_success:
                 logger.info(f"    - Action '{step.action_type.value}' executed successfully (Simulated).")
                 # --- Conceptual: Update instance context ---
                 # If step definition specified output_vars, update instance.context
                 # e.g., if action_params had 'output_vars': ['ip_info', 'related_alerts']
                 # instance.context['ip_info'] = sim_result_data.get('ip_info')
                 # --- End Conceptual Context Update ---
                 return True, sim_result_data
            else:
                 logger.warning(f"    - Action '{step.action_type.value}' failed (Simulated).")
                 return False, sim_result_data

        except Exception as e:
             logger.error(f"    - Error calling action executor for '{step.action_type.value}': {e}")
             return False, {"error": f"Executor failed: {e}"}
        # --- End Placeholder ---


    def get_execution_status(self, instance_id: str) -> Optional[PlaybookExecutionInstance]:
        """Gets the current status and details of a specific playbook execution instance."""
        return self.active_executions.get(instance_id)


# Example Usage (conceptual)
if __name__ == "__main__":
    # Create dummy executor for conceptual calls
    class DummyActionExecutor:
         def execute(self, action_type, params, context):
             print(f"  DummyExecutor: Received action '{action_type}' with params {params}")
             time.sleep(0.2) # Simulate work
             success = random.choice([True, True, False]) # Simulate outcome
             result_data = {"message": f"Dummy result for {action_type}", "found_suspicious": success if action_type == 'threat_intel_lookup' else None}
             return {"success": success, "data": result_data}

    print("\n--- SOC Playbook Manager Example ---")
    # Use temporary files
    defs_path = "./temp_playbook_defs/" # Not actually used as defs are hardcoded in skeleton
    state_path = "./temp_playbook_state.json"
    if os.path.exists(state_path): os.remove(state_path)

    executor = DummyActionExecutor()
    manager = SOCPlaybookManager(
        action_executor=executor,
        instance_state_path=state_path
    )

    # List playbooks
    print("\nAvailable Playbooks:")
    playbooks = manager.list_playbooks()
    for pb_summary in playbooks: print(f"- {pb_summary['name']} ({pb_summary['id']})")

    # Trigger a playbook based on a mock alert
    print("\nTriggering Phishing Playbook...")
    mock_alert = {
        "alert_name": "Phishing Email Reported",
        "severity": "medium", # Lowercase matches example condition "severity:medium" implicitly
        "source": "UserSubmission",
        "email_message_id": "<xyz123@mail.example.com>"
    }
    instance_id = manager.trigger_playbook(mock_alert)

    if instance_id:
         print(f"Playbook triggered. Execution Instance ID: {instance_id}")
         # Monitor status (in this sync example, it will likely be completed/failed already)
         time.sleep(0.5) # Give execution time if it were async
         final_instance_state = manager.get_execution_status(instance_id)
         if final_instance_state:
             print(f"\nFinal status for instance '{instance_id}': {final_instance_state.status.value}")
             print("Execution Log:")
             for step_log in final_instance_state.step_results:
                 print(f"  - Step: {step_log['step_name']}, Success: {step_log['success']}, Result: {str(step_log['result_data'])[:100]}...")
             if final_instance_state.error_message:
                  print(f"Error Message: {final_instance_state.error_message}")
         else:
              print("Could not retrieve final instance state.")
    else:
         print("No playbook was triggered for the mock alert.")

    # Check persistence
    print("\nReloading manager to check execution persistence...")
    del manager
    manager_reloaded = SOCPlaybookManager(instance_state_path=state_path)
    print(f"Number of execution instances loaded after reload: {len(manager_reloaded.active_executions)}")


    # Clean up temp file
    if os.path.exists(state_path): os.remove(state_path)


    print("\n--- End Example ---")
