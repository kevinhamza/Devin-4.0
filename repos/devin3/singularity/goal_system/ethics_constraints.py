# Devin/singularity/goal_system/ethics_constraints.py
# Purpose: Defines a formal, programmable framework for the AGI's ethical
#          guardrails, ensuring all actions align with core safety principles.

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional

try:
    # --- Integration with other Devin modules ---
    from modules.all_ais_modules import AIAgent, AIProvider
    # Define a placeholder for a Plan object, matching the one in utility_function.py
    @dataclass
    class Plan:
        steps: List[Dict[str, Any]]
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("EthicalConstraints")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

class EthicalSeverity(Enum):
    """Defines the severity of an ethical constraint violation."""
    ADVISORY = 1  # A potential issue to be aware of.
    WARNING = 2   # A significant issue that should likely halt the plan.
    VETO = 3      # A critical violation that MUST halt the plan.

@dataclass
class Violation:
    """Represents a detected violation of an ethical constraint."""
    constraint: 'EthicalConstraint'
    details: str

class EthicalConstraint(ABC):
    """An abstract base class for defining a single ethical rule."""
    def __init__(self, name: str, description: str, severity: EthicalSeverity):
        self.name = name
        self.description = description
        self.severity = severity

    @abstractmethod
    def check(self, plan: Plan) -> Optional[Violation]:
        """
        Checks if a plan violates this constraint.

        Returns:
            A Violation object if the constraint is violated, otherwise None.
        """
        pass

# --- Concrete Implementations of Ethical Constraints ---

class DoNoHarmConstraint(EthicalConstraint):
    """Prevents the execution of destructive or irreversible commands."""
    def __init__(self):
        super().__init__(
            name="Do No Harm",
            description="Prevents actions that could cause irreversible damage to the system or data.",
            severity=EthicalSeverity.VETO
        )
        # Regex for dangerous shell commands
        self.dangerous_patterns = [
            r"^\s*rm\s+-rf\s+/\s*",            # rm -rf /
            r"mkfs\.",                        # Formatting a drive
            r":\(\)\{:|:&};:",                 # Fork bomb
        ]

    def check(self, plan: Plan) -> Optional[Violation]:
        for step in plan.steps:
            if step.get("tool") == "execute_shell":
                command = step.get("command", "").strip()
                for pattern in self.dangerous_patterns:
                    if re.search(pattern, command):
                        return Violation(self, f"Plan contains a highly destructive command: '{command}'")
        return None

class DataPrivacyConstraint(EthicalConstraint):
    """Prevents unauthorized access or transmission of sensitive data."""
    def __init__(self):
        super().__init__(
            name="Data Privacy",
            description="Restricts the access and transmission of files that may contain PII.",
            severity=EthicalSeverity.VETO
        )
        self.sensitive_keywords = ["password", "secret", "private_key", "credential", "ssn"]
    
    def check(self, plan: Plan) -> Optional[Violation]:
        for step in plan.steps:
            # Check for exfiltration of sensitive files
            if step.get("tool") in ["upload_file", "send_email_with_attachment"]:
                filepath = step.get("parameters", {}).get("path", "")
                if any(keyword in filepath.lower() for keyword in self.sensitive_keywords):
                    return Violation(self, f"Plan attempts to transmit a potentially sensitive file: '{filepath}'")
        return None

class HonestyAndTransparencyConstraint(EthicalConstraint):
    """Ensures the AGI's communications are not deceptive."""
    def __init__(self, ai_agent: AIAgent):
        super().__init__(
            name="Honesty and Transparency",
            description="Requires all generated communications to be truthful and not misleading.",
            severity=EthicalSeverity.WARNING
        )
        self.ai_agent = ai_agent

    def check(self, plan: Plan) -> Optional[Violation]:
        for step in plan.steps:
            if step.get("tool") == "send_email":
                body = step.get("parameters", {}).get("body", "")
                if not body: continue

                prompt = (
                    "You are an AI ethics auditor. Analyze the following text content intended for an email. "
                    "Determine if it is deceptive, manipulative, or misleading in any way. "
                    "Respond with 'CLEAR' if it is honest. If it is deceptive, respond with a brief "
                    f"explanation of why.\n\nText to analyze: \"{body}\""
                )
                response = self.ai_agent.get_general_chat_response([{"role": "user", "content": prompt}], provider=AIProvider.OPENAI)
                if "CLEAR" not in response.upper():
                    return Violation(self, f"LLM auditor flagged generated text as potentially deceptive. Reason: {response}")
        return None

# --- Main Constraint Management System ---

class ConstraintSet:
    """A collection of ethical constraints that can be checked against a plan."""
    def __init__(self, constraints: List[EthicalConstraint]):
        self.constraints = constraints
        logger.info(f"ConstraintSet initialized with {len(constraints)} ethical constraints.")

    def check_plan(self, plan: Plan) -> List[Violation]:
        """Checks a plan against all constraints in the set."""
        violations = []
        for constraint in self.constraints:
            violation = constraint.check(plan)
            if violation:
                violations.append(violation)
                logger.critical(f"ETHICAL VIOLATION ({violation.constraint.severity.name}): {violation.details}")
        return violations

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== AGI Ethical Constraint System Demo ⚖️ ===")
    print("=========================================================")
    
    if not DEVIN_CORE_AVAILABLE:
        print(f"\nERROR: A core Devin module is missing: {_import_error}")
    else:
        # --- 1. Setup Dependencies for the Demo ---
        class MockDeceptiveAgent:
            def get_general_chat_response(self, *args, **kwargs):
                # Simulate the LLM detecting deception
                return "This text is misleading because it implies a false sense of urgency."
        
        # --- 2. Define the AGI's Ethical Framework ---
        constraint_set = ConstraintSet(constraints=[
            DoNoHarmConstraint(),
            DataPrivacyConstraint(),
            HonestyAndTransparencyConstraint(ai_agent=MockDeceptiveAgent())
        ])

        # --- 3. Define Scenarios ---
        plan_safe = Plan(steps=[{"tool": "execute_shell", "command": "ls -l"}])
        plan_harmful = Plan(steps=[{"tool": "execute_shell", "command": "rm -rf /"}])
        plan_privacy_breach = Plan(steps=[{"tool": "upload_file", "parameters": {"path": "/home/user/.ssh/id_rsa_private_key"}}])
        plan_deceptive = Plan(steps=[{"tool": "send_email", "parameters": {"body": "Urgent action required: your account will be deleted unless you click here."}}])

        scenarios = {
            "Safe Plan": (plan_safe, 0),
            "Harmful Plan": (plan_harmful, 1),
            "Privacy Violating Plan": (plan_privacy_breach, 1),
            "Deceptive Plan": (plan_deceptive, 1)
        }
        
        # --- 4. Evaluate Each Plan ---
        for name, (plan, expected_violations) in scenarios.items():
            print(f"\n--- Checking: {name} ---")
            violations = constraint_set.check_plan(plan)
            
            if len(violations) == expected_violations:
                print(f"  [SUCCESS] Correctly found {len(violations)} violations.")
            else:
                print(f"  [FAILURE] Incorrectly found {len(violations)} violations (expected {expected_violations}).")
            
            for v in violations:
                print(f"    - Violated '{v.constraint.name}' ({v.constraint.severity.name}): {v.details}")
    
    print("\n=========================================================")
    print("=== Ethical Constraint Demo Complete ===")
    print("=========================================================")
