"""Google-Branded Minimal & Visual-Rich Interactive Presentation Deck (`ormwo_executive_presentation.html`).

Designed with ZERO wasted whitespace: every slide uses a full-viewport (`calc(100vh - 108px)`) CSS Grid layout
where every card contains auto-scaling SVG Offshore Rig CAD Outlines (Jack-Up Rigs, DP3 Drillships, 3x AHTS Tugs,
Pawan Hans Helicopters), official-style SVG partner logos (Google Cloud, Vertex AI, DeepMind, ONGC, CAG India),
embedded high-res map imagery, and interactive click-to-inspect controls.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path


def _get_embedded_png_data_uri() -> str:
    """Return a base64 data URI of the 4-panel India EEZ infographic PNG so images render 100% offline/inline."""
    candidates = [
        Path("/usr/local/google/home/zuhaibp/.gemini/jetski/brain/81eeda2f-6522-478b-b72b-d7d51e3709cb/india_eez_4panel_infographic.png"),
        Path(__file__).resolve().parent.parent / "static" / "india_eez_4panel_latest.png",
    ]
    for p in candidates:
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            return f"data:image/png;base64,{b64}"
    try:
        from app.integration.tools import _queue_india_map_surface
        from app.render.india_map_png import render_india_eez_map_png
        raw = render_india_eez_map_png(_queue_india_map_surface(None))
        return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"
    except Exception:
        return ""


def build_executive_presentation_html(project_id: str | None = None) -> str:
    """Return the self-contained Google-branded interactive presentation website with rig outlines on every page."""
    proj = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT") or "zuhaibp-ai"
    bucket = f"{proj}-agent-staging"
    map_url = f"https://storage.mtls.cloud.google.com/{bucket}/interactive_maps/india_eez_latest.html"
    sop_url = f"https://storage.mtls.cloud.google.com/{bucket}/interactive_maps/india_eez_rig_move_sop_latest.html"
    png_url = f"https://storage.mtls.cloud.google.com/{bucket}/interactive_maps/india_eez_4panel_latest.png"
    inline_png_src = _get_embedded_png_data_uri() or png_url

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>ORMWO — Google Cloud & Vertex AI Interactive Executive Deck</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --g-blue: #1a73e8;
    --g-blue-soft: #e8f0fe;
    --g-red: #d93025;
    --g-red-soft: #fce8e6;
    --g-yellow: #f9ab00;
    --g-yellow-soft: #fef7e0;
    --g-green: #1e8e3e;
    --g-green-soft: #e6f4ea;
    --ink: #202124;
    --ink-2: #5f6368;
    --border: #dadce0;
    --surface: #ffffff;
    --canvas: #f1f3f4;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--canvas);
    color: var(--ink);
    height: 100vh;
    width: 100vw;
    overflow: hidden;
    display: grid;
    grid-template-rows: 4px 56px 1fr 50px;
  }}

  /* Row 1: 4-Color Google Bar */
  .g-bar {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
  }}
  .g-bar div:nth-child(1) {{ background: #4285F4; }}
  .g-bar div:nth-child(2) {{ background: #EA4335; }}
  .g-bar div:nth-child(3) {{ background: #FBBC04; }}
  .g-bar div:nth-child(4) {{ background: #34A853; }}

  /* Row 2: Top Header with Logos & Slide Tabs */
  header.top-nav {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }}

  .brand-cluster {{
    display: flex;
    align-items: center;
    gap: 14px;
  }}

  .logo-pill-strip {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding-left: 12px;
    border-left: 1px solid var(--border);
  }}

  .partner-badge {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 9px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    background: #f8f9fa;
    border: 1px solid var(--border);
    color: var(--ink);
  }}

  .nav-pills {{
    display: flex;
    align-items: center;
    gap: 4px;
    background: #f1f3f4;
    padding: 4px;
    border-radius: 999px;
  }}
  .nav-pill {{
    border: none;
    background: transparent;
    color: var(--ink-2);
    font-size: 12px;
    font-weight: 600;
    padding: 6px 13px;
    border-radius: 999px;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    gap: 5px;
  }}
  .nav-pill:hover {{ color: var(--g-blue); background: rgba(255,255,255,0.6); }}
  .nav-pill.active {{
    background: var(--g-blue);
    color: #fff;
    box-shadow: 0 1px 4px rgba(26,115,232,0.3);
  }}

  /* Row 3: Full-Height Slide Viewport (Zero Wasted Space) */
  main.stage {{
    width: 100%;
    height: 100%;
    overflow: hidden;
    padding: 14px 22px;
  }}

  .slide {{
    display: none;
    width: 100%;
    height: 100%;
    grid-template-rows: auto 1fr;
    gap: 12px;
  }}
  .slide.active {{
    display: grid;
    animation: slideFade 0.2s ease-out;
  }}

  @keyframes slideFade {{
    from {{ opacity: 0; transform: scale(0.995); }}
    to {{ opacity: 1; transform: scale(1); }}
  }}

  /* Top Title Strip inside each slide */
  .slide-hdr {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    box-shadow: 0 1px 2px rgba(60,64,67,0.05);
  }}
  .slide-kicker {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--g-blue);
  }}
  .slide-title {{
    font-family: 'Google Sans', 'Inter', sans-serif;
    font-size: 21px;
    font-weight: 700;
    color: var(--ink);
    letter-spacing: -0.015em;
  }}
  .hdr-kpis {{
    display: flex;
    gap: 10px;
    flex-shrink: 0;
  }}
  .hdr-kpi {{
    background: #f8f9fa;
    border: 1px solid var(--border);
    border-left: 3px solid var(--g-blue);
    border-radius: 8px;
    padding: 6px 12px;
    min-width: 130px;
  }}
  .hdr-kpi.red {{ border-left-color: var(--g-red); }}
  .hdr-kpi.green {{ border-left-color: var(--g-green); }}
  .hdr-kpi.yellow {{ border-left-color: var(--g-yellow); }}
  .hdr-kpi-v {{ font-size: 16px; font-weight: 700; color: var(--ink); }}
  .hdr-kpi-l {{ font-size: 10.5px; color: var(--ink-2); }}

  /* Full-Height Content Grids */
  .body-split-2 {{
    display: grid;
    grid-template-columns: 1.05fr 0.95fr;
    gap: 14px;
    height: 100%;
    min-height: 0;
  }}
  .body-split-equal {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    height: 100%;
    min-height: 0;
  }}
  .body-split-sidebar {{
    display: grid;
    grid-template-columns: 340px 1fr;
    gap: 14px;
    height: 100%;
    min-height: 0;
  }}

  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(60,64,67,0.06);
  }}

  .svg-stage {{
    background: linear-gradient(180deg, #0b192c 0%, #112240 100%);
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    flex: 1;
    width: 100%;
    min-height: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
  }}
  .svg-stage.light {{
    background: linear-gradient(180deg, #f8fbff 0%, #eef5ff 100%);
    border: 1px solid #d2e3fc;
  }}

  .click-item {{
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 11px 14px;
    cursor: pointer;
    transition: all 0.15s ease;
    background: #fff;
  }}
  .click-item:hover {{
    border-color: var(--g-blue);
    background: #f8fbff;
  }}
  .click-item.active {{
    border: 2px solid var(--g-blue);
    background: var(--g-blue-soft);
  }}

  .tag {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
  }}
  .tag-blue {{ background: var(--g-blue-soft); color: var(--g-blue); }}
  .tag-green {{ background: var(--g-green-soft); color: var(--g-green); }}
  .tag-red {{ background: var(--g-red-soft); color: var(--g-red); }}
  .tag-yellow {{ background: var(--g-yellow-soft); color: #b06000; }}

  /* Row 4: Footer Navigation */
  footer.bot-nav {{
    background: var(--surface);
    border-top: 1px solid var(--border);
    padding: 0 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}

  .btn {{
    background: var(--g-blue);
    color: #fff;
    border: none;
    padding: 7px 18px;
    border-radius: 999px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }}
  .btn:hover:not(:disabled) {{ background: #1557b0; }}
  .btn.outline {{
    background: #fff;
    color: var(--ink);
    border: 1px solid var(--border);
  }}
  .btn.outline:hover:not(:disabled) {{ background: #f1f3f4; }}
  .btn:disabled {{ opacity: 0.35; cursor: not-allowed; }}

  table.modern-tbl {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }}
  table.modern-tbl th {{
    background: #f1f3f4;
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
    border-bottom: 1px solid var(--border);
  }}
  table.modern-tbl td {{
    padding: 8px 10px;
    border-bottom: 1px solid #eee;
  }}
  table.modern-tbl tr:hover td {{
    background: #f4f8ff;
    cursor: pointer;
  }}
</style>
</head>
<body>

<!-- 1. Google 4-Color Strip -->
<div class="g-bar"><div></div><div></div><div></div><div></div></div>

<!-- 2. Header with Official-Style Partner Logos & Navigation Tabs -->
<header class="top-nav">
  <div class="brand-cluster">
    <!-- Google G SVG -->
    <svg width="24" height="24" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3h3.86c2.26-2.09 3.685-5.17 3.685-9.09z"/>
      <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.86-3c-1.08.72-2.45 1.16-4.07 1.16-3.13 0-5.78-2.11-6.73-4.96H1.29v3.09C3.26 21.3 7.37 24 12 24z"/>
      <path fill="#FBBC04" d="M5.27 14.29c-.25-.72-.38-1.49-.38-2.29s.13-1.57.38-2.29V6.62H1.29C.47 8.24 0 10.06 0 12s.47 3.76 1.29 5.38l3.98-3.09z"/>
      <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.37 0 3.26 2.7 1.29 6.62l3.98 3.09c.95-2.85 3.6-4.96 6.73-4.96z"/>
    </svg>
    <div>
      <div style="font-family:'Google Sans',sans-serif; font-weight:700; font-size:14.5px;">ORMWO — Offshore Rig Mobilization & Weather Optimizer</div>
      <div style="font-size:11px; color:var(--ink-2);">Interactive Executive Briefing · Click Any Rig Blueprint, Persona, or Architecture Node</div>
    </div>

    <!-- Partner & Technology Logos Strip -->
    <div class="logo-pill-strip">
      <span class="partner-badge">☁️ Google Cloud Vertex AI</span>
      <span class="partner-badge">🧠 DeepMind WeatherNext</span>
      <span class="partner-badge">🛢️ ONGC India EEZ</span>
      <span class="partner-badge">🏛️ CAG Audit #15117</span>
    </div>
  </div>

  <div class="nav-pills">
    <button class="nav-pill active" onclick="showSlide(0)">01 · CAG #15117 Problem</button>
    <button class="nav-pill" onclick="showSlide(1)">02 · Rig Physics & CAD</button>
    <button class="nav-pill" onclick="showSlide(2)">03 · Personas & Workflows</button>
    <button class="nav-pill" onclick="showSlide(3)">04 · ADK Architecture</button>
    <button class="nav-pill" onclick="showSlide(4)">05 · EEZ Map & Rigs [1]–[6]</button>
    <button class="nav-pill" onclick="showSlide(5)">06 · ROI & Live Prompts</button>
  </div>
</header>

<!-- 3. Main Full-Height Slide Stage -->
<main class="stage">

  <!-- ==================== SLIDE 1: THE ₹512 CR PROBLEM + FULL-HEIGHT RIG & COST VISUAL ==================== -->
  <section class="slide active" id="s0">
    <div class="slide-hdr">
      <div>
        <div class="slide-kicker">01 · Government of India Audit Origin (CAG Report #15117)</div>
        <div class="slide-title">Why Idle Offshore Rigs Cost ₹512 Crore Across 426.5 Waiting Rig-Days</div>
      </div>
      <div class="hdr-kpis">
        <div class="hdr-kpi red"><div class="hdr-kpi-v">₹1.20 Cr/day</div><div class="hdr-kpi-l">Rig Charter Burn Rate</div></div>
        <div class="hdr-kpi yellow"><div class="hdr-kpi-v">426.5 Days</div><div class="hdr-kpi-l">Avoidable Idle NPT (CAG #15117)</div></div>
        <div class="hdr-kpi"><div class="hdr-kpi-v">1.50 m (5 ft)</div><div class="hdr-kpi-l">MWS Spudcan Wave Ceiling</div></div>
        <div class="hdr-kpi green"><div class="hdr-kpi-v">₹71.50 Cr</div><div class="hdr-kpi-l">Saved Across Rigs [1]–[6]</div></div>
      </div>
    </div>

    <div class="body-split-2">
      <!-- Left Card: Interactive Audit Pillars + Cost Bar Visualization -->
      <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-size:12px; font-weight:700; color:var(--g-blue); text-transform:uppercase;">👇 Click Any CAG Audit #15117 Root Cause to Inspect on the Rig Schematic →</span>
          <a href="https://cag.gov.in/en/audit-report/details/15117" target="_blank" style="font-size:11.5px; font-weight:600; color:var(--g-blue); text-decoration:none;">Official CAG Report #15117 ↗</a>
        </div>

        <div style="display:flex; flex-direction:column; gap:10px;">
          <div class="click-item active" id="cag0" onclick="selectSlide1Pillar(0)">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span class="tag tag-red">Pillar 01 · Statutory Clearances (MoEFCC EC & Navy NOC)</span>
              <strong style="color:var(--g-red); font-size:13px;">₹218 Cr Idle Loss (42.5%)</strong>
            </div>
            <p style="font-size:12px; color:var(--ink-2); margin-top:4px;">
              Rigs completed a well and were towed to the geographically closest well—only to wait weeks at ₹1.2 Cr/day because the target well lacked Environmental Clearance (`EC`), Defence `NOC`, or a `500m` subsea pipeline buffer.
            </p>
          </div>

          <div class="click-item" id="cag1" onclick="selectSlide1Pillar(1)">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span class="tag tag-yellow">Pillar 02 · Monsoon & MWS Sea-State Lock (`Hs > 1.50m`)</span>
              <strong style="color:#b06000; font-size:13px;">₹184 Cr Idle Loss (36.0%)</strong>
            </div>
            <p style="font-size:12px; color:var(--ink-2); margin-top:4px;">
              Missing a 38-hour calm sea window (`Hs ≤ 1.50m`) trapped completed jack-up rigs on location throughout monsoon swells, while active deepwater drillships needed automated LMRP disconnect & helicopter evacuation triggers.
            </p>
          </div>

          <div class="click-item" id="cag2" onclick="selectSlide1Pillar(2)">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span class="tag tag-blue">Pillar 03 · 3× AHTS Tug & Helicopter Dispatch Silos</span>
              <strong style="color:var(--g-blue); font-size:13px;">₹110 Cr Idle Loss (21.5%)</strong>
            </div>
            <p style="font-size:12px; color:var(--ink-2); margin-top:4px;">
              Manual spreadsheet scheduling across 20 rigs, 120 wells, `3× 150T Bollard-Pull AHTS Tugs`, and `Pawan Hans Dauphin N3` helicopters caused cascading waiting-on-vessel delays.
            </p>
          </div>
        </div>

        <!-- Visual Stacked Cost Bar -->
        <div style="background:#f8f9fa; border:1px solid var(--border); border-radius:10px; padding:12px 14px;">
          <div style="display:flex; justify-content:space-between; font-size:11.5px; font-weight:600; margin-bottom:6px;">
            <span>CAG Report #15117 Avoidable NPT Breakdown (`₹512 Crore Total`)</span>
            <span style="color:var(--g-green);">100% Addressed by ORMWO Agent</span>
          </div>
          <div style="height:18px; width:100%; border-radius:999px; overflow:hidden; display:flex;">
            <div style="width:42.5%; background:#ea4335; color:#fff; font-size:10px; font-weight:700; display:flex; align-items:center; justify-content:center;">EC/NOC Delays (42.5%)</div>
            <div style="width:36%; background:#fbbc04; color:#202124; font-size:10px; font-weight:700; display:flex; align-items:center; justify-content:center;">MWS Swell Lock (36%)</div>
            <div style="width:21.5%; background:#4285f4; color:#fff; font-size:10px; font-weight:700; display:flex; align-items:center; justify-content:center;">Tug/Heli (21.5%)</div>
          </div>
        </div>
      </div>

      <!-- Right Card: Full-Height Offshore Rig Blueprint & Live Audit Callout Schematic -->
      <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <span class="tag tag-blue" id="s1RigBadge">CAD SCHEMATIC · JACK-UP RIG & SUBSEA CLEARANCE ANATOMY</span>
          <span style="font-family:'JetBrains Mono',monospace; font-size:11.5px; color:var(--g-red); font-weight:700;">🔥 IDLE BURN: ₹5.00 LAKH / HOUR</span>
        </div>

        <div class="svg-stage">
          <svg viewBox="0 0 580 340" width="100%" height="100%" preserveAspectRatio="xMidYMid meet">
            <!-- Grid lines -->
            <g stroke="rgba(66,133,244,0.12)" stroke-width="1">
              <line x1="0" y1="60" x2="580" y2="60"/><line x1="0" y1="120" x2="580" y2="120"/>
              <line x1="0" y1="180" x2="580" y2="180"/><line x1="0" y1="240" x2="580" y2="240"/>
              <line x1="140" y1="0" x2="140" y2="340"/><line x1="290" y1="0" x2="290" y2="340"/><line x1="440" y1="0" x2="440" y2="340"/>
            </g>

            <!-- Sea Surface -->
            <path d="M0 195 Q 45 182, 90 195 T 180 195 T 270 195 T 360 195 T 450 195 T 580 195 L 580 285 L 0 285 Z" fill="rgba(26,115,232,0.22)"/>
            <line x1="0" y1="195" x2="580" y2="195" stroke="#4da3ff" stroke-width="2" stroke-dasharray="6,4"/>
            <text x="14" y="186" fill="#8ab4f8" font-size="10.5" font-family="'JetBrains Mono'">SEA SURFACE · MWS LIMIT Hs ≤ 1.50m (5 FT)</text>

            <!-- Seabed Clay Layer -->
            <rect x="0" y="285" width="580" height="55" fill="#172a3a"/>
            <line x1="0" y1="285" x2="580" y2="285" stroke="#ffb74d" stroke-width="2"/>
            <text x="14" y="306" fill="#ffd54f" font-size="10.5" font-family="'JetBrains Mono'">SEABED SILT/CLAY · SPUDCAN PENETRATION 8m–15m</text>

            <!-- Jack-Up Rig Outline (Left-Center) -->
            <!-- 3 Truss Legs -->
            <g stroke="#90caf9" stroke-width="2.5" fill="none">
              <rect x="105" y="38" width="22" height="262"/>
              <path d="M105 45 L127 65 L105 85 L127 105 L105 125 L127 145 L105 165 L127 185 L105 205 L127 225 L105 245 L127 265 L105 285" stroke-width="1.4"/>
              <rect x="265" y="38" width="22" height="262"/>
              <path d="M265 45 L287 65 L265 85 L287 105 L265 125 L287 145 L265 165 L287 185 L265 205 L287 225 L265 245 L287 265 L265 285" stroke-width="1.4"/>
            </g>
            <!-- Spudcans in Seabed -->
            <polygon points="95,300 137,300 116,322" fill="#ea4335" stroke="#fff" stroke-width="1.5"/>
            <polygon points="255,300 297,300 276,322" fill="#ea4335" stroke="#fff" stroke-width="1.5"/>

            <!-- Elevated Jack-Up Hull & Derrick -->
            <rect x="85" y="118" width="225" height="34" rx="5" fill="#1e293b" stroke="#60a5fa" stroke-width="2.5"/>
            <text x="115" y="139" fill="#fff" font-size="11.5" font-weight="700">ONGC JACK-UP (`SAGAR SAMRAT`)</text>
            <!-- Derrick Mast -->
            <polygon points="180,118 214,118 197,32" fill="rgba(251,188,4,0.15)" stroke="#fbbc04" stroke-width="2.2"/>
            <!-- Helideck + Helicopter Outline -->
            <rect x="55" y="106" width="45" height="8" rx="2" fill="#34a853"/>
            <path d="M62 100 L88 100 M75 100 L75 106 M68 96 L82 96" stroke="#fff" stroke-width="2"/>

            <!-- AHTS Ocean Tug Outline (Right Side) -->
            <path d="M375 182 L455 182 L468 195 L370 195 Z" fill="#34a853" stroke="#fff" stroke-width="1.5"/>
            <rect x="390" y="168" width="32" height="14" fill="#e6f4ea"/>
            <text x="372" y="160" fill="#81c995" font-size="10.5" font-weight="700">🚢 3× ONGC AHTS TUGS (150T BP)</text>
            <!-- Tow Bridle Cable -->
            <path d="M310 138 Q 345 175, 375 188" fill="none" stroke="#fbbc04" stroke-width="2.5" stroke-dasharray="5,3"/>

            <!-- Target Well EC/NOC Callout Box -->
            <rect x="355" y="45" width="205" height="92" rx="8" fill="rgba(15,23,42,0.92)" stroke="#60a5fa" stroke-width="1.8"/>
            <text x="368" y="66" fill="#60a5fa" font-size="11" font-weight="700" id="svgCalloutHdr">CAG #15117 CLEARANCE GATE</text>
            <text x="368" y="86" fill="#fff" font-size="11" id="svgCalloutLine1">❌ MH-N-002 (4.1 NM): No MoEFCC EC</text>
            <text x="368" y="104" fill="#81c995" font-size="11" font-weight="700" id="svgCalloutLine2">✅ WELL-IND-004 (8.4 NM): EC + NOC OK</text>
            <text x="368" y="122" fill="#fbbc04" font-size="10.5" id="svgCalloutLine3">Saved NPT: ₹11.50 Cr · 38.1h Move</text>
          </svg>
        </div>
      </div>
    </div>
  </section>

  <!-- ==================== SLIDE 2: RIG PHYSICS CAD BLUEPRINTS (JACK-UP vs DRILLSHIP) ==================== -->
  <section class="slide" id="s1">
    <div class="slide-hdr">
      <div>
        <div class="slide-kicker">02 · Offshore Petroleum Engineering Physics & DNV-ST-N001 MWS Rules</div>
        <div class="slide-title">Why Active Rigs NEVER Move in a 48h Storm vs. Calm Window Completed-Well Moves</div>
      </div>
      <div style="display:flex; gap:8px;">
        <span class="tag tag-green">🟢 Calm Window (`Hs ≤ 1.50m`): Wet Tow Completed Rigs [1]–[4]</span>
        <span class="tag tag-red">🔴 Storm Lock (`Hs > 2.50m`): BOP Hang-Off & 🚁 Evac [5]–[6]</span>
      </div>
    </div>

    <div class="body-split-equal">
      <!-- Left Full-Height Blueprint: Jack-Up Rig Move Physics -->
      <div class="card" style="border-top:4px solid var(--g-green);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <span class="tag tag-green">USE CASE B · CALM MWS WINDOW (MUMBAI HIGH TODAY: Hs = 1.22m)</span>
            <h3 style="font-size:16px; margin-top:4px;">Jack-Up Rig Blueprint (`Sagar Samrat [1]` & `Sagar Ratna [2]`)</h3>
          </div>
          <strong style="font-size:13px; color:var(--g-green);">38.1h Total Move</strong>
        </div>

        <div class="svg-stage" style="margin:8px 0;">
          <svg viewBox="0 0 520 230" width="100%" height="100%" preserveAspectRatio="xMidYMid meet">
            <rect width="520" height="230" fill="#0d1b2a"/>
            <!-- Calm Waterline -->
            <line x1="0" y1="135" x2="520" y2="135" stroke="#34a853" stroke-width="2.5"/>
            <text x="12" y="126" fill="#81c995" font-size="10.5" font-weight="700">🟢 LIVE MUMBAI HIGH Hs = 1.22m ≤ 1.50m MWS SPUDCAN LIMIT</text>
            <!-- Seabed -->
            <rect x="0" y="190" width="520" height="40" fill="#1e293b"/>
            <!-- Step 1 Rig (Extracting Spudcans) -->
            <g transform="translate(45,18)">
              <rect x="10" y="0" width="12" height="175" fill="none" stroke="#60a5fa" stroke-width="2"/>
              <rect x="78" y="0" width="12" height="175" fill="none" stroke="#60a5fa" stroke-width="2"/>
              <rect x="0" y="75" width="100" height="24" rx="3" fill="#1e293b" stroke="#34a853" stroke-width="2"/>
              <polygon points="38,75 62,75 50,15" fill="none" stroke="#fbbc04" stroke-width="2"/>
              <circle cx="16" cy="175" r="8" fill="#ea4335"/>
              <circle cx="84" cy="175" r="8" fill="#ea4335"/>
              <text x="-5" y="200" fill="#ffd54f" font-size="10" font-weight="700">14h High-Pressure Jetting</text>
            </g>
            <!-- Arrow & 3x AHTS Tow -->
            <path d="M 165 112 L 325 112" stroke="#34a853" stroke-width="3.5" stroke-dasharray="6,4"/>
            <polygon points="325,106 338,112 325,118" fill="#34a853"/>
            <text x="178" y="100" fill="#81c995" font-size="11" font-weight="700">🚢 3× AHTS Wet Tow (8.4 NM @ 4kt)</text>
            <!-- Target EC-Cleared Well -->
            <g transform="translate(355,18)">
              <rect x="10" y="0" width="12" height="175" fill="none" stroke="#34a853" stroke-width="2"/>
              <rect x="78" y="0" width="12" height="175" fill="none" stroke="#34a853" stroke-width="2"/>
              <rect x="0" y="45" width="100" height="24" rx="3" fill="#064e3b" stroke="#34a853" stroke-width="2"/>
              <text x="10" y="61" fill="#fff" font-size="10" font-weight="700">WELL-IND-004</text>
              <text x="0" y="200" fill="#81c995" font-size="10" font-weight="700">12h Pre-Load · EC Cleared</text>
            </g>
          </svg>
        </div>

        <!-- 4-Phase Gantt Strip -->
        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:6px; font-size:11px;">
          <div style="background:#e8f0fe; padding:7px; border-radius:6px; text-align:center;"><strong>10.0h</strong><br/>Plug & BOP</div>
          <div style="background:#fef7e0; padding:7px; border-radius:6px; text-align:center;"><strong>14.0h</strong><br/>Spudcan Pull</div>
          <div style="background:#e6f4ea; padding:7px; border-radius:6px; text-align:center;"><strong>2.1h</strong><br/>3× AHTS Tow</div>
          <div style="background:#e6f4ea; padding:7px; border-radius:6px; text-align:center;"><strong>12.0h</strong><br/>Pre-Load Jack</div>
        </div>
      </div>

      <!-- Right Full-Height Blueprint: Deepwater Drillship Storm Hang-Off & Heli Evac -->
      <div class="card" style="border-top:4px solid var(--g-red);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <span class="tag tag-red">USE CASE A · CYCLONIC SWELL LOCK (BAY OF BENGAL TODAY: Hs = 4.98m)</span>
            <h3 style="font-size:16px; margin-top:4px;">DP3 Drillship Blueprint (`Dhirubhai KG1 [5]` & `Platinum [6]`)</h3>
          </div>
          <strong style="font-size:13px; color:var(--g-red);">NO RIG MOVE!</strong>
        </div>

        <div class="svg-stage" style="margin:8px 0;">
          <svg viewBox="0 0 520 230" width="100%" height="100%" preserveAspectRatio="xMidYMid meet">
            <rect width="520" height="230" fill="#1a0f14"/>
            <!-- Storm Wave Crest -->
            <path d="M0 82 Q 40 55, 80 82 T 160 82 T 240 82 T 320 82 T 400 82 T 520 82 L 520 190 L 0 190 Z" fill="rgba(234,67,53,0.18)"/>
            <text x="12" y="24" fill="#ff8a80" font-size="10.5" font-weight="700">🔴 BAY OF BENGAL Hs = 2.80m–4.98m · RIG MOVE PHYSICALLY IMPOSSIBLE</text>
            <!-- DP3 Drillship Hull -->
            <polygon points="65,62 245,62 230,88 80,88" fill="#1e293b" stroke="#ff8a80" stroke-width="2"/>
            <polygon points="142,62 168,62 155,16" fill="none" stroke="#fbbc04" stroke-width="2"/>
            <!-- Helideck + Pawan Hans Helicopter Outline -->
            <rect x="215" y="52" width="38" height="8" fill="#34a853"/>
            <path d="M 255 46 Q 345 18, 420 55" fill="none" stroke="#81c995" stroke-width="2.5" stroke-dasharray="5,3"/>
            <!-- Helicopter SVG icon -->
            <g transform="translate(325,22)">
              <ellipse cx="16" cy="10" rx="14" ry="6" fill="#fbbc04"/>
              <line x1="2" y1="2" x2="30" y2="2" stroke="#fff" stroke-width="2"/>
              <text x="-35" y="-5" fill="#81c995" font-size="10.5" font-weight="700">🚁 Pawan Hans Evac (114 Crew)</text>
            </g>
            <!-- Shore Base -->
            <rect x="405" y="55" width="102" height="44" rx="6" fill="#064e3b" stroke="#34a853" stroke-width="2"/>
            <text x="413" y="74" fill="#fff" font-size="10" font-weight="700">ONGC SHORE BASE</text>
            <text x="413" y="89" fill="#81c995" font-size="9.5">Rajahmundry / Paradip</text>
            <!-- LMRP Unlatch & Subsea BOP -->
            <line x1="155" y1="88" x2="155" y2="142" stroke="#ff8a80" stroke-width="3" stroke-dasharray="5,4"/>
            <text x="166" y="125" fill="#ff8a80" font-size="10.5" font-weight="700">⚡ 45s LMRP Disconnect (3 NM DP3 Box)</text>
            <rect x="138" y="158" width="34" height="32" rx="3" fill="#37474f" stroke="#ff8a80" stroke-width="2"/>
            <rect x="0" y="190" width="520" height="40" fill="#1e293b"/>
            <text x="15" y="213" fill="#ffd54f" font-size="10" font-weight="700">SUBSEA BOP BLIND-SHEAR RAMS LOCKED (1,500m DEPTH)</text>
          </svg>
        </div>

        <!-- 4-Phase Storm Protocol Strip -->
        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:6px; font-size:11px;">
          <div style="background:#fce8e6; padding:7px; border-radius:6px; text-align:center;"><strong>10.0h</strong><br/>BOP Hang-Off</div>
          <div style="background:#fce8e6; padding:7px; border-radius:6px; text-align:center;"><strong>45 sec</strong><br/>LMRP Unlatch</div>
          <div style="background:#fef7e0; padding:7px; border-radius:6px; text-align:center;"><strong>2.0h</strong><br/>3 NM DP3 Box</div>
          <div style="background:#e6f4ea; padding:7px; border-radius:6px; text-align:center;"><strong>25 min</strong><br/>🚁 114 Crew Evac</div>
        </div>
      </div>
    </div>
  </section>

  <!-- ==================== SLIDE 3: INTERACTIVE USER PERSONAS & RIG COCKPIT ==================== -->
  <section class="slide" id="s2">
    <div class="slide-hdr">
      <div>
        <div class="slide-kicker">03 · Stakeholder Personas & Operational Workflows</div>
        <div class="slide-title">How Four Offshore Personas Use ORMWO in Gemini Enterprise</div>
      </div>
      <span class="tag tag-blue">👇 Click Any Persona on the Left to Update the Cockpit</span>
    </div>

    <div class="body-split-sidebar">
      <!-- Left Sidebar: 4 Persona Selector Cards -->
      <div style="display:flex; flex-direction:column; gap:8px; height:100%;">
        <div class="click-item active" id="pCard0" onclick="selectPersona(0)" style="flex:1; display:flex; flex-direction:column; justify-content:center;">
          <span class="tag tag-blue" style="width:fit-content;">Persona 01 · Offshore Rig</span>
          <strong style="font-size:14px; margin-top:4px;">👷‍♂️ Offshore Installation Manager (OIM)</strong>
          <span style="font-size:11.5px; color:var(--ink-2);">Commanding Officer onboard `Sagar Samrat` / `KG1`</span>
        </div>
        <div class="click-item" id="pCard1" onclick="selectPersona(1)" style="flex:1; display:flex; flex-direction:column; justify-content:center;">
          <span class="tag tag-green" style="width:fit-content;">Persona 02 · Certifying Authority</span>
          <strong style="font-size:14px; margin-top:4px;">⚓ Marine Warranty Surveyor (MWS)</strong>
          <span style="font-size:11.5px; color:var(--ink-2);">DNV-ST-N001 CoA Approver (`Hs ≤ 1.50m`)</span>
        </div>
        <div class="click-item" id="pCard2" onclick="selectPersona(2)" style="flex:1; display:flex; flex-direction:column; justify-content:center;">
          <span class="tag tag-yellow" style="width:fit-content;">Persona 03 · Fleet & Aviation</span>
          <strong style="font-size:14px; margin-top:4px;">🚁 Marine & Helicopter Logistics Chief</strong>
          <span style="font-size:11.5px; color:var(--ink-2);">3× AHTS Tugs & Pawan Hans Dauphin N3 Dispatch</span>
        </div>
        <div class="click-item" id="pCard3" onclick="selectPersona(3)" style="flex:1; display:flex; flex-direction:column; justify-content:center;">
          <span class="tag tag-red" style="width:fit-content;">Persona 04 · Governance</span>
          <strong style="font-size:14px; margin-top:4px;">🏛️ ONGC Director & CAG #15117 Auditor</strong>
          <span style="font-size:11.5px; color:var(--ink-2);">Statutory MoEFCC EC / Defence NOC Compliance</span>
        </div>
      </div>

      <!-- Right Cockpit: Dynamic Persona Visual & Workflow -->
      <div class="card" id="personaCockpit">
        <!-- Populated by selectPersona() -->
      </div>
    </div>
  </section>

  <!-- ==================== SLIDE 4: INTERACTIVE ADK & VERTEX AI ARCHITECTURE ==================== -->
  <section class="slide" id="s3">
    <div class="slide-hdr">
      <div>
        <div class="slide-kicker">04 · System Architecture & Zero-Hallucination Guardrails</div>
        <div class="slide-title">Single-Root ADK Agent (`Gemini 2.5 Flash`) + Deterministic Python Metocean Engine</div>
      </div>
      <span class="tag tag-green">👇 Click Any Architecture Block in the Diagram Below</span>
    </div>

    <div style="display:grid; grid-template-rows: 1.05fr 0.95fr; gap:12px; height:100%; min-height:0;">
      <!-- Top Row: Interactive SVG System Architecture Diagram with Rig & Satellite Outlines -->
      <div class="svg-stage light" style="padding:10px;">
        <svg viewBox="0 0 1180 215" width="100%" height="100%" preserveAspectRatio="xMidYMid meet">
          <!-- Connecting Flow Arrows -->
          <g stroke="#1a73e8" stroke-width="2.5" stroke-dasharray="5,3" fill="none">
            <line x1="190" y1="108" x2="240" y2="108"/>
            <line x1="415" y1="108" x2="465" y2="108"/>
            <line x1="665" y1="65" x2="730" y2="50"/>
            <line x1="665" y1="108" x2="730" y2="108"/>
            <line x1="665" y1="150" x2="730" y2="168"/>
            <line x1="935" y1="108" x2="985" y2="108"/>
          </g>

          <!-- Node 1: Gemini Enterprise UI -->
          <g cursor="pointer" onclick="inspectArch(0)">
            <rect x="14" y="38" width="176" height="140" rx="10" fill="#ffffff" stroke="#1a73e8" stroke-width="2.5"/>
            <text x="28" y="62" fill="#1a73e8" font-size="11" font-weight="700">01 · GEMINI ENTERPRISE</text>
            <text x="28" y="82" fill="#202124" font-size="13" font-weight="700">Visual A2UI Card +</text>
            <text x="28" y="99" fill="#202124" font-size="13" font-weight="700">Outer Sheets Tables</text>
            <text x="28" y="122" fill="#5f6368" font-size="10.5">• VegaChart inside card</text>
            <text x="28" y="138" fill="#5f6368" font-size="10.5">• Copy-ready tables outside</text>
            <text x="28" y="162" fill="#1a73e8" font-size="10" font-weight="700">🔍 Click to Inspect Code</text>
          </g>

          <!-- Node 2: before_model_callback -->
          <g cursor="pointer" onclick="inspectArch(1)">
            <rect x="240" y="38" width="175" height="140" rx="10" fill="#fef7e0" stroke="#f9ab00" stroke-width="2"/>
            <text x="254" y="62" fill="#b06000" font-size="11" font-weight="700">02 · SANITIZER GUARD</text>
            <text x="254" y="82" fill="#202124" font-size="13" font-weight="700">`before_model_callback`</text>
            <text x="254" y="106" fill="#5f6368" font-size="10.5">• Scrubs prior A2UI JSON</text>
            <text x="254" y="122" fill="#5f6368" font-size="10.5">• Strips inline PNG bytes</text>
            <text x="254" y="138" fill="#5f6368" font-size="10.5">• Prevents token runaway</text>
            <text x="254" y="162" fill="#b06000" font-size="10" font-weight="700">🔍 Click to Inspect Code</text>
          </g>

          <!-- Node 3: Single Root Agent -->
          <g cursor="pointer" onclick="inspectArch(2)">
            <rect x="465" y="38" width="200" height="140" rx="10" fill="#e8f0fe" stroke="#1a73e8" stroke-width="2.5"/>
            <text x="480" y="62" fill="#1a73e8" font-size="11" font-weight="700">03 · VERTEX AI AGENT ENGINE</text>
            <text x="480" y="82" fill="#202124" font-size="13.5" font-weight="700">Single Root ADK Agent</text>
            <text x="480" y="100" fill="#1e8e3e" font-size="11" font-weight="700">`gemini-2.5-flash` (temp=0.0)</text>
            <text x="480" y="122" fill="#5f6368" font-size="10.5">• Zero math in LLM tokens</text>
            <text x="480" y="138" fill="#5f6368" font-size="10.5">• CAG #15117 domain rules</text>
            <text x="480" y="162" fill="#1a73e8" font-size="10" font-weight="700">🔍 Click to Inspect Code</text>
          </g>

          <!-- Node 4A, 4B, 4C: Deterministic Python Tool Suite -->
          <g cursor="pointer" onclick="inspectArch(3)">
            <rect x="730" y="12" width="205" height="56" rx="8" fill="#e6f4ea" stroke="#1e8e3e" stroke-width="2"/>
            <text x="742" y="32" fill="#1e8e3e" font-size="10.5" font-weight="700">04A · OPEN-METEO MARINE API</text>
            <text x="742" y="50" fill="#202124" font-size="11" font-weight="600">Live ECMWF `Hs`, `Tp` & Wind</text>
          </g>
          <g cursor="pointer" onclick="inspectArch(4)">
            <rect x="730" y="78" width="205" height="56" rx="8" fill="#e6f4ea" stroke="#1e8e3e" stroke-width="2"/>
            <text x="742" y="98" fill="#1e8e3e" font-size="10.5" font-weight="700">04B · 10,000-RUN MONTE CARLO</text>
            <text x="742" y="116" fill="#202124" font-size="11" font-weight="600">3× AHTS Wet-Tow & P50 Cost</text>
          </g>
          <g cursor="pointer" onclick="inspectArch(5)">
            <rect x="730" y="144" width="205" height="56" rx="8" fill="#fce8e6" stroke="#d93025" stroke-width="2"/>
            <text x="742" y="164" fill="#d93025" font-size="10.5" font-weight="700">04C · 120-WELL EC/NOC REGISTRY</text>
            <text x="742" y="182" fill="#202124" font-size="11" font-weight="600">Rejects Non-EC Wells (CAG #15117)</text>
          </g>

          <!-- Node 5: After-Agent Publisher -->
          <g cursor="pointer" onclick="inspectArch(6)">
            <rect x="985" y="38" width="180" height="140" rx="10" fill="#ffffff" stroke="#1e8e3e" stroke-width="2.5"/>
            <text x="998" y="62" fill="#1e8e3e" font-size="11" font-weight="700">05 · VISUAL PUBLISHER</text>
            <text x="998" y="82" fill="#202124" font-size="12.5" font-weight="700">`after_agent_callback`</text>
            <text x="998" y="104" fill="#5f6368" font-size="10.5">• 1680×1080 4-Panel PNG</text>
            <text x="998" y="120" fill="#5f6368" font-size="10.5">• Interactive HTML EEZ Map</text>
            <text x="998" y="136" fill="#5f6368" font-size="10.5">• Printable MWS SOP Doc</text>
            <text x="998" y="162" fill="#1e8e3e" font-size="10" font-weight="700">🔍 Click to Inspect Code</text>
          </g>
        </svg>
      </div>

      <!-- Bottom Row: Split Code & Live Contract Drawer -->
      <div class="body-split-2" id="archDetailBox">
        <!-- Populated by inspectArch() -->
      </div>
    </div>
  </section>

  <!-- ==================== SLIDE 5: EMBEDDED 4-PANEL INFOGRAPHIC + CLICKABLE FLEET [1]–[6] ==================== -->
  <section class="slide" id="s4">
    <div class="slide-hdr">
      <div>
        <div class="slide-kicker">05 · Live India EEZ Visual Infographic & Fleet Directives [1]–[6]</div>
        <div class="slide-title">Click Any Rig Row to Inspect Its Hull Outline, Live Wave Gate & Rejected Non-EC Well</div>
      </div>
      <div style="display:flex; gap:8px;">
        <a href="{map_url}" target="_blank" class="btn outline" style="text-decoration:none; padding:5px 12px;">🌐 Launch Full-Screen HTML Map ↗</a>
        <a href="{sop_url}" target="_blank" class="btn outline" style="text-decoration:none; padding:5px 12px;">📋 Open Printable MWS SOP ↗</a>
      </div>
    </div>

    <div class="body-split-2">
      <!-- Left: Actual High-Res 4-Panel Infographic Image + Selected Rig Blueprint Overlay -->
      <div class="card" style="padding:12px; gap:8px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span class="tag tag-blue" id="selectedRigTitle">SELECTED RIG [1] · SAGAR SAMRAT (JACK-UP · MUMBAI HIGH)</span>
          <a href="{png_url}" target="_blank" style="font-size:11.5px; font-weight:600; color:var(--g-blue); text-decoration:none;">🔍 Open Full 1680×1080 PNG ↗</a>
        </div>
        <div class="svg-stage" style="background:#090f1c; position:relative;">
          <img src="{inline_png_src}" alt="India EEZ 4-Panel Tactical Infographic" style="width:100%; height:100%; object-fit:contain;" />
        </div>
      </div>

      <!-- Right: Interactive Fleet Directives Table + Selected Rig Outline Card -->
      <div class="card">
        <table class="modern-tbl">
          <thead>
            <tr>
              <th>Rig (`Click Row`)</th>
              <th>Basin & Live `Hs`</th>
              <th>MWS Directive</th>
              <th>Target / Shore Base</th>
              <th>Saved</th>
            </tr>
          </thead>
          <tbody>
            <tr onclick="selectRigRow(0)" style="background:#e8f0fe;">
              <td><strong>[1] Sagar Samrat</strong></td>
              <td>Mumbai High · <span class="tag tag-green">1.22m</span></td>
              <td>🟢 Wet Tow (`8.4 NM`)</td>
              <td><code>WELL-IND-004</code></td>
              <td><strong>₹11.50 Cr</strong></td>
            </tr>
            <tr onclick="selectRigRow(1)">
              <td><strong>[2] Sagar Ratna</strong></td>
              <td>Mumbai High · <span class="tag tag-green">1.21m</span></td>
              <td>🟢 Wet Tow (`9.6 NM`)</td>
              <td><code>WELL-IND-005</code></td>
              <td><strong>₹10.80 Cr</strong></td>
            </tr>
            <tr onclick="selectRigRow(2)">
              <td><strong>[3] Sagar Bhushan</strong></td>
              <td>Heera-Bassein · <span class="tag tag-green">1.18m</span></td>
              <td>🟢 Wet Tow (`7.2 NM`)</td>
              <td><code>WELL-IND-006</code></td>
              <td><strong>₹9.60 Cr</strong></td>
            </tr>
            <tr onclick="selectRigRow(3)">
              <td><strong>[4] Aban Ice</strong></td>
              <td>Tapti-Daman · <span class="tag tag-green">0.78m</span></td>
              <td>🟢 Wet Tow (`6.8 NM`)</td>
              <td><code>WELL-IND-008</code></td>
              <td><strong>₹8.90 Cr</strong></td>
            </tr>
            <tr onclick="selectRigRow(4)">
              <td><strong>[5] Dhirubhai KG1</strong></td>
              <td>KG-DWN · <span class="tag tag-red">2.80m</span></td>
              <td>🔴 BOP Hang-Off + 🚁 Evac</td>
              <td><code>🚁 Rajahmundry</code></td>
              <td><strong>₹14.20 Cr</strong></td>
            </tr>
            <tr onclick="selectRigRow(5)">
              <td><strong>[6] Platinum Explorer</strong></td>
              <td>Mahanadi · <span class="tag tag-red">4.98m</span></td>
              <td>🔴 LMRP Unlatch + 🚁 Evac</td>
              <td><code>🚁 Paradip Base</code></td>
              <td><strong>₹16.50 Cr</strong></td>
            </tr>
          </tbody>
        </table>

        <!-- Selected Rig Engineering & Rejected Well Box -->
        <div id="rigRowDetailBox" style="background:#f8fbff; border:1px solid #d2e3fc; border-radius:10px; padding:12px 14px;">
          <!-- Populated by selectRigRow() -->
        </div>
      </div>
    </div>
  </section>

  <!-- ==================== SLIDE 6: ROI & LIVE GEMINI ENTERPRISE PROMPT SIMULATOR ==================== -->
  <section class="slide" id="s5">
    <div class="slide-hdr">
      <div>
        <div class="slide-kicker">06 · Live Meeting Demo Runner & Quantified Impact</div>
        <div class="slide-title">Click Any Prompt to Copy for Gemini Enterprise & Preview the Deterministic Output</div>
      </div>
      <span class="tag tag-green">Reasoning Engine: `4687908012755517440`</span>
    </div>

    <div class="body-split-2">
      <!-- Left: 3 Interactive Prompt Cards -->
      <div style="display:flex; flex-direction:column; gap:10px; height:100%;">
        <div class="click-item active" id="demoCard0" onclick="selectDemoPrompt(0)" style="flex:1; display:flex; flex-direction:column; justify-content:space-between;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="tag tag-blue">Demo Prompt 01 · Executive Fleet Sweep</span>
            <button class="btn" style="padding:4px 12px; font-size:11px;" onclick="event.stopPropagation(); copyDemoPrompt(0, this)">📋 Copy Prompt</button>
          </div>
          <p style="font-size:12px; color:var(--ink); font-weight:500;" id="demoP0">Run a live metocean and CAG Audit #15117 fleet assessment across all 20 offshore rigs in India's EEZ. Compare today's real-time wave and wind conditions in Mumbai High versus the Bay of Bengal (KG-DWN and Mahanadi), and show the exact operational directive, well-to-well move or in-place storm protocol, and avoided NPT for rigs [1] through [6].</p>
        </div>

        <div class="click-item" id="demoCard1" onclick="selectDemoPrompt(1)" style="flex:1; display:flex; flex-direction:column; justify-content:space-between;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="tag tag-green">Demo Prompt 02 · Calm MWS Rig Move (`[1]–[4]`)</span>
            <button class="btn" style="padding:4px 12px; font-size:11px; background:var(--g-green);" onclick="event.stopPropagation(); copyDemoPrompt(1, this)">📋 Copy Prompt</button>
          </div>
          <p style="font-size:12px; color:var(--ink); font-weight:500;" id="demoP1">Sagar Samrat [1] and Sagar Ratna [2] have completed their current wells in Mumbai High. Check live Open-Meteo wave height against the 1.50m MWS spudcan extraction limit, explain why closer non-EC wells were rejected per CAG Report #15117, and provide the hour-by-hour 3x AHTS tug wet-tow plan.</p>
        </div>

        <div class="click-item" id="demoCard2" onclick="selectDemoPrompt(2)" style="flex:1; display:flex; flex-direction:column; justify-content:space-between;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="tag tag-red">Demo Prompt 03 · Bay of Bengal Swell Lock (`[5]–[6]`)</span>
            <button class="btn" style="padding:4px 12px; font-size:11px; background:var(--g-red);" onclick="event.stopPropagation(); copyDemoPrompt(2, this)">📋 Copy Prompt</button>
          </div>
          <p style="font-size:12px; color:var(--ink); font-weight:500;" id="demoP2">Why can't Dhirubhai Deepwater KG1 [5] and Platinum Explorer [6] move to a new well during today's high swells in the Bay of Bengal? Provide the DNV-ST-N001 MWS limits, the in-place BOP Hang-Off and LMRP Disconnect timeline, and the Pawan Hans helicopter evacuation plan.</p>
        </div>
      </div>

      <!-- Right: Simulated Gemini Enterprise Response Preview + Rig Silhouette -->
      <div class="card" id="demoPreviewBox" style="background:#0d1b2a; color:#fff; border-color:#1e3a5f;">
        <!-- Populated by selectDemoPrompt() -->
      </div>
    </div>
  </section>

</main>

<!-- 4. Bottom Navigation Footer -->
<footer class="bot-nav">
  <button class="btn outline" id="prevBtn" onclick="stepSlide(-1)" disabled>← Previous Slide</button>
  <div style="font-size:12px; font-weight:600; color:var(--ink-2);" id="footerStatus">
    Slide 1 of 6 · Press <kbd style="background:#f1f3f4;padding:2px 6px;border-radius:4px;border:1px solid #ccc;">←</kbd> <kbd style="background:#f1f3f4;padding:2px 6px;border-radius:4px;border:1px solid #ccc;">→</kbd> or Click Any Interactive Element
  </div>
  <button class="btn" id="nextBtn" onclick="stepSlide(1)">Next Slide →</button>
</footer>

<script>
  let cur = 0;
  const total = 6;

  function showSlide(n) {{
    cur = Math.max(0, Math.min(total - 1, n));
    for (let i = 0; i < total; i++) {{
      document.getElementById(`s${{i}}`).classList.toggle('active', i === cur);
    }}
    document.querySelectorAll('.nav-pill').forEach((p, i) => p.classList.toggle('active', i === cur));
    document.getElementById('prevBtn').disabled = (cur === 0);
    const nb = document.getElementById('nextBtn');
    if (cur === total - 1) {{
      nb.innerText = '↺ Restart Deck';
      nb.onclick = () => showSlide(0);
    }} else {{
      nb.innerText = 'Next Slide →';
      nb.onclick = () => stepSlide(1);
    }}
    document.getElementById('footerStatus').innerHTML =
      `Slide ${{cur + 1}} of ${{total}} · Press <kbd style="background:#f1f3f4;padding:2px 6px;border-radius:4px;border:1px solid #ccc;">←</kbd> <kbd style="background:#f1f3f4;padding:2px 6px;border-radius:4px;border:1px solid #ccc;">→</kbd> or Click Any Interactive Element`;
  }}

  function stepSlide(d) {{ showSlide(cur + d); }}

  document.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowRight' || e.key === 'PageDown') stepSlide(1);
    if (e.key === 'ArrowLeft' || e.key === 'PageUp') stepSlide(-1);
  }});

  // Slide 1 Interactive Pillar Switcher
  const s1Data = [
    {{
      hdr: 'CAG #15117 PILLAR 01 · STATUTORY EC & NOC GATE',
      l1: '❌ Rejected MH-N-002 (4.1 NM): Missing MoEFCC EC',
      l2: '✅ Selected WELL-IND-004 (8.4 NM): EC + Navy NOC OK',
      l3: 'Avoided Waiting-on-Clearance NPT: ₹11.50 Cr'
    }},
    {{
      hdr: 'CAG #15117 PILLAR 02 · MWS 1.50m WAVE GATE',
      l1: '🟢 Mumbai High Live Hs = 1.22m <= 1.50m (Move OK)',
      l2: '🔴 Bay of Bengal Live Hs = 4.98m (Move Prohibited)',
      l3: 'Avoided Storm Riser Damage & Idle NPT: ₹30.70 Cr'
    }},
    {{
      hdr: 'CAG #15117 PILLAR 03 · 3× AHTS TUG & HELI DISPATCH',
      l1: '🚢 3× ONGC 150T AHTS Tugs Synchronized (4.0 kt)',
      l2: '🚁 Pawan Hans Dauphin N3 (114 Crew Evac in 25m)',
      l3: 'Eliminates Vessel Waiting Time Across 20 Rigs'
    }}
  ];
  function selectSlide1Pillar(idx) {{
    [0,1,2].forEach(i => document.getElementById(`cag${{i}}`).classList.toggle('active', i === idx));
    const d = s1Data[idx];
    document.getElementById('svgCalloutHdr').textContent = d.hdr;
    document.getElementById('svgCalloutLine1').textContent = d.l1;
    document.getElementById('svgCalloutLine2').textContent = d.l2;
    document.getElementById('svgCalloutLine3').textContent = d.l3;
  }}

  // Slide 3 Personas Cockpit
  const personas = [
    {{
      title: '👷‍♂️ Offshore Installation Manager (OIM) — Rig Commander (`Sagar Samrat` / `Dhirubhai KG1`)',
      pain: 'Must decide whether to begin a 14-hour spudcan water-jetting extraction or lock into subsea BOP storm hang-off with 110 personnel onboard.',
      action: 'Queries ORMWO in Gemini Enterprise to verify live Open-Meteo `Hs` against the `1.50m` MWS ceiling and prints the hour-by-hour MWS Engineering SOP.',
      sla: 'Decision time reduced from 6 hours of shore phone calls to 12 seconds.'
    }},
    {{
      title: '⚓ Marine Warranty Surveyor (MWS — DNV-ST-N001 Certifying Authority)',
      pain: 'Cannot issue a Certificate of Approval (CoA) for a jack-up rig move unless the 48h forecast swell remains ≤ 1.50m and 3× AHTS tugs meet bollard-pull margins.',
      action: 'Reviews the 10,000-iteration Monte Carlo simulation (`P10 / P50 / P90` wet-tow duration) and GenCast/GraphCast 48h wave envelope on the 4-Panel Infographic.',
      sla: '100% auditable DNV-ST-N001 wave & wind compliance logged automatically.'
    }},
    {{
      title: '🚁 Marine & Aviation Logistics Chief (`3× AHTS Tugs` & `Pawan Hans Helicopters`)',
      pain: 'Needs exact mobilization hours for `3× ONGC AHTS Tugs` in Mumbai High while scheduling `Pawan Hans Dauphin N3` crew evacuation sorties in the Bay of Bengal.',
      action: 'Copies the outer Markdown Engineering Phase Table with 1 click directly into Google Sheets to dispatch vessels and shore-base helicopters.',
      sla: 'Zero waiting-on-tug NPT; 114 non-essential crew evacuated to Rajahmundry & Paradip in 25 minutes.'
    }},
    {{
      title: '🏛️ ONGC Asset Director & CAG #15117 Compliance Auditor',
      pain: 'Accountable to the Ministry of Petroleum & Natural Gas and CAG auditors for eliminating the 426.5 idle rig-days caused by mobilizing rigs to un-cleared wells.',
      action: 'Audits the rejected closer wells (`MH-N-002` rejected due to missing MoEFCC EC) and verifies the ₹71.50 Crore avoided NPT ledger.',
      sla: '100% statutory MoEFCC EC & Defence NOC compliance across all 120 candidate wells.'
    }}
  ];
  function selectPersona(idx) {{
    [0,1,2,3].forEach(i => document.getElementById(`pCard${{i}}`).classList.toggle('active', i === idx));
    const p = personas[idx];
    document.getElementById('personaCockpit').innerHTML = `
      <div>
        <span class="tag tag-blue">ACTIVE PERSONA WORKFLOW & RIG TELEMETRY VIEW</span>
        <h3 style="font-size:18px; margin-top:6px;">${{p.title}}</h3>
      </div>
      <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:12px;">
        <div style="background:#fce8e6; padding:12px; border-radius:8px; border-left:3px solid var(--g-red);">
          <strong style="font-size:11px; color:var(--g-red); text-transform:uppercase;">Operational Bottleneck</strong>
          <p style="font-size:12px; margin-top:4px; line-height:1.45;">${{p.pain}}</p>
        </div>
        <div style="background:#e8f0fe; padding:12px; border-radius:8px; border-left:3px solid var(--g-blue);">
          <strong style="font-size:11px; color:var(--g-blue); text-transform:uppercase;">Gemini Enterprise Workflow</strong>
          <p style="font-size:12px; margin-top:4px; line-height:1.45;">${{p.action}}</p>
        </div>
        <div style="background:#e6f4ea; padding:12px; border-radius:8px; border-left:3px solid var(--g-green);">
          <strong style="font-size:11px; color:var(--g-green); text-transform:uppercase;">Quantified SLA Gain</strong>
          <p style="font-size:12px; margin-top:4px; line-height:1.45;">${{p.sla}}</p>
        </div>
      </div>
      <div class="svg-stage" style="max-height:185px;">
        <svg viewBox="0 0 680 140" width="100%" height="100%" preserveAspectRatio="xMidYMid meet">
          <rect width="680" height="140" fill="#0d1b2a"/>
          <text x="20" y="26" fill="#60a5fa" font-size="11" font-weight="700">BEFORE vs. AFTER ORMWO AGENT EXECUTION TIMELINE</text>
          <rect x="20" y="42" width="420" height="28" rx="4" fill="#ea4335"/>
          <text x="30" y="60" fill="#fff" font-size="11" font-weight="700">❌ Legacy Manual Triage: 6.0 Hours Phone/Spreadsheet Delay + Un-Cleared Well Risk</text>
          <rect x="20" y="84" width="165" height="28" rx="4" fill="#34a853"/>
          <text x="30" y="102" fill="#fff" font-size="11" font-weight="700">✅ ORMWO Agent: 12s</text>
          <text x="200" y="102" fill="#81c995" font-size="11.5" font-weight="700">Live Open-Meteo + EC/NOC Gate + 10,000-Run Monte Carlo + Printable SOP</text>
        </svg>
      </div>
    `;
  }}

  // Slide 4 Architecture Inspector
  const archDetails = [
    {{
      title: '01 · Gemini Enterprise & A2UI v0.9 Presentation Layer (`app/render/rig_fleet_card.py`)',
      why: 'Renders ONLY the visual `VegaChart` interactive infographic inside the card box while emitting copy-ready Google Sheets tables and `###` headed links outside in the main Markdown stream.',
      code: `chart_comp = {{"id": "rfc-chart-vega", "component": "VegaChart", "spec": vega_spec, "height": 860}}\n# Text tables & links emitted OUTSIDE card for 1-click copy-paste to Google Sheets`
    }},
    {{
      title: '02 · History Sanitizer Guardrail (`app/integration/agent.py :: sanitize_llm_request_history`)',
      why: 'Scrubs prior-turn `<a2a_datapart_json>` envelopes and `inline_data` PNG bytes before calling Gemini 2.5 Flash so multi-turn conversations never hit token exhaustion loops.',
      code: `for part in content.parts:\n    if part.inline_data is not None: continue  # Strip prior PNG bytes\n    if "<a2a_datapart_json>" in (part.text or ""): continue`
    }},
    {{
      title: '03 · Single Root ADK Agent (`Gemini 2.5 Flash`, `temperature=0.0`)',
      why: 'Enforces strict determinism (`thinking_budget=0`, `temperature=0.0`) and delegates 100% of oceanography, geometry, and cost calculations to Python tools.',
      code: `root_agent = Agent(name="rig_navigator_agent", model=Gemini(model="gemini-2.5-flash"),\n                   tools=[forecast_storm_zones_and_redeployments, ...])`
    }},
    {{
      title: '04A · Live Open-Meteo Marine & Atmospheric Feed (`app/rigs/live_metocean_feed.py`)',
      why: 'Queries `https://marine-api.open-meteo.com/v1/marine` in real time across all 7 Indian offshore basins (`Mumbai High Hs = 1.22m` vs `Bay of Bengal Hs = 4.98m`).',
      code: `GET https://marine-api.open-meteo.com/v1/marine?latitude=19.41&longitude=71.33&current=wave_height\n-> {{"basin": "Mumbai High", "live_hs_m": 1.22, "gate": "GREEN_MWS_RIG_MOVE_WINDOW"}}`
    }},
    {{
      title: '04B · 10,000-Iteration NumPy Monte Carlo Optimizer (`app/rigs/monte_carlo_optimizer.py`)',
      why: 'Simulates 10,000 wet-tow trajectories with `3× ONGC AHTS Tugs` (150T BP) to compute P10/P50/P90 transit hours and net avoided NPT (`₹ Cr`).',
      code: `sim = execute_monte_carlo_transit_simulation(rig_id="RIG-OFFSHORE-04")\n# -> p50_hours=38.1, distance_nm=8.4, avoided_npt_cr=11.50`
    }},
    {{
      title: '04C · 120-Well Statutory EC/NOC Registry (`app/rigs/india_eez_dataset.py`)',
      why: 'Prevents the #1 CAG Report #15117 failure mode by rejecting geographically closer wells that lack MoEFCC Environmental Clearance or Defence NOC.',
      code: `Rejected: MH-N-002 (4.1 NM) -> Reason: Missing MoEFCC Environmental Clearance\nSelected: WELL-IND-004 (8.4 NM) -> Status: EC_CLEARED + DEFENCE_NOC_VERIFIED`
    }},
    {{
      title: '05 · Multi-Surface Cloud Publisher (`after_agent_callback`)',
      why: 'Generates the 1680×1080 4-Panel PNG Infographic, Full-Screen Interactive HTML Map, and Printable MWS SOP Document, publishing all three to GCS.',
      code: `publish_interactive_html_map(pending_fleet, surface_id, png_bytes=png_bytes)\n# Uploads india_eez_latest.html, india_eez_rig_move_sop_latest.html & 4-panel PNG`
    }}
  ];
  function inspectArch(idx) {{
    const d = archDetails[idx];
    document.getElementById('archDetailBox').innerHTML = `
      <div class="card" style="background:#f8fbff; border-color:#d2e3fc;">
        <span class="tag tag-blue">SELECTED ARCHITECTURE COMPONENT</span>
        <h3 style="font-size:16px; color:var(--g-blue); margin-top:4px;">${{d.title}}</h3>
        <p style="font-size:13px; color:var(--ink); line-height:1.55; margin-top:6px;">${{d.why}}</p>
        <div style="font-size:11.5px; color:var(--g-green); font-weight:700; margin-top:auto;">✅ Verified by 13 Automated Unit Tests (`pytest tests/unit`)</div>
      </div>
      <div class="card" style="background:#1e1e1e; color:#e8eaed;">
        <span style="font-family:'JetBrains Mono',monospace; font-size:11px; color:#8ab4f8;">LIVE PYTHON IMPLEMENTATION CONTRACT</span>
        <pre style="font-family:'JetBrains Mono',monospace; font-size:12px; color:#e8eaed; white-space:pre-wrap; line-height:1.5; margin-top:8px;">${{d.code}}</pre>
      </div>
    `;
  }}

  // Slide 5 Rig Row Selector
  const rigRows = [
    {{ name: '[1] Sagar Samrat (Jack-Up · Mumbai High)', wave: 'Live Hs = 1.22m (🟢 Calm MWS Window <= 1.50m)', plan: '10h BOP/Plug + 14h Spudcan Jetting + 2.1h Wet Tow (8.4 NM via 3× AHTS) + 12h Pre-Load Jacking = 38.1h Total', rej: 'Rejected closer well `MH-N-002` (4.1 NM) due to missing MoEFCC Environmental Clearance (CAG #15117).' }},
    {{ name: '[2] Sagar Ratna (Jack-Up · Mumbai High)', wave: 'Live Hs = 1.21m (🟢 Calm MWS Window <= 1.50m)', plan: '10h Dry-Hole P&A + 14h Spudcan Pull + 2.4h Wet Tow (9.6 NM via 3× AHTS) + 12h Pre-Load = 38.4h Total', rej: 'Rejected closer well `MH-S-003` (5.2 NM) due to 500m subsea pipeline safety buffer violation.' }},
    {{ name: '[3] Sagar Bhushan (Drillship · Heera-Bassein)', wave: 'Live Hs = 1.18m (🟢 Calm MWS Window <= 1.50m)', plan: '8h Xmas Tree Cap + 4h Anchor Pull + 1.8h Wet Tow (7.2 NM) + 8h Spread Mooring = 21.8h Total', rej: 'Rejected closer well `HPB-004` (3.9 NM) because 30-inch conductor was not pre-jetted.' }},
    {{ name: '[4] Aban Ice (Jack-Up · Tapti-Daman)', wave: 'Live Hs = 0.78m (🟢 Calm MWS Window <= 1.50m)', plan: '10h BOP Disconnect + 12h Spudcan Pull + 1.7h Wet Tow (6.8 NM via 3× AHTS) + 11h Pre-Load = 34.7h Total', rej: 'Rejected closer well `TD-C26-02` (4.4 NM) due to pending Naval Defence NOC.' }},
    {{ name: '[5] Dhirubhai Deepwater KG1 (DP3 Drillship · Bay of Bengal)', wave: 'Live Hs = 2.80m (🔴 Active Cyclonic Swell Lock > 2.50m)', plan: 'NO RIG MOVE! 10h Subsea BOP Hang-Off + 45s LMRP Disconnect (3.0 NM DP3 Storm Box) + 🚁 25m Flight (54 Crew to Rajahmundry)', rej: 'Rig move strictly prohibited by MWS (`Hs = 2.80m > 1.50m` ceiling).' }},
    {{ name: '[6] Platinum Explorer (DP3 Drillship · Mahanadi Bay of Bengal)', wave: 'Live Hs = 4.98m (🔴 Severe Cyclonic Swell Lock > 2.50m)', plan: 'NO RIG MOVE! 9.5h Blind-Shear Ram Shut-In + 45s LMRP Unlatch (DP3 Weather-Vane) + 🚁 18m Flight (60 Crew to Paradip Base)', rej: 'Rig move strictly prohibited by MWS (`Hs = 4.98m > 1.50m` ceiling).' }}
  ];
  function selectRigRow(idx) {{
    const r = rigRows[idx];
    document.getElementById('selectedRigTitle').textContent = `SELECTED RIG · ${{r.name}}`;
    document.getElementById('rigRowDetailBox').innerHTML = `
      <div style="font-size:13px; font-weight:700; color:var(--g-blue);">${{r.name}} — ${{r.wave}}</div>
      <div style="font-size:12px; color:var(--ink); margin-top:4px;"><strong>Engineering Breakdown:</strong> ${{r.plan}}</div>
      <div style="font-size:11.5px; color:var(--g-red); margin-top:4px;"><strong>CAG #15117 Statutory Gate:</strong> ${{r.rej}}</div>
    `;
  }}

  // Slide 6 Demo Simulator
  const demoOutputs = [
    `### ⚓ 1. Live Metocean Reality & CAG Audit #15117 Briefing\n• 🟢 Western Offshore (Mumbai High Hs = 1.22m <= 1.50m): Authorized 3× AHTS Wet Tow for Completed Rigs [1]–[4].\n• 🔴 Eastern Offshore (Bay of Bengal Hs = 2.80m–4.98m): Active Swell Lock! In-Place BOP Hang-Off + 🚁 Evacuate 114 Crew [5]–[6].\n\n### 📋 2. Master Fleet Directives (Copy-Ready for Google Sheets)\n[1] Sagar Samrat -> WELL-IND-004 (8.4 NM · 38.1h · ₹11.50 Cr)\n[5] Dhirubhai KG1 -> 🚁 Rajahmundry Base (BOP Hang-Off · ₹14.20 Cr)`,
    `### 🟢 Mumbai High Calm MWS Rig-Move Plan ([1] Sagar Samrat & [2] Sagar Ratna)\n• Live Open-Meteo Wave Height: Hs = 1.22m (Passes DNV-ST-N001 <= 1.50m Spudcan Limit)\n• CAG #15117 Clearance Gate: Rejected MH-N-002 (4.1 NM — Missing MoEFCC EC); Selected WELL-IND-004 (8.4 NM — EC & NOC Verified)\n• 38.1h Execution: 10h Plug/BOP + 14h Spudcan Jetting + 2.1h 3× AHTS Tow + 12h Pre-Load Jacking`,
    `### 🔴 Bay of Bengal Cyclonic Swell Lock & Helicopter Evacuation ([5] KG1 & [6] Platinum)\n• Why Rigs Cannot Move: Lowering legs or pulling 1,500m riser in Hs = 2.80m–4.98m causes catastrophic leg punch-through / riser buckle.\n• Emergency Protocol: 10h Subsea BOP Hang-Off -> 45s LMRP Unlatch -> 3.0 NM DP3 Storm Box -> 🚁 Pawan Hans Dauphin N3 Evac (114 Crew to Rajahmundry & Paradip)`
  ];
  function selectDemoPrompt(idx) {{
    [0,1,2].forEach(i => document.getElementById(`demoCard${{i}}`).classList.toggle('active', i === idx));
    document.getElementById('demoPreviewBox').innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span class="tag tag-green">SIMULATED GEMINI ENTERPRISE RESPONSE PREVIEW</span>
        <span style="font-size:11px; color:#8ab4f8; font-family:'JetBrains Mono';">A2UI Card + Outer Copyable Markdown</span>
      </div>
      <div class="svg-stage" style="max-height:130px; margin:4px 0;">
        <svg viewBox="0 0 560 115" width="100%" height="100%" preserveAspectRatio="xMidYMid meet">
          <rect width="560" height="115" fill="#091322"/>
          <line x1="0" y1="78" x2="560" y2="78" stroke="#4da3ff" stroke-width="2" stroke-dasharray="4,3"/>
          <!-- Left Jack-Up Rig Outline -->
          <rect x="45" y="18" width="10" height="78" fill="none" stroke="#60a5fa" stroke-width="2"/>
          <rect x="105" y="18" width="10" height="78" fill="none" stroke="#60a5fa" stroke-width="2"/>
          <rect x="35" y="45" width="90" height="18" rx="3" fill="#1e293b" stroke="#34a853" stroke-width="2"/>
          <polygon points="70,45 90,45 80,12" fill="none" stroke="#fbbc04" stroke-width="2"/>
          <text x="22" y="104" fill="#81c995" font-size="9.5" font-weight="700">[1]–[4] Jack-Up Wet Tow (Hs=1.22m)</text>
          <!-- Middle 3x AHTS Tug -->
          <path d="M 140 66 L 235 66" stroke="#34a853" stroke-width="2.5" stroke-dasharray="5,3"/>
          <polygon points="240,60 295,60 305,72 235,72" fill="#34a853"/>
          <text x="235" y="52" fill="#fff" font-size="9.5" font-weight="700">🚢 3× AHTS Tugs</text>
          <!-- Right DP3 Drillship + Helicopter -->
          <polygon points="370,60 490,60 480,76 380,76" fill="#1e293b" stroke="#ea4335" stroke-width="2"/>
          <polygon points="420,60 440,60 430,15" fill="none" stroke="#fbbc04" stroke-width="2"/>
          <text x="365" y="104" fill="#ff8a80" font-size="9.5" font-weight="700">[5]–[6] DP3 BOP Hang-Off + 🚁 Evac (Hs=4.98m)</text>
        </svg>
      </div>
      <pre style="font-family:'JetBrains Mono',monospace; font-size:11.5px; color:#e8eaed; white-space:pre-wrap; line-height:1.48; background:#112240; padding:12px; border-radius:8px; border:1px solid #1e3a5f; flex:1;">${{demoOutputs[idx]}}</pre>
      <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#81c995;">
        <span>✅ Visual 4-Panel Infographic Attached in A2UI Card</span>
        <span>✅ Outer Tables Ready for 1-Click Copy to Google Sheets</span>
      </div>
    `;
  }}

  function copyDemoPrompt(idx, btn) {{
    const txt = document.getElementById(`demoP${{idx}}`).innerText;
    navigator.clipboard.writeText(txt);
    const old = btn.innerText;
    btn.innerText = '✅ Copied!';
    setTimeout(() => {{ btn.innerText = old; }}, 1800);
  }}

  // Initialize all interactive views
  selectSlide1Pillar(0);
  selectPersona(0);
  inspectArch(0);
  selectRigRow(0);
  selectDemoPrompt(0);
</script>
</body>
</html>
"""
