import asyncio
import os
import json
from twikit import Client
from configparser import ConfigParser

# Configuration
QUERY = "chatgpt"
COOKIES_FILE = 'cookies.json'
config = ConfigParser()
config.read('config.ini')
username = config['X']['username']
email = config['X']['email']
password = config['X']['password']
client = Client(language='en-US')

# Login to Twitter
async def x_login():
    try:
        await client.login(
            auth_info_1=username,
            auth_info_2=email,
            password=password
        )
        
        # Explicitly save cookies after login
        await save_cookies()
        print("Login successful and cookies saved.")
    except Exception as e:
        print(f"Login failed: {e}")
        raise

# Save cookies function with error handling
async def save_cookies():
    try:
        # Get the cookies
        client.save_cookies('cookies.json')
    except Exception as e:
        print(f"Error saving cookies: {e}")

# Load cookies function with error handling
def load_cookies():
    try:
       client.load_cookies('cookies.json')
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return False

# Get Tweets
async def get_tweets(client, username, max_tweets=100):
    """
    Retrieve tweets from a specific user handle
    
    :param client: Twikit Client instance
    :param username: Twitter/X username without the '@' symbol
    :param max_tweets: Maximum number of tweets to retrieve (default 100)
    :return: List of tweets from the specified user
    """
    try:
        # Fetch user information first
        user = await client.get_user_by_screen_name(username)
        
        # Retrieve user's tweets
        tweets = await client.get_user_tweets(
            user_id=user.id, 
            tweet_type='Tweets', 
            count=max_tweets
        )
        for tweet in tweets:
            print(f"Tweet by {username}:")
            print(f"Content: {tweet.text}")
            print(f"Profile Image: {user.profile_image_url}")
            print("---")
        return tweets
    
    except Exception as e:
        print(f"Error retrieving tweets for {username}: {e}")
        return []


# Main Async Function
async def main():
    # Try to load existing cookies first
    if not load_cookies():
        # If loading cookies fails, perform login
        await x_login()
    # Fetch tweets
    try:
        target_user = "aniketvish0" 
        user_tweets = await get_tweets(client, target_user, max_tweets=50)
    except Exception as e:
        print(f"An error occurred: {e}")


# Run the event loop
if __name__ == "__main__":
    asyncio.run(main())