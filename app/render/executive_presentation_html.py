"""Google-Branded Interactive Minimal Website-Style Presentation (HTML PPT) for ORMWO.

Features:
- High-density, minimal, modern Google Cloud / DeepMind widescreen 16:9 executive presentation deck.
- Bulletproof slide navigation: direct DOM activation (`.slide.active`), Next/Prev buttons, slide pill jumps, and arrow keys (←/→).
- Rich technical blueprints: Vector SVG outlines of Jack-Up rigs (spudcan, legs, hull, derrick), DP3 Drillships (subsea BOP, LMRP unlatch, helideck, thrusters), AHTS tugs, and Pawan Hans evacuation helicopters.
- Interactive hotspots: Click any part of a rig schematic to inspect its physical limits (spudcan penetration, 1.50m wave punch-through, LMRP disconnect).
- Real-time metocean basin comparison: Mumbai High calm window vs. Bay of Bengal cyclonic swell lock.
- Clean Google typography, Google 4-color branding (#4285F4, #EA4335, #FBBC04, #34A853), and zero wasted whitespace.
"""

from __future__ import annotations

import os


def build_executive_presentation_html(project_id: str | None = None) -> str:
    """Return the complete self-contained minimal Google-branded interactive presentation website."""
    proj = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT") or "zuhaibp-ai"
    bucket = f"{proj}-agent-staging"
    map_url = f"https://storage.mtls.cloud.google.com/{bucket}/interactive_maps/india_eez_latest.html"
    sop_url = f"https://storage.mtls.cloud.google.com/{bucket}/interactive_maps/india_eez_rig_move_sop_latest.html"
    png_url = f"https://storage.mtls.cloud.google.com/{bucket}/interactive_maps/india_eez_4panel_latest.png"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>ORMWO — Executive Presentation & Technical Blueprints</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --g-blue: #1a73e8;
    --g-blue-light: #e8f0fe;
    --g-red: #ea4335;
    --g-red-light: #fce8e6;
    --g-yellow: #fbbc04;
    --g-yellow-light: #fef7e0;
    --g-green: #34a853;
    --g-green-light: #e6f4ea;
    --g-dark: #202124;
    --g-gray: #5f6368;
    --g-border: #dadce0;
    --g-surface: #ffffff;
    --g-bg: #f8f9fa;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--g-bg);
    color: var(--g-dark);
    height: 100vh;
    width: 100vw;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    user-select: none;
  }}

  /* Top 4-Color Google Brand Bar */
  .google-bar {{
    height: 4px;
    width: 100%;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    flex-shrink: 0;
  }}
  .google-bar div:nth-child(1) {{ background: #4285F4; }}
  .google-bar div:nth-child(2) {{ background: #EA4335; }}
  .google-bar div:nth-child(3) {{ background: #FBBC04; }}
  .google-bar div:nth-child(4) {{ background: #34A853; }}

  /* Minimal Executive Navigation Bar */
  header.nav-header {{
    background: var(--g-surface);
    border-bottom: 1px solid var(--g-border);
    padding: 10px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-shrink: 0;
    z-index: 50;
  }}

  .logo-block {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}

  .google-g-icon {{
    width: 26px;
    height: 26px;
    flex-shrink: 0;
  }}

  .deck-title {{
    font-family: 'Google Sans', 'Inter', sans-serif;
    font-size: 15px;
    font-weight: 700;
    color: var(--g-dark);
    letter-spacing: -0.01em;
  }}
  .deck-subtitle {{
    font-size: 11.5px;
    color: var(--g-gray);
    display: flex;
    align-items: center;
    gap: 6px;
  }}

  /* Top Navigation Slide Tabs */
  .slide-tabs {{
    display: flex;
    align-items: center;
    gap: 6px;
    background: #f1f3f4;
    padding: 4px;
    border-radius: 999px;
  }}
  .slide-tab {{
    background: transparent;
    border: none;
    color: var(--g-gray);
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .slide-tab:hover {{
    color: var(--g-blue);
    background: rgba(255,255,255,0.7);
  }}
  .slide-tab.active {{
    background: var(--g-surface);
    color: var(--g-blue);
    box-shadow: 0 1px 3px rgba(60,64,67,0.18);
  }}
  .slide-tab .tab-num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    opacity: 0.75;
  }}

  /* Main Slide Stage */
  main.slide-stage {{
    flex: 1;
    position: relative;
    overflow: hidden;
    background: #fdfdfd;
  }}

  .slide {{
    display: none;
    width: 100%;
    height: 100%;
    padding: 24px 36px 72px 36px;
    overflow-y: auto;
    animation: fadeIn 0.22s ease-in-out;
  }}
  .slide.active {{
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}

  @keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(4px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}

  /* Header inside slide */
  .slide-title-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #edf0f2;
    padding-bottom: 12px;
    flex-shrink: 0;
  }}
  .slide-eyebrow {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--g-blue);
    margin-bottom: 2px;
  }}
  .slide-heading {{
    font-family: 'Google Sans', 'Inter', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--g-dark);
    letter-spacing: -0.015em;
  }}
  .slide-caption {{
    font-size: 13px;
    color: var(--g-gray);
    margin-top: 2px;
  }}

  /* Grid Layouts with zero wasted whitespace */
  .split-2 {{
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 18px;
    flex: 1;
    min-height: 0;
  }}
  .split-even {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
    flex: 1;
  }}
  .grid-3 {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
  }}
  .grid-4 {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }}

  /* Sleek White Cards */
  .panel-card {{
    background: var(--g-surface);
    border: 1px solid var(--g-border);
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 1px 2px rgba(60,64,67,0.06);
    display: flex;
    flex-direction: column;
    gap: 10px;
    overflow: hidden;
  }}
  .panel-card.interactive {{
    cursor: pointer;
    transition: all 0.18s ease;
  }}
  .panel-card.interactive:hover {{
    border-color: var(--g-blue);
    box-shadow: 0 4px 12px rgba(26,115,232,0.14);
    transform: translateY(-2px);
  }}
  .panel-card.interactive.active {{
    border: 2px solid var(--g-blue);
    background: #fbfdff;
  }}

  /* KPI Badges */
  .kpi-chip-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }}
  .kpi-chip {{
    background: var(--g-surface);
    border: 1px solid var(--g-border);
    border-left: 4px solid var(--g-blue);
    border-radius: 8px;
    padding: 10px 14px;
  }}
  .kpi-chip.red {{ border-left-color: var(--g-red); }}
  .kpi-chip.green {{ border-left-color: var(--g-green); }}
  .kpi-chip.yellow {{ border-left-color: var(--g-yellow); }}
  .kpi-number {{
    font-size: 19px;
    font-weight: 700;
    color: var(--g-dark);
    font-family: 'Google Sans', 'Inter', sans-serif;
  }}
  .kpi-label {{
    font-size: 11px;
    color: var(--g-gray);
    margin-top: 2px;
  }}

  /* Technical Blueprint Vector Canvas */
  .blueprint-box {{
    background: #0d1b2a;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    min-height: 280px;
  }}
  .blueprint-grid {{
    position: absolute;
    inset: 0;
    background-image: linear-gradient(to right, rgba(66, 133, 244, 0.08) 1px, transparent 1px),
                      linear-gradient(to bottom, rgba(66, 133, 244, 0.08) 1px, transparent 1px);
    background-size: 20px 20px;
    pointer-events: none;
  }}
  .blueprint-tag {{
    position: absolute;
    top: 10px;
    left: 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    color: #4da3ff;
    letter-spacing: 0.05em;
    background: rgba(13, 27, 42, 0.85);
    padding: 3px 8px;
    border-radius: 4px;
    border: 1px solid #1e3a5f;
  }}

  /* Interactive Hotspots on Diagrams */
  .hotspot-pill {{
    background: var(--g-surface);
    border: 1px solid var(--g-border);
    border-radius: 8px;
    padding: 10px 12px;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  .hotspot-pill:hover {{
    border-color: var(--g-blue);
    background: var(--g-blue-light);
  }}
  .hotspot-pill.active {{
    border: 2px solid var(--g-blue);
    background: var(--g-blue-light);
  }}
  .hotspot-name {{
    font-size: 12.5px;
    font-weight: 700;
    color: var(--g-dark);
  }}
  .hotspot-desc {{
    font-size: 11px;
    color: var(--g-gray);
    margin-top: 3px;
    line-height: 1.35;
  }}

  /* High-Density Compact Table */
  table.compact-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    background: var(--g-surface);
    border: 1px solid var(--g-border);
    border-radius: 8px;
    overflow: hidden;
  }}
  table.compact-table th {{
    background: #f1f3f4;
    color: var(--g-dark);
    font-weight: 600;
    text-align: left;
    padding: 8px 12px;
    border-bottom: 1px solid var(--g-border);
  }}
  table.compact-table td {{
    padding: 8px 12px;
    border-bottom: 1px solid #edf0f2;
    color: var(--g-dark);
  }}
  table.compact-table tr:hover td {{
    background: #f8fbff;
  }}

  /* Pill Badges */
  .pill {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 10.5px;
    font-weight: 600;
  }}
  .pill-green {{ background: var(--g-green-light); color: var(--g-green); }}
  .pill-red {{ background: var(--g-red-light); color: var(--g-red); }}
  .pill-blue {{ background: var(--g-blue-light); color: var(--g-blue); }}
  .pill-yellow {{ background: var(--g-yellow-light); color: #b06000; }}

  /* Bottom Controls Footer */
  footer.controls-footer {{
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 52px;
    background: var(--g-surface);
    border-top: 1px solid var(--g-border);
    padding: 0 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 50;
  }}

  .btn-nav {{
    background: var(--g-blue);
    color: #ffffff;
    border: none;
    padding: 8px 20px;
    border-radius: 999px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    transition: all 0.15s ease;
  }}
  .btn-nav:hover:not(:disabled) {{
    background: #1557b0;
  }}
  .btn-nav.ghost {{
    background: transparent;
    color: var(--g-dark);
    border: 1px solid var(--g-border);
  }}
  .btn-nav.ghost:hover:not(:disabled) {{
    background: #f1f3f4;
  }}
  .btn-nav:disabled {{
    opacity: 0.35;
    cursor: not-allowed;
  }}

  .quick-link-btn {{
    font-size: 11.5px;
    font-weight: 600;
    color: var(--g-blue);
    text-decoration: none;
    padding: 6px 12px;
    border-radius: 6px;
    background: var(--g-blue-light);
    transition: background 0.15s;
  }}
  .quick-link-btn:hover {{
    background: #d2e3fc;
  }}

  /* Code Block in Architecture */
  pre.compact-code {{
    background: #1e1e1e;
    color: #e8eaed;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11.5px;
    padding: 10px 12px;
    border-radius: 6px;
    overflow-x: auto;
    line-height: 1.45;
  }}
</style>
</head>
<body>

<div class="google-bar">
  <div></div><div></div><div></div><div></div>
</div>

<header class="nav-header">
  <div class="logo-block">
    <svg class="google-g-icon" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3h3.86c2.26-2.09 3.685-5.17 3.685-9.09z"/>
      <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.86-3c-1.08.72-2.45 1.16-4.07 1.16-3.13 0-5.78-2.11-6.73-4.96H1.29v3.09C3.26 21.3 7.37 24 12 24z"/>
      <path fill="#FBBC04" d="M5.27 14.29c-.25-.72-.38-1.49-.38-2.29s.13-1.57.38-2.29V6.62H1.29C.47 8.24 0 10.06 0 12s.47 3.76 1.29 5.38l3.98-3.09z"/>
      <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.37 0 3.26 2.7 1.29 6.62l3.98 3.09c.95-2.85 3.6-4.96 6.73-4.96z"/>
    </svg>
    <div>
      <div class="deck-title">ORMWO — Offshore Rig Mobilization & Weather Optimizer</div>
      <div class="deck-subtitle">
        <span>Google Cloud Vertex AI Agent Engine</span>
        <span>•</span>
        <span>Grounded in CAG Audit Report #15117</span>
      </div>
    </div>
  </div>

  <div class="slide-tabs">
    <button class="slide-tab active" onclick="jumpTo(0)"><span class="tab-num">01</span> Overview & Problem</button>
    <button class="slide-tab" onclick="jumpTo(1)"><span class="tab-num">02</span> Rig Physics Blueprints</button>
    <button class="slide-tab" onclick="jumpTo(2)"><span class="tab-num">03</span> Metocean & Basin Gates</button>
    <button class="slide-tab" onclick="jumpTo(3)"><span class="tab-num">04</span> Fleet Directives [1]–[6]</button>
    <button class="slide-tab" onclick="jumpTo(4)"><span class="tab-num">05</span> ADK Architecture</button>
    <button class="slide-tab" onclick="jumpTo(5)"><span class="tab-num">06</span> Live Try-It Prompts</button>
  </div>
</header>

<main class="slide-stage">

  <!-- ==================== SLIDE 1: PROBLEM & CAG AUDIT ==================== -->
  <section class="slide active" id="slide-0">
    <div class="slide-title-bar">
      <div>
        <div class="slide-eyebrow">Slide 01 · Executive Briefing</div>
        <div class="slide-heading">Eliminating ₹512 Crore in Avoidable Idle Rig Non-Productive Time</div>
        <div class="slide-caption">Based on Comptroller and Auditor General of India (CAG) Performance Audit Report #15117 ("Utilisation of Rigs in ONGC")</div>
      </div>
      <span class="pill pill-red">426.5 Avoidable Rig-Days</span>
    </div>

    <div class="kpi-chip-row">
      <div class="kpi-chip red">
        <div class="kpi-number">₹1.0 – ₹1.2 Cr</div>
        <div class="kpi-label">Daily Rig Operating & Charter Cost</div>
      </div>
      <div class="kpi-chip yellow">
        <div class="kpi-number">1.50 m (5 ft)</div>
        <div class="kpi-label">MWS Leg Punch-Through Swell Limit</div>
      </div>
      <div class="kpi-chip">
        <div class="kpi-number">34 – 42 Hours</div>
        <div class="kpi-label">Minimum Jack-Up Move & Pre-Load Duration</div>
      </div>
      <div class="kpi-chip green">
        <div class="kpi-number">₹71.50 Cr</div>
        <div class="kpi-label">Total NPT Protected Across Rigs [1]–[6]</div>
      </div>
    </div>

    <div class="split-2">
      <div class="panel-card" style="justify-content:space-between;">
        <div>
          <div style="font-size:12px; font-weight:700; color:var(--g-blue); text-transform:uppercase;">The Three Audit Traps Identified by CAG Report #15117</div>
          <div style="display:flex; flex-direction:column; gap:10px; margin-top:10px;">
            <div style="background:#fce8e6; border-left:3px solid var(--g-red); padding:10px 12px; border-radius:6px;">
              <strong style="font-size:12.5px; color:var(--g-red);">1. Mobilizing to Wells Lacking MoEFCC EC or Defence NOC</strong>
              <p style="font-size:11.5px; color:#3c4043; margin-top:2px;">Rigs towed to the nearest geographical well sat idle for weeks waiting for statutory forest/environmental clearance, Navy NOC, or pre-jetted 30" conductors.</p>
            </div>
            <div style="background:#fef7e0; border-left:3px solid #f9ab00; padding:10px 12px; border-radius:6px;">
              <strong style="font-size:12.5px; color:#b06000;">2. Missing Calm MWS Weather Windows (Hs ≤ 1.50m)</strong>
              <p style="font-size:11.5px; color:#3c4043; margin-top:2px;">Failure to synchronize well completion with forecast calm windows trapped rigs on location throughout monsoon swells at full charter hire.</p>
            </div>
            <div style="background:#e8f0fe; border-left:3px solid var(--g-blue); padding:10px 12px; border-radius:6px;">
              <strong style="font-size:12.5px; color:var(--g-blue);">3. Disjointed Marine (3× AHTS Tugs) & Aviation (Heli) Dispatch</strong>
              <p style="font-size:11.5px; color:#3c4043; margin-top:2px;">Tug coordination delays created waiting-on-tug NPT, while storm demobilizations lacked automated crew evacuation schedules.</p>
            </div>
          </div>
        </div>
        <div style="font-size:11.5px; color:var(--g-gray); border-top:1px solid #edf0f2; padding-top:8px;">
          Primary Document: <a href="https://cag.gov.in/en/audit-report/details/15117" target="_blank" style="color:var(--g-blue); text-decoration:none; font-weight:600;">CAG Report #15117 ("Utilisation of Rigs in ONGC") ↗</a>
        </div>
      </div>

      <div class="panel-card" style="background:#f8fbff; border-color:#d2e3fc;">
        <div style="font-size:12px; font-weight:700; color:var(--g-green); text-transform:uppercase;">The ORMWO High-Code Solution</div>
        <p style="font-size:12px; color:var(--g-dark); line-height:1.5;">
          A single production-grade AI Agent deployed on Vertex AI Agent Engine that couples:
        </p>
        <ul style="padding-left:16px; font-size:11.5px; color:var(--g-dark); line-height:1.6; display:flex; flex-direction:column; gap:6px;">
          <li><strong>Live Metocean Telemetry:</strong> Real-time wave (`Hs`), swell period (`Tp`), and wind from Open-Meteo across 7 EEZ basins.</li>
          <li><strong>DeepMind 48h Weather Forecasts:</strong> GenCast & GraphCast ensemble wave polygons to catch calm windows before swell builds.</li>
          <li><strong>120-Well Statutory Registry:</strong> Strictly verifies MoEFCC EC, Defence NOC, and conductor readiness before selecting any destination well.</li>
          <li><strong>10,000-Run Monte Carlo Optimizer:</strong> Computes P10/P50/P90 wet-tow durations with 3× AHTS tug bollard pull.</li>
        </ul>
        <div style="background:var(--g-surface); border:1px solid #d2e3fc; padding:10px; border-radius:8px; margin-top:auto;">
          <div style="font-size:11px; font-weight:700; color:var(--g-blue);">CORE PRINCIPLE: ZERO MATH IN PROMPT TOKENS</div>
          <div style="font-size:11px; color:var(--g-gray); margin-top:2px;">All physical constraints, coordinates, and cost simulations are computed deterministically in Python tools.</div>
        </div>
      </div>
    </div>
  </section>

  <!-- ==================== SLIDE 2: RIG BLUEPRINTS & OPERATIONAL LIMITS ==================== -->
  <section class="slide" id="slide-1">
    <div class="slide-title-bar">
      <div>
        <div class="slide-eyebrow">Slide 02 · Offshore Rig Blueprints & Physical Constraints</div>
        <div class="slide-heading">Why Active Rigs Never Move in a 48h Storm vs. When They Move</div>
        <div class="slide-caption">Click the technical blueprints or hotspot components below to inspect real-world physical limits:</div>
      </div>
      <div style="display:flex; gap:8px;">
        <button class="pill pill-red" onclick="switchBlueprint('jackup')">Jack-Up Rig Blueprint</button>
        <button class="pill pill-blue" onclick="switchBlueprint('drillship')">DP3 Drillship Blueprint</button>
      </div>
    </div>

    <div class="split-2">
      <!-- Vector Technical Blueprint Canvas -->
      <div class="blueprint-box">
        <div class="blueprint-grid"></div>
        <div class="blueprint-tag" id="bpTag">JACK-UP DRILLING UNIT · 300 FT LATTICE LEGS</div>

        <!-- Jack-Up SVG Blueprint -->
        <svg id="svgJackup" viewBox="0 0 540 320" width="100%" height="100%" style="padding:10px;">
          <!-- Ocean Line & Wave -->
          <path d="M0 200 Q 60 190, 120 200 T 240 200 T 360 200 T 480 200 T 540 200 L 540 320 L 0 320 Z" fill="rgba(66, 133, 244, 0.15)"/>
          <line x1="0" y1="200" x2="540" y2="200" stroke="#4da3ff" stroke-width="1.5" stroke-dasharray="4,3"/>
          <text x="15" y="192" fill="#4da3ff" font-size="10" font-family="'JetBrains Mono'">WATERLINE (CALM Hs ≤ 1.50m / STORM Hs &gt; 2.50m)</text>

          <!-- Seabed -->
          <rect x="0" y="275" width="540" height="45" fill="#1b2a3a"/>
          <line x1="0" y1="275" x2="540" y2="275" stroke="#78909c" stroke-width="2"/>
          <text x="15" y="300" fill="#90a4ae" font-size="10" font-family="'JetBrains Mono'">SEABED CLAY / SILT LAYER (8–15m SPUDCAN PENETRATION)</text>

          <!-- 3 Lattice Legs -->
          <!-- Left Leg -->
          <line x1="120" y1="35" x2="120" y2="285" stroke="#90caf9" stroke-width="4"/>
          <line x1="140" y1="35" x2="140" y2="285" stroke="#90caf9" stroke-width="4"/>
          <!-- Leg Cross Bracing -->
          <path d="M120 40 L140 60 L120 80 L140 100 L120 120 L140 140 L120 160 L140 180 L120 200 L140 220 L120 240 L140 260 L120 280" stroke="#42a5f5" stroke-width="1.5" fill="none"/>
          <!-- Spudcan Left -->
          <polygon points="110,285 150,285 130,305" fill="#e53935" stroke="#ff8a80" stroke-width="2"/>

          <!-- Right Leg -->
          <line x1="380" y1="35" x2="380" y2="285" stroke="#90caf9" stroke-width="4"/>
          <line x1="400" y1="35" x2="400" y2="285" stroke="#90caf9" stroke-width="4"/>
          <path d="M380 40 L400 60 L380 80 L400 100 L380 120 L400 140 L380 160 L400 180 L380 200 L400 220 L380 240 L400 260 L380 280" stroke="#42a5f5" stroke-width="1.5" fill="none"/>
          <!-- Spudcan Right -->
          <polygon points="370,285 410,285 390,305" fill="#e53935" stroke="#ff8a80" stroke-width="2"/>

          <!-- Jack-Up Hull (Elevated) -->
          <rect x="90" y="120" width="340" height="35" rx="4" fill="#263238" stroke="#64b5f6" stroke-width="2"/>
          <text x="210" y="142" fill="#ffffff" font-size="12" font-weight="700" font-family="'Inter'">JACK-UP HULL (ELEVATED)</text>

          <!-- Cantilever & Derrick -->
          <rect x="290" y="105" width="100" height="15" fill="#37474f"/>
          <polygon points="320,105 360,105 340,30" fill="none" stroke="#ffb74d" stroke-width="2"/>
          <text x="325" y="24" fill="#ffb74d" font-size="10" font-weight="700">DERRICK</text>

          <!-- Warning Box on Punch Through -->
          <rect x="180" y="165" width="160" height="28" rx="4" fill="rgba(234, 67, 53, 0.85)" stroke="#ea4335"/>
          <text x="190" y="182" fill="#ffffff" font-size="9.5" font-weight="700" font-family="'JetBrains Mono'">⚠️ 1.50m (5ft) PUNCH-THROUGH LIMIT</text>
        </svg>

        <!-- DP3 Drillship SVG Blueprint (Hidden by default) -->
        <svg id="svgDrillship" viewBox="0 0 540 320" width="100%" height="100%" style="padding:10px; display:none;">
          <!-- Ocean Line -->
          <rect x="0" y="90" width="540" height="230" fill="rgba(66, 133, 244, 0.12)"/>
          <line x1="0" y1="90" x2="540" y2="90" stroke="#4da3ff" stroke-width="1.5" stroke-dasharray="4,3"/>

          <!-- Drillship Hull -->
          <polygon points="60,90 440,90 410,130 90,130" fill="#263238" stroke="#90caf9" stroke-width="2"/>
          <text x="190" y="115" fill="#ffffff" font-size="12" font-weight="700">DP3 DRILLSHIP HULL (1,500m WATER)</text>

          <!-- Twin Derrick -->
          <polygon points="230,90 270,90 250,25" fill="none" stroke="#ffb74d" stroke-width="2"/>
          <!-- Helideck -->
          <rect x="390" y="75" width="60" height="12" rx="2" fill="#1b5e20"/>
          <text x="400" y="84" fill="#ffffff" font-size="8.5" font-weight="700">🚁 HELIDECK</text>

          <!-- Azimuth Thrusters -->
          <rect x="110" y="130" width="14" height="16" fill="#42a5f5"/>
          <rect x="380" y="130" width="14" height="16" fill="#42a5f5"/>
          <text x="135" y="142" fill="#90caf9" font-size="9" font-family="'JetBrains Mono'">DP3 AZIMUTH THRUSTERS (±0.5m STATION)</text>

          <!-- Marine Riser -->
          <line x1="250" y1="130" x2="250" y2="210" stroke="#ffb74d" stroke-width="3"/>
          <text x="260" y="170" fill="#ffb74d" font-size="9.5" font-family="'JetBrains Mono'">1,500m MARINE RISER</text>

          <!-- LMRP Disconnect Point -->
          <rect x="235" y="210" width="30" height="18" fill="#e53935" stroke="#ffffff" stroke-width="1.5"/>
          <text x="275" y="222" fill="#ff8a80" font-size="10" font-weight="700" font-family="'JetBrains Mono'">⚡ LMRP UNLATCH (45 SECONDS)</text>

          <!-- Subsea BOP Stack -->
          <rect x="230" y="235" width="40" height="45" rx="3" fill="#37474f" stroke="#90caf9" stroke-width="2"/>
          <text x="280" y="258" fill="#4da3ff" font-size="9.5" font-weight="700">SUBSEA BOP (BLIND SHEAR RAMS)</text>

          <!-- Seabed Wellhead -->
          <rect x="0" y="285" width="540" height="35" fill="#1b2a3a"/>
          <text x="15" y="305" fill="#78909c" font-size="10" font-family="'JetBrains Mono'">SEABED WELLHEAD (CLOSED & SECURED)</text>
        </svg>
      </div>

      <!-- Right Column: Interactive Hotspot Details -->
      <div style="display:flex; flex-direction:column; gap:10px;">
        <div class="hotspot-pill active" onclick="showHotspot('punch')">
          <div class="hotspot-name">1. Spudcan Seabed Penetration & Leg Punch-Through</div>
          <div class="hotspot-desc">Jack-up legs penetrate 8–15 meters into clay. Lowering hull in waves > 1.50m (5ft) causes wave heave to slam leg tips, risking leg buckle or capsize.</div>
        </div>
        <div class="hotspot-pill" onclick="showHotspot('duration')">
          <div class="hotspot-name">2. The 34–42 Hour Rig Move Reality</div>
          <div class="hotspot-desc">Jetting spudcans from seabed takes 14h, towing at 4.0 kt takes 3–5h, pre-loading at target takes 12h. A cyclone builds in 12–18h — jack-downs into storms are strictly prohibited by MWS.</div>
        </div>
        <div class="hotspot-pill" onclick="showHotspot('deepwater')">
          <div class="hotspot-name">3. Deepwater LMRP Disconnect & 🚁 Pawan Hans Evacuation</div>
          <div class="hotspot-desc">When swells exceed 2.50m (Bay of Bengal today), deepwater drillships hang off drill pipe, disconnect LMRP in 45s, and evacuate non-essential crew via helicopter.</div>
        </div>
        <div class="hotspot-pill" onclick="showHotspot('completed')">
          <div class="hotspot-name">4. When Rigs DO Move (Calm MWS Window)</div>
          <div class="hotspot-desc">When a well is completed (or plugged dry) during calm seas (Hs ≤ 1.50m, Mumbai High today), the rig executes a planned 3× AHTS wet tow to the closest EC-cleared well.</div>
        </div>
      </div>
    </div>
  </section>

  <!-- ==================== SLIDE 3: METOCEAN & BASIN GATES ==================== -->
  <section class="slide" id="slide-2">
    <div class="slide-title-bar">
      <div>
        <div class="slide-eyebrow">Slide 03 · Real-Time Oceanography</div>
        <div class="slide-heading">Live Open-Meteo Basin Telemetry & MWS Operational Gates</div>
        <div class="slide-caption">Why Mumbai High is Green for Completed-Well Moves while the Bay of Bengal is Under Swell Lock:</div>
      </div>
      <span class="pill pill-blue">Live Telemetry Today</span>
    </div>

    <div class="split-even">
      <!-- Western Offshore Card -->
      <div class="panel-card" style="border-top:4px solid var(--g-green);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span class="pill pill-green">🟢 WESTERN OFFSHORE · CALM MWS WINDOW</span>
          <strong style="font-size:12px; color:var(--g-green);">Hs ≤ 1.50m MWS Limit</strong>
        </div>
        <h3 style="font-size:17px; margin-top:4px;">Mumbai High, Bassein & Tapti Basins</h3>
        <p style="font-size:12px; color:var(--g-gray);">Live Open-Meteo Marine API confirms wave height is below the 5-ft spudcan extraction limit. Rig moves permitted for completed wells.</p>

        <div style="background:#f4fbf6; border:1px solid #ceead6; border-radius:8px; padding:12px; display:grid; grid-template-columns:repeat(3, 1fr); gap:8px;">
          <div>
            <div style="font-size:10.5px; color:var(--g-gray);">Mumbai High North</div>
            <div style="font-size:16px; font-weight:700; color:var(--g-green);">1.22 m</div>
            <div style="font-size:10px; color:var(--g-gray);">Wind: 16.6 kts</div>
          </div>
          <div>
            <div style="font-size:10.5px; color:var(--g-gray);">Heera-Bassein</div>
            <div style="font-size:16px; font-weight:700; color:var(--g-green);">1.18 m</div>
            <div style="font-size:10px; color:var(--g-gray);">Wind: 17.0 kts</div>
          </div>
          <div>
            <div style="font-size:10.5px; color:var(--g-gray);">Tapti-Daman</div>
            <div style="font-size:16px; font-weight:700; color:var(--g-green);">0.78 m</div>
            <div style="font-size:10px; color:var(--g-gray);">Wind: 11.3 kts</div>
          </div>
        </div>

        <div style="font-size:12px; line-height:1.5; color:var(--g-dark);">
          <strong>Directives [1]–[4] Authorized:</strong> Completed/dry rigs (<em>Sagar Samrat, Sagar Ratna, Sagar Bhushan, Aban Ice</em>) execute 3× AHTS wet tows (6.8–9.6 NM) to closest EC-cleared candidate wells.
        </div>
      </div>

      <!-- Eastern Offshore Card -->
      <div class="panel-card" style="border-top:4px solid var(--g-red);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span class="pill pill-red">🔴 EASTERN OFFSHORE · CYCLONIC SWELL LOCK</span>
          <strong style="font-size:12px; color:var(--g-red);">Hs &gt; 2.50m Limit</strong>
        </div>
        <h3 style="font-size:17px; margin-top:4px;">KG-DWN-98/2 & Mahanadi Basins (Bay of Bengal)</h3>
        <p style="font-size:12px; color:var(--g-gray);">Severe monsoon swell and gusts above 40 kts. Rig moves prohibited by Marine Warranty Surveyors (MWS). Emergency storm protocols active.</p>

        <div style="background:#fce8e6; border:1px solid #fad2cf; border-radius:8px; padding:12px; display:grid; grid-template-columns:repeat(2, 1fr); gap:8px;">
          <div>
            <div style="font-size:10.5px; color:var(--g-gray);">KG-DWN-98/2</div>
            <div style="font-size:16px; font-weight:700; color:var(--g-red);">2.80 m</div>
            <div style="font-size:10px; color:var(--g-gray);">Wind: 26.4 kt · Gust: 36.5 kt</div>
          </div>
          <div>
            <div style="font-size:10.5px; color:var(--g-gray);">Mahanadi Basin</div>
            <div style="font-size:16px; font-weight:700; color:var(--g-red);">4.98 m</div>
            <div style="font-size:10px; color:var(--g-gray);">Wind: 29.6 kt · Gust: 41.2 kt</div>
          </div>
        </div>

        <div style="font-size:12px; line-height:1.5; color:var(--g-dark);">
          <strong>Directives [5]–[6] Active:</strong> Deepwater drillships (<em>Dhirubhai KG1, Platinum Explorer</em>) execute BOP Hang-Off, 45s LMRP Unlatch into 3 NM DP3 Storm Box, and 🚁 Pawan Hans crew evacuation to Rajahmundry & Paradip.
        </div>
      </div>
    </div>
  </section>

  <!-- ==================== SLIDE 4: MASTER FLEET DIRECTIVES [1]–[6] ==================== -->
  <section class="slide" id="slide-3">
    <div class="slide-title-bar">
      <div>
        <div class="slide-eyebrow">Slide 04 · Operational Directives</div>
        <div class="slide-heading">Fleet Relocation & Storm Evacuation Directives [1] through [6]</div>
        <div class="slide-caption">Copy-ready format for Google Sheets / Excel, fully compliant with CAG Report #15117 statutory clearances:</div>
      </div>
      <div style="display:flex; gap:8px;">
        <a href="{map_url}" target="_blank" class="quick-link-btn">🌐 Open Interactive Map ↗</a>
        <a href="{sop_url}" target="_blank" class="quick-link-btn">📋 Open Printable SOP ↗</a>
      </div>
    </div>

    <table class="compact-table">
      <thead>
        <tr>
          <th>Badge & Rig</th>
          <th>Basin & Live Sea State</th>
          <th>Well Status (`CAG #15117`)</th>
          <th>Operational Directive</th>
          <th>Target Location</th>
          <th>Rejected Closer Well (Audit Reason)</th>
          <th>Saved NPT</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>[1] Sagar Samrat</strong> (Jack-Up)</td>
          <td>Mumbai High · <span class="pill pill-green">Hs = 1.22m</span></td>
          <td>Completed (`MH-N-001`)</td>
          <td>🟢 <strong>Wet Tow (8.4 NM @ 4kt)</strong> via 3× AHTS</td>
          <td><code>WELL-IND-004 (MH-N-B193)</code></td>
          <td><code>MH-N-002</code> (4.1 NM — No MoEFCC EC)</td>
          <td><strong>38.1h · ₹11.50 Cr</strong></td>
        </tr>
        <tr>
          <td><strong>[2] Sagar Ratna</strong> (Jack-Up)</td>
          <td>Mumbai High · <span class="pill pill-green">Hs = 1.21m</span></td>
          <td>Dry Hole P&A (`MH-S-002`)</td>
          <td>🟢 <strong>Wet Tow (9.6 NM @ 4kt)</strong> via 3× AHTS</td>
          <td><code>WELL-IND-005 (MH-S-D18)</code></td>
          <td><code>MH-S-003</code> (5.2 NM — Subsea Pipeline Buffer)</td>
          <td><strong>38.4h · ₹10.80 Cr</strong></td>
        </tr>
        <tr>
          <td><strong>[3] Sagar Bhushan</strong> (Drillship)</td>
          <td>Heera-Bassein · <span class="pill pill-green">Hs = 1.18m</span></td>
          <td>Completed (`HPB-003`)</td>
          <td>🟢 <strong>Wet Tow (7.2 NM @ 4kt)</strong> via 3× AHTS</td>
          <td><code>WELL-IND-006 (Neelam-14)</code></td>
          <td><code>HPB-004</code> (3.9 NM — Conductor Not Pre-Jetted)</td>
          <td><strong>21.8h · ₹9.60 Cr</strong></td>
        </tr>
        <tr>
          <td><strong>[4] Aban Ice</strong> (Jack-Up)</td>
          <td>Tapti-Daman · <span class="pill pill-green">Hs = 0.78m</span></td>
          <td>Completed (`TD-C26-01`)</td>
          <td>🟢 <strong>Wet Tow (6.8 NM @ 4kt)</strong> via 3× AHTS</td>
          <td><code>WELL-IND-008 (Daman-04)</code></td>
          <td><code>TD-C26-02</code> (4.4 NM — Pending Navy Defence NOC)</td>
          <td><strong>34.7h · ₹8.90 Cr</strong></td>
        </tr>
        <tr>
          <td><strong>[5] Dhirubhai KG1</strong> (DP3)</td>
          <td>KG-DWN (BoB) · <span class="pill pill-red">Hs = 2.80m</span></td>
          <td>Active Drilling (`KG-U1`)</td>
          <td>🔴 <strong>NO RIG MOVE</strong> · BOP Hang-Off + 🚁 Evac</td>
          <td><code>🚁 Rajahmundry Base (54 POB)</code></td>
          <td>Rig Move Prohibited (`Hs = 2.80m > 1.50m`)</td>
          <td><strong>14.5h · ₹14.20 Cr</strong></td>
        </tr>
        <tr>
          <td><strong>[6] Platinum Explorer</strong> (DP3)</td>
          <td>Mahanadi (BoB) · <span class="pill pill-red">Hs = 4.98m</span></td>
          <td>Active Drilling (`MND-01`)</td>
          <td>🔴 <strong>NO RIG MOVE</strong> · LMRP Unlatch + 🚁 Evac</td>
          <td><code>🚁 Paradip Base (60 POB)</code></td>
          <td>Rig Move Prohibited (`Hs = 4.98m > 1.50m`)</td>
          <td><strong>12.5h · ₹16.50 Cr</strong></td>
        </tr>
      </tbody>
    </table>

    <div style="background:#f1f3f4; padding:10px 14px; border-radius:8px; display:flex; justify-content:space-between; align-items:center;">
      <span style="font-size:12px; color:var(--g-dark);"><strong>Notice:</strong> This table is formatted with atomic columns so users can highlight and paste directly into Google Sheets / Excel without broken line-wraps.</span>
      <span style="font-size:12px; font-weight:700; color:var(--g-green);">Total Fleet Protection: ₹71.50 Crore</span>
    </div>
  </section>

  <!-- ==================== SLIDE 5: SYSTEM ARCHITECTURE ==================== -->
  <section class="slide" id="slide-4">
    <div class="slide-title-bar">
      <div>
        <div class="slide-eyebrow">Slide 05 · Software Architecture</div>
        <div class="slide-heading">High-Code ADK Agent on Vertex AI Agent Engine</div>
        <div class="slide-caption">Click any component block to inspect the production Python code and guardrails:</div>
      </div>
      <span class="pill pill-blue">Single-Root Agent</span>
    </div>

    <div class="split-2">
      <div style="display:flex; flex-direction:column; gap:8px;">
        <div class="panel-card interactive active" onclick="showArch('ui')">
          <div style="display:flex; justify-content:space-between;">
            <strong style="font-size:13px; color:var(--g-blue);">1. Gemini Enterprise & A2UI v0.9</strong>
            <span class="pill pill-blue">Client Surface</span>
          </div>
          <p style="font-size:11.5px; color:var(--g-gray);">Renders visual VegaChart infographic inside card; all copyable tables & links live outside in main chat stream.</p>
        </div>
        <div class="panel-card interactive" onclick="showArch('guard')">
          <div style="display:flex; justify-content:space-between;">
            <strong style="font-size:13px; color:var(--g-yellow);">2. History Sanitizer Guardrail</strong>
            <span class="pill pill-yellow">Token Guard</span>
          </div>
          <p style="font-size:11.5px; color:var(--g-gray);">Strips prior-turn A2UI envelopes and PNG bytes before invoking Gemini to prevent token runaway loops.</p>
        </div>
        <div class="panel-card interactive" onclick="showArch('tools')">
          <div style="display:flex; justify-content:space-between;">
            <strong style="font-size:13px; color:var(--g-green);">3. Open-Meteo & Monte Carlo Tools</strong>
            <span class="pill pill-green">Discrete Math</span>
          </div>
          <p style="font-size:11.5px; color:var(--g-gray);">Queries live ECMWF marine telemetry, 10,000-run wet-tow transit simulations, and 120-well clearance registry.</p>
        </div>
      </div>

      <div class="panel-card" style="background:#1e1e1e; border-color:#333;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-size:11px; font-weight:700; color:#4da3ff; font-family:'JetBrains Mono';" id="archCodeTitle">A2UI v0.9 CARD RENDERER (app/render/rig_fleet_card.py)</span>
          <span class="pill pill-blue" style="background:#333; color:#fff;">Python 3.13</span>
        </div>
        <pre class="compact-code" id="archCodeBody">def build_rig_fleet_components(summary: FleetSummary):
    # Pure visual interactive infographic inside the card
    chart_comp = {{
        "id": "rfc-chart-vega",
        "component": "VegaChart",
        "spec": vega_spec,
        "height": 860
    }}
    # Text tables & headed links emitted OUTSIDE in main Markdown
    return [root_card, column, chart_comp]</pre>
      </div>
    </div>
  </section>

  <!-- ==================== SLIDE 6: TEST PROMPTS & IMPACT ==================== -->
  <section class="slide" id="slide-5">
    <div class="slide-title-bar">
      <div>
        <div class="slide-eyebrow">Slide 06 · Production Demo Suite</div>
        <div class="slide-heading">Try ORMWO in Gemini Enterprise / Vertex AI Agent Engine</div>
        <div class="slide-caption">Click any prompt card to copy it directly into your clipboard for live meeting demos:</div>
      </div>
      <span class="pill pill-green">Live on Vertex AI</span>
    </div>

    <div class="grid-3">
      <div class="panel-card interactive" onclick="copyPrompt('p1', this)">
        <span class="pill pill-blue">Prompt 01 · Full Fleet Sweep</span>
        <h4 style="font-size:14px; margin-top:4px;">Live Metocean + CAG #15117 Sweep</h4>
        <p style="font-size:11.5px; color:var(--g-gray); line-height:1.45;" id="p1">Run a live metocean and CAG Audit #15117 fleet assessment across all 20 offshore rigs in India's EEZ. Compare today's real-time wave and wind conditions in Mumbai High versus the Bay of Bengal (KG-DWN and Mahanadi), and show the exact operational directive, well-to-well move or in-place storm protocol, and avoided NPT for rigs [1] through [6].</p>
        <div style="font-size:11px; font-weight:700; color:var(--g-blue); margin-top:auto;">📋 Click to Copy Prompt</div>
      </div>

      <div class="panel-card interactive" onclick="copyPrompt('p2', this)">
        <span class="pill pill-green">Prompt 02 · Calm MWS Rig Move</span>
        <h4 style="font-size:14px; margin-top:4px;">Mumbai High Wet Tow ([1]–[4])</h4>
        <p style="font-size:11.5px; color:var(--g-gray); line-height:1.45;" id="p2">Sagar Samrat [1] and Sagar Ratna [2] have completed their current wells in Mumbai High. Check live Open-Meteo wave height against the 1.50m MWS spudcan extraction limit, explain why closer non-EC wells were rejected per CAG Report #15117, and provide the hour-by-hour 3x AHTS tug wet-tow plan.</p>
        <div style="font-size:11px; font-weight:700; color:var(--g-green); margin-top:auto;">📋 Click to Copy Prompt</div>
      </div>

      <div class="panel-card interactive" onclick="copyPrompt('p3', this)">
        <span class="pill pill-red">Prompt 03 · Cyclone Swell Lock</span>
        <h4 style="font-size:14px; margin-top:4px;">Bay of Bengal Crew Evacuation ([5]–[6])</h4>
        <p style="font-size:11.5px; color:var(--g-gray); line-height:1.45;" id="p3">Why can't Dhirubhai Deepwater KG1 [5] and Platinum Explorer [6] move to a new well during today's high swells in the Bay of Bengal? Provide the DNV-ST-N001 MWS limits, the in-place BOP Hang-Off and LMRP Disconnect timeline, and the Pawan Hans helicopter evacuation plan.</p>
        <div style="font-size:11px; font-weight:700; color:var(--g-red); margin-top:auto;">📋 Click to Copy Prompt</div>
      </div>
    </div>

    <div class="panel-card" style="background:#f4fbf6; border-color:#ceead6; display:flex; flex-direction:row; align-items:center; justify-content:space-between;">
      <div>
        <strong style="font-size:13px; color:var(--g-dark);">Live Production Reasoning Engine Resource:</strong>
        <div style="font-size:11.5px; font-family:'JetBrains Mono'; color:var(--g-gray); margin-top:2px;">projects/632239123109/locations/us-central1/reasoningEngines/4687908012755517440</div>
      </div>
      <div style="display:flex; gap:10px;">
        <a href="https://github.com/zuhaibp656/oil-and-gas-rig-navigator-agent" target="_blank" class="quick-link-btn">💻 GitHub Repository ↗</a>
        <a href="{map_url}" target="_blank" class="quick-link-btn">🗺️ Live Command Map ↗</a>
      </div>
    </div>
  </section>

</main>

<footer class="controls-footer">
  <button class="btn-nav ghost" id="btnPrev" onclick="navigate(-1)" disabled>← Previous</button>
  <div style="font-size:12.5px; font-weight:600; color:var(--g-gray);" id="slideCounter">
    Slide 1 of 6 · Use <kbd style="background:#f1f3f4;padding:2px 6px;border-radius:4px;border:1px solid #dadce0;">←</kbd> <kbd style="background:#f1f3f4;padding:2px 6px;border-radius:4px;border:1px solid #dadce0;">→</kbd> Arrow Keys
  </div>
  <button class="btn-nav" id="btnNext" onclick="navigate(1)">Next Slide →</button>
</footer>

<script>
  let activeSlide = 0;
  const slideCount = 6;

  function jumpTo(index) {{
    activeSlide = Math.max(0, Math.min(slideCount - 1, index));

    // Bulletproof direct DOM class toggling
    for (let i = 0; i < slideCount; i++) {{
      const el = document.getElementById(`slide-${{i}}`);
      if (el) el.classList.toggle('active', i === activeSlide);
    }}

    // Update Top Tabs
    const tabs = document.querySelectorAll('.slide-tab');
    tabs.forEach((t, i) => t.classList.toggle('active', i === activeSlide));

    // Update Bottom Footer Controls
    document.getElementById('btnPrev').disabled = (activeSlide === 0);
    const nextBtn = document.getElementById('btnNext');
    if (activeSlide === slideCount - 1) {{
      nextBtn.innerText = '↺ First Slide';
      nextBtn.onclick = () => jumpTo(0);
    }} else {{
      nextBtn.innerText = 'Next Slide →';
      nextBtn.onclick = () => navigate(1);
    }}

    document.getElementById('slideCounter').innerHTML =
      `Slide ${{activeSlide + 1}} of ${{slideCount}} · Use <kbd style="background:#f1f3f4;padding:2px 6px;border-radius:4px;border:1px solid #dadce0;">←</kbd> <kbd style="background:#f1f3f4;padding:2px 6px;border-radius:4px;border:1px solid #dadce0;">→</kbd> Arrow Keys`;
  }}

  function navigate(delta) {{
    jumpTo(activeSlide + delta);
  }}

  // Keyboard navigation
  document.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {{
      e.preventDefault();
      navigate(1);
    }} else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{
      e.preventDefault();
      navigate(-1);
    }}
  }});

  // Slide 2: Switch Vector Blueprints
  function switchBlueprint(type) {{
    const j = document.getElementById('svgJackup');
    const d = document.getElementById('svgDrillship');
    const tag = document.getElementById('bpTag');
    if (type === 'jackup') {{
      j.style.display = 'block';
      d.style.display = 'none';
      tag.innerText = 'JACK-UP DRILLING UNIT · 300 FT LATTICE LEGS · 1.50m PUNCH-THROUGH LIMIT';
    }} else {{
      j.style.display = 'none';
      d.style.display = 'block';
      tag.innerText = 'DP3 ULTRA-DEEPWATER DRILLSHIP · 1,500m RISER · 45s LMRP UNLATCH';
    }}
  }}

  // Slide 2: Hotspot selection
  function showHotspot(topic) {{
    const pills = document.querySelectorAll('.hotspot-pill');
    pills.forEach(p => p.classList.remove('active'));
    event.currentTarget.classList.add('active');
    if (topic === 'punch' || topic === 'duration' || topic === 'completed') {{
      switchBlueprint('jackup');
    }} else {{
      switchBlueprint('drillship');
    }}
  }}

  // Slide 5: Architecture code inspector
  const archSnippets = {{
    ui: {{
      title: 'A2UI v0.9 CARD RENDERER (app/render/rig_fleet_card.py)',
      code: `def build_rig_fleet_components(summary: FleetSummary):
    # Pure visual interactive infographic inside the card
    chart_comp = {{
        "id": "rfc-chart-vega",
        "component": "VegaChart",
        "spec": vega_spec,
        "height": 860
    }}
    # Text tables & headed links emitted OUTSIDE in main Markdown
    return [root_card, column, chart_comp]`
    }},
    guard: {{
      title: 'HISTORY SANITIZER (app/integration/agent.py)',
      code: `def sanitize_llm_request_history(callback_context, llm_request):
    # Strips prior <a2a_datapart_json> and inline_data PNG bytes
    for content in llm_request.contents:
        content.parts = [p for p in content.parts if not p.inline_data]
    llm_request.config.temperature = 0.0
    llm_request.config.thinking_config = ThinkingConfig(thinking_budget=0)`
    }},
    tools: {{
      title: 'OPEN-METEO MARINE API TOOL (app/rigs/live_metocean_feed.py)',
      code: `@tool
def get_marine_weather_forecast(lat: float, lon: float):
    # Real-time ECMWF WAM wave & wind telemetry
    url = f"https://marine-api.open-meteo.com/v1/marine?latitude={{lat}}&longitude={{lon}}&current=wave_height"
    res = requests.get(url, timeout=3.0).json()
    return {{"live_hs_m": res["current"]["wave_height"], "mws_status": ...}}`
    }}
  }};

  function showArch(key) {{
    document.querySelectorAll('.panel-card.interactive').forEach(c => c.classList.remove('active'));
    event.currentTarget.classList.add('active');
    const s = archSnippets[key];
    if (s) {{
      document.getElementById('archCodeTitle').innerText = s.title;
      document.getElementById('archCodeBody').innerText = s.code;
    }}
  }}

  // Slide 6: Prompt Copying
  function copyPrompt(id, card) {{
    const txt = document.getElementById(id).innerText;
    navigator.clipboard.writeText(txt);
    const badge = card.querySelector('div:last-child');
    const prev = badge.innerText;
    badge.innerText = '✅ Copied to Clipboard!';
    badge.style.color = '#1e8e3e';
    setTimeout(() => {{
      badge.innerText = prev;
      badge.style.color = '';
    }}, 2000);
  }}
</script>
</body>
</html>
"""
