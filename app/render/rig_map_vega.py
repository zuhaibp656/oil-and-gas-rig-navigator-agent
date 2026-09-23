"""Vega-Lite v5 specification generator for Offshore Rig Mobilization & Weather Optimizer (ORMWO).

Builds an interactive 5-Layer Cartographic Map of India & Surrounding EEZ Waters
(Coastline Outline + 48h Storm Zones + 120 Wells + 20 Rigs + Monte Carlo Waypoint Trajectories)
paired with a 48-Hour Metocean Forecast Confidence Chart for Gemini Enterprise A2UI v0.9.
"""

from __future__ import annotations

from typing import Any

try:
    from app.contracts import FleetSummary, RigUnit
    from app.rigs.india_eez_dataset import (
        ACTIVE_48H_STORM_ZONES,
        INDIA_120_WELL_REGISTRY,
        get_india_coastline_layer_values,
    )
    from app.rigs.metocean_engine import compute_marine_weather_forecast
except ImportError:
    from contracts import FleetSummary, RigUnit
    from rigs.india_eez_dataset import (
        ACTIVE_48H_STORM_ZONES,
        INDIA_120_WELL_REGISTRY,
        get_india_coastline_layer_values,
    )
    from rigs.metocean_engine import compute_marine_weather_forecast

VEGA_LITE_SCHEMA: str = "https://vega.github.io/schema/vega-lite/v5.json"
SPEC_KEY: str = "spec"
SPEC_POINTER: str = f"/{SPEC_KEY}"


def build_rig_fleet_map_spec(summary: FleetSummary) -> dict[str, Any]:
    """Build a 5-layer Map of India & EEZ Waters + 48h Weather Forecast Vega-Lite v5 spec."""
    # 1. India Coastline Polygon Points
    coastline_values = get_india_coastline_layer_values()

    # 2. Active 48h Storm Zones
    storm_zones = summary.active_storm_zones or ACTIVE_48H_STORM_ZONES

    # 3. 120 Candidate & Active Wells (highlight recommended target wells)
    recommended_well_ids = {
        sim.destination_well_id for sim in (summary.transit_simulations or [])
    }
    source_wells = summary.wells or INDIA_120_WELL_REGISTRY
    well_points: list[dict[str, Any]] = []
    for w in source_wells:
        well_state = "RECOMMENDED_TARGET" if w.well_id in recommended_well_ids else w.status.value
        well_points.append({
            "well_id": w.well_id,
            "well_name": w.well_name,
            "basin": w.basin_name,
            "latitude": w.latitude,
            "longitude": w.longitude,
            "water_depth_m": w.water_depth_m,
            "well_state": well_state,
            "peak_48h_hs_m": w.peak_48h_hs_m,
            "peak_48h_wind_kts": w.peak_48h_wind_kts,
        })

    # 4. 20 Offshore Rigs
    rig_points: list[dict[str, Any]] = []
    for rig in summary.rigs:
        rig_points.append({
            "rig_id": rig.rig_id,
            "rig_name": rig.rig_name,
            "operator": rig.operator,
            "status": rig.status.value,
            "rig_type": rig.rig_type.ormwo_label,
            "latitude": rig.location.latitude,
            "longitude": rig.location.longitude,
            "basin": rig.location.basin_name,
            "well_name": rig.current_well_name,
            "water_depth": rig.location.water_depth_m,
            "current_depth": rig.telemetry.measured_depth_m if rig.telemetry else 0.0,
            "daily_cost_cr": round(rig.daily_operating_cost_inr / 10000000.0, 2),
        })

    # 5. Monte Carlo Evacuation / Redeployment Waypoint Trajectories
    trajectory_points: list[dict[str, Any]] = []
    for sim in (summary.transit_simulations or []):
        for step_idx, wp in enumerate(sim.optimal_routing_waypoints):
            if len(wp) >= 2:
                trajectory_points.append({
                    "rig_id": sim.rig_id,
                    "step": step_idx,
                    "latitude": wp[0],
                    "longitude": wp[1],
                    "destination_well": sim.destination_well_id,
                    "eta_hours": sim.expected_transit_hours,
                })

    # 6. 48-Hour Weather Forecast Series (for Bottom Synchronized Panel)
    weather_series = summary.weather_series
    if not weather_series:
        ref_lat = summary.rigs[0].location.latitude if summary.rigs else 19.25
        ref_lon = summary.rigs[0].location.longitude if summary.rigs else 71.85
        weather_series = compute_marine_weather_forecast(ref_lat, ref_lon, forecast_hours=48, step_hours=3)

    weather_rows: list[dict[str, Any]] = []
    for pt in weather_series:
        weather_rows.append({
            "hour": pt.forecast_hour,
            "timestamp": pt.timestamp,
            "hs_m": pt.significant_wave_height_m,
            "hs_p05": pt.hs_p05_m,
            "hs_p95": pt.hs_p95_m,
            "wind_kts": pt.wind_speed_knots,
            "sea_state": pt.sea_state,
            "threat_level": pt.cyclone_threat_level,
            "threshold_m": 2.5,
        })

    # Build Map Layers
    map_layers: list[dict[str, Any]] = [
        # Layer 1: India Coastline & Peninsula Outline
        {
            "data": {"values": coastline_values},
            "mark": {
                "type": "line",
                "fill": "#1E293B",
                "fillOpacity": 0.22,
                "stroke": "#475569",
                "strokeWidth": 1.6,
            },
            "encoding": {
                "x": {
                    "field": "longitude",
                    "type": "quantitative",
                    "scale": {"domain": [67.0, 89.5]},
                    "axis": {"title": "Longitude (°E — Arabian Sea to Bay of Bengal)", "grid": True},
                },
                "y": {
                    "field": "latitude",
                    "type": "quantitative",
                    "scale": {"domain": [6.0, 24.5]},
                    "axis": {"title": "Latitude (°N — Indian EEZ)", "grid": True},
                },
                "detail": {"field": "group", "type": "nominal"},
                "order": {"field": "order", "type": "quantitative"},
            },
        },
        # Layer 2: 48h Storm Cyclone Hazard Zones
        {
            "data": {"values": storm_zones},
            "mark": {
                "type": "circle",
                "size": 3200,
                "color": "#EF4444",
                "opacity": 0.18,
                "stroke": "#DC2626",
                "strokeWidth": 1.5,
                "strokeDash": [4, 3],
            },
            "encoding": {
                "x": {"field": "longitude", "type": "quantitative"},
                "y": {"field": "latitude", "type": "quantitative"},
                "tooltip": [
                    {"field": "storm_name", "type": "nominal", "title": "48h Weather Alert"},
                    {"field": "basin", "type": "nominal", "title": "Affected Basin"},
                    {"field": "peak_hs_m", "type": "quantitative", "title": "Peak Wave Hs (m)"},
                    {"field": "peak_wind_kts", "type": "quantitative", "title": "Peak Wind (kts)"},
                    {"field": "threat_level", "type": "nominal", "title": "Cyclone Threat"},
                ],
            },
        },
        # Layer 3: 120 Candidate & Active Offshore Well Locations
        {
            "data": {"values": well_points},
            "mark": {"type": "circle", "size": 36, "opacity": 0.82},
            "encoding": {
                "x": {"field": "longitude", "type": "quantitative"},
                "y": {"field": "latitude", "type": "quantitative"},
                "color": {
                    "field": "well_state",
                    "type": "nominal",
                    "scale": {
                        "domain": [
                            "SAFE_READY_TO_SPUD",
                            "STORM_LOCKED",
                            "ACTIVE_DRILLING",
                            "RECOMMENDED_TARGET",
                        ],
                        "range": ["#10B981", "#EF4444", "#38BDF8", "#FACC15"],
                    },
                    "legend": {"title": "Well & Rig Layer", "orient": "bottom"},
                },
                "tooltip": [
                    {"field": "well_id", "type": "nominal", "title": "Well ID"},
                    {"field": "basin", "type": "nominal", "title": "Basin"},
                    {"field": "well_state", "type": "nominal", "title": "48h Status"},
                    {"field": "latitude", "type": "quantitative", "title": "Lat (°N)", "format": ".3f"},
                    {"field": "longitude", "type": "quantitative", "title": "Lon (°E)", "format": ".3f"},
                    {"field": "water_depth_m", "type": "quantitative", "title": "Water Depth (m)"},
                    {"field": "peak_48h_hs_m", "type": "quantitative", "title": "48h Peak Hs (m)"},
                ],
            },
        },
        # Layer 4: 20 Active Offshore Rigs
        {
            "data": {"values": rig_points},
            "mark": {
                "type": "point",
                "shape": "triangle-up",
                "filled": True,
                "size": 145,
                "color": "#0F172A",
                "stroke": "#FACC15",
                "strokeWidth": 1.6,
            },
            "encoding": {
                "x": {"field": "longitude", "type": "quantitative"},
                "y": {"field": "latitude", "type": "quantitative"},
                "tooltip": [
                    {"field": "rig_id", "type": "nominal", "title": "Rig ID"},
                    {"field": "rig_name", "type": "nominal", "title": "Rig Name"},
                    {"field": "rig_type", "type": "nominal", "title": "Hull Type"},
                    {"field": "status", "type": "nominal", "title": "Status"},
                    {"field": "well_name", "type": "nominal", "title": "Current Well"},
                    {"field": "basin", "type": "nominal", "title": "Basin"},
                    {"field": "daily_cost_cr", "type": "quantitative", "title": "Burn Rate (₹ Cr/day)"},
                ],
            },
        },
    ]

    if trajectory_points:
        map_layers.append({
            "data": {"values": trajectory_points},
            "mark": {
                "type": "line",
                "color": "#F59E0B",
                "strokeWidth": 2.6,
                "strokeDash": [5, 2],
                "point": {"filled": True, "color": "#FACC15", "size": 55},
            },
            "encoding": {
                "x": {"field": "longitude", "type": "quantitative"},
                "y": {"field": "latitude", "type": "quantitative"},
                "detail": {"field": "rig_id", "type": "nominal"},
                "order": {"field": "step", "type": "quantitative"},
                "tooltip": [
                    {"field": "rig_id", "type": "nominal", "title": "Evacuating Rig"},
                    {"field": "destination_well", "type": "nominal", "title": "Target Safe Well"},
                    {"field": "eta_hours", "type": "quantitative", "title": "Expected Transit (hrs)"},
                ],
            },
        })

    weather_panel = {
        "width": 480,
        "height": 125,
        "title": "48-Hour Metocean Wave Forecast (Hs m) with 95% CI & 2.5m Critical Threshold",
        "data": {"values": weather_rows},
        "layer": [
            {
                "mark": {"type": "area", "color": "#38BDF8", "opacity": 0.22},
                "encoding": {
                    "x": {"field": "hour", "type": "quantitative", "axis": {"title": "Forecast Horizon (Hours Ahead: T+0h to T+48h)"}},
                    "y": {"field": "hs_p05", "type": "quantitative", "axis": {"title": "Wave Height Hs (m)"}},
                    "y2": {"field": "hs_p95"},
                },
            },
            {
                "mark": {"type": "line", "color": "#0284C7", "strokeWidth": 2.4, "point": True},
                "encoding": {
                    "x": {"field": "hour", "type": "quantitative"},
                    "y": {"field": "hs_m", "type": "quantitative"},
                    "tooltip": [
                        {"field": "timestamp", "type": "nominal", "title": "UTC Timestamp"},
                        {"field": "hs_m", "type": "quantitative", "title": "Significant Wave Height (m)"},
                        {"field": "wind_kts", "type": "quantitative", "title": "Wind Speed (kts)"},
                        {"field": "sea_state", "type": "quantitative", "title": "Douglas Sea Scale (0-9)"},
                        {"field": "threat_level", "type": "nominal", "title": "Threat Level"},
                    ],
                },
            },
            {
                "mark": {"type": "rule", "color": "#DC2626", "strokeDash": [4, 4], "strokeWidth": 1.8},
                "encoding": {"y": {"field": "threshold_m", "type": "quantitative"}},
            },
        ],
    }

    return {
        "$schema": VEGA_LITE_SCHEMA,
        "description": "India EEZ Map: 20 Offshore Rigs, 120 Candidate Wells, 48h Storm Zones & Transit Trajectories",
        "padding": {"left": 8, "right": 8, "top": 8, "bottom": 8},
        "vconcat": [
            {
                "width": 480,
                "height": 310,
                "title": "Map of India & EEZ: 20 Rigs (▲), 120 Candidate Wells (●), 48h Storm Cones & Optimal Routes",
                "layer": map_layers,
            },
            weather_panel,
        ],
    }


def build_rig_telemetry_chart_spec(rig: RigUnit) -> dict[str, Any]:
    """Build a gauge/bar telemetry breakdown for an individual rig unit."""
    t = rig.telemetry
    if not t:
        metrics = []
    else:
        metrics = [
            {"metric": "ROP (m/hr)", "value": t.rate_of_penetration_m_hr, "unit": "m/hr"},
            {"metric": "RPM", "value": t.rotary_rpm, "unit": "rpm"},
            {"metric": "Torque (kft-lbs)", "value": t.torque_kft_lbs, "unit": "kft-lbs"},
            {"metric": "SPP (psi / 100)", "value": t.standpipe_pressure_psi / 100.0, "unit": "x100 psi"},
            {"metric": "Gas (units)", "value": t.gas_units_total, "unit": "units"},
        ]

    return {
        "$schema": VEGA_LITE_SCHEMA,
        "description": f"Real-Time Telemetry for {rig.rig_name}",
        "width": 420,
        "height": 180,
        "padding": {"left": 10, "right": 10, "top": 10, "bottom": 10},
        "data": {"values": metrics},
        "mark": {"type": "bar", "cornerRadiusEnd": 3, "color": "#0284C7"},
        "encoding": {
            "y": {"field": "metric", "type": "nominal", "axis": {"title": None}},
            "x": {"field": "value", "type": "quantitative", "axis": {"title": "Value", "grid": True}},
            "tooltip": [
                {"field": "metric", "type": "nominal", "title": "Parameter"},
                {"field": "value", "type": "quantitative", "title": "Reading", "format": ",.2f"},
                {"field": "unit", "type": "nominal", "title": "Unit"},
            ],
        },
    }
