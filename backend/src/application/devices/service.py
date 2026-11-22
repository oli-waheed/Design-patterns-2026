from typing import Protocol
from uuid import UUID

from application.actuators.allowed_commands import allowed_commands_for
from domain.actuators.context import ActuatorContext
from domain.devices.entity import Device
from domain.devices.family_factory import get_family_factory
from infrastructure.persistence.device_repository import DeviceRepository


class SamplingConfigPublisher(Protocol):
    """Pushes sampling settings to devices that cannot ask for them.

    Phase 12: only MQTT devices use this, through a retained message.
    HTTP devices read the same values with GET .../sampling instead.
    """

    def publish_sampling_config(
        self,
        device_id: UUID,
        sampling_interval_seconds: int,
        tracking_enabled: bool,
    ) -> None:
        ...


class DevicesService:
    def __init__(
        self,
        repository: DeviceRepository,
        config_publisher: SamplingConfigPublisher | None = None,
    ):
        self._repository = repository
        self._config_publisher = config_publisher

    def get_device(self, device_id: UUID) -> Device | None:
        return self._repository.get_device_by_id(device_id)

    def provision_family(
        self,
        family: str,
    ) -> list[Device]:
        factory = get_family_factory(family)
        devices = factory.create_device_set()
        return self._repository.save_devices(devices)

    def list_devices(
        self,
        device_family: str | None = None,
        role: str | None = None,
    ) -> list[Device]:
        return self._repository.list_devices(
            device_family=device_family,
            role=role,
        )

    def assign_zone(
        self,
        device_id: UUID,
        zone_id: UUID | None,
    ) -> bool:
        return self._repository.assign_zone(
            device_id=device_id,
            zone_id=zone_id,
        )

    def update_sampling(
        self,
        device_id: UUID,
        sampling_interval_seconds: int,
        tracking_enabled: bool,
    ) -> Device | None:
        device = self._repository.update_sampling(
            device_id=device_id,
            sampling_interval_seconds=sampling_interval_seconds,
            tracking_enabled=tracking_enabled,
        )

        # HTTP devices read these columns with GET .../sampling, so nothing
        # is pushed. MQTT devices get a retained config message, but only
        # when a broker is configured.
        if (
            device is not None
            and device.default_config.get("protocol") == "mqtt"
            and self._config_publisher is not None
        ):
            self._config_publisher.publish_sampling_config(
                device_id=device.id,
                sampling_interval_seconds=device.sampling_interval_seconds,
                tracking_enabled=device.tracking_enabled,
            )

        return device

    def list_devices_in_zone(
        self,
        location_id: UUID,
        zone_id: UUID,
    ) -> list[Device]:
        return self._repository.list_devices_in_zone(
            location_id=location_id,
            zone_id=zone_id,
        )

    def get_actuator_state(self, device_id: UUID) -> dict | None:
        device = self._repository.get_device_by_id(device_id)

        if device is None or device.role != "actuator":
            return None

        current_state = self._repository.get_actuator_state(device_id)

        if current_state is None:
            return None

        context = ActuatorContext(current_state)

        return {
            "device_id": device_id,
            "state": context.state.value,
            "allowed_commands": allowed_commands_for(device, context),
        }
