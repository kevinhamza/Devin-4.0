# Devin/servers/task_orchestrator.py
# Purpose: The central task management and execution engine for Devin.
#          Manages a queue of tasks and a pool of worker threads.

import logging
import queue
import threading
import uuid
import importlib
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# Configure basic logging
logger = logging.getLogger("TaskOrchestrator")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

@dataclass
class Task:
    """Represents a single unit of work for the orchestrator."""
    task_id: str
    tool_name: str
    parameters: Dict[str, Any]
    status: str = "PENDING"
    result: Optional[Any] = None
    error: Optional[str] = None
    submitted_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

class TaskOrchestrator:
    """
    Manages a thread-safe task queue and a pool of worker threads
    that can execute any registered tool from the Devin project.
    """
    def __init__(self, num_workers: int = 5):
        self.task_queue: queue.Queue = queue.Queue()
        self.tasks: Dict[str, Task] = {}
        self.lock = threading.Lock()
        self.num_workers = num_workers
        self.workers: List[threading.Thread] = []
        self._stop_event = threading.Event()

    def _worker_loop(self):
        """The main loop for each worker thread."""
        while not self._stop_event.is_set():
            try:
                task_id = self.task_queue.get(timeout=1)
                if task_id is None: # Sentinel value to stop
                    break
                
                with self.lock:
                    task = self.tasks[task_id]
                    task.status = "RUNNING"
                
                logger.info(f"Worker {threading.get_ident()} picked up task {task.task_id} ({task.tool_name})")
                
                try:
                    # --- Dynamic Tool Dispatch ---
                    module_path, function_name = task.tool_name.rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    
                    # This assumes the tool is a function. A more complex dispatcher
                    # could handle classes and methods.
                    tool_function = getattr(module, function_name)
                    
                    # Execute the tool
                    task_result = tool_function(**task.parameters)
                    
                    with self.lock:
                        task.status = "COMPLETED"
                        task.result = task_result
                        task.completed_at = datetime.now()

                except Exception as e:
                    logger.error(f"Task {task.task_id} failed: {e}", exc_info=True)
                    with self.lock:
                        task.status = "FAILED"
                        task.error = str(e)
                        task.completed_at = datetime.now()
                
                self.task_queue.task_done()

            except queue.Empty:
                continue

    def start(self):
        """Starts the worker threads."""
        logger.warning(f"Starting Task Orchestrator with {self.num_workers} workers.")
        for _ in range(self.num_workers):
            worker = threading.Thread(target=self._worker_loop)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)

    def shutdown(self):
        """Stops all worker threads gracefully."""
        logger.warning("Shutting down Task Orchestrator...")
        self._stop_event.set()
        # Unblock any waiting workers
        for _ in self.workers:
            self.task_queue.put(None)
        for worker in self.workers:
            worker.join()
        logger.info("All worker threads have been stopped.")

    def submit_task(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Submits a new task to the queue."""
        task_id = str(uuid.uuid4())
        task = Task(task_id=task_id, tool_name=tool_name, parameters=parameters)
        
        with self.lock:
            self.tasks[task_id] = task
        
        self.task_queue.put(task_id)
        logger.info(f"Submitted new task {task_id} for tool '{tool_name}'")
        return task_id

    def get_task_status(self, task_id: str) -> Optional[Task]:
        """Retrieves the status and result of a task."""
        with self.lock:
            return self.tasks.get(task_id)

# --- Example Usage ---

# Define some dummy functions to act as our "tools" for the demo
def long_running_scan(target: str, duration: int):
    logger.info(f"Starting a long scan on '{target}' for {duration} seconds...")
    time.sleep(duration)
    return {"target": target, "status": "scan complete", "ports_found": [22, 80, 443]}

def quick_calculation(x: int, y: int):
    logger.info(f"Calculating {x} + {y}...")
    time.sleep(1)
    return {"result": x + y}


if __name__ == "__main__":
    print("=========================================================")
    print("=== Multi-Threaded Task Orchestrator Prototype 🚀⚙️ ===")
    print("=========================================================")
    
    # We need to add our current directory to the path for dynamic import to work
    import sys
    sys.path.append(os.getcwd())
    
    orchestrator = TaskOrchestrator(num_workers=3)
    orchestrator.start()
    
    try:
        # 1. Submit a batch of tasks
        print("\n--- Submitting a batch of concurrent tasks ---")
        task1_id = orchestrator.submit_task("servers.task_orchestrator.long_running_scan", {"target": "10.0.0.1", "duration": 8})
        task2_id = orchestrator.submit_task("servers.task_orchestrator.quick_calculation", {"x": 100, "y": 200})
        task3_id = orchestrator.submit_task("servers.task_orchestrator.long_running_scan", {"target": "api.example.com", "duration": 6})
        task4_id = orchestrator.submit_task("servers.task_orchestrator.quick_calculation", {"x": 5, "y": 7})
        task_ids = [task1_id, task2_id, task3_id, task4_id]

        # 2. Monitor their status until all are complete
        print("\n--- Monitoring task progress ---")
        all_done = False
        while not all_done:
            all_done = True
            print("\n--- Current Statuses ---")
            for tid in task_ids:
                task = orchestrator.get_task_status(tid)
                print(f"  Task {tid[:8]}... ({task.tool_name.split('.')[-1]}): {task.status}")
                if task.status in ["PENDING", "RUNNING"]:
                    all_done = False
            time.sleep(2)
            
        print("\n\n--- All tasks complete. Final Results: ---")
        for tid in task_ids:
            task = orchestrator.get_task_status(tid)
            print(f"\n  Task {tid[:8]}:")
            print(f"    Status: {task.status}")
            print(f"    Result: {task.result}")

    finally:
        orchestrator.shutdown()

    print("\n=========================================================")
    print("=== Task Orchestrator Prototype Complete ===")
    print("=========================================================")
