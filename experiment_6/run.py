"""Experiment 6 — LangChain Middleware Advisor Strategy.

Implements the advisor pattern using LangChain v1's middleware architecture:
  - A fast executor model (Haiku) handles most turns
  - A stronger advisor model (Opus) is consulted via wrap_model_call middleware
  - The middleware intercepts model calls, decides when to escalate, and
    injects the advisor's guidance into the executor's context

This is the open-source, model-agnostic equivalent of Anthropic's native
advisor tool (Experiment 4), built with LangChain's create_agent + middleware.

Ref: https://x.com/IeloEmanuele/status/2042547043021832530
"""

import os

from dotenv import load_dotenv

load_dotenv()

from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentMiddleware,
    wrap_model_call,
    ModelRequest,
    ModelResponse,
)
from langchain_anthropic import ChatAnthropic


# ── Models ───────────────────────────────────────────────────────────────────

executor_model = ChatAnthropic(model="claude-haiku-4-5", max_tokens=4096)
advisor_model = ChatAnthropic(model="claude-opus-4-6", max_tokens=2048)


# ── Advisor Middleware ───────────────────────────────────────────────────────

class AdvisorMiddleware(AgentMiddleware):
    """Middleware that consults a stronger advisor model before the executor.

    On the first model call and periodically thereafter, the middleware:
    1. Sends the full conversation to the advisor model
    2. Asks for a strategic plan (concise, enumerated steps)
    3. Injects the advisor's guidance into the executor's system prompt
    4. Lets the executor proceed, informed by the advice

    This mirrors Anthropic's native advisor tool but is:
    - Open source (LangChain middleware)
    - Model agnostic (any LLM pair works)
    - Fully customizable (you control when/how to consult)
    """

    def __init__(self, advisor, consult_every_n: int = 3):
        """
        Args:
            advisor: The stronger model to consult for strategic guidance.
            consult_every_n: Consult the advisor every N model calls.
        """
        self.advisor = advisor
        self.consult_every_n = consult_every_n
        self.call_count = 0
        self.last_advice = None

    def wrap_model_call(self, handler):
        """Intercept model calls to inject advisor guidance."""

        async def wrapped(request: ModelRequest) -> ModelResponse:
            self.call_count += 1
            should_consult = (
                self.call_count == 1  # Always consult on first call
                or self.call_count % self.consult_every_n == 0  # Periodic
            )

            if should_consult:
                print(f"\n  [Advisor middleware: consulting Opus (call #{self.call_count})...]")

                # Build the advisor prompt from the current conversation
                advisor_messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are a strategic advisor. Review the conversation and "
                            "provide concise guidance in under 100 words. Use enumerated "
                            "steps, not explanations. Focus on approach, pitfalls to "
                            "avoid, and key decisions."
                        ),
                    },
                    *[
                        {"role": m.type if hasattr(m, "type") else "user", "content": str(m.content)}
                        for m in request.messages[-10:]  # Last 10 messages for context
                    ],
                    {
                        "role": "user",
                        "content": "Provide your strategic guidance for the task above.",
                    },
                ]

                # Consult the advisor
                advice_response = await self.advisor.ainvoke(advisor_messages)
                self.last_advice = advice_response.content
                print(f"  [Advisor says: {self.last_advice[:150]}...]")
                print()

            # Inject advice into the system message if available
            if self.last_advice:
                advice_block = (
                    f"\n\n<advisor_guidance>\n{self.last_advice}\n</advisor_guidance>\n\n"
                    "Consider the advisor's guidance above when responding. "
                    "Follow the enumerated steps where applicable."
                )
                current_system = request.system_message.content if request.system_message else ""
                from langchain_core.messages import SystemMessage

                request = request.override(
                    system_message=SystemMessage(content=current_system + advice_block)
                )

            # Call the executor with the enriched context
            return await handler(request)

        return wrapped


# ── Example 1: Single-turn with Advisor ──────────────────────────────────────

def run_single_turn():
    """Single-turn: advisor guides architecture design."""
    print("=" * 60)
    print("EXAMPLE 1: Single-turn — Advisor-Guided Architecture")
    print(f"  Executor: claude-haiku-4-5")
    print(f"  Advisor:  claude-opus-4-6")
    print("=" * 60)
    print()

    advisor_mw = AdvisorMiddleware(advisor=advisor_model, consult_every_n=3)

    agent = create_agent(
        model=executor_model,
        tools=[],
        system_prompt=(
            "You are a senior software architect. Provide clear, "
            "well-structured technical designs with code examples."
        ),
        middleware=[advisor_mw],
    )

    result = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": (
                    "Design a rate limiter for an API gateway that supports "
                    "per-user and per-endpoint limits with sliding window counters. "
                    "Provide a Python implementation."
                ),
            }
        ]
    })

    for msg in reversed(result["messages"]):
        if hasattr(msg, "content") and isinstance(msg.content, str) and msg.content:
            print(msg.content)
            break

    print(f"\n  [Total advisor consultations: {advisor_mw.call_count}]")
    print()


# ── Example 2: Multi-turn with Periodic Advisor ─────────────────────────────

def run_multi_turn():
    """Multi-turn: advisor consulted periodically as complexity grows."""
    print("=" * 60)
    print("EXAMPLE 2: Multi-turn — Periodic Advisor Consultation")
    print("=" * 60)
    print()

    advisor_mw = AdvisorMiddleware(advisor=advisor_model, consult_every_n=2)

    agent = create_agent(
        model=executor_model,
        tools=[],
        system_prompt="You are a helpful coding assistant.",
        middleware=[advisor_mw],
    )

    conversations = [
        "Design a simple event sourcing system in Python with an event store and aggregate root.",
        "Now add snapshot support so we don't replay all events from the beginning.",
        "Add a projection system that builds read models from the event stream.",
    ]

    messages = []
    for i, user_msg in enumerate(conversations, 1):
        print(f"--- Turn {i}: {user_msg[:60]}... ---\n")
        messages.append({"role": "user", "content": user_msg})

        result = agent.invoke({"messages": messages})

        # Get the assistant's response
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and isinstance(msg.content, str) and msg.content:
                # Print first 300 chars of each response
                preview = msg.content[:300]
                if len(msg.content) > 300:
                    preview += "..."
                print(preview)
                messages.append({"role": "assistant", "content": msg.content})
                break

        print()

    print(f"  [Total advisor consultations across {len(conversations)} turns: {advisor_mw.call_count}]")
    print()


# ── Example 3: Comparison — Native vs Middleware Advisor ─────────────────────

def run_comparison():
    """Side-by-side comparison of the two advisor approaches."""
    print("=" * 60)
    print("COMPARISON: Native Advisor Tool vs Middleware Advisor")
    print("=" * 60)
    print()
    print(f"{'Feature':<30} {'Anthropic Native (Exp 4)':<28} {'LangChain Middleware (Exp 6)':<28}")
    print(f"{'-'*30} {'-'*28} {'-'*28}")
    print(f"{'Implementation':<30} {'Server-side tool':<28} {'Client-side middleware':<28}")
    print(f"{'Executor decides when':<30} {'Yes (tool call)':<28} {'No (middleware logic)':<28}")
    print(f"{'Advisor sees full context':<30} {'Yes (server-managed)':<28} {'Yes (middleware passes it)':<28}")
    print(f"{'Round trips':<30} {'0 (single API request)':<28} {'1 extra (advisor call)':<28}")
    print(f"{'Model lock-in':<30} {'Claude only':<28} {'Any LLM pair':<28}")
    print(f"{'Customizable timing':<30} {'Via system prompt':<28} {'Full code control':<28}")
    print(f"{'Advisor caching':<30} {'Built-in (ephemeral)':<28} {'DIY (add your own cache)':<28}")
    print(f"{'Streaming':<30} {'Pauses during advisor':<28} {'Separate calls':<28}")
    print(f"{'Open source':<30} {'No':<28} {'Yes (LangChain MIT)':<28}")
    print(f"{'Beta header required':<30} {'Yes':<28} {'No':<28}")
    print(f"{'Cost tracking':<30} {'usage.iterations[]':<28} {'Manual (two API calls)':<28}")
    print()


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nExperiment 6 — LangChain Middleware Advisor Strategy\n")
    print("Implements the advisor pattern (cf. Experiment 4) using LangChain's")
    print("middleware architecture instead of Anthropic's native advisor tool.\n")

    # Always show the comparison
    run_comparison()

    try:
        run_single_turn()
        run_multi_turn()
    except ImportError as e:
        print(f"Import error: {e}")
        print("\nMake sure dependencies are installed:")
        print("  pip install langchain langchain-anthropic")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print("Done.")
