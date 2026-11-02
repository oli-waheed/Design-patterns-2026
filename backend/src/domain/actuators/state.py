
from enum import Enum


class ActuatorState(str, Enum):
    OFF = "off"
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class IllegalTransitionError(Exception):
    """Raised when an actuator transition is not allowed."""


# Legal transitions between actuator states.
ALLOWED_TRANSITIONS = {
    ActuatorState.OFF: {
        ActuatorState.IDLE,
    },
    ActuatorState.IDLE: {
        ActuatorState.RUNNING,
        ActuatorState.MAINTENANCE,
        ActuatorState.ERROR,
        ActuatorState.OFF,
    },
    ActuatorState.RUNNING: {
        ActuatorState.IDLE,
        ActuatorState.ERROR,
    },
    ActuatorState.ERROR: {
        ActuatorState.IDLE,
        ActuatorState.MAINTENANCE,
        ActuatorState.OFF,
    },
    ActuatorState.MAINTENANCE: {
        ActuatorState.IDLE,
        ActuatorState.OFF,
    },
}


# Commands available in each state.
ALLOWED_COMMANDS = {
    ActuatorState.OFF: ["power_on"],
    ActuatorState.IDLE: ["start_pump"],
    ActuatorState.RUNNING: ["stop_pump"],
    ActuatorState.ERROR: ["reset_error"],
    ActuatorState.MAINTENANCE: ["finish_maintenance"],
}
