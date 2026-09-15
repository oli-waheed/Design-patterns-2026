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