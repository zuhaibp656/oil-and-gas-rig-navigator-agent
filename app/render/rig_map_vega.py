"""Vega-Lite v5 interactive specification generator for Offshore Rig Mobilization & Weather Optimizer (ORMWO).

Builds an interactive 5-Layer Cartographic Map of India & Surrounding EEZ Waters
with full mouse scroll-wheel zoom, click-drag pan (`"bind": "scales"`), and rich hover tooltips
for all 20 Offshore Rigs, 120 Candidate/Active Wells, 48h Cyclone Cones, and Monte Carlo Waypoints,
paired with an interactive 48-Hour Metocean Forecast Chart for Gemini Enterprise A2UI v0.9.
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
    """Build an interactive zoomable/hoverable 5-layer Map of India & EEZ + 48h Weather Forecast Vega-Lite v5 spec."""
    # 1. India Coastline Polygon Points
    coastline_values = get_india_coastline_layer_values()

    # 2. Active 48h Storm Zones
    storm_zones = summary.active_storm_zones or ACTIVE_48H_STORM_ZONES

    # 3. 120 Candidate & Active Wells (with rich hover metadata)
    recommended_well_ids = {
        sim.destination_well_id for sim in (summary.transit_simulations or [])
    }
    source_wells = summary.wells or INDIA_120_WELL_REGISTRY
    well_points: list[dict[str, Any]] = []
    for w in source_wells:
        well_state = "RECOMMENDED_TARGET" if w.well_id in recommended_well_ids else w.status.value
        compat_rigs = ", ".join(rt.ormwo_label for rt in getattr(w, "compatible_rig_types", [])) or "ALL_OFFSHORE"
        well_points.append({
            "well_id": w.well_id,
            "well_name": w.well_name,
            "basin": w.basin_name,
            "latitude": w.latitude,
            "longitude": w.longitude,
            "water_depth_m": w.water_depth_m,
            "target_depth_m": getattr(w, "target_depth_m", 3200.0),
            "well_state": well_state,
            "peak_48h_hs_m": w.peak_48h_hs_m,
            "peak_48h_wind_kts": w.peak_48h_wind_kts,
            "compatible_rigs": compat_rigs,
        })

    # 4. 20 Offshore Rigs (with full drilling telemetry for interactive mouse hover)
    rig_points: list[dict[str, Any]] = []
    for rig in summary.rigs:
        t = rig.telemetry
        rig_points.append({
            "rig_id": rig.rig_id,
            "rig_name": rig.rig_name,
            "operator": rig.operator,
            "status": rig.status.value,
            "rig_type": rig.rig_type.ormwo_label,
            "latitude": rig.location.latitude,
            "longitude": rig.location.longitude,
            "basin": rig.location.basin_name,
            "block_id": rig.location.block_id,
            "well_name": rig.current_well_name,
            "water_depth": rig.location.water_depth_m,
            "current_depth": t.measured_depth_m if t else 0.0,
            "target_depth": rig.target_depth_m,
            "rop_m_hr": t.rate_of_penetration_m_hr if t else 0.0,
            "rotary_rpm": t.rotary_rpm if t else 0.0,
            "torque_kft_lbs": t.torque_kft_lbs if t else 0.0,
            "spp_psi": t.standpipe_pressure_psi if t else 0.0,
            "daily_cost_cr": round(rig.daily_operating_cost_inr / 10000000.0, 2),
            "is_selected": "SELECTED_FOCUS" if rig.rig_id == summary.selected_rig_id else "FLEET_UNIT",
        })

    # 5. Monte Carlo Evacuation / Redeployment Waypoint Trajectories
    trajectory_points: list[dict[str, Any]] = []
    for sim in (summary.transit_simulations or []):
        savings_cr = round(sim.avoided_npt_savings_inr / 10000000.0, 2)
        npt_cr = round(sim.estimated_npt_cost_inr / 10000000.0, 2)
        for step_idx, wp in enumerate(sim.optimal_routing_waypoints):
            if isinstance(wp, dict):
                w_lat, w_lon = float(wp["lat"]), float(wp["lon"])
            else:
                w_lat, w_lon = float(wp[0]), float(wp[1])
            trajectory_points.append({
                "rig_id": sim.rig_id,
                "step": step_idx,
                "waypoint_label": f"WP-{step_idx}" if step_idx < len(sim.optimal_routing_waypoints) - 1 else f"TARGET ({sim.destination_well_id})",
                "latitude": w_lat,
                "longitude": w_lon,
                "destination_well": sim.destination_well_id,
                "eta_hours": sim.expected_transit_hours,
                "avoided_npt_cr": savings_cr,
                "transit_burn_cr": npt_cr,
                "departure_utc": sim.recommended_departure_time,
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
            "swell_sec": pt.swell_period_sec,
            "sea_state": pt.sea_state,
            "threat_level": pt.cyclone_threat_level,
            "safe_status": "SAFE (<2.5m)" if pt.safe_for_operations else "CRITICAL BREACH (>2.5m)",
            "threshold_m": 2.5,
        })

    # Build Interactive Map Layers (with scroll-wheel zoom + drag pan + hover highlight)
    map_layers: list[dict[str, Any]] = [
        # Layer 1: India Coastline & Peninsula Outline (with pan/zoom scale binding)
        {
            "params": [
                {
                    "name": "india_eez_zoom_pan",
                    "select": "interval",
                    "bind": "scales",
                }
            ],
            "data": {"values": coastline_values},
            "mark": {
                "type": "line",
                "fill": "#1E293B",
                "fillOpacity": 0.25,
                "stroke": "#38BDF8",
                "strokeWidth": 1.8,
                "tooltip": True,
            },
            "encoding": {
                "x": {
                    "field": "longitude",
                    "type": "quantitative",
                    "scale": {"domain": [66.5, 89.5]},
                    "axis": {"title": "Longitude (°E — Scroll to Zoom / Drag to Pan across India EEZ)", "grid": True},
                },
                "y": {
                    "field": "latitude",
                    "type": "quantitative",
                    "scale": {"domain": [5.5, 24.5]},
                    "axis": {"title": "Latitude (°N — Indian EEZ)", "grid": True},
                },
                "detail": {"field": "group", "type": "nominal"},
                "order": {"field": "order", "type": "quantitative"},
            },
        },
        # Layer 2: 48h Storm Cyclone Hazard Zones (Red Circles)
        {
            "data": {"values": storm_zones},
            "mark": {
                "type": "circle",
                "size": 3600,
                "color": "#EF4444",
                "opacity": 0.22,
                "stroke": "#DC2626",
                "strokeWidth": 2.2,
                "strokeDash": [4, 3],
            },
            "encoding": {
                "x": {"field": "longitude", "type": "quantitative"},
                "y": {"field": "latitude", "type": "quantitative"},
                "tooltip": [
                    {"field": "storm_id", "type": "nominal", "title": "Storm ID"},
                    {"field": "storm_name", "type": "nominal", "title": "48h Weather Alert"},
                    {"field": "basin", "type": "nominal", "title": "Affected Basin"},
                    {"field": "peak_hs_m", "type": "quantitative", "title": "Peak Wave Hs (m)"},
                    {"field": "peak_wind_kts", "type": "quantitative", "title": "Peak Wind (kts)"},
                    {"field": "swell_period_s", "type": "quantitative", "title": "Swell Period (s)"},
                    {"field": "threat_level", "type": "nominal", "title": "Cyclone Threat Level"},
                ],
            },
        },
        # Layer 3: 120 Candidate & Active Offshore Well Locations (hoverable pinpoint circles)
        {
            "params": [
                {
                    "name": "well_hover",
                    "select": {"type": "point", "on": "mouseover", "clear": "mouseout"},
                },
                {
                    "name": "well_legend_filter",
                    "select": {"type": "point", "fields": ["well_state"]},
                    "bind": "legend",
                },
            ],
            "data": {"values": well_points},
            "mark": {"type": "circle", "stroke": "#0F172A", "strokeWidth": 0.8},
            "encoding": {
                "x": {"field": "longitude", "type": "quantitative"},
                "y": {"field": "latitude", "type": "quantitative"},
                "size": {
                    "condition": {"param": "well_hover", "value": 160, "empty": False},
                    "value": 48,
                },
                "opacity": {
                    "condition": {"param": "well_legend_filter", "value": 0.92},
                    "value": 0.2,
                },
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
                    "legend": {"title": "120 Wells Status (Click Legend to Filter)", "orient": "bottom"},
                },
                "tooltip": [
                    {"field": "well_id", "type": "nominal", "title": "Well ID"},
                    {"field": "well_name", "type": "nominal", "title": "Well Name"},
                    {"field": "basin", "type": "nominal", "title": "Basin"},
                    {"field": "well_state", "type": "nominal", "title": "48h Readiness"},
                    {"field": "latitude", "type": "quantitative", "title": "Latitude (°N)", "format": ".4f"},
                    {"field": "longitude", "type": "quantitative", "title": "Longitude (°E)", "format": ".4f"},
                    {"field": "water_depth_m", "type": "quantitative", "title": "Water Depth (m)", "format": ",.1f"},
                    {"field": "target_depth_m", "type": "quantitative", "title": "Target Depth (m)", "format": ",.0f"},
                    {"field": "peak_48h_hs_m", "type": "quantitative", "title": "48h Peak Wave Hs (m)"},
                    {"field": "peak_48h_wind_kts", "type": "quantitative", "title": "48h Peak Wind (kts)"},
                    {"field": "compatible_rigs", "type": "nominal", "title": "Compatible Hulls"},
                ],
            },
        },
        # Layer 4: 20 Active Offshore Rigs (hoverable triangles with live drilling telemetry)
        {
            "params": [
                {
                    "name": "rig_hover",
                    "select": {"type": "point", "on": "mouseover", "clear": "mouseout"},
                }
            ],
            "data": {"values": rig_points},
            "mark": {
                "type": "point",
                "shape": "triangle-up",
                "filled": True,
                "color": "#FACC15",
                "stroke": "#0F172A",
                "strokeWidth": 1.8,
            },
            "encoding": {
                "x": {"field": "longitude", "type": "quantitative"},
                "y": {"field": "latitude", "type": "quantitative"},
                "size": {
                    "condition": {"param": "rig_hover", "value": 340, "empty": False},
                    "value": 175,
                },
                "tooltip": [
                    {"field": "rig_id", "type": "nominal", "title": "Rig ID"},
                    {"field": "rig_name", "type": "nominal", "title": "Rig Name"},
                    {"field": "operator", "type": "nominal", "title": "Operator"},
                    {"field": "rig_type", "type": "nominal", "title": "Hull Type"},
                    {"field": "status", "type": "nominal", "title": "Operational Status"},
                    {"field": "well_name", "type": "nominal", "title": "Current Well"},
                    {"field": "basin", "type": "nominal", "title": "Basin"},
                    {"field": "block_id", "type": "nominal", "title": "Block ID"},
                    {"field": "latitude", "type": "quantitative", "title": "Latitude (°N)", "format": ".4f"},
                    {"field": "longitude", "type": "quantitative", "title": "Longitude (°E)", "format": ".4f"},
                    {"field": "water_depth", "type": "quantitative", "title": "Water Depth (m)", "format": ",.1f"},
                    {"field": "current_depth", "type": "quantitative", "title": "Measured Depth (m)", "format": ",.0f"},
                    {"field": "rop_m_hr", "type": "quantitative", "title": "ROP (m/hr)", "format": ".1f"},
                    {"field": "rotary_rpm", "type": "quantitative", "title": "Rotary RPM", "format": ".0f"},
                    {"field": "torque_kft_lbs", "type": "quantitative", "title": "Torque (kft-lbs)", "format": ".1f"},
                    {"field": "spp_psi", "type": "quantitative", "title": "Standpipe Pressure (psi)", "format": ",.0f"},
                    {"field": "daily_cost_cr", "type": "quantitative", "title": "Burn Rate (₹ Cr/day)", "format": ".2f"},
                ],
            },
        },
    ]

    if trajectory_points:
        map_layers.append({
            "data": {"values": trajectory_points},
            "mark": {
                "type": "line",
                "color": "#22C55E",
                "strokeWidth": 3.0,
                "strokeDash": [5, 2],
                "point": {"filled": True, "color": "#4ADE80", "stroke": "#FFFFFF", "strokeWidth": 1.5, "size": 75},
            },
            "encoding": {
                "x": {"field": "longitude", "type": "quantitative"},
                "y": {"field": "latitude", "type": "quantitative"},
                "detail": {"field": "rig_id", "type": "nominal"},
                "order": {"field": "step", "type": "quantitative"},
                "tooltip": [
                    {"field": "waypoint_label", "type": "nominal", "title": "Routing Waypoint"},
                    {"field": "rig_id", "type": "nominal", "title": "Mobilizing Rig"},
                    {"field": "destination_well", "type": "nominal", "title": "Target Safe Well"},
                    {"field": "latitude", "type": "quantitative", "title": "Waypoint Lat (°N)", "format": ".4f"},
                    {"field": "longitude", "type": "quantitative", "title": "Waypoint Lon (°E)", "format": ".4f"},
                    {"field": "departure_utc", "type": "nominal", "title": "Recommended Departure"},
                    {"field": "eta_hours", "type": "quantitative", "title": "Expected Transit (hrs)", "format": ".1f"},
                    {"field": "avoided_npt_cr", "type": "quantitative", "title": "Avoided NPT Savings (₹ Cr)", "format": ".2f"},
                    {"field": "transit_burn_cr", "type": "quantitative", "title": "Transit Cost (₹ Cr)", "format": ".2f"},
                ],
            },
        })

    # Top-level Text Callouts for Red Storm Circles & Numbered Rig Escapes [1]..[6]
    map_layers.append({
        "data": {
            "values": [
                {
                    "longitude": 71.35,
                    "latitude": 20.65,
                    "label": "RED CIRCLE 1: MUMBAI HIGH CYCLONE (Hs=4.2m - DO NOT DRILL)",
                },
                {
                    "longitude": 82.25,
                    "latitude": 17.55,
                    "label": "RED CIRCLE 2: KG-BASIN SWELL (Hs=3.8m - DO NOT DRILL)",
                },
                {
                    "longitude": 71.5,
                    "latitude": 18.0,
                    "label": "[1] Sagar Samrat -> WELL-IND-004 | [2] Sagar Ratna -> WELL-IND-005",
                },
                {
                    "longitude": 82.5,
                    "latitude": 15.0,
                    "label": "[5] Dhirubhai KG1 -> WELL-IND-048 | [6] Platinum Exp -> WELL-IND-049",
                },
            ]
        },
        "mark": {
            "type": "text",
            "fontSize": 10,
            "fontWeight": "bold",
            "color": "#F8FAFC",
            "fill": "#F8FAFC",
        },
        "encoding": {
            "x": {"field": "longitude", "type": "quantitative"},
            "y": {"field": "latitude", "type": "quantitative"},
            "text": {"field": "label", "type": "nominal"},
        },
    })

    weather_panel = {
        "width": 520,
        "height": 140,
        "title": "48-Hour Metocean Wave Forecast (Hs m) — Hover Points for Wind, Swell & Sea State",
        "data": {"values": weather_rows},
        "layer": [
            {
                "params": [
                    {
                        "name": "weather_zoom_pan",
                        "select": "interval",
                        "bind": "scales",
                    }
                ],
                "mark": {"type": "area", "color": "#38BDF8", "opacity": 0.22},
                "encoding": {
                    "x": {"field": "hour", "type": "quantitative", "axis": {"title": "Forecast Horizon (Hours Ahead: T+0h to T+48h)"}},
                    "y": {"field": "hs_p05", "type": "quantitative", "axis": {"title": "Wave Height Hs (m)"}},
                    "y2": {"field": "hs_p95"},
                },
            },
            {
                "params": [
                    {
                        "name": "forecast_hover",
                        "select": {"type": "point", "on": "mouseover", "clear": "mouseout"},
                    }
                ],
                "mark": {"type": "line", "color": "#0284C7", "strokeWidth": 2.6, "point": {"filled": True, "size": 65}},
                "encoding": {
                    "x": {"field": "hour", "type": "quantitative"},
                    "y": {"field": "hs_m", "type": "quantitative"},
                    "tooltip": [
                        {"field": "timestamp", "type": "nominal", "title": "UTC Timestamp"},
                        {"field": "hour", "type": "quantitative", "title": "Lead Time (+hrs)"},
                        {"field": "hs_m", "type": "quantitative", "title": "Significant Wave Height Hs (m)"},
                        {"field": "wind_kts", "type": "quantitative", "title": "Wind Speed (kts)"},
                        {"field": "swell_sec", "type": "quantitative", "title": "Swell Period (s)"},
                        {"field": "sea_state", "type": "quantitative", "title": "Douglas Sea Scale (0-9)"},
                        {"field": "threat_level", "type": "nominal", "title": "Threat Level"},
                        {"field": "safe_status", "type": "nominal", "title": "Operational Safety"},
                    ],
                },
            },
            {
                "mark": {"type": "rule", "color": "#DC2626", "strokeDash": [4, 4], "strokeWidth": 2.0},
                "encoding": {"y": {"field": "threshold_m", "type": "quantitative"}},
            },
        ],
    }

    return {
        "$schema": VEGA_LITE_SCHEMA,
        "description": "Interactive India EEZ Map: Scroll to Zoom, Drag to Pan, Hover over 20 Rigs & 120 Candidate Wells",
        "padding": {"left": 8, "right": 8, "top": 8, "bottom": 8},
        "vconcat": [
            {
                "width": 520,
                "height": 340,
                "title": "Interactive Map of India & EEZ: 20 Rigs (▲), 120 Wells (●), 48h Storm Cones (Scroll Zoom & Hover)",
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
