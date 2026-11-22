"""Phase 12 hardening revision: indexes, checks, and the demo seed."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from infrastructure.db import SessionLocal
from main import app


DEMO_SENSOR_ID = "00000000-0000-4000-8000-000000000003"
DEMO_ZONE_ID = "00000000-0000-4000-8000-000000000002"

client = TestClient(app)


def query(sql, **params):
    db = SessionLocal()
    try:
        return db.execute(text(sql), params).all()
    finally:
        db.close()


def test_hardening_indexes_exist():
    names = {row[0] for row in query("SELECT indexname FROM pg_indexes")}

    assert {
        "ix_sensor_readings_device_recorded_at",
        "ix_alerts_location_created_at",
        "ix_alerts_status_created_at",
        "ix_command_log_created_at",
        "ix_actuator_execution_log_created_at",
        "ix_devices_location_id",
    } <= names


def test_seed_has_one_tracked_five_second_simulation_sensor():
    rows = query(
        """
        SELECT sampling_interval_seconds, tracking_enabled,
               device_family, default_config ->> 'protocol', zone_id
        FROM devices WHERE id = :id
        """,
        id=DEMO_SENSOR_ID,
    )

    assert len(rows) == 1
    interval, tracking, family, protocol, zone_id = rows[0]
    assert (interval, tracking, family, protocol) == (5, True, "simulation", "simulation")
    assert str(zone_id) == DEMO_ZONE_ID


def test_alert_severity_check_rejects_unknown_values():
    db = SessionLocal()
    try:
        with pytest.raises(IntegrityError):
            db.execute(
                text(
                    "INSERT INTO alerts (severity, message, event_type) "
                    "VALUES ('panic', 'x', 'command.failed')"
                )
            )
            db.flush()
    finally:
        db.rollback()
        db.close()


def test_rest_surface_is_under_api():
    paths = client.get("/openapi.json").json()["paths"]

    assert all(
        path.startswith("/api/") or path in {"/health", "/"}
        for path in paths
    )
    assert "/api/devices/{device_id}/execute" not in paths
    assert "post" in paths["/api/devices/{device_id}/readings"]
    assert "get" in paths["/api/devices/{device_id}/sampling"]
