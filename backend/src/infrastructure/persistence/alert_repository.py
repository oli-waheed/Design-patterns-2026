from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.persistence.models import AlertRow


class AlertRepository:
    """Repository for persisted alerts."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def save(
        self,
        event_type: str,
        severity: str,
        message: str,
        location_id: UUID | None = None,
        zone_id: UUID | None = None,
        device_id: UUID | None = None,
    ) -> AlertRow:
        """Insert one active alert row."""

        row = AlertRow(
            event_type=event_type,
            severity=severity,
            message=message,
            location_id=location_id,
            zone_id=zone_id,
            device_id=device_id,
            status="active",
        )

        try:
            self._db.add(row)
            self._db.commit()
            self._db.refresh(row)
            return row

        except Exception:
            self._db.rollback()
            raise

    def list_alerts(
        self,
        status: str | None = "active",
        location_id: UUID | None = None,
        zone_id: UUID | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[AlertRow]:
        """Return alerts newest first.

        ``status=None`` returns alerts of every status.
        """

        statement = select(AlertRow)

        if status is not None:
            statement = statement.where(AlertRow.status == status)

        if location_id is not None:
            statement = statement.where(AlertRow.location_id == location_id)

        if zone_id is not None:
            statement = statement.where(AlertRow.zone_id == zone_id)

        if since is not None:
            statement = statement.where(AlertRow.created_at >= since)

        statement = statement.order_by(
            AlertRow.created_at.desc(),
            AlertRow.id.desc(),
        ).limit(limit)

        return list(self._db.scalars(statement).all())
