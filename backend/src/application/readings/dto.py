from datetime import datetime
from uuid import UUID

from domain.sensors.reading import Reading


class ReadingDto:
    def __init__(
        self,
        device_id: UUID,
        value: float,
        unit: str,
        source: str,
        recorded_at: datetime,
    ):
        self.device_id = device_id
        self.value = value
        self.unit = unit
        self.source = source
        self.recorded_at = recorded_at

    @classmethod
    def from_reading(cls, reading: Reading) -> "ReadingDto":
        return cls(
            device_id=reading.device_id,
            value=reading.value,
            unit=reading.unit,
            source=reading.source,
            recorded_at=reading.recorded_at,
        )