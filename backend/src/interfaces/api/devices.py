from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from application.devices.dto import DeviceDto
from application.devices.mapper import DeviceMapper
from application.devices.service import DevicesService
from application.locations.dto import DeviceAssignmentDto
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository


router = APIRouter(
    prefix="/api/devices",
    tags=["devices"],
)


class SamplingUpdateRequest(BaseModel):
    sampling_interval_seconds: int = Field(
        ge=5,
    )
    tracking_enabled: bool


class SamplingResponse(BaseModel):
    device_id: UUID
    sampling_interval_seconds: int
    tracking_enabled: bool


def get_devices_service(
    db: Session = Depends(get_db),
) -> DevicesService:
    repository = DeviceRepository(db)
    return DevicesService(repository)


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