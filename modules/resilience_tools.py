# Devin/modules/resilience_tools.py
# Purpose: A high-level facade that orchestrates Devin's resilience toolkit --
#          digital twins, chaos-engineering experiments, filesystem
#          rollback/backup, and process-heartbeat monitoring -- into a
#          single, agent-friendly interface.

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Import the low-level resilience tools this facade will manage ---
# digital_twins/* and chaos_engineering/* have no optional third-party
# dependencies (pure stdlib), so their imports are not guarded. recovery/*
# is likewise pure stdlib (shutil/json/psutil, and psutil is already a hard
# Devin dependency) but we still guard every import here so a
# missing/renamed submodule can never take the facade (and, via main.py,
# the whole assistant) down with it.

try:
    from digital_twins.system_twin import SystemDigitalTwin
    _HAS_SYSTEM_TWIN_MOD = True
except ImportError:
    _HAS_SYSTEM_TWIN_MOD = False

try:
    from digital_twins.user_twin import UserDigitalTwin
    _HAS_USER_TWIN_MOD = True
except ImportError:
    _HAS_USER_TWIN_MOD = False

try:
    from chaos_engineering.latency_injector import LatencyInjector
    _HAS_LATENCY_MOD = True
except ImportError:
    _HAS_LATENCY_MOD = False

try:
    from chaos_engineering.network_partitioner import NetworkPartitioner
    _HAS_PARTITIONER_MOD = True
except ImportError:
    _HAS_PARTITIONER_MOD = False

try:
    from recovery.auto_rollback import AutoRollback
    _HAS_ROLLBACK_MOD = True
except ImportError:
    _HAS_ROLLBACK_MOD = False

try:
    from recovery.disaster_recovery import DisasterRecovery
    _HAS_DISASTER_RECOVERY_MOD = True
except ImportError:
    _HAS_DISASTER_RECOVERY_MOD = False

try:
    from recovery.heartbeat_monitor import HeartbeatManager, HeartbeatMonitor
    _HAS_HEARTBEAT_MOD = True
except ImportError:
    _HAS_HEARTBEAT_MOD = False

# NOTE: chaos_engineering/failure_recovery_test.py and
# recovery/dna_storage_recovery.py + recovery/quantum_self_repair/* are
# intentionally NOT wrapped here -- see the module docstring below and the
# task report for why.

# Configure basic logging
logger = logging.getLogger("ResilienceFacade")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False


class ResilienceFacade:
    """
    A single, simplified interface to Devin's resilience toolchain: digital
    twins (system + user state modeling), chaos-engineering experiments
    (SIMULATED latency/partition injection -- see warning below), filesystem
    snapshot/rollback, full backup/restore, and a process-heartbeat watchdog.

    Important safety notes:
      * LatencyInjector / NetworkPartitioner are entirely IN-PROCESS
        SIMULATIONS. Their `_run_chaos_command` never actually calls
        subprocess or any real chaos-engineering backend (that line is
        commented out in the source) -- it just sleeps briefly and returns
        a canned "success". They do NOT touch real host networking (no
        iptables, no network namespaces, nothing). They are safe to call
        freely and do not need `is_dangerous=True`.
      * AutoRollback, DisasterRecovery, and HeartbeatMonitor ARE real and
        DO touch the real filesystem / real OS processes (delete/overwrite
        files, move/restore backups, terminate and respawn processes).
        Their mutating methods should be registered `is_dangerous=True`.
        See each method's docstring for specifics.

    Every component degrades gracefully if its module can't be imported:
    it's disabled (logged as a warning) and its methods return None/False
    instead of raising.
    """

    def __init__(self):
        # --- Digital twins: managed as named collections, since twins are
        # inherently per-entity (per-system, per-user) rather than a single
        # global instance. ---
        self._system_twin_available = _HAS_SYSTEM_TWIN_MOD
        self.system_twins: Dict[str, "SystemDigitalTwin"] = {}
        if not self._system_twin_available:
            logger.warning("digital_twins.system_twin module not found; system twins disabled.")

        self._user_twin_available = _HAS_USER_TWIN_MOD
        self.user_twins: Dict[str, "UserDigitalTwin"] = {}
        if not self._user_twin_available:
            logger.warning("digital_twins.user_twin module not found; user twins disabled.")

        # --- Chaos engineering (simulated only -- see class docstring) ---
        self.latency_injector: Optional["LatencyInjector"] = None
        if _HAS_LATENCY_MOD:
            try:
                self.latency_injector = LatencyInjector()
            except Exception as e:
                logger.warning(f"Latency injector unavailable: {e}")
        else:
            logger.warning("chaos_engineering.latency_injector module not found; disabled.")

        self.network_partitioner: Optional["NetworkPartitioner"] = None
        if _HAS_PARTITIONER_MOD:
            try:
                self.network_partitioner = NetworkPartitioner()
            except Exception as e:
                logger.warning(f"Network partitioner unavailable: {e}")
        else:
            logger.warning("chaos_engineering.network_partitioner module not found; disabled.")

        # --- Filesystem rollback (real, DANGEROUS -- see method docstrings) ---
        # AutoRollback instances are opened per snapshot_dir, cached here.
        self._rollback_available = _HAS_ROLLBACK_MOD
        self._rollback_cache: Dict[str, "AutoRollback"] = {}
        if not self._rollback_available:
            logger.warning("recovery.auto_rollback module not found; snapshot/rollback disabled.")

        # --- Disaster recovery / full backups (real, DANGEROUS) ---
        self._disaster_recovery_available = _HAS_DISASTER_RECOVERY_MOD
        if not self._disaster_recovery_available:
            logger.warning("recovery.disaster_recovery module not found; backup/restore disabled.")

        # --- Process heartbeat watchdog (real, DANGEROUS -- kills/respawns
        # real OS processes). One shared watchdog instance per facade. ---
        self.heartbeat_monitor: Optional["HeartbeatMonitor"] = None
        self._heartbeat_manager: Optional["HeartbeatManager"] = None
        self._heartbeat_available = _HAS_HEARTBEAT_MOD
        if self._heartbeat_available:
            try:
                self.heartbeat_monitor = HeartbeatMonitor()
            except Exception as e:
                logger.warning(f"Heartbeat monitor unavailable: {e}")
        else:
            logger.warning("recovery.heartbeat_monitor module not found; watchdog disabled.")

        logger.info("ResilienceFacade initialized.")

    # ------------------------------------------------------------------
    # System digital twin
    # ------------------------------------------------------------------

    def create_system_twin(self, twin_id: str, initial_config: Dict[str, Any]) -> bool:
        """
        Creates a new virtual replica ("digital twin") of a system, tracking
        its static configuration and simulated dynamic state (CPU load,
        running services, security posture, etc.).

        Args:
            twin_id: Unique identifier for this twin.
            initial_config: Static configuration dict (os, cpu_cores,
                installed_software, known vulnerabilities, ...).

        Returns:
            True if the twin was created, False if unavailable/invalid.
        """
        if not self._system_twin_available:
            logger.error("System digital twin unavailable.")
            return False
        try:
            self.system_twins[twin_id] = SystemDigitalTwin(twin_id, initial_config)
            return True
        except Exception as e:
            logger.error(f"Failed to create system twin '{twin_id}': {e}")
            return False

    def get_system_twin_state(self, twin_id: str, key: Optional[str] = None) -> Optional[Any]:
        """Reads the current simulated dynamic state of a system twin (or one key of it)."""
        twin = self.system_twins.get(twin_id)
        if not twin:
            logger.error(f"System twin '{twin_id}' not found.")
            return None
        return twin.get_state(key)

    def update_system_twin_state(self, twin_id: str, state_changes: Dict[str, Any]) -> bool:
        """Applies state changes (e.g. simulated load/service changes) to a system twin."""
        twin = self.system_twins.get(twin_id)
        if not twin:
            logger.error(f"System twin '{twin_id}' not found.")
            return False
        twin.update_state(state_changes)
        return True

    def simulate_system_twin_event(self, twin_id: str, event_type: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Simulates an event (e.g. 'HIGH_LOAD_REQUEST', 'PATCH_APPLIED',
        'SERVICE_CRASH') affecting a system twin's state, using simple
        rule-based state changes -- useful for "what happens if..." analysis.
        """
        twin = self.system_twins.get(twin_id)
        if not twin:
            logger.error(f"System twin '{twin_id}' not found.")
            return None
        return twin.simulate_event(event_type, params)

    def check_system_twin_vulnerability(self, twin_id: str, cve_id: str) -> Optional[bool]:
        """Checks whether a CVE is listed against a system twin's configuration."""
        twin = self.system_twins.get(twin_id)
        if not twin:
            logger.error(f"System twin '{twin_id}' not found.")
            return None
        return twin.check_vulnerability(cve_id)

    # ------------------------------------------------------------------
    # User digital twin
    # ------------------------------------------------------------------

    def create_user_twin(
        self, user_id: str, profile_source: Optional[str] = None, log_source: Optional[str] = None
    ) -> bool:
        """
        Creates a digital twin for a user, loading their static profile
        (from a YAML file, if profile_source is given) and generating a
        summary of their interaction history.

        Args:
            user_id: Unique identifier for the user.
            profile_source: Optional path to a YAML file of user profiles.
            log_source: Optional path to interaction logs (used for the
                history-summary heuristics).

        Returns:
            True if the twin was created, False otherwise.
        """
        if not self._user_twin_available:
            logger.error("User digital twin unavailable.")
            return False
        try:
            kwargs: Dict[str, Any] = {}
            if profile_source is not None:
                kwargs["profile_source"] = profile_source
            if log_source is not None:
                kwargs["log_source"] = log_source
            self.user_twins[user_id] = UserDigitalTwin(user_id, **kwargs)
            return True
        except Exception as e:
            logger.error(f"Failed to create user twin '{user_id}': {e}")
            return False

    def get_user_twin_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Returns a combined summary (profile + history) of a user twin."""
        twin = self.user_twins.get(user_id)
        if not twin:
            logger.error(f"User twin '{user_id}' not found.")
            return None
        return twin.get_summary()

    def get_user_twin_preference(self, user_id: str, preference_key: str, default: Any = None) -> Any:
        """Reads a specific preference (e.g. 'theme') from a user twin's profile."""
        twin = self.user_twins.get(user_id)
        if not twin:
            logger.error(f"User twin '{user_id}' not found.")
            return default
        return twin.get_preference(preference_key, default)

    def predict_user_twin_next_action(self, user_id: str, current_task_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Heuristically predicts a user's likely next action given the current
        task context (a lightweight, rule-of-thumb estimate -- not a trained
        ML model).
        """
        twin = self.user_twins.get(user_id)
        if not twin:
            logger.error(f"User twin '{user_id}' not found.")
            return None
        return twin.predict_next_action(current_task_context)

    # ------------------------------------------------------------------
    # Chaos engineering (SIMULATED -- no real network manipulation; see
    # class docstring above)
    # ------------------------------------------------------------------

    def inject_latency(
        self,
        description: str,
        target_selector: Dict[str, str],
        latency_ms: int,
        jitter_ms: int = 0,
        duration_sec: Optional[int] = None,
    ) -> Optional[str]:
        """
        SIMULATES injecting network latency for traffic matching a target
        selector (state-tracking only -- no real traffic shaping occurs).

        Returns:
            A unique injection ID, or None on failure/if unavailable.
        """
        if not self.latency_injector:
            logger.error("Latency injector unavailable.")
            return None
        return self.latency_injector.inject_latency(description, target_selector, latency_ms, jitter_ms, duration_sec=duration_sec)

    def restore_latency(self, injection_id: str) -> bool:
        """Ends a simulated latency injection experiment."""
        if not self.latency_injector:
            logger.error("Latency injector unavailable.")
            return False
        return self.latency_injector.restore_normal_latency(injection_id)

    def list_latency_injections(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """Lists currently active simulated latency injections."""
        if not self.latency_injector:
            return None
        return self.latency_injector.list_active_injections()

    def create_network_partition(
        self,
        description: str,
        source_selector: Dict[str, str],
        target_selector: Dict[str, str],
        direction: str = "both",
        duration_sec: Optional[int] = None,
    ) -> Optional[str]:
        """
        SIMULATES a network partition between two selectors (state-tracking
        only -- no real iptables/network-namespace manipulation occurs).

        Args:
            direction: One of 'to', 'from', 'both'.

        Returns:
            A unique partition ID, or None on failure/if unavailable.
        """
        if not self.network_partitioner:
            logger.error("Network partitioner unavailable.")
            return None
        return self.network_partitioner.create_partition(description, source_selector, target_selector, direction, duration_sec)

    def simulate_network_outage(
        self, description: str, target_selector: Dict[str, str], duration_sec: Optional[int] = None
    ) -> Optional[str]:
        """SIMULATES a complete network outage for a target selector (state-tracking only)."""
        if not self.network_partitioner:
            logger.error("Network partitioner unavailable.")
            return None
        return self.network_partitioner.simulate_outage(description, target_selector, duration_sec)

    def restore_network_connectivity(self, partition_id: str) -> bool:
        """Ends a simulated network partition/outage."""
        if not self.network_partitioner:
            logger.error("Network partitioner unavailable.")
            return False
        return self.network_partitioner.restore_connectivity(partition_id)

    def list_network_partitions(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """Lists currently active simulated network partitions/outages."""
        if not self.network_partitioner:
            return None
        return self.network_partitioner.list_active_partitions()

    # ------------------------------------------------------------------
    # Filesystem snapshot & rollback (REAL, DANGEROUS)
    # ------------------------------------------------------------------

    def create_snapshot(self, snapshot_dir: str, target_path: str, reason: str = "Pre-update snapshot") -> Optional[str]:
        """
        Creates a compressed archive snapshot of a real file or directory.
        Safe/non-destructive on its own (only reads the target and writes a
        new archive) -- the dangerous half of this pair is `rollback_to_snapshot`.

        Args:
            snapshot_dir: Directory where snapshot archives + manifest are kept.
            target_path: The real file or directory to snapshot.
            reason: Human-readable description of why this snapshot was taken.

        Returns:
            The snapshot ID, or None on failure/if unavailable.
        """
        if not self._rollback_available:
            logger.error("Filesystem rollback unavailable.")
            return None
        rollback = self._get_rollback(snapshot_dir)
        if not rollback:
            return None
        return rollback.create_snapshot(Path(target_path), reason)

    def rollback_to_snapshot(self, snapshot_dir: str, snapshot_id: str) -> bool:
        """
        DANGEROUS: Deletes the current file/directory at the snapshot's
        original path and replaces it with the contents of a prior
        snapshot. This is a real, destructive filesystem write -- register
        as `is_dangerous=True` and confirm with the user before calling.

        Args:
            snapshot_dir: Directory containing the snapshot archives + manifest.
            snapshot_id: The snapshot to revert to (from create_snapshot()).

        Returns:
            True on success, False on failure/if unavailable.
        """
        if not self._rollback_available:
            logger.error("Filesystem rollback unavailable.")
            return False
        rollback = self._get_rollback(snapshot_dir)
        if not rollback:
            return False
        return rollback.rollback(snapshot_id)

    def _get_rollback(self, snapshot_dir: str) -> Optional["AutoRollback"]:
        """Internal: lazily opens (and caches) an AutoRollback for a given snapshot directory."""
        if snapshot_dir in self._rollback_cache:
            return self._rollback_cache[snapshot_dir]
        try:
            rollback = AutoRollback(Path(snapshot_dir))
            self._rollback_cache[snapshot_dir] = rollback
            return rollback
        except Exception as e:
            logger.error(f"Cannot open rollback snapshot directory '{snapshot_dir}': {e}")
            return None

    # ------------------------------------------------------------------
    # Disaster recovery: full backup & restore (REAL, DANGEROUS)
    # ------------------------------------------------------------------

    def create_full_backup(self, config_path: str, backup_location: str, retention_days: int = 7) -> Optional[str]:
        """
        Creates a full, compressed backup of every path listed in the
        backup config file. Safe/non-destructive on its own (only reads
        source paths and writes a new archive, though it does prune backups
        older than `retention_days`) -- the dangerous half of this pair is
        `restore_from_backup`.

        Args:
            config_path: Path to a JSON file with a "paths_to_backup" list.
            backup_location: Directory where backup archives are stored.
            retention_days: Backups older than this are deleted automatically.

        Returns:
            The path to the new backup archive, or None on failure/if unavailable.
        """
        if not self._disaster_recovery_available:
            logger.error("Disaster recovery unavailable.")
            return None
        try:
            dr = DisasterRecovery(Path(config_path), Path(backup_location), retention_days)
            archive_path = dr.create_backup()
            return str(archive_path) if archive_path else None
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return None

    def restore_from_backup(
        self,
        config_path: str,
        backup_location: str,
        backup_archive: Optional[str] = None,
        retention_days: int = 7,
    ) -> bool:
        """
        DANGEROUS: Moves every path listed in the backup config to a
        quarantine directory and unpacks a backup archive over the
        application root. This is a real, destructive filesystem operation
        that can overwrite current data -- register as `is_dangerous=True`
        and confirm with the user before calling.

        Args:
            config_path: Path to a JSON file with a "paths_to_backup" list.
            backup_location: Directory where backup archives are stored.
            backup_archive: Specific archive to restore; if None, the
                newest backup in backup_location is used.
            retention_days: Passed through to the DisasterRecovery instance
                (only affects future create_full_backup calls).

        Returns:
            True on success, False on failure/if unavailable.
        """
        if not self._disaster_recovery_available:
            logger.error("Disaster recovery unavailable.")
            return False
        try:
            dr = DisasterRecovery(Path(config_path), Path(backup_location), retention_days)
            archive = Path(backup_archive) if backup_archive else None
            return dr.restore_from_backup(archive)
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Process heartbeat watchdog (REAL, DANGEROUS)
    # ------------------------------------------------------------------

    def register_monitored_process(self, name: str, command: List[str], heartbeat_file: str) -> bool:
        """
        DANGEROUS: Registers a process with the watchdog. Once monitoring is
        started (`start_process_watchdog`), if this process's heartbeat file
        goes stale the watchdog will terminate its old PID (if any) and
        spawn a brand-new OS process by executing `command` -- register as
        `is_dangerous=True` since it defines what gets force-killed and
        re-executed, and confirm with the user before calling.

        Args:
            name: A unique name for this monitored process.
            command: The full command line used to (re)start the process.
            heartbeat_file: Path the process is expected to periodically
                touch (see start_heartbeat_reporter) to prove it's alive.
        """
        if not self.heartbeat_monitor:
            logger.error("Heartbeat watchdog unavailable.")
            return False
        self.heartbeat_monitor.register_process(name, command, Path(heartbeat_file))
        return True

    def start_process_watchdog(self, check_interval_sec: int = 10, stale_threshold_sec: int = 30) -> bool:
        """
        DANGEROUS: Starts the watchdog's background monitoring thread. From
        this point on, any registered process whose heartbeat file goes
        stale will have its old PID terminated and a new one spawned
        automatically -- register as `is_dangerous=True` and confirm with
        the user before calling.
        """
        if not self.heartbeat_monitor:
            logger.error("Heartbeat watchdog unavailable.")
            return False
        try:
            self.heartbeat_monitor.check_interval = check_interval_sec
            self.heartbeat_monitor.stale_threshold = stale_threshold_sec
            self.heartbeat_monitor.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start heartbeat watchdog: {e}")
            return False

    def stop_process_watchdog(self) -> bool:
        """Stops the watchdog's background monitoring thread (safe -- does not touch monitored processes)."""
        if not self.heartbeat_monitor:
            logger.error("Heartbeat watchdog unavailable.")
            return False
        self.heartbeat_monitor.stop()
        return True

    def list_monitored_processes(self) -> Optional[List[str]]:
        """Lists the names of all processes currently registered with the watchdog."""
        if not self.heartbeat_monitor:
            return None
        return list(self.heartbeat_monitor.monitored_processes.keys())

    def start_heartbeat_reporter(self, heartbeat_file: str, interval_sec: int = 5) -> bool:
        """
        Starts a background thread that periodically "touches" a heartbeat
        file -- meant to be called by the process BEING monitored (proving
        it's still alive to a HeartbeatMonitor watching that file), not by
        the watchdog itself. Safe: only touches one local file.
        """
        if not self._heartbeat_available:
            logger.error("Heartbeat reporter unavailable.")
            return False
        try:
            self._heartbeat_manager = HeartbeatManager(Path(heartbeat_file), interval_sec)
            self._heartbeat_manager.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start heartbeat reporter: {e}")
            return False

    def stop_heartbeat_reporter(self) -> bool:
        """Stops this process's own heartbeat-reporting thread, if one was started."""
        if not self._heartbeat_manager:
            logger.error("No heartbeat reporter is running.")
            return False
        self._heartbeat_manager.stop()
        return True


# --- Example Usage ---
if __name__ == "__main__":
    import json

    print("=========================================================")
    print("=== Resilience Facade Demo ===")
    print("=========================================================")

    facade = ResilienceFacade()

    print("\n--- System digital twin ---")
    facade.create_system_twin("web-01", {"type": "web_server", "vulnerabilities": ["CVE-2021-XXXX"]})
    print("Initial state:", facade.get_system_twin_state("web-01"))
    print("Event result:", facade.simulate_system_twin_event("web-01", "HIGH_LOAD_REQUEST", {}))

    print("\n--- Simulated chaos engineering ---")
    inj_id = facade.inject_latency("demo", {"app": "payments"}, latency_ms=100, duration_sec=60)
    print("Injection ID:", inj_id, "| Active:", facade.list_latency_injections())
    if inj_id:
        facade.restore_latency(inj_id)

    print("\n=========================================================")
    print("=== Resilience Facade Demo Complete ===")
    print("=========================================================")
