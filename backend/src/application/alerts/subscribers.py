import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from domain.events.bus import EventBus
from domain.events.events import (
    ActuatorStateChanged,
    AlertCreated,
    CommandFailed,
    ReadingCreated,
    ThresholdCrossed,
)
from infrastructure.persistence.alert_repository import AlertRepository
from infrastructure.persistence.location_repository import (
    LocationRepository,
)


logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Session]


class MoistureThresholdSubscriber:
    """Concrete observer: turns low-moisture readings into ThresholdCrossed.

    It does not write alerts itself; it publishes a new event and lets the
    persistence subscriber decide what to store.
    """

    def __init__(
        self,
        bus: EventBus,
        session_factory: SessionFactory,
    ) -> None:
        self._bus = bus
        self._session_factory = session_factory

    def on_reading(self, event: ReadingCreated) -> None:
        if event.unit != "vwc":
            return

        # Unassigned devices have no zone, so there is no threshold.
        if event.zone_id is None:
            return

        db = self._session_factory()

        try:
            zone = LocationRepository(db).get_zone(event.zone_id)
        finally:
            db.close()

        if zone is None:
            return

        if event.value < zone.moisture_threshold_low:
            self._bus.publish(
                ThresholdCrossed(
                    device_id=event.device_id,
                    moisture=event.value,
                    threshold_low=zone.moisture_threshold_low,
                    location_id=event.location_id,
                    zone_id=event.zone_id,
                )
            )


class AlertPersistenceSubscriber:
    """Concrete observer: the only object that inserts alert rows."""

    def __init__(
        self,
        bus: EventBus,
        session_factory: SessionFactory,
    ) -> None:
        self._bus = bus
        self._session_factory = session_factory

    def on_threshold(self, event: ThresholdCrossed) -> None:
        self._insert(
            event_type=ThresholdCrossed.event_type,
            severity="warning",
            message="Moisture below zone low",
            event=event,
        )

    def on_command(self, event: CommandFailed) -> None:
        self._insert(
            event_type=CommandFailed.event_type,
            severity="warning",
            message=event.message,
            event=event,
        )

    def on_state(self, event: ActuatorStateChanged) -> None:
        # Every state save is published, but only errors become alerts.
        if event.state != "error":
            return

        self._insert(
            event_type=ActuatorStateChanged.event_type,
            severity="critical",
            message="Actuator entered error",
            event=event,
        )

    def _insert(
        self,
        event_type: str,
        severity: str,
        message: str,
        event: ThresholdCrossed | CommandFailed | ActuatorStateChanged,
    ) -> None:
        db = self._session_factory()

        try:
            row = AlertRepository(db).save(
                event_type=event_type,
                severity=severity,
                message=message,
                location_id=event.location_id,
                zone_id=event.zone_id,
                device_id=event.device_id,
            )

            alert = AlertCreated(
                alert_id=row.id,
                event_type_source=row.event_type,
                severity=row.severity,
                message=row.message,
                created_at=row.created_at,
                device_id=row.device_id,
                location_id=row.location_id,
                zone_id=row.zone_id,
            )
        finally:
            db.close()

        # Handoff for Phase 12: the dashboard socket subscribes here.
        self._bus.publish(alert)


def register_alert_subscribers(
    bus: EventBus,
    session_factory: SessionFactory,
) -> None:
    """Subscribe both alert handlers to the bus."""

    threshold_subscriber = MoistureThresholdSubscriber(
        bus=bus,
        session_factory=session_factory,
    )
    persistence_subscriber = AlertPersistenceSubscriber(
        bus=bus,
        session_factory=session_factory,
    )

    bus.subscribe(ReadingCreated, threshold_subscriber.on_reading)
    bus.subscribe(ThresholdCrossed, persistence_subscriber.on_threshold)
    bus.subscribe(CommandFailed, persistence_subscriber.on_command)
    bus.subscribe(ActuatorStateChanged, persistence_subscriber.on_state)
