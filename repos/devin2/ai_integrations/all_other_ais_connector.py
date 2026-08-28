# Devin/ai_integrations/all_other_ais_connector.py # For all other ais.

import os
import time
import json
import requests # Using requests library for HTTP calls
from typing import Dict, Any, List, Optional, Union, Literal

# --- Constants ---
DEFAULT_TIMEOUT_SECONDS = 120
MAX_RETRIES = 2
INITIAL_RETRY_DELAY_SECONDS = 1

# Define Authentication Info structure
AuthType = Literal['bearer', 'api_key_header', 'none']
AuthInfo = Dict[str, Union[str, AuthType]] # Example: {'type': 'bearer', 'key_env_var': 'SOME_API_KEY'}

class GenericAIConnector:
    """
    A generic connector for interacting with various AI APIs that may not have
    a dedicated connector. Requires the calling code to know the specific API's
    endpoint structure, request format, and response format.

    Handles basic HTTP requests, authentication types, and simple retry logic.
    """

    def __init__(self,
                 api_base_url: str,
                 auth_info: Optional[AuthInfo] = None,
                 default_headers: Optional[Dict[str, str]] = None):
        """
        Initializes the GenericAIConnector.

        Args:
            api_base_url (str): The base URL for the target AI API.
            auth_info (Optional[AuthInfo]): Dictionary describing the authentication method.
                Examples:
                - {'type': 'bearer', 'key_env_var': 'SOME_API_KEY'}
                - {'type': 'api_key_header', 'header_name': 'X-API-Key', 'key_env_var': 'ANOTHER_KEY'}
                - {'type': 'none'} or None for APIs without authentication.
                *** API keys are read from environment variables specified by 'key_env_var'. ***
            default_headers (Optional[Dict[str, str]]): Any default headers to include in all requests.
        """
        if not api_base_url:
            raise ValueError("api_base_url is required for GenericAIConnector")

        self.api_base_url = api_base_url.strip('/')
        self.auth_info = auth_info or {'type': 'none'}
        self.default_headers = default_headers or {}
        self.api_key = None

        # Load API key securely based on auth_info
        auth_type = self.auth_info.get('type', 'none')
        if auth_type != 'none':
            key_env_var = self.auth_info.get('key_env_var')
            if not key_env_var:
                 print(f"WARNING: 'key_env_var' missing in auth_info for auth type '{auth_type}'. Authentication might fail.")
            else:
                self.api_key = os.environ.get(key_env_var)
                if not self.api_key:
                    print(f"WARNING: API key environment variable '{key_env_var}' not set. Authentication might fail.")

        print(f"GenericAIConnector initialized (Base URL: {self.api_base_url}, Auth Type: {auth_type})")

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepares headers including authentication based on auth_info."""
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        headers.update(self.default_headers) # Add any user-defined default headers

        auth_type = self.auth_info.get('type', 'none')

        if self.api_key: # Only add auth header if key was successfully loaded
            if auth_type == 'bearer':
                headers["Authorization"] = f"Bearer {self.api_key}"
            elif auth_type == 'api_key_header':
                header_name = self.auth_info.get('header_name')
                if header_name:
                    headers[header_name] = self.api_key
                else:
                    print("WARNING: 'header_name' missing in auth_info for 'api_key_header' type.")
        elif auth_type != 'none':
             print("Warning: Attempting authenticated request without a loaded API key.")

        return headers

    def send_request(self,
                     endpoint: str,
                     method: Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] = 'POST',
                     payload: Optional[Dict[str, Any]] = None,
                     params: Optional[Dict[str, Any]] = None
                    ) -> Optional[Dict[str, Any]]:
        """
        Sends a generic request to the configured API endpoint.

        Args:
            endpoint (str): The specific API endpoint path (e.g., "/v1/completions", "/generate").
            method (Literal['GET', 'POST', ...]): The HTTP method to use. Defaults to 'POST'.
            payload (Optional[Dict[str, Any]]): The JSON body for POST/PUT/PATCH requests.
            params (Optional[Dict[str, Any]]): URL query parameters for GET requests.

        Returns:
            Optional[Dict[str, Any]]: The parsed JSON response from the API,
                                      or None if the request failed after retries.
                                      The caller is responsible for interpreting this dictionary
                                      based on the specific API's documentation.
        """
        full_url = f"{self.api_base_url}/{endpoint.lstrip('/')}"
        headers = self._prepare_headers()

        print(f"\nSending {method} request to Generic AI API: {full_url}...")
        # print(f"  - Payload Preview: {str(payload)[:500]}...") # Be cautious logging sensitive data

        current_retry = 0
        while current_retry <= MAX_RETRIES:
            try:
                response = requests.request( # Use requests.request for flexibility
                    method=method.upper(),
                    url=full_url,
                    headers=headers,
                    json=payload if method.upper() in ['POST', 'PUT', 'PATCH'] else None,
                    params=params if method.upper() == 'GET' else None,
                    timeout=DEFAULT_TIMEOUT_SECONDS
                )
                response.raise_for_status() # Check for HTTP errors (4xx, 5xx)
                print("  - Request successful.")
                # Try to parse JSON, but handle potential empty or non-JSON responses
                try:
                     return response.json()
                except json.JSONDecodeError:
                     print("  - Warning: Response was not valid JSON. Returning raw text.")
                     # Depending on need, might return response.text or just None
                     return {"raw_response": response.text} # Return text in a dict

            except requests.exceptions.ConnectionError as e:
                 print(f"  - Error: Cannot connect to API at {self.api_base_url}. ({e})")
                 return None # Connection errors usually aren't retryable immediately
            except requests.exceptions.Timeout as e:
                 print(f"  - Error: Request timed out after {DEFAULT_TIMEOUT_SECONDS}s (Attempt {current_retry+1}/{MAX_RETRIES+1}): {e}")
                 # Optionally retry timeouts
                 if current_retry < MAX_RETRIES:
                     delay = (INITIAL_RETRY_DELAY_SECONDS * (2 ** current_retry)) + random.uniform(0, 1)
                     print(f"    - Retrying after {delay:.2f} seconds...")
                     time.sleep(delay)
                     current_retry += 1
                 else:
                    return None
            except requests.exceptions.RequestException as e:
                print(f"  - Error during Generic API request (Attempt {current_retry+1}/{MAX_RETRIES+1}): {e}")
                error_code = e.response.status_code if e.response is not None else None
                try:
                    error_details = e.response.json() if e.response is not None else None
                    print(f"    - API Error Details: {error_details}")
                except: pass # Ignore JSON decoding errors on error response

                # Basic retry for generic server errors (5xx) or rate limits (429)
                if error_code in [429, 500, 502, 503, 504] and current_retry < MAX_RETRIES:
                    delay = (INITIAL_RETRY_DELAY_SECONDS * (2 ** current_retry)) + random.uniform(0, 1)
                    print(f"    - Retrying after {delay:.2f} seconds...")
                    time.sleep(delay)
                    current_retry += 1
                else:
                    return None # Failed or non-retryable error
            except Exception as e:
                 print(f"  - Unexpected error sending request: {e}")
                 return None

        print(f"  - Error: Failed to get response from Generic AI API after {MAX_RETRIES} retries.")
        return None


# Example Usage (conceptual)
if __name__ == "__main__":
    print("\n--- Generic AI Connector Example (Conceptual) ---")

    # Example 1: Connecting to a hypothetical service using Bearer Token Auth
    print("\nExample 1: Hypothetical Service with Bearer Token")
    # Assume SOME_HYPOTHETICAL_KEY is set in environment
    hypothetical_auth_bearer = {'type': 'bearer', 'key_env_var': 'SOME_HYPOTHETICAL_KEY'}
    connector_bearer = GenericAIConnector(
        api_base_url="https://api.hypothetical-ai.com",
        auth_info=hypothetical_auth_bearer
    )
    # The caller needs to know the specific endpoint and payload structure
    payload_bearer = {"prompt": "Analyze this sentiment: 'I love this!'", "model": "sentiment-v2"}
    response_bearer = connector_bearer.send_request(endpoint="/analyze", method='POST', payload=payload_bearer)
    if response_bearer:
        print("Response from Hypothetical Bearer Service:")
        print(json.dumps(response_bearer, indent=2))
    else:
        print("Failed to get response (check API URL, key env var, and if service exists).")


    # Example 2: Connecting to a hypothetical service using Header API Key Auth
    print("\nExample 2: Hypothetical Service with Header API Key")
    # Assume ANOTHER_HYPOTHETICAL_KEY is set in environment
    hypothetical_auth_header = {'type': 'api_key_header', 'header_name': 'X-Custom-API-Key', 'key_env_var': 'ANOTHER_HYPOTHETICAL_KEY'}
    connector_header = GenericAIConnector(
        api_base_url="http://some-other-ai.internal:9000/api",
        auth_info=hypothetical_auth_header
    )
    # Example GET request with parameters
    params_get = {"text": "Translate to French: 'Hello'", "target_lang": "fr"}
    response_get = connector_header.send_request(endpoint="/translate", method='GET', params=params_get)
    if response_get:
        print("Response from Hypothetical Header Key Service:")
        print(json.dumps(response_get, indent=2))
    else:
        print("Failed to get response.")

    # Example 3: Connecting to a service with no auth (e.g., simple local service)
    print("\nExample 3: Hypothetical Service with No Auth")
    connector_no_auth = GenericAIConnector(api_base_url="http://localhost:5555")
    payload_no_auth = {"data": [1, 2, 3]}
    response_no_auth = connector_no_auth.send_request(endpoint="/process", method='POST', payload=payload_no_auth)
    if response_no_auth:
        print("Response from Hypothetical No-Auth Service:")
        print(json.dumps(response_no_auth, indent=2))
    else:
        print("Failed to get response.")


    print("\n--- End Example ---")
