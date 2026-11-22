from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


# Domain events are plain immutable facts about something that already
# happened. location_id and zone_id are copied from the device when the
# event is published, and stay None when the device is unassigned.


@dataclass(frozen=True)
class ReadingCreated:
    """reading.created: a tracked reading was stored."""

    device_id: UUID
    value: float
    unit: str
    source: str
    recorded_at: datetime
    location_id: UUID | None = None
    zone_id: UUID | None = None

    event_type = "reading.created"


@dataclass(frozen=True)
class ThresholdCrossed:
    """threshold.crossed: moisture fell strictly below the zone low."""

    device_id: UUID
    moisture: float
    threshold_low: float
    location_id: UUID | None = None
    zone_id: UUID | None = None

    event_type = "threshold.crossed"


@dataclass(frozen=True)
class CommandFailed:
    """command.failed: an actuator command failed during execution."""

    device_id: UUID
    command_type: str
    message: str
    location_id: UUID | None = None
    zone_id: UUID | None = None

    event_type = "command.failed"


@dataclass(frozen=True)
class ActuatorStateChanged:
    """state.changed: an actuator state was saved."""

    device_id: UUID
    previous_state: str
    state: str
    location_id: UUID | None = None
    zone_id: UUID | None = None

    event_type = "state.changed"


@dataclass(frozen=True)
class AlertCreated:
    """alert.created: an alert row was inserted.

    Nothing subscribes in Phase 11. Phase 12 subscribes the dashboard
    WebSocket to this event instead of re-implementing pub/sub.
    """

    alert_id: UUID
    event_type_source: str
    severity: str
    message: str
    created_at: datetime
    device_id: UUID | None = None
    location_id: UUID | None = None
    zone_id: UUID | None = None

    event_type = "alert.created"
