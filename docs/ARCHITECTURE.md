# Oil & Gas Rig Navigator Agent — Architecture & Methodology Guide

## 1. The Core Problem with Previous Agents
Most traditional agent implementations fail in enterprise production environments (especially Gemini Enterprise) due to five systemic flaws:

1. **Multi-Agent Chain Hallucination**: Creating tangled webs of sub-agents passing loose conversational context back and forth causes non-deterministic output drift, state desynchronization, and silent failures.
2. **LLMs Authoring Complex UI Payloads**: Models cannot reliably author 100 KB JSON specifications (such as Vega-Lite or A2UI) without syntax errors or token budget blowouts.
3. **History Polluting Loops**: In A2A protocols, when an A2UI payload or base64 image is returned on Turn $N$, it re-enters the conversation history on Turn $N+1$ wrapped in `<a2a_datapart_json>`. The LLM reads its own past payloads, attempts to imitate them in text prose, and spins for minutes until hitting max token limits.
4. **Silent A2UI Dropping**: Declaring A2UI on an agent card is insufficient; the client-side host (Gemini Enterprise) requires runtime A2UI extension negotiation at the executor level (`X-A2A-Extensions`).
5. **Verbosity vs. Determinism**: Enterprise users need instant, concise answers with authoritative visual surfaces, not paragraphs of conversational filler.

---

## 2. The Production Architecture (Learned from Reference Repos)

This agent adopts the exact architecture proven in `Well-Log-Digitization` and `ppac-energy-intelligence-agent`:

```
+-----------------------------------------------------------------------------------+
|                            Gemini Enterprise (Client)                             |
|  - A2UI v0.9 Host (Angular Renderer, Material 3, @safe_vega, Base64 Image)        |
+-----------------------------------------------------------------------------------+
                                         ▲
                                         │ A2A JSON-RPC + X-A2A-Extensions
                                         ▼
+-----------------------------------------------------------------------------------+
|               Vertex AI Agent Runtime (Reasoning Engine in asia-south1)            |
|                                                                                   |
|  1. A2uiNegotiatingExecutor:                                                      |
|     - Inspects client requested extensions ('https://a2ui.org/a2a-extension/a2ui/v0.9')|
|     - Activates A2UI v0.9 in context state                                       |
|                                                                                   |
|  2. Single ADK Root Agent (gemini-2.5-flash):                                     |
|     - Instruction: Crisp, deterministic prose only.                               |
|     - Token ceiling: max_output_tokens=1024                                       |
|                                                                                   |
|  3. Strict Guardrail Triad:                                                       |
|     [before_model_callback] sanitize_llm_request_history                          |
|         - Strips <a2a_datapart_json> blobs from history so Gemini context is pure|
|     [after_model_callback] strip_fabricated_a2ui                                  |
|         - Catches and deletes any UI JSON the model accidentally wrote in prose   |
|     [after_agent_callback] emit_a2ui_surface                                      |
|         - Reads pending key in callback_context.state                             |
|         - 100% deterministic Python builder generates A2UI + Vega-Lite spec       |
|         - Wraps in <a2a_datapart_json> and attaches as Part                       |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                           Domain & Infrastructure Layer                           |
|  - Rigs Engine: Coordinates, status, live telemetry                               |
|  - BigQuery: Historical well logs, kicks, drilling audit trail                    |
|  - Google Cloud Storage: Telemetry data lakes and reports                          |
+-----------------------------------------------------------------------------------+
```

---

## 3. Key Design Invariants

| Invariant | Implementation Rule |
|---|---|
| **One file, one job** | Modules only import `contracts.py`; pure domain logic without side-effects. |
| **Model never authors Vega/UI** | Vega charts and A2UI component trees are generated deterministically in Python. |
| **One message per Part** | `wrap_a2ui_part` wraps exactly one lifecycle message (`createSurface`, `updateDataModel`, `updateComponents`). |
| **`updateDataModel` uses `value`** | The payload key is `value`, NOT `data`. (Using `data` breaks the Gemini Enterprise parser). |
| **Root Component ID** | The leading component MUST have `id: "root"` (usually a Card holding a Column). |
| **Payload Budget** | Total message size kept under 400 KiB (hard platform cap is 512 KiB). |
| **Fast Model & Region** | `gemini-2.5-flash` in `asia-south1` or specified project region for sub-second latency. |
