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
| 1 | [Web Research](experiment_1/) | Managed Agents | Web research, SSE streaming, file download | `claude-haiku-4-5` |
| 2 | [Stock Analyst](experiment_2/) | Managed Agents | Custom tools, client-side execution, tool result round-trip | `claude-haiku-4-5` |
| 3 | [Data Analyst](experiment_3/) | Managed Agents | File upload, session resources, restricted networking, per-tool config | `claude-haiku-4-5` |
| 4 | [Advisor Tool](experiment_4/) | Messages API | Executor + advisor pairing, strategic guidance, cost comparison | `claude-haiku-4-5` + `claude-opus-4-6` |

### Run a single experiment

```bash
python experiment_1/run.py    # Web Research — agentic AI dashboard
python experiment_2/run.py    # Stock Analyst — custom tool round-trip
python experiment_3/run.py    # Data Analyst — file upload + restricted networking
python experiment_4/run.py    # Advisor Tool — Haiku executor + Opus advisor
```

### Run all experiments

```bash
# Run sequentially (each creates, runs, and tears down its own resources)
python experiment_1/run.py && \
python experiment_2/run.py && \
python experiment_3/run.py && \
python experiment_4/run.py
```

### What each experiment does

**Experiment 1 — Web Research** (Managed Agents)
The agent searches the web for the latest agentic AI developments and generates an HTML dashboard. Demonstrates basic managed agent lifecycle: create agent → create session → stream events → download output → teardown.

**Experiment 2 — Stock Analyst** (Managed Agents)
The agent uses **custom tools** (`get_stock_price`, `get_company_news`) that YOUR code executes locally. When the agent calls a custom tool, the session goes idle, your code runs the tool, sends the result back, and the agent resumes. Demonstrates the `agent.custom_tool_use` → `user.custom_tool_result` round-trip.

**Experiment 3 — Data Analyst** (Managed Agents)
You **upload a CSV file** via the Files API and mount it into the agent's container. The agent analyzes it using Python in a **restricted networking** environment (no internet). Web tools are **disabled per-tool config**. Demonstrates file resources and locked-down agents.

**Experiment 4 — Advisor Tool** (Messages API)
A fast **Haiku executor** consults a smarter **Opus advisor** mid-generation for strategic guidance — all within a single API request. Runs three sub-examples: single-turn architecture design, multi-turn iterative refinement, and a cost comparison with vs without advisor. Requires `advisor-tool-2026-03-01` beta access.

### Step-by-step mode (experiment 1 only)

Experiment 1 also has separate scripts if you want to keep the agent alive across multiple runs:

```bash
python experiment_1/setup.py     # Create agent + environment, save IDs to .env
python experiment_1/main.py      # Run a session (repeatable)
python experiment_1/cleanup.py   # Archive agent, delete environment
```

## Project Structure

```
├── .env                    # API key + experiment resource IDs (gitignored)
├── .gitignore
├── requirements.txt        # Shared Python dependencies
├── README.md               # This file
│
├── experiment_1/           # Web Research — Agentic AI Dashboard
│   ├── README.md
│   ├── run.py              # All-in-one: setup → run → teardown
│   ├── setup.py            # One-time setup (alternative)
│   ├── main.py             # Per-run (alternative)
│   └── cleanup.py          # Teardown (alternative)
│
├── experiment_2/           # Stock Analyst — Custom Tools
│   ├── README.md
│   └── run.py              # All-in-one: setup → run → teardown
│
├── experiment_3/           # Data Analyst — File Upload + Restricted Networking
│   ├── README.md
│   ├── sample_data.csv     # Input data (mounted into the container)
│   └── run.py              # All-in-one: setup → run → teardown
│
└── experiment_4/           # Advisor Tool — Executor + Advisor Strategy (Messages API)
    ├── README.md
    └── run.py              # Runs 3 examples: single-turn, multi-turn, cost comparison
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

Each experiment has its own `cleanup.py`. To tear down everything:

```bash
python experiment_1/cleanup.py
```

Experiments 2 and 3 use `run.py` which tears down automatically. Experiment 1's `run.py` also self-cleans.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `KeyError: 'EXP1_AGENT_ID'` | Run `python experiment_1/setup.py` first |
| `authentication_error` | Check that `ANTHROPIC_API_KEY` in `.env` is valid |
| No files downloaded | ~3s indexing lag after session goes idle. Scripts account for this. |
| `cannot delete while running` | Session is still active. Send an interrupt event first. |

## Further Reading

- [Managed Agents Overview](https://platform.claude.com/docs/en/managed-agents/overview)
- [Agent Setup](https://platform.claude.com/docs/en/managed-agents/agent-setup)
- [Sessions](https://platform.claude.com/docs/en/managed-agents/sessions)
- [Events and Streaming](https://platform.claude.com/docs/en/managed-agents/events-and-streaming)
- [Tools](https://platform.claude.com/docs/en/managed-agents/tools)
