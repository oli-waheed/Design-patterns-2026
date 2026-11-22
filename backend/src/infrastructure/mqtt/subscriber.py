import json
import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from application.readings.service import ReadingIngest
from domain.events.bus import EventBus
from infrastructure.mqtt.client import create_mqtt_client
from infrastructure.mqtt.topics import (
    READING_TOPIC_FILTER,
    config_topic,
    device_id_from_reading_topic,
)
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository


logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Session]


def handle_reading_message(
    topic: str,
    payload: bytes,
    session_factory: SessionFactory,
    event_bus: EventBus,
) -> bool:
    """Translate one broker message and pass it to ReadingIngest.

    Returns True when a reading was stored. Unknown devices and bad
    payloads are logged and dropped. This function never inserts rows or
    publishes events itself; ReadingIngest does both.
    """

    device_id = device_id_from_reading_topic(topic)

    if device_id is None:
        logger.warning("Dropping MQTT message on unexpected topic %s", topic)
        return False

    try:
        body = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("Dropping MQTT message with invalid JSON on %s", topic)
        return False

    if not isinstance(body, dict):
        logger.warning("Dropping MQTT message that is not an object on %s", topic)
        return False

    db = session_factory()

    try:
        ingest = ReadingIngest(
            device_repository=DeviceRepository(db),
            reading_repository=ReadingRepository(db),
            event_bus=event_bus,
        )

        ingest.record_payload(device_id, body, source="mqtt")
        return True

    except ValueError as exc:
        # Includes "Device not found." for unknown devices.
        logger.warning("Dropping MQTT reading for %s: %s", device_id, exc)
        return False

    finally:
        db.close()


class MqttGateway:
    """Optional broker connection, started only when a URL is configured.

    - Subscribes to greenhouse/devices/+/reading and hands each message to
      ReadingIngest through handle_reading_message.
    - Publishes retained sampling config on greenhouse/devices/{id}/config
      (implements SamplingConfigPublisher for DevicesService).
    """

    def __init__(
        self,
        broker_url: str,
        session_factory: SessionFactory,
        event_bus: EventBus,
    ) -> None:
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._client, self._host, self._port = create_mqtt_client(
            broker_url,
            client_id="greenhouse-backend",
        )
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    def start(self) -> None:
        # connect_async + loop_start: the backend still starts if the broker
        # is down, and paho keeps reconnecting in its own thread.
        self._client.connect_async(self._host, self._port)
        self._client.loop_start()
        logger.info("MQTT gateway started for %s:%s", self._host, self._port)

    def stop(self) -> None:
        self._client.disconnect()
        self._client.loop_stop()

    def publish_sampling_config(
        self,
        device_id,
        sampling_interval_seconds: int,
        tracking_enabled: bool,
    ) -> None:
        message = json.dumps(
            {
                "sampling_interval_seconds": sampling_interval_seconds,
                "tracking_enabled": tracking_enabled,
            }
        )

        self._client.publish(
            config_topic(device_id),
            message,
            qos=1,
            retain=True,
        )

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        # Re-subscribe on every (re)connect.
        client.subscribe(READING_TOPIC_FILTER, qos=1)

    def _on_message(self, client, userdata, message) -> None:
        handle_reading_message(
            topic=message.topic,
            payload=message.payload,
            session_factory=self._session_factory,
            event_bus=self._event_bus,
        )
