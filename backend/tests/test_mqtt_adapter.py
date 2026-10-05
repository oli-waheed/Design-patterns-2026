from uuid import uuid4

from infrastructure.adapters.sensors.mqtt import MqttSensorAdapter


def test_mqtt_sensor_adapter_translates_payload():
    device_id = uuid4()

    payload = {
        "value": 0.41,
        "unit": "vwc",
        "recorded_at": "2026-10-05T05:00:00+00:00",
    }

    adapter = MqttSensorAdapter(payload)

    reading = adapter.read(device_id)

    assert reading.device_id == device_id
    assert reading.value == 0.41
    assert reading.unit == "vwc"
    assert reading.source == "mqtt"
    assert reading.recorded_at.isoformat() == "2026-10-05T05:00:00+00:00"