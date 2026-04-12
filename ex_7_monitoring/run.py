"""Experiment 7 — Monitoring & Tracing: Observability for Managed Agents.

Demonstrates how to build a monitoring/tracing layer around a managed agent session:
  - Captures span events (model_request_start/end) for latency tracking
  - Traces all tool calls with timing and input/output
  - Records session lifecycle events (running, idle, terminated)
  - Tracks cumulative token usage and cost
  - Integrates with LangSmith for trace visualization
  - Produces a JSON trace file and prints a summary report

Requires:
  pip install langsmith
  Set LANGSMITH_API_KEY and optionally LANGSMITH_PROJECT in .env
"""

import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

from dotenv import load_dotenv

import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ── LangSmith integration ─────────────────────────────────────────────────────

LANGSMITH_ENABLED = bool(os.environ.get("LANGSMITH_API_KEY"))

if LANGSMITH_ENABLED:
    from langsmith import Client as LangSmithClient
    from langsmith.run_trees import RunTree

    ls_client = LangSmithClient()
    LS_PROJECT = os.environ.get("LANGSMITH_PROJECT", "claude-managed-agents")
    print(f"LangSmith enabled — project: {LS_PROJECT}")
else:
    print("LangSmith disabled (set LANGSMITH_API_KEY to enable)")


# ── Trace data structures ──────────────────────────────────────────────────────

@dataclass
class SpanRecord:
    """A single model inference span."""
    started_at: str = ""
    ended_at: str = ""
    duration_ms: float = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0


@dataclass
class ToolCallRecord:
    """A single tool invocation."""
    tool_name: str = ""
    tool_type: str = ""  # agent, mcp, custom
    input: dict = field(default_factory=dict)
    output_preview: str = ""
    timestamp: str = ""


@dataclass
class SessionTrace:
    """Complete trace of a managed agent session."""
    session_id: str = ""
    agent_id: str = ""
    started_at: str = ""
    ended_at: str = ""
    total_duration_ms: float = 0
    status_transitions: list = field(default_factory=list)
    spans: list = field(default_factory=list)
    tool_calls: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    events_received: int = 0
    final_usage: dict = field(default_factory=dict)


# ── Cost calculation ───────────────────────────────────────────────────────────

PRICING = {
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},  # per 1M tokens
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-opus-4-6": {"input": 5.00, "output": 25.00},
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD."""
    prices = PRICING.get(model, PRICING["claude-haiku-4-5"])
    return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000


# ── Monitoring wrapper ─────────────────────────────────────────────────────────

class AgentMonitor:
    """Wraps SSE event consumption to produce a structured trace + LangSmith runs."""

    def __init__(self, session_id: str, agent_id: str, model: str):
        self.trace = SessionTrace(session_id=session_id, agent_id=agent_id)
        self.model = model
        self._current_span_start: float | None = None
        self._current_span_start_ts: str = ""
        self._start_time = time.time()
        self.trace.started_at = datetime.now(timezone.utc).isoformat()

        # LangSmith: create the root run for the entire session
        self._root_run: RunTree | None = None
        self._current_llm_run: RunTree | None = None
        if LANGSMITH_ENABLED:
            self._root_run = RunTree(
                name=f"managed-agent-session",
                run_type="chain",
                project_name=LS_PROJECT,
                inputs={"session_id": session_id, "agent_id": agent_id, "model": model},
            )

    def process_event(self, event) -> None:
        """Process a single SSE event and update the trace."""
        self.trace.events_received += 1

        match event.type:
            # ── Span events (model inference timing) ───────────────────
            case "span.model_request_start":
                self._current_span_start = time.time()
                self._current_span_start_ts = datetime.now(timezone.utc).isoformat()
                print(f"  [SPAN] Model request started")

                # LangSmith: start a child LLM run
                if LANGSMITH_ENABLED and self._root_run:
                    self._current_llm_run = self._root_run.create_child(
                        name=f"model-inference-{len(self.trace.spans) + 1}",
                        run_type="llm",
                        inputs={"model": self.model},
                    )

            case "span.model_request_end":
                span = SpanRecord(
                    started_at=self._current_span_start_ts,
                    ended_at=datetime.now(timezone.utc).isoformat(),
                )
                if self._current_span_start:
                    span.duration_ms = (time.time() - self._current_span_start) * 1000
                if hasattr(event, "model_usage") and event.model_usage:
                    span.input_tokens = getattr(event.model_usage, "input_tokens", 0)
                    span.output_tokens = getattr(event.model_usage, "output_tokens", 0)
                    span.cache_read_tokens = getattr(event.model_usage, "cache_read_input_tokens", 0)
                    span.cache_creation_tokens = getattr(event.model_usage, "cache_creation_input_tokens", 0)
                self.trace.spans.append(asdict(span))
                print(f"  [SPAN] Model request ended — {span.duration_ms:.0f}ms, "
                      f"{span.input_tokens} in / {span.output_tokens} out")
                self._current_span_start = None

                # LangSmith: end the LLM run with usage metadata
                if LANGSMITH_ENABLED and self._current_llm_run:
                    self._current_llm_run.end(
                        outputs={
                            "duration_ms": span.duration_ms,
                            "input_tokens": span.input_tokens,
                            "output_tokens": span.output_tokens,
                        },
                    )
                    self._current_llm_run.post()
                    self._current_llm_run = None

            # ── Tool call events ───────────────────────────────────────
            case "agent.tool_use":
                self._record_tool_call(event, "agent")

            case "agent.mcp_tool_use":
                self._record_tool_call(event, "mcp")

            case "agent.custom_tool_use":
                self._record_tool_call(event, "custom")

            # ── Session lifecycle events ───────────────────────────────
            case "session.status_running":
                self._record_status("running")

            case "session.status_idle":
                self._record_status("idle")

            case "session.status_rescheduled":
                self._record_status("rescheduled")
                print(f"  [WARN] Session rescheduled (transient error, retrying)")

            case "session.status_terminated":
                self._record_status("terminated")
                print(f"  [ERROR] Session terminated")

            # ── Error events ───────────────────────────────────────────
            case "session.error":
                error_info = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": getattr(event.error, "message", "unknown") if hasattr(event, "error") else "unknown",
                    "retry_status": getattr(event.error, "retry_status", None) if hasattr(event, "error") else None,
                }
                self.trace.errors.append(error_info)
                print(f"  [ERROR] {error_info['message']}")

    def _record_tool_call(self, event, tool_type: str) -> None:
        tool_name = getattr(event, "tool_name", "unknown")
        tool_input = getattr(event, "input", {})
        record = ToolCallRecord(
            tool_name=tool_name,
            tool_type=tool_type,
            input=tool_input,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.trace.tool_calls.append(asdict(record))
        print(f"  [TOOL] {tool_type}.{tool_name}")

        # LangSmith: log tool call as a child run
        if LANGSMITH_ENABLED and self._root_run:
            tool_run = self._root_run.create_child(
                name=f"{tool_type}.{tool_name}",
                run_type="tool",
                inputs={"tool_name": tool_name, "tool_input": tool_input},
            )
            tool_run.end(outputs={"status": "invoked"})
            tool_run.post()

    def _record_status(self, status: str) -> None:
        self.trace.status_transitions.append({
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_ms": (time.time() - self._start_time) * 1000,
        })

    def finalize(self, session) -> None:
        """Finalize the trace with session-level usage data."""
        self.trace.ended_at = datetime.now(timezone.utc).isoformat()
        self.trace.total_duration_ms = (time.time() - self._start_time) * 1000

        # Pull cumulative usage from the session object
        if hasattr(session, "usage") and session.usage:
            self.trace.final_usage = {
                "input_tokens": getattr(session.usage, "input_tokens", 0),
                "output_tokens": getattr(session.usage, "output_tokens", 0),
                "cache_read_input_tokens": getattr(session.usage, "cache_read_input_tokens", 0),
                "cache_creation_input_tokens": getattr(session.usage, "cache_creation_input_tokens", 0),
            }

        # LangSmith: end and post the root run
        if LANGSMITH_ENABLED and self._root_run:
            self._root_run.end(
                outputs={
                    "total_duration_ms": self.trace.total_duration_ms,
                    "events_received": self.trace.events_received,
                    "model_spans": len(self.trace.spans),
                    "tool_calls": len(self.trace.tool_calls),
                    "errors": len(self.trace.errors),
                    "usage": self.trace.final_usage,
                    "estimated_cost_usd": estimate_cost(
                        self.model,
                        self.trace.final_usage.get("input_tokens", 0),
                        self.trace.final_usage.get("output_tokens", 0),
                    ),
                },
            )
            self._root_run.post()
            print(f"\n  LangSmith trace posted to project: {LS_PROJECT}")

    def print_report(self) -> None:
        """Print a human-readable summary report."""
        print("\n" + "=" * 60)
        print("  SESSION TRACE REPORT")
        print("=" * 60)
        print(f"\n  Session ID:     {self.trace.session_id}")
        print(f"  Duration:       {self.trace.total_duration_ms / 1000:.1f}s")
        print(f"  Events:         {self.trace.events_received}")
        print(f"  Model Spans:    {len(self.trace.spans)}")
        print(f"  Tool Calls:     {len(self.trace.tool_calls)}")
        print(f"  Errors:         {len(self.trace.errors)}")

        # Latency breakdown
        if self.trace.spans:
            durations = [s["duration_ms"] for s in self.trace.spans]
            total_inference = sum(durations)
            print(f"\n  --- Latency ---")
            print(f"  Total inference time:  {total_inference:.0f}ms")
            print(f"  Avg per span:          {total_inference / len(durations):.0f}ms")
            print(f"  Min span:              {min(durations):.0f}ms")
            print(f"  Max span:              {max(durations):.0f}ms")

        # Token usage
        if self.trace.final_usage:
            u = self.trace.final_usage
            print(f"\n  --- Token Usage ---")
            print(f"  Input tokens:          {u['input_tokens']:,}")
            print(f"  Output tokens:         {u['output_tokens']:,}")
            print(f"  Cache read:            {u['cache_read_input_tokens']:,}")
            print(f"  Cache creation:        {u['cache_creation_input_tokens']:,}")
            cost = estimate_cost(self.model, u["input_tokens"], u["output_tokens"])
            print(f"  Estimated cost:        ${cost:.4f}")

        # Tool call breakdown
        if self.trace.tool_calls:
            print(f"\n  --- Tool Calls ---")
            tool_counts: dict[str, int] = {}
            for tc in self.trace.tool_calls:
                key = f"{tc['tool_type']}.{tc['tool_name']}"
                tool_counts[key] = tool_counts.get(key, 0) + 1
            for tool, count in sorted(tool_counts.items(), key=lambda x: -x[1]):
                print(f"  {tool}: {count}x")

        # Status transitions
        if self.trace.status_transitions:
            print(f"\n  --- Lifecycle ---")
            for t in self.trace.status_transitions:
                print(f"  [{t['elapsed_ms']:>8.0f}ms] → {t['status']}")

        print("\n" + "=" * 60)

    def save_trace(self, path: str) -> None:
        """Save the full trace as JSON."""
        with open(path, "w") as f:
            json.dump(asdict(self.trace), f, indent=2)
        print(f"\n  Trace saved to: {path}")


# ── 1. Setup ─────────────────────────────────────────────────────────────────

MODEL = "claude-haiku-4-5"

print("\n=== Setting up agent and environment ===\n")

environment = client.beta.environments.create(
    name=f"monitoring-env-{int(time.time())}",
    config={
        "type": "cloud",
        "networking": {"type": "unrestricted"},
    },
)
print(f"Environment created: {environment.id}")

agent = client.beta.agents.create(
    name="Monitored Research Agent",
    model=MODEL,
    system=(
        "You are a research agent. Search the web for the latest news about "
        "Claude and Anthropic, then write a brief 3-paragraph summary to "
        "/mnt/session/outputs/summary.txt. Be concise."
    ),
    tools=[
        {"type": "agent_toolset_20260401", "default_config": {"enabled": True}},
    ],
)
print(f"Agent created: {agent.id}")

# ── 2. Run session with monitoring ────────────────────────────────────────────

print("\n=== Starting monitored session ===\n")

session = client.beta.sessions.create(
    agent=agent.id,
    environment_id=environment.id,
    title="Monitored Research Session",
)
print(f"Session created: {session.id}\n")
print("-" * 60)
print("  EVENT LOG")
print("-" * 60)

monitor = AgentMonitor(session_id=session.id, agent_id=agent.id, model=MODEL)

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
                            "Research the latest news about Claude and Anthropic "
                            "from the past week. Write a brief summary."
                        ),
                    }
                ],
            }
        ],
    )

    for event in stream:
        # Feed every event to the monitor
        monitor.process_event(event)

        # Still handle the agent loop
        if event.type == "session.status_idle":
            if event.stop_reason.type != "requires_action":
                break
        elif event.type == "session.status_terminated":
            break

print("-" * 60)

# ── 3. Finalize trace with session usage ──────────────────────────────────────

time.sleep(2)

# Re-fetch session to get cumulative usage
final_session = client.beta.sessions.retrieve(session.id)
monitor.finalize(final_session)
monitor.print_report()

# Save trace to file
trace_path = os.path.abspath("session_trace.json")
monitor.save_trace(trace_path)

# ── 4. Teardown ──────────────────────────────────────────────────────────────

print("\n=== Tearing down ===\n")

client.beta.sessions.archive(session_id=session.id)
print(f"Session archived: {session.id}")

client.beta.agents.archive(agent_id=agent.id)
print(f"Agent archived: {agent.id}")

client.beta.environments.delete(environment_id=environment.id)
print(f"Environment deleted: {environment.id}")

print("\nDone.")
