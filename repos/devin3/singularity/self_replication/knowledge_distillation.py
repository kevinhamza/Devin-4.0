# Devin/singularity/self_replication/knowledge_distillation.py
# Purpose: Provides a complete pipeline for an AGI to improve a smaller,
#          local "student" model by learning from a larger "teacher" model.

import logging
import json
from pathlib import Path
from typing import List, Dict, Optional

try:
    # --- Integration with other Devin modules ---
    from modules.all_ais_modules import AIAgent, AIProvider
    from modules.ai_learning_module import AILearningFacade
    from modules.all_otherais_modules import GenericOpenAICompatibleModule
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("KnowledgeDistillation")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)


class KnowledgeDistillationPipeline:
    """
    Orchestrates the entire workflow of generating data from a teacher model
    and using it to fine-tune a student model.
    """
    def __init__(self, ai_agent: AIAgent, learning_facade: AILearningFacade, student_model_client: GenericOpenAICompatibleModule):
        if not DEVIN_CORE_AVAILABLE:
            raise ImportError(f"A core Devin module is missing. Error: {_import_error}")
        
        self.agent = ai_agent
        self.learning_facade = learning_facade
        self.student_client = student_model_client
        self.teacher_model = "gpt-4o" # Use the most powerful model as the teacher
        self.output_dir = Path("./distillation_data")
        self.output_dir.mkdir(exist_ok=True)

    def generate_synthetic_prompts(self, topic: str, count: int) -> Optional[List[str]]:
        """Uses the teacher model to generate a diverse set of training prompts."""
        logger.info(f"Generating {count} synthetic prompts on the topic: '{topic}'...")
        prompt = (
            "You are a master curriculum designer for training AI models. Your task is to generate a set of diverse, high-quality prompts. "
            f"The topic is: '{topic}'. The prompts should cover a range of difficulties, from basic definitions to complex, multi-step problems. "
            f"Respond ONLY with a single, valid JSON object containing a single key 'prompts', which is a list of exactly {count} strings."
        )
        try:
            response = self.agent.get_general_chat_response([{"role": "user", "content": prompt}], provider=AIProvider.OPENAI)
            data = json.loads(response)
            prompts = data['prompts']
            logger.info("Synthetic prompts generated successfully.")
            return prompts
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to generate or parse synthetic prompts: {e}")
            return None

    def create_training_dataset(self, prompts: List[str], dataset_name: str) -> Optional[Path]:
        """Uses the teacher model to answer the prompts, creating a fine-tuning dataset."""
        dataset_path = self.output_dir / f"{dataset_name}.jsonl"
        logger.info(f"Creating training dataset at '{dataset_path}'...")
        
        with open(dataset_path, 'w') as f:
            for i, p in enumerate(prompts):
                logger.info(f"  Getting teacher's response for prompt {i+1}/{len(prompts)}...")
                # Get a high-quality, detailed response from the teacher model
                teacher_response = self.agent.get_general_chat_response(
                    [{"role": "user", "content": p}],
                    provider=AIProvider.OPENAI,
                    config={"model": self.teacher_model}
                )
                if not teacher_response:
                    logger.warning(f"  Skipping prompt due to empty response from teacher.")
                    continue
                
                # Format for fine-tuning (OpenAI's chat format)
                record = {"messages": [{"role": "user", "content": p}, {"role": "assistant", "content": teacher_response}]}
                f.write(json.dumps(record) + "\n")
        
        logger.info("Training dataset created successfully.")
        return dataset_path

    def start_fine_tuning_job(self, dataset_path: Path) -> Optional[str]:
        """Submits the fine-tuning job to the AILearningServer."""
        logger.info(f"Submitting fine-tuning job for dataset '{dataset_path}'...")
        # In a real system, we'd specify the base model to fine-tune.
        # Here, we use a conceptual model name.
        job_id = self.learning_facade.start_training_job(
            model_name="conceptual_student_model",
            parameters={"dataset_path": str(dataset_path), "epochs": 3}
        )
        if not job_id:
            logger.error("Failed to submit fine-tuning job.")
            return None

        # Poll for completion
        logger.info(f"Waiting for fine-tuning job {job_id} to complete...")
        while True:
            status = self.learning_facade.get_training_job_status(job_id)
            if not status or status.get("status") == "FAILED":
                logger.error("Fine-tuning job failed.")
                return None
            if status.get("status") == "COMPLETED":
                logger.info("Fine-tuning job completed successfully!")
                return status.get("fine_tuned_model_id", "student-model-v1")
            time.sleep(2)

    def run_distillation_cycle(self, topic: str, prompt_count: int):
        """Runs the full distillation workflow."""
        # 1. Generate Data
        prompts = self.generate_synthetic_prompts(topic, prompt_count)
        if not prompts: return

        # 2. Create Dataset
        dataset_path = self.create_training_dataset(prompts, f"{topic.replace(' ', '_')}_dataset")
        if not dataset_path: return

        # 3. Fine-Tune Student Model
        new_model_id = self.start_fine_tuning_job(dataset_path)
        if not new_model_id: return
            
        logger.info(f"Knowledge distillation cycle complete. New student model ID: '{new_model_id}'")

# --- Example Usage ---
if __name__ == "__main__":
    import os
    print("=========================================================")
    print("=== Knowledge Distillation Pipeline (Live Demo) 🧠🎓 ===")
    print("=========================================================")
    
    # Check for all required components
    if not DEVIN_CORE_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        print("\nERROR: This demo requires the full Devin core and an OPENAI_API_KEY environment variable.")
    else:
        print("\n!!! PREREQUISITE: This demo requires the `AILearningServer` to be running. !!!")
        print("1. In a separate terminal, run: python -m servers.ai_learning_server")
        print("2. Once the server is running, run this script.\n")
        
        try:
            # --- 1. Initialize all of Devin's core components ---
            print("--- Initializing Devin's core systems for distillation... ---")
            agent = AIAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))
            learning_facade = AILearningFacade() # Connects to the server on localhost
            # The student model would be a local model, e.g., served via Ollama
            student_client = GenericOpenAICompatibleModule(model_name="llama3", api_base_url="http://localhost:11434/v1")
            
            # --- 2. Instantiate and run the distillation pipeline ---
            pipeline = KnowledgeDistillationPipeline(
                ai_agent=agent,
                learning_facade=learning_facade,
                student_model_client=student_client
            )
            
            pipeline.run_distillation_cycle(topic="Explain object-oriented programming in Python", prompt_count=5)

        except Exception as e:
            logger.error(f"Demo failed to run. Is the AILearningServer running? Error: {e}", exc_info=True)

    print("\n=========================================================")
    print("=== Knowledge Distillation Demo Complete ===")
    print("=========================================================")
