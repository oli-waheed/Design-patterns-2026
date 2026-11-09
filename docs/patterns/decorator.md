# Decorator Pattern — Smart Greenhouse

## Overview

The Decorator pattern adds behaviour to an existing object by wrapping it with another object that implements the same interface.

In the Smart Greenhouse application, the pattern adds policies around actuator commands without modifying the underlying simulation adapter.

The execution chain is:

`LoggingActuatorDecorator → MaxRunTimeActuatorDecorator → SimulationActuatorAdapter`

## Problem

Actuator commands need additional behaviour, such as execution logging and runtime protection.

Putting these responsibilities directly inside the simulation adapter would mix different concerns and make the implementation harder to extend and test.

The Decorator pattern allows these behaviours to be added independently while preserving the common actuator interface.

## Actuator port

The common interface is `ActuatorPort`.

It defines the operation:

```python
apply(device_id: UUID, command: str, payload: dict) -> None
```

The simulation adapter and both decorators implement this interface. Therefore, a decorator can wrap another actuator implementation without changing how the client calls it.

## Decorator chain

| Component | Responsibility |
|---|---|
| `ActuatorPort` | Defines the common actuator interface. |
| `SimulationActuatorAdapter` | Performs the underlying simulated actuator operation. |
| `MaxRunTimeActuatorDecorator` | Checks whether a running actuator has exceeded its maximum runtime. |
| `LoggingActuatorDecorator` | Records successful and failed execution attempts in the database. |
| `DevicesService` | Composes the decorators and executes actuator commands. |

The logging decorator is the outermost layer. The maximum-runtime decorator is inside it, and the simulation adapter is the innermost component.

## Maximum runtime policy

The maximum-runtime decorator checks the actuator state and its last update time.

If the actuator is running and its state has not been updated for at least 30 minutes, execution is blocked.

The decorator raises `MaxRunTimeExceeded` with the message:

`Max run time exceeded`

The inner simulation adapter is not called when this policy blocks execution.

## Execution logging

The logging decorator records each execution attempt in the database.

Successful execution records contain:

- `success`: `true`
- `policy_applied`: `["logging"]`
- `message`: `null`

When the maximum-runtime policy blocks execution, the record contains:

- `success`: `false`
- `policy_applied`: `["maxRunTime", "logging"]`
- `message`: `Max run time exceeded`

The logging decorator records the failure and propagates the exception so the API can return the appropriate error response.

## Persistence

Execution records are stored in the `actuator_execution_log` table.

| Column | Description |
|---|---|
| `id` | UUID primary key. |
| `device_id` | UUID foreign key referencing the device. |
| `success` | Indicates whether execution succeeded. |
| `policy_applied` | JSONB list of applied policies. |
| `message` | Optional execution or policy message. |
| `created_at` | Timestamp of the execution attempt. |

The `ExecutionLogRepository` saves execution records and retrieves recent records for the API.

## API endpoints

### Execute an actuator command

`POST /api/devices/{device_id}/execute`

Example request:

```json
{
  "command": "start_pump",
  "payload": {}
}
```

A successful execution returns a success response. If the maximum-runtime policy blocks the command, the API returns HTTP `409 Conflict` with the message `Max run time exceeded`.

### Get recent execution records

`GET /api/actuators/executions?limit=20`

Returns recent actuator execution records, including the device name, result, applied policies, message, and timestamp.

## Frontend

The dashboard includes an `ExecutionLog` component in the Events section.

It retrieves recent execution records from the API and displays:

- Execution time
- Device name
- Success or failure status
- Applied policies
- Execution message

The component also provides loading, error, refresh, and empty states.

## Benefits

- Adds behaviour without modifying the simulation adapter.
- Keeps logging and runtime protection as separate responsibilities.
- Allows decorators to be combined in a defined order.
- Makes policy behaviour easier to test independently.
- Persists execution attempts for later review.
- Supports adding further decorators in the future.

## Testing

The Phase 9 implementation was tested for successful and blocked execution.

The tests verify that:

- The maximum-runtime decorator blocks an actuator running for at least 30 minutes.
- The inner adapter is not called when the runtime policy blocks execution.
- A blocked attempt is recorded in the database.
- A successful execution is recorded with the logging policy.
- The execution-log API returns recent records.

Run the backend tests from the `backend` directory:

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
```