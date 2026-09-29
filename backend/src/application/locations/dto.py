from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ZoneCreateDto(BaseModel):
    name: str = Field(min_length=1)
    moisture_threshold_low: float = Field(
        ge=0.0,
        le=1.0,
    )
    moisture_threshold_high: float = Field(
        ge=0.0,
        le=1.0,
    )
    schedule: dict[str, Any] = Field(
        default_factory=dict
    )


class ZoneUpdateDto(BaseModel):
    name: str = Field(min_length=1)
    moisture_threshold_low: float = Field(
        ge=0.0,
        le=1.0,
    )
    moisture_threshold_high: float = Field(
        ge=0.0,
        le=1.0,
    )
    schedule: dict[str, Any] = Field(
        default_factory=dict
    )


class LocationCreateDto(BaseModel):
    location_name: str = Field(min_length=1)
    zones: list[ZoneCreateDto] = Field(
        min_length=1
    )


class LocationSummaryDto(BaseModel):
    id: UUID
    name: str


class ZoneResponseDto(BaseModel):
    id: UUID
    location_id: UUID
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict[str, Any]


class LocationResponseDto(BaseModel):
    location: LocationSummaryDto
    zones: list[ZoneResponseDto]


class DeviceAssignmentDto(BaseModel):
    zone_id: UUID | None