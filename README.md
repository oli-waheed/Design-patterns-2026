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