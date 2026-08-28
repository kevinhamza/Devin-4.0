# Devin/security/ethical_enforcer/human_override/deadman_switch.py
# Purpose: A fail-safe mechanism that triggers a shutdown if a regular
#          "heartbeat" from the main application is not received.

import logging
import threading
import time
from typing import Callable, Optional

# Configure basic logging
logger = logging.getLogger("DeadmanSwitch")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)


class DeadmanSwitch:
    """
    A watchdog that executes a fail-safe action if not "petted" periodically.
    """
    def __init__(self, timeout_sec: int, fail_safe_action: Callable[[], None]):
        """
        Initializes the Dead Man's Switch.

        Args:
            timeout_sec: The grace period in seconds. If no check-in occurs
                         within this time, the switch triggers.
            fail_safe_action: The function to call when the switch triggers.
                              This function should take no arguments.
        """
        self.timeout = timeout_sec
        self.fail_safe_action = fail_safe_action
        
        self.last_pet_time = 0.0
        self.lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.triggered = False

    def _monitor_loop(self):
        """The main monitoring loop that runs in a background thread."""
        logger.info("Dead man's switch monitor thread started.")
        while not self._stop_event.wait(1.0): # Check every second
            with self.lock:
                time_since_last_pet = time.time() - self.last_pet_time
                
            if time_since_last_pet > self.timeout:
                if not self.triggered:
                    self.triggered = True
                    logger.critical("!!! DEAD MAN'S SWITCH TRIGGERED !!!")
                    logger.critical("No heartbeat received within the timeout period.")
                    self.fail_safe_action()
                break # Exit the thread after triggering

    def pet(self):
        """Resets the timer. The main application must call this periodically."""
        with self.lock:
            self.last_pet_time = time.time()
        logger.debug("Dead man's switch was petted.")

    def start(self):
        """Starts the monitoring service in a background thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Switch is already running.")
            return
            
        logger.warning(f"Dead man's switch armed with a {self.timeout} second timeout.")
        self.pet() # Initial pet to start the timer
        self.triggered = False
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Gracefully disarms and stops the monitoring service."""
        logger.info("Disarming dead man's switch.")
        self._stop_event.set()
        if self._thread:
            self._thread.join()

# --- Example Usage ---
shutdown_flag = threading.Event()

def critical_shutdown_procedure():
    """A sample fail-safe action to be executed when the switch triggers."""
    print("\n----------------------------------------------------")
    print("CRITICAL: Executing fail-safe shutdown procedure!")
    print("----------------------------------------------------")
    # In a real application, this would gracefully close databases,
    # terminate subprocesses, save state, etc.
    shutdown_flag.set()

if __name__ == "__main__":
    print("=========================================================")
    print("=== Dead Man's Switch Prototype 💀⏰ ===")
    print("=========================================================")
    
    # 1. Initialize the switch with a 3-second timeout
    switch = DeadmanSwitch(timeout_sec=3, fail_safe_action=critical_shutdown_procedure)
    
    try:
        # 2. Start the switch
        switch.start()
        
        # 3. Simulate normal operation where the app is responsive
        print("\n--- Simulating normal operation (8 seconds) ---")
        print("The main application will 'pet' the switch every 2 seconds.")
        for i in range(4):
            if shutdown_flag.is_set(): break
            time.sleep(2)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Main app is alive. Petting the switch...")
            switch.pet()

        if not shutdown_flag.is_set():
            # 4. Simulate a crash or freeze
            print("\n\n--- Simulating application freeze (5 seconds) ---")
            print("The main application will now become unresponsive and stop petting the switch.")
            print(f"The switch should trigger in ~3 seconds...")
            time.sleep(5)
        
        # 5. Check the result
        print("\n--- Demo Finished ---")
        if shutdown_flag.is_set():
            print("[SUCCESS] The dead man's switch was triggered as expected.")
        else:
            print("[FAILURE] The switch did not trigger when it should have.")

    finally:
        # 6. Clean up
        switch.stop()

    print("\n=========================================================")
    print("=== Dead Man's Switch Prototype Complete ===")
    print("=========================================================")
