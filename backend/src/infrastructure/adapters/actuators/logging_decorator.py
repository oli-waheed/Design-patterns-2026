
from typing import Any
from uuid import UUID

from domain.actuators.ports import ActuatorPort
from infrastructure.persistence.execution_log_repository import (
    ExecutionLogRepository,
)


class MaxRunTimeExceeded(Exception):
    """Raised when an actuator exceeds its permitted runtime."""

    pass


class LoggingActuatorDecorator(ActuatorPort):
    """Decorator that persists actuator execution attempts."""

    def __init__(
        self,
        wrapped: ActuatorPort,
        execution_log_repository: ExecutionLogRepository,
    ) -> None:
        self._wrapped = wrapped
        self._execution_log_repository = execution_log_repository

    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        try:
            self._wrapped.apply(
                device_id=device_id,
                command=command,
                payload=payload,
            )

        except MaxRunTimeExceeded as exc:
            self._execution_log_repository.save(
                device_id=device_id,
                success=False,
                policy_applied=["maxRunTime", "logging"],
                message=str(exc),
            )
            raise

        except Exception as exc:
            self._execution_log_repository.save(
                device_id=device_id,
                success=False,
                policy_applied=["logging"],
                message=str(exc),
            )
            raise

        self._execution_log_repository.save(
            device_id=device_id,
            success=True,
            policy_applied=["logging"],
            message=None,
        )
