from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Any
from uuid import UUID

from application.commands.dto import CommandLogDto
from application.commands.service import CommandService
from composition import get_event_bus
from domain.events.bus import EventBus
from infrastructure.db import get_db
from infrastructure.persistence.command_log_repository import (
    CommandLogRepository,
)
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.execution_log_repository import (
    ExecutionLogRepository,
)


router = APIRouter(
    prefix="/api/commands",
    tags=["commands"],
)


class CommandRequest(BaseModel):
    device_id: UUID
    command_type: str
    payload: dict[str, Any] = Field(default_factory=dict)


def get_command_service(
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
) -> CommandService:
    device_repository = DeviceRepository(db)
    execution_log_repository = ExecutionLogRepository(db)
    command_log_repository = CommandLogRepository(db)

    return CommandService(
        device_repository=device_repository,
        execution_log_repository=execution_log_repository,
        command_log_repository=command_log_repository,
        event_bus=event_bus,
    )


@router.post(
    "",
    response_model=CommandLogDto,
    status_code=status.HTTP_200_OK,
)
def execute_command(
    request: CommandRequest,
    service: CommandService = Depends(get_command_service),
):
    try:
        result = service.execute(
            device_id=request.device_id,
            command_type=request.command_type,
            payload=request.payload,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or is not an actuator.",
        )

    if result.status == "rejected":
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=jsonable_encoder(result),
        )

    return result


@router.get(
    "",
    response_model=list[CommandLogDto],
)
def list_commands(
    limit: int = Query(default=50, ge=1, le=200),
    service: CommandService = Depends(get_command_service),
) -> list[CommandLogDto]:
    return service.list_recent(limit=limit)
