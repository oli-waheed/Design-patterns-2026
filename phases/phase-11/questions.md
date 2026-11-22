# Phase 11 — Observer questions

**Pattern / focus:** Observer.

**Read first:** [Guide 11](../../materials/guides/11-observer.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example live auction bids) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to the event bus, alerts, publishers, and the event feed from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Observer in plain language. What is a **one-to-many** dependency here, and why must the subject notify dependents **without** knowing their concrete classes?

> [!NOTE]
> **_Your Answer_**
>
> The Observer pattern lets one object announce that something has happened, while other objects react to it without the announcing object knowing about them. A one-to-many dependency means that one event can have several listeners. In our project, `EventBus` is the subject, and a single event such as `ReadingCreated` can be handled by any number of subscribers. The subject must not know the concrete subscriber classes, because then every new reaction would require changing the publisher. With the bus, we can add a new subscriber, for example for metrics or the Phase 12 WebSocket, without modifying `ReadingIngest` or `CommandService`.

2. Name the participants (**subject / event bus**, **observer / subscriber**, **concrete observers**, **event**, **publisher**). What does `subscribe` / `unsubscribe` / `publish` (or `notify`) each do? This example’s `EventBus` implements `subscribe` and `publish` only.

> [!NOTE]
> **_Your Answer_**
>
> The subject is `EventBus`, which keeps a list of handlers for each event type. A subscriber is a handler that reacts to one type of event. Our concrete observers are `MoistureThresholdSubscriber` and `AlertPersistenceSubscriber`. The events are small immutable objects, such as `ReadingCreated`, `ThresholdCrossed`, `CommandFailed`, and `ActuatorStateChanged`. The publishers are `ReadingIngest`, `CommandService`, and `ActuatorTransitionService`. `subscribe` registers a handler for an event class, and `publish` delivers an event to every handler of that class in subscription order. `unsubscribe` would remove a handler, but our `EventBus` does not need it because all subscribers live for the whole backend process.

3. When should you use Observer, and when should you skip it (only one listener forever; or you need a strict multi-step workflow with guaranteed order)?

> [!NOTE]
> **_Your Answer_**
>
> Observer is useful when several independent parts of the application need to react to the same event, and the publisher should not depend on them. In our project, a stored reading can lead to a threshold check and an alert, and later also to a WebSocket message. If there will only ever be one listener, a direct method call is simpler. Observer is also not suitable for a strict multi-step workflow where every step must succeed in a guaranteed order, because the publisher does not control what the subscribers do. In that case, an application service should call each step directly.

## B. This phase of the application

4. Give at least two **domain events** you publish in this lab, including `reading.created` (only when `tracking_enabled` is true), a threshold-crossed event, command-failed, and `ActuatorStateChanged`. The persistence subscriber stores `state.changed` only when that state is `error`. Who publishes `reading.created`, and why do a manual read, the simulation sampler, and MQTT translation share that one ingest publish? Why must a publisher **not** import the alerts repository or the UI?

> [!NOTE]
> **_Your Answer_**
>
> We publish four domain events: `ReadingCreated` (`reading.created`), `ThresholdCrossed` (`threshold.crossed`), `CommandFailed` (`command.failed`), and `ActuatorStateChanged` (`state.changed`). `ReadingIngest` publishes `reading.created` after it has saved a reading, but only when the device has `tracking_enabled` set to true. `CommandService` publishes `CommandFailed` when a command fails, and both `CommandService` and `ActuatorTransitionService` publish `ActuatorStateChanged` after each successful state save. The persistence subscriber stores `state.changed` only when the new state is `error`.
>
> A manual read, the simulation sampler, and a translated MQTT reading all go through `ReadingIngest`, so they share one writer of `sensor_readings` and one publish rule. This avoids a separate publish path for the sampler and keeps the tracking rule in one place. A publisher must not import the alerts repository or the UI, because then it would depend on its listeners again. It should only describe what happened and leave the reaction to the subscribers.

5. What does `AlertPersistenceSubscriber` (or your equivalent) do when it handles an event? Name the three stored rows: `threshold.crossed` / `warning` / `Moisture below zone low`, `command.failed` / `warning` / the failure message, and `state.changed` / `critical` / `Actuator entered error`. Why do alerts live in the `alerts` table so the event feed still shows them after a **refresh**?

> [!NOTE]
> **_Your Answer_**
>
> `AlertPersistenceSubscriber` is the only object that writes alerts. When it handles an event, it inserts one active row into the `alerts` table and copies `device_id`, `location_id`, and `zone_id` from the event. It stores `threshold.crossed` with severity `warning` and the message `Moisture below zone low`, `command.failed` with severity `warning` and the failure message, for example `Max run time exceeded`, and `state.changed` with severity `critical` and the message `Actuator entered error`. After each insert, it also publishes `AlertCreated` for Phase 12. Alerts are saved in the database instead of only in React state, so the event feed can load them again after a page refresh or a backend restart.

6. The dashboard Event feed **polls** `GET /api/alerts` every 5 seconds in this phase. `services/realtime.ts` is only a **stub**. Why is full WebSocket **not** required in this phase? What should Phase 12 plug into so you do **not** re-implement pub/sub inside socket handlers? Phase 12 subscribes a dashboard socket to this same bus, and the example publishes `AlertCreated` after each insert for that socket.

> [!NOTE]
> **_Your Answer_**
>
> A full WebSocket is not required in this phase because the goal is to introduce the event bus and persist alerts. Polling `GET /api/alerts` every 5 seconds is enough to show new alerts in the event feed, and `realtime.ts` only defines the `RealtimeEvent` type and a `subscribeRealtime` function that does nothing yet. In Phase 12, the dashboard WebSocket should become another subscriber on the same `EventBus`, for example for `AlertCreated`, which our persistence subscriber already publishes after each insert. This way, the socket only forwards events and we do not need to implement publish/subscribe again inside the socket handlers.

7. Describe the must-demo path: a **tracked** low-moisture reading leads to an alert row that appears in the feed after poll. Which objects collaborate (reading pipeline → bus → subscriber → API → UI), and which object must **not** write the alert directly? What is stored, and what is not published, when `tracking_enabled` is false?

> [!NOTE]
> **_Your Answer_**
>
> A manual read through `POST /api/sensors/{id}/read`, or the simulation sampler, calls `ReadingIngest`. It reads the sensor through its adapter, saves the reading, and publishes `ReadingCreated` with the device's `location_id` and `zone_id`. `MoistureThresholdSubscriber` receives the event, loads the zone, and publishes `ThresholdCrossed` if the moisture is strictly below the zone's low threshold. For example, `0.10` on Bench 1 with a low threshold of `0.20` crosses it. `AlertPersistenceSubscriber` then inserts the alert row, `GET /api/alerts` returns it, and `EventFeed` shows it after the next poll.
>
> The reading service and the HTTP router must not write the alert directly. When `tracking_enabled` is false, the reading is still stored in `sensor_readings`, but `ReadingCreated` is not published, so no threshold check or alert happens.

## C. Compare, contrast, and scenarios

8. Contrast Observer with **Facade**. Facade simplifies **calling into** a subsystem. Observer **fans out** notifications after something happened. How do both appear in this greenhouse (Phase 7 overview vs this phase)?

> [!NOTE]
> **_Your Answer_**
>
> Facade gives the caller one simple entry point into several parts of a subsystem. Observer works in the other direction: after something has happened, it sends a notification to everyone who is interested. In Phase 7, `OverviewFacade` combines location, zone, device, reading, and automation data into one overview response when the client asks for it. In this phase, `EventBus` sends events such as `ReadingCreated` to the alert subscribers without the publisher knowing who receives them. So Facade simplifies a request into the system, while Observer spreads the result of an event out of it.

9. Contrast Observer with **Command**. Command captures **intent to act**. Observer propagates **outcomes**. How can `execute()` publish an event without the command class knowing who persists alerts?

> [!NOTE]
> **_Your Answer_**
>
> Command represents an intention to do something, such as `StartPumpCommand` or `StopPumpCommand`. Observer reports what happened after the action. In our project, the command does not publish events itself. `CommandService` executes the command through the `CommandInvoker`, and if execution fails, it publishes `CommandFailed` to the injected `EventBus`. The service only knows the bus and the event, not `AlertPersistenceSubscriber` or the `alerts` table. Because of this, the command code does not need to change if we later add another subscriber, for example a WebSocket or a notification.

10. One subscriber throws during `notify` / `publish` and aborts the loop, so later subscribers never run. Why is that a trap? What should the bus do so a failing alert writer does not block metrics (or later WebSocket) subscribers?

> [!NOTE]
> **_Your Answer_**
>
> If one subscriber raises an exception and the loop stops, the later subscribers never receive the event. That is a trap because one broken part, such as an alert writer that cannot reach the database, would also stop independent parts like metrics or the Phase 12 WebSocket. The exception could also reach the publisher and turn a reading that was already saved into an HTTP error. In our `EventBus`, `publish` catches the exception from each handler separately, logs it, and continues with the next handler. Our tests check that a failing handler does not block the handlers after it.
