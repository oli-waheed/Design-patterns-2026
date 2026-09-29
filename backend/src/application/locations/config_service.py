from uuid import UUID

from application.locations.dto import (
    LocationCreateDto,
    LocationResponseDto,
    LocationSummaryDto,
    ZoneCreateDto,
    ZoneResponseDto,
    ZoneUpdateDto,
)
from domain.locations.config_builder import LocationConfigBuilder
from infrastructure.persistence.location_repository import LocationRepository


class LocationConfigService:
    def __init__(
        self,
        repository: LocationRepository,
    ):
        self._repository = repository

    def create(
        self,
        request: LocationCreateDto,
    ) -> LocationResponseDto:
        builder = LocationConfigBuilder()

        builder.set_location_name(
            request.location_name
        )

        for zone in request.zones:
            builder.add_zone(
                name=zone.name,
                moisture_threshold_low=(
                    zone.moisture_threshold_low
                ),
                moisture_threshold_high=(
                    zone.moisture_threshold_high
                ),
                schedule=zone.schedule,
            )

        config = builder.build()

        saved_config = self._repository.save_config(
            config
        )

        return self._to_response(saved_config)

    def get(
        self,
        location_id: UUID,
    ) -> LocationResponseDto | None:
        config = self._repository.get_config(
            location_id
        )

        if config is None:
            return None

        return self._to_response(config)

    def list_locations(
        self,
    ) -> list[LocationSummaryDto]:
        rows = self._repository.list_locations()

        return [
            LocationSummaryDto(
                id=row.id,
                name=row.name,
            )
            for row in rows
        ]

    def delete(
        self,
        location_id: UUID,
    ) -> bool:
        return self._repository.delete_location(
            location_id
        )

    def add_zone(
        self,
        location_id: UUID,
        request: ZoneCreateDto,
    ) -> ZoneResponseDto:
        if (
            request.moisture_threshold_low
            >= request.moisture_threshold_high
        ):
            raise ValueError(
                "Low moisture threshold must be less than high threshold."
            )

        zone = self._repository.add_zone(
            location_id=location_id,
            name=request.name.strip(),
            moisture_threshold_low=(
                request.moisture_threshold_low
            ),
            moisture_threshold_high=(
                request.moisture_threshold_high
            ),
            schedule=request.schedule,
        )

        return self._zone_to_response(
            zone,
            location_id,
        )

    def update_zone(
        self,
        location_id: UUID,
        zone_id: UUID,
        request: ZoneUpdateDto,
    ) -> ZoneResponseDto | None:
        if (
            request.moisture_threshold_low
            >= request.moisture_threshold_high
        ):
            raise ValueError(
                "Low moisture threshold must be less than high threshold."
            )

        zone = self._repository.update_zone(
            location_id=location_id,
            zone_id=zone_id,
            name=request.name.strip(),
            moisture_threshold_low=(
                request.moisture_threshold_low
            ),
            moisture_threshold_high=(
                request.moisture_threshold_high
            ),
            schedule=request.schedule,
        )

        if zone is None:
            return None

        return self._zone_to_response(
            zone,
            location_id,
        )

    def delete_zone(
        self,
        location_id: UUID,
        zone_id: UUID,
    ) -> bool:
        return self._repository.delete_zone(
            location_id=location_id,
            zone_id=zone_id,
        )

    @staticmethod
    def _to_response(
        config,
    ) -> LocationResponseDto:
        location = config.location

        return LocationResponseDto(
            location=LocationSummaryDto(
                id=location.id,
                name=location.name,
            ),
            zones=[
                ZoneResponseDto(
                    id=zone.id,
                    location_id=location.id,
                    name=zone.name,
                    moisture_threshold_low=(
                        zone.moisture_threshold_low
                    ),
                    moisture_threshold_high=(
                        zone.moisture_threshold_high
                    ),
                    schedule=zone.schedule,
                )
                for zone in location.zones
            ],
        )

    @staticmethod
    def _zone_to_response(
        zone,
        location_id: UUID,
    ) -> ZoneResponseDto:
        return ZoneResponseDto(
            id=zone.id,
            location_id=location_id,
            name=zone.name,
            moisture_threshold_low=(
                zone.moisture_threshold_low
            ),
            moisture_threshold_high=(
                zone.moisture_threshold_high
            ),
            schedule=zone.schedule,
        )