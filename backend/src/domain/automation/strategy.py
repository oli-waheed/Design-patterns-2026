
from dataclasses import dataclass
from typing import Protocol

from domain.automation.context import LocationAutomationContext


@dataclass(frozen=True)
class Recommendation:
    action: str
    reason: str
    score: float | None = None


class AutomationStrategy(Protocol):
    def decide(
        self,
        context: LocationAutomationContext,
    ) -> Recommendation:
        ...


class ConservativeMoistureStrategy:
    def decide(
        self,
        context: LocationAutomationContext,
    ) -> Recommendation:
        if context.moisture is None:
            return Recommendation(
                action="wait",
                reason="No moisture sensor in this zone.",
            )

        if context.moisture < context.low:
            return Recommendation(
                action="irrigate",
                reason="Moisture is below the zone's low threshold.",
            )

        return Recommendation(
            action="wait",
            reason="Conservative strategy waits until moisture "
                   "falls below the low threshold.",
        )


class AggressiveMoistureStrategy:
    def decide(
        self,
        context: LocationAutomationContext,
    ) -> Recommendation:
        if context.moisture is None:
            return Recommendation(
                action="wait",
                reason="No moisture sensor in this zone.",
            )

        if context.moisture < context.high:
            return Recommendation(
                action="irrigate",
                reason="Aggressive strategy irrigates below "
                       "the zone's high threshold.",
            )

        return Recommendation(
            action="wait",
            reason="Moisture has reached the high threshold.",
        )


STRATEGIES: dict[str, AutomationStrategy] = {
    "conservative": ConservativeMoistureStrategy(),
    "aggressive": AggressiveMoistureStrategy(),
}


def get_strategy(key: str) -> AutomationStrategy:
    try:
        return STRATEGIES[key]
    except KeyError:
        raise ValueError(f"Unknown strategy key: {key}") from None
