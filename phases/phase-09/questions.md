# Phase 9 — Decorator questions

**Pattern / focus:** Decorator.

**Read first:** [Guide 09](../../materials/guides/09-decorator.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example HTTP client wrappers) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to `ActuatorPort`, policy decorators, and `actuator_execution_log` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Decorator in plain language. Why is stacking wrappers a flexible alternative to a combinatorial explosion of subclasses (`LoggingRetryMaxRuntimeActuator`, …)?

> [!NOTE]
> ***Your Answer***
>
> The Decorator pattern adds extra behaviour to an existing object by wrapping it with another object that has the same interface. We can stack different decorators to add features such as logging, retry, or runtime protection. Without decorators, we might need to create many subclasses for every possible combination of features. With composition, we can combine the behaviours more easily and change the order when needed.

2. Name the participants (**component**, **concrete component**, **decorator**, **concrete decorators**). What interface does every decorator present to the caller, and why must that match the wrapped component?

> [!NOTE]
> ***Your Answer***
>
> The component is `ActuatorPort`, which defines the common `apply()` method. The concrete component is `SimulationActuatorAdapter`, which performs the actual simulated operation. The decorator is a wrapper that also implements `ActuatorPort`, and the concrete decorators in our project are `LoggingActuatorDecorator` and `MaxRunTimeActuatorDecorator`. Every decorator must keep the same interface so the caller can use the wrapped object without knowing how many decorators are in the chain.

3. **Order matters.** Using logging and retry (or logging and max-run-time) as an example, explain how wrapping A around B can change what you observe compared with wrapping B around A.

> [!NOTE]
> ***Your Answer***
>
> The order of decorators changes which operations are performed first and what gets recorded. In our project, logging is the outer decorator and max run-time is inside it. When max run-time blocks a command, the logging decorator catches the exception and records the failed attempt. If logging were placed inside the max-runtime decorator, it might never be called when the runtime policy blocks execution, so the failed attempt could be missed. Therefore, the order is important for correct logging.

## B. This phase of the application

4. What is `ActuatorPort` here, and which **at least two** decorators did you stack around the real adapter (for example logging and max run-time)? Where is the chain wired (composition root / factory), and why not inside the HTTP router?

> [!NOTE]
> ***Your Answer***
>
> `ActuatorPort` is the common interface for actuator operations. In our implementation, I use `LoggingActuatorDecorator` and `MaxRunTimeActuatorDecorator` around `SimulationActuatorAdapter`. The chain is built in one place, the `build_actuator_port()` factory in `infrastructure/adapters/actuators/factory.py`, and the application services such as `CommandService` call it. It should not be created inside the HTTP router because the router should handle HTTP requests and responses, not contain the logic for composing actuator policies. Keeping the chain in one factory makes it easier to test and to change the order or add a new policy.

5. Max run-time can **short-circuit**: the inner adapter is never called. Why must a blocked attempt still produce a row in `actuator_execution_log` with `success=false` and the policy named in `policy_applied`?

> [!NOTE]
> ***Your Answer***
>
> Even if the command is blocked, it is still an execution attempt that should be recorded. The database log helps us understand what happened and why the actuator did not execute the command. It also provides a history for the dashboard and makes failures easier to investigate. In this case, the record has `success=false`, `policy_applied` contains `maxRunTime` and `logging`, and the message explains that the maximum runtime was exceeded.

6. How does max run-time know the actuator has been running too long (for example `actuator_states.updated_at` from Phase 8)? Why is that data from **State**, not something the decorator should invent as a second lifecycle?

> [!NOTE]
> ***Your Answer***
>
> The max-runtime decorator reads the actuator state and its `updated_at` timestamp from the existing actuator state data. If the actuator is still running and the last update was at least 30 minutes ago, the decorator blocks the command. This information belongs to the State implementation because it already manages the actuator lifecycle and stores its current state. The decorator should only use that information to apply the runtime policy, not create another state system.

7. `GET /api/actuators/executions` feeds the dashboard execution log. Why persist attempts in the database instead of only printing to stdout? What should the UI show after a blocked attempt and a refresh?

> [!NOTE]
> ***Your Answer***
>
> Printing messages to stdout is useful during development, but those messages are not a reliable execution history and are not available to the dashboard. By saving attempts in `actuator_execution_log`, the records remain available after a backend restart and can be retrieved through the API. After a blocked attempt and a refresh, the UI should show the failed result, the device name, the applied policies, the error message, and the execution time.

## C. Compare, contrast, and scenarios

8. Contrast Decorator with **Adapter**. Both wrap. One **keeps** the interface and **adds** behaviour; the other **changes** the interface and **translates**. Which is which in this greenhouse (Phase 9 vs Phase 5)?

> [!NOTE]
> ***Your Answer***
>
> Decorator keeps the same interface and adds extra behaviour around an existing object. In Phase 9, the decorators implement `ActuatorPort` and add logging and runtime protection. Adapter has a different purpose: it translates an existing or external interface into the interface that our application expects. In Phase 5, the sensor adapters translate different data formats into one `Reading`. For example, `VendorSensorAdapter` converts fields such as `readingValue` and `measurementUnit`, and `MqttSensorAdapter` converts an MQTT payload. So Decorator adds behaviour, while Adapter makes different interfaces work together.

9. Contrast Decorator with **inheritance** of combined policies. How does composition let you add or remove a policy without a new subclass for every combination?

> [!NOTE]
> ***Your Answer***
>
> With inheritance, we might need separate subclasses for combinations such as logging with runtime protection, logging with retry, or all three together. This can create too many classes and make the code harder to maintain. With Decorator, we can wrap the actuator with only the policies we need. We can add, remove, or reorder decorators without creating a new subclass for every combination.

10. A classmate’s decorator changes the method signature “a little” (extra required argument, different return type). Another ignores wrap order and cannot explain whether logging runs once per logical call or per inner attempt. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> Every decorator should follow the same `ActuatorPort` interface and method signature. If one decorator changes the arguments or return type, it breaks the common interface and makes the chain difficult to use interchangeably. The order also matters because it determines what gets logged and when. For example, logging outside a retry decorator can record one logical operation, while logging inside it can record each individual attempt. In our implementation, logging is outside max run-time so even a blocked operation is recorded.
