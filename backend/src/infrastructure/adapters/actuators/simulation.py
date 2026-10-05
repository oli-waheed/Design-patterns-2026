from typing import Any
from uuid import UUID

from domain.actuators.ports import ActuatorPort


class SimulationActuatorAdapter(ActuatorPort):
    """Simulation actuator that records commands in memory."""

    def __init__(self) -> None:
        self.commands: list[dict[str, Any]] = []

    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        self.commands.append(
            {
                "device_id": device_id,
                "command": command,
                "payload": payload,
            }
        )