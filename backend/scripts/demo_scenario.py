"""API demo scenario: one happy path through the patterns (Phase 14).

Runs against a live backend and prints each step with its HTTP status:

    python scripts/demo_scenario.py                 # http://localhost:8000
    python scripts/demo_scenario.py http://host:8000

It uses only the demo seed (Demo Greenhouse / Bench 1 / Demo Moisture
Sensor / Demo Water Pump), so it needs no hardware and no broker, and it
leaves the pump idle again so it can be re-run. docs/demo.md describes the
same story with the matching dashboard areas and module paths.
"""

import json
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

DEMO_LOCATION_ID = "00000000-0000-4000-8000-000000000001"
DEMO_ZONE_ID = "00000000-0000-4000-8000-000000000002"
DEMO_SENSOR_ID = "00000000-0000-4000-8000-000000000003"
DEMO_PUMP_ID = "00000000-0000-4000-8000-000000000004"

# (method, path, json body) -> (status code, parsed body)
Http = Callable[[str, str, Any], tuple[int, Any]]


class ScenarioError(AssertionError):
    pass


def urllib_http(base_url: str) -> Http:
    def call(method: str, path: str, body: Any = None) -> tuple[int, Any]:
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            base_url.rstrip("/") + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                raw = response.read()
                return response.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            return exc.code, json.loads(raw) if raw else None

    return call


def run_scenario(http: Http, log: Callable[[str], None] = print) -> dict:
    """Run every step; raise ScenarioError on the first unexpected result."""

    results: dict[str, Any] = {}

    def step(title: str, method: str, path: str, body: Any = None,
             expect: tuple[int, ...] = (200,)) -> Any:
        status, data = http(method, path, body)
        log(f"[{status}] {method:5} {path}  - {title}")

        if status not in expect:
            raise ScenarioError(f"{title}: expected {expect}, got {status}: {data}")

        return data

    log("== 0. Health and reset")
    health = step("API and database are up", "GET", "/health")
    if health.get("db") != "ok":
        raise ScenarioError(f"Database not ok: {health}")

    state = step("Pump state", "GET", f"/api/devices/{DEMO_PUMP_ID}/state")
    if state["state"] == "running":
        step("Reset: stop the pump", "POST", "/api/commands",
             {"device_id": DEMO_PUMP_ID, "command_type": "stop_pump"},
             expect=(200,))
    elif state["state"] != "idle":
        step("Reset: pump back to idle", "POST",
             f"/api/devices/{DEMO_PUMP_ID}/transition", {"target": "idle"})

    log("== 1. Adapter reads the sensor; Observer publishes reading.created")
    reading = step("Read the demo moisture sensor", "POST",
                   f"/api/sensors/{DEMO_SENSOR_ID}/read")
    log(f"     reading {reading['value']:.3f} {reading['unit']} "
        f"(source {reading['source']})")
    results["reading"] = reading

    log("== 2. Strategy recommends; Facade shows it on the overview")
    step("Save the aggressive strategy", "PUT",
         f"/api/locations/{DEMO_LOCATION_ID}/automation/strategy",
         {"strategy_key": "aggressive"})
    evaluation = step("Evaluate automation", "POST",
                      f"/api/locations/{DEMO_LOCATION_ID}/automation/evaluate")
    recommendation = evaluation["recommendations"][0]
    log(f"     {recommendation['zone_name']}: {recommendation['action']} - "
        f"{recommendation['reason']}")
    results["recommendation"] = recommendation

    overview = step("Overview (Facade)", "GET",
                    f"/api/locations/{DEMO_LOCATION_ID}/overview")
    if overview["strategy_key"] != "aggressive":
        raise ScenarioError("Overview does not show the saved strategy")

    log("== 3. Command runs; State allows idle -> running; Decorators apply")
    command = step("Start the pump", "POST", "/api/commands",
                   {"device_id": DEMO_PUMP_ID, "command_type": "start_pump"})
    if command["status"] != "success":
        raise ScenarioError(f"start_pump was {command['status']}")

    state = step("Pump state after start", "GET",
                 f"/api/devices/{DEMO_PUMP_ID}/state")
    log(f"     state {state['state']}, allowed {state['allowed_commands']}")
    if state["state"] != "running":
        raise ScenarioError("Pump is not running")

    executions = step("Execution log (Decorator)", "GET",
                      "/api/actuators/executions?limit=1")
    log(f"     policies {executions[0]['policy_applied']}, "
        f"success {executions[0]['success']}")

    rejected = step("Start again is rejected by State", "POST", "/api/commands",
                    {"device_id": DEMO_PUMP_ID, "command_type": "start_pump"},
                    expect=(409,))
    log(f"     {rejected['status']}: {rejected['error_message']}")

    log("== 4. Low moisture -> Observer -> alert in the event feed")
    step("Device HTTP posts 0.10 vwc", "POST",
         f"/api/devices/{DEMO_SENSOR_ID}/readings",
         {"value": 0.10, "unit": "vwc"}, expect=(201,))
    alerts = step("Active alerts for Bench 1", "GET",
                  f"/api/alerts?zone_id={DEMO_ZONE_ID}")
    alert = next(
        (item for item in alerts if item["event_type"] == "threshold.crossed"),
        None,
    )
    if alert is None:
        raise ScenarioError("No threshold.crossed alert for Bench 1")
    log(f"     {alert['severity']}: {alert['message']}")
    results["alert"] = alert

    log("== 5. Operator stops the pump and resolves the alert")
    step("Stop the pump", "POST", "/api/commands",
         {"device_id": DEMO_PUMP_ID, "command_type": "stop_pump"})
    step("Resolve the alert", "PATCH", f"/api/alerts/{alert['id']}",
         {"status": "resolved"})
    active = step("Active alerts for Bench 1", "GET",
                  f"/api/alerts?zone_id={DEMO_ZONE_ID}")
    if any(item["id"] == alert["id"] for item in active):
        raise ScenarioError("Resolved alert is still active")

    log("Demo scenario passed.")
    return results


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    try:
        run_scenario(urllib_http(base))
    except (ScenarioError, urllib.error.URLError) as exc:
        print(f"Demo scenario FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
