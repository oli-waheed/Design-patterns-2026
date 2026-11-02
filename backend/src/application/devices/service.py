
from uuid import UUID

from domain.devices.entity import Device
from domain.devices.family_factory import get_family_factory
from domain.actuators.context import ActuatorContext
from domain.actuators.state import ActuatorState
from infrastructure.persistence.device_repository import DeviceRepository


class DevicesService:
    def __init__(
        self,
        repository: DeviceRepository,
    ):
        self._repository = repository

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
        return self._repository.update_sampling(
            device_id=device_id,
            sampling_interval_seconds=sampling_interval_seconds,
            tracking_enabled=tracking_enabled,
        )

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
            "allowed_commands": context.allowed_commands(),
        }

    def transition_actuator(
        self,
        device_id: UUID,
        target: ActuatorState | str,
    ) -> dict | None:
        device = self._repository.get_device_by_id(device_id)

        if device is None or device.role != "actuator":
            return None

        current_state = self._repository.get_actuator_state(device_id)

        if current_state is None:
            return None

        context = ActuatorContext(current_state)

        # The domain context validates the requested transition.
        context.transition(target)

        # Update the database only after successful validation.
        self._repository.update_actuator_state(
            device_id=device_id,
            state=context.state.value,
        )

        return {
            "device_id": device_id,
            "state": context.state.value,
            "allowed_commands": context.allowed_commands(),
        }
