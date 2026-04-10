"""All-in-one: setup → run session → teardown."""

import os
import time
import webbrowser

from dotenv import load_dotenv

import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ── 1. Setup ─────────────────────────────────────────────────────────────────

print("=== Setting up agent and environment ===\n")

environment = client.beta.environments.create(
    name=f"web-research-env-{int(time.time())}",
    config={
        "type": "cloud",
        "networking": {"type": "unrestricted"},
    },
)
print(f"Environment created: {environment.id}")

agent = client.beta.agents.create(
    name="Web Research",
    model="claude-haiku-4-5",
    system=(
        "You are a research agent. Search the web thoroughly for the latest updates "
        "in agentic AI, synthesize your findings, and produce a single self-contained "
        "HTML dashboard with clean styling and key insights."
    ),
    tools=[
        {"type": "agent_toolset_20260401", "default_config": {"enabled": True}},
    ],
)
print(f"Agent created: {agent.id}")

# ── 2. Run session ───────────────────────────────────────────────────────────

print("\n=== Starting session ===\n")

session = client.beta.sessions.create(
    agent=agent.id,
    environment_id=environment.id,
    title="Agentic AI Research",
)
print(f"Session created: {session.id}\n")

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

print("\n\n=== Session complete ===\n")

# Download output files
time.sleep(3)

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

# ── 3. Teardown ──────────────────────────────────────────────────────────────

print("\n=== Tearing down ===\n")

client.beta.sessions.archive(session_id=session.id)
print(f"Session archived: {session.id}")

client.beta.agents.archive(agent_id=agent.id)
print(f"Agent archived: {agent.id}")

client.beta.environments.delete(environment_id=environment.id)
print(f"Environment deleted: {environment.id}")

# Open the dashboard
if dashboard_path:
    print(f"\nOpening dashboard: {dashboard_path}")
    webbrowser.open(f"file://{dashboard_path}")

print("\nDone.")
