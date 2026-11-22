from uuid import uuid4

import pytest

from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from infrastructure.adapters.sensors.mqtt import MqttSensorAdapter


def make_mqtt_device(device_id=None):
    return Device(
        id=device_id,
        device_type="moisture_sensor",
        role="sensor",
        device_family="mqtt",
        display_name="MQTT Moisture Sensor",
        default_config={
            "unit": "vwc",
            "protocol": "mqtt",
        },
    )


def test_mqtt_sensor_adapter_translates_payload():
    device_id = uuid4()

    payload = {
        "value": 0.41,
        "unit": "vwc",
        "recorded_at": "2026-10-05T05:00:00+00:00",
    }

    adapter = MqttSensorAdapter(payload)

    reading = adapter.read(make_mqtt_device(device_id))

    assert reading.device_id == device_id
    assert reading.value == 0.41
    assert reading.unit == "vwc"
    assert reading.source == "mqtt"
    assert reading.recorded_at.isoformat() == "2026-10-05T05:00:00+00:00"


def test_mqtt_sensor_adapter_implements_sensor_port():
    adapter = MqttSensorAdapter({"value": 0.41, "unit": "vwc"})

    assert isinstance(adapter, SensorPort)


def test_mqtt_sensor_adapter_requires_device_id():
    adapter = MqttSensorAdapter({"value": 0.41, "unit": "vwc"})

    with pytest.raises(ValueError, match="without an id"):
        adapter.read(make_mqtt_device(device_id=None))


def test_mqtt_sensor_adapter_rejects_missing_field():
    adapter = MqttSensorAdapter({"unit": "vwc"})

    with pytest.raises(ValueError, match="Missing MQTT payload field: value"):
        adapter.read(make_mqtt_device(uuid4()))
