
from uuid import uuid4

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_actuator_state_api_and_transitions():
    # Find an existing actuator.
    devices_response = client.get(
        "/api/devices",
        params={"role": "actuator"},
    )

    assert devices_response.status_code == 200

    actuators = devices_response.json()
    assert len(actuators) > 0

    device_id = actuators[0]["id"]

    # Check the initial state.
    state_response = client.get(
        f"/api/devices/{device_id}/state"
    )

    assert state_response.status_code == 200

    state_data = state_response.json()

    assert state_data["state"] == "idle"
    assert state_data["allowed_commands"] == ["start_pump"]

    # Transition from idle to running.
    transition_response = client.post(
        f"/api/devices/{device_id}/transition",
        json={"target": "running"},
    )

    assert transition_response.status_code == 200

    transition_data = transition_response.json()

    assert transition_data["state"] == "running"
    assert transition_data["allowed_commands"] == ["stop_pump"]

    # Running to maintenance is not allowed.
    illegal_response = client.post(
        f"/api/devices/{device_id}/transition",
        json={"target": "maintenance"},
    )

    assert illegal_response.status_code == 409

    # Confirm that the illegal transition did not change the state.
    check_response = client.get(
        f"/api/devices/{device_id}/state"
    )

    assert check_response.status_code == 200
    assert check_response.json()["state"] == "running"

    # Restore the original idle state.
    restore_response = client.post(
        f"/api/devices/{device_id}/transition",
        json={"target": "idle"},
    )

    assert restore_response.status_code == 200
    assert restore_response.json()["state"] == "idle"


def test_missing_actuator_returns_404():
    unknown_device_id = uuid4()

    response = client.get(
        f"/api/devices/{unknown_device_id}/state"
    )

    assert response.status_code == 404


def test_missing_actuator_transition_returns_404():
    unknown_device_id = uuid4()

    response = client.post(
        f"/api/devices/{unknown_device_id}/transition",
        json={"target": "running"},
    )

    assert response.status_code == 404
