"""Experiment 4 — Advisor Tool: Haiku executor + Opus advisor.

Demonstrates the advisor strategy pattern:
  - A fast, cheap executor model (Haiku 4.5) handles the bulk of generation
  - A smarter advisor model (Opus 4.6) provides strategic guidance mid-generation
  - The executor decides WHEN to consult the advisor (like any other tool)
  - All happens in a single API request — no extra round trips

This uses the Messages API (not Managed Agents) with the advisor-tool beta.
"""

import json
import os

from dotenv import load_dotenv

import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ── Configuration ────────────────────────────────────────────────────────────

EXECUTOR_MODEL = "claude-haiku-4-5"      # fast, cheap — does the heavy lifting
ADVISOR_MODEL = "claude-opus-4-6"        # smart — provides strategic guidance

TOOLS = [
    {
        "type": "advisor_20260301",
        "name": "advisor",
        "model": ADVISOR_MODEL,
        "caching": {"type": "ephemeral", "ttl": "5m"},
    }
]

SYSTEM_PROMPT = """\
You are a senior software architect. You have access to an `advisor` tool \
backed by a stronger reviewer model. It takes NO parameters — when you call \
advisor(), your entire conversation history is automatically forwarded.

Call advisor BEFORE substantive work — before writing code, before committing \
to an architecture, before building on an assumption.

Also call advisor:
- When you believe the task is complete, to validate your solution.
- When stuck — errors recurring, approach not converging.
- When considering a change of approach.

The advisor should respond in under 100 words and use enumerated steps, not \
explanations.

Give the advice serious weight. If you follow a step and it fails empirically, \
adapt. If you have evidence that contradicts specific advice, surface the \
conflict in one more advisor call.
"""


# ── Helper functions ─────────────────────────────────────────────────────────

def print_response(response):
    """Print response content blocks with type labels."""
    for block in response.content:
        if block.type == "text":
            print(block.text)
        elif block.type == "server_tool_use" and block.name == "advisor":
            print("\n  [Consulting advisor (Opus 4.6)...]\n")
        elif block.type == "advisor_tool_result":
            content = block.content
            if content.type == "advisor_result":
                print(f"  [Advisor says: {content.text[:200]}...]" if len(content.text) > 200
                      else f"  [Advisor says: {content.text}]")
                print()
            elif content.type == "advisor_tool_result_error":
                print(f"  [Advisor error: {content.error_code}]")
                print()


def print_usage(response):
    """Print token usage breakdown by iteration."""
    usage = response.usage
    print(f"\n{'='*60}")
    print("TOKEN USAGE BREAKDOWN")
    print(f"{'='*60}")
    print(f"Top-level (executor totals):")
    print(f"  Input:  {usage.input_tokens}")
    print(f"  Output: {usage.output_tokens}")

    if hasattr(usage, "iterations") and usage.iterations:
        print(f"\nPer-iteration breakdown:")
        for i, iteration in enumerate(usage.iterations):
            model_label = "Executor" if iteration.type == "message" else "Advisor (Opus)"
            print(f"\n  Iteration {i+1} ({model_label}):")
            print(f"    Input:  {iteration.input_tokens}")
            print(f"    Output: {iteration.output_tokens}")
            if hasattr(iteration, "cache_read_input_tokens") and iteration.cache_read_input_tokens:
                print(f"    Cache read: {iteration.cache_read_input_tokens}")
    print(f"{'='*60}")


# ── Single-turn example ─────────────────────────────────────────────────────

print("=" * 60)
print("EXAMPLE 1: Single-turn — Architecture Design")
print("=" * 60)
print()

response = client.beta.messages.create(
    model=EXECUTOR_MODEL,
    max_tokens=4096,
    betas=["advisor-tool-2026-03-01"],
    system=SYSTEM_PROMPT,
    tools=TOOLS,
    messages=[
        {
            "role": "user",
            "content": (
                "Design a rate limiter for an API gateway that supports "
                "per-user and per-endpoint limits with sliding window counters. "
                "Provide a Python implementation."
            ),
        }
    ],
)

print_response(response)
print_usage(response)

# ── Multi-turn example ───────────────────────────────────────────────────────

print("\n\n")
print("=" * 60)
print("EXAMPLE 2: Multi-turn — Iterative Refinement")
print("=" * 60)
print()

messages = [
    {
        "role": "user",
        "content": (
            "Design a simple event sourcing system in Python. "
            "Include an event store, aggregate root, and event replay."
        ),
    }
]

# Turn 1: Initial design
print("--- Turn 1: Initial Design ---\n")
response = client.beta.messages.create(
    model=EXECUTOR_MODEL,
    max_tokens=4096,
    betas=["advisor-tool-2026-03-01"],
    system=SYSTEM_PROMPT,
    tools=TOOLS,
    messages=messages,
)
print_response(response)
print_usage(response)

# Preserve full response content (including advisor_tool_result blocks)
messages.append({"role": "assistant", "content": response.content})

# Turn 2: Follow-up refinement
print("\n\n--- Turn 2: Add Snapshotting ---\n")
messages.append({
    "role": "user",
    "content": "Now add snapshot support so we don't have to replay all events from the beginning.",
})

response = client.beta.messages.create(
    model=EXECUTOR_MODEL,
    max_tokens=4096,
    betas=["advisor-tool-2026-03-01"],
    system=SYSTEM_PROMPT,
    tools=TOOLS,
    messages=messages,
)
print_response(response)
print_usage(response)

# ── Comparison: with vs without advisor ──────────────────────────────────────

print("\n\n")
print("=" * 60)
print("EXAMPLE 3: Cost Comparison — With vs Without Advisor")
print("=" * 60)
print()

test_prompt = "Implement a thread-safe LRU cache in Python with TTL support."

# Without advisor
print("--- Without Advisor (Haiku only) ---\n")
response_no_advisor = client.beta.messages.create(
    model=EXECUTOR_MODEL,
    max_tokens=4096,
    betas=["advisor-tool-2026-03-01"],
    messages=[{"role": "user", "content": test_prompt}],
)
haiku_input = response_no_advisor.usage.input_tokens
haiku_output = response_no_advisor.usage.output_tokens
haiku_cost = (haiku_input * 1.0 + haiku_output * 5.0) / 1_000_000
print(f"  Input: {haiku_input}, Output: {haiku_output}")
print(f"  Estimated cost: ${haiku_cost:.6f}")

# With advisor
print("\n--- With Advisor (Haiku + Opus) ---\n")
response_with_advisor = client.beta.messages.create(
    model=EXECUTOR_MODEL,
    max_tokens=4096,
    betas=["advisor-tool-2026-03-01"],
    system=SYSTEM_PROMPT,
    tools=TOOLS,
    messages=[{"role": "user", "content": test_prompt}],
)

total_cost = 0.0
if hasattr(response_with_advisor.usage, "iterations") and response_with_advisor.usage.iterations:
    for iteration in response_with_advisor.usage.iterations:
        if iteration.type == "message":
            # Haiku rates: $1/1M input, $5/1M output
            cost = (iteration.input_tokens * 1.0 + iteration.output_tokens * 5.0) / 1_000_000
            total_cost += cost
        elif iteration.type == "advisor_message":
            # Opus rates: $5/1M input, $25/1M output
            cost = (iteration.input_tokens * 5.0 + iteration.output_tokens * 25.0) / 1_000_000
            total_cost += cost
            print(f"  Advisor call: input={iteration.input_tokens}, output={iteration.output_tokens}")
else:
    # Fallback if iterations not available
    total_cost = (response_with_advisor.usage.input_tokens * 1.0
                  + response_with_advisor.usage.output_tokens * 5.0) / 1_000_000

print(f"  Executor: input={response_with_advisor.usage.input_tokens}, output={response_with_advisor.usage.output_tokens}")
print(f"  Estimated total cost: ${total_cost:.6f}")
print(f"\n  Cost difference: ${total_cost - haiku_cost:+.6f}")
print(f"  (You pay more, but get Opus-level strategic guidance with Haiku-speed execution)")

print("\n\nDone.")
