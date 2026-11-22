from datetime import datetime
from typing import Any
from uuid import UUID

from application.realtime.connection_manager import ConnectionManager
from domain.events.bus import EventBus
from domain.events.events import (
    ActuatorStateChanged,
    AlertCreated,
    ReadingCreated,
)


def _id(value: UUID | None) -> str | None:
    return str(value) if value is not None else None


def _time(value: datetime) -> str:
    return value.isoformat()


def envelope(message_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """WebSocket JSON envelope: { "type": ..., "payload": {...} }."""

    return {"type": message_type, "payload": payload}


class WebSocketEventForwarder:
    """Observer subscriber that forwards bus events to dashboard sockets.

    It only converts events to JSON. It never writes alerts or readings and
    contains no Strategy, Command, or Adapter logic.
    """

    def __init__(self, manager: ConnectionManager) -> None:
        self._manager = manager

    def on_reading_created(self, event: ReadingCreated) -> None:
        self._manager.broadcast_threadsafe(
            envelope(
                "reading.created",
                {
                    "device_id": _id(event.device_id),
                    "value": event.value,
                    "unit": event.unit,
                    "source": event.source,
                    "recorded_at": _time(event.recorded_at),
                    "location_id": _id(event.location_id),
                    "zone_id": _id(event.zone_id),
                },
            )
        )

    def on_state_changed(self, event: ActuatorStateChanged) -> None:
        self._manager.broadcast_threadsafe(
            envelope(
                "actuator.state_changed",
                {
                    "device_id": _id(event.device_id),
                    "previous_state": event.previous_state,
                    "state": event.state,
                    "location_id": _id(event.location_id),
                    "zone_id": _id(event.zone_id),
                },
            )
        )

    def on_alert_created(self, event: AlertCreated) -> None:
        self._manager.broadcast_threadsafe(
            envelope(
                "alert.created",
                {
                    "id": _id(event.alert_id),
                    "severity": event.severity,
                    "message": event.message,
                    "event_type": event.event_type_source,
                    "status": "active",
                    "created_at": _time(event.created_at),
                    "device_id": _id(event.device_id),
                    "location_id": _id(event.location_id),
                    "zone_id": _id(event.zone_id),
                },
            )
        )


def register_websocket_subscriber(
    bus: EventBus,
    manager: ConnectionManager,
) -> WebSocketEventForwarder:
    forwarder = WebSocketEventForwarder(manager)

    bus.subscribe(ReadingCreated, forwarder.on_reading_created)
    bus.subscribe(ActuatorStateChanged, forwarder.on_state_changed)
    bus.subscribe(AlertCreated, forwarder.on_alert_created)

    return forwarder
