# Adapter Pattern — Smart Greenhouse

## Problem

Sensor readings arrive in different shapes. The simulation produces numbers in memory, a vendor device sends fields such as `sensorId`, `readingValue` and `measurementUnit`, and MQTT or HTTP devices push a small JSON payload. If the reading service understood every format, each new device type would mean editing business code, and vendor field names would leak into the rest of the application.

## Pattern and intent

**Adapter** converts an interface the application cannot use directly into the one it expects. In this project every adapter turns its own input into the same normalized `Reading` (`device_id`, `value`, `unit`, `source`, `recorded_at`), so the rest of the system never sees vendor formats.

## Participants

| Role | Class | Notes |
|---|---|---|
| Target interface (port) | `SensorPort` | `read(device) -> Reading` |
| Adapters | `SimulationSensorAdapter` | Generates readings, `source = "simulation"` |
| | `VendorSensorAdapter` | Translates vendor field names; rejects a payload whose `sensorId` does not match the device |
| | `MqttSensorAdapter` | The Phase 5 translator for pushed payloads `{value, unit}`; `source` is `mqtt` (broker) or `http` (device HTTP, Phase 12) |
| Selector | `SensorAdapterSelector` | Picks the adapter from the device's `protocol` |
| Client | `ReadingIngest` | The single writer of `sensor_readings`; publishes `reading.created` (Observer) |

The actuator side has the same idea: `ActuatorPort.apply()` is the target and `SimulationActuatorAdapter` is the adapter. The Phase 9 decorators wrap that port.

## Flow

1. `POST /api/sensors/{id}/read` (or the simulation sampler) → `ReadingIngest.record`.
2. `SensorAdapterSelector.select(device)` returns the adapter for the device's protocol.
3. `adapter.read(device)` returns a `Reading`; ingest saves it and publishes the event.

Pushed readings take a second entry point into the same ingest: device HTTP `POST /api/devices/{id}/readings` and the optional MQTT subscriber both call `ReadingIngest.record_payload(..., source=...)`, which uses `MqttSensorAdapter`.

## Where to look in code

| What | Path |
|---|---|
| Port and normalized type | `backend/src/domain/sensors/ports.py`, `backend/src/domain/sensors/reading.py` |
| Adapters | `backend/src/infrastructure/adapters/sensors/simulation.py`, `vendor_stub.py`, `mqtt.py` |
| Selector | `backend/src/infrastructure/adapters/sensors/selector.py` |
| Client | `backend/src/application/readings/service.py` (`ReadingIngest`) |
| Actuator port and adapter | `backend/src/domain/actuators/ports.py`, `backend/src/infrastructure/adapters/actuators/simulation.py` |
| Tests | `backend/tests/test_sensor_adapters.py`, `test_vendor_adapter.py`, `test_mqtt_adapter.py`, `test_reading_ingest.py` |

## Adapter vs other patterns

- **Decorator** (Phase 9) keeps the interface and adds behaviour; Adapter changes the interface.
- **Facade** (Phase 7) simplifies calling several subsystems; Adapter makes one incompatible interface fit.

## Try this extension

Add a **LoRaWAN-style adapter** for a payload such as `{"devEui": "...", "m": 412, "scale": 1000}`, where the moisture is `m / scale`. Implement it as a `SensorPort`, register a new protocol (for example `"lorawan"`) in `SensorAdapterSelector`, and test that it returns a `Reading` with `value == 0.412`, `unit == "vwc"` and `source == "lorawan"`. Nothing in `ReadingIngest`, the alerts or the dashboard should need to change.
