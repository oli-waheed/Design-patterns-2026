from uuid import uuid4

from domain.devices.entity import Device
from infrastructure.adapters.sensors.simulation import (
    SimulationSensorAdapter,
)


def test_simulation_sensor_adapter_reads_moisture_sensor():
    device = Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name="Test Moisture Sensor",
        default_config={
            "unit": "vwc",
            "protocol": "simulation",
        },
    )

    adapter = SimulationSensorAdapter()

    reading = adapter.read(device)

    assert reading.device_id == device.id
    assert reading.unit == "vwc"
    assert reading.source == "simulation"
    assert 0.2 <= reading.value <= 0.6


def test_simulation_sensor_adapter_reads_light_sensor():
    device = Device(
        id=uuid4(),
        device_type="light_sensor",
        role="sensor",
        device_family="simulation",
        display_name="Test Light Sensor",
        default_config={
            "unit": "lux",
            "protocol": "simulation",
        },
    )

    adapter = SimulationSensorAdapter()

    reading = adapter.read(device)

    assert reading.device_id == device.id
    assert reading.unit == "lux"
    assert reading.source == "simulation"
    assert 200.0 <= reading.value <= 2000.0