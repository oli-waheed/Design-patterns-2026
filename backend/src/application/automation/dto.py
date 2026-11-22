
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StrategySelectionRequest(BaseModel):
    strategy_key: str = Field(
        min_length=1,
        max_length=32,
    )


class ZoneRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    zone_id: UUID
    zone_name: str
    moisture: float | None
    low_threshold: float
    high_threshold: float
    action: str
    reason: str
    score: float | None = None


class AutomationEvaluationResponse(BaseModel):
    location_id: UUID
    strategy_key: str
    recommendations: list[ZoneRecommendationResponse]


class StrategyResponse(BaseModel):
    location_id: UUID
    strategy_key: str | None
