from uuid import UUID

from application.readings.dto import ReadingDto
from domain.devices.entity import Device
from domain.events.bus import EventBus
from domain.events.events import ReadingCreated
from domain.sensors.reading import Reading
from infrastructure.adapters.sensors.selector import SensorAdapterSelector
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository


class ReadingIngest:
    """Single writer of sensor_readings and single publisher of
    reading.created, shared by manual reads, the sampler and MQTT."""

    def __init__(
        self,
        device_repository: DeviceRepository,
        reading_repository: ReadingRepository,
        event_bus: EventBus | None = None,
    ):
        self._device_repository = device_repository
        self._reading_repository = reading_repository
        self._event_bus = event_bus

    def record(
        self,
        device_id: UUID,
        vendor_payload: dict | None = None,
        mqtt_payload: dict | None = None,
    ) -> ReadingDto:

        device = self._get_device(device_id)

        adapter = SensorAdapterSelector.select(
            device=device,
            vendor_payload=vendor_payload,
            mqtt_payload=mqtt_payload,
        )

        # Every adapter implements SensorPort, so no protocol checks here.
        reading = adapter.read(device)

        return self._store_and_publish(device, reading)

    def record_reading(
        self,
        reading: Reading,
    ) -> ReadingDto:
        device = self._get_device(reading.device_id)

        return self._store_and_publish(device, reading)

    def _get_device(self, device_id: UUID) -> Device:
        device = self._device_repository.get_device_by_id(device_id)

        if device is None:
            raise ValueError("Device not found.")

        return device

    def _store_and_publish(
        self,
        device: Device,
        reading: Reading,
    ) -> ReadingDto:
        saved_reading = self._reading_repository.save(reading)

        # The row is always stored; the event is only published while
        # tracking is enabled for this device.
        if self._event_bus is not None and device.tracking_enabled:
            self._event_bus.publish(
                ReadingCreated(
                    device_id=saved_reading.device_id,
                    value=saved_reading.value,
                    unit=saved_reading.unit,
                    source=saved_reading.source,
                    recorded_at=saved_reading.recorded_at,
                    location_id=device.location_id,
                    zone_id=device.zone_id,
                )
            )

        return ReadingDto.from_reading(saved_reading)
