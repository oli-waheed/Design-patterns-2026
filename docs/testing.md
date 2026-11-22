# Testing — Smart Greenhouse

All commands run from `backend/` with the virtual environment active and PostgreSQL running (`docker compose up -d` from the project root).

## Run everything

```powershell
pytest -q
```

## The test database

The suite **never uses your development database**. `tests/conftest.py`:

1. Uses `TEST_DATABASE_URL` if it is set; otherwise takes `DATABASE_URL` from `.env` and adds `_test` to the name (`greenhouse` → `greenhouse_test`).
2. Creates that database if it does not exist and runs `alembic upgrade head` once per run.
3. After **every** test, truncates all tables and inserts the Phase 12 demo seed again, so each test starts from the same state and tests do not depend on each other.

To use another database explicitly:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://greenhouse:greenhouse@localhost:5432/greenhouse_test"
pytest -q
```

## Migration smoke test

Empty PostgreSQL database → `alembic upgrade head`:

```powershell
python scripts/migration_smoke.py
```

It creates a throwaway database `greenhouse_migration_smoke`, runs the real `alembic upgrade head`, checks that it is at head with all tables and the demo seed, runs the upgrade again (nothing to do), and drops the database. `tests/integration/test_migration_smoke.py` runs the same check inside pytest.

## API demo scenario

With the backend running:

```powershell
python scripts/demo_scenario.py
```

See [demo.md](demo.md) for the story it follows. `tests/integration/test_demo_scenario.py` runs it in the test suite as well.

## What is covered

### Unit tests — pattern seams (no database, no UI)

| Seam | What is asserted | Test file |
|---|---|---|
| Factory Method | Each creator has its own defaults | `tests/test_factory_method.py` |
| Abstract Factory | Simulation and edge kits differ | `tests/test_abstract_factory.py` |
| Builder | Invalid configs are rejected (name, zones, thresholds, duplicates) | `tests/test_location_builder.py` |
| Adapter | Vendor and MQTT payloads become a normalized `Reading`; wrong device rejected | `tests/test_vendor_adapter.py`, `test_mqtt_adapter.py`, `test_sensor_adapters.py` |
| Strategy | Same context, two keys, different decision | `tests/test_automation_strategy.py` |
| Facade | Overview assembled from fakes; one batched readings query; recommendation only with a saved strategy | `tests/test_overview_facade.py` |
| State | Illegal transition raises and leaves the state unchanged | `tests/test_actuator_state.py` |
| Decorator | Max run-time blocks the inner adapter; blocked attempt logged | `tests/test_actuator_decorators.py` |
| Command | Rejected command does not reach the adapter or change state | `tests/test_commands.py` |
| Observer | Subscribers run in order on publish; a failing subscriber does not stop others | `tests/test_event_bus.py`, `test_alert_subscribers.py`, `test_reading_events.py` |

Some files (for example `test_alert_subscribers.py`) also insert rows to prove that a subscriber persists; they use the test database.

### Integration tests — HTTP + PostgreSQL (`tests/integration/`)

The `client` fixture overrides FastAPI's `get_db` so every request uses a session on the test database, and the `db` fixture lets the test check rows directly.

| File | Flow |
|---|---|
| `test_locations_api.py` | Create a location config (Builder) and check `locations` / `zones` rows; invalid config saves nothing; rename persists |
| `test_readings_api.py` | Take a reading; device HTTP reading with `source = http`; time-range query returns exactly the rows in the window |
| `test_automation_api.py` | Save a strategy, evaluate, check `automation_rules`; overview (Facade) shows it |
| `test_commands_api.py` | Post commands: success changes `actuator_states`, rejected does not and never reaches the execution log |
| `test_migration_smoke.py` | Empty database → head |
| `test_demo_scenario.py` | The documented demo, twice in a row |

Other HTTP tests at the top level of `tests/` cover alerts, WebSocket frames, device HTTP, MQTT handling without a broker, and the schema hardening.

### Frontend

`npm run lint` and `npm run build` (TypeScript type check) run in CI. There are no component tests; the API demo scenario documents and checks the dashboard's click path instead (see [demo.md](demo.md)).

### Not covered (on purpose)

- A real Mosquitto broker and a physical ESP32: the MQTT path is tested by calling the message handler directly, and the device HTTP path through the API.
- Browser end-to-end tests: replaced by the API scenario script, as the Phase 14 requirements allow.

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request:

1. **backend:** PostgreSQL 16 service → `pip install -e ".[dev]"` → `python scripts/migration_smoke.py` → `pytest -q`
2. **frontend:** `npm ci` → `npm run lint` → `npm run build`
