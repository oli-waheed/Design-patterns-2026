"""Composition root.

One EventBus is built for the whole process (Phase 11). Every subscriber
is attached here, and the same bus is injected into every publisher
(ReadingIngest, CommandService, ActuatorTransitionService).

Phase 12 adds:
- the dashboard WebSocket forwarder as one more bus subscriber
- the optional MQTT gateway, built only when MQTT_BROKER_URL is set
"""

from application.alerts.subscribers import register_alert_subscribers
from application.devices.service import SamplingConfigPublisher
from application.realtime.connection_manager import ConnectionManager
from application.realtime.ws_subscriber import register_websocket_subscriber
from domain.events.bus import EventBus
from infrastructure.db import SessionLocal
from infrastructure.settings import settings


def build_event_bus(manager: ConnectionManager) -> EventBus:
    bus = EventBus()
    # The WebSocket forwarder is subscribed first so a reading.created
    # frame reaches the dashboard before any alert.created it causes.
    register_websocket_subscriber(bus, manager)
    register_alert_subscribers(bus, SessionLocal)
    return bus


connection_manager = ConnectionManager()
event_bus = build_event_bus(connection_manager)


def build_mqtt_gateway():
    """Return an MqttGateway, or None when no broker URL is configured."""

    if not settings.mqtt_broker_url:
        return None

    from infrastructure.mqtt.subscriber import MqttGateway

    return MqttGateway(
        broker_url=settings.mqtt_broker_url,
        session_factory=SessionLocal,
        event_bus=event_bus,
    )


mqtt_gateway = build_mqtt_gateway()


def get_event_bus() -> EventBus:
    """FastAPI dependency returning the shared bus."""

    return event_bus


def get_sampling_config_publisher() -> SamplingConfigPublisher | None:
    """FastAPI dependency: the MQTT gateway, or None without a broker."""

    return mqtt_gateway
