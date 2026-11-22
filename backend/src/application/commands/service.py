from typing import Any
from uuid import UUID

from application.commands.dto import CommandLogDto
from domain.actuators.context import ActuatorContext
from domain.actuators.state import ActuatorState
from domain.commands.invoker import CommandInvoker, CommandRegistry
from domain.devices.entity import Device
from domain.events.bus import EventBus
from domain.events.events import ActuatorStateChanged, CommandFailed
from infrastructure.adapters.actuators.factory import build_actuator_port
from infrastructure.persistence.command_log_repository import (
    CommandLogRepository,
)
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.execution_log_repository import (
    ExecutionLogRepository,
)


# Each command is restricted to its intended actuator type.
COMMAND_DEVICE_TYPES = {
    "start_pump": "water_pump",
    "stop_pump": "water_pump",
    "set_light_level": "grow_light",
}


# Define the states in which each command is permitted.
COMMAND_ALLOWED_STATES = {
    "start_pump": {ActuatorState.IDLE},
    "stop_pump": {ActuatorState.RUNNING},
    "set_light_level": {
        ActuatorState.IDLE,
        ActuatorState.RUNNING,
    },
}


# Commands that change actuator state.
# set_light_level deliberately has no state transition.
COMMAND_TARGET_STATES = {
    "start_pump": ActuatorState.RUNNING,
    "stop_pump": ActuatorState.IDLE,
}


class CommandService:
    """Application service responsible for executing actuator commands."""

    def __init__(
        self,
        device_repository: DeviceRepository,
        execution_log_repository: ExecutionLogRepository,
        command_log_repository: CommandLogRepository,
        event_bus: EventBus | None = None,
    ) -> None:
        self._device_repository = device_repository
        self._event_bus = event_bus
        self._execution_log_repository = execution_log_repository
        self._command_log_repository = command_log_repository

        self._registry = CommandRegistry()
        self._invoker = CommandInvoker()

    def execute(
        self,
        device_id: UUID,
        command_type: str,
        payload: dict[str, Any] | None = None,
    ) -> CommandLogDto | None:
        """Validate, execute, and record an actuator command."""

        command_payload = payload or {}

        # Unknown commands are rejected before creating a log record.
        command = self._registry.create(command_type)

        device = self._device_repository.get_device_by_id(device_id)

        if device is None or device.role != "actuator":
            return None

        # A known command must target its intended actuator type.
        expected_device_type = COMMAND_DEVICE_TYPES[command_type]

        if device.device_type != expected_device_type:
            return self._save_result(
                device_id=device_id,
                command_type=command_type,
                payload=command_payload,
                status="rejected",
                error_message=(
                    f"Command '{command_type}' is not supported "
                    f"by device type '{device.device_type}'."
                ),
            )

        current_state = self._device_repository.get_actuator_state(
            device_id
        )

        if current_state is None:
            return None

        context = ActuatorContext(current_state)

        allowed_states = COMMAND_ALLOWED_STATES[command_type]

        if context.state not in allowed_states:
            return self._save_result(
                device_id=device_id,
                command_type=command_type,
                payload=command_payload,
                status="rejected",
                error_message=(
                    f"Command '{command_type}' is not allowed "
                    f"when actuator state is '{context.state.value}'."
                ),
            )

        # Validate the requested transition before executing.
        target_state = COMMAND_TARGET_STATES.get(command_type)

        if target_state is not None:
            try:
                context.transition(target_state)
            except Exception as exc:
                return self._save_result(
                    device_id=device_id,
                    command_type=command_type,
                    payload=command_payload,
                    status="rejected",
                    error_message=str(exc),
                )

        # Build the Phase 9 decorated actuator port.
        actuator_port = build_actuator_port(
            device_repository=self._device_repository,
            execution_log_repository=self._execution_log_repository,
        )

        try:
            self._invoker.execute(
                command=command,
                port=actuator_port,
                device_id=device_id,
                payload=command_payload,
            )

        except Exception as exc:
            # Includes MaxRunTimeExceeded from the Phase 9 decorator, whose
            # message "Max run time exceeded" becomes the alert message.
            result = self._save_result(
                device_id=device_id,
                command_type=command_type,
                payload=command_payload,
                status="failed",
                error_message=str(exc),
            )

            self._publish_command_failed(
                device=device,
                command_type=command_type,
                message=str(exc),
            )

            return result

        # Persist state only after successful command execution.
        if target_state is not None and context.state != ActuatorState(
            current_state
        ):
            self._device_repository.update_actuator_state(
                device_id=device_id,
                state=context.state.value,
            )

            self._publish_state_changed(
                device=device,
                previous_state=current_state,
                state=context.state.value,
            )

        return self._save_result(
            device_id=device_id,
            command_type=command_type,
            payload=command_payload,
            status="success",
            error_message=None,
        )

    def list_recent(
        self,
        limit: int = 50,
    ) -> list[CommandLogDto]:
        """Return recent command history."""

        records = self._command_log_repository.list_recent(limit=limit)

        return [
            CommandLogDto.model_validate(record)
            for record in records
        ]

    def _publish_command_failed(
        self,
        device: Device,
        command_type: str,
        message: str,
    ) -> None:
        if self._event_bus is None:
            return

        self._event_bus.publish(
            CommandFailed(
                device_id=device.id,
                command_type=command_type,
                message=message,
                location_id=device.location_id,
                zone_id=device.zone_id,
            )
        )

    def _publish_state_changed(
        self,
        device: Device,
        previous_state: str,
        state: str,
    ) -> None:
        if self._event_bus is None:
            return

        self._event_bus.publish(
            ActuatorStateChanged(
                device_id=device.id,
                previous_state=ActuatorState(previous_state).value,
                state=state,
                location_id=device.location_id,
                zone_id=device.zone_id,
            )
        )

    def _save_result(
        self,
        device_id: UUID,
        command_type: str,
        payload: dict[str, Any],
        status: str,
        error_message: str | None,
    ) -> CommandLogDto:
        """Save and convert a command result to its application DTO."""

        record = self._command_log_repository.save(
            device_id=device_id,
            command_type=command_type,
            payload=payload,
            status=status,
            error_message=error_message,
        )

        return CommandLogDto.model_validate(record)
