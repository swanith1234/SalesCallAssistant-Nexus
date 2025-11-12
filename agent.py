from dotenv import load_dotenv
import os
import asyncio
import logging
import httpx
import time

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, UserInputTranscribedEvent
from livekit.plugins import deepgram, silero, google

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv(".env")

# Assistant agent
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a sales person convice the customers please to sell an Educational courses on AI and Machine learning keep it in one setnece")
        self.fastapi_url = "http://localhost:8000"

    async def send_transcript_to_fastapi(self, text: str, room_id: str, speaker: str = "user"):
        """Send transcript (user or assistant) to FastAPI backend for processing"""
        try:
            payload = {
                "text": text,
                "speaker": speaker,
                "timestamp": time.time(),
                "room_id": room_id
            }
            print(f"Sending to FastAPI: {payload}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.fastapi_url}/process-transcription",
                    json=payload
                )
                if response.status_code == 200:
                    result = response.json()
                    print(f"FastAPI response: {result}")
                else:
                    print(f"FastAPI error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error sending to FastAPI: {e}")

    async def save_session(self, room_id: str):
        """Call FastAPI to save session when room disconnects"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.fastapi_url}/save-session",
                    params={"room_id": room_id}
                )
                print("Save session response:", response.json())
        except Exception as e:
            print("Error saving session:", e)

# Async handler for user transcripts
async def handle_transcript(event, session: AgentSession):
    text = event.get("user_transcript", "")
    language = event.get("language", "unknown")
    logging.info(f"[Transcript] {text} ({language})")
    if text:
        reply_text = await session.generate_reply(
            instructions=f"Respond naturally to the user: {text}"
        )
        logging.info(f"[Reply] {reply_text}")

# Async entrypoint
async def entrypoint(ctx: agents.JobContext):
    assistant = Assistant()

    # Prepare session first so we can still use events for logging/streaming
    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
            api_key=os.getenv("DEEPGRAM_API_KEY")
        ),
        tts=deepgram.TTS(
            model="aura-asteria-en",
            api_key=os.getenv("DEEPGRAM_API_KEY")
        ),
        llm=google.LLM(
            model="gemini-2.0-flash",
            api_key=os.getenv("GOOGLE_API_KEY")
        ),
        vad=silero.VAD.load(),
        turn_detection=None
    )

    room_name = ctx.room.name

    # Register a shutdown callback EARLY that runs on any termination path
    async def _on_shutdown():
        # Bound this to avoid stalling shutdown; default job shutdown budget is ~60s
        try:
            await asyncio.wait_for(assistant.save_session(room_name), timeout=12.0)
        except Exception as e:
            print("Shutdown save_session failed:", e)

    ctx.add_shutdown_callback(_on_shutdown)

    # Optional: event for visibility; saving is handled by shutdown callback
    @session.on("session_disconnected")
    def on_session_disconnected(event):
        print(f"Session disconnected for room={room_name}, scheduling save...")

    # Handle user speech (final transcript)
    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event: UserInputTranscribedEvent):
        if event.is_final:
            print(f"Final user transcript: {event.transcript}")
            asyncio.create_task(
                assistant.send_transcript_to_fastapi(event.transcript, room_name, speaker="user")
            )
        else:
            print(f"Interim transcript: {event.transcript}")

    # Handle agent (assistant) messages
    @session.on("conversation_item_added")
    def on_conversation_item_added(event):
        if hasattr(event.item, "role") and event.item.role == "assistant":
            print(f"Agent message: {event.item.text_content}")
            asyncio.create_task(
                assistant.send_transcript_to_fastapi(event.item.text_content, room_name, speaker="assistant")
            )

    # Start session and connect
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            noise_cancellation=None,
            close_on_disconnect=False
        ),
    )

    await ctx.connect()

    # Initial greeting
    await session.generate_reply(
        instructions="Hello! I am listening. How can I assist you today?"
    )

# Main entrypoint
if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
            ws_url=os.getenv("LIVEKIT_WS_URL"),
            # Optional: if your save is slow, extend the process shutdown budget
            # shutdown_process_timeout=90,
        )
    )
