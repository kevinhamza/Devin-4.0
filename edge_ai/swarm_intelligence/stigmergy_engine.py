# Devin/edge_ai/swarm_intelligence/stigmergy_engine.py
# Purpose: Implements stigmergy concepts for swarm agent coordination.

import time
import math
import logging
import threading
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple, Union

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("StigmergyEngine")

# --- Type Definitions ---
# Location can be complex (e.g., graph node ID, 3D coordinates)
# Using simple tuple of ints for this example (e.g., grid coordinates)
Location = Tuple[int, ...] # Example: (x, y) or (x, y, z)
TraceType = str # e.g., "food_found", "danger_signal", "path_intensity", "task_available"

@dataclasses.dataclass # Using dataclass for TraceInfo
class TraceInfo:
    """Holds information about a trace left in the environment."""
    intensity: float = 1.0 # Strength of the trace/pheromone
    timestamp: float = field(default_factory=time.monotonic) # Time it was last updated/deposited
    agent_id: Optional[str] = None # ID of the agent that left/updated the trace
    data: Optional[Dict] = None # Optional extra data associated with the trace


class StigmergyEngine:
    """
    Manages a shared environment where agents can deposit and read traces
    for indirect coordination (stigmergy).

    Implements trace deposition, retrieval, and decay mechanisms.
    Uses a dictionary to represent the environment state (mapping location to traces).
    Includes basic thread safety for concurrent agent access.
    """

    def __init__(self, default_decay_rate: float = 0.05, decay_interval_sec: float = 1.0, persistence_path: Optional[str] = None):
        """
        Initializes the StigmergyEngine.

        Args:
            default_decay_rate (float): Fractional decay per second (e.g., 0.05 = 5% decay per second).
                                       Lower value means slower decay. Set to 0 to disable decay.
            decay_interval_sec (float): How often the background decay process should ideally run.
            persistence_path (Optional[str]): Path to save/load environment state (conceptual).
        """
        # Environment state: { Location: { TraceType: TraceInfo } }
        self.environment_state: Dict[Location, Dict[TraceType, TraceInfo]] = defaultdict(dict)
        self.decay_rate = default_decay_rate # Decay factor per second
        self.decay_interval = decay_interval_sec
        self.persistence_path = persistence_path # Path for saving/loading state (conceptual)
        self._lock = threading.Lock() # Lock for thread-safe access to environment_state
        self._stop_decay_event = threading.Event()
        self._decay_thread: Optional[threading.Thread] = None

        self._load_state() # Conceptual load

        if self.decay_rate > 0 and self.decay_interval > 0:
             self._start_decay_thread()

        logger.info(f"StigmergyEngine initialized. Decay Rate: {self.decay_rate}/s, Interval: {self.decay_interval}s")

    def _load_state(self):
        """Conceptual loading of environment state from persistence."""
        if self.persistence_path and os.path.exists(self.persistence_path):
             logger.info(f"Conceptual: Loading stigmergy state from {self.persistence_path}")
             # In reality: Load JSON/Pickle, handle errors, deserialize TraceInfo objects
             # with self._lock: self.environment_state = load_from_file(self.persistence_path)
        else:
             logger.info("Starting with empty stigmergy environment state.")

    def _save_state(self):
        """Conceptual saving of environment state."""
        if self.persistence_path:
             logger.info(f"Conceptual: Saving stigmergy state to {self.persistence_path}")
             # In reality: Serialize self.environment_state (handle TraceInfo objects) and save to file
             # with self._lock: save_to_file(self.environment_state, self.persistence_path)

    def deposit_trace(self, location: Location, trace_type: TraceType, intensity: float = 1.0, agent_id: Optional[str] = None, data: Optional[Dict] = None, mode: Literal['set', 'add', 'max'] = 'add'):
        """
        An agent deposits or reinforces a trace at a specific location.

        Args:
            location (Location): The location (e.g., coordinates) in the environment.
            trace_type (TraceType): The type/meaning of the trace.
            intensity (float): The strength to add or set for the trace. Must be positive.
            agent_id (Optional[str]): ID of the agent depositing the trace.
            data (Optional[Dict]): Optional dictionary for extra data associated with the trace.
            mode (Literal['set', 'add', 'max']): How to update intensity if trace exists:
                - 'set': Overwrite with new intensity.
                - 'add': Add to existing intensity.
                - 'max': Set to max(existing_intensity, new_intensity).
        """
        if intensity <= 0:
             logger.warning(f"Ignoring attempt to deposit trace '{trace_type}' at {location} with non-positive intensity {intensity}.")
             return

        with self._lock:
            current_time = time.monotonic()
            location_traces = self.environment_state[location] # defaultdict ensures location exists
            existing_trace = location_traces.get(trace_type)

            new_intensity = intensity
            if existing_trace:
                if mode == 'add':
                    new_intensity = existing_trace.intensity + intensity
                elif mode == 'max':
                    new_intensity = max(existing_trace.intensity, intensity)
                # elif mode == 'set': new_intensity remains as the input intensity

            # Cap intensity? Optional based on application needs (e.g., max pheromone level)
            # new_intensity = min(new_intensity, MAX_INTENSITY_PER_TYPE.get(trace_type, 100.0))

            trace_info = TraceInfo(
                intensity=new_intensity,
                timestamp=current_time,
                agent_id=agent_id,
                data=data
            )
            location_traces[trace_type] = trace_info
            logger.debug(f"Trace '{trace_type}' deposited/updated at {location}. Intensity: {new_intensity:.2f}, Mode: {mode}")

            # Conceptual: Trigger save state periodically or based on change volume?
            # self._save_state() # Saving on every deposit might be inefficient

    def read_traces_at(self, location: Location) -> Dict[TraceType, TraceInfo]:
        """
        Reads all traces currently present at a specific location.

        Args:
            location (Location): The location to query.

        Returns:
            Dict[TraceType, TraceInfo]: A dictionary of traces at the location.
                                        Returns empty dict if no traces found.
                                        Returns copies to prevent external modification.
        """
        with self._lock:
            # Return a copy to prevent modification of internal state
            traces = self.environment_state.get(location)
            return {ttype: dataclasses.replace(tinfo) for ttype, tinfo in traces.items()} if traces else {}

    def read_traces_nearby(self, location: Location, radius: float) -> Dict[TraceType, List[Tuple[Location, TraceInfo]]]:
        """
        Reads traces within a certain radius of a location.
        *** Placeholder: Assumes a simple grid and Manhattan distance for now. ***
        Requires efficient spatial indexing for large environments.

        Args:
            location (Location): The center location (e.g., (x,y)).
            radius (float): The search radius.

        Returns:
            Dict[TraceType, List[Tuple[Location, TraceInfo]]]: Traces grouped by type, each entry is (location, trace_info).
        """
        logger.debug(f"Reading traces nearby {location} within radius {radius} (Conceptual)...")
        nearby_traces = defaultdict(list)
        if not isinstance(location, tuple) or len(location) < 2:
             logger.warning("Nearby search requires tuple location (e.g., (x,y)).")
             return dict(nearby_traces) # Return empty

        # --- Placeholder: Spatial Query ---
        # Iterate through self.environment_state (inefficient for large state!)
        # Or use a spatial index (k-d tree, quadtree) if implemented.
        with self._lock:
            for loc, traces in self.environment_state.items():
                 if not isinstance(loc, tuple) or len(loc) < len(location): continue
                 # Simple Manhattan distance for example (assumes grid-like locations)
                 distance = sum(abs(l1 - l2) for l1, l2 in zip(location, loc))
                 if distance <= radius:
                     for trace_type, trace_info in traces.items():
                         # Return copies
                          nearby_traces[trace_type].append((loc, dataclasses.replace(trace_info)))
        # --- End Placeholder ---
        logger.debug(f"Found nearby traces for types: {list(nearby_traces.keys())}")
        return dict(nearby_traces)


    def _decay_step(self):
        """Performs a single decay pass over all traces."""
        with self._lock:
            current_time = time.monotonic()
            locations_to_delete = []
            traces_to_delete: List[Tuple[Location, TraceType]] = []
            min_intensity_threshold = 0.01 # Remove traces with very low intensity

            for location, traces in self.environment_state.items():
                 for trace_type, trace_info in traces.items():
                     time_elapsed = current_time - trace_info.timestamp
                     # Exponential decay: intensity *= (1 - decay_rate) ^ time_elapsed (approx by rate * time for small steps)
                     # Or simpler linear decay: intensity -= decay_rate * time_elapsed
                     # Using exponential decay factor per second: decay_factor = math.exp(-self.decay_rate * time_elapsed)
                     # Or simpler approximation for discrete steps: decay = intensity * self.decay_rate * time_elapsed? Be careful rate isn't > 1/interval
                     # Let's use simple multiplicative decay based on interval rate
                     decay_multiplier = math.exp(-self.decay_rate * time_elapsed) # Factor per second
                     # Update intensity (only if decay rate > 0)
                     if self.decay_rate > 0:
                          trace_info.intensity *= decay_multiplier
                     trace_info.timestamp = current_time # Reset timestamp even if no decay

                     if trace_info.intensity < min_intensity_threshold:
                         traces_to_delete.append((location, trace_type))

            # Remove decayed traces
            if traces_to_delete:
                logger.debug(f"Decaying {len(traces_to_delete)} traces below threshold...")
                for loc, ttype in traces_to_delete:
                    if loc in self.environment_state and ttype in self.environment_state[loc]:
                         del self.environment_state[loc][ttype]
                    # Check if location is now empty
                    if loc in self.environment_state and not self.environment_state[loc]:
                         locations_to_delete.append(loc)

            # Remove empty locations
            if locations_to_delete:
                 logger.debug(f"Removing {len(locations_to_delete)} empty locations...")
                 for loc in locations_to_delete:
                      if loc in self.environment_state: # Check again inside lock
                           del self.environment_state[loc]

            # logger.debug("Decay step finished.")


    def _decay_loop(self):
        """Background thread function to periodically decay traces."""
        logger.info("Starting background decay thread...")
        while not self._stop_decay_event.wait(self.decay_interval):
            # logger.debug("Running periodic decay step...")
            try:
                self._decay_step()
            except Exception as e:
                 logger.error(f"Error during background decay step: {e}")
            # Optional: Persist state periodically from decay thread?
            # self._save_state()
        logger.info("Background decay thread stopped.")

    def _start_decay_thread(self):
        """Starts the background decay process if not already running."""
        if self._decay_thread is None or not self._decay_thread.is_alive():
             self._stop_decay_event.clear()
             self._decay_thread = threading.Thread(target=self._decay_loop, daemon=True) # Daemon thread exits with main app
             self._decay_thread.start()
        else:
             logger.warning("Decay thread already running.")

    def stop_decay_thread(self):
        """Signals the background decay thread to stop."""
        if self._decay_thread and self._decay_thread.is_alive():
            logger.info("Stopping background decay thread...")
            self._stop_decay_event.set()
            self._decay_thread.join(timeout=self.decay_interval * 2) # Wait for thread to exit
            if self._decay_thread.is_alive():
                 logger.warning("Decay thread did not stop gracefully.")
            self._decay_thread = None
        else:
             logger.info("Decay thread not running.")

    def __del__(self):
        # Ensure decay thread is stopped when object is garbage collected
        self.stop_decay_thread()
        # Optional: Save state on exit?
        # self._save_state()


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Stigmergy Engine Example ---")

    # Initialize engine with decay
    engine = StigmergyEngine(default_decay_rate=0.1, decay_interval_sec=1.0) # 10% decay per second

    # Define some locations (simple 2D grid)
    loc1: Location = (10, 5)
    loc2: Location = (11, 5)
    loc3: Location = (10, 6)

    # Agent 1 deposits food trace
    print(f"\nAgent 1 deposits 'food' at {loc1}")
    engine.deposit_trace(loc1, "food", intensity=5.0, agent_id="agent_1", mode='set')

    # Agent 2 deposits path trace
    print(f"Agent 2 deposits 'path' at {loc1} and {loc2}")
    engine.deposit_trace(loc1, "path", intensity=1.0, agent_id="agent_2", mode='add')
    engine.deposit_trace(loc2, "path", intensity=1.0, agent_id="agent_2", mode='set')

    # Read traces at loc1
    print(f"\nTraces at {loc1}:")
    traces_at_loc1 = engine.read_traces_at(loc1)
    print(json.dumps({k:asdict(v) for k,v in traces_at_loc1.items()}, indent=2, default=str))

    # Read traces nearby loc1 (conceptual radius)
    print(f"\nTraces nearby {loc1} (radius 1):")
    nearby = engine.read_traces_nearby(loc1, radius=1.0) # Will find loc1, loc2, loc3 conceptually
    print(json.dumps({k:[asdict(t[1]) for t in v] for k,v in nearby.items()}, indent=2, default=str)) # Print only trace info for brevity

    # Wait for decay to occur
    wait_seconds = 3
    print(f"\nWaiting {wait_seconds} seconds for decay...")
    time.sleep(wait_seconds)
    # Manually trigger decay step for predictable results in example (usually runs in background)
    # engine._decay_step() # Call manually if thread timing is tricky for demo
    # Note: The background thread should handle decay, but call manually to show effect *now*.
    # For clean exit in __main__ without waiting for daemon, stop it.
    engine.stop_decay_thread() # Stop background thread before explicit step
    engine._decay_step() # Apply decay that occurred during sleep

    # Read traces at loc1 again
    print(f"\nTraces at {loc1} after decay:")
    traces_at_loc1_after = engine.read_traces_at(loc1)
    print(json.dumps({k:asdict(v) for k,v in traces_at_loc1_after.items()}, indent=2, default=str))
    # Expected: Intensities should be lower due to decay_rate=0.1 over ~3 seconds

    # Stop the decay thread explicitly if it was started (important for clean exit if not daemon)
    # engine.stop_decay_thread() # Already stopped above for manual step

    print("\n--- End Example ---")
