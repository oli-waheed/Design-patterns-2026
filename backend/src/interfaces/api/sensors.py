from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from application.readings.dto import ReadingDto
from application.readings.service import ReadingIngest
from application.sensors.service import SensorService
from composition import get_event_bus
from domain.events.bus import EventBus
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository


router = APIRouter(
    prefix="/api/sensors",
    tags=["sensors"],
)


class SensorCreateRequest(BaseModel):
    type: str
    display_name: str | None = None


class SensorResponse(BaseModel):
    id: UUID
    device_type: str
    display_name: str
    default_config: dict


class ReadingResponse(BaseModel):
    device_id: UUID
    value: float
    unit: str
    source: str
    recorded_at: str


class SamplingUpdateRequest(BaseModel):
    sampling_interval_seconds: int = Field(
        ge=5,
    )
    tracking_enabled: bool


class SamplingResponse(BaseModel):
    device_id: UUID
    sampling_interval_seconds: int
    tracking_enabled: bool


def get_sensor_service(
    db: Session = Depends(get_db),
) -> SensorService:
    repository = DeviceRepository(db)
    return SensorService(repository)


def get_reading_ingest(
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
) -> ReadingIngest:
    device_repository = DeviceRepository(db)
    reading_repository = ReadingRepository(db)

    return ReadingIngest(
        device_repository=device_repository,
        reading_repository=reading_repository,
        event_bus=event_bus,
    )


@router.get(
    "",
    response_model=list[SensorResponse],
)
def list_sensors(
    service: SensorService = Depends(get_sensor_service),
) -> list[SensorResponse]:

    sensors = service.list_sensors()

    return [
        SensorResponse(
            id=sensor.id,
            device_type=sensor.device_type,
            display_name=sensor.display_name,
            default_config=sensor.default_config,
        )
        for sensor in sensors
    ]


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sensor(
    request: SensorCreateRequest,
    service: SensorService = Depends(get_sensor_service),
) -> SensorResponse:

    try:
        sensor = service.create_sensor(
            sensor_type=request.type,
            display_name=request.display_name,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return SensorResponse(
        id=sensor.id,
        device_type=sensor.device_type,
        display_name=sensor.display_name,
        default_config=sensor.default_config,
    )


@router.post(
    "/{sensor_id}/read",
    response_model=ReadingResponse,
)
def read_sensor(
    sensor_id: UUID,
    ingest: ReadingIngest = Depends(get_reading_ingest),
) -> ReadingResponse:

    try:
        reading = ingest.record(sensor_id)

    except ValueError as exc:
        message = str(exc)

        if message == "Device not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc

    return ReadingResponse(
        device_id=reading.device_id,
        value=reading.value,
        unit=reading.unit,
        source=reading.source,
        recorded_at=reading.recorded_at.isoformat(),
    )


@router.get(
    "/{sensor_id}/readings",
    response_model=list[ReadingResponse],
    summary="List readings: latest N, or a time range for charts",
)
def list_readings(
    sensor_id: UUID,
    limit: int | None = Query(
        default=None,
        ge=1,
        le=10000,
        description="Latest mode default 10; range mode default 2000.",
    ),
    from_: datetime | None = Query(
        default=None,
        alias="from",
        description="ISO-8601 start (inclusive). Enables range mode.",
    ),
    to: datetime | None = Query(
        default=None,
        description="ISO-8601 end (inclusive). Enables range mode.",
    ),
    db: Session = Depends(get_db),
) -> list[ReadingResponse]:
    """Two modes on one path.

    - Without ``from``/``to``: the latest ``limit`` readings, newest first
      (Phase 5 sensor cards).
    - With ``from`` and/or ``to``: readings in that window, **oldest first**
      (Phase 13 history chart).
    """

    if from_ is not None and to is not None and from_ > to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'from' must be before 'to'.",
        )

    if DeviceRepository(db).get_device_by_id(sensor_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found.",
        )

    reading_repository = ReadingRepository(db)

    if from_ is not None or to is not None:
        readings = reading_repository.list_range(
            device_id=sensor_id,
            start=from_,
            end=to,
            limit=limit or 2000,
        )
    else:
        readings = reading_repository.list_recent(
            device_id=sensor_id,
            limit=limit or 10,
        )

    return [
        ReadingResponse(
            device_id=reading.device_id,
            value=reading.value,
            unit=reading.unit,
            source=reading.source,
            recorded_at=reading.recorded_at.isoformat(),
        )
        for reading in readings
    ]
