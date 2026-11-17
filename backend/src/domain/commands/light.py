from typing import Any
from uuid import UUID

from domain.actuators.ports import ActuatorPort
from domain.commands.base import Command


class SetLightLevelCommand(Command):
    """Command to change the grow light level."""

    def execute(
        self,
        port: ActuatorPort,
        device_id: UUID,
        payload: dict[str, Any],
    ) -> None:
        port.apply(
            device_id=device_id,
            command="set_light_level",
            payload=payload,
        )
