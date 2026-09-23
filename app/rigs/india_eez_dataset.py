"""India Exclusive Economic Zone (EEZ) Spatial Dataset: Coastline, 20 Rigs & 120 Wells.

In : None (deterministic geospatial coordinate tables).
Out:
  - INDIA_COASTLINE_POINTS: Polygon/polyline coordinates tracing India's mainland coast,
    Sri Lanka, and Andaman & Nicobar islands for Vega-Lite v5 cartographic rendering.
  - INDIA_20_RIG_FLEET: 20 realistic offshore drilling units across Indian sedimentary basins.
  - INDIA_120_WELL_REGISTRY: 120 pinpoint offshore well locations with water depth,
    required hull type, and 48h metocean exposure status.
"""

from __future__ import annotations

from typing import Any

try:
    from app.contracts import (
        RigCoordinates,
        RigOperationalStatus,
        RigTelemetry,
        RigType,
        RigUnit,
        WellPad,
        WellReadinessStatus,
    )
except ImportError:
    from contracts import (
        RigCoordinates,
        RigOperationalStatus,
        RigTelemetry,
        RigType,
        RigUnit,
        WellPad,
        WellReadinessStatus,
    )


# ==============================================================================
# 1. India Mainland Coastline & Island Outlines (for Vega-Lite Geospatial Layer)
# ==============================================================================

# Ordered coastal perimeter from Kutch (West) -> Kanyakumari (South) -> Sundarbans (East)
# Closed inland across Northern Peninsula so Vega-Lite can render both fill area and border stroke.
INDIA_MAINLAND_POLYGON: list[tuple[float, float]] = [
    # Kutch & Gujarat Peninsula
    (68.10, 23.65), (68.45, 23.10), (68.95, 22.45), (69.65, 22.50),
    (70.05, 22.30), (69.05, 22.20), (69.60, 21.55), (70.40, 20.90),
    (71.15, 20.75), (72.15, 21.65), (72.65, 22.25), (72.90, 21.65),
    (72.82, 20.95), (72.75, 20.10),
    # Mumbai, Konkan & Goa Coast
    (72.82, 19.07), (72.95, 18.40), (73.15, 17.65), (73.30, 16.98),
    (73.48, 16.05), (73.82, 15.42), (74.12, 14.80),
    # Karnataka & Kerala Coast
    (74.45, 14.10), (74.82, 12.88), (75.35, 11.88), (75.78, 11.25),
    (76.18, 10.52), (76.26, 9.95), (76.58, 8.88), (77.05, 8.38),
    # Kanyakumari Apex
    (77.55, 8.08),
    # Tamil Nadu / Coromandel / Cauvery Coast
    (78.15, 8.78), (79.12, 9.28), (79.32, 9.28), (79.84, 10.30),
    (79.85, 10.76), (79.82, 11.45), (79.85, 11.95), (80.18, 12.65),
    (80.28, 13.08), (80.32, 13.65),
    # Andhra Pradesh / Krishna-Godavari (KG) Basin Delta
    (80.08, 14.45), (80.18, 15.35), (80.85, 15.75), (81.15, 15.95),
    (81.82, 16.38), (82.25, 16.65), (82.28, 16.98), (82.65, 17.32),
    (83.30, 17.70), (84.10, 18.35), (84.85, 19.15),
    # Odisha / Mahanadi & West Bengal Coast
    (85.82, 19.80), (86.67, 20.26), (86.95, 20.75), (87.08, 21.15),
    (87.52, 21.62), (88.10, 21.95), (88.65, 21.65), (89.10, 21.65),
    # Northern Peninsula Closure (for clean landmass shading)
    (88.20, 23.80), (83.00, 24.30), (77.00, 24.30), (71.50, 24.20),
    (68.10, 23.65),
]

SRI_LANKA_POLYGON: list[tuple[float, float]] = [
    (79.85, 9.75), (80.25, 9.60), (81.20, 8.55), (81.85, 7.40),
    (81.20, 6.12), (80.20, 5.95), (79.85, 6.92), (79.75, 8.25),
    (79.85, 9.75),
]


def get_india_coastline_layer_values() -> list[dict[str, Any]]:
    """Return ordered coastline vertices for Vega-Lite landmass rendering."""
    rows: list[dict[str, Any]] = []
    for order_idx, (lon, lat) in enumerate(INDIA_MAINLAND_POLYGON):
        rows.append({
            "group": "India Mainland",
            "order": order_idx,
            "longitude": lon,
            "latitude": lat,
        })
    for order_idx, (lon, lat) in enumerate(SRI_LANKA_POLYGON):
        rows.append({
            "group": "Sri Lanka",
            "order": order_idx,
            "longitude": lon,
            "latitude": lat,
        })
    return rows


# ==============================================================================
# 2. Active Storm Hazard Zones (48h Forecast Cone)
# ==============================================================================

ACTIVE_48H_STORM_ZONES: list[dict[str, Any]] = [
    {
        "storm_id": "CYC-ARB-2026-01",
        "storm_name": "Arabian Sea Severe Cyclonic Surge (T+32h)",
        "basin": "Mumbai High & Bassein Offshore",
        "latitude": 19.22,
        "longitude": 71.65,
        "radius_deg": 0.95,
        "peak_hs_m": 4.4,
        "peak_wind_kts": 48.0,
        "swell_period_s": 13.8,
        "threat_level": "SEVERE",
    },
    {
        "storm_id": "SWELL-BOB-2026-02",
        "storm_name": "Bay of Bengal Deepwater Swell Front (T+40h)",
        "basin": "Krishna-Godavari Deepwater North",
        "latitude": 16.58,
        "longitude": 82.65,
        "radius_deg": 0.55,
        "peak_hs_m": 3.1,
        "peak_wind_kts": 37.5,
        "swell_period_s": 12.9,
        "threat_level": "MODERATE",
    },
]


def is_coordinate_in_storm_zone(lat: float, lon: float) -> tuple[bool, dict[str, Any] | None]:
    """Check if (lat, lon) falls within any active 48-hour critical weather hazard radius."""
    for zone in ACTIVE_48H_STORM_ZONES:
        dlat = lat - float(zone["latitude"])
        dlon = lon - float(zone["longitude"])
        dist_deg = (dlat * dlat + dlon * dlon) ** 0.5
        if dist_deg <= float(zone["radius_deg"]):
            return True, zone
    return False, None


# ==============================================================================
# 3. The 20 Realistic Indian Offshore & Coastal Rigs (ORMWO Fleet)
# ==============================================================================

def _build_20_rig_fleet() -> list[RigUnit]:
    specs = [
        # (rig_id, name, operator, rig_type, status, lat, lon, water_depth, basin, block, well_id, target_depth, md, rop, cost_inr, unlatch_hrs)
        ("RIG-OFFSHORE-01", "Ocean Titan", "ONGC", RigType.OFFSHORE_DRILLSHIP, RigOperationalStatus.DRILLING, 19.38, 71.42, 92.0, "Mumbai High Offshore", "MB-OSN-2005/1", "MH-N-001", 3450.0, 2845.0, 12.4, 11800000.0, 10),
        ("RIG-OFFSHORE-02", "Deepwater Explorer", "ONGC / RIL JV", RigType.OFFSHORE_SEMISUB, RigOperationalStatus.DRILLING, 16.52, 82.58, 1240.0, "Krishna-Godavari Deepwater", "KG-DWN-98/3", "KG-D6-081", 4850.0, 4210.0, 6.8, 12000000.0, 12),
        ("RIG-OFFSHORE-03", "Sagar Bhushan", "ONGC", RigType.OFFSHORE_JACKUP, RigOperationalStatus.DRILLING, 18.92, 72.18, 64.0, "Bassein Offshore", "BSN-DEV-03", "BSN-W-031", 2650.0, 2410.0, 9.1, 10400000.0, 14),
        ("RIG-OFFSHORE-04", "Sagar Samrat II", "ONGC", RigType.OFFSHORE_JACKUP, RigOperationalStatus.DRILLING, 19.25, 71.85, 78.0, "Mumbai High Offshore", "MB-OSN-2005/2", "MH-N-004", 3100.0, 2680.0, 10.5, 11500000.0, 14),
        ("RIG-OFFSHORE-05", "Sagar Jyoti", "ONGC", RigType.OFFSHORE_JACKUP, RigOperationalStatus.DRILLING, 19.52, 71.30, 81.0, "Mumbai High Offshore", "MB-OSN-2005/1", "MH-N-008", 2950.0, 2150.0, 11.2, 10800000.0, 14),
        ("RIG-OFFSHORE-06", "Sagar Ratna", "ONGC", RigType.OFFSHORE_JACKUP, RigOperationalStatus.STANDBY, 19.15, 71.68, 74.0, "Mumbai High Offshore", "MB-OSN-2005/3", "MH-S-015", 2800.0, 2800.0, 0.0, 10600000.0, 12),
        ("RIG-OFFSHORE-07", "Virtue I", "ONGC Charter", RigType.OFFSHORE_JACKUP, RigOperationalStatus.DRILLING, 19.44, 71.55, 84.0, "Mumbai High Offshore", "MB-OSN-2005/2", "MH-N-011", 3200.0, 1940.0, 13.0, 11000000.0, 14),
        ("RIG-OFFSHORE-08", "Greatdrill Chaaya", "ONGC Charter", RigType.OFFSHORE_JACKUP, RigOperationalStatus.DRILLING, 19.08, 71.92, 68.0, "Bassein Offshore", "BSN-DEV-01", "BSN-W-035", 2750.0, 2210.0, 10.8, 10200000.0, 14),
        ("RIG-OFFSHORE-09", "Sagar Gaurav", "ONGC", RigType.OFFSHORE_JACKUP, RigOperationalStatus.DRILLING, 19.02, 72.08, 61.0, "Bassein Offshore", "BSN-DEV-02", "BSN-W-039", 2550.0, 1820.0, 11.6, 10100000.0, 14),
        ("RIG-OFFSHORE-10", "Sagar Shakti", "ONGC", RigType.OFFSHORE_JACKUP, RigOperationalStatus.STANDBY, 18.84, 72.26, 55.0, "Bassein Offshore", "BSN-DEV-04", "BSN-W-042", 2400.0, 2400.0, 0.0, 10000000.0, 12),
        ("RIG-OFFSHORE-11", "Sagar Kiran", "ONGC", RigType.OFFSHORE_JACKUP, RigOperationalStatus.DRILLING, 18.25, 72.38, 52.0, "Heera-Panna-Mukta Offshore", "HPM-OSN-01", "HPM-S-051", 2350.0, 1760.0, 14.2, 10300000.0, 14),
        ("RIG-OFFSHORE-12", "Sagar Uday", "ONGC", RigType.OFFSHORE_JACKUP, RigOperationalStatus.DRILLING, 18.02, 72.44, 49.0, "Heera-Panna-Mukta Offshore", "HPM-OSN-02", "HPM-S-056", 2280.0, 1590.0, 13.5, 10250000.0, 14),
        ("RIG-OFFSHORE-13", "Jindal Explorer", "ONGC Charter", RigType.OFFSHORE_JACKUP, RigOperationalStatus.DRILLING, 17.85, 72.50, 46.0, "Ratna South Offshore", "R-SERIES-01", "HPM-S-061", 2190.0, 1420.0, 12.9, 10500000.0, 14),
        ("RIG-OFFSHORE-14", "Sagar Vijay", "ONGC", RigType.OFFSHORE_DRILLSHIP, RigOperationalStatus.DRILLING, 22.15, 68.42, 115.0, "Kutch-Saurashtra Offshore", "GK-OSN-2009/1", "GK-W-069", 3600.0, 2910.0, 9.8, 11600000.0, 10),
        ("RIG-OFFSHORE-15", "Greatdrill Chitra", "ONGC Charter", RigType.OFFSHORE_JACKUP, RigOperationalStatus.DRILLING, 20.85, 70.15, 58.0, "Kutch-Saurashtra Offshore", "GS-OSN-2004/1", "GK-W-074", 2700.0, 2050.0, 11.4, 10400000.0, 14),
        ("RIG-OFFSHORE-16", "Dhirubhai Deepwater KG1", "ONGC", RigType.OFFSHORE_DRILLSHIP, RigOperationalStatus.DRILLING, 16.05, 82.15, 980.0, "Krishna-Godavari Deepwater", "KG-DWN-98/2", "KG-D6-086", 4600.0, 3890.0, 8.2, 12200000.0, 10),
        ("RIG-OFFSHORE-17", "Platinum Explorer", "ONGC", RigType.OFFSHORE_DRILLSHIP, RigOperationalStatus.DRILLING, 15.88, 81.92, 760.0, "Krishna-Godavari Deepwater", "KG-DWN-98/2", "KG-D6-091", 4350.0, 3420.0, 8.9, 11900000.0, 10),
        ("RIG-OFFSHORE-18", "Aban Ice", "ONGC Charter", RigType.OFFSHORE_DRILLSHIP, RigOperationalStatus.STANDBY, 16.22, 82.05, 420.0, "Krishna-Godavari Shallow", "KG-OSN-2004/1", "KG-D6-096", 3500.0, 3500.0, 0.0, 11100000.0, 10),
        ("RIG-OFFSHORE-19", "Discovery I", "ONGC", RigType.OFFSHORE_JACKUP, RigOperationalStatus.DRILLING, 11.25, 80.18, 65.0, "Cauvery Offshore", "CY-OSN-97/1", "CY-E-103", 2900.0, 2340.0, 10.7, 10300000.0, 14),
        ("RIG-OFFSHORE-20", "Sagar Pragati", "ONGC", RigType.OFFSHORE_JACKUP, RigOperationalStatus.DRILLING, 20.05, 87.12, 72.0, "Mahanadi Offshore", "MN-OSN-2000/2", "MN-E-113", 3050.0, 2490.0, 9.5, 10450000.0, 14),
    ]

    fleet: list[RigUnit] = []
    for (
        rig_id, name, operator, rtype, status, lat, lon, wdepth,
        basin, block, well_id, tdepth, md, rop, cost_inr, unlatch_hrs
    ) in specs:
        telemetry = RigTelemetry(
            measured_depth_m=md,
            rate_of_penetration_m_hr=rop,
            hook_load_klbs=310.0 if rtype != RigType.OFFSHORE_SEMISUB else 445.0,
            standpipe_pressure_psi=3250.0 if rop > 0 else 450.0,
            rotary_rpm=108.0 if rop > 0 else 0.0,
            torque_kft_lbs=19.2 if rop > 0 else 0.0,
            gas_units_total=42.0 if rop > 0 else 8.0,
            active_mud_volume_bbl=1320.0,
        )
        fleet.append(
            RigUnit(
                rig_id=rig_id,
                rig_name=name,
                operator=operator,
                rig_type=rtype,
                status=status,
                location=RigCoordinates(
                    latitude=lat,
                    longitude=lon,
                    water_depth_m=wdepth,
                    basin_name=basin,
                    block_id=block,
                ),
                current_well_name=well_id,
                target_depth_m=tdepth,
                telemetry=telemetry,
                contract_expiry="2028-03-31",
                daily_operating_cost_inr=cost_inr,
                planned_release_date="2026-09-25T06:00:00Z",
                unlatch_lead_hours=unlatch_hrs,
            )
        )
    return fleet


INDIA_20_RIG_FLEET: list[RigUnit] = _build_20_rig_fleet()


# ==============================================================================
# 4. The 120 Pinpoint Indian Offshore Well Registry (Candidate & Active Wells)
# ==============================================================================

def _build_120_well_registry() -> list[WellPad]:
    """Generate 120 deterministic, realistic offshore wells across 7 Indian EEZ clusters."""
    active_well_to_rig = {r.current_well_name: r.rig_id for r in INDIA_20_RIG_FLEET}

    # Define 7 real Indian offshore basin clusters:
    # (prefix, basin_name, block_id, count, lat_start, lat_end, lon_start, lon_end, base_wdepth, req_hull)
    clusters = [
        ("MH-N", "Mumbai High Offshore", "MB-OSN-2005/1", 15, 19.20, 19.65, 71.18, 71.88, 80.0, "JACKUP"),
        ("MH-S", "Mumbai High Offshore", "MB-OSN-2005/3", 15, 18.98, 19.22, 71.35, 71.90, 72.0, "JACKUP"),
        ("BSN-W", "Bassein Offshore", "BSN-DEV-02", 20, 18.75, 19.12, 71.95, 72.35, 62.0, "JACKUP"),
        ("HPM-S", "Heera-Panna-Mukta Offshore", "HPM-OSN-01", 18, 17.65, 18.42, 72.25, 72.62, 50.0, "JACKUP"),
        ("GK-W", "Kutch-Saurashtra Offshore", "GK-OSN-2009/1", 12, 20.65, 22.35, 68.25, 70.35, 68.0, "JACKUP"),
        ("KG-D6", "Krishna-Godavari Deepwater", "KG-DWN-98/2", 22, 15.65, 16.72, 81.75, 82.82, 850.0, "DRILLSHIP"),
        ("CY-E", "Cauvery Offshore", "CY-OSN-97/1", 10, 10.68, 11.62, 79.98, 80.38, 65.0, "JACKUP"),
        ("MN-E", "Mahanadi Offshore", "MN-OSN-2000/2", 8, 19.78, 20.38, 86.85, 87.48, 74.0, "JACKUP"),
    ]

    wells: list[WellPad] = []
    global_idx = 1

    for prefix, basin, block, count, lat0, lat1, lon0, lon1, wdepth, req_hull in clusters:
        for i in range(count):
            well_id = f"{prefix}-{global_idx:03d}"
            # Deterministic golden-ratio lattice inside basin bounding box
            frac_lat = (i + 0.5) / count
            frac_lon = ((i * 7 + 3) % count) / max(count - 1, 1)
            lat = round(lat0 + frac_lat * (lat1 - lat0), 4)
            lon = round(lon0 + frac_lon * (lon1 - lon0), 4)

            # If this well is an active rig's well, snap to exact rig coordinates
            matching_rigs = [r for r in INDIA_20_RIG_FLEET if r.current_well_name == well_id]
            if matching_rigs:
                lat = matching_rigs[0].location.latitude
                lon = matching_rigs[0].location.longitude

            in_storm, storm_zone = is_coordinate_in_storm_zone(lat, lon)
            if in_storm and storm_zone is not None:
                peak_hs = round(float(storm_zone["peak_hs_m"]) - 0.3 * (i % 3), 2)
                peak_wind = round(float(storm_zone["peak_wind_kts"]) - 1.5 * (i % 3), 1)
            else:
                peak_hs = round(1.05 + 0.12 * (i % 4), 2)
                peak_wind = round(15.0 + 2.0 * (i % 4), 1)

            if well_id in active_well_to_rig:
                status = WellReadinessStatus.ACTIVE_DRILLING
                assigned_rig = active_well_to_rig[well_id]
            elif in_storm:
                status = WellReadinessStatus.STORM_LOCKED
                assigned_rig = None
            else:
                status = WellReadinessStatus.SAFE_READY_TO_SPUD
                assigned_rig = None

            wells.append(
                WellPad(
                    well_id=well_id,
                    well_name=f"{basin.split()[0]} Well #{global_idx:03d}",
                    basin_name=basin,
                    block_id=block,
                    latitude=lat,
                    longitude=lon,
                    water_depth_m=round(wdepth + (i % 5) * 8.0, 1),
                    target_depth_m=round(2400.0 + (global_idx % 12) * 180.0, 0),
                    required_rig_type=req_hull,
                    priority_rank=global_idx,
                    status=status,
                    assigned_rig_id=assigned_rig,
                    peak_48h_hs_m=peak_hs,
                    peak_48h_wind_kts=peak_wind,
                )
            )
            global_idx += 1

    return wells


INDIA_120_WELL_REGISTRY: list[WellPad] = _build_120_well_registry()


def resolve_rig_by_identifier(identifier: str | None) -> RigUnit:
    """Find a rig by ORMWO ID ('RIG-OFFSHORE-04'), legacy ID ('RIG-OFF-01'), or name ('Ocean Titan')."""
    if not identifier:
        return INDIA_20_RIG_FLEET[3]  # Default to RIG-OFFSHORE-04 (Sagar Samrat II in Mumbai High)

    q = identifier.strip().upper()
    # Normalize RIG-OFF-0X -> RIG-OFFSHORE-0X
    if q.startswith("RIG-OFF-") and not q.startswith("RIG-OFFSHORE-"):
        suffix = q.replace("RIG-OFF-", "")
        q_norm = f"RIG-OFFSHORE-{suffix}"
    else:
        q_norm = q

    for rig in INDIA_20_RIG_FLEET:
        if (
            q_norm == rig.rig_id.upper()
            or q in rig.rig_id.upper()
            or q in rig.rig_name.upper()
            or q in rig.current_well_name.upper()
            or q in rig.location.basin_name.upper()
        ):
            return rig

    return INDIA_20_RIG_FLEET[3]


def find_nearest_safe_candidate_well(origin_lat: float, origin_lon: float, rig_type: RigType) -> WellPad:
    """Pinpoint the nearest metocean-safe candidate well (Hs <= 2.5m, Wind <= 35 kts) from the 120-well registry."""
    safe_wells = [
        w for w in INDIA_120_WELL_REGISTRY
        if w.status == WellReadinessStatus.SAFE_READY_TO_SPUD
    ]
    if not safe_wells:
        return INDIA_120_WELL_REGISTRY[52]

    # Prefer matching hull capability (deepwater vs shallow jackup)
    want_deep = rig_type in (RigType.DRILLSHIP, RigType.OFFSHORE_DRILLSHIP, RigType.SEMI_SUB, RigType.OFFSHORE_SEMISUB)
    filtered = [
        w for w in safe_wells
        if (w.water_depth_m >= 100.0 if want_deep else w.water_depth_m <= 150.0)
    ] or safe_wells

    def dist_sq(w: WellPad) -> float:
        return (w.latitude - origin_lat) ** 2 + (w.longitude - origin_lon) ** 2

    return min(filtered, key=dist_sq)
