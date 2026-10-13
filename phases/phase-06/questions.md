# Phase 6 — Strategy questions

**Pattern / focus:** Strategy.

**Read first:** [Guide 06](../../materials/guides/06-strategy.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example shipping quotes) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to irrigation (or lighting) policies, location context, and the automation API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Strategy in plain language. How does the **context** use a strategy, and why must “choose which algorithm” stay separate from “run the algorithm”?

> [!NOTE]
> ***Your Answer***
>
> Strategy keeps different ways of solving a problem in separate classes. The context calls the selected strategy through a common interface, so we can change the algorithm without rewriting the whole process.

2. Name the participants (**strategy**, **concrete strategies**, **context**, **client**). What goes wrong when all policies live as `if/elif` inside the context (or inside an HTTP router)?

> [!NOTE]
> ***Your Answer***
>
> `AutomationStrategy` is the common interface, and the conservative and aggressive classes contain the decision rules. `AutomationService` manages the evaluation, while the client selects the strategy. Too many `if/elif` branches make the code harder to maintain and test.

3. When should you use Strategy, and when should you skip it (one algorithm only; or the variation is a **lifecycle mode** rather than a chosen policy)?

> [!NOTE]
> ***Your Answer***
>
> Strategy is useful when we need different ways to perform the same task, such as choosing an irrigation policy. If there is only one simple algorithm, it may be unnecessary. If behaviour changes with an object's lifecycle, State may be a better choice.

## B. This phase of the application

4. In this lab, what does a strategy’s `decide(context)` return (action + reason)? Give a concrete difference you implemented (or were required to implement) between **conservative** and **aggressive** on the **same** moisture reading and zone thresholds.

> [!NOTE]
> ***Your Answer***
>
> The method returns an action and a reason. If moisture is `0.45`, with thresholds of `0.30` and `0.60`, the conservative strategy recommends `wait`, while the aggressive strategy recommends `irrigate`.

5. Where do the numbers in `LocationAutomationContext` (or your equivalent) come from? Latest moisture may already be in `sensor_readings` from a manual read, the simulation sampler, or MQTT translation — why does this phase not add a scheduler or a broker? Why must strategies receive a plain context object, not SQLAlchemy rows or FastAPI types? Why are thresholds read from **zones**, not hardcoded in the strategy class?

> [!NOTE]
> ***Your Answer***
>
> Moisture comes from the latest stored reading of a sensor assigned to the zone, and the thresholds come from that zone's database record. We do not add another scheduler or broker because readings can already come from existing processes. A plain context keeps strategies independent of the database and API, while zone-specific thresholds allow each zone to have its own settings.

6. The active `strategy_key` is **persisted** per `location_id` (for example in `automation_rules`). Why must `POST .../automation/evaluate` use the **saved** key rather than a key the client sends only in that request? What happens on the next evaluate after the operator changes strategy but moisture stays the same?

> [!NOTE]
> ***Your Answer***
>
> Saving the strategy ensures that each location uses the operator's chosen policy. After the operator changes and saves it, the next evaluation uses the new strategy. With the same moisture reading, the conservative and aggressive strategies can give different recommendations.

7. Strategy **recommends** (irrigate / wait). It should not itself start a pump. Why keep **decide** separate from **execute**? Which later pattern is meant to carry out the action?

> [!NOTE]
> ***Your Answer***
>
> A strategy should only recommend an action, not start the pump itself. Keeping these responsibilities separate allows safety checks before irrigation. The Command pattern in Phase 10 is intended to handle actions like controlling a device.

## C. Compare, contrast, and scenarios

8. Contrast Strategy with **State** (Phase 8). Both delegate to an object with the same shape. Who typically **changes** the active object, and is the variation a **policy** or a **lifecycle**?

> [!NOTE]
> ***Your Answer***
>
> The client usually chooses the active strategy, such as conservative or aggressive irrigation. State changes according to an object's lifecycle. Strategy represents a policy choice, while State represents the object's current mode.

9. Contrast Strategy with **Adapter** (Phase 5) and with **Builder** (Phase 4). Which one translates a foreign API, which one assembles a valid aggregate, and which one swaps an algorithm?

> [!NOTE]
> ***Your Answer***
>
> Adapter translates an external interface into a format our application understands. Builder creates a complex object step by step. Strategy lets us switch between algorithms, such as different irrigation policies.

10. A classmate writes one “mega-strategy” that still contains `if conservative` / `if aggressive` inside a single class. Another strategy class calls the actuator adapter to water immediately. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> A mega-strategy keeps all the rules in one class, making them harder to test and maintain. Each strategy should have its own decision logic. Calling the actuator directly is also wrong, because the strategy should recommend irrigation, not start the pump.