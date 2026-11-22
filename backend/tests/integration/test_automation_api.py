"""Strategy (Phase 6) through HTTP: persisted key, same data, different decision."""

from sqlalchemy import select

from infrastructure.persistence.models import AutomationRuleRow

from .seed_ids import DEMO_LOCATION_ID, DEMO_SENSOR_ID


def set_moisture(client, value):
    response = client.post(
        f"/api/devices/{DEMO_SENSOR_ID}/readings",
        json={"value": value, "unit": "vwc"},
    )
    assert response.status_code == 201


def evaluate(client):
    response = client.post(
        f"/api/locations/{DEMO_LOCATION_ID}/automation/evaluate"
    )
    assert response.status_code == 200
    return response.json()


def save(client, key):
    response = client.put(
        f"/api/locations/{DEMO_LOCATION_ID}/automation/strategy",
        json={"strategy_key": key},
    )
    assert response.status_code == 200


def test_saved_strategy_decides_and_is_persisted(client, db):
    # Bench 1 thresholds from the seed: low 0.20, high 0.60.
    set_moisture(client, 0.45)

    save(client, "conservative")
    conservative = evaluate(client)

    save(client, "aggressive")
    aggressive = evaluate(client)

    assert conservative["recommendations"][0]["action"] == "wait"
    assert aggressive["recommendations"][0]["action"] == "irrigate"
    assert aggressive["recommendations"][0]["moisture"] == 0.45

    rule = db.scalars(
        select(AutomationRuleRow).where(
            AutomationRuleRow.location_id == DEMO_LOCATION_ID
        )
    ).one()
    assert rule.strategy_key == "aggressive"


def test_below_low_threshold_both_strategies_irrigate(client):
    set_moisture(client, 0.10)

    for key in ("conservative", "aggressive"):
        save(client, key)
        assert evaluate(client)["recommendations"][0]["action"] == "irrigate"


def test_overview_facade_shows_saved_strategy_and_recommendation(client):
    set_moisture(client, 0.45)
    save(client, "aggressive")

    overview = client.get(f"/api/locations/{DEMO_LOCATION_ID}/overview").json()

    assert overview["strategy_key"] == "aggressive"
    assert overview["last_recommendation"]["recommendations"][0]["action"] == "irrigate"
    assert overview["zones"][0]["latest_readings"][0]["value"] == 0.45
