# Experiment 6 — LangChain Middleware Advisor Strategy

Implements the **advisor strategy pattern** using LangChain v1's middleware architecture — the open-source, model-agnostic equivalent of Anthropic's native advisor tool (Experiment 4).

Ref: [LangChain middleware advisor implementation](https://x.com/IeloEmanuele/status/2042547043021832530)

## What's New (vs Experiments 4 & 5)

| Concept | Description |
|---------|-------------|
| **`wrap_model_call` middleware** | Intercepts every model call to inject advisor guidance |
| **`AdvisorMiddleware` class** | Custom middleware that consults a stronger model before the executor |
| **Client-side advisor** | Advisor runs as a separate API call (vs Experiment 4's server-side tool) |
| **Configurable frequency** | `consult_every_n` controls how often the advisor is consulted |
| **Model agnostic** | Works with any LLM pair, not just Claude |

## How It Works

```
User message arrives
  │
  ▼
wrap_model_call middleware fires
  │
  ├── Should consult advisor? (first call, or every N calls)
  │     │
  │     ├── YES: Send conversation to Opus → get strategic guidance
  │     │         Inject advice into system prompt
  │     │
  │     └── NO: Use cached advice from last consultation
  │
  ▼
Executor (Haiku) generates response with advisor context
```

### vs Anthropic's Native Advisor Tool (Experiment 4)

| Feature | Native (Exp 4) | Middleware (Exp 6) |
|---------|---------------|-------------------|
| Implementation | Server-side tool | Client-side middleware |
| Executor decides when | Yes (tool call) | No (middleware logic) |
| Round trips | 0 (single API request) | 1 extra (advisor call) |
| Model lock-in | Claude only | Any LLM pair |
| Customizable timing | Via system prompt | Full code control |
| Open source | No | Yes (LangChain MIT) |

## Examples

| # | Example | What It Shows |
|---|---------|---------------|
| 1 | Single-turn Architecture | Advisor guides rate limiter design on first call |
| 2 | Multi-turn Refinement | Advisor consulted periodically as complexity grows |
| 3 | Comparison Table | Native vs middleware advisor side-by-side |

## Installation

```bash
pip install langchain langchain-anthropic
```

## Usage

```bash
python ex_6_advisor_middleware/run.py
```

## Customizing the Advisor

### Change consultation frequency

```python
# Consult every 2 model calls
advisor_mw = AdvisorMiddleware(advisor=advisor_model, consult_every_n=2)

# Consult on every call (most expensive, highest quality)
advisor_mw = AdvisorMiddleware(advisor=advisor_model, consult_every_n=1)
```

### Use different model pairs

```python
from langchain_openai import ChatOpenAI

# GPT-4.1-mini executor + GPT-4.1 advisor
executor = ChatOpenAI(model="gpt-4.1-mini")
advisor = ChatOpenAI(model="gpt-4.1")
advisor_mw = AdvisorMiddleware(advisor=advisor)
agent = create_agent(model=executor, middleware=[advisor_mw])
```

### Combine with other middleware

```python
from langchain.agents.middleware import HumanInTheLoopMiddleware

agent = create_agent(
    model=executor_model,
    middleware=[
        AdvisorMiddleware(advisor=advisor_model),    # Strategic guidance
        HumanInTheLoopMiddleware(),                  # Approval gates
    ],
)
```
