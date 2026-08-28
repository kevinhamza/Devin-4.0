"""
modules/social_media_automation.py

Automates repetitive tasks on social media platforms, such as posting on a schedule,
responding to comments, and fetching analytics.
"""

import time
from datetime import datetime
from typing import List, Dict
from social_media_api import SocialMediaAPI

class SocialMediaAutomation:
    def __init__(self, platform_api_keys: Dict[str, str]):
        """
        Initializes the automation tool with the required API keys for each platform.
        
        Args:
            platform_api_keys (Dict[str, str]): A dictionary of platform names and their corresponding API keys.
        """
        self.api_clients = {}
        for platform, api_key in platform_api_keys.items():
            self.api_clients[platform] = SocialMediaAPI(api_key)

    def schedule_post(self, platform: str, content: str, schedule_time: datetime):
        """
        Schedules a post to be published at a specific time.
        
        Args:
            platform (str): The social media platform to post to.
            content (str): The content of the post.
            schedule_time (datetime): The time to publish the post.
        """
        delay = (schedule_time - datetime.now()).total_seconds()
        if delay > 0:
            time.sleep(delay)
        self.api_clients[platform].post(content)
        print(f"Post scheduled on {platform} at {schedule_time}.")

    def auto_respond(self, platform: str, keywords: List[str], response: str):
        """
        Automatically responds to comments containing specific keywords.
        
        Args:
            platform (str): The social media platform to monitor.
            keywords (List[str]): Keywords to trigger an automatic response.
            response (str): The response to post.
        """
        comments = self.api_clients[platform].fetch_comments()
        for comment in comments:
            if any(keyword in comment for keyword in keywords):
                self.api_clients[platform].respond_to_comment(comment_id=comment['id'], response=response)
                print(f"Responded to comment '{comment['text']}' on {platform}.")

    def fetch_analytics(self, platform: str) -> Dict[str, int]:
        """
        Fetches engagement analytics for the specified platform.
        
        Args:
            platform (str): The social media platform to fetch analytics from.
            
        Returns:
            Dict[str, int]: A dictionary containing engagement metrics.
        """
        analytics = self.api_clients[platform].get_analytics()
        print(f"Analytics for {platform}: {analytics}")
        return analytics

if __name__ == "__main__":
    # Example usage
    platform_keys = {
        "twitter": "TWITTER_API_KEY",
        "instagram": "INSTAGRAM_API_KEY",
    }

    social_bot = SocialMediaAutomation(platform_keys)

    # Schedule a post
    post_time = datetime.now() + timedelta(seconds=30)  # Schedule a post 30 seconds from now
    social_bot.schedule_post("twitter", "Hello, Twitter!", post_time)

    # Automate responses
    social_bot.auto_respond("instagram", ["help", "issue"], "Thank you for reaching out. We will get back to you soon.")

    # Fetch analytics
    social_bot.fetch_analytics("twitter")
