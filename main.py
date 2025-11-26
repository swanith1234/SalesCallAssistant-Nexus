import os
import json
import logging
from datetime import datetime, timezone
from typing import Literal, List, Dict, Optional

from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import uvicorn
from google import genai
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError, OperationFailure
from livekit import api

# Import auth helpers (must exist in your project)
from auth import (
    UserCreate, UserLogin, Token, UserResponse,
    hash_password, verify_password, create_access_token,
    user_to_response, security, decode_token
)

# -------------------------------------------------------------------
# SETUP
# -------------------------------------------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)

# === Google Gemini Setup ===
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")
genai_client = genai.Client(api_key=GOOGLE_API_KEY)

# === LiveKit Setup ===
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_WS_URL = os.getenv("LIVEKIT_WS_URL", "ws://localhost:7880")

if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
    raise ValueError("Missing LIVEKIT_API_KEY or LIVEKIT_API_SECRET")

# === MongoDB Setup ===
MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise ValueError("MONGODB_URI not found in environment variables")

try:
    client = MongoClient(MONGO_URI, connect=False, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    logging.info("✅ Connected to MongoDB")
except PyMongoError as e:
    logging.error(f"❌ Mongo error: {e}")
    raise

db = client["sales_agent"]

# Create collections if they don't exist
for col in ["messages", "transcripts", "call_summaries", "users"]:
    if col not in db.list_collection_names():
        db.create_collection(col)

messages_collection = db["messages"]
sessions_collection = db["transcripts"]
call_summaries_collection = db["call_summaries"]
users_collection = db["users"]

# ✅ SAFE INDEX CREATION
try:
    messages_collection.create_index(
        [("room_id", ASCENDING), ("sent_ts", ASCENDING)],
        name="room_ts_idx"
    )
except OperationFailure as e:
    logging.warning(f"Could not create messages index (may already exist): {e}")

try:
    users_collection.create_index("email", unique=True, name="email_idx")
except OperationFailure as e:
    logging.warning(f"Could not create users index (may already exist): {e}")

try:
    call_summaries_collection.create_index("userId", name="userId_idx")
except OperationFailure as e:
    logging.warning(f"Could not create call_summaries index (may already exist): {e}")

try:
    sessions_collection.create_index(
        [("session_id", ASCENDING), ("timestamp", ASCENDING)],
        name="session_ts_idx"
    )
except OperationFailure as e:
    logging.warning(f"Could not create sessions index (may already exist): {e}")

# === In-memory temporary stores ===
STORE: Dict[str, List[dict]] = {}
ANALYSIS_STORE: Dict[str, dict] = {}

# -------------------------------------------------------------------
# MODELS
# -------------------------------------------------------------------
class TranscriptIn(BaseModel):
    text: str = Field(..., min_length=1)
    speaker: Literal["user", "assistant"]
    timestamp: float
    room_id: str

class SentimentAnalysis(BaseModel):
    sentiment: str
    confidence: float
    key_points: List[str]
    recommendation_to_salesperson: str

class TranscriptResponse(BaseModel):
    ok: bool
    room_id: str
    count_in_room: int
    analysis: Optional[SentimentAnalysis] = None
    latest_user_message: Optional[str] = None

class SaveSessionResponse(BaseModel):
    ok: bool
    room_id: str
    mongo_id: Optional[str] = None
    total_messages: int

class TokenRequest(BaseModel):
    room_name: str
    participant_name: str
    userId: Optional[str] = None

class MessageResponse(BaseModel):
    text: str
    speaker: Literal["user", "assistant"]
    sent_ts: float
    received_at: str
    room_id: str

class AnalysisResponse(BaseModel):
    room_id: str
    analysis: Optional[SentimentAnalysis]

# -------------------------------------------------------------------
# APP SETUP
# -------------------------------------------------------------------
app = FastAPI(title="Sales Voice Backend", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# AUTH HELPERS
# -------------------------------------------------------------------
async def get_current_user_dep(credentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")

    user = users_collection.find_one({"_id": user_id})
    if not user:
        raise HTTPException(401, "Invalid authentication")

    return user

# -------------------------------------------------------------------
# AUTH ROUTES
# -------------------------------------------------------------------
@app.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    if users_collection.find_one({"email": user_data.email}):
        raise HTTPException(400, "Email already registered")

    user_id = f"user_{int(datetime.now(timezone.utc).timestamp()*1000)}"

    user_doc = {
        "_id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "phone_number": user_data.phone_number,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    users_collection.insert_one(user_doc)

    token = create_access_token({"sub": user_id, "email": user_data.email})
    return Token(access_token=token, token_type="bearer", user=user_to_response(user_doc))


@app.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user = users_collection.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(401, "Invalid email or password")

    token = create_access_token({"sub": user["_id"], "email": user["email"]})
    return Token(access_token=token, token_type="bearer", user=user_to_response(user))


@app.get("/auth/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user_dep)):
    return user_to_response(current_user)

# -------------------------------------------------------------------
# LIVEKIT TOKEN ENDPOINT
# -------------------------------------------------------------------
@app.post("/get-token")
async def get_token(request: TokenRequest):
    try:
        user_id = request.userId or f"user_{int(datetime.now().timestamp()*1000)}"
        room_with_user = f"{request.room_name}-user-{user_id}"

        token = api.AccessToken(
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET
        )

        token.with_identity(request.participant_name)
        token.with_name(request.participant_name)
        token.with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_with_user,
                can_publish=True,
                can_subscribe=True,
            )
        )

        jwt_token = token.to_jwt()

        return {
            "token": jwt_token,
            "url": LIVEKIT_WS_URL,
            "room": room_with_user,
            "userId": user_id
        }

    except Exception as e:
        logging.exception("Token generation error")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------
# GEMINI ANALYSIS FUNCTIONS
# -------------------------------------------------------------------
def analyze_with_gemini(user_text: str) -> dict:
    prompt = f"""
Analyze the customer's message:
"{user_text}"

Return strict JSON only:
{{
  "sentiment": "positive" | "neutral" | "negative",
  "confidence": 0..1,
  "key_points": ["point1", "point2"],
  "recommendation_to_salesperson": "short advice"
}}
"""

    try:
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        raw = (resp.text or "").strip()

        # clean markdown fences
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)

        return {
            "sentiment": parsed.get("sentiment", "neutral").lower(),
            "confidence": float(parsed.get("confidence", 0.0)),
            "key_points": parsed.get("key_points", []),
            "recommendation_to_salesperson": parsed.get(
                "recommendation_to_salesperson",
                "Continue the conversation normally."
            ),
        }

    except Exception as e:
        logging.exception("Gemini error")
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "key_points": [],
            "recommendation_to_salesperson": "Unable to analyze.",
        }


def analyze_full_conversation(messages: List[dict]) -> dict:
    """Analyze the entire conversation for comprehensive insights"""
    
    if not messages or len(messages) == 0:
        return {
            "sentiment": "neutral",
            "confidence": 0.5,
            "key_points": ["No conversation data"],
            "recommendation_to_salesperson": "No messages to analyze.",
        }
    
    conversation_text = "\n".join([
        f"{'Customer' if msg['speaker'] == 'user' else 'Agent'}: {msg['text']}"
        for msg in messages
    ])
    
    if len(conversation_text) > 3000:
        conversation_text = conversation_text[-3000:]
    
    logging.info(f"📝 Conversation text length: {len(conversation_text)} characters")
    
    prompt = f"""
Analyze this complete sales conversation about AI/ML educational courses:

CONVERSATION:
{conversation_text}

Provide a comprehensive analysis in ONLY valid JSON format (no markdown, no code blocks):

{{
  "sentiment": "positive" OR "neutral" OR "negative",
  "confidence": 0.0 to 1.0,
  "key_points": ["point1", "point2", "point3"],
  "customer_interests": ["interest1", "interest2"],
  "customer_concerns": ["concern1", "concern2"],
  "recommendation_to_salesperson": "clear actionable recommendation"
}}

Analysis Guidelines:
- sentiment: "positive" if customer is interested/engaged, "negative" if explicitly rejecting/upset, "neutral" if undecided
- confidence: 0.8+ for clear sentiment, 0.5-0.7 for mixed signals
- key_points: 3-5 most important things from the ENTIRE conversation
- customer_interests: what did the customer ask about or show interest in?
- customer_concerns: what objections or hesitations did they express?
- recommendation: ONE specific action the salesperson should take next

IMPORTANT: Always provide at least 3 key points based on the conversation content.
"""

    try:
        logging.info("🤖 Calling Gemini API for full conversation analysis...")
        
        resp = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        logging.info("✅ Gemini API responded successfully")
        
        raw = (resp.text or "").strip()
        logging.info(f"📄 Raw response length: {len(raw)} characters")

        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)
        logging.info("✅ JSON parsed successfully")

        all_key_points = []
        all_key_points.extend(parsed.get("key_points", []))
        all_key_points.extend(parsed.get("customer_interests", []))
        all_key_points.extend(parsed.get("customer_concerns", []))
        
        logging.info(f"📊 Extracted {len(all_key_points)} key points from analysis")
        
        if not all_key_points:
            logging.warning("⚠️ No key points in Gemini response, extracting from messages")
            user_messages = [m for m in messages if m['speaker'] == 'user']
            if user_messages:
                all_key_points = [f"Customer message: {m['text'][:80]}" for m in user_messages[:3]]
            else:
                all_key_points = ["Conversation completed"]

        result = {
            "sentiment": parsed.get("sentiment", "neutral").lower(),
            "confidence": max(float(parsed.get("confidence", 0.6)), 0.5),
            "key_points": all_key_points[:7],
            "recommendation_to_salesperson": parsed.get(
                "recommendation_to_salesperson",
                "Follow up based on customer interests expressed in the conversation."
            ),
        }
        
        logging.info(f"✅ Analysis complete: {result['sentiment']} sentiment with {len(result['key_points'])} key points")
        return result
        
    except json.JSONDecodeError as e:
        logging.error(f"❌ JSON parse error: {e}")
        user_messages = [m for m in messages if m['speaker'] == 'user']
        return {
            "sentiment": "neutral",
            "confidence": 0.5,
            "key_points": [m['text'][:100] for m in user_messages[:5]] if user_messages else ["Customer engaged in conversation"],
            "recommendation_to_salesperson": "Review full transcript for context and follow up appropriately.",
        }
    except Exception as e:
        logging.error(f"❌ Full conversation analysis error: {type(e).__name__}: {str(e)}")
        user_messages = [m for m in messages if m['speaker'] == 'user']
        return {
            "sentiment": "neutral",
            "confidence": 0.5,
            "key_points": [
                f"Conversation had {len(messages)} total messages",
                f"Customer spoke {len(user_messages)} times",
                "See transcript for details"
            ],
            "recommendation_to_salesperson": "Review the conversation transcript and follow up based on customer's responses.",
        }

# -------------------------------------------------------------------
# PROCESS TRANSCRIPTION
# -------------------------------------------------------------------
@app.post("/process-transcription", response_model=TranscriptResponse)
async def process_transcription(payload: TranscriptIn):
    try:
        text_clean = payload.text.strip()
        if not text_clean:
            raise HTTPException(422, "Empty message")

        record = {
            "text": text_clean,
            "speaker": payload.speaker,
            "sent_ts": float(payload.timestamp),
            "received_at": datetime.now(timezone.utc).isoformat(),
            "room_id": payload.room_id,
        }

        STORE.setdefault(payload.room_id, []).append(record)

        try:
            messages_collection.insert_one(record.copy())
        except PyMongoError as e:
            logging.error(f"Mongo insert failed: {e}")

        analysis_obj = None
        latest_user_message = None

        if payload.speaker == "user":
            latest_user_message = text_clean
            analysis_dict = analyze_with_gemini(text_clean)
            ANALYSIS_STORE[payload.room_id] = analysis_dict
            analysis_obj = SentimentAnalysis(**analysis_dict)
            
            logging.info(
                f"✅ Analysis: {analysis_obj.sentiment} "
                f"({analysis_obj.confidence:.2f}) - {analysis_obj.recommendation_to_salesperson}"
            )

        return TranscriptResponse(
            ok=True,
            room_id=payload.room_id,
            count_in_room=len(STORE[payload.room_id]),
            analysis=analysis_obj,
            latest_user_message=latest_user_message,
        )

    except Exception as e:
        logging.exception("Processing error")
        raise HTTPException(500, str(e))

# -------------------------------------------------------------------
# GET LATEST ANALYSIS FOR A ROOM
# -------------------------------------------------------------------
@app.get("/analysis/{room_id}", response_model=AnalysisResponse)
async def get_latest_analysis(room_id: str):
    """Get the latest sentiment analysis for a room"""
    try:
        # First check in-memory store
        if room_id in ANALYSIS_STORE:
            analysis_dict = ANALYSIS_STORE[room_id]
            return AnalysisResponse(
                room_id=room_id,
                analysis=SentimentAnalysis(**analysis_dict)
            )
        
        # If not in memory, return neutral default
        return AnalysisResponse(
            room_id=room_id,
            analysis=None
        )

    except Exception as e:
        logging.exception("Error fetching analysis")
        raise HTTPException(500, str(e))

# -------------------------------------------------------------------
# GET MESSAGES FOR A ROOM
# -------------------------------------------------------------------
@app.get("/messages/{room_id}")
async def get_messages(room_id: str, limit: int = Query(50, ge=1, le=500)):
    """Get recent messages for a room"""
    try:
        messages = STORE.get(room_id, [])
        
        if len(messages) < limit:
            try:
                mongo_messages = list(
                    messages_collection
                    .find({"room_id": room_id}, {"_id": 0})
                    .sort("sent_ts", DESCENDING)
                    .limit(limit)
                )
                all_messages = messages + mongo_messages
                all_messages.sort(key=lambda x: x.get("sent_ts", 0))
                messages = all_messages[-limit:] if len(all_messages) > limit else all_messages
            except PyMongoError as e:
                logging.error(f"MongoDB query error: {e}")
        
        return {
            "room_id": room_id,
            "messages": messages[-limit:]
        }

    except Exception as e:
        logging.exception("Error fetching messages")
        raise HTTPException(500, str(e))

# -------------------------------------------------------------------
# SAVE SESSION
# -------------------------------------------------------------------
@app.post("/save-session", response_model=SaveSessionResponse)
async def save_session(room_id: str = Query(...)):
    try:
        if room_id not in STORE:
            existing = sessions_collection.find_one({"session_id": room_id})
            if existing:
                return SaveSessionResponse(
                    ok=True,
                    room_id=room_id,
                    mongo_id=str(existing.get("_id", "")),
                    total_messages=existing.get("total_messages", 0),
                )
            raise HTTPException(404, "Room not found in memory or database")

        messages = STORE[room_id]
        existing_session = sessions_collection.find_one({"session_id": room_id})
        
        logging.info(f"🔍 Analyzing full conversation with {len(messages)} messages")
        full_analysis = analyze_full_conversation(messages)
        
        if existing_session:
            sessions_collection.update_one(
                {"session_id": room_id},
                {
                    "$set": {
                        "messages": messages,
                        "total_messages": len(messages),
                        "latest_analysis": full_analysis,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                }
            )
            mongo_id = str(existing_session["_id"])
        else:
            session_doc = {
                "session_id": room_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "messages": messages,
                "total_messages": len(messages),
                "latest_analysis": full_analysis,
            }
            result = sessions_collection.insert_one(session_doc)
            mongo_id = str(result.inserted_id)

        logging.info(f"💾 Session {room_id} saved with {len(messages)} messages")

        return SaveSessionResponse(
            ok=True,
            room_id=room_id,
            mongo_id=mongo_id,
            total_messages=len(messages),
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Save error")
        raise HTTPException(500, str(e))

# -------------------------------------------------------------------
# END CALL — SAVE SUMMARY
# -------------------------------------------------------------------
@app.post("/end-call")
async def end_call(
    room_id: str = Query(...), 
    phone_number: Optional[str] = Query(None), 
    userId: str = Query(...)
):
    """End call and create comprehensive summary"""
    # Avoid duplicates
    existing = call_summaries_collection.find_one({"room_id": room_id})
    if existing:
        return {
            "ok": True,
            "message": "Summary already exists.",
            "duration": existing.get("duration")
        }

    messages = STORE.get(room_id, [])
    if not messages:
        # Try DB fallback with prefix match
        try:
            messages = list(
                messages_collection
                .find({"room_id": {"$regex": f"^{room_id}"}}, {"_id": 0})
                .sort("sent_ts", 1)
            )
        except Exception as e:
            logging.error(f"Failed to fetch messages from DB: {e}")
            messages = []

    if not messages:
        raise HTTPException(404, "No messages found")

    # Compute duration
    try:
        start = float(messages[0]["sent_ts"])
        end = float(messages[-1]["sent_ts"])
        duration_seconds = max(0, int(round(end - start)))
    except Exception:
        duration_seconds = 0
    duration_mmss = f"{duration_seconds//60}:{duration_seconds%60:02d}"

    transcript = "\n".join([f"{m['speaker']}: {m['text']}" for m in messages])

    # Gemini Summary
    try:
        prompt = f"""
Summarize this SALES CALL:
I want you to give the value of userExperience only  as Positive, Neutral, or Negative based on the customer's tone and engagement..no other text.
{transcript}

Return ONLY JSON:
{{
  "summary": "",
  "callPurpose": "",
  "userExperience": ""
}}
"""
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        raw = (resp.text or "").strip().replace("```json", "").replace("```", "")
        summary_data = json.loads(raw)
    except Exception:
        summary_data = {
            "summary": "", 
            "callPurpose": "", 
            "userExperience": "Neutral"
        }

    # Lookup user for email / phone fallback
    user = users_collection.find_one({"_id": userId})
    saved_phone = phone_number or (user.get("phone_number") if user else None)

    doc = {
        "room_id": room_id,
        "userId": userId,
        "userEmail": user["email"] if user else None,
        "userName": user["full_name"] if user else None,
        "summary": summary_data.get("summary", ""),
        "callPurpose": summary_data.get("callPurpose", ""),
        "userExperience": summary_data.get("userExperience", "Neutral"),
        "phoneNumber": saved_phone,
        "duration": {"seconds": int(duration_seconds), "mmss": duration_mmss},
        "callDate": datetime.now(timezone.utc).isoformat(),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "totalMessages": len(messages)
    }

    result = call_summaries_collection.insert_one(doc)

    # Cleanup memory
    STORE.pop(room_id, None)
    ANALYSIS_STORE.pop(room_id, None)

    return {
        "ok": True,
        "mongo_id": str(result.inserted_id),
        "duration": doc["duration"]
    }

# -------------------------------------------------------------------
# GET DASHBOARD STATS
# -------------------------------------------------------------------
@app.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user_dep)):
    """Get dynamic dashboard statistics for the current user"""
    try:
        userId = current_user["_id"]
        
        # Query filter for current user
        query_filter = {"userId": userId}
        
        # Total calls count
        total_calls = call_summaries_collection.count_documents(query_filter)
        
        # Get all calls for this user
        all_calls = list(call_summaries_collection.find(query_filter, {"_id": 0}))
        
        # Calculate success rate (Positive / Total)
        if total_calls > 0:
            positive_calls = sum(1 for c in all_calls if c.get("userExperience") == "Positive")
            success_rate = round((positive_calls / total_calls) * 100)
        else:
            success_rate = 0
        
        # Active users is always 1 for user-specific view
        active_users = 1
        
        # Calculate average rating
        if total_calls > 0:
            rating_map = {"Positive": 5, "Neutral": 3, "Negative": 2}
            total_rating = sum(rating_map.get(c.get("userExperience", "Neutral"), 3) for c in all_calls)
            avg_rating = round(total_rating / total_calls, 1)
        else:
            avg_rating = 0.0
        
        # Get previous period stats for trends (last 30 days vs previous 30 days)
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)
        
        # Current period
        current_period_filter = {**query_filter, "callDate": {"$gte": thirty_days_ago.isoformat()}}
        current_calls = call_summaries_collection.count_documents(current_period_filter)
        
        # Previous period
        previous_period_filter = {
            **query_filter, 
            "callDate": {
                "$gte": sixty_days_ago.isoformat(),
                "$lt": thirty_days_ago.isoformat()
            }
        }
        previous_calls = call_summaries_collection.count_documents(previous_period_filter)
        
        # Calculate trend
        if previous_calls > 0:
            calls_trend = round(((current_calls - previous_calls) / previous_calls) * 100)
        else:
            calls_trend = 100 if current_calls > 0 else 0
        
        # Success rate trend
        current_positive = call_summaries_collection.count_documents({
            **query_filter,
            "callDate": {"$gte": thirty_days_ago.isoformat()},
            "userExperience": "Positive"
        })
        current_success_rate = round((current_positive / current_calls) * 100) if current_calls > 0 else 0
        
        previous_positive = call_summaries_collection.count_documents({
            **query_filter,
            "callDate": {
                "$gte": sixty_days_ago.isoformat(),
                "$lt": thirty_days_ago.isoformat()
            },
            "userExperience": "Positive"
        })
        previous_success_rate = round((previous_positive / previous_calls) * 100) if previous_calls > 0 else 0
        
        success_trend = current_success_rate - previous_success_rate
        
        # Calculate rating trend
        if current_calls > 0 and previous_calls > 0:
            current_calls_data = list(call_summaries_collection.find(current_period_filter, {"userExperience": 1}))
            previous_calls_data = list(call_summaries_collection.find(previous_period_filter, {"userExperience": 1}))
            
            rating_map = {"Positive": 5, "Neutral": 3, "Negative": 2}
            current_avg = sum(rating_map.get(c.get("userExperience", "Neutral"), 3) for c in current_calls_data) / len(current_calls_data)
            previous_avg = sum(rating_map.get(c.get("userExperience", "Neutral"), 3) for c in previous_calls_data) / len(previous_calls_data)
            rating_trend = round(current_avg - previous_avg, 1)
        else:
            rating_trend = 0.0
        
        return {
            "total_calls": total_calls,
            "success_rate": success_rate,
            "active_users": active_users,
            "avg_rating": avg_rating,
            "trends": {
                "calls": f"+{calls_trend}%" if calls_trend >= 0 else f"{calls_trend}%",
                "success_rate": f"+{success_trend}%" if success_trend >= 0 else f"{success_trend}%",
                "users": "+0%",  # Always 0 for single user view
                "rating": f"+{rating_trend}" if rating_trend >= 0 else f"{rating_trend}"
            }
        }
    
    except Exception as e:
        logging.exception("Error fetching dashboard stats")
        raise HTTPException(500, str(e))

# -------------------------------------------------------------------
# RECENT CALLS
# -------------------------------------------------------------------
@app.get("/recent-calls")
async def recent_calls(
    limit: int = Query(20, ge=1, le=200),
    current_user: dict = Depends(get_current_user_dep)
):
    """Return recent call summaries for the current logged-in user (newest first)"""
    try:
        userId = current_user["_id"]
        
        # Query filter for current user only
        query_filter = {"userId": userId}
        
        calls = list(
            call_summaries_collection
            .find(query_filter, {"_id": 0})
            .sort("callDate", -1)
            .limit(limit)
        )
    except Exception as e:
        logging.error(f"Failed to query recent calls: {e}")
        calls = []

    output = []
    for c in calls:
        exp = c.get("userExperience", "Neutral")
        sentiment = "Happy" if exp == "Positive" else "Upset" if exp == "Negative" else "Neutral"
        rating_map = {"Positive": 5, "Neutral": 3, "Negative": 2}

        output.append({
            "id": c.get("room_id", ""),
            "customerName": c.get("userName") or c.get("userEmail") or "Unknown",
            "sentiment": sentiment,
            "duration": c.get("duration", {}).get("mmss", "0:00"),
            "rating": rating_map.get(exp, 3),
            "callDate": c.get("callDate", ""),
            "summary": c.get("summary", ""),
            "callPurpose": c.get("callPurpose", ""),
            "phoneNumber": c.get("phoneNumber")
        })

    return {"calls": output}

# -------------------------------------------------------------------
# GET SINGLE CALL SUMMARY
# -------------------------------------------------------------------
@app.get("/call-summary/{room_id}")
async def get_call_summary(room_id: str):
    """Get detailed call summary for a specific room"""
    summary = call_summaries_collection.find_one({"room_id": room_id}, {"_id": 0})
    if not summary:
        raise HTTPException(404, "Summary not found")
    return summary

# -------------------------------------------------------------------
# GET CONVERSATIONS
# -------------------------------------------------------------------
@app.get("/conversations")
async def get_conversations():
    try:
        in_memory = [
            {"room_id": room_id, "count": len(messages)}
            for room_id, messages in STORE.items()
        ]
        
        try:
            saved_sessions = list(
                sessions_collection
                .find({}, {"_id": 0, "session_id": 1, "total_messages": 1, "timestamp": 1})
                .sort("timestamp", DESCENDING)
                .limit(50)
            )
            mongo_sessions = [
                {"room_id": s["session_id"], "count": s.get("total_messages", 0)}
                for s in saved_sessions
            ]
        except PyMongoError as e:
            logging.error(f"MongoDB query error: {e}")
            mongo_sessions = []
        
        all_sessions = {}
        for sess in in_memory + mongo_sessions:
            all_sessions[sess["room_id"]] = sess
        
        return {
            "sessions": list(all_sessions.values())
        }
    except Exception as e:
        raise HTTPException(500, str(e))

# -------------------------------------------------------------------
# GET STORED SESSION
# -------------------------------------------------------------------
@app.get("/session/{session_id}")
async def get_session(session_id: str):
    try:
        doc = sessions_collection.find_one({"session_id": session_id}, {"_id": 0})
        
        if not doc:
            if session_id in STORE:
                return {
                    "session_id": session_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "messages": STORE[session_id],
                    "total_messages": len(STORE[session_id]),
                    "latest_analysis": ANALYSIS_STORE.get(session_id),
                }
            raise HTTPException(404, f"Session not found: {session_id}")
        
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Session fetch error")
        raise HTTPException(500, str(e))

# -------------------------------------------------------------------
# DEBUG ENDPOINTS
# -------------------------------------------------------------------
@app.get("/debug/sessions")
async def debug_sessions():
    """Debug endpoint to see all sessions"""
    try:
        sessions = list(sessions_collection.find({}, {"_id": 0}).limit(10))
        return {"count": len(sessions), "sessions": sessions}
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/room/{room_id}")
async def debug_room(room_id: str):
    """Debug endpoint to see everything about a specific room"""
    try:
        return {
            "room_id": room_id,
            "in_memory_messages": len(STORE.get(room_id, [])),
            "messages": STORE.get(room_id, [])[-5:] if room_id in STORE else [],
            "has_analysis": room_id in ANALYSIS_STORE,
            "analysis": ANALYSIS_STORE.get(room_id),
            "db_message_count": messages_collection.count_documents({"room_id": room_id})
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/analysis-store")
async def debug_analysis_store():
    """Debug endpoint to see all stored analyses"""
    return {
        "total_rooms": len(ANALYSIS_STORE),
        "rooms": list(ANALYSIS_STORE.keys()),
        "analyses": ANALYSIS_STORE
    }

# -------------------------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------------------------
@app.get("/health")
async def health_check():
    try:
        client.admin.command("ping")
        mongodb_status = "connected"
    except Exception:
        mongodb_status = "disconnected"
    return {
        "status": "healthy", 
        "rooms": len(STORE), 
        "mongodb": mongodb_status
    }

# -------------------------------------------------------------------
# MAIN ENTRY
# -------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)