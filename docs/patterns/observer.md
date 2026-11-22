# Observer Pattern — Smart Greenhouse

## Overview

The Observer pattern lets one object announce that something happened, while any number of other objects react to it. The object that announces the change does not know who is listening.

In the Smart Greenhouse application, Phase 11 adds an in-process `EventBus`. Application services publish domain events to the bus, and subscribers turn those events into persisted alerts. The dashboard event feed reads the alerts through `GET /api/alerts`.

The main flow is:

`ReadingIngest → EventBus → MoistureThresholdSubscriber → EventBus → AlertPersistenceSubscriber → alerts table → GET /api/alerts → EventFeed`

## Problem

Several parts of the application need to react when something happens: a low moisture reading, a failed command, or an actuator entering `error`.

If `ReadingIngest`, `CommandService` and the transition service wrote alerts directly, every publisher would depend on the alerts table, and every new reaction (metrics, notifications, the Phase 12 WebSocket) would mean editing those services again.

With Observer, publishers only describe what happened. Each reaction lives in its own subscriber.

## Participants

| Role | Smart Greenhouse class | Responsibility |
|---|---|---|
| Subject / event bus | `EventBus` (`domain/events/bus.py`) | Keeps the subscriber list per event type and delivers each published event. |
| Event | `ReadingCreated`, `ThresholdCrossed`, `CommandFailed`, `ActuatorStateChanged`, `AlertCreated` (`domain/events/events.py`) | Immutable facts about something that already happened. |
| Publisher | `ReadingIngest`, `CommandService`, `ActuatorTransitionService` | Saves its own work, then publishes an event. Never imports `AlertRepository`. |
| Observer / subscriber | A handler function `(event) -> None` | Reacts to one event type. |
| Concrete observers | `MoistureThresholdSubscriber`, `AlertPersistenceSubscriber` | Apply the alert rules and insert alert rows. |

`EventBus` has two operations:

- `subscribe(event_type, handler)` registers a handler for one event class. Handlers for the same event class run in subscription order.
- `publish(event)` calls every handler subscribed to that event's class.

This bus has no `unsubscribe`, because all subscribers live for the whole process.

## Events

| Event | Published by | When |
|---|---|---|
| `ReadingCreated` (`reading.created`) | `ReadingIngest` | After a reading is saved, only if the device has `tracking_enabled = true`. |
| `ThresholdCrossed` (`threshold.crossed`) | `MoistureThresholdSubscriber` | Unit is `vwc`, the device has a zone, and the value is strictly below the zone's `moisture_threshold_low`. |
| `CommandFailed` (`command.failed`) | `CommandService` | Command execution raised an error, for example `Max run time exceeded`. |
| `ActuatorStateChanged` (`state.changed`) | `CommandService`, `ActuatorTransitionService` | After every successful actuator state save. |
| `AlertCreated` (`alert.created`) | `AlertPersistenceSubscriber` | After an alert row is inserted. The Phase 12 WebSocket forwarder subscribes to it. |

Each event carries `device_id`, `location_id` and `zone_id`. The ids are copied from the device when the event is published. They stay `null` for an unassigned device; no zone is invented.

## One ingest publisher

Manual reads (`POST /api/sensors/{id}/read`), the simulation sampler and translated MQTT readings all go through `ReadingIngest`. It is the only writer of `sensor_readings` and the only publisher of `reading.created`. That way every source follows the same tracking rule, and there is no separate publish path for the sampler.

When tracking is off, the reading row is still stored, but `ReadingCreated` is not published, so no threshold alert is created.

## Alert rows

`AlertPersistenceSubscriber` is the only object that inserts into `alerts`:

| `event_type` | `severity` | `message` |
|---|---|---|
| `threshold.crossed` | `warning` | `Moisture below zone low` |
| `command.failed` | `warning` | The failure message, e.g. `Max run time exceeded` |
| `state.changed` | `critical` | `Actuator entered error` (only when the new state is `error`) |

Alerts are stored in the database, so the event feed still shows them after a page refresh.

## Composition root

`backend/src/composition.py` builds one `EventBus` for the process and subscribes both alert subscribers. FastAPI dependencies (`get_event_bus`) and the simulation sampler in `main.py` inject that same bus into every publisher.

Subscribers open their own database session for each event. The publisher has already committed its own work before it publishes.

## Failing subscribers

`EventBus.publish` catches and logs an exception from one handler and continues with the next handler. A failing alert writer therefore does not stop other subscribers (such as a metrics subscriber or the Phase 12 WebSocket), and it does not turn an already-saved reading or command into an HTTP error.

## API and UI

`GET /api/alerts` returns alerts newest first.

| Query parameter | Default | Notes |
|---|---|---|
| `status` | `active` | `active`, `resolved` or `all`; anything else returns 400. |
| `location_id` | — | Only alerts for this location. |
| `zone_id` | — | Only alerts for this zone. |
| `since` | — | Only alerts with `created_at` at or after this time. |
| `limit` | `50` | 1–200. |

The response does not include `acknowledged_at`, although the column exists.

`EventFeed` (`frontend/src/components/alerts/EventFeed.tsx`) is shown in the dashboard's `#events` section. Since Phase 12 it refreshes when an `alert.created` frame arrives and polls `GET /api/alerts` every 5 seconds only while the WebSocket is down. It can filter by one location and one zone, colours each alert by severity, and has an empty state.

## Observer and the Phase 12 WebSocket

Phase 11 kept everything in-process and the browser polled. `realtime.ts` was a stub.

In Phase 12, `WebSocketEventForwarder` (`application/realtime/ws_subscriber.py`) became one more subscriber on the same `EventBus`. It forwards `ReadingCreated`, `ActuatorStateChanged` and `AlertCreated` to `WS /api/ws` as JSON frames. It does not implement its own publish/subscribe and never writes rows. Device HTTP and the optional MQTT broker call `ReadingIngest` instead of publishing on their own, so they reuse the same publish rule.

## Comparison with other patterns

| Pattern | Purpose in this project |
|---|---|
| Facade (Phase 7) | Simplifies calling into several subsystems to build one overview response. |
| Command (Phase 10) | Captures an intent to act on an actuator. |
| Observer (Phase 11) | Fans out the outcome after something happened, without the publisher knowing who reacts. |

## Tests

The Phase 11 tests verify that:

- Handlers run in subscription order, and a failing handler does not block later handlers.
- Ingest with tracking on publishes `ReadingCreated` with the device's `location_id` and `zone_id`; with tracking off the row is stored and nothing is published.
- A translated MQTT reading follows the same publish rule.
- `MoistureThresholdSubscriber` only publishes for `vwc` readings in a zone that are strictly below the low threshold.
- A moisture reading of `0.10` on Bench 1 (low `0.20`) inserts `threshold.crossed`, and `GET /api/alerts?zone_id=` returns it for Bench 1 only.
- With tracking off, a low reading is stored but creates no alert.
- A failed `stop_pump` on an unassigned pump that has run for 31 minutes inserts `command.failed` with message `Max run time exceeded` and null `location_id` and `zone_id`.
- `POST /api/devices/{id}/transition` with `target=error` inserts `state.changed`, severity `critical`, message `Actuator entered error`; other transitions insert nothing.
- `status` other than `active`, `resolved` or `all` returns 400, and `since` filters by `created_at`.
- `ReadingIngest`, `CommandService` and `ActuatorTransitionService` do not import `AlertRepository`.
