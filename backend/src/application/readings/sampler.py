from datetime import datetime, timezone

from application.readings.service import ReadingIngest
from domain.events.bus import EventBus
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository


class SimulationSampler:
    def __init__(
        self,
        device_repository: DeviceRepository,
        reading_repository: ReadingRepository,
        event_bus: EventBus | None = None,
    ) -> None:
        self._device_repository = device_repository
        self._reading_repository = reading_repository
        self._ingest = ReadingIngest(
            device_repository=device_repository,
            reading_repository=reading_repository,
            event_bus=event_bus,
        )

    def sample_once(
        self,
        now: datetime | None = None,
    ) -> int:
        if now is None:
            now = datetime.now(timezone.utc)

        sampled_count = 0

        devices = self._device_repository.list_devices(
            device_family="simulation",
            role="sensor",
        )

        for device in devices:
            if device.id is None:
                continue

            if not device.tracking_enabled:
                continue

            # HTTP and MQTT devices push their own readings on their own
            # clock; the sampler only drives simulation devices.
            protocol = device.default_config.get("protocol", "simulation")

            if protocol != "simulation":
                continue

            last_readings = self._reading_repository.list_recent(
                device_id=device.id,
                limit=1,
            )

            if last_readings:
                last_recorded_at = last_readings[0].recorded_at

                elapsed_seconds = (
                    now - last_recorded_at
                ).total_seconds()

                if elapsed_seconds < device.sampling_interval_seconds:
                    continue

            self._ingest.record(device.id)
            sampled_count += 1

        return sampled_count