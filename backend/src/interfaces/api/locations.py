from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from application.devices.mapper import DeviceMapper
from application.devices.service import DevicesService
from application.locations.config_service import LocationConfigService
from application.locations.dto import (
    LocationCreateDto,
    LocationResponseDto,
    LocationSummaryDto,
    ZoneCreateDto,
    ZoneResponseDto,
    ZoneUpdateDto,
)
from domain.locations.errors import ConfigurationError
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository


router = APIRouter(
    prefix="/api/locations",
    tags=["locations"],
)


def get_location_config_service(
    db: Session = Depends(get_db),
) -> LocationConfigService:
    repository = LocationRepository(db)
    return LocationConfigService(repository)


def get_devices_service(
    db: Session = Depends(get_db),
) -> DevicesService:
    repository = DeviceRepository(db)
    return DevicesService(repository)


@router.post(
    "",
    response_model=LocationResponseDto,
    status_code=status.HTTP_201_CREATED,
)
def create_location(
    request: LocationCreateDto,
    service: LocationConfigService = Depends(
        get_location_config_service
    ),
) -> LocationResponseDto:
    try:
        return service.create(request)
    except ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[LocationSummaryDto],
)
def list_locations(
    service: LocationConfigService = Depends(
        get_location_config_service
    ),
) -> list[LocationSummaryDto]:
    return service.list_locations()


@router.get(
    "/{location_id}",
    response_model=LocationResponseDto,
)
def get_location(
    location_id: UUID,
    service: LocationConfigService = Depends(
        get_location_config_service
    ),
) -> LocationResponseDto:
    location = service.get(location_id)

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found.",
        )

    return location


@router.delete(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_location(
    location_id: UUID,
    service: LocationConfigService = Depends(
        get_location_config_service
    ),
) -> None:
    deleted = service.delete(location_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found.",
        )


@router.post(
    "/{location_id}/zones",
    response_model=ZoneResponseDto,
    status_code=status.HTTP_201_CREATED,
)
def add_zone(
    location_id: UUID,
    request: ZoneCreateDto,
    service: LocationConfigService = Depends(
        get_location_config_service
    ),
) -> ZoneResponseDto:
    try:
        return service.add_zone(
            location_id=location_id,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{location_id}/zones/{zone_id}",
    response_model=ZoneResponseDto,
)
def update_zone(
    location_id: UUID,
    zone_id: UUID,
    request: ZoneUpdateDto,
    service: LocationConfigService = Depends(
        get_location_config_service
    ),
) -> ZoneResponseDto:
    try:
        zone = service.update_zone(
            location_id=location_id,
            zone_id=zone_id,
            request=request,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found.",
        )

    return zone


@router.delete(
    "/{location_id}/zones/{zone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_zone(
    location_id: UUID,
    zone_id: UUID,
    service: LocationConfigService = Depends(
        get_location_config_service
    ),
) -> None:
    try:
        deleted = service.delete_zone(
            location_id=location_id,
            zone_id=zone_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found.",
        )


@router.get(
    "/{location_id}/zones/{zone_id}/devices",
    response_model=list,
)
def list_zone_devices(
    location_id: UUID,
    zone_id: UUID,
    service: DevicesService = Depends(
        get_devices_service
    ),
):
    try:
        devices = service.list_devices_in_zone(
            location_id=location_id,
            zone_id=zone_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return [
        DeviceMapper.to_dto(device)
        for device in devices
    ]