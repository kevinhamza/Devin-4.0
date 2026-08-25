# # Devin/modules/social_media_api.py
# # Purpose: Provides a conceptual interface for interacting with social media
# #          platforms like Twitter and Reddit for OSINT and automation.
# # Interacts with social media platforms 🌐🗣️

# import logging
# import uuid
# import random
# from datetime import datetime, timezone, timedelta
# from dataclasses import dataclass, field
# from typing import List, Dict, Any, Optional

# # Configure basic logging
# logger = logging.getLogger("SocialMediaAPI")
# if not logger.handlers:
#     _console_handler = logging.StreamHandler()
#     _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
#     logger.addHandler(_console_handler)
#     logger.setLevel(logging.INFO)

# class SocialMediaPlatform(Enum):
#     """Enumeration for supported social media platforms."""
#     TWITTER = "Twitter"
#     REDDIT = "Reddit"
#     LINKEDIN = "LinkedIn" # Placeholder for future expansion

# @dataclass
# class Post:
#     """A generic representation of a social media post."""
#     platform: SocialMediaPlatform
#     post_id: str
#     author_id: str
#     author_username: str
#     content: str
#     timestamp_utc: datetime
#     stats: Dict[str, int] = field(default_factory=dict) # e.g., {"likes": 10, "retweets": 5, "comments": 2}
#     url: Optional[str] = None

# class TwitterTools:
#     """
#     Conceptually interacts with the Twitter API (v2).
#     In a real system, this would be a wrapper around a library like 'tweepy'.
#     """
#     def __init__(self, bearer_token_placeholder: str, api_key_placeholder: str, api_secret_placeholder: str, access_token_placeholder: str, access_secret_placeholder: str):
#         self.credentials = {
#             "bearer_token": bearer_token_placeholder,
#             "api_key": api_key_placeholder,
#             "api_secret": api_secret_placeholder,
#             "access_token": access_token_placeholder,
#             "access_secret": access_secret_placeholder,
#         }
#         logger.info("TwitterTools initialized with conceptual API credentials.")
#         logger.warning("All Twitter operations are conceptual and do not represent real API calls.")

#     def search_tweets_conceptual(self, query: str, count: int = 10) -> List[Post]:
#         """Conceptually searches for recent tweets matching a query."""
#         logger.info(f"CONCEPTUAL TWEEPY: Searching for {count} tweets with query: '{query}'")
#         # Real-world: client.search_recent_tweets(query, max_results=count)
        
#         results = []
#         for i in range(random.randint(1, count)):
#             author = random.choice(["TechCrunch", "elonmusk", "OpenAI", "GergelyOrosz"])
#             results.append(Post(
#                 platform=SocialMediaPlatform.TWITTER,
#                 post_id=str(random.randint(10**18, 10**19-1)),
#                 author_id=str(random.randint(10**8, 10**9-1)),
#                 author_username=author,
#                 content=f"This is a conceptual tweet about '{query}'. #{query.split()[0]} #AI",
#                 timestamp_utc=datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 120)),
#                 stats={"likes": random.randint(10, 5000), "retweets": random.randint(5, 1000)},
#                 url=f"https://twitter.com/{author}/status/{random.randint(10**18, 10**19-1)}"
#             ))
#         return results

#     def post_tweet_conceptual(self, text_content: str) -> Optional[Post]:
#         """Conceptually posts a new tweet."""
#         if len(text_content) > 280:
#             logger.error("Tweet is too long.")
#             return None
            
#         logger.info(f"CONCEPTUAL TWEEPY: Posting tweet: '{text_content[:50]}...'")
#         # Real-world: client.create_tweet(text=text_content)
        
#         post_id = str(random.randint(10**18, 10**19-1))
#         return Post(
#             platform=SocialMediaPlatform.TWITTER,
#             post_id=post_id,
#             author_id="devin_user_id",
#             author_username="DevinAI_Bot",
#             content=text_content,
#             timestamp_utc=datetime.now(timezone.utc),
#             stats={"likes": 0, "retweets": 0},
#             url=f"https://twitter.com/DevinAI_Bot/status/{post_id}"
#         )

#     def get_user_timeline_conceptual(self, username: str, count: int = 10) -> List[Post]:
#         """Conceptually retrieves the most recent tweets from a user's timeline."""
#         logger.info(f"CONCEPTUAL TWEEPY: Getting last {count} tweets for user '{username}'.")
#         # Real-world: client.get_users_tweets(user_id, max_results=count)
        
#         # This is a simplified version of the search method for demo purposes.
#         return self.search_tweets_conceptual(query=f"from:{username}", count=count)


# class RedditTools:
#     """
#     Conceptually interacts with the Reddit API.
#     In a real system, this would be a wrapper around the 'praw' library.
#     """
#     def __init__(self, client_id_placeholder: str, client_secret_placeholder: str, user_agent: str, username_placeholder: Optional[str] = None, password_placeholder: Optional[str] = None):
#         self.credentials = {
#             "client_id": client_id_placeholder,
#             "client_secret": client_secret_placeholder,
#             "user_agent": user_agent,
#             "username": username_placeholder,
#             "password": password_placeholder,
#         }
#         logger.info(f"RedditTools initialized with conceptual API credentials (User-Agent: {user_agent}).")
#         logger.warning("All Reddit operations are conceptual and do not represent real API calls.")

#     def search_submissions_conceptual(self, subreddit_name: str, query: str, limit: int = 10) -> List[Post]:
#         """Conceptually searches for submissions in a specific subreddit."""
#         logger.info(f"CONCEPTUAL PRAW: Searching r/{subreddit_name} for '{query}' (limit: {limit}).")
#         # Real-world: reddit.subreddit(subreddit_name).search(query, limit=limit)
        
#         results = []
#         for i in range(random.randint(1, limit)):
#             post_id = uuid.uuid4().hex[:6]
#             author = f"user_{random.randint(1000, 9999)}"
#             results.append(Post(
#                 platform=SocialMediaPlatform.REDDIT,
#                 post_id=post_id,
#                 author_id=f"t2_{author}",
#                 author_username=author,
#                 content=f"This is the body of a conceptual Reddit post about '{query}'. It might be longer.",
#                 timestamp_utc=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
#                 stats={"score": random.randint(-10, 2000), "comments": random.randint(0, 500)},
#                 url=f"https://www.reddit.com/r/{subreddit_name}/comments/{post_id}/"
#             ))
#         return results

#     def submit_post_conceptual(self, subreddit_name: str, title: str, selftext: str) -> Optional[Post]:
#         """Conceptually creates a new self-text submission (post)."""
#         logger.info(f"CONCEPTUAL PRAW: Submitting post to r/{subreddit_name}: '{title[:50]}...'")
#         # Real-world: reddit.subreddit(subreddit_name).submit(title, selftext=selftext)
        
#         if not self.credentials["username"]:
#             logger.error("Cannot submit post: Conceptual user authentication not configured.")
#             return None
        
#         post_id = uuid.uuid4().hex[:6]
#         return Post(
#             platform=SocialMediaPlatform.REDDIT,
#             post_id=post_id,
#             author_id="devin_reddit_id",
#             author_username=self.credentials["username"],
#             content=selftext,
#             timestamp_utc=datetime.now(timezone.utc),
#             stats={"score": 1, "comments": 0},
#             url=f"https://www.reddit.com/r/{subreddit_name}/comments/{post_id}/"
#         )
        
#     def get_subreddit_hot_conceptual(self, subreddit_name: str, limit: int = 10) -> List[Post]:
#         """Conceptually gets the top 'hot' posts from a subreddit."""
#         logger.info(f"CONCEPTUAL PRAW: Getting top {limit} 'hot' posts from r/{subreddit_name}.")
#         # Real-world: reddit.subreddit(subreddit_name).hot(limit=limit)
        
#         # This is a simplified version of the search method for demo purposes.
#         return self.search_submissions_conceptual(subreddit_name, query="hot posts", limit=limit)

# import logging # Already imported in Part 1
# import uuid # Already imported in Part 1
# import random # Already imported in Part 1
# from datetime import datetime, timezone, timedelta # Already imported in Part 1
# from dataclasses import dataclass, field # Already imported in Part 1
# from typing import List, Dict, Any, Optional # Already imported in Part 1
# from enum import Enum # Imported in Part 1, repeated here for clarity if separated

# class SocialMediaManager:
#     """
#     A high-level facade that provides a unified interface for interacting with
#     various social media platforms using their specific toolsets.
#     """
#     def __init__(self, twitter_creds: Optional[Dict] = None, reddit_creds: Optional[Dict] = None):
#         """
#         Initializes the manager and its underlying platform-specific tools.

#         Args:
#             twitter_creds (Optional[Dict]): Conceptual credentials for Twitter.
#             reddit_creds (Optional[Dict]): Conceptual credentials for Reddit.
#         """
#         logger.info("SocialMediaManager initializing...")
#         self.twitter: Optional[TwitterTools] = None
#         self.reddit: Optional[RedditTools] = None

#         if twitter_creds:
#             self.twitter = TwitterTools(**twitter_creds)
#             logger.info("  -> TwitterTools instance created.")
        
#         if reddit_creds:
#             self.reddit = RedditTools(**reddit_creds)
#             logger.info("  -> RedditTools instance created.")
            
#         logger.info("SocialMediaManager initialization complete.")

#     def search_posts(self, platform: SocialMediaPlatform, query: str, count: int = 5) -> Optional[List[Post]]:
#         """
#         Searches for posts on a specified platform.

#         Args:
#             platform (SocialMediaPlatform): The platform to search on.
#             query (str): The search query.
#             count (int): The number of posts to retrieve.

#         Returns:
#             Optional[List[Post]]: A list of Post objects or None if platform is unsupported.
#         """
#         logger.info(f"Manager: Received request to search for '{query}' on {platform.value}.")
#         if platform == SocialMediaPlatform.TWITTER and self.twitter:
#             return self.twitter.search_tweets_conceptual(query, count=count)
#         elif platform == SocialMediaPlatform.REDDIT and self.reddit:
#             # Reddit search is usually per-subreddit. We'll default to a common one like 'all'.
#             # A more advanced implementation would take subreddit as a parameter.
#             subreddit = "all"
#             logger.info(f"  Searching on Reddit requires a subreddit, defaulting to r/{subreddit}.")
#             return self.reddit.search_submissions_conceptual(subreddit, query, limit=count)
#         else:
#             logger.error(f"Platform {platform.value} is not configured or supported for search.")
#             return None

#     def post_update(self, platform: SocialMediaPlatform, content: Dict[str, str]) -> Optional[Post]:
#         """
#         Posts an update to a specified platform.

#         Args:
#             platform (SocialMediaPlatform): The platform to post to.
#             content (Dict[str, str]): The content to post. Keys vary by platform
#                                       (e.g., {"text": "..."} for Twitter,
#                                        {"title": "...", "body": "..."} for Reddit).

#         Returns:
#             Optional[Post]: The created Post object or None on failure.
#         """
#         logger.info(f"Manager: Received request to post an update to {platform.value}.")
#         if platform == SocialMediaPlatform.TWITTER and self.twitter:
#             text = content.get("text")
#             if not text:
#                 logger.error("Content for Twitter must include a 'text' key.")
#                 return None
#             return self.twitter.post_tweet_conceptual(text)
#         elif platform == SocialMediaPlatform.REDDIT and self.reddit:
#             title = content.get("title")
#             body = content.get("body")
#             subreddit = content.get("subreddit") # Require subreddit for posting
#             if not all([title, body, subreddit]):
#                 logger.error("Content for Reddit must include 'title', 'body', and 'subreddit' keys.")
#                 return None
#             return self.reddit.submit_post_conceptual(subreddit, title, body)
#         else:
#             logger.error(f"Platform {platform.value} is not configured or supported for posting.")
#             return None
            
#     def get_user_activity(self, platform: SocialMediaPlatform, username: str, count: int = 5) -> Optional[List[Post]]:
#         """Retrieves recent activity for a user on a specified platform."""
#         logger.info(f"Manager: Received request to get activity for '{username}' on {platform.value}.")
#         if platform == SocialMediaPlatform.TWITTER and self.twitter:
#             return self.twitter.get_user_timeline_conceptual(username, count=count)
#         elif platform == SocialMediaPlatform.REDDIT and self.reddit:
#              # PRAW gets user activity via `reddit.redditor(username).submissions.new()` etc.
#              # We'll simulate this by searching for posts by the author.
#              logger.info(f"  Simulating user activity fetch by searching for posts by author:'{username}'.")
#              return self.reddit.search_submissions_conceptual(subreddit="all", query=f"author:{username}", limit=count)
#         else:
#             logger.error(f"Platform {platform.value} is not configured or supported for user activity.")
#             return None

# # --- Example Usage ---
# if __name__ == "__main__":
#     print("================================================================")
#     print("=== Social Media Manager Prototype (Unified Interface Demo) 🌐🗣️ ===")
#     print("================================================================")

#     # Conceptual credentials for initializing the toolsets
#     # In a real app, these would come from a secure config or environment variables
#     twitter_credentials = {
#         "bearer_token_placeholder": "CONCEPTUAL_TWITTER_BEARER_TOKEN",
#         "api_key_placeholder": "CONCEPTUAL_TWITTER_API_KEY",
#         "api_secret_placeholder": "CONCEPTUAL_TWITTER_API_SECRET",
#         "access_token_placeholder": "CONCEPTUAL_TWITTER_ACCESS_TOKEN",
#         "access_secret_placeholder": "CONCEPTUAL_TWITTER_ACCESS_SECRET"
#     }
    
#     reddit_credentials = {
#         "client_id_placeholder": "CONCEPTUAL_REDDIT_CLIENT_ID",
#         "client_secret_placeholder": "CONCEPTUAL_REDDIT_CLIENT_SECRET",
#         "user_agent": "Devin-AI-Agent/0.1 by u/DevinBot",
#         "username_placeholder": "DevinBot",
#         "password_placeholder": "CONCEPTUAL_REDDIT_PASSWORD"
#     }

#     # Initialize the manager with all toolsets
#     social_media_manager = SocialMediaManager(
#         twitter_creds=twitter_credentials,
#         reddit_creds=reddit_credentials
#     )

#     # --- 1. Search across different platforms using the unified interface ---
#     print("\n--- Task 1: Searching for 'AI safety' on Twitter and Reddit ---")
    
#     # Search Twitter
#     twitter_results = social_media_manager.search_posts(SocialMediaPlatform.TWITTER, "AI safety", count=2)
#     print("\n  Twitter Search Results:")
#     if twitter_results:
#         for post in twitter_results:
#             print(f"    - @{post.author_username}: {post.content[:60]}... (Likes: {post.stats.get('likes')})")
#     else:
#         print("    No conceptual results from Twitter.")
        
#     # Search Reddit
#     reddit_results = social_media_manager.search_posts(SocialMediaPlatform.REDDIT, "AI safety", count=2)
#     print("\n  Reddit Search Results:")
#     if reddit_results:
#         for post in reddit_results:
#             print(f"    - u/{post.author_username}: {post.content[:60]}... (Score: {post.stats.get('score')})")
#     else:
#         print("    No conceptual results from Reddit.")

#     # --- 2. Post an update to a specific platform ---
#     print("\n\n--- Task 2: Posting a status update to Twitter ---")
#     twitter_post_content = {"text": "Initiating a new conceptual software development project. Task planning phase is starting now. #DevinAI"}
#     created_tweet = social_media_manager.post_update(SocialMediaPlatform.TWITTER, twitter_post_content)
#     if created_tweet:
#         print(f"  Successfully posted to Twitter! New Post URL (conceptual): {created_tweet.url}")
#     else:
#         print("  Failed to post to Twitter.")

#     print("\n--- Task 3: Posting a question to a Reddit subreddit ---")
#     reddit_post_content = {
#         "subreddit": "learnpython",
#         "title": "What are the best practices for structuring a large modular project?",
#         "body": "My AI agent, Devin, is building a large project and I'm looking for community advice on how to best structure the modules and servers for maintainability. Any suggestions?"
#     }
#     created_reddit_post = social_media_manager.post_update(SocialMediaPlatform.REDDIT, reddit_post_content)
#     if created_reddit_post:
#         print(f"  Successfully posted to Reddit! New Post URL (conceptual): {created_reddit_post.url}")
#     else:
#         print("  Failed to post to Reddit.")

#     # --- 4. Get user activity ---
#     print("\n\n--- Task 4: Getting recent user activity ---")
#     username_to_check = "OpenAI"
#     user_tweets = social_media_manager.get_user_activity(SocialMediaPlatform.TWITTER, username_to_check, count=1)
#     print(f"\n  Recent activity for '{username_to_check}' on Twitter:")
#     if user_tweets:
#         print(f"    - @{user_tweets[0].author_username}: {user_tweets[0].content[:80]}...")
#     else:
#         print("    Could not retrieve user activity.")


#     print("\n================================================================")
#     print("=== Social Media Manager Prototype Complete ===")
#     print("================================================================")


# Devin/modules/social_media_api.py
# Purpose: A functional, integrated interface for interacting with social media
#          platforms like Twitter, Reddit, Facebook, Instagram, and LinkedIn for
#          OSINT and automation.

import logging
import os
from datetime import datetime, timezone
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

import requests

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False

# Configure basic logging
logger = logging.getLogger("SocialMediaAPI")
if not logger.handlers:
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_console_handler)
    logger.setLevel(logging.INFO)
logger.propagate = False

class SocialMediaPlatform(Enum):
    TWITTER = "Twitter"
    REDDIT = "Reddit"
    FACEBOOK = "Facebook"
    INSTAGRAM = "Instagram"
    LINKEDIN = "LinkedIn"

@dataclass
class Post:
    platform: SocialMediaPlatform
    post_id: str
    author_username: str
    content: str
    timestamp_utc: datetime
    stats: Dict[str, int] = field(default_factory=dict)
    url: Optional[str] = None

class TwitterTools:
    """Interacts with the Twitter API (v2) using Tweepy."""
    def __init__(self, bearer_token: str):
        if not TWEEPY_AVAILABLE:
            raise ImportError("Tweepy is required. 'pip install tweepy'")
        try:
            self.client = tweepy.Client(bearer_token)
            # Verify credentials
            self.client.get_me()
            logger.info("TwitterTools initialized and authenticated successfully.")
        except Exception as e:
            raise ConnectionError(f"Failed to authenticate with Twitter API: {e}")

    def search_tweets(self, query: str, count: int = 10) -> List[Post]:
        logger.info(f"Searching Twitter for '{query}'...")
        try:
            response = self.client.search_recent_tweets(
                query, 
                max_results=max(10, min(100, count)), # API has min/max limits
                tweet_fields=["public_metrics", "created_at", "author_id"]
            )
            if not response.data: return []

            return [self._normalize_tweet(tweet) for tweet in response.data]
        except tweepy.errors.TweepyException as e:
            logger.error(f"Error searching Twitter: {e}")
            return []

    def _normalize_tweet(self, tweet: tweepy.Tweet) -> Post:
        """Converts a Tweepy Tweet object to our standard Post dataclass."""
        return Post(
            platform=SocialMediaPlatform.TWITTER,
            post_id=str(tweet.id),
            author_username=f"user_id_{tweet.author_id}", # Getting username requires another call, simplifying here
            content=tweet.text,
            timestamp_utc=tweet.created_at,
            stats={
                "likes": tweet.public_metrics.get('like_count', 0),
                "retweets": tweet.public_metrics.get('retweet_count', 0),
                "replies": tweet.public_metrics.get('reply_count', 0),
            },
            url=f"https://twitter.com/anyuser/status/{tweet.id}"
        )


class RedditTools:
    """Interacts with the Reddit API using PRAW."""
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        if not PRAW_AVAILABLE:
            raise ImportError("PRAW is required. 'pip install praw'")
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )
            # Verify credentials by checking read-only status
            assert self.reddit.read_only is True
            logger.info("RedditTools initialized and authenticated successfully (read-only).")
        except Exception as e:
            raise ConnectionError(f"Failed to authenticate with Reddit API: {e}")

    def search_submissions(self, subreddit_name: str, query: str, limit: int = 10) -> List[Post]:
        logger.info(f"Searching r/{subreddit_name} on Reddit for '{query}'...")
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            results = subreddit.search(query, limit=limit)
            return [self._normalize_submission(sub) for sub in results]
        except Exception as e:
            logger.error(f"Error searching Reddit: {e}")
            return []

    def _normalize_submission(self, submission: praw.models.Submission) -> Post:
        """Converts a PRAW Submission object to our standard Post dataclass."""
        return Post(
            platform=SocialMediaPlatform.REDDIT,
            post_id=submission.id,
            author_username=submission.author.name if submission.author else "[deleted]",
            content=submission.selftext or submission.title, # Use selftext if available, else title
            timestamp_utc=datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
            stats={
                "score": submission.score,
                "comments": submission.num_comments,
                "upvote_ratio": int(submission.upvote_ratio * 100)
            },
            url=f"https://www.reddit.com{submission.permalink}"
        )


class FacebookTools:
    """Interacts with the Facebook Graph API (posting to/reading the user's own feed)."""
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v19.0"

    def post_update(self, message: str) -> Dict[str, Any]:
        try:
            response = requests.post(
                f"{self.base_url}/me/feed",
                params={"access_token": self.access_token},
                data={"message": message},
                timeout=15,
            )
            response.raise_for_status()
            return {"status": "success", "result": response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting to Facebook: {e}")
            return {"status": "error", "message": str(e)}

    def get_feed(self, limit: int = 10) -> Dict[str, Any]:
        try:
            response = requests.get(
                f"{self.base_url}/me/feed",
                params={"access_token": self.access_token, "limit": limit},
                timeout=15,
            )
            response.raise_for_status()
            return {"status": "success", "posts": response.json().get("data", [])}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Facebook feed: {e}")
            return {"status": "error", "message": str(e)}


class InstagramTools:
    """Interacts with the Instagram Graph API (via a connected Facebook Page/Business account)."""
    def __init__(self, access_token: str, ig_user_id: str):
        self.access_token = access_token
        self.ig_user_id = ig_user_id
        self.base_url = "https://graph.facebook.com/v19.0"

    def post_image(self, image_url: str, caption: str) -> Dict[str, Any]:
        try:
            create_response = requests.post(
                f"{self.base_url}/{self.ig_user_id}/media",
                params={"access_token": self.access_token},
                data={"image_url": image_url, "caption": caption},
                timeout=30,
            )
            create_response.raise_for_status()
            creation_id = create_response.json().get("id")
            publish_response = requests.post(
                f"{self.base_url}/{self.ig_user_id}/media_publish",
                params={"access_token": self.access_token},
                data={"creation_id": creation_id},
                timeout=30,
            )
            publish_response.raise_for_status()
            return {"status": "success", "result": publish_response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting to Instagram: {e}")
            return {"status": "error", "message": str(e)}

    def get_recent_posts(self, limit: int = 10) -> Dict[str, Any]:
        try:
            response = requests.get(
                f"{self.base_url}/{self.ig_user_id}/media",
                params={"access_token": self.access_token, "fields": "caption,timestamp,permalink", "limit": limit},
                timeout=15,
            )
            response.raise_for_status()
            return {"status": "success", "posts": response.json().get("data", [])}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Instagram posts: {e}")
            return {"status": "error", "message": str(e)}


class LinkedInTools:
    """Interacts with the LinkedIn API (UGC Posts) for the authenticated member."""
    def __init__(self, access_token: str, member_urn: str):
        self.access_token = access_token
        self.member_urn = member_urn  # e.g. "urn:li:person:abc123"
        self.base_url = "https://api.linkedin.com/v2"

    def post_update(self, message: str) -> Dict[str, Any]:
        try:
            response = requests.post(
                f"{self.base_url}/ugcPosts",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
                json={
                    "author": self.member_urn,
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {"text": message},
                            "shareMediaCategory": "NONE",
                        }
                    },
                    "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
                },
                timeout=15,
            )
            response.raise_for_status()
            return {"status": "success", "result": response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting to LinkedIn: {e}")
            return {"status": "error", "message": str(e)}


class SocialMediaManager:
    """A high-level facade for interacting with social media platforms."""
    def __init__(
        self,
        twitter_bearer: Optional[str] = None,
        reddit_creds: Optional[Dict] = None,
        facebook_access_token: Optional[str] = None,
        instagram_creds: Optional[Dict] = None,
        linkedin_creds: Optional[Dict] = None,
    ):
        self.twitter: Optional[TwitterTools] = None
        self.reddit: Optional[RedditTools] = None
        self.facebook: Optional[FacebookTools] = None
        self.instagram: Optional[InstagramTools] = None
        self.linkedin: Optional[LinkedInTools] = None

        if twitter_bearer:
            try:
                self.twitter = TwitterTools(bearer_token=twitter_bearer)
            except (ImportError, ConnectionError) as e:
                logger.error(f"Failed to initialize TwitterTools: {e}")

        if reddit_creds:
            try:
                self.reddit = RedditTools(**reddit_creds)
            except (ImportError, ConnectionError) as e:
                logger.error(f"Failed to initialize RedditTools: {e}")

        if facebook_access_token:
            self.facebook = FacebookTools(access_token=facebook_access_token)

        if instagram_creds:
            self.instagram = InstagramTools(**instagram_creds)

        if linkedin_creds:
            self.linkedin = LinkedInTools(**linkedin_creds)

    def search_posts(self, platform: SocialMediaPlatform, query: str, count: int = 5) -> Optional[List[Post]]:
        if platform == SocialMediaPlatform.TWITTER and self.twitter:
            return self.twitter.search_tweets(query, count=count)
        elif platform == SocialMediaPlatform.REDDIT and self.reddit:
            return self.reddit.search_submissions("all", query, limit=count)
        else:
            logger.error(f"Platform {platform.value} is not configured or supported for search.")
            return None

    def post_update(self, platform: SocialMediaPlatform, message: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        """Posts a status update to the given platform (Facebook, Instagram, or LinkedIn)."""
        if platform == SocialMediaPlatform.FACEBOOK and self.facebook:
            return self.facebook.post_update(message)
        elif platform == SocialMediaPlatform.INSTAGRAM and self.instagram:
            if not image_url:
                return {"status": "error", "message": "Instagram posts require an image_url."}
            return self.instagram.post_image(image_url, message)
        elif platform == SocialMediaPlatform.LINKEDIN and self.linkedin:
            return self.linkedin.post_update(message)
        else:
            return {"status": "error", "message": f"Platform {platform.value} is not configured or supported for posting."}

    def get_feed(self, platform: SocialMediaPlatform, limit: int = 10) -> Dict[str, Any]:
        """Fetches the authenticated user's own recent posts/feed from the given platform."""
        if platform == SocialMediaPlatform.FACEBOOK and self.facebook:
            return self.facebook.get_feed(limit)
        elif platform == SocialMediaPlatform.INSTAGRAM and self.instagram:
            return self.instagram.get_recent_posts(limit)
        else:
            return {"status": "error", "message": f"Platform {platform.value} is not configured or supported for feed retrieval."}


# --- Example Usage ---
if __name__ == "__main__":
    import json
    print("=========================================================")
    print("=== Integrated Social Media API (Live Demo) 🌐🗣️ ===")
    print("=========================================================")
    
    # --- PREREQUISITES ---
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    
    if not all([TWITTER_BEARER_TOKEN, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET]):
        print("\n!!! ERROR: Missing one or more required environment variables for the live demo.")
        print("Please set the following environment variables with your developer API credentials:")
        print("  - TWITTER_BEARER_TOKEN")
        print("  - REDDIT_CLIENT_ID")
        print("  - REDDIT_CLIENT_SECRET")
    else:
        social_manager = SocialMediaManager(
            twitter_bearer=TWITTER_BEARER_TOKEN,
            reddit_creds={
                "client_id": REDDIT_CLIENT_ID,
                "client_secret": REDDIT_CLIENT_SECRET,
                "user_agent": "DevinAI/1.0"
            }
        )

        search_query = "python programming"
        
        # --- 1. Search Twitter ---
        print(f"\n--- 1. Searching Twitter for '{search_query}' ---")
        if social_manager.twitter:
            twitter_results = social_manager.search_posts(SocialMediaPlatform.TWITTER, search_query, count=3)
            if twitter_results:
                print("  Live Twitter Results:")
                for post in twitter_results:
                    print(f"    - @{post.author_username}: {post.content[:80]}... (Likes: {post.stats.get('likes')})")
            else:
                print("  No recent tweets found for the query.")
        else:
            print("  Skipping Twitter search (module not initialized).")
            
        # --- 2. Search Reddit ---
        print(f"\n\n--- 2. Searching Reddit for '{search_query}' ---")
        if social_manager.reddit:
            reddit_results = social_manager.search_posts(SocialMediaPlatform.REDDIT, search_query, count=3)
            if reddit_results:
                print("  Live Reddit Results:")
                for post in reddit_results:
                    print(f"    - u/{post.author_username}: {post.content[:80]}... (Score: {post.stats.get('score')})")
            else:
                print("  No submissions found for the query.")
        else:
            print("  Skipping Reddit search (module not initialized).")


    print("\n=========================================================")
    print("=== Social Media API Prototype Complete ===")
    print("=========================================================")
