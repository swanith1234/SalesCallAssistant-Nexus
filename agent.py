# # agent.py - FINAL SINGLE /end-call CALL VERSION
# import os
# import asyncio
# import logging
# import httpx
# import time
# from dotenv import load_dotenv
# from livekit import agents, rtc
# from livekit.agents import AgentSession, Agent, RoomInputOptions, UserInputTranscribedEvent
# from livekit.plugins import deepgram, silero, google

# load_dotenv()

# BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
# USER_ID_FALLBACK = os.getenv("USER_ID")

# logging.basicConfig(level=logging.INFO)

# class Assistant(Agent):
#     def __init__(self, userId):
#         super().__init__(instructions="You are a sales person. Convince customers to buy AI/ML courses.")
#         self.fastapi_url = BACKEND_URL
#         self.userId = userId

#     async def send_transcript(self, text, room_id, speaker="user"):
#         try:
#             async with httpx.AsyncClient(timeout=20) as client:
#                 await client.post(
#                     f"{self.fastapi_url}/process-transcription",
#                     json={
#                         "text": text,
#                         "speaker": speaker,
#                         "timestamp": time.time(),
#                         "room_id": room_id,
#                     }
#                 )
#         except Exception as e:
#             print("Transcript error:", e)

#     async def finalize(self, room_id):
#         """Save session + generate summary ONCE only"""
#         try:
#             async with httpx.AsyncClient(timeout=20) as client:
#                 await client.post(
#                     f"{self.fastapi_url}/save-session",
#                     params={"room_id": room_id}
#                 )
#         except Exception as e:
#             print("Save session error:", e)

#         await asyncio.sleep(2)

#         try:
#             async with httpx.AsyncClient(timeout=30) as client:
#                 await client.post(
#                     f"{self.fastapi_url}/end-call",
#                     params={
#                         "room_id": room_id,
#                         "phone_number": "9999999999",
#                         "userId": self.userId,
#                     }
#                 )
#         except Exception as e:
#             print("End-call error:", e)


# async def entrypoint(ctx: agents.JobContext):
#     room = ctx.room
#     room_name = room.name or ""

#     # Extract userId from room name
#     userId = None
#     if "-user-" in room_name:
#         userId = room_name.split("-user-")[-1]

#     userId = userId or USER_ID_FALLBACK or "anonymous-user"

#     assistant = Assistant(userId)

#     finalized = False

#     async def try_finalize():
#         nonlocal finalized
#         if finalized:
#             return
#         finalized = True
#         print("🔥 FINALIZE CALLED ONCE ONLY")
#         await assistant.finalize(room_name)

#     @room.on("participant_disconnected")
#     def on_disconnect(participant: rtc.RemoteParticipant):
#         if participant.identity != "agent":
#             asyncio.create_task(try_finalize())

#     session = AgentSession(
#         stt=deepgram.STT(
#             model="nova-3",
#             language="multi",
#             api_key=os.getenv("DEEPGRAM_API_KEY"),
#         ),
#         tts=deepgram.TTS(
#             model="aura-asteria-en",
#             api_key=os.getenv("DEEPGRAM_API_KEY"),
#         ),
#         llm=google.LLM(
#             model="gemini-2.5-flash",
#             api_key=os.getenv("GOOGLE_API_KEY"),
#         ),
#         vad=silero.VAD.load(),
#         turn_detection=None,
#     )

#     @session.on("user_input_transcribed")
#     def on_user_text(event: UserInputTranscribedEvent):
#         if event.is_final:
#             asyncio.create_task(assistant.send_transcript(event.transcript, room_name, "user"))

#     @session.on("conversation_item_added")
#     def on_ai(item):
#         if getattr(item.item, "role", "") == "assistant":
#             asyncio.create_task(assistant.send_transcript(item.item.text_content, room_name, "assistant"))

#     await session.start(room=room, agent=assistant, room_input_options=RoomInputOptions(close_on_disconnect=True))
#     await ctx.connect()


# if __name__ == "__main__":
#     logging.info("Starting agent worker…")
#     agents.cli.run_app(
#         agents.WorkerOptions(
#             entrypoint_fnc=entrypoint,
#             api_key=os.getenv("LIVEKIT_API_KEY"),
#             api_secret=os.getenv("LIVEKIT_API_SECRET"),
#             ws_url=os.getenv("LIVEKIT_WS_URL"),
#         )
#     )


#-----Groq----
# agent.py - FINAL SINGLE /end-call CALL VERSION (with Groq via OpenAI-compatible API)
import os
import asyncio
import logging
import httpx
import time
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentSession, Agent, RoomInputOptions, UserInputTranscribedEvent
from livekit.plugins import deepgram, silero, openai

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
USER_ID_FALLBACK = os.getenv("USER_ID")

logging.basicConfig(level=logging.INFO)

class Assistant(Agent):
    def __init__(self, userId):
        super().__init__(instructions="You are a sales person. Convince customers to buy AI/ML courses.")
        self.fastapi_url = BACKEND_URL
        self.userId = userId

    async def send_transcript(self, text, room_id, speaker="user"):
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                await client.post(
                    f"{self.fastapi_url}/process-transcription",
                    json={
                        "text": text,
                        "speaker": speaker,
                        "timestamp": time.time(),
                        "room_id": room_id,
                    }
                )
        except Exception as e:
            print("Transcript error:", e)

    async def finalize(self, room_id):
        """Save session + generate summary ONCE only"""
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                await client.post(
                    f"{self.fastapi_url}/save-session",
                    params={"room_id": room_id}
                )
        except Exception as e:
            print("Save session error:", e)

        await asyncio.sleep(2)

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                await client.post(
                    f"{self.fastapi_url}/end-call",
                    params={
                        "room_id": room_id,
                        "phone_number": "9999999999",
                        "userId": self.userId,
                    }
                )
        except Exception as e:
            print("End-call error:", e)


async def entrypoint(ctx: agents.JobContext):
    room = ctx.room
    room_name = room.name or ""

    # Extract userId from room name
    userId = None
    if "-user-" in room_name:
        userId = room_name.split("-user-")[-1]

    userId = userId or USER_ID_FALLBACK or "anonymous-user"

    assistant = Assistant(userId)

    finalized = False

    async def try_finalize():
        nonlocal finalized
        if finalized:
            return
        finalized = True
        print("🔥 FINALIZE CALLED ONCE ONLY")
        await assistant.finalize(room_name)

    @room.on("participant_disconnected")
    def on_disconnect(participant: rtc.RemoteParticipant):
        if participant.identity != "agent":
            asyncio.create_task(try_finalize())

    # Use OpenAI plugin with Groq's API endpoint
    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
            api_key=os.getenv("DEEPGRAM_API_KEY"),
        ),
        tts=deepgram.TTS(
            model="aura-asteria-en",
            api_key=os.getenv("DEEPGRAM_API_KEY"),
        ),
        llm=openai.LLM(
            model="llama-3.3-70b-versatile",  # Groq model name
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",  # Groq's OpenAI-compatible endpoint
        ),
        vad=silero.VAD.load(),
        turn_detection=None,
    )

    @session.on("user_input_transcribed")
    def on_user_text(event: UserInputTranscribedEvent):
        if event.is_final:
            asyncio.create_task(assistant.send_transcript(event.transcript, room_name, "user"))

    @session.on("conversation_item_added")
    def on_ai(item):
        if getattr(item.item, "role", "") == "assistant":
            asyncio.create_task(assistant.send_transcript(item.item.text_content, room_name, "assistant"))

    await session.start(room=room, agent=assistant, room_input_options=RoomInputOptions(close_on_disconnect=True))
    await ctx.connect()


if __name__ == "__main__":
    logging.info("Starting agent worker…")
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
            ws_url=os.getenv("LIVEKIT_WS_URL"),
        )
    )