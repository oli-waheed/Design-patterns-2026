from uuid import uuid4

import pytest

from domain.devices.entity import Device
from infrastructure.adapters.sensors.vendor_stub import VendorSensorAdapter


def test_vendor_sensor_adapter_translates_payload():
    device_id = uuid4()

    device = Device(
        id=device_id,
        device_type="moisture_sensor",
        role="sensor",
        device_family="vendor",
        display_name="Vendor Moisture Sensor",
        default_config={
            "unit": "vwc",
            "protocol": "vendor_stub",
        },
    )

    payload = {
        "sensorId": str(device_id),
        "readingValue": 0.42,
        "measurementUnit": "vwc",
        "time": "2026-10-05T05:00:00+00:00",
    }

    adapter = VendorSensorAdapter(payload)

    reading = adapter.read(device)

    assert reading.device_id == device_id
    assert reading.value == 0.42
    assert reading.unit == "vwc"
    assert reading.source == "vendor"

def make_vendor_device(device_id):
    return Device(
        id=device_id,
        device_type="moisture_sensor",
        role="sensor",
        device_family="vendor",
        display_name="Vendor Moisture Sensor",
        default_config={
            "unit": "vwc",
            "protocol": "vendor_stub",
        },
    )


def test_vendor_sensor_adapter_rejects_payload_for_other_device():
    """A payload for another sensor must not be saved under this one."""
    device = make_vendor_device(uuid4())

    payload = {
        "sensorId": str(uuid4()),
        "readingValue": 0.42,
        "measurementUnit": "vwc",
    }

    adapter = VendorSensorAdapter(payload)

    with pytest.raises(ValueError, match="does not match"):
        adapter.read(device)


def test_vendor_sensor_adapter_rejects_invalid_sensor_id():
    device = make_vendor_device(uuid4())

    payload = {
        "sensorId": "not-a-uuid",
        "readingValue": 0.42,
        "measurementUnit": "vwc",
    }

    adapter = VendorSensorAdapter(payload)

    with pytest.raises(ValueError, match="Invalid vendor sensorId"):
        adapter.read(device)
