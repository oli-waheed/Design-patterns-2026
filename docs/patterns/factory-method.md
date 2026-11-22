# Factory Method — Smart Greenhouse Sensors

## 1. Problem

The Smart Greenhouse application supports different types of sensors.

In Phase 2, the application supports:

- Moisture sensors
- Light sensors

Each sensor type has its own:

- `device_type`
- default configuration
- measurement unit
- sampling interval
- threshold

If the application created every sensor directly in the API or service layer, the creation logic would become harder to maintain as more sensor types are added.

For example, the application should not need to contain large conditional blocks such as:

```python
if sensor_type == "moisture":
    ...
elif sensor_type == "light":
    ...
elif sensor_type == "temperature":
    ...
```

That `if/elif` chain would grow with every new sensor type, and every place that creates sensors would need to change.

## 2. Pattern and intent

**Factory Method** lets a subclass decide which concrete object to create. The caller asks a *creator* for a sensor and does not need to know which sensor class or default settings it gets.

## 3. How it works in this project

| Participant | Class | Responsibility |
|---|---|---|
| Creator | `SensorCreator` | Declares `create_sensor(display_name)` |
| Concrete creators | `MoistureSensorCreator`, `LightSensorCreator` | Return a `Sensor` with type-specific defaults |
| Product | `Sensor` | The created sensor entity |
| Client | `SensorService` | Picks a creator with `get_creator(sensor_type)` and saves the result |

Each creator owns its defaults:

| Creator | `device_type` | Unit | Sampling interval | Threshold |
|---|---|---|---|---|
| `MoistureSensorCreator` | `moisture_sensor` | `vwc` | 300 s | 30 |
| `LightSensorCreator` | `light_sensor` | `lux` | 60 s | 1000 |

`get_creator()` looks the creator up in the `CREATORS` registry and raises `ValueError` for an unknown type, which the API turns into HTTP 400.

Flow: `POST /api/sensors {"type": "moisture"}` → `SensorService.create_sensor` → `get_creator("moisture").create_sensor()` → `DeviceRepository.save_sensor`.

Later phases reuse the same creators: the Abstract Factory (Phase 3) builds its sensors through them.

## 4. Where to look in code

| What | Path |
|---|---|
| Creator, concrete creators, registry | `backend/src/domain/sensors/creators.py` |
| Product | `backend/src/domain/sensors/entity.py` |
| Client | `backend/src/application/sensors/service.py` |
| API | `backend/src/interfaces/api/sensors.py` (`POST /api/sensors`) |
| Tests | `backend/tests/test_factory_method.py` |

## 5. Try this extension

Add a **temperature sensor**: create `TemperatureSensorCreator` returning `device_type="temperature_sensor"`, unit `celsius`, a 120-second interval and a threshold of 30, then register it in `CREATORS` under `"temperature"`. Write a test like `test_moisture_creator_defaults` for it. Notice that `SensorService` and the API do not change; only the registry does.
