"""ADK Tool bindings for the Offshore Rig Mobilization & Weather Optimizer (ORMWO).

In : User or agent tool parameters (rig_id, lat, lon, forecast_hours, origin, destination).
Out: Deterministic JSON/dict structures matching the ORMWO specification, while queuing
     the 5-layer India EEZ Map (20 Rigs + 120 Wells + 48h Storm Zones + Waypoints)
     via a lightweight memory token in callback_context.state[PENDING_RIG_FLEET_KEY]
     so ADK session storage (`session.db` and `/run_sse`) never bloats or fails to fetch.
"""

from __future__ import annotations

from datetime import timedelta
import json
import logging
from typing import Any
import uuid

from google.adk.agents.callback_context import CallbackContext

try:
    from app.bq.audit_logger import record_governance_audit_trail
    from app.contracts import (
        FleetSummary,
        MarineWeatherPoint,
        MonteCarloTransitResult,
        RigOperationalStatus,
        RigUnit,
    )
    from app.rigs.india_eez_dataset import (
        ACTIVE_48H_STORM_ZONES,
        INDIA_120_WELL_REGISTRY,
        INDIA_20_RIG_FLEET,
        find_nearest_safe_candidate_well,
        resolve_rig_by_identifier,
    )
    from app.rigs.metocean_engine import (
        BASE_ASSESSMENT_TIME_UTC,
        compute_marine_weather_forecast,
    )
    from app.rigs.monte_carlo_optimizer import execute_monte_carlo_transit_simulation
except ImportError:
    from bq.audit_logger import record_governance_audit_trail
    from contracts import (
        FleetSummary,
        MarineWeatherPoint,
        MonteCarloTransitResult,
        RigOperationalStatus,
        RigUnit,
    )
    from rigs.india_eez_dataset import (
        ACTIVE_48H_STORM_ZONES,
        INDIA_120_WELL_REGISTRY,
        INDIA_20_RIG_FLEET,
        find_nearest_safe_candidate_well,
        resolve_rig_by_identifier,
    )
    from rigs.metocean_engine import (
        BASE_ASSESSMENT_TIME_UTC,
        compute_marine_weather_forecast,
    )
    from rigs.monte_carlo_optimizer import execute_monte_carlo_transit_simulation

logger = logging.getLogger(__name__)

PENDING_RIG_FLEET_KEY: str = "pending_rig_fleet"
PENDING_RIG_DETAIL_KEY: str = "pending_rig_detail"
_MOCK_RIG_FLEET: list[RigUnit] = INDIA_20_RIG_FLEET

# Lightweight in-memory surface cache keyed by short token so ADK session.db
# only serializes a 22-byte string instead of 65 KB of dataclasses per tool call.
_SURFACE_MEMORY_CACHE: dict[str, FleetSummary] = {}


def resolve_pending_fleet_summary(val: Any) -> FleetSummary | None:
    """Resolve either a direct FleetSummary (unit tests) or a cache token string (ADK runtime)."""
    if isinstance(val, FleetSummary):
        return val
    if isinstance(val, str) and val in _SURFACE_MEMORY_CACHE:
        return _SURFACE_MEMORY_CACHE.pop(val, None)
    return None


def _queue_india_map_surface(
    callback_context: CallbackContext | None,
    rigs: list[RigUnit] | None = None,
    selected_rig_id: str | None = None,
    weather_series: list[MarineWeatherPoint] | None = None,
    transit_sim: MonteCarloTransitResult | None = None,
    audit_reference_id: str = "",
) -> FleetSummary:
    """Populate callback_context.state so emit_a2ui_surface renders the India EEZ Map."""
    fleet_rigs = rigs or INDIA_20_RIG_FLEET
    active_drilling = sum(1 for r in fleet_rigs if r.status == RigOperationalStatus.DRILLING)
    in_transit = sum(1 for r in fleet_rigs if r.status == RigOperationalStatus.TRANSIT)
    standby_maint = len(fleet_rigs) - active_drilling - in_transit

    existing: FleetSummary | None = None
    if callback_context and hasattr(callback_context, "state") and callback_context.state is not None:
        raw = callback_context.state.get(PENDING_RIG_FLEET_KEY)
        if isinstance(raw, FleetSummary):
            existing = raw
        elif isinstance(raw, str) and raw in _SURFACE_MEMORY_CACHE:
            existing = _SURFACE_MEMORY_CACHE[raw]

    merged_weather = weather_series or (existing.weather_series if existing else [])
    merged_sims = (
        [transit_sim]
        if transit_sim is not None
        else (existing.transit_simulations if existing else [])
    )
    merged_audit = audit_reference_id or (existing.audit_reference_id if existing else "")

    summary = FleetSummary(
        total_rigs=len(fleet_rigs),
        active_drilling=active_drilling,
        in_transit=in_transit,
        standby_maintenance=standby_maint,
        rigs=fleet_rigs,
        selected_rig_id=selected_rig_id or (existing.selected_rig_id if existing else None),
        wells=INDIA_120_WELL_REGISTRY,
        weather_series=merged_weather,
        transit_simulations=merged_sims,
        active_storm_zones=ACTIVE_48H_STORM_ZONES,
        audit_reference_id=merged_audit,
    )

    if callback_context and hasattr(callback_context, "state") and callback_context.state is not None:
        if isinstance(callback_context, CallbackContext):
            token = f"map-{uuid.uuid4().hex[:12]}"
            _SURFACE_MEMORY_CACHE[token] = summary
            callback_context.state[PENDING_RIG_FLEET_KEY] = token
        else:
            # Direct dataclass assignment for lightweight unit test MockContext
            callback_context.state[PENDING_RIG_FLEET_KEY] = summary
    return summary


# ==============================================================================
# ORMWO Specification Tool 1: get_rig_telemetry
# ==============================================================================

def get_rig_telemetry(
    rig_id: str,
    callback_context: CallbackContext | None = None,
) -> dict[str, Any]:
    """Retrieves the current state, coordinates, daily operating cost, 48h metocean risk, and safe target well for a drilling rig.

    Args:
        rig_id: Unique identifier (e.g., 'RIG-OFFSHORE-04', 'RIG-OFFSHORE-01', or rig name 'Ocean Titan').
        callback_context: ADK callback context to attach the India EEZ map surface.
    """
    rig = resolve_rig_by_identifier(rig_id)
    safe_well = find_nearest_safe_candidate_well(
        rig.location.latitude,
        rig.location.longitude,
        rig.rig_type,
    )
    weather = compute_marine_weather_forecast(
        rig.location.latitude,
        rig.location.longitude,
        forecast_hours=48,
        step_hours=6,
    )
    sim = execute_monte_carlo_transit_simulation(rig_id=rig.rig_id)
    audit = record_governance_audit_trail(
        event_type="CRITICAL_ACTION_REQUIRED",
        payload={"rig_id": rig.rig_id, "destination_well": safe_well.well_id},
    )
    _queue_india_map_surface(
        callback_context,
        rigs=INDIA_20_RIG_FLEET,
        selected_rig_id=rig.rig_id,
        weather_series=weather,
        transit_sim=sim,
        audit_reference_id=str(audit["audit_reference_id"]),
    )

    peak_wave_m = max(pt.significant_wave_height_m for pt in weather)
    peak_wind_kts = max(pt.wind_speed_knots for pt in weather)

    return {
        "rig_id": rig.rig_id,
        "rig_name": rig.rig_name,
        "rig_type": rig.rig_type.ormwo_label,
        "coordinates": {
            "lat": rig.location.latitude,
            "lon": rig.location.longitude,
        },
        "basin_name": rig.location.basin_name,
        "current_status": rig.status.value,
        "daily_operating_cost_inr": rig.daily_operating_cost_inr,
        "current_well_id": rig.current_well_name,
        "planned_release_date": rig.planned_release_date,
        "recommended_safe_destination_well": {
            "well_id": safe_well.well_id,
            "lat": safe_well.latitude,
            "lon": safe_well.longitude,
            "basin_name": safe_well.basin_name,
        },
        "weather_48h_summary": {
            "peak_significant_wave_height_m": peak_wave_m,
            "peak_wind_speed_knots": peak_wind_kts,
            "threshold_exceeded": bool(peak_wave_m > 2.5 or peak_wind_kts > 35.0),
            "primary_threat": "WEATHER_CYCLONE" if peak_wind_kts > 35.0 else "HIGH_SWELL",
        },
        "monte_carlo_transit_directive": {
            "recommended_departure_time": sim.recommended_departure_time,
            "expected_transit_hours": sim.expected_transit_hours,
            "estimated_npt_cost_inr": sim.estimated_npt_cost_inr,
            "avoided_npt_savings_inr": sim.avoided_npt_savings_inr,
            "decision_deadline": (BASE_ASSESSMENT_TIME_UTC + timedelta(hours=16)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "audit_reference_id": audit["audit_reference_id"],
    }


# ==============================================================================
# ORMWO Specification Tool 2: get_marine_weather_forecast
# ==============================================================================

def get_marine_weather_forecast(
    lat: float,
    lon: float,
    forecast_hours: int = 48,
    callback_context: CallbackContext | None = None,
) -> list[dict[str, Any]]:
    """Retrieves high-precision 48-hour metocean data for the target coordinate.

    Args:
        lat: Target latitude (°N).
        lon: Target longitude (°E).
        forecast_hours: Forecast lead-time window in hours (default 48).
        callback_context: ADK callback context to attach the India EEZ map surface.
    """
    points = compute_marine_weather_forecast(
        lat=float(lat),
        lon=float(lon),
        forecast_hours=int(forecast_hours),
        step_hours=6,
    )
    _queue_india_map_surface(
        callback_context,
        rigs=INDIA_20_RIG_FLEET,
        weather_series=points,
    )

    return [
        {
            "timestamp": pt.timestamp,
            "wind_speed_knots": pt.wind_speed_knots,
            "significant_wave_height_m": pt.significant_wave_height_m,
            "swell_period_sec": pt.swell_period_sec,
            "cyclone_threat_level": pt.cyclone_threat_level,
            "sea_state": pt.sea_state,
            "safe_for_operations": pt.safe_for_operations,
        }
        for pt in points
    ]


# ==============================================================================
# ORMWO Specification Tool 3: run_monte_carlo_transit_simulation
# ==============================================================================

def run_monte_carlo_transit_simulation(
    rig_id: str,
    origin: dict[str, Any] | None = None,
    destination: dict[str, Any] | None = None,
    departure_window_hours: list[int] | None = None,
    callback_context: CallbackContext | None = None,
) -> dict[str, Any]:
    """Executes a stochastic Monte Carlo simulation of transit windows and optimal waypoints.

    Args:
        rig_id: Unique rig identifier (e.g. 'RIG-OFFSHORE-04').
        origin: Origin coordinate dict {'lat': float, 'lon': float}.
        destination: Destination coordinate dict {'lat': float, 'lon': float}.
        departure_window_hours: Candidate departure offsets in hours (e.g. [4, 8, 12, 18, 24]).
        callback_context: ADK callback context to attach the India EEZ map surface.
    """
    sim = execute_monte_carlo_transit_simulation(
        rig_id=rig_id,
        origin=origin,
        destination=destination,
        departure_window_hours=departure_window_hours,
    )
    _queue_india_map_surface(
        callback_context,
        rigs=INDIA_20_RIG_FLEET,
        selected_rig_id=sim.rig_id,
        transit_sim=sim,
    )

    return {
        "rig_id": sim.rig_id,
        "target_safe_well_id": sim.destination_well_id,
        "recommended_coordinates": {
            "lat": sim.destination_lat,
            "lon": sim.destination_lon,
        },
        "recommended_departure_time": sim.recommended_departure_time,
        "expected_transit_hours": sim.expected_transit_hours,
        "probability_of_weather_standby": sim.probability_of_weather_standby,
        "estimated_npt_cost_inr": sim.estimated_npt_cost_inr,
        "avoided_npt_savings_inr": sim.avoided_npt_savings_inr,
        "optimal_routing_waypoints": sim.optimal_routing_waypoints,
    }


# ==============================================================================
# ORMWO Specification Tool 4: log_audit_trail
# ==============================================================================

def log_audit_trail(
    event_type: str,
    payload: dict[str, Any],
    callback_context: CallbackContext | None = None,
) -> dict[str, Any]:
    """Writes an immutable audit log to BigQuery/GCS for CAG Report #15117 compliance.

    Args:
        event_type: Audit event classification (e.g., 'CRITICAL_ACTION_REQUIRED', 'NORMAL_CLEAR').
        payload: Decision inputs, coordinates, NPT risk assessment, and directive details.
        callback_context: ADK callback context.
    """
    receipt = record_governance_audit_trail(event_type=event_type, payload=payload)
    _queue_india_map_surface(
        callback_context,
        audit_reference_id=str(receipt["audit_reference_id"]),
    )
    return receipt


# ==============================================================================
# Fleet & Legacy Compatibility Tools (list_rig_fleet, query_rig_telemetry)
# ==============================================================================

def list_rig_fleet(
    basin_filter: str | None = None,
    callback_context: CallbackContext | None = None,
) -> str:
    """Lists active drilling rigs and candidate wells across India's EEZ and attaches the India Map."""
    rigs = INDIA_20_RIG_FLEET
    if basin_filter:
        q = basin_filter.strip().lower()
        rigs = [r for r in rigs if q in r.location.basin_name.lower() or q in r.rig_name.lower()]

    default_sim = execute_monte_carlo_transit_simulation(
        rig_id=rigs[0].rig_id if rigs else "RIG-OFFSHORE-04"
    )
    audit = record_governance_audit_trail(
        event_type="FLEET_METOCEAN_SWEEP",
        payload={"rigs_evaluated": len(rigs), "wells_evaluated": len(INDIA_120_WELL_REGISTRY)},
    )
    _queue_india_map_surface(
        callback_context,
        rigs=rigs,
        transit_sim=default_sim,
        audit_reference_id=str(audit["audit_reference_id"]),
    )

    rig_ref = rigs[0] if rigs else INDIA_20_RIG_FLEET[3]
    deadline_iso = (BASE_ASSESSMENT_TIME_UTC + timedelta(hours=16)).strftime("%Y-%m-%dT%H:%M:%SZ")
    strict_payload = {
        "rig_id": rig_ref.rig_id,
        "assessment_timestamp": BASE_ASSESSMENT_TIME_UTC.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "CRITICAL_ACTION_REQUIRED",
        "npt_risk_assessment": {
            "estimated_downtime_hours": round(default_sim.expected_transit_hours, 1),
            "projected_cost_exposure_inr": round(default_sim.estimated_npt_cost_inr, 2),
            "primary_threat": "WEATHER_CYCLONE",
        },
        "operational_directive": {
            "action": "INITIATE_PREVENTATIVE_TRANSIT",
            "decision_deadline": deadline_iso,
            "recommended_coordinates": {
                "lat": default_sim.destination_lat,
                "lon": default_sim.destination_lon,
            },
        },
        "audit_reference_id": audit["audit_reference_id"],
    }
    return (
        f"Tracked {len(rigs)} rig(s) and {len(INDIA_120_WELL_REGISTRY)} wells across India's EEZ. "
        f"{json.dumps(strict_payload)}"
    )


def query_rig_telemetry(
    rig_identifier: str,
    callback_context: CallbackContext | None = None,
) -> str:
    """Queries live drilling telemetry and 48h ORMWO directive for a specific rig."""
    q = rig_identifier.strip().lower()
    exact_match = [
        r for r in INDIA_20_RIG_FLEET
        if q in r.rig_id.lower() or q in r.rig_name.lower() or q.replace("rig-off-", "rig-offshore-") in r.rig_id.lower()
    ]
    if not exact_match:
        return (
            f"No rig found matching '{rig_identifier}'. "
            f"Available: {', '.join(r.rig_name for r in INDIA_20_RIG_FLEET[:6])}."
        )

    rig = exact_match[0]
    t = rig.telemetry
    sim = execute_monte_carlo_transit_simulation(rig_id=rig.rig_id)
    audit = record_governance_audit_trail(
        event_type="RIG_TELEMETRY_AND_WEATHER_CHECK",
        payload={"rig_id": rig.rig_id, "target_well": sim.destination_well_id},
    )
    _queue_india_map_surface(
        callback_context,
        rigs=[rig],
        selected_rig_id=rig.rig_id,
        transit_sim=sim,
        audit_reference_id=str(audit["audit_reference_id"]),
    )

    if not t:
        return f"{rig.rig_name} ({rig.operator}) is currently {rig.status.value} in {rig.location.basin_name}."

    return (
        f"{rig.rig_name} ({rig.rig_id}, {rig.operator}) drilling well {rig.current_well_name} in {rig.location.basin_name} "
        f"({rig.location.latitude:.3f}°N, {rig.location.longitude:.3f}°E). "
        f"Depth: {t.measured_depth_m:,.0f} m / {rig.target_depth_m:,.0f} m. ROP: {t.rate_of_penetration_m_hr:.1f} m/h, "
        f"RPM: {t.rotary_rpm:.0f}, Torque: {t.torque_kft_lbs:.1f} kft-lbs, SPP: {t.standpipe_pressure_psi:.0f} psi. "
        f"Safe Redeployment Target: {sim.destination_well_id} ({sim.destination_lat:.3f}°N, {sim.destination_lon:.3f}°E)."
    )
