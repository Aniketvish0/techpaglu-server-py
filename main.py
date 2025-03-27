import asyncio
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from configparser import ConfigParser
from twikit import Client
import google.generativeai as genai
import json

# Configuration
config = ConfigParser()
config.read('config.ini')

# X (Twitter) Credentials
USERNAME = config['X']['username']
EMAIL = config['X']['email']
PASSWORD = config['X']['password']

# Gemini API Key
GEMINI_API_KEY = config['GEMINI']['api_key']

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://techpaglu.vercel.app"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize X client
client = Client(language='en-US')

# Login to X
async def x_login():
    try:
        await client.login(
            auth_info_1=USERNAME,
            auth_info_2=EMAIL,
            password=PASSWORD
        )
        client.save_cookies('cookies.json')
    except Exception as e:
        print(f"❌ Login failed: {e}")
        raise

# Load cookies
def load_cookies():
    try:
        client.load_cookies('cookies.json')
        return True
    except Exception as e:
        print(f"❌ Error loading cookies: {e}")
        return False

# Get User Tweets
async def get_tweets(username, max_tweets=300):
    try:
        # Ensure logged in
        if not load_cookies():
            print("🔄 Cookies not loaded, attempting login...")
            await x_login()
        
        # Fetch user information

        user = await client.get_user_by_screen_name(username)
        
        # Retrieve initial set of tweets
        tweets = await client.get_user_tweets(
            user_id=user.id, 
            tweet_type='Tweets', 
            count=50  # Start with a reasonable initial count
        )
        
        # List to store all tweets
        all_tweets = list(tweets)
        
        # Pagination loop
        try:
            while len(all_tweets) < max_tweets:
                # Try to get more tweets
                more_tweets = await tweets.next()
                
                # If no more tweets, break the loop
                if not more_tweets:
                    break
                
                # Add new tweets to the collection
                all_tweets.extend(more_tweets)
                
                # Update tweets for next iteration
                tweets = more_tweets
                
                # Optional: Break if we've reached or exceeded max_tweets
                if len(all_tweets) >= max_tweets:
                    break
        except Exception as e:
            print(f"❌ Pagination error: {e}")
        
        # Trim to max_tweets if necessary
        
        # Extract tweet texts
        tweet_texts = [tweet.text for tweet in all_tweets]
        
        result = {
            "total_tweets": len(tweet_texts),
            "tweets": tweet_texts,
            "profile_url": user.profile_image_url
        }
        return result
    
    except Exception as e:
        print(f"❌ Error retrieving tweets for {username}: {e}")
        return {"tweets": [], "profile_url": ""}
# Analyze Tweets with Gemini
def analyze_tweets_with_gemini(tweets):
    try:
        
        # Combine tweets into a single string
        tweets_text = " ".join(tweets)
        print(f"📝 Total tweet text length: {len(tweets_text)} characters")
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Prompt for tech enthusiasm analysis
        prompt = f"""
        Analyze the following tweets and provide a JSON response that evaluates the user's tech enthusiasm:
        all the tweets are in quotes("") seperated with commas(,)
        Tweets: {tweets_text}
        
        Please provide a JSON with these keys:
        - tech_enthusiasm_score: A score out of 100 representing how much of a tech enthusiast the person is
        - tech_topics_percentage: Percentage of tweets related to technology
        - key_tech_interests: Top 3-5 tech areas mentioned
        - analysis_summary: A brief explanation of the scoring
        
        Scoring Criteria:
        - How much the user is tweeting about technology and engineering and anythings related to technology
        - How much is the ratio of tech tweets
        """
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Try to parse the response as JSON
        try:
            # Extract JSON from response text
            json_start = response.text.find('{')
            json_end = response.text.rfind('}') + 1
            json_response = response.text[json_start:json_end]
            
            # Parse and validate JSON
            analysis = json.loads(json_response)
            return analysis
        except Exception as e:
            # Fallback parsing if direct JSON extraction fails
            return {
                "tech_enthusiasm_score": 50,
                "tech_topics_percentage": 50,
                "key_tech_interests": ["Unable to parse specific interests"],
                "analysis_summary": f"Analysis attempted. Raw response: {response.text}"
            }
    
    except Exception as e:
        return {
            "error": str(e),
            "tech_enthusiasm_score": 0
        }

# FastAPI Routes
@app.get("/analyse/{username}")
async def analyze_user(username: str):
    try:
        print(f"🔎 Starting analysis for username: {username}")
        
        # Get tweets
        tweets_data = await get_tweets(username)
        
        # Analyze tweets
        analysis = analyze_tweets_with_gemini(tweets_data['tweets'])
        
        # Combine results
        result = {
            **analysis,
            "total_tweets": tweets_data['total_tweets'],
            "tweets" : tweets_data['tweets'],
            "profile_url": tweets_data['profile_url']
        }
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Main entry point
if __name__ == "__main__":
    # Change to localhost
    print("🚀 Starting server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)