"""Experiment 5 — LangChain Deep Agents: Open Alternative to Claude Managed Agents.

Demonstrates LangChain's Deep Agents — an open-source, model-agnostic agent harness
that provides similar capabilities to Claude Managed Agents:
  - Built-in tools (filesystem, shell, web search, planning)
  - Streaming support
  - Custom tools
  - Model agnostic (works with Claude, GPT, Gemini, etc.)

Ref: https://blog.langchain.com/deep-agents-deploy-an-open-alternative-to-claude-managed-agents/
"""

import os

from dotenv import load_dotenv

load_dotenv()


# ── Example 1: Basic Agent with Custom Tool ──────────────────────────────────

def run_basic_example():
    """Basic deep agent with a custom tool — comparable to Experiment 2's custom tools."""
    from deepagents import create_deep_agent

    print("=" * 60)
    print("EXAMPLE 1: Basic Agent with Custom Tool")
    print("=" * 60)
    print()

    def get_stock_price(ticker: str) -> str:
        """Get the current stock price for a given ticker symbol."""
        prices = {
            "AAPL": "198.50 (+0.62%)",
            "GOOGL": "178.30 (-0.49%)",
            "MSFT": "425.10 (+0.82%)",
            "NVDA": "135.20 (+4.38%)",
        }
        return prices.get(ticker.upper(), f"Unknown ticker: {ticker}")

    def get_company_news(ticker: str) -> str:
        """Get recent news headlines for a company by ticker symbol."""
        news = {
            "AAPL": "Apple announces new AI features for iOS 20",
            "GOOGL": "Google DeepMind unveils next-gen reasoning model",
            "MSFT": "Microsoft expands Copilot agents across Office suite",
            "NVDA": "NVIDIA announces next-gen Blackwell Ultra GPU architecture",
        }
        return news.get(ticker.upper(), f"No recent news for {ticker}")

    agent = create_deep_agent(
        model="anthropic:claude-haiku-4-5",
        tools=[get_stock_price, get_company_news],
        system_prompt=(
            "You are a stock market analyst. Use the available tools to fetch "
            "stock prices and news, then provide a brief market summary."
        ),
    )

    print("Sending: Analyze AAPL, GOOGL, MSFT, NVDA\n")

    result = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": (
                    "Get the current stock prices and latest news for "
                    "AAPL, GOOGL, MSFT, and NVDA. Give me a brief market summary."
                ),
            }
        ]
    })

    # Extract the final assistant message
    for msg in reversed(result["messages"]):
        if hasattr(msg, "content") and isinstance(msg.content, str) and msg.content:
            print(msg.content)
            break

    print()


# ── Example 2: Streaming Agent ───────────────────────────────────────────────

def run_streaming_example():
    """Deep agent with streaming output — comparable to Experiment 1's SSE streaming."""
    from deepagents import create_deep_agent

    print("=" * 60)
    print("EXAMPLE 2: Streaming Agent")
    print("=" * 60)
    print()

    agent = create_deep_agent(
        model="anthropic:claude-haiku-4-5",
        system_prompt=(
            "You are a research assistant. Provide concise, well-structured answers."
        ),
    )

    print("Streaming response for: What are the latest trends in agentic AI?\n")

    for chunk in agent.stream({
        "messages": [
            {
                "role": "user",
                "content": "What are the latest trends in agentic AI? Keep it under 200 words.",
            }
        ]
    }):
        # Stream chunks contain messages — print text deltas
        if "messages" in chunk:
            for msg in chunk["messages"]:
                if hasattr(msg, "content") and isinstance(msg.content, str):
                    print(msg.content, end="", flush=True)

    print("\n")


# ── Example 3: Agent with Built-in Tools ─────────────────────────────────────

def run_builtin_tools_example():
    """Deep agent using built-in filesystem and shell tools.

    Deep Agents come with batteries included:
      - write_todos: task planning and progress tracking
      - read_file, write_file, edit_file: filesystem operations
      - execute: shell command execution
      - ls, glob, grep: file search
      - task: delegate work to sub-agents
    """
    from deepagents import create_deep_agent

    print("=" * 60)
    print("EXAMPLE 3: Agent with Built-in Tools (Filesystem + Shell)")
    print("=" * 60)
    print()

    agent = create_deep_agent(
        model="anthropic:claude-haiku-4-5",
        system_prompt=(
            "You are a helpful coding assistant. Use the built-in tools to "
            "create files and run commands as needed."
        ),
    )

    print("Asking agent to create a Python script and run it...\n")

    result = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": (
                    "Create a Python script called /tmp/deep_agent_test.py that "
                    "calculates the first 10 Fibonacci numbers and prints them. "
                    "Then run it and show me the output."
                ),
            }
        ]
    })

    for msg in reversed(result["messages"]):
        if hasattr(msg, "content") and isinstance(msg.content, str) and msg.content:
            print(msg.content)
            break

    print()


# ── Example 4: Side-by-Side Comparison ───────────────────────────────────────

def run_comparison():
    """Compare Deep Agents vs Claude Managed Agents conceptually."""
    print("=" * 60)
    print("COMPARISON: Deep Agents vs Claude Managed Agents")
    print("=" * 60)
    print()
    print(f"{'Feature':<30} {'Claude Managed Agents':<25} {'LangChain Deep Agents':<25}")
    print(f"{'-'*30} {'-'*25} {'-'*25}")
    print(f"{'Open source':<30} {'No':<25} {'Yes (MIT)':<25}")
    print(f"{'Model agnostic':<30} {'No (Claude only)':<25} {'Yes (any LLM)':<25}")
    print(f"{'Hosting':<30} {'Anthropic managed':<25} {'Self-hosted / LangSmith':<25}")
    print(f"{'Container sandbox':<30} {'Per-session (managed)':<25} {'Optional (Daytona etc.)':<25}")
    print(f"{'Built-in tools':<30} {'bash, read, write, etc.':<25} {'bash, read, write, etc.':<25}")
    print(f"{'Custom tools':<30} {'Yes (client-side)':<25} {'Yes (Python functions)':<25}")
    print(f"{'MCP support':<30} {'Yes (server-side)':<25} {'Yes (HTTP/SSE only)':<25}")
    print(f"{'Streaming':<30} {'SSE events':<25} {'LangGraph streaming':<25}")
    print(f"{'Memory':<30} {'Anthropic-managed':<25} {'User-owned (open fmt)':<25}")
    print(f"{'Agent config':<30} {'API objects (versioned)':<25} {'AGENTS.md + TOML files':<25}")
    print(f"{'Deployment':<30} {'API call':<25} {'deepagents deploy':<25}")
    print(f"{'A2A protocol':<30} {'No':<25} {'Yes':<25}")
    print(f"{'Agent protocol':<30} {'No':<25} {'Yes':<25}")
    print()


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔬 Experiment 5 — LangChain Deep Agents\n")
    print("An open-source, model-agnostic alternative to Claude Managed Agents.")
    print("Ref: https://blog.langchain.com/deep-agents-deploy-an-open-alternative-to-claude-managed-agents/")
    print()

    # Always show the comparison table
    run_comparison()

    # Run the agent examples
    try:
        run_basic_example()
        run_streaming_example()
        run_builtin_tools_example()
    except ImportError as e:
        print(f"Import error: {e}")
        print("\nMake sure deepagents is installed:")
        print("  pip install deepagents")
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Deep Agents requires langchain and related dependencies.")
        print("Install with: pip install deepagents")

    print("Done.")
