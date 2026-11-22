
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from domain.actuators.ports import ActuatorPort
from infrastructure.adapters.actuators.logging_decorator import (
    LoggingActuatorDecorator,
    MaxRunTimeExceeded,
)
from infrastructure.adapters.actuators.max_runtime_decorator import (
    MaxRunTimeActuatorDecorator,
)


def test_max_runtime_does_not_call_inner():
    device_id = uuid4()

    inner_adapter = Mock(spec=ActuatorPort)
    device_repository = Mock()

    device_repository.get_actuator_state_details.return_value = {
        "state": "running",
        "updated_at": datetime.now(timezone.utc)
        - timedelta(minutes=31),
    }

    decorator = MaxRunTimeActuatorDecorator(
        wrapped=inner_adapter,
        device_repository=device_repository,
    )

    with pytest.raises(
        MaxRunTimeExceeded,
        match="Max run time exceeded",
    ):
        decorator.apply(
            device_id=device_id,
            command="start_pump",
            payload={},
        )

    inner_adapter.apply.assert_not_called()


def test_failed_policy_writes_execution_row():
    device_id = uuid4()

    inner_adapter = Mock(spec=ActuatorPort)
    device_repository = Mock()
    execution_log_repository = Mock()

    device_repository.get_actuator_state_details.return_value = {
        "state": "running",
        "updated_at": datetime.now(timezone.utc)
        - timedelta(minutes=31),
    }

    max_runtime_decorator = MaxRunTimeActuatorDecorator(
        wrapped=inner_adapter,
        device_repository=device_repository,
    )

    logging_decorator = LoggingActuatorDecorator(
        wrapped=max_runtime_decorator,
        execution_log_repository=execution_log_repository,
    )

    with pytest.raises(
        MaxRunTimeExceeded,
        match="Max run time exceeded",
    ):
        logging_decorator.apply(
            device_id=device_id,
            command="start_pump",
            payload={},
        )

    execution_log_repository.save.assert_called_once_with(
        device_id=device_id,
        success=False,
        policy_applied=["maxRunTime", "logging"],
        message="Max run time exceeded",
    )

    inner_adapter.apply.assert_not_called()


def test_max_runtime_allows_stop_pump_after_limit():
    """An over-running pump must still be stoppable."""
    device_id = uuid4()

    inner_adapter = Mock(spec=ActuatorPort)
    device_repository = Mock()

    device_repository.get_actuator_state_details.return_value = {
        "state": "running",
        "updated_at": datetime.now(timezone.utc)
        - timedelta(minutes=45),
    }

    decorator = MaxRunTimeActuatorDecorator(
        wrapped=inner_adapter,
        device_repository=device_repository,
    )

    decorator.apply(
        device_id=device_id,
        command="stop_pump",
        payload={},
    )

    inner_adapter.apply.assert_called_once_with(
        device_id=device_id,
        command="stop_pump",
        payload={},
    )


def test_max_runtime_allows_commands_before_limit():
    device_id = uuid4()

    inner_adapter = Mock(spec=ActuatorPort)
    device_repository = Mock()

    device_repository.get_actuator_state_details.return_value = {
        "state": "running",
        "updated_at": datetime.now(timezone.utc)
        - timedelta(minutes=10),
    }

    decorator = MaxRunTimeActuatorDecorator(
        wrapped=inner_adapter,
        device_repository=device_repository,
    )

    decorator.apply(
        device_id=device_id,
        command="set_light_level",
        payload={"level": 50},
    )

    inner_adapter.apply.assert_called_once()
