# Phase 8 — State questions

**Pattern / focus:** State.

**Read first:** [Guide 08](../../materials/guides/08-state.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example support-ticket states) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to actuator lifecycle, persisted state, and `allowed_commands` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of the State pattern in plain language. What problem appears when lifecycle is modelled as boolean flags and scattered if guards?

> [!NOTE]
> ***Your Answer***
>
> The State pattern lets an object behave according to its current state. In our project, an actuator can be idle, running, or in another defined state, and each state allows different actions. If we use many boolean flags and separate if statements, it is easy to create confusing or conflicting situations, for example, an actuator could be marked as running and in maintenance at the same time. It also becomes harder to keep the rules in one place.

2. Name the participants (**context**, **state interface**, **concrete states**, **client**). How does a successful command lead to a transition, and where do guards live?

> [!NOTE]
> ***Your Answer***
>
> The context in our implementation is `ActuatorContext`. It holds the current state and checks whether a transition is allowed. We use `ActuatorState` for the state values, and `ALLOWED_TRANSITIONS` and `ALLOWED_COMMANDS` for the rules. We do not have separate state-interface and concrete-state classes in this implementation. The service and API are the clients. When a transition is requested, the context checks the rules first, and changes the state only if the transition is allowed. These checks, or guards, are kept in the domain layer.

3. What is `allowed_commands` (or equivalent) for? Why is exposing “what can I do now?” better than letting the UI guess from a raw state string?

> [!NOTE]
> ***Your Answer***
>
> `allowed_commands` shows which actions are available in the current state. For example, an actuator in the idle state can use `start_pump`, while a running actuator can use `stop_pump`. This helps the dashboard show the correct actions. The frontend does not need to guess the rules from the state name, and the backend remains the main place where the rules are defined.

## B. This phase of the application

4. Which actuator states did you implement (for example `idle`, `running`, `error`)? Sketch the legal transitions (which command or event moves `idle` → `running`, `running` → `idle`, into `error`, and out of `error`).

> [!NOTE]
> ***Your Answer***
>
> I implemented five states, off, idle, running, error, and maintenance. The legal transitions are: off to idle; idle to running, maintenance, error, or off; running to idle or error; error to idle or maintenance; and maintenance to idle or off. The `start_pump` command moves an actuator from idle to running, and `stop_pump` moves it from running to idle. An error can move an actuator into the error state. From error, it can return to idle or move to maintenance.

5. Why is actuator state stored in `actuator_states` (or equivalent) rather than only in process memory? What must still be true after you restart the backend?

> [!NOTE]
> ***Your Answer***
>
> The actuator state is stored in the `actuator_states` table so that it is not lost when the backend stops or restarts. Each state record is connected to a device through `device_id`. Existing actuators get the initial idle state from the database migration, and new actuators also get an initial state when they are saved. After a restart, the backend should load the saved state and return the same state and allowed commands, unless a valid transition has changed them.

6. An illegal transition must raise a domain error and must **not** update the database. Why? Which HTTP status is reasonable for that case (400 or 409), and why should the rule live in the domain rather than in React?

> [!NOTE]
> ***Your Answer***
>
> An illegal transition must be rejected because it does not follow the actuator's lifecycle rules. The context raises `IllegalTransitionError` before the repository saves anything, so the database is not changed. HTTP 409 Conflict is suitable because the requested transition conflicts with the actuator's current state. The rule belongs in the domain, not only in React, because other clients or parts of the application must follow the same rules too.

7. Device JSON gains state and `allowed_commands`. How does the dashboard use those fields (badges, disable illegal buttons)? How does this prepare Phase 10 Command?

> [!NOTE]
> ***Your Answer***
>
> The dashboard loads the state information for each actuator from the actuator-state API endpoint. It displays the current state as a coloured badge, and it also shows the allowed commands returned by the backend. At this stage, the dashboard does not have control buttons to disable. Those controls are planned for Phase 10. The state and allowed-command information will help Phase 10 show only the commands that are valid at that moment.

## C. Compare, contrast, and scenarios

8. Contrast State with **Strategy**. Both look like “context delegates to an object.” Who typically changes the active object, and is the variation a **lifecycle** or a selectable **policy**? Give a greenhouse example of each (this phase vs Phase 6).

> [!NOTE]
> ***Your Answer***
>
> The State pattern manages the lifecycle of an object. Its current state decides which actions and transitions are allowed. In this phase, an actuator changes between states such as idle and running. The Strategy pattern is different, because it provides a choice between policies or algorithms. In Phase 6, the greenhouse can use a conservative or aggressive strategy to decide whether irrigation is recommended. The actuator changes state through valid transitions, while a strategy is selected as an automation policy.

9. Contrast State with a **pile of booleans** (`is_running`, `is_fault`, `is_maintenance`). Why do illegal combinations of flags appear, and how do explicit state objects (or a transition table) prevent that?

> [!NOTE]
> ***Your Answer***
>
> With several boolean flags, each flag can be changed separately. This can create combinations that do not make sense, for example, `is_running` and `is_maintenance` could both be true. An explicit state value represents the actuator's current condition in one place. The transition table then lists the allowed next states, and the context checks the table before changing the state. This prevents transitions that are not permitted.

10. A classmate puts HTTP status mapping or SQLAlchemy commits inside a concrete state class. Another state mutates a flag directly and skips `transition` / `set_state`. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> HTTP status codes and database commits should not be placed inside state classes, because they belong to different parts of the application. The domain should check whether a transition is allowed, the API should convert domain errors into HTTP responses, and the repository should save changes to the database. This keeps the domain independent of FastAPI and SQLAlchemy. Changing a flag or state directly is also risky, because it skips the transition checks. State changes should go through the context so the rules are always applied.
