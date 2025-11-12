from pymongo import MongoClient
from dotenv import load_dotenv
from google import genai
from datetime import datetime, timedelta, timezone
import os, json, time

# --- Load environment ---
load_dotenv(".env")

# --- MongoDB setup ---
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["sales_agent"]
messages_collection = db["messages"]
print("✅ Connected to MongoDB")

# --- Gemini setup ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found in .env")

genai_client = genai.Client(api_key=GOOGLE_API_KEY)

# --- Gemini analysis function ---
def analyze_with_gemini(text):
    prompt = f"""
    Analyze the sentiment of this customer message and respond only with JSON:
    {{
      "sentiment": "positive" | "neutral" | "negative",
      "confidence": 0..1,
      "key_points": ["point 1", "point 2"],
      "recommendation": "next step"
    }}
    Message: "{text}"
    """
    try:
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        raw = (resp.text or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`").replace("json", "").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"⚠️ Error analyzing message: {e}")
        return None

# --- Get all messages (no time filter) ---
messages = list(messages_collection.find({}))
print(f"🧾 Found {len(messages)} total messages in database")

summary = {"positive": 0, "neutral": 0, "negative": 0}
analyzed_count = 0

# --- Analyze and update ---
for msg in messages:
    text = msg.get("content")
    if text:  # make sure message has text content
        result = analyze_with_gemini(text)
        if result:
            sentiment = result.get("sentiment", "neutral")
            summary[sentiment] = summary.get(sentiment, 0) + 1
            messages_collection.update_one(
                {"_id": msg["_id"]},
                {"$set": {"analysis": result}}
            )
            analyzed_count += 1
            print(f"✅ Updated {msg['_id']} | Sentiment: {sentiment}")
        time.sleep(1)  # avoid API rate limits

print(f"\n📊 Summary of sentiment updates ({analyzed_count} messages analyzed):")
for s, count in summary.items():
    print(f"  {s}: {count}")

print("\n🎉 Done!")
