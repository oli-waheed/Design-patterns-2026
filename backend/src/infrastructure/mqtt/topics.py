"""MQTT topic names. "greenhouse/" is a channel prefix, not a column."""

from uuid import UUID


READING_TOPIC_FILTER = "greenhouse/devices/+/reading"


def reading_topic(device_id: UUID | str) -> str:
    return f"greenhouse/devices/{device_id}/reading"


def config_topic(device_id: UUID | str) -> str:
    return f"greenhouse/devices/{device_id}/config"


def device_id_from_reading_topic(topic: str) -> UUID | None:
    """Return the device id from greenhouse/devices/{id}/reading."""

    parts = topic.split("/")

    if (
        len(parts) != 4
        or parts[0] != "greenhouse"
        or parts[1] != "devices"
        or parts[3] != "reading"
    ):
        return None

    try:
        return UUID(parts[2])
    except ValueError:
        return None
