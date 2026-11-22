
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from domain.actuators.ports import ActuatorPort
from infrastructure.adapters.actuators.logging_decorator import (
    MaxRunTimeExceeded,
)
from infrastructure.persistence.device_repository import DeviceRepository


class MaxRunTimeActuatorDecorator(ActuatorPort):
    """Blocks commands when an actuator has run for 30 minutes or longer.

    Stop commands are always let through: they are how an over-running
    actuator is brought back to a safe state, so blocking them would
    leave it stuck in ``running``.
    """

    MAX_RUNTIME = timedelta(minutes=30)
    ALWAYS_ALLOWED_COMMANDS = frozenset({"stop_pump"})

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
        if command in self.ALWAYS_ALLOWED_COMMANDS:
            self._wrapped.apply(
                device_id=device_id,
                command=command,
                payload=payload,
            )
            return

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
