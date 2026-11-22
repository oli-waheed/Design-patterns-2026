"""End-to-end Phase 11 checks through the HTTP API and the shared bus."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import update

from infrastructure.db import SessionLocal
from infrastructure.persistence.models import ActuatorStateRow
from main import app


client = TestClient(app)


def provision_simulation_devices():
    response = client.post(
        "/api/devices/provision",
        params={"family": "simulation"},
    )
    assert response.status_code == 201
    return response.json()


def create_location_with_two_benches():
    response = client.post(
        "/api/locations",
        json={
            "location_name": f"Observer test {uuid4().hex[:8]}",
            "zones": [
                {
                    "name": "Bench 1",
                    "moisture_threshold_low": 0.20,
                    "moisture_threshold_high": 0.60,
                },
                {
                    "name": "Bench 2",
                    "moisture_threshold_low": 0.20,
                    "moisture_threshold_high": 0.60,
                },
            ],
        },
    )
    assert response.status_code == 201
    body = response.json()
    zones = {zone["name"]: zone["id"] for zone in body["zones"]}
    return body["location"]["id"], zones


def alerts_for(**params):
    response = client.get("/api/alerts", params={"limit": 200, **params})
    assert response.status_code == 200
    return response.json()


def alerts_for_device(device_id):
    return [
        alert
        for alert in alerts_for(status="all")
        if alert["device_id"] == device_id
    ]


def test_low_moisture_on_bench_1_creates_zone_alert(monkeypatch):
    devices = provision_simulation_devices()
    moisture = next(
        d for d in devices if d["device_type"] == "moisture_sensor"
    )
    location_id, zones = create_location_with_two_benches()

    assign = client.patch(
        f"/api/devices/{moisture['id']}/zone",
        json={"zone_id": zones["Bench 1"]},
    )
    assert assign.status_code == 204

    # Force the simulated moisture value to 0.10.
    monkeypatch.setattr(
        "infrastructure.adapters.sensors.simulation.random.uniform",
        lambda low, high: 0.10,
    )

    read = client.post(f"/api/sensors/{moisture['id']}/read")
    assert read.status_code == 200
    assert read.json()["value"] == 0.10

    bench_1_alerts = alerts_for(zone_id=zones["Bench 1"])
    assert len(bench_1_alerts) == 1

    alert = bench_1_alerts[0]
    assert alert["event_type"] == "threshold.crossed"
    assert alert["severity"] == "warning"
    assert alert["message"] == "Moisture below zone low"
    assert alert["status"] == "active"
    assert alert["location_id"] == location_id
    assert alert["zone_id"] == zones["Bench 1"]
    assert alert["device_id"] == moisture["id"]
    assert "acknowledged_at" not in alert

    assert alerts_for(zone_id=zones["Bench 2"]) == []
    assert len(alerts_for(location_id=location_id)) == 1


def test_tracking_off_stores_reading_without_alert(monkeypatch):
    devices = provision_simulation_devices()
    moisture = next(
        d for d in devices if d["device_type"] == "moisture_sensor"
    )
    _, zones = create_location_with_two_benches()

    client.patch(
        f"/api/devices/{moisture['id']}/zone",
        json={"zone_id": zones["Bench 1"]},
    )
    client.patch(
        f"/api/devices/{moisture['id']}/sampling",
        json={"sampling_interval_seconds": 60, "tracking_enabled": False},
    )

    monkeypatch.setattr(
        "infrastructure.adapters.sensors.simulation.random.uniform",
        lambda low, high: 0.10,
    )

    read = client.post(f"/api/sensors/{moisture['id']}/read")
    assert read.status_code == 200

    history = client.get(f"/api/sensors/{moisture['id']}/readings")
    assert history.status_code == 200
    assert len(history.json()) == 1

    assert alerts_for(zone_id=zones["Bench 1"]) == []


def test_failed_stop_pump_on_unassigned_pump_creates_command_alert():
    devices = provision_simulation_devices()
    pump = next(d for d in devices if d["device_type"] == "water_pump")
    assert pump["zone_id"] is None

    started = client.post(
        "/api/commands",
        json={"device_id": pump["id"], "command_type": "start_pump"},
    )
    assert started.json()["status"] == "success"

    # Pretend the pump has been running for 31 minutes.
    db = SessionLocal()
    try:
        db.execute(
            update(ActuatorStateRow)
            .where(ActuatorStateRow.device_id == pump["id"])
            .values(
                updated_at=datetime.now(timezone.utc)
                - timedelta(minutes=31)
            )
        )
        db.commit()
    finally:
        db.close()

    stopped = client.post(
        "/api/commands",
        json={"device_id": pump["id"], "command_type": "stop_pump"},
    )
    assert stopped.status_code == 200
    assert stopped.json()["status"] == "failed"
    assert stopped.json()["error_message"] == "Max run time exceeded"

    pump_alerts = alerts_for_device(pump["id"])
    assert len(pump_alerts) == 1

    alert = pump_alerts[0]
    assert alert["event_type"] == "command.failed"
    assert alert["severity"] == "warning"
    assert alert["message"] == "Max run time exceeded"
    assert alert["location_id"] is None
    assert alert["zone_id"] is None


def test_transition_to_error_creates_critical_alert():
    devices = provision_simulation_devices()
    pump = next(d for d in devices if d["device_type"] == "water_pump")

    running = client.post(
        f"/api/devices/{pump['id']}/transition",
        json={"target": "running"},
    )
    assert running.status_code == 200

    # A non-error state change is published but not stored.
    assert alerts_for_device(pump["id"]) == []

    error = client.post(
        f"/api/devices/{pump['id']}/transition",
        json={"target": "error"},
    )
    assert error.status_code == 200
    assert error.json()["state"] == "error"

    pump_alerts = alerts_for_device(pump["id"])
    assert len(pump_alerts) == 1

    alert = pump_alerts[0]
    assert alert["event_type"] == "state.changed"
    assert alert["severity"] == "critical"
    assert alert["message"] == "Actuator entered error"


def test_alerts_are_newest_first_and_since_filters():
    devices = provision_simulation_devices()
    pump = next(d for d in devices if d["device_type"] == "water_pump")

    client.post(
        f"/api/devices/{pump['id']}/transition",
        json={"target": "error"},
    )
    client.post(
        f"/api/devices/{pump['id']}/transition",
        json={"target": "idle"},
    )
    client.post(
        f"/api/devices/{pump['id']}/transition",
        json={"target": "error"},
    )

    pump_alerts = alerts_for_device(pump["id"])
    assert len(pump_alerts) == 2
    assert pump_alerts[0]["created_at"] >= pump_alerts[1]["created_at"]

    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    assert alerts_for(since=future) == []


def test_invalid_status_returns_400():
    response = client.get("/api/alerts", params={"status": "open"})

    assert response.status_code == 400


def test_limit_out_of_range_is_rejected():
    response = client.get("/api/alerts", params={"limit": 500})

    assert response.status_code == 422


def test_alerts_endpoint_is_documented():
    schema = client.get("/openapi.json").json()

    assert "get" in schema["paths"]["/api/alerts"]
