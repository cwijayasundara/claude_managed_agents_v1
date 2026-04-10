"""ONE-TIME SETUP — run once, save the IDs to .env"""

import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# 1. Create the environment
environment = client.beta.environments.create(
    name="web-research-env",
    config={
        "type": "cloud",
        "networking": {"type": "unrestricted"},
    },
)

# 2. Create the agent
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

# Append IDs to .env (preserves existing keys like ANTHROPIC_API_KEY)
with open(".env", "a") as f:
    f.write(f"\n# Experiment 1 — Web Research\n")
    f.write(f"EXP1_AGENT_ID={agent.id}\n")
    f.write(f"EXP1_AGENT_VERSION={agent.version}\n")
    f.write(f"EXP1_ENVIRONMENT_ID={environment.id}\n")

print(f"EXP1_AGENT_ID={agent.id}")
print(f"EXP1_AGENT_VERSION={agent.version}")
print(f"EXP1_ENVIRONMENT_ID={environment.id}")
print("\nSaved to .env — you can now run ex_1_web_research/main.py")
