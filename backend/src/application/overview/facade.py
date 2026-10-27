
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

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
from infrastructure.persistence.models import (
    DeviceRow,
    LocationRow,
    ReadingRow,
    ZoneRow,
)


class OverviewFacade:
    """Assemble the data required by the greenhouse overview."""

    def __init__(
        self,
        db: Session,
        automation_service: AutomationService,
        automation_repository: AutomationRepository,
    ):
        self._db = db
        self._automation_service = automation_service
        self._automation_repository = automation_repository

    def get_overview(self, location_id: UUID) -> OverviewResponseDto:
        location = self._db.get(LocationRow, location_id)

        if location is None:
            raise LookupError("Location not found.")

        zones = list(
            self._db.scalars(
                select(ZoneRow)
                .where(ZoneRow.location_id == location_id)
                .order_by(ZoneRow.name)
            ).all()
        )

        # Only devices assigned to a zone at this location are included.
        devices = list(
            self._db.scalars(
                select(DeviceRow)
                .where(
                    DeviceRow.location_id == location_id,
                    DeviceRow.zone_id.is_not(None),
                )
                .order_by(DeviceRow.created_at.desc())
            ).all()
        )

        device_ids = [device.id for device in devices]

        # Fetch the newest reading for all assigned devices in one query.
        latest_readings_by_device = {}

        if device_ids:
            ranked_readings = (
                select(
                    ReadingRow.device_id,
                    ReadingRow.value,
                    ReadingRow.unit,
                    ReadingRow.recorded_at,
                    func.row_number()
                    .over(
                        partition_by=ReadingRow.device_id,
                        order_by=ReadingRow.recorded_at.desc(),
                    )
                    .label("reading_rank"),
                )
                .where(ReadingRow.device_id.in_(device_ids))
                .subquery()
            )

            reading_statement = select(ranked_readings).where(
                ranked_readings.c.reading_rank == 1
            )

            for row in self._db.execute(reading_statement).all():
                latest_readings_by_device[row.device_id] = OverviewReadingDto(
                    device_id=row.device_id,
                    value=float(row.value),
                    unit=row.unit,
                    recorded_at=row.recorded_at,
                    tracking_enabled=self._tracking_enabled(
                        devices, row.device_id
                    ),
                    sampling_interval_seconds=self._sampling_interval(
                        devices, row.device_id
                    ),
                )

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

            reading = latest_readings_by_device.get(device.id)
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

    @staticmethod
    def _tracking_enabled(devices, device_id: UUID) -> bool:
        return next(
            device.tracking_enabled
            for device in devices
            if device.id == device_id
        )

    @staticmethod
    def _sampling_interval(devices, device_id: UUID) -> int:
        return next(
            device.sampling_interval_seconds
            for device in devices
            if device.id == device_id
        )
