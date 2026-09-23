"""Data contracts and shared domain models for the Offshore Rig Mobilization & Weather Optimizer (ORMWO).

In : None (standalone definitions).
Out: Dataclasses defining rigs, 120+ candidate wells, 48h marine weather forecasts,
     Monte Carlo transit simulations, CAG governance audit records, and A2UI v0.9 messages.
Rule: This module imports NOTHING from this project. All modules import this for shared contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ==============================================================================
# 1. Rig Specifications, Candidate Wells & ORMWO Domain Contracts
# ==============================================================================

class RigType(str, Enum):
    """Classification of onshore and offshore drilling units (ORMWO & ADK compatible)."""
    JACKUP = "JACKUP"
    DRILLSHIP = "DRILLSHIP"
    SEMI_SUB = "SEMI_SUB"
    OFFSHORE_JACKUP = "OFFSHORE_JACKUP"
    OFFSHORE_SEMISUB = "OFFSHORE_SEMISUB"
    OFFSHORE_DRILLSHIP = "OFFSHORE_DRILLSHIP"
    ONSHORE_LAND_RIG = "ONSHORE_LAND_RIG"
    FIXED_PLATFORM = "FIXED_PLATFORM"

    @property
    def ormwo_label(self) -> str:
        """Canonical ORMWO schema label: JACKUP | DRILLSHIP | SEMI_SUB."""
        if self in (RigType.JACKUP, RigType.OFFSHORE_JACKUP, RigType.FIXED_PLATFORM, RigType.ONSHORE_LAND_RIG):
            return "JACKUP"
        if self in (RigType.DRILLSHIP, RigType.OFFSHORE_DRILLSHIP):
            return "DRILLSHIP"
        return "SEMI_SUB"


class RigOperationalStatus(str, Enum):
    """Operational status of a rig unit."""
    DRILLING = "DRILLING"
    COMPLETION = "COMPLETION"
    WORKOVER = "WORKOVER"
    STANDBY = "STANDBY"
    TRANSIT = "TRANSIT"
    MAINTENANCE = "MAINTENANCE"


class OperationalAlertState(str, Enum):
    """ORMWO assessment status levels."""
    NORMAL = "NORMAL"
    ADVISORY = "ADVISORY"
    CRITICAL_ACTION_REQUIRED = "CRITICAL_ACTION_REQUIRED"


class CycloneThreatLevel(str, Enum):
    """Metocean cyclone threat classification."""
    NONE = "NONE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"


class PrimaryThreatType(str, Enum):
    """Primary operational NPT risk driver."""
    WEATHER_CYCLONE = "WEATHER_CYCLONE"
    HIGH_SWELL = "HIGH_SWELL"
    EQUIPMENT_IDLE = "EQUIPMENT_IDLE"
    NONE = "NONE"


class OperationalDirectiveAction(str, Enum):
    """Deterministic directive actions under 48h advance cutoff."""
    CONTINUE_OPERATIONS = "CONTINUE_OPERATIONS"
    SUSPEND_AND_LATCH = "SUSPEND_AND_LATCH"
    INITIATE_PREVENTATIVE_TRANSIT = "INITIATE_PREVENTATIVE_TRANSIT"


class WellReadinessStatus(str, Enum):
    """Status of each candidate well among the 120+ India EEZ well locations."""
    ACTIVE_DRILLING = "ACTIVE_DRILLING"
    SAFE_READY_TO_SPUD = "SAFE_READY_TO_SPUD"
    STORM_LOCKED = "STORM_LOCKED"
    RECOMMENDED_TARGET = "RECOMMENDED_TARGET"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True)
class RigCoordinates:
    """Geographic position of a rig or well."""
    latitude: float
    longitude: float
    water_depth_m: float = 0.0
    basin_name: str = ""
    block_id: str = ""


@dataclass(frozen=True)
class WellPad:
    """Pinpoint coordinate and engineering metadata for one of India's 120+ candidate wells."""
    well_id: str
    well_name: str
    basin_name: str
    block_id: str
    latitude: float
    longitude: float
    water_depth_m: float
    target_depth_m: float
    required_rig_type: str              # 'JACKUP' | 'DRILLSHIP' | 'SEMI_SUB'
    priority_rank: int                  # 1 (Highest priority production) .. 100
    status: WellReadinessStatus = WellReadinessStatus.SAFE_READY_TO_SPUD
    assigned_rig_id: str | None = None
    peak_48h_hs_m: float = 1.1
    peak_48h_wind_kts: float = 16.0


@dataclass(frozen=True)
class RigTelemetry:
    """Live drilling and navigation telemetry metrics."""
    measured_depth_m: float
    rate_of_penetration_m_hr: float
    hook_load_klbs: float
    standpipe_pressure_psi: float
    rotary_rpm: float
    torque_kft_lbs: float
    gas_units_total: float
    active_mud_volume_bbl: float


@dataclass(frozen=True)
class RigUnit:
    """Full profile of an onshore/offshore rig."""
    rig_id: str
    rig_name: str
    operator: str
    rig_type: RigType
    status: RigOperationalStatus
    location: RigCoordinates
    current_well_name: str
    target_depth_m: float
    telemetry: RigTelemetry | None = None
    contract_expiry: str = ""
    daily_operating_cost_inr: float = 11200000.0  # Default ₹1.12 Crore/day
    planned_release_date: str = "2026-09-25T06:00:00Z"
    unlatch_lead_hours: int = 12


@dataclass(frozen=True)
class MarineWeatherPoint:
    """Single timestamp entry from get_marine_weather_forecast."""
    timestamp: str
    forecast_hour: int
    wind_speed_knots: float
    significant_wave_height_m: float
    swell_period_sec: float
    cyclone_threat_level: str           # 'NONE' | 'LOW' | 'MODERATE' | 'SEVERE'
    sea_state: int                      # 0 - 9 Douglas Sea Scale
    safe_for_operations: bool
    hs_p05_m: float = 0.0
    hs_p95_m: float = 0.0
    wind_p05_kts: float = 0.0
    wind_p95_kts: float = 0.0


@dataclass(frozen=True)
class MonteCarloTransitResult:
    """Result of run_monte_carlo_transit_simulation."""
    rig_id: str
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    destination_well_id: str
    recommended_departure_time: str
    expected_transit_hours: float
    transit_hours_p10: float
    transit_hours_p90: float
    probability_of_weather_standby: float
    estimated_npt_cost_inr: float
    static_weather_in_npt_loss_inr: float
    avoided_npt_savings_inr: float
    optimal_routing_waypoints: list[list[float]] = field(default_factory=list)


@dataclass(frozen=True)
class FleetSummary:
    """Consolidated overview of all monitored rigs, candidate wells, weather, and trajectories."""
    total_rigs: int
    active_drilling: int
    in_transit: int
    standby_maintenance: int
    rigs: list[RigUnit] = field(default_factory=list)
    selected_rig_id: str | None = None
    wells: list[WellPad] = field(default_factory=list)
    weather_series: list[MarineWeatherPoint] = field(default_factory=list)
    transit_simulations: list[MonteCarloTransitResult] = field(default_factory=list)
    active_storm_zones: list[dict[str, Any]] = field(default_factory=list)
    ormwo_json_report: dict[str, Any] | None = None
    audit_reference_id: str = ""


# ==============================================================================
# 2. A2UI Protocol Contracts
# ==============================================================================

class A2uiCatalogVersion(str, Enum):
    """Supported A2UI catalog schema versions."""
    V0_8 = "v0.8"
    V0_9 = "v0.9"


ACTIVE_A2UI_CATALOG_VERSION: A2uiCatalogVersion = A2uiCatalogVersion.V0_9


@dataclass(frozen=True)
class A2uiMessage:
    """In-memory representation of an individual A2UI lifecycle event."""
    message_type: str                   # 'createSurface', 'updateComponents', 'updateDataModel', 'deleteSurface'
    surface_id: str                     # Unique surface identifier per conversation turn
    payload: dict[str, Any]             # Message contents
    catalog_version: A2uiCatalogVersion = ACTIVE_A2UI_CATALOG_VERSION


# ==============================================================================
# 3. GCS Storage Inventory Contracts
# ==============================================================================

@dataclass(frozen=True)
class GcsObjectInfo:
    """Metadata for a single telemetry or well file observed in Cloud Storage."""
    name: str
    size_bytes: int
    content_type: str
    updated: str | None = None

    @property
    def size_kib(self) -> float:
        return self.size_bytes / 1024.0

    @property
    def basename(self) -> str:
        return self.name.rsplit("/", 1)[-1]


@dataclass(frozen=True)
class BucketInventory:
    """Result of scanning the agent's bucket for rig telemetry and logs."""
    bucket: str
    region: str
    files: list[GcsObjectInfo] = field(default_factory=list)
    ok: bool = True
    error: str | None = None

    @property
    def total_objects(self) -> int:
        return len(self.files)

    @property
    def total_bytes(self) -> int:
        return sum(o.size_bytes for o in self.files)
