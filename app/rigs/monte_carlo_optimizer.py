"""Stochastic / Monte Carlo Rig Transit & Zero-Idle Redeployment Simulator (ORMWO Tool 3).

In : rig_id, origin {lat, lon}, destination {lat, lon}, departure_window_hours list.
Out: MonteCarloTransitResult with recommended_departure_time, expected_transit_hours,
     probability_of_weather_standby, estimated_npt_cost_inr, and optimal_routing_waypoints.
"""

from __future__ import annotations

from datetime import timedelta
import math
from typing import Any

import numpy as np

try:
    from app.contracts import MonteCarloTransitResult
    from app.rigs.india_eez_dataset import (
        find_nearest_safe_candidate_well,
        is_coordinate_in_storm_zone,
        resolve_rig_by_identifier,
    )
    from app.rigs.metocean_engine import BASE_ASSESSMENT_TIME_UTC
except ImportError:
    from contracts import MonteCarloTransitResult
    from rigs.india_eez_dataset import (
        find_nearest_safe_candidate_well,
        is_coordinate_in_storm_zone,
        resolve_rig_by_identifier,
    )
    from rigs.metocean_engine import BASE_ASSESSMENT_TIME_UTC

EARTH_RADIUS_NM: float = 3440.065


def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate exact Great-Circle maritime distance in nautical miles."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_NM * math.asin(min(1.0, math.sqrt(a)))


def _build_sheltered_waypoints(
    orig_lat: float,
    orig_lon: float,
    dest_lat: float,
    dest_lon: float,
) -> list[list[float]]:
    """Construct a 4-waypoint coastal leeward routing arc that skirts East of Arabian Sea storm core."""
    mid1_lat = round(orig_lat * 0.68 + dest_lat * 0.32, 4)
    mid1_lon = round(orig_lon * 0.62 + dest_lon * 0.38 + 0.14, 4)
    mid2_lat = round(orig_lat * 0.32 + dest_lat * 0.68, 4)
    mid2_lon = round(orig_lon * 0.30 + dest_lon * 0.70 + 0.10, 4)
    return [
        [round(orig_lat, 4), round(orig_lon, 4)],
        [mid1_lat, mid1_lon],
        [mid2_lat, mid2_lon],
        [round(dest_lat, 4), round(dest_lon, 4)],
    ]


def execute_monte_carlo_transit_simulation(
    rig_id: str,
    origin: dict[str, Any] | None = None,
    destination: dict[str, Any] | None = None,
    departure_window_hours: list[int] | None = None,
    trials: int = 2500,
) -> MonteCarloTransitResult:
    """Run vectorized Monte Carlo simulation (N=2500) to optimize rig departure & routing."""
    rig = resolve_rig_by_identifier(rig_id)
    orig_lat = float((origin or {}).get("lat", rig.location.latitude))
    orig_lon = float((origin or {}).get("lon", rig.location.longitude))

    # Automatically select nearest metocean-safe candidate well from the 120-well registry
    # if destination is missing or inside a storm zone
    safe_well = find_nearest_safe_candidate_well(orig_lat, orig_lon, rig.rig_type)
    dest_lat = float((destination or {}).get("lat", safe_well.latitude))
    dest_lon = float((destination or {}).get("lon", safe_well.longitude))
    dest_in_storm, _ = is_coordinate_in_storm_zone(dest_lat, dest_lon)
    if dest_in_storm or (abs(dest_lat - orig_lat) < 0.05 and abs(dest_lon - orig_lon) < 0.05):
        dest_lat = safe_well.latitude
        dest_lon = safe_well.longitude
        dest_well_id = safe_well.well_id
    else:
        dest_well_id = str((destination or {}).get("well_id", safe_well.well_id))

    waypoints = _build_sheltered_waypoints(orig_lat, orig_lon, dest_lat, dest_lon)
    total_dist_nm = 0.0
    for idx in range(len(waypoints) - 1):
        total_dist_nm += haversine_nm(
            waypoints[idx][0], waypoints[idx][1],
            waypoints[idx + 1][0], waypoints[idx + 1][1],
        )
    total_dist_nm = max(18.0, total_dist_nm)

    windows = departure_window_hours or [4, 8, 12, 18, 24]
    rng = np.random.default_rng(seed=42 + sum(ord(c) for c in rig.rig_id))

    # Base calm tow/transit speed (knots) by hull type
    calm_speed_kts = 9.2 if rig.rig_type.ormwo_label == "DRILLSHIP" else 5.4
    best_dep_hour = int(windows[0])
    best_cost_inr = float("inf")
    best_transit_p50 = 0.0
    best_transit_p10 = 0.0
    best_transit_p90 = 0.0
    best_standby_prob = 0.0

    for dep_h in windows:
        dep_h_int = int(dep_h)
        # Storm intensity increases exponentially as dep_h approaches peak hour 32
        storm_exposure = math.exp(-((dep_h_int - 32.0) ** 2) / (2.0 * (12.0 ** 2)))
        hs_samples = rng.normal(loc=1.6 + 2.3 * storm_exposure, scale=0.35, size=trials)
        hs_samples = np.clip(hs_samples, 0.6, 6.5)
        current_samples = rng.normal(loc=-0.35 * storm_exposure, scale=0.25, size=trials)

        # Kwon speed degradation formula
        speed_factor = np.clip(1.0 - 0.045 * (hs_samples ** 2), 0.38, 0.98)
        eff_speed = np.maximum(2.2, calm_speed_kts * speed_factor + current_samples)
        transit_hrs = total_dist_nm / eff_speed

        # Weather standby occurs if wave height during departure > 2.5m
        standby_flags = hs_samples > 2.5
        standby_prob = float(np.mean(standby_flags))
        standby_penalty_hrs = np.where(standby_flags, 36.0, 0.0)

        total_npt_hrs = transit_hrs + standby_penalty_hrs
        hourly_burn_inr = rig.daily_operating_cost_inr / 24.0
        cost_samples_inr = total_npt_hrs * hourly_burn_inr

        mean_cost = float(np.mean(cost_samples_inr))
        if mean_cost < best_cost_inr:
            best_cost_inr = mean_cost
            best_dep_hour = dep_h_int
            best_transit_p50 = round(float(np.percentile(transit_hrs, 50)), 2)
            best_transit_p10 = round(float(np.percentile(transit_hrs, 10)), 2)
            best_transit_p90 = round(float(np.percentile(transit_hrs, 90)), 2)
            best_standby_prob = round(standby_prob, 3)

    rec_dep_iso = (BASE_ASSESSMENT_TIME_UTC + timedelta(hours=best_dep_hour)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    # Static schedule loss = 6 days of Waiting-on-Weather + well suspension NPT
    static_loss_inr = round(rig.daily_operating_cost_inr * 6.0, 2)
    est_npt_cost_inr = round(best_cost_inr, 2)
    avoided_savings_inr = round(max(0.0, static_loss_inr - est_npt_cost_inr), 2)

    return MonteCarloTransitResult(
        rig_id=rig.rig_id,
        origin_lat=round(orig_lat, 4),
        origin_lon=round(orig_lon, 4),
        destination_lat=round(dest_lat, 4),
        destination_lon=round(dest_lon, 4),
        destination_well_id=dest_well_id,
        recommended_departure_time=rec_dep_iso,
        expected_transit_hours=best_transit_p50,
        transit_hours_p10=best_transit_p10,
        transit_hours_p90=best_transit_p90,
        probability_of_weather_standby=best_standby_prob,
        estimated_npt_cost_inr=est_npt_cost_inr,
        static_weather_in_npt_loss_inr=static_loss_inr,
        avoided_npt_savings_inr=avoided_savings_inr,
        optimal_routing_waypoints=waypoints,
    )
