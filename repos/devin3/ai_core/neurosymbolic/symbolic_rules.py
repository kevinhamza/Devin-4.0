# Devin/ai_core/neurosymbolic/symbolic_rules.py

from typing import Dict, Any, List, Callable, Optional, Set
import operator

# --- Data Structures for Rules ---

class Fact:
    """Represents a basic fact or piece of information."""
    def __init__(self, predicate: str, *args: Any):
        self.predicate = predicate.lower()
        self.args = args

    def __eq__(self, other):
        if not isinstance(other, Fact):
            return NotImplemented
        return self.predicate == other.predicate and self.args == other.args

    def __hash__(self):
        return hash((self.predicate, self.args))

    def __repr__(self):
        args_repr = ', '.join(map(repr, self.args))
        return f"Fact({self.predicate!r}, {args_repr})"

class Condition:
    """Represents a condition to be checked against facts."""
    def __init__(self, predicate: str, *args: Any, comparison_op: Optional[Callable] = None, value: Any = None, variable_map: Optional[Dict[str, int]] = None):
        """
        Initializes a condition. Can represent simple fact existence or comparisons.

        Args:
            predicate (str): The predicate of the fact to check.
            *args: Arguments of the fact, can include variables (strings starting with '?').
            comparison_op (Optional[Callable]): Operator for comparison (e.g., operator.gt, operator.eq).
                                                 If None, checks for fact existence matching predicate and args pattern.
            value (Any): The value to compare an argument against using comparison_op. Requires exactly one variable in args.
            variable_map (Optional[Dict[str, int]]): Maps variable names (e.g., '?x') to their argument index.
                                                     Auto-generated if None.
        """
        self.predicate = predicate.lower()
        self.args_pattern = args
        self.comparison_op = comparison_op
        self.comparison_value = value
        self.variable_map = variable_map or {arg: i for i, arg in enumerate(args) if isinstance(arg, str) and arg.startswith('?')}

        if comparison_op is not None and len(self.variable_map) != 1:
             raise ValueError("Comparison conditions require exactly one variable in the arguments pattern.")

    def check(self, facts: Set[Fact]) -> List[Dict[str, Any]]:
        """
        Checks the condition against a set of facts and returns variable bindings if met.

        Args:
            facts (Set[Fact]): The current set of known facts.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a valid variable binding
                                  that satisfies the condition. Empty list if condition not met.
                                  For simple existence checks, the dict might be empty if no vars.
                                  For comparisons, the variable binding is included.
        """
        matching_bindings = []
        for fact in facts:
            if fact.predicate == self.predicate and len(fact.args) == len(self.args_pattern):
                binding = {}
                match = True
                comparison_variable_value = None
                comparison_variable_name = None

                for i, pattern_arg in enumerate(self.args_pattern):
                    fact_arg = fact.args[i]
                    if isinstance(pattern_arg, str) and pattern_arg.startswith('?'):
                        var_name = pattern_arg
                        if var_name in binding and binding[var_name] != fact_arg:
                            match = False # Variable already bound to a different value
                            break
                        binding[var_name] = fact_arg
                        if self.comparison_op and var_name in self.variable_map:
                            comparison_variable_value = fact_arg
                            comparison_variable_name = var_name
                    elif pattern_arg != fact_arg:
                        match = False # Constant pattern doesn't match fact argument
                        break

                if match:
                    # Perform comparison if specified
                    if self.comparison_op is not None:
                         if comparison_variable_value is None:
                             # This shouldn't happen if validation is correct, but check anyway
                             match = False
                         else:
                             try:
                                 if not self.comparison_op(comparison_variable_value, self.comparison_value):
                                     match = False # Comparison failed
                             except TypeError:
                                 match = False # Cannot compare types

                    if match:
                        # If it's a comparison check, ensure the bound variable is returned
                        if comparison_variable_name:
                             matching_bindings.append({comparison_variable_name: comparison_variable_value})
                        else:
                             # For existence checks, return the full binding dict
                             matching_bindings.append(binding) # Add the binding that satisfied the condition
        return matching_bindings

    def __repr__(self):
        pattern_repr = ', '.join(map(repr, self.args_pattern))
        comp_repr = ""
        if self.comparison_op:
            op_name = getattr(self.comparison_op, '__name__', repr(self.comparison_op))
            comp_repr = f", comparison={op_name}(?, {self.comparison_value!r})"
        return f"Condition({self.predicate!r}, {pattern_repr}{comp_repr})"


class Rule:
    """Represents an IF-THEN rule."""
    def __init__(self, name: str, conditions: List[Condition], conclusion: Fact):
        """
        Initializes a rule.

        Args:
            name (str): A unique name for the rule.
            conditions (List[Condition]): A list of conditions that must ALL be met (AND).
            conclusion (Fact): The fact concluded if all conditions are met. Variables in the
                               conclusion must be bound by the conditions.
        """
        self.name = name
        self.conditions = conditions
        self.conclusion = conclusion
        # Basic validation: Check if conclusion variables are present in conditions
        conclusion_vars = {arg for arg in conclusion.args if isinstance(arg, str) and arg.startswith('?')}
        condition_vars = set()
        for cond in conditions:
            condition_vars.update(cond.variable_map.keys())
        if not conclusion_vars.issubset(condition_vars):
            raise ValueError(f"Rule '{name}': Conclusion variables {conclusion_vars - condition_vars} not bound in conditions.")

    def apply(self, facts: Set[Fact]) -> List[Fact]:
        """
        Applies the rule to a set of facts. If conditions are met, generates concluded facts.

        Args:
            facts (Set[Fact]): The current set of known facts.

        Returns:
            List[Fact]: A list of new facts concluded by this rule instance.
        """
        new_facts = []
        # This implements a simple joining of bindings across conditions
        # Starts with initial empty bindings, iteratively refines them
        current_bindings_list = [{}] # List of possible bindings, starts with one empty possibility

        for condition in self.conditions:
            next_bindings_list = []
            for current_binding in current_bindings_list:
                # Check the condition against the facts
                condition_results = condition.check(facts)

                # For each successful check of the condition, try to merge bindings
                for result_binding in condition_results:
                    merged_binding = current_binding.copy()
                    compatible = True
                    for var, value in result_binding.items():
                        if var in merged_binding and merged_binding[var] != value:
                            compatible = False # Conflicting binding
                            break
                        merged_binding[var] = value

                    if compatible:
                        next_bindings_list.append(merged_binding)

            current_bindings_list = next_bindings_list
            if not current_bindings_list:
                break # If any condition fails to produce bindings, the rule fails

        # If we have valid bindings after checking all conditions
        for final_binding in current_bindings_list:
            # Substitute variables in the conclusion
            concluded_args = []
            possible = True
            for arg in self.conclusion.args:
                if isinstance(arg, str) and arg.startswith('?'):
                    if arg in final_binding:
                        concluded_args.append(final_binding[arg])
                    else:
                        # This shouldn't happen due to validation in __init__
                        print(f"Error applying rule '{self.name}': Unbound variable '{arg}' in conclusion.")
                        possible = False
                        break
                else:
                    concluded_args.append(arg)

            if possible:
                new_fact = Fact(self.conclusion.predicate, *concluded_args)
                # Avoid adding duplicate facts if the rule fires multiple times with same result
                if new_fact not in facts and new_fact not in new_facts:
                    new_facts.append(new_fact)
                    # print(f"Rule '{self.name}' fired with binding {final_binding}, concluding: {new_fact}")


        return new_facts

    def __repr__(self):
        cond_repr = ' AND '.join(map(repr, self.conditions))
        return f"Rule({self.name!r}: IF {cond_repr} THEN {self.conclusion!r})"

# --- Simple Rule Engine (Forward Chaining) ---

class RuleEngine:
    """A basic forward-chaining rule engine."""
    def __init__(self, rules: List[Rule]):
        self.rules = rules
        print(f"RuleEngine initialized with {len(rules)} rules.")

    def run(self, initial_facts: Set[Fact], max_iterations: int = 10) -> Set[Fact]:
        """
        Runs the rule engine, applying rules iteratively until no new facts are derived.

        Args:
            initial_facts (Set[Fact]): The starting set of facts.
            max_iterations (int): Maximum number of iterations to prevent infinite loops.

        Returns:
            Set[Fact]: The final set of facts after rule application.
        """
        facts = initial_facts.copy()
        print(f"\n--- Rule Engine Run Start ---")
        print(f"Initial Facts ({len(facts)}): {facts}")
        for i in range(max_iterations):
            print(f"\nIteration {i+1}/{max_iterations}")
            newly_derived_facts = set()
            for rule in self.rules:
                derived = rule.apply(facts)
                for fact in derived:
                     if fact not in facts: # Check again to be sure
                          newly_derived_facts.add(fact)

            if not newly_derived_facts:
                print("No new facts derived. Halting.")
                break # Fixed point reached

            print(f"Derived {len(newly_derived_facts)} new facts: {newly_derived_facts}")
            facts.update(newly_derived_facts)
        else:
            print("Warning: Rule engine reached max iterations.")

        print(f"--- Rule Engine Run End ---")
        print(f"Final Facts ({len(facts)}): {facts}")
        return facts

# --- Example Rules and Usage ---

# Define some example rules relevant to Devin's potential domains
example_rules = [
    # Simple deduction
    Rule(
        name="CanScanIfHasToolAndTarget",
        conditions=[
            Condition("has_tool", "?user", "nmap"),
            Condition("has_target", "?user", "?target")
        ],
        conclusion=Fact("can_scan", "?user", "?target", "nmap")
    ),
    # Rule using comparison
    Rule(
        name="HighSeverityIfCVSSAbove7",
        conditions=[
            Condition("vulnerability_found", "?target", "?cve"),
            Condition("has_cvss", "?cve", "?score"),
            Condition("?score", comparison_op=operator.gt, value=7.0) # Check if ?score > 7.0
        ],
        conclusion=Fact("severity", "?cve", "high")
    ),
    # Rule chaining
    Rule(
        name="RequiresReportIfHighSeverity",
        conditions=[
            Condition("severity", "?cve", "high")
        ],
        conclusion=Fact("requires_report", "?cve")
    ),
     # Ethical constraint example
    Rule(
        name="IllegalActionIfNoPermissionScan",
        conditions=[
            Condition("scan_target", "?target"),
            Condition("has_permission", "?target", False) # Checks for explicit lack of permission
        ],
        conclusion=Fact("illegal_action_proposed", "scan", "?target")
    )
    # Add more complex rules for planning, diagnostics, ethics etc.
]

if __name__ == "__main__":
    print("\n--- Symbolic Rules Example ---")

    # Initial state / facts from Working Memory or LTM perhaps
    initial_facts = {
        Fact("has_tool", "devin_agent", "nmap"),
        Fact("has_target", "devin_agent", "example.com"),
        Fact("vulnerability_found", "example.com", "CVE-2024-1234"),
        Fact("has_cvss", "CVE-2024-1234", 9.8),
        Fact("scan_target", "unauthorized.com"),
        Fact("has_permission", "unauthorized.com", False),
        Fact("has_permission", "example.com", True)
    }

    # Initialize and run the engine
    engine = RuleEngine(example_rules)
    final_facts = engine.run(initial_facts)

    # Check for specific conclusions
    print("\nChecking specific conclusions:")
    print(f"Can Scan example.com? {'Yes' if Fact('can_scan', 'devin_agent', 'example.com', 'nmap') in final_facts else 'No'}")
    print(f"Severity of CVE-2024-1234 High? {'Yes' if Fact('severity', 'CVE-2024-1234', 'high') in final_facts else 'No'}")
    print(f"Report Required for CVE-2024-1234? {'Yes' if Fact('requires_report', 'CVE-2024-1234') in final_facts else 'No'}")
    print(f"Illegal Scan Proposed for unauthorized.com? {'Yes' if Fact('illegal_action_proposed', 'scan', 'unauthorized.com') in final_facts else 'No'}")

    print("--- End Example ---")
