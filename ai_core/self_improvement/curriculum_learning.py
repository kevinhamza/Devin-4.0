# Devin/ai_core/self_improvement/curriculum_learning.py

import random
from typing import Dict, Any, List, Optional, TypedDict, Literal
from collections import defaultdict

# --- Task Definition ---

class Task(TypedDict):
    """Represents a learning task within the curriculum."""
    task_id: str
    description: str
    difficulty_level: Literal['easy', 'medium', 'hard', 'expert'] # Predefined difficulty levels
    task_type: str # e.g., 'web_navigation', 'code_generation', 'pentest_scan', 'file_management'
    parameters: Dict[str, Any] # Specific parameters for the task (e.g., target_url, file_path, query)
    success_criteria: str # Description of how success is measured

# --- Curriculum Manager ---

class CurriculumManager:
    """
    Manages the curriculum for AI self-improvement.

    Selects appropriate tasks for the AI to learn based on its current
    competence level, ensuring a gradual increase in difficulty.
    """

    def __init__(self):
        """Initializes the Curriculum Manager."""
        self.tasks: Dict[str, List[Task]] = {
            'easy': [],
            'medium': [],
            'hard': [],
            'expert': []
        }
        # Track AI performance on tasks/types
        # Structure: {task_type: {'attempts': int, 'successes': int, 'avg_score': float}}
        self.performance_tracker: Dict[str, Dict[str, Any]] = defaultdict(lambda: {'attempts': 0, 'successes': 0, 'avg_score': 0.0})
        # Track overall competence or current learning stage
        self.current_stage: Literal['easy', 'medium', 'hard', 'expert'] = 'easy'
        self.stage_mastery_threshold: Dict[Literal['easy', 'medium', 'hard'], float] = {
            'easy': 0.90, # Success rate needed to move from easy to medium
            'medium': 0.80, # Success rate needed to move from medium to hard
            'hard': 0.70  # Success rate needed to move from hard to expert
        }
        print("CurriculumManager initialized.")

    def define_task(self, task: Task):
        """
        Adds a new task definition to the curriculum.

        Args:
            task (Task): The task definition dictionary.
        """
        level = task.get('difficulty_level', 'medium')
        task_id = task.get('task_id')
        if not task_id:
            print("Warning: Task definition missing 'task_id'. Skipping.")
            return

        if level in self.tasks:
            # Check for duplicate task IDs
            if any(t['task_id'] == task_id for t in self.tasks[level]):
                 print(f"Warning: Task ID '{task_id}' already exists in level '{level}'. Overwriting.")
                 self.tasks[level] = [t for t in self.tasks[level] if t['task_id'] != task_id] # Remove old one

            self.tasks[level].append(task)
            print(f"Defined Task '{task_id}' (Level: {level}, Type: {task['task_type']})")
        else:
            print(f"Warning: Invalid difficulty level '{level}' for task '{task_id}'. Skipping.")

    def update_progress(self, task_id: str, task_type: str, success: bool, score: Optional[float] = None):
        """
        Updates the AI's performance tracker based on the result of a completed task.

        Args:
            task_id (str): The ID of the completed task.
            task_type (str): The type of the completed task.
            success (bool): Whether the task was successfully completed.
            score (Optional[float]): An optional numerical score (e.g., from reward model).
        """
        print(f"Updating progress for Task '{task_id}' (Type: {task_type}): Success={success}, Score={score}")
        stats = self.performance_tracker[task_type]
        stats['attempts'] += 1
        if success:
            stats['successes'] += 1

        # Update average score if provided
        if score is not None:
            # Simple rolling average calculation
            current_total_score = stats['avg_score'] * (stats['attempts'] - 1)
            stats['avg_score'] = (current_total_score + score) / stats['attempts']

        # Re-evaluate current learning stage
        self._update_learning_stage()

    def _calculate_competence(self, level: Literal['easy', 'medium', 'hard', 'expert']) -> float:
        """
        Estimates the AI's overall success rate for tasks at a given difficulty level.
        (Simple implementation based on task types predominantly at that level).

        Args:
            level (Literal['easy', 'medium', 'hard', 'expert']): The difficulty level.

        Returns:
            float: Estimated success rate (0.0 to 1.0). Returns 0.0 if no attempts.
        """
        total_attempts = 0
        total_successes = 0
        # Consider tasks predominantly of this level (simplistic approach)
        # A better approach might tag task_types with typical difficulties
        relevant_task_types = [t['task_type'] for t in self.tasks[level]] # Get types at this level
        # Use performance data for these types
        for task_type in set(relevant_task_types):
             if task_type in self.performance_tracker:
                  stats = self.performance_tracker[task_type]
                  total_attempts += stats['attempts']
                  total_successes += stats['successes']

        if total_attempts == 0:
            return 0.0 # No attempts yet at this level (or relevant types)
        return total_successes / total_attempts

    def _update_learning_stage(self):
        """ Checks if the AI has mastered the current stage and can move to the next. """
        original_stage = self.current_stage
        if self.current_stage == 'easy':
            competence = self._calculate_competence('easy')
            if competence >= self.stage_mastery_threshold['easy']:
                self.current_stage = 'medium'
        elif self.current_stage == 'medium':
            competence = self._calculate_competence('medium')
            if competence >= self.stage_mastery_threshold['medium']:
                 self.current_stage = 'hard'
        elif self.current_stage == 'hard':
             competence = self._calculate_competence('hard')
             if competence >= self.stage_mastery_threshold['hard']:
                  self.current_stage = 'expert'
        # Cannot advance beyond 'expert' in this model

        if self.current_stage != original_stage:
             print(f"*** Curriculum Stage Advanced: {original_stage} -> {self.current_stage} ***")


    def get_next_task(self, requested_type: Optional[str] = None, force_level: Optional[Literal['easy', 'medium', 'hard', 'expert']] = None) -> Optional[Task]:
        """
        Selects the next task for the AI to learn.

        Prioritizes tasks at the AI's current learning stage or below.
        Can optionally focus on a specific task type or force a difficulty level.

        Args:
            requested_type (Optional[str]): If specified, try to find a task of this type.
            force_level (Optional[Literal['easy', 'medium', 'hard', 'expert']]):
                If specified, force selection from this difficulty level.

        Returns:
            Optional[Task]: The selected task definition, or None if no suitable task found.
        """
        print(f"\nGetting next task...")
        level_priority = ['easy', 'medium', 'hard', 'expert']
        target_level = force_level or self.current_stage
        print(f"  - Current Stage: {self.current_stage}")
        print(f"  - Target Level for Selection: {target_level}")
        if requested_type:
             print(f"  - Requested Type: {requested_type}")

        # Determine the search order for levels
        search_levels = []
        if force_level:
            search_levels = [force_level]
        else:
            # Start from target level and go down, then maybe slightly up if needed
            current_index = level_priority.index(target_level)
            search_levels.extend(reversed(level_priority[:current_index+1])) # Target level and below
            # Optionally add the next level up if comfortable
            if current_index + 1 < len(level_priority):
                 search_levels.append(level_priority[current_index + 1])

        print(f"  - Level Search Order: {search_levels}")

        # Find a suitable task
        for level in search_levels:
            available_tasks = self.tasks.get(level, [])
            if not available_tasks:
                continue

            potential_tasks = available_tasks
            # Filter by type if requested
            if requested_type:
                potential_tasks = [t for t in available_tasks if t['task_type'] == requested_type]

            if potential_tasks:
                # --- Placeholder: Add more sophisticated selection logic ---
                # Could prioritize tasks not attempted often, tasks failed recently,
                # tasks related to a specific skill gap, etc.
                # Simple random selection for now:
                selected_task = random.choice(potential_tasks)
                print(f"  - Selected Task '{selected_task['task_id']}' (Level: {level}, Type: {selected_task['task_type']})")
                return selected_task
                # --- End Placeholder ---

        print("  - No suitable task found in the curriculum based on current criteria.")
        return None


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Curriculum Learning Example ---")

    manager = CurriculumManager()

    # Define some tasks
    task1: Task = {'task_id': 'web_nav_easy_1', 'description': 'Navigate to login page on example.com', 'difficulty_level': 'easy', 'task_type': 'web_navigation', 'parameters': {'url': 'http://example.com'}, 'success_criteria': 'Login page title detected'}
    task2: Task = {'task_id': 'file_manage_easy_1', 'description': 'Create a directory named temp_dir', 'difficulty_level': 'easy', 'task_type': 'file_management', 'parameters': {'dir_name': 'temp_dir'}, 'success_criteria': 'Directory exists'}
    task3: Task = {'task_id': 'web_nav_medium_1', 'description': 'Log in to example.com with credentials', 'difficulty_level': 'medium', 'task_type': 'web_navigation', 'parameters': {'url': 'http://example.com', 'user': 'test', 'pass': 'pass'}, 'success_criteria': 'Welcome message detected'}
    task4: Task = {'task_id': 'pentest_scan_medium_1', 'description': 'Run nmap -sV on target', 'difficulty_level': 'medium', 'task_type': 'pentest_scan', 'parameters': {'target': '192.168.1.1', 'tool': 'nmap', 'args': '-sV'}, 'success_criteria': 'Scan completes, report generated'}

    manager.define_task(task1)
    manager.define_task(task2)
    manager.define_task(task3)
    manager.define_task(task4)

    # Simulate getting tasks and providing feedback
    print("\nSimulating learning loop:")
    for i in range(5): # Simulate a few learning steps
        next_task = manager.get_next_task()
        if next_task:
            print(f"Step {i+1}: AI attempts Task '{next_task['task_id']}'")
            # Simulate task outcome (e.g., higher success on easy tasks initially)
            success = random.random() < 0.95 if next_task['difficulty_level'] == 'easy' else random.random() < 0.6
            score = 1.0 if success else 0.0
            manager.update_progress(next_task['task_id'], next_task['task_type'], success, score)
        else:
            print(f"Step {i+1}: No suitable task found.")
            break

    # Check competence and stage after simulation
    print(f"\nCompetence on easy tasks: {manager._calculate_competence('easy'):.2f}")
    print(f"Competence on medium tasks: {manager._calculate_competence('medium'):.2f}")
    print(f"Current Learning Stage: {manager.current_stage}")

    # Get a specific type of task
    specific_task = manager.get_next_task(requested_type='pentest_scan')
    if specific_task:
         print(f"\nRequested specific task type 'pentest_scan': Found '{specific_task['task_id']}'")


    print("--- End Example ---")
