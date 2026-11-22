"""Phase 13 API additions: chart range, alert resolve, saved strategy,
location rename, and recommendation thresholds."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from domain.sensors.reading import Reading
from infrastructure.db import SessionLocal
from infrastructure.persistence.reading_repository import ReadingRepository
from main import app


client = TestClient(app)


def provision_sensor():
    devices = client.post(
        "/api/devices/provision", params={"family": "simulation"}
    ).json()
    return next(d for d in devices if d["device_type"] == "moisture_sensor")


def store_readings(device_id, minutes_ago_values):
    """Insert readings at fixed times: [(minutes_ago, value), ...]."""
    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        repository = ReadingRepository(db)
        for minutes_ago, value in minutes_ago_values:
            repository.save(
                Reading(
                    device_id=device_id,
                    value=value,
                    unit="vwc",
                    source="simulation",
                    recorded_at=now - timedelta(minutes=minutes_ago),
                )
            )
    finally:
        db.close()
    return now


def iso(moment):
    return moment.isoformat()


def test_range_returns_only_window_oldest_first():
    sensor = provision_sensor()
    now = store_readings(
        sensor["id"], [(120, 0.10), (50, 0.20), (30, 0.30), (10, 0.40)]
    )

    response = client.get(
        f"/api/sensors/{sensor['id']}/readings",
        params={
            "from": iso(now - timedelta(hours=1)),
            "to": iso(now),
        },
    )

    assert response.status_code == 200
    assert [row["value"] for row in response.json()] == [0.20, 0.30, 0.40]


def test_range_with_no_rows_is_empty_list():
    sensor = provision_sensor()
    now = datetime.now(timezone.utc)

    response = client.get(
        f"/api/sensors/{sensor['id']}/readings",
        params={
            "from": iso(now - timedelta(days=30)),
            "to": iso(now - timedelta(days=29)),
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_range_rejects_from_after_to():
    sensor = provision_sensor()
    now = datetime.now(timezone.utc)

    response = client.get(
        f"/api/sensors/{sensor['id']}/readings",
        params={"from": iso(now), "to": iso(now - timedelta(hours=1))},
    )

    assert response.status_code == 400


def test_latest_mode_is_unchanged_newest_first():
    sensor = provision_sensor()
    store_readings(sensor["id"], [(3, 0.31), (2, 0.32), (1, 0.33)])

    response = client.get(
        f"/api/sensors/{sensor['id']}/readings", params={"limit": 2}
    )

    assert [row["value"] for row in response.json()] == [0.33, 0.32]


def make_alert():
    devices = client.post(
        "/api/devices/provision", params={"family": "simulation"}
    ).json()
    pump = next(d for d in devices if d["device_type"] == "water_pump")
    client.post(
        f"/api/devices/{pump['id']}/transition", json={"target": "error"}
    )
    alerts = client.get("/api/alerts", params={"status": "all", "limit": 200}).json()
    return next(a for a in alerts if a["device_id"] == pump["id"])


def test_resolve_alert_persists_and_moves_between_filters():
    alert = make_alert()

    response = client.patch(
        f"/api/alerts/{alert['id']}", json={"status": "resolved"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"

    active_ids = {
        a["id"] for a in client.get("/api/alerts", params={"limit": 200}).json()
    }
    resolved_ids = {
        a["id"]
        for a in client.get(
            "/api/alerts", params={"status": "resolved", "limit": 200}
        ).json()
    }

    assert alert["id"] not in active_ids
    assert alert["id"] in resolved_ids

    db = SessionLocal()
    try:
        from infrastructure.persistence.models import AlertRow

        row = db.get(AlertRow, alert["id"])
        assert row.acknowledged_at is not None
    finally:
        db.close()


def test_reopen_alert_clears_acknowledged_at():
    alert = make_alert()
    client.patch(f"/api/alerts/{alert['id']}", json={"status": "resolved"})

    response = client.patch(
        f"/api/alerts/{alert['id']}", json={"status": "active"}
    )

    assert response.json()["status"] == "active"


def test_alert_patch_validation():
    assert (
        client.patch(f"/api/alerts/{uuid4()}", json={"status": "resolved"}).status_code
        == 404
    )
    alert = make_alert()
    assert (
        client.patch(f"/api/alerts/{alert['id']}", json={"status": "done"}).status_code
        == 422
    )


def create_location():
    response = client.post(
        "/api/locations",
        json={
            "location_name": f"P13 {uuid4().hex[:6]}",
            "zones": [
                {
                    "name": "Bench 1",
                    "moisture_threshold_low": 0.2,
                    "moisture_threshold_high": 0.6,
                }
            ],
        },
    )
    return response.json()["location"]["id"]


def test_saved_strategy_is_null_then_persisted_value():
    location_id = create_location()
    url = f"/api/locations/{location_id}/automation/strategy"

    assert client.get(url).json()["strategy_key"] is None

    client.put(url, json={"strategy_key": "aggressive"})

    assert client.get(url).json() == {
        "location_id": location_id,
        "strategy_key": "aggressive",
    }
    assert client.get(f"/api/locations/{uuid4()}/automation/strategy").status_code == 404


def test_rename_location():
    location_id = create_location()

    response = client.patch(
        f"/api/locations/{location_id}", json={"location_name": "  Renamed  "}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"
    assert client.get(f"/api/locations/{location_id}").json()["location"]["name"] == "Renamed"
    assert (
        client.patch(f"/api/locations/{location_id}", json={"location_name": "   "}).status_code
        == 400
    )
    assert (
        client.patch(f"/api/locations/{uuid4()}", json={"location_name": "x"}).status_code
        == 404
    )


def test_recommendations_include_zone_thresholds():
    location_id = create_location()

    body = client.post(
        f"/api/locations/{location_id}/automation/evaluate"
    ).json()

    recommendation = body["recommendations"][0]
    assert recommendation["low_threshold"] == 0.2
    assert recommendation["high_threshold"] == 0.6
    assert "score" in recommendation
