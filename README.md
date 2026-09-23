# Oil & Gas Rig Navigator Agent

> **Autonomous Upstream Rig Tracking, Operational Telemetry & Interactive Geospatial A2UI Surfaces for Gemini Enterprise**

[![Platform](https://img.shields.io/badge/Vertex%20AI-Agent%20Runtime-4285F4.svg)]()
[![Google ADK](https://img.shields.io/badge/Google%20ADK-2.6.2-orange.svg)]()
[![A2UI Protocol](https://img.shields.io/badge/A2UI-v0.9-green.svg)]()
[![Model](https://img.shields.io/badge/Model-Gemini%202.5%20Flash-blue.svg)]()
[![Region](https://img.shields.io/badge/Region-asia--south1-purple.svg)]()

---

## Overview

The **Oil & Gas Rig Navigator Agent** provides real-time fleet visibility, geospatial tracking, and operational drilling telemetry across offshore (drillships, semisubs, jackups) and onshore rigs directly within **Gemini Enterprise chat**.

Built on Google's **Agent Development Kit (ADK)** and deployed to **Vertex AI Agent Runtime**, this agent features:

1. **Deterministic Single-Agent Design**: No complex sub-agent hallucinations. The LLM handles natural language intent and tool routing; deterministic Python code handles calculations and rendering.
2. **Interactive A2UI v0.9 Surfaces**: Renders live geospatial rig maps and telemetry bar gauges inside chat using `@safe_vega` (Vega-Lite v5).
3. **No UI / Direct Gemini Enterprise Integration**: Communicates via standard Agent-to-Agent (A2A) protocol with runtime extension negotiation.
4. **Guardrail Triad**:
   - `before_model_callback`: Strips past A2UI markers from context to eliminate token runaway loops.
   - `after_model_callback`: Removes any accidental UI markup in the model's text prose.
   - `after_agent_callback`: Attaches authoritative visual cards deterministically.

---

## Project Structure

```
oil-and-gas-rig-navigator-agent/
├── agents-cli-manifest.yaml   # Deployment manifest for Google Agents CLI
├── deployment_metadata.json   # Vertex AI Reasoning Engine mapping
├── pyproject.toml             # uv package dependencies (ADK, A2A, Vega)
├── GEMINI.md                  # Operational guidance for coding agents
├── assets/                    # Official vector icons and brand assets
│   └── rig_navigator_icon.svg
├── app/
│   ├── contracts.py           # Domain dataclasses & A2UI models (zero dependencies)
│   ├── agent.py               # Re-exports root_agent and app
│   ├── fast_api_app.py        # FastAPI server with A2A routes and Reasoning Engine adapter
│   ├── app_utils/             # A2A routes, session services, reasoning engine proxy
│   ├── integration/
│   │   ├── agent.py           # Root Agent definition with guardrail callbacks
│   │   ├── agent_card.py      # Capabilities declaration (A2UI v0.9 extension)
│   │   ├── executor.py        # Runtime A2UI extension negotiator
│   │   └── tools.py           # Deterministic tools (list_rig_fleet, query_rig_telemetry)
│   ├── render/
│   │   ├── a2ui_envelope.py   # <a2a_datapart_json> wrapper for A2A DataPart transport
│   │   ├── a2ui_lifecycle.py  # createSurface, updateComponents, updateDataModel builders
│   │   ├── a2ui_emit.py       # Callback surface emitter
│   │   ├── rig_map_vega.py    # Safe Vega-Lite v5 geospatial & telemetry charts
│   │   └── rig_fleet_card.py  # A2UI v0.9 card component hierarchy
│   ├── rigs/                  # Rig domain logic & kinematics
│   ├── gcs/                   # Cloud Storage clients & paths
│   └── bq/                    # BigQuery audit & telemetry connectors
├── docs/                      # Architectural guides & coding standards
└── tests/                     # Unit & integration test suites
```

---

## Quickstart

### 1. Installation
```bash
cd oil-and-gas-rig-navigator-agent
uv sync
```

### 2. Run Tests
```bash
uv run pytest tests/unit
```

### 3. Local Development Server
```bash
uv run python app/fast_api_app.py
```
Open `http://localhost:8000/docs` to inspect the OpenAPI schema and A2A endpoints.

### 4. Deploy to Vertex AI Agent Runtime & Gemini Enterprise
```bash
agents-cli deploy --project <YOUR_GCP_PROJECT_ID>
```
