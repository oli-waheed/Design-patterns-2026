
from typing import Any
from uuid import UUID

from application.actuators.allowed_commands import allowed_commands_for
from domain.devices.entity import Device
from domain.devices.family_factory import get_family_factory
from domain.actuators.context import ActuatorContext

from infrastructure.adapters.actuators.factory import (
    build_actuator_port,
)
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.execution_log_repository import (
    ExecutionLogRepository,
)


class DevicesService:
    def __init__(
        self,
        repository: DeviceRepository,
        execution_log_repository: ExecutionLogRepository | None = None,
    ):
        self._repository = repository
        self._execution_log_repository = execution_log_repository

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
            "allowed_commands": allowed_commands_for(device, context),
        }

    def execute_actuator_command(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any] | None = None,
    ) -> dict | None:
        device = self._repository.get_device_by_id(device_id)

        if device is None or device.role != "actuator":
            return None

        if self._execution_log_repository is None:
            raise RuntimeError(
                "Execution logging repository is not configured."
            )

        actuator = build_actuator_port(
            device_repository=self._repository,
            execution_log_repository=self._execution_log_repository,
        )

        actuator.apply(
            device_id=device_id,
            command=command,
            payload=payload or {},
        )

        return {
            "device_id": device_id,
            "command": command,
            "success": True,
        }
