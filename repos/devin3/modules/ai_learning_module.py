# # Devin/modules/ai_learning_module.py
# # Purpose: Conceptually handles reinforcement learning (RL) and supervised
# #          fine-tuning to enable Devin to learn from its interactions.
# # Reinforcement and supervised learning modules 🧠💡

# import logging
# import uuid
# import json
# import random
# from enum import Enum, auto
# from datetime import datetime, timezone
# from typing import List, Dict, Any, Optional, Union
# from pathlib import Path

# # Configure basic logging
# logger = logging.getLogger("AILearningModule")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class LearningDataType(Enum):
#     """Types of data that can be logged for learning."""
#     ACTION_TRAJECTORY = auto() # A sequence of (state, action, outcome) for RL
#     SUPERVISED_FINE_TUNE_PAIR = auto() # A (prompt, ideal_completion) pair
#     USER_FEEDBACK = auto() # Explicit user feedback (e.g., thumbs up/down)

# class TrainingJobStatus(Enum):
#     """Status of a conceptual fine-tuning job."""
#     PENDING = auto()
#     PREPARING_DATA = auto()
#     UPLOADING_DATASET = auto()
#     QUEUED = auto()
#     RUNNING = auto()
#     SUCCEEDED = auto()
#     FAILED = auto()
#     CANCELLED = auto()

# @dataclass
# class TrainingJob:
#     """Represents a conceptual fine-tuning job."""
#     job_id: str = field(default_factory=lambda: f"ftjob_{uuid.uuid4().hex[:12]}")
#     base_model: str
#     training_dataset_ref: str
#     status: TrainingJobStatus = TrainingJobStatus.PENDING
#     created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
#     finished_at: Optional[datetime] = None
#     fine_tuned_model_id: Optional[str] = None
#     error_message: Optional[str] = None

# class AILearningModule:
#     """
#     Conceptually manages Devin's ability to learn and adapt over time through
#     reinforcement learning and supervised fine-tuning.
#     """

#     def __init__(self, data_storage_path: str = "devin_learning_data", model_registry_path: str = "devin_model_registry.json"):
#         """
#         Initializes the learning module.

#         Args:
#             data_storage_path (str): Path to store logged interaction data.
#             model_registry_path (str): Path to a conceptual file tracking fine-tuned models.
#         """
#         self.data_storage_path = Path(data_storage_path)
#         self.model_registry_path = Path(model_registry_path)
#         self.data_storage_path.mkdir(parents=True, exist_ok=True)

#         # In-memory conceptual storage for this simulation
#         self.interaction_log: List[Dict[str, Any]] = []
#         self.training_jobs: Dict[str, TrainingJob] = {}
#         self.rl_policy_conceptual: Dict[str, float] = {"policy_version": 1.0} # Dummy policy weights

#         logger.info(f"AILearningModule initialized. Data will be conceptually stored in '{self.data_storage_path.resolve()}'")

#     def log_interaction_for_learning(self,
#                                      data_type: LearningDataType,
#                                      interaction_id: str,
#                                      data: Dict,
#                                      metadata: Optional[Dict] = None) -> None:
#         """
#         Logs an interaction that can be used for future learning.

#         Args:
#             data_type (LearningDataType): The type of data being logged.
#             interaction_id (str): A unique ID for the interaction or task.
#             data (Dict): The core data for learning (e.g., prompt/completion, state/action).
#             metadata (Optional[Dict]): Additional context.
#         """
#         log_entry = {
#             "log_id": f"learn_{uuid.uuid4().hex[:8]}",
#             "interaction_id": interaction_id,
#             "data_type": data_type.name,
#             "data": data,
#             "metadata": metadata or {},
#             "timestamp": datetime.now(timezone.utc).isoformat()
#         }
#         self.interaction_log.append(log_entry)
#         logger.info(f"Logged interaction '{interaction_id}' of type '{data_type.name}' for future learning.")
#         # In a real system, this would write to a persistent log file or database.
#         # with open(self.data_storage_path / f"{log_entry['log_id']}.json", "w") as f:
#         #     json.dump(log_entry, f, indent=2)

#     def process_user_feedback(self, interaction_id: str, feedback_type: str, rating: float) -> None:
#         """
#         Processes explicit user feedback and converts it into a learning signal.

#         Args:
#             interaction_id (str): The ID of the interaction being rated.
#             feedback_type (str): e.g., "thumbs_up", "thumbs_down", "correction_provided".
#             rating (float): A numerical rating (e.g., 1.0 for positive, -1.0 for negative).
#         """
#         feedback_data = {"type": feedback_type, "rating": rating}
#         self.log_interaction_for_learning(
#             data_type=LearningDataType.USER_FEEDBACK,
#             interaction_id=interaction_id,
#             data=feedback_data
#         )
#         # This feedback can now be used for RL
#         self.update_rl_policy_conceptual(interaction_id, reward=rating)

#     def update_rl_policy_conceptual(self, interaction_id: str, reward: float) -> None:
#         """
#         Conceptually updates the internal reinforcement learning policy.
#         In a real system, this would involve complex algorithms like PPO or Q-learning.
#         """
#         logger.info(f"CONCEPTUAL RL: Applying reward of '{reward}' to interaction '{interaction_id}'.")
#         # Find the relevant past actions (trajectory) for this interaction
#         trajectory = [log for log in self.interaction_log if log["interaction_id"] == interaction_id and log["data_type"] == "ACTION_TRAJECTORY"]
#         if not trajectory:
#             logger.warning(f"  No action trajectory found for interaction '{interaction_id}' to apply RL reward.")
#             return

#         # Simulate updating the policy. A real system would backpropagate the reward.
#         # Here, we just increment a version number as a placeholder for learning.
#         old_version = self.rl_policy_conceptual['policy_version']
#         self.rl_policy_conceptual['policy_version'] += 0.01 * reward # Small update
#         logger.info(f"  RL policy conceptually updated. Version changed from {old_version:.3f} to {self.rl_policy_conceptual['policy_version']:.3f}.")

#     def create_fine_tuning_dataset_conceptual(self, dataset_name: str, interaction_ids: List[str]) -> Optional[str]:
#         """
#         Conceptually creates a fine-tuning dataset from logged interactions.
#         This would typically format data into a specific JSONL format required by the fine-tuning API.
#         """
#         logger.info(f"CONCEPTUAL: Creating fine-tuning dataset '{dataset_name}' from {len(interaction_ids)} interactions.")
#         dataset_content = []
#         # Filter for high-quality supervised pairs or interactions with positive feedback
#         for log in self.interaction_log:
#             if log["interaction_id"] in interaction_ids and log["data_type"] == "SUPERVISED_FINE_TUNE_PAIR":
#                 # Assuming data is in {"prompt": "...", "completion": "..."} format
#                 # This could be adapted for OpenAI's {"messages": [...]} format
#                 dataset_content.append(log["data"])

#         if not dataset_content:
#             logger.error("  No suitable data found in logs for the provided interaction IDs.")
#             return None

#         dataset_path = self.data_storage_path / f"{dataset_name}_{uuid.uuid4().hex[:6]}.jsonl"
#         # Simulate writing the file
#         try:
#             with open(dataset_path, "w") as f:
#                 for item in dataset_content:
#                     f.write(json.dumps(item) + "\n")
#             logger.info(f"  Successfully created conceptual dataset file at '{dataset_path}'. Contains {len(dataset_content)} examples.")
#             return str(dataset_path)
#         except Exception as e:
#             logger.error(f"  Failed to write conceptual dataset file: {e}")
#             return None

#     def start_fine_tuning_job_conceptual(self, base_model: str, dataset_path: str) -> TrainingJob:
#         """
#         Conceptually starts a fine-tuning job with a given dataset and base model.
#         """
#         logger.info(f"CONCEPTUAL: Submitting fine-tuning job for base model '{base_model}' with dataset '{dataset_path}'.")
#         # In a real system, this would make an API call to OpenAI, Google AI Platform, etc.
#         job = TrainingJob(base_model=base_model, training_dataset_ref=dataset_path, status=TrainingJobStatus.QUEUED)
#         self.training_jobs[job.job_id] = job
#         logger.info(f"  Fine-tuning job created with ID '{job.job_id}' and status '{job.status.name}'.")
#         return job

#     def check_training_job_status(self, job_id: str) -> Optional[TrainingJob]:
#         """Conceptually checks and updates the status of a training job."""
#         job = self.training_jobs.get(job_id)
#         if not job:
#             logger.error(f"Job ID '{job_id}' not found.")
#             return None

#         # Simulate status progression
#         current_status = job.status
#         if current_status in [TrainingJobStatus.SUCCEEDED, TrainingJobStatus.FAILED, TrainingJobStatus.CANCELLED]:
#             return job # Job is already finished

#         # Randomly advance the status for simulation
#         if random.random() < 0.8: # 80% chance of progressing
#             status_progression = {
#                 TrainingJobStatus.QUEUED: TrainingJobStatus.RUNNING,
#                 TrainingJobStatus.RUNNING: TrainingJobStatus.SUCCEEDED,
#             }
#             new_status = status_progression.get(current_status, current_status)
#             if new_status != current_status:
#                 job.status = new_status
#                 logger.info(f"  Status of job '{job_id}' updated to: {job.status.name}")
#                 if job.status == TrainingJobStatus.SUCCEEDED:
#                     job.finished_at = datetime.now(timezone.utc)
#                     job.fine_tuned_model_id = f"devin-ft-{job.base_model.replace('.','-')}-{uuid.uuid4().hex[:6]}"
#                     logger.info(f"  Job '{job_id}' succeeded! New model ID: {job.fine_tuned_model_id}")
#         elif random.random() < 0.1: # 10% chance of failing
#             job.status = TrainingJobStatus.FAILED
#             job.error_message = "Simulated training failure: gradient explosion."
#             logger.error(f"  Job '{job_id}' has FAILED. Reason: {job.error_message}")
#             job.finished_at = datetime.now(timezone.utc)

#         return job

# # Example Usage
# if __name__ == "__main__":
#     print("=========================================================")
#     print("=== AI Learning Module Prototype 🧠💡 ===")
#     print("=========================================================")

#     learning_module = AILearningModule()

#     # --- 1. Simulate some interactions to log ---
#     print("\n--- Step 1: Logging Devin's Interactions ---")
#     task1_id = "task_fix_bug_123"
#     # A successful interaction becomes a good fine-tuning example
#     learning_module.log_interaction_for_learning(
#         data_type=LearningDataType.SUPERVISED_FINE_TUNE_PAIR,
#         interaction_id=task1_id,
#         data={"prompt": "Bug report: 'Login fails on username with special chars'. Code: ...", "completion": "Solution: Sanitize username input here... (correct code patch)"}
#     )
#     # The actions taken for that task are logged for RL
#     learning_module.log_interaction_for_learning(
#         data_type=LearningDataType.ACTION_TRAJECTORY,
#         interaction_id=task1_id,
#         data={"state": "bug_identified", "action": "read_file:login.py"}
#     )

#     task2_id = "task_refactor_api_456"
#     # A less successful interaction
#     learning_module.log_interaction_for_learning(
#         data_type=LearningDataType.SUPERVISED_FINE_TUNE_PAIR,
#         interaction_id=task2_id,
#         data={"prompt": "Refactor the API endpoint.", "completion": "Refactoring attempt that introduced a new bug..."}
#     )
#     learning_module.log_interaction_for_learning(
#         data_type=LearningDataType.ACTION_TRAJECTORY,
#         interaction_id=task2_id,
#         data={"state": "refactor_started", "action": "apply_code_diff"}
#     )
#     print("")

#     # --- 2. Process User Feedback on these tasks ---
#     print("\n--- Step 2: Processing User Feedback ---")
#     # User marks the first task as successful
#     learning_module.process_user_feedback(interaction_id=task1_id, feedback_type="thumbs_up", rating=1.0)
#     # User marks the second task as unsuccessful
#     learning_module.process_user_feedback(interaction_id=task2_id, feedback_type="thumbs_down", rating=-1.0)
#     print("")

#     # --- 3. Create a Fine-Tuning Dataset ---
#     print("\n--- Step 3: Creating a Supervised Fine-Tuning Dataset ---")
#     # We only want to use the successful task for fine-tuning
#     dataset_path = learning_module.create_fine_tuning_dataset_conceptual(
#         dataset_name="successful_bug_fixes",
#         interaction_ids=[task1_id] # We only pass the ID of the good interaction
#     )
#     print("")

#     # --- 4. Start and Monitor a Fine-Tuning Job ---
#     if dataset_path:
#         print("\n--- Step 4: Starting and Monitoring a Fine-Tuning Job ---")
#         job = learning_module.start_fine_tuning_job_conceptual(
#             base_model="gpt-4o",
#             dataset_path=dataset_path
#         )
        
#         # Simulate checking the job over time
#         max_checks = 5
#         for check_num in range(max_checks):
#             print(f"  Checking job status (Attempt {check_num + 1}/{max_checks})...")
#             updated_job = learning_module.check_training_job_status(job.job_id)
#             if updated_job.status in [TrainingJobStatus.SUCCEEDED, TrainingJobStatus.FAILED]:
#                 break
#             time.sleep(0.1) # Simulate time passing

#         final_job_status = learning_module.training_jobs.get(job.job_id)
#         if final_job_status:
#              print(f"\nFinal Job Status for '{job.job_id}': {final_job_status.status.name}")
#              if final_job_status.fine_tuned_model_id:
#                  print(f"  New Fine-Tuned Model is available: '{final_job_status.fine_tuned_model_id}'")
#     else:
#         print("\nSkipping fine-tuning job creation as dataset was not created.")

#     print("\n=========================================================")
#     print("=== AI Learning Module Prototype Complete ===")
#     print("=========================================================")


# Devin/modules/ai_learning_module.py
# Purpose: A facade for managing Devin's learning processes, including
#          data logging and interacting with the AI Learning Server.

import logging
import uuid
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import requests
    DEPS_AVAILABLE = True
except ImportError as e:
    DEPS_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("AILearningFacade")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class AILearningFacade:
    """
    Manages Devin's ability to learn by logging interactions and
    dispatching training jobs to the AILearningServer.
    """
    def __init__(
        self,
        server_url: str = "http://127.0.0.1:5005",
        data_storage_path: str = "devin_learning_data"
    ):
        if not DEPS_AVAILABLE:
            raise ImportError(f"A required library is missing. Error: {_import_error}")
            
        self.server_url = server_url
        self.session = requests.Session()
        self.data_storage_path = Path(data_storage_path)
        self.data_storage_path.mkdir(parents=True, exist_ok=True)
        self.interaction_log: List[Dict[str, Any]] = []
        logger.info(f"AILearningFacade initialized. Server: {server_url}")

    def log_supervised_pair(self, interaction_id: str, prompt: str, ideal_completion: str):
        """Logs a high-quality prompt/completion pair for fine-tuning."""
        log_entry = {
            "interaction_id": interaction_id,
            "type": "SUPERVISED_FINE_TUNE_PAIR",
            "data": {"prompt": prompt, "completion": ideal_completion}
        }
        self.interaction_log.append(log_entry)
        logger.info(f"Logged supervised learning pair for interaction '{interaction_id}'.")

    def create_fine_tuning_dataset(self, dataset_name: str, interaction_ids: List[str]) -> Optional[Path]:
        """Creates a fine-tuning dataset file from logged interactions."""
        logger.info(f"Creating fine-tuning dataset '{dataset_name}'...")
        dataset_content = []
        for log in self.interaction_log:
            if log["interaction_id"] in interaction_ids and log["type"] == "SUPERVISED_FINE_TUNE_PAIR":
                # A common format is JSONL with {"messages": [{"role": "user", ...}, {"role": "assistant", ...}]}
                formatted_entry = {
                    "messages": [
                        {"role": "user", "content": log["data"]["prompt"]},
                        {"role": "assistant", "content": log["data"]["completion"]}
                    ]
                }
                dataset_content.append(formatted_entry)
        
        if not dataset_content:
            logger.error("No suitable data found in logs for the provided interaction IDs.")
            return None
            
        dataset_path = self.data_storage_path / f"{dataset_name}.jsonl"
        with open(dataset_path, "w") as f:
            for item in dataset_content:
                f.write(json.dumps(item) + "\n")
        
        logger.info(f"Dataset saved to '{dataset_path}' with {len(dataset_content)} examples.")
        return dataset_path

    def start_training_job(self, model_name: str, parameters: Dict) -> Optional[str]:
        """
        Submits a training job to the AILearningServer.
        
        Returns:
            The job_id if submission was successful, otherwise None.
        """
        logger.info(f"Submitting training job for model '{model_name}' to the server...")
        payload = {"model_name": model_name, "parameters": parameters}
        try:
            response = self.session.post(f"{self.server_url}/train", json=payload)
            response.raise_for_status()
            return response.json().get("job_id")
        except requests.RequestException as e:
            logger.error(f"Failed to submit training job to server: {e}")
            return None

    def get_training_job_status(self, job_id: str) -> Optional[Dict]:
        """Polls the AILearningServer for the status of a job."""
        try:
            response = self.session.get(f"{self.server_url}/train/status/{job_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get job status from server: {e}")
            return None


# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Integrated AI Learning Facade Prototype 🧠⚙️ ===")
    print("=========================================================")

    if not DEPS_AVAILABLE:
        print(f"\nERROR: A required library is missing. Error: {_import_error}")
    else:
        print("!!! PREREQUISITE: This client requires the `ai_learning_server.py` to be running first. !!!")
        print("\n1. In a separate terminal, run: python -m servers.ai_learning_server")
        print("2. Once the server is running, run this script.\n")

        # 1. Initialize the facade
        facade = AILearningFacade(server_url="http://127.0.0.1:5005")
        
        try:
            # 2. Log some successful interactions (client-side)
            facade.log_supervised_pair(
                interaction_id="task_abc",
                prompt="Write a Python function to check for palindromes.",
                ideal_completion="def is_palindrome(s):\n    return s == s[::-1]"
            )
            facade.log_supervised_pair(
                interaction_id="task_def",
                prompt="Generate a bash command to list all running Docker containers.",
                ideal_completion="docker ps -a"
            )
            
            # 3. Create a dataset file from the logs (client-side)
            dataset_file = facade.create_fine_tuning_dataset(
                dataset_name="coding_examples_v1",
                interaction_ids=["task_abc", "task_def"]
            )
            if not dataset_file:
                raise RuntimeError("Failed to create dataset file.")

            # 4. Submit a training job to the server
            print("--- 1. Submitting training job to the AI Learning Server ---")
            job_id = facade.start_training_job(
                model_name="dummy_classifier",
                parameters={"epochs": 5, "learning_rate": 0.01, "dataset_path": str(dataset_file)}
            )
            
            if not job_id:
                raise RuntimeError("Failed to submit job to the server.")
            
            print(f"Server accepted the training job. Job ID: {job_id[:8]}...")
            
            # 5. Poll for the job's completion
            print("\n--- 2. Polling for training status ---")
            while True:
                status_data = facade.get_training_job_status(job_id)
                if not status_data:
                    print("  Could not retrieve job status. Halting.")
                    break
                
                print(f"  Current job status: {status_data['status']}")
                
                if status_data['status'] in ["COMPLETED", "FAILED"]:
                    print("\n--- 3. Job finished ---")
                    print("Final Result from Server:")
                    print(json.dumps(status_data, indent=2))
                    break
                time.sleep(1)

        except requests.ConnectionError:
            print("\n[FATAL ERROR] Could not connect to the AILearningServer. Please ensure it is running.")
        except Exception as e:
            logger.error(f"Demo failed: {e}", exc_info=True)

    print("\n=========================================================")
    print("=== AI Learning Facade Prototype Complete ===")
    print("=========================================================")
