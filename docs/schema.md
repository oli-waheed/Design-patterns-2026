# Database schema — Smart Greenhouse

The schema is created only by Alembic. From an empty PostgreSQL database:

```powershell
cd backend
alembic upgrade head
```

## Migration chain

| Revision | Phase | Change |
|---|---|---|
| `001` | 1 | Baseline |
| `edc342b0be5c` | 2 | `devices` |
| `4538b4a53013` | 3 | `devices.device_family` |
| `089e40b8395c` | 4 | `locations`, `zones`, device zone assignment |
| `d57d17a10ef2` | 5 | `sensor_readings`, sampling columns |
| `2427c8314716` | 6 | `automation_rules` |
| `5a8c2f1d9e30` | 8 | `actuator_states` |
| `334a58db4f16` | 9 | `actuator_execution_log` |
| `ab97c0ab7037` | 10 | `command_log` |
| `4ca2aa600344` | 11 | `alerts` |
| `8cc04ca37e07` | 12 | Schema hardening: indexes, checks, threshold type, demo seed |

Applied revisions are never edited; every change is a new revision.

## Foreign keys and `ON DELETE`

| Table.column | References | On delete | Why |
|---|---|---|---|
| `zones.location_id` | `locations` | `CASCADE` | A zone cannot exist without its location. |
| `devices.location_id` | `locations` | `SET NULL` | Deleting a location unassigns devices; the devices remain. |
| `devices.zone_id` | `zones` | `SET NULL` | Deleting a zone unassigns its devices. |
| `automation_rules.location_id` | `locations` | `CASCADE` | The saved strategy belongs to the location. |
| `sensor_readings.device_id` | `devices` | `CASCADE` | Readings are meaningless without the device. |
| `actuator_states.device_id` | `devices` | `CASCADE` | One state row per actuator. |
| `actuator_execution_log.device_id` | `devices` | `CASCADE` | Execution history of the device. |
| `command_log.device_id` | `devices` | `CASCADE` | Command history of the device. |
| `alerts.location_id`, `zone_id`, `device_id` | `locations`, `zones`, `devices` | `SET NULL` | Alerts stay as history even if what they refer to is deleted. |

## Indexes for live traffic

| Index | Used by |
|---|---|
| `sensor_readings (device_id, recorded_at)` | Latest reading per device: sensor cards, overview, automation, sampler |
| `alerts (location_id, created_at)` | Event feed filtered by location, newest first |
| `alerts (status, created_at)` | Default `GET /api/alerts?status=active` |
| `alerts (zone_id)`, `alerts (created_at)` | Zone filter, `since` filter |
| `command_log (created_at)` | `GET /api/commands`, newest first |
| `actuator_execution_log (created_at)` | `GET /api/actuators/executions`, newest first |
| `devices (location_id)`, `devices (zone_id)` | Overview and zone device lists |
| `automation_rules (location_id)` unique | One saved strategy per location |

## Check constraints

| Constraint | Allowed values |
|---|---|
| `ck_alerts_severity` | `info`, `warning`, `critical` |
| `ck_alerts_status` | `active`, `resolved` |
| `ck_command_log_status` | `success`, `failed`, `rejected` |

## Demo seed

The hardening revision inserts demo rows with fixed ids and `ON CONFLICT DO NOTHING`, so running it again adds nothing:

| Row | Details |
|---|---|
| Location `Demo Greenhouse` | `00000000-0000-4000-8000-000000000001` |
| Zone `Bench 1` | thresholds 0.20 / 0.60 |
| `Demo Moisture Sensor` | simulation, `sampling_interval_seconds = 5`, `tracking_enabled = true`, assigned to Bench 1 |
| `Demo Water Pump` | simulation, unassigned, state `idle` |
| One reading | 0.42 vwc for the demo sensor |

With only this seed, no ESP32 and no broker, the simulation sampler produces a new reading every 5 seconds and the dashboard updates live.
