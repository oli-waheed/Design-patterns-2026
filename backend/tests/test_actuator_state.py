
import pytest

from domain.actuators.context import ActuatorContext
from domain.actuators.state import (
    ActuatorState,
    IllegalTransitionError,
)


def test_idle_to_running_allowed():
    context = ActuatorContext(ActuatorState.IDLE)

    context.transition(ActuatorState.RUNNING)

    assert context.state == ActuatorState.RUNNING


def test_running_to_maintenance_rejected():
    context = ActuatorContext(ActuatorState.RUNNING)

    with pytest.raises(IllegalTransitionError):
        context.transition(ActuatorState.MAINTENANCE)


def test_illegal_transition_does_not_change_state():
    context = ActuatorContext(ActuatorState.RUNNING)

    with pytest.raises(IllegalTransitionError):
        context.transition(ActuatorState.MAINTENANCE)

    assert context.state == ActuatorState.RUNNING


def test_idle_allowed_commands():
    context = ActuatorContext(ActuatorState.IDLE)

    assert context.allowed_commands() == ["start_pump"]


def test_running_allowed_commands():
    context = ActuatorContext(ActuatorState.RUNNING)

    assert context.allowed_commands() == ["stop_pump"]
