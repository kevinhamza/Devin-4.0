# Devin/edge_ai/swarm_intelligence/swarm_orchestrator.py
# Purpose: Orchestrates tasks and coordination for a swarm of agents.

import time
import logging
import uuid
import datetime
from enum import Enum
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict

# --- Conceptual Imports ---
try:
    # Assumes StigmergyEngine is defined elsewhere if used
    from .stigmergy_engine import StigmergyEngine, Location, TraceType
except ImportError:
    print("WARNING: Cannot import StigmergyEngine. Stigmergy-based coordination disabled.")
    StigmergyEngine = None # type: ignore
    Location = Any
    TraceType = str

# Placeholder for the communication layer with agents (e.g., MQTT client, API wrapper)
class AgentCommunicatorPlaceholder:
    def send_task(self, agent_id: str, task: 'SwarmTask') -> bool:
        logger.info(f"COMMUNICATOR PLACEHOLDER: Sending task '{task.task_id}' (Type: {task.type}) to agent '{agent_id}'")
        time.sleep(0.05) # Simulate send delay
        # Simulate success/failure based on agent being known maybe
        return True # Assume success for now
    def broadcast_message(self, topic: str, message: Dict):
         logger.info(f"COMMUNICATOR PLACEHOLDER: Broadcasting message on topic '{topic}': {str(message)[:100]}...")
         time.sleep(0.02)

# --- Enums and Data Structures ---

class AgentSwarmStatus(str, Enum):
    IDLE = "Idle"
    WORKING = "Working" # Actively performing an assigned task
    MOVING = "Moving" # Traveling to a task location
    ERROR = "Error"
    OFFLINE = "Offline" # No recent heartbeat

@dataclass
class AgentState:
    """Represents the state of an individual agent in the swarm."""
    agent_id: str
    status: AgentSwarmStatus = AgentSwarmStatus.IDLE
    last_heartbeat_utc: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    current_task_id: Optional[str] = None
    location: Optional[Location] = None # Current reported location (e.g., grid coords, GPS)
    capabilities: List[str] = field(default_factory=list) # e.g., ["sensor_temp", "manipulator", "camera"]
    metadata: Dict[str, Any] = field(default_factory=dict) # Other agent-specific info

class TaskStatus(str, Enum):
    PENDING = "Pending" # Created, not assigned
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress" # Agent reported starting
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"

@dataclass
class SwarmTask:
    """Represents a task to be performed by an agent in the swarm."""
    task_id: str = field(default_factory=lambda: f"SWARM-TASK-{uuid.uuid4().hex[:8].upper()}")
    type: str # e.g., "explore_area", "monitor_location", "retrieve_item", "process_data"
    params: Dict[str, Any] # Task-specific parameters (e.g., {'target_location': (x,y), 'duration': 60})
    priority: int = 0 # Higher value means higher priority
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent_id: Optional[str] = None
    creation_time_utc: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    completion_time_utc: Optional[str] = None
    result: Optional[Any] = None


# --- Swarm Orchestrator Class ---

class SwarmOrchestrator:
    """
    Manages and coordinates a swarm of agents towards collective goals.

    Handles agent registration, status tracking, task assignment,
    and potentially utilizes stigmergy for coordination.
    """
    HEARTBEAT_TIMEOUT_SEC = 120.0 # Mark agent offline if no heartbeat for this long

    def __init__(self,
                 stigmergy_engine: Optional[StigmergyEngine] = None,
                 agent_communicator: Optional[Any] = None,
                 config: Optional[Dict] = None):
        """
        Initializes the Swarm Orchestrator.

        Args:
            stigmergy_engine (Optional[StigmergyEngine]): Instance for indirect coordination.
            agent_communicator (Optional[Any]): Instance for direct communication with agents.
            config (Optional[Dict]): Configuration parameters for the orchestrator.
        """
        self.stigmergy: Optional[StigmergyEngine] = stigmergy_engine
        self.communicator: Any = agent_communicator or AgentCommunicatorPlaceholder() # Use placeholder if none provided
        self.config = config or {}

        # State tracking
        self.swarm_state: Dict[str, AgentState] = {} # {agent_id: AgentState}
        self.active_tasks: Dict[str, SwarmTask] = {} # {task_id: SwarmTask}
        self.task_queue: List[SwarmTask] = [] # Simple list queue for pending tasks

        self._lock = threading.Lock() # For thread safety if accessed concurrently
        logger.info("SwarmOrchestrator initialized.")
        if self.stigmergy: logger.info("  - Stigmergy Engine integration enabled.")
        if not isinstance(self.communicator, AgentCommunicatorPlaceholder): logger.info("  - Using provided Agent Communicator.")


    def register_agent(self, agent_id: str, capabilities: List[str], initial_location: Optional[Location] = None, metadata: Optional[Dict] = None) -> bool:
        """Registers a new agent with the swarm."""
        with self._lock:
            if agent_id in self.swarm_state:
                 logger.warning(f"Agent '{agent_id}' already registered. Updating capabilities/metadata.")
                 self.swarm_state[agent_id].capabilities = capabilities
                 self.swarm_state[agent_id].location = initial_location if initial_location is not None else self.swarm_state[agent_id].location
                 self.swarm_state[agent_id].metadata = metadata or self.swarm_state[agent_id].metadata
                 self.swarm_state[agent_id].last_heartbeat_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
                 self.swarm_state[agent_id].status = AgentSwarmStatus.IDLE # Reset status on registration?
            else:
                 logger.info(f"Registering new agent: {agent_id}")
                 new_agent = AgentState(
                     agent_id=agent_id,
                     capabilities=capabilities,
                     location=initial_location,
                     metadata=metadata or {}
                 )
                 self.swarm_state[agent_id] = new_agent
            return True

    def update_agent_status(self, agent_id: str, status: AgentSwarmStatus, location: Optional[Location] = None, current_task_id: Optional[str] = None, metadata_update: Optional[Dict] = None):
        """Receives and updates the status of an agent."""
        with self._lock:
            if agent_id not in self.swarm_state:
                logger.warning(f"Received status update for unknown agent '{agent_id}'. Register agent first.")
                return False # Or maybe auto-register?

            logger.debug(f"Updating status for agent '{agent_id}': Status={status.value}, Loc={location}")
            agent = self.swarm_state[agent_id]
            agent.status = status
            agent.last_heartbeat_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
            if location is not None:
                agent.location = location
            # Only update task ID if provided, otherwise keep existing
            if current_task_id is not None:
                 agent.current_task_id = current_task_id
            if metadata_update:
                agent.metadata.update(metadata_update)
            return True

    def check_agent_heartbeats(self):
        """Checks for agents that haven't reported recently and marks them offline."""
        with self._lock:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            offline_threshold = now_utc - datetime.timedelta(seconds=self.HEARTBEAT_TIMEOUT_SEC)
            offline_agents = []
            for agent_id, agent in self.swarm_state.items():
                 if agent.status != AgentSwarmStatus.OFFLINE:
                      last_hb = datetime.datetime.fromisoformat(agent.last_heartbeat_utc)
                      if last_hb < offline_threshold:
                           logger.warning(f"Agent '{agent_id}' timed out (last heartbeat: {agent.last_heartbeat_utc}). Marking as OFFLINE.")
                           agent.status = AgentSwarmStatus.OFFLINE
                           offline_agents.append(agent_id)
                           # Optional: Fail/reassign task assigned to this agent
                           if agent.current_task_id and agent.current_task_id in self.active_tasks:
                                self.fail_task(agent.current_task_id, "Agent became offline.")
            # Potentially remove offline agents after a longer period?
            # if offline_agents: self._save_state() # Persist status change


    def add_task(self, task_type: str, params: Dict[str, Any], priority: int = 0) -> SwarmTask:
        """Adds a new task to the orchestrator's queue."""
        with self._lock:
            task = SwarmTask(type=task_type, params=params, priority=priority)
            self.active_tasks[task.task_id] = task
            # Simple queue for now, add based on priority
            self.task_queue.append(task)
            self.task_queue.sort(key=lambda t: t.priority, reverse=True) # Higher priority first
            logger.info(f"Added task {task.task_id} (Type: {task.type}) to queue. Queue size: {len(self.task_queue)}")
            # self._save_state() # Persist active tasks
            return task

    def assign_pending_tasks(self):
        """Attempts to assign tasks from the queue to available idle agents."""
        with self._lock:
            if not self.task_queue:
                return # No tasks to assign

            # Find idle agents
            idle_agents = [agent for agent in self.swarm_state.values() if agent.status == AgentSwarmStatus.IDLE]
            if not idle_agents:
                 logger.debug("No idle agents available to assign tasks.")
                 return

            logger.info(f"Attempting to assign {len(self.task_queue)} pending tasks to {len(idle_agents)} idle agents...")
            assigned_count = 0
            remaining_tasks = []
            # Iterate through queue (highest priority first)
            for task in self.task_queue:
                if not idle_agents: break # No more idle agents

                # --- Placeholder: Task Assignment Logic ---
                # Find best agent for this task (based on capabilities, location, etc.)
                # Simple: Assign to first available idle agent
                suitable_agent: Optional[AgentState] = None
                # Example: Check if task needs specific capability
                required_caps = task.params.get("required_capabilities", [])
                best_agent_candidate = None
                for agent in idle_agents:
                    if not required_caps or all(cap in agent.capabilities for cap in required_caps):
                         # TODO: Add location-based scoring if needed
                         best_agent_candidate = agent
                         break # Assign to first suitable agent found

                if best_agent_candidate:
                    agent_to_assign = best_agent_candidate
                    logger.info(f"Assigning task {task.task_id} ({task.type}) to agent {agent_to_assign.agent_id}")
                    task.assigned_agent_id = agent_to_assign.agent_id
                    task.status = TaskStatus.ASSIGNED
                    agent_to_assign.current_task_id = task.task_id
                    agent_to_assign.status = AgentSwarmStatus.WORKING # Assume agent starts working immediately

                    # --- Conceptual: Send task via communicator ---
                    send_ok = self.communicator.send_task(agent_to_assign.agent_id, task)
                    if not send_ok:
                         logger.error(f"Failed to send task {task.task_id} to agent {agent_to_assign.agent_id}. Reverting assignment.")
                         task.assigned_agent_id = None
                         task.status = TaskStatus.PENDING # Put back in queue state
                         agent_to_assign.current_task_id = None
                         agent_to_assign.status = AgentSwarmStatus.IDLE # Mark as idle again
                         remaining_tasks.append(task) # Keep task in queue
                    else:
                         assigned_count += 1
                         idle_agents.remove(agent_to_assign) # Agent is no longer idle
                else:
                    # No suitable agent found for this task right now
                    remaining_tasks.append(task)
                # --- End Placeholder ---

            self.task_queue = remaining_tasks # Update queue with unassigned tasks
            if assigned_count > 0:
                 self._save_execution_history() # Persist task assignments / agent state changes
                 # self._save_state() # Alternative state saving if needed
            logger.info(f"Task assignment complete. Assigned: {assigned_count}, Remaining in queue: {len(self.task_queue)}")


    def update_task_status(self, task_id: str, status: TaskStatus, result: Optional[Any] = None, message: Optional[str] = None):
         """Updates the status and potentially the result of an active task."""
         with self._lock:
             task = self.active_tasks.get(task_id)
             if not task:
                 logger.warning(f"Cannot update status for unknown task ID: {task_id}")
                 return False

             logger.info(f"Updating task '{task_id}' status to {status.value}")
             task.status = status
             if result is not None:
                 task.result = result
             if message:
                 # Append to message? Overwrite? Depends on desired logging
                 logger.info(f"Task '{task_id}' Message: {message}")

             agent_id = task.assigned_agent_id
             if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                 task.completion_time_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
                 # Mark assigned agent as idle again if they were working on this task
                 if agent_id and agent_id in self.swarm_state:
                     agent = self.swarm_state[agent_id]
                     if agent.current_task_id == task_id:
                          agent.current_task_id = None
                          agent.status = AgentSwarmStatus.IDLE
                          logger.info(f"Agent '{agent_id}' status set to IDLE after task {task_id} completion/failure.")
                     else:
                          logger.warning(f"Task {task_id} finished, but assigned agent {agent_id} was no longer assigned to it (Current task: {agent.current_task_id})")
                 # Optional: Remove completed/failed tasks from active_tasks after some time?
                 # del self.active_tasks[task_id]

             self._save_execution_history() # Persist task status change
             # self._save_state()
             return True


    def fail_task(self, task_id: str, reason: str):
        """Convenience method to mark a task as failed."""
        self.update_task_status(task_id, TaskStatus.FAILED, message=reason)

    def get_swarm_status(self) -> List[AgentState]:
        """Returns the current state of all registered agents."""
        with self._lock:
            # Return copies to prevent external modification
            return [dataclasses.replace(state) for state in self.swarm_state.values()]

    def get_task_status(self, task_id: str) -> Optional[SwarmTask]:
         """Gets the current status and details of a specific task."""
         with self._lock:
              task = self.active_tasks.get(task_id)
              return dataclasses.replace(task) if task else None


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Swarm Orchestrator Example (Conceptual) ---")

    # Initialize orchestrator (no stigmergy, using placeholder communicator)
    orchestrator = SwarmOrchestrator()

    # Register agents
    agent1_id = "drone_01"
    agent2_id = "rover_02"
    orchestrator.register_agent(agent1_id, capabilities=["camera", "movement_air"], initial_location=(0,0,10))
    orchestrator.register_agent(agent2_id, capabilities=["sensor_temp", "movement_ground"], initial_location=(5,5,0))

    print("\nCurrent Swarm Status:")
    status_list = orchestrator.get_swarm_status()
    for agent_state in status_list: print(f"  - {agent_state.agent_id}: {agent_state.status.value} at {agent_state.location}")

    # Add tasks
    print("\nAdding tasks...")
    task1 = orchestrator.add_task("explore_area", params={"area_coords": [(10,10), (20,20)], "required_capabilities": ["movement_air"]}, priority=10)
    task2 = orchestrator.add_task("monitor_location", params={"location": (5,5), "duration": 300, "required_capabilities": ["sensor_temp"]}, priority=5)
    task3 = orchestrator.add_task("recharge", params={"station_id": "CS-01"}, priority=0) # Lower priority

    # Assign tasks
    print("\nAssigning tasks...")
    orchestrator.assign_pending_tasks()

    print("\nSwarm Status after assignment:")
    status_list_after = orchestrator.get_swarm_status()
    for agent_state in status_list_after: print(f"  - {agent_state.agent_id}: {agent_state.status.value} (Task: {agent_state.current_task_id})")

    # Simulate agent completing a task
    print("\nSimulating task completion...")
    assigned_task_id = status_list_after[0].current_task_id # Get task assigned to first agent
    if assigned_task_id:
        orchestrator.update_task_status(assigned_task_id, TaskStatus.COMPLETED, result={"area_map": "...", "anomalies_found": 0})
    else:
        print("Could not get assigned task ID for simulation.")


    print("\nSwarm Status after task completion:")
    status_list_final = orchestrator.get_swarm_status()
    for agent_state in status_list_final: print(f"  - {agent_state.agent_id}: {agent_state.status.value} (Task: {agent_state.current_task_id})")

    # Simulate heartbeat timeout check
    print("\nSimulating heartbeat check (wait > timeout)...")
    # Need to manually set last_heartbeat far in the past for simulation
    if agent1_id in orchestrator.swarm_state:
         past_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=orchestrator.HEARTBEAT_TIMEOUT_SEC + 1)).isoformat()
         orchestrator.swarm_state[agent1_id].last_heartbeat_utc = past_time
    orchestrator.check_agent_heartbeats()
    print("\nSwarm Status after heartbeat check:")
    status_list_hb = orchestrator.get_swarm_status()
    for agent_state in status_list_hb: print(f"  - {agent_state.agent_id}: {agent_state.status.value}")

    print("\n--- End Example ---")
