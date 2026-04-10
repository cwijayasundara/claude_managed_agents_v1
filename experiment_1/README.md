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

All commands run from the **project root** (not this directory).

```bash
# 1. One-time setup — creates agent + environment
python experiment_1/setup.py

# 2. Run a research session
python experiment_1/main.py

# 3. Teardown when done
python experiment_1/cleanup.py
```

## Environment Variables

Stored in the root `.env` file with `EXP1_` prefix:

| Key | Description |
|-----|-------------|
| `EXP1_AGENT_ID` | Web Research agent ID |
| `EXP1_AGENT_VERSION` | Agent version |
| `EXP1_ENVIRONMENT_ID` | Environment ID |
