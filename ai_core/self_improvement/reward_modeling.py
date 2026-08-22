# Devin/ai_core/self_improvement/reward_modeling.py

from typing import Dict, Any, Optional, List

# Placeholder for Task definition (could import if structure allows)
class TaskOutcome(TypedDict):
    """Represents the outcome data needed to calculate reward."""
    task_id: str
    task_type: str
    success: bool # Did the task meet its defined success criteria?
    steps_taken: Optional[int]
    time_taken_sec: Optional[float]
    resource_usage: Optional[Dict[str, float]] # e.g., {'cpu': 0.8, 'memory_mb': 512}
    violated_constraints: Optional[List[str]] # List of safety/ethical rules violated
    user_feedback: Optional[Literal['positive', 'negative', 'neutral']]
    final_state: Optional[Any] # Representation of the state after the task
    goal_achieved_rating: Optional[float] # How well the final state matches the goal (0.0-1.0)


class RewardModel:
    """
    Calculates a reward signal based on the outcome of an AI's action or task.

    This reward signal is crucial for reinforcement learning and performance-based
    self-improvement. It quantifies how "good" an outcome was based on various factors.
    """

    def __init__(self,
                 completion_reward: float = 100.0,
                 failure_penalty: float = -100.0,
                 step_penalty_factor: float = -0.1, # Penalty per step
                 time_penalty_factor: float = -0.05, # Penalty per second
                 constraint_violation_penalty: float = -200.0, # Heavy penalty for violations
                 user_positive_feedback_bonus: float = 50.0,
                 user_negative_feedback_penalty: float = -75.0
                 ):
        """
        Initializes the RewardModel with configurable weights/factors.

        Args:
            completion_reward (float): Base reward for successfully completing the task.
            failure_penalty (float): Base penalty for failing the task.
            step_penalty_factor (float): Penalty applied per step taken.
            time_penalty_factor (float): Penalty applied per second taken.
            constraint_violation_penalty (float): Penalty for each constraint violated.
            user_positive_feedback_bonus (float): Bonus reward for positive user feedback.
            user_negative_feedback_penalty (float): Penalty for negative user feedback.
        """
        self.completion_reward = completion_reward
        self.failure_penalty = failure_penalty
        self.step_penalty_factor = step_penalty_factor
        self.time_penalty_factor = time_penalty_factor
        self.constraint_violation_penalty = constraint_violation_penalty
        self.user_positive_feedback_bonus = user_positive_feedback_bonus
        self.user_negative_feedback_penalty = user_negative_feedback_penalty
        print("RewardModel initialized with configured weights.")

    def _calculate_completion_reward(self, outcome: TaskOutcome) -> float:
        """Calculates reward/penalty based purely on task success/failure."""
        if outcome.get('success', False):
            # Optional: Scale reward by goal achievement rating if available
            goal_rating = outcome.get('goal_achieved_rating', 1.0) # Default to full reward if rating unavailable
            if goal_rating is None: goal_rating = 1.0 # Handle None case
            return self.completion_reward * max(0.0, min(1.0, goal_rating)) # Clamp rating
        else:
            return self.failure_penalty

    def _calculate_efficiency_penalty(self, outcome: TaskOutcome) -> float:
        """Calculates penalties based on resource usage (steps, time, etc.)."""
        penalty = 0.0
        if outcome.get('steps_taken') is not None:
            penalty += outcome['steps_taken'] * self.step_penalty_factor
        if outcome.get('time_taken_sec') is not None:
            penalty += outcome['time_taken_sec'] * self.time_penalty_factor

        # Placeholder for resource usage penalty (e.g., CPU, memory)
        # This would require defining expected/baseline usage or setting caps
        # Example:
        # if outcome.get('resource_usage'):
        #     cpu_penalty = max(0, outcome['resource_usage'].get('cpu', 0.0) - 1.0) * -10 # Penalize CPU > 100% avg
        #     mem_penalty = max(0, outcome['resource_usage'].get('memory_mb', 0.0) - 1024) * -0.01 # Penalize MB over 1GB
        #     penalty += cpu_penalty + mem_penalty

        return penalty

    def _calculate_safety_ethics_penalty(self, outcome: TaskOutcome) -> float:
        """Calculates penalties for violating defined safety or ethical constraints."""
        penalty = 0.0
        violations = outcome.get('violated_constraints', [])
        if violations:
            penalty = len(violations) * self.constraint_violation_penalty
            print(f"  - Safety/Ethics Penalty Applied: {penalty} for violations: {violations}")
        return penalty

    def _calculate_user_feedback_reward(self, outcome: TaskOutcome) -> float:
        """Calculates reward/penalty based on explicit user feedback."""
        feedback = outcome.get('user_feedback')
        if feedback == 'positive':
            return self.user_positive_feedback_bonus
        elif feedback == 'negative':
            return self.user_negative_feedback_penalty
        else: # 'neutral' or None
            return 0.0

    def calculate_reward(self, outcome: TaskOutcome) -> float:
        """
        Calculates the total reward for a given task outcome.

        Combines various reward components (completion, efficiency, safety, feedback).

        Args:
            outcome (TaskOutcome): Dictionary containing details about the task's result.

        Returns:
            float: The calculated scalar reward value.
        """
        print(f"\nCalculating reward for Task '{outcome.get('task_id', 'Unknown')}'...")

        # --- Calculate individual components ---
        completion_r = self._calculate_completion_reward(outcome)
        efficiency_p = self._calculate_efficiency_penalty(outcome)
        safety_p = self._calculate_safety_ethics_penalty(outcome)
        feedback_r = self._calculate_user_feedback_reward(outcome)

        # --- Combine components ---
        # Simple summation, could use more complex weighting or logic
        total_reward = completion_r + efficiency_p + safety_p + feedback_r

        print(f"  - Completion: {completion_r:.2f}")
        print(f"  - Efficiency Penalty: {efficiency_p:.2f}")
        print(f"  - Safety/Ethics Penalty: {safety_p:.2f}")
        print(f"  - User Feedback Bonus/Penalty: {feedback_r:.2f}")
        print(f"  - TOTAL REWARD: {total_reward:.2f}")

        return total_reward

# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Reward Modeling Example ---")

    reward_model = RewardModel()

    # Example 1: Successful, efficient task with positive feedback
    outcome1: TaskOutcome = {
        'task_id': 'task_001', 'task_type': 'file_management', 'success': True,
        'steps_taken': 5, 'time_taken_sec': 2.5, 'resource_usage': {'cpu': 0.1, 'memory_mb': 50},
        'violated_constraints': [], 'user_feedback': 'positive', 'goal_achieved_rating': 1.0
    }
    reward1 = reward_model.calculate_reward(outcome1)

    # Example 2: Failed task
    outcome2: TaskOutcome = {
        'task_id': 'task_002', 'task_type': 'web_navigation', 'success': False,
        'steps_taken': 15, 'time_taken_sec': 12.8, 'resource_usage': {'cpu': 0.3, 'memory_mb': 150},
        'violated_constraints': [], 'user_feedback': None, 'goal_achieved_rating': 0.0
    }
    reward2 = reward_model.calculate_reward(outcome2)

    # Example 3: Successful but inefficient task with constraint violation and negative feedback
    outcome3: TaskOutcome = {
        'task_id': 'task_003', 'task_type': 'pentest_scan', 'success': True,
        'steps_taken': 150, 'time_taken_sec': 300.0, 'resource_usage': {'cpu': 0.9, 'memory_mb': 1024},
        'violated_constraints': ['scan_outside_scope'], 'user_feedback': 'negative', 'goal_achieved_rating': 0.8 # Partially achieved goal despite violation
    }
    reward3 = reward_model.calculate_reward(outcome3)

    print("\nExample Rewards Calculated:")
    print(f"Outcome 1 (Success, Efficient, Positive FB): {reward1:.2f}")
    print(f"Outcome 2 (Failure): {reward2:.2f}")
    print(f"Outcome 3 (Success, Inefficient, Violation, Negative FB): {reward3:.2f}")

    print("--- End Example ---")
