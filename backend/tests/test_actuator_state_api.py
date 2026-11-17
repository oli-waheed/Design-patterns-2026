
from uuid import uuid4

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_actuator_state_api_and_transitions():
    devices_response = client.get(
        "/api/devices",
        params={"role": "actuator"},
    )

    assert devices_response.status_code == 200

    actuators = devices_response.json()

    water_pumps = [
        device
        for device in actuators
        if device["device_type"] == "water_pump"
    ]

    assert len(water_pumps) > 0

    device_id = water_pumps[0]["id"]

    state_response = client.get(
        f"/api/devices/{device_id}/state"
    )

    assert state_response.status_code == 200

    state_data = state_response.json()

    assert state_data["state"] == "idle"
    assert state_data["allowed_commands"] == ["start_pump"]

    transition_response = client.post(
        f"/api/devices/{device_id}/transition",
        json={"target": "running"},
    )

    assert transition_response.status_code == 200

    transition_data = transition_response.json()

    assert transition_data["state"] == "running"
    assert transition_data["allowed_commands"] == ["stop_pump"]

    illegal_response = client.post(
        f"/api/devices/{device_id}/transition",
        json={"target": "maintenance"},
    )

    assert illegal_response.status_code == 409

    restore_response = client.post(
        f"/api/devices/{device_id}/transition",
        json={"target": "idle"},
    )

    assert restore_response.status_code == 200
    assert restore_response.json()["state"] == "idle"


def test_actuator_state_returns_404_for_missing_device():
    response = client.get(
        f"/api/devices/{uuid4()}/state"
    )

    assert response.status_code == 404


def test_actuator_state_returns_404_for_non_actuator():
    sensors_response = client.get(
        "/api/devices",
        params={"role": "sensor"},
    )

    assert sensors_response.status_code == 200

    sensors = sensors_response.json()
    assert len(sensors) > 0

    sensor_id = sensors[0]["id"]

    response = client.get(
        f"/api/devices/{sensor_id}/state"
    )

    assert response.status_code == 404
