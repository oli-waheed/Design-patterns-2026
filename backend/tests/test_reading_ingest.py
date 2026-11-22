from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

from application.readings.service import ReadingIngest
from domain.devices.entity import Device


def test_ingest_reads_mqtt_device_through_sensor_port():
    """ReadingIngest treats MQTT like every other adapter."""
    device_id = uuid4()

    device = Device(
        id=device_id,
        device_type="moisture_sensor",
        role="sensor",
        device_family="mqtt",
        display_name="MQTT Moisture Sensor",
        default_config={"protocol": "mqtt"},
    )

    device_repository = Mock()
    device_repository.get_device_by_id.return_value = device

    reading_repository = Mock()
    reading_repository.save.side_effect = lambda reading: reading

    ingest = ReadingIngest(
        device_repository=device_repository,
        reading_repository=reading_repository,
    )

    result = ingest.record(
        device_id,
        mqtt_payload={
            "value": 0.37,
            "unit": "vwc",
            "recorded_at": datetime(2026, 11, 22, tzinfo=timezone.utc),
        },
    )

    device_repository.get_device_by_id.assert_called_once_with(device_id)
    assert result.device_id == device_id
    assert result.value == 0.37
    assert result.source == "mqtt"
