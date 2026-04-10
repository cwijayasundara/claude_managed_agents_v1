# Experiment 4 — Advisor Tool: Strategic Guidance Pattern

Demonstrates the **advisor tool** — a fast executor model consults a smarter advisor model mid-generation for strategic guidance, all within a single API request.

## What's New (vs Experiments 1–3)

| Concept | Description |
|---------|-------------|
| **Advisor tool** | Server-side tool where the executor consults a stronger model |
| **Executor + Advisor pairing** | Haiku 4.5 (fast/cheap) + Opus 4.6 (smart) |
| **Messages API (not Managed Agents)** | Uses `client.beta.messages.create()` directly |
| **Multi-turn with advisor** | Must preserve `advisor_tool_result` blocks in conversation history |
| **Cost tracking** | `usage.iterations[]` breaks down tokens per model |
| **Advisor caching** | Caches advisor transcript across calls in a conversation |

## How It Works

```
User: "Design a rate limiter..."

Executor (Haiku 4.5):
  → "Let me consult the advisor on architecture..."
  → server_tool_use: advisor()        ← executor decides WHEN to ask
  
  [Anthropic runs Opus 4.6 sub-inference with full transcript]
  
  → advisor_tool_result: "1. Use sliding window... 2. Redis backend..."
  → Executor continues, informed by Opus-level advice
  → Generates full implementation at Haiku speed/cost
```

The advisor sees the full conversation but runs **without tools** and **without streaming**. Only the advice text reaches the executor. All happens in a single `/v1/messages` request.

## Examples in This Experiment

| # | Example | What It Shows |
|---|---------|---------------|
| 1 | Architecture Design | Single-turn: advisor guides an API rate limiter design |
| 2 | Iterative Refinement | Multi-turn: advisor guides event sourcing, then snapshotting |
| 3 | Cost Comparison | Same task with and without advisor — shows token breakdown |

## Model Compatibility

The advisor must be at least as capable as the executor:

| Executor | Valid Advisors |
|----------|---------------|
| Claude Haiku 4.5 | Claude Opus 4.6 |
| Claude Sonnet 4.6 | Claude Opus 4.6 |
| Claude Opus 4.6 | Claude Opus 4.6 |

## Billing

- **Executor tokens** billed at executor model rates (Haiku: $1/$5 per 1M)
- **Advisor tokens** billed at advisor model rates (Opus: $5/$25 per 1M)
- Advisor output is typically 400–700 text tokens (1,400–1,800 total with thinking)
- Net effect: close to Opus quality, bulk of generation at Haiku cost

## Beta Access

Requires the `advisor-tool-2026-03-01` beta header. The SDK sets this via `betas=["advisor-tool-2026-03-01"]`.

## Usage

```bash
python experiment_4/run.py
```

## Key Takeaways

- The executor **decides** when to call the advisor — like any other tool
- Advisor input is always empty (`{}`) — the server constructs the advisor's view automatically
- In multi-turn, **preserve full `response.content`** including `advisor_tool_result` blocks
- If you remove the advisor tool from `tools`, also strip `advisor_tool_result` blocks from history
- Advisor output **does not stream** — expect a pause while the sub-inference runs
