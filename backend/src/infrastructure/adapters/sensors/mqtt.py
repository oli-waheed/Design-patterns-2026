from datetime import datetime, timezone

from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from domain.sensors.reading import Reading


class MqttSensorAdapter(SensorPort):
    """Translate a pushed payload dict into a normalized Reading.

    This is the Phase 5 translator. It never opens a connection itself.
    Phase 12 reuses it for both push paths: the optional MQTT broker
    subscriber (source "mqtt") and device HTTP POST (source "http").
    """

    def __init__(self, payload: dict, source: str = "mqtt"):
        self._payload = payload
        self._source = source

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
            source=self._source,
            recorded_at=recorded_at,
        )
