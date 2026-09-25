"""A2UI v0.9 component tree for ORMWO India EEZ Live Metocean, MWS Rig-Move & Storm Evacuation Card.

Grounds the visual dashboard in:
1) Real-Time Live Open-Meteo Marine Telemetry (Mumbai High `Hs=1.22m` Green MWS Rig-Move Window vs
   Bay of Bengal `Hs=2.80m-4.98m` Red Cyclonic Swell Lock).
2) Real Offshore Petroleum Engineering & CAG Audit Report #15117 Compliance:
   - Rigs [1]–[4] (Completed/Dry Wells in Calm Western Offshore `Hs <= 1.50m`): Wet Tow (6.8–9.6 NM @ 4.0 kt
     via 3× AHTS Tugs) to Closest EC-Cleared Ready Wells.
   - Rigs [5]–[6] (Active Deepwater Drilling in Stormy Bay of Bengal `Hs = 2.80m–4.98m`): Rig Move Prohibited!
     In-Place BOP Hang-Off + LMRP Unlatch (3 NM DP3 Holding Box) + Pawan Hans Helicopter Crew Evacuation (🚁).
3) Standout Top & Bottom Clickable Links for the Interactive HTML Map, Engineering SOP Guidelines Document, and 4-Panel PNG.
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
        "| Badge & Rig | Current Well & Live Sea State | Operational Directive (`MWS / CAG #15117`) | Target Well / 🚁 Shore Base | Total Time & Saved |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in rows:
        is_move = r["idx"] <= 4
        action_str = (
            f"🟢 **Wet Tow ({r['dist_nm']} NM @ 4kt)** via 3× AHTS Tugs"
            if is_move
            else "🔴 **NO RIG MOVE (`Hs>1.5m`)** · BOP Hang-Off + 🚁 Crew Evac"
        )
        lines.append(
            f"| **`[{r['idx']}]` {r['rig_name']}** | `{r['orig_well']}` (`Live Hs={r['storm_hs']}m, {r['storm_wind']}kt`) | "
            f"{action_str} | **`{r['dest_well']}`** | "
            f"**{r.get('total_op_hrs', r['transit_hrs'])}h** · **₹{r['savings_cr']:.2f} Cr** |"
        )
    return "\n".join(lines)


def build_rig_fleet_components(summary: FleetSummary) -> list[dict[str, Any]]:
    """Build the A2UI v0.9 component hierarchy containing ONLY the visual interactive infographic.

    All text briefings, copy-ready Google Sheets tables, and properly headed links are emitted
    outside in the main Markdown response so users can easily read, copy, and paste them.
    """
    children: list[str] = []
    components: list[dict[str, Any]] = []

    def add(component: dict[str, Any]) -> None:
        components.append(component)
        children.append(component["id"])

    wells = summary.wells or INDIA_120_WELL_REGISTRY
    vega_spec = build_rig_fleet_map_spec(summary)

    add(
        _text(
            "rfc-title",
            "ORMWO — India EEZ Live Metocean & MWS Tactical Infographic",
            "h4",
        )
    )
    add(
        _text(
            "rfc-subtitle",
            (
                f"🟢 Western Offshore Calm MWS Window (Hs = 1.18m–1.22m <= 1.50m — Rigs [1]–[4] Wet Tow)  ·  "
                f"🔴 Bay of Bengal Swell Lock (Hs = 2.80m–4.98m — Rigs [5]–[6] BOP Hang-Off & 🚁 Evac)  ·  "
                f"{summary.total_rigs} Rigs & {len(wells)} Wells"
            ),
            "caption",
        )
    )

    # Pure visual interactive infographic inside the card rendering (no cramped text tables inside the card)
    chart_comp = {
        "id": "rfc-chart-vega",
        "component": "VegaChart",
        "spec": vega_spec,
        "height": 860,
    }
    components.append(chart_comp)
    children.append("rfc-chart-vega")

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

