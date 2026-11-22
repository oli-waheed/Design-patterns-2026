"""Test database setup for the whole backend suite (Phase 14).

- Tests never touch the development database. They use a separate
  database: TEST_DATABASE_URL if set, otherwise the DATABASE_URL from .env
  with "_test" appended to the database name (greenhouse -> greenhouse_test).
- The test database is created if it does not exist and migrated to head
  once per run (the same Alembic chain as production).
- After every test all tables are truncated and the Phase 12 demo seed is
  inserted again, so each test starts from the same known state.

This file is imported by pytest before any test module, which is why it
can point the app's settings at the test database before the engine in
infrastructure.db is created.
"""

import importlib.util
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from infrastructure.settings import settings

BACKEND_DIR = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"
ALEMBIC_DIR = BACKEND_DIR / "alembic"


def _test_database_url() -> str:
    explicit = os.environ.get("TEST_DATABASE_URL")

    if explicit:
        return explicit

    url = make_url(settings.database_url)
    name = url.database or "greenhouse"

    if not name.endswith("_test"):
        name = f"{name}_test"

    return url.set(database=name).render_as_string(hide_password=False)


TEST_DATABASE_URL = _test_database_url()

# Point the app (engine, sessions, Alembic env.py) at the test database
# before infrastructure.db is imported anywhere.
settings.database_url = TEST_DATABASE_URL
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from infrastructure.db import engine


def _ensure_database_exists(url: str) -> None:
    parsed = make_url(url)
    admin = create_engine(
        parsed.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )

    try:
        with admin.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": parsed.database},
            ).scalar()

            if not exists:
                connection.execute(text(f'CREATE DATABASE "{parsed.database}"'))
    finally:
        admin.dispose()


def _alembic_config():
    from alembic.config import Config

    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(ALEMBIC_DIR))
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    return config


def _load_hardening_migration():
    """The Phase 12 revision that holds the idempotent demo seed."""

    path = next(ALEMBIC_DIR.glob("versions/*_schema_hardening.py"))
    spec = importlib.util.spec_from_file_location("schema_hardening", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _reset_database(seed_module) -> None:
    """Truncate every app table, then insert the demo seed again."""

    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext

    with engine.begin() as connection:
        # Fail instead of hanging if a test left a transaction open.
        connection.execute(text("SET LOCAL lock_timeout = '5s'"))

        tables = connection.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        ).scalars().all()

        if tables:
            joined = ", ".join(f'"{name}"' for name in tables)
            connection.execute(text(f"TRUNCATE {joined} RESTART IDENTITY CASCADE"))

        context = MigrationContext.configure(connection)

        with Operations.context(context):
            seed_module.seed_demo_data()


@pytest.fixture(scope="session")
def test_database():
    """Create and migrate the test database once per run."""

    from alembic import command

    _ensure_database_exists(TEST_DATABASE_URL)
    command.upgrade(_alembic_config(), "head")

    seed_module = _load_hardening_migration()
    _reset_database(seed_module)

    yield seed_module

    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(test_database):
    """Every test starts from the migrated schema plus the demo seed."""

    yield
    _reset_database(test_database)
