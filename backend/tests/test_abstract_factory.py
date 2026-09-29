from domain.devices.family_factory import (
    EdgeDeviceFactory,
    SimulationDeviceFactory,
)


def test_simulation_factory_creates_four_devices():
    factory = SimulationDeviceFactory()

    devices = factory.create_device_set()

    assert len(devices) == 4
    assert all(device.device_family == "simulation" for device in devices)

    roles = {device.role for device in devices}

    assert roles == {"sensor", "actuator"}


def test_edge_factory_creates_four_devices():
    factory = EdgeDeviceFactory()

    devices = factory.create_device_set()

    assert len(devices) == 4
    assert all(device.device_family == "edge" for device in devices)

    roles = {device.role for device in devices}

    assert roles == {"sensor", "actuator"}


def test_edge_factory_differs_from_simulation_factory():
    simulation_devices = (
        SimulationDeviceFactory().create_device_set()
    )

    edge_devices = EdgeDeviceFactory().create_device_set()

    assert simulation_devices[0].device_family != (
        edge_devices[0].device_family
    )

    assert simulation_devices[0].default_config != (
        edge_devices[0].default_config
    )