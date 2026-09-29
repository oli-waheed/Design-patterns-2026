from abc import ABC, abstractmethod

from domain.devices.entity import Device
from domain.sensors.creators import get_creator


class DeviceFamilyFactory(ABC):
    @property
    @abstractmethod
    def family_key(self) -> str:
        pass

    @abstractmethod
    def create_device_set(self) -> list[Device]:
        pass


class SimulationDeviceFactory(DeviceFamilyFactory):
    @property
    def family_key(self) -> str:
        return "simulation"

    def create_device_set(self) -> list[Device]:
        moisture_sensor = get_creator("moisture").create_sensor(
            display_name="Simulation Moisture Sensor"
        )

        light_sensor = get_creator("light").create_sensor(
            display_name="Simulation Light Sensor"
        )

        devices = [
            Device(
                id=moisture_sensor.id,
                device_type=moisture_sensor.device_type,
                role="sensor",
                device_family=self.family_key,
                display_name=moisture_sensor.display_name,
                default_config={
                    **moisture_sensor.default_config,
                    "protocol": "simulation",
                },
            ),
            Device(
                id=light_sensor.id,
                device_type=light_sensor.device_type,
                role="sensor",
                device_family=self.family_key,
                display_name=light_sensor.display_name,
                default_config={
                    **light_sensor.default_config,
                    "protocol": "simulation",
                },
            ),
            Device(
                id=None,
                device_type="water_pump",
                role="actuator",
                device_family=self.family_key,
                display_name="Simulation Water Pump",
                default_config={
                    "protocol": "simulation",
                    "power": "low",
                    "default_state": "off",
                },
            ),
            Device(
                id=None,
                device_type="grow_light",
                role="actuator",
                device_family=self.family_key,
                display_name="Simulation Grow Light",
                default_config={
                    "protocol": "simulation",
                    "power": "medium",
                    "default_state": "off",
                },
            ),
        ]

        return devices


class EdgeDeviceFactory(DeviceFamilyFactory):
    @property
    def family_key(self) -> str:
        return "edge"

    def create_device_set(self) -> list[Device]:
        moisture_sensor = get_creator("moisture").create_sensor(
            display_name="Edge Moisture Sensor"
        )

        light_sensor = get_creator("light").create_sensor(
            display_name="Edge Light Sensor"
        )

        devices = [
            Device(
                id=moisture_sensor.id,
                device_type=moisture_sensor.device_type,
                role="sensor",
                device_family=self.family_key,
                display_name=moisture_sensor.display_name,
                default_config={
                    **moisture_sensor.default_config,
                    "protocol": "gpio",
                    "pin": 34,
                },
            ),
            Device(
                id=light_sensor.id,
                device_type=light_sensor.device_type,
                role="sensor",
                device_family=self.family_key,
                display_name=light_sensor.display_name,
                default_config={
                    **light_sensor.default_config,
                    "protocol": "i2c",
                    "address": "0x23",
                },
            ),
            Device(
                id=None,
                device_type="water_pump",
                role="actuator",
                device_family=self.family_key,
                display_name="Edge Water Pump",
                default_config={
                    "protocol": "gpio",
                    "pin": 25,
                    "default_state": "off",
                },
            ),
            Device(
                id=None,
                device_type="grow_light",
                role="actuator",
                device_family=self.family_key,
                display_name="Edge Grow Light",
                default_config={
                    "protocol": "gpio",
                    "pin": 26,
                    "default_state": "off",
                },
            ),
        ]

        return devices


FACTORIES: dict[str, DeviceFamilyFactory] = {
    "simulation": SimulationDeviceFactory(),
    "edge": EdgeDeviceFactory(),
}


def get_family_factory(family: str) -> DeviceFamilyFactory:
    try:
        return FACTORIES[family]
    except KeyError:
        raise ValueError(
            f"Unknown device family: {family}. "
            "Supported families: simulation, edge."
        )