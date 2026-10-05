from abc import ABC, abstractmethod

from domain.devices.entity import Device
from domain.sensors.reading import Reading


class SensorPort(ABC):
    @abstractmethod
    def read(self, device: Device) -> Reading:
        """Read a sensor and return a normalized Reading."""
        raise NotImplementedError