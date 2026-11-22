"""Device HTTP: GET sampling and POST readings for protocol=http devices."""

import inspect
from uuid import uuid4

from fastapi.testclient import TestClient

from domain.devices.entity import Device
from infrastructure.db import SessionLocal
from infrastructure.persistence.device_repository import DeviceRepository
from main import app
import interfaces.api.devices as devices_api


client = TestClient(app)


def create_http_sensor(tracking_enabled=True):
    db = SessionLocal()
    try:
        device = DeviceRepository(db).save_device(
            Device(
                id=None,
                device_type="moisture_sensor",
                role="sensor",
                device_family="edge",
                display_name="ESP32 Moisture",
                default_config={"unit": "vwc", "protocol": "http"},
                sampling_interval_seconds=30,
                tracking_enabled=tracking_enabled,
            )
        )
        return str(device.id)
    finally:
        db.close()


def test_get_sampling_returns_device_columns():
    device_id = create_http_sensor()

    response = client.get(f"/api/devices/{device_id}/sampling")

    assert response.status_code == 200
    assert response.json() == {
        "device_id": device_id,
        "sampling_interval_seconds": 30,
        "tracking_enabled": True,
    }


def test_get_sampling_for_missing_device_is_404():
    response = client.get(f"/api/devices/{uuid4()}/sampling")

    assert response.status_code == 404


def test_get_then_post_stores_http_reading_and_sends_frame():
    device_id = create_http_sensor()

    assert client.get(f"/api/devices/{device_id}/sampling").status_code == 200

    with client.websocket_connect("/api/ws") as ws:
        response = client.post(
            f"/api/devices/{device_id}/readings",
            json={"value": 0.41, "unit": "vwc"},
        )

        frame = ws.receive_json()

    assert response.status_code == 201
    assert response.json()["source"] == "http"
    assert response.json()["value"] == 0.41

    assert frame["type"] == "reading.created"
    assert frame["payload"]["device_id"] == device_id
    assert frame["payload"]["source"] == "http"

    history = client.get(f"/api/sensors/{device_id}/readings").json()
    assert [(row["value"], row["source"]) for row in history] == [(0.41, "http")]


def test_tracking_off_stores_http_reading_without_frame():
    off_id = create_http_sensor(tracking_enabled=False)
    on_id = create_http_sensor(tracking_enabled=True)

    with client.websocket_connect("/api/ws") as ws:
        off = client.post(
            f"/api/devices/{off_id}/readings",
            json={"value": 0.30, "unit": "vwc"},
        )
        client.post(
            f"/api/devices/{on_id}/readings",
            json={"value": 0.31, "unit": "vwc"},
        )

        frame = ws.receive_json()

    assert off.status_code == 201
    assert frame["payload"]["device_id"] == on_id

    history = client.get(f"/api/sensors/{off_id}/readings").json()
    assert len(history) == 1


def test_post_reading_for_unknown_device_is_dropped_with_404():
    response = client.post(
        f"/api/devices/{uuid4()}/readings",
        json={"value": 0.41, "unit": "vwc"},
    )

    assert response.status_code == 404


def test_post_reading_requires_value_and_unit():
    device_id = create_http_sensor()

    response = client.post(
        f"/api/devices/{device_id}/readings",
        json={"value": 0.41},
    )

    assert response.status_code == 422


def test_device_route_does_not_publish_events_itself():
    source = inspect.getsource(devices_api.post_device_reading)

    assert ".publish(" not in source
    assert "ReadingCreated" not in source
    assert "record_payload" in source
