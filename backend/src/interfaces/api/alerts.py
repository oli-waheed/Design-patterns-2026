from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from application.alerts.dto import AlertDto
from application.alerts.service import AlertQueryService
from infrastructure.db import get_db
from infrastructure.persistence.alert_repository import AlertRepository


router = APIRouter(
    prefix="/api/alerts",
    tags=["alerts"],
)


def get_alert_query_service(
    db: Session = Depends(get_db),
) -> AlertQueryService:
    return AlertQueryService(AlertRepository(db))


@router.get(
    "",
    response_model=list[AlertDto],
    summary="List alerts, newest first",
)
def list_alerts(
    status_filter: str = Query(
        default="active",
        alias="status",
        description="active, resolved, or all.",
    ),
    location_id: UUID | None = Query(default=None),
    zone_id: UUID | None = Query(default=None),
    since: datetime | None = Query(
        default=None,
        description="Only alerts created at or after this time.",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    service: AlertQueryService = Depends(get_alert_query_service),
) -> list[AlertDto]:
    try:
        return service.list_alerts(
            status=status_filter,
            location_id=location_id,
            zone_id=zone_id,
            since=since,
            limit=limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
