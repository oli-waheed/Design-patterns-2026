
from uuid import UUID

from application.automation.dto import (
    AutomationEvaluationResponse,
    ZoneRecommendationResponse,
)
from domain.automation.context import LocationAutomationContext
from domain.automation.strategy import get_strategy
from infrastructure.persistence.automation_repository import (
    AutomationRepository,
)


class AutomationService:
    """Coordinates strategy selection and zone evaluation."""

    def __init__(self, repository: AutomationRepository):
        self._repository = repository

    def save_strategy(
        self,
        location_id: UUID,
        strategy_key: str,
    ) -> str:
        if not self._repository.location_exists(location_id):
            raise LookupError("Location not found.")

        # Validate the key before saving it.
        get_strategy(strategy_key)

        return self._repository.save_strategy_key(
            location_id,
            strategy_key,
        )

    def evaluate(
        self,
        location_id: UUID,
    ) -> AutomationEvaluationResponse:
        if not self._repository.location_exists(location_id):
            raise LookupError("Location not found.")

        strategy_key = self._repository.get_strategy_key(location_id)

        if strategy_key is None:
            strategy_key = "conservative"
            self._repository.save_strategy_key(
                location_id,
                strategy_key,
            )

        strategy = get_strategy(strategy_key)
        zones = self._repository.list_zones(location_id)

        recommendations = []

        for zone in zones:
            moisture = self._repository.latest_moisture_for_zone(
                zone.id
            )

            context = LocationAutomationContext(
                location_id=location_id,
                zone_id=zone.id,
                moisture=moisture,
                low=float(zone.moisture_threshold_low),
                high=float(zone.moisture_threshold_high),
            )

            recommendation = strategy.decide(context)

            recommendations.append(
                ZoneRecommendationResponse(
                    zone_id=zone.id,
                    zone_name=zone.name,
                    moisture=moisture,
                    action=recommendation.action,
                    reason=recommendation.reason,
                )
            )

        return AutomationEvaluationResponse(
            location_id=location_id,
            strategy_key=strategy_key,
            recommendations=recommendations,
        )
