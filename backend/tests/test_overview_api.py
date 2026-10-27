
from uuid import uuid4

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_overview_returns_strategy_and_readings():
    # Create one location with two zones, including a zone that will remain empty.
    create_location_response = client.post(
        "/api/locations",
        json={
            "location_name": "Overview Integration Test",
            "zones": [
                {
                    "name": "Assigned Zone",
                    "moisture_threshold_low": 0.3,
                    "moisture_threshold_high": 0.7,
                    "schedule": {},
                },
                {
                    "name": "Empty Zone",
                    "moisture_threshold_low": 0.2,
                    "moisture_threshold_high": 0.6,
                    "schedule": {},
                },
            ],
        },
    )

    assert create_location_response.status_code == 201
    created_location = create_location_response.json()
    location_id = created_location["location"]["id"]

    zones = created_location["zones"]
    assigned_zone = next(
        zone for zone in zones if zone["name"] == "Assigned Zone"
    )
    empty_zone = next(
        zone for zone in zones if zone["name"] == "Empty Zone"
    )

    # Provision simulation devices.
    provision_response = client.post(
        "/api/devices/provision?family=simulation"
    )
    assert provision_response.status_code == 201
    provisioned_devices = provision_response.json()

    sensor = next(
        device
        for device in provisioned_devices
        if device["role"] == "sensor"
    )
    unassigned_device = next(
        device
        for device in provisioned_devices
        if device["role"] == "actuator"
    )

    # Assign only the sensor to the location's first zone.
    assignment_response = client.patch(
        f"/api/devices/{sensor['id']}/zone",
        json={"zone_id": assigned_zone["id"]},
    )
    assert assignment_response.status_code == 204

    # Record a reading for the assigned sensor.
    reading_response = client.post(
        f"/api/sensors/{sensor['id']}/read"
    )
    assert reading_response.status_code == 200

    # Confirm that the unassigned device has no location or zone assignment.
    # The provision endpoint creates unassigned devices by default.

    # Before a strategy is saved, overview must return null values.
    overview_response = client.get(
        f"/api/locations/{location_id}/overview"
    )
    assert overview_response.status_code == 200

    overview = overview_response.json()
    assert overview["location"]["id"] == location_id
    assert overview["location"]["name"] == "Overview Integration Test"

    # Only the assigned sensor is counted; the unassigned actuator is excluded.
    assert overview["device_counts"] == {
        "sensor": 1,
        "actuator": 0,
    }

    overview_zones = {
        zone["name"]: zone for zone in overview["zones"]
    }
    assert set(overview_zones) == {"Assigned Zone", "Empty Zone"}

    assigned_overview_zone = overview_zones["Assigned Zone"]
    assert len(assigned_overview_zone["devices"]) == 1
    assert assigned_overview_zone["devices"][0]["id"] == sensor["id"]

    assert len(assigned_overview_zone["latest_readings"]) == 1
    latest_reading = assigned_overview_zone["latest_readings"][0]
    assert latest_reading["device_id"] == sensor["id"]
    assert isinstance(latest_reading["value"], (int, float))
    assert latest_reading["unit"]
    assert latest_reading["recorded_at"]
    assert latest_reading["tracking_enabled"] is True
    assert latest_reading["sampling_interval_seconds"] >= 5

    empty_overview_zone = overview_zones["Empty Zone"]
    assert empty_overview_zone["devices"] == []
    assert empty_overview_zone["latest_readings"] == []

    all_overview_device_ids = {
        device["id"]
        for zone in overview["zones"]
        for device in zone["devices"]
    }
    assert unassigned_device["id"] not in all_overview_device_ids

    assert overview["strategy_key"] is None
    assert overview["last_recommendation"] is None

    # Save a strategy, then confirm the overview computes a recommendation.
    strategy_response = client.put(
        f"/api/locations/{location_id}/automation/strategy",
        json={"strategy_key": "conservative"},
    )
    assert strategy_response.status_code == 200

    updated_overview_response = client.get(
        f"/api/locations/{location_id}/overview"
    )
    assert updated_overview_response.status_code == 200

    updated_overview = updated_overview_response.json()
    assert updated_overview["strategy_key"] == "conservative"
    assert updated_overview["last_recommendation"] is not None


def test_overview_returns_location_and_empty_zone():
    create_response = client.post(
        "/api/locations",
        json={
            "location_name": "Overview Empty Zone Test",
            "zones": [
                {
                    "name": "Empty Zone",
                    "moisture_threshold_low": 0.3,
                    "moisture_threshold_high": 0.7,
                    "schedule": {},
                }
            ],
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    location_id = created["location"]["id"]

    response = client.get(
        f"/api/locations/{location_id}/overview"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["location"]["id"] == location_id
    assert data["location"]["name"] == "Overview Empty Zone Test"
    assert data["device_counts"] == {
        "sensor": 0,
        "actuator": 0,
    }
    assert len(data["zones"]) == 1
    assert data["zones"][0]["name"] == "Empty Zone"
    assert data["zones"][0]["devices"] == []
    assert data["zones"][0]["latest_readings"] == []
    assert data["strategy_key"] is None
    assert data["last_recommendation"] is None


def test_overview_returns_404_for_missing_location():
    missing_location_id = uuid4()

    response = client.get(
        f"/api/locations/{missing_location_id}/overview"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Location not found."
