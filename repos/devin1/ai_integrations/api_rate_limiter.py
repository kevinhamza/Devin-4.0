"""
api_rate_limiter.py
-------------------
Handles rate limiting for external API calls to prevent exceeding usage limits.
This module is designed to ensure that API integrations adhere to rate limits imposed
by external services such as ChatGPT, Copilot, Gemini, and others.
"""

import time
import threading
from collections import defaultdict
from typing import Callable, Dict, Any

class APIRateLimiter:
    """
    A class to manage API rate limiting across multiple services.
    """
    def __init__(self):
        self.limits = defaultdict(lambda: {"limit": 0, "interval": 0})
        self.lock = threading.Lock()
        self.calls = defaultdict(list)

    def set_limit(self, api_name: str, limit: int, interval: int):
        """
        Configures the rate limit for a specific API.

        Args:
            api_name (str): Name of the API.
            limit (int): Maximum number of calls allowed.
            interval (int): Time window in seconds for the rate limit.
        """
        with self.lock:
            self.limits[api_name]["limit"] = limit
            self.limits[api_name]["interval"] = interval
            self.calls[api_name] = []

    def is_request_allowed(self, api_name: str) -> bool:
        """
        Checks if a new request can be made to the given API.

        Args:
            api_name (str): Name of the API.

        Returns:
            bool: True if the request is allowed, False otherwise.
        """
        with self.lock:
            if api_name not in self.limits:
                return True  # No limits defined
            
            current_time = time.time()
            interval = self.limits[api_name]["interval"]
            self.calls[api_name] = [
                call for call in self.calls[api_name] if current_time - call < interval
            ]

            if len(self.calls[api_name]) < self.limits[api_name]["limit"]:
                self.calls[api_name].append(current_time)
                return True

            return False

    def execute_request(self, api_name: str, function: Callable, *args, **kwargs) -> Any:
        """
        Executes a request if it is within the rate limit.

        Args:
            api_name (str): Name of the API.
            function (Callable): Function to execute for the API request.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            Any: Result of the function call, or None if the request is denied.
        """
        if self.is_request_allowed(api_name):
            return function(*args, **kwargs)
        else:
            raise Exception(f"Rate limit exceeded for API: {api_name}")

    def wait_and_execute(self, api_name: str, function: Callable, *args, **kwargs) -> Any:
        """
        Waits if necessary and then executes the request within rate limits.

        Args:
            api_name (str): Name of the API.
            function (Callable): Function to execute for the API request.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            Any: Result of the function call.
        """
        while not self.is_request_allowed(api_name):
            time.sleep(0.1)
        return function(*args, **kwargs)


# Example usage
if __name__ == "__main__":
    limiter = APIRateLimiter()

    # Configure rate limits for an API
    limiter.set_limit("ChatGPT", limit=5, interval=60)

    def example_request(api_name):
        print(f"Request to {api_name} executed at {time.time()}")

    # Simulate API requests
    for i in range(10):
        try:
            limiter.execute_request("ChatGPT", example_request, "ChatGPT")
        except Exception as e:
            print(e)
        time.sleep(10)
