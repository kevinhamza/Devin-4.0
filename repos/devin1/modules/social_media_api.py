"""
modules/social_media_api.py

This module provides tools for interacting with various social media platforms via their APIs.
Includes functionalities for posting, fetching, and managing content.
"""

import requests
import json
import logging
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)

class SocialMediaAPI:
    """
    A generic class for interacting with social media APIs.
    """

    def __init__(self, platform: str, api_key: Optional[str] = None):
        """
        Initialize the API handler.
        :param platform: Name of the social media platform (e.g., "twitter", "facebook").
        :param api_key: API key for the platform (if required).
        """
        self.platform = platform.lower()
        self.api_key = api_key
        self.base_url = self._get_base_url()

    def _get_base_url(self) -> str:
        """
        Retrieve the base URL for the API based on the platform.
        :return: Base URL as a string.
        """
        base_urls = {
            "twitter": "https://api.twitter.com/2",
            "facebook": "https://graph.facebook.com",
            "instagram": "https://graph.instagram.com",
            "linkedin": "https://api.linkedin.com/v2",
        }
        return base_urls.get(self.platform, "")

    def post_content(self, content: str, media_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Post content to the social media platform.
        :param content: Text content to post.
        :param media_url: Optional URL of media to include in the post.
        :return: API response as a dictionary.
        """
        if not self.api_key or not self.base_url:
            logging.error("API key or base URL missing.")
            return {"error": "Invalid configuration."}

        url = f"{self.base_url}/post"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"content": content}
        if media_url:
            payload["media_url"] = media_url

        response = requests.post(url, headers=headers, json=payload)
        return self._handle_response(response)

    def fetch_posts(self, count: int = 10) -> Dict[str, Any]:
        """
        Fetch recent posts from the social media platform.
        :param count: Number of posts to fetch.
        :return: API response as a dictionary.
        """
        if not self.api_key or not self.base_url:
            logging.error("API key or base URL missing.")
            return {"error": "Invalid configuration."}

        url = f"{self.base_url}/posts"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"limit": count}

        response = requests.get(url, headers=headers, params=params)
        return self._handle_response(response)

    def like_post(self, post_id: str) -> Dict[str, Any]:
        """
        Like a post on the social media platform.
        :param post_id: ID of the post to like.
        :return: API response as a dictionary.
        """
        if not self.api_key or not self.base_url:
            logging.error("API key or base URL missing.")
            return {"error": "Invalid configuration."}

        url = f"{self.base_url}/posts/{post_id}/like"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        response = requests.post(url, headers=headers)
        return self._handle_response(response)

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle the API response.
        :param response: Response object from the API call.
        :return: Parsed response as a dictionary.
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logging.error(f"HTTP Error: {e}")
            return {"error": str(e)}
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON response.")
            return {"error": "Invalid JSON response."}
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return {"error": str(e)}


if __name__ == "__main__":
    # Example usage:
    api = SocialMediaAPI(platform="twitter", api_key="your-twitter-api-key")
    print(api.post_content("Hello, Twitter!"))
    print(api.fetch_posts(count=5))
    print(api.like_post(post_id="1234567890"))
