# Devin/servers/automation_server.py
# Purpose: A job scheduler that automates workflows and routines by triggering
#          tasks in the TaskOrchestrator based on a defined schedule.

import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    APS_AVAILABLE = True
except ImportError:
    APS_AVAILABLE = False
    
try:
    from servers.task_orchestrator import TaskOrchestrator, long_running_scan # Import for demo
    DEVIN_CORE_AVAILABLE = True
except ImportError as e:
    DEVIN_CORE_AVAILABLE = False
    _import_error = e

# Configure basic logging
logger = logging.getLogger("AutomationServer")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)

class AutomationServer:
    """
    Reads a job configuration and schedules tasks to be run by the orchestrator.
    """
    def __init__(self, orchestrator: TaskOrchestrator, jobs_config_path: Path):
        if not all([YAML_AVAILABLE, APS_AVAILABLE, DEVIN_CORE_AVAILABLE]):
            raise ImportError(f"A required library or module is missing. YAML: {YAML_AVAILABLE}, APS: {APS_AVAILABLE}. Core Error: {_import_error}")

        self.orchestrator = orchestrator
        self.jobs_config_path = jobs_config_path
        self.scheduler = BackgroundScheduler()

    def _load_and_schedule_jobs(self):
        """Loads jobs from the YAML config and adds them to the scheduler."""
        logger.info(f"Loading automation jobs from '{self.jobs_config_path}'...")
        with open(self.jobs_config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        jobs = config.get('jobs', [])
        if not jobs:
            logger.warning("No automation jobs found in the configuration file.")
            return

        for job in jobs:
            try:
                job_name = job['name']
                schedule = job['schedule']
                task = job['task']
                
                trigger = schedule.pop('trigger')
                
                self.scheduler.add_job(
                    func=self.orchestrator.submit_task,
                    trigger=trigger,
                    id=job_name,
                    name=job_name,
                    kwargs={
                        "tool_name": task['tool_name'],
                        "parameters": task['parameters']
                    },
                    **schedule
                )
                logger.info(f"Scheduled job: '{job_name}' with trigger '{trigger}'")
            except KeyError as e:
                logger.error(f"Failed to schedule job. Missing required key: {e}")
            except Exception as e:
                logger.error(f"Failed to schedule job '{job.get('name', 'N/A')}': {e}")
    
    def start(self):
        """Loads jobs and starts the scheduler."""
        self._load_and_schedule_jobs()
        self.scheduler.start()
        logger.warning("Automation Server started. Scheduled jobs are now active.")

    def shutdown(self):
        """Stops the scheduler."""
        logger.warning("Shutting down Automation Server.")
        self.scheduler.shutdown()

# --- Example Usage ---
if __name__ == "__main__":
    print("=========================================================")
    print("=== Automation Server Prototype 🤖⏰ ===")
    print("=========================================================")
    
    if not all([YAML_AVAILABLE, APS_AVAILABLE, DEVIN_CORE_AVAILABLE]):
        print(f"\nERROR: A required library or module is missing. Please check your installation.")
        print(f"YAML: {YAML_AVAILABLE}, APScheduler: {APS_AVAILABLE}, Core Error: {_import_error}")
    else:
        # 1. Setup a dummy job configuration file for the demo
        jobs_file = Path("automation_jobs.yml")
        demo_jobs_content = """
        jobs:
          - name: "Test Scan Every 8 Seconds"
            schedule:
              trigger: "interval"
              seconds: 8
            task:
              tool_name: "servers.task_orchestrator.long_running_scan"
              parameters:
                target: "scheduled.example.com"
                duration: 3
        """
        jobs_file.write_text(demo_jobs_content)
        
        # We need to add our current directory to the path for dynamic import to work
        import sys
        import os
        sys.path.append(os.getcwd())
        
        # 2. Initialize the backend components
        orchestrator = TaskOrchestrator(num_workers=2)
        automation_server = AutomationServer(orchestrator, jobs_file)
        
        try:
            # 3. Start the services
            orchestrator.start()
            automation_server.start()
            
            print("\nAutomation server is running. A test scan will be triggered every 8 seconds.")
            print("The orchestrator will execute the task. (Press Ctrl+C to exit)")
            
            # Keep the main thread alive to see the scheduled jobs run
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            # 4. Clean up
            automation_server.shutdown()
            orchestrator.shutdown()
            if jobs_file.exists():
                jobs_file.unlink()

    print("\n=========================================================")
    print("=== Automation Server Prototype Complete ===")
    print("=========================================================")
