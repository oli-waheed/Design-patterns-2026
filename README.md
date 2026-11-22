# Smart Greenhouse

Design Patterns course project for XAMK.

This project is a three-tier Smart Greenhouse application consisting of:

- Python FastAPI backend
- PostgreSQL database
- React + TypeScript frontend

## Technologies

### Backend

- Python 3.11+
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL 16

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router

### Infrastructure

- Docker Compose
- PostgreSQL 16
- Mosquitto MQTT broker (optional Compose profile, Phase 12)

## Project Structure

```text
design-patterns-2026/
├── backend/
│   ├── alembic/
│   └── src/
├── frontend/
│   └── src/
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## Requirements

- Python 3.11 or newer
- Node.js 20 LTS or newer
- npm
- Docker Desktop
- Git

## Setup

### 1. Clone the repository

```powershell
git clone https://github.com/oli-waheed/Design-patterns-2026.git
cd Design-patterns-2026
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and adjust the values if necessary.

The `.env` file is not committed to Git.

### 3. Start PostgreSQL

From the project root:

```powershell
docker compose up -d
```

Check the database:

```powershell
docker compose ps
```

### 4. Start the backend

Open a terminal:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

API reference:

```text
http://localhost:8000/scalar
```

OpenAPI:

```text
http://localhost:8000/openapi.json
```

Swagger UI is intentionally disabled.

### 5. Start the frontend

Open another terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Frontend:

```text
http://localhost:5173
```

Dashboard:

```text
http://localhost:5173/dashboard
```

## Phase 1

Phase 1 establishes the project foundation:

- Three-tier architecture
- FastAPI backend
- PostgreSQL database
- Alembic baseline migration
- React + TypeScript frontend
- Tailwind CSS
- React Router
- Backend health check
- Frontend health status
- Smart Greenhouse dashboard placeholders

No design pattern is implemented in Phase 1.

## API and realtime (Phase 12)

The course demo needs **no hardware and no broker**. After `alembic upgrade head`, the seed data includes a simulation moisture sensor (`Demo Moisture Sensor`) that the backend samples every 5 seconds, so the dashboard moves on its own.

### REST

All REST endpoints live under `/api` (plus `GET /health`). Scalar at `http://localhost:8000/scalar` lists every route. The frontend reads the backend host from `VITE_API_BASE_URL` in one place (`frontend/src/services/api.ts`).

### Dashboard WebSocket

```text
ws://localhost:8000/api/ws
```

Dashboard only. Devices never connect here. Every frame has the shape `{ "type": string, "payload": object }`:

| `type` | `payload` |
|---|---|
| `reading.created` | `device_id`, `value`, `unit`, `source`, `recorded_at`, `location_id`, `zone_id` |
| `actuator.state_changed` | `device_id`, `previous_state`, `state`, `location_id`, `zone_id` |
| `alert.created` | `id`, `severity`, `message`, `event_type`, `status`, `created_at`, `device_id`, `location_id`, `zone_id` |

`location_id` and `zone_id` are `null` for unassigned devices. Devices with `tracking_enabled = false` produce no `reading.created` frames.

The socket is one more subscriber on the Phase 11 `EventBus`. It only forwards events and never writes rows.

**Fallback:** the header badge shows `Live`, `Connecting…` or `Offline – retrying`. While the socket is connected, the sensor cards and the event feed update from frames and do not poll. While it is down, the sensor cards poll `GET /api/sensors/{id}/readings` and the event feed polls `GET /api/alerts`, both every 5 seconds, until the socket reconnects.

### Device HTTP (for example an ESP32 with `protocol: http`)

The device reads its settings, then posts readings on its own clock. The backend never polls the device and never pushes config to it.

```powershell
# Use the id of a device whose default_config has "protocol": "http".
$id = "<device-id>"
Invoke-RestMethod http://localhost:8000/api/devices/$id/sampling
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/devices/$id/readings -ContentType "application/json" -Body '{"value": 0.41, "unit": "vwc"}'
```

The POST is translated by the Phase 5 translator with `source` `http` and stored by `ReadingIngest`, which publishes `reading.created` when tracking is on. An unknown device returns 404.

### Optional MQTT broker (`protocol: mqtt`)

Mosquitto is a Compose **profile**, so a normal `docker compose up -d` does not start it, and the backend only connects when `MQTT_BROKER_URL` is set.

```powershell
docker compose --profile mqtt up -d mosquitto
```

Then set `MQTT_BROKER_URL=mqtt://localhost:1883` in `.env` and restart the backend.

| Topic | Direction | Body |
|---|---|---|
| `greenhouse/devices/{device_id}/reading` | device → backend | `{ "value": 0.41, "unit": "vwc" }` |
| `greenhouse/devices/{device_id}/config` | backend → device (retained) | `{ "sampling_interval_seconds": 30, "tracking_enabled": true }` |

The retained config is published when `PATCH /api/devices/{device_id}/sampling` updates a device with `protocol: mqtt`. A device on the broker path should follow it. HTTP devices use `GET .../sampling` instead.

Smoke test with the profile running (from `backend/`, venv active, replace `<device-id>` with an MQTT device):

```powershell
python scripts/mqtt_smoke.py <device-id> 0.37
```

A new `sensor_readings` row with `source` `mqtt` appears, and the dashboard receives a `reading.created` frame when tracking is on. Unknown devices are logged and dropped.

### Schema

See [docs/schema.md](docs/schema.md) for the migration chain, foreign-key `ON DELETE` rules, indexes and seed data.

## Dashboard polish (Phase 13, optional)

Phase 13 polishes the existing dashboard; it is not a rewrite and adds no business tables.

- **Design tokens:** `frontend/src/index.css` defines Tailwind v4 `@theme` status colors (ok = emerald, warn = amber, error = red) and shared utilities (`card`, `panel`, `field`, `btn`, `badge-*`, `alert-*`, `empty-state`, `skeleton`). Every panel uses them.
- **Responsive:** sections stack on narrow screens; sensor cards are a 1/2/3-column grid; filters wrap. Checked at 390 px width with no horizontal overflow.
- **Loading / empty / error:** skeletons while loading, an empty state on every list, and an error boundary around each dashboard section so one crash does not blank the page.
- **History chart:** the History section plots stored readings from `GET /api/sensors/{id}/readings?from=&to=` (ISO-8601; range mode returns rows **oldest first**, without `from`/`to` the endpoint keeps returning the latest N newest first). Ranges 15 min to 7 days, hover crosshair with tooltip, zone target band, table view, and “No readings in this range” when empty. New readings are appended live.
- **Index:** no new migration. The Phase 5 index `ix_sensor_readings_device_recorded_at (device_id, recorded_at)` already serves the range query.
- **Alerts:** filter Active / All / Resolved, sort newest or most severe first, scrollable list, and Resolve / Reopen through `PATCH /api/alerts/{id}` with `{ "status": "resolved" }` (resolving also sets `acknowledged_at`).
- **WebSocket:** exponential backoff 1 s → 2 s → 4 s → 8 s → 15 s cap. The header badge shows Live / Connecting / Offline with a retry countdown and a “Retry now” button.
- **API types:** `services/api.ts` matches OpenAPI. Automation recommendations now include `low_threshold`, `high_threshold` and `score`, which the UI already displayed.

### Panel checklist

| Area | Polish task | Status |
|---|---|---|
| Overview | Single refresh; stale-data indicator | Done: one Refresh button; badge shows “updated … ago” and turns into a warning after 60 s without an update |
| Sensors | Sparkline or last-value trend on cards | Done: latest value plus a sparkline of the last 20 readings, live over WebSocket |
| Automation | Show strategy from persisted config | Done: `GET /api/locations/{id}/automation/strategy` loads the saved strategy and flags unsaved changes |
| Controls | Confirm dialog for pump start | Done: Tailwind modal before `start_pump` (Escape or Cancel closes it) |
| Events | Scrollable feed, severity sorting | Done: scrollable list, “Most severe first” sort, resolve / reopen |
| Config | Edit existing location | Done: rename a location (`PATCH /api/locations/{id}`); zones were already editable |

Out of scope, as the requirements say: authentication / roles and a visual rule editor.

## Tests, demo and documentation (Phase 14, optional)

| What | Where |
|---|---|
| Run all backend tests (separate `greenhouse_test` database, reset after every test) | `cd backend` then `pytest -q` — see [docs/testing.md](docs/testing.md) |
| Migration smoke test: empty database → `alembic upgrade head` | `python scripts/migration_smoke.py` (from `backend/`) |
| Demo story touching every pattern, with dashboard areas and code paths | [docs/demo.md](docs/demo.md) |
| Demo as a script that prints each HTTP step (backend running) | `python scripts/demo_scenario.py` (from `backend/`) |
| Pattern notes (problem, intent, code, extension exercise) | [Factory Method](docs/patterns/factory-method.md) · [Abstract Factory](docs/patterns/abstract-factory.md) · [Builder](docs/patterns/builder.md) · [Adapter](docs/patterns/adapter.md) · [Strategy](docs/patterns/strategy.md) · [Facade](docs/patterns/facade.md) · [State](docs/patterns/state.md) · [Decorator](docs/patterns/decorator.md) · [Command](docs/patterns/command.md) · [Observer](docs/patterns/observer.md) |
| Database schema, migrations, indexes, seed | [docs/schema.md](docs/schema.md) |
| Continuous integration (tests, migration smoke, lint, build) | `.github/workflows/ci.yml` |

## Phase Roadmap

See [docs/phases/README.md](docs/phases/README.md) for the complete phase order.

## API Health

The backend provides:

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "db": "ok"
}
```

## License

Course project for educational purposes.