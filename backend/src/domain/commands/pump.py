from typing import Any
from uuid import UUID

from domain.actuators.ports import ActuatorPort
from domain.commands.base import Command


class StartPumpCommand(Command):
    """Command to start a water pump."""

    def execute(
        self,
        port: ActuatorPort,
        device_id: UUID,
        payload: dict[str, Any],
    ) -> None:
        port.apply(
            device_id=device_id,
            command="start_pump",
            payload=payload,
        )


class StopPumpCommand(Command):
    """Command to stop a water pump."""

    def execute(
        self,
        port: ActuatorPort,
        device_id: UUID,
        payload: dict[str, Any],
    ) -> None:
        port.apply(
            device_id=device_id,
            command="stop_pump",
            payload=payload,
        )
