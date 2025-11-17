# main1.py - FINAL (fixed recent-calls + ensure phone saved when available + safe index creation)
import os
import json
import logging
from datetime import datetime, timezone
from typing import Literal, List, Dict, Optional

from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn
from google import genai
from pymongo import MongoClient, ASCENDING, errors as pymongo_errors
from livekit import api

# Import auth helpers (must exist in your project)
from auth import (
    UserCreate, UserLogin, Token, UserResponse,
    hash_password, verify_password, create_access_token,
    user_to_response, security, decode_token
)

# Load environment
load_dotenv()
logging.basicConfig(level=logging.INFO)

# API KEYS
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY missing")

genai_client = genai.Client(api_key=GOOGLE_API_KEY)

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_WS_URL = os.getenv("LIVEKIT_WS_URL", "ws://localhost:7880")

MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise ValueError("MONGODB_URI missing")

# ----------------------------------------------------------
# CONNECT TO MONGODB
# ----------------------------------------------------------
try:
    client = MongoClient(MONGO_URI, connect=False, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    logging.info("✅ Connected to MongoDB")
except pymongo_errors.PyMongoError as e:
    logging.error(f"❌ Mongo error: {e}")
    raise

db = client["sales_agent"]

# Required collections
for col in ["messages", "transcripts", "call_summaries", "users"]:
    if col not in db.list_collection_names():
        db.create_collection(col)

messages_collection = db["messages"]
sessions_collection = db["transcripts"]
call_summaries_collection = db["call_summaries"]
users_collection = db["users"]

# Indexes - create safely (ignore index conflict errors)
try:
    messages_collection.create_index(
        [("room_id", ASCENDING), ("sent_ts", ASCENDING)],
        name="room_ts_idx"
    )
except pymongo_errors.OperationFailure as e:
    logging.warning(f"Could not create messages index (may already exist): {e}")

try:
    users_collection.create_index("email", unique=True, name="email_idx")
except pymongo_errors.OperationFailure as e:
    logging.warning(f"Could not create users index (may already exist): {e}")

try:
    call_summaries_collection.create_index("userId", name="userId_idx")
except pymongo_errors.OperationFailure as e:
    logging.warning(f"Could not create call_summaries index (may already exist): {e}")

# In-memory store
STORE: Dict[str, List[dict]] = {}
ANALYSIS_STORE: Dict[str, dict] = {}

# ----------------------------------------------------------
# MODELS
# ----------------------------------------------------------
class TranscriptIn(BaseModel):
    text: str
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
    analysis: Optional[SentimentAnalysis]
    latest_user_message: Optional[str]


class SaveSessionResponse(BaseModel):
    ok: bool
    room_id: str
    mongo_id: Optional[str]
    total_messages: int


class TokenRequest(BaseModel):
    room_name: str
    participant_name: str
    userId: Optional[str] = None


# ----------------------------------------------------------
# FASTAPI APP
# ----------------------------------------------------------
app = FastAPI(title="Sales Voice Backend", version="3.2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------
# AUTH HELPERS
# ----------------------------------------------------------
async def get_current_user_dep(credentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")

    user = users_collection.find_one({"_id": user_id})
    if not user:
        raise HTTPException(401, "Invalid authentication")

    return user


# ----------------------------------------------------------
# AUTH ROUTES
# ----------------------------------------------------------
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


# ----------------------------------------------------------
# LIVEKIT TOKEN
# ----------------------------------------------------------
@app.post("/get-token")
async def get_token(request: TokenRequest):
    user_id = request.userId or f"user_{int(datetime.now().timestamp()*1000)}"
    room_with_user = f"{request.room_name}-user-{user_id}"

    token = api.AccessToken(api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
    token.with_identity(request.participant_name)
    token.with_name(request.participant_name)
    token.with_grants(api.VideoGrants(room_join=True, room=room_with_user, can_publish=True, can_subscribe=True))

    return {"token": token.to_jwt(), "url": LIVEKIT_WS_URL, "room": room_with_user, "userId": user_id}


# ----------------------------------------------------------
# PROCESS TRANSCRIPTION
# ----------------------------------------------------------
@app.post("/process-transcription", response_model=TranscriptResponse)
async def process_transcription(payload: TranscriptIn):
    text = payload.text.strip()

    record = {
        "text": text,
        "speaker": payload.speaker,
        "sent_ts": payload.timestamp,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "room_id": payload.room_id
    }

    STORE.setdefault(payload.room_id, []).append(record)
    try:
        messages_collection.insert_one(record)
    except Exception as e:
        logging.warning(f"Failed to insert message into MongoDB: {e}")

    analysis = None
    latest_user = text if payload.speaker == "user" else None

    if payload.speaker == "user":
        try:
            prompt = f"""
Analyze the following message:
{text}

Return ONLY JSON:
{{
  "sentiment": "positive" | "neutral" | "negative",
  "confidence": 0.0,
  "key_points": [],
  "recommendation_to_salesperson": ""
}}
"""
            resp = genai_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            raw = (resp.text or "").strip().replace("```", "")
            result = json.loads(raw)
        except Exception:
            result = {
                "sentiment": "neutral",
                "confidence": 0.0,
                "key_points": [],
                "recommendation_to_salesperson": ""
            }

        ANALYSIS_STORE[payload.room_id] = result
        try:
            analysis = SentimentAnalysis(**result)
        except Exception:
            analysis = None

    return TranscriptResponse(
        ok=True,
        room_id=payload.room_id,
        count_in_room=len(STORE[payload.room_id]),
        analysis=analysis,
        latest_user_message=latest_user
    )


# ----------------------------------------------------------
# SAVE SESSION
# ----------------------------------------------------------
@app.post("/save-session", response_model=SaveSessionResponse)
async def save_session(room_id: str = Query(...)):
    messages = STORE.get(room_id)
    if not messages:
        raise HTTPException(404, "Room not found")

    session_doc = {
        "session_id": room_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "messages": messages,
        "total_messages": len(messages),
        "latest_analysis": ANALYSIS_STORE.get(room_id),
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    result = sessions_collection.insert_one(session_doc)

    return SaveSessionResponse(ok=True, room_id=room_id, mongo_id=str(result.inserted_id), total_messages=len(messages))


# ----------------------------------------------------------
# END CALL — SAVE SUMMARY
# ----------------------------------------------------------
@app.post("/end-call")
async def end_call(room_id: str = Query(...), phone_number: Optional[str] = Query(None), userId: str = Query(...)):
    # avoid duplicates
    existing = call_summaries_collection.find_one({"room_id": room_id})
    if existing:
        return {
            "ok": True,
            "message": "Summary already exists.",
            "duration": existing.get("duration")
        }

    messages = STORE.get(room_id, [])
    if not messages:
        # try DB fallback with prefix match (handles room-xxx-user-yyy cases)
        try:
            messages = list(messages_collection.find({"room_id": {"$regex": f"^{room_id}"}}, {"_id": 0}).sort("sent_ts", 1))
        except Exception as e:
            logging.error(f"Failed to fetch messages from DB: {e}")
            messages = []

    if not messages:
        raise HTTPException(404, "No messages found")

    # compute duration
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

{transcript}

Return ONLY JSON:
{{
  "summary": "",
  "callPurpose": "",
  "userExperience": ""
}}
"""
        resp = genai_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        raw = (resp.text or "").strip().replace("```json", "").replace("```", "")
        summary_data = json.loads(raw)
    except Exception:
        summary_data = {"summary": "", "callPurpose": "", "userExperience": "Neutral"}

    # Lookup user for email / phone fallback
    user = users_collection.find_one({"_id": userId})

    # prefer phone_number passed into endpoint; fallback to saved user profile phone_number (if any)
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

    # cleanup memory
    STORE.pop(room_id, None)
    ANALYSIS_STORE.pop(room_id, None)

    return {
        "ok": True,
        "mongo_id": str(result.inserted_id),
        "duration": doc["duration"]
    }


# ----------------------------------------------------------
# RECENT CALLS - return global mixed list (newest first)
# ----------------------------------------------------------
@app.get("/recent-calls")
async def recent(limit: int = Query(20, ge=1, le=200)):
    """
    Return recent call summaries across all users (mixed).
    If you want to only return for a particular user, the frontend can filter,
    or we can add an optional userId query param to filter.
    """
    try:
        calls = list(call_summaries_collection.find({}, {"_id": 0}).sort("callDate", -1).limit(limit))
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


# ----------------------------------------------------------
# GET SINGLE CALL SUMMARY (FOR Summary.tsx)
# ----------------------------------------------------------
@app.get("/call-summary/{room_id}")
async def get_call_summary(room_id: str):
    summary = call_summaries_collection.find_one({"room_id": room_id}, {"_id": 0})
    if not summary:
        raise HTTPException(404, "Summary not found")
    return summary


# ----------------------------------------------------------
# HEALTH
# ----------------------------------------------------------
@app.get("/health")
async def health():
    try:
        client.admin.command("ping")
        mongodb_status = "connected"
    except Exception:
        mongodb_status = "disconnected"
    return {"status": "ok", "mongodb": mongodb_status}


# ----------------------------------------------------------
# START SERVER
# ----------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main1:app", host="127.0.0.1", port=8000, reload=True)
