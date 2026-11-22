# Command Pattern - Smart Greenhouse

## At a glance

**Problem.** Operators send actions such as start pump, stop pump and set light level. Calling the actuator directly from the router would skip state checks, policies and history, and every new action would add another branch to the API.

**Intent.** **Command** turns each request into an object with `execute()`, so it can be validated, run through one invoker and recorded in `command_log`.

## Overview

The Command pattern encapsulates a request as an object. This separates the object that requests an operation from the object that performs it.

In the Smart Greenhouse application, the pattern handles actuator commands such as starting a water pump, stopping a water pump, and setting a grow light level.

Each command is represented by a separate command class. A registry creates the appropriate command, and an invoker executes it through the common actuator interface.

## Problem

The application needs to support different actuator operations without placing all command-specific logic inside the API router.

If the router directly handled every command, it would become more difficult to maintain and extend when new actuator operations are introduced.

The Command pattern separates command creation, execution, and API handling. It also provides a consistent way to record command execution history.

## Command interface

The common interface is `Command`.

It defines the operation:

```python
execute(port, device_id, payload)
```

Each concrete command implements this operation and delegates the actual actuator operation to the supplied `ActuatorPort`.

## Concrete commands

The implementation includes three commands:

| Command | Class | Responsibility |
|---|---|---|
| `start_pump` | `StartPumpCommand` | Starts a water pump. |
| `stop_pump` | `StopPumpCommand` | Stops a water pump. |
| `set_light_level` | `SetLightLevelCommand` | Sets the grow light intensity. |

The light-level command receives its requested level through the payload.

Example:

```json
{
  "level": 50
}
```

## Command registry and invoker

The implementation uses two components to manage command execution.

| Component | Responsibility |
|---|---|
| `CommandRegistry` | Maps command names to their concrete command classes and creates command objects. |
| `CommandInvoker` | Executes a command through the common actuator port. |

The registry makes it possible to add new command types without adding command-specific conditional logic to the invoker.

The invoker does not need to know the internal implementation of each concrete command.

## Command execution flow

The command execution process follows these steps:

1. The frontend sends a command request to the API.
2. The API passes the request to `CommandService`.
3. The service creates the appropriate command using `CommandRegistry`.
4. The service checks the device type and current actuator state.
5. If the command is allowed, the invoker executes it through the actuator port.
6. The actuator port uses the existing Decorator chain for runtime protection and execution logging.
7. The service updates the actuator state when a successful command requires a state transition.
8. The command result is saved in the command history.

## State validation

The Command pattern works together with the State pattern.

Before executing a command, the service checks whether the actuator is in a state that allows the requested operation.

| Command | Required device | Allowed state | Resulting state |
|---|---|---|---|
| `start_pump` | `water_pump` | `idle` | `running` |
| `stop_pump` | `water_pump` | `running` | `idle` |
| `set_light_level` | `grow_light` | `idle` or `running` | No state change |

An illegal command is rejected before the actuator port is called.

The current actuator state remains unchanged when a command is rejected or fails.

## Integration with the Decorator pattern

The Command pattern reuses the existing actuator port and Decorator chain.

The actuator execution chain is:

`LoggingActuatorDecorator -> MaxRunTimeActuatorDecorator -> SimulationActuatorAdapter`

The shared `build_actuator_port()` factory creates this chain for command execution.

This means command execution benefits from the existing logging and maximum-runtime protection without duplicating those responsibilities in the command classes.

If the maximum-runtime policy blocks execution, the command is recorded as failed and the exception is handled by the command service.

## Command history persistence

Command execution results are stored in the `command_log` table.

The table contains:

| Column | Description |
|---|---|
| `id` | UUID primary key. |
| `device_id` | UUID foreign key referencing `devices.id`. |
| `command_type` | Name of the executed command. |
| `payload` | JSONB data supplied with the command. |
| `status` | Execution result: `success`, `failed`, or `rejected`. |
| `error_message` | Optional error or rejection message. |
| `created_at` | Timestamp of the command record. |

The `CommandLogRepository` handles saving command results and retrieving recent command history.

Unknown command types are rejected before a command history record is created.

## API endpoints

### Execute a command

`POST /api/commands`

Example request:

```json
{
  "device_id": "example-device-id",
  "command_type": "start_pump",
  "payload": {}
}
```

The API returns the command execution record.

Possible responses:

| HTTP status | Description |
|---|---|
| `200 OK` | Command execution succeeded or failed. |
| `409 Conflict` | Command was rejected because it was not allowed. |
| `400 Bad Request` | Unknown command type. |
| `404 Not Found` | Device does not exist or is not an actuator. |

A failed execution, such as a maximum-runtime violation, is recorded with status `failed`.

A rejected command is recorded with status `rejected`.

### Get command history

`GET /api/commands?limit=50`

Returns recent command records, ordered from newest to oldest.

The limit can be between 1 and 200 records.

## Frontend

The dashboard includes a `CommandPanel` component in the Controls section.

It provides:

- Start and stop controls for water pumps.
- A slider for setting grow light intensity.
- Buttons disabled when the requested command is not available.
- Current actuator information.
- A command history table showing execution status and timestamps.

After a command is submitted, the frontend refreshes actuator information and command history.

The Events section continues to display the existing actuator execution log.

## Benefits

- Separates command requests from command execution.
- Keeps command-specific behaviour in separate classes.
- Avoids command-specific conditional logic in the invoker.
- Supports adding new commands through the registry.
- Reuses the existing actuator interface and Decorator chain.
- Integrates with the State pattern to prevent illegal operations.
- Records successful, failed, and rejected commands.
- Provides command history through the API and frontend.

## Testing

The Phase 10 implementation was tested for:

- Successful execution of the start pump command.
- Rejection and logging of an illegal stop pump command.
- Rejection of an unknown command without creating a history record.
- Retrieval of recent command history.
- Successful frontend command execution.
- Command history updates in the dashboard.
- Maximum-runtime failures being recorded correctly.

Run the backend tests from the `backend` directory:

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
```

## Where to look in code

| What | Path |
|---|---|
| Command interface | `backend/src/domain/commands/base.py` |
| Concrete commands | `backend/src/domain/commands/pump.py`, `backend/src/domain/commands/light.py` |
| Registry and invoker | `backend/src/domain/commands/invoker.py` |
| Client (state checks, logging, events) | `backend/src/application/commands/service.py` |
| API | `backend/src/interfaces/api/commands.py` (`POST`/`GET /api/commands`) |
| Tests | `backend/tests/test_commands.py`, `backend/tests/integration/test_commands_api.py` |

## Try this extension

Add a **`ResetErrorCommand`** (`reset_error`), which `ALLOWED_COMMANDS` already lists for the `error` state. Register it, map it to the `error → idle` transition in `CommandService`, and test that it is rejected in every other state. As a second step, add `undo()` to the pump commands by capturing the previous state before `execute()`.
