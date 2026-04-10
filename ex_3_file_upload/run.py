"""Experiment 3 — File Upload + Data Analysis (Restricted Networking).

Demonstrates:
  - Uploading files via the Files API and mounting them in a session
  - Restricted networking (no internet — agent works only with uploaded data)
  - Per-tool config (web_search and web_fetch disabled)
  - Downloading session output files
"""

import os
import time
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SCRIPT_DIR = Path(__file__).parent

# ── 1. Setup ─────────────────────────────────────────────────────────────────

print("=== Setting up agent and environment ===\n")

# Restricted networking — no internet access
environment = client.beta.environments.create(
    name=f"data-analyst-env-{int(time.time())}",
    config={
        "type": "cloud",
        "networking": {"type": "package_managers_and_custom", "allowed_hosts": []},
    },
)
print(f"Environment created: {environment.id}")

# Agent with web tools disabled — can only work with uploaded files
agent = client.beta.agents.create(
    name="Data Analyst",
    model="claude-haiku-4-5",
    system=(
        "You are a data analyst agent. You receive CSV data files mounted in "
        "/workspace/. Analyze the data using Python (pandas, matplotlib are "
        "available via pip). Produce a self-contained HTML report with summary "
        "statistics, trends, and insights. Include inline CSS for styling. "
        "Write the report to /mnt/session/outputs/analysis_report.html."
    ),
    tools=[
        {
            "type": "agent_toolset_20260401",
            "default_config": {"enabled": True},
            "configs": [
                {"name": "web_search", "enabled": False},
                {"name": "web_fetch", "enabled": False},
            ],
        },
    ],
)
print(f"Agent created: {agent.id}")

# ── 2. Upload file via Files API ─────────────────────────────────────────────

print("\n=== Uploading data file ===\n")

csv_path = SCRIPT_DIR / "sample_data.csv"
with open(csv_path, "rb") as f:
    uploaded_file = client.beta.files.upload(file=f)
print(f"File uploaded: {uploaded_file.id} ({uploaded_file.filename})")

# ── 3. Run session with mounted file ─────────────────────────────────────────

print("\n=== Starting session ===\n")

session = client.beta.sessions.create(
    agent=agent.id,
    environment_id=environment.id,
    title="Sales Data Analysis",
    resources=[
        {
            "type": "file",
            "file_id": uploaded_file.id,
            "mount_path": "/workspace/sales_data.csv",
        },
    ],
)
print(f"Session created: {session.id}")
print(f"File mounted at: /workspace/sales_data.csv\n")

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
                            "Analyze the sales data in /workspace/sales_data.csv. "
                            "The file contains monthly sales data by product and region. "
                            "Please:\n"
                            "1. Summarize total revenue, units sold, and profit by product and region\n"
                            "2. Identify trends over time (which products are growing/declining)\n"
                            "3. Calculate profit margins by product\n"
                            "4. Find the best and worst performing product-region combinations\n"
                            "5. Create a comprehensive HTML dashboard with your findings"
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

# ── 4. Download outputs ──────────────────────────────────────────────────────

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

# ── 5. Teardown ──────────────────────────────────────────────────────────────

print("\n=== Tearing down ===\n")

client.beta.sessions.archive(session_id=session.id)
print(f"Session archived: {session.id}")

# Clean up the uploaded file
client.beta.files.delete(uploaded_file.id)
print(f"Uploaded file deleted: {uploaded_file.id}")

client.beta.agents.archive(agent_id=agent.id)
print(f"Agent archived: {agent.id}")

client.beta.environments.delete(environment_id=environment.id)
print(f"Environment deleted: {environment.id}")

if dashboard_path:
    print(f"\nOpening report: {dashboard_path}")
    webbrowser.open(f"file://{dashboard_path}")

print("\nDone.")
