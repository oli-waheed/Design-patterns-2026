"""Publish one MQTT reading for the Phase 12 smoke test.

Usage (from backend/, with the mqtt Compose profile running):

    python scripts/mqtt_smoke.py <device-id> [value] [broker-url]
"""

import json
import sys

import paho.mqtt.client as mqtt


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)

    device_id = sys.argv[1]
    value = float(sys.argv[2]) if len(sys.argv) > 2 else 0.37
    broker = sys.argv[3] if len(sys.argv) > 3 else "localhost"

    topic = f"greenhouse/devices/{device_id}/reading"
    body = json.dumps({"value": value, "unit": "vwc"})

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(broker, 1883)
    client.loop_start()
    client.publish(topic, body, qos=1).wait_for_publish(timeout=5)
    client.loop_stop()
    client.disconnect()

    print(f"Published {body} to {topic}")


if __name__ == "__main__":
    main()
