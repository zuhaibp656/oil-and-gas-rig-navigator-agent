# Coding Agent Guide — Oil & Gas Rig Navigator Agent

## Prerequisites
Install the CLI:
```bash
uv tool install google-agents-cli
```

## Development & Deployment
1. Local Testing: `uv run python app/fast_api_app.py` or `agents-cli playground`
2. Tests: `uv run pytest tests/unit`
3. Linting: `uvx ruff check app tests`
4. Deploy to Vertex AI Agent Runtime: `agents-cli deploy --project <PROJECT_ID>`

## Operational Principles
- **Single Root Agent**: Do not introduce multi-agent orchestration or sub-agents unless explicitly requested.
- **Concise Prose**: The model outputs terse, deterministic prose answers. It never outputs UI markup, raw `<a2a_datapart_json>`, or raw Vega specs in its text stream.
- **Deterministic Python UI Generation**: All A2UI v0.9 cards and Vega-Lite specs are constructed in Python and attached via `after_agent_callback`.
- **History Sanitization**: Prior turn UI envelopes are scrubbed before reaching Gemini to prevent token runaway loops.
- **Model**: Fast `gemini-2.5-flash` with `max_output_tokens=1024`.
