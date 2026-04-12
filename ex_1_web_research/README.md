# Experiment 1 — Web Research (Agentic AI Dashboard)

A managed agent that researches the latest developments in agentic AI and produces a self-contained HTML dashboard.

## Agent Config

| Setting | Value |
|---------|-------|
| **Name** | Web Research |
| **Model** | `claude-haiku-4-5` |
| **Tools** | Full prebuilt toolset (`agent_toolset_20260401`) |
| **Networking** | Unrestricted |
| **Output** | Self-contained HTML dashboard |

## Usage

Run from the **project root**:

```bash
python ex_1_web_research/run.py
```

This handles the full lifecycle: creates the agent + environment, runs a research session, downloads the HTML dashboard, and tears everything down.
