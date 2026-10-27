
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.automation.automation_service import AutomationService
from application.overview.dto import OverviewResponseDto
from application.overview.facade import OverviewFacade
from infrastructure.db import get_db
from infrastructure.persistence.automation_repository import (
    AutomationRepository,
)


router = APIRouter(
    prefix="/api/locations",
    tags=["overview"],
)


def get_overview_facade(
    db: Session = Depends(get_db),
) -> OverviewFacade:
    automation_repository = AutomationRepository(db)
    automation_service = AutomationService(automation_repository)

    return OverviewFacade(
        db=db,
        automation_service=automation_service,
        automation_repository=automation_repository,
    )


@router.get(
    "/{location_id}/overview",
    response_model=OverviewResponseDto,
)
def get_location_overview(
    location_id: UUID,
    facade: OverviewFacade = Depends(get_overview_facade),
) -> OverviewResponseDto:
    try:
        return facade.get_overview(location_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
