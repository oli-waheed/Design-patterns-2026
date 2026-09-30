from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_create_location_with_zones():
    response = client.post(
        "/api/locations",
        json={
            "location_name": "API Test Location",
            "zones": [
                {
                    "name": "Zone A",
                    "moisture_threshold_low": 0.3,
                    "moisture_threshold_high": 0.7,
                    "schedule": {
                        "start": "08:00",
                        "end": "18:00",
                    },
                },
                {
                    "name": "Zone B",
                    "moisture_threshold_low": 0.2,
                    "moisture_threshold_high": 0.8,
                    "schedule": {},
                },
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["location"]["name"] == "API Test Location"
    assert "id" in data["location"]

    assert len(data["zones"]) == 2
    assert data["zones"][0]["location_id"] == data["location"]["id"]
    assert data["zones"][1]["location_id"] == data["location"]["id"]


def test_create_location_with_invalid_threshold_returns_400():
    response = client.post(
        "/api/locations",
        json={
            "location_name": "Invalid Location",
            "zones": [
                {
                    "name": "Zone A",
                    "moisture_threshold_low": 0.8,
                    "moisture_threshold_high": 0.3,
                    "schedule": {},
                }
            ],
        },
    )

    assert response.status_code == 400


def test_get_location_returns_saved_configuration():
    create_response = client.post(
        "/api/locations",
        json={
            "location_name": "Read Test Location",
            "zones": [
                {
                    "name": "Zone A",
                    "moisture_threshold_low": 0.25,
                    "moisture_threshold_high": 0.75,
                    "schedule": {},
                }
            ],
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()
    location_id = created["location"]["id"]

    response = client.get(
        f"/api/locations/{location_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["location"]["id"] == location_id
    assert data["location"]["name"] == "Read Test Location"
    assert len(data["zones"]) == 1
    assert data["zones"][0]["name"] == "Zone A"


def test_list_locations_returns_created_locations():
    response = client.get("/api/locations")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    names = [location["name"] for location in data]

    assert "API Test Location" in names
    assert "Read Test Location" in names


def test_delete_location_returns_204():
    create_response = client.post(
        "/api/locations",
        json={
            "location_name": "Delete Test Location",
            "zones": [
                {
                    "name": "Zone A",
                    "moisture_threshold_low": 0.3,
                    "moisture_threshold_high": 0.7,
                    "schedule": {},
                }
            ],
        },
    )

    assert create_response.status_code == 201

    location_id = create_response.json()["location"]["id"]

    delete_response = client.delete(
        f"/api/locations/{location_id}"
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/api/locations/{location_id}"
    )

    assert get_response.status_code == 404