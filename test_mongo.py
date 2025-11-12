from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv(".env")

uri = os.getenv("MONGODB_URI")
print(f"MongoDB URI loaded: {uri[:50]}...")  # Print first 50 chars

try:
    client = MongoClient(uri)
    db = client["sales_agent"]
    
    # Try to insert a test document
    test_collection = db["test"]
    result = test_collection.insert_one({"test": "hello", "timestamp": "now"})
    print(f"✅ MongoDB connection successful!")
    print(f"✅ Inserted test document with ID: {result.inserted_id}")
    
    # Clean up
    test_collection.delete_one({"_id": result.inserted_id})
    
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")