# Devin/cyber_range/ai_red_team/autonomous_hacking_agents.py
# Purpose: Conceptual framework for managing autonomous agents simulating hacking activities for research ONLY.
# WARNING: HIGHLY EXPERIMENTAL AND SPECULATIVE. DOES NOT PERFORM REAL HACKING.
#          Core action execution is PLACEHOLDER requiring human oversight/safe integration.

import os
import json
import uuid
import datetime
import logging
import time
from enum import Enum
from typing import Dict, List, Optional, Any, TypedDict, Literal
from dataclasses import dataclass, field, asdict

# --- Conceptual Imports ---
# Needs connectors to LLMs (e.g., GPT-4 via OpenAI API)
# Needs potential interface to Mitre ATT&CK KB
# Needs interface to SAFE, APPROVED, SANDBOXED tools or simulation environment
try:
    from ....ai_integrations.chatgpt_connector import ChatGPTConnector # Example LLM connector
    # from ..adversary_emulation.mitre_attck import MitreAttackKnowledgeBase # Example KB
    # from ...tools.safe_scanner import SafeScanner # Example hypothetical safe tool interface
except ImportError:
    print("WARNING: Could not import dependencies (Connectors, KB, Safe Tools). Using placeholders.")
    class PlaceholderConnector:
        def get_chat_completion(self, *args, **kwargs): return "LLM Placeholder: Suggest running nmap scan on target X."
    ChatGPTConnector = PlaceholderConnector # type: ignore
    # MitreAttackKnowledgeBase = object
    # SafeScanner = object

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("AutonomousHackingAgent")


# --- Enums and Data Structures ---

class AgentStatus(str, Enum):
    IDLE = "Idle"
    CONFIGURING = "Configuring"
    RUNNING = "Running"
    PAUSED_FOR_APPROVAL = "Paused - Awaiting Approval"
    COMPLETED = "Completed"
    FAILED = "Failed"
    STOPPED = "Stopped"

class FindingSeverity(str, Enum):
    INFO = "Informational"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

@dataclass
class PotentialFinding:
    """Represents a potential vulnerability or finding identified by the agent."""
    finding_id: str = field(default_factory=lambda: f"FIND-{uuid.uuid4().hex[:8].upper()}")
    timestamp_utc: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    description: str
    severity_estimate: FindingSeverity
    affected_resource: Optional[str] = None # e.g., IP, URL, hostname
    technique_id_guess: Optional[str] = None # MITRE ATT&CK ID if guessed by LLM
    confidence_score: float = 0.5 # How confident the agent/LLM is (0.0-1.0)
    supporting_evidence: Optional[str] = None # Log snippet, tool output etc.
    requires_validation: bool = True # Findings from AI usually need human validation

@dataclass
class AgentConfiguration:
    """Configuration for a specific autonomous agent instance."""
    agent_id: str
    name: str = "Unnamed Agent"
    goal: str # High-level objective (e.g., "Find web vulnerabilities on target X", "Attempt initial access via phishing simulation")
    target_scope: List[str] # List of IPs, domains, URLs strictly defining the allowed scope
    rules_of_engagement: List[str] # e.g., "No DoS", "No data exfiltration", "Stop on first shell"
    # --- AI Configuration ---
    llm_connector_id: str = "openai" # Which configured connector to use
    llm_model_name: Optional[str] = None # Specific model override (e.g., "gpt-4-turbo")
    base_prompt_template: Optional[str] = None # Custom system prompt for the agent's persona
    # --- Operational Parameters ---
    max_cycles: int = 100 # Limit number of think-act cycles
    max_duration_min: int = 60 # Limit total runtime
    # *** CRITICAL: Requires human approval before executing potentially impactful actions ***
    require_human_approval_for_actions: List[str] = field(default_factory=lambda: ["run_exploit", "modify_system", "send_phish"]) # List of action types needing explicit approval

@dataclass
class AgentExecutionState:
    """Tracks the runtime state of an agent instance."""
    instance_id: str = field(default_factory=lambda: f"AGENT-RUN-{uuid.uuid4().hex[:12].upper()}")
    agent_id: str
    config: AgentConfiguration
    status: AgentStatus = AgentStatus.IDLE
    start_time_utc: Optional[str] = None
    end_time_utc: Optional[str] = None
    current_cycle: int = 0
    cycle_history: List[Dict[str, Any]] = field(default_factory=list) # Log of thoughts, proposed actions, results
    findings: List[PotentialFinding] = field(default_factory=list)
    last_error: Optional[str] = None
    human_approval_pending_action: Optional[Dict[str, Any]] = None # Stores action awaiting approval


# --- Agent Manager Class ---

class AutonomousAgentManager:
    """
    Manages the configuration and execution lifecycle of conceptual autonomous hacking agents.

    *** WARNING: This manager orchestrates potentially high-risk simulations.
    *** All actions performed by agents MUST be heavily sandboxed, monitored,
    *** and require human oversight, especially those involving potential 'hacking' steps.
    """
    DEFAULT_AGENT_CONFIG_PATH = "./cyber_range/ai_red_team/agent_configs/" # Dir for agent JSON/YAML defs
    DEFAULT_EXECUTION_STATE_PATH = "./data/agent_execution_state.json" # Persistence for runs

    def __init__(self,
                 agent_config_path: Optional[str] = None,
                 execution_state_path: Optional[str] = None,
                 # Dependencies (Conceptual)
                 llm_connectors: Optional[Dict[str, Any]] = None, # e.g., {'openai': ChatGPTConnector(), ...}
                 action_executor: Optional[Any] = None, # Secure/Sandboxed action executor
                 mitre_kb: Optional[Any] = None # MitreAttackKnowledgeBase instance
                 ):
        """Initializes the Agent Manager."""
        self.config_path = agent_config_path or self.DEFAULT_AGENT_CONFIG_PATH
        self.state_path = execution_state_path or self.DEFAULT_EXECUTION_STATE_PATH

        # Store dependencies (replace None with actual injected instances)
        self.llm_connectors = llm_connectors or {"openai": PlaceholderConnector()} # Example default
        self.action_executor = action_executor # CRITICAL: This needs to be safe/sandboxed
        self.mitre_kb = mitre_kb

        # {agent_id: AgentConfiguration}
        self.agent_definitions: Dict[str, AgentConfiguration] = {}
        # {instance_id: AgentExecutionState}
        self.active_executions: Dict[str, AgentExecutionState] = {}

        self._load_agent_definitions()
        self._load_execution_state()
        logger.info(f"AutonomousAgentManager initialized. Loaded {len(self.agent_definitions)} agent configs. Tracking {len(self.active_executions)} executions.")

        if not self.action_executor:
             logger.warning("Action Executor not provided. Agent actions will only be logged, not executed.")

    def _load_agent_definitions(self):
        """Loads agent configurations from files (conceptual)."""
        logger.info(f"Loading agent definitions from '{self.config_path}'...")
        # In reality: Scan directory, parse JSON/YAML, validate schema.
        # For skeleton: Use a hardcoded example.
        dummy_agent_id = f"AGENT-{uuid.uuid4().hex[:4].upper()}"
        self.agent_definitions[dummy_agent_id] = AgentConfiguration(
            agent_id=dummy_agent_id,
            name="Web Vuln Scanner Agent (Conceptual)",
            goal="Identify common web vulnerabilities (XSS, SQLi - simulated checks only) in targets listed in scope.",
            target_scope=["http://test-target-web.example.local"],
            rules_of_engagement=["Read-only discovery", "No exploitation", "Report findings only"],
            llm_connector_id="openai", # Use the configured openai connector
            require_human_approval_for_actions=["run_scanner_tool", "attempt_sqli_payload"] # Example restricted actions
        )
        logger.info(f"Loaded {len(self.agent_definitions)} dummy agent definitions.")

    def _load_execution_state(self):
        """Loads ongoing/recent agent execution states from file."""
        if not os.path.exists(self.state_path):
            logger.info(f"Execution state file '{self.state_path}' not found. Starting fresh.")
            self.active_executions = {}
            return
        try:
            with open(self.state_path, 'r') as f:
                raw_data = json.load(f)
                # Deserialize (requires handling nested dataclasses/enums properly)
                self.active_executions = {}
                for iid, idata in raw_data.items():
                     try:
                         config_data = idata.pop('config', {})
                         findings_data = idata.pop('findings', [])
                         idata['status'] = AgentStatus(idata.get('status', 'FAILED'))
                         instance = AgentExecutionState(**idata)
                         instance.config = AgentConfiguration(**config_data)
                         instance.findings = [PotentialFinding(**f) for f in findings_data]
                         self.active_executions[iid] = instance
                     except Exception as deser_e:
                          logger.error(f"Failed to deserialize execution state for instance '{iid}': {deser_e}")
            logger.info(f"Loaded state for {len(self.active_executions)} agent executions from '{self.state_path}'.")
            # TODO: Potentially resume RUNNING or PAUSED agents on startup? Complex.
        except (IOError, json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error(f"Failed to load or parse execution state from '{self.state_path}': {e}. Resetting state.")
            self.active_executions = {}

    def _save_execution_state(self):
        """Saves the current state of active agent executions."""
        # Add locking if manager accessed concurrently
        # with self._lock:
        try:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            data_to_save = {}
            # Serialize dataclasses/enums correctly for JSON
            for iid, instance in self.active_executions.items():
                 instance_dict = asdict(instance)
                 instance_dict['status'] = instance.status.value # Convert enum to string
                 # Convert nested dataclasses/enums if needed
                 instance_dict['config']['require_human_approval_for_actions'] = instance.config.require_human_approval_for_actions
                 instance_dict['findings'] = [asdict(f) for f in instance.findings]
                 for finding in instance_dict['findings']:
                     if isinstance(finding.get('severity_estimate'), Enum):
                          finding['severity_estimate'] = finding['severity_estimate'].value
                 data_to_save[iid] = instance_dict

            with open(self.state_path, 'w') as f:
                json.dump(data_to_save, f, indent=2)
            # logger.debug("Saved execution state.")
        except IOError as e:
            logger.error(f"Failed to save execution state to '{self.state_path}': {e}")

    # Add methods for list_agent_definitions, get_agent_definition etc.

# --- Agent Manager Class Continued ---

    def create_and_start_agent(self, agent_id: str, user_id: str = "system") -> Optional[str]:
        """
        Creates a new execution instance for a defined agent and starts its run conceptually.

        Args:
            agent_id (str): The ID of the agent definition to use.
            user_id (str): Identifier for the user initiating the agent run.

        Returns:
            Optional[str]: The unique instance ID of the agent execution, or None if failed.
        """
        definition = self.agent_definitions.get(agent_id)
        if not definition:
            logger.error(f"Cannot create agent: Definition ID '{agent_id}' not found.")
            return None

        logger.info(f"Creating and starting new execution instance for agent '{definition.name}' ({agent_id})...")
        instance = AgentExecutionState(
            agent_id=agent_id,
            config=definition # Store copy of config at execution start
            # user_id=user_id # Might add this field to AgentExecutionState
        )
        instance.status = AgentStatus.RUNNING # Set to running conceptually
        instance.start_time_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.active_executions[instance.instance_id] = instance
        self._save_execution_state()
        logger.info(f"Agent instance '{instance.instance_id}' created and marked as RUNNING.")

        # --- Trigger Background Execution ---
        # In a real system, this should run in a separate thread or task queue
        # to avoid blocking the main application.
        logger.info(f"Conceptual: Starting execution loop for instance '{instance.instance_id}' (synchronous in skeleton)...")
        self._run_agent_instance(instance.instance_id)
        # --- End Trigger ---

        return instance.instance_id

    def _run_agent_instance(self, instance_id: str):
        """
        Conceptual execution loop for a single agent instance.
        *** Should run as a background task/thread in a real system. ***
        """
        instance = self.active_executions.get(instance_id)
        if not instance:
            logger.error(f"_run_agent_instance: Instance '{instance_id}' not found.")
            return

        logger.info(f"Instance '{instance_id}': Starting execution loop (Max Cycles: {instance.config.max_cycles}, Max Duration: {instance.config.max_duration_min} min).")
        start_monotonic = time.monotonic()

        while instance.status == AgentStatus.RUNNING:
            if instance.current_cycle >= instance.config.max_cycles:
                 logger.warning(f"Instance '{instance_id}': Reached max cycle limit ({instance.config.max_cycles}). Stopping.")
                 instance.status = AgentStatus.COMPLETED # Or maybe FAILED if goal not met?
                 break

            duration_sec = time.monotonic() - start_monotonic
            if duration_sec > instance.config.max_duration_min * 60:
                 logger.warning(f"Instance '{instance_id}': Reached max duration limit ({instance.config.max_duration_min} min). Stopping.")
                 instance.status = AgentStatus.COMPLETED # Or FAILED?
                 break

            instance.current_cycle += 1
            cycle_log_entry = {"cycle": instance.current_cycle, "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat()}
            logger.info(f"Instance '{instance_id}': Starting Cycle {instance.current_cycle}/{instance.config.max_cycles}")

            try:
                # 1. Gather Context (Placeholder)
                current_context = {
                    "goal": instance.config.goal,
                    "scope": instance.config.target_scope,
                    "previous_actions": [h.get("action") for h in instance.cycle_history if h.get("action")],
                    "recent_findings": [asdict(f) for f in instance.findings[-5:]], # Last 5 findings
                    "cycle_history_summary": f"Completed {instance.current_cycle-1} cycles." # Simple summary
                }
                cycle_log_entry["context_summary"] = f"Goal: {instance.config.goal[:50]}..., Findings: {len(instance.findings)}"

                # 2. Think (LLM Call)
                connector = self.llm_connectors.get(instance.config.llm_connector_id)
                if not connector: raise ValueError(f"LLM Connector '{instance.config.llm_connector_id}' not found.")

                prompt = self._prepare_prompt(instance.config, current_context, instance.cycle_history)
                cycle_log_entry["llm_prompt_summary"] = prompt[:200] + "..." # Log truncated prompt
                logger.debug(f"Instance '{instance_id}' Cycle {instance.current_cycle}: Sending prompt to LLM...")

                llm_response = connector.get_chat_completion(
                    messages=[{"role": "user", "content": prompt}], # Structure depends on connector/model
                    model=instance.config.llm_model_name, # Use specific model if set
                    temperature=0.5 # Example temperature for more deterministic actions?
                )

                if llm_response is None: raise RuntimeError("LLM call failed or returned empty response.")
                cycle_log_entry["llm_response_summary"] = llm_response[:200] + "..."
                logger.debug(f"Instance '{instance_id}' Cycle {instance.current_cycle}: Received LLM response.")

                # 3. Parse LLM Response (Placeholder)
                parsed_action = self._analyze_llm_response(llm_response) # Returns dict like {'action_type': '...', 'params': {...}} or {'finding': {...}} or None
                cycle_log_entry["parsed_llm_output"] = parsed_action

                if not parsed_action:
                     logger.warning(f"Instance '{instance_id}' Cycle {instance.current_cycle}: Could not parse action/finding from LLM response.")
                     # Decide: Stop? Ask LLM to clarify? Continue? Let's continue for now.
                     action_result = None
                     action_status = "skipped"
                elif "finding" in parsed_action:
                     logger.info(f"Instance '{instance_id}' Cycle {instance.current_cycle}: LLM proposed a finding.")
                     # Validate finding structure?
                     try:
                          finding = PotentialFinding(**parsed_action["finding"])
                          instance.findings.append(finding)
                          logger.info(f"  - Added finding: {finding.description[:100]}...")
                     except Exception as find_e:
                           logger.error(f"  - Invalid finding structure from LLM: {find_e}")
                     action_result = parsed_action["finding"]
                     action_status = "finding_logged"
                     # Continue to next cycle after logging finding
                     time.sleep(1) # Small delay after finding
                elif "action_type" in parsed_action:
                     action_type = parsed_action["action_type"]
                     action_params = parsed_action.get("params", {})
                     cycle_log_entry["action"] = parsed_action # Log proposed action

                     # 4. Check for Human Approval
                     if action_type in instance.config.require_human_approval_for_actions:
                          logger.warning(f"Instance '{instance_id}' Cycle {instance.current_cycle}: Action '{action_type}' REQUIRES HUMAN APPROVAL.")
                          instance.status = AgentStatus.PAUSED_FOR_APPROVAL
                          instance.human_approval_pending_action = parsed_action
                          self._save_execution_state() # Save paused state
                          self._notify_human_for_approval(instance_id, parsed_action) # Conceptual notification
                          break # Pause execution loop

                     # 5. Execute Action Safely (Placeholder)
                     action_result = self._execute_action_safely(instance_id, action_type, action_params)
                     action_status = "executed_safely" if action_result is not None else "execution_failed"
                     cycle_log_entry["action_result_summary"] = str(action_result)[:200] if action_result is not None else "None"
                     if action_result is None:
                          logger.error(f"Instance '{instance_id}' Cycle {instance.current_cycle}: Safe action execution failed for '{action_type}'.")
                          # Stop? Or let LLM handle failure in next cycle? Let's continue.
                else:
                     logger.warning(f"Instance '{instance_id}' Cycle {instance.current_cycle}: LLM response did not yield a recognized action or finding.")
                     action_result = None
                     action_status = "no_action_parsed"

            except Exception as cycle_e:
                logger.exception(f"Instance '{instance_id}' Cycle {instance.current_cycle}: Error during cycle execution.")
                instance.status = AgentStatus.FAILED
                instance.last_error = f"Cycle {instance.current_cycle} failed: {cycle_e}"
                action_status = "cycle_error"
            finally:
                 cycle_log_entry["end_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                 cycle_log_entry["status"] = action_status
                 instance.cycle_history.append(cycle_log_entry)
                 # Save state after each cycle? Or batch? Saving here.
                 self._save_execution_state()

            # Check if goal met based on findings/state (Conceptual)
            if self._check_goal_completion(instance):
                 logger.info(f"Instance '{instance_id}': Goal condition met. Completing run.")
                 instance.status = AgentStatus.COMPLETED
                 break

        # --- Loop Finished ---
        instance.end_time_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if instance.status == AgentStatus.RUNNING: # If loop ended naturally without setting final state
            instance.status = AgentStatus.COMPLETED # Assume completed if max cycles/duration reached without error/pause
        logger.info(f"Instance '{instance_id}': Execution loop finished. Final Status: {instance.status.value}")
        self._save_execution_state()

    def _prepare_prompt(self, config: AgentConfiguration, current_context: Dict, history: List[Dict]) -> str:
        """Creates the prompt for the LLM based on goal, context, and history."""
        logger.debug("Preparing LLM prompt...")
        # --- Placeholder: Needs sophisticated prompt engineering ---
        # Include: Persona, Goal, Rules of Engagement, Scope, Current Context, History Summary, Request for Next Action/Analysis
        prompt = f"You are '{config.name}', an AI agent.\n"
        prompt += f"Your Goal: {config.goal}\n"
        prompt += f"Scope: {config.target_scope}\n"
        prompt += f"Rules: {config.rules_of_engagement}\n\n"
        prompt += f"Current Context:\n{json.dumps(current_context, indent=2)}\n\n"
        prompt += f"Previous Cycle Summaries (Max 5):\n"
        for entry in history[-5:]:
             prompt += f"- Cycle {entry.get('cycle')}: Action='{entry.get('action',{}).get('action_type','N/A')}', Result Status='{entry.get('status')}'\n"
        prompt += "\nBased on the context and history, determine the single best *next* action to take towards the goal OR identify a specific finding."
        prompt += " Respond ONLY with a JSON object containing either {'action_type': '...', 'params': {...}} OR {'finding': {'description': '...', 'severity_estimate': '...', ...}}."
        prompt += " Valid action_types: [query_mitre, web_scan, analyze_data, run_scanner_tool, attempt_sqli_payload, report_finding, no_action]." # Example actions
        # --- End Placeholder ---
        return prompt

    def _analyze_llm_response(self, response_text: str) -> Optional[Dict]:
        """Parses the LLM's text response into a structured action or finding."""
        logger.debug("Parsing LLM response...")
        # --- Placeholder: Needs robust JSON parsing and validation ---
        try:
            # Expecting JSON directly based on prompt
            parsed = json.loads(response_text)
            if isinstance(parsed, dict):
                 if "action_type" in parsed and "params" in parsed:
                      # TODO: Validate action_type and params structure
                      logger.info(f"  - Parsed Action: {parsed['action_type']}")
                      return parsed
                 elif "finding" in parsed and isinstance(parsed["finding"], dict):
                      # TODO: Validate finding structure against PotentialFinding fields
                      logger.info(f"  - Parsed Finding: {parsed['finding'].get('description', 'No description')[:50]}...")
                      return parsed
                 else:
                      logger.warning(f"  - LLM response JSON lacks expected 'action_type'/'params' or 'finding' keys: {parsed}")
            else:
                logger.warning(f"  - LLM response was valid JSON but not a dictionary: {type(parsed)}")
        except json.JSONDecodeError:
            logger.warning(f"  - LLM response was not valid JSON: {response_text[:200]}...")
            # TODO: Could try regex or prompting LLM again to format correctly
        except Exception as e:
             logger.error(f"  - Error parsing LLM response: {e}")
        # --- End Placeholder ---
        return None

    def _execute_action_safely(self, instance_id: str, action_type: str, params: Dict) -> Optional[Any]:
        """
        *** CRITICAL PLACEHOLDER - DOES NOT EXECUTE REAL ACTIONS ***
        Logs the intended action and returns simulated result.
        A real implementation MUST integrate with heavily sandboxed and approved tools ONLY.
        """
        logger.warning(f"Instance '{instance_id}': Attempting SAFE EXECUTION (Placeholder) of action '{action_type}' with params: {params}")
        # --- Placeholder Implementation ---
        # 1. Log the intended action in detail.
        # 2. Check against fine-grained permissions / rules of engagement AGAIN.
        # 3. If the action is allowed conceptually:
        #    - Call a *sandboxed* tool execution function (e.g., run nmap in container, call safe web scraper)
        #    - OR provide simulated output based on action type for testing flow.
        # 4. NEVER directly execute exploits, OS commands, or file modifications here without EXTREME sandboxing and oversight.
        simulated_success = random.choice([True, True, False]) # Simulate outcome
        simulated_output = None
        if simulated_success:
            simulated_output = f"Simulated successful output for {action_type} on {params.get('target', 'unknown')}"
            logger.info(f"  - Action '{action_type}' simulated successfully.")
        else:
            simulated_output = f"Simulated failure for {action_type} on {params.get('target', 'unknown')}"
            logger.error(f"  - Action '{action_type}' simulated as failed.")

        # Return conceptual result
        return {"success": simulated_success, "output": simulated_output} if simulated_success else None
        # --- End Placeholder ---

    def _notify_human_for_approval(self, instance_id: str, action: Dict):
        """Placeholder: Sends notification that human approval is needed."""
        logger.critical(f"ACTION REQUIRED: Agent instance '{instance_id}' requires approval for action: {action}")
        # --- Placeholder: Integrate with AlertingSystem ---
        # self.alert_system.send_alert("HIGH", f"Agent '{instance_id}' requires approval", action)
        # --- End Placeholder ---


    def _check_goal_completion(self, instance: AgentExecutionState) -> bool:
        """Conceptual check if the agent's goal has been met based on findings/state."""
        # --- Placeholder: Implement actual goal checking logic ---
        # e.g., check if a finding with 'CRITICAL' severity exists, or if specific target achieved
        # --- End Placeholder ---
        return False # Default to not completed


    def stop_agent(self, instance_id: str) -> bool:
        """Requests an agent instance to stop its execution loop gracefully."""
        logger.info(f"Requesting stop for agent instance '{instance_id}'...")
        with self._lock: # Assuming state access needs locking if run loop is threaded
             instance = self.active_executions.get(instance_id)
             if instance and instance.status == AgentStatus.RUNNING or instance.status == AgentStatus.PAUSED_FOR_APPROVAL:
                  instance.status = AgentStatus.STOPPED
                  instance.end_time_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
                  self._save_execution_state()
                  logger.info(f"Agent instance '{instance_id}' marked as STOPPED.")
                  return True
             elif instance:
                  logger.warning(f"Agent instance '{instance_id}' already in non-running state: {instance.status.value}")
                  return False # Or True if already stopped?
             else:
                  logger.error(f"Cannot stop agent: Instance ID '{instance_id}' not found.")
                  return False

    def approve_action(self, instance_id: str, approved: bool = True) -> bool:
        """Allows a human operator to approve or deny a paused action."""
        logger.info(f"Received approval={approved} for action on instance '{instance_id}'...")
        with self._lock:
            instance = self.active_executions.get(instance_id)
            if not instance or instance.status != AgentStatus.PAUSED_FOR_APPROVAL or instance.human_approval_pending_action is None:
                logger.error(f"Cannot approve/deny action: Instance '{instance_id}' not found or not awaiting approval.")
                return False

            action_to_execute = instance.human_approval_pending_action
            instance.human_approval_pending_action = None # Clear pending action

            cycle_log_entry = {"cycle": instance.current_cycle, "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat()} # Log approval action
            cycle_log_entry["action"] = action_to_execute

            if approved:
                logger.info(f"Action approved by human. Executing safely...")
                action_result = self._execute_action_safely(instance_id, action_to_execute['action_type'], action_to_execute.get('params', {}))
                action_status = "executed_safely_approved" if action_result is not None else "execution_failed_approved"
                cycle_log_entry["action_result_summary"] = str(action_result)[:200] if action_result is not None else "None"
                # Resume the agent's run loop
                instance.status = AgentStatus.RUNNING
                logger.info(f"Instance '{instance_id}' resuming execution.")
                # In a real system, signal the background thread/task to continue
                # For skeleton, we might call _run_agent_instance again or assume loop continues
                # self._run_agent_instance(instance_id) # CAUTION: Potential recursion if called directly
            else:
                logger.warning(f"Action denied by human. Agent will need to replan.")
                action_status = "action_denied"
                # Agent needs to re-evaluate context in next cycle
                instance.status = AgentStatus.RUNNING # Allow loop to continue for replanning
                logger.info(f"Instance '{instance_id}' resuming execution for replanning.")
                # self._run_agent_instance(instance_id) # As above

            cycle_log_entry["end_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cycle_log_entry["status"] = action_status
            instance.cycle_history.append(cycle_log_entry)
            self._save_execution_state()
            return True

    def get_agent_status(self, instance_id: str) -> Optional[AgentExecutionState]:
        """Gets the current state of a specific agent execution instance."""
        return self.active_executions.get(instance_id)

    def list_running_agents(self) -> List[AgentExecutionState]:
        """Lists all agent instances currently in a running or paused state."""
        return [inst for inst in self.active_executions.values() if inst.status in [AgentStatus.RUNNING, AgentStatus.PAUSED_FOR_APPROVAL]]

    def get_agent_findings(self, instance_id: str) -> Optional[List[PotentialFinding]]:
        """Gets the list of potential findings reported by an agent instance."""
        instance = self.get_agent_status(instance_id)
        return instance.findings if instance else None


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Autonomous Hacking Agent Manager Example (Conceptual & Safe Simulation) ---")
    print("*** WARNING: This demonstrates framework ONLY. No real hacking occurs. ***")

    # Setup conceptual dependencies
    connectors = {"openai": PlaceholderConnector()}
    # Action executor MUST be safe/sandboxed - using None here means actions are only logged
    executor = None

    manager = AutonomousAgentManager(
        llm_connectors=connectors,
        action_executor=executor # Set to None for safety in example
    )

    # Get agent definition ID (using the dummy one loaded)
    agent_def_id = list(manager.agent_definitions.keys())[0] if manager.agent_definitions else None

    if agent_def_id:
        # Create and start an agent instance
        print(f"\nStarting agent '{agent_def_id}'...")
        instance_id = manager.create_and_start_agent(agent_id=agent_def_id, user_id="test_user")

        if instance_id:
            print(f"Agent instance created with ID: {instance_id}")

            # Check status periodically (simulation runs synchronously here)
            time.sleep(1) # Allow conceptual cycles to run
            status_info = manager.get_agent_status(instance_id)
            if status_info:
                print(f"\nCurrent agent status: {status_info.status.value}")
                print(f"Current cycle: {status_info.current_cycle}")
                print(f"Findings: {len(status_info.findings)}")

                # Simulate needing approval (if applicable based on config/LLM output)
                if status_info.status == AgentStatus.PAUSED_FOR_APPROVAL:
                    print("\nAgent paused for action approval:")
                    print(json.dumps(status_info.human_approval_pending_action, indent=2))
                    # Conceptually approve the action
                    approved = manager.approve_action(instance_id, approved=True)
                    print(f"Action approval processed: {approved}")
                    # Check status again after conceptual continuation
                    status_info_after = manager.get_agent_status(instance_id)
                    if status_info_after: print(f"Status after approval: {status_info_after.status.value}")


            # Stop the agent (if it hasn't completed/failed already)
            print("\nRequesting agent stop...")
            stopped = manager.stop_agent(instance_id)
            print(f"Agent stop requested: {stopped}")
            final_status_info = manager.get_agent_status(instance_id)
            if final_status_info: print(f"Final status: {final_status_info.status.value}")

            # Get findings
            findings = manager.get_agent_findings(instance_id)
            if findings:
                 print("\nReported Findings:")
                 print(json.dumps([asdict(f) for f in findings], indent=2))

        else:
            print("Failed to start agent instance.")
    else:
        print("No agent definitions loaded.")

    # Cleanup state file
    if os.path.exists(manager.state_path): os.remove(manager.state_path)

    print("\n--- End Example ---")
