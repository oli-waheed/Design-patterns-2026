
from uuid import UUID

from application.automation.automation_service import AutomationService
from application.overview.dto import (
    OverviewDeviceCountsDto,
    OverviewDeviceDto,
    OverviewLocationDto,
    OverviewReadingDto,
    OverviewResponseDto,
    OverviewZoneDto,
)
from infrastructure.persistence.automation_repository import AutomationRepository
from infrastructure.persistence.overview_repository import OverviewRepository


class OverviewFacade:
    """Coordinate overview data and assemble the response DTO."""

    def __init__(
        self,
        overview_repository: OverviewRepository,
        automation_service: AutomationService,
        automation_repository: AutomationRepository,
    ):
        self._overview_repository = overview_repository
        self._automation_service = automation_service
        self._automation_repository = automation_repository

    def get_overview(self, location_id: UUID) -> OverviewResponseDto:
        location = self._overview_repository.get_location(location_id)

        if location is None:
            raise LookupError("Location not found.")

        zones = self._overview_repository.list_zones(location_id)
        devices = self._overview_repository.list_assigned_devices(location_id)

        device_by_id = {device.id: device for device in devices}
        device_ids = list(device_by_id)

        reading_rows = self._overview_repository.get_latest_readings(device_ids)

        readings_by_device = {
            row.device_id: OverviewReadingDto(
                device_id=row.device_id,
                value=float(row.value),
                unit=row.unit,
                recorded_at=row.recorded_at,
                tracking_enabled=device_by_id[row.device_id].tracking_enabled,
                sampling_interval_seconds=(
                    device_by_id[row.device_id].sampling_interval_seconds
                ),
            )
            for row in reading_rows
        }

        devices_by_zone = {zone.id: [] for zone in zones}
        readings_by_zone = {zone.id: [] for zone in zones}

        sensor_count = 0
        actuator_count = 0

        for device in devices:
            if device.role == "sensor":
                sensor_count += 1
            elif device.role == "actuator":
                actuator_count += 1

            if device.zone_id not in devices_by_zone:
                continue

            devices_by_zone[device.zone_id].append(
                OverviewDeviceDto(
                    id=device.id,
                    device_type=device.device_type,
                    role=device.role,
                    display_name=device.display_name,
                )
            )

            reading = readings_by_device.get(device.id)
            if reading is not None:
                readings_by_zone[device.zone_id].append(reading)

        strategy_key = self._automation_repository.get_strategy_key(
            location_id
        )

        last_recommendation = None
        if strategy_key is not None:
            last_recommendation = self._automation_service.evaluate(
                location_id
            )

        return OverviewResponseDto(
            location=OverviewLocationDto(
                id=location.id,
                name=location.name,
            ),
            device_counts=OverviewDeviceCountsDto(
                sensor=sensor_count,
                actuator=actuator_count,
            ),
            zones=[
                OverviewZoneDto(
                    id=zone.id,
                    name=zone.name,
                    moisture_threshold_low=float(
                        zone.moisture_threshold_low
                    ),
                    moisture_threshold_high=float(
                        zone.moisture_threshold_high
                    ),
                    devices=devices_by_zone[zone.id],
                    latest_readings=readings_by_zone[zone.id],
                )
                for zone in zones
            ],
            strategy_key=strategy_key,
            last_recommendation=last_recommendation,
        )
