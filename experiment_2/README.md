# Experiment 2 — Custom Tools: Stock Analyst Agent

Demonstrates the **custom tool round-trip** — the agent calls tools that YOUR code executes locally, not in the container.

## What's New (vs Experiment 1)

| Concept | Description |
|---------|-------------|
| **Custom tools** | Agent declares tools; your app handles execution |
| **`agent.custom_tool_use` event** | Fired when the agent wants to call your tool |
| **`user.custom_tool_result` event** | You send the result back to the agent |
| **Idle → tool result → running cycle** | The session goes idle waiting for your tool result, then resumes |

## How It Works

```
Agent: "I need the stock price for AAPL"
  → agent.custom_tool_use: get_stock_price({ticker: "AAPL"})
  → session goes idle (requires_action)

Your code: executes get_stock_price("AAPL") locally
  → user.custom_tool_result: {price: 198.50, change: +1.23, ...}
  → session resumes running

Agent: uses the result, calls more tools, builds the dashboard
```

## Agent Config

| Setting | Value |
|---------|-------|
| **Name** | Stock Analyst |
| **Model** | `claude-haiku-4-5` |
| **Tools** | Full prebuilt toolset + 2 custom tools |
| **Custom Tools** | `get_stock_price`, `get_company_news` |
| **Networking** | Unrestricted |
| **Output** | Stock market HTML dashboard |

## Custom Tools

| Tool | Input | Output |
|------|-------|--------|
| `get_stock_price` | `{ticker: "AAPL"}` | Price, change, change % |
| `get_company_news` | `{ticker: "AAPL"}` | Recent news headlines |

Both use simulated data. Replace with real API calls (e.g., Alpha Vantage, Yahoo Finance) for production use.

## Usage

```bash
python experiment_2/run.py
```
