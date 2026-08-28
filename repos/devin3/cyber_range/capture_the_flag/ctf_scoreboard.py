# Devin/cyber_range/capture_the_flag/ctf_scoreboard.py
# Purpose: Tracks player scores, rankings, and potentially solved challenges in the CTF.

import os
import json
import datetime
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Data Structures ---

@dataclass
class PlayerScore:
    """Represents the score and progress of a single player/user."""
    user_id: str
    display_name: str # Optional: Could be fetched from a user profile system
    total_score: int = 0
    # Dictionary mapping solved challenge IDs to UTC ISO timestamp strings
    solved_challenges: Dict[str, str] = field(default_factory=dict)
    last_solve_timestamp: Optional[str] = None # For tie-breaking

    def record_solve(self, challenge_id: str, points: int, timestamp: str):
        """Updates score for a solved challenge, avoiding duplicates."""
        if challenge_id not in self.solved_challenges:
            self.solved_challenges[challenge_id] = timestamp
            self.total_score += points
            self.last_solve_timestamp = timestamp
            logger.info(f"Recorded solve for user '{self.user_id}', challenge '{challenge_id}', points {points}.")
            return True
        else:
            logger.warning(f"User '{self.user_id}' already solved challenge '{challenge_id}'. No points added.")
            return False

# --- Scoreboard Manager ---

class CTFScoreboard:
    """
    Manages player scores and rankings for the CTF.

    Uses JSON file for persistence (Database recommended for production).
    """
    DEFAULT_STORAGE_PATH = "./data/ctf_scoreboard.json"

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initializes the CTFScoreboard.

        Args:
            storage_path (Optional[str]): Path to the JSON file for storing scores.
                                          Defaults to DEFAULT_STORAGE_PATH.
        """
        self.storage_path = storage_path or self.DEFAULT_STORAGE_PATH
        # Stores scores keyed by user_id: {user_id: PlayerScore}
        self.scores: Dict[str, PlayerScore] = {}
        self._load_scores()
        logger.info(f"CTFScoreboard initialized. Storage: '{self.storage_path}'")

    def _load_scores(self):
        """Loads scores from the persistent JSON file."""
        if not os.path.exists(self.storage_path):
            logger.info(f"Scoreboard file '{self.storage_path}' not found. Starting fresh.")
            self.scores = {}
            return
        try:
            with open(self.storage_path, 'r') as f:
                raw_data = json.load(f)
                # Deserialize back into PlayerScore objects
                self.scores = {uid: PlayerScore(**pdata) for uid, pdata in raw_data.items()}
            logger.info(f"Loaded scores for {len(self.scores)} players from '{self.storage_path}'.")
        except (IOError, json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to load or parse scoreboard from '{self.storage_path}': {e}. Resetting scores.")
            self.scores = {}

    def _save_scores(self):
        """Saves the current scores to the persistent JSON file."""
        # Note: Simple file write isn't safe under high concurrency. DB solves this.
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            # Serialize PlayerScore objects to dictionaries for JSON
            data_to_save = {uid: asdict(pscore) for uid, pscore in self.scores.items()}
            with open(self.storage_path, 'w') as f:
                json.dump(data_to_save, f, indent=2)
            # logger.debug(f"Saved scores for {len(self.scores)} players to '{self.storage_path}'.")
        except IOError as e:
            logger.error(f"Failed to save scoreboard to '{self.storage_path}': {e}")

    def record_solve(self, user_id: str, display_name: str, challenge_id: str, points: int):
        """
        Records a successful challenge solve for a user.

        Args:
            user_id (str): The unique identifier of the user.
            display_name (str): The user's display name (used if creating new entry).
            challenge_id (str): The unique identifier of the solved challenge.
            points (int): The points awarded for solving the challenge.
        """
        logger.info(f"Attempting to record solve: User='{user_id}', Challenge='{challenge_id}', Points={points}")
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Get existing player or create new one
        player_score = self.scores.get(user_id)
        if not player_score:
            logger.info(f"New player '{user_id}' ({display_name}) added to scoreboard.")
            player_score = PlayerScore(user_id=user_id, display_name=display_name)
            self.scores[user_id] = player_score

        # Update the player's score data
        solve_recorded = player_score.record_solve(challenge_id, points, timestamp)

        if solve_recorded:
            self._save_scores() # Persist the changes if a solve was actually recorded

    def get_score(self, user_id: str) -> Optional[PlayerScore]:
        """Retrieves the score details for a specific user."""
        logger.debug(f"Getting score for user: {user_id}")
        return self.scores.get(user_id)

    def get_scoreboard(self, limit: Optional[int] = None) -> List[PlayerScore]:
        """
        Retrieves the ranked scoreboard.

        Args:
            limit (Optional[int]): Limit the number of top players returned.

        Returns:
            List[PlayerScore]: A list of PlayerScore objects sorted by score (desc)
                               and then by last solve time (asc).
        """
        logger.info(f"Retrieving scoreboard (Limit: {limit})...")
        # Sort players: higher score first. If scores are equal, player who solved last earlier ranks higher.
        sorted_players = sorted(
            self.scores.values(),
            key=lambda p: (p.total_score, datetime.datetime.fromisoformat(p.last_solve_timestamp) if p.last_solve_timestamp else datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)),
            reverse=True # Sort by score descending first
        )

        if limit is not None and limit > 0:
            return sorted_players[:limit]
        else:
            return sorted_players

    def get_challenge_solvers(self, challenge_id: str) -> List[Tuple[str, str]]:
        """Finds users who have solved a specific challenge."""
        logger.info(f"Finding solvers for challenge: {challenge_id}")
        solvers = []
        for user_id, pscore in self.scores.items():
            if challenge_id in pscore.solved_challenges:
                solvers.append((user_id, pscore.solved_challenges[challenge_id])) # (user_id, solve_timestamp)

        # Sort by timestamp ascending
        solvers.sort(key=lambda x: datetime.datetime.fromisoformat(x[1]))
        logger.info(f"Found {len(solvers)} solvers for challenge {challenge_id}.")
        return solvers

    def reset_scoreboard(self):
        """Clears all scores and solved challenges."""
        logger.warning(f"Resetting CTF scoreboard stored at '{self.storage_path}'!")
        self.scores = {}
        self._save_scores()
        logger.info("Scoreboard has been reset.")

# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- CTF Scoreboard Example ---")

    # Use a temporary file for this example run
    temp_storage = "./temp_scoreboard.json"
    if os.path.exists(temp_storage): os.remove(temp_storage)

    scoreboard = CTFScoreboard(storage_path=temp_storage)

    # Record some solves
    scoreboard.record_solve(user_id="alice", display_name="Alice", challenge_id="CTF-WEB101", points=50)
    time.sleep(0.1) # Ensure timestamps differ slightly
    scoreboard.record_solve(user_id="bob", display_name="Bob", challenge_id="CTF-WEB101", points=50)
    time.sleep(0.1)
    scoreboard.record_solve(user_id="alice", display_name="Alice", challenge_id="CTF-PWN101", points=100)
    time.sleep(0.1)
    # Duplicate solve attempt for Alice on WEB101
    scoreboard.record_solve(user_id="alice", display_name="Alice", challenge_id="CTF-WEB101", points=50)

    # Get individual scores
    print("\nIndividual Scores:")
    alice_score = scoreboard.get_score("alice")
    bob_score = scoreboard.get_score("bob")
    print(f"Alice: {alice_score}")
    print(f"Bob: {bob_score}")

    # Get ranked scoreboard
    print("\nRanked Scoreboard:")
    ranked_list = scoreboard.get_scoreboard()
    for i, player in enumerate(ranked_list):
        print(f"  {i+1}. {player.display_name} ({player.user_id}) - Score: {player.total_score} (Last Solve: {player.last_solve_timestamp})")

    # Get solvers for a challenge
    print("\nSolvers for CTF-WEB101:")
    solvers = scoreboard.get_challenge_solvers("CTF-WEB101")
    for user, timestamp in solvers:
        print(f"  - User: {user}, Solved At: {timestamp}")

    # Test persistence
    print("\nReloading scoreboard to check persistence...")
    del scoreboard
    scoreboard_reloaded = CTFScoreboard(storage_path=temp_storage)
    reloaded_ranked = scoreboard_reloaded.get_scoreboard()
    print(f"Reloaded scoreboard has {len(reloaded_ranked)} players.")
    print(f"Top player score after reload: {reloaded_ranked[0].total_score if reloaded_ranked else 'N/A'}")

    # Reset
    # print("\nResetting scoreboard...")
    # scoreboard_reloaded.reset_scoreboard()
    # print(f"Scoreboard size after reset: {len(scoreboard_reloaded.get_scoreboard())}")


    # Clean up temp file
    if os.path.exists(temp_storage): os.remove(temp_storage)

    print("\n--- End Example ---")
