"""RUNTIME — run on every invocation to kick off a research session."""

import os
import time
import webbrowser

from dotenv import load_dotenv

import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

AGENT_ID = os.environ["EXP1_AGENT_ID"]
ENVIRONMENT_ID = os.environ["EXP1_ENVIRONMENT_ID"]

# 1. Create a session
session = client.beta.sessions.create(
    agent=AGENT_ID,
    environment_id=ENVIRONMENT_ID,
    title="Agentic AI Research",
)
print(f"Session created: {session.id}\n")

# 2. Open stream FIRST, then send the kickoff message
with client.beta.sessions.events.stream(session.id) as stream:
    client.beta.sessions.events.send(
        session.id,
        events=[
            {
                "type": "user.message",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Research the latest developments in agentic AI from the "
                            "past week and create a dashboard."
                        ),
                    }
                ],
            }
        ],
    )

    for event in stream:
        if event.type == "agent.message":
            for block in event.content:
                if block.type == "text":
                    print(block.text, end="", flush=True)
        elif event.type == "session.status_idle":
            if event.stop_reason.type != "requires_action":
                break
        elif event.type == "session.status_terminated":
            break

print("\n\n--- Session complete ---")

# 3. Download output files (the HTML dashboard)
time.sleep(3)  # brief indexing lag before files appear

files = client.beta.files.list(
    scope_id=session.id,
    betas=["managed-agents-2026-04-01"],
)
dashboard_path = None
for f in files.data:
    print(f"Downloading: {f.filename}")
    content = client.beta.files.download(f.id)
    content.write_to_file(f.filename)
    if f.filename.endswith(".html"):
        dashboard_path = os.path.abspath(f.filename)

# 4. Clean up
client.beta.sessions.archive(session_id=session.id)
print("Session archived.")

# 5. Open the dashboard in the browser
if dashboard_path:
    print(f"\nOpening dashboard: {dashboard_path}")
    webbrowser.open(f"file://{dashboard_path}")
