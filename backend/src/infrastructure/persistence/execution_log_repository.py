
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.persistence.models import (
    ActuatorExecutionLogRow,
    DeviceRow,
)


class ExecutionLogRepository:
    """Repository for actuator execution history."""

    def __init__(self, db: Session):
        self._db = db

    def save(
        self,
        device_id: UUID,
        success: bool,
        policy_applied: list[str],
        message: str | None = None,
    ) -> ActuatorExecutionLogRow:
        row = ActuatorExecutionLogRow(
            device_id=device_id,
            success=success,
            policy_applied=policy_applied,
            message=message,
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
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 100))

        statement = (
            select(ActuatorExecutionLogRow, DeviceRow.display_name)
            .join(
                DeviceRow,
                DeviceRow.id == ActuatorExecutionLogRow.device_id,
            )
            .order_by(ActuatorExecutionLogRow.created_at.desc())
            .limit(safe_limit)
        )

        results = self._db.execute(statement).all()

        return [
            {
                "id": log.id,
                "device_id": log.device_id,
                "device_name": device_name,
                "success": log.success,
                "policy_applied": log.policy_applied,
                "message": log.message,
                "created_at": log.created_at,
            }
            for log, device_name in results
        ]
