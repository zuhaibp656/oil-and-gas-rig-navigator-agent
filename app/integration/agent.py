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
    """Build a well-spaced, properly headed Markdown section for the Interactive HTML Map, 4-Panel Infographic, SOP Guidelines & Executive Deck."""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or "zuhaibp-ai"
    bucket_name = f"{project_id}-agent-staging"
    html_mtls = f"https://storage.mtls.cloud.google.com/{bucket_name}/interactive_maps/india_eez_latest.html"
    html_cloud = f"https://storage.cloud.google.com/{bucket_name}/interactive_maps/india_eez_latest.html"
    sop_mtls = f"https://storage.mtls.cloud.google.com/{bucket_name}/interactive_maps/india_eez_rig_move_sop_latest.html"
    png_mtls = f"https://storage.mtls.cloud.google.com/{bucket_name}/interactive_maps/india_eez_4panel_latest.png"
    deck_mtls = f"https://storage.mtls.cloud.google.com/{bucket_name}/interactive_maps/ormwo_executive_presentation.html"
    deck_cloud = f"https://storage.cloud.google.com/{bucket_name}/interactive_maps/ormwo_executive_presentation.html"
    return (
        "\n\n---\n\n"
        "## 📊 Executive Visual Artifacts & Printable Engineering Documents\n\n"
        "### 1. 🌐 Interactive Full-Screen India EEZ Command Map (HTML)\n"
        "Explore real-time bathymetry, 20 rigs, 120 candidate wells, live Open-Meteo telemetry, and click-to-fly relocation corridors in full screen.\n\n"
        f"👉 **[Open Interactive Full-Screen India EEZ Map (HTML) ↗]({html_mtls})**  \n"
        f"*(Mirror: [Open via storage.cloud.google.com ↗]({html_cloud}))*\n\n"
        "---\n\n"
        "### 2. 🖼️ High-Resolution Tactical Infographic (1680×1080 PNG)\n"
        "Minimalist Google Cloud design featuring strategic EEZ theater map, Mumbai High & Bay of Bengal insets, and executive unit directives.\n\n"
        f"👉 **[Open High-Resolution Tactical Infographic (PNG) ↗]({png_mtls})**\n\n"
        "---\n\n"
        "### 3. 📑 Executive Briefing & Transformation Deck (Interactive HTML)\n"
        "Modern light-minimalist presentation deck with animated slide navigator, architecture blueprints, CAG Audit metrics, and live telemetry.\n\n"
        f"👉 **[Open Executive Briefing & Transformation Deck (HTML) ↗]({deck_mtls})**  \n"
        f"*(Mirror: [Open via storage.cloud.google.com ↗]({deck_cloud}))*\n\n"
        "---\n\n"
        "### 4. 📋 ONGC / CAG Audit #15117 Engineering SOP & Logistics Guidelines (HTML)\n"
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
     Live waves (`0.78m–1.22m`) are well within the `1.50m` MWS spudcan extraction ceiling. **4 ONGC Units (`[1]`–`[4]`) that completed their wells / dry holes** are cleared for planned jack-down, spudcan extraction, and wet tow (`6.8–9.6 NM @ 4.0 kt` via `3× ONGC AHTS Tugs`) to **Closest EC-Cleared Ready Wells**.

   - **🔴 Eastern Offshore (`Bay of Bengal: KG-DWN-98/2` `Hs = 2.80m` & `Mahanadi` `Hs = 4.98m, Gusts 41.2 kt`) — ACTIVE CYCLONIC SWELL LOCK (`Hs > 2.50m` Limit)**  
     Moving an active rig to a new well during high swell is physically prohibited by MWS. Deepwater drillships **`[5]` & `[6]`** execute **In-Place BOP Hang-Off, LMRP Disconnect into a `3.0 NM` DP3 Storm Box, and `🚁` Pawan Hans Helicopter Crew Evacuation (`114 POB`)** to Rajahmundry & Paradip Shore Bases.

   ---

   ### 🧭 2. Tactical Mobilization & Voyage Directives (Detailed Operational Cards)

   #### `[1]` Sagar Samrat (Jack-Up Rig) — Mumbai High North
   - **Operational Mode**: Post-Completion Rig Move (Target Depth 3,280m reached & cased).
   - **Departure Window & Sea State**: Immediate 36h Calm Window (`Live Hs = 1.22m`, Wind 16.6 kt — safe below 1.50m MWS limit).
   - **Transit Corridor**: `MH-N-001` (19.38° N, 71.32° E) ➔ `WELL-IND-004` / MH-N-B193 (19.26° N, 71.44° E) | `8.4 NM @ 142° SE`.
   - **Tow Spread & Mechanics**: 3× ONGC 150T AHTS Tugs (*Sindhu-14/16/19*) in Delta formation | Tow speed 4.0 kt | Spudcan jetting at 120 bar.
   - **Multi-Phase Timeline**: Secure/BOP `10.0h` ➔ Spudcan extraction `14.0h` ➔ Underway tow `2.1h` ➔ Pinning & preload `12.0h` | **Total: 38.1h**.
   - **Capital & Compliance**: **₹11.50 Cr Avoided NPT** | Closer well `MH-N-002` (4.1 NM) rejected due to pending MoEFCC clearance per CAG #15117.

   #### `[2]` Sagar Ratna (Jack-Up Rig) — Mumbai High South
   - **Operational Mode**: Dry Hole Redeployment (Plug & Abandonment cement plugs set).
   - **Departure Window & Sea State**: Immediate Calm Window (`Live Hs = 1.21m`, Wind 16.2 kt).
   - **Transit Corridor**: `MH-S-002` (19.18° N, 71.36° E) ➔ `WELL-IND-005` / MH-S-D18 (19.04° N, 71.48° E) | `9.6 NM @ 139° SE`.
   - **Tow Spread & Mechanics**: 3× ONGC AHTS Tugs | Tow speed 4.0 kt | 16m clay penetration extraction with bottom jetting.
   - **Multi-Phase Timeline**: Plug verification `10.0h` ➔ Spudcan pull `14.0h` ➔ Underway tow `2.4h` ➔ Pinning & preload `12.0h` | **Total: 38.4h**.
   - **Capital & Compliance**: **₹10.80 Cr Avoided NPT** | Closer well `MH-S-003` (5.3 NM) rejected (subsea pipeline crossing lacks 500m MWS buffer).

   #### `[3]` Sagar Bhushan (Floater / Drillship) — Heera-Panna-Bassein
   - **Operational Mode**: Production Well Completed (Xmas tree installed, rig released).
   - **Departure Window & Sea State**: Immediate Window (`Live Hs = 1.18m`, Wind 17.0 kt).
   - **Transit Corridor**: `HPB-003` (18.78° N, 72.08° E) ➔ `WELL-IND-006` / Neelam-14 (18.66° N, 72.18° E) | `7.2 NM @ 140° SE`.
   - **Tow Spread & Mechanics**: 8-Point Spread Mooring Anchor handling via 2× AHTS | Field transit @ 4.0 kt.
   - **Multi-Phase Timeline**: BOP recovery `8.0h` ➔ Anchor recovery `4.0h` ➔ Transit `1.8h` ➔ Spread mooring reset `8.0h` | **Total: 21.8h**.
   - **Capital & Compliance**: **₹9.60 Cr Avoided NPT** | Closer well `HPB-004` (3.8 NM) rejected (awaiting conductor jetting vessel).

   #### `[4]` Aban Ice (Jack-Up Rig) — Tapti-Daman Sector
   - **Operational Mode**: New Campaign Deployment (Testing completed at TD-C26-01).
   - **Departure Window & Sea State**: Ultra-calm window (`Live Hs = 0.78m`, Wind 11.3 kt).
   - **Transit Corridor**: `TD-C26-01` (20.78° N, 71.88° E) ➔ `WELL-IND-008` / Daman-04 (20.66° N, 71.82° E) | `6.8 NM @ 207° SW`.
   - **Tow Spread & Mechanics**: 3× ONGC AHTS Tugs | Tow speed 4.0 kt | Spudcan jetting at 110 bar.
   - **Multi-Phase Timeline**: Deck sea-fastening `10.0h` ➔ Spudcan pull `12.0h` ➔ Underway tow `1.7h` ➔ Preload jack `11.0h` | **Total: 34.7h**.
   - **Capital & Compliance**: **₹8.90 Cr Avoided NPT** | Closer well `TD-C26-02` (2.9 NM) rejected (pending Naval Hydrographic NOC).

   #### `[5]` Dhirubhai Deepwater KG1 (DP3 Drillship) — KG-DWN-98/2
   - **Operational Mode**: In-Place Well Hang-Off & 🚁 Crew Evacuation (Active deepwater drilling @ 2,840m).
   - **Sea State & Storm Alert**: 🔴 Severe Swell Lock (`Live Hs = 2.80m`, Peak 3.10m, Gusts 36.5 kt — Rig Move Prohibited).
   - **Hold & Evacuation Corridor**: `WELL-IND-045` (16.32° N, 82.16° E) ➔ 3.0 NM DP3 Storm Holding Box + `🚁` Evacuation to Kakinada Base (38 NM).
   - **Operational Mechanics**: RTTS storm packer set, drill pipe hung off in subsea BOP shear rams (12h) | LMRP unlatched in 45s | DP3 weather-vaning into 210° swell | 2× Pawan Hans AW139 helicopters evacuate 54 non-essential crew.
   - **Timeline & Capital**: Hang-off `10.0h` ➔ LMRP unlatch `2.0h` ➔ DP3 station `2.0h` ➔ 🚁 Evacuation `0.5h` | **Total: 14.5h** | **₹14.20 Cr Saved**.

   #### `[6]` Platinum Explorer (DP3 Drillship) — Mahanadi Deepwater
   - **Operational Mode**: Emergency LMRP Unlatch & 🚁 Crew Evacuation (Active drilling @ 3,110m).
   - **Sea State & Storm Alert**: 🔴 Cyclonic Depression Alert (`Live Hs = 4.98m`, Gusts 41.2 kt — Extreme Ocean Risk).
   - **Hold & Evacuation Corridor**: `WELL-IND-046` (19.85° N, 86.75° E) ➔ 2.8 NM DP3 Storm Holding Box + `🚁` Evacuation to Paradip Base (25 NM).
   - **Operational Mechanics**: Emergency Disconnect Sequence (EDS) initiated | Shear ram lock on drill string | DP3 thrusters heading into 224° swell | Pawan Hans helicopter evacuation of 60 crew.
   - **Timeline & Capital**: Hang-off `9.5h` ➔ LMRP unlatch `1.5h` ➔ DP3 station `1.2h` ➔ 🚁 Evacuation `0.3h` | **Total: 12.5h** | **₹16.50 Cr Saved**.

   ---

   ### 📋 3. Master Fleet Relocation Ledger (`Copy-Ready for Google Sheets`)

   | Unit & Basin | Operational Directive | Transit Corridor (From ➔ To) | Tow Spread & Speed | Multi-Phase Time & Saved |
   | :--- | :--- | :--- | :--- | :--- |
   | `[1]` Sagar Samrat (Mumbai High N) | 🟢 Wet Tow (Completed Well) | `MH-N-001` ➔ `WELL-IND-004` (8.4 NM) | 3× AHTS Tugs @ 4.0 kt | `38.1 h` · `₹11.50 Cr` |
   | `[2]` Sagar Ratna (Mumbai High S) | 🟢 Wet Tow (Dry Hole P&A) | `MH-S-002` ➔ `WELL-IND-005` (9.6 NM) | 3× AHTS Tugs @ 4.0 kt | `38.4 h` · `₹10.80 Cr` |
   | `[3]` Sagar Bhushan (Bassein) | 🟢 Field Move (Completed Well) | `HPB-003` ➔ `WELL-IND-006` (7.2 NM) | 8-Pt Mooring @ 4.0 kt | `21.8 h` · `₹9.60 Cr` |
   | `[4]` Aban Ice (Tapti-Daman) | 🟢 Wet Tow (New Campaign) | `TD-C26-01` ➔ `WELL-IND-008` (6.8 NM) | 3× AHTS Tugs @ 4.0 kt | `34.7 h` · `₹8.90 Cr` |
   | `[5]` Dhirubhai KG1 (KG-DWN BoB) | 🔴 Hold & LMRP Unlatch + 🚁 Evac | `KG-DWN-U1` ➔ 3 NM DP3 Box / Kakinada | DP3 Dynamic Pos. / AW139 | `14.5 h` · `₹14.20 Cr` |
   | `[6]` Platinum Explorer (Mahanadi BoB) | 🔴 Emergency EDS + 🚁 Evac | `MND-OSN-01` ➔ 2.8 NM DP3 Box / Paradip | DP3 Dynamic Pos. / AW139 | `12.5 h` · `₹16.50 Cr` |
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

