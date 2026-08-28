# Devin/prototypes/scheduler_prototypes.py
# Purpose: Prototype implementations for scheduling tasks at specific times or intervals.

import logging
import time
import functools
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum

# --- Conceptual Import for Scheduling Library ---
try:
    # Requires 'schedule': pip install schedule
    import schedule
    SCHEDULE_LIB_AVAILABLE = True
    print("Conceptual: Assuming 'schedule' library is available.")
except ImportError:
    print("WARNING: 'schedule' library not found (pip install schedule). Scheduler prototype will be non-functional placeholder.")
    schedule = None # type: ignore
    SCHEDULE_LIB_AVAILABLE = False

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("SchedulerPrototype")

# --- Type Definitions ---
JobFunc = Callable[..., Any] # Type hint for the function to be scheduled

class IntervalUnit(str, Enum):
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"

class Weekday(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class TaskSchedulerPrototype:
    """
    Conceptual prototype for scheduling functions to run periodically or at specific times.
    Uses the 'schedule' library conceptually. Manages a background thread to run pending jobs.
    """

    def __init__(self):
        """Initializes the scheduler."""
        if not SCHEDULE_LIB_AVAILABLE:
            logger.error("Cannot initialize scheduler: 'schedule' library not installed.")
            self._scheduler_instance = None # Indicate library unavailable
            return

        # Use the main schedule object from the library
        self._scheduler_instance = schedule
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_run_loop = threading.Event()
        logger.info("TaskSchedulerPrototype initialized (using 'schedule' library conceptually).")

    def _job_wrapper(self, job_func: JobFunc, *args, **kwargs):
        """Internal wrapper to execute the job function and catch exceptions."""
        func_name = getattr(job_func, '__name__', repr(job_func))
        logger.info(f"Scheduler executing job: {func_name} with args={args}, kwargs={kwargs}")
        try:
            job_func(*args, **kwargs)
            logger.debug(f"Job {func_name} completed.")
        except Exception as e:
            logger.exception(f"Error executing scheduled job {func_name}: {e}") # Log traceback

    def schedule_interval_job(self,
                              interval_value: int,
                              unit: IntervalUnit,
                              job_func: JobFunc,
                              *args, **kwargs) -> Optional[Any]:
        """
        Schedules a job to run every 'interval_value' of 'unit'.

        Args:
            interval_value (int): The number of units between runs.
            unit (IntervalUnit): The time unit (seconds, minutes, hours, days, weeks).
            job_func (JobFunc): The function to execute.
            *args: Positional arguments to pass to job_func.
            **kwargs: Keyword arguments to pass to job_func.

        Returns:
            Optional[Any]: The job object created by the schedule library, or None on error.
                           Can be used with cancel_job.
        """
        if not self._scheduler_instance: return None
        logger.info(f"Scheduling job '{getattr(job_func, '__name__', 'unknown')}' to run every {interval_value} {unit.value}")
        try:
            schedule_unit = getattr(self._scheduler_instance.every(interval_value), unit.value)
            # Use wrapper to handle function arguments and exceptions
            wrapped_job = functools.partial(self._job_wrapper, job_func, *args, **kwargs)
            job = schedule_unit.do(wrapped_job)
            logger.info(f"  - Job scheduled: {job}")
            return job
        except Exception as e:
            logger.error(f"Failed to schedule interval job: {e}")
            return None

    def schedule_daily_at(self, time_str: str, job_func: JobFunc, *args, **kwargs) -> Optional[Any]:
        """
        Schedules a job to run every day at a specific time.

        Args:
            time_str (str): The time string in HH:MM or HH:MM:SS format (24-hour clock).
            job_func (JobFunc): The function to execute.
            *args: Positional arguments to pass to job_func.
            **kwargs: Keyword arguments to pass to job_func.

        Returns:
            Optional[Any]: The job object created by the schedule library, or None on error.
        """
        if not self._scheduler_instance: return None
        logger.info(f"Scheduling job '{getattr(job_func, '__name__', 'unknown')}' to run daily at {time_str}")
        try:
            wrapped_job = functools.partial(self._job_wrapper, job_func, *args, **kwargs)
            job = self._scheduler_instance.every().day.at(time_str).do(wrapped_job)
            logger.info(f"  - Job scheduled: {job}")
            return job
        except Exception as e: # Catches potential schedule.ScheduleError for bad time format
            logger.error(f"Failed to schedule daily job for time '{time_str}': {e}")
            return None

    def schedule_weekly_at(self, day_of_week: Weekday, time_str: str, job_func: JobFunc, *args, **kwargs) -> Optional[Any]:
        """
        Schedules a job to run on a specific day of the week at a specific time.

        Args:
            day_of_week (Weekday): The enum member for the day (e.g., Weekday.MONDAY).
            time_str (str): The time string in HH:MM or HH:MM:SS format.
            job_func (JobFunc): The function to execute.
            *args: Positional arguments to pass to job_func.
            **kwargs: Keyword arguments to pass to job_func.

        Returns:
            Optional[Any]: The job object created by the schedule library, or None on error.
        """
        if not self._scheduler_instance: return None
        logger.info(f"Scheduling job '{getattr(job_func, '__name__', 'unknown')}' weekly on {day_of_week.value} at {time_str}")
        try:
            schedule_day = getattr(self._scheduler_instance.every(), day_of_week.value)
            wrapped_job = functools.partial(self._job_wrapper, job_func, *args, **kwargs)
            job = schedule_day.at(time_str).do(wrapped_job)
            logger.info(f"  - Job scheduled: {job}")
            return job
        except Exception as e:
            logger.error(f"Failed to schedule weekly job for {day_of_week.value} at {time_str}: {e}")
            return None

    def cancel_job(self, job_to_cancel: Any) -> bool:
        """
        Cancels a previously scheduled job.

        Args:
            job_to_cancel (Any): The job object returned by one of the schedule_* methods.

        Returns:
            bool: True if cancellation was attempted, False otherwise.
        """
        if not self._scheduler_instance: return False
        if not job_to_cancel:
             logger.warning("Cannot cancel job: Invalid job object provided.")
             return False
        logger.info(f"Cancelling scheduled job: {job_to_cancel}")
        try:
            self._scheduler_instance.cancel_job(job_to_cancel)
            logger.info("  - Job cancelled successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel job {job_to_cancel}: {e}")
            return False

    def list_jobs(self) -> List[Any]:
        """Returns a list of all currently scheduled jobs."""
        if not self._scheduler_instance: return []
        return self._scheduler_instance.get_jobs()

    # --- Background Execution Loop ---
    def _run_loop(self):
        """Internal method to run pending scheduled jobs periodically."""
        if not self._scheduler_instance: return
        logger.info("Starting scheduler background thread...")
        while not self._stop_run_loop.is_set():
            try:
                self._scheduler_instance.run_pending()
            except Exception as e:
                 logger.error(f"Error during schedule.run_pending(): {e}")
            # Sleep until the next check is needed or for a short interval
            # schedule.idle_seconds() tells how long until the *next* job
            # Use min(idle_seconds, some_max_interval) to ensure loop isn't blocked too long
            # Simple approach: sleep for 1 second
            time.sleep(1)
        logger.info("Scheduler background thread stopped.")

    def start(self, run_in_background: bool = True):
        """Starts the scheduler execution loop."""
        if not self._scheduler_instance:
             logger.error("Cannot start scheduler: Not initialized correctly (schedule library missing?).")
             return

        if run_in_background:
            if self._scheduler_thread and self._scheduler_thread.is_alive():
                logger.warning("Scheduler background thread already running.")
                return
            self._stop_run_loop.clear()
            self._scheduler_thread = threading.Thread(target=self._run_loop, daemon=True)
            self._scheduler_thread.start()
        else:
             # Run in foreground (blocking) - useful for simple scripts
             logger.info("Running scheduler in foreground (blocking)... Press Ctrl+C to exit.")
             while True:
                 try:
                      self._scheduler_instance.run_pending()
                      time.sleep(1)
                 except KeyboardInterrupt:
                      logger.info("Foreground scheduler stopped by user.")
                      break

    def stop(self):
        """Stops the background scheduler thread if running."""
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            logger.info("Stopping scheduler background thread...")
            self._stop_run_loop.set()
            self._scheduler_thread.join(timeout=5) # Wait briefly for thread to finish
            if self._scheduler_thread.is_alive():
                 logger.warning("Scheduler thread did not terminate gracefully.")
            self._scheduler_thread = None
        else:
             logger.info("Scheduler background thread not running.")


# --- Example Usage ---
if __name__ == "__main__":
    print("===========================================")
    print("=== Running Task Scheduler Prototype ===")
    print("===========================================")
    print("(Note: Relies on conceptual implementations & 'schedule' library)")

    # Dummy task function for scheduling
    def example_task_func(task_name: str, parameter: Any):
        timestamp = datetime.datetime.now().isoformat()
        logger.info(f"*** Scheduled Task Executing *** Name: '{task_name}', Param: '{parameter}', Time: {timestamp}")
        # In Devin, this function would likely queue a task with the TaskOrchestrator
        # E.g., task_orchestrator.queue_task(task_name, params={'parameter': parameter})

    if not SCHEDULE_LIB_AVAILABLE:
        print("\n'schedule' library not found. Skipping prototype demonstration.")
    else:
        scheduler = TaskSchedulerPrototype()

        # Schedule some jobs
        print("\nScheduling jobs...")
        job1 = scheduler.schedule_interval_job(5, IntervalUnit.SECONDS, example_task_func, "Heartbeat Check", {"details": "Checking system health"})
        job2 = scheduler.schedule_daily_at("10:30", example_task_func, "Daily Report", "Generate summary")
        job3 = scheduler.schedule_weekly_at(Weekday.FRIDAY, "22:00", example_task_func, "Weekly Cleanup", None)

        # List scheduled jobs
        print("\nCurrently Scheduled Jobs:")
        jobs = scheduler.list_jobs()
        for job in jobs:
            print(f"  - {job}")

        # Start the scheduler loop in the background
        print("\nStarting scheduler background thread...")
        scheduler.start(run_in_background=True)

        # Let it run for a bit to see interval job trigger
        print("\nScheduler running in background for ~12 seconds...")
        time.sleep(12)

        # Cancel one of the jobs
        if job3:
             print("\nCancelling weekly job...")
             scheduler.cancel_job(job3)

        print("\nCurrently Scheduled Jobs (after cancel):")
        jobs_after = scheduler.list_jobs()
        for job in jobs_after:
             print(f"  - {job}")

        # Stop the background thread
        print("\nStopping scheduler background thread...")
        scheduler.stop()
        print("Scheduler stopped.")

    print("\n===========================================")
    print("=== Scheduler Prototypes Complete ===")
    print("===========================================")
