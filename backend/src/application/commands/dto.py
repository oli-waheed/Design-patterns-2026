from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


CommandStatus = Literal["success", "failed", "rejected"]


class CommandExecutionDto(BaseModel):
    """Input data for executing an actuator command."""

    device_id: UUID
    command_type: str
    payload: dict = Field(default_factory=dict)


class CommandLogDto(BaseModel):
    """Command execution result and history record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: UUID
    command_type: str
    payload: dict
    status: CommandStatus
    error_message: str | None = None
    created_at: datetime
