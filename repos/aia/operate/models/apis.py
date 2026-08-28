import requests
import os
import logging
from typing import Dict, Any, Optional


class APIManager:
    """
    Centralized API interaction handler.
    Handles requests to external APIs like OpenAI, WhiteRabbit AI, and social media platforms.
    """

    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.logger = logging.getLogger("APIManager")
        self.session = requests.Session()

    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment variables."""
        keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "whiterabbit": os.getenv("WHITERABBIT_API_KEY"),
            "twitter": os.getenv("TWITTER_API_KEY"),
            "facebook": os.getenv("FACEBOOK_API_KEY"),
        }
        missing_keys = [key for key, value in keys.items() if not value]
        if missing_keys:
            self.logger.warning(f"Missing API keys for: {', '.join(missing_keys)}")
        return keys

    def send_request(
        self, service: str, endpoint: str, payload: Dict[str, Any], method: str = "POST"
    ) -> Optional[Dict[str, Any]]:
        """
        Sends a request to the specified API service.

        Args:
            service: The name of the service (e.g., 'openai', 'whiterabbit').
            endpoint: The API endpoint for the request.
            payload: The request body or parameters.
            method: HTTP method ('GET', 'POST', etc.).

        Returns:
            JSON response if successful, None otherwise.
        """
        base_urls = {
            "openai": "https://api.openai.com/v1",
            "whiterabbit": "https://api.whiterabbitneo.com/v1",
            "twitter": "https://api.twitter.com/2",
            "facebook": "https://graph.facebook.com/v14.0",
        }

        if service not in base_urls:
            self.logger.error(f"Unknown service: {service}")
            return None

        url = f"{base_urls[service]}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_keys.get(service)}"}
        self.logger.debug(f"Sending {method} request to {url} with payload {payload}")

        try:
            if method.upper() == "POST":
                response = self.session.post(url, json=payload, headers=headers)
            elif method.upper() == "GET":
                response = self.session.get(url, params=payload, headers=headers)
            else:
                self.logger.error(f"Unsupported HTTP method: {method}")
                return None

            response.raise_for_status()
            self.logger.info(f"API call to {service} succeeded.")
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"API call to {service} failed: {e}")
            return None

    def generate_text_with_openai(self, prompt: str) -> Optional[str]:
        """
        Generate text using OpenAI's API.

        Args:
            prompt: Text prompt for the model.

        Returns:
            Generated response if successful, None otherwise.
        """
        payload = {"model": "gpt-4", "prompt": prompt, "max_tokens": 100}
        response = self.send_request("openai", "/completions", payload)
        return response.get("choices", [{}])[0].get("text") if response else None

    def analyze_with_whiterabbit(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Perform text analysis using WhiteRabbit AI.

        Args:
            text: Text input for analysis.

        Returns:
            Analysis result if successful, None otherwise.
        """
        payload = {"text": text}
        response = self.send_request("whiterabbit", "/analyze", payload)
        return response if response else None


# Example Usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    api_manager = APIManager()

    # OpenAI usage example
    prompt = "What is the capital of France?"
    generated_text = api_manager.generate_text_with_openai(prompt)
    if generated_text:
        print(f"OpenAI response: {generated_text}")

    # WhiteRabbit AI usage example
    analysis_result = api_manager.analyze_with_whiterabbit("Analyze this sentence.")
    if analysis_result:
        print(f"WhiteRabbit analysis: {analysis_result}")
