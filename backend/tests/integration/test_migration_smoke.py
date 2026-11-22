"""Migration smoke: an empty database migrates to head (scripts/migration_smoke.py)."""

import importlib.util
from pathlib import Path

from infrastructure.settings import settings


def load_smoke_script():
    path = Path(__file__).resolve().parents[2] / "scripts" / "migration_smoke.py"
    spec = importlib.util.spec_from_file_location("migration_smoke", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_empty_database_upgrades_to_head():
    steps = []

    load_smoke_script().run_smoke(settings.database_url, log=steps.append)

    assert steps[-1] == "Migration smoke test passed."
    assert any(step.startswith("   OK: at head") for step in steps)
