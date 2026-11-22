"""Dashboard WebSocket: frames come from the EventBus, not from routes."""

from uuid import uuid4

from fastapi.testclient import TestClient

from application.realtime.connection_manager import ConnectionManager
from main import app


client = TestClient(app)


def provision():
    response = client.post(
        "/api/devices/provision",
        params={"family": "simulation"},
    )
    assert response.status_code == 201
    return response.json()


def create_zone():
    response = client.post(
        "/api/locations",
        json={
            "location_name": f"WS test {uuid4().hex[:8]}",
            "zones": [
                {
                    "name": "Bench 1",
                    "moisture_threshold_low": 0.20,
                    "moisture_threshold_high": 0.60,
                }
            ],
        },
    )
    assert response.status_code == 201
    body = response.json()
    return body["location"]["id"], body["zones"][0]["id"]


def test_reading_created_frame_includes_zone(monkeypatch):
    devices = provision()
    sensor = next(d for d in devices if d["device_type"] == "moisture_sensor")
    location_id, zone_id = create_zone()
    client.patch(f"/api/devices/{sensor['id']}/zone", json={"zone_id": zone_id})

    monkeypatch.setattr(
        "infrastructure.adapters.sensors.simulation.random.uniform",
        lambda low, high: 0.45,
    )

    with client.websocket_connect("/api/ws") as ws:
        assert client.post(f"/api/sensors/{sensor['id']}/read").status_code == 200

        frame = ws.receive_json()

    assert frame["type"] == "reading.created"
    payload = frame["payload"]
    assert payload["device_id"] == sensor["id"]
    assert payload["value"] == 0.45
    assert payload["unit"] == "vwc"
    assert payload["source"] == "simulation"
    assert payload["zone_id"] == zone_id
    assert payload["location_id"] == location_id
    assert "recorded_at" in payload


def test_low_reading_sends_reading_then_alert_frame(monkeypatch):
    devices = provision()
    sensor = next(d for d in devices if d["device_type"] == "moisture_sensor")
    _, zone_id = create_zone()
    client.patch(f"/api/devices/{sensor['id']}/zone", json={"zone_id": zone_id})

    monkeypatch.setattr(
        "infrastructure.adapters.sensors.simulation.random.uniform",
        lambda low, high: 0.10,
    )

    with client.websocket_connect("/api/ws") as ws:
        client.post(f"/api/sensors/{sensor['id']}/read")

        first = ws.receive_json()
        second = ws.receive_json()

    assert first["type"] == "reading.created"
    assert second["type"] == "alert.created"
    assert second["payload"]["severity"] == "warning"
    assert second["payload"]["message"] == "Moisture below zone low"
    assert second["payload"]["event_type"] == "threshold.crossed"
    assert second["payload"]["zone_id"] == zone_id
    assert second["payload"]["id"]


def test_state_change_sends_actuator_frame():
    devices = provision()
    pump = next(d for d in devices if d["device_type"] == "water_pump")

    with client.websocket_connect("/api/ws") as ws:
        response = client.post(
            f"/api/devices/{pump['id']}/transition",
            json={"target": "running"},
        )
        assert response.status_code == 200

        frame = ws.receive_json()

    assert frame["type"] == "actuator.state_changed"
    assert frame["payload"]["device_id"] == pump["id"]
    assert frame["payload"]["previous_state"] == "idle"
    assert frame["payload"]["state"] == "running"


def test_tracking_off_sends_no_reading_frame():
    devices = provision()
    sensors = [d for d in devices if d["role"] == "sensor"]
    off_sensor, on_sensor = sensors[0], sensors[1]

    client.patch(
        f"/api/devices/{off_sensor['id']}/sampling",
        json={"sampling_interval_seconds": 60, "tracking_enabled": False},
    )

    with client.websocket_connect("/api/ws") as ws:
        # Stored, but not published.
        assert client.post(f"/api/sensors/{off_sensor['id']}/read").status_code == 200
        # Published: the next frame must be for this device, which shows
        # the tracking-off reading produced no frame before it.
        assert client.post(f"/api/sensors/{on_sensor['id']}/read").status_code == 200

        frame = ws.receive_json()

    assert frame["payload"]["device_id"] == on_sensor["id"]

    history = client.get(f"/api/sensors/{off_sensor['id']}/readings")
    assert len(history.json()) == 1


def test_broadcast_without_clients_is_a_no_op():
    manager = ConnectionManager()

    # No loop and no connections yet: nothing to send, nothing raised.
    manager.broadcast_threadsafe({"type": "reading.created", "payload": {}})

    assert manager.connection_count == 0
