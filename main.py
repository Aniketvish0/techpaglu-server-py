import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from twikit import Client
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv('X_USERNAME')
EMAIL = os.getenv('X_EMAIL')
PASSWORD = os.getenv('X_PASSWORD')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


genai.configure(api_key=GEMINI_API_KEY)


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://techpaglu.vercel.app"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


client = Client(language='en-US')


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

def load_cookies():
    try:
        client.load_cookies('cookies.json')
        return True
    except Exception as e:
        print(f"❌ Error loading cookies: {e}")
        return False


async def get_tweets(username, max_tweets=300):
    try:
       
        if not load_cookies():
            print("🔄 Cookies not loaded, attempting login...")
            await x_login()
        

        user = await client.get_user_by_screen_name(username)
        
        tweets = await client.get_user_tweets(
            user_id=user.id, 
            tweet_type='Tweets', 
            count=50  
        )
        
        all_tweets = list(tweets)
        
        try:
            while len(all_tweets) < max_tweets:
               
                more_tweets = await tweets.next()
                
                if not more_tweets:
                    break
                
                all_tweets.extend(more_tweets)
                
                tweets = more_tweets
                
                if len(all_tweets) >= max_tweets:
                    break
        except Exception as e:
            print(f"❌ Pagination error: {e}")
        
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
        
        tweets_text = " ".join(tweets)
        print(f"📝 Total tweet text length: {len(tweets_text)} characters")
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        
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
        
        response = model.generate_content(prompt)
        
        # Try to parse the response as JSON
        try:
            json_start = response.text.find('{')
            json_end = response.text.rfind('}') + 1
            json_response = response.text[json_start:json_end]
            
            analysis = json.loads(json_response)
            return analysis
        except Exception as e:
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
        
        tweets_data = await get_tweets(username)
    
        analysis = analyze_tweets_with_gemini(tweets_data['tweets'])
       
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
    print("🚀 Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)