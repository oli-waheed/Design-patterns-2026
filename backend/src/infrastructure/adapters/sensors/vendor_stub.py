from datetime import datetime, timezone
from uuid import UUID

from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading


class VendorSensorAdapter(SensorPort):
    """Translate a vendor-specific sensor payload into a Reading."""

    def __init__(self, vendor_payload: dict):
        self._vendor_payload = vendor_payload

    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise ValueError("Cannot read a device without an id.")

        try:
            raw_device_id = self._vendor_payload["sensorId"]
            raw_value = self._vendor_payload["readingValue"]
            raw_unit = self._vendor_payload["measurementUnit"]
        except KeyError as exc:
            raise ValueError(
                f"Missing vendor field: {exc.args[0]}"
            ) from exc

        device_id = UUID(str(raw_device_id))

        raw_time = self._vendor_payload.get("time")

        if raw_time is None:
            recorded_at = datetime.now(timezone.utc)

        elif isinstance(raw_time, datetime):
            recorded_at = raw_time

        else:
            recorded_at = datetime.fromisoformat(
                str(raw_time).replace("Z", "+00:00")
            )

        return Reading(
            device_id=device_id,
            value=float(raw_value),
            unit=str(raw_unit),
            source="vendor",
            recorded_at=recorded_at,
        )