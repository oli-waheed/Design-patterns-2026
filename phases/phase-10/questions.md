# Phase 10 — Command questions

**Pattern / focus:** Command.

**Read first:** [Guide 10](../../materials/guides/10-command.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example editor undo commands) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to command objects, the invoker, `command_log`, and the controls UI from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Command in plain language. What does it mean to **objectify a request**, and what can you do with that object that you cannot do with a bare `actuator.start()` call (queue, audit, undo, history)?

> [!NOTE]
> **_Your Answer_**
>
> The Command pattern represents an operation as a separate object instead of calling a method directly. This is what objectifying a request means. The application can pass the command between different components and record information about it. It also makes features such as command history, auditing, scheduling, or undo possible. In Smart Greenhouse, command objects represent actuator operations, and their results are stored in the database.

2. Name the participants (**command**, **receiver**, **invoker**, **client**). Who creates the command, who triggers `execute()`, and who actually changes actuator/hardware state?

> [!NOTE]
> **_Your Answer_**
>
> The command is an object representing an operation, such as `StartPumpCommand` or `StopPumpCommand`. The receiver is the actuator port and its underlying adapter, which performs the requested operation. The invoker triggers the command by calling its `execute()` method. In our application, the frontend is the client, and the `CommandService` creates the command through `CommandRegistry`. The `CommandInvoker` then executes it through the actuator port. Our current simulation adapter records the operation; it does not directly control physical hardware.

3. If a command supports undo, when must it capture the data needed to reverse the action? Why is “capture **before** mutate” critical?

> [!NOTE]
> **_Your Answer_**
>
> A command must capture the previous value before changing anything. For example, if a grow light level changes from 30 to 70, the command would need to remember the original level of 30. If it only saves the value after the change, the information needed to restore the previous state is lost. Undo is not currently implemented in our project, but capturing the previous value first would make it possible.

## B. This phase of the application

4. Which command types did you implement (for example `start_pump`, `stop_pump`, `set_light_level`)? Why does the HTTP handler create a command and pass it to an **invoker** (or application service) instead of calling the actuator adapter from the router?

> [!NOTE]
> **_Your Answer_**
>
> We implemented `start_pump`, `stop_pump`, and `set_light_level`. The HTTP router passes the request to the application service instead of calling the adapter directly. The service validates the device and command, creates the correct command through the registry, and uses the invoker to execute it. This keeps the API separate from the actuator implementation and ensures that state validation, decorators, and command logging are handled consistently.

5. Walk through the execute path: (1) consult State / `allowed_commands`, (2) if illegal → **rejected**, (3) if legal → decorated `apply`, update `actuator_states`, log **success** or **failed**. Why must a rejected command **not** change actuator state and **not** reach inner `apply`?

> [!NOTE]
> **_Your Answer_**
>
> First, the application checks the device and its current actuator state to decide whether the requested command is allowed. The frontend also uses `allowed_commands` to show which actions are available. If a command is not allowed, the service saves it as `rejected` in `command_log` and stops without calling the actuator port. If it is allowed, the command runs through the decorated actuator port. After successful execution, the service updates the actuator state when a transition is required and records `success`. If execution fails, it records `failed` and keeps the previous state. A rejected command must not reach `apply` because an illegal operation should never be executed or change the actuator state.

6. Distinguish **`rejected`** vs **`failed`** vs **`success`** in `command_log`. Give one greenhouse example of each. Why is “illegal in this state” not the same as “policy or adapter error after the command was accepted”?

> [!NOTE]
> **_Your Answer_**
>
> `success` means the command was accepted and executed successfully, for example starting a pump while it is idle. `rejected` means the command was not allowed in the current state, such as trying to stop a pump while it is idle. `failed` means the command was accepted, but an error occurred during execution, for example when the maximum runtime decorator raises `Max run time exceeded`. A rejected command fails the state validation before execution, while a failed command reaches the execution stage and encounters an error.

7. Why is `command_log` a **different** table from Phase 9 `actuator_execution_log`? What concern does each log record (operator intent vs policy/adapter attempt)?

> [!NOTE]
> **_Your Answer_**
>
> The two tables record different parts of the process. `command_log` records the requested operation, its payload, and the final status, such as success, failed, or rejected. It represents the command request and its outcome. The Phase 9 `actuator_execution_log` records what happened when the decorated actuator port attempted to execute an operation, including whether execution succeeded and which policy was applied. Keeping them separate makes it possible to distinguish a rejected request from an actual execution attempt.

## C. Compare, contrast, and scenarios

8. Contrast Command with **Strategy**. Strategy is an interchangeable **algorithm** (decide / quote). Command is a **side-effectful request** with history. How do they cooperate in this app (Phase 6 recommends; Phase 10 executes)?

> [!NOTE]
> **_Your Answer_**
>
> Strategy and Command solve different problems. Strategy selects an algorithm or decision policy. In our project, an automation strategy evaluates sensor readings and recommends whether irrigation is needed. Command represents an operation that can be executed, such as starting the water pump, and records its result. They can work together because Strategy can make the recommendation, while Command carries out the requested actuator operation.

9. Contrast Command with **State**. Who **triggers** the action, and who **decides whether it is legal**? Why must commands not bypass state guards?

> [!NOTE]
> **_Your Answer_**
>
> Command represents and triggers the requested operation, while State determines which operations are allowed in the current actuator state. For example, a pump can be started when it is idle, but it cannot be stopped when it is already idle. The command service checks this before execution. Commands must not bypass state guards because that could allow invalid operations and cause inconsistent actuator states.

10. The controls UI should disable actions that are not in `allowed_commands`. Why must the **backend** still reject illegal commands even if the UI is correct? What happens if a classmate’s command calls the raw adapter and skips State and Decorator?

> [!NOTE]
> **_Your Answer_**
>
> The frontend improves usability by disabling actions that are not allowed, but it cannot be trusted as the only protection. Someone could send a request directly to the API without using the UI. Therefore, the backend must validate every command independently. If a command calls the raw adapter and skips State and Decorator, it could execute an operation that should not be allowed and bypass protections such as maximum runtime checking and execution logging. Using the application service and decorated actuator port keeps these checks in place.

