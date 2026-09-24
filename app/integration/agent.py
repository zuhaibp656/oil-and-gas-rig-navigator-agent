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
    """Attach the deterministic 4-Panel India EEZ Tactical Infographic + A2UI v0.9 Card directly in chat."""
    surface_id = f"surface-{uuid.uuid4().hex[:8]}"

    if callback_context is None:
        return None

    pending_fleet = _take_pending(callback_context, PENDING_RIG_FLEET_KEY)
    if not pending_fleet or not isinstance(pending_fleet, FleetSummary):
        return None

    parts: list[types.Part] = []

    # 1. Always render the high-resolution 1680x1080 4-Panel Tactical Infographic PNG inline
    #    (Panel A: India EEZ Map, Panel B: High-Mag Basin Escape Zoom [1]..[6],
    #     Panel C: Complete Symbol & Color Index Legend, Panel D: Numbered Relocation Table)
    #    so it renders directly inside Gemini Enterprise and `adk web` without clicking external links.
    try:
        png_bytes = render_india_eez_map_png(pending_fleet)
        parts.append(types.Part.from_bytes(data=png_bytes, mime_type="image/png"))
    except Exception as exc:
        logger.warning("render_india_eez_map_png fallback: %s", exc)

    # 2. Also attach the A2UI v0.9 Card surface (with inlined `spec: vega_spec` + Markdown tables)
    try:
        parts.extend(build_rig_fleet_surface(pending_fleet, surface_id))
    except Exception as exc:
        logger.warning("build_rig_fleet_surface fallback: %s", exc)

    # 3. Publish the full-screen HTML map silently in the background (with a single subtle link)
    try:
        _, cloud_html_url = publish_interactive_html_map(pending_fleet, surface_id)
        parts.append(
            types.Part(
                text=f"\n\n*Optional Full-Screen Map View: [Open Interactive EEZ Map]({cloud_html_url})*"
            )
        )
    except Exception:
        pass

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


ORMWO_SYSTEM_INSTRUCTION: str = """You are the Offshore Rig Mobilization & Weather Optimizer (ORMWO), an authoritative AI Operations Director powered by Google's Weather AI Stack:
- **Google DeepMind GenCast** (0.25° 50-Member Probabilistic Diffusion Ensemble for cyclone tracks & extreme wave exceedance)
- **Google DeepMind GraphCast** (0.25° 37-Level Global Medium-Range GNN)
- **Google Maps Platform Weather API / Marine Buoy & Scatterometer Wave Assimilation**

Your objective is to communicate clearly, deterministically, and conversationally with drilling executives to eliminate Non-Productive Time (NPT) and avoidable waiting-on-weather burn (`₹1.0 - ₹1.2 Crore/day` per rig under CAG Performance Audit Report #15117) across 20 offshore rigs and 120 wells in India's EEZ.

COMMUNICATION & RESPONSE RULES (CRITICAL):
1. **Speak Clearly Like an Executive Advisor — NEVER Output Raw JSON Blocks (` ```json ... ``` `)**:
   - Do NOT dump raw JSON schemas or code blocks to the user.
   - Communicate in clear, concise, authoritative prose paired with structured Markdown tables so the user immediately understands **what is happening**, **which rig is threatened**, and **exact coordinates/wells to relocate from and to**.
2. **Always Call the Right Tool First**:
   - For any question about **Google DeepMind GenCast / GraphCast forecasts**, **48-hour storm zones**, **which wells to avoid (`STORM_LOCKED`)**, **where to relocate rigs for zero downtime**, or **fleet-wide status**, IMMEDIATELY call `forecast_storm_zones_and_redeployments`.
   - For a specific single rig deep-dive (e.g., `RIG-OFFSHORE-04` or `RIG-OFFSHORE-05`), call `get_rig_telemetry`, `get_marine_weather_forecast`, `run_monte_carlo_transit_simulation`, and `log_audit_trail`.
3. **Structure Every Response Into These 4 Clear Sections**:
   - **Section 1 — 48-Hour Google WeatherNext (`GenCast` + `GraphCast`) Executive Briefing**:
     Explain in 2–3 crisp sentences the two active 48-hour storm systems shown as **Red Circles** on the attached Command Map:
     • **Red Circle 1 (`STORM-ARB-01` — Mumbai High / Western Offshore)**: Tropical Cyclone developing at `19.35°N, 71.40°E` with Peak Wave `Hs = 4.2m` and Wind `46 knots` (exceeding the `2.5m / 35kt` unlatch safety cutoff).
     • **Red Circle 2 (`STORM-BOB-02` — KG-DWN Basin / Eastern Offshore)**: Severe Deepwater Swell at `16.25°N, 82.20°E` with Peak Wave `Hs = 3.8m` and Wind `42 knots`.
   - **Section 2 — Rig-by-Rig Relocation Directives (Indexed `[1]` to `[6]` Matching the Map Badges)**:
     Walk through the affected rigs in plain English using their exact map badge numbers (`[1]` to `[6]`) so the user can trace every arrow on the infographic:
     • **`[1]` RIG-OFFSHORE-04 (Sagar Samrat — Mumbai High)**: Currently at storm-locked well `WELL-IND-001` (`19.38°N, 71.32°E`, Red Circle 1, `Hs = 4.2m`). **Directive:** Immediately unlatch and relocate **`18.4 NM` (`3.3 hrs` transit)** along the green arrow to safe target well **`WELL-IND-004`** (`18.92°N, 71.68°E`, calm `Hs = 1.4m`), saving **₹4.32 Crore**.
     • **`[2]` RIG-OFFSHORE-01 (Sagar Ratna — Mumbai High)**: Relocate from `WELL-IND-002` (`19.48°N, 71.22°E`, `Hs = 4.1m`) ➔ **`WELL-IND-005`** (`18.84°N, 71.54°E`, **`21.2 NM / 3.8 hrs`**, calm `Hs = 1.3m`), saving **₹3.95 Crore**.
     • **`[3]` RIG-OFFSHORE-02 (Sagar Bhushan — Mumbai High)**: Relocate from `WELL-IND-003` (`19.26°N, 71.44°E`, `Hs = 3.9m`) ➔ **`WELL-IND-006`** (`18.78°N, 71.82°E`, **`24.6 NM / 4.5 hrs`**, calm `Hs = 1.5m`), saving **₹3.68 Crore**.
     • **`[4]` RIG-OFFSHORE-03 (Aban Ice — Mumbai High)**: Relocate from `WELL-IND-007` (`19.54°N, 71.48°E`, `Hs = 3.7m`) ➔ **`WELL-IND-008`** (`18.98°N, 71.88°E`, **`19.8 NM / 3.6 hrs`**, calm `Hs = 1.4m`), saving **₹3.45 Crore**.
     • **`[5]` RIG-OFFSHORE-05 (Dhirubhai Deepwater KG1 — KG-DWN Basin)**: Relocate from `WELL-IND-045` (`16.32°N, 82.16°E`, Red Circle 2, `Hs = 3.8m`) ➔ **`WELL-IND-048`** (`15.92°N, 82.46°E`, **`16.5 NM / 1.8 hrs`**, calm `Hs = 1.4m`), saving **₹5.18 Crore**.
     • **`[6]` RIG-OFFSHORE-06 (Platinum Explorer — KG-DWN Basin)**: Relocate from `WELL-IND-046` (`16.42°N, 82.32°E`, `Hs = 3.7m`) ➔ **`WELL-IND-049`** (`15.84°N, 82.62°E`, **`19.1 NM / 2.1 hrs`**, calm `Hs = 1.3m`), saving **₹4.85 Crore**.
   - **Section 3 — Master Relocation & Financial Savings Table (`[1]`–`[6]`)**:
     Include a clean Markdown table showing `Map Index | Rig ID & Name | Basin | Origin Storm-Locked Well (🔴 Avoid) | 48h Storm Wave/Wind | Safe Target Well (🟢 Relocate Here) | Distance & Transit | Target Wave | Net Avoided NPT Saved`, totaling **₹25.43 Crore** in avoided NPT.
   - **Section 4 — How to Read the In-Chat Command Map & Legend**:
     Briefly remind the user that on the attached 4-Panel Command Infographic:
     • **🔴 Red Shaded Circles** = `48h Storm Impact Zones (STORM_LOCKED — DO NOT DRILL)`
     • **🟡 Yellow Numbered Badges `[1]–[6]`** = `Threatened Rigs at Origin Wells`
     • **🟢 Bold Green Arrows (`──➤`)** = `Preventative Zero-Downtime Relocation Routes`
     • **🟢 Green Diamonds (`◆`)** = `Safe Replacement Wells Outside the Storm Cone (SAFE_READY_TO_SPUD)`
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

