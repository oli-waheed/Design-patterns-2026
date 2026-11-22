from uuid import UUID

from application.readings.dto import ReadingDto
from domain.sensors.reading import Reading
from infrastructure.adapters.sensors.selector import SensorAdapterSelector
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository


class ReadingIngest:
    def __init__(
        self,
        device_repository: DeviceRepository,
        reading_repository: ReadingRepository,
    ):
        self._device_repository = device_repository
        self._reading_repository = reading_repository

    def record(
        self,
        device_id: UUID,
        vendor_payload: dict | None = None,
        mqtt_payload: dict | None = None,
    ) -> ReadingDto:

        device = self._device_repository.get_device_by_id(device_id)

        if device is None:
            raise ValueError("Device not found.")

        adapter = SensorAdapterSelector.select(
            device=device,
            vendor_payload=vendor_payload,
            mqtt_payload=mqtt_payload,
        )

        # Every adapter implements SensorPort, so no protocol checks here.
        reading = adapter.read(device)

        saved_reading = self._reading_repository.save(reading)

        return ReadingDto.from_reading(saved_reading)

    def record_reading(
        self,
        reading: Reading,
    ) -> ReadingDto:
        saved_reading = self._reading_repository.save(
            reading
        )

        return ReadingDto.from_reading(saved_reading)