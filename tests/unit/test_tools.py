"""Unit tests for ORMWO ADK tools and 20-Rig / 120-Well India EEZ dataset."""

from app.contracts import FleetSummary
from app.integration.tools import (
    PENDING_RIG_FLEET_KEY,
    get_marine_weather_forecast,
    get_rig_telemetry,
    list_rig_fleet,
    log_audit_trail,
    query_rig_telemetry,
    run_monte_carlo_transit_simulation,
)
from app.rigs.india_eez_dataset import INDIA_120_WELL_REGISTRY, INDIA_20_RIG_FLEET


class MockContext:
    def __init__(self):
        self.state = {}


def test_india_eez_20_rigs_and_120_wells():
    assert len(INDIA_20_RIG_FLEET) == 20
    assert len(INDIA_120_WELL_REGISTRY) == 120


def test_list_rig_fleet():
    ctx = MockContext()
    res = list_rig_fleet(callback_context=ctx)
    assert "Tracked 20 rig(s) and 120 wells" in res
    assert PENDING_RIG_FLEET_KEY in ctx.state
    assert isinstance(ctx.state[PENDING_RIG_FLEET_KEY], FleetSummary)


def test_query_rig_telemetry():
    ctx = MockContext()
    res = query_rig_telemetry("Ocean Titan", callback_context=ctx)
    assert "Ocean Titan" in res
    assert "ROP" in res


def test_ormwo_tool_pipeline():
    ctx = MockContext()

    # 1. Ingest Telemetry
    tel = get_rig_telemetry("RIG-OFFSHORE-04", callback_context=ctx)
    assert tel["rig_id"] == "RIG-OFFSHORE-04"
    assert tel["rig_type"] == "JACKUP"
    assert tel["daily_operating_cost_inr"] > 10000000.0

    # 2. 48h Marine Weather Check
    forecast = get_marine_weather_forecast(
        lat=tel["coordinates"]["lat"],
        lon=tel["coordinates"]["lon"],
        forecast_hours=48,
        callback_context=ctx,
    )
    assert len(forecast) > 0
    assert any(not pt["safe_for_operations"] for pt in forecast)
    assert any(pt["significant_wave_height_m"] > 2.5 or pt["wind_speed_knots"] > 35.0 for pt in forecast)

    # 3. Monte Carlo Transit Simulation
    sim = run_monte_carlo_transit_simulation(
        rig_id="RIG-OFFSHORE-04",
        origin=tel["coordinates"],
        destination=tel["recommended_safe_destination_well"],
        departure_window_hours=[4, 8, 12, 18, 24],
        callback_context=ctx,
    )
    assert sim["expected_transit_hours"] > 0
    assert len(sim["optimal_routing_waypoints"]) >= 4
    assert sim["avoided_npt_savings_inr"] > 0

    # 4. Governance Audit Trail
    audit = log_audit_trail(
        event_type="CRITICAL_ACTION_REQUIRED",
        payload={"rig_id": "RIG-OFFSHORE-04", "simulation": sim},
        callback_context=ctx,
    )
    assert audit["audit_reference_id"].startswith("AUD-ONGC-15117-")
