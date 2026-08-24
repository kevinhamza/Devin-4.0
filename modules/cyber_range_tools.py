# Devin/modules/cyber_range_tools.py
# Purpose: A facade exposing the CTF and blue-team (defensive) portions of
#          the cyber_range/ authorized security-training sandbox as
#          agent-callable tools.
#
# Scope note: this deliberately wraps only the CTF challenge/scoreboard
# system and defensive blue-team tooling (SOC playbooks, threat hunting),
# all of which operate against dummy in-process resource/SIEM/EDR
# connectors by default -- nothing here reaches real infrastructure.
# cyber_range/red_team/, ai_red_team/, and cyber_battle_simulator/ (the
# ransomware simulator, autonomous "hacking agent" framework, and AI
# attack-orchestration commander) are intentionally NOT wired here.

import logging
from typing import Any, Dict, List, Optional

try:
    from cyber_range.capture_the_flag.ctf_challenges import CTFChallengeManager
    CTF_AVAILABLE = True
except Exception as e:
    CTF_AVAILABLE = False
    _ctf_import_error = e

try:
    from cyber_range.capture_the_flag.ctf_scoreboard import CTFScoreboard
    SCOREBOARD_AVAILABLE = True
except Exception as e:
    SCOREBOARD_AVAILABLE = False
    _scoreboard_import_error = e

try:
    from cyber_range.blue_team.soc_playbooks import SOCPlaybookManager
    SOC_AVAILABLE = True
except Exception as e:
    SOC_AVAILABLE = False
    _soc_import_error = e

try:
    from cyber_range.blue_team.threat_hunting import ThreatHuntingManager
    HUNTING_AVAILABLE = True
except Exception as e:
    HUNTING_AVAILABLE = False
    _hunting_import_error = e

logger = logging.getLogger("CyberRangeFacade")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False


class CyberRangeFacade:
    """A single interface to the CTF training sandbox and defensive (blue-team) simulation tools."""

    def __init__(self):
        self.ctf: Optional["CTFChallengeManager"] = None
        if CTF_AVAILABLE:
            try:
                self.ctf = CTFChallengeManager()
            except Exception as e:
                logger.warning(f"CTF challenge manager unavailable: {e}")
        else:
            logger.warning(f"CTF challenge manager unavailable: {_ctf_import_error}")

        self.scoreboard: Optional["CTFScoreboard"] = None
        if SCOREBOARD_AVAILABLE:
            try:
                self.scoreboard = CTFScoreboard()
            except Exception as e:
                logger.warning(f"CTF scoreboard unavailable: {e}")
        else:
            logger.warning(f"CTF scoreboard unavailable: {_scoreboard_import_error}")

        self.soc: Optional["SOCPlaybookManager"] = None
        if SOC_AVAILABLE:
            try:
                self.soc = SOCPlaybookManager()
            except Exception as e:
                logger.warning(f"SOC playbook manager unavailable: {e}")
        else:
            logger.warning(f"SOC playbook manager unavailable: {_soc_import_error}")

        self.threat_hunting: Optional["ThreatHuntingManager"] = None
        if HUNTING_AVAILABLE:
            try:
                self.threat_hunting = ThreatHuntingManager()
            except Exception as e:
                logger.warning(f"Threat hunting manager unavailable: {e}")
        else:
            logger.warning(f"Threat hunting manager unavailable: {_hunting_import_error}")

        logger.info("CyberRangeFacade initialized.")

    def ctf_list_challenges(self) -> List[Dict[str, Any]]:
        """Lists available CTF training challenges in the sandbox."""
        if not self.ctf:
            return [{"error": "CTF challenge manager is not available."}]
        return self.ctf.list_challenges()

    def ctf_start_challenge(self, challenge_id: str) -> Dict[str, Any]:
        """Starts (provisions) a CTF challenge instance in the training sandbox."""
        if not self.ctf:
            return {"error": "CTF challenge manager is not available."}
        return self.ctf.start_challenge(challenge_id) or {"error": "Failed to start challenge."}

    def ctf_stop_challenge(self, challenge_id: str) -> Dict[str, Any]:
        """Stops (deprovisions) a running CTF challenge instance."""
        if not self.ctf:
            return {"error": "CTF challenge manager is not available."}
        return {"stopped": self.ctf.stop_challenge(challenge_id)}

    def ctf_submit_flag(self, challenge_id: str, submitted_flag: str, user_id: str = "default_user") -> Dict[str, Any]:
        """Submits a flag for a CTF challenge and records the result on the scoreboard if correct."""
        if not self.ctf:
            return {"error": "CTF challenge manager is not available."}
        return {"correct": self.ctf.submit_flag(challenge_id, submitted_flag, user_id)}

    def ctf_get_scoreboard(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Gets the current CTF scoreboard, ranked by points."""
        if not self.scoreboard:
            return [{"error": "CTF scoreboard is not available."}]
        return [s.__dict__ for s in self.scoreboard.get_scoreboard(limit)]

    def soc_list_playbooks(self) -> List[Dict[str, Any]]:
        """Lists available SOC (Security Operations Center) defensive response playbooks."""
        if not self.soc:
            return [{"error": "SOC playbook manager is not available."}]
        return self.soc.list_playbooks()

    def soc_trigger_playbook(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Triggers a matching SOC defensive playbook in the training sandbox for a given (simulated) alert."""
        if not self.soc:
            return {"error": "SOC playbook manager is not available."}
        instance_id = self.soc.trigger_playbook(alert_data)
        return {"execution_instance_id": instance_id} if instance_id else {"error": "No matching playbook found."}

    def threat_hunting_list_hunts(self) -> List[Dict[str, Any]]:
        """Lists defined threat-hunting queries/hypotheses available in the training sandbox."""
        if not self.threat_hunting:
            return [{"error": "Threat hunting manager is not available."}]
        return self.threat_hunting.list_hunts()

    def threat_hunting_execute_hunt(self, hunt_id: str) -> Dict[str, Any]:
        """Executes a defined threat hunt against the (simulated) SIEM/EDR data in the training sandbox."""
        if not self.threat_hunting:
            return {"error": "Threat hunting manager is not available."}
        execution_id = self.threat_hunting.execute_hunt(hunt_id)
        return {"execution_id": execution_id} if execution_id else {"error": "Failed to execute hunt."}
