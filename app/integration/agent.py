"""ADK Root Agent for the Offshore Rig Mobilization & Weather Optimizer (ORMWO).

In : Operational trigger or user inquiry regarding India's 20 offshore rigs, 120+ candidate wells,
     48-hour metocean forecasts, or storm evacuation/redeployment optimization.
Out: Strict deterministic JSON (or concise tabular report) + visual 5-Layer Map of India & EEZ
     (20 Rigs, 120 Candidate Wells, 48h Storm Zones & Waypoint Trajectories).
Rule: The model outputs strict JSON/terse text only. Interactive Vega maps (for Gemini Enterprise)
      and inline high-res India EEZ maps (for `adk web`) are attached deterministically in Python.
"""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Any
import uuid

# Automatically enable Vertex AI mode whenever running inside Vertex AI Agent Engine / Cloud Run
# (where GEMINI_API_KEY / GOOGLE_API_KEY is not used) so Playground never asks for an API key.
if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "zuhaibp-ai")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

import google.auth
import google.oauth2.credentials
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types


class _GcloudCliCredentials(google.oauth2.credentials.Credentials):
    """Self-refreshing OAuth2 credentials backed by Argolis ADC or `gcloud auth print-access-token`."""

    def __init__(self) -> None:
        adc_file = os.path.expanduser("~/.config/gcloud/argolis_admin_adc.json")
        if os.path.exists(adc_file):
            from google.auth.transport.requests import Request
            c = google.oauth2.credentials.Credentials.from_authorized_user_file(
                adc_file,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            c.refresh(Request())
            super().__init__(token=c.token)
            return
        token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
        super().__init__(token=token)

    def refresh(self, request: Any) -> None:
        adc_file = os.path.expanduser("~/.config/gcloud/argolis_admin_adc.json")
        if os.path.exists(adc_file):
            from google.auth.transport.requests import Request
            c = google.oauth2.credentials.Credentials.from_authorized_user_file(
                adc_file,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            c.refresh(Request())
            self.token = c.token
            return
        self.token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()


_ORIG_GOOGLE_AUTH_DEFAULT = google.auth.default


def _patched_google_auth_default(*args: Any, **kwargs: Any) -> tuple[Any, str | None]:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or "zuhaibp-ai"
    adc_file = os.path.expanduser("~/.config/gcloud/argolis_admin_adc.json")
    if os.path.exists(adc_file):
        try:
            from google.auth.transport.requests import Request
            c = google.oauth2.credentials.Credentials.from_authorized_user_file(
                adc_file,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            c.refresh(Request())
            return c, project
        except Exception:
            pass
    return _ORIG_GOOGLE_AUTH_DEFAULT(*args, **kwargs)


if (
    os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
    and os.path.exists(os.path.expanduser("~/.config/gcloud/argolis_admin_adc.json"))
):
    google.auth.default = _patched_google_auth_default

try:
    from app.contracts import FleetSummary
    from app.integration.tools import (
        PENDING_RIG_FLEET_KEY,
        forecast_storm_zones_and_redeployments,
        get_marine_weather_forecast,
        get_rig_telemetry,
        list_rig_fleet,
        log_audit_trail,
        query_rig_telemetry,
        resolve_pending_fleet_summary,
        run_monte_carlo_transit_simulation,
    )
    from app.render.a2ui_emit import build_rig_fleet_surface
    from app.render.a2ui_envelope import (
        A2A_DATA_PART_CLOSE_TAG,
        A2A_DATA_PART_OPEN_TAG,
    )
    from app.render.india_map_png import render_india_eez_map_png
    from app.render.interactive_html_map import publish_interactive_html_map
except ImportError:
    from contracts import FleetSummary
    from integration.tools import (
        PENDING_RIG_FLEET_KEY,
        forecast_storm_zones_and_redeployments,
        get_marine_weather_forecast,
        get_rig_telemetry,
        list_rig_fleet,
        log_audit_trail,
        query_rig_telemetry,
        resolve_pending_fleet_summary,
        run_monte_carlo_transit_simulation,
    )
    from render.a2ui_emit import build_rig_fleet_surface
    from render.a2ui_envelope import (
        A2A_DATA_PART_CLOSE_TAG,
        A2A_DATA_PART_OPEN_TAG,
    )
    from render.india_map_png import render_india_eez_map_png
    from render.interactive_html_map import publish_interactive_html_map

logger = logging.getLogger(__name__)

MODEL: str = os.environ.get(
    "ORMWO_MODEL",
    "gemini-2.5-flash"
    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "TRUE").upper() == "TRUE"
    else "gemini-3-flash-preview",
)


def _take_pending(callback_context: CallbackContext | None, key: str) -> FleetSummary | None:
    """Safely read, resolve, and clear whatever a tool queued under key."""
    if callback_context is None or callback_context.state is None:
        return None
    val = callback_context.state.get(key)
    if val is not None:
        try:
            callback_context.state[key] = None
        except Exception:
            pass
    return resolve_pending_fleet_summary(val)


def emit_a2ui_surface(
    callback_context: CallbackContext | None = None,
    **kwargs: Any,
) -> types.Content | None:
    """Attach the deterministic India EEZ Map surface earned this turn to the model's reply."""
    surface_id = f"surface-{uuid.uuid4().hex[:8]}"

    if callback_context is None:
        return None

    pending_fleet = _take_pending(callback_context, PENDING_RIG_FLEET_KEY)
    if not pending_fleet or not isinstance(pending_fleet, FleetSummary):
        return None

    use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
    force_a2ui = os.environ.get("ORMWO_EMIT_A2UI_DATAPART", "FALSE").upper() == "TRUE"

    parts: list[types.Part] = []
    if use_vertex or force_a2ui:
        # In Gemini Enterprise / Vertex AI Agent Engine, emit pure A2UI v0.9 parts
        # so Gemini Enterprise mounts the interactive VegaChart (scroll-zoom, drag-pan, hover tooltips)
        # instead of falling back to a static PNG image.
        parts.extend(build_rig_fleet_surface(pending_fleet, surface_id))
    else:
        # In local `adk web` (which does not parse <a2a_datapart_json>), publish the
        # interactive Leaflet.js + Vega-Lite HTML5 map and attach a clickable link + inline preview.
        _, cloud_html_url = publish_interactive_html_map(pending_fleet, surface_id)
        parts.append(
            types.Part(
                text=(
                    "\n\n🌐 **Interactive India EEZ Map (Zoom, Pan & Hover Over 20 Rigs + 120 Wells)**:\n"
                    "- **Local Interactive Leaflet.js + Vega-Lite Map**: "
                    "[Open http://127.0.0.1:8088/india_eez_interactive_map.html](http://127.0.0.1:8088/india_eez_interactive_map.html)\n"
                    f"- **Cloud Console Interactive Map**: [Open in Google Cloud Storage]({cloud_html_url})"
                )
            )
        )
        try:
            png_bytes = render_india_eez_map_png(pending_fleet)
            parts.append(types.Part.from_bytes(data=png_bytes, mime_type="image/png"))
        except Exception as exc:
            logger.warning("render_india_eez_map_png fallback: %s", exc)

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
    llm_response.content.parts = cleaned or [types.Part(text="[India EEZ Map Surface Attached]")]
    return llm_response


def sanitize_llm_request_history(
    callback_context: CallbackContext | None = None,
    llm_request: LlmRequest | None = None,
    **kwargs: Any,
) -> LlmResponse | None:
    """Scrub A2UI tags and inline_data payloads from prior turns to prevent token exhaustion loops."""
    if llm_request is None or not getattr(llm_request, "contents", None):
        return None

    for content in llm_request.contents:
        if not getattr(content, "parts", None):
            continue
        cleaned_parts: list[types.Part] = []
        for part in content.parts:
            # 1. Strip any inline_data (PNG map images or A2UI wire blobs) from prior turns
            if getattr(part, "inline_data", None) is not None:
                continue
            # 2. Strip any <a2a_datapart_json> text blobs
            text = getattr(part, "text", None)
            if text and A2A_DATA_PART_OPEN_TAG in text:
                stripped = _remove_datapart_blobs(text)
                if stripped.strip():
                    cleaned_parts.append(types.Part(text=stripped))
            else:
                cleaned_parts.append(part)

        content.parts = cleaned_parts or [
            types.Part(text="[Visual India EEZ Map Surface Rendered in UI]")
        ]

    if llm_request.config is None:
        llm_request.config = types.GenerateContentConfig(
            max_output_tokens=2048,
            temperature=0.0,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
    else:
        if (
            not getattr(llm_request.config, "max_output_tokens", None)
            or llm_request.config.max_output_tokens > 2048
        ):
            llm_request.config.max_output_tokens = 2048
        llm_request.config.temperature = 0.0
        llm_request.config.thinking_config = types.ThinkingConfig(thinking_budget=0)

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


ORMWO_SYSTEM_INSTRUCTION: str = """You are the Offshore Rig Mobilization & Weather Optimizer (ORMWO) powered by Google's Weather AI Stack:
- **Google DeepMind GenCast** (0.25° 50-Member Probabilistic Diffusion Ensemble for cyclone track & wave exceedance probabilities)
- **Google DeepMind GraphCast** (0.25° 37-Level Global Medium-Range GNN)
- **Google Maps Platform Weather API / Global Marine Wave & Swell Assimilation**
- **Gemini-2.5-Flash Synoptic Cyclone Track & Zero-Downtime Well Relocation Optimizer**

Your objective is to minimize Non-Productive Time (NPT) and eliminate avoidable idling costs (benchmark: ₹1.0 - ₹1.2 Cr/day per rig, CAG Audit Report #15117) across 20 offshore drilling rigs and 120 candidate well locations in the Indian Exclusive Economic Zone (EEZ).

OPERATIONAL PRINCIPLES:
1. **Google Weather Models First (`forecast_storm_zones_and_redeployments`)**:
   - Whenever the user asks about **storm zones**, **weather forecasts**, **which basins/rigs/wells will be hit by a storm**, **which wells to avoid drilling**, or **where to move rigs so there is zero downtime**, IMMEDIATELY call `forecast_storm_zones_and_redeployments`.
   - When assessing a specific rig (e.g. 'RIG-OFFSHORE-04'), call `get_rig_telemetry`, `get_marine_weather_forecast`, `run_monte_carlo_transit_simulation`, and `log_audit_trail` in a single batch.
2. **Actionable Storm-Zone & Safe-Well Relocation Guidance**:
   - Always clearly explain:
     a) **Google WeatherNext (GenCast + GraphCast) 48h Storm Cones**: Identify the exact storm systems (`STORM-ARB-01` in Mumbai High / Arabian Sea with Peak Wave `Hs = 4.2m`, Wind `46 kts`, and `STORM-BOB-02` in KG-DWN Basin / Bay of Bengal with Peak Wave `Hs = 3.8m`, Wind `42 kts`).
     b) **Wells NOT to Drill (`STORM_LOCKED` — Do Not Place Rigs Here)**: List the specific wells inside the storm cone that exceed the 48-hour safety latch limit (`Hs > 2.5m` or `Wind > 35 kts`) and warn against spudding or staying unlatched on them.
     c) **Zero-Downtime Nearby Safe Candidate Wells (`SAFE_READY_TO_SPUD`)**: Present a concise markdown table mapping each storm-threatened rig (`RIG-OFFSHORE-04 Sagar Samrat`, `RIG-OFFSHORE-01 Sagar Ratna`, `RIG-OFFSHORE-02 Sagar Bhushan`, `RIG-OFFSHORE-05 Dhirubhai Deepwater KG1`, `RIG-OFFSHORE-06 Platinum Explorer`, etc.) from its vulnerable storm-hit well to its **nearest metocean-safe replacement well** (`WELL-IND-004`, `WELL-IND-005`, `WELL-IND-048`, etc.) with exact coordinates (`Lat, Lon`), distance (`NM`), expected transit (`hours`), calm wave height (`Hs < 1.8m`), and **Net Avoided NPT Savings (`₹ Crore`)** so drilling continues with zero downtime.
   - Follow the operational table with the deterministic ORMWO JSON block below.
3. **Interactive India EEZ Map Surface**: Every tool invocation automatically attaches the Interactive 5-Layer Map of India & EEZ Waters via `after_agent_callback`. NEVER emit Vega JSON or `<a2a_datapart_json>` tags in your text output.

REQUIRED OUTPUT JSON SCHEMA (include after your concise operational storm/relocation table):
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
    description="Offshore Rig Mobilization & Weather Optimizer (ORMWO) — Google WeatherNext (GenCast/GraphCast) 48h Storm Forecasting, Zero-Downtime Well Relocation & Interactive India EEZ Map",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    generate_content_config=types.GenerateContentConfig(
        max_output_tokens=2048,
        temperature=0.0,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    ),
    instruction=ORMWO_SYSTEM_INSTRUCTION,
    tools=[
        forecast_storm_zones_and_redeployments,
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

try:
    from vertexai.preview.reasoning_engines import AdkApp

    class ORMWOAdkApp(AdkApp):
        """Production ADK App wrapper for Vertex AI Agent Engine with Playground & Streaming support."""

        def __init__(self, agent: Agent = root_agent, **kwargs: Any) -> None:
            super().__init__(agent=agent, **kwargs)

        def query(self, *args: Any, **kwargs: Any) -> Any:
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
            os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "zuhaibp-ai")
            os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
            return super().query(*args, **kwargs)

        def stream_query(self, *args: Any, **kwargs: Any) -> Any:
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
            os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "zuhaibp-ai")
            os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
            yield from super().stream_query(*args, **kwargs)

    def get_app() -> ORMWOAdkApp:
        """Factory function for initializing ORMWOAdkApp with tracing enabled for Playground."""
        return ORMWOAdkApp(agent=root_agent, enable_tracing=True)

except ImportError:
    pass

