"""The documented demo (docs/demo.md, scripts/demo_scenario.py) runs green
against the API with the demo seed only."""

import importlib.util
from pathlib import Path


def load_scenario():
    path = Path(__file__).resolve().parents[2] / "scripts" / "demo_scenario.py"
    spec = importlib.util.spec_from_file_location("demo_scenario", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_demo_scenario_happy_path(client):
    scenario = load_scenario()

    def http(method, path, body=None):
        response = client.request(method, path, json=body)
        return response.status_code, response.json() if response.content else None

    steps = []
    results = scenario.run_scenario(http, log=steps.append)

    assert steps[-1] == "Demo scenario passed."
    assert results["recommendation"]["action"] in {"irrigate", "wait"}
    assert results["alert"]["message"] == "Moisture below zone low"


def test_demo_scenario_can_run_twice(client):
    scenario = load_scenario()

    def http(method, path, body=None):
        response = client.request(method, path, json=body)
        return response.status_code, response.json() if response.content else None

    scenario.run_scenario(http, log=lambda _: None)
    scenario.run_scenario(http, log=lambda _: None)
