
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from domain.actuators.ports import ActuatorPort
from infrastructure.adapters.actuators.logging_decorator import (
    MaxRunTimeExceeded,
)
from infrastructure.persistence.device_repository import DeviceRepository


class MaxRunTimeActuatorDecorator(ActuatorPort):
    """Blocks commands when an actuator has run for 30 minutes or longer."""

    MAX_RUNTIME = timedelta(minutes=30)

    def __init__(
        self,
        wrapped: ActuatorPort,
        device_repository: DeviceRepository,
    ) -> None:
        self._wrapped = wrapped
        self._device_repository = device_repository

    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        state_details = self._device_repository.get_actuator_state_details(
            device_id
        )

        if state_details is None:
            raise ValueError("Actuator state not found.")

        current_state = state_details["state"]
        updated_at = state_details["updated_at"]

        if current_state == "running":
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)

            runtime = datetime.now(timezone.utc) - updated_at

            if runtime >= self.MAX_RUNTIME:
                raise MaxRunTimeExceeded("Max run time exceeded")

        self._wrapped.apply(
            device_id=device_id,
            command=command,
            payload=payload,
        )
