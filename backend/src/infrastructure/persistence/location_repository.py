from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.locations.entity import Location, LocationConfig, Zone
from infrastructure.persistence.models import (
    DeviceRow,
    LocationRow,
    ZoneRow,
)


class LocationRepository:
    def __init__(self, db: Session):
        self._db = db

    def save_config(
        self,
        config: LocationConfig,
    ) -> LocationConfig:
        try:
            location = config.location

            location_row = LocationRow(
                name=location.name,
            )

            self._db.add(location_row)
            self._db.flush()

            zone_rows = []

            for zone in location.zones:
                zone_row = ZoneRow(
                    location_id=location_row.id,
                    name=zone.name,
                    moisture_threshold_low=zone.moisture_threshold_low,
                    moisture_threshold_high=zone.moisture_threshold_high,
                    schedule=zone.schedule,
                )

                self._db.add(zone_row)
                zone_rows.append(zone_row)

            self._db.flush()
            self._db.commit()

            return self._rows_to_config(
                location_row,
                zone_rows,
            )

        except Exception:
            self._db.rollback()
            raise

    def get_config(
        self,
        location_id: UUID,
    ) -> LocationConfig | None:
        statement = (
            select(LocationRow)
            .where(LocationRow.id == location_id)
        )

        location_row = self._db.scalars(
            statement
        ).first()

        if location_row is None:
            return None

        zone_statement = (
            select(ZoneRow)
            .where(
                ZoneRow.location_id == location_id
            )
            .order_by(ZoneRow.name)
        )

        zone_rows = self._db.scalars(
            zone_statement
        ).all()

        return self._rows_to_config(
            location_row,
            list(zone_rows),
        )

    def list_locations(
        self,
    ) -> list[LocationRow]:
        statement = (
            select(LocationRow)
            .order_by(
                LocationRow.created_at.desc()
            )
        )

        return list(
            self._db.scalars(statement).all()
        )

    def delete_location(
        self,
        location_id: UUID,
    ) -> bool:
        location_row = self._db.get(
            LocationRow,
            location_id,
        )

        if location_row is None:
            return False

        try:
            self._db.delete(location_row)
            self._db.commit()

            return True

        except Exception:
            self._db.rollback()
            raise

    def add_zone(
        self,
        location_id: UUID,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict,
    ) -> Zone:
        location_statement = (
            select(LocationRow)
            .where(LocationRow.id == location_id)
        )

        location = self._db.scalars(
            location_statement
        ).first()

        if location is None:
            raise ValueError(
                "Location not found."
            )

        zone = ZoneRow(
            location_id=location_id,
            name=name,
            moisture_threshold_low=moisture_threshold_low,
            moisture_threshold_high=moisture_threshold_high,
            schedule=schedule,
        )

        try:
            self._db.add(zone)
            self._db.commit()
            self._db.refresh(zone)

            return self._row_to_zone(zone)

        except Exception:
            self._db.rollback()
            raise

    def update_zone(
        self,
        location_id: UUID,
        zone_id: UUID,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict,
    ) -> Zone | None:
        zone_statement = (
            select(ZoneRow)
            .where(ZoneRow.id == zone_id)
        )

        zone = self._db.scalars(
            zone_statement
        ).first()

        if zone is None:
            return None

        if zone.location_id != location_id:
            return None

        try:
            zone.name = name
            zone.moisture_threshold_low = (
                moisture_threshold_low
            )
            zone.moisture_threshold_high = (
                moisture_threshold_high
            )
            zone.schedule = schedule

            self._db.commit()
            self._db.refresh(zone)

            return self._row_to_zone(zone)

        except Exception:
            self._db.rollback()
            raise

    def delete_zone(
        self,
        location_id: UUID,
        zone_id: UUID,
    ) -> bool:
        zone_statement = (
            select(ZoneRow)
            .where(ZoneRow.id == zone_id)
        )

        zone = self._db.scalars(
            zone_statement
        ).first()

        if zone is None:
            return False

        if zone.location_id != location_id:
            return False

        zone_count_statement = (
            select(ZoneRow)
            .where(
                ZoneRow.location_id == location_id
            )
        )

        zones = self._db.scalars(
            zone_count_statement
        ).all()

        if len(zones) <= 1:
            raise ValueError(
                "A location must have at least one zone."
            )

        try:
            device_statement = (
                select(DeviceRow)
                .where(
                    DeviceRow.zone_id == zone_id
                )
            )

            devices = self._db.scalars(
                device_statement
            ).all()

            for device in devices:
                device.zone_id = None
                device.location_id = None

            self._db.delete(zone)
            self._db.commit()

            return True

        except Exception:
            self._db.rollback()
            raise

    @staticmethod
    def _row_to_zone(
        row: ZoneRow,
    ) -> Zone:
        return Zone(
            id=row.id,
            name=row.name,
            moisture_threshold_low=float(
                row.moisture_threshold_low
            ),
            moisture_threshold_high=float(
                row.moisture_threshold_high
            ),
            schedule=row.schedule,
        )

    @staticmethod
    def _rows_to_config(
        location_row: LocationRow,
        zone_rows: list[ZoneRow],
    ) -> LocationConfig:
        zones = tuple(
            Zone(
                id=zone_row.id,
                name=zone_row.name,
                moisture_threshold_low=float(
                    zone_row.moisture_threshold_low
                ),
                moisture_threshold_high=float(
                    zone_row.moisture_threshold_high
                ),
                schedule=zone_row.schedule,
            )
            for zone_row in zone_rows
        )

        location = Location(
            id=location_row.id,
            name=location_row.name,
            zones=zones,
        )

        return LocationConfig(
            location=location,
        )