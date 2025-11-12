import os
import json
import logging
from datetime import datetime, timezone
from typing import Literal, List, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import uvicorn
from google import genai
from livekit import api  # ADD THIS IMPORT

# -------------------------------------------------------------------
# SETUP
# -------------------------------------------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# ADD THESE
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_WS_URL = os.getenv("LIVEKIT_WS_URL", "ws://localhost:7880")

if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
    raise ValueError("LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set")

# Gemini client
genai_client = genai.Client(api_key=GOOGLE_API_KEY)

# In-memory temporary store
STORE: Dict[str, List[dict]] = {}
ANALYSIS_STORE: Dict[str, dict] = {}

# -------------------------------------------------------------------
# MODELS
# -------------------------------------------------------------------
class TranscriptIn(BaseModel):
    text: str = Field(..., min_length=1)
    speaker: Literal["user", "assistant"]
    timestamp: float = Field(..., description="Unix timestamp from sender")
    room_id: str = Field(..., min_length=1)

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

# ADD THIS MODEL
class TokenRequest(BaseModel):
    room_name: str
    participant_name: str

# -------------------------------------------------------------------
# APP
# -------------------------------------------------------------------
app = FastAPI(title="Sales Voice Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# GEMINI ANALYSIS
# -------------------------------------------------------------------
def analyze_with_gemini(user_text: str) -> dict:
    """Perform sentiment and recommendation analysis using Gemini."""
    prompt = f"""
You are an analysis system. Analyze this customer's message related to purchasing an education course:
"{user_text}"

Return only JSON with these exact fields:
{{
  "sentiment": "positive" | "neutral" | "negative",
  "confidence": 0..1,
  "key_points": ["point 1", "point 2", "point 3"],
  "recommendation_to_salesperson": "Short next-step suggestion (max 2 sentences)"
}}
"""
    try:
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        raw = (resp.text or "").strip()
        # Clean possible code fences
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)
        return {
            "sentiment": str(parsed.get("sentiment", "neutral")).lower(),
            "confidence": float(parsed.get("confidence", 0.0)),
            "key_points": parsed.get("key_points", []),
            "recommendation_to_salesperson": parsed.get(
                "recommendation_to_salesperson",
                "Continue the conversation naturally."
            ),
        }

    except json.JSONDecodeError as e:
        logging.error(f"Gemini JSON parsing error: {e}")
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "key_points": [],
            "recommendation_to_salesperson": "Unable to process analysis.",
        }
    except Exception as e:
        logging.exception(f"Gemini error: {e}")
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "key_points": [],
            "recommendation_to_salesperson": "No analysis available.",
        }

# -------------------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------------------

# ADD THIS NEW ENDPOINT FOR TOKEN GENERATION
@app.post("/get-token")
async def get_token(request: TokenRequest):
    """Generate LiveKit access token for client"""
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
        
        logging.info(f"Generated token for {request.participant_name} in room {request.room_name}")
        
        return {
            "token": jwt_token,
            "url": LIVEKIT_WS_URL,
            "room": request.room_name
        }
    except Exception as e:
        logging.exception(f"Token generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-transcription", response_model=TranscriptResponse)
async def process_transcription(payload: TranscriptIn):
    """Store each transcript in memory, analyze user messages, and return results."""
    try:
        text_clean = payload.text.strip()

        # Store in memory
        record = {
            "text": text_clean,
            "speaker": payload.speaker,
            "sent_ts": payload.timestamp,
            "received_at": datetime.now(timezone.utc).isoformat(),
            "room_id": payload.room_id,
        }
        STORE.setdefault(payload.room_id, []).append(record)
        print(record)
        logging.info(f"Stored transcript from {payload.speaker} in room {payload.room_id}")

        analysis_obj = None
        latest_user_message = None

        # Analyze only user messages
        if payload.speaker == "user" and text_clean:
            latest_user_message = text_clean
            logging.info(f"Analyzing user message: {latest_user_message}")

            analysis_dict = analyze_with_gemini(text_clean)
            ANALYSIS_STORE[payload.room_id] = analysis_dict
            analysis_obj = SentimentAnalysis(**analysis_dict)

            logging.info(
                f"Analysis complete - Sentiment: {analysis_obj.sentiment}, "
                f"Confidence: {analysis_obj.confidence}"
            )

        count_in_room = len(STORE[payload.room_id])

        return TranscriptResponse(
            ok=True,
            room_id=payload.room_id,
            count_in_room=count_in_room,
            analysis=analysis_obj,
            latest_user_message=latest_user_message,
        )

    except Exception as e:
        logging.exception("Processing error")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------
# SAVE SESSION
# -------------------------------------------------------------------
@app.post("/save-session")
async def save_session(room_id: str):
    """Save entire in-memory session to file (sessions.json)."""
    try:
        if room_id not in STORE:
            raise HTTPException(status_code=404, detail="Room not found")

        messages = STORE[room_id]
        session_doc = {
            "session_id": room_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "messages": messages,
            "total_messages": len(messages),
        }

        # Append to local file (acts as lightweight persistence)
        with open("sessions.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(session_doc) + "\n")

        logging.info(f"💾 Saved session {room_id} locally ({len(messages)} messages)")

        return {"ok": True, "room_id": room_id}

    except Exception as e:
        logging.exception(f"Error saving session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------
# FETCH CONVERSATIONS
# -------------------------------------------------------------------
@app.get("/conversations")
async def get_conversations():
    """Fetch recent saved conversations from memory."""
    try:
        sessions = [
            {"room_id": room_id, "count": len(messages)}
            for room_id, messages in STORE.items()
        ]
        return {"sessions": sessions}
    except Exception as e:
        logging.exception(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "healthy", "memory_rooms": len(STORE)}

# -------------------------------------------------------------------
# MAIN ENTRY
# -------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)