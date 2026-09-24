"""A2UI v0.9 component tree for ORMWO India EEZ Map, 48h Weather & Rig Mobilization Card.

Matches the `ppac-energy-intelligence-agent` interactive Card box pattern:
1) Inlines `"spec": vega_spec` directly on the `VegaChart` component (in addition to `updateDataModel`).
2) Embeds the Visual Map Legend, Numbered Rig Relocation Index Table ([1]–[6]), and CAG #15117
   Financial KPI summary directly inside the A2UI `Card` -> `Column` container.
"""

from __future__ import annotations

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
        "| Map Index | Rig ID & Name | Basin | Origin Storm-Locked Well (🔴 Avoid) | 48h Storm Peak | Safe Target Well (🟢 Relocate Here) | Distance / Transit | Safe Wave | Avoided NPT Saved |",
        "| :---: | :--- | :--- | :--- | :---: | :--- | :---: | :---: | :---: |",
    ]
    for r in rows:
        lines.append(
            f"| **[{r['idx']}]** | **{r['rig_id']}** ({r['rig_name']}) | {r['basin']} | "
            f"🔴 `{r['orig_well']}` ({r['orig_lat']:.2f}°N, {r['orig_lon']:.2f}°E) | "
            f"`Hs={r['storm_hs']}m, {r['storm_wind']}kt` | "
            f"🟢 **`{r['dest_well']}`** ({r['dest_lat']:.2f}°N, {r['dest_lon']:.2f}°E) | "
            f"**{r['dist_nm']:.1f} NM** ({r['transit_hrs']:.1f}h) | `Hs={r['safe_hs']}m` | "
            f"**₹{r['savings_cr']:.2f} Cr** |"
        )
    return "\n".join(lines)


def build_rig_fleet_components(summary: FleetSummary) -> list[dict[str, Any]]:
    """Build the A2UI v0.9 component hierarchy for the ORMWO India EEZ Map & Decision Card."""
    children: list[str] = []
    components: list[dict[str, Any]] = []

    def add(component: dict[str, Any]) -> None:
        components.append(component)
        children.append(component["id"])

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
    add({"id": "rfc-div-1", "component": "Divider"})

    # Inline `vega_spec` directly on VegaChart (matching `ppac-energy-intelligence-agent`)
    # so Gemini Enterprise renders the interactive chart box natively.
    chart_comp = {
        "id": "rfc-chart-vega",
        "component": "VegaChart",
        "spec": vega_spec,
        "height": 520,
    }
    components.append(chart_comp)
    children.append("rfc-chart-vega")
    add({"id": "rfc-div-2", "component": "Divider"})

    # Section 1: Visual Legend & Symbol Key
    add(_text("rfc-legend-hdr", "Visual Map Legend & Symbol Key (How to Read the Map)", "h5"))
    add(
        _text(
            "rfc-legend-body",
            (
                "• **🔴 Large Red Dashed Circle (`STORM-ARB-01` & `STORM-BOB-02`)**: "
                "48-Hour Storm Impact Zone (`GenCast` + `GraphCast` Peak Wave `Hs > 2.5m`, Wind `> 35kt` — **DO NOT DRILL**)  \n"
                "• **🔴 Red Solid Dot (`●`)**: `STORM_LOCKED` Origin Well inside the storm cone (unsafe to spud or stay unlatched)  \n"
                "• **🟡 Yellow Triangle / Badge (`[1]–[6]`)**: Storm-Threatened Offshore Rig Origin (matches the Relocation Index Table below)  \n"
                "• **🟢 Green Dashed Line (`━➤`)**: Monte Carlo Preventative Relocation Route out of the red storm circle (zero downtime)  \n"
                "• **🟢 Green Circle / Diamond (`◆`)**: Recommended `SAFE_READY_TO_SPUD` Replacement Well outside the storm cone (`Hs = 1.3m–1.5m`)"
            ),
            "body",
        )
    )
    add({"id": "rfc-div-3", "component": "Divider"})

    # Section 2: Numbered Rig Relocation Index Table ([1] to [6])
    add(_text("rfc-table-hdr", "Numbered Rig Relocation Index [1]–[6] (Origin Storm-Locked Well ➔ Safe Target Well)", "h5"))
    add(_text("rfc-table-body", _build_relocation_markdown_table(), "body"))

    if summary.audit_reference_id:
        add({"id": "rfc-div-4", "component": "Divider"})
        add(
            _text(
                "rfc-audit-footer",
                f"CAG Performance Audit Report #15117 Governance Reference: `{summary.audit_reference_id}`",
                "caption",
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
