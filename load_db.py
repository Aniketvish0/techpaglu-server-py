from pymongo import MongoClient
import json

# MongoDB connection
MONGO_URI = "mongodb+srv://aniketvishwakarma2004:bXdX9y5uxGFBtc9N@techpaglu.agmdx6p.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["cookies_db"]
collection = db["cookies"]

# Load cookies.json and store in MongoDB
with open("cookies.json", "r") as f:
    cookies_data = json.load(f)
    collection.update_one({"_id": "cookie_storage"}, {"$set": {"data": cookies_data}}, upsert=True)

print("Cookies saved to MongoDB!")
