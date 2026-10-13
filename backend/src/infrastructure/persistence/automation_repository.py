
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.persistence.models import (
    AutomationRuleRow,
    DeviceRow,
    LocationRow,
    ReadingRow,
    ZoneRow,
)


class AutomationRepository:
    """Database operations used by greenhouse automation."""

    def __init__(self, db: Session):
        self._db = db

    def location_exists(self, location_id: UUID) -> bool:
        return self._db.get(LocationRow, location_id) is not None

    def get_strategy_key(self, location_id: UUID) -> str | None:
        rule = self._db.scalars(
            select(AutomationRuleRow).where(
                AutomationRuleRow.location_id == location_id
            )
        ).first()

        if rule is None:
            return None

        return rule.strategy_key

    def save_strategy_key(
        self,
        location_id: UUID,
        strategy_key: str,
    ) -> str:
        """Save the strategy selected for a location."""
        try:
            rule = self._db.scalars(
                select(AutomationRuleRow).where(
                    AutomationRuleRow.location_id == location_id
                )
            ).first()

            if rule is None:
                rule = AutomationRuleRow(
                    location_id=location_id,
                    strategy_key=strategy_key,
                    parameters={},
                )
                self._db.add(rule)
            else:
                rule.strategy_key = strategy_key

            self._db.commit()
            self._db.refresh(rule)
            return rule.strategy_key

        except Exception:
            self._db.rollback()
            raise

    def list_zones(self, location_id: UUID) -> list[ZoneRow]:
        statement = (
            select(ZoneRow)
            .where(ZoneRow.location_id == location_id)
            .order_by(ZoneRow.name)
        )
        return list(self._db.scalars(statement).all())

    def latest_moisture_for_zone(
        self,
        zone_id: UUID,
    ) -> float | None:
        """Return the latest moisture reading for a zone, if available."""
        statement = (
            select(ReadingRow.value)
            .join(
                DeviceRow,
                ReadingRow.device_id == DeviceRow.id,
            )
            .where(
                DeviceRow.zone_id == zone_id,
                DeviceRow.role == "sensor",
                DeviceRow.device_type.ilike("%moisture%"),
            )
            .order_by(ReadingRow.recorded_at.desc())
            .limit(1)
        )

        value = self._db.scalars(statement).first()

        if value is None:
            return None

        return float(value)
