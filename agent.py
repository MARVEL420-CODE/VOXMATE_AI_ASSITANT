"""
agent.py — fixed version
Runs DeepFace face authentication BEFORE LiveKit agent initialization.
"""



import os
import sys
import webbrowser
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation, google

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from tools import (
    get_weather,
    search_web,
    send_email,
    open_instagram,
    open_youtube,
)
from face_auth_deepface import authenticate_face_deepface

load_dotenv()


# ------------------------------------------------------------
# Assistant Definition
# ------------------------------------------------------------
class Assistant(Agent):
    """Defines the voxmate AI Assistant agent."""

    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                voice="Aoede",
                temperature=0.8,
            ),
            tools=[
                get_weather,
                search_web,
                send_email,
                open_youtube,
                open_instagram,
            ],
        )


# ------------------------------------------------------------
# LiveKit Entry Function
# ------------------------------------------------------------
async def entrypoint(ctx: agents.JobContext):
    """Start LiveKit AI Assistant after authentication."""
    print("🎧 Starting LiveKit voxmate Assistant...\n")

    session = AgentSession()
    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()
    await session.generate_reply(instructions=SESSION_INSTRUCTION)


# ------------------------------------------------------------
# Application Runner
# ------------------------------------------------------------
if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "console"
    print(f"🚀 Running voxmate Assistant in {mode.upper()} mode...\n")

    # Step 1: Face Authentication BEFORE LiveKit starts
    print("\n🔒 Starting Face Authentication...\n")
    ok = authenticate_face_deepface()
    if not ok:
        print("❌ Face Authentication Failed. Exiting...\n")
        sys.exit(1)

    print("✅ Face Authentication Successful! Launching LiveKit...\n")

    # Step 2: Open dashboard after auth success
    LIVEKIT_DASHBOARD_URL = os.getenv("LIVEKIT_DASHBOARD_URL", "http://localhost:3000")
    try:
        print(f"🌍 Opening LiveKit Dashboard: {LIVEKIT_DASHBOARD_URL}")
        webbrowser.open(LIVEKIT_DASHBOARD_URL)
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")

    # Step 3: Start LiveKit worker (only now camera initializes)
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)
    )
