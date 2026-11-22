from typing import Any

from domain.devices.entity import Device
from domain.sensors.ports import SensorPort

from infrastructure.adapters.sensors.mqtt import MqttSensorAdapter
from infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from infrastructure.adapters.sensors.vendor_stub import VendorSensorAdapter


class SensorAdapterSelector:
    """Select the sensor adapter based on the device configuration."""

    @staticmethod
    def select(
        device: Device,
        vendor_payload: dict[str, Any] | None = None,
        mqtt_payload: dict[str, Any] | None = None,
    ) -> SensorPort:

        protocol = device.default_config.get(
            "protocol",
            "simulation",
        )

        if protocol == "simulation":
            return SimulationSensorAdapter()

        if protocol == "mqtt":
            if mqtt_payload is None:
                raise ValueError(
                    "MQTT payload is required for an MQTT sensor."
                )

            return MqttSensorAdapter(mqtt_payload)

        if protocol == "vendor_stub":
            if vendor_payload is None:
                raise ValueError(
                    "Vendor payload is required for a vendor sensor."
                )

            return VendorSensorAdapter(vendor_payload)

        raise ValueError(
            f"Unsupported sensor protocol: {protocol}"
        )