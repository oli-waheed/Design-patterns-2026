
from domain.actuators.state import (
    ActuatorState,
    IllegalTransitionError,
    ALLOWED_TRANSITIONS,
    ALLOWED_COMMANDS,
)


class ActuatorContext:
    """Manages the current state of an actuator."""

    def __init__(self, state: ActuatorState | str):
        self._state = ActuatorState(state)

    @property
    def state(self) -> ActuatorState:
        return self._state

    def transition(self, target: ActuatorState | str) -> None:
        target_state = ActuatorState(target)

        allowed_states = ALLOWED_TRANSITIONS[self._state]

        if target_state not in allowed_states:
            raise IllegalTransitionError(
                f"Transition from '{self._state.value}' "
                f"to '{target_state.value}' is not allowed."
            )

        self._state = target_state

    def allowed_commands(self) -> list[str]:
        return ALLOWED_COMMANDS[self._state].copy()
