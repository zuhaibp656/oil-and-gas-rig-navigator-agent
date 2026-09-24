"""Vega-Lite v5 3-Tier Bathymetric Command Infographic for Offshore Rig Mobilization & Weather Optimizer (ORMWO).

Renders a Full-Width (680px), High-Contrast Dark Bathymetric Ocean Command Dashboard inside Gemini Enterprise's
A2UI v0.9 `VegaChart` component:
- Tier 1 (width: 680, height: 420): Full India EEZ Bathymetric Map (Deep Ocean #0B2545, Continental Shelf #134E7A,
  Golden-Tan India Terrain #C89D66, Multi-Ring Red 48h Storm Cones, 120 Wells, Green Escape Arrows, Badges [1]–[6]).
- Tier 2 (hconcat of two 320x250 panels):
  • Zoom A: Mumbai High / Western Offshore Escape Routes [1]–[4] (de-clustered origin -> safe target wells)
  • Zoom B: KG-DWN Basin / Eastern Offshore Escape Routes [5]–[6] (de-clustered origin -> safe target wells)
- Tier 3 (width: 680, height: 145): 48-Hour Google WeatherNext (GenCast + GraphCast) Wave Height (Hs) vs 2.5m Limit.
"""

from __future__ import annotations

from typing import Any

try:
    from app.contracts import FleetSummary, RigUnit
    from app.render.india_map_png import _get_six_relocation_rows
    from app.rigs.india_eez_dataset import (
        ACTIVE_48H_STORM_ZONES,
        INDIA_120_WELL_REGISTRY,
        get_india_coastline_layer_values,
    )
    from app.rigs.metocean_engine import compute_marine_weather_forecast
except ImportError:
    from contracts import FleetSummary, RigUnit
    from render.india_map_png import _get_six_relocation_rows
    from rigs.india_eez_dataset import (
        ACTIVE_48H_STORM_ZONES,
        INDIA_120_WELL_REGISTRY,
        get_india_coastline_layer_values,
    )
    from rigs.metocean_engine import compute_marine_weather_forecast

VEGA_LITE_SCHEMA: str = "https://vega.github.io/schema/vega-lite/v5.json"
SPEC_KEY: str = "spec"
SPEC_POINTER: str = f"/{SPEC_KEY}"

# Continental Shelf <200m Bathymetry Polygon along Western & Eastern Indian Margins
_SHELF_BATHYMETRY_VALUES: list[dict[str, Any]] = [
    {"longitude": 67.0, "latitude": 23.8, "order": 1, "group": "shelf"},
    {"longitude": 68.8, "latitude": 22.5, "order": 2, "group": "shelf"},
    {"longitude": 72.6, "latitude": 21.6, "order": 3, "group": "shelf"},
    {"longitude": 72.8, "latitude": 19.0, "order": 4, "group": "shelf"},
    {"longitude": 74.8, "latitude": 13.0, "order": 5, "group": "shelf"},
    {"longitude": 77.5, "latitude": 8.0, "order": 6, "group": "shelf"},
    {"longitude": 80.3, "latitude": 13.1, "order": 7, "group": "shelf"},
    {"longitude": 82.5, "latitude": 17.0, "order": 8, "group": "shelf"},
    {"longitude": 88.5, "latitude": 21.5, "order": 9, "group": "shelf"},
    {"longitude": 89.0, "latitude": 19.8, "order": 10, "group": "shelf"},
    {"longitude": 83.6, "latitude": 15.6, "order": 11, "group": "shelf"},
    {"longitude": 81.2, "latitude": 12.2, "order": 12, "group": "shelf"},
    {"longitude": 77.5, "latitude": 6.8, "order": 13, "group": "shelf"},
    {"longitude": 73.2, "latitude": 12.2, "order": 14, "group": "shelf"},
    {"longitude": 70.2, "latitude": 18.2, "order": 15, "group": "shelf"},
    {"longitude": 68.5, "latitude": 20.5, "order": 16, "group": "shelf"},
    {"longitude": 66.6, "latitude": 23.2, "order": 17, "group": "shelf"},
]


def build_rig_fleet_map_spec(summary: FleetSummary) -> dict[str, Any]:
    """Build a Full-Width (680px) 3-Tier Dark Bathymetric Vega-Lite v5 Command Infographic."""
    coastline_values = get_india_coastline_layer_values()
    storm_zones = summary.active_storm_zones or ACTIVE_48H_STORM_ZONES
    relocation_rows = _get_six_relocation_rows()

    recommended_well_ids = {r["dest_well"] for r in relocation_rows}
    origin_well_ids = {r["orig_well"] for r in relocation_rows}

    source_wells = summary.wells or INDIA_120_WELL_REGISTRY
    well_points: list[dict[str, Any]] = []
    for w in source_wells:
        if w.well_id in recommended_well_ids:
            well_state = "SAFE_TARGET_WELL (◆ Relocate Here)"
        elif w.well_id in origin_well_ids or w.status.value == "STORM_LOCKED":
            well_state = "STORM_LOCKED_WELL (🔴 Do Not Drill)"
        else:
            well_state = "SAFE_READY_WELL (🟢 Calm Metocean)"
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

    # Build explicit origin -> destination route segments and badge points for [1]..[6]
    escape_segments: list[dict[str, Any]] = []
    origin_badges: list[dict[str, Any]] = []
    dest_diamonds: list[dict[str, Any]] = []
    for r in relocation_rows:
        label_offset_dy = -12 if r["idx"] in (1, 2, 5) else 13
        escape_segments.append({
            "idx": r["idx"],
            "badge": f"[{r['idx']}]",
            "rig_id": r["rig_id"],
            "rig_name": r["rig_name"],
            "basin": r["basin"],
            "orig_well": r["orig_well"],
            "orig_lat": r["orig_lat"],
            "orig_lon": r["orig_lon"],
            "dest_well": r["dest_well"],
            "dest_lat": r["dest_lat"],
            "dest_lon": r["dest_lon"],
            "dist_nm": r["dist_nm"],
            "transit_hrs": r["transit_hrs"],
            "storm_hs": r["storm_hs"],
            "safe_hs": r["safe_hs"],
            "savings_cr": r["savings_cr"],
            "zoom_call": f"[{r['idx']}] {r['rig_name']} ➔ {r['dest_well']} ({r['dist_nm']} NM | ₹{r['savings_cr']}Cr)",
            "dy": label_offset_dy,
        })
        origin_badges.append({
            "idx": str(r["idx"]),
            "badge": f"[{r['idx']}]",
            "rig_id": r["rig_id"],
            "rig_name": r["rig_name"],
            "basin": r["basin"],
            "latitude": r["orig_lat"],
            "longitude": r["orig_lon"],
            "orig_well": r["orig_well"],
            "dest_well": r["dest_well"],
            "storm_hs": r["storm_hs"],
            "savings_cr": r["savings_cr"],
        })
        dest_diamonds.append({
            "idx": str(r["idx"]),
            "dest_well": r["dest_well"],
            "rig_name": r["rig_name"],
            "basin": r["basin"],
            "latitude": r["dest_lat"],
            "longitude": r["dest_lon"],
            "safe_hs": r["safe_hs"],
            "dist_nm": r["dist_nm"],
            "savings_cr": r["savings_cr"],
        })

    storm_labels = [
        {
            "longitude": 71.40,
            "latitude": 20.55,
            "banner": "🔴 STORM CIRCLE 1: MUMBAI HIGH (Hs=4.2m, 46kt — EVACUATE [1]–[4])",
        },
        {
            "longitude": 82.20,
            "latitude": 17.45,
            "banner": "🔴 STORM CIRCLE 2: KG-DWN BASIN (Hs=3.8m, 42kt — EVACUATE [5]–[6])",
        },
    ]

    # 48-Hour Weather Forecast Series
    weather_series = summary.weather_series
    if not weather_series:
        weather_series = compute_marine_weather_forecast(19.25, 71.85, forecast_hours=48, step_hours=3)

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
            "threshold_m": 2.5,
        })

    # TIER 1: Full-Width India EEZ Bathymetric Command Map (680 x 420)
    main_map_panel: dict[str, Any] = {
        "width": 660,
        "height": 410,
        "view": {"fill": "#0B2545", "stroke": "#38BDF8", "strokeWidth": 1.5},
        "title": {
            "text": "PANEL A — INDIA EEZ BATHYMETRIC COMMAND MAP (20 Rigs, 120 Wells, 48h Red Storm Cones & Badges [1]–[6])",
            "subtitle": "Deep Blue = Deepwater (>1,000m)  |  Cyan Shelf = Shallow Shelf (<200m)  |  Tan = India Landmass  |  Scroll to Zoom & Hover any Well/Rig",
            "color": "#F8FAFC",
            "subtitleColor": "#93C5FD",
            "fontSize": 13,
            "subtitleFontSize": 11,
        },
        "layer": [
            # Layer 1: Continental Shelf Bathymetry (<200m)
            {
                "data": {"values": _SHELF_BATHYMETRY_VALUES},
                "mark": {
                    "type": "line",
                    "fill": "#134E7A",
                    "fillOpacity": 0.65,
                    "stroke": "#38BDF8",
                    "strokeDash": [4, 3],
                    "strokeWidth": 1.2,
                },
                "encoding": {
                    "x": {
                        "field": "longitude",
                        "type": "quantitative",
                        "scale": {"domain": [66.5, 89.5]},
                        "axis": {
                            "title": "Longitude (°E — Arabian Sea / Mumbai High ➔ Bay of Bengal / KG-DWN Basin)",
                            "grid": True,
                            "gridColor": "#1E3A8A",
                            "labelColor": "#E2E8F0",
                            "titleColor": "#93C5FD",
                        },
                    },
                    "y": {
                        "field": "latitude",
                        "type": "quantitative",
                        "scale": {"domain": [5.5, 24.5]},
                        "axis": {
                            "title": "Latitude (°N — Indian EEZ)",
                            "grid": True,
                            "gridColor": "#1E3A8A",
                            "labelColor": "#E2E8F0",
                            "titleColor": "#93C5FD",
                        },
                    },
                    "order": {"field": "order", "type": "quantitative"},
                },
            },
            # Layer 2: India & Sri Lanka Landmass (Golden-Tan Terrain Fill + Pan/Zoom Bind)
            {
                "params": [{"name": "eez_pan_zoom", "select": "interval", "bind": "scales"}],
                "data": {"values": coastline_values},
                "mark": {
                    "type": "line",
                    "fill": "#C89D66",
                    "fillOpacity": 0.92,
                    "stroke": "#FDE68A",
                    "strokeWidth": 2.0,
                },
                "encoding": {
                    "x": {"field": "longitude", "type": "quantitative"},
                    "y": {"field": "latitude", "type": "quantitative"},
                    "detail": {"field": "group", "type": "nominal"},
                    "order": {"field": "order", "type": "quantitative"},
                },
            },
            # Layer 3: Outer 48h Storm Warning Halo (Red Dashed Circle)
            {
                "data": {"values": storm_zones},
                "mark": {
                    "type": "circle",
                    "size": 9500,
                    "color": "#EF4444",
                    "opacity": 0.22,
                    "stroke": "#F87171",
                    "strokeWidth": 2.2,
                    "strokeDash": [6, 4],
                },
                "encoding": {
                    "x": {"field": "longitude", "type": "quantitative"},
                    "y": {"field": "latitude", "type": "quantitative"},
                },
            },
            # Layer 4: Inner 48h Cyclone Core (High-Opacity Crimson Circle)
            {
                "data": {"values": storm_zones},
                "mark": {
                    "type": "circle",
                    "size": 4200,
                    "color": "#DC2626",
                    "opacity": 0.38,
                    "stroke": "#FECACA",
                    "strokeWidth": 2.5,
                },
                "encoding": {
                    "x": {"field": "longitude", "type": "quantitative"},
                    "y": {"field": "latitude", "type": "quantitative"},
                    "tooltip": [
                        {"field": "storm_id", "type": "nominal", "title": "Storm Circle ID"},
                        {"field": "storm_name", "type": "nominal", "title": "48h Weather System"},
                        {"field": "basin", "type": "nominal", "title": "Basin"},
                        {"field": "peak_hs_m", "type": "quantitative", "title": "Peak Wave Hs (m)"},
                        {"field": "peak_wind_kts", "type": "quantitative", "title": "Peak Wind (kts)"},
                    ],
                },
            },
            # Layer 5: 120 Candidate & Active Offshore Wells
            {
                "data": {"values": well_points},
                "mark": {"type": "circle", "stroke": "#0F172A", "strokeWidth": 0.9, "opacity": 0.92},
                "encoding": {
                    "x": {"field": "longitude", "type": "quantitative"},
                    "y": {"field": "latitude", "type": "quantitative"},
                    "size": {
                        "field": "well_state",
                        "type": "nominal",
                        "scale": {
                            "domain": [
                                "SAFE_READY_WELL (🟢 Calm Metocean)",
                                "STORM_LOCKED_WELL (🔴 Do Not Drill)",
                                "SAFE_TARGET_WELL (◆ Relocate Here)",
                            ],
                            "range": [55, 85, 190],
                        },
                        "legend": None,
                    },
                    "color": {
                        "field": "well_state",
                        "type": "nominal",
                        "scale": {
                            "domain": [
                                "SAFE_READY_WELL (🟢 Calm Metocean)",
                                "STORM_LOCKED_WELL (🔴 Do Not Drill)",
                                "SAFE_TARGET_WELL (◆ Relocate Here)",
                            ],
                            "range": ["#10B981", "#EF4444", "#22C55E"],
                        },
                        "legend": {
                            "title": "Map Legend: 120 Offshore Wells & Storm Zones",
                            "orient": "top",
                            "labelColor": "#F8FAFC",
                            "titleColor": "#FACC15",
                            "labelFontSize": 11,
                            "titleFontSize": 11,
                        },
                    },
                    "tooltip": [
                        {"field": "well_id", "type": "nominal", "title": "Well ID"},
                        {"field": "well_name", "type": "nominal", "title": "Well Name"},
                        {"field": "basin", "type": "nominal", "title": "Basin"},
                        {"field": "well_state", "type": "nominal", "title": "48h Status"},
                        {"field": "latitude", "type": "quantitative", "title": "Lat (°N)", "format": ".3f"},
                        {"field": "longitude", "type": "quantitative", "title": "Lon (°E)", "format": ".3f"},
                        {"field": "peak_48h_hs_m", "type": "quantitative", "title": "48h Wave Hs (m)"},
                    ],
                },
            },
            # Layer 6: Bold Green Escape Route Vectors (Origin -> Safe Target Well)
            {
                "data": {"values": escape_segments},
                "mark": {"type": "rule", "color": "#22C55E", "strokeWidth": 3.5},
                "encoding": {
                    "x": {"field": "orig_lon", "type": "quantitative"},
                    "y": {"field": "orig_lat", "type": "quantitative"},
                    "x2": {"field": "dest_lon"},
                    "y2": {"field": "dest_lat"},
                    "tooltip": [
                        {"field": "badge", "type": "nominal", "title": "Map Badge"},
                        {"field": "rig_name", "type": "nominal", "title": "Rig"},
                        {"field": "orig_well", "type": "nominal", "title": "Evacuate From (🔴)"},
                        {"field": "dest_well", "type": "nominal", "title": "Relocate To (🟢)"},
                        {"field": "dist_nm", "type": "quantitative", "title": "Distance (NM)"},
                        {"field": "savings_cr", "type": "quantitative", "title": "Avoided NPT (₹ Cr)"},
                    ],
                },
            },
            # Layer 7: Yellow Numbered Rig Origin Badges [1]–[6]
            {
                "data": {"values": origin_badges},
                "mark": {
                    "type": "circle",
                    "size": 340,
                    "color": "#FACC15",
                    "stroke": "#0F172A",
                    "strokeWidth": 2.0,
                },
                "encoding": {
                    "x": {"field": "longitude", "type": "quantitative"},
                    "y": {"field": "latitude", "type": "quantitative"},
                    "tooltip": [
                        {"field": "badge", "type": "nominal", "title": "Rig Index"},
                        {"field": "rig_id", "type": "nominal", "title": "Rig ID"},
                        {"field": "rig_name", "type": "nominal", "title": "Rig Name"},
                        {"field": "orig_well", "type": "nominal", "title": "Storm-Locked Well"},
                        {"field": "dest_well", "type": "nominal", "title": "Target Safe Well"},
                        {"field": "savings_cr", "type": "quantitative", "title": "Saved (₹ Cr)"},
                    ],
                },
            },
            # Layer 8: Bold Black Badge Numbers Inside Yellow Circles
            {
                "data": {"values": origin_badges},
                "mark": {
                    "type": "text",
                    "fontSize": 11,
                    "fontWeight": "bold",
                    "color": "#0F172A",
                },
                "encoding": {
                    "x": {"field": "longitude", "type": "quantitative"},
                    "y": {"field": "latitude", "type": "quantitative"},
                    "text": {"field": "idx", "type": "nominal"},
                },
            },
            # Layer 9: High-Contrast Storm Circle Banners
            {
                "data": {"values": storm_labels},
                "mark": {
                    "type": "text",
                    "fontSize": 11,
                    "fontWeight": "bold",
                    "color": "#FEF08A",
                },
                "encoding": {
                    "x": {"field": "longitude", "type": "quantitative"},
                    "y": {"field": "latitude", "type": "quantitative"},
                    "text": {"field": "banner", "type": "nominal"},
                },
            },
        ],
    }

    # TIER 2: High-Magnification Split Basin Zoom Panels ([1]–[4] Mumbai High & [5]–[6] KG-DWN)
    mumbai_escape = [r for r in escape_segments if r["idx"] in (1, 2, 3, 4)]
    kg_escape = [r for r in escape_segments if r["idx"] in (5, 6)]

    def _build_basin_zoom_panel(
        title_str: str,
        subtitle_str: str,
        segments: list[dict[str, Any]],
        lon_domain: list[float],
        lat_domain: list[float],
        storm_lon: float,
        storm_lat: float,
    ) -> dict[str, Any]:
        return {
            "width": 310,
            "height": 235,
            "view": {"fill": "#0B2545", "stroke": "#38BDF8", "strokeWidth": 1.5},
            "title": {
                "text": title_str,
                "subtitle": subtitle_str,
                "color": "#FACC15",
                "subtitleColor": "#E2E8F0",
                "fontSize": 11,
                "subtitleFontSize": 10,
            },
            "layer": [
                # Red Storm Cone Sector in Zoom View
                {
                    "data": {"values": [{"lon": storm_lon, "lat": storm_lat}]},
                    "mark": {
                        "type": "circle",
                        "size": 18000,
                        "color": "#EF4444",
                        "opacity": 0.25,
                        "stroke": "#F87171",
                        "strokeDash": [5, 4],
                        "strokeWidth": 2.0,
                    },
                    "encoding": {
                        "x": {
                            "field": "lon",
                            "type": "quantitative",
                            "scale": {"domain": lon_domain},
                            "axis": {"title": "Longitude (°E)", "grid": True, "gridColor": "#1E3A8A", "labelColor": "#CBD5E1", "titleColor": "#93C5FD"},
                        },
                        "y": {
                            "field": "lat",
                            "type": "quantitative",
                            "scale": {"domain": lat_domain},
                            "axis": {"title": "Latitude (°N)", "grid": True, "gridColor": "#1E3A8A", "labelColor": "#CBD5E1", "titleColor": "#93C5FD"},
                        },
                    },
                },
                # Green Escape Trajectory Lines
                {
                    "data": {"values": segments},
                    "mark": {"type": "rule", "color": "#22C55E", "strokeWidth": 4.0},
                    "encoding": {
                        "x": {"field": "orig_lon", "type": "quantitative"},
                        "y": {"field": "orig_lat", "type": "quantitative"},
                        "x2": {"field": "dest_lon"},
                        "y2": {"field": "dest_lat"},
                    },
                },
                # Green Target Safe Diamond Wells
                {
                    "data": {"values": segments},
                    "mark": {
                        "type": "point",
                        "shape": "diamond",
                        "filled": True,
                        "size": 260,
                        "color": "#10B981",
                        "stroke": "#FFFFFF",
                        "strokeWidth": 1.8,
                    },
                    "encoding": {
                        "x": {"field": "dest_lon", "type": "quantitative"},
                        "y": {"field": "dest_lat", "type": "quantitative"},
                        "tooltip": [
                            {"field": "dest_well", "type": "nominal", "title": "Safe Target Well (🟢)"},
                            {"field": "rig_name", "type": "nominal", "title": "Incoming Rig"},
                            {"field": "safe_hs", "type": "quantitative", "title": "Safe Wave Hs (m)"},
                            {"field": "dist_nm", "type": "quantitative", "title": "Distance (NM)"},
                        ],
                    },
                },
                # Yellow Origin Rig Badges [1]..[6]
                {
                    "data": {"values": segments},
                    "mark": {
                        "type": "circle",
                        "size": 420,
                        "color": "#FACC15",
                        "stroke": "#0F172A",
                        "strokeWidth": 2.0,
                    },
                    "encoding": {
                        "x": {"field": "orig_lon", "type": "quantitative"},
                        "y": {"field": "orig_lat", "type": "quantitative"},
                    },
                },
                # Bold Badge Numbers Inside Yellow Circles
                {
                    "data": {"values": segments},
                    "mark": {"type": "text", "fontSize": 12, "fontWeight": "bold", "color": "#0F172A"},
                    "encoding": {
                        "x": {"field": "orig_lon", "type": "quantitative"},
                        "y": {"field": "orig_lat", "type": "quantitative"},
                        "text": {"field": "idx", "type": "nominal"},
                    },
                },
                # Crisp Callout Labels at Safe Destination Wells
                {
                    "data": {"values": segments},
                    "mark": {
                        "type": "text",
                        "fontSize": 10,
                        "fontWeight": "bold",
                        "color": "#86EFAC",
                        "dy": 14,
                    },
                    "encoding": {
                        "x": {"field": "dest_lon", "type": "quantitative"},
                        "y": {"field": "dest_lat", "type": "quantitative"},
                        "text": {"field": "zoom_call", "type": "nominal"},
                    },
                },
            ],
        }

    zoom_row: dict[str, Any] = {
        "hconcat": [
            _build_basin_zoom_panel(
                "PANEL B1 — MUMBAI HIGH ZOOM: ESCAPE ROUTES [1]–[4]",
                "Red Circle Origin Wells (Hs=3.7–4.2m) ➔ Green Safe Wells (Hs=1.3–1.5m)",
                mumbai_escape,
                [71.0, 72.1],
                [18.65, 19.70],
                71.35,
                19.42,
            ),
            _build_basin_zoom_panel(
                "PANEL B2 — KG-DWN BASIN ZOOM: ESCAPE ROUTES [5]–[6]",
                "Red Circle Origin Wells (Hs=3.7–3.8m) ➔ Green Safe Wells (Hs=1.3–1.4m)",
                kg_escape,
                [82.0, 82.8],
                [15.70, 16.55],
                82.22,
                16.38,
            ),
        ]
    }

    # TIER 3: 48-Hour Metocean Wave Height Timeline
    weather_panel: dict[str, Any] = {
        "width": 660,
        "height": 140,
        "view": {"fill": "#0B2545", "stroke": "#38BDF8", "strokeWidth": 1.5},
        "title": {
            "text": "PANEL C — 48-Hour Google WeatherNext (GenCast + GraphCast) Significant Wave Height (Hs) vs 2.5m Unlatch Safety Cutoff",
            "color": "#F8FAFC",
            "fontSize": 12,
        },
        "data": {"values": weather_rows},
        "layer": [
            {
                "mark": {"type": "area", "color": "#38BDF8", "opacity": 0.22},
                "encoding": {
                    "x": {
                        "field": "hour",
                        "type": "quantitative",
                        "axis": {
                            "title": "Forecast Horizon (+Hours Ahead)",
                            "grid": True,
                            "gridColor": "#1E3A8A",
                            "labelColor": "#E2E8F0",
                            "titleColor": "#93C5FD",
                        },
                    },
                    "y": {
                        "field": "hs_p05",
                        "type": "quantitative",
                        "axis": {
                            "title": "Wave Height Hs (m)",
                            "grid": True,
                            "gridColor": "#1E3A8A",
                            "labelColor": "#E2E8F0",
                            "titleColor": "#93C5FD",
                        },
                    },
                    "y2": {"field": "hs_p95"},
                },
            },
            {
                "mark": {"type": "line", "color": "#38BDF8", "strokeWidth": 2.8, "point": {"filled": True, "size": 65, "color": "#FACC15"}},
                "encoding": {
                    "x": {"field": "hour", "type": "quantitative"},
                    "y": {"field": "hs_m", "type": "quantitative"},
                    "tooltip": [
                        {"field": "hour", "type": "quantitative", "title": "Lead Time (+hrs)"},
                        {"field": "hs_m", "type": "quantitative", "title": "Significant Wave Height Hs (m)"},
                        {"field": "wind_kts", "type": "quantitative", "title": "Wind Speed (kts)"},
                    ],
                },
            },
            {
                "mark": {"type": "rule", "color": "#EF4444", "strokeDash": [5, 4], "strokeWidth": 2.4},
                "encoding": {"y": {"field": "threshold_m", "type": "quantitative"}},
            },
        ],
    }

    return {
        "$schema": VEGA_LITE_SCHEMA,
        "description": "ORMWO 3-Tier Bathymetric Command Infographic: India EEZ Map + Mumbai High & KG-DWN Basin Escape Zooms + 48h Wave Forecast",
        "background": "#07192F",
        "padding": {"left": 12, "right": 12, "top": 12, "bottom": 12},
        "vconcat": [
            main_map_panel,
            zoom_row,
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
