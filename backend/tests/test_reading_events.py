from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

from application.readings.service import ReadingIngest
from domain.devices.entity import Device
from domain.events.bus import EventBus
from domain.events.events import ReadingCreated
from domain.sensors.reading import Reading


def make_ingest(tracking_enabled, zone_id=None, location_id=None):
    device_id = uuid4()

    device = Device(
        id=device_id,
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name="Moisture",
        default_config={"protocol": "simulation"},
        zone_id=zone_id,
        location_id=location_id,
        tracking_enabled=tracking_enabled,
    )

    device_repository = Mock()
    device_repository.get_device_by_id.return_value = device

    reading_repository = Mock()
    reading_repository.save.side_effect = lambda reading: reading

    bus = EventBus()
    published = []
    bus.subscribe(ReadingCreated, published.append)

    ingest = ReadingIngest(
        device_repository=device_repository,
        reading_repository=reading_repository,
        event_bus=bus,
    )

    return ingest, device, reading_repository, published


def test_tracking_on_publishes_reading_created_with_device_ids():
    zone_id = uuid4()
    location_id = uuid4()
    ingest, device, reading_repository, published = make_ingest(
        tracking_enabled=True,
        zone_id=zone_id,
        location_id=location_id,
    )

    ingest.record(device.id)

    reading_repository.save.assert_called_once()
    assert len(published) == 1

    event = published[0]
    assert event.device_id == device.id
    assert event.unit == "vwc"
    assert event.source == "simulation"
    assert event.zone_id == zone_id
    assert event.location_id == location_id


def test_tracking_off_stores_reading_but_does_not_publish():
    ingest, device, reading_repository, published = make_ingest(
        tracking_enabled=False,
    )

    ingest.record(device.id)

    reading_repository.save.assert_called_once()
    assert published == []


def test_translated_mqtt_reading_uses_same_publish_rule():
    ingest, device, _, published = make_ingest(tracking_enabled=True)

    ingest.record_reading(
        Reading(
            device_id=device.id,
            value=0.33,
            unit="vwc",
            source="mqtt",
            recorded_at=datetime.now(timezone.utc),
        )
    )

    assert len(published) == 1
    assert published[0].source == "mqtt"


def test_unassigned_device_publishes_null_ids():
    ingest, device, _, published = make_ingest(tracking_enabled=True)

    ingest.record(device.id)

    assert published[0].zone_id is None
    assert published[0].location_id is None
