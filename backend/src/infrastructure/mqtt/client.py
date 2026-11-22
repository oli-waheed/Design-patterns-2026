from urllib.parse import urlparse


def create_mqtt_client(broker_url: str, client_id: str):
    """Create a paho client for mqtt://host:port (not connected yet).

    paho is imported here, so the backend never needs it unless a broker
    URL is configured.
    """

    import paho.mqtt.client as mqtt

    parsed = urlparse(broker_url)

    if parsed.scheme not in {"mqtt", "tcp"} or not parsed.hostname:
        raise ValueError(
            f"Unsupported MQTT broker URL: {broker_url}. "
            "Use mqtt://host:port."
        )

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
    )

    if parsed.username:
        client.username_pw_set(parsed.username, parsed.password)

    return client, parsed.hostname, parsed.port or 1883
