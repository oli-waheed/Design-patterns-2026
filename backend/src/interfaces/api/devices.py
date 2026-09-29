from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from application.devices.dto import DeviceDto
from application.devices.mapper import DeviceMapper
from application.devices.service import DevicesService
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository


router = APIRouter(
    prefix="/api/devices",
    tags=["devices"],
)


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