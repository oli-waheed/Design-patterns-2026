
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.devices.entity import Device
from domain.sensors.entity import Sensor
from infrastructure.persistence.models import (
    ActuatorStateRow,
    DeviceRow,
    ZoneRow,
)


class DeviceRepository:
    def __init__(self, db: Session):
        self._db = db

    def save_sensor(self, sensor: Sensor) -> Sensor:
        sampling_interval_seconds = int(
            sensor.default_config.get("sampling_interval_seconds", 300)
        )

        row = DeviceRow(
            device_type=sensor.device_type,
            role="sensor",
            device_family="simulation",
            display_name=sensor.display_name,
            default_config=sensor.default_config,
            sampling_interval_seconds=sampling_interval_seconds,
            tracking_enabled=True,
        )

        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)

        return Sensor(
            id=row.id,
            device_type=row.device_type,
            display_name=row.display_name,
            default_config=row.default_config,
        )

    def list_sensors(self) -> list[Sensor]:
        statement = (
            select(DeviceRow)
            .where(DeviceRow.role == "sensor")
            .order_by(DeviceRow.created_at.desc())
        )

        rows = self._db.scalars(statement).all()

        return [
            Sensor(
                id=row.id,
                device_type=row.device_type,
                display_name=row.display_name,
                default_config=row.default_config,
            )
            for row in rows
        ]

    def save_device(self, device: Device) -> Device:
        row = DeviceRow(
            device_type=device.device_type,
            role=device.role,
            device_family=device.device_family,
            display_name=device.display_name,
            default_config=device.default_config,
            sampling_interval_seconds=device.sampling_interval_seconds,
            tracking_enabled=device.tracking_enabled,
        )

        try:
            self._db.add(row)
            self._db.flush()

            if row.role == "actuator":
                self._db.add(
                    ActuatorStateRow(
                        device_id=row.id,
                        state="idle",
                    )
                )

            self._db.commit()
            self._db.refresh(row)

            return self._row_to_device(row)

        except Exception:
            self._db.rollback()
            raise

    def save_devices(self, devices: list[Device]) -> list[Device]:
        rows = [
            DeviceRow(
                device_type=device.device_type,
                role=device.role,
                device_family=device.device_family,
                display_name=device.display_name,
                default_config=device.default_config,
                sampling_interval_seconds=device.sampling_interval_seconds,
                tracking_enabled=device.tracking_enabled,
            )
            for device in devices
        ]

        try:
            self._db.add_all(rows)
            self._db.flush()

            actuator_states = [
                ActuatorStateRow(
                    device_id=row.id,
                    state="idle",
                )
                for row in rows
                if row.role == "actuator"
            ]

            if actuator_states:
                self._db.add_all(actuator_states)

            self._db.commit()

            for row in rows:
                self._db.refresh(row)

            return [self._row_to_device(row) for row in rows]

        except Exception:
            self._db.rollback()
            raise

    def get_device_by_id(self, device_id: UUID) -> Device | None:
        row = self._db.get(DeviceRow, device_id)

        if row is None:
            return None

        return self._row_to_device(row)

    def list_devices(
        self,
        device_family: str | None = None,
        role: str | None = None,
    ) -> list[Device]:
        statement = select(DeviceRow)

        if device_family is not None:
            statement = statement.where(
                DeviceRow.device_family == device_family
            )

        if role is not None:
            statement = statement.where(
                DeviceRow.role == role
            )

        statement = statement.order_by(DeviceRow.created_at.desc())

        rows = self._db.scalars(statement).all()

        return [
            self._row_to_device(row)
            for row in rows
        ]

    def get_actuator_state(self, device_id: UUID) -> str | None:
        statement = select(ActuatorStateRow.state).where(
            ActuatorStateRow.device_id == device_id
        )

        return self._db.scalar(statement)

    def get_actuator_state_details(
        self,
        device_id: UUID,
    ) -> dict | None:
        """Return actuator state and its last update timestamp."""
        row = self._db.get(ActuatorStateRow, device_id)

        if row is None:
            return None

        return {
            "state": row.state,
            "updated_at": row.updated_at,
        }

    def update_actuator_state(
        self,
        device_id: UUID,
        state: str,
    ) -> bool:
        row = self._db.get(ActuatorStateRow, device_id)

        if row is None:
            return False

        try:
            row.state = state
            self._db.commit()
            self._db.refresh(row)
            return True

        except Exception:
            self._db.rollback()
            raise

    def assign_zone(
        self,
        device_id: UUID,
        zone_id: UUID | None,
    ) -> bool:
        device = self._db.get(DeviceRow, device_id)

        if device is None:
            return False

        try:
            if zone_id is None:
                device.zone_id = None
                device.location_id = None
            else:
                zone = self._db.get(ZoneRow, zone_id)

                if zone is None:
                    raise ValueError("Zone not found.")

                device.zone_id = zone.id
                device.location_id = zone.location_id

            self._db.commit()
            self._db.refresh(device)

            return True

        except Exception:
            self._db.rollback()
            raise

    def update_sampling(
        self,
        device_id: UUID,
        sampling_interval_seconds: int,
        tracking_enabled: bool,
    ) -> Device | None:
        device = self._db.get(DeviceRow, device_id)

        if device is None:
            return None

        device.sampling_interval_seconds = sampling_interval_seconds
        device.tracking_enabled = tracking_enabled

        self._db.commit()
        self._db.refresh(device)

        return self._row_to_device(device)

    def list_devices_in_zone(
        self,
        location_id: UUID,
        zone_id: UUID,
    ) -> list[Device]:
        zone = self._db.get(ZoneRow, zone_id)

        if zone is None:
            raise ValueError("Zone not found.")

        if zone.location_id != location_id:
            raise ValueError(
                "Zone does not belong to this location."
            )

        statement = (
            select(DeviceRow)
            .where(DeviceRow.zone_id == zone_id)
            .order_by(DeviceRow.created_at.desc())
        )

        rows = self._db.scalars(statement).all()

        return [
            self._row_to_device(row)
            for row in rows
        ]

    @staticmethod
    def _row_to_device(row: DeviceRow) -> Device:
        return Device(
            id=row.id,
            device_type=row.device_type,
            role=row.role,
            device_family=row.device_family,
            display_name=row.display_name,
            default_config=row.default_config,
            zone_id=row.zone_id,
            location_id=row.location_id,
            sampling_interval_seconds=row.sampling_interval_seconds,
            tracking_enabled=row.tracking_enabled,
        )
