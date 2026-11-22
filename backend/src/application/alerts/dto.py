from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


AlertSeverity = Literal["info", "warning", "critical"]
AlertStatus = Literal["active", "resolved"]


class AlertDto(BaseModel):
    """Alert response. acknowledged_at is stored but not returned."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location_id: UUID | None
    zone_id: UUID | None
    device_id: UUID | None
    severity: AlertSeverity
    message: str
    event_type: str
    status: AlertStatus
    created_at: datetime
