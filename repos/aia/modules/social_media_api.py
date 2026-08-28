import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class SocialMediaAPI:
    def __init__(self):
        self.twitter_api_key = os.getenv("TWITTER_API_KEY")
        self.twitter_access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.facebook_access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        self.instagram_access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.linkedin_access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")

    # Twitter API methods
    def post_to_twitter(self, message):
        url = "https://api.twitter.com/2/tweets"
        headers = {
            "Authorization": f"Bearer {self.twitter_access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "status": message
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            print("Successfully posted to Twitter!")
        else:
            print(f"Error posting to Twitter: {response.status_code}")

    def get_twitter_timeline(self):
        url = f"https://api.twitter.com/2/timeline/home.json"
        headers = {
            "Authorization": f"Bearer {self.twitter_access_token}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            tweets = response.json()
            for tweet in tweets['data']:
                print(f"Tweet: {tweet['text']}")
        else:
            print(f"Error fetching Twitter timeline: {response.status_code}")

    # Facebook API methods
    def post_to_facebook(self, message):
        url = f"https://graph.facebook.com/v10.0/me/feed"
        headers = {
            "Authorization": f"Bearer {self.facebook_access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "message": message
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Successfully posted to Facebook!")
        else:
            print(f"Error posting to Facebook: {response.status_code}")

    def get_facebook_feed(self):
        url = f"https://graph.facebook.com/v10.0/me/feed"
        headers = {
            "Authorization": f"Bearer {self.facebook_access_token}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            posts = response.json()
            for post in posts['data']:
                print(f"Post: {post['message']}")
        else:
            print(f"Error fetching Facebook feed: {response.status_code}")

    # Instagram API methods (via Graph API)
    def post_to_instagram(self, image_url, caption):
        url = f"https://graph.instagram.com/v12.0/{self.instagram_access_token}/media"
        payload = {
            "image_url": image_url,
            "caption": caption
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Successfully posted to Instagram!")
        else:
            print(f"Error posting to Instagram: {response.status_code}")

    def get_instagram_posts(self):
        url = f"https://graph.instagram.com/v12.0/{self.instagram_access_token}/media"
        response = requests.get(url)
        if response.status_code == 200:
            posts = response.json()
            for post in posts['data']:
                print(f"Instagram Post: {post['caption']}")
        else:
            print(f"Error fetching Instagram posts: {response.status_code}")

    # LinkedIn API methods
    def post_to_linkedin(self, message):
        url = f"https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {self.linkedin_access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "author": "urn:li:person:{self.linkedin_user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": message
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            print("Successfully posted to LinkedIn!")
        else:
            print(f"Error posting to LinkedIn: {response.status_code}")

    def get_linkedin_posts(self):
        url = f"https://api.linkedin.com/v2/shares"
        headers = {
            "Authorization": f"Bearer {self.linkedin_access_token}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            posts = response.json()
            for post in posts['elements']:
                print(f"LinkedIn Post: {post['text']}")
        else:
            print(f"Error fetching LinkedIn posts: {response.status_code}")

    # Utility function to check if all keys are set up
    def check_api_keys(self):
        missing_keys = []
        if not self.twitter_access_token:
            missing_keys.append("Twitter Access Token")
        if not self.facebook_access_token:
            missing_keys.append("Facebook Access Token")
        if not self.instagram_access_token:
            missing_keys.append("Instagram Access Token")
        if not self.linkedin_access_token:
            missing_keys.append("LinkedIn Access Token")

        if missing_keys:
            print(f"Missing API keys: {', '.join(missing_keys)}")
            return False
        return True

if __name__ == "__main__":
    sm_api = SocialMediaAPI()

    if sm_api.check_api_keys():
        sm_api.post_to_twitter("Hello, Twitter!")
        sm_api.get_twitter_timeline()
        sm_api.post_to_facebook("Hello, Facebook!")
        sm_api.get_facebook_feed()
        sm_api.post_to_instagram("https://your_image_url.com", "Hello, Instagram!")
        sm_api.get_instagram_posts()
        sm_api.post_to_linkedin("Hello, LinkedIn!")
        sm_api.get_linkedin_posts()
