from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from domain.actuators.ports import ActuatorPort


class Command(ABC):
    """Base interface for all actuator commands."""

    @abstractmethod
    def execute(
        self,
        port: ActuatorPort,
        device_id: UUID,
        payload: dict[str, Any],
    ) -> None:
        """Execute the command through an actuator port."""
        raise NotImplementedError
