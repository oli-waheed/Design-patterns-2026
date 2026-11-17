from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.persistence.models import CommandLogRow


class CommandLogRepository:
    """Repository for actuator command history."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def save(
        self,
        device_id: UUID,
        command_type: str,
        payload: dict[str, Any],
        status: str,
        error_message: str | None = None,
    ) -> CommandLogRow:
        """Persist a command execution result."""

        row = CommandLogRow(
            device_id=device_id,
            command_type=command_type,
            payload=payload,
            status=status,
            error_message=error_message,
        )

        try:
            self._db.add(row)
            self._db.commit()
            self._db.refresh(row)
            return row

        except Exception:
            self._db.rollback()
            raise

    def list_recent(
        self,
        limit: int = 50,
    ) -> list[CommandLogRow]:
        """Return recent command records, newest first."""

        safe_limit = max(1, min(limit, 200))

        statement = (
            select(CommandLogRow)
            .order_by(CommandLogRow.created_at.desc())
            .limit(safe_limit)
        )

        return list(self._db.scalars(statement).all())
