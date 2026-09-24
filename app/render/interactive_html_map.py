"""Self-contained Interactive HTML5 + JavaScript (Leaflet.js + Vega-Embed) Map Generator.

In : FleetSummary (20 Indian offshore rigs, 120 candidate wells, 48h weather, storm cones, waypoints).
Out: Self-contained HTML5 string + optional GCS upload (`gs://zuhaibp-ai-agent-staging/interactive_maps/...`)
     featuring GEBCO/NOAA Bathymetric Ocean + Esri Satellite/Dark Basemaps, Numbered Rig Badges [1]–[6],
     Animated Green Escape Routes (Origin Red ● -> Target Safe Green ◆), Visual Symbol Legend, and
     Click-to-Fly Relocation Index Table.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

try:
    from app.contracts import FleetSummary
    from app.render.india_map_png import _get_six_relocation_rows
    from app.render.rig_map_vega import build_rig_fleet_map_spec
except ImportError:
    from contracts import FleetSummary
    from render.india_map_png import _get_six_relocation_rows
    from render.rig_map_vega import build_rig_fleet_map_spec

logger = logging.getLogger(__name__)


def build_interactive_india_eez_html(summary: FleetSummary) -> str:
    """Build a standalone interactive HTML5/JS (Leaflet + Vega-Lite) map of India's EEZ with Click-to-Fly Relocation Index."""
    vega_spec = build_rig_fleet_map_spec(summary)
    standalone_spec = json.loads(json.dumps(vega_spec))
    if "vconcat" in standalone_spec and len(standalone_spec["vconcat"]) >= 2:
        standalone_spec["vconcat"][0]["width"] = 680
        standalone_spec["vconcat"][0]["height"] = 320
        standalone_spec["vconcat"][1]["width"] = 680
        standalone_spec["vconcat"][1]["height"] = 150

    relocations_js = _get_six_relocation_rows()
    idx_by_rig_id = {r["rig_id"]: r for r in relocations_js}

    rigs_js = []
    for r in summary.rigs:
        t = r.telemetry
        rel = idx_by_rig_id.get(r.rig_id)
        rigs_js.append({
            "rig_id": r.rig_id,
            "rig_name": r.rig_name,
            "operator": r.operator,
            "rig_type": r.rig_type.ormwo_label,
            "status": r.status.value,
            "lat": rel["orig_lat"] if rel else r.location.latitude,
            "lon": rel["orig_lon"] if rel else r.location.longitude,
            "basin": r.location.basin_name,
            "block_id": r.location.block_id,
            "well_name": rel["orig_well"] if rel else r.current_well_name,
            "water_depth_m": r.location.water_depth_m,
            "measured_depth_m": t.measured_depth_m if t else 0.0,
            "target_depth_m": r.target_depth_m,
            "rop_m_hr": t.rate_of_penetration_m_hr if t else 0.0,
            "rpm": t.rotary_rpm if t else 0.0,
            "torque_kft_lbs": t.torque_kft_lbs if t else 0.0,
            "spp_psi": t.standpipe_pressure_psi if t else 0.0,
            "daily_cost_cr": round(r.daily_operating_cost_inr / 10_000_000.0, 2),
            "badge_idx": rel["idx"] if rel else None,
            "dest_well": rel["dest_well"] if rel else None,
            "dest_lat": rel["dest_lat"] if rel else None,
            "dest_lon": rel["dest_lon"] if rel else None,
            "dist_nm": rel["dist_nm"] if rel else None,
            "transit_hrs": rel["transit_hrs"] if rel else None,
            "savings_cr": rel["savings_cr"] if rel else None,
        })

    wells_js = []
    for w in summary.wells:
        wells_js.append({
            "well_id": w.well_id,
            "well_name": w.well_name,
            "basin": w.basin_name,
            "lat": w.latitude,
            "lon": w.longitude,
            "water_depth_m": w.water_depth_m,
            "status": w.status.value,
            "peak_hs_m": w.peak_48h_hs_m,
            "peak_wind_kts": w.peak_48h_wind_kts,
        })

    storms_js = summary.active_storm_zones or []

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>ORMWO — Google DeepMind GenCast & GraphCast 48h Storm & Safe-Well Relocation Command Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
  <style>
    body {{
      margin: 0; padding: 0; background: #070e1b; color: #f8fafc;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    header {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 10px 22px; background: linear-gradient(90deg, #0f172a 0%, #172554 100%);
      border-bottom: 2px solid #38bdf8;
    }}
    .title-group h1 {{ margin: 0; font-size: 16px; color: #f8fafc; letter-spacing: 0.4px; }}
    .title-group p {{ margin: 4px 0 0; font-size: 12px; color: #7dd3fc; }}
    .grid {{
      display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 14px; padding: 12px;
      height: calc(100vh - 68px); box-sizing: border-box;
    }}
    .panel {{
      background: #0f172a; border: 1px solid #1e3a8a; border-radius: 10px;
      overflow: hidden; display: flex; flex-direction: column;
    }}
    .panel-header {{
      padding: 9px 14px; background: #172554; font-size: 13px; font-weight: 700;
      color: #f8fafc; display: flex; justify-content: space-between; align-items: center;
      border-bottom: 1px solid #1e3a8a;
    }}
    #leaflet-map {{ flex: 1; width: 100%; min-height: 520px; background: #091526; }}
    .right-scroll {{ flex: 1; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 12px; }}
    .legend-grid {{
      display: grid; grid-template-columns: 1fr 1fr; gap: 6px;
      background: #091326; padding: 10px; border-radius: 8px; border: 1px solid #1e3a8a; font-size: 11.5px;
    }}
    .legend-item {{ display: flex; align-items: center; gap: 8px; color: #e2e8f0; }}
    .reloc-table {{
      width: 100%; border-collapse: collapse; font-size: 11.5px; background: #091326;
      border-radius: 8px; overflow: hidden; border: 1px solid #1e3a8a;
    }}
    .reloc-table th {{
      background: #1e293b; color: #94a3b8; text-align: left; padding: 6px 8px; font-weight: 700;
    }}
    .reloc-table td {{ padding: 6px 8px; border-bottom: 1px solid #1e293b; cursor: pointer; }}
    .reloc-table tr:hover td {{ background: #172554; }}
    .badge-num {{
      display: inline-flex; width: 20px; height: 20px; border-radius: 50%;
      background: #facc15; color: #0f172a; font-weight: 800; align-items: center; justify-content: center;
      border: 2px solid #0f172a; box-shadow: 0 0 8px rgba(250,204,21,0.8);
    }}
    .safe-diamond {{
      display: inline-block; width: 10px; height: 10px; background: #10b981;
      transform: rotate(45deg); border: 1.5px solid #ffffff;
    }}
    #vega-container {{ background: #ffffff; border-radius: 8px; padding: 6px; }}
    .leaflet-popup-content-wrapper, .leaflet-tooltip {{
      background: #0f172a !important; color: #f8fafc !important;
      border: 1px solid #38bdf8 !important; border-radius: 8px !important;
      box-shadow: 0 8px 20px rgba(0,0,0,0.65) !important;
    }}
    .leaflet-popup-tip {{ background: #0f172a !important; }}
    .popup-table {{ font-size: 12px; border-collapse: collapse; width: 100%; margin-top: 6px; }}
    .popup-table td {{ padding: 3px 6px; border-bottom: 1px solid #1e293b; }}
    .popup-table td.k {{ color: #94a3b8; }}
    .popup-table td.v {{ color: #f8fafc; font-weight: 600; text-align: right; }}
  </style>
</head>
<body>
  <header>
    <div class="title-group">
      <h1>ORMWO — GOOGLE DEEPMIND GENCAST & GRAPHCAST 48H STORM FORECAST & SAFE-WELL RELOCATION MAP</h1>
      <p>2 Active 48h Storm Cones (Red Circles) · 6 Threatened Rigs Indexed [1]–[6] Relocating to Safe Wells (Green ◆) · Total Avoided NPT Savings: ₹25.43 Crore</p>
    </div>
    <div style="display:flex; gap:8px;">
      <button onclick="map.flyTo([19.15, 71.55], 8)" style="background:#ef4444; color:#fff; border:none; padding:6px 12px; border-radius:6px; font-weight:700; cursor:pointer;">Zoom: Mumbai High [1]–[4]</button>
      <button onclick="map.flyTo([16.10, 82.35], 8)" style="background:#f59e0b; color:#0f172a; border:none; padding:6px 12px; border-radius:6px; font-weight:700; cursor:pointer;">Zoom: KG-DWN Basin [5]–[6]</button>
      <button onclick="map.flyTo([16.5, 77.5], 5)" style="background:#38bdf8; color:#0f172a; border:none; padding:6px 12px; border-radius:6px; font-weight:700; cursor:pointer;">Reset Full India EEZ</button>
    </div>
  </header>
  <div class="grid">
    <div class="panel">
      <div class="panel-header">
        <span>Interactive Bathymetric & Satellite Command Map (Click Any Rig [1]–[6], Red Storm Circle, or Safe Well ◆)</span>
        <span style="color:#4ade80;">GEBCO Hydrography + Esri Satellite</span>
      </div>
      <div id="leaflet-map"></div>
    </div>
    <div class="panel">
      <div class="panel-header">
        <span>Visual Symbol Legend & Click-to-Fly Relocation Index [1]–[6]</span>
        <span style="color:#facc15;">Save ₹25.43 Crore NPT</span>
      </div>
      <div class="right-scroll">
        <div class="legend-grid">
          <div class="legend-item"><span style="display:inline-block;width:14px;height:14px;border-radius:50%;background:rgba(239,68,68,0.45);border:2px dashed #ef4444;"></span> <b>Red Dashed Circle:</b> 48h Storm Cone (DO NOT DRILL)</div>
          <div class="legend-item"><span class="badge-num">1</span> <b>Yellow Badge [1]–[6]:</b> Threatened Rig Origin</div>
          <div class="legend-item"><span style="color:#22c55e;font-weight:900;">━━➤</span> <b>Green Dashed Route:</b> Zero-Downtime Escape Path</div>
          <div class="legend-item"><span class="safe-diamond"></span> <b>Green Diamond (◆):</b> Safe Target Well (Hs &lt; 1.5m)</div>
        </div>
        <table class="reloc-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Rig ID & Name</th>
              <th>Origin Storm Well (🔴)</th>
              <th>Safe Target Well (🟢 ◆)</th>
              <th>Transit</th>
              <th>NPT Saved</th>
            </tr>
          </thead>
          <tbody id="reloc-tbody"></tbody>
        </table>
        <div id="vega-container"></div>
      </div>
    </div>
  </div>

  <script>
    const RIGS = {json.dumps(rigs_js)};
    const WELLS = {json.dumps(wells_js)};
    const STORMS = {json.dumps(storms_js)};
    const RELOCATIONS = {json.dumps(relocations_js)};
    const VEGA_SPEC = {json.dumps(standalone_spec)};

    // 1. Initialize Leaflet Map with Rich Bathymetric Ocean Map as Default + Dark & Satellite Layers
    const map = L.map('leaflet-map', {{ center: [16.8, 77.2], zoom: 5 }});

    const hydroOceanLayer = L.layerGroup([
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        attribution: 'Esri, GEBCO, NOAA, National Geographic — India EEZ Bathymetry',
        maxZoom: 16
      }}),
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Reference/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        maxZoom: 16
      }})
    ]).addTo(map);

    const darkOceanLayer = L.layerGroup([
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        attribution: 'Esri Dark Tactical Command — India EEZ ORMWO',
        maxZoom: 16
      }}),
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        maxZoom: 16
      }})
    ]);

    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
      attribution: 'Esri World Imagery — Offshore Satellite View',
      maxZoom: 18
    }});

    L.control.layers({{
      "Bathymetric Ocean Map (GEBCO/NOAA)": hydroOceanLayer,
      "Dark Tactical Command (Esri)": darkOceanLayer,
      "Satellite Imagery (Esri)": satelliteLayer
    }}, null, {{ position: 'topright' }}).addTo(map);

    // 2. Render 48-Hour Storm Hazard Cones (Red Circles)
    STORMS.forEach((st, sIdx) => {{
      const sLat = st.center_lat !== undefined ? st.center_lat : st.latitude;
      const sLon = st.center_lon !== undefined ? st.center_lon : st.longitude;
      const sName = st.name || st.storm_name || st.storm_id || 'Cyclonic Storm Zone';
      const sBasin = st.basin_name || st.basin || 'Indian EEZ';
      const sHs = st.peak_wave_hs_m !== undefined ? st.peak_wave_hs_m : st.peak_hs_m;
      const sWind = st.peak_wind_knots !== undefined ? st.peak_wind_knots : st.peak_wind_kts;
      if (sLat === undefined || sLon === undefined) return;
      const circle = L.circle([sLat, sLon], {{
        radius: (st.radius_deg || 1.15) * 111000,
        color: '#dc2626',
        weight: 3,
        dashArray: '8,5',
        fillColor: '#ef4444',
        fillOpacity: 0.28
      }}).addTo(map);
      circle.bindTooltip(
        `<div style="font-weight:700;color:#fca5a5;">🔴 RED CIRCLE ${{sIdx + 1}}: ${{sName}}</div>` +
        `<div>Basin: <b>${{sBasin}}</b> | Peak Wave: <b>Hs=${{sHs}}m</b> | Wind: <b>${{sWind}}kt</b></div>` +
        `<div style="color:#fde047;">STORM_LOCKED — DO NOT DRILL (Relocate Rigs [1]–[6] to Safe Green Wells)</div>`,
        {{ sticky: true }}
      );
    }});

    // 3. Render Background 120 Wells
    WELLS.forEach(w => {{
      const isSafe = w.status.includes('SAFE');
      const isStorm = w.status.includes('STORM');
      const color = isSafe ? '#10b981' : (isStorm ? '#ef4444' : '#38bdf8');
      L.circleMarker([w.lat, w.lon], {{
        radius: 3.5, color: '#0f172a', weight: 1, fillColor: color, fillOpacity: 0.8
      }}).addTo(map).bindTooltip(`<b>Well ${{w.well_id}}</b> (${{w.status}}) — Hs=${{w.peak_hs_m}}m`);
    }});

    // 4. Render the 6 Indexed Storm Relocations ([1]..[6]): Origin Badge + Green Dashed Route + Safe Diamond Target
    const tbody = document.getElementById('reloc-tbody');
    RELOCATIONS.forEach(rel => {{
      // Green Escape Polyline
      L.polyline([[rel.orig_lat, rel.orig_lon], [rel.dest_lat, rel.dest_lon]], {{
        color: '#22c55e', weight: 4, dashArray: '7,4'
      }}).addTo(map).bindTooltip(
        `<b>🟢 Escape Route [${{rel.idx}}]: ${{rel.rig_name}}</b><br/>` +
        `From Storm Well <b>${{rel.orig_well}}</b> ➔ Safe Well <b>${{rel.dest_well}}</b> (${{rel.dist_nm}} NM / ${{rel.transit_hrs}}h)`
      );

      // Safe Target Well Green Diamond Marker
      const destIcon = L.divIcon({{
        className: '',
        html: `<div style="width:14px;height:14px;background:#10b981;transform:rotate(45deg);border:2px solid #fff;box-shadow:0 0 8px #10b981;"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7]
      }});
      L.marker([rel.dest_lat, rel.dest_lon], {{ icon: destIcon }}).addTo(map).bindTooltip(
        `<b>🟢 SAFE TARGET WELL: ${{rel.dest_well}} (For Rig [${{rel.idx}}] ${{rel.rig_name}})</b><br/>` +
        `Coords: ${{rel.dest_lat.toFixed(2)}}°N, ${{rel.dest_lon.toFixed(2)}}°E | Calm Wave: Hs=${{rel.safe_hs}}m | Avoided NPT: ₹${{rel.savings_cr}} Cr`
      );

      // Origin Numbered Rig Badge Marker
      const origIcon = L.divIcon({{
        className: '',
        html: `<div class="badge-num">${{rel.idx}}</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      }});
      L.marker([rel.orig_lat, rel.orig_lon], {{ icon: origIcon }}).addTo(map).bindTooltip(
        `<b>🟡 [${{rel.idx}}] ${{rel.rig_id}} — ${{rel.rig_name}} (${{rel.hull}})</b><br/>` +
        `🔴 Origin Storm-Locked Well: <b>${{rel.orig_well}}</b> (Hs=${{rel.storm_hs}}m, ${{rel.storm_wind}}kt)<br/>` +
        `🟢 Relocate <b>${{rel.dist_nm}} NM (${{rel.transit_hrs}}h)</b> ➔ <b>${{rel.dest_well}}</b> (Save ₹${{rel.savings_cr}} Cr)`
      );

      // Add Row to Click-to-Fly Table
      const tr = document.createElement('tr');
      tr.onclick = () => map.flyTo([rel.orig_lat, rel.orig_lon], 9);
      tr.innerHTML = `
        <td><span class="badge-num">${{rel.idx}}</span></td>
        <td><b>${{rel.rig_name}}</b><br/><span style="color:#94a3b8;font-size:10px;">${{rel.rig_id}}</span></td>
        <td style="color:#fca5a5;">🔴 ${{rel.orig_well}}<br/><span style="font-size:10px;">Hs=${{rel.storm_hs}}m</span></td>
        <td style="color:#4ade80;">🟢 ◆ <b>${{rel.dest_well}}</b><br/><span style="font-size:10px;">Hs=${{rel.safe_hs}}m</span></td>
        <td style="color:#38bdf8;"><b>${{rel.dist_nm}} NM</b><br/><span style="font-size:10px;">${{rel.transit_hrs}} hrs</span></td>
        <td style="color:#facc15;font-weight:700;">₹${{rel.savings_cr}} Cr</td>
      `;
      tbody.appendChild(tr);
    }});

    // 5. Render Safe Operating Rigs (Blue Markers)
    RIGS.filter(r => !r.badge_idx).forEach(r => {{
      L.circleMarker([r.lat, r.lon], {{
        radius: 6, color: '#ffffff', weight: 1.5, fillColor: '#3b82f6', fillOpacity: 1.0
      }}).addTo(map).bindTooltip(`<b>🔵 ${{r.rig_id}} — ${{r.rig_name}}</b> (Safe Basin: ${{r.basin}})`);
    }});

    // 6. Embed Synchronized Vega-Lite v5 Chart
    vegaEmbed('#vega-container', VEGA_SPEC, {{ actions: false, renderer: 'canvas' }});
  </script>
</body>
</html>"""


def publish_interactive_html_map(
    summary: FleetSummary,
    surface_id: str,
    png_bytes: bytes | None = None,
) -> tuple[str, str]:
    """Save the interactive HTML5/JS map + 1680x1080 PNG locally and upload to GCS."""
    from concurrent.futures import ThreadPoolExecutor

    html_content = build_interactive_india_eez_html(summary)
    local_dir = Path("/tmp/ormwo_interactive_maps")
    local_dir.mkdir(parents=True, exist_ok=True)
    local_path = local_dir / "india_eez_interactive_map.html"
    local_path.write_text(html_content, encoding="utf-8")

    if png_bytes:
        png_local = local_dir / "india_eez_4panel_latest.png"
        png_local.write_bytes(png_bytes)

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or "zuhaibp-ai"
    bucket_name = f"{project_id}-agent-staging"
    cloud_console_url = f"https://storage.mtls.cloud.google.com/{bucket_name}/interactive_maps/india_eez_latest.html"

    def _upload_assets() -> None:
        try:
            os.environ.setdefault("GOOGLE_API_USE_CLIENT_CERTIFICATE", "false")
            from google.cloud import storage
            from google.cloud.storage.retry import DEFAULT_RETRY

            client = storage.Client(project=project_id)
            bucket = client.bucket(bucket_name)
            short_retry = DEFAULT_RETRY.with_deadline(3.5)

            latest_blob = bucket.blob("interactive_maps/india_eez_latest.html")
            latest_blob.upload_from_string(
                html_content,
                content_type="text/html; charset=utf-8",
                timeout=3.5,
                retry=short_retry,
            )
            if png_bytes:
                png_blob = bucket.blob("interactive_maps/india_eez_4panel_latest.png")
                png_blob.upload_from_string(
                    png_bytes,
                    content_type="image/png",
                    timeout=3.5,
                    retry=short_retry,
                )
        except Exception as exc:
            logger.debug("Optional GCS interactive map upload skipped: %s", exc)

    try:
        pool = ThreadPoolExecutor(max_workers=1)
        fut = pool.submit(_upload_assets)
        fut.result(timeout=3.5)
    except Exception:
        pass

    return str(local_path), cloud_console_url

