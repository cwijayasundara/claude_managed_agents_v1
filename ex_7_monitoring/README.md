# Experiment 7 — Monitoring & Tracing (Managed Agent Observability + LangSmith)

Demonstrates how to build observability around Claude Managed Agent sessions by consuming span events, tool call events, and session lifecycle events — with LangSmith integration for trace visualization.

## What It Does

- Captures `span.model_request_start/end` events for per-inference latency tracking
- Traces all tool calls (agent, MCP, custom) with timing
- Records session lifecycle transitions (running → idle → terminated)
- Fetches cumulative token usage from the session object post-completion
- Estimates cost based on model pricing
- **Posts structured traces to LangSmith** (root chain → child LLM/tool runs)
- Falls back to local JSON trace when LangSmith is not configured

## Agent Config

| Setting | Value |
|---------|-------|
| **Name** | Monitored Research Agent |
| **Model** | `claude-haiku-4-5` |
| **Tools** | Full prebuilt toolset (`agent_toolset_20260401`) |
| **Networking** | Unrestricted |

## Setup

Add to your `.env`:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional — enables LangSmith tracing
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=claude-managed-agents   # defaults to this if omitted
```

Install:

```bash
pip install langsmith
```

## Usage

Run from the **project root**:

```bash
python ex_7_monitoring/run.py
```

## Output

1. **Real-time event log** — prints each span, tool call, and status change as it happens
2. **Summary report** — latency breakdown, token usage, cost estimate, tool call counts
3. **`session_trace.json`** — full structured trace for ingestion into external systems
4. **LangSmith trace** — viewable at https://smith.langchain.com (if configured)

## LangSmith Trace Structure

```
managed-agent-session (chain)
├── model-inference-1 (llm) — duration, token usage
├── agent.web_search (tool) — tool name, input
├── model-inference-2 (llm) — duration, token usage
├── agent.write (tool) — tool name, input
└── model-inference-3 (llm) — duration, token usage
```

## Key Events Used

| Event | Purpose |
|-------|---------|
| `span.model_request_start` | Start timing a model inference |
| `span.model_request_end` | End timing, capture token usage |
| `agent.tool_use` | Track built-in tool invocations |
| `agent.mcp_tool_use` | Track MCP tool invocations |
| `agent.custom_tool_use` | Track custom tool invocations |
| `session.status_*` | Lifecycle transitions |
| `session.error` | Error capture with retry status |
| `session.usage` (via retrieve) | Cumulative token counts |
