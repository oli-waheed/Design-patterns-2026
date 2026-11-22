# Demo — one story through the patterns

This walk-through uses only the demo seed from the Phase 12 migration, so it needs no hardware and no MQTT broker:

| Seed row | Name |
|---|---|
| Location | Demo Greenhouse |
| Zone | Bench 1 (moisture low 0.20, high 0.60) |
| Sensor | Demo Moisture Sensor (simulation, every 5 s, tracking on, in Bench 1) |
| Actuator | Demo Water Pump (simulation, unassigned, idle) |

## Before you start

```powershell
docker compose up -d                  # PostgreSQL
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head                  # schema + demo seed
cd src
uvicorn main:app --reload --port 8000
```

In a second terminal: `cd frontend` then `npm run dev`, and open `http://localhost:5173/dashboard`. The header badge should say **Live**.

To run the same story without the browser, use the API script (from `backend/`, with the backend running):

```powershell
python scripts/demo_scenario.py
```

It prints every step with its HTTP status and fails loudly if a step does not behave as described below. The test suite runs the same scenario (`tests/integration/test_demo_scenario.py`).

## The story

### 1. A reading arrives — Adapter, then Observer

| | |
|---|---|
| **In the dashboard** | **Sensors** → *Demo Moisture Sensor* → **Read now** (or just wait: the sampler reads it every 5 s). The value and sparkline update without polling. |
| **What happens** | `SensorAdapterSelector` picks `SimulationSensorAdapter`, which returns a normalized `Reading`. `ReadingIngest` stores it and publishes `ReadingCreated` on the `EventBus`. The WebSocket subscriber forwards it to the browser as `reading.created`. |
| **Code** | `backend/src/infrastructure/adapters/sensors/` · `backend/src/application/readings/service.py` · `backend/src/domain/events/bus.py` · `backend/src/application/realtime/ws_subscriber.py` · `frontend/src/features/sensors/SensorList.tsx` |
| **Script step** | `== 1. Adapter reads the sensor; Observer publishes reading.created` |

### 2. The system recommends — Strategy, shown through the Facade

| | |
|---|---|
| **In the dashboard** | **Automation** → location *Demo Greenhouse* → choose **Aggressive** → **Save Strategy** → **Evaluate Automation**. Then **Overview** (press **Refresh** if needed) shows the saved strategy, the recommendation, and Bench 1's latest reading. |
| **What happens** | `AutomationService` loads the saved key, builds a `LocationAutomationContext` and calls `AggressiveMoistureStrategy.decide()`. With moisture between 0.20 and 0.60 the aggressive strategy says *irrigate* where conservative would say *wait*. `OverviewFacade.get_overview()` combines location, zones, devices, latest readings and the recommendation in one response. |
| **Code** | `backend/src/domain/automation/strategy.py` · `backend/src/application/automation/automation_service.py` · `backend/src/application/overview/facade.py` · `frontend/src/features/automation/StrategyPanel.tsx` · `frontend/src/features/overview/OverviewPanel.tsx` |
| **Script step** | `== 2. Strategy recommends; Facade shows it on the overview` |

### 3. The operator acts — Command, State, Decorator

| | |
|---|---|
| **In the dashboard** | **Controls** → *Demo Water Pump* → **Start pump** → confirm in the dialog. The state badge changes to *running*, **Command history** shows *success*, and **Events → Recent actuator executions** shows the attempt with policies `logging`. Clicking Start again is impossible (the button is disabled); through the API it is *rejected*. |
| **What happens** | `CommandService` creates `StartPumpCommand` from the registry, checks the State rules (`idle → running` is allowed), and runs it through `CommandInvoker` against the decorated port: `LoggingActuatorDecorator → MaxRunTimeActuatorDecorator → SimulationActuatorAdapter`. The new state is saved and `ActuatorStateChanged` is published, so other open dashboards update too. |
| **Code** | `backend/src/domain/commands/` · `backend/src/application/commands/service.py` · `backend/src/domain/actuators/state.py` · `backend/src/infrastructure/adapters/actuators/` · `frontend/src/features/actuators/CommandPanel.tsx` |
| **Script step** | `== 3. Command runs; State allows idle -> running; Decorators apply` |

### 4. Moisture drops — Observer creates an alert, WebSocket pushes it

| | |
|---|---|
| **In the dashboard** | Watch **Events → Alerts** while a low reading arrives. The quickest way is device HTTP (PowerShell, from any folder):<br>`Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/devices/00000000-0000-4000-8000-000000000003/readings -ContentType "application/json" -Body '{"value": 0.10, "unit": "vwc"}'`<br>A **Warning – Moisture below zone low** alert appears within a second, and **History** shows the dip. |
| **What happens** | The reading goes through the Phase 5 translator and `ReadingIngest` (source `http`). `MoistureThresholdSubscriber` sees 0.10 < 0.20 for Bench 1 and publishes `ThresholdCrossed`; `AlertPersistenceSubscriber` stores the alert and publishes `AlertCreated`; the WebSocket subscriber pushes `alert.created`. No publisher writes the alert itself. |
| **Code** | `backend/src/interfaces/api/devices.py` (`POST .../readings`) · `backend/src/application/alerts/subscribers.py` · `backend/src/composition.py` · `frontend/src/components/alerts/EventFeed.tsx` · `frontend/src/features/history/SensorHistoryChart.tsx` |
| **Script step** | `== 4. Low moisture -> Observer -> alert in the event feed` |

### 5. Back to normal — stop the pump and resolve the alert

| | |
|---|---|
| **In the dashboard** | **Controls** → **Stop pump** (state returns to *idle*). **Events → Alerts** → **Resolve** on the alert; switch the filter to **Resolved** to see it there, and reload the page to show it stays resolved. |
| **What happens** | `StopPumpCommand` runs (`running → idle`). `PATCH /api/alerts/{id}` sets `status = resolved` and `acknowledged_at`. |
| **Code** | `backend/src/interfaces/api/alerts.py` · `backend/src/infrastructure/persistence/alert_repository.py` |
| **Script step** | `== 5. Operator stops the pump and resolves the alert` |

### Optional: show resilience

- Stop the backend (Ctrl+C). The header badge turns to **Offline · retry in N s**, and the sensor cards fall back to polling.
- Start it again. The badge returns to **Live** without reloading the page (backoff 1 s → 2 s → 4 s → 8 s → 15 s).

## Patterns covered

| Phase | Pattern | Step |
|---|---|---|
| 2 | Factory Method | **Sensors → Add sensor** creates a sensor through `MoistureSensorCreator` / `LightSensorCreator` defaults (the demo seed itself is inserted by the migration) |
| 3 | Abstract Factory | **Devices → Provision device family** creates a whole simulation or edge kit |
| 4 | Builder | **Configuration → Create** a location (invalid thresholds or duplicate zone names are rejected) |
| 5 | Adapter | Step 1, step 4 |
| 6 | Strategy | Step 2 |
| 7 | Facade | Step 2 |
| 8 | State | Step 3, step 5 |
| 9 | Decorator | Step 3 |
| 10 | Command | Step 3, step 5 |
| 11 | Observer | Steps 1, 3, 4 |
| 12 | WebSocket / device HTTP | Steps 1, 4, resilience |
| 13 | Dashboard polish | History chart, alert resolve, confirm dialog, connection badge |
