import os
import json
import logging
from datetime import datetime, timezone
from typing import Literal, List, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import uvicorn
from google import genai
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

# ✅ LiveKit
from livekit import api

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

client = MongoClient(MONGO_URI, connect=False)
db = client["sales_agent"]
messages_collection = db["messages"]
sessions_collection = db["transcripts"]

# ✅ SAFE INDEX CREATION
existing_msg_indexes = messages_collection.index_information()
if "room_ts_idx" not in existing_msg_indexes:
    messages_collection.create_index(
        [("room_id", ASCENDING), ("sent_ts", ASCENDING)],
        name="room_ts_idx"
    )

existing_session_indexes = sessions_collection.index_information()
if "session_ts_idx" not in existing_session_indexes:
    sessions_collection.create_index(
        [("session_id", ASCENDING), ("timestamp", ASCENDING)],
        name="session_ts_idx"
    )

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

# ✅ For LiveKit token API
class TokenRequest(BaseModel):
    room_name: str
    participant_name: str

# ✅ NEW: Response models for frontend
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
app = FastAPI(title="Sales Voice Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# GEMINI ANALYSIS FUNCTION
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

# -------------------------------------------------------------------
# ✅ LIVEKIT TOKEN ENDPOINT
# -------------------------------------------------------------------
@app.post("/get-token")
async def get_token(request: TokenRequest):
    try:
        token = api.AccessToken(
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET
        )

        token.with_identity(request.participant_name)
        token.with_name(request.participant_name)
        token.with_grants(
            api.VideoGrants(
                room_join=True,
                room=request.room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )

        jwt_token = token.to_jwt()

        return {
            "token": jwt_token,
            "url": LIVEKIT_WS_URL,
            "room": request.room_name,
        }

    except Exception as e:
        logging.exception("Token generation error")
        raise HTTPException(status_code=500, detail=str(e))

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
# ✅ NEW: GET LATEST ANALYSIS FOR A ROOM
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
# ✅ NEW: GET MESSAGES FOR A ROOM (WITH LIMIT)
# -------------------------------------------------------------------
@app.get("/messages/{room_id}")
async def get_messages(room_id: str, limit: int = Query(50, ge=1, le=500)):
    """Get recent messages for a room"""
    try:
        # First try in-memory store (most recent)
        messages = STORE.get(room_id, [])
        
        # If not enough in memory, query MongoDB
        if len(messages) < limit:
            try:
                mongo_messages = list(
                    messages_collection
                    .find({"room_id": room_id}, {"_id": 0})
                    .sort("sent_ts", DESCENDING)
                    .limit(limit)
                )
                # Merge and deduplicate
                all_messages = messages + mongo_messages
                # Sort by timestamp
                all_messages.sort(key=lambda x: x.get("sent_ts", 0))
                # Take most recent 'limit' messages
                messages = all_messages[-limit:] if len(all_messages) > limit else all_messages
            except PyMongoError as e:
                logging.error(f"MongoDB query error: {e}")
        
        return {
            "room_id": room_id,
            "messages": messages[-limit:]  # Return most recent
        }

    except Exception as e:
        logging.exception("Error fetching messages")
        raise HTTPException(500, str(e))

# -------------------------------------------------------------------
# SAVE SESSION → MONGODB
# -------------------------------------------------------------------
# @app.post("/save-session", response_model=SaveSessionResponse)
# async def save_session(room_id: str = Query(...)):
#     try:
#         if room_id not in STORE:
#             raise HTTPException(404, "Room not found")

#         messages = STORE[room_id]

#         session_doc = {
#             "session_id": room_id,
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#             "messages": messages,
#             "total_messages": len(messages),
#             "latest_analysis": ANALYSIS_STORE.get(room_id),
#         }

#         result = sessions_collection.insert_one(session_doc)
#         mongo_id = str(result.inserted_id)

#         logging.info(f"💾 Session {room_id} saved with {len(messages)} messages")

#         return SaveSessionResponse(
#             ok=True,
#             room_id=room_id,
#             mongo_id=mongo_id,
#             total_messages=len(messages),
#         )

#     except Exception as e:
#         logging.exception("Save error")
#         raise HTTPException(500, str(e))


@app.post("/save-session", response_model=SaveSessionResponse)
async def save_session(room_id: str = Query(...)):
    try:
        # First check in-memory store
        if room_id not in STORE:
            # If not in memory, check if already in MongoDB
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

        # Check if session already exists in MongoDB
        existing_session = sessions_collection.find_one({"session_id": room_id})
        
        if existing_session:
            # Update existing session
            sessions_collection.update_one(
                {"session_id": room_id},
                {
                    "$set": {
                        "messages": messages,
                        "total_messages": len(messages),
                        "latest_analysis": ANALYSIS_STORE.get(room_id),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                }
            )
            mongo_id = str(existing_session["_id"])
        else:
            # Create new session
            session_doc = {
                "session_id": room_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "messages": messages,
                "total_messages": len(messages),
                "latest_analysis": ANALYSIS_STORE.get(room_id),
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
# GET CONVERSATIONS (IN-MEMORY ONLY)
# -------------------------------------------------------------------
# @app.get("/conversations")
# async def get_conversations():
#     try:
#         return {
#             "sessions": [
#                 {"room_id": room_id, "count": len(messages)}
#                 for room_id, messages in STORE.items()
#             ]
#         }
#     except Exception as e:
#         raise HTTPException(500, str(e))



@app.get("/conversations")
async def get_conversations():
    try:
        # Get in-memory sessions
        in_memory = [
            {"room_id": room_id, "count": len(messages)}
            for room_id, messages in STORE.items()
        ]
        
        # Get saved sessions from MongoDB (LIMIT TO 50 MOST RECENT)
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
        
        # Combine and deduplicate
        all_sessions = {}
        for sess in in_memory + mongo_sessions:
            all_sessions[sess["room_id"]] = sess
        
        return {
            "sessions": list(all_sessions.values())
        }
    except Exception as e:
        raise HTTPException(500, str(e))
    

# -------------------------------------------------------------------
# GET STORED SESSION FROM MONGODB
# -------------------------------------------------------------------
# @app.get("/session/{session_id}")
# async def get_session(session_id: str):
#     try:
#         doc = sessions_collection.find_one({"session_id": session_id}, {"_id": 0})
#         if not doc:
#             raise HTTPException(404, "Session not found")
#         return doc
#     except Exception as e:
#         raise HTTPException(500, str(e))


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    try:
        # Try to find in MongoDB
        doc = sessions_collection.find_one({"session_id": session_id}, {"_id": 0})
        
        if not doc:
            # If not found, maybe it's still in memory
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
# HEALTH CHECK
# -------------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "healthy", "rooms": len(STORE)}



@app.get("/debug/sessions")
async def debug_sessions():
    """Debug endpoint to see all sessions"""
    try:
        sessions = list(sessions_collection.find({}, {"_id": 0}).limit(10))
        return {"count": len(sessions), "sessions": sessions}
    except Exception as e:
        return {"error": str(e)}

# -------------------------------------------------------------------
# MAIN ENTRY
# -------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)