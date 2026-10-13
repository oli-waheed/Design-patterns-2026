# Strategy Pattern — Smart Greenhouse

## Overview

The Strategy pattern defines a family of algorithms, keeps each algorithm in a separate class, and makes them interchangeable.

In the Smart Greenhouse application, strategies evaluate soil moisture readings and recommend whether irrigation is needed. The application can switch between different decision policies without rewriting the evaluation process.

A strategy only makes a recommendation. It does not activate a pump or directly control greenhouse hardware.

## Problem

If all irrigation rules are placed in one large service method with `if/elif` branches, the code becomes harder to maintain and test. Adding another policy also requires changing the same method.

The Strategy pattern solves this problem by separating each decision policy into its own class. The application selects a strategy through a common interface, and the selected strategy makes the decision.

## Strategy interface

The common interface is `AutomationStrategy`. Each strategy implements:

`decide(context)`

The method receives a `LocationAutomationContext` and returns a `Recommendation` containing an action, a reason, and an optional score.

The context is a plain Python object. It contains the location ID, zone ID, latest moisture reading, and the zone's low and high moisture thresholds. Strategy classes do not depend on SQLAlchemy models or FastAPI request objects.

## Concrete strategies

### Conservative moisture strategy

The conservative strategy recommends `irrigate` when moisture is below the zone's low threshold. Otherwise, it recommends `wait`.

### Aggressive moisture strategy

The aggressive strategy recommends `irrigate` when moisture is below the zone's high threshold. Otherwise, it recommends `wait`.

For example, if the low threshold is `0.30`, the high threshold is `0.60`, and moisture is `0.45`, the conservative strategy recommends `wait`, while the aggressive strategy recommends `irrigate`.

If a zone has no available moisture reading, the strategy recommends `wait` and explains that the reading is unavailable.

## Where the pattern is used

| Component | Responsibility |
|---|---|
| `LocationAutomationContext` | Holds the location, zone, moisture reading, and thresholds. |
| `AutomationStrategy` | Defines the common `decide(context)` interface. |
| `ConservativeMoistureStrategy` | Implements the conservative decision rules. |
| `AggressiveMoistureStrategy` | Implements the aggressive decision rules. |
| `STRATEGIES` | Maps supported strategy keys to strategy instances. |
| `AutomationRepository` | Reads zone and sensor data, and saves the selected strategy. |
| `AutomationService` | Loads the selected strategy and evaluates each zone. |
| Automation API router | Provides endpoints to save a strategy and request an evaluation. |

## Persistence choice

This implementation uses a dedicated `automation_rules` table rather than adding strategy fields to the `locations` table.

Each rule stores a `location_id`, a `strategy_key`, optional JSON parameters, and an update timestamp. The `location_id` is unique, so each location has one active strategy selection.

The supported strategy keys are `conservative` and `aggressive`. The application validates a key before saving it. If no strategy has been saved, the current service uses `conservative` as its default and saves that choice during evaluation.

## Evaluation workflow

1. The client selects a strategy and saves it for a location.
2. The application validates the strategy key and persists it.
3. When evaluation is requested, the service loads the saved strategy key.
4. The service loads the zones belonging to the location.
5. For each zone, it reads that zone's own moisture thresholds and the latest reading from an assigned moisture sensor.
6. The service builds a `LocationAutomationContext` and passes it to the selected strategy.
7. The strategy returns a recommendation, which the application includes in the evaluation response.

A zone must not borrow readings from an unassigned device. Readings may already exist from a manual read, the simulation sampler, or a translated MQTT payload. This phase does not add another scheduler or an MQTT broker.

## API endpoints

### Save the selected strategy

`PUT /api/locations/{location_id}/automation/strategy`

Example request:

```json
{
  "strategy_key": "aggressive"
}
```

The selected key is stored for that location. An unknown key returns HTTP `400 Bad Request`, while a missing location returns HTTP `404 Not Found`.

### Evaluate automation

`POST /api/locations/{location_id}/automation/evaluate`

The service uses the persisted strategy key and evaluates the location's zones. The response contains the location ID, strategy key, and a recommendation for each zone, including its action and reason.

Evaluation does not activate any pump.

## Benefits

- Decision rules are separated from database and API code.
- The application can switch policies without rewriting the evaluation workflow.
- Each strategy can be tested independently.
- New strategies can be added without putting every rule in one large conditional block.
- Different zones can use their own thresholds.

## Adding a third strategy

As an exercise, add a `BalancedMoistureStrategy` class with a decision rule of your choice.

1. Implement `decide(context)` and return a `Recommendation`.
2. Handle a missing moisture reading safely.
3. Register the new strategy in `STRATEGIES` with a key such as `balanced`.
4. Add a unit test that checks its recommendation.
5. Verify that the existing conservative and aggressive strategies still work.

The new strategy should use the thresholds from the context. Do not hardcode zone-specific values, import SQLAlchemy into the strategy class, or activate a pump from `decide()`.

## Testing

The strategy unit tests check that:

- The conservative strategy waits when moisture is above the low threshold.
- The aggressive strategy irrigates when moisture is below the high threshold.
- Both strategies return different recommendations for the same context when appropriate.
- Both strategies recommend waiting when the moisture reading is missing.
- Supported strategy keys resolve correctly.
- Unknown strategy keys are rejected.

Run the backend tests from the `backend` directory:

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
```

## Safety and future improvements

The current strategies provide recommendations only. A separate control workflow must handle execution, with the necessary safety checks before activating equipment. The Command pattern in Phase 10 is intended to represent actions such as controlling a device.

Future improvements could include additional strategies, configurable parameters, or other environmental readings. Each new policy should remain separate from the application and hardware-control logic.