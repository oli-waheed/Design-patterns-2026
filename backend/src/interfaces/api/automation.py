
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.automation.automation_service import AutomationService
from application.automation.dto import (
    AutomationEvaluationResponse,
    StrategySelectionRequest,
)
from infrastructure.db import get_db
from infrastructure.persistence.automation_repository import (
    AutomationRepository,
)


router = APIRouter(
    prefix="/api/locations",
    tags=["automation"],
)


def get_automation_service(
    db: Session = Depends(get_db),
) -> AutomationService:
    repository = AutomationRepository(db)
    return AutomationService(repository)


@router.put(
    "/{location_id}/automation/strategy",
)
def save_strategy(
    location_id: UUID,
    request: StrategySelectionRequest,
    service: AutomationService = Depends(get_automation_service),
) -> dict[str, str]:
    try:
        strategy_key = service.save_strategy(
            location_id=location_id,
            strategy_key=request.strategy_key,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "location_id": str(location_id),
        "strategy_key": strategy_key,
        "message": "Automation strategy saved successfully.",
    }


@router.post(
    "/{location_id}/automation/evaluate",
    response_model=AutomationEvaluationResponse,
)
def evaluate_automation(
    location_id: UUID,
    service: AutomationService = Depends(get_automation_service),
) -> AutomationEvaluationResponse:
    try:
        return service.evaluate(location_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
