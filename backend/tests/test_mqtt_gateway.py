"""Optional MQTT path, tested without a broker."""

import json
from unittest.mock import Mock
from uuid import uuid4

from application.devices.service import DevicesService
from domain.devices.entity import Device
from domain.events.bus import EventBus
from domain.events.events import ReadingCreated
from infrastructure.adapters.sensors.mqtt import MqttSensorAdapter
from infrastructure.db import SessionLocal
from infrastructure.mqtt.subscriber import handle_reading_message
from infrastructure.mqtt.topics import (
    config_topic,
    device_id_from_reading_topic,
    reading_topic,
)
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository


def create_mqtt_sensor():
    db = SessionLocal()
    try:
        device = DeviceRepository(db).save_device(
            Device(
                id=None,
                device_type="moisture_sensor",
                role="sensor",
                device_family="edge",
                display_name="MQTT Moisture",
                default_config={"unit": "vwc", "protocol": "mqtt"},
            )
        )
        return device.id
    finally:
        db.close()


def capture_bus():
    bus = EventBus()
    published = []
    bus.subscribe(ReadingCreated, published.append)
    return bus, published


def test_translator_defaults_to_mqtt_and_accepts_http_source():
    device = Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="edge",
        display_name="x",
        default_config={},
    )
    payload = {"value": 0.4, "unit": "vwc"}

    assert MqttSensorAdapter(payload).read(device).source == "mqtt"
    assert MqttSensorAdapter(payload, source="http").read(device).source == "http"


def test_topics_round_trip():
    device_id = uuid4()

    assert reading_topic(device_id) == f"greenhouse/devices/{device_id}/reading"
    assert config_topic(device_id) == f"greenhouse/devices/{device_id}/config"
    assert device_id_from_reading_topic(reading_topic(device_id)) == device_id
    assert device_id_from_reading_topic("greenhouse/devices/nope/reading") is None
    assert device_id_from_reading_topic(f"other/devices/{device_id}/reading") is None


def test_broker_message_goes_through_ingest():
    device_id = create_mqtt_sensor()
    bus, published = capture_bus()

    stored = handle_reading_message(
        topic=reading_topic(device_id),
        payload=json.dumps({"value": 0.37, "unit": "vwc"}).encode(),
        session_factory=SessionLocal,
        event_bus=bus,
    )

    assert stored is True
    assert len(published) == 1
    assert published[0].source == "mqtt"

    db = SessionLocal()
    try:
        rows = ReadingRepository(db).list_recent(device_id=device_id, limit=5)
    finally:
        db.close()

    assert [(row.value, row.source) for row in rows] == [(0.37, "mqtt")]


def test_unknown_device_and_bad_payloads_are_dropped():
    bus, published = capture_bus()

    unknown = handle_reading_message(
        topic=reading_topic(uuid4()),
        payload=b'{"value": 0.5, "unit": "vwc"}',
        session_factory=SessionLocal,
        event_bus=bus,
    )
    bad_json = handle_reading_message(
        topic=reading_topic(create_mqtt_sensor()),
        payload=b"not json",
        session_factory=SessionLocal,
        event_bus=bus,
    )
    bad_topic = handle_reading_message(
        topic="greenhouse/devices/abc/reading",
        payload=b'{"value": 0.5, "unit": "vwc"}',
        session_factory=SessionLocal,
        event_bus=bus,
    )

    assert (unknown, bad_json, bad_topic) == (False, False, False)
    assert published == []


def make_device(protocol):
    return Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="edge",
        display_name="x",
        default_config={"protocol": protocol},
        sampling_interval_seconds=30,
        tracking_enabled=True,
    )


def test_sampling_patch_publishes_retained_config_only_for_mqtt():
    for protocol, expected_calls in [("mqtt", 1), ("http", 0), ("simulation", 0)]:
        device = make_device(protocol)
        repository = Mock()
        repository.update_sampling.return_value = device
        publisher = Mock()

        DevicesService(repository, config_publisher=publisher).update_sampling(
            device_id=device.id,
            sampling_interval_seconds=30,
            tracking_enabled=True,
        )

        assert publisher.publish_sampling_config.call_count == expected_calls

        if expected_calls:
            publisher.publish_sampling_config.assert_called_once_with(
                device_id=device.id,
                sampling_interval_seconds=30,
                tracking_enabled=True,
            )


def test_sampling_patch_without_broker_does_not_fail():
    device = make_device("mqtt")
    repository = Mock()
    repository.update_sampling.return_value = device

    result = DevicesService(repository, config_publisher=None).update_sampling(
        device_id=device.id,
        sampling_interval_seconds=30,
        tracking_enabled=True,
    )

    assert result is device


def test_no_gateway_is_built_without_broker_url():
    import composition

    assert composition.mqtt_gateway is None
    assert composition.get_sampling_config_publisher() is None
