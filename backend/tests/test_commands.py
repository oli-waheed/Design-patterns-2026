
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from application.commands.service import CommandService


def make_log_record(
    device_id,
    command_type,
    payload,
    status,
    error_message=None,
):
    return SimpleNamespace(
        id=uuid4(),
        device_id=device_id,
        command_type=command_type,
        payload=payload,
        status=status,
        error_message=error_message,
        created_at=datetime.now(timezone.utc),
    )


def make_service(
    monkeypatch,
    device_type="water_pump",
    state="idle",
):
    device_id = uuid4()

    device_repository = Mock()
    execution_log_repository = Mock()
    command_log_repository = Mock()

    device_repository.get_device_by_id.return_value = SimpleNamespace(
        id=device_id,
        role="actuator",
        device_type=device_type,
    )

    device_repository.get_actuator_state.return_value = state

    def save_command(**kwargs):
        return make_log_record(**kwargs)

    command_log_repository.save.side_effect = save_command

    actuator_port = Mock()

    monkeypatch.setattr(
        "application.commands.service.build_actuator_port",
        lambda **kwargs: actuator_port,
    )

    service = CommandService(
        device_repository=device_repository,
        execution_log_repository=execution_log_repository,
        command_log_repository=command_log_repository,
    )

    return (
        service,
        device_id,
        device_repository,
        command_log_repository,
        actuator_port,
    )


def test_start_pump_executes_successfully(monkeypatch):
    (
        service,
        device_id,
        device_repository,
        command_log_repository,
        actuator_port,
    ) = make_service(monkeypatch, state="idle")

    result = service.execute(
        device_id=device_id,
        command_type="start_pump",
        payload={},
    )

    assert result.status == "success"
    assert result.command_type == "start_pump"

    actuator_port.apply.assert_called_once_with(
        device_id=device_id,
        command="start_pump",
        payload={},
    )

    device_repository.update_actuator_state.assert_called_once_with(
        device_id=device_id,
        state="running",
    )

    command_log_repository.save.assert_called_once()


def test_illegal_stop_pump_is_rejected_and_logged(monkeypatch):
    (
        service,
        device_id,
        device_repository,
        command_log_repository,
        actuator_port,
    ) = make_service(monkeypatch, state="idle")

    result = service.execute(
        device_id=device_id,
        command_type="stop_pump",
        payload={},
    )

    assert result.status == "rejected"
    assert "not allowed" in result.error_message

    actuator_port.apply.assert_not_called()

    device_repository.update_actuator_state.assert_not_called()

    command_log_repository.save.assert_called_once()

    saved_record = command_log_repository.save.call_args.kwargs

    assert saved_record["status"] == "rejected"
    assert saved_record["command_type"] == "stop_pump"


def test_unknown_command_raises_error_without_logging(monkeypatch):
    (
        service,
        device_id,
        device_repository,
        command_log_repository,
        actuator_port,
    ) = make_service(monkeypatch)

    with pytest.raises(
        ValueError,
        match="Unknown command type",
    ):
        service.execute(
            device_id=device_id,
            command_type="unknown_command",
            payload={},
        )

    command_log_repository.save.assert_not_called()
    device_repository.get_device_by_id.assert_not_called()
    actuator_port.apply.assert_not_called()


def test_command_history_returns_repository_records(monkeypatch):
    (
        service,
        device_id,
        device_repository,
        command_log_repository,
        actuator_port,
    ) = make_service(monkeypatch)

    record = make_log_record(
        device_id=device_id,
        command_type="start_pump",
        payload={},
        status="success",
    )

    command_log_repository.list_recent.return_value = [record]

    result = service.list_recent(limit=10)

    assert len(result) == 1
    assert result[0].command_type == "start_pump"
    assert result[0].status == "success"

    command_log_repository.list_recent.assert_called_once_with(
        limit=10,
    )
