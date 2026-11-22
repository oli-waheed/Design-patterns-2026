"""Facade (Phase 7) unit test with fakes: OverviewFacade assembles one DTO
from several collaborators, without a database."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from application.overview.facade import OverviewFacade


def make_facade(strategy_key="aggressive"):
    location_id = uuid4()
    zone_a, zone_b = uuid4(), uuid4()
    sensor_id, pump_id, unassigned_id = uuid4(), uuid4(), uuid4()

    overview_repository = Mock()
    overview_repository.get_location.return_value = SimpleNamespace(
        id=location_id, name="Greenhouse A"
    )
    overview_repository.list_zones.return_value = [
        SimpleNamespace(
            id=zone_a, name="Bench 1",
            moisture_threshold_low=0.2, moisture_threshold_high=0.6,
        ),
        SimpleNamespace(
            id=zone_b, name="Bench 2",
            moisture_threshold_low=0.3, moisture_threshold_high=0.7,
        ),
    ]
    overview_repository.list_assigned_devices.return_value = [
        SimpleNamespace(
            id=sensor_id, device_type="moisture_sensor", role="sensor",
            display_name="Moisture", zone_id=zone_a,
            tracking_enabled=True, sampling_interval_seconds=5,
        ),
        SimpleNamespace(
            id=pump_id, device_type="water_pump", role="actuator",
            display_name="Pump", zone_id=zone_a,
            tracking_enabled=True, sampling_interval_seconds=300,
        ),
        # Assigned to the location but to no known zone: counted, not listed.
        SimpleNamespace(
            id=unassigned_id, device_type="light_sensor", role="sensor",
            display_name="Light", zone_id=None,
            tracking_enabled=True, sampling_interval_seconds=60,
        ),
    ]
    overview_repository.get_latest_readings.return_value = [
        SimpleNamespace(
            device_id=sensor_id, value=0.42, unit="vwc",
            recorded_at=datetime.now(timezone.utc),
        )
    ]

    automation_repository = Mock()
    automation_repository.get_strategy_key.return_value = strategy_key

    automation_service = Mock()
    automation_service.evaluate.return_value = {
        "location_id": str(location_id),
        "strategy_key": strategy_key,
        "recommendations": [],
    }

    facade = OverviewFacade(
        overview_repository=overview_repository,
        automation_service=automation_service,
        automation_repository=automation_repository,
    )

    ids = SimpleNamespace(
        location=location_id, zone_a=zone_a, zone_b=zone_b, sensor=sensor_id
    )
    return facade, ids, overview_repository, automation_service


def test_overview_assembles_location_counts_zones_and_readings():
    facade, ids, _, _ = make_facade()

    overview = facade.get_overview(ids.location)

    assert overview.location.name == "Greenhouse A"
    assert (overview.device_counts.sensor, overview.device_counts.actuator) == (2, 1)
    assert [zone.name for zone in overview.zones] == ["Bench 1", "Bench 2"]

    bench_1, bench_2 = overview.zones
    assert {device.display_name for device in bench_1.devices} == {"Moisture", "Pump"}
    assert [reading.value for reading in bench_1.latest_readings] == [0.42]
    assert bench_2.devices == [] and bench_2.latest_readings == []
    assert overview.strategy_key == "aggressive"


def test_latest_readings_are_fetched_in_one_call():
    facade, ids, overview_repository, _ = make_facade()

    facade.get_overview(ids.location)

    # One batched query for all devices, not one per device (no N+1).
    overview_repository.get_latest_readings.assert_called_once()


def test_recommendation_only_when_a_strategy_is_saved():
    facade, ids, _, automation_service = make_facade(strategy_key=None)

    overview = facade.get_overview(ids.location)

    assert overview.strategy_key is None
    assert overview.last_recommendation is None
    automation_service.evaluate.assert_not_called()


def test_missing_location_raises_lookup_error():
    facade, _, overview_repository, _ = make_facade()
    overview_repository.get_location.return_value = None

    with pytest.raises(LookupError):
        facade.get_overview(uuid4())
