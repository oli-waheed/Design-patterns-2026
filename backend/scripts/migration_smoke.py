"""Migration smoke test: empty PostgreSQL database -> alembic upgrade head.

Creates a throwaway database, runs the real `alembic upgrade head` command
against it, checks the result, then drops the database again. Your
development and test databases are not touched.

Usage (from backend/, venv active, Postgres running):

    python scripts/migration_smoke.py

It reads the server address from DATABASE_URL (.env). Exit code 0 means
the full migration chain works from an empty database.
"""

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
SMOKE_DATABASE = "greenhouse_migration_smoke"

EXPECTED_TABLES = {
    "locations",
    "zones",
    "devices",
    "sensor_readings",
    "automation_rules",
    "actuator_states",
    "actuator_execution_log",
    "command_log",
    "alerts",
}

DEMO_SENSOR_ID = "00000000-0000-4000-8000-000000000003"


def _server_url() -> str:
    url = os.environ.get("DATABASE_URL")

    if not url:
        sys.path.insert(0, str(BACKEND_DIR / "src"))
        from infrastructure.settings import settings

        url = settings.database_url

    return url


def _alembic(args: list[str], database_url: str) -> str:
    env = {**os.environ, "DATABASE_URL": database_url}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"alembic {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}"
        )

    return result.stdout + result.stderr


def _head_revision() -> str:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return ScriptDirectory.from_config(config).get_current_head()


def run_smoke(server_url: str | None = None, log=print) -> None:
    server_url = server_url or _server_url()
    base = make_url(server_url)
    smoke_url = base.set(database=SMOKE_DATABASE).render_as_string(
        hide_password=False
    )

    admin = create_engine(base.set(database="postgres"), isolation_level="AUTOCOMMIT")

    def recreate(drop_only: bool = False) -> None:
        with admin.connect() as connection:
            connection.execute(
                text(f'DROP DATABASE IF EXISTS "{SMOKE_DATABASE}" WITH (FORCE)')
            )
            if not drop_only:
                connection.execute(text(f'CREATE DATABASE "{SMOKE_DATABASE}"'))

    try:
        log(f"1. Create empty database {SMOKE_DATABASE}")
        recreate()

        log("2. alembic upgrade head")
        _alembic(["upgrade", "head"], smoke_url)

        log("3. Check revision, tables and seed")
        engine = create_engine(smoke_url)
        try:
            with engine.connect() as connection:
                current = connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one()
                tables = set(inspect(connection).get_table_names())
                seeded = connection.execute(
                    text(
                        "SELECT sampling_interval_seconds, tracking_enabled "
                        "FROM devices WHERE id = :id"
                    ),
                    {"id": DEMO_SENSOR_ID},
                ).one_or_none()
        finally:
            engine.dispose()

        head = _head_revision()

        if current != head:
            raise AssertionError(f"Database is at {current}, expected head {head}")

        missing = EXPECTED_TABLES - tables
        if missing:
            raise AssertionError(f"Missing tables after upgrade: {sorted(missing)}")

        if seeded is None or tuple(seeded) != (5, True):
            raise AssertionError("Demo seed sensor (5 s, tracking on) is missing")

        log(f"   OK: at head {head}, {len(tables)} tables, demo seed present")

        log("4. alembic upgrade head again (nothing to do)")
        _alembic(["upgrade", "head"], smoke_url)

    finally:
        log(f"5. Drop {SMOKE_DATABASE}")
        recreate(drop_only=True)
        admin.dispose()

    log("Migration smoke test passed.")


if __name__ == "__main__":
    try:
        run_smoke()
    except Exception as exc:  # noqa: BLE001 - print a clear failure for the CLI
        print(f"Migration smoke test FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
