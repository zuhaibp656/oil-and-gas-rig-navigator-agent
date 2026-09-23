"""Deterministic 48-Hour Metocean & Douglas Sea Scale Forecast Engine (ORMWO Tool 2).

In : Target coordinates (lat, lon) and forecast horizon (default 48 hours).
Out: Hourly/stepped MarineWeatherPoint forecasts with Douglas Sea Scale (0-9),
     Cyclone Threat Level, P05/P95 confidence bounds, and strict 2.5m / 35 kts threshold flags.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
from typing import Any

try:
    from app.contracts import MarineWeatherPoint
    from app.rigs.india_eez_dataset import ACTIVE_48H_STORM_ZONES
except ImportError:
    from contracts import MarineWeatherPoint
    from rigs.india_eez_dataset import ACTIVE_48H_STORM_ZONES

BASE_ASSESSMENT_TIME_UTC = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)


def _douglas_sea_scale(hs_m: float) -> int:
    """Convert Significant Wave Height (m) to standard 0-9 Douglas Sea Scale."""
    if hs_m <= 0.0:
        return 0
    if hs_m < 0.1:
        return 1
    if hs_m < 0.5:
        return 2
    if hs_m < 1.25:
        return 3
    if hs_m < 2.5:
        return 4
    if hs_m < 4.0:
        return 5
    if hs_m < 6.0:
        return 6
    if hs_m < 9.0:
        return 7
    if hs_m < 14.0:
        return 8
    return 9


def _classify_cyclone_threat(hs_m: float, wind_kts: float) -> str:
    """Classify cyclone threat level per ORMWO schema: NONE | LOW | MODERATE | SEVERE."""
    if hs_m > 3.0 or wind_kts > 40.0:
        return "SEVERE"
    if hs_m > 2.5 or wind_kts > 35.0:
        return "MODERATE"
    if hs_m > 1.8 or wind_kts > 25.0:
        return "LOW"
    return "NONE"


def compute_marine_weather_forecast(
    lat: float,
    lon: float,
    forecast_hours: int = 48,
    step_hours: int = 3,
) -> list[MarineWeatherPoint]:
    """Compute deterministic 48-hour metocean forecast for (lat, lon).

    Enforces the ORMWO rule:
      safe_for_operations = (significant_wave_height_m <= 2.5) and (wind_speed_knots <= 35.0)
    """
    horizon = max(6, min(int(forecast_hours), 72))
    step = max(1, int(step_hours))

    # Measure proximity to nearest active 48h storm cell
    min_dist_deg = 999.0
    nearest_zone: dict[str, Any] | None = None
    for zone in ACTIVE_48H_STORM_ZONES:
        d = math.hypot(lat - float(zone["latitude"]), lon - float(zone["longitude"]))
        if d < min_dist_deg:
            min_dist_deg = d
            nearest_zone = zone

    in_storm_influence = (
        nearest_zone is not None
        and min_dist_deg <= float(nearest_zone["radius_deg"]) * 1.25
    )

    series: list[MarineWeatherPoint] = []
    for h in range(0, horizon + 1, step):
        ts = (BASE_ASSESSMENT_TIME_UTC + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")

        if in_storm_influence and nearest_zone is not None:
            # Storm peaks around T+28h to T+36h
            peak_hs = float(nearest_zone["peak_hs_m"]) * max(0.65, 1.0 - 0.35 * min_dist_deg)
            peak_wind = float(nearest_zone["peak_wind_kts"]) * max(0.70, 1.0 - 0.30 * min_dist_deg)
            bell = math.exp(-((h - 32.0) ** 2) / (2.0 * (13.5 ** 2)))
            hs_p50 = round(1.45 + (peak_hs - 1.45) * bell, 2)
            wind_p50 = round(21.0 + (peak_wind - 21.0) * bell, 1)
            swell_sec = round(9.8 + (float(nearest_zone["swell_period_s"]) - 9.8) * bell, 1)
        else:
            # Calm/moderate monsoon background corridor
            wave_mod = 0.22 * math.sin(h * math.pi / 24.0)
            hs_p50 = round(1.15 + wave_mod, 2)
            wind_p50 = round(16.5 + 3.2 * math.sin(h * math.pi / 24.0), 1)
            swell_sec = round(8.4 + 0.8 * math.sin(h * math.pi / 24.0), 1)

        # Ornstein-Uhlenbeck 95% confidence dispersion growing with sqrt(lead_time)
        sigma_hs = 0.12 * math.sqrt(1.0 + 0.18 * h)
        sigma_wind = 1.4 * math.sqrt(1.0 + 0.18 * h)
        hs_p05 = round(max(0.3, hs_p50 - 1.645 * sigma_hs), 2)
        hs_p95 = round(hs_p50 + 1.645 * sigma_hs, 2)
        wind_p05 = round(max(5.0, wind_p50 - 1.645 * sigma_wind), 1)
        wind_p95 = round(wind_p50 + 1.645 * sigma_wind, 1)

        # Evaluate safety strictly against ORMWO 2.5m / 35 kts threshold
        is_safe = (hs_p50 <= 2.5) and (wind_p50 <= 35.0)
        sea_state = _douglas_sea_scale(hs_p50)
        threat = _classify_cyclone_threat(hs_p50, wind_p50)

        series.append(
            MarineWeatherPoint(
                timestamp=ts,
                forecast_hour=h,
                wind_speed_knots=wind_p50,
                significant_wave_height_m=hs_p50,
                swell_period_sec=swell_sec,
                cyclone_threat_level=threat,
                sea_state=sea_state,
                safe_for_operations=is_safe,
                hs_p05_m=hs_p05,
                hs_p95_m=hs_p95,
                wind_p05_kts=wind_p05,
                wind_p95_kts=wind_p95,
            )
        )

    return series
