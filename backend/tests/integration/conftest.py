"""Fixtures for HTTP + database integration tests.

The root tests/conftest.py already points the app at the migrated test
database and resets it after every test. Here the FastAPI dependency
get_db is overridden so each request uses a session from that database,
and `db` gives the test its own session to check rows directly.
"""

import pytest
from fastapi.testclient import TestClient

from infrastructure.db import SessionLocal, get_db
from main import app


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
