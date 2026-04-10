"""Experiment 2 — Custom Tools: Stock Analyst Agent.

Demonstrates the custom tool round-trip:
  agent fires agent.custom_tool_use → your code executes → user.custom_tool_result → agent resumes.
"""

import json
import os
import time
import webbrowser
from datetime import datetime, timedelta

from dotenv import load_dotenv

import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


# ── Custom tool implementations (run on YOUR machine, not the container) ─────

def get_stock_price(ticker: str) -> dict:
    """Simulate fetching a stock price. Replace with a real API if desired."""
    prices = {
        "AAPL": {"price": 198.50, "change": +1.23, "change_pct": 0.62},
        "GOOGL": {"price": 178.30, "change": -0.87, "change_pct": -0.49},
        "MSFT": {"price": 425.10, "change": +3.45, "change_pct": 0.82},
        "NVDA": {"price": 135.20, "change": +5.67, "change_pct": 4.38},
        "AMZN": {"price": 195.80, "change": +2.10, "change_pct": 1.08},
        "META": {"price": 595.40, "change": -4.20, "change_pct": -0.70},
        "TSLA": {"price": 252.30, "change": +8.90, "change_pct": 3.66},
    }
    data = prices.get(ticker.upper())
    if data:
        return {"ticker": ticker.upper(), "currency": "USD", **data}
    return {"error": f"Unknown ticker: {ticker}"}


def get_company_news(ticker: str) -> dict:
    """Simulate fetching recent news headlines."""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    news = {
        "AAPL": [
            {"date": today, "headline": "Apple announces new AI features for iOS 20"},
            {"date": yesterday, "headline": "Apple supplier reports strong Q1 demand"},
        ],
        "GOOGL": [
            {"date": today, "headline": "Google DeepMind unveils next-gen reasoning model"},
            {"date": yesterday, "headline": "Alphabet cloud revenue beats estimates"},
        ],
        "MSFT": [
            {"date": today, "headline": "Microsoft expands Copilot agents across Office suite"},
            {"date": yesterday, "headline": "Azure AI services see 40% growth in enterprise adoption"},
        ],
        "NVDA": [
            {"date": today, "headline": "NVIDIA announces next-gen Blackwell Ultra GPU architecture"},
            {"date": yesterday, "headline": "NVIDIA data center revenue surges on AI demand"},
        ],
        "AMZN": [
            {"date": today, "headline": "Amazon launches new AI-powered logistics platform"},
            {"date": yesterday, "headline": "AWS unveils managed agent hosting service"},
        ],
        "META": [
            {"date": today, "headline": "Meta open-sources new Llama model with 1T parameters"},
            {"date": yesterday, "headline": "Meta Reality Labs posts first quarterly profit"},
        ],
        "TSLA": [
            {"date": today, "headline": "Tesla robotaxi service launches in Austin"},
            {"date": yesterday, "headline": "Tesla FSD v13 achieves new safety milestone"},
        ],
    }
    headlines = news.get(ticker.upper(), [])
    if headlines:
        return {"ticker": ticker.upper(), "headlines": headlines}
    return {"ticker": ticker.upper(), "headlines": [], "note": "No recent news found"}


def execute_custom_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch a custom tool call and return the JSON result."""
    if tool_name == "get_stock_price":
        result = get_stock_price(tool_input["ticker"])
    elif tool_name == "get_company_news":
        result = get_company_news(tool_input["ticker"])
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result)


# ── 1. Setup ─────────────────────────────────────────────────────────────────

print("=== Setting up agent and environment ===\n")

environment = client.beta.environments.create(
    name=f"stock-analyst-env-{int(time.time())}",
    config={
        "type": "cloud",
        "networking": {"type": "unrestricted"},
    },
)
print(f"Environment created: {environment.id}")

agent = client.beta.agents.create(
    name="Stock Analyst",
    model="claude-haiku-4-5",
    system=(
        "You are a stock market analyst agent. You have access to custom tools "
        "to fetch real-time stock prices and company news. Use these tools to "
        "gather data, then combine it with your own analysis to produce a single "
        "self-contained HTML dashboard with stock cards, price changes, news "
        "summaries, and your market outlook. Write the dashboard to "
        "/mnt/session/outputs/stock_dashboard.html."
    ),
    tools=[
        {"type": "agent_toolset_20260401", "default_config": {"enabled": True}},
        {
            "type": "custom",
            "name": "get_stock_price",
            "description": (
                "Get the current stock price for a given ticker symbol. "
                "Returns price, change, and change percentage in USD. "
                "Use this for real-time price data."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol, e.g. AAPL, GOOGL, MSFT",
                    }
                },
                "required": ["ticker"],
            },
        },
        {
            "type": "custom",
            "name": "get_company_news",
            "description": (
                "Get recent news headlines for a company by ticker symbol. "
                "Returns the latest headlines with dates. "
                "Use this to understand recent developments affecting the stock."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol, e.g. AAPL, GOOGL, MSFT",
                    }
                },
                "required": ["ticker"],
            },
        },
    ],
)
print(f"Agent created: {agent.id}")

# ── 2. Run session with custom tool handling ─────────────────────────────────

print("\n=== Starting session ===\n")

session = client.beta.sessions.create(
    agent=agent.id,
    environment_id=environment.id,
    title="Stock Market Analysis",
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
                            "Analyze these tech stocks: AAPL, GOOGL, MSFT, NVDA, AMZN, META, TSLA. "
                            "For each, get the current price and recent news. Then create a "
                            "comprehensive HTML dashboard with your analysis."
                        ),
                    }
                ],
            }
        ],
    )

    pending_tool_calls = []

    for event in stream:
        if event.type == "agent.message":
            for block in event.content:
                if block.type == "text":
                    print(block.text, end="", flush=True)

        elif event.type == "agent.custom_tool_use":
            print(f"\n  [Custom tool call: {event.tool_name}({json.dumps(event.input)})]")
            pending_tool_calls.append(event)

        elif event.type == "session.status_idle":
            if pending_tool_calls:
                # Execute all pending custom tools and send results back
                results = []
                for call in pending_tool_calls:
                    result = execute_custom_tool(call.tool_name, call.input)
                    print(f"  [Tool result for {call.tool_name}: {result[:80]}...]")
                    results.append({
                        "type": "user.custom_tool_result",
                        "custom_tool_use_id": call.id,
                        "content": [{"type": "text", "text": result}],
                    })

                client.beta.sessions.events.send(
                    session.id,
                    events=results,
                )
                pending_tool_calls = []
                print()
            elif event.stop_reason.type != "requires_action":
                break

        elif event.type == "session.status_terminated":
            break

print("\n\n=== Session complete ===\n")

# ── 3. Download outputs ──────────────────────────────────────────────────────

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

# ── 4. Teardown ──────────────────────────────────────────────────────────────

print("\n=== Tearing down ===\n")

client.beta.sessions.archive(session_id=session.id)
print(f"Session archived: {session.id}")

client.beta.agents.archive(agent_id=agent.id)
print(f"Agent archived: {agent.id}")

client.beta.environments.delete(environment_id=environment.id)
print(f"Environment deleted: {environment.id}")

if dashboard_path:
    print(f"\nOpening dashboard: {dashboard_path}")
    webbrowser.open(f"file://{dashboard_path}")

print("\nDone.")
