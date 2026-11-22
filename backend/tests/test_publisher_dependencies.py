"""Publishers must publish events, never write alerts themselves."""

import inspect

import pytest

import application.actuators.transition_service as transition_module
import application.commands.service as command_module
import application.readings.service as reading_module


@pytest.mark.parametrize(
    "module",
    [reading_module, command_module, transition_module],
)
def test_publishers_do_not_import_alert_repository(module):
    source = inspect.getsource(module)

    assert "AlertRepository" not in source
    assert "alert_repository" not in source
    assert "AlertRow" not in source
