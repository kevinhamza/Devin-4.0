# Devin/ai_integrations/api_rate_limiter.py # Purpose: Manages rate limits across different AI API integrations to prevent exceeding quotas.

import time
import threading
from collections import deque
from typing import Dict, Optional, Tuple

# Note: This implements a conceptual Token Bucket algorithm for rate limiting.
# It aims to be thread-safe for use in concurrent applications.
# Different APIs might have complex limits (e.g., separate RPM/TPM, different tiers).
# This provides a basic framework that could be extended.

class APIRateLimiter:
    """
    Manages API rate limits using a token bucket algorithm (per service key).

    Allows defining limits (e.g., requests per minute, tokens per minute) for
    different API services and provides a mechanism to wait if the rate limit
    is exceeded, ensuring compliance with API usage policies. Thread-safe.
    """

    def __init__(self):
        """Initializes the rate limiter registry."""
        # Stores the state for each rate-limited service/key
        # Format: { 'service_key': {'tokens': float, 'last_refill_time': float, 'capacity': float, 'refill_rate_per_sec': float} }
        self._limiters: Dict[str, Dict[str, float]] = {}
        # Lock for thread safety when accessing/modifying limiter states
        self._lock = threading.Lock()
        print("APIRateLimiter initialized.")

    def configure_limit(self,
                        service_key: str,
                        max_rate: float,
                        period_seconds: float = 60.0,
                        initial_burst_factor: float = 1.0):
        """
        Configures or updates the rate limit for a specific service key.

        Args:
            service_key (str): A unique identifier for the service/endpoint being limited
                               (e.g., "openai_chat_rpm", "gemini_generate_tpm", "perplexity_api").
            max_rate (float): The maximum number of requests/tokens allowed within the period.
            period_seconds (float): The time period over which max_rate applies (e.g., 60 for per minute).
            initial_burst_factor (float): Factor to determine initial bucket capacity relative
                                          to max_rate (e.g., 1.0 means capacity = max_rate,
                                          1.5 allows for some initial burst).
        """
        if max_rate <= 0 or period_seconds <= 0:
            raise ValueError("max_rate and period_seconds must be positive.")

        capacity = max_rate * max(1.0, initial_burst_factor) # Bucket capacity
        refill_rate_per_sec = max_rate / period_seconds # Tokens refilled per second

        with self._lock:
            # Initialize or update the limiter state for this service key
            current_time = time.monotonic()
            if service_key not in self._limiters:
                 # Start with a full bucket
                self._limiters[service_key] = {
                    'tokens': capacity,
                    'last_refill_time': current_time,
                    'capacity': capacity,
                    'refill_rate_per_sec': refill_rate_per_sec
                }
                print(f"Configured limit for '{service_key}': Capacity={capacity:.2f}, Rate={refill_rate_per_sec:.4f}/s (Max Rate: {max_rate}/{period_seconds}s)")
            else:
                 # Update existing - reset tokens to new capacity? Or keep current?
                 # Let's reset to new capacity for simplicity here.
                 self._limiters[service_key]['tokens'] = capacity
                 self._limiters[service_key]['last_refill_time'] = current_time
                 self._limiters[service_key]['capacity'] = capacity
                 self._limiters[service_key]['refill_rate_per_sec'] = refill_rate_per_sec
                 print(f"Updated limit for '{service_key}': Capacity={capacity:.2f}, Rate={refill_rate_per_sec:.4f}/s (Max Rate: {max_rate}/{period_seconds}s)")


    def _refill_bucket(self, state: Dict[str, float], current_time: float):
        """Helper function to refill tokens based on elapsed time. Must be called within lock."""
        time_elapsed = current_time - state['last_refill_time']
        if time_elapsed > 0:
            tokens_to_add = time_elapsed * state['refill_rate_per_sec']
            state['tokens'] = min(state['capacity'], state['tokens'] + tokens_to_add)
            state['last_refill_time'] = current_time
            # print(f"DEBUG Refill: Added {tokens_to_add:.4f} tokens. Current: {state['tokens']:.2f}") # Debug log

    def acquire(self, service_key: str, tokens_required: float = 1.0, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Attempts to acquire the required number of tokens for a service key.

        If blocking is True, it will wait until tokens are available or timeout occurs.
        If blocking is False, it returns immediately whether tokens were acquired or not.

        Args:
            service_key (str): The identifier of the service limit to check.
            tokens_required (float): The number of tokens needed for this operation (e.g., 1 for RPM,
                                     estimated token count for TPM).
            blocking (bool): If True, wait for tokens. If False, return immediately.
            timeout (Optional[float]): Maximum time in seconds to wait if blocking is True.
                                       If None, waits indefinitely.

        Returns:
            bool: True if tokens were successfully acquired, False otherwise (e.g., non-blocking
                  call found insufficient tokens, or timeout occurred).
        """
        start_wait_time = time.monotonic()
        while True: # Loop handles waiting/retrying check
            with self._lock:
                # Get or initialize state if configure_limit wasn't called first (use defaults?)
                # For robustness, it's better to require configure_limit to be called first.
                if service_key not in self._limiters:
                     # Option 1: Raise Error
                     # raise ValueError(f"Rate limit for '{service_key}' not configured.")
                     # Option 2: Log warning and deny request
                     print(f"Warning: Rate limit for '{service_key}' not configured. Denying request.")
                     return False

                state = self._limiters[service_key]
                current_time = time.monotonic()

                # Refill the bucket based on time passed since last refill/check
                self._refill_bucket(state, current_time)

                # Check if enough tokens are available
                if state['tokens'] >= tokens_required:
                    # Consume tokens and grant request
                    state['tokens'] -= tokens_required
                    # print(f"DEBUG Acquire: Granted {tokens_required:.2f} tokens for '{service_key}'. Remaining: {state['tokens']:.2f}") # Debug log
                    return True
                else:
                    # Not enough tokens
                    if not blocking:
                        # print(f"DEBUG Acquire Non-Blocking: Denied {tokens_required:.2f} tokens for '{service_key}'. Available: {state['tokens']:.2f}") # Debug log
                        return False # Not enough tokens and not waiting

                    # Calculate estimated wait time if blocking
                    tokens_needed = tokens_required - state['tokens']
                    if state['refill_rate_per_sec'] <= 0:
                        # Cannot refill, will never acquire
                        print(f"Warning: Cannot acquire {tokens_required:.2f} tokens for '{service_key}' - refill rate is zero.")
                        return False # Or raise error

                    wait_time_needed = tokens_needed / state['refill_rate_per_sec']

            # --- Wait logic (outside the lock to allow other threads to proceed) ---
            elapsed_wait_time = time.monotonic() - start_wait_time
            if timeout is not None and elapsed_wait_time + wait_time_needed > timeout:
                print(f"Warning: Timeout ({timeout}s) exceeded while waiting for {tokens_required:.2f} tokens for '{service_key}'.")
                return False # Timed out

            # Determine actual sleep duration, considering potential small oversleeps
            sleep_duration = max(0.001, wait_time_needed) # Sleep at least a tiny bit
            # print(f"DEBUG Acquire Blocking: Need {tokens_needed:.2f}, Wait ~{wait_time_needed:.4f}s for '{service_key}'. Sleeping...") # Debug log
            time.sleep(sleep_duration)
            # Loop back to re-check after waiting (another thread might have used tokens)


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- API Rate Limiter Example ---")

    limiter = APIRateLimiter()

    # Configure limits: Service A allows 5 requests per 10 seconds (0.5 req/sec)
    limiter.configure_limit("service_A_rpm", max_rate=5, period_seconds=10)
    # Configure limits: Service B allows 100 tokens per 1 second (100 tokens/sec)
    limiter.configure_limit("service_B_tpm", max_rate=100, period_seconds=1)

    print("\nTesting Service A (5 req / 10 sec):")
    for i in range(7):
        print(f"Request {i+1} for Service A...")
        acquired = limiter.acquire("service_A_rpm", tokens_required=1, blocking=True, timeout=15) # Wait up to 15s
        if acquired:
             print(f"  -> Acquired token {i+1} for Service A at {time.monotonic():.2f}")
             # Simulate doing work
             time.sleep(0.2) # Simulate work taking less time than refill rate allows
        else:
             print(f"  -> Failed to acquire token {i+1} for Service A (Rate limit hit or Timeout).")
             break # Stop trying if we hit limit/timeout

    print("\nTesting Service B (100 tokens / 1 sec):")
    acquired_b1 = limiter.acquire("service_B_tpm", tokens_required=60) # Acquire 60 tokens
    print(f"Acquired 60 tokens for Service B: {acquired_b1}")
    acquired_b2 = limiter.acquire("service_B_tpm", tokens_required=50) # Try to acquire 50 more immediately
    print(f"Acquired 50 more tokens for Service B (non-blocking): {acquired_b2}") # Should likely fail if non-blocking
    acquired_b3 = limiter.acquire("service_B_tpm", tokens_required=50, blocking=False) # Explicit non-blocking check
    print(f"Acquired 50 more tokens for Service B (non-blocking explicitly): {acquired_b3}") # Should likely fail
    print("Waiting 0.6 seconds for refill...")
    time.sleep(0.6) # Wait > 0.5s for bucket to refill enough for 50 tokens (100/sec rate)
    acquired_b4 = limiter.acquire("service_B_tpm", tokens_required=50, blocking=True, timeout=1)
    print(f"Acquired 50 more tokens for Service B after waiting: {acquired_b4}") # Should succeed

    # --- Conceptual Thread Safety Test ---
    print("\nTesting Thread Safety (Conceptual)...")
    results = defaultdict(int)
    results_lock = threading.Lock()
    test_service_key = "thread_test_rpm"
    limiter.configure_limit(test_service_key, max_rate=10, period_seconds=1) # 10 req/sec

    def worker_thread(worker_id):
        for i in range(5): # Each thread tries 5 requests
            print(f"Thread {worker_id}: Attempting request {i+1}...")
            if limiter.acquire(test_service_key, blocking=True, timeout=2):
                 print(f"Thread {worker_id}: Acquired request {i+1}!")
                 with results_lock: results[worker_id] += 1
                 time.sleep(random.uniform(0.05, 0.15)) # Simulate work
            else:
                 print(f"Thread {worker_id}: FAILED request {i+1} (Timeout/Limit)")

    threads = []
    num_threads = 5 # Start 5 threads concurrently
    for i in range(num_threads):
        thread = threading.Thread(target=worker_thread, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join() # Wait for all threads to finish

    print("\nThread Safety Test Results (Acquired counts per thread):")
    total_acquired = 0
    for i in range(num_threads):
        print(f"  Thread {i}: {results[i]} requests acquired.")
        total_acquired += results[i]
    print(f"Total requests acquired by {num_threads} threads: {total_acquired} (Max expected ~10-12 within ~1 sec + timeout)") # Rough estimate

    print("\n--- End Example ---")
