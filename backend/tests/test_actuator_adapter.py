from uuid import uuid4

from infrastructure.adapters.actuators.simulation import (
    SimulationActuatorAdapter,
)


def test_simulation_actuator_adapter_stores_command():
    device_id = uuid4()

    adapter = SimulationActuatorAdapter()

    adapter.apply(
        device_id=device_id,
        command="water",
        payload={
            "duration_seconds": 10,
        },
    )

    assert len(adapter.commands) == 1
    assert adapter.commands[0]["device_id"] == device_id
    assert adapter.commands[0]["command"] == "water"
    assert adapter.commands[0]["payload"] == {
        "duration_seconds": 10,
    }