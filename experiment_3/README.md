# Experiment 3 — File Upload + Data Analysis (Restricted Networking)

Demonstrates **file uploads**, **restricted networking**, and **per-tool configuration**.

## What's New (vs Experiments 1 & 2)

| Concept | Description |
|---------|-------------|
| **Files API upload** | Upload a local file and mount it into the agent's container |
| **Session resources** | Mount files at specific paths (`/workspace/sales_data.csv`) |
| **Restricted networking** | `package_managers_and_custom` with no allowed hosts — no internet |
| **Per-tool config** | `web_search` and `web_fetch` disabled; only file/bash tools enabled |
| **File cleanup** | Delete uploaded files after the session |

## How It Works

```
Your code: uploads sales_data.csv via Files API
  → file_id returned

Your code: creates session with resource mount
  → file mounted at /workspace/sales_data.csv (read-only)

Agent: reads the CSV, runs Python analysis in the container
  → (no internet — can only use the uploaded data)
  → writes HTML report to /mnt/session/outputs/

Your code: downloads the report, cleans up everything
```

## Agent Config

| Setting | Value |
|---------|-------|
| **Name** | Data Analyst |
| **Model** | `claude-haiku-4-5` |
| **Tools** | Prebuilt toolset minus `web_search` and `web_fetch` |
| **Networking** | Restricted (package managers only, no allowed hosts) |
| **Input** | `sample_data.csv` (6 months of product sales by region) |
| **Output** | HTML analysis report |

## Sample Data

`sample_data.csv` contains 36 rows of monthly sales data:
- **Products:** Widget A, Widget B, Widget C
- **Regions:** North, South
- **Metrics:** units_sold, revenue, cost
- **Period:** January–June 2025

## Usage

```bash
python experiment_3/run.py
```
