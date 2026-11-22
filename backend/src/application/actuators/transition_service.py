from uuid import UUID

from application.actuators.allowed_commands import allowed_commands_for
from domain.actuators.context import ActuatorContext
from domain.actuators.state import ActuatorState
from domain.events.bus import EventBus
from domain.events.events import ActuatorStateChanged
from infrastructure.persistence.device_repository import DeviceRepository


class ActuatorTransitionService:
    """Applies manual state transitions and publishes each saved change."""

    def __init__(
        self,
        repository: DeviceRepository,
        event_bus: EventBus | None = None,
    ) -> None:
        self._repository = repository
        self._event_bus = event_bus

    def transition(
        self,
        device_id: UUID,
        target: ActuatorState | str,
    ) -> dict | None:
        device = self._repository.get_device_by_id(device_id)

        if device is None or device.role != "actuator":
            return None

        current_state = self._repository.get_actuator_state(device_id)

        if current_state is None:
            return None

        context = ActuatorContext(current_state)

        # Raises IllegalTransitionError before anything is saved.
        context.transition(target)

        self._repository.update_actuator_state(
            device_id=device_id,
            state=context.state.value,
        )

        if self._event_bus is not None:
            self._event_bus.publish(
                ActuatorStateChanged(
                    device_id=device_id,
                    previous_state=ActuatorState(current_state).value,
                    state=context.state.value,
                    location_id=device.location_id,
                    zone_id=device.zone_id,
                )
            )

        return {
            "device_id": device_id,
            "state": context.state.value,
            "allowed_commands": allowed_commands_for(device, context),
        }
