# Devin/quantum/optimization/annealing_scheduler.py
# Purpose: A tool that uses the simulated annealing algorithm to solve complex
#          task scheduling problems with dependencies.

import logging
import random
import math
import copy
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple

# Configure basic logging
logger = logging.getLogger("AnnealingScheduler")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

@dataclass
class Task:
    """Represents a single task with an ID and duration."""
    id: str
    duration: int

class AnnealingScheduler:
    """
    Uses simulated annealing to find a near-optimal task schedule.
    """
    def __init__(self, tasks: List[Task], dependencies: Dict[str, List[str]]):
        self.tasks = {t.id: t for t in tasks}
        self.dependencies = dependencies
        self._validate_dependencies()
        
    def _validate_dependencies(self):
        """Ensures all task IDs in dependencies exist."""
        all_task_ids = set(self.tasks.keys())
        for task_id, deps in self.dependencies.items():
            if task_id not in all_task_ids:
                raise ValueError(f"Task '{task_id}' in dependencies not found in task list.")
            for dep_id in deps:
                if dep_id not in all_task_ids:
                    raise ValueError(f"Dependency '{dep_id}' for task '{task_id}' not found.")

    def _calculate_cost(self, schedule: List[str]) -> int:
        """
        Calculates the cost (total completion time or makespan) of a schedule.
        This is the core evaluation function.
        """
        completion_times = {}
        for task_id in schedule:
            prereq_completion_time = 0
            # Find the latest completion time among all prerequisites for the current task
            if task_id in self.dependencies:
                for prereq_id in self.dependencies[task_id]:
                    if prereq_id not in completion_times:
                        # This schedule is invalid because a dependency hasn't been met yet.
                        # Assign a very high cost to penalize this schedule.
                        return float('inf')
                    prereq_completion_time = max(prereq_completion_time, completion_times[prereq_id])
            
            # The start time of this task is when all its prerequisites are done.
            start_time = prereq_completion_time
            # The completion time is its start time plus its own duration.
            completion_times[task_id] = start_time + self.tasks[task_id].duration
        
        # The total cost (makespan) is the completion time of the very last task.
        return max(completion_times.values()) if completion_times else 0

    def _get_neighbor_solution(self, schedule: List[str]) -> List[str]:
        """Creates a new schedule by swapping two adjacent, non-dependent tasks."""
        new_schedule = schedule[:]
        if len(new_schedule) < 2:
            return new_schedule

        for _ in range(len(new_schedule)): # Try a few times to find a valid swap
            i = random.randint(0, len(new_schedule) - 2)
            j = i + 1
            
            task1_id, task2_id = new_schedule[i], new_schedule[j]
            
            # Check if swapping is valid: task1 must not be a dependency of task2
            if task1_id not in self.dependencies.get(task2_id, []):
                new_schedule[i], new_schedule[j] = new_schedule[j], new_schedule[i]
                return new_schedule
                
        return new_schedule # Return original if no valid swap found

    def solve(self, initial_temp: float, cooling_rate: float, max_iterations: int) -> Tuple[List[str], int]:
        """
        Runs the simulated annealing algorithm to find the optimal schedule.
        """
        # Create an initial valid solution (simple topological sort)
        logger.info("Generating initial valid schedule...")
        current_solution = []
        tasks_to_schedule = set(self.tasks.keys())
        while tasks_to_schedule:
            ready_tasks = {t for t in tasks_to_schedule if all(d in current_solution for d in self.dependencies.get(t, []))}
            if not ready_tasks: raise ValueError("Cyclic dependency detected in tasks.")
            task_to_add = random.choice(list(ready_tasks))
            current_solution.append(task_to_add)
            tasks_to_schedule.remove(task_to_add)
        
        best_solution = current_solution
        current_cost = self._calculate_cost(current_solution)
        best_cost = current_cost
        current_temp = initial_temp
        
        logger.info(f"Initial schedule: {best_solution} | Initial cost (makespan): {best_cost}")
        logger.warning("Starting simulated annealing optimization...")

        for i in range(max_iterations):
            neighbor_solution = self._get_neighbor_solution(current_solution)
            neighbor_cost = self._calculate_cost(neighbor_solution)
            
            cost_diff = neighbor_cost - current_cost
            
            # If the new solution is better, accept it.
            # If it's worse, accept it with a certain probability.
            if cost_diff < 0 or random.random() < math.exp(-cost_diff / current_temp):
                current_solution = neighbor_solution
                current_cost = neighbor_cost
            
            # Update the best solution found so far
            if current_cost < best_cost:
                best_solution = current_solution
                best_cost = current_cost
                
            # Cool the temperature
            current_temp *= cooling_rate
            if (i + 1) % 1000 == 0:
                logger.info(f"Iteration {i+1}/{max_iterations} | Current Best Cost: {best_cost}")
        
        logger.warning("Optimization finished.")
        return best_solution, best_cost


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Simulated Annealing Task Scheduler Prototype 🔥⚙️ ===")
    print("=========================================================")
    
    # 1. Define a set of tasks and their dependencies
    tasks = [
        Task(id='A', duration=5),  # Recon
        Task(id='B', duration=10), # Port Scan on main domain
        Task(id='C', duration=8),  # Web Scan on main domain
        Task(id='D', duration=12), # Vuln Assessment on main domain
        Task(id='E', duration=3),  # Analyze Recon results
        Task(id='F', duration=15)  # Port Scan on discovered subdomains
    ]
    dependencies = {
        'C': ['B'], # Web scan requires port scan to be done
        'D': ['C'], # Vuln assessment requires web scan
        'E': ['A'], # Analysis requires recon
        'F': ['E']  # Scanning subdomains requires recon analysis
    }
    
    print("--- Problem Definition ---")
    print(f"Tasks: {[t.id for t in tasks]}")
    print(f"Dependencies: {dependencies}")
    
    # 2. Initialize and run the scheduler
    scheduler = AnnealingScheduler(tasks, dependencies)
    
    # Annealing parameters
    initial_temperature = 1000.0
    cooling_rate = 0.995
    iterations = 20000
    
    optimal_schedule, min_cost = scheduler.solve(initial_temperature, cooling_rate, iterations)
    
    # 3. Print the results
    print("\n--- Results ---")
    print(f"Optimal schedule found: {optimal_schedule}")
    print(f"Minimum completion time (makespan): {min_cost} units")
    
    print("\n=========================================================")
    print("=== Annealing Scheduler Prototype Complete ===")
    print("=========================================================")
