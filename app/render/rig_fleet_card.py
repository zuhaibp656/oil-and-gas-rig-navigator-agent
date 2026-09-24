"""A2UI v0.9 component tree for ORMWO India EEZ Map, 48h Weather & Rig Mobilization Card.

Matches the `ppac-energy-intelligence-agent` interactive Card box pattern:
1) Inlines `"spec": vega_spec` directly on the `VegaChart` component (3-Tier Full-Width Bathymetric Dashboard).
2) Embeds Standout Clickable Links for the Interactive Full-Screen HTML Command Map & 1680x1080 PNG Infographic
   at BOTH the top and bottom of the A2UI Card.
3) Embeds a clean, scannable 5-Column Relocation Index Table ([1]–[6]) and Visual Legend inside the Card.
"""

from __future__ import annotations

import os
from typing import Any

try:
    from app.contracts import FleetSummary, WellReadinessStatus
    from app.render.india_map_png import _get_six_relocation_rows
    from app.render.rig_map_vega import build_rig_fleet_map_spec
    from app.rigs.india_eez_dataset import INDIA_120_WELL_REGISTRY
except ImportError:
    from contracts import FleetSummary, WellReadinessStatus
    from render.india_map_png import _get_six_relocation_rows
    from render.rig_map_vega import build_rig_fleet_map_spec
    from rigs.india_eez_dataset import INDIA_120_WELL_REGISTRY

ROOT_CARD_ID: str = "root"
ROOT_COLUMN_ID: str = "rig-fleet-column"


def _text(component_id: str, text: str, variant: str = "body") -> dict[str, Any]:
    return {
        "id": component_id,
        "component": "Text",
        "text": text,
        "variant": variant,
    }


def _build_relocation_markdown_table() -> str:
    rows = _get_six_relocation_rows()
    lines = [
        "| Badge & Rig | Basin | 🔴 Evacuate Storm-Locked Well (`Hs`) | 🟢 Relocate to Safe Target Well (`Hs`) | Transit & NPT Saved |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in rows:
        lines.append(
            f"| **`[{r['idx']}]` {r['rig_name']}** (`{r['rig_id']}`) | {r['basin']} | "
            f"🔴 `{r['orig_well']}` ({r['orig_lat']:.2f}°N, {r['orig_lon']:.2f}°E · **`{r['storm_hs']}m`**) | "
            f"🟢 **`{r['dest_well']}`** ({r['dest_lat']:.2f}°N, {r['dest_lon']:.2f}°E · **`{r['safe_hs']}m`**) | "
            f"**{r['dist_nm']:.1f} NM** (`{r['transit_hrs']:.1f}h`) · **₹{r['savings_cr']:.2f} Cr** |"
        )
    return "\n".join(lines)


def build_rig_fleet_components(summary: FleetSummary) -> list[dict[str, Any]]:
    """Build the A2UI v0.9 component hierarchy for the ORMWO India EEZ Map & Decision Card."""
    children: list[str] = []
    components: list[dict[str, Any]] = []

    def add(component: dict[str, Any]) -> None:
        components.append(component)
        children.append(component["id"])

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or "zuhaibp-ai"
    bucket_name = f"{project_id}-agent-staging"
    html_mtls_url = f"https://storage.mtls.cloud.google.com/{bucket_name}/interactive_maps/india_eez_latest.html"
    html_cloud_url = f"https://storage.cloud.google.com/{bucket_name}/interactive_maps/india_eez_latest.html"
    png_mtls_url = f"https://storage.mtls.cloud.google.com/{bucket_name}/interactive_maps/india_eez_4panel_latest.png"

    wells = summary.wells or INDIA_120_WELL_REGISTRY
    safe_well_count = sum(1 for w in wells if w.status == WellReadinessStatus.SAFE_READY_TO_SPUD)
    storm_well_count = sum(1 for w in wells if w.status == WellReadinessStatus.STORM_LOCKED)
    vega_spec = build_rig_fleet_map_spec(summary)

    add(
        _text(
            "rfc-title",
            "ORMWO — Google DeepMind GenCast & GraphCast 48h Storm & Safe-Well Relocation Dashboard",
            "h4",
        )
    )
    add(
        _text(
            "rfc-subtitle",
            (
                f"India EEZ Operations: {summary.total_rigs} Offshore Rigs  ·  {len(wells)} Candidate & Active Wells "
                f"({safe_well_count} Metocean-Safe, {storm_well_count} Storm-Locked)  ·  "
                "6 Storm-Threatened Rigs Indexed [1]–[6]  ·  Total Avoided NPT Savings: ₹25.43 Crore"
            ),
            "caption",
        )
    )

    # Prominent Top Action Bar for Full-Screen Interactive HTML Map & 4-Panel High-Res PNG
    add(
        _text(
            "rfc-top-links",
            (
                f"🌐 **[🚀 CLICK HERE TO LAUNCH FULL-SCREEN INTERACTIVE BATHYMETRIC HTML MAP (Leaflet + Click-to-Fly [1]–[6]) ↗]({html_mtls_url})**  \n"
                f"🔗 *Alternate Direct Links:* [**Open Interactive HTML Map (Standard URL) ↗**]({html_cloud_url})  ·  "
                f"[**Open Full-Resolution 1680×1080 4-Panel PNG Infographic ↗**]({png_mtls_url})"
            ),
            "body",
        )
    )
    add({"id": "rfc-div-1", "component": "Divider"})

    # Inline Full-Width 3-Tier Bathymetric `vega_spec` directly on VegaChart
    chart_comp = {
        "id": "rfc-chart-vega",
        "component": "VegaChart",
        "spec": vega_spec,
        "height": 860,
    }
    components.append(chart_comp)
    children.append("rfc-chart-vega")
    add({"id": "rfc-div-2", "component": "Divider"})

    # Section 1: Visual Legend & Symbol Key
    add(_text("rfc-legend-hdr", "Visual Map Legend & Symbol Key (How to Read Panel A & Panel B1/B2)", "h5"))
    add(
        _text(
            "rfc-legend-body",
            (
                "• **🔴 Red Shaded Circles (`STORM-ARB-01` Mumbai High & `STORM-BOB-02` KG-DWN)**: "
                "48-Hour Storm Impact Zones (`GenCast` + `GraphCast` Peak Wave `Hs = 3.8m–4.2m`, Wind `42–46kt` — **DO NOT DRILL**)  \n"
                "• **🟡 Yellow Numbered Circles (`[1]`–`[6]`)**: Storm-Threatened Offshore Rig Origins inside the Red Storm Circles  \n"
                "• **🟢 Bold Green Lines (`──➤`)**: Zero-Downtime Preventative Relocation Routes out of the storm zone  \n"
                "• **🟢 Green Diamonds (`◆`)**: Recommended `SAFE_READY_TO_SPUD` Replacement Wells in calm waters (`Hs = 1.3m–1.5m`)"
            ),
            "body",
        )
    )
    add({"id": "rfc-div-3", "component": "Divider"})

    # Section 2: Clean 5-Column Relocation Index Table ([1] to [6])
    add(_text("rfc-table-hdr", "Numbered Rig Relocation Index [1]–[6] (Origin Storm-Locked Well ➔ Safe Target Well)", "h5"))
    add(_text("rfc-table-body", _build_relocation_markdown_table(), "body"))
    add({"id": "rfc-div-4", "component": "Divider"})

    # Prominent Bottom Call-to-Action Button/Banner for Interactive HTML Map
    add(
        _text(
            "rfc-bottom-cta-hdr",
            "🌐 Full-Screen Interactive Command Map & High-Resolution Infographic",
            "h5",
        )
    )
    add(
        _text(
            "rfc-bottom-cta-body",
            (
                f"👉 **[🚀 LAUNCH INTERACTIVE FULL-SCREEN BATHYMETRIC HTML COMMAND MAP (Click-to-Fly Rigs [1]–[6] + Satellite/Ocean Layers) ↗]({html_mtls_url})**  \n"
                f"👉 **[🖼️ VIEW FULL-SIZE 1680×1080 4-PANEL COMMAND INFOGRAPHIC (PNG) ↗]({png_mtls_url})**  \n"
                f"*(CAG Performance Audit Report #15117 Governance Reference: `{summary.audit_reference_id or 'CAG-15117-EEZ-2026'}`)*"
            ),
            "body",
        )
    )

    root_card = {
        "id": ROOT_CARD_ID,
        "component": "Card",
        "child": ROOT_COLUMN_ID,
    }
    column = {
        "id": ROOT_COLUMN_ID,
        "component": "Column",
        "children": children,
    }

    return [root_card, column, *components]
