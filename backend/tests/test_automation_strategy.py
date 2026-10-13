
from uuid import uuid4

from domain.automation.context import LocationAutomationContext
from domain.automation.strategy import (
    AggressiveMoistureStrategy,
    ConservativeMoistureStrategy,
    get_strategy,
)


def make_context(
    moisture: float | None,
    low: float = 0.30,
    high: float = 0.60,
) -> LocationAutomationContext:
    return LocationAutomationContext(
        location_id=uuid4(),
        zone_id=uuid4(),
        moisture=moisture,
        low=low,
        high=high,
    )


def test_conservative_strategy_waits_above_low_threshold():
    result = ConservativeMoistureStrategy().decide(
        make_context(moisture=0.45)
    )

    assert result.action == "wait"


def test_aggressive_strategy_irrigates_below_high_threshold():
    result = AggressiveMoistureStrategy().decide(
        make_context(moisture=0.45)
    )

    assert result.action == "irrigate"


def test_strategies_can_make_different_recommendations():
    context = make_context(moisture=0.45)

    conservative = ConservativeMoistureStrategy().decide(context)
    aggressive = AggressiveMoistureStrategy().decide(context)

    assert conservative.action == "wait"
    assert aggressive.action == "irrigate"


def test_both_strategies_wait_without_moisture_reading():
    context = make_context(moisture=None)

    assert ConservativeMoistureStrategy().decide(context).action == "wait"
    assert AggressiveMoistureStrategy().decide(context).action == "wait"


def test_strategy_registry_returns_known_strategies():
    assert isinstance(
        get_strategy("conservative"),
        ConservativeMoistureStrategy,
    )
    assert isinstance(
        get_strategy("aggressive"),
        AggressiveMoistureStrategy,
    )


def test_unknown_strategy_key_is_rejected():
    try:
        get_strategy("unknown")
    except ValueError as exc:
        assert "Unknown strategy key" in str(exc)
    else:
        raise AssertionError("Unknown strategy key should be rejected")
