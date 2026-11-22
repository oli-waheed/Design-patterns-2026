# State Pattern — Smart Greenhouse

## At a glance

**Problem.** An actuator's allowed actions depend on its lifecycle: a pump can only start when idle and only stop when running. Modelling this with booleans and scattered `if` checks allows impossible combinations such as running *and* in maintenance.

**Intent.** **State** makes the current state explicit and lets it decide which transitions and commands are legal. This project uses a transition table plus an `ActuatorContext` rather than one class per state.

## Overview

The State pattern allows an object to change its behaviour depending on its current state.

In the Smart Greenhouse application, the State pattern manages the lifecycle of actuator devices. An actuator can be off, idle, running, in error, or in maintenance.

The application checks whether a transition is allowed before changing the actuator's state.

## Problem

Without a clear state-management system, actuator behaviour can become difficult to maintain. For example, a pump should not start when it is already running or when it is in maintenance.

If all state rules are placed in different service methods, the same conditions may be repeated in several places.

The State pattern provides one place to define the allowed transitions and commands. This makes actuator behaviour easier to understand and test.

## Actuator states

The implementation supports five states:

| State | Description |
|---|---|
| `off` | The actuator is switched off. |
| `idle` | The actuator is ready but not running. |
| `running` | The actuator is currently operating. |
| `error` | The actuator has an error that needs attention. |
| `maintenance` | The actuator is under maintenance. |

## State transitions

Not every transition is allowed. The application uses a transition table to define the valid changes.

| Current state | Allowed next states |
|---|---|
| `off` | `idle` |
| `idle` | `running`, `maintenance`, `error`, `off` |
| `running` | `idle`, `error` |
| `error` | `idle`, `maintenance` |
| `maintenance` | `idle`, `off` |

For example, an actuator in the `idle` state can start running. However, an actuator in the `running` state cannot directly enter maintenance. It must first return to `idle`.

If a transition is not allowed, the application raises an `IllegalTransitionError` and keeps the current state unchanged.

## Where the pattern is used

| Component | Responsibility |
|---|---|
| `ActuatorState` | Defines the five possible actuator states. |
| `ALLOWED_TRANSITIONS` | Defines which state changes are permitted. |
| `ALLOWED_COMMANDS` | Defines the commands available in each state. |
| `ActuatorContext` | Holds the current state and validates transitions. |
| `IllegalTransitionError` | Represents an invalid state transition. |
| `ActuatorStateRow` | Represents the persisted actuator state in the database. |
| `DeviceRepository` | Reads and updates actuator states. |
| `DeviceService` | Applies state transitions and provides state information. |
| Devices API router | Provides endpoints to read actuator states and request transitions. |

## Allowed commands

The application also provides commands according to the current state.

| State | Allowed commands |
|---|---|
| `off` | `power_on` |
| `idle` | `start_pump` |
| `running` | `stop_pump` |
| `error` | `reset_error` |
| `maintenance` | `finish_maintenance` |

The `allowed_commands()` method returns a copy of the commands for the current state. This allows the frontend to display only the actions that are currently available.

## Persistence choice

Actuator states are stored in a separate `actuator_states` table.

The table contains:

- `device_id`: the primary key and foreign key referencing `devices.id`.
- `state`: the current actuator state.
- `updated_at`: the time when the state was last updated.

A database migration creates the table and inserts an initial `idle` state for existing actuator devices.

New actuator devices also receive an initial `idle` state when they are saved.

This means the actuator state is retained in the database when the application restarts.

## API endpoints

### Get actuator state

`GET /api/devices/{device_id}/state`

Returns the current state and allowed commands.

Example response:

```json
{
  "device_id": "example-device-id",
  "state": "idle",
  "allowed_commands": [
    "start_pump"
  ]
}
```

A missing device or a device that is not an actuator returns HTTP `404 Not Found`.

### Change actuator state

`POST /api/devices/{device_id}/transition`

Example request:

```json
{
  "target": "running"
}
```

The service checks the requested transition before saving the new state.

An invalid transition returns HTTP `409 Conflict`. An invalid state value returns HTTP `400 Bad Request`. A missing actuator returns HTTP `404 Not Found`.

## Frontend

The frontend retrieves actuator state from the API and displays it as a badge.

The badge colours help distinguish the states:

- `idle`: slate
- `running`: emerald
- `error`: red
- `maintenance`: amber
- `off`: slate

The frontend also displays the allowed commands returned by the API.

The actual control buttons can be added with the Command pattern in Phase 10.

## Benefits

- Actuator state transitions are managed consistently.
- Illegal transitions are rejected.
- The current state is stored in the database.
- Allowed commands depend on the current state.
- The frontend can display the current state and available actions.
- State-management logic can be tested independently.

## Testing

The Phase 8 tests check that:

- An actuator can transition from `idle` to `running`.
- A transition from `running` to `maintenance` is rejected.
- An illegal transition does not change the current state.
- Allowed commands depend on the current state.
- The API returns the correct actuator state.
- The API rejects illegal transitions.
- Missing actuators return HTTP `404 Not Found`.

Run the backend tests from the `backend` directory:

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
```

## State pattern and Strategy pattern

The State pattern and Strategy pattern can look similar because both use separate objects or rules to manage behaviour.

However, they solve different problems.

The State pattern changes the available behaviour according to an object's current state. In this project, actuator commands depend on the actuator's lifecycle state.

The Strategy pattern selects an algorithm or decision policy. In this project, automation strategies evaluate sensor readings and recommend whether irrigation is needed.

The State pattern manages actuator lifecycle, while the Strategy pattern manages automation decisions.

## Where to look in code

| What | Path |
|---|---|
| States and transition / command tables | `backend/src/domain/actuators/state.py` |
| Context | `backend/src/domain/actuators/context.py` |
| Manual transitions (publishes `ActuatorStateChanged`) | `backend/src/application/actuators/transition_service.py` |
| Allowed commands for the UI | `backend/src/application/actuators/allowed_commands.py` |
| API | `backend/src/interfaces/api/devices.py` (`GET .../state`, `POST .../transition`) |
| Tests | `backend/tests/test_actuator_state.py`, `backend/tests/test_actuator_state_api.py` |

## Try this extension

Turn the table into **state classes**: an `ActuatorStateBase` with `allowed_targets()` and `allowed_commands()`, and one subclass per state (`IdleState`, `RunningState`, ...). Keep `ActuatorContext`'s public methods the same, so `test_actuator_state.py` passes unchanged. Then compare which version is easier to extend with a new `paused` state.
