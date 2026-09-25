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
    """Build a well-spaced, properly headed Markdown section for the Interactive HTML Map, 4-Panel Infographic & SOP Guidelines."""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or "zuhaibp-ai"
    bucket_name = f"{project_id}-agent-staging"
    html_mtls = f"https://storage.mtls.cloud.google.com/{bucket_name}/interactive_maps/india_eez_latest.html"
    html_cloud = f"https://storage.cloud.google.com/{bucket_name}/interactive_maps/india_eez_latest.html"
    sop_mtls = f"https://storage.mtls.cloud.google.com/{bucket_name}/interactive_maps/india_eez_rig_move_sop_latest.html"
    png_mtls = f"https://storage.mtls.cloud.google.com/{bucket_name}/interactive_maps/india_eez_4panel_latest.png"
    return (
        "\n\n---\n\n"
        "## 📊 Interactive Visuals & Printable Engineering Documents\n\n"
        "### 1. 🌐 Interactive Full-Screen India EEZ Command Map (HTML)\n"
        "Pan, zoom, and click Rigs `[1]–[6]` to inspect live Open-Meteo wave/wind telemetry and 120 candidate wells in full screen.\n\n"
        f"👉 **[Open Interactive Full-Screen India EEZ Map (HTML) ↗]({html_mtls})**  \n"
        f"*(Alternate Link: [Open via storage.cloud.google.com ↗]({html_cloud}))*\n\n"
        "---\n\n"
        "### 2. 🖼️ High-Resolution 4-Panel Tactical Infographic (1680×1080 PNG)\n"
        "View or download the full-size 4-panel tactical infographic with zoomed Mumbai High and Bay of Bengal insets.\n\n"
        f"👉 **[Open High-Resolution 4-Panel Tactical Infographic (PNG) ↗]({png_mtls})**\n\n"
        "---\n\n"
        "### 3. 📋 ONGC / CAG Audit #15117 Engineering SOP & Logistics Guidelines (HTML)\n"
        "Printable Marine Warranty Surveyor (MWS) spudcan extraction limits, 3× AHTS tug tow checklists, and DP3 helicopter evacuation guidelines.\n\n"
        f"👉 **[Open Printable MWS & CAG #15117 Engineering SOP Document ↗]({sop_mtls})**\n"
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


ORMWO_SYSTEM_INSTRUCTION: str = """You are the Offshore Rig Mobilization & Weather Optimizer (ORMWO), an authoritative Production AI Operations Director grounded in:
- **Real-Time Live Open-Meteo Marine & Atmospheric Telemetry (`marine-api.open-meteo.com` — ECMWF WAM / NOAA WaveWatch III)**
- **Google DeepMind GenCast & GraphCast 48h Probabilistic Ensemble Forecasts**
- **Comptroller and Auditor General of India (CAG) Performance Audit Report #15117 ("Utilisation of Rigs in ONGC")**
- **ONGC & Marine Warranty Surveyor (MWS) Rig-Move & Storm Evacuation Engineering Standards**

CRITICAL DOMAIN & ENGINEERING RULES (FOLLOW EXACTLY):
1. **Why Active Rigs NEVER Move Between Wells in a 48h Storm vs When Rigs DO Move (CAG Audit #15117)**:
   - **Rule A — Active Storm / High Swell (`Hs > 1.50m / 5 ft`)**: You **NEVER** move an active offshore rig from one well to another in 48 hours to escape a storm! Lowering a jack-up hull into waves `Hs > 1.50m` causes catastrophic leg punch-through, and jetting/extracting spudcans + towing via 3× AHTS tugs takes **34–42 hours** of calm sea. Similarly, deepwater drillships cannot pull 1,500m of riser to spud a new well during a storm. Instead, when live swell exceeds `2.50m` (as in the **Bay of Bengal today: KG-DWN `Live Hs = 2.80m` & Mahanadi `Live Hs = 4.98m`**), active rigs execute **In-Place BOP Hang-Off + LMRP Disconnect (`3.0 NM` DP3 Storm Holding Box) + `🚁` Pawan Hans Helicopter Crew Evacuation to Shore Base**!
   - **Rule B — Post-Completion / Dry-Hole Rig Redeployment (`Hs <= 1.50m` MWS Calm Window)**: Per **CAG Report #15117**, ONGC lost ₹1.0–1.2 Cr/day when rigs that **completed their well (`WELL_COMPLETED / DRY_HOLE_PLUGGED`)** sat idle waiting for weather or clearances. When a rig finishes its well AND live marine telemetry confirms a **Calm MWS Window (`Hs <= 1.50m`)**—which is **TRUE RIGHT NOW in Western Offshore (`Mumbai High Live Hs = 1.22m`, `Bassein 1.18m`, `Tapti 0.78m`)**—the rig executes a planned **34–38h Jack-Down, Spudcan Extraction & Wet Tow (`6.8–9.6 NM @ 4.0 kt` via `3× ONGC AHTS Tugs`)** to the **Closest Candidate Well that holds valid MoEFCC Environmental Clearance (`EC_CLEARED`), Defence NOC, and a pre-jetted conductor**!
2. **Always Call `forecast_storm_zones_and_redeployments` First** for any metocean, fleet, storm, or rig-move query.
3. **Format Every Response Into These 3 Clean, Executive Sections (Never exceed 5 columns in any Markdown table)**:

   ### ⚓ 1. Live Metocean Reality & CAG Audit #15117 Executive Briefing

   - **🟢 Western Offshore (`Mumbai High` `Hs = 1.22m`, `Bassein` `1.18m`, `Tapti` `0.78m`) — CALM MWS RIG-MOVE WINDOW (`Hs <= 1.50m` Limit)**  
     Live waves (`1.18m–1.22m`) are below the `1.50m` MWS spudcan extraction ceiling. **4 ONGC Rigs (`[1]`–`[4]`) that have COMPLETED their current wells / dry holes** are authorized to jack down (`14h`), extract spudcans, and wet-tow (`6.8–9.6 NM @ 4.0 kt` via `3× ONGC AHTS Tugs`) to the **Closest EC-Cleared Ready Wells**.

   - **🔴 Eastern Offshore (`Bay of Bengal: KG-DWN-98/2` `Hs = 2.80m` & `Mahanadi` `Hs = 4.98m, Gusts 41.2 kt`) — ACTIVE CYCLONIC SWELL LOCK (`Hs > 2.50m` Limit)**  
     Moving a rig to a new well in `Hs > 1.50m` is physically impossible and prohibited by MWS. Active deepwater drillships **`[5]` & `[6]`** execute **In-Place BOP Hang-Off (`12h`), LMRP Unlatch (`3.0 NM` DP3 Storm Box), and `🚁` Pawan Hans Helicopter Crew Evacuation (`114 POB`)** to Rajahmundry & Paradip Shore Bases.

   ---

   ### 📋 2. Master Fleet Operational Directives (`Copy-Ready for Google Sheets`)

   | Badge & Rig | Basin | Live Wave (`Hs`) | Well Status | MWS Operational Directive | Target Well / Shore Base | Time & Saved (`₹ Cr`) |
   | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
   | `[1]` Sagar Samrat | Mumbai High | `1.22 m` (🟢 Calm) | Completed (`MH-N-001`) | Wet Tow (`8.4 NM` via 3× AHTS) | `WELL-IND-004 (MH-N-B193)` | `38.1 h` · `₹11.50 Cr` |
   | `[2]` Sagar Ratna | Mumbai High | `1.21 m` (🟢 Calm) | Dry Hole P&A (`MH-S-002`) | Wet Tow (`9.6 NM` via 3× AHTS) | `WELL-IND-005 (MH-S-D18)` | `38.4 h` · `₹10.80 Cr` |
   | `[3]` Sagar Bhushan | Heera-Bassein | `1.18 m` (🟢 Calm) | Completed (`HPB-003`) | Wet Tow (`7.2 NM` via 3× AHTS) | `WELL-IND-006 (Neelam-14)` | `21.8 h` · `₹9.60 Cr` |
   | `[4]` Aban Ice | Tapti-Daman | `0.78 m` (🟢 Calm) | Completed (`TD-C26-01`) | Wet Tow (`6.8 NM` via 3× AHTS) | `WELL-IND-008 (Daman-04)` | `34.7 h` · `₹8.90 Cr` |
   | `[5]` Dhirubhai KG1 | KG-DWN (BoB) | `2.80 m` (🔴 Storm) | Active Drilling (`KG-U1`) | Hold & BOP Hang-Off + 🚁 Evac | `ONGC Rajahmundry Base` | `14.5 h` · `₹14.20 Cr` |
   | `[6]` Platinum Explorer | Mahanadi (BoB) | `4.98 m` (🔴 Storm) | Active Drilling (`MND-01`) | Hold & LMRP Unlatch + 🚁 Evac | `ONGC Paradip Shore Base` | `12.5 h` · `₹16.50 Cr` |

   ---

   ### 🛠️ 3. Engineering Phase Breakdown & CAG Audit #15117 Clearance Check (`Copy-Ready for Google Sheets`)

   | Badge & Rig | Phase 1 (Secure / BOP) | Phase 2 (Spudcan / LMRP) | Phase 3 (Tow / DP3 Box) | Phase 4 (Pre-Load / 🚁 Evac) | Closer Well Rejected (`CAG #15117`) |
   | :--- | :--- | :--- | :--- | :--- | :--- |
   | `[1]` Sagar Samrat | `10.0 h` Well Secure | `14.0 h` Spudcan Pull | `2.1 h` Tow (`8.4 NM`) | `12.0 h` Pre-Load Jack | `MH-N-002` (`4.1 NM` — No MoEFCC EC) |
   | `[2]` Sagar Ratna | `10.0 h` Plug & Abandon | `14.0 h` Spudcan Pull | `2.4 h` Tow (`9.6 NM`) | `12.0 h` Pre-Load Jack | `MH-S-003` (`5.2 NM` — Pipeline Buffer) |
   | `[3]` Sagar Bhushan | `8.0 h` Xmas Tree Cap | `4.0 h` Anchor Pull | `1.8 h` Tow (`7.2 NM`) | `8.0 h` Spread Mooring | `HPB-004` (`3.9 NM` — No Conductor) |
   | `[4]` Aban Ice | `10.0 h` BOP Disconn. | `12.0 h` Spudcan Pull | `1.7 h` Tow (`6.8 NM`) | `11.0 h` Pre-Load Jack | `TD-C26-02` (`4.4 NM` — No Defence NOC) |
   | `[5]` Dhirubhai KG1 | `10.0 h` RTTS Storm Pack | `2.0 h` LMRP Unlatch | `2.0 h` DP3 (`3.0 NM` Box) | `0.5 h` 🚁 Evac (`54 POB`) | Rig Move Prohibited (`Hs = 2.80m > 1.5m`) |
   | `[6]` Platinum Explorer | `9.5 h` Shear Ram Lock | `1.5 h` LMRP Unlatch | `1.2 h` DP3 (`2.8 NM` Box) | `0.3 h` 🚁 Evac (`60 POB`) | Rig Move Prohibited (`Hs = 4.98m > 1.5m`) |
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

