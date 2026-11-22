from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

from application.readings.sampler import SimulationSampler
from domain.devices.entity import Device


def make_sensor(protocol):
    return Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name=protocol,
        default_config={"protocol": protocol},
        sampling_interval_seconds=5,
        tracking_enabled=True,
    )


def test_sampler_only_samples_simulation_protocol(monkeypatch):
    devices = [make_sensor("simulation"), make_sensor("http"), make_sensor("mqtt")]

    device_repository = Mock()
    device_repository.list_devices.return_value = devices
    reading_repository = Mock()
    reading_repository.list_recent.return_value = []

    sampler = SimulationSampler(device_repository, reading_repository)
    recorded = []
    monkeypatch.setattr(sampler._ingest, "record", recorded.append)

    count = sampler.sample_once(now=datetime.now(timezone.utc))

    assert count == 1
    assert recorded == [devices[0].id]
