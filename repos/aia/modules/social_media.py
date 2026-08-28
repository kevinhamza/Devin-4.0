import os
import requests
import json
from config.settings import Config  # Ensure you import the Config class

class SocialMediaManager:
    def __init__(self, config):
        # Ensure config is passed and use proper methods to access keys
        self.config = config

        # Access Twitter and Facebook API keys using methods from Config
        self.twitter_api_key = self.config.get_api_key("TWITTER_API_KEY")
        self.facebook_api_key = self.config.get_api_key("FACEBOOK_API_KEY")

    def post_to_twitter(self, message):
        url = "https://api.twitter.com/2/tweets"
        headers = {
            "Authorization": f"Bearer {self.twitter_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": message
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            print("Successfully posted to Twitter!")
        else:
            print(f"Error posting to Twitter: {response.status_code} - {response.text}")

    def post_to_facebook(self, message):
        url = "https://graph.facebook.com/v10.0/me/feed"
        headers = {
            "Authorization": f"Bearer {self.facebook_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "message": message
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Successfully posted to Facebook!")
        else:
            print(f"Error posting to Facebook: {response.status_code} - {response.text}")

    def get_latest_posts(self, platform="twitter"):
        if platform == "twitter":
            url = "https://api.twitter.com/2/tweets"
            headers = {
                "Authorization": f"Bearer {self.twitter_api_key}"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                print("Latest posts from Twitter:", response.json())
            else:
                print(f"Error fetching posts from Twitter: {response.status_code} - {response.text}")
        elif platform == "facebook":
            url = "https://graph.facebook.com/v10.0/me/feed"
            headers = {
                "Authorization": f"Bearer {self.facebook_api_key}"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                print("Latest posts from Facebook:", response.json())
            else:
                print(f"Error fetching posts from Facebook: {response.status_code} - {response.text}")
        else:
            print("Invalid platform specified.")

if __name__ == "__main__":
    from config.settings import load_config

    # Example of initializing with the Config object
    config = load_config()
    smm = SocialMediaManager(config=config)

    # Example usage
    smm.post_to_twitter("Hello from my assistant!")
    smm.get_latest_posts("twitter")
    
