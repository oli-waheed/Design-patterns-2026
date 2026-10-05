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

        devices = self._device_repository.list_devices()

        device = next(
            (
                item
                for item in devices
                if item.id == device_id
            ),
            None,
        )

        if device is None:
            raise ValueError("Device not found.")

        adapter = SensorAdapterSelector.select(
            device=device,
            vendor_payload=vendor_payload,
            mqtt_payload=mqtt_payload,
        )

        if device.default_config.get("protocol", "simulation") == "mqtt":
            if device.id is None:
                raise ValueError("Device has no id.")

            reading = adapter.read(device.id)
        else:
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