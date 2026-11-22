from datetime import datetime, timedelta, timezone

from domain.devices.family_factory import get_family_factory
from infrastructure.db import SessionLocal
from infrastructure.persistence.device_repository import DeviceRepository


def test_state_update_timestamp_is_utc_aware():
    """updated_at must be the real current time, independent of the
    machine's local time zone, so the max-runtime check is correct."""
    db = SessionLocal()
    pump = None

    try:
        repository = DeviceRepository(db)

        devices = repository.save_devices(
            get_family_factory("simulation").create_device_set()
        )

        pump = next(d for d in devices if d.device_type == "water_pump")

        assert repository.update_actuator_state(
            device_id=pump.id,
            state="running",
        )

        details = repository.get_actuator_state_details(pump.id)
        updated_at = details["updated_at"]

        assert updated_at.tzinfo is not None
        assert abs(
            datetime.now(timezone.utc) - updated_at
        ) < timedelta(minutes=1)
    finally:
        if pump is not None:
            repository.update_actuator_state(
                device_id=pump.id,
                state="idle",
            )
        db.close()
