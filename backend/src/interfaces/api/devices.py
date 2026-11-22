
import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from application.actuators.transition_service import (
    ActuatorTransitionService,
)
from application.devices.dto import DeviceDto
from application.devices.mapper import DeviceMapper
from application.devices.service import DevicesService
from application.locations.dto import DeviceAssignmentDto
from application.readings.service import ReadingIngest
from composition import get_event_bus, get_sampling_config_publisher
from application.devices.service import SamplingConfigPublisher
from domain.events.bus import EventBus
from domain.actuators.state import ActuatorState, IllegalTransitionError
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository
from infrastructure.persistence.execution_log_repository import (
    ExecutionLogRepository,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/devices",
    tags=["devices"],
)

actuator_router = APIRouter(
    prefix="/api/actuators",
    tags=["actuators"],
)


class SamplingUpdateRequest(BaseModel):
    sampling_interval_seconds: int = Field(ge=5)
    tracking_enabled: bool


class SamplingResponse(BaseModel):
    device_id: UUID
    sampling_interval_seconds: int
    tracking_enabled: bool


class DeviceReadingRequest(BaseModel):
    """Body an HTTP device (for example an ESP32) posts."""

    value: float
    unit: str = Field(min_length=1, max_length=32)


class DeviceReadingResponse(BaseModel):
    device_id: UUID
    value: float
    unit: str
    source: str
    recorded_at: datetime


class ActuatorTransitionRequest(BaseModel):
    target: ActuatorState


class ActuatorStateResponse(BaseModel):
    device_id: UUID
    state: str
    allowed_commands: list[str]


class ExecutionLogResponse(BaseModel):
    id: UUID
    device_id: UUID
    device_name: str
    success: bool
    policy_applied: list[str]
    message: str | None
    created_at: datetime


def get_devices_service(
    db: Session = Depends(get_db),
    config_publisher: SamplingConfigPublisher | None = Depends(
        get_sampling_config_publisher
    ),
) -> DevicesService:
    return DevicesService(
        repository=DeviceRepository(db),
        config_publisher=config_publisher,
    )


def get_reading_ingest(
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
) -> ReadingIngest:
    return ReadingIngest(
        device_repository=DeviceRepository(db),
        reading_repository=ReadingRepository(db),
        event_bus=event_bus,
    )


def get_transition_service(
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
) -> ActuatorTransitionService:
    return ActuatorTransitionService(
        repository=DeviceRepository(db),
        event_bus=event_bus,
    )


def get_execution_log_repository(
    db: Session = Depends(get_db),
) -> ExecutionLogRepository:
    return ExecutionLogRepository(db)


@router.get(
    "",
    response_model=list[DeviceDto],
)
def list_devices(
    family: str | None = Query(default=None),
    role: str | None = Query(default=None),
    service: DevicesService = Depends(get_devices_service),
) -> list[DeviceDto]:
    devices = service.list_devices(
        device_family=family,
        role=role,
    )

    return [
        DeviceMapper.to_dto(device)
        for device in devices
    ]


@router.post(
    "/provision",
    response_model=list[DeviceDto],
    status_code=status.HTTP_201_CREATED,
)
def provision_devices(
    family: str = Query(...),
    service: DevicesService = Depends(get_devices_service),
) -> list[DeviceDto]:
    try:
        devices = service.provision_family(family)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return [
        DeviceMapper.to_dto(device)
        for device in devices
    ]


@router.get(
    "/{device_id}",
    response_model=DeviceDto,
)
def get_device(
    device_id: UUID,
    service: DevicesService = Depends(get_devices_service),
) -> DeviceDto:
    device = service.get_device(device_id)

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found.",
        )

    return DeviceMapper.to_dto(device)


@router.get(
    "/{device_id}/sampling",
    response_model=SamplingResponse,
    summary="Device HTTP: read sampling settings",
)
def get_device_sampling(
    device_id: UUID,
    service: DevicesService = Depends(get_devices_service),
) -> SamplingResponse:
    """An HTTP device calls this to learn its interval and tracking flag.

    The device applies the interval on its own clock; the backend never
    polls the device.
    """

    device = service.get_device(device_id)

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found.",
        )

    return SamplingResponse(
        device_id=device.id,
        sampling_interval_seconds=device.sampling_interval_seconds,
        tracking_enabled=device.tracking_enabled,
    )


@router.post(
    "/{device_id}/readings",
    response_model=DeviceReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Device HTTP: post one reading",
)
def post_device_reading(
    device_id: UUID,
    request: DeviceReadingRequest,
    ingest: ReadingIngest = Depends(get_reading_ingest),
) -> DeviceReadingResponse:
    """Translate the body with the Phase 5 translator (source "http") and
    pass it to ReadingIngest, which stores it and publishes
    reading.created when tracking is on. This route publishes nothing.
    """

    try:
        reading = ingest.record_payload(
            device_id,
            request.model_dump(),
            source="http",
        )

    except ValueError as exc:
        if str(exc) == "Device not found.":
            logger.warning(
                "Dropping HTTP reading for unknown device %s",
                device_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found.",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return DeviceReadingResponse(
        device_id=reading.device_id,
        value=reading.value,
        unit=reading.unit,
        source=reading.source,
        recorded_at=reading.recorded_at,
    )


@router.get(
    "/{device_id}/state",
    response_model=ActuatorStateResponse,
)
def get_actuator_state(
    device_id: UUID,
    service: DevicesService = Depends(get_devices_service),
) -> ActuatorStateResponse:
    result = service.get_actuator_state(device_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actuator not found.",
        )

    return ActuatorStateResponse(**result)


@router.post(
    "/{device_id}/transition",
    response_model=ActuatorStateResponse,
)
def transition_actuator(
    device_id: UUID,
    request: ActuatorTransitionRequest,
    service: ActuatorTransitionService = Depends(get_transition_service),
) -> ActuatorStateResponse:
    try:
        result = service.transition(
            device_id=device_id,
            target=request.target,
        )

    except IllegalTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actuator not found.",
        )

    return ActuatorStateResponse(**result)


@router.patch(
    "/{device_id}/zone",
    status_code=status.HTTP_204_NO_CONTENT,
)
def assign_device_to_zone(
    device_id: UUID,
    request: DeviceAssignmentDto,
    service: DevicesService = Depends(get_devices_service),
) -> None:
    try:
        device_exists = service.assign_zone(
            device_id=device_id,
            zone_id=request.zone_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if not device_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found.",
        )


@router.patch(
    "/{device_id}/sampling",
    response_model=SamplingResponse,
)
def update_sampling(
    device_id: UUID,
    request: SamplingUpdateRequest,
    service: DevicesService = Depends(get_devices_service),
) -> SamplingResponse:
    device = service.update_sampling(
        device_id=device_id,
        sampling_interval_seconds=request.sampling_interval_seconds,
        tracking_enabled=request.tracking_enabled,
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found.",
        )

    return SamplingResponse(
        device_id=device.id,
        sampling_interval_seconds=device.sampling_interval_seconds,
        tracking_enabled=device.tracking_enabled,
    )


@actuator_router.get(
    "/executions",
    response_model=list[ExecutionLogResponse],
)
def list_actuator_executions(
    limit: int = Query(default=20, ge=1, le=100),
    repository: ExecutionLogRepository = Depends(
        get_execution_log_repository
    ),
) -> list[ExecutionLogResponse]:
    records = repository.list_recent(limit=limit)

    return [
        ExecutionLogResponse(**record)
        for record in records
    ]
