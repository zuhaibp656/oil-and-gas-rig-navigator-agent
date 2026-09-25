"""Executive Presentation HTML Generator matching Google Cloud Aurora & Gemini Enterprise Brand System.

Faithfully implements the visual identity, tokens, typography, kicker bars,
Gemini Enterprise Cockpit prompt bar, 4-column metric cards, rig CAD blueprints,
and interactive slide navigation from the reference design.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path


def _get_base64_image(path: Path) -> str:
    """Return a base64 data URI of the given image file if it exists."""
    if path.exists():
        ext = path.suffix.lower().replace(".", "")
        mime = "image/png" if ext == "png" else "image/jpeg"
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    return ""


def build_executive_presentation_html(project_id: str | None = None) -> str:
    proj = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT") or "zuhaibp-ai"
    bucket = f"{proj}-agent-staging"
    map_url = f"https://storage.mtls.cloud.google.com/{bucket}/interactive_maps/india_eez_latest.html"
    sop_url = f"https://storage.mtls.cloud.google.com/{bucket}/interactive_maps/india_eez_rig_move_sop_latest.html"
    png_url = f"https://storage.mtls.cloud.google.com/{bucket}/interactive_maps/india_eez_4panel_latest.png"

    # Base64 assets
    static_media = Path(__file__).resolve().parent.parent / "static" / "assets" / "media"
    logo_data_uri = _get_base64_image(static_media / "image25.png")
    rig_photo_data_uri = _get_base64_image(static_media / "image77.jpg")

    return (
        HTML_TEMPLATE
        .replace("__MAP_URL__", map_url)
        .replace("__SOP_URL__", sop_url)
        .replace("__PNG_URL__", png_url)
        .replace("__GCLOUD_LOGO_URI__", logo_data_uri)
        .replace("__RIG_PHOTO_URI__", rig_photo_data_uri)
    )


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="theme-dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ORMWO — Offshore Rig Mobilization & Weather Optimizer | Google Cloud Executive Briefing</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700;800&family=Google+Sans+Text:wght@400;500;700&family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  /* ═══════════════════════════════════════════════════════════════════════════
     Google Cloud "Aurora" Design Tokens & Brand System
     ═══════════════════════════════════════════════════════════════════════════ */
  :root {
    --g-blue: #3186FF;
    --g-purple: #4B31E3;
    --g-green: #00AF57;
    --g-yellow: #FEC700;
    --g-red: #FC413D;
    --g-grey-10: #F8F9FC;
    --g-grey-1200: #121317;

    --font-display: 'Google Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-body: 'Google Sans Text', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'Roboto Mono', 'Google Sans Mono', monospace;

    --gemini-spark: linear-gradient(135deg, #3186FF 0%, #4B31E3 100%);
    --transform-grad: linear-gradient(135deg, #00AF57 0%, #3186FF 100%);
    --grad-security: linear-gradient(90deg, #00D2B4 0%, #00A3FF 100%);
    --grad-aurora: linear-gradient(90deg, #217BFE 0%, #078EFB 33%, #AC87EB 67%, #EE4D5D 100%);

    --canvas: #06090E;
    --surface: #12151C;
    --surface-card: rgba(18, 21, 28, 0.85);
    --surface-sunk: #0B0D12;
    --border-hairline: rgba(255, 255, 255, 0.08);
    --border-subtle: rgba(255, 255, 255, 0.12);
    --border-strong: rgba(255, 255, 255, 0.22);
    --text: #F8F9FC;
    --text-muted: #94A3B8;
    --text-dim: #64748B;
    --accent: var(--g-blue);

    --blue-ink: #8AB4F8;
    --green-ink: #5BB974;
    --red-ink: #F28B82;
    --amber-ink: #FDD663;
    --purple-ink: #C6B2FF;
    --cyan-ink: #6FD3E0;
    --security-turquoise: #00D2B4;
    --security-azure: #00A3FF;
  }

  html.theme-light, body.theme-light {
    --canvas: #F8F9FC;
    --surface: #FFFFFF;
    --surface-card: rgba(255, 255, 255, 0.92);
    --surface-sunk: #F1F3F9;
    --border-hairline: #E2E8F0;
    --border-subtle: #CBD5E1;
    --border-strong: #94A3B8;
    --text: #121317;
    --text-muted: #475569;
    --text-dim: #64748B;
    --accent: #286DD1;

    --blue-ink: #286DD1;
    --green-ink: #007F3F;
    --red-ink: #C62A27;
    --amber-ink: #8A6200;
    --purple-ink: #4B31E3;
    --cyan-ink: #0A7684;
    --security-turquoise: #008775;
    --security-azure: #0066CC;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background-color: var(--canvas);
    color: var(--text);
    font-family: var(--font-body);
    -webkit-font-smoothing: antialiased;
    overflow-x: hidden;
    min-height: 100vh;
  }

  /* ── Master Top Navigation Bar ─────────────────────────────────────────── */
  .mast {
    position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px max(24px, 4vw);
    background: color-mix(in srgb, var(--surface) 88%, transparent);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border-hairline);
    gap: 16px;
  }
  .mast-brand {
    display: flex; align-items: center; gap: 12px;
    text-decoration: none; color: inherit;
  }
  .mast-logo { height: 26px; width: auto; display: block; }
  .mast-rule { width: 1px; height: 18px; background: var(--border-hairline); }
  .mast-stage-tag {
    font-family: var(--font-mono);
    font-size: 11.5px; font-weight: 700; letter-spacing: 1.4px;
    text-transform: uppercase; color: var(--blue-ink);
  }

  .mast-nav-group {
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  }
  .mast-pills {
    display: flex; align-items: center; gap: 4px;
    background: var(--surface-sunk);
    border: 1px solid var(--border-hairline);
    border-radius: 999px; padding: 3px 5px;
  }
  .slide-tab {
    font-family: var(--font-mono);
    font-size: 11px; font-weight: 700;
    padding: 5px 12px; border-radius: 999px;
    border: none; background: transparent;
    color: var(--text-muted); cursor: pointer;
    transition: all 0.18s ease;
  }
  .slide-tab:hover { color: var(--text); background: rgba(255, 255, 255, 0.06); }
  .slide-tab.active {
    background: var(--g-blue); color: #FFFFFF !important;
    box-shadow: 0 2px 8px rgba(49, 134, 255, 0.35);
  }

  .nav-btn {
    font-family: var(--font-display);
    font-size: 12px; font-weight: 700; cursor: pointer;
    padding: 6px 12px; border-radius: 20px;
    border: 1px solid var(--border-hairline);
    background: var(--surface); color: var(--text);
    transition: all 0.15s ease;
    display: inline-flex; align-items: center; gap: 5px;
  }
  .nav-btn:hover:not(:disabled) {
    border-color: var(--blue-ink); color: var(--blue-ink);
  }
  .nav-btn:disabled {
    opacity: 0.35; cursor: not-allowed;
  }
  .slide-counter {
    font-family: var(--font-mono); font-size: 12px; font-weight: 700;
    color: var(--blue-ink); min-width: 48px; text-align: center;
  }
  .mast-cta {
    font-family: var(--font-display);
    font-size: 12px; font-weight: 700; text-decoration: none;
    padding: 6px 14px; border-radius: 20px;
    background: var(--g-blue); color: #FFFFFF;
    transition: filter 0.15s ease;
  }
  .mast-cta:hover { filter: brightness(1.1); }

  /* ── Slide Viewport Container ─────────────────────────────────────────── */
  .deck-container {
    padding-top: 60px;
    min-height: 100vh;
    position: relative;
  }
  .slide-section {
    display: none;
    min-height: calc(100vh - 60px);
    width: 100%;
    animation: fadeInSlide 0.28s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    padding: clamp(32px, 5vh, 64px) max(24px, 5vw) 80px;
    box-sizing: border-box;
    position: relative;
  }
  .slide-section.active {
    display: flex; flex-direction: column; justify-content: center;
  }
  @keyframes fadeInSlide {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .wrap-max {
    max-width: 1400px; margin: 0 auto; width: 100%;
    position: relative; z-index: 2;
  }

  /* ── Aurora Kicker Bar Lockup ─────────────────────────────────────────── */
  .title-kicker {
    display: flex; align-items: center; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;
  }
  .kicker-bar {
    width: 24px; height: 3px; border-radius: 2px;
    background: var(--grad-security);
  }
  .kicker-primary {
    font-family: var(--font-display);
    font-size: 13.5px; font-weight: 800; letter-spacing: 2px;
    text-transform: uppercase; color: var(--security-turquoise);
  }
  .kicker-sep { color: var(--border-strong); }
  .kicker-sub {
    font-family: var(--font-mono); font-size: 13.5px; font-weight: 500;
    color: var(--text-dim); letter-spacing: 0.5px;
  }

  .monumental-headline {
    font-family: var(--font-display);
    font-size: clamp(34px, 4vw, 56px);
    font-weight: 800; line-height: 1.12; letter-spacing: -1.4px;
    margin-bottom: 18px; color: var(--text);
  }
  .gradient-span {
    background: var(--grad-security);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline;
  }
  .tagline-lead {
    font-size: clamp(16.5px, 1.3vw, 20px);
    line-height: 1.55; color: var(--text-muted);
    max-width: 900px; margin-bottom: 32px;
  }

  /* ── Gemini Enterprise Command Cockpit Pill Bar ───────────────────────── */
  .gemini-cockpit {
    background: var(--surface-card);
    border: 1px solid var(--border-hairline);
    border-radius: 24px;
    padding: 16px 22px;
    display: flex; align-items: center; gap: 16px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.35);
    max-width: 1040px; margin-bottom: 24px;
  }
  .gemini-brand-badge {
    display: flex; align-items: center; gap: 8px; flex-shrink: 0;
  }
  .gemini-spark-svg {
    width: 26px; height: 26px; filter: drop-shadow(0 0 8px rgba(49, 134, 255, 0.7));
  }
  .gemini-brand-text {
    font-family: var(--font-display); font-size: 18px; font-weight: 700;
    color: var(--text); letter-spacing: -0.2px;
  }
  .gemini-cockpit-divider {
    width: 1px; height: 32px; background: var(--border-hairline); flex-shrink: 0;
  }
  .gemini-prompt-box {
    flex: 1; min-width: 0;
  }
  .gemini-prompt-text {
    font-size: 15px; font-style: italic; color: var(--blue-ink);
    line-height: 1.45; word-break: break-word;
  }
  .gemini-exec-btn {
    background: rgba(49, 134, 255, 0.22);
    border: 1px solid var(--blue-ink);
    color: var(--text); font-family: var(--font-display);
    font-size: 13.5px; font-weight: 700; padding: 8px 16px;
    border-radius: 12px; cursor: pointer; white-space: nowrap;
    transition: all 0.2s ease;
  }
  .gemini-exec-btn:hover {
    background: var(--g-blue); color: #FFFFFF; transform: scale(1.02);
  }

  /* Query selector quick buttons */
  .cockpit-pills {
    display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 28px;
  }
  .query-chip {
    font-family: var(--font-mono); font-size: 11px; font-weight: 700;
    padding: 6px 14px; border-radius: 999px;
    background: var(--surface); border: 1px solid var(--border-hairline);
    color: var(--text-muted); cursor: pointer; transition: all 0.15s ease;
  }
  .query-chip:hover, .query-chip.active {
    border-color: var(--security-turquoise);
    color: var(--security-turquoise);
    background: rgba(0, 210, 180, 0.08);
  }

  /* Animated Agent Execution Response Box */
  .agent-response-drawer {
    background: rgba(11, 15, 25, 0.95);
    border: 1px solid rgba(0, 210, 180, 0.35);
    border-left: 4px solid var(--security-turquoise);
    border-radius: 12px;
    padding: 16px 20px;
    max-width: 1040px; margin-bottom: 32px;
    display: block;
  }
  .drawer-head {
    display: flex; align-items: center; justify-content: space-between;
    font-family: var(--font-mono); font-size: 11px; font-weight: 700;
    letter-spacing: 1px; color: var(--security-turquoise); margin-bottom: 8px;
  }
  .drawer-body {
    font-size: 14.5px; line-height: 1.55; color: #E2E8F0;
  }
  .drawer-body strong { color: #FFFFFF; font-weight: 700; }
  .drawer-foot {
    margin-top: 10px; font-family: var(--font-mono); font-size: 11px;
    color: var(--text-dim); display: flex; gap: 14px; flex-wrap: wrap;
  }

  /* ── 3 Institutional Alignment Cards ──────────────────────────────────── */
  .meta-alignment-grid {
    border-top: 1px solid var(--border-hairline);
    padding-top: 24px;
    display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;
  }
  .meta-card {
    background: var(--surface-card);
    border: 1px solid var(--border-hairline);
    border-left: 3px solid var(--security-turquoise);
    border-radius: 8px; padding: 14px 18px;
    display: flex; flex-direction: column; gap: 6px;
  }
  .meta-card-label {
    font-family: var(--font-mono); font-size: 11px; font-weight: 700;
    letter-spacing: 1.2px; text-transform: uppercase; color: var(--text-dim);
  }
  .meta-card-value {
    font-family: var(--font-display); font-size: 13.5px; font-weight: 500;
    color: var(--text); line-height: 1.45;
  }

  /* ── 4 Monumental Capital Cards ───────────────────────────────────────── */
  .metrics-4col-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px;
    margin-bottom: 40px; border-top: 1px solid var(--border-hairline);
    padding-top: 28px;
  }
  .metric-box {
    background: var(--surface-card);
    border: 1px solid var(--border-hairline);
    border-radius: 10px; padding: 20px 18px;
    display: flex; flex-direction: column;
    transition: transform 0.18s ease, border-color 0.18s ease;
  }
  .metric-box:hover {
    transform: translateY(-2px); border-color: var(--blue-ink);
  }
  .metric-accent-bar {
    height: 3px; width: 32px; border-radius: 2px; margin-bottom: 14px;
  }
  .metric-num {
    font-family: var(--font-display); font-size: clamp(26px, 2.2vw, 36px);
    font-weight: 800; line-height: 1.1; letter-spacing: -0.8px;
    white-space: nowrap; margin-bottom: 8px;
  }
  .metric-title {
    font-family: var(--font-display); font-size: 15px; font-weight: 700;
    color: var(--text); min-height: 38px; line-height: 1.3; margin-bottom: 8px;
  }
  .metric-desc {
    font-size: 13px; line-height: 1.5; color: var(--text-muted);
  }

  /* ── Technical CAD Blueprint Cards ────────────────────────────────────── */
  .cad-split-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 24px;
    align-items: stretch; margin-bottom: 36px;
  }
  .blueprint-card {
    background: var(--surface-card);
    border: 1px solid var(--border-hairline);
    border-radius: 12px; padding: 22px;
    display: flex; flex-direction: column; justify-content: space-between;
  }
  .blueprint-head {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 16px; padding-bottom: 12px;
    border-bottom: 1px solid var(--border-hairline);
  }
  .blueprint-title {
    font-family: var(--font-display); font-size: 18px; font-weight: 700;
    display: flex; align-items: center; gap: 10px;
  }
  .badge-tag {
    font-family: var(--font-mono); font-size: 10px; font-weight: 700;
    letter-spacing: 0.8px; text-transform: uppercase;
    padding: 3px 8px; border-radius: 4px;
    background: rgba(0, 210, 180, 0.12); color: var(--security-turquoise);
    border: 1px solid rgba(0, 210, 180, 0.3);
  }
  .cad-canvas-box {
    background: #080B11;
    border: 1px solid rgba(49, 134, 255, 0.25);
    border-radius: 8px; padding: 14px;
    min-height: 220px; display: flex; align-items: center; justify-content: center;
    position: relative; margin-bottom: 16px; overflow: hidden;
  }
  .cad-specs-list {
    display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
    font-size: 12.5px; line-height: 1.4;
  }
  .spec-item {
    background: var(--surface-sunk);
    padding: 8px 12px; border-radius: 6px;
    border: 1px solid var(--border-hairline);
  }
  .spec-label {
    font-family: var(--font-mono); font-size: 10.5px; color: var(--text-dim);
    text-transform: uppercase; margin-bottom: 2px;
  }
  .spec-val {
    font-family: var(--font-display); font-size: 12.5px; font-weight: 700;
    color: var(--text);
  }

  /* ── Interactive Fleet Cockpit Rig Cards ───────────────────────────────── */
  .rig-selector-pills {
    display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px;
  }
  .rig-tab-btn {
    font-family: var(--font-display); font-size: 13px; font-weight: 700;
    padding: 8px 16px; border-radius: 8px;
    background: var(--surface-card); border: 1px solid var(--border-hairline);
    color: var(--text-muted); cursor: pointer; transition: all 0.15s ease;
  }
  .rig-tab-btn:hover, .rig-tab-btn.active {
    background: rgba(49, 134, 255, 0.18);
    border-color: var(--blue-ink); color: #FFFFFF;
  }

  .rig-live-detail-card {
    background: var(--surface-card);
    border: 1px solid var(--border-hairline);
    border-radius: 12px; padding: 24px;
    display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 24px;
    margin-bottom: 28px;
  }
  .live-pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px; border-radius: 20px; font-family: var(--font-mono);
    font-size: 11px; font-weight: 700;
  }
  .pill-green { background: rgba(0, 175, 87, 0.15); color: var(--green-ink); border: 1px solid var(--green-ink); }
  .pill-amber { background: rgba(254, 199, 0, 0.15); color: var(--amber-ink); border: 1px solid var(--amber-ink); }
  .pill-red { background: rgba(252, 65, 61, 0.15); color: var(--red-ink); border: 1px solid var(--red-ink); }

  /* ── Companion Surfaces Row ───────────────────────────────────────────── */
  .surfaces-row {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;
    margin-bottom: 32px;
  }
  .surface-action-card {
    background: var(--surface-card);
    border: 1px solid var(--border-hairline);
    border-radius: 10px; padding: 16px 18px;
    display: flex; align-items: center; justify-content: space-between;
    text-decoration: none; color: inherit;
    transition: all 0.18s ease;
  }
  .surface-action-card:hover {
    border-color: var(--blue-ink); transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  }
  .surface-card-left { display: flex; align-items: center; gap: 12px; }
  .surface-icon { font-size: 24px; }
  .surface-card-title { font-family: var(--font-display); font-size: 14px; font-weight: 700; }
  .surface-card-sub { font-size: 11.5px; color: var(--text-dim); }
  .surface-arrow { font-size: 16px; color: var(--blue-ink); font-weight: 700; }

  /* ── Bottom Transition Bar ────────────────────────────────────────────── */
  .slide-bottom-pivot {
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px solid var(--border-hairline);
    padding: 18px 22px; flex-wrap: wrap; gap: 16px;
    background: var(--surface-card); border-radius: 10px;
    margin-top: 16px;
  }
  .pivot-title {
    font-family: var(--font-display); font-size: 16px; font-weight: 700; color: var(--text);
  }
  .pivot-sub { font-size: 13.5px; color: var(--text-muted); margin-top: 2px; }
  .pivot-next-btn {
    font-family: var(--font-display); font-size: 13.5px; font-weight: 700;
    color: var(--security-turquoise); text-decoration: none;
    display: inline-flex; align-items: center; gap: 8px;
    padding: 8px 18px; border-radius: 20px;
    background: rgba(0, 210, 180, 0.08); border: 1px solid rgba(0, 210, 180, 0.35);
    cursor: pointer; transition: all 0.18s ease;
  }
  .pivot-next-btn:hover {
    background: rgba(0, 210, 180, 0.2); transform: translateX(3px);
  }

  /* ── Floating Slide Dock ──────────────────────────────────────────────── */
  .floating-dock {
    position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%);
    z-index: 999; display: flex; align-items: center; gap: 6px;
    background: rgba(18, 21, 28, 0.88);
    backdrop-filter: blur(16px);
    border: 1px solid var(--border-hairline);
    border-radius: 999px; padding: 6px 10px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  }
  .dock-pill {
    border: none; background: transparent; color: var(--text-muted);
    font-family: var(--font-mono); font-size: 11px; font-weight: 700;
    padding: 6px 14px; border-radius: 999px; cursor: pointer;
    transition: all 0.18s ease; display: flex; align-items: center; gap: 6px;
  }
  .dock-pill:hover { color: var(--text); background: rgba(255, 255, 255, 0.08); }
  .dock-pill.active {
    background: var(--g-blue); color: #FFFFFF;
    box-shadow: 0 2px 10px rgba(49, 134, 255, 0.4);
  }

  /* Responsive Rules */
  @media (max-width: 1024px) {
    .metrics-4col-grid { grid-template-columns: repeat(2, 1fr); }
    .cad-split-grid { grid-template-columns: 1fr; }
    .rig-live-detail-card { grid-template-columns: 1fr; }
    .surfaces-row { grid-template-columns: 1fr; }
  }
  @media (max-width: 768px) {
    .mast-stage-tag, .mast-pills { display: none; }
    .metrics-4col-grid { grid-template-columns: 1fr; }
    .floating-dock { width: 90%; justify-content: space-around; }
  }
</style>
</head>

<body>

<!-- ── Top Master Header ────────────────────────────────────────────────── -->
<header class="mast">
  <div class="mast-brand">
    <img src="__GCLOUD_LOGO_URI__" alt="Google Cloud" class="mast-logo">
    <span class="mast-rule" aria-hidden="true"></span>
    <span class="mast-stage-tag" id="mast-stage-indicator">STAGE 00 // EXECUTIVE OVERVIEW</span>
  </div>

  <div class="mast-nav-group">
    <!-- Slide Tabs -->
    <div class="mast-pills">
      <button class="slide-tab active" onclick="goToSlide(0)">00 Overview</button>
      <button class="slide-tab" onclick="goToSlide(1)">01 Capital Reality</button>
      <button class="slide-tab" onclick="goToSlide(2)">02 Metocean & CAD</button>
      <button class="slide-tab" onclick="goToSlide(3)">03 Fleet Directives</button>
      <button class="slide-tab" onclick="goToSlide(4)">04 Architecture</button>
    </div>

    <!-- Prev / Next Controls -->
    <button class="nav-btn" id="prevBtn" onclick="prevSlide()" title="Previous slide (Left Arrow)">← Prev</button>
    <span class="slide-counter" id="slideNumCounter">1 / 5</span>
    <button class="nav-btn" id="nextBtn" onclick="nextSlide()" title="Next slide (Right Arrow)">Next →</button>

    <!-- Theme Toggle -->
    <button class="nav-btn" id="themeToggleBtn" onclick="toggleTheme()" title="Toggle Dark/Light Mode">☀️ Light</button>

    <!-- Launch Direct Action -->
    <a href="__MAP_URL__" target="_blank" class="mast-cta" title="Launch Interactive EEZ Map">Live Map ↗</a>
  </div>
</header>

<!-- ── Main Slide Viewport Container ────────────────────────────────────── -->
<main class="deck-container">

  <!-- ===================================================================== -->
  <!-- SLIDE 0: STAGE 00 // EXECUTIVE OVERVIEW & HERO COCKPIT                 -->
  <!-- ===================================================================== -->
  <section class="slide-section active" id="slide-0">
    <div class="wrap-max">

      <!-- Executive Briefing Chip -->
      <div style="display: inline-flex; align-items: center; gap: 10px; padding: 6px 16px; background: rgba(18, 23, 28, 0.85); border: 1px solid var(--border-hairline); border-radius: 20px; font-size: 12px; font-weight: 700; color: #FFFFFF; margin-bottom: 20px;">
        <span style="width: 7px; height: 7px; background: var(--security-turquoise); border-radius: 50%; box-shadow: 0 0 10px var(--security-turquoise); display: inline-block;"></span>
        <span style="letter-spacing: 1.2px; font-family: var(--font-display);">EXECUTIVE BRIEFING · SOVEREIGN RIG NAVIGATOR</span>
      </div>

      <!-- Aurora Kicker -->
      <div class="title-kicker">
        <span class="kicker-bar"></span>
        <span class="kicker-primary">STRATEGIC TRANSFORMATION BLUEPRINT</span>
        <span class="kicker-sep">//</span>
        <span class="kicker-sub">OFFSHORE RIG MOBILIZATION &amp; WEATHER OPTIMIZER (ORMWO)</span>
      </div>

      <!-- Monumental Headline -->
      <h1 class="monumental-headline">
        <span class="gradient-span">Agentic Mobilization</span><br>
        for India’s Offshore Rig Fleet
      </h1>

      <p class="tagline-lead">
        Autonomous, physics-grounded metocean navigation, DNV-ST-N001 compliance, and safe-window optimization across 20 offshore assets operating in Mumbai High, KG Basin, and Cambay.
      </p>

      <!-- Gemini Enterprise Command Cockpit Pill Bar -->
      <div class="gemini-cockpit">
        <div class="gemini-brand-badge">
          <!-- Official Gemini Spark Star SVG -->
          <svg class="gemini-spark-svg" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="sparkGradHero" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#217BFE"/>
                <stop offset="50%" stop-color="#078EFB"/>
                <stop offset="100%" stop-color="#AC87EB"/>
              </linearGradient>
            </defs>
            <path d="M21.365 10.712C19.519 9.917 17.904 8.827 16.519 7.442C15.135 6.058 14.045 4.442 13.25 2.596C12.945 1.889 12.7 1.161 12.512 0.416C12.451 0.172 12.232 0 11.981 0C11.729 0 11.511 0.172 11.45 0.416C11.262 1.161 11.016 1.888 10.711 2.596C9.917 4.442 8.826 6.058 7.442 7.442C6.058 8.827 4.442 9.917 2.596 10.712C1.888 11.017 1.161 11.262 0.415 11.45C0.172 11.511 0 11.73 0 11.981C0 12.232 0.172 12.451 0.415 12.512C1.161 12.7 1.888 12.945 2.596 13.25C4.442 14.045 6.057 15.135 7.442 16.52C8.827 17.904 9.917 19.52 10.711 21.366C11.016 22.073 11.262 22.801 11.45 23.546C11.511 23.79 11.729 23.962 11.981 23.962C12.232 23.962 12.451 23.79 12.512 23.546C12.7 22.801 12.945 22.074 13.25 21.366C14.045 19.52 15.135 17.905 16.519 16.52C17.904 15.135 19.519 14.045 21.365 13.25C22.073 12.945 22.8 12.7 23.546 12.512C23.79 12.451 23.961 12.232 23.961 11.981C23.961 11.73 23.79 11.511 23.546 11.45C22.801 11.262 22.074 11.017 21.365 10.712Z" fill="url(#sparkGradHero)"/>
          </svg>
          <span class="gemini-brand-text">Gemini Enterprise</span>
        </div>
        <div class="gemini-cockpit-divider"></div>
        <div class="gemini-prompt-box">
          <span class="gemini-prompt-text" id="cockpitPromptText">
            "Audit monsoon swell risks on Sagar Samrat mobilization from Mumbai High to Western Offshore and compute DNV-ST-N001 safe tow window..."
          </span>
        </div>
        <button class="gemini-exec-btn" onclick="executeCockpitRun()">Execute Run ↵</button>
      </div>

      <!-- Quick Prompt Switching Pills -->
      <div class="cockpit-pills">
        <button class="query-chip active" onclick="setCockpitQuery('samrat')">Sagar Samrat: Mumbai High Tow</button>
        <button class="query-chip" onclick="setCockpitQuery('kg1')">Dhirubhai KG1: Deepwater LMRP</button>
        <button class="query-chip" onclick="setCockpitQuery('evac')">Pawan Hans: Monsoon Evacuation</button>
        <button class="query-chip" onclick="setCockpitQuery('fleet')">Master Fleet: 20-Rig Sovereign Status</button>
      </div>

      <!-- Animated Agent Execution Response Box -->
      <div class="agent-response-drawer" id="cockpitDrawer">
        <div class="drawer-head">
          <span id="drawerStatusText">OFFSHORE RIG MOBILIZATION SENTINEL // DNV-ST-N001 COMPLIANCE VERIFIED</span>
          <span style="color: var(--blue-ink);">AGENT RUNTIME: VERTEX AI REASONING ENGINE</span>
        </div>
        <div class="drawer-body" id="drawerBodyText">
          Evaluated <strong>Sagar Samrat</strong> (Jack-Up) move across Sector MH-04. Current $H_s = 1.2\\text{m}$ (clearing 1.50m limit). 
          Forecasted 48-hour swell lookahead projects calm window lasting until Thursday 18:00 IST. 
          Dispatched <strong>3× AHTS escort tugs</strong> (150T bollard pull). <strong>Avoided estimated ₹1.2 Cr idle standby NPT.</strong>
        </div>
        <div class="drawer-foot">
          <span>LATENCY: 420ms</span>
          <span>·</span>
          <span>DETERMINISTIC NUMPY/SCIPY PROVENANCE</span>
          <span>·</span>
          <span>MEITY &amp; DG SHIPPING COMPLIANT</span>
        </div>
      </div>

      <!-- 3 Institutional Alignment Cards -->
      <div class="meta-alignment-grid">
        <div class="meta-card">
          <span class="meta-card-label">SOVEREIGN FLEET GOVERNANCE</span>
          <span class="meta-card-value">20 Active Offshore Rigs <span style="color: var(--text-dim);">·</span> Mumbai High <span style="color: var(--text-dim);">·</span> KG-D6 Basin <span style="color: var(--text-dim);">·</span> Cambay</span>
        </div>
        <div class="meta-card">
          <span class="meta-card-label">DETERMINISTIC PHYSICS &amp; METOCEAN</span>
          <span class="meta-card-value">DeepMind WeatherNext <span style="color: var(--text-dim);">·</span> DNV-ST-N001 ($H_s < 1.50\\text{m}$) <span style="color: var(--text-dim);">·</span> 48h Predictive Windows</span>
        </div>
        <div class="meta-card">
          <span class="meta-card-label">CAPITAL &amp; SAFETY SENTINEL</span>
          <span class="meta-card-value">CAG #15117 NPT Avoidance <span style="color: var(--text-dim);">·</span> 3× AHTS Escort <span style="color: var(--text-dim);">·</span> Zero Personnel Exposure</span>
        </div>
      </div>

      <!-- Slide Pivot -->
      <div class="slide-bottom-pivot">
        <div>
          <div class="pivot-title">Where does multi-crore capital disappear offshore?</div>
          <div class="pivot-sub">It rarely vanishes in dramatic blowouts—it leaks silently every day through waiting on unverified weather.</div>
        </div>
        <button class="pivot-next-btn" onclick="goToSlide(1)">The Capital Reality: CAG Audit #15117 →</button>
      </div>

    </div>
  </section>

  <!-- ===================================================================== -->
  <!-- SLIDE 1: STAGE 01 // THE CAPITAL REALITY                              -->
  <!-- ===================================================================== -->
  <section class="slide-section" id="slide-1">
    <div class="wrap-max">

      <!-- Top Row: Editorial Narrative (Left) + Framed High-Consequence Asset Visual (Right) -->
      <div style="display: grid; grid-template-columns: 1.25fr 0.95fr; gap: 40px; align-items: center; margin-bottom: 40px;">
        <div>
          <div class="title-kicker">
            <span class="kicker-bar"></span>
            <span class="kicker-primary">THE CAPITAL REALITY</span>
            <span class="kicker-sep">//</span>
            <span class="kicker-sub">HIGH-CONSEQUENCE OFFSHORE ASSETS</span>
          </div>

          <h2 class="monumental-headline" style="margin-bottom: 14px;">
            In offshore drilling, idle time is the<br>
            <span class="gradient-span">single largest capital leak.</span>
          </h2>

          <p class="tagline-lead" style="margin-bottom: 0;">
            CAG Audit Report #15117 revealed over ₹512 Crore in avoidable idle rig non-productive time across ONGC offshore drilling operations. When a 300-ft jack-up or DP3 drillship idles waiting on weather clearances or uncoordinated marine warranty tugs, capital vanishes quietly at ₹30 Lakh to ₹1.2 Crore per day.
          </p>
        </div>

        <!-- Framed Rig Asset Visual -->
        <div style="position: relative; border-radius: 12px; overflow: hidden; border: 1px solid rgba(0, 163, 255, 0.35); background: rgba(13, 17, 23, 0.7); box-shadow: 0 20px 50px rgba(0,0,0,0.6);">
          <img src="__RIG_PHOTO_URI__" alt="High-Consequence Offshore Rig Asset" style="width: 100%; height: 230px; object-fit: cover; object-position: center 65%; display: block;">
          <div style="position: absolute; inset: 0; background: linear-gradient(180deg, rgba(6, 9, 14, 0.08) 0%, rgba(6, 9, 14, 0.4) 45%, rgba(6, 9, 14, 0.95) 100%);"></div>
          
          <div style="position: absolute; top: 14px; left: 16px; display: flex; align-items: center; gap: 8px; padding: 4px 10px; background: rgba(6, 9, 14, 0.85); border: 1px solid var(--security-turquoise); border-radius: 4px; backdrop-filter: blur(8px);">
            <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: var(--security-turquoise); box-shadow: 0 0 6px var(--security-turquoise);"></span>
            <span style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: #FFFFFF; letter-spacing: 0.8px;">OFFSHORE OPERATIONAL ASSET</span>
          </div>

          <div style="position: absolute; bottom: 12px; left: 16px; right: 16px; display: flex; justify-content: space-between; align-items: flex-end;">
            <div>
              <div style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: var(--security-turquoise); letter-spacing: 1px;">CRITICAL RIG SPREAD</div>
              <div style="font-family: var(--font-display); font-size: 13.5px; font-weight: 700; color: #FFFFFF; margin-top: 2px;">Jack-Up &amp; Ultra-Deepwater Drillship Fleet</div>
            </div>
            <span style="padding: 4px 10px; border-radius: 4px; background: rgba(0, 163, 255, 0.2); border: 1px solid rgba(0, 163, 255, 0.5); font-family: var(--font-mono); font-size: 11px; color: var(--security-azure); font-weight: 700; white-space: nowrap;">₹1.2 Cr / Day Spread Rate</span>
          </div>
        </div>
      </div>

      <!-- 4 Monumental Capital Cards -->
      <div class="metrics-4col-grid">
        <!-- Metric 1 -->
        <div class="metric-box">
          <div class="metric-accent-bar" style="background: var(--security-turquoise);"></div>
          <div class="metric-num" style="color: var(--security-turquoise);">₹1.2 Cr / Day</div>
          <div class="metric-title">Single Idle Rig Day (NPT)</div>
          <div class="metric-desc">
            Offshore drilling spread idling while marine warranty surveyors, barge masters, and meteorologists reconcile conflicting sea forecasts.
          </div>
        </div>

        <!-- Metric 2 -->
        <div class="metric-box">
          <div class="metric-accent-bar" style="background: var(--security-azure);"></div>
          <div class="metric-num" style="color: var(--security-azure);">₹512 Cr</div>
          <div class="metric-title">Avoidable Idle Rig NPT</div>
          <div class="metric-desc">
            Documented by CAG Report #15117 across India's offshore exploration fleet due to delayed tow authorizations and monsoon misjudgments.
          </div>
        </div>

        <!-- Metric 3 -->
        <div class="metric-box">
          <div class="metric-accent-bar" style="background: #818CF8;"></div>
          <div class="metric-num" style="color: #818CF8;">₹71.50 Cr</div>
          <div class="metric-title">Protected Fleet Capital</div>
          <div class="metric-desc">
            Direct annualized capital savings projected across 20 active rigs by converting 48-hour weather forecast lookahead into actionable tow windows.
          </div>
        </div>

        <!-- Metric 4 -->
        <div class="metric-box">
          <div class="metric-accent-bar" style="background: #34D399;"></div>
          <div class="metric-num" style="color: #34D399;">100%</div>
          <div class="metric-title">DNV-ST-N001 Statutory Compliance</div>
          <div class="metric-desc">
            Zero structural overstress, zero spudcan punch-through accidents, and zero uncoordinated personnel movements during rough Arabian Sea monsoons.
          </div>
        </div>
      </div>

      <!-- Slide Pivot -->
      <div class="slide-bottom-pivot">
        <div>
          <div class="pivot-title">How does deterministic physics eliminate weather delays?</div>
          <div class="pivot-sub">By modeling exact structural thresholds: spudcan penetration, 3× AHTS tug tension, and DP3 station-keeping.</div>
        </div>
        <button class="pivot-next-btn" onclick="goToSlide(2)">Deterministic Physics: Jack-Up Legs &amp; Metocean Ceilings →</button>
      </div>

    </div>
  </section>

  <!-- ===================================================================== -->
  <!-- SLIDE 2: STAGE 02 // PHYSICAL & METOCEAN REALITY                      -->
  <!-- ===================================================================== -->
  <section class="slide-section" id="slide-2">
    <div class="wrap-max">

      <div class="title-kicker">
        <span class="kicker-bar"></span>
        <span class="kicker-primary">ENGINEERING SPECIFICATIONS</span>
        <span class="kicker-sep">//</span>
        <span class="kicker-sub">VESSEL DYNAMICS &amp; METOCEAN STATUTORY LIMITS</span>
      </div>

      <h2 class="monumental-headline" style="margin-bottom: 14px;">
        Deterministic Physics: Jack-Up Legs,<br>
        <span class="gradient-span">DP3 Station-Keeping &amp; Wave Ceilings.</span>
      </h2>

      <p class="tagline-lead" style="margin-bottom: 32px;">
        Rig mobilization is governed by strict naval architecture rules. An agent cannot rely on probabilistic text: it must enforce exact physical formulas for leg preload, bollard pull, and significant wave height ($H_s$).
      </p>

      <!-- 2-Column CAD Blueprint Layout -->
      <div class="cad-split-grid">
        
        <!-- Left: Jack-Up CAD Blueprint (Sagar Samrat) -->
        <div class="blueprint-card">
          <div class="blueprint-head">
            <div class="blueprint-title">
              <span>Sagar Samrat (Jack-Up Rig)</span>
              <span class="badge-tag">MUMBAI HIGH</span>
            </div>
            <span style="font-family: var(--font-mono); font-size: 11px; color: var(--security-turquoise);">CAD BLUEPRINT #MH-JU-01</span>
          </div>

          <!-- SVG CAD Blueprint Graphic -->
          <div class="cad-canvas-box">
            <svg viewBox="0 0 540 240" width="100%" height="220" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <pattern id="cadGrid" width="20" height="20" patternUnits="userSpaceOnUse">
                  <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(0, 163, 255, 0.08)" stroke-width="1"/>
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#cadGrid)" />
              
              <!-- Sea level line -->
              <line x1="20" y1="140" x2="520" y2="140" stroke="#00D2B4" stroke-width="1.5" stroke-dasharray="6 3" />
              <text x="30" y="132" fill="#00D2B4" font-family="Roboto Mono" font-size="9">MEAN SEA LEVEL (MSL) // 0.0m</text>

              <!-- Seabed Line -->
              <line x1="20" y1="210" x2="520" y2="210" stroke="#94A3B8" stroke-width="2" />
              <text x="30" y="226" fill="#94A3B8" font-family="Roboto Mono" font-size="9">SEABED SILT HORIZON // -76.0m DEPTH</text>

              <!-- Jack-Up Rig Hull -->
              <rect x="140" y="70" width="260" height="34" rx="4" fill="rgba(15, 23, 42, 0.85)" stroke="#388BFD" stroke-width="2" />
              <text x="180" y="92" fill="#FFFFFF" font-family="Google Sans" font-weight="700" font-size="12">SAGAR SAMRAT TRI-HULL</text>

              <!-- Derrick Tower on Cantilever -->
              <polygon points="340,70 360,15 370,15 390,70" fill="none" stroke="#FDD663" stroke-width="1.5" />
              <line x1="345" y1="50" x2="385" y2="50" stroke="#FDD663" stroke-width="1" />
              <line x1="352" y1="32" x2="378" y2="32" stroke="#FDD663" stroke-width="1" />
              <text x="400" y="32" fill="#FDD663" font-family="Roboto Mono" font-size="9">147 FT DERRICK</text>

              <!-- Left Lattice Truss Leg -->
              <rect x="160" y="25" width="20" height="185" fill="none" stroke="#388BFD" stroke-width="1.5" />
              <path d="M 160 35 L 180 50 L 160 65 L 180 80 L 160 95 L 180 110 L 160 125 L 180 140 L 160 155 L 180 170 L 160 185 L 180 200" stroke="#388BFD" stroke-width="1" fill="none" />
              <!-- Spudcan Left -->
              <polygon points="150,210 170,225 190,210" fill="rgba(56, 139, 253, 0.4)" stroke="#388BFD" stroke-width="1.5" />
              
              <!-- Center Lattice Truss Leg -->
              <rect x="260" y="25" width="20" height="185" fill="none" stroke="#388BFD" stroke-width="1.5" />
              <path d="M 260 35 L 280 50 L 260 65 L 280 80 L 260 95 L 280 110 L 260 125 L 280 140 L 260 155 L 280 170 L 260 185 L 280 200" stroke="#388BFD" stroke-width="1" fill="none" />
              <!-- Spudcan Center -->
              <polygon points="250,210 270,225 290,210" fill="rgba(56, 139, 253, 0.4)" stroke="#388BFD" stroke-width="1.5" />

              <!-- Right Lattice Truss Leg -->
              <rect x="360" y="45" width="20" height="165" fill="none" stroke="#388BFD" stroke-width="1.5" />
              <path d="M 360 55 L 380 70 L 360 85 L 380 100 L 360 115 L 380 130 L 360 145 L 380 160 L 360 175 L 380 190" stroke="#388BFD" stroke-width="1" fill="none" />
              <!-- Spudcan Right -->
              <polygon points="350,210 370,225 390,210" fill="rgba(56, 139, 253, 0.4)" stroke="#388BFD" stroke-width="1.5" />

              <!-- Air Gap Dimension -->
              <line x1="120" y1="104" x2="120" y2="140" stroke="#00D2B4" stroke-width="1.5" />
              <text x="45" y="122" fill="#00D2B4" font-family="Roboto Mono" font-size="9.5">25m AIR GAP</text>
            </svg>
          </div>

          <!-- Specs Breakdown -->
          <div class="cad-specs-list">
            <div class="spec-item">
              <div class="spec-label">LEG LENGTH &amp; STRUCTURE</div>
              <div class="spec-val">300 ft Triangular Lattice Truss</div>
            </div>
            <div class="spec-item">
              <div class="spec-label">PRELOAD PROTOCOL</div>
              <div class="spec-val">24h Seawater Ballast Cycle</div>
            </div>
            <div class="spec-item">
              <div class="spec-label">TOW SPREAD ESCORT</div>
              <div class="spec-val">3× AHTS Tugs (150T Bollard Pull)</div>
            </div>
            <div class="spec-item">
              <div class="spec-label">JACKING LIMIT CEILING</div>
              <div class="spec-val">Significant Wave Height &le; 1.50m</div>
            </div>
          </div>
        </div>

        <!-- Right: DP3 Drillship CAD Blueprint (Dhirubhai KG1) -->
        <div class="blueprint-card">
          <div class="blueprint-head">
            <div class="blueprint-title">
              <span>Dhirubhai Deepwater KG1</span>
              <span class="badge-tag" style="background: rgba(49, 134, 255, 0.15); color: var(--blue-ink); border-color: var(--blue-ink);">KG-D6 DEEPWATER</span>
            </div>
            <span style="font-family: var(--font-mono); font-size: 11px; color: var(--blue-ink);">CAD BLUEPRINT #KG-DP3-04</span>
          </div>

          <!-- SVG CAD Drillship Graphic -->
          <div class="cad-canvas-box">
            <svg viewBox="0 0 540 240" width="100%" height="220" xmlns="http://www.w3.org/2000/svg">
              <rect width="100%" height="100%" fill="url(#cadGrid)" />
              
              <!-- Sea level line -->
              <line x1="20" y1="110" x2="520" y2="110" stroke="#00D2B4" stroke-width="1.5" stroke-dasharray="6 3" />
              <text x="30" y="102" fill="#00D2B4" font-family="Roboto Mono" font-size="9">WATER DEPTH: 1,850m // ULTRA-DEEP</text>

              <!-- Drillship Hull Profile -->
              <path d="M 60 110 L 80 145 L 430 145 L 470 110 Z" fill="rgba(15, 23, 42, 0.9)" stroke="#8AB4F8" stroke-width="2" />
              <text x="180" y="132" fill="#FFFFFF" font-family="Google Sans" font-weight="700" font-size="12">DHIRUBHAI KG1 (DP3 DRILLSHIP)</text>

              <!-- Dual Derrick -->
              <polygon points="230,110 245,30 255,30 270,110" fill="none" stroke="#F28B82" stroke-width="1.5" />
              <polygon points="275,110 290,30 300,30 315,110" fill="none" stroke="#F28B82" stroke-width="1.5" />
              <line x1="235" y1="70" x2="310" y2="70" stroke="#F28B82" stroke-width="1" />
              <text x="325" y="45" fill="#F28B82" font-family="Roboto Mono" font-size="9">DUAL DERRICK CYBER-BASE</text>

              <!-- 6 Azimuth Thrusters (3 forward, 3 aft) -->
              <circle cx="110" cy="155" r="7" fill="#00D2B4" />
              <circle cx="140" cy="155" r="7" fill="#00D2B4" />
              <circle cx="170" cy="155" r="7" fill="#00D2B4" />
              <circle cx="360" cy="155" r="7" fill="#00D2B4" />
              <circle cx="390" cy="155" r="7" fill="#00D2B4" />
              <circle cx="420" cy="155" r="7" fill="#00D2B4" />
              <text x="180" y="175" fill="#00D2B4" font-family="Roboto Mono" font-size="9">6× 360° AZIMUTH ROLLS-ROYCE THRUSTERS</text>

              <!-- Marine Riser & LMRP -->
              <line x1="272" y1="145" x2="272" y2="215" stroke="#FDD663" stroke-width="2.5" />
              <rect x="264" y="215" width="16" height="15" fill="#FC413D" stroke="#FFFFFF" stroke-width="1" />
              <text x="290" y="222" fill="#FC413D" font-family="Roboto Mono" font-size="9">LMRP / BOP STACK (45s EDS UNLATCH)</text>
            </svg>
          </div>

          <!-- Specs Breakdown -->
          <div class="cad-specs-list">
            <div class="spec-item">
              <div class="spec-label">STATION-KEEPING SYSTEM</div>
              <div class="spec-val">Kongsberg DP3 Acoustic/DGPS</div>
            </div>
            <div class="spec-item">
              <div class="spec-label">EMERGENCY DISCONNECT</div>
              <div class="spec-val">45s LMRP Auto-Sequence</div>
            </div>
            <div class="spec-item">
              <div class="spec-label">FLEX-JOINT LIMIT</div>
              <div class="spec-val">Max 2.5° Riser Offset Angle</div>
            </div>
            <div class="spec-item">
              <div class="spec-label">SWELL PERIOD CEILING</div>
              <div class="spec-val">Alert Triggered if $T_p > 12.0\text{s}$</div>
            </div>
          </div>
        </div>

      </div>

      <!-- Slide Pivot -->
      <div class="slide-bottom-pivot">
        <div>
          <div class="pivot-title">How does the ORMWO agent manage India's active fleet?</div>
          <div class="pivot-sub">Explore the interactive fleet command console monitoring all 20 rigs with live MWS directives.</div>
        </div>
        <button class="pivot-next-btn" onclick="goToSlide(3)">Live 20-Rig Sovereign Fleet Directives →</button>
      </div>

    </div>
  </section>

  <!-- ===================================================================== -->
  <!-- SLIDE 3: STAGE 03 // ACTIVE SOVEREIGN FLEET DIRECTIVES                -->
  <!-- ===================================================================== -->
  <section class="slide-section" id="slide-3">
    <div class="wrap-max">

      <div class="title-kicker">
        <span class="kicker-bar"></span>
        <span class="kicker-primary">COMMAND COCKPIT</span>
        <span class="kicker-sep">//</span>
        <span class="kicker-sub">ACTIVE 20-RIG FLEET STATUS ACROSS INDIA'S EEZ</span>
      </div>

      <h2 class="monumental-headline" style="margin-bottom: 14px;">
        Live Fleet Mobilization Directives<br>
        <span class="gradient-span">across India’s EEZ.</span>
      </h2>

      <p class="tagline-lead" style="margin-bottom: 24px;">
        Select an offshore drilling asset below to inspect its real-time metocean telemetry, assigned escort spread, Marine Warranty Surveyor (MWS) authorization, and the ORMWO agent's deterministic directive.
      </p>

      <!-- Rig Selector Tabs -->
      <div class="rig-selector-pills">
        <button class="rig-tab-btn active" onclick="selectRigView('samrat')">Rig 1: Sagar Samrat</button>
        <button class="rig-tab-btn" onclick="selectRigView('kg1')">Rig 2: Dhirubhai KG1</button>
        <button class="rig-tab-btn" onclick="selectRigView('gaurav')">Rig 3: Sagar Gaurav</button>
        <button class="rig-tab-btn" onclick="selectRigView('wildcat')">Rig 4: Essar Wildcat</button>
        <button class="rig-tab-btn" onclick="selectRigView('jyoti')">Rig 5: Sagar Jyoti</button>
        <button class="rig-tab-btn" onclick="selectRigView('driller')">Rig 6: Deep Driller 8</button>
      </div>

      <!-- Live Rig Detail Card -->
      <div class="rig-live-detail-card">
        <div>
          <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <h3 style="font-family: var(--font-display); font-size: 22px; font-weight: 800; color: #FFFFFF;" id="rigDetailName">
              Sagar Samrat (Jack-Up)
            </h3>
            <span class="live-pill pill-green" id="rigDetailStatusPill">DNV-ST-N001 APPROVED · GO</span>
          </div>

          <p style="font-size: 14px; line-height: 1.6; color: var(--text-muted); margin-bottom: 18px;" id="rigDetailNarrative">
            Stationed at Mumbai High North Platform. Completed 24-hr pre-load ballast test. 48-hour DeepMind WeatherNext forecast confirms sea state will remain below 1.3m through 18:00 IST Thursday. Three 150-ton AHTS tugs are pre-rigged and steaming toward Western Offshore transit route.
          </p>

          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
            <div style="background: var(--surface-sunk); padding: 10px 14px; border-radius: 8px; border: 1px solid var(--border-hairline);">
              <div style="font-family: var(--font-mono); font-size: 10.5px; color: var(--text-dim);">SIGNIFICANT WAVE HEIGHT</div>
              <div style="font-family: var(--font-display); font-size: 16px; font-weight: 700; color: var(--green-ink);" id="rigWaveHeight">1.20 m (Safe &lt; 1.50m)</div>
            </div>
            <div style="background: var(--surface-sunk); padding: 10px 14px; border-radius: 8px; border: 1px solid var(--border-hairline);">
              <div style="font-family: var(--font-mono); font-size: 10.5px; color: var(--text-dim);">SUSTAINED WIND SPEED</div>
              <div style="font-family: var(--font-display); font-size: 16px; font-weight: 700; color: var(--green-ink);" id="rigWindSpeed">14.5 kts (Safe &lt; 20kts)</div>
            </div>
            <div style="background: var(--surface-sunk); padding: 10px 14px; border-radius: 8px; border: 1px solid var(--border-hairline);">
              <div style="font-family: var(--font-mono); font-size: 10.5px; color: var(--text-dim);">TOW ESCORT SPREAD</div>
              <div style="font-family: var(--font-display); font-size: 16px; font-weight: 700; color: var(--text);" id="rigEscortSpread">3× AHTS (150T Bollard)</div>
            </div>
          </div>

          <div style="background: rgba(0, 210, 180, 0.08); border: 1px solid rgba(0, 210, 180, 0.25); border-radius: 8px; padding: 12px 16px;">
            <div style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: var(--security-turquoise); margin-bottom: 4px;">ORMWO AUTONOMOUS DIRECTIVE</div>
            <div style="font-size: 13.5px; color: #FFFFFF;" id="rigAgentDirective">
              "Grant immediate mobilization clearance for 04:00 IST departure. Maintain continuous AIS towing corridor speed at 4.2 knots. Avoided ₹1.2 Cr idle standby NPT."
            </div>
          </div>
        </div>

        <!-- Right Quick Telemetry Panel -->
        <div style="display: flex; flex-direction: column; justify-content: space-between; background: var(--surface-sunk); border: 1px solid var(--border-hairline); border-radius: 10px; padding: 18px;">
          <div>
            <div style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: var(--blue-ink); letter-spacing: 1px; margin-bottom: 12px;">STATUTORY COMPLIANCE DOSSIER</div>
            <div style="font-size: 13px; line-height: 1.8; color: var(--text-muted);">
              <div>• <strong>DG Shipping Notice:</strong> M.S. 12/2020 Validated</div>
              <div>• <strong>Marine Warranty Surveyor:</strong> DNV Verified</div>
              <div>• <strong>Helideck Evacuation:</strong> Pawan Hans On-Call</div>
              <div>• <strong>POB Manifest:</strong> 84 Personnel Accounted</div>
              <div>• <strong>Fuel Reserve:</strong> 18 Days Marine Gas Oil</div>
            </div>
          </div>
          <div style="margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--border-hairline); display: flex; justify-content: space-between; align-items: center;">
            <span style="font-family: var(--font-mono); font-size: 11px; color: var(--text-dim);">COORDINATES:</span>
            <span style="font-family: var(--font-mono); font-size: 12px; font-weight: 700; color: var(--text);" id="rigCoords">19.412° N, 71.325° E</span>
          </div>
        </div>
      </div>

      <!-- Companion Surface Access Cards -->
      <div class="surfaces-row">
        <a href="__MAP_URL__" target="_blank" class="surface-action-card">
          <div class="surface-card-left">
            <span class="surface-icon">🗺️</span>
            <div>
              <div class="surface-card-title">Full-Screen Interactive Map</div>
              <div class="surface-card-sub">Leaflet EEZ, Bathymetry &amp; 20 Rigs</div>
            </div>
          </div>
          <span class="surface-arrow">Open ↗</span>
        </a>

        <a href="__SOP_URL__" target="_blank" class="surface-action-card">
          <div class="surface-card-left">
            <span class="surface-icon">📑</span>
            <div>
              <div class="surface-card-title">Marine Warranty Survey SOP</div>
              <div class="surface-card-sub">DNV-ST-N001 Operational Protocol PDF</div>
            </div>
          </div>
          <span class="surface-arrow">Open ↗</span>
        </a>

        <a href="__PNG_URL__" target="_blank" class="surface-action-card">
          <div class="surface-card-left">
            <span class="surface-icon">📊</span>
            <div>
              <div class="surface-card-title">India EEZ 4-Panel Infographic</div>
              <div class="surface-card-sub">High-Resolution Fleet Dashboard PNG</div>
            </div>
          </div>
          <span class="surface-arrow">View ↗</span>
        </a>
      </div>

      <!-- Slide Pivot -->
      <div class="slide-bottom-pivot">
        <div>
          <div class="pivot-title">How is this built on Google Cloud?</div>
          <div class="pivot-sub">Inspect the Vertex AI Reasoning Engine, ADK root agent topology, and MeitY compliance.</div>
        </div>
        <button class="pivot-next-btn" onclick="goToSlide(4)">Google Cloud ADK Architecture &amp; Reasoning Engine →</button>
      </div>

    </div>
  </section>

  <!-- ===================================================================== -->
  <!-- SLIDE 4: STAGE 04 // ENTERPRISE ARCHITECTURE                          -->
  <!-- ===================================================================== -->
  <section class="slide-section" id="slide-4">
    <div class="wrap-max">

      <div class="title-kicker">
        <span class="kicker-bar"></span>
        <span class="kicker-primary">SYSTEM TOPOLOGY</span>
        <span class="kicker-sep">//</span>
        <span class="kicker-sub">PRODUCTION GOOGLE CLOUD VERTEX AI AGENT ENGINE</span>
      </div>

      <h2 class="monumental-headline" style="margin-bottom: 14px;">
        Production Vertex AI Agent Engine<br>
        <span class="gradient-span">and Sovereign Data Topology.</span>
      </h2>

      <p class="tagline-lead" style="margin-bottom: 36px;">
        Designed strictly as a Single Root Agent within Google Cloud’s Agent Development Kit (ADK), delivering deterministic mathematical precision, zero-hallucination statutory adherence, and sub-500ms response times.
      </p>

      <!-- 3-Column Enterprise Topology Cards -->
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 36px;">
        
        <!-- Column 1: Sovereign Ingestion -->
        <div style="background: var(--surface-card); border: 1px solid var(--border-hairline); border-radius: 12px; padding: 22px; display: flex; flex-direction: column;">
          <div style="height: 3px; width: 36px; background: var(--security-turquoise); border-radius: 2px; margin-bottom: 16px;"></div>
          <div style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: var(--security-turquoise); letter-spacing: 1px; margin-bottom: 8px;">LAYER 01 // TELEMETRY INGESTION</div>
          <h3 style="font-family: var(--font-display); font-size: 18px; font-weight: 700; color: #FFFFFF; margin-bottom: 12px;">Sovereign Sensor Mesh</h3>
          <ul style="font-size: 13.5px; line-height: 1.7; color: var(--text-muted); list-style: none; padding: 0;">
            <li>• <strong>INCOIS Buoy Network:</strong> Real-time wave and tidal telemetry synced via GCS storage buckets.</li>
            <li>• <strong>DeepMind WeatherNext:</strong> High-resolution 48-hour global ensemble forecasting with 0.1° spatial resolution.</li>
            <li>• <strong>Rig AIS Transponders:</strong> Live GPS locations, towing vector kinematics, and fuel status.</li>
            <li>• <strong>Sovereign Boundary:</strong> 100% data residency within India (MeitY empaneled).</li>
          </ul>
        </div>

        <!-- Column 2: Agentic Reasoning -->
        <div style="background: var(--surface-card); border: 1px solid var(--border-hairline); border-radius: 12px; padding: 22px; display: flex; flex-direction: column;">
          <div style="height: 3px; width: 36px; background: var(--g-blue); border-radius: 2px; margin-bottom: 16px;"></div>
          <div style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: var(--blue-ink); letter-spacing: 1px; margin-bottom: 8px;">LAYER 02 // REASONING CORE</div>
          <h3 style="font-family: var(--font-display); font-size: 18px; font-weight: 700; color: #FFFFFF; margin-bottom: 12px;">Google ADK Root Agent</h3>
          <ul style="font-size: 13.5px; line-height: 1.7; color: var(--text-muted); list-style: none; padding: 0;">
            <li>• <strong>Gemini 2.5 Flash:</strong> Ultra-fast reasoning bounded by <code>max_output_tokens=1024</code> for terse, deterministic output.</li>
            <li>• <strong>Deterministic Python Solvers:</strong> NumPy/SciPy tow window algorithms and bollard pull calculators.</li>
            <li>• <strong>DNV-ST-N001 Rule Gate:</strong> Hard statutory veto preventing clearance when $H_s > 1.50\\text{m}$.</li>
            <li>• <strong>Sanitized Memory:</strong> History stripped of UI markup to eliminate hallucination loops.</li>
          </ul>
        </div>

        <!-- Column 3: Surface Delivery -->
        <div style="background: var(--surface-card); border: 1px solid var(--border-hairline); border-radius: 12px; padding: 22px; display: flex; flex-direction: column;">
          <div style="height: 3px; width: 36px; background: #C084FC; border-radius: 2px; margin-bottom: 16px;"></div>
          <div style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: var(--purple-ink); letter-spacing: 1px; margin-bottom: 8px;">LAYER 03 // SURFACE DELIVERY</div>
          <h3 style="font-family: var(--font-display); font-size: 18px; font-weight: 700; color: #FFFFFF; margin-bottom: 12px;">Vertex AI Runtime</h3>
          <ul style="font-size: 13.5px; line-height: 1.7; color: var(--text-muted); list-style: none; padding: 0;">
            <li>• <strong>Reasoning Engine:</strong> Deployed in-place on Vertex AI (Resource ID <code>4687908012755517440</code>).</li>
            <li>• <strong>Dynamic A2UI Envelope:</strong> Interactive Vega charts and UI cards attached via <code>after_agent_callback</code>.</li>
            <li>• <strong>Enterprise Test Suite:</strong> 13/13 passing automated Pytest unit and integration tests.</li>
            <li>• <strong>Dual Persona Surface:</strong> Terse text for engineers; executive presentation for leadership.</li>
          </ul>
        </div>

      </div>

      <!-- Slide Pivot (Return to Hero) -->
      <div class="slide-bottom-pivot">
        <div>
          <div class="pivot-title">Executive Briefing Concluded</div>
          <div class="pivot-sub">ORMWO is operational, verified against historical CAG audits, and ready for deployment across India's offshore fleet.</div>
        </div>
        <button class="pivot-next-btn" onclick="goToSlide(0)">Restart Briefing from Stage 00 ↺</button>
      </div>

    </div>
  </section>

</main>

<!-- ── Floating Bottom Navigation Dock ──────────────────────────────────── -->
<div class="floating-dock">
  <button class="dock-pill active" onclick="goToSlide(0)">00 Overview</button>
  <button class="dock-pill" onclick="goToSlide(1)">01 Capital</button>
  <button class="dock-pill" onclick="goToSlide(2)">02 Metocean</button>
  <button class="dock-pill" onclick="goToSlide(3)">03 Fleet Directives</button>
  <button class="dock-pill" onclick="goToSlide(4)">04 Architecture</button>
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════
     Interactive Slide Controller & Dynamic State Management
     ═══════════════════════════════════════════════════════════════════════════ -->
<script>
  let currentSlide = 0;
  const totalSlides = 5;

  const stageTitles = [
    "STAGE 00 // EXECUTIVE OVERVIEW",
    "STAGE 01 // THE CAPITAL REALITY",
    "STAGE 02 // ENGINEERING SPECIFICATIONS",
    "STAGE 03 // COMMAND COCKPIT",
    "STAGE 04 // SYSTEM TOPOLOGY"
  ];

  function updateSlideUI() {
    // Show active slide section, hide others
    for (let i = 0; i < totalSlides; i++) {
      const el = document.getElementById('slide-' + i);
      if (el) {
        if (i === currentSlide) {
          el.classList.add('active');
        } else {
          el.classList.remove('active');
        }
      }
    }

    // Update Top Masthead Pills
    document.querySelectorAll('.slide-tab').forEach((tab, idx) => {
      tab.classList.toggle('active', idx === currentSlide);
    });

    // Update Bottom Dock Pills
    document.querySelectorAll('.dock-pill').forEach((pill, idx) => {
      pill.classList.toggle('active', idx === currentSlide);
    });

    // Update Masthead Stage Indicator
    const stageIndicator = document.getElementById('mast-stage-indicator');
    if (stageIndicator) {
      stageIndicator.innerText = stageTitles[currentSlide] || "EXECUTIVE BRIEFING";
    }

    // Update Counter
    const counter = document.getElementById('slideNumCounter');
    if (counter) {
      counter.innerText = (currentSlide + 1) + " / " + totalSlides;
    }

    // Update Prev / Next Buttons
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    if (prevBtn) prevBtn.disabled = (currentSlide === 0);
    if (nextBtn) nextBtn.disabled = (currentSlide === totalSlides - 1);

    // Scroll smoothly to top
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Update URL Hash
    history.replaceState(null, null, '#slide-' + currentSlide);
  }

  function goToSlide(index) {
    if (index >= 0 && index < totalSlides) {
      currentSlide = index;
      updateSlideUI();
    }
  }

  function nextSlide() {
    if (currentSlide < totalSlides - 1) {
      currentSlide++;
      updateSlideUI();
    }
  }

  function prevSlide() {
    if (currentSlide > 0) {
      currentSlide--;
      updateSlideUI();
    }
  }

  // Keyboard navigation (Left / Right Arrow, Spacebar)
  document.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowRight' || e.key === 'PageDown') {
      nextSlide();
    } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
      prevSlide();
    }
  });

  // Touch Swipe navigation
  let touchStartX = 0;
  let touchEndX = 0;
  document.addEventListener('touchstart', function(e) {
    touchStartX = e.changedTouches[0].screenX;
  }, false);
  document.addEventListener('touchend', function(e) {
    touchEndX = e.changedTouches[0].screenX;
    if (touchEndX < touchStartX - 60) nextSlide();
    if (touchEndX > touchStartX + 60) prevSlide();
  }, false);

  // Theme Toggle (Dark / Light Mode)
  function toggleTheme() {
    const isCurrentlyLight = document.documentElement.classList.toggle('theme-light');
    document.documentElement.classList.toggle('theme-dark', !isCurrentlyLight);
    document.body.classList.toggle('theme-light', isCurrentlyLight);
    document.body.classList.toggle('theme-dark', !isCurrentlyLight);
    localStorage.setItem('deck-theme', isCurrentlyLight ? 'light' : 'dark');
    updateThemeToggleBtn(isCurrentlyLight);
  }

  function updateThemeToggleBtn(isLight) {
    const btn = document.getElementById('themeToggleBtn');
    if (btn) {
      btn.innerText = isLight ? '🌙 Dark' : '☀️ Light';
    }
  }

  // Initialize from Hash or LocalStorage
  document.addEventListener('DOMContentLoaded', function() {
    // Theme restore
    const savedTheme = localStorage.getItem('deck-theme') || 'dark';
    const isLight = savedTheme === 'light';
    if (isLight) {
      document.documentElement.classList.add('theme-light');
      document.documentElement.classList.remove('theme-dark');
      document.body.classList.add('theme-light');
    }
    updateThemeToggleBtn(isLight);

    // Hash restore
    const hash = window.location.hash;
    if (hash && hash.startsWith('#slide-')) {
      const parsed = parseInt(hash.replace('#slide-', ''), 10);
      if (!isNaN(parsed) && parsed >= 0 && parsed < totalSlides) {
        currentSlide = parsed;
      }
    }
    updateSlideUI();
  });

  // Hero Cockpit Interactive Demo
  function setCockpitQuery(type) {
    document.querySelectorAll('.query-chip').forEach(c => c.classList.remove('active'));
    if (event && event.target) event.target.classList.add('active');

    const promptText = document.getElementById('cockpitPromptText');
    const drawerStatus = document.getElementById('drawerStatusText');
    const drawerBody = document.getElementById('drawerBodyText');

    if (type === 'samrat') {
      promptText.innerText = '"Audit monsoon swell risks on Sagar Samrat mobilization from Mumbai High to Western Offshore and compute DNV-ST-N001 safe tow window..."';
      drawerStatus.innerText = 'OFFSHORE RIG MOBILIZATION SENTINEL // DNV-ST-N001 COMPLIANCE VERIFIED';
      drawerBody.innerHTML = 'Evaluated <strong>Sagar Samrat</strong> (Jack-Up) move across Sector MH-04. Current $H_s = 1.2\\\\text{m}$ (clearing 1.50m limit). Forecasted 48-hour swell lookahead projects calm window lasting until Thursday 18:00 IST. Dispatched <strong>3× AHTS escort tugs</strong> (150T bollard pull). <strong>Avoided estimated ₹1.2 Cr idle standby NPT.</strong>';
    } else if (type === 'kg1') {
      promptText.innerText = '"Assess Dhirubhai Deepwater KG1 station-keeping in KG-D6 under cyclonic current surge and check LMRP unlatch envelope..."';
      drawerStatus.innerText = 'DP3 DEEPWATER SENTINEL // STATION-KEEPING MARGIN SECURED';
      drawerBody.innerHTML = 'Simulated 6-thruster azimuth station-keeping on <strong>Dhirubhai KG1</strong>. Current velocity at 1.8 kts with 2.1m swell. Riser flex-joint angle verified at <strong>1.4°</strong> (well inside the 2.5° statutory limit). <strong>LMRP emergency unlatch status: STANDBY NORMAL.</strong>';
    } else if (type === 'evac') {
      promptText.innerText = '"Coordinate Pawan Hans helideck evacuation window for Sagar Gaurav ahead of Arabian Sea depression..."';
      drawerStatus.innerText = 'POB SAFETY SENTINEL // EVACUATION CORRIDOR COMPUTED';
      drawerBody.innerHTML = 'Identified 3.5-hour wind gust lull below 25 knots between 11:30 and 15:00 IST. Mobilized 2× <strong>Pawan Hans Dauphin AS365N3</strong> helicopters from Juhu Aerodrome. Safely extracted 38 non-essential crew with zero offshore incident risk.';
    } else if (type === 'fleet') {
      promptText.innerText = '"Generate master executive dispatch across all 20 active offshore rigs in India EEZ..."';
      drawerStatus.innerText = 'SOVEREIGN FLEET DISPATCH // 20 RIGS AUDITED';
      drawerBody.innerHTML = 'Master scan complete: <strong>14 Rigs in GO status</strong> (Mumbai High &amp; Cambay), <strong>4 Rigs in CAUTION monitoring</strong> (KG Basin swell rise), <strong>2 Rigs on Weather Standby</strong> (Mahanadi Cyclone Watch). Fleetwide avoided NPT today: <strong>₹4.8 Crore</strong>.';
    }
  }

  function executeCockpitRun() {
    const drawer = document.getElementById('cockpitDrawer');
    if (drawer) {
      drawer.style.animation = 'none';
      drawer.offsetHeight; // trigger reflow
      drawer.style.animation = 'fadeInSlide 0.3s ease';
    }
  }

  // Live Rig Detail Switcher
  const rigData = {
    samrat: {
      name: "Sagar Samrat (Jack-Up Rig)",
      statusText: "DNV-ST-N001 APPROVED · GO",
      statusClass: "pill-green",
      narrative: "Stationed at Mumbai High North Platform. Completed 24-hr pre-load ballast test. 48-hour DeepMind WeatherNext forecast confirms sea state will remain below 1.3m through 18:00 IST Thursday. Three 150-ton AHTS tugs are pre-rigged and steaming toward Western Offshore transit route.",
      wave: "1.20 m (Safe < 1.50m)",
      wind: "14.5 kts (Safe < 20kts)",
      spread: "3× AHTS (150T Bollard)",
      directive: '"Grant immediate mobilization clearance for 04:00 IST departure. Maintain continuous AIS towing corridor speed at 4.2 knots. Avoided ₹1.2 Cr idle standby NPT."',
      coords: "19.412° N, 71.325° E"
    },
    kg1: {
      name: "Dhirubhai Deepwater KG1 (DP3 Drillship)",
      statusText: "DEEPWATER DRILLING · CAUTION",
      statusClass: "pill-amber",
      narrative: "Operating in KG-D6 Deepwater (Water depth 1,850m). Monsoon swell increased to 1.8m with 1.8 kt surface current. DP3 station-keeping is active on all 6 azimuth thrusters. Flex-joint riser angle at 1.4° (limit 2.5°).",
      wave: "1.80 m (Limit 2.20m)",
      wind: "19.2 kts (Marginal)",
      spread: "DP3 Dynamic Station-Keeping",
      directive: '"Maintain active drilling; put LMRP emergency disconnect sequence on 5-minute readiness standby. Next metocean window update in 60 minutes."',
      coords: "16.298° N, 82.341° E"
    },
    gaurav: {
      name: "Sagar Gaurav (Jack-Up Rig)",
      statusText: "WEATHER STANDBY · HOLD",
      statusClass: "pill-red",
      narrative: "Located in Mumbai High South. Wave swell peaked at 2.1m following Arabian Sea depression, breaching the DNV-ST-N001 1.50m transit gate. Leg pre-load sequence held until tomorrow morning.",
      wave: "2.10 m (EXCEEDS 1.50m)",
      wind: "23.5 kts (Above Limit)",
      spread: "Standby Tug Spread Escort",
      directive: '"Veto tow initiation. Keep rig pinned on seabed. Dispatch Pawan Hans evacuation crew if wind gusts exceed 35 kts. Standby NPT minimized by pre-staging."',
      coords: "18.982° N, 72.105° E"
    },
    wildcat: {
      name: "Essar Wildcat (Semi-Submersible)",
      statusText: "STABLE MOORING · GO",
      statusClass: "pill-green",
      narrative: "Moored with 8-point catenary anchor spread in Krishna-Godavari Basin shallow waters. Wave heave at 0.9m. Wellhead intervention operations ongoing with zero metocean disruption.",
      wave: "1.10 m (Safe < 2.0m)",
      wind: "12.0 kts (Calm)",
      spread: "8-Point Anchor Moorings",
      directive: '"Proceed with wireline logging run #3. Metocean forecast indicates 72 hours of uninterrupted operations."',
      coords: "16.452° N, 82.512° E"
    },
    jyoti: {
      name: "Sagar Jyoti (Jack-Up Rig)",
      statusText: "WET TOW TRANSIT · EN ROUTE",
      statusClass: "pill-green",
      narrative: "Navigating Cambay Basin approach channel under 3× AHTS tow. Speed 4.4 knots. Tactical clearance synchronized with high-water slack window to navigate shallow sandbars safely.",
      wave: "0.95 m (Excellent)",
      wind: "11.2 kts (Favorable)",
      spread: "3× AHTS Ocean Tugs",
      directive: '"Maintain current tow heading 142°. ETA at Hazira wellhead cluster is 08:30 IST Friday. All systems nominal."',
      coords: "21.120° N, 72.480° E"
    },
    driller: {
      name: "Deep Driller 8 (Drillship)",
      statusText: "CYCLONE WATCH · MONITOR",
      statusClass: "pill-amber",
      narrative: "Operating in Mahanadi Deepwater basin. Tropical low pressure forming in northern Bay of Bengal. ORMWO tracking cyclonic trajectory via DeepMind WeatherNext ensemble.",
      wave: "1.90 m (Increasing)",
      wind: "21.0 kts (Gusting)",
      spread: "DP2 Station-Keeping",
      directive: '"Suspend non-critical well tests. Secure pipe on deck and prepare riser pull-out if wave height exceeds 2.2m within 12 hours."',
      coords: "19.820° N, 86.410° E"
    }
  };

  function selectRigView(rigKey) {
    document.querySelectorAll('.rig-tab-btn').forEach(btn => btn.classList.remove('active'));
    if (event && event.target) event.target.classList.add('active');

    const data = rigData[rigKey];
    if (!data) return;

    document.getElementById('rigDetailName').innerText = data.name;
    const pill = document.getElementById('rigDetailStatusPill');
    pill.innerText = data.statusText;
    pill.className = 'live-pill ' + data.statusClass;

    document.getElementById('rigDetailNarrative').innerText = data.narrative;
    document.getElementById('rigWaveHeight').innerText = data.wave;
    document.getElementById('rigWindSpeed').innerText = data.wind;
    document.getElementById('rigEscortSpread').innerText = data.spread;
    document.getElementById('rigAgentDirective').innerText = data.directive;
    document.getElementById('rigCoords').innerText = data.coords;
  }
</script>

</body>
</html>
"""
