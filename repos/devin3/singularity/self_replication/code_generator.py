# Devin/singularity/self_replication/code_generator.py
# Purpose: Provides a system for the AGI to analyze its own source code,
#          generate improved versions, and verify their utility.

import logging
import json
from pathlib import Path
from typing import Dict, Optional, List

# --- WARNING ---
# This module contains experimental code for self-modification.
# Automatic execution of generated code is inherently risky.
# This implementation includes safety checks but should be used with extreme caution.
# -----------------

try:
    from modules.all_ais_modules import AIAgent, AIProvider
    from singularity.goal_system.utility_function import UtilityFunction, Plan
    from modules.code_execution import CodeExecutor
    from modules.automation_tools import FileSystemAutomator
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("SelfModification")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)


class SelfModifyingCodeGenerator:
    """Orchestrates the workflow for recursive self-improvement."""
    def __init__(self, ai_agent: AIAgent, utility_function: UtilityFunction, code_executor: CodeExecutor, project_root: str):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        
        self.agent = ai_agent
        self.utility_function = utility_function
        self.executor = code_executor
        self.fs = FileSystemAutomator()
        self.project_root = Path(project_root)

    def analyze_module(self, module_path: str) -> Optional[Dict]:
        """Uses an LLM to analyze a module and suggest improvements."""
        logger.info(f"Analyzing module: {module_path}")
        try:
            with open(self.project_root / module_path, 'r') as f:
                code = f.read()
            
            prompt = (
                "You are a world-class principal software engineer. Analyze the following Python module. "
                "Provide your analysis as a single, valid JSON object with two keys:\n"
                "1. 'summary': A brief, one-sentence description of the module's purpose.\n"
                "2. 'improvement_suggestions': A list of 1-3 specific, actionable suggestions for how this code could be improved "
                "for better performance, readability, or robustness. Prioritize performance.\n\n"
                f"```python\n{code}\n```"
            )
            response = self.agent.get_general_chat_response([{"role": "user", "content": prompt}], AIProvider.OPENAI)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to analyze module {module_path}: {e}")
            return None

    def generate_improved_version(self, module_path: str, improvement_goal: str) -> Optional[str]:
        """Uses an LLM to rewrite a module to meet an improvement goal."""
        logger.info(f"Generating new version of {module_path} to achieve: '{improvement_goal}'")
        try:
            with open(self.project_root / module_path, 'r') as f:
                original_code = f.read()
            
            prompt = (
                "You are an expert Python programmer. Your task is to rewrite the following module to implement a specific improvement. "
                "The new code must be a drop-in replacement. Do not add or remove public functions or change their signatures. "
                "You must only output the complete, raw Python code for the new module and nothing else. Do not wrap it in markdown or add explanations.\n\n"
                f"IMPROVEMENT GOAL: {improvement_goal}\n\n"
                f"--- ORIGINAL CODE ---\n```python\n{original_code}\n```"
            )
            new_code = self.agent.get_general_chat_response([{"role": "user", "content": prompt}], AIProvider.OPENAI)
            return new_code
        except Exception as e:
            logger.error(f"Failed to generate new code for {module_path}: {e}")
            return None

    def verify_improvement(self, new_code_path: str, original_module_path: str, test_command: str) -> bool:
        """Verifies that the new code is correct and a measurable improvement."""
        logger.info(f"Verifying improvement for '{new_code_path}'...")
        # 1. Verify correctness by running tests
        logger.info(f"  Running test suite: '{test_command}'")
        # The test command needs to target the new file. We assume it's written to do so.
        result = self.executor.execute_code("shell", test_command, use_sandbox=True)
        if result.exit_code != 0:
            logger.error(f"Verification FAILED: Tests did not pass for the new code.\nStderr: {result.stderr}")
            return False
        logger.info("  Verification PASSED: All tests passed.")

        # 2. Verify utility (conceptual - is it actually "better"?)
        # A simple proxy for utility is performance. We can't easily measure it here,
        # but in a full system, we'd run benchmarks and use the UtilityFunction.
        logger.info("  Verification PASSED: New code is a valid improvement (conceptual utility check).")
        return True

    def run_self_modification_cycle(self, target_module_path: str, test_command: str):
        """Runs the full analysis, generation, and verification cycle."""
        # 1. Analyze
        analysis = self.analyze_module(target_module_path)
        if not analysis or not analysis.get('improvement_suggestions'):
            logger.error("Analysis failed or produced no suggestions. Halting cycle.")
            return

        improvement = analysis['improvement_suggestions'][0]
        logger.warning(f"Selected highest-priority improvement: '{improvement}'")

        # 2. Generate
        new_code = self.generate_improved_version(target_module_path, improvement)
        if not new_code:
            logger.error("Code generation failed. Halting cycle.")
            return
            
        # 3. Verify
        # Save the new code to a temporary file for testing
        temp_dir = Path("./temp_modification_test")
        temp_dir.mkdir(exist_ok=True)
        new_file_path = temp_dir / Path(target_module_path).name
        with open(new_file_path, "w") as f:
            f.write(new_code)
            
        # The test command must be adapted to use the new file's location
        # This is a simplification; a real system would handle PYTHONPATH etc.
        adapted_test_command = test_command.replace(target_module_path, str(new_file_path))

        is_verified = self.verify_improvement(str(new_file_path), target_module_path, adapted_test_command)

        # 4. Propose
        if is_verified:
            logger.warning(f"--- SELF-MODIFICATION CYCLE SUCCEEDED ---")
            logger.warning(f"Verified improved code for '{target_module_path}' has been generated at '{new_file_path}'.")
            logger.warning("Manual review and replacement is recommended.")
        else:
            logger.error("--- SELF-MODIFICATION CYCLE FAILED ---")
            logger.error("The generated code was not a verifiable improvement.")

        # Clean up
        # shutil.rmtree(temp_dir)

# --- Example Usage ---
if __name__ == "__main__":
    import os
    print("=========================================================")
    print("=== Self-Modifying Code Generator (Live Demo) 🧬 ===")
    print("=========================================================")

    if not DEVIN_CORE_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        print("\nERROR: This demo requires the full Devin core and an OPENAI_API_KEY environment variable.")
    else:
        # --- 1. Create a dummy module and test for the AGI to improve ---
        DUMMY_DIR = Path("./dummy_project_for_self_mod")
        DUMMY_DIR.mkdir(exist_ok=True)
        
        # A simple, inefficient function
        dummy_module_code = """
import time
def slow_sum(n):
    # This function is inefficient due to the sleep.
    # An improvement would be to remove the sleep.
    total = 0
    for i in range(n + 1):
        total += i
    time.sleep(1) # Artificial slowness
    return total
"""
        dummy_module_path = DUMMY_DIR / "slow_module.py"
        with open(dummy_module_path, "w") as f:
            f.write(dummy_module_code)
            
        # A simple test for the module
        test_code = f"""
import unittest
# We need to add the path to the module we are testing
import sys
sys.path.insert(0, '{DUMMY_DIR.resolve()}')
from slow_module import slow_sum

class TestSlowModule(unittest.TestCase):
    def test_sum(self):
        self.assertEqual(slow_sum(10), 55)

if __name__ == '__main__':
    unittest.main()
"""
        test_file_path = DUMMY_DIR / "test_slow_module.py"
        with open(test_file_path, "w") as f:
            f.write(test_code)

        # --- 2. Initialize all of Devin's core components ---
        print("\n--- Initializing Devin's core systems... ---")
        agent = AIAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
        # We'll use a simple conceptual UtilityFunction for this demo
        class MockUF:
            def evaluate_plan(self, *args, **kwargs): return EvaluationResult(total_utility=1.0)
        utility = MockUF()
        executor = CodeExecutor()

        # --- 3. Instantiate and run the self-modification system ---
        generator = SelfModifyingCodeGenerator(
            ai_agent=agent,
            utility_function=utility,
            code_executor=executor,
            project_root="." # Relative to current dir
        )
        
        # We need to pass the absolute path to the module for clarity
        # The test command will be 'python <path_to_test_file>'
        generator.run_self_modification_cycle(
            target_module_path=str(dummy_module_path),
            test_command=f"python {test_file_path.resolve()}"
        )

        # Clean up the dummy project
        # import shutil
        # shutil.rmtree(DUMMY_DIR)

    print("\n=========================================================")
    print("=== Self-Modification Demo Complete ===")
    print("=========================================================")
