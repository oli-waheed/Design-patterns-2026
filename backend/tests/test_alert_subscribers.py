from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

from application.alerts.subscribers import (
    AlertPersistenceSubscriber,
    MoistureThresholdSubscriber,
    register_alert_subscribers,
)
from domain.events.bus import EventBus
from domain.events.events import (
    ActuatorStateChanged,
    AlertCreated,
    CommandFailed,
    ReadingCreated,
    ThresholdCrossed,
)
from domain.locations.entity import Zone
from infrastructure.db import SessionLocal
from infrastructure.persistence.alert_repository import AlertRepository
from infrastructure.persistence.models import AlertRow


def make_reading(value=0.10, unit="vwc", zone_id=None):
    return ReadingCreated(
        device_id=uuid4(),
        value=value,
        unit=unit,
        source="simulation",
        recorded_at=datetime.now(timezone.utc),
        location_id=uuid4() if zone_id else None,
        zone_id=zone_id,
    )


def make_threshold_subscriber(monkeypatch, low=0.20):
    bus = EventBus()
    published = []
    bus.subscribe(ThresholdCrossed, published.append)

    zone = Zone(
        id=uuid4(),
        name="Bench 1",
        moisture_threshold_low=low,
        moisture_threshold_high=0.60,
    )

    monkeypatch.setattr(
        "application.alerts.subscribers.LocationRepository",
        lambda db: Mock(get_zone=Mock(return_value=zone)),
    )

    subscriber = MoistureThresholdSubscriber(
        bus=bus,
        session_factory=Mock,
    )

    return subscriber, published, zone


def test_threshold_subscriber_publishes_below_zone_low(monkeypatch):
    subscriber, published, zone = make_threshold_subscriber(monkeypatch)

    event = make_reading(value=0.10, zone_id=zone.id)
    subscriber.on_reading(event)

    assert len(published) == 1
    assert published[0].moisture == 0.10
    assert published[0].threshold_low == 0.20
    assert published[0].zone_id == zone.id
    assert published[0].location_id == event.location_id


def test_threshold_subscriber_ignores_value_equal_to_low(monkeypatch):
    subscriber, published, zone = make_threshold_subscriber(monkeypatch)

    subscriber.on_reading(make_reading(value=0.20, zone_id=zone.id))

    assert published == []


def test_threshold_subscriber_ignores_non_moisture_units(monkeypatch):
    subscriber, published, zone = make_threshold_subscriber(monkeypatch)

    subscriber.on_reading(
        make_reading(value=0.10, unit="lux", zone_id=zone.id)
    )

    assert published == []


def test_threshold_subscriber_ignores_unassigned_device(monkeypatch):
    subscriber, published, _ = make_threshold_subscriber(monkeypatch)

    subscriber.on_reading(make_reading(value=0.10, zone_id=None))

    assert published == []


def get_alert(alert_id):
    db = SessionLocal()
    try:
        return db.get(AlertRow, alert_id)
    finally:
        db.close()


def capture_alert_created(bus):
    created = []
    bus.subscribe(AlertCreated, created.append)
    return created


def test_persistence_subscriber_inserts_command_failed_row():
    bus = EventBus()
    register_alert_subscribers(bus, SessionLocal)
    created = capture_alert_created(bus)

    bus.publish(
        CommandFailed(
            device_id=None,
            command_type="stop_pump",
            message="Max run time exceeded",
        )
    )

    assert len(created) == 1
    row = get_alert(created[0].alert_id)

    assert row.event_type == "command.failed"
    assert row.severity == "warning"
    assert row.message == "Max run time exceeded"
    assert row.status == "active"
    assert row.location_id is None
    assert row.zone_id is None


def test_persistence_subscriber_stores_only_error_state_changes():
    bus = EventBus()
    register_alert_subscribers(bus, SessionLocal)
    created = capture_alert_created(bus)

    bus.publish(
        ActuatorStateChanged(
            device_id=None,
            previous_state="idle",
            state="running",
        )
    )

    assert created == []

    bus.publish(
        ActuatorStateChanged(
            device_id=None,
            previous_state="running",
            state="error",
        )
    )

    assert len(created) == 1
    row = get_alert(created[0].alert_id)

    assert row.event_type == "state.changed"
    assert row.severity == "critical"
    assert row.message == "Actuator entered error"


def test_persistence_subscriber_inserts_threshold_row():
    bus = EventBus()
    subscriber = AlertPersistenceSubscriber(bus, SessionLocal)
    created = capture_alert_created(bus)

    subscriber.on_threshold(
        ThresholdCrossed(
            device_id=None,
            moisture=0.10,
            threshold_low=0.20,
        )
    )

    row = get_alert(created[0].alert_id)

    assert row.event_type == "threshold.crossed"
    assert row.severity == "warning"
    assert row.message == "Moisture below zone low"


def test_alert_repository_status_all_includes_every_status():
    db = SessionLocal()

    try:
        repository = AlertRepository(db)
        row = repository.save(
            event_type="command.failed",
            severity="warning",
            message="resolved example",
        )
        row.status = "resolved"
        db.commit()

        active_ids = {a.id for a in repository.list_alerts("active", limit=200)}
        all_ids = {a.id for a in repository.list_alerts(None, limit=200)}

        assert row.id not in active_ids
        assert row.id in all_ids
    finally:
        db.close()
