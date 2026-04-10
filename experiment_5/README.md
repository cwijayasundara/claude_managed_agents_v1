# Experiment 5 — LangChain Deep Agents: Open Alternative to Claude Managed Agents

Demonstrates [LangChain Deep Agents](https://blog.langchain.com/deep-agents-deploy-an-open-alternative-to-claude-managed-agents/) — an open-source, model-agnostic agent harness that provides similar capabilities to Claude Managed Agents.

## What's New (vs Experiments 1–4)

| Concept | Description |
|---------|-------------|
| **LangChain Deep Agents** | Open-source alternative to Claude Managed Agents |
| **Model agnostic** | Works with Claude, GPT, Gemini, or any LLM with tool calling |
| **`create_deep_agent()`** | Single function to create a fully-featured agent |
| **Built-in tools** | Filesystem, shell, planning, sub-agents — included by default |
| **Streaming via LangGraph** | Native streaming support through LangGraph's `.stream()` |

## How It Compares

| Feature | Claude Managed Agents | LangChain Deep Agents |
|---------|----------------------|----------------------|
| Open source | No | Yes (MIT) |
| Model agnostic | No (Claude only) | Yes (any LLM) |
| Hosting | Anthropic managed | Self-hosted / LangSmith |
| Container sandbox | Per-session (managed) | Optional (Daytona, etc.) |
| Built-in tools | bash, read, write, etc. | bash, read, write, etc. |
| Custom tools | Yes (client-side) | Yes (Python functions) |
| MCP support | Yes (server-side) | Yes (HTTP/SSE only) |
| Memory | Anthropic-managed | User-owned (open format) |
| Agent config | API objects (versioned) | AGENTS.md + TOML files |
| Deployment | API call | `deepagents deploy` |

## Examples in This Experiment

| # | Example | What It Shows |
|---|---------|---------------|
| 1 | Custom Tool Agent | Custom `get_stock_price` / `get_company_news` tools (cf. Experiment 2) |
| 2 | Streaming Agent | `.stream()` output (cf. Experiment 1's SSE streaming) |
| 3 | Built-in Tools | Filesystem + shell execution (cf. Experiment 3's bash tools) |
| 4 | Comparison Table | Side-by-side feature comparison |

## Installation

Deep Agents requires a separate install (not included in the shared `requirements.txt`):

```bash
pip install deepagents
```

## Usage

```bash
python experiment_5/run.py
```

## Configuration

Deep Agents uses `anthropic:claude-haiku-4-5` as the model in these examples. You can swap to any supported model:

```python
# Claude
agent = create_deep_agent(model="anthropic:claude-sonnet-4-6")

# OpenAI
agent = create_deep_agent(model="openai:gpt-4o")

# Google
agent = create_deep_agent(model="google:gemini-2.0-flash")
```

## CLI Deployment (Beyond This Experiment)

Deep Agents also supports CLI-based deployment for production:

```bash
deepagents init my-agent       # Scaffold a new project
deepagents dev --port 2024     # Local testing
deepagents deploy              # Deploy to LangSmith
```

This creates a horizontally scalable server with 30+ endpoints supporting MCP, A2A, Agent Protocol, human-in-the-loop, and memory.

## References

- [Blog post](https://blog.langchain.com/deep-agents-deploy-an-open-alternative-to-claude-managed-agents/)
- [GitHub](https://github.com/langchain-ai/deepagents)
- [Documentation](https://docs.langchain.com/oss/python/deepagents/overview)
