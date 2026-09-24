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


def _build_standout_links_markdown() -> str:
    """Build a prominent, impossible-to-miss Call-to-Action Markdown block for the Interactive HTML Map & 4-Panel PNG."""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or "zuhaibp-ai"
    bucket_name = f"{project_id}-agent-staging"
    html_mtls = f"https://storage.mtls.cloud.google.com/{bucket_name}/interactive_maps/india_eez_latest.html"
    html_cloud = f"https://storage.cloud.google.com/{bucket_name}/interactive_maps/india_eez_latest.html"
    png_mtls = f"https://storage.mtls.cloud.google.com/{bucket_name}/interactive_maps/india_eez_4panel_latest.png"
    return (
        "\n\n---\n"
        "### 🌐 Interactive Full-Screen Command Map & High-Res 4-Panel Infographic\n"
        f"- 🚀 **[CLICK HERE TO LAUNCH INTERACTIVE FULL-SCREEN BATHYMETRIC HTML MAP (Leaflet + Click-to-Fly Rigs [1]–[6]) ↗]({html_mtls})**  \n"
        f"  *(Alternate Link: [Open Interactive HTML Map via storage.cloud.google.com ↗]({html_cloud}))*\n"
        f"- 🖼️ **[CLICK HERE TO OPEN FULL-SIZE 1680×1080 4-PANEL COMMAND INFOGRAPHIC (PNG) ↗]({png_mtls})**\n"
    )


def emit_a2ui_surface(
    callback_context: CallbackContext | None = None,
    **kwargs: Any,
) -> types.Content | None:
    """Attach the Full-Width 3-Tier Bathymetric A2UI v0.9 Card + upload Interactive HTML & 4-Panel PNG to GCS."""
    surface_id = f"surface-{uuid.uuid4().hex[:8]}"

    if callback_context is None:
        return None

    pending_fleet = _take_pending(callback_context, PENDING_RIG_FLEET_KEY)
    if not pending_fleet or not isinstance(pending_fleet, FleetSummary):
        return None

    parts: list[types.Part] = []

    # 1. Generate the 1680x1080 4-Panel Tactical Infographic PNG and publish both HTML + PNG to GCS
    png_bytes: bytes | None = None
    try:
        png_bytes = render_india_eez_map_png(pending_fleet)
    except Exception as exc:
        logger.warning("render_india_eez_map_png fallback: %s", exc)

    try:
        publish_interactive_html_map(pending_fleet, surface_id, png_bytes=png_bytes)
    except Exception as exc:
        logger.warning("publish_interactive_html_map fallback: %s", exc)

    # Only attach raw Part.from_bytes when running in local `adk web` (in Gemini Enterprise, raw
    # inline_data renders as a tiny 64px chip, whereas the A2UI Card's 3-Tier VegaChart renders at full 680x860px width).
    if png_bytes and os.path.exists("/usr/local/google/home/zuhaibp"):
        parts.append(types.Part.from_bytes(data=png_bytes, mime_type="image/png"))

    # 2. Attach the Full-Width A2UI v0.9 Card surface (with inlined 3-Tier Bathymetric `spec: vega_spec`,
    #    prominent top/bottom Interactive HTML Map links, Legend, and 5-Column Relocation Table)
    try:
        parts.extend(build_rig_fleet_surface(pending_fleet, surface_id))
    except Exception as exc:
        logger.warning("build_rig_fleet_surface fallback: %s", exc)

    if not parts:
        return None

    logger.info("emit_a2ui_surface: surface=%s parts=%d", surface_id, len(parts))
    return types.Content(role="model", parts=parts)


def strip_fabricated_a2ui(
    callback_context: CallbackContext | None = None,
    llm_response: LlmResponse | None = None,
    **kwargs: Any,
) -> LlmResponse | None:
    """Delete any fabricated A2UI payload and deterministically append the Standout HTML Map & PNG Links to final prose."""
    if llm_response is None or llm_response.content is None:
        return None

    parts = llm_response.content.parts or []
    has_function_call = any(getattr(p, "function_call", None) is not None for p in parts)
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

    # If this is the final text turn (no tool calls), guarantee the standout Interactive HTML Map & PNG links
    # appear right at the bottom of the main chat bubble (above the copy/feedback buttons and A2UI Card).
    if not has_function_call and cleaned:
        last_idx = -1
        for i in range(len(cleaned) - 1, -1, -1):
            if getattr(cleaned[i], "text", None):
                last_idx = i
                break
        if last_idx >= 0:
            existing_text = cleaned[last_idx].text or ""
            if "india_eez_latest.html" not in existing_text:
                cleaned[last_idx] = types.Part(text=existing_text.rstrip() + _build_standout_links_markdown())
                llm_response.content.parts = cleaned
                return llm_response

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
            max_output_tokens=4096,
            temperature=0.0,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
    else:
        llm_request.config.max_output_tokens = 4096
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

Your objective is to communicate with crystal clarity, elegance, and executive brevity to eliminate Non-Productive Time (NPT) (`₹1.0 - ₹1.2 Crore/day` per rig under CAG Performance Audit Report #15117) across 20 offshore rigs and 120 wells in India's EEZ.

FORMATTING & READABILITY RULES (CRITICAL — FOLLOW EXACTLY):
1. **Keep Text Elegantly Formatted, Scannable, and Concise (Never Jumbled or Over-Wordy)**:
   - Do NOT output raw JSON blocks (` ```json ... ``` `).
   - Do NOT repeat the same 6 rigs twice (do NOT write a long 6-bullet paragraph AND a 9-column table—that causes text clutter and column wrapping!).
   - NEVER create a Markdown table with more than **5 columns**! Wide 8–9 column tables wrap into unreadable narrow vertical columns in chat. Always use the **exact 5-Column Executive Table** below.
2. **Always Call `forecast_storm_zones_and_redeployments` First** for any fleet, storm, metocean, or relocation query.
3. **Use This Exact 3-Part Executive Layout**:

   ### 🌊 1. 48-Hour Google WeatherNext (`GenCast` + `GraphCast`) Storm Briefing
   - **🔴 Red Storm Circle 1 (`STORM-ARB-01` — Mumbai High / Western Offshore)**: Cyclone center at `19.35°N, 71.40°E` (`Hs = 4.2m`, Wind `46 kt` — exceeds `2.5m / 35kt` unlatch limit). **4 Rigs (`[1]`–`[4]`) must evacuate immediately.**
   - **🔴 Red Storm Circle 2 (`STORM-BOB-02` — KG-DWN Basin / Eastern Offshore)**: Deepwater swell at `16.25°N, 82.20°E` (`Hs = 3.8m`, Wind `42 kt`). **2 Rigs (`[5]`–`[6]`) must evacuate immediately.**
   - **💰 Fleet Financial Impact (CAG Audit #15117)**: Pre-emptive relocation of Rigs `[1]`–`[6]` achieves **Zero Waiting-on-Weather Downtime** and saves **₹25.43 Crore** in avoided NPT (`14` remaining rigs continue safe drilling in calm basins).

   ### 🧭 2. Master Rig Relocation Directive (`[1]`–`[6]` Matching Map Badges)
   *(Render this exact 5-column table so every row stays crisp and readable without wrapping):*

   | Badge & Rig | Basin | 🔴 Evacuate Storm Well (`Hs`) | 🟢 Relocate to Safe Well (`Hs`) | Transit & Saved |
   | :--- | :--- | :--- | :--- | :--- |
   | **`[1]` Sagar Samrat** (`RIG-04`) | Mumbai High | `WELL-IND-001` (`19.38°N, 71.32°E` · **4.2m**) | **`WELL-IND-004`** (`18.92°N, 71.68°E` · **1.4m**) | **18.4 NM** (`3.3h`) · **₹4.32 Cr** |
   | **`[2]` Sagar Ratna** (`RIG-01`) | Mumbai High | `WELL-IND-002` (`19.48°N, 71.22°E` · **4.1m**) | **`WELL-IND-005`** (`18.84°N, 71.54°E` · **1.3m**) | **21.2 NM** (`3.8h`) · **₹3.95 Cr** |
   | **`[3]` Sagar Bhushan** (`RIG-02`) | Mumbai High | `WELL-IND-003` (`19.26°N, 71.44°E` · **3.9m**) | **`WELL-IND-006`** (`18.78°N, 71.82°E` · **1.5m**) | **24.6 NM** (`4.5h`) · **₹3.68 Cr** |
   | **`[4]` Aban Ice** (`RIG-03`) | Mumbai High | `WELL-IND-007` (`19.54°N, 71.48°E` · **3.7m**) | **`WELL-IND-008`** (`18.98°N, 71.88°E` · **1.4m**) | **19.8 NM** (`3.6h`) · **₹3.45 Cr** |
   | **`[5]` Dhirubhai KG1** (`RIG-05`) | KG-DWN Basin | `WELL-IND-045` (`16.32°N, 82.16°E` · **3.8m**) | **`WELL-IND-048`** (`15.92°N, 82.46°E` · **1.4m**) | **16.5 NM** (`1.8h`) · **₹5.18 Cr** |
   | **`[6]` Platinum Explorer** (`RIG-06`) | KG-DWN Basin | `WELL-IND-046` (`16.42°N, 82.32°E` · **3.7m**) | **`WELL-IND-049`** (`15.84°N, 82.62°E` · **1.3m**) | **19.1 NM** (`2.1h`) · **₹4.85 Cr** |

   ### 🗺️ 3. Quick Map Legend (`Panel A` India EEZ + `Panel B1/B2` Basin Escape Zooms Below)
   - **🔴 Red Circles**: 48h Storm Impact Zones (`DO NOT DRILL`)  ·  **🟡 Yellow Badges `[1]–[6]`**: Threatened Rig Origins  ·  **🟢 Green Arrows (`──➤`)**: Safe Escape Routes  ·  **🟢 Green Diamonds (`◆`)**: Safe Replacement Wells (`Hs = 1.3m–1.5m`).
"""


root_agent = Agent(
    name="rig_navigator_agent",
    description="Offshore Rig Mobilization & Weather Optimizer (ORMWO) — Google WeatherNext (GenCast/GraphCast) 48h Storm Forecasting, Zero-Downtime Well Relocation & Interactive India EEZ Map",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    generate_content_config=types.GenerateContentConfig(
        max_output_tokens=4096,
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

