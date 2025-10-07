from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins import google
# from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv(".env")

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a user and sales person will try to convince you to buy some product.")

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        # llm=google.beta.realtime.RealtimeModel(
        #  voice="Aoede"
        # ),
         llm=google.LLM(
            model="gemini-2.0-flash",
        ),
        tts=deepgram.TTS(
            model="aura-asteria-en",
        ),
        vad=silero.VAD.load(),
        # turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # For telephony applications, use BVCTelephony instead for best results
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))