from abc import ABC, abstractmethod

from domain.sensors.entity import Sensor


class SensorCreator(ABC):
    @abstractmethod
    def create_sensor(
        self,
        display_name: str | None = None,
    ) -> Sensor:
        pass


class MoistureSensorCreator(SensorCreator):
    def create_sensor(
        self,
        display_name: str | None = None,
    ) -> Sensor:
        return Sensor(
            id=None,
            device_type="moisture_sensor",
            display_name=display_name or "Moisture Sensor",
            default_config={
                "unit": "vwc",
                "sampling_interval_seconds": 300,
                "threshold": 30,
            },
        )


class LightSensorCreator(SensorCreator):
    def create_sensor(
        self,
        display_name: str | None = None,
    ) -> Sensor:
        return Sensor(
            id=None,
            device_type="light_sensor",
            display_name=display_name or "Light Sensor",
            default_config={
                "unit": "lux",
                "sampling_interval_seconds": 60,
                "threshold": 1000,
            },
        )


CREATORS: dict[str, SensorCreator] = {
    "moisture": MoistureSensorCreator(),
    "light": LightSensorCreator(),
}


def get_creator(sensor_type: str) -> SensorCreator:
    try:
        return CREATORS[sensor_type]
    except KeyError:
        raise ValueError(
            f"Unknown sensor type: {sensor_type}. "
            "Supported types: moisture, light."
        )