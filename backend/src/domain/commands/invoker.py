from typing import Any
from uuid import UUID

from domain.actuators.ports import ActuatorPort
from domain.commands.base import Command
from domain.commands.light import SetLightLevelCommand
from domain.commands.pump import (
    StartPumpCommand,
    StopPumpCommand,
)


class CommandRegistry:
    """Maps command names to their concrete command classes."""

    def __init__(self) -> None:
        self._commands: dict[str, type[Command]] = {
            "start_pump": StartPumpCommand,
            "stop_pump": StopPumpCommand,
            "set_light_level": SetLightLevelCommand,
        }

    def create(self, command_type: str) -> Command:
        command_class = self._commands.get(command_type)

        if command_class is None:
            raise ValueError(
                f"Unknown command type: {command_type}"
            )

        return command_class()

    def supports(self, command_type: str) -> bool:
        return command_type in self._commands


class CommandInvoker:
    """Executes commands without knowing their concrete types."""

    def execute(
        self,
        command: Command,
        port: ActuatorPort,
        device_id: UUID,
        payload: dict[str, Any],
    ) -> None:
        command.execute(
            port=port,
            device_id=device_id,
            payload=payload,
        )
