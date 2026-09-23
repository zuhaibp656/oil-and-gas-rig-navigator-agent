"""Unit tests for domain contracts."""

from app.contracts import (
    FleetSummary,
    RigCoordinates,
    RigOperationalStatus,
    RigTelemetry,
    RigType,
    RigUnit,
)


def test_rig_unit_instantiation():
    coords = RigCoordinates(latitude=19.25, longitude=71.85, basin_name="Mumbai High")
    tel = RigTelemetry(
        measured_depth_m=3000.0,
        rate_of_penetration_m_hr=15.0,
        hook_load_klbs=350.0,
        standpipe_pressure_psi=3200.0,
        rotary_rpm=100.0,
        torque_kft_lbs=18.0,
        gas_units_total=40.0,
        active_mud_volume_bbl=1100.0,
    )
    rig = RigUnit(
        rig_id="RIG-TEST-01",
        rig_name="Test Rig",
        operator="ONGC",
        rig_type=RigType.OFFSHORE_DRILLSHIP,
        status=RigOperationalStatus.DRILLING,
        location=coords,
        current_well_name="TEST-1",
        target_depth_m=3500.0,
        telemetry=tel,
    )
    assert rig.rig_name == "Test Rig"
    assert rig.status == RigOperationalStatus.DRILLING
    assert rig.location.latitude == 19.25


def test_fleet_summary_creation():
    summary = FleetSummary(
        total_rigs=5,
        active_drilling=3,
        in_transit=1,
        standby_maintenance=1,
    )
    assert summary.total_rigs == 5
    assert summary.active_drilling == 3
