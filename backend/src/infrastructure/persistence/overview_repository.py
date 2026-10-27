
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from infrastructure.persistence.models import (
    DeviceRow,
    LocationRow,
    ReadingRow,
    ZoneRow,
)


class OverviewRepository:
    """Database queries used to assemble a location overview."""

    def __init__(self, db: Session):
        self._db = db

    def get_location(self, location_id: UUID) -> LocationRow | None:
        return self._db.get(LocationRow, location_id)

    def list_zones(self, location_id: UUID) -> list[ZoneRow]:
        statement = (
            select(ZoneRow)
            .where(ZoneRow.location_id == location_id)
            .order_by(ZoneRow.name)
        )
        return list(self._db.scalars(statement).all())

    def list_assigned_devices(self, location_id: UUID) -> list[DeviceRow]:
        statement = (
            select(DeviceRow)
            .where(
                DeviceRow.location_id == location_id,
                DeviceRow.zone_id.is_not(None),
            )
            .order_by(DeviceRow.created_at.desc())
        )
        return list(self._db.scalars(statement).all())

    def get_latest_readings(
        self,
        device_ids: list[UUID],
    ) -> list:
        """Return one newest reading row per device in a single query."""
        if not device_ids:
            return []

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

        statement = select(ranked_readings).where(
            ranked_readings.c.reading_rank == 1
        )

        return list(self._db.execute(statement).all())
