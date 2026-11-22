from domain.actuators.context import ActuatorContext
from domain.actuators.state import ActuatorState
from domain.devices.entity import Device


def allowed_commands_for(
    device: Device,
    context: ActuatorContext,
) -> list[str]:
    """Commands the UI may offer for this actuator in its current state."""

    if device.device_type == "water_pump":
        return context.allowed_commands()

    if device.device_type == "grow_light":
        if context.state in {
            ActuatorState.IDLE,
            ActuatorState.RUNNING,
        }:
            return ["set_light_level"]

    return []
