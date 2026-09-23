"""A2UI v0.9 component tree for ORMWO India EEZ Map, 48h Weather & Rig Mobilization Card.

Renders the interactive Map of India, 20 rigs, 120 candidate wells, 48h storm alerts,
and Monte Carlo redeployment coordinates directly in Gemini Enterprise chat.
"""

from __future__ import annotations

from typing import Any

try:
    from app.contracts import FleetSummary, WellReadinessStatus
    from app.render.rig_map_vega import SPEC_POINTER
    from app.rigs.india_eez_dataset import INDIA_120_WELL_REGISTRY
except ImportError:
    from contracts import FleetSummary, WellReadinessStatus
    from render.rig_map_vega import SPEC_POINTER
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

    add(_text("rfc-title", "ORMWO — India EEZ Offshore Rig & 48h Weather Optimizer", "h3"))
    add(
        _text(
            "rfc-subtitle",
            (
                f"India EEZ Theater: {summary.total_rigs} Rigs  ·  {len(wells)} Candidate/Active Wells "
                f"({safe_well_count} Metocean-Safe, {storm_well_count} Storm-Locked)"
            ),
            "caption",
        )
    )
    add({"id": "rfc-div-1", "component": "Divider"})

    # Interactive 2-Panel Vega Map of India + 48h Weather Forecast
    chart_comp = {
        "id": "rfc-chart-vega",
        "component": "VegaChart",
        "spec": {"path": SPEC_POINTER},
        "height": 470,
    }
    components.append(chart_comp)
    children.append("rfc-chart-vega")
    add({"id": "rfc-div-2", "component": "Divider"})

    # If a specific ORMWO strict assessment or transit simulation was executed, show directive summary
    if summary.transit_simulations:
        sim = summary.transit_simulations[0]
        savings_cr = sim.avoided_npt_savings_inr / 10000000.0
        npt_cr = sim.estimated_npt_cost_inr / 10000000.0
        add(_text("rfc-sim-hdr", "48h Storm Evacuation & Zero-Idle Well Redeployment Directive", "h5"))
        add(
            _text(
                "rfc-sim-body",
                (
                    f"• **Rig**: `{sim.rig_id}`  →  **Target Safe Well**: `{sim.destination_well_id}` "
                    f"(`{sim.destination_lat:.4f}°N, {sim.destination_lon:.4f}°E`)  \n"
                    f"• **Departure Window**: `{sim.recommended_departure_time}` · "
                    f"**Expected Transit**: `{sim.expected_transit_hours:.1f} hrs` · "
                    f"**Avoided NPT Savings**: `₹{savings_cr:.2f} Crore` (Transit Burn: `₹{npt_cr:.2f} Cr`)"
                ),
                "body",
            )
        )
        add({"id": "rfc-div-3", "component": "Divider"})

    # Operational Rig Roster & Pinpoint Coordinates
    add(_text("rfc-roster-hdr", "Active Indian EEZ Rig Fleet & Pinpoint Coordinates", "h5"))
    for idx, rig in enumerate(summary.rigs[:6]):
        loc = rig.location
        cost_cr = rig.daily_operating_cost_inr / 10000000.0
        line = (
            f"• **{rig.rig_id} — {rig.rig_name}** ({rig.rig_type.ormwo_label}) — `[{rig.status.value}]`  \n"
            f"  Coord: `{loc.latitude:.3f}°N, {loc.longitude:.3f}°E` · Well: `{rig.current_well_name}` · "
            f"Basin: {loc.basin_name} · Burn: `₹{cost_cr:.2f} Cr/day`"
        )
        add(_text(f"rfc-rig-{idx}", line, "body"))

    if summary.audit_reference_id:
        add(
            _text(
                "rfc-audit-footer",
                f"CAG Report #15117 Governance Audit Reference: `{summary.audit_reference_id}`",
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
