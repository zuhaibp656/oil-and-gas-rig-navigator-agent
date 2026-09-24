"""Unit tests for India EEZ Map & 48h Weather Vega-Lite v5 specification generator."""

from app.contracts import FleetSummary
from app.integration.tools import _MOCK_RIG_FLEET
from app.render.rig_map_vega import build_rig_fleet_map_spec, build_rig_telemetry_chart_spec
from app.rigs.india_eez_dataset import INDIA_120_WELL_REGISTRY
from app.rigs.monte_carlo_optimizer import execute_monte_carlo_transit_simulation


def test_build_rig_fleet_map_spec():
    sim = execute_monte_carlo_transit_simulation("RIG-OFFSHORE-04")
    summary = FleetSummary(
        total_rigs=len(_MOCK_RIG_FLEET),
        active_drilling=17,
        in_transit=0,
        standby_maintenance=3,
        rigs=_MOCK_RIG_FLEET,
        wells=INDIA_120_WELL_REGISTRY,
        transit_simulations=[sim],
    )
    spec = build_rig_fleet_map_spec(summary)

    assert spec["$schema"] == "https://vega.github.io/schema/vega-lite/v5.json"
    assert "vconcat" in spec
    assert len(spec["vconcat"]) == 2

    india_map_panel = spec["vconcat"][0]
    assert "layer" in india_map_panel
    # 6 layers: India Coastline + 48h Storm Zones + Callout Labels + 120 Wells + 20 Rigs + Waypoint Trajectory
    assert len(india_map_panel["layer"]) >= 5
    # Verify 120 wells and 20 rigs in layers
    assert len(india_map_panel["layer"][2]["data"]["values"]) == 120
    assert len(india_map_panel["layer"][3]["data"]["values"]) == 20


def test_build_rig_telemetry_chart_spec():
    rig = _MOCK_RIG_FLEET[0]
    spec = build_rig_telemetry_chart_spec(rig)

    assert spec["$schema"] == "https://vega.github.io/schema/vega-lite/v5.json"
    assert "data" in spec
    assert len(spec["data"]["values"]) > 0
