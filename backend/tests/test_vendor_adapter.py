from uuid import uuid4

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