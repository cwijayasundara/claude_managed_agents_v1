"""Cleanup — archive the agent and delete the environment."""

import os

from dotenv import load_dotenv

import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

agent_id = os.environ.get("EXP1_AGENT_ID")
environment_id = os.environ.get("EXP1_ENVIRONMENT_ID")

# 1. Archive the agent (no hard delete available for agents)
if agent_id:
    client.beta.agents.archive(agent_id=agent_id)
    print(f"Agent archived: {agent_id}")

# 2. Delete the environment
if environment_id:
    client.beta.environments.delete(environment_id=environment_id)
    print(f"Environment deleted: {environment_id}")

print("\nDone. You can remove EXP1_* keys from .env.")
