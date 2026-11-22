from datetime import datetime
from uuid import UUID

from application.alerts.dto import AlertDto
from infrastructure.persistence.alert_repository import AlertRepository


ALLOWED_STATUS_FILTERS = {"active", "resolved", "all"}


class AlertQueryService:
    """Read side of alerts for the event feed."""

    def __init__(self, repository: AlertRepository) -> None:
        self._repository = repository

    def list_alerts(
        self,
        status: str = "active",
        location_id: UUID | None = None,
        zone_id: UUID | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[AlertDto]:
        if status not in ALLOWED_STATUS_FILTERS:
            raise ValueError(
                f"Invalid status: {status}. "
                "Allowed values: active, resolved, all."
            )

        rows = self._repository.list_alerts(
            status=None if status == "all" else status,
            location_id=location_id,
            zone_id=zone_id,
            since=since,
            limit=limit,
        )

        return [AlertDto.model_validate(row) for row in rows]
