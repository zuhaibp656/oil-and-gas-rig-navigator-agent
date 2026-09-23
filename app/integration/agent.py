"""ADK Root Agent for the Offshore Rig Mobilization & Weather Optimizer (ORMWO).

In : Operational trigger or user inquiry regarding India's 20 offshore rigs, 120+ candidate wells,
     48-hour metocean forecasts, or storm evacuation/redeployment optimization.
Out: Strict deterministic JSON (or concise tabular report) + native A2UI v0.9 Map of India & EEZ
     (20 Rigs, 120 Candidate Wells, 48h Storm Zones & Waypoint Trajectories).
Rule: The model outputs strict JSON/terse text only. Interactive Vega maps and A2UI cards are attached
      deterministically by callbacks in Python.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

try:
    from app.contracts import FleetSummary
    from app.integration.tools import (
        PENDING_RIG_FLEET_KEY,
        get_marine_weather_forecast,
        get_rig_telemetry,
        list_rig_fleet,
        log_audit_trail,
        query_rig_telemetry,
        run_monte_carlo_transit_simulation,
    )
    from app.render.a2ui_emit import build_rig_fleet_surface
    from app.render.a2ui_envelope import (
        A2A_DATA_PART_CLOSE_TAG,
        A2A_DATA_PART_OPEN_TAG,
    )
except ImportError:
    from contracts import FleetSummary
    from integration.tools import (
        PENDING_RIG_FLEET_KEY,
        get_marine_weather_forecast,
        get_rig_telemetry,
        list_rig_fleet,
        log_audit_trail,
        query_rig_telemetry,
        run_monte_carlo_transit_simulation,
    )
    from render.a2ui_emit import build_rig_fleet_surface
    from render.a2ui_envelope import (
        A2A_DATA_PART_CLOSE_TAG,
        A2A_DATA_PART_OPEN_TAG,
    )

logger = logging.getLogger(__name__)

MODEL: str = "gemini-2.5-flash"


def _take_pending(callback_context: CallbackContext | None, key: str) -> Any | None:
    """Safely read and clear whatever a tool queued under key."""
    if callback_context is None or callback_context.state is None:
        return None
    val = callback_context.state.get(key)
    if val is not None:
        try:
            callback_context.state[key] = None
        except Exception:
            pass
    return val


def emit_a2ui_surface(
    callback_context: CallbackContext | None = None,
    **kwargs: Any,
) -> types.Content | None:
    """Attach the deterministic A2UI India EEZ Map surface earned this turn to the model's reply."""
    surface_id = f"surface-{uuid.uuid4().hex[:8]}"

    if callback_context is None:
        return None

    pending_fleet = _take_pending(callback_context, PENDING_RIG_FLEET_KEY)

    parts: list[types.Part] = []
    if pending_fleet and isinstance(pending_fleet, FleetSummary):
        parts = build_rig_fleet_surface(pending_fleet, surface_id)
    else:
        return None

    if not parts:
        return None

    logger.info("emit_a2ui_surface: surface=%s parts=%d", surface_id, len(parts))
    return types.Content(role="model", parts=parts)


def strip_fabricated_a2ui(
    llm_response: LlmResponse | None = None,
    **kwargs: Any,
) -> LlmResponse | None:
    """Delete any A2UI payload the model wrote into its own prose."""
    if llm_response is None or llm_response.content is None:
        return None

    parts = llm_response.content.parts or []
    cleaned: list[types.Part] = []
    removed = 0

    for part in parts:
        text = getattr(part, "text", None)
        if not text or A2A_DATA_PART_OPEN_TAG not in text:
            cleaned.append(part)
            continue

        stripped = _remove_datapart_blobs(text)
        removed += 1
        if stripped.strip():
            cleaned.append(types.Part(text=stripped))

    if not removed:
        return None

    logger.warning("strip_fabricated_a2ui: removed A2UI payloads from %d text part(s)", removed)
    llm_response.content.parts = cleaned or [types.Part(text="")]
    return llm_response


def sanitize_llm_request_history(
    callback_context: CallbackContext | None = None,
    llm_request: LlmRequest | None = None,
    **kwargs: Any,
) -> LlmResponse | None:
    """Scrub A2UI tags and base64 payloads from prior turns to prevent token exhaustion loops."""
    if llm_request is None or not getattr(llm_request, "contents", None):
        return None

    for content in llm_request.contents:
        if not getattr(content, "parts", None):
            continue
        cleaned_parts: list[types.Part] = []
        for part in content.parts:
            text = getattr(part, "text", None)
            if text and A2A_DATA_PART_OPEN_TAG in text:
                stripped = _remove_datapart_blobs(text)
                if stripped.strip():
                    cleaned_parts.append(types.Part(text=stripped))
            else:
                cleaned_parts.append(part)

        content.parts = cleaned_parts or [types.Part(text="")]

    if llm_request.config is None:
        llm_request.config = types.GenerateContentConfig(max_output_tokens=1024)
    elif (
        not getattr(llm_request.config, "max_output_tokens", None)
        or llm_request.config.max_output_tokens > 1024
    ):
        llm_request.config.max_output_tokens = 1024

    return None


def _remove_datapart_blobs(text: str) -> str:
    """Cut every <a2a_datapart_json> region out of a string."""
    out: list[str] = []
    rest = text
    while True:
        start = rest.find(A2A_DATA_PART_OPEN_TAG)
        if start == -1:
            out.append(rest)
            return "".join(out)

        out.append(rest[:start])
        end = rest.find(A2A_DATA_PART_CLOSE_TAG, start)
        if end == -1:
            return "".join(out)
        rest = rest[end + len(A2A_DATA_PART_CLOSE_TAG):]


ORMWO_SYSTEM_INSTRUCTION: str = """You are the Offshore Rig Mobilization & Weather Optimizer (ORMWO).
Your objective is to minimize Non-Productive Time (NPT) and eliminate avoidable idling costs (benchmark: ₹1.0 - ₹1.2 Cr/day per rig, CAG Audit Report #15117) across 20 offshore drilling rigs and 120+ candidate well locations in the Indian Exclusive Economic Zone (EEZ).

OPERATIONAL PRINCIPLES:
1. Determinism First: Never calculate trajectories, distances, transit durations, or probabilistic costs in prompt tokens. Delegate all computations to Python tools.
2. Non-Verbose Output: Respond strictly in the ORMWO structured JSON schema (or a concise 3-line tabular summary if explicitly asked). Do not provide conversational filler or preambles.
3. Actionable Early Warnings: Enforce a strict 48-hour advance decision threshold (significant_wave_height_m > 2.5m OR wind_speed_knots > 35 kts) for weather-induced suspension, relocation, or re-assigning a rig to a safe alternate well coordinate so it never sits idle.
4. Interactive India EEZ Map Surface: Every tool invocation automatically renders the interactive 5-Layer Map of India & EEZ Waters (India coastline, 20 Rigs, 120 Candidate Wells, 48h Storm Hazard Zones, and Waypoint Trajectories) via after_agent_callback. NEVER emit Vega JSON or <a2a_datapart_json> tags in your text output.

DETERMINISTIC EXECUTION PIPELINE:
Upon receiving an inquiry or operational trigger:
1. INGEST: Fetch target rig telemetry via `get_rig_telemetry` (or `list_rig_fleet` for a basin/fleet sweep).
2. WEATHER CHECK: Fetch 48-hour metocean forecast via `get_marine_weather_forecast`.
3. THRESHOLD EVALUATION:
   - If `significant_wave_height_m` > 2.5m OR `wind_speed_knots` > 35 kts within 48h:
     - Mark weather threat as CRITICAL.
     - Execute `run_monte_carlo_transit_simulation` to determine the optimal safe well coordinate and routing waypoints.
   - Else:
     - Mark operational window as CLEAR.
4. AUDIT: Call `log_audit_trail` with decision inputs and outputs.
5. REPORT: Return the structured JSON outcome adhering to:
{
  "rig_id": "string",
  "assessment_timestamp": "ISO 8601 string",
  "status": "NORMAL" | "ADVISORY" | "CRITICAL_ACTION_REQUIRED",
  "npt_risk_assessment": {
    "estimated_downtime_hours": float,
    "projected_cost_exposure_inr": float,
    "primary_threat": "WEATHER_CYCLONE" | "HIGH_SWELL" | "EQUIPMENT_IDLE" | "NONE"
  },
  "operational_directive": {
    "action": "CONTINUE_OPERATIONS" | "SUSPEND_AND_LATCH" | "INITIATE_PREVENTATIVE_TRANSIT",
    "decision_deadline": "ISO 8601 string (48h advance cutoff)",
    "recommended_coordinates": {"lat": float, "lon": float}
  },
  "audit_reference_id": "string"
}
"""


root_agent = Agent(
    name="rig_navigator_agent",
    description="Offshore Rig Mobilization & Weather Optimizer (ORMWO) — 48h Metocean Risk, Monte Carlo Well Redeployment & Interactive India EEZ Map for Gemini Enterprise",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    generate_content_config=types.GenerateContentConfig(
        max_output_tokens=1024,
    ),
    instruction=ORMWO_SYSTEM_INSTRUCTION,
    tools=[
        get_rig_telemetry,
        get_marine_weather_forecast,
        run_monte_carlo_transit_simulation,
        log_audit_trail,
        list_rig_fleet,
        query_rig_telemetry,
    ],
    before_model_callback=sanitize_llm_request_history,
    after_model_callback=strip_fabricated_a2ui,
    after_agent_callback=emit_a2ui_surface,
)

app = App(
    root_agent=root_agent,
    name="rig_navigator_agent",
)
