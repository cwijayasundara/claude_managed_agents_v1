# Claude Managed Agents — Experiments

A collection of experiments testing [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview), Anthropic's hosted agent service.

## What is Claude Managed Agents?

Anthropic runs the agent loop and provisions a sandboxed container per session. You supply the agent config (model, system prompt, tools) and environment config (networking, packages). Each run is a **session**.

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Agent** | Persisted, versioned config (model, system prompt, tools). Created once, reused across sessions. |
| **Environment** | Container template (networking, packages). Reusable across agents. |
| **Session** | A single agent run. References an agent + environment. Produces an event stream. |
| **Events** | Messages between your app and the agent (user messages, tool results, status updates). |

### Architecture

```
Your code
    │
    ├── sessions.create()              → provisions a container
    ├── sessions.events.stream()       → opens SSE event stream
    ├── sessions.events.send()         → sends the prompt
    │
    │   ┌──────────────────────────────────────────┐
    │   │  Anthropic orchestration layer            │
    │   │  Agent loop: Claude (model of choice)     │
    │   │  Tools: bash, read, write, web_search,    │
    │   │         web_fetch, edit, glob, grep        │
    │   └──────────────┬───────────────────────────┘
    │                  │ tool calls
    │                  ▼
    │          Container (sandbox)
    │          └── /mnt/session/outputs/ ← agent output files
    │
    ├── files.list() + files.download() → retrieves output files
    └── sessions.archive()              → cleans up the session
```

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/settings/keys)

## Getting Started

### 1. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

> All subsequent commands assume the virtual environment is active. Run `source .venv/bin/activate` in each new terminal session.

### 2. Create your `.env` file

```bash
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env
```

### 3. Run an experiment

Each experiment has a self-contained `run.py` that handles setup, execution, and teardown in one go. Just pick one and run it.

## Experiments

| # | Name | API Surface | Key Concepts | Model |
|---|------|-------------|-------------|-------|
| 1 | [Web Research](ex_1_web_research/) | Managed Agents | Web research, SSE streaming, file download | `claude-haiku-4-5` |
| 2 | [Stock Analyst](ex_2_custom_tools/) | Managed Agents | Custom tools, client-side execution, tool result round-trip | `claude-haiku-4-5` |
| 3 | [Data Analyst](ex_3_file_upload/) | Managed Agents | File upload, session resources, restricted networking, per-tool config | `claude-haiku-4-5` |
| 4 | [Advisor Tool](ex_4_advisor_native/) | Messages API | Executor + advisor pairing, strategic guidance, cost comparison | `claude-haiku-4-5` + `claude-opus-4-6` |
| 5 | [Deep Agents](ex_5_deep_agents/) | LangChain | Open-source alternative, model-agnostic, built-in tools, comparison | `anthropic:claude-haiku-4-5` |
| 6 | [Middleware Advisor](ex_6_advisor_middleware/) | LangChain | Advisor strategy via middleware, wrap_model_call, open-source advisor | `claude-haiku-4-5` + `claude-opus-4-6` |
| 7 | [Monitoring & Tracing](ex_7_monitoring/) | Managed Agents | Span events, tool tracing, usage tracking, LangSmith integration | `claude-haiku-4-5` |

### Run a single experiment

```bash
python ex_1_web_research/run.py    # Web Research — agentic AI dashboard
python ex_2_custom_tools/run.py    # Stock Analyst — custom tool round-trip
python ex_3_file_upload/run.py    # Data Analyst — file upload + restricted networking
python ex_4_advisor_native/run.py    # Advisor Tool — Haiku executor + Opus advisor
python ex_5_deep_agents/run.py    # Deep Agents — LangChain open-source alternative
python ex_6_advisor_middleware/run.py    # Middleware Advisor — LangChain advisor strategy
python ex_7_monitoring/run.py    # Monitoring — span events, tracing, LangSmith
```

### Run all experiments

```bash
# Run sequentially (each creates, runs, and tears down its own resources)
python ex_1_web_research/run.py && \
python ex_2_custom_tools/run.py && \
python ex_3_file_upload/run.py && \
python ex_4_advisor_native/run.py && \
python ex_5_deep_agents/run.py && \
python ex_6_advisor_middleware/run.py && \
python ex_7_monitoring/run.py
```

> **Note:** Experiments 5 and 6 require additional installs: `pip install deepagents langchain langchain-anthropic`. Experiment 7 requires `pip install langsmith`.

### What each experiment does

**Experiment 1 — Web Research** (Managed Agents)
The agent searches the web for the latest agentic AI developments and generates an HTML dashboard. Demonstrates basic managed agent lifecycle: create agent → create session → stream events → download output → teardown.

**Experiment 2 — Stock Analyst** (Managed Agents)
The agent uses **custom tools** (`get_stock_price`, `get_company_news`) that YOUR code executes locally. When the agent calls a custom tool, the session goes idle, your code runs the tool, sends the result back, and the agent resumes. Demonstrates the `agent.custom_tool_use` → `user.custom_tool_result` round-trip.

**Experiment 3 — Data Analyst** (Managed Agents)
You **upload a CSV file** via the Files API and mount it into the agent's container. The agent analyzes it using Python in a **restricted networking** environment (no internet). Web tools are **disabled per-tool config**. Demonstrates file resources and locked-down agents.

**Experiment 4 — Advisor Tool** (Messages API)
A fast **Haiku executor** consults a smarter **Opus advisor** mid-generation for strategic guidance — all within a single API request. Runs three sub-examples: single-turn architecture design, multi-turn iterative refinement, and a cost comparison with vs without advisor. Requires `advisor-tool-2026-03-01` beta access.

**Experiment 5 — Deep Agents** (LangChain)
[LangChain's open-source alternative](https://blog.langchain.com/deep-agents-deploy-an-open-alternative-to-claude-managed-agents/) to Claude Managed Agents. Model-agnostic, MIT-licensed, with built-in tools (filesystem, shell, planning, sub-agents). Runs custom tool, streaming, and built-in tool examples, plus a side-by-side comparison table. Requires `pip install deepagents`.

**Experiment 6 — Middleware Advisor** (LangChain)
Implements the **advisor strategy** (cf. Experiment 4) using LangChain v1's `wrap_model_call` middleware instead of Anthropic's native advisor tool. A custom `AdvisorMiddleware` intercepts model calls, consults Opus for strategic guidance, and injects the advice into the executor's system prompt. Open-source, model-agnostic, fully customizable timing. Requires `pip install langchain langchain-anthropic`.

**Experiment 7 — Monitoring & Tracing** (Managed Agents + LangSmith)
Builds an **observability layer** around a managed agent session. An `AgentMonitor` class consumes `span.model_request_start/end` events for per-inference latency, traces all tool calls, records lifecycle transitions, and fetches cumulative token usage. Integrates with **LangSmith** to post structured traces (root chain run → child LLM/tool runs) for visualization. Falls back to local JSON traces when LangSmith is not configured. Requires `pip install langsmith`.

## Project Structure

```
├── .env                    # API key + experiment resource IDs (gitignored)
├── .gitignore
├── requirements.txt        # Shared Python dependencies
├── README.md               # This file
│
├── ex_1_web_research/           # Web Research — Agentic AI Dashboard
│   ├── README.md
│   └── run.py              # All-in-one: setup → run → teardown
│
├── ex_2_custom_tools/           # Stock Analyst — Custom Tools
│   ├── README.md
│   └── run.py              # All-in-one: setup → run → teardown
│
├── ex_3_file_upload/           # Data Analyst — File Upload + Restricted Networking
│   ├── README.md
│   ├── sample_data.csv     # Input data (mounted into the container)
│   └── run.py              # All-in-one: setup → run → teardown
│
├── ex_4_advisor_native/           # Advisor Tool — Executor + Advisor Strategy (Messages API)
│   ├── README.md
│   └── run.py              # Runs 3 examples: single-turn, multi-turn, cost comparison
│
├── ex_5_deep_agents/           # Deep Agents — LangChain Open-Source Alternative
│   ├── README.md
│   └── run.py              # Custom tools, streaming, built-in tools, comparison
│
├── ex_6_advisor_middleware/           # Middleware Advisor — LangChain Advisor Strategy
│   ├── README.md
│   └── run.py              # wrap_model_call advisor, single-turn, multi-turn
│
└── ex_7_monitoring/           # Monitoring & Tracing — Observability + LangSmith
    ├── README.md
    └── run.py              # Span events, tool tracing, usage tracking, LangSmith
```

## Billing

Managed Agents bills through standard Claude API token pricing:

| Model | Input $/1M | Output $/1M |
|-------|-----------|------------|
| Claude Opus 4.6 | $5.00 | $25.00 |
| Claude Sonnet 4.6 | $3.00 | $15.00 |
| Claude Haiku 4.5 | $1.00 | $5.00 |

Prompt caching and context compaction are applied automatically to reduce costs.

## Cleanup

Each experiment's `run.py` handles teardown automatically (archives sessions/agents, deletes environments).

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `KeyError: 'ANTHROPIC_API_KEY'` | Ensure `.env` contains a valid API key |
| `authentication_error` | Check that `ANTHROPIC_API_KEY` in `.env` is valid |
| No files downloaded | ~3s indexing lag after session goes idle. Scripts account for this. |
| `cannot delete while running` | Session is still active. Send an interrupt event first. |

## Further Reading

- [Managed Agents Overview](https://platform.claude.com/docs/en/managed-agents/overview)
- [Agent Setup](https://platform.claude.com/docs/en/managed-agents/agent-setup)
- [Sessions](https://platform.claude.com/docs/en/managed-agents/sessions)
- [Events and Streaming](https://platform.claude.com/docs/en/managed-agents/events-and-streaming)
- [Tools](https://platform.claude.com/docs/en/managed-agents/tools)
