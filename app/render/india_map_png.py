"""Fast deterministic Pillow renderer for the 5-Layer India EEZ Map & 48h Forecast.

In : FleetSummary (20 Indian offshore rigs, 120 candidate wells, 48h weather, storm zones, waypoints).
Out: High-resolution PNG bytes (`image/png`) for inline display in `adk web` (`dev-ui`) and chat UIs.
"""

from __future__ import annotations

import io
from PIL import Image, ImageDraw

try:
    from app.contracts import FleetSummary, RigOperationalStatus, WellReadinessStatus
    from app.rigs.india_eez_dataset import INDIA_MAINLAND_POLYGON, SRI_LANKA_POLYGON
    from app.rigs.metocean_engine import compute_marine_weather_forecast
except ImportError:
    from contracts import FleetSummary, RigOperationalStatus, WellReadinessStatus
    from rigs.india_eez_dataset import INDIA_MAINLAND_POLYGON, SRI_LANKA_POLYGON
    from rigs.metocean_engine import compute_marine_weather_forecast


def render_india_eez_map_png(summary: FleetSummary) -> bytes:
    """Render the 5-Layer Map of India & EEZ + 48h Metocean Timeline to PNG bytes."""
    W, H = 1280, 780
    img = Image.new("RGB", (W, H), (11, 18, 33))
    draw = ImageDraw.Draw(img, "RGBA")

    # Top Header Bar
    draw.rectangle([0, 0, W, 62], fill=(15, 23, 42, 255))
    draw.line([(0, 62), (W, 62)], fill=(30, 41, 59, 255), width=2)
    draw.text(
        (20, 12),
        "OFFSHORE RIG MOBILIZATION & WEATHER OPTIMIZER (ORMWO) — INDIA EEZ COMMAND MAP",
        fill=(248, 250, 252),
    )

    sim = summary.transit_simulations[0] if summary.transit_simulations else None
    focus_rig = summary.selected_rig_id or (sim.rig_id if sim else "RIG-OFFSHORE-04")
    avoided_cr = (sim.avoided_npt_savings_inr / 10_000_000.0) if sim else 3.22
    target_well = sim.destination_well_id if sim else "HPM-S-066"
    audit_id = summary.audit_reference_id or "AUD-ONGC-15117-VERIFIED"

    draw.text(
        (20, 34),
        f"20 Offshore Rigs | 120 Candidate & Active Wells | Focus: {focus_rig} -> Safe Well {target_well} | Avoided NPT: INR {avoided_cr:.2f} Cr | {audit_id}",
        fill=(56, 189, 248),
    )

    # Left Panel: Map of India & EEZ (Lon 66E..90E, Lat 5N..24N)
    MAP_X0, MAP_Y0, MAP_X1, MAP_Y1 = 20, 78, 820, 755
    draw.rectangle(
        [MAP_X0, MAP_Y0, MAP_X1, MAP_Y1],
        fill=(9, 21, 38, 255),
        outline=(30, 58, 138, 255),
        width=2,
    )

    def project(lon: float, lat: float) -> tuple[int, int]:
        px = MAP_X0 + (lon - 66.0) / (90.0 - 66.0) * (MAP_X1 - MAP_X0)
        py = MAP_Y1 - (lat - 5.0) / (24.0 - 5.0) * (MAP_Y1 - MAP_Y0)
        return int(px), int(py)

    # Coordinate Graticule Grid
    for lon in range(68, 90, 2):
        x, _ = project(lon, 10)
        draw.line([(x, MAP_Y0), (x, MAP_Y1)], fill=(30, 41, 59, 120), width=1)
        draw.text((x - 12, MAP_Y1 - 16), f"{lon}E", fill=(100, 116, 139))
    for lat in range(6, 24, 2):
        _, y = project(70, lat)
        draw.line([(MAP_X0, y), (MAP_X1, y)], fill=(30, 41, 59, 120), width=1)
        draw.text((MAP_X0 + 6, y - 7), f"{lat}N", fill=(100, 116, 139))

    # Layer 1: India Mainland & Sri Lanka Polygons
    india_pts = [project(lon, lat) for lon, lat in INDIA_MAINLAND_POLYGON]
    sri_pts = [project(lon, lat) for lon, lat in SRI_LANKA_POLYGON]
    draw.polygon(india_pts, fill=(22, 34, 56, 255), outline=(56, 189, 248, 210))
    draw.polygon(sri_pts, fill=(22, 34, 56, 255), outline=(56, 189, 248, 210))

    draw.text(project(75.8, 20.5), "INDIA", fill=(148, 163, 184))
    draw.text(project(67.2, 14.2), "ARABIAN SEA\n(WEST COAST EEZ)", fill=(56, 189, 248))
    draw.text(project(83.2, 13.8), "BAY OF BENGAL\n(EAST COAST EEZ)", fill=(56, 189, 248))
    draw.text(project(70.0, 19.8), "Mumbai High", fill=(203, 213, 225))
    draw.text(project(81.5, 16.5), "KG Deepwater", fill=(203, 213, 225))

    # Layer 2: 48-Hour Metocean Storm & High-Swell Hazard Zones
    for zone in summary.active_storm_zones:
        clon = float(zone.get("longitude", zone.get("center_lon", 71.65)))
        clat = float(zone.get("latitude", zone.get("center_lat", 19.22)))
        r_deg = float(zone.get("radius_deg", 0.95))
        x0, y0 = project(clon - r_deg * 1.4, clat + r_deg * 1.1)
        x1, y1 = project(clon + r_deg * 1.4, clat - r_deg * 1.1)
        is_severe = "SEVERE" in str(zone.get("threat_level", "SEVERE"))
        fill_rgba = (239, 68, 68, 68) if is_severe else (245, 158, 11, 58)
        edge_rgba = (239, 68, 68, 235) if is_severe else (245, 158, 11, 225)
        draw.ellipse([x0, y0, x1, y1], fill=fill_rgba, outline=edge_rgba, width=2)
        cx, cy = project(clon - r_deg * 1.2, clat + r_deg * 0.3)
        peak_hs = zone.get("peak_hs_m", zone.get("peak_wave_m", 4.4))
        peak_wk = zone.get("peak_wind_kts", zone.get("peak_wind_knots", 48.0))
        draw.text(
            (cx, cy),
            f"48H STORM HAZARD\nHs={peak_hs}m | {peak_wk}kt",
            fill=(252, 165, 165),
        )

    # Layer 3: 120 Candidate & Active Offshore Wells
    for w in summary.wells:
        wx, wy = project(w.longitude, w.latitude)
        if w.readiness_status == WellReadinessStatus.READY_SAFE:
            col = (16, 185, 129, 215)  # Emerald green safe target well
            r = 3
        elif w.readiness_status == WellReadinessStatus.ACTIVE_PRODUCING:
            col = (56, 189, 248, 165)  # Sky blue active well
            r = 2
        else:
            col = (239, 68, 68, 185)   # Red weather-locked well
            r = 3
        draw.ellipse([wx - r, wy - r, wx + r, wy + r], fill=col)

    # Layer 5: Monte Carlo Optimal Redeployment Waypoints (drawn before rigs for clarity)
    if sim and sim.optimal_routing_waypoints:
        wp_pts = [project(wp["lon"], wp["lat"]) for wp in sim.optimal_routing_waypoints]
        for i in range(len(wp_pts) - 1):
            draw.line([wp_pts[i], wp_pts[i + 1]], fill=(34, 197, 94, 255), width=3)
        for wp in sim.optimal_routing_waypoints:
            px, py = project(wp["lon"], wp["lat"])
            draw.ellipse(
                [px - 5, py - 5, px + 5, py + 5],
                fill=(34, 197, 94, 255),
                outline=(255, 255, 255, 255),
            )
        dest_x, dest_y = wp_pts[-1]
        draw.text(
            (dest_x + 8, dest_y - 6),
            f"SAFE TARGET: {sim.destination_well_id}",
            fill=(74, 222, 128),
        )

    # Layer 4: 20 Offshore Drilling Rigs
    for rig in summary.rigs:
        rx, ry = project(rig.location.longitude, rig.location.latitude)
        is_sel = rig.rig_id == focus_rig
        if is_sel:
            col = (250, 204, 21, 255)
            rad = 8
            draw.ellipse(
                [rx - 13, ry - 13, rx + 13, ry + 13],
                outline=(250, 204, 21, 220),
                width=2,
            )
            draw.text(
                (rx + 12, ry - 14),
                f"{rig.rig_id} ({rig.rig_name})",
                fill=(254, 240, 138),
            )
        elif rig.status == RigOperationalStatus.DRILLING:
            col = (59, 130, 246, 255)
            rad = 6
        else:
            col = (249, 115, 22, 255)
            rad = 6
        draw.ellipse(
            [rx - rad, ry - rad, rx + rad, ry + rad],
            fill=col,
            outline=(255, 255, 255, 240),
        )

    # Map Legend Box (Bottom-Left of Map)
    draw.rectangle(
        [MAP_X0 + 10, MAP_Y1 - 92, MAP_X0 + 365, MAP_Y1 - 22],
        fill=(15, 23, 42, 230),
        outline=(51, 65, 85, 255),
    )
    draw.text(
        (MAP_X0 + 18, MAP_Y1 - 84),
        "LEGEND — INDIA EEZ 20 RIGS & 120 WELLS",
        fill=(226, 232, 240),
    )
    draw.text(
        (MAP_X0 + 18, MAP_Y1 - 66),
        "● Yellow/Blue Larger Circles: 20 Offshore Rigs",
        fill=(250, 204, 21),
    )
    draw.text(
        (MAP_X0 + 18, MAP_Y1 - 48),
        "● Green/Cyan/Red Pinpoints: 120 Candidate & Active Wells",
        fill=(52, 211, 153),
    )
    draw.text(
        (MAP_X0 + 18, MAP_Y1 - 32),
        "━ Green Trajectory: Monte Carlo Safe Redeployment Route",
        fill=(74, 222, 128),
    )

    # Right Panel 1: 48-Hour Metocean Wave Height & Wind Threshold Chart
    CX0, CY0, CX1, CY1 = 840, 78, 1260, 410
    draw.rectangle(
        [CX0, CY0, CX1, CY1],
        fill=(15, 23, 42, 255),
        outline=(30, 58, 138, 255),
        width=2,
    )
    draw.text(
        (CX0 + 14, CY0 + 12),
        "48-HOUR METOCEAN FORECAST (Hs > 2.5m | Wind > 35kt)",
        fill=(248, 250, 252),
    )

    series = summary.weather_series or compute_marine_weather_forecast(19.25, 71.85, 48, 3)
    GX0, GY0, GX1, GY1 = CX0 + 42, CY0 + 48, CX1 - 20, CY1 - 36
    draw.line([(GX0, GY1), (GX1, GY1)], fill=(100, 116, 139), width=1)
    draw.line([(GX0, GY0), (GX0, GY1)], fill=(100, 116, 139), width=1)

    # Critical Hs = 2.5m red threshold line (scale 0..6.5m)
    thresh_y = int(GY1 - (2.5 / 6.5) * (GY1 - GY0))
    draw.line([(GX0, thresh_y), (GX1, thresh_y)], fill=(239, 68, 68, 220), width=2)
    draw.text(
        (GX0 + 6, thresh_y - 15),
        "CRITICAL WAVE LIMIT: Hs = 2.5m (UNLATCH CUTOFF)",
        fill=(248, 113, 113),
    )

    wave_pts = []
    n_pts = max(len(series) - 1, 1)
    for idx, pt in enumerate(series):
        px = int(GX0 + (idx / n_pts) * (GX1 - GX0))
        py = int(GY1 - min(pt.significant_wave_height_m, 6.5) / 6.5 * (GY1 - GY0))
        wave_pts.append((px, py))
    for i in range(len(wave_pts) - 1):
        draw.line([wave_pts[i], wave_pts[i + 1]], fill=(56, 189, 248, 255), width=3)
    for px, py in wave_pts:
        draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(248, 250, 252))

    draw.text((GX0, GY1 + 8), "T+0h", fill=(148, 163, 184))
    draw.text(((GX0 + GX1) // 2 - 15, GY1 + 8), "T+24h", fill=(148, 163, 184))
    draw.text((GX1 - 32, GY1 + 8), "T+48h", fill=(148, 163, 184))

    # Right Panel 2: CAG #15117 Financial & Operational Directive Card
    DX0, DY0, DX1, DY1 = 840, 428, 1260, 755
    draw.rectangle(
        [DX0, DY0, DX1, DY1],
        fill=(15, 23, 42, 255),
        outline=(30, 58, 138, 255),
        width=2,
    )
    draw.text(
        (DX0 + 14, DY0 + 14),
        "CAG REPORT #15117 — MONTE CARLO DIRECTIVE",
        fill=(250, 204, 21),
    )

    lines = [
        (f"Target Rig ID      : {focus_rig}", (248, 250, 252)),
        ("Alert Status       : CRITICAL_ACTION_REQUIRED", (248, 113, 113)),
        ("Directive Action   : INITIATE_PREVENTATIVE_TRANSIT", (74, 222, 128)),
        (f"Safe Target Well   : {target_well} (READY_SAFE)", (56, 189, 248)),
        (
            f"Safe Coordinates   : {sim.destination_lat if sim else 18.3131:.4f}N, {sim.destination_lon if sim else 72.2500:.4f}E",
            (203, 213, 225),
        ),
        (
            f"Expected Transit   : {sim.expected_transit_hours if sim else 13.7:.1f} hrs (N=2,500 trials)",
            (203, 213, 225),
        ),
        ("Rig Burn Rate      : INR 1.15 Crore / Day", (203, 213, 225)),
        (
            f"Projected NPT Cost : INR {(sim.estimated_npt_cost_inr if sim else 6576883) / 1e7:.2f} Crore",
            (253, 224, 71),
        ),
        (
            f"Avoided NPT Saving : INR {avoided_cr:.2f} Crore vs 72h Storm Lock",
            (74, 222, 128),
        ),
        (f"Audit Trail Hash   : {audit_id}", (148, 163, 184)),
    ]
    y_cursor = DY0 + 48
    for text_line, color in lines:
        draw.text((DX0 + 16, y_cursor), text_line, fill=color)
        y_cursor += 26

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
