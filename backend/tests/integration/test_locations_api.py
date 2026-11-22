"""Builder (Phase 4) through HTTP into Postgres."""

from sqlalchemy import func, select

from infrastructure.persistence.models import LocationRow, ZoneRow


def zone(name, low=0.2, high=0.6):
    return {
        "name": name,
        "moisture_threshold_low": low,
        "moisture_threshold_high": high,
    }


def test_create_location_config_persists_location_and_zones(client, db):
    response = client.post(
        "/api/locations",
        json={
            "location_name": "Greenhouse B",
            "zones": [zone("Bench 1"), zone("Bench 2", 0.3, 0.7)],
        },
    )

    assert response.status_code == 201
    location_id = response.json()["location"]["id"]

    location = db.get(LocationRow, location_id)
    zones = db.scalars(
        select(ZoneRow).where(ZoneRow.location_id == location_id)
    ).all()

    assert location.name == "Greenhouse B"
    assert sorted((z.name, float(z.moisture_threshold_low)) for z in zones) == [
        ("Bench 1", 0.2),
        ("Bench 2", 0.3),
    ]


def test_invalid_builder_config_is_rejected_and_nothing_is_saved(client, db):
    before = db.scalar(select(func.count()).select_from(LocationRow))

    duplicate_zones = client.post(
        "/api/locations",
        json={
            "location_name": "Broken",
            "zones": [zone("Bench 1"), zone("bench 1")],
        },
    )
    low_above_high = client.post(
        "/api/locations",
        json={"location_name": "Broken", "zones": [zone("Bench 1", 0.7, 0.3)]},
    )

    assert duplicate_zones.status_code == 400
    assert low_above_high.status_code == 400
    assert db.scalar(select(func.count()).select_from(LocationRow)) == before


def test_rename_location_persists(client, db):
    location_id = client.post(
        "/api/locations",
        json={"location_name": "Old name", "zones": [zone("Bench 1")]},
    ).json()["location"]["id"]

    response = client.patch(
        f"/api/locations/{location_id}",
        json={"location_name": "New name"},
    )

    assert response.status_code == 200
    assert db.get(LocationRow, location_id).name == "New name"
