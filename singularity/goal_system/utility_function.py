# Devin/singularity/goal_system/utility_function.py
# Purpose: Defines the core decision-making engine for the AGI, providing a
#          formal utility function to evaluate and select the best plan of action.

import logging
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

try:
    # --- Integration with other Devin modules ---
    from modules.all_ais_modules import AIAgent, AIProvider
    from security.security_dashboard import SecurityDashboard, AlertLevel
    # Define a placeholder for a Plan object
    @dataclass
    class Plan:
        steps: List[Dict[str, Any]] # e.g., [{"tool": "execute_shell", "command": "ls -l"}]
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("UtilityFunction")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
logger.propagate = False

@dataclass
class EvaluationResult:
    """Holds the detailed results of a utility function evaluation."""
    total_utility: float
    plan: Plan
    component_scores: Dict[str, float] = field(default_factory=dict)

# --- Abstract Base Class for all Utility Components ---
class UtilityComponent(ABC):
    """An abstract component of the main utility function."""
    def __init__(self, weight: float):
        if not (0.0 <= weight <= 1.0):
            raise ValueError("Component weight must be between 0.0 and 1.0")
        self.weight = weight

    @abstractmethod
    def evaluate(self, plan: Plan, user_goal: str, constraints: List[str]) -> float:
        """
        Evaluates a plan and returns a score between -1.0 (worst) and 1.0 (best).
        A component can return a very large negative number to effectively veto a plan.
        """
        pass

# --- Concrete Implementations of Utility Components ---

class TaskCompletionComponent(UtilityComponent):
    """Evaluates how well a plan achieves the user's stated goal."""
    def __init__(self, weight: float, ai_agent: AIAgent):
        super().__init__(weight)
        self.ai_agent = ai_agent

    def evaluate(self, plan: Plan, user_goal: str, constraints: List[str]) -> float:
        if self.ai_agent.mode == 'mock':
            logger.info("TaskCompletionComponent: Running in mock mode. Returning default score.")
            return 1.0 # Return a default high score in mock mode; no real LLM to ask.

        plan_steps_str = "\n".join([f"- {step['tool']}: {step.get('command') or step.get('parameters')}" for step in plan.steps])
        prompt = (
            "You are a meticulous AI project manager. Evaluate the following plan based on how effectively it achieves the user's goal. "
            f"The high-level goal is: '{user_goal}'.\n\n"
            f"The proposed plan is:\n{plan_steps_str}\n\n"
            "Respond with a single floating-point number between -1.0 (completely irrelevant or counter-productive) "
            "and 1.0 (a perfect plan to achieve the goal). Your response must be ONLY the number."
        )
        try:
            # Hardcoding OPENAI here meant this always failed (and silently
            # scored every plan 0.0) whenever only another provider, e.g.
            # Claude, was configured. Use whichever tool-calling provider is
            # actually available, same preference as AIAgent's tool selection.
            provider = AIProvider.ANTHROPIC if self.ai_agent.claude_module else AIProvider.OPENAI
            response = self.ai_agent.get_general_chat_response([{"role": "user", "content": prompt}], provider=provider)
            return float(response.strip())
        except (ValueError, TypeError):
            logger.error("Could not parse LLM response for Task Completion evaluation.")
            return 0.0 # Neutral score on failure

class SafetyComponent(UtilityComponent):
    """Evaluates the safety of a plan, integrating with the Security Dashboard."""
    VETO_SCORE = -1000.0
    
    def __init__(self, weight: float, security_dashboard: SecurityDashboard):
        super().__init__(weight)
        self.dashboard = security_dashboard

    def evaluate(self, plan: Plan, user_goal: str, constraints: List[str]) -> float:
        for step in plan.steps:
            if step.get("tool") == "execute_shell":
                command = step.get("command", "")
                # Use the dashboard to check the command
                alert = self.dashboard.check_command(command)
                if alert and alert.level in [AlertLevel.CRITICAL, AlertLevel.HIGH]:
                    logger.critical(f"SAFETY VETO: Plan contains dangerous command '{command}'. Reason: {alert.reason}")
                    return self.VETO_SCORE
        return 1.0 # Plan is safe

class EfficiencyComponent(UtilityComponent):
    """Evaluates the efficiency of a plan (prefers shorter, simpler plans)."""
    def evaluate(self, plan: Plan, user_goal: str, constraints: List[str]) -> float:
        # Penalize plans for being too long. Normalize score based on a "reasonable" length.
        num_steps = len(plan.steps)
        # Score is 1.0 for 1 step, and decays to 0.0 for 20 steps.
        score = max(0.0, 1.0 - (num_steps / 20.0))
        return score

class ConstraintAdherenceComponent(UtilityComponent):
    """Evaluates whether the plan violates any user-defined constraints."""
    VETO_SCORE = -1000.0
    
    def evaluate(self, plan: Plan, user_goal: str, constraints: List[str]) -> float:
        plan_str = json.dumps(plan.steps)
        for constraint in constraints:
            # Simple check: does the plan mention a forbidden keyword?
            if constraint.lower() in plan_str.lower():
                logger.critical(f"CONSTRAINT VETO: Plan violates user constraint: '{constraint}'")
                return self.VETO_SCORE
        return 1.0 # No constraints violated

# --- The Main Utility Function Class ---

class UtilityFunction:
    """The core decision-making engine that aggregates scores from all components."""
    def __init__(self, components: Dict[str, UtilityComponent]):
        self.components = components
        # Normalize weights to ensure they sum to 1.0
        total_weight = sum(c.weight for c in components.values())
        if total_weight > 0:
            for c in self.components.values():
                c.weight /= total_weight
        logger.info("UtilityFunction initialized with weighted components.")

    def evaluate_plan(self, plan: Plan, user_goal: str, constraints: List[str]) -> EvaluationResult:
        """Evaluates a plan and returns a detailed result."""
        total_utility = 0.0
        component_scores = {}
        
        for name, component in self.components.items():
            raw_score = component.evaluate(plan, user_goal, constraints)
            
            # Handle veto scores
            if raw_score <= -1000.0:
                return EvaluationResult(total_utility=raw_score, component_scores={name: raw_score}, plan=plan)

            weighted_score = raw_score * component.weight
            component_scores[name] = weighted_score
            total_utility += weighted_score
            
        return EvaluationResult(total_utility=total_utility, component_scores=component_scores, plan=plan)

# --- Example Usage ---
if __name__ == "__main__":
    import os
    print("=========================================================")
    print("=== AGI Utility Function (Value Alignment) Demo 🧠 ===")
    print("=========================================================")

    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module is missing: {_import_error}")
    else:
        # --- 1. Setup Dependencies for the Demo ---
        # In a real run, these would be the live, fully configured modules.
        agent = AIAgent(openai_api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
        dashboard = SecurityDashboard()
        
        if not agent:
            print("WARNING: OPENAI_API_KEY not set. Task completion scores will be 0.0")
            # Create a mock agent for the demo to run
            class MockAgent:
                def get_general_chat_response(*args, **kwargs): return "0.8"
            agent = MockAgent()
            
        # --- 2. Define the AGI's Value System ---
        # Weights determine the AGI's priorities. Here, safety is paramount.
        utility_components = {
            "TaskCompletion": TaskCompletionComponent(weight=0.6, ai_agent=agent),
            "Safety": SafetyComponent(weight=1.0, security_dashboard=dashboard), # Highest weight
            "Efficiency": EfficiencyComponent(weight=0.2),
            "ConstraintAdherence": ConstraintAdherenceComponent(weight=1.0),
        }
        utility_function = UtilityFunction(components=utility_components)

        # --- 3. Define Scenarios ---
        user_goal = "Refactor the database connection logic in 'db.py' to use a connection pool."
        user_constraints = ["do not use the 'os' module"]

        plan_good = Plan(steps=[
            {"tool": "read_file", "parameters": {"path": "db.py"}},
            {"tool": "write_file", "parameters": {"path": "db.py", "content": "# New code with a connection pool..."}},
            {"tool": "execute_shell", "command": "python -m pytest tests/test_db.py"}
        ])

        plan_unsafe = Plan(steps=[
            {"tool": "read_file", "parameters": {"path": "db.py"}},
            {"tool": "execute_shell", "command": "rm -rf / --no-preserve-root"} # Extremely dangerous
        ])
        
        plan_violates_constraint = Plan(steps=[
            {"tool": "write_file", "parameters": {"path": "bootstrap.py", "content": "import os; os.system('...') "}},
        ])

        scenarios = {
            "Good Plan (Safe, Efficient, On-Topic)": plan_good,
            "Unsafe Plan (Should be Vetoed)": plan_unsafe,
            "Constraint Violating Plan (Should be Vetoed)": plan_violates_constraint,
        }

        # --- 4. Evaluate Each Plan ---
        for name, plan in scenarios.items():
            print(f"\n\n--- Evaluating: {name} ---")
            result = utility_function.evaluate_plan(plan, user_goal, user_constraints)
            
            print(f"  FINAL UTILITY SCORE: {result.total_utility:.4f}")
            print("  Component Scores:")
            for comp_name, score in result.component_scores.items():
                print(f"    - {comp_name:<25}: {score:.4f}")
            
            if result.total_utility < 0:
                print("  DECISION: Plan REJECTED.")
            else:
                print("  DECISION: Plan is ACCEPTABLE.")

    print("\n=========================================================")
    print("=== Utility Function Demo Complete ===")
    print("=========================================================")
