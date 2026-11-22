from datetime import datetime, timezone

from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading


class MqttSensorAdapter(SensorPort):
    """Translate an MQTT-style payload into a normalized Reading.

    Phase 5 only translates the payload.
    It does not connect to an MQTT broker.
    """

    def __init__(self, payload: dict):
        self._payload = payload

    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise ValueError("Cannot read a device without an id.")

        try:
            value = self._payload["value"]
            unit = self._payload["unit"]
        except KeyError as exc:
            raise ValueError(
                f"Missing MQTT payload field: {exc.args[0]}"
            ) from exc

        recorded_at = self._payload.get("recorded_at")

        if recorded_at is None:
            recorded_at = datetime.now(timezone.utc)

        elif isinstance(recorded_at, str):
            recorded_at = datetime.fromisoformat(
                recorded_at.replace("Z", "+00:00")
            )

        return Reading(
            device_id=device.id,
            value=float(value),
            unit=str(unit),
            source="mqtt",
            recorded_at=recorded_at,
        )
