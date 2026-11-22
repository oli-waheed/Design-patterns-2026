"""Command (Phase 10) + State (Phase 8) + Decorator (Phase 9) through HTTP."""

from sqlalchemy import select

from infrastructure.persistence.models import (
    ActuatorExecutionLogRow,
    ActuatorStateRow,
    CommandLogRow,
)

from .seed_ids import DEMO_PUMP_ID


def post_command(client, command_type):
    return client.post(
        "/api/commands",
        json={"device_id": DEMO_PUMP_ID, "command_type": command_type},
    )


def pump_state(db):
    db.expire_all()
    return db.get(ActuatorStateRow, DEMO_PUMP_ID).state


def test_start_pump_succeeds_and_persists_running(client, db):
    response = post_command(client, "start_pump")

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert pump_state(db) == "running"

    log = db.scalars(select(CommandLogRow)).all()
    assert [(row.command_type, row.status) for row in log] == [("start_pump", "success")]

    executions = db.scalars(select(ActuatorExecutionLogRow)).all()
    assert [row.success for row in executions] == [True]


def test_rejected_command_does_not_change_state(client, db):
    # The seeded pump is idle; stop_pump is only allowed while running.
    response = post_command(client, "stop_pump")

    assert response.status_code == 409
    assert response.json()["status"] == "rejected"
    assert pump_state(db) == "idle"

    # Rejected commands never reach the decorated actuator port.
    assert db.scalars(select(ActuatorExecutionLogRow)).all() == []


def test_start_then_stop_returns_to_idle(client, db):
    post_command(client, "start_pump")
    response = post_command(client, "stop_pump")

    assert response.json()["status"] == "success"
    assert pump_state(db) == "idle"

    history = client.get("/api/commands").json()
    assert [item["command_type"] for item in history] == ["stop_pump", "start_pump"]
