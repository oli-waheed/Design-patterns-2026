"""Composition root for the Phase 11 event bus.

One EventBus is built for the whole process. Both alert subscribers are
subscribed here, and the same bus is injected into every publisher
(ReadingIngest, CommandService, ActuatorTransitionService).
"""

from application.alerts.subscribers import register_alert_subscribers
from domain.events.bus import EventBus
from infrastructure.db import SessionLocal


def build_event_bus() -> EventBus:
    bus = EventBus()
    register_alert_subscribers(bus, SessionLocal)
    return bus


event_bus = build_event_bus()


def get_event_bus() -> EventBus:
    """FastAPI dependency returning the shared bus."""

    return event_bus
